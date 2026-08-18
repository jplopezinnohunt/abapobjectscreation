"""
agent_trace_hook.py — PostToolUse + SubagentStop. THE INVOCATION TRACE (s099).
=============================================================================
Records that a subagent actually RAN.

WHY THIS EXISTS
    Measured at s099: this project has four trigger layers and they are not equally
    reliable.

        hooks (4)          fired by the harness, always            MECHANICAL
        quality checks     fired by the rebuild, by glob           MECHANICAL
        agents (3)         fired only if the model chooses to      NOT
        skills (48)        fired only if the model chooses to      NOT

    stop_steward_hook.py cannot invoke the brain-steward. It prints a request asking the
    model to. If the model does not comply, nothing runs — and NOTHING RECORDS THAT
    NOTHING RAN. That is the disease of the 13 quality checks that sat idle for months,
    one floor up: what depends on somebody remembering does not happen.

    This session proved it. The steward gate fired twice; both times the pass was done by
    the main agent directly (which is correct per the project rule — the main agent
    executes, it does not delegate the protocol). But the `brain-steward` subagent ran
    zero times, and no artifact anywhere would tell you that.

    You cannot gate what you cannot measure. This is the measurement.

WHAT IT WRITES
    brain_v2/agent_invocations.jsonl — one line per event, append-only:
        {"at": iso, "event": "PostToolUse"|"SubagentStop", "agent": name,
         "session_ts": marker, "description": short}

    Append-only on purpose: a trace that can be rewritten is not a trace. Reading it is
    agent_invocation_check.py, which reports which agents have NEVER run and how long
    since each last did.

CONTRACT
    Fail-safe. Any error -> exit 0 silently. A trace that breaks the session is worse
    than no trace, and this one is not load-bearing for anything the user is doing.
"""
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
TRACE = HERE / "agent_invocations.jsonl"
TS_MARKER = HERE / ".session_start_ts"

# The Agent tool is surfaced under more than one name depending on the client; match any
# of them rather than guessing one and silently recording nothing.
AGENT_TOOLS = {"Task", "Agent"}


def session_ts():
    try:
        return TS_MARKER.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        sys.exit(0)

    event = payload.get("hook_event_name") or payload.get("hookEventName") or ""
    record = None

    if event == "PostToolUse":
        tool = payload.get("tool_name") or ""
        if tool not in AGENT_TOOLS:
            sys.exit(0)
        inp = payload.get("tool_input") or {}
        record = {
            "event": "PostToolUse",
            "agent": inp.get("subagent_type") or "(unspecified)",
            "description": str(inp.get("description") or "")[:120],
        }

    elif event == "SubagentStop":
        record = {
            "event": "SubagentStop",
            "agent": payload.get("subagent_type") or "(unspecified)",
            "description": "",
        }

    if record is None:
        sys.exit(0)

    record["at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    record["session_ts"] = session_ts()

    try:
        with TRACE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:          # noqa: BLE001 - a trace must never break a session
        sys.exit(0)
