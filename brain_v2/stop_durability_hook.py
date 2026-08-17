"""
stop_durability_hook.py — Stop hook (s080). The DURABILITY GATE, enforced.
========================================================================
Fires at the end of every turn. When THIS session has uncommitted SOURCE changes
not yet in git, it injects a NON-BLOCKING reminder to commit (focused) and to flag
the 2 assets that are local-only / not in git (Golden DB + ~/.claude memory).

Design (matches the Claude Code Stop-hook contract):
  * NON-BLOCKING — emits hookSpecificOutput.additionalContext, never decision:block.
    The gate informs; it does not force a commit mid-task or risk a stop-loop.
  * stop_hook_active guard — if already in a stop continuation, exit 0 immediately.
  * Session-scoped — only flags files with mtime >= .session_start_ts (written by
    session_start_hook.py), so the dozens of STALE uncommitted files from other
    sessions don't create noise. Fallback window = last 6h if the marker is absent.
  * Dedup'd — nudges only when the uncommitted-source SET changes (sha1 in
    .last_durability_nudge), so it does not repeat the same reminder every turn.
  * Source-only — code/rules/knowledge/config; never generated artifacts
    (brain_state.json, brain_v2/output|index, *.db, *.log) or the gitignored Golden DB.
  * Fail-safe — any error -> exit 0 silently; never breaks the session.
"""
import json, sys, os, time, subprocess, hashlib
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent
ROOT = HERE.parent
TS_MARKER = HERE / ".session_start_ts"
NUDGE_MARKER = HERE / ".last_durability_nudge"

SOURCE_PREFIXES = (
    "scripts/",
    "brain_v2/agent_rules/", "brain_v2/capability_model/", "brain_v2/ingestors/",
    "brain_v2/core/", "brain_v2/claims/", "brain_v2/incidents/", "brain_v2/agi/",
    "brain_v2/annotations/", "brain_v2/research/",
    ".agents/", "knowledge/", ".claude/settings",
)
EXCLUDE_SUBSTR = (
    "brain_v2/output/", "brain_v2/index/", "brain_state.json", "/sqlite/",
    ".db", ".log", ".session_start_ts", ".last_curation", ".last_durability_nudge",
)


def is_source(path):
    p = path.replace("\\", "/")
    if any(x in p for x in EXCLUDE_SUBSTR):
        return False
    if any(p.startswith(pre) for pre in SOURCE_PREFIXES):
        return True
    # top-level brain_v2 python (build_brain_state.py, rebuild_all.py, graph_queries.py, hooks)
    if p.startswith("brain_v2/") and p.endswith(".py") and p.count("/") == 1:
        return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if data.get("stop_hook_active"):
        sys.exit(0)  # already continuing from a stop hook — never loop
    cwd = data.get("cwd") or str(ROOT)

    try:
        r = subprocess.run(["git", "status", "--porcelain"], cwd=cwd,
                           capture_output=True, text=True, timeout=8)
        if r.returncode != 0:
            sys.exit(0)
        lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    except Exception:
        sys.exit(0)

    try:
        cutoff = float(TS_MARKER.read_text(encoding="utf-8").strip())
    except Exception:
        cutoff = time.time() - 6 * 3600  # fallback: this-session ~= last 6h

    changed = []
    for ln in lines:
        path = ln[3:].strip() if len(ln) > 3 else ln.strip()
        if " -> " in path:                 # rename: keep the new name
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        if not is_source(path):
            continue
        full = os.path.join(cwd, path)
        try:
            if os.path.exists(full) and os.path.getmtime(full) < cutoff:
                continue                   # not touched this session
        except Exception:
            pass
        changed.append(path)

    if not changed:
        sys.exit(0)

    _ = local_only_status  # defined below; referenced from the message build
    sig = hashlib.sha1("\n".join(sorted(changed)).encode("utf-8")).hexdigest()
    try:
        if NUDGE_MARKER.read_text(encoding="utf-8").strip() == sig:
            sys.exit(0)                    # same set already nudged — stay silent
    except Exception:
        pass
    try:
        NUDGE_MARKER.write_text(sig, encoding="utf-8")
    except Exception:
        pass

    shown = changed[:12]
    flist = "".join("\n  - " + f for f in shown)
    if len(changed) > 12:
        flist += f"\n  - (+{len(changed) - 12} more)"
    msg = (
        "DURABILITY GATE — this session has uncommitted SOURCE changes not yet in git:" + flist +
        "\nCommit them FOCUSED before the session closes: `git add <these files>` then commit "
        "(NEVER `git add -A`; do NOT commit brain_state.json — it is generated/entangled). "
        + unlanded_status()
        + local_only_status()
    )
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": msg}
    }))
    sys.exit(0)


def unlanded_status():
    """Name what was discovered and never written down. s099: discovery without landing
    is the largest silent loss in this project — bigger than any single uncommitted file."""
    try:
        p = ROOT / "brain_v2" / "methods" / "unlanded_discoveries.json"
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return ""
    items = d.get("items") or []
    if not items:
        return ""
    high = [i for i in items if i.get("severity") == "HIGH"]
    names = ", ".join(i["term"] for i in (high or items)[:6])
    return ("\nUNLANDED DISCOVERIES — "
            f"{len(items)} custom identifiers the code touches that the brain cannot explain, "
            f"{len(high)} of them gating a routine that can BLOCK a posting: {names}. "
            "Each is a thing we found and never wrote down. Land the ones this session "
            "touched as a claim before closing "
            "(python brain_v2/methods/unlanded_discoveries.py for the full list).")


def _dir_size(path):
    total = files = 0
    for root, dirs, names in os.walk(path):
        dirs[:] = [d for d in dirs
                   if d not in {"file-history", "shell-snapshots", "statsig", "telemetry",
                                "__pycache__", "node_modules", "tasks", "tool-results"}]
        for n in names:
            try:
                total += os.path.getsize(os.path.join(root, n))
                files += 1
            except OSError:
                pass
    return total, files


def local_only_status():
    """MEASURE the two local-only assets at close — never quote a hardcoded size.

    s099: the figure '~6.4 GB' had been repeated in the memory, in this hook and in the
    session-start hook for months. Measured, the Golden DB is 15.2 GB — off by 2.4x, and a
    backup plan sized on the stale number is wrong. A constant that describes a live asset
    rots silently, which is the same class of defect as a reminder that never executes.

    And the size is not decoration: if it CHANGED since the last close, the existing backup
    no longer covers what is on disk, so the change itself is the trigger.
    """
    state_path = Path(__file__).parent / ".local_only_state.json"
    gold = ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
    mem = Path(os.path.expanduser("~")) / ".claude" / "projects"

    now = {}
    try:
        now["golden_bytes"] = gold.stat().st_size if gold.exists() else 0
    except OSError:
        now["golden_bytes"] = 0
    try:
        b, f = _dir_size(mem)
        now["memory_bytes"], now["memory_files"] = b, f
    except Exception:
        now["memory_bytes"] = now["memory_files"] = 0

    prev = {}
    try:
        prev = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        pass

    def gb(x):
        return f"{x / 1024**3:.2f} GB"

    parts = [
        "\nLOCAL-ONLY ASSETS (git does NOT protect these — measured just now): "
        f"Golden DB {gb(now['golden_bytes'])} · ~/.claude memory {gb(now['memory_bytes'])} "
        f"in {now['memory_files']} files."
    ]

    drift = []
    for key, label in (("golden_bytes", "Golden DB"), ("memory_bytes", "memory")):
        old = prev.get(key)
        if old and old != now[key]:
            delta = now[key] - old
            drift.append(f"{label} {'+' if delta > 0 else ''}{delta / 1024**2:.1f} MB")
    if drift:
        parts.append(
            "CHANGED since the last close (" + ", ".join(drift) + ") — so any existing "
            "backup no longer covers what is on disk. THE CHANGE IS THE TRIGGER: run "
            "`python scripts/backup_golden.py --dest <disk>` or say explicitly that it was "
            "deferred and why."
        )
    elif prev:
        parts.append("Unchanged since the last close — an existing backup still covers it.")
    else:
        parts.append("No prior measurement on record; this is the baseline.")

    try:
        pointer = ROOT / "Zagentexecution" / "sap_data_extraction" / "backup_location.json"
        if pointer.exists():
            p = json.loads(pointer.read_text(encoding="utf-8"))
            parts.append(f"Last recorded backup destination: {p.get('dest', '?')}.")
        else:
            parts.append("NO backup destination has ever been recorded "
                         "(Zagentexecution/sap_data_extraction/backup_location.json absent).")
    except Exception:
        pass

    try:
        now["recorded_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        state_path.write_text(json.dumps(now, indent=1), encoding="utf-8")
    except Exception:
        pass

    return " ".join(parts)


if __name__ == "__main__":
    main()
