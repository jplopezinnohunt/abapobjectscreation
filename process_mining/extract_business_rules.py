"""extract_business_rules.py — ALGORITHM A9: the rules that live in code, not in config.

**The decisions that govern a process are frequently not in customizing.** They sit in a
custom BAdI implementation as a hard-coded constant, a branch condition, or a comment
stating an intent that no table records. A config-frontier analysis cannot see any of them,
which is why a domain can look fully configured and still behave in a way nobody documented.

The case that produced this, read from PRODUCTION source (`ZCL_IM__UNESCO_ENCUMB`, the
encumbrance calculation behind the largest write path in the tenant):

    "until a configuration for the enddate determination rules
    "is available, use hard-coded values
    ********Quasi-config *****************************
    *{   REPLACE        D01K9B04Y9
    *\      mv_extension_years = 1.
          MV_EXTENSION_YEARS = 10.
    *}   REPLACE

A business rule — how far into the future a temporary position is financed — living as a
constant, changed from 1 to 10 by a named transport, with the reasoning in a comment. No
configuration analysis finds that. **Neither does reading the class signature.**

So this extracts six things every ABAP codebase carries, none SAP-version-specific:

    QUASI_CONFIG    a literal the author FLAGGED as standing in for missing configuration
    HARD_CONSTANT   a literal assigned to a member/constant — a threshold, limit or key
    INTENT          a comment stating a requirement ("requires", "must", "only", "never")
    MODIFICATION    a `*{ REPLACE <transport>` block: what changed, and under which transport
    OVERRIDE        which STANDARD interface or BAdI this code takes over
    LEFTOVER        debug and prototype artifacts still in production

**Why LEFTOVER is not pedantry.** The same production class carries `BREAK-POINT ID
Z_ENCUMB_PROTO` and a method commented `"prototype`. A checkpoint group in the code that
computes commitments is a live switch, and the word prototype on the largest write path in
the installation is a fact about the system, not a style complaint.

**What it cannot do.** It reads text. A branch it does not recognise is silently not
reported, so absence here is never evidence — the output names what it FOUND, and the file
line count tells a reader how much went unexamined. Confirm every rule against the source
before acting on it; the line reference is emitted for exactly that.

Emits: brain_v2/business_rules.json
Run:   python process_mining/extract_business_rules.py [CORPUS_DIR]
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = REPO / "extracted_sap_p01"
OUT = REPO / "brain_v2" / "business_rules.json"

# a literal assigned to a member, global or constant — thresholds, limits, magic keys
ASSIGN = re.compile(r"^\s*(?:CONSTANTS\s+)?([MGC][VSTO]?_[A-Z0-9_]{2,}|[A-Z][A-Z0-9_]{3,})\s*"
                    r"(?:TYPE\s+\S+\s+VALUE|=)\s*('[^']*'|\d+)\s*\.", re.I)
COMMENT = re.compile(r"^\s*[*\"](.*)$")
# SAP's modification assistant: *{ REPLACE <transport> ... *}
MOD_OPEN = re.compile(r"^\*\{\s+(\w+)\s+(\S+)")
# a BAdI or interface method implementation: METHOD IF_EX_X~Y or ZIF_X~Y
OVERRIDE = re.compile(r"^\s*METHOD\s+((?:IF_EX_|CL_|IF_)[A-Z0-9_]+)~([A-Z0-9_]+)", re.I)
LEFTOVER = re.compile(r"\b(BREAK-POINT|BREAK\s+\w+|prototype|TODO|FIXME|XXX|hard.?coded|"
                      r"WRITE\s*:?\s*/)", re.I)
# a comment that states a REQUIREMENT rather than describing mechanics
INTENT_WORDS = re.compile(r"\b(requires?|must|only|never|always|should|shall|not allowed|"
                          r"as per|change request|business)\b", re.I)


def scan(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    found = {"quasi_config": [], "hard_constant": [], "intent": [], "modification": [],
             "override": [], "leftover": []}
    recent = []          # rolling comment context, so a constant carries its reasoning
    in_mod = None
    for i, ln in enumerate(lines, 1):
        m = MOD_OPEN.match(ln)
        if m:
            in_mod = {"line": i, "kind": m.group(1), "transport": m.group(2), "replaced": [],
                      "_why": ("SAP's modification assistant records WHO changed a delivered "
                               "or protected line and under which transport — the old line is "
                               "kept commented, so the DELTA is readable")}
            continue
        if in_mod is not None:
            if ln.startswith("*}"):
                found["modification"].append(in_mod)
                in_mod = None
            elif ln.startswith("*\\"):
                in_mod["replaced"].append(ln[2:].strip())
            elif ln.strip():
                in_mod.setdefault("new", []).append(ln.strip())
            continue

        c = COMMENT.match(ln)
        if c:
            txt = c.group(1).strip()
            if txt:
                recent.append(txt)
                recent[:] = recent[-6:]
            if re.search(r"quasi.?config|hard.?coded|until a config|no config", txt, re.I):
                found["quasi_config"].append({
                    "line": i, "comment": txt[:200],
                    "_why": ("the author is saying the DECISION HAS NO CONFIGURATION. It is a "
                             "business rule frozen in code, and only a code read finds it")})
            if INTENT_WORDS.search(txt) and len(txt) > 25:
                found["intent"].append({"line": i, "states": txt[:240]})
            continue

        a = ASSIGN.match(ln)
        if a and not ln.strip().startswith(("DATA", "TYPES", "FIELD-SYMBOLS")):
            found["hard_constant"].append({
                "line": i, "name": a.group(1), "value": a.group(2).strip("'"),
                "reasoning": " | ".join(recent[-4:])[:400] or None})
        o = OVERRIDE.match(ln)
        if o:
            found["override"].append({"line": i, "interface": o.group(1),
                                      "method": o.group(2),
                                      "_why": "this code REPLACES standard behaviour"})
        lo = LEFTOVER.search(ln)
        if lo and not ln.strip().startswith(("*", '"')):
            found["leftover"].append({"line": i, "what": lo.group(1),
                                      "code": ln.strip()[:120]})
        if ln.strip() and not ln.strip().startswith(("*", '"')):
            recent.clear()
    return found, len(lines)


def main():
    corpus = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CORPUS
    files = sorted(corpus.rglob("*.abap"))
    if not files:
        print(f"no source under {corpus}", file=sys.stderr)
        return 1

    objects, totals = {}, {k: 0 for k in
                           ("quasi_config", "hard_constant", "intent", "modification",
                            "override", "leftover")}
    for f in files:
        found, n = scan(f)
        if not any(found.values()):
            continue
        objects[f.stem] = {"source": str(f.relative_to(REPO)).replace("\\", "/"),
                           "lines": n, **found}
        for k in totals:
            totals[k] += len(found[k])

    json.dump({
        "_generated_by": "process_mining/extract_business_rules.py",
        "_algorithm": "A9 — business rules that live in code, not in configuration",
        "_why": ("the decisions governing a process are frequently NOT in customizing. They "
                 "are hard-coded constants, branch conditions and comments stating intent. A "
                 "config-frontier analysis cannot see any of them, so a domain can look fully "
                 "configured and still behave in a way nobody documented."),
        "_read_from": ("PRODUCTION source. D01 answers what was built; only P01 answers what "
                       "is valid — see feedback_code_d01_to_develop_p01_to_evaluate"),
        "_limits": ("this reads TEXT. A construct it does not recognise is simply not "
                    "reported, so ABSENCE HERE IS NEVER EVIDENCE. Every finding carries its "
                    "line so it can be confirmed against the source before anyone acts on it."),
        "corpus": str(corpus.relative_to(REPO)).replace("\\", "/"),
        "files_scanned": len(files), "objects_with_findings": len(objects),
        "totals": totals, "objects": objects,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[business rules] {len(files)} source files, {len(objects)} with findings")
    for k, v in totals.items():
        print(f"    {k:16s} {v}")
    print(f"wrote {OUT}")

    # the two that change what a reader believes, surfaced by default
    for name, o in objects.items():
        for q in o["quasi_config"]:
            print(f"\n  QUASI-CONFIG  {name}:{q['line']}\n    {q['comment']}")
        for m in o["modification"]:
            if m.get("replaced"):
                print(f"\n  MODIFIED under {m['transport']}  {name}:{m['line']}")
                print(f"    was: {' / '.join(m['replaced'])[:110]}")
                print(f"    now: {' / '.join(m.get('new', []))[:110]}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
