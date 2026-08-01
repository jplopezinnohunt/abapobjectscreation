"""audit_prose_classifications.py — which analysis is trapped in prose? (s097)

A classification written into a markdown table is invisible to every algorithm. It reads
well, it is often correct, and nothing can query it — so the next question RE-DERIVES it,
and the two answers drift apart with nothing able to notice the drift.

This is not hypothetical. `knowledge/domains/Integration/integration_map_complete.md`
classifies 48 integration flows into 8 channels — RFC, IDoc, middleware, file jobs, batch
input, LSMW, DBCON, HTTP/SOAP — records that Coupa arrives as a FILE processed by a job, and
that TULIP and UNESDIR come over a direct database connection and fail 93% of the time. All
of it in tables. The consequence: `interface_boundary.json` contained the word "channel"
ZERO times, and a new algorithm was about to re-derive the entire taxonomy from the audit
log while the answer sat in a document nobody could query.

**The check.** A markdown table with several data rows and a column that names a CATEGORY is
a classification. If no tool in the repository reads that file, the classification is
trapped: it exists, and the machine cannot use it.

**What it does not claim.** Not every table should become a store — a table of examples, or
one illustrating a narrative, is doing its job as prose. So a document can declare itself
narrative with the marker `<!-- narrative-only -->`, and the point of the audit is that the
choice becomes DELIBERATE rather than accidental.

Run: python brain_v2/methods/audit_prose_classifications.py     (reports, never blocks)
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE = REPO / "knowledge"
BRAIN = REPO / "brain_v2"
CODE_DIRS = ["brain_v2", "process_mining", "scripts", "Zagentexecution"]
OUT = REPO / "brain_v2" / "methods" / "prose_classifications.json"

MIN_ROWS = 4
# a column heading that names a category rather than a measurement
CATEGORY_COLUMN = re.compile(
    r"\b(channel|type|kind|category|status|classification|direction|tier|source|"
    r"system|module|domain|owner|method|mechanism)\b", re.I)
NARRATIVE = "<!-- narrative-only -->"

# HISTORICAL RECORDS are narrative by nature and must not inflate the worklist. A session
# retro is a record of what happened on one day; a plan is what someone intended. Neither is
# a live classification the algorithms should be querying, and counting them made the first
# run report 87 "trapped" documents — a number that is technically derived and practically
# useless, which is its own kind of wrong answer.
HISTORICAL = ("session_plans/", "session_retros/", "/incidents/", "pmo_tracker",
              "_retro", "_plan", "adoption_backlog", "brain_coverage_audit")


def _readers():
    """Every knowledge file that some tool actually opens."""
    read = set()
    for d in CODE_DIRS:
        root = REPO / d
        if not root.exists():
            continue
        for py in root.rglob("*.py"):
            try:
                txt = py.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in re.finditer(r'["\']([^"\']*\.md)["\']', txt):
                read.add(Path(m.group(1)).name)
            # paths built from parts, e.g. "Integration" / "integration_map_complete.md"
            for m in re.finditer(r'/\s*["\']([\w.\-]+\.md)["\']', txt):
                read.add(m.group(1))
    return read


def _tables(text):
    """(heading_cells, data_row_count) for every markdown table in the document."""
    out, head, rows = [], None, 0
    for ln in text.splitlines():
        st = ln.strip()
        if st.startswith("|") and st.count("|") >= 3:
            cells = [c.strip() for c in st.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):        # the separator row
                continue
            if head is None:
                head = cells
            else:
                rows += 1
        else:
            if head is not None:
                out.append((head, rows))
            head, rows = None, 0
    if head is not None:
        out.append((head, rows))
    return out


def _numbers_in_prose():
    """MEASUREMENTS buried inside a text field of a JSON store.

    FIXED (s098) — it returned 0 because the NUM pattern below had been saved with three
    literal U+0008 BACKSPACE control characters at the three places a backslash-b word
    boundary was meant, so the compiled regex required a backspace character beside every
    figure and matched nothing in any store; retyping the line outside the module produced a
    real two-character escape, which is why "the same regex" worked there. Control characters
    are invisible in an editor and in a diff — when a regex matches NOTHING ANYWHERE, hexdump
    the pattern before doubting the traversal.

    A different failure from the markdown one, and easier to miss because the file LOOKS
    structured. A record whose 'finding' field reads '3,230,958 calls, ONE identity, 100%
    itself' is prose wearing a schema: nothing can ask which accounts went opaque this month,
    or whether a satellite started carrying its caller, because the numbers are inside a
    sentence.

    I committed exactly this an hour after writing the rule against it, which is why this
    check exists rather than a reminder.

    Heuristic: a long string field carrying three or more separate figures is almost always a
    measurement that should have been a list of records. Reported, never auto-fixed — some
    narrative legitimately cites numbers, and a checker that rewrites prose would destroy the
    reasoning the numbers came from.
    """
    NUM = re.compile(r"\b\d[\d,\.]{3,}\b|\b\d+%")
    SKIP = ("_why", "_design", "_concept", "_one_line", "why", "how_to_apply", "rule",
            "_means", "consequence", "_note", "note", "resolution_notes", "claim")
    out = []
    for f in sorted((BRAIN).rglob("*.json")):
        if "output" in str(f) or "brain_state" in f.name:
            continue
        try:
            blob = json.load(open(f, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        stack = [("", blob)]
        while stack:
            path, node = stack.pop()
            if isinstance(node, dict):
                for k, v in node.items():
                    stack.append((f"{path}/{k}", v))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    stack.append((f"{path}[{i}]", v))
            elif isinstance(node, str) and len(node) > 120:
                key = path.rsplit("/", 1)[-1]
                if key in SKIP or key.startswith("_"):
                    continue
                # A bare year is not a measurement. Without this, "2024, 2025, 2026" in a
                # sentence counts as three figures and the worklist fills with narrative —
                # 312 hits of which a large share were calendar years. A checker whose list
                # is mostly noise gets ignored, which costs more than the defect it finds.
                hits = [h for h in NUM.findall(node)
                        if not (h.isdigit() and 1990 <= int(h) <= 2099)]
                if len(hits) >= 3:
                    out.append({"store": str(f.relative_to(BRAIN.parent)).replace("\\", "/"),
                                "field": path, "figures": hits[:6],
                                "_why": ("three or more figures in one text field — this is a "
                                         "measurement that should be records")})
    return out


def main():
    readers = _readers()
    trapped, narrative, structured = [], [], []

    for md in sorted(KNOWLEDGE.rglob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        rel = str(md.relative_to(REPO)).replace("\\", "/")
        classifications = [(h, n) for h, n in _tables(text)
                           if n >= MIN_ROWS and any(CATEGORY_COLUMN.search(c) for c in h)]
        if not classifications:
            continue
        if any(h in rel for h in HISTORICAL) or NARRATIVE in text:
            narrative.append(rel)
        elif md.name in readers:
            structured.append(rel)
        else:
            trapped.append({
                "doc": rel,
                "classification_tables": len(classifications),
                "rows": sum(n for _h, n in classifications),
                "category_columns": sorted({c for h, _n in classifications for c in h
                                            if CATEGORY_COLUMN.search(c)})[:6],
            })

    trapped.sort(key=lambda x: -x["rows"])
    nip = _numbers_in_prose()
    json.dump({
        "_generated_by": "brain_v2/methods/audit_prose_classifications.py",
        "_question": "which analysis is trapped in prose, where no algorithm can reach it?",
        "_why": ("a classification only a human can read gets RE-DERIVED by the next "
                 "question, and the two answers drift with nothing able to notice. The "
                 "integration map classified 48 flows into 8 channels and F1 carried no "
                 "channel at all."),
        "_how_to_clear_one": ("either write a small parser that lifts the table into a store "
                              "the algorithms query — brain_v2/build_channel_registry.py is "
                              f"the worked example — or mark the document `{NARRATIVE}` when "
                              "the table is genuinely illustrative. The point is that the "
                              "choice becomes deliberate."),
        "counts": {"trapped": len(trapped), "structured": len(structured),
                   "declared_narrative": len(narrative)},
        "trapped": trapped,
        "already_structured": structured,
        "declared_narrative": narrative,
        "numbers_buried_in_prose": nip,
        "_second_kind_of_trap": (
            "a MEASUREMENT inside a text field of a JSON store is prose wearing a schema. The "
            "file looks structured, so it passes every eye — but nothing can ask which "
            "accounts went opaque this month when the numbers are inside a sentence."),
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"\n[numbers buried in prose] {len(nip)} text field(s) carrying measurements")
    for x in nip[:8]:
        print(f"    {x['store']}{x['field']}")
        print(f"      figures: {', '.join(x['figures'])}")

    print(f"[prose classifications] {len(trapped)} trapped in the LIVE reference · "
          f"{len(structured)} structured · {len(narrative)} historical or declared narrative")
    for t in trapped[:12]:
        print(f"    {t['rows']:>4} rows  {t['doc']}")
        print(f"              category columns: {', '.join(t['category_columns'][:4])}")
    if not trapped:
        print("  OK — every classification a document makes is reachable by a tool")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
