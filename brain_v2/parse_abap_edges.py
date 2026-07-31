"""parse_abap_edges.py — C3: code edges from the ABAP source we already hold (s097).

C3 was the weakest algorithm in the catalogue and its number was misleading in the way this
project keeps rediscovering: "98 of 1,212 objects have code edges" measured the WRONG
POPULATION. A table does not read tables. A GL account does not call function modules. A
synthesised concept is not code.

Against the population that CAN have edges:

    code objects        245
    with edges           86   (ABAP_REPORT 64%, ABAP_CLASS 78%)
    without edges       159
        source on disk    25   <- a PARSER gap, fixable now
        no source        134   <- an EXTRACTION gap, needs ADT

Two different problems wearing one number. This closes the first.

**Why the edges matter more than their percentage.** With thin edge coverage, an impact
question — "what breaks if I change this table?" — answers *nothing depends on it*, which
is the most dangerous false negative the model can produce. It is also the strongest signal
for deriving a custom object's domain, which is the portability blocker.

**Deliberately conservative.** ABAP has many ways to touch a table; this recognises the
common, unambiguous ones and skips the rest. An edge we are unsure of is worse than a
missing edge: a wrong dependency sends someone to change the wrong thing.
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "brain_v2" / "brain_state.json"
SOURCE_DIRS = ["extracted_code", "extracted_sap"]
OUT = REPO / "brain_v2" / "parsed_edges.json"

CODE_TYPES = {"ABAP_REPORT", "ABAP_CLASS", "PROGRAM_OR_CUSTOM", "FUNCTION_MODULE",
              "CODE_OBJECT", "ABAP_INCLUDE", "FUNCTION_GROUP"}

# Read patterns. FROM/INTO TABLE forms are unambiguous; dynamic ones are skipped on purpose.
READ = [
    re.compile(r"\bSELECT\b.*?\bFROM\s+([A-Z_][A-Z0-9_/]{2,})", re.I | re.S),
    re.compile(r"\bREAD\s+TABLE\s+([A-Z_][A-Z0-9_/]{2,})", re.I),
]
WRITE = [
    re.compile(r"\b(?:INSERT|UPDATE|MODIFY|DELETE)\s+(?:FROM\s+)?([A-Z_][A-Z0-9_/]{2,})", re.I),
]
CALL = [
    re.compile(r"CALL\s+FUNCTION\s+'([A-Z0-9_/]+)'", re.I),
    re.compile(r"CALL\s+METHOD\s+([A-Z0-9_/=>]+)", re.I),
]

# ABAP keywords that follow the same grammar as a table name and are not tables.
NOT_A_TABLE = {
    "TABLE", "ITAB", "LT", "LS", "GT", "GS", "SCREEN", "SY", "SPACE", "INITIAL",
    "MEMORY", "ID", "SET", "GET", "DATA", "TYPE", "LIKE", "INTO", "WHERE", "AND",
    "OR", "NOT", "SINGLE", "CORRESPONDING", "FIELDS", "REPORT", "FORM", "ENDFORM",
    "LOOP", "ENDLOOP", "IF", "ENDIF", "TRANSPORTING", "COMPARING", "ASSIGNING",
    "REFERENCE", "STANDARD", "SORTED", "HASHED", "INDEX", "KEY", "BINARY", "SEARCH",
}


def index_source():
    idx = {}
    for d in SOURCE_DIRS:
        base = REPO / d
        if not base.exists():
            continue
        for root, _, files in os.walk(base):
            for f in files:
                if f.lower().endswith((".abap", ".txt", ".src", ".md")) or "." not in f:
                    idx.setdefault(os.path.splitext(f)[0].upper(), Path(root) / f)
    return idx


def clean(tokens):
    out = set()
    for t in tokens:
        t = t.strip().upper().rstrip(".,")
        if (len(t) < 3 or t in NOT_A_TABLE or t.startswith(("LT_", "LS_", "GT_", "GS_",
                                                            "IT_", "ET_", "IS_", "ES_"))):
            continue
        out.add(t)
    return sorted(out)


def main():
    state = json.load(open(STATE, encoding="utf-8"))
    objects = state.get("objects", {})
    idx = index_source()

    targets = [k for k, v in objects.items()
               if v.get("type") in CODE_TYPES
               and not (v.get("reads_tables") or v.get("calls_fms") or v.get("writes_tables"))
               and k.upper() in idx]

    parsed, results = 0, {}
    for name in targets:
        try:
            src = idx[name.upper()].read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # strip full-line comments so a commented-out SELECT never becomes a dependency
        src = "\n".join(l for l in src.split("\n") if not l.lstrip().startswith("*"))

        reads = clean(m for p in READ for m in p.findall(src))
        writes = clean(m for p in WRITE for m in p.findall(src))
        calls = clean(m for p in CALL for m in p.findall(src))
        if not (reads or writes or calls):
            continue
        parsed += 1
        results[name] = {"reads_tables": reads[:40], "writes_tables": writes[:20],
                         "calls_fms": calls[:40],
                         "source": str(idx[name.upper()].relative_to(REPO)).replace("\\", "/")}

    out = {
        "_generated_by": "brain_v2/parse_abap_edges.py",
        "_algorithm": "C3 — static edge extraction",
        "_denominator_note": ("'98 of 1,212 objects' measured the wrong population: tables, "
                              "GL accounts, variants and synthesised concepts cannot have code "
                              "edges. Against CODE objects the figure was 86/245, and the gap "
                              "splits into a parser gap (25, closed here) and an extraction "
                              "gap (134, needs ADT)."),
        "_conservative": ("ABAP has many ways to touch a table; this recognises the common "
                          "unambiguous forms and skips dynamic ones. An edge we are unsure of "
                          "is worse than a missing edge: a wrong dependency sends someone to "
                          "change the wrong thing."),
        "candidates": len(targets), "parsed": parsed, "objects": results,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    # MERGE into brain_state. Parsing without merging leaves the edges in a side file
    # that nothing reads — the same "produces an artifact nobody consumes" failure the
    # asset gate exists to catch.
    merged = 0
    for name, r in results.items():
        o = objects.get(name)
        if not o:
            continue
        for key in ("reads_tables", "writes_tables", "calls_fms"):
            if r[key] and not o.get(key):
                o[key] = r[key]
                o.setdefault("_edge_source", "parsed from extracted source, s097")
                merged += 1
    if merged:
        STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"wrote {OUT}")
    print(f"  merged {merged} edge set(s) into brain_state")
    print(f"  {len(targets)} code objects had source and no edges · {parsed} yielded edges")
    for n, r in list(results.items())[:8]:
        print(f"    {n:34s} reads={len(r['reads_tables']):>2} writes={len(r['writes_tables']):>2} "
              f"calls={len(r['calls_fms']):>2}")
    if parsed < len(targets):
        print(f"  {len(targets)-parsed} produced nothing — likely includes or non-ABAP content")


if __name__ == "__main__":
    main()
