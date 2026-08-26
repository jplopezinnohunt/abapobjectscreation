"""Is the open work REACHABLE from the files a fresh session actually reads?

WHY THIS EXISTS
---------------
Session #099 landed a complete Purpose of Payment analysis: claims 484-496, two companions, a
source doc, a closed research, a first-class incident record with the ten-code fix and the
transport order. All durable. All queryable. And then JP asked the question that mattered --
"if we close this session, how do you reuse it?" -- and the measurement was:

    brain_v2/BRAIN_INDEX.md   (every session's mandatory first read)   0 mentions
    MEMORY.md                 (auto-loaded)                            0 mentions
    graph_queries.py incident INC-EGYPT-PPC                            the complete fix

The knowledge was stored and unreachable. The only way to find it was to already know the
incident ID -- which is exactly what a new session does not know. The index printed the
incident COUNT and never said which ones. A count is not a pointer.

So this check asserts the property that actually survives a session boundary: every incident
still awaiting action must be REACHABLE from the bootstrap index, and one carrying a hard
deadline must also state what to do next.

It does not check that the knowledge is good. It checks that a stranger can find it.
"""
import io
import json
import sys
from pathlib import Path

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "herramientas",  # datos_sap | conocimiento | herramientas
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": "every open incident must be reachable from BRAIN_INDEX.md",
}

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
INDEX = REPO / "brain_v2" / "BRAIN_INDEX.md"
INCIDENTS = REPO / "brain_v2" / "incidents" / "incidents.json"
DONE = {"CLOSED", "RESOLVED", "DONE", "CLOSED_WITH_CLEANUP"}


def main():
    if not INCIDENTS.exists():
        print("SKIPPED - incidents.json not found. Not a pass: nothing was verified.")
        return 3
    if not INDEX.exists():
        print("FINDING - BRAIN_INDEX.md does not exist. Every session is told to read it "
              "first; nothing can be reached through a file that is not there.")
        return 1

    index = INDEX.read_text(encoding="utf-8")
    data = json.loads(INCIDENTS.read_text(encoding="utf-8"))
    inc = data if isinstance(data, list) else data.get("incidents", [])
    live = [i for i in inc if str(i.get("status", "")).upper() not in DONE]

    print("=" * 74)
    print("knowledge reachability - can a fresh session find the open work?")
    print("=" * 74)
    print("open incidents: {}".format(len(live)))

    unreachable, mute = [], []
    for i in live:
        iid = i.get("id") or ""
        if iid and iid not in index:
            unreachable.append(i)
        elif i.get("deadline") and not i.get("next_action"):
            mute.append(i)

    for i in unreachable:
        print("  [UNREACHABLE] {} - {} - not mentioned in BRAIN_INDEX.md".format(
            i.get("id"), i.get("status")))
        print("      a session would have to already know this id to ever find it")
    for i in mute:
        print("  [NO NEXT ACTION] {} - DUE {} but no next_action recorded".format(
            i.get("id"), i.get("deadline")))
        print("      a deadline with no stated next step is a date, not a plan")

    if unreachable or mute:
        print()
        print("Fix at the GENERATOR (brain_v2/build_brain_index.py), never by hand-editing")
        print("BRAIN_INDEX.md -- it is regenerated on every rebuild and a hand edit is lost.")
        return 1

    print("\nPASS - every open incident is reachable from the bootstrap index, and every")
    print("one with a deadline says what to do next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
