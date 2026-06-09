"""
session_start_hook.py — SessionStart hook (s079).
=================================================
Two jobs, every session start:
  1. ONCE-PER-DAY brain curation ("dreaming" emulation) — on the FIRST session of the day,
     spawn curate.py in the BACKGROUND (non-blocking, detached). Guarded by a date marker so it
     runs at most once per active day. This replaces the OS scheduled task (no OS permission;
     native Claude Code hook; travels with settings.json).
  2. Inject the bootstrap context: read the LEAN index first (tiered loading), the model EXISTS,
     do not re-invent.

Fast (<1s): it only SPAWNS the background job and prints JSON. The heavy rebuild runs detached.
"""
import json, sys, subprocess, datetime
from pathlib import Path

HERE = Path(__file__).parent
MARKER = HERE / ".last_curation"
LOG = HERE / "curation.log"


def maybe_curate():
    """First session of the day -> spawn curate.py detached. Returns a note for the context."""
    try:
        today = datetime.date.today().isoformat()
        last = MARKER.read_text(encoding="utf-8").strip() if MARKER.exists() else ""
        if last == today:
            return ""  # already curated today
        MARKER.write_text(today, encoding="utf-8")
        flags = 0
        if sys.platform == "win32":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        with open(LOG, "a", encoding="utf-8") as lf:
            subprocess.Popen([sys.executable, str(HERE / "curate.py")],
                             cwd=str(HERE.parent), stdout=lf, stderr=subprocess.STDOUT,
                             creationflags=flags, close_fds=True)
        return " | daily brain curation (dreaming) started in background — see brain_v2/curation.log"
    except Exception as e:
        return f" | (curation skip: {str(e)[:60]})"


def main():
    try:
        sys.stdin.read()
    except Exception:
        pass
    note = maybe_curate()
    ctx = (
        "MANDATORY FIRST ACTION (TIERED LOADING): read brain_v2/BRAIN_INDEX.md FIRST (~800 tokens, lean L1 "
        "index) — NOT the full 400K brain_state.json. Then DRILL on demand: python brain_v2/graph_queries.py "
        "capability_gaps | capability <dom> | domain <name> | incident <id> | what_reads <table> | stats. "
        "Read full brain_v2/brain_state.json ONLY when you need depth the index lacks. CRITICAL: this project "
        "ALREADY HAS an operating model — Layer 15 capability_model (domain x 10 capabilities; AS-DESIGNED + "
        "AS-RUN; G=delta=product). DO NOT re-invent it, propose a new framework, or redesign brain_state.json "
        "schema — EXTEND it. Model: brain_v2/capability_model/. Verified research: brain_v2/research/ (8 closed; "
        "dedupe vs sources_index.json; never re-assert findings_registry refuted). If stale (graph_queries.py "
        "stats): python brain_v2/rebuild_all.py. See STOP block at top of CLAUDE.md." + note
    )
    print(json.dumps({
        "systemMessage": "Brain v3 — read brain_v2/BRAIN_INDEX.md first (lean). MODEL EXISTS (Layer 15) — do NOT re-invent." + note,
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx},
    }))


if __name__ == "__main__":
    main()
