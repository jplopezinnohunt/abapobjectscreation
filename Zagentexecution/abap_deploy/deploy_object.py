"""
deploy_object.py — THE single gated ABAP write path (ported from CRP `unescrp/scripts/deploy_object.py`).

This REPLACES the ~78 ad-hoc deploy_*/reconstruct_*/force_*/direct_insert_* scripts with ONE path that
runs the CRP gate stack. It is the disciplined answer to INC-CLASS-LOSS: every gate below exists because
the incident skipped it.

GATE STACK (frozen order):
  0. OWN-OBJECTS-ONLY      — object MUST be in objects_manifest.yaml (tier=custom) AND Z*/Y*/customer ns.
                             (Manifest membership is THE gate that would have stopped the N_MENARD write.)
  1. TADIR / metadata pre-flight — object exists; for CLASS, SEOCLASS present (no write to broken metadata).
  2. PRE-READBACK          — snapshot D01 active source to artifacts/readback/<ts>/<name>.PRE_DEPLOY.abap.
  3. HARD DIFF-GATE        — normalize canonical(local) vs live(D01); HALT (exit 3) if the write would
                             DELETE lines D01 has, unless --accept-deletions "<reason>".
  4. W-5 operator guard    — warn on operator/condition inversions on control-flow lines (logic flip).
  5. CONCURRENT-WRITER     — warn if another live session is writing to D01 (we hit this with S-123).
  6. CONFIRMATION          — refuse to touch D01 without --yes (you confirm in chat first).
  7. WRITE (gated)         — lock -> freshness re-check -> set_source(corrNr) -> POST-readback byte-verify
                             -> unlock -> activate. The PUT respects the ALLOW_D01_WRITES kill-switch.
  8. POST-READBACK verify  — D01 active == canonical, else exit 1.

DEFAULT is --dry-run (gates 0-5 only, no write). Read-only gates work today even with writes kill-switched.

NOT YET (POINT B, deferred by JP 2026-06-15): create/RELEASE the transport + ATC-via-REST gate. The release
is what makes the durable version; today we pin to an open TR and release manually (SE09).

Usage:
  python deploy_object.py ZCL_CRP_CERT_READER --dry-run
  python deploy_object.py ZCL_CRP_CERT_READER --yes                 # real write (needs ALLOW_D01_WRITES=1)
  python deploy_object.py ZCL_CRP_CERT_READER --yes --accept-deletions "refactor: removed dead method foo"
"""
import os
import sys
import argparse
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mcp-backend-server-python"))

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

from sap_adt_rfc_client import from_env, AdtRfcError  # proven RFC-backed ADT client

MANIFEST = os.path.join(HERE, "objects_manifest.yaml")
READBACK_DIR = os.path.join(HERE, "artifacts", "readback")
ACCEPT_LOG = os.path.join(HERE, "artifacts", "accept-deletions.log")

OWN_NS_PREFIXES = ("Z", "Y")  # plus /namespace/ — customer namespace


# ── helpers ──────────────────────────────────────────────────────────────────
def normalize(src: str) -> str:
    """CRLF->LF, strip trailing whitespace per line, single final newline. (CRP parity.)"""
    lines = [ln.rstrip() for ln in src.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def is_own_namespace(name: str) -> bool:
    n = name.upper()
    return n.startswith(OWN_NS_PREFIXES) or n.startswith("/")


def load_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_entry(man, name):
    for o in man.get("objects", []):
        if o["name"].upper() == name.upper():
            return o
    return None


def concurrent_writers(self_pid):
    """Scan ~/.claude/projects/*/*.jsonl modified in the last 150s for active deploy/LOCK/activation
    signatures from OTHER sessions (ported from CRP S-123 concurrent-writer guard)."""
    import glob, time
    root = os.path.expanduser("~/.claude/projects")
    hits = []
    now = time.time()
    for f in glob.glob(os.path.join(root, "*", "*.jsonl")):
        try:
            if now - os.path.getmtime(f) > 150:
                continue
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                tail = fh.read()[-8000:]
            if any(s in tail for s in ("deploy_object", "/adt/activation", "set_source", "write_source", "_action=LOCK")):
                hits.append(os.path.basename(f))
        except OSError:
            continue
    return hits


def hard_diff_gate(canonical: str, live: str, accept_deletions: str):
    """Return (status, deleted_lines). status: 'identical' | 'ok' | 'HALT'."""
    can = normalize(canonical).split("\n")
    liv = normalize(live).split("\n")
    if can == liv:
        return "identical", []
    can_set = set(can)
    deleted = [ln for ln in liv if ln.strip() and ln not in can_set]  # in D01, not in local -> would be removed
    if deleted and not accept_deletions:
        return "HALT", deleted
    return "ok", deleted


def w5_operator_guard(canonical: str, live: str):
    """Warn on operator inversions on control-flow lines (CRP W-5, lightweight)."""
    CTRL = ("IF ", "ELSEIF ", "WHEN ", "CHECK ", "WHILE ", "WHERE ", "AND ", "OR ")
    OPS = ("=", "<>", "EQ", "NE", "GT", "LT", "GE", "LE", "ABAP_TRUE", "ABAP_FALSE",
           "IS INITIAL", "IS NOT INITIAL", "IS BOUND", "NOT ")
    can = set(normalize(canonical).split("\n"))
    removed = [ln for ln in normalize(live).split("\n") if ln not in can]
    flags = []
    for ln in removed:
        u = ln.upper()
        if any(c in u for c in CTRL) and any(o in u for o in OPS):
            flags.append(ln.strip())
    return flags


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Gated ABAP deploy (CRP gate stack)")
    ap.add_argument("name", help="object name (must be in objects_manifest.yaml)")
    ap.add_argument("--yes", action="store_true", help="confirm a REAL write to D01")
    ap.add_argument("--dry-run", action="store_true", help="run gates only, never write (default)")
    ap.add_argument("--accept-deletions", default="", metavar="REASON",
                    help="acknowledge that the write removes lines D01 has (audited)")
    args = ap.parse_args()
    dry = args.dry_run or not args.yes

    man = load_manifest()
    entry = find_entry(man, args.name)

    # GATE 0 — OWN-OBJECTS-ONLY (manifest membership + namespace)
    if entry is None:
        sys.exit(f"HALT gate-0: {args.name} is NOT in objects_manifest.yaml. "
                 f"We only deploy objects we own. (This gate would have stopped INC-CLASS-LOSS.)")
    if entry.get("tier") != "custom":
        sys.exit(f"HALT gate-0: {args.name} is tier={entry.get('tier')} — not hand-deployable.")
    if not is_own_namespace(args.name):
        sys.exit(f"HALT gate-0: {args.name} is not in Z*/Y*/customer namespace.")
    otype = entry.get("type", "CLASS")
    print(f"gate-0 OWN-OBJECTS-ONLY: {args.name} ({otype}) is in manifest, tier=custom, own-ns  OK")

    adt = from_env("D01")

    # GATE 1 — TADIR / metadata pre-flight
    info = adt.check_tadir(otype, args.name)
    if not info.get("found"):
        sys.exit(f"HALT gate-1: {args.name} not in TADIR on D01.")
    print(f"gate-1 TADIR: package={info.get('package')} author={info.get('author')}  OK")

    # GATE 2 — PRE-READBACK
    try:
        live = adt.read_source(otype, args.name)
    except AdtRfcError as e:
        sys.exit(f"HALT gate-2: cannot read live source ({e}).")
    ts = os.environ.get("DEPLOY_TS") or "session"
    snap_dir = os.path.join(READBACK_DIR, ts)
    os.makedirs(snap_dir, exist_ok=True)
    snap = os.path.join(snap_dir, f"{args.name.lower()}.PRE_DEPLOY.abap")
    with open(snap, "w", encoding="utf-8") as f:
        f.write(live)
    print(f"gate-2 PRE-READBACK: {len(live.splitlines())} lines snapshotted -> {snap}  OK")

    # canonical (local mirror)
    canon_path = os.path.join(HERE, entry["canonical"])
    if not os.path.exists(canon_path):
        print(f"gate-3 DIFF: no canonical mirror at {entry['canonical']} yet.")
        print("        -> run verify_mirror.py --adopt to seed it from D01 first. Nothing to deploy.")
        print("\nDRY-RUN complete (read-only). No write attempted." if dry else
              "\nNo canonical source to write. Stopping.")
        return 0
    with open(canon_path, encoding="utf-8") as f:
        canonical = f.read()

    # GATE 3 — HARD DIFF-GATE
    status, deleted = hard_diff_gate(canonical, live, args.accept_deletions)
    if status == "identical":
        print("gate-3 DIFF: canonical == D01 active. Nothing to deploy. OK")
        return 0
    if status == "HALT":
        print(f"\n*** HALT gate-3 (exit 3): the write would REMOVE {len(deleted)} line(s) that exist on D01:")
        for ln in deleted[:40]:
            print(f"   - {ln}")
        if len(deleted) > 40:
            print(f"   ... (+{len(deleted) - 40} more)")
        print('Pass --accept-deletions "<reason>" to proceed (it is audited).')
        sys.exit(3)
    if deleted:
        print(f"gate-3 DIFF: {len(deleted)} deletion(s) ACCEPTED — reason: {args.accept_deletions}")
        os.makedirs(os.path.dirname(ACCEPT_LOG), exist_ok=True)
        with open(ACCEPT_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.date.today()} {args.name} ({len(deleted)} lines): {args.accept_deletions}\n")
    else:
        print("gate-3 DIFF: additive/in-place change (no deletions). OK")

    # GATE 4 — W-5 operator guard
    flags = w5_operator_guard(canonical, live)
    if flags:
        print(f"gate-4 W-5 WARNING: {len(flags)} control-flow line(s) changed operators — verify logic not inverted:")
        for ln in flags[:10]:
            print(f"   ~ {ln}")

    # GATE 5 — CONCURRENT-WRITER guard
    others = concurrent_writers(os.getpid())
    if others:
        print(f"gate-5 CONCURRENT-WRITER WARNING: {len(others)} other live session(s) may be writing to D01: {others}")
        print("        (One-writer-at-a-time. Confirm no parallel deploy before proceeding.)")

    if dry:
        print("\nDRY-RUN complete — all read-only gates passed. No write attempted.")
        print("Re-run with --yes to write (requires ALLOW_D01_WRITES=1; transport release = POINT B).")
        return 0

    # GATE 6 — CONFIRMATION (already via --yes) + GATE 7 WRITE
    corrnr = (man.get("meta") or {}).get("workbench_tr")
    print(f"\ngate-7 WRITE: transport pin = {corrnr or '(none — POINT B)'}")
    lock = None
    try:
        lock = adt.lock(otype, args.name)
        # freshness re-check (W-2): re-read after lock; if D01 changed vs our diff baseline, HALT
        fresh = adt.read_source(otype, args.name)
        if normalize(fresh) != normalize(live):
            sys.exit("HALT gate-7 (W-2): D01 changed after lock — stale baseline. Re-run.")
        adt.write_source(otype, args.name, canonical, lock)   # respects ALLOW_D01_WRITES kill-switch
        # GATE 8 — POST-READBACK byte-verify
        after = adt.read_source(otype, args.name)
        if normalize(after) != normalize(canonical):
            print("gate-8 POST-READBACK: MISMATCH — D01 active != canonical (exit 1)")
            sys.exit(1)
        print("gate-8 POST-READBACK: D01 active == canonical  OK")
    finally:
        if lock:
            try:
                adt.unlock(otype, args.name, lock)
            except Exception:
                pass
    adt.activate(otype, args.name)
    print("WRITE + ACTIVATE complete. (Remember POINT B: release the transport via SE09 for a durable version.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
