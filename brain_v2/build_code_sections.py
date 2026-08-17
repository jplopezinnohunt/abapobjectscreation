"""Code sections — the ROUTINE is the unit of knowledge, not the file.

WHY (s099, JP)
--------------
Mapping objects says almost nothing. `YRGGBS00` is ONE object, 1,593 lines, and it
holds ~69 independent business rules: UAEP forces asset fund mapping, UATF clears the
WBS element, U904 maps payment supplement to segment, U915 forces bank disambiguation,
U917 blocks a posting when the purpose code is missing, UXR1/UXR2/UZLS tag the office
and route the payment. Different triggers, different domains, different owners — inside
one file. "Which domain is YRGGBS00?" is the wrong question. "What does line 1547 do,
when does it fire, and who does it serve?" is the right one.

The existing parsers/abap_parser.py works at FILE level (SELECTs, CALL FUNCTIONs for a
whole file). This module adds the level below it: routine boundaries with line ranges,
and for each routine what it reads, what it writes, how it decides, and what it is for.

WHAT IT EXTRACTS PER ROUTINE
----------------------------
  name, kind (FORM/METHOD/FUNCTION/MODULE), start_line..end_line, loc
  header_comment   the ABAP comment block directly above it — usually the author's
                   own statement of intent ("Check SCB indicator is filled for some
                   bank countries")
  guards           CHECK / IF-return conditions = WHEN this routine declines to act
  reads/writes     tables touched, and the DDIC fields it assigns
  calls            function modules and PERFORMs
  messages         MESSAGE eNNN(id) — a hard error means it can stop a posting
  role             VALIDATION | SUBSTITUTION | DERIVATION | READ | HELPER, inferred
                   from what it does with its result, not from its name
  registered_as    for exit form pools, the `exits-name = 'U917'` registration that
                   wires the routine into GGB0/GGB1

Output: brain_v2/code_sections.json, indexed by object and by routine name.
Run standalone or via rebuild_all.py (Step 0g).
"""

from __future__ import annotations

import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
BRAIN = REPO / "brain_v2"
INVENTORY = BRAIN / "code_inventory.json"
OUT = BRAIN / "code_sections.json"

OPEN_RE = re.compile(
    r"^\s*(?P<kind>form|method|function|module)\s+(?P<name>[\w/~=<>-]+)", re.I)
CLOSE_RE = re.compile(r"^\s*end(form|method|function|module)\s*[\.\s]", re.I)

RE_SELECT = re.compile(r"\bselect\b(?:\s+single)?(?:.*?)\bfrom\s+@?([\w/]+)", re.I | re.S)
RE_WRITE_TAB = re.compile(
    r"\b(?:update|insert|modify|delete)\s+(?:from\s+)?([a-z][\w/]{2,})", re.I)
RE_CALL_FM = re.compile(r"call\s+function\s+'([^']+)'", re.I)
RE_PERFORM = re.compile(r"\bperform\s+([\w/]+)", re.I)
RE_MESSAGE = re.compile(r"\bmessage\s+([aeiswx])(\d+)\(([\w/]+)\)", re.I)
RE_MSG_TYPE = re.compile(r"\bmessage\b.*?\btype\s+'([AEIWSX])'", re.I | re.S)
RE_CHECK = re.compile(r"^\s*check\s+(.+?)\.\s*$", re.I)
RE_FIELD_ASSIGN = re.compile(r"\b([a-z]\w{1,9})-(\w+)\s*=", re.I)
RE_RESULT_FALSE = re.compile(r"\b\w*result\w*\s*=\s*(b_false|abap_false|space|'\s*')", re.I)
RE_RESULT_TRUE = re.compile(r"\b\w*result\w*\s*=\s*(b_true|abap_true|'X')", re.I)
RE_EXITS_NAME = re.compile(r"exits-name\s*=\s*'([^']+)'", re.I)
RE_RAISE = re.compile(r"^\s*raise\s+(\w+)", re.I | re.M)

# Table-ish names we never want to record as a table.
NOT_A_TABLE = {"screen", "sy", "space", "abap", "table", "itab", "lt", "ls", "gt", "gs",
               "memory", "dynpro", "report", "dataset", "shared", "database"}


def decode(path: Path):
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        enc = "utf-16"
    elif raw[:3] == b"\xef\xbb\xbf":
        enc = "utf-8-sig"
    else:
        enc = "utf-8"
    return raw.decode(enc, errors="replace")


def strip_comment(line: str) -> str:
    """ABAP: '*' in column 1 comments the whole line; '"' comments to end of line."""
    if line[:1] == "*":
        return ""
    out, in_str = [], False
    for ch in line:
        if ch == "'":
            in_str = not in_str
        if ch == '"' and not in_str:
            break
        out.append(ch)
    return "".join(out)


def is_comment(line: str) -> bool:
    s = line.strip()
    return s.startswith("*") or s.startswith('"')


def comment_text(line: str) -> str:
    return line.strip().lstrip("*").lstrip('"').strip(" *-_|")


def header_comment(lines, start_idx):
    """The contiguous comment block immediately above a routine = author's intent."""
    out = []
    i = start_idx - 1
    while i >= 0 and len(out) < 8:
        raw = lines[i]
        if not raw.strip():
            if out:
                break
            i -= 1
            continue
        if not is_comment(raw):
            break
        t = comment_text(raw)
        if t and not re.fullmatch(r"[-=*_ ]+", t):
            out.append(t)
        i -= 1
    return " | ".join(reversed(out))[:300]


def classify(body: str, sets_fields, msgs, has_result_false) -> str:
    hard_msg = any(m[0].upper() in ("E", "A", "X") for m in msgs)
    if has_result_false or hard_msg or RE_RAISE.search(body):
        return "VALIDATION"
    if sets_fields:
        return "SUBSTITUTION"
    if RE_SELECT.search(body):
        return "DERIVATION"
    return "HELPER"


def parse_file(path: Path, rel: str):
    try:
        text = decode(path)
    except Exception:
        return [], []
    lines = text.splitlines()
    code = [strip_comment(l) for l in lines]

    registrations = RE_EXITS_NAME.findall(text)

    sections = []
    i = 0
    n = len(lines)
    while i < n:
        m = OPEN_RE.match(code[i])
        if not m:
            i += 1
            continue
        kind = m.group("kind").upper()
        name = m.group("name").rstrip(".").upper()
        # CLASS ... DEFINITION lines also match nothing here; METHOD inside a definition
        # has no body — it closes on the same construct, handled by the scanner below.
        j = i + 1
        depth = 1
        while j < n:
            if OPEN_RE.match(code[j]) and not CLOSE_RE.match(code[j]):
                depth += 1
            elif CLOSE_RE.match(code[j]):
                depth -= 1
                if depth == 0:
                    break
            j += 1
        end = min(j, n - 1)
        body_raw = "\n".join(code[i:end + 1])
        if len(body_raw) < 12:
            i = end + 1
            continue

        tables = {t.upper() for t in RE_SELECT.findall(body_raw)
                  if t.lower() not in NOT_A_TABLE and len(t) > 2}
        writes = {t.upper() for t in RE_WRITE_TAB.findall(body_raw)
                  if t.lower() not in NOT_A_TABLE and len(t) > 2}
        fms = sorted({f.upper() for f in RE_CALL_FM.findall(body_raw)})
        performs = sorted({p.upper() for p in RE_PERFORM.findall(body_raw)})
        msgs = [(t, num, cls) for t, num, cls in RE_MESSAGE.findall(body_raw)]
        for t in RE_MSG_TYPE.findall(body_raw):
            msgs.append((t, "", ""))
        guards = [g.strip()[:120] for g in
                  (RE_CHECK.match(strip_comment(l)) and
                   RE_CHECK.match(strip_comment(l)).group(1) or "" for l in lines[i:end + 1])
                  if g]
        set_fields = sorted({f"{a.upper()}-{b.upper()}" for a, b in
                             RE_FIELD_ASSIGN.findall(body_raw)
                             if a.lower() not in ("sy", "ls", "lt", "gs", "gt", "wa")})[:12]
        has_false = bool(RE_RESULT_FALSE.search(body_raw))

        sections.append({
            "object_file": rel,
            "routine": name,
            "kind": kind,
            "start_line": i + 1,
            "end_line": end + 1,
            "loc": end - i + 1,
            "header_comment": header_comment(lines, i),
            "role": classify(body_raw, set_fields, msgs, has_false),
            "guards": guards[:8],
            "reads_tables": sorted(tables)[:15],
            "writes_tables": sorted(writes)[:10],
            "sets_fields": set_fields,
            "calls_fms": fms[:15],
            "performs": performs[:15],
            "messages": [f"{t.upper()}{num}({cls})" if num else f"TYPE {t.upper()}"
                         for t, num, cls in msgs][:8],
            "can_block_posting": bool(has_false or
                                      any(t.upper() in ("E", "A", "X") for t, _, _ in msgs)),
            "registered_as_exit": name if name in {r.upper() for r in registrations} else None,
        })
        i = end + 1
    return sections, registrations


def build():
    if not INVENTORY.exists():
        print("code_inventory.json missing — run build_code_inventory.py first")
        return None
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))

    # parse the PRIMARY source of every object (the real body, not the stub)
    seen_paths = set()
    targets = []
    for name, o in inv["objects"].items():
        p = o["primary_source"]
        if p in seen_paths:
            continue
        seen_paths.add(p)
        targets.append((name, p, o))

    print(f"parsing {len(targets)} primary sources...")
    all_sections = []
    per_object = {}
    parsed = 0
    for name, rel, o in targets:
        fp = REPO / rel
        if not fp.exists():
            continue
        secs, _ = parse_file(fp, rel)
        if not secs:
            continue
        parsed += 1
        doms = [d["domain"] for d in o.get("domains", [])]
        procs = o.get("processes", [])
        for s in secs:
            s["object"] = name
            s["domains"] = doms
            s["processes"] = procs
        per_object[name] = {
            "object": name,
            "source": rel,
            "lines": o.get("lines"),
            "domains": doms,
            "processes": procs,
            "section_count": len(secs),
            "roles": dict(sorted(
                {r: sum(1 for x in secs if x["role"] == r)
                 for r in {x["role"] for x in secs}}.items())),
            "blocking_sections": [s["routine"] for s in secs if s["can_block_posting"]],
            "sections": secs,
        }
        all_sections.extend(secs)

    by_routine = defaultdict(list)
    for s in all_sections:
        by_routine[s["routine"]].append(
            {"object": s["object"], "source": s["object_file"],
             "lines": f'{s["start_line"]}-{s["end_line"]}', "role": s["role"]})

    roles = defaultdict(int)
    for s in all_sections:
        roles[s["role"]] += 1

    out = {
        "_meta": {
            "built_by": "brain_v2/build_code_sections.py",
            "why": "a routine is the unit of behaviour; one object holds many rules",
            "objects_parsed": parsed,
            "sections": len(all_sections),
        },
        "_roles": dict(sorted(roles.items(), key=lambda x: -x[1])),
        "_blocking_count": sum(1 for s in all_sections if s["can_block_posting"]),
        "objects": per_object,
        "by_routine": {k: v for k, v in sorted(by_routine.items()) if v},
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(f"  objects with sections: {parsed}")
    print(f"  sections (routines):   {len(all_sections):,}")
    print(f"  roles: {dict(sorted(roles.items(), key=lambda x: -x[1]))}")
    print(f"  sections that can BLOCK a posting: {out['_blocking_count']}")
    return out


if __name__ == "__main__":
    build()
