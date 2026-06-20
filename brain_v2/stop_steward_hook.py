"""
stop_steward_hook.py — Stop hook (s082). The KNOWLEDGE-PROMOTION GATE.
======================================================================
Fires at turn-end. ONCE PER SESSION, it injects a NON-BLOCKING reminder to run the
`brain-steward` subagent before the conversation closes — so knowledge that surfaced
in the chat is promoted to a central, queryable store instead of dying with the
context window (CP-001). This is the *semantic* half of "dreaming"; curate.py is the
*structural* half. SessionEnd can only run shell (no LLM/subagent), so the steward —
which needs the transcript — is triggered here, via the in-session agent.

The objective the user set: "generate more knowledge on each topic at each close."

Design (mirrors stop_durability_hook.py — same proven contract):
  * NON-BLOCKING — emits hookSpecificOutput.additionalContext, never decision:block.
  * stop_hook_active guard — if already continuing from a stop hook, exit 0 (no loop).
  * ONCE PER SESSION — keyed on the session_start_ts marker; nudges a single time so
    it does not repeat every turn. (Wording tells the agent to act when wrapping up.)
  * Fail-safe — any error -> exit 0 silently; never breaks the session.

Rule: feedback_promote_conversational_knowledge_to_central_store (#158).
Agent: .claude/agents/brain-steward.md
"""
import json, sys, time
from pathlib import Path

HERE = Path(__file__).parent
TS_MARKER = HERE / ".session_start_ts"
NUDGE_MARKER = HERE / ".steward_nudged"


def session_key():
    """A stable id for THIS session = the session_start_ts written by the start hook
    (fallback: the current hour bucket if the marker is absent)."""
    try:
        return TS_MARKER.read_text(encoding="utf-8").strip()
    except Exception:
        return str(int(time.time() // 3600))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if data.get("stop_hook_active"):
        sys.exit(0)  # already continuing from a stop hook — never loop

    key = session_key()
    try:
        if NUDGE_MARKER.read_text(encoding="utf-8").strip() == key:
            sys.exit(0)  # already nudged this session — stay silent
    except Exception:
        pass
    try:
        NUDGE_MARKER.write_text(key, encoding="utf-8")
    except Exception:
        pass

    msg = (
        "KNOWLEDGE-PROMOTION GATE — before this conversation closes, run a brain-steward pass "
        "so new knowledge does not stay trapped in the chat (CP-001). "
        "Invoke the `brain-steward` subagent (Agent tool, subagent_type: \"brain-steward\"): "
        "HARVEST new/corrected durable facts from this session → CLASSIFY each to its home store "
        "(enhancement registry / claims.json / incidents.json / domain doc / capability_model / feedback_rules) "
        "→ DEDUPE (latest-wins, supersede not delete) → PROMOTE with evidence path + tier + cross-link "
        "(apply the cross-reference rule: grep the entity across ALL companions/reports and fix stale refs) "
        "→ run `python brain_v2/curate.py` and confirm coverage did not drop → output the Steward ledger. "
        "Route incidents to incident-analyst. If nothing is left trapped in chat, say so in one line and proceed. "
        "Rule #158 (feedback_promote_conversational_knowledge_to_central_store)."
    )
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": msg}
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
