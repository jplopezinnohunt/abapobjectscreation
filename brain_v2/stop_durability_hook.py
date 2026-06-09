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
        "And ALWAYS state the 2 assets that are LOCAL-ONLY and NOT in git: the Golden DB "
        "(~6.4GB, gitignored) and ~/.claude memory — git does not protect them; a disk/offsite backup does."
    )
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": msg}
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
