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
import json, sys, subprocess, datetime, time
from pathlib import Path

HERE = Path(__file__).parent
MARKER = HERE / ".last_curation"
LOG = HERE / "curation.log"
TS_MARKER = HERE / ".session_start_ts"          # consumed by stop_durability_hook.py
NUDGE_MARKER = HERE / ".last_durability_nudge"   # reset each session so leftovers re-nudge once


def stamp_session():
    """Record session-start epoch (so the Stop durability hook scopes to THIS session's
    files) and reset the durability dedup marker so any leftover uncommitted source from a
    prior session gets one fresh nudge."""
    try:
        TS_MARKER.write_text(str(time.time()), encoding="utf-8")
        if NUDGE_MARKER.exists():
            NUDGE_MARKER.unlink()
    except Exception:
        pass


def meta_headline():
    """Read the cached meta-capability self-assessment (instant — no recompute) and return the
    one-line headline. This makes our OWN way-of-working maturity 'considered at every session start'
    (user directive 2026-06-22): every session opens knowing its weakest lever to improve."""
    try:
        m = json.loads((HERE / "meta_capability.json").read_text(encoding="utf-8"))
        weak = m.get("weakest", "?")
        ws = m.get("dimensions", {}).get(weak, {}).get("score", 0)
        return (f" SELF-ASSESSMENT (meta-capability, measured): {m.get('meta_maturity_pct','?')}% maturity in "
                f"OUR way of working; weakest capability = {weak} ({ws}). Run `python brain_v2/meta_capability.py` "
                f"for the sub-lever scorecard and `python brain_v2/claims_health.py` for the claim-verification "
                f"worklist. Pick ONE weak sub-lever and move it this session; that is how we evolve.")
    except Exception:
        return " (meta_capability.json missing — run python brain_v2/meta_capability.py to self-assess)"


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


def cycle_headline():
    """Has the loop turned? Surfaced at session start, because DETECTION IS NOT ACTION.

    The cycle is scheduled weekly. A scheduled task that stops firing produces no error and
    no artifact, and the absence of fresh artifacts reads as 'nothing changed' — the most
    expensive kind of silence. check_triggers can MEASURE the gap, but nothing acts on a
    measurement nobody reads, so the instruction has to reach the agent at the one moment it
    is guaranteed to look: the start of a session.
    """
    import datetime
    st = HERE / "methods" / "cycle_state.json"
    if not st.exists():
        return (" | LOOP: the analysis cycle has NEVER recorded a run — RUN IT NOW: "
                "python brain_v2/methods/run_analysis_cycle.py")
    try:
        d = json.loads(st.read_text(encoding="utf-8"))
        last = datetime.datetime.fromisoformat(d["last_run_utc"])
        days = (datetime.datetime.now(datetime.timezone.utc) - last).days
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return " | LOOP: cycle_state.json is unreadable — run the cycle and let it rewrite it"
    if days > 8:
        return (f" | LOOP STALE: the analysis cycle last ran {days} days ago (weekly expected). "
                f"A missed schedule is silent — RUN IT NOW: "
                f"python brain_v2/methods/run_analysis_cycle.py")
    if d.get("steps_failed"):
        return (f" | LOOP: last cycle {days}d ago had {d['steps_failed']} FAILED step(s): "
                f"{', '.join(d.get('failed') or [])[:80]} — fix before trusting its artifacts")
    return f" | loop healthy: cycle ran {days}d ago, {d.get('steps_ran')} steps, 0 failed"


def main():
    try:
        sys.stdin.read()
    except Exception:
        pass
    stamp_session()
    note = maybe_curate()
    meta = meta_headline()
    loop = cycle_headline()
    ctx = (
        "MANDATORY FIRST ACTION (TIERED LOADING): read brain_v2/BRAIN_INDEX.md FIRST (~800 tokens, lean L1 "
        "index) — NOT the full 400K brain_state.json. Then DRILL on demand: python brain_v2/graph_queries.py "
        "capability_gaps | capability <dom> | domain <name> | incident <id> | what_reads <table> | stats. "
        "Read full brain_v2/brain_state.json ONLY when you need depth the index lacks. CRITICAL: this project "
        "ALREADY HAS an operating model — Layer 15 capability_model (domain x 10 capabilities; AS-DESIGNED + "
        "AS-RUN; G=delta=product). DO NOT re-invent it, propose a new framework, or redesign brain_state.json "
        "schema — EXTEND it. Model: brain_v2/capability_model/. Verified research: brain_v2/research/ (8 closed; "
        "dedupe vs sources_index.json; never re-assert findings_registry refuted). If stale (graph_queries.py "
        "stats): python brain_v2/rebuild_all.py. See STOP block at top of CLAUDE.md. "
        "OPERATING GATES (apply AT the decision point, NOT from memory — this is the working model, not intuition): "
        "(1) BLOCKED — when a read/method fails, STOP: test the CORE tool empirically (reads = RFC_READ_TABLE over SNC SSO; "
        "verify, never assume), then conclude against the HARD CONSTRAINTS [P01 = READ-ONLY via RFC/SSO ONLY; NO ADT against "
        "prod; NO new objects/transports in P01; Excel is NEVER a source]. Park the gap as an execution_backlog task. Do NOT "
        "invent exotic channels (ADT-HTTP, SPNEGO/password, deploy-to-P01) — that re-litigates settled constraints (rule #156). "
        "(2) CLOSE — commit SOURCE changes FOCUSED (never 'git add -A'; brain_state.json is GENERATED, don't commit it entangled) "
        "AND ALWAYS flag the 2 assets that are LOCAL-ONLY, not in git: the Golden DB (15.2GB measured 2026-08-17, gitignored) + ~/.claude memory "
        "(git does NOT protect them — a disk/offsite backup does); then capture SAP learnings." + note + meta + loop
    )
    print(json.dumps({
        "systemMessage": "Brain v3 — read brain_v2/BRAIN_INDEX.md first (lean). MODEL EXISTS (Layer 15) — do NOT re-invent." + note + meta + loop,
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx},
    }))


if __name__ == "__main__":
    main()
