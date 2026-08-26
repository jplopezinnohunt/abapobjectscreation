"""Incident record coverage check — every incident doc must be reachable from the brain.

WHY THIS EXISTS
---------------
Session #099 opened and found 11 incident docs under knowledge/incidents/ but only 7
first-class records in brain_v2/incidents/incidents.json. Three incidents
(INC-000011781, INC-180995, INC-CLASS-LOSS-2026-06) existed only as prose on disk.

That is not a cosmetic gap. Step 2 of the sap_incident_analyst protocol is BRAIN LOOKUP:
the agent traverses brain_state.incidents -> indexes.by_incident -> objects[X]. A doc with
no record is not in that traversal, so the next agent handling a sibling ticket starts from
zero and re-derives what we already paid for. INC-000011781 in particular carries the richest
BCM signatory precedent we have (IT1218 node selection, the drift sweep, the role gap) — it
was invisible for ~2 months.

Root cause of the gap: the PMO recorded "TODO: run rebuild_all.py to fold INC-000011781 in"
(2026-06-18) and it never ran. A TODO is not a control. This is the control.

WHAT IT CHECKS
--------------
1. Every INC-*.md under knowledge/incidents/ has a record in incidents.json
2. Every record's analysis_doc points at a file that exists
3. Every record carries the fields BRAIN LOOKUP actually reads

Companion docs (a second .md for the same incident, e.g. *_full_history.md or
*_executive_brief.md) are matched to their parent by incident id and do not need their own
record.

USAGE
-----
    python Zagentexecution/quality_checks/incident_record_coverage_check.py

Exit 0 = clean. Exit 1 = at least one incident is invisible to the brain.
"""

from __future__ import annotations

# --- self-declaration, read by quality_checks/run_all.py -------------------
# An undeclared script is reported as UNCLASSIFIED and fails the runner loudly:
# a central registry is a list someone forgets to update.
QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": "every incident doc must have a first-class record the brain can reach",
}
# --------------------------------------------------------------------------

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO / "knowledge" / "incidents"
RECORDS = REPO / "brain_v2" / "incidents" / "incidents.json"

# Fields the BRAIN LOOKUP traversal (skill step 2) actually dereferences.
REQUIRED_FIELDS = [
    "id",
    "status",
    "title",
    "domain",
    "analysis_doc",
    "related_objects",
]

# id as it appears at the start of a doc filename: INC-000006073, INC-180995,
# INC-BUDGETRATE-EQG, INC-CLASS-LOSS-2026-06
DOC_ID_RE = re.compile(r"^(INC-[A-Z0-9]+(?:-[A-Z0-9]+)*?)(?:_|\.md$)")


def doc_incident_id(filename: str) -> str | None:
    m = DOC_ID_RE.match(filename)
    return m.group(1) if m else None


def main() -> int:
    if not RECORDS.exists():
        print(f"FAIL: {RECORDS} not found")
        return 1
    if not DOCS_DIR.exists():
        print(f"FAIL: {DOCS_DIR} not found")
        return 1

    records = json.loads(RECORDS.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in records}

    docs: dict[str, list[str]] = {}
    for p in sorted(DOCS_DIR.glob("INC-*.md")):
        inc_id = doc_incident_id(p.name)
        if inc_id is None:
            docs.setdefault("__UNPARSEABLE__", []).append(p.name)
            continue
        docs.setdefault(inc_id, []).append(p.name)

    problems: list[str] = []

    # 1 — docs with no first-class record
    for inc_id, files in sorted(docs.items()):
        if inc_id == "__UNPARSEABLE__":
            problems.append(
                f"UNPARSEABLE filename(s), cannot map to an incident id: {', '.join(files)}"
            )
            continue
        if inc_id not in by_id:
            problems.append(
                f"{inc_id}: doc(s) on disk ({', '.join(files)}) but NO record in "
                f"incidents.json -> invisible to BRAIN LOOKUP"
            )

    # 2 — records whose analysis_doc is dangling
    for inc_id, rec in sorted(by_id.items()):
        doc = rec.get("analysis_doc")
        if not doc:
            problems.append(f"{inc_id}: record has no analysis_doc")
            continue
        if not (REPO / doc).exists():
            problems.append(f"{inc_id}: analysis_doc points at a missing file -> {doc}")

    # 3 — records missing fields the traversal reads
    for inc_id, rec in sorted(by_id.items()):
        missing = [f for f in REQUIRED_FIELDS if not rec.get(f)]
        if missing:
            problems.append(f"{inc_id}: record missing field(s) {missing}")

    docs_count = len([k for k in docs if k != "__UNPARSEABLE__"])
    print(f"incident docs (distinct ids): {docs_count}")
    print(f"first-class records:          {len(records)}")

    if problems:
        print(f"\nFAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        print(
            "\nFix: add the missing record to brain_v2/incidents/incidents.json "
            "(schema: see any existing record), then run python brain_v2/rebuild_all.py"
        )
        return 1

    print("\nOK — every incident doc is reachable from the brain, every record resolves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
