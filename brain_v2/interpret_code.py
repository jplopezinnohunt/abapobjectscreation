"""Brain-informed code interpretation — read the code THROUGH what we already know.

WHY (s099, JP)
--------------
Parsing code syntactically tells you `SELECT ... FROM lfbk` and `bseg-lzbkz`. That is not
understanding. Understanding is knowing that at UNESCO `LZBKZ` is the German SCB indicator
REPURPOSED as the payment purpose code, that `LFBK-BANKS` is the field that decides whether
that code is mandatory, that `USR05-Y_USERFO` carries an office code that also routes the
payment method, and that `GSBER` has exactly four legal values in company code UNES. None of
that is in the source. All of it is already in the brain, written down by earlier analyses.

So any reading of code that does not consult the brain is a weak reading — it re-derives
what was already paid for, and it cannot relate the routine it is looking at to the incident,
claim or domain that explains it.

THE ALGORITHM
-------------
For every routine (from code_sections.json):

  1. HARVEST identifiers  — tables, DDIC fields, called FMs, PERFORMs, message classes and
                            the literals appearing in its guards.
  2. RESOLVE each one against the brain:
       - claims / annotations / incidents whose text or related_objects mention it
       - the gold table registry (table -> domain)
       - other objects that read the same table (co-readers = who else cares)
     Each resolution keeps its SOURCE so the interpretation stays auditable (CP-003).
  3. INTERPRET  — assemble a statement in UNESCO terms: what this routine decides, on which
                  business concept, under which conditions, and what it can stop.
  4. SCORE      — explained = identifiers the brain could explain / identifiers found.
                  This is the honest measure of how much of our own code we understand.
  5. GAP        — every unexplained identifier becomes a concrete extraction/analysis task,
                  named, not a vague "improve coverage".
  6. CONFLICT   — a claim that names this object but whose asserted terms do NOT appear in
                  its code is surfaced for review. This is the check that would have caught
                  both claim 116 (control "does not exist" — it is at line 1547) and the
                  EXO// note-to-payee story (asserted by a spec, absent from the source).

Output: brain_v2/code_interpretation.json
Run standalone or via rebuild_all.py (Step 0h — after sections, which it consumes).
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
OUT = BRAIN / "code_interpretation.json"

# An SAP identifier worth resolving: TABLE-FIELD, or a table/object-ish token.
RE_TERM = re.compile(r"\b([A-Z][A-Z0-9_/]{2,})(?:-([A-Z0-9_]{2,}))?\b")

# Local ABAP variables carry no business meaning and pollute both the resolution and the
# gap list. LV_BANKS matched a claim purely because that claim's prose quotes the routine.
RE_LOCAL = re.compile(r"^(LV|LS|LT|LR|LO|GV|GS|GT|GR|GO|W|L|P|E|I|C|R|X|Y|Z)_", re.I)

# Words that look like identifiers but carry no business meaning.
NOISE = {
    "SELECT", "SINGLE", "FROM", "WHERE", "INTO", "TABLE", "DATA", "TYPE", "LIKE", "VALUE",
    "CHECK", "CLEAR", "MOVE", "LOOP", "ENDLOOP", "FORM", "ENDFORM", "METHOD", "ENDMETHOD",
    "AND", "OR", "NOT", "INITIAL", "SPACE", "ABAP_TRUE", "ABAP_FALSE", "SY", "SUBRC",
    "IMPORTING", "EXPORTING", "CHANGING", "USING", "TABLES", "STRUCTURE", "REFERENCE",
    "IF", "ELSE", "ENDIF", "CASE", "WHEN", "ENDCASE", "APPEND", "MODIFY", "TRANSPORTING",
    "CONCATENATE", "WRITE", "MESSAGE", "RAISE", "EXIT", "RETURN", "PERFORM", "CALL",
    "FUNCTION", "ENDFUNCTION", "TRUE", "FALSE", "NULL", "THE", "AND", "FOR", "WITH",
}


def load(rel):
    p = REPO / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


# ------------------------------------------------------------------ brain term index

def build_term_index():
    """term -> [{kind, id, text, domain}]  — everything the brain can explain."""
    idx = defaultdict(list)

    def index_record(kind, ident, text, domain, related):
        base = {"kind": kind, "id": ident, "text": (text or "")[:300], "domain": domain}
        seen = set()
        # DIRECT: the record explicitly declares this object as related. Strongest.
        for obj in (related or []):
            if isinstance(obj, str):
                t = obj.upper().strip()
                if t and t not in NOISE and len(t) >= 3 and t not in seen:
                    seen.add(t)
                    idx[t].append({**base, "direct": True})
        # PROSE: merely mentioned in the text. Weaker — a claim that quotes a routine's own
        # local variable would otherwise outrank a record that actually describes the field.
        for m in RE_TERM.finditer((text or "").upper()):
            tab, fld = m.group(1), m.group(2)
            for t in filter(None, (f"{tab}-{fld}" if fld else None, tab)):
                if t in NOISE or len(t) < 3 or t in seen or RE_LOCAL.match(t):
                    continue
                seen.add(t)
                idx[t].append({**base, "direct": False})

    claims = load("brain_v2/claims/claims.json") or []
    for c in claims:
        if not isinstance(c, dict):
            continue
        status = c.get("status")
        index_record("claim" if status != "superseded" else "claim(superseded)",
                     c.get("id"), c.get("claim"), c.get("domain"),
                     c.get("related_objects"))

    incs = load("brain_v2/incidents/incidents.json") or []
    for i in incs:
        if isinstance(i, dict):
            index_record("incident", i.get("id"),
                         f'{i.get("title","")} — {i.get("root_cause_summary","")}',
                         i.get("domain"), i.get("related_objects"))

    anns = load("brain_v2/annotations/annotations.json")
    if isinstance(anns, dict):
        anns = anns.get("annotations") or []
    for a in (anns or []):
        if isinstance(a, dict):
            index_record("annotation", a.get("object") or a.get("tag"),
                         a.get("finding"), a.get("domain"),
                         [a.get("object")] if a.get("object") else [])

    rules = load("brain_v2/agent_rules/feedback_rules.json") or []
    for r in rules:
        if isinstance(r, dict):
            index_record("rule", r.get("id"), r.get("rule"), None, [])

    return idx


def build_table_domain():
    reg = load("brain_v2/gold_table_registry.json") or {}
    out = {}
    for dom, cats in (reg.get("domains") or {}).items():
        if isinstance(cats, dict):
            for rows in cats.values():
                for x in (rows or []):
                    if isinstance(x, dict) and x.get("gold"):
                        out.setdefault(x["gold"].upper(), dom)
    return out


def build_interface_index():
    """NESTED CALL — C7 consumes F1 (boundary), F2 (satellites) and the execution census.

    Algorithms here are not pure; they call each other as needed (see algorithms.json
    `_nesting`, and satellites.json which declares itself 'F2, nested: F1 boundary ->
    satellite'). C7 was resolving identifiers only against claims and the table registry,
    so every `CALL FUNCTION` came back unexplained — and function modules were the single
    largest bucket of unexplained identifiers. A called FM is not an opaque name: the
    interface layer knows whether it crosses the boundary, the satellite layer knows WHO
    calls it, and the census knows how often and by which account.
    """
    idx = defaultdict(list)

    def add(term, kind, ident, text, domain):
        t = (term or "").upper().strip()
        if t and t not in NOISE and len(t) >= 3:
            idx[t].append({"kind": kind, "id": ident, "text": text[:300],
                           "domain": domain, "direct": True})

    inv = load("brain_v2/interface_inventory.json") or {}
    for r in (inv.get("interfaces") or []):
        art = r.get("artifact")
        ev = r.get("evidence_it_runs")
        add(art, "interface", r.get("channel"),
            f"{r.get('channel')} {r.get('direction')} interface"
            + (f", ours because {r['ours_because']}" if r.get("ours_because") else "")
            + (f", running evidence: {ev}" if ev else
               f", execution UNVERIFIED: {r.get('why_no_evidence', '')[:80]}"),
            "Integration")

    sat = load("brain_v2/satellites.json") or {}
    for s in (sat.get("satellites") or []):
        name = s.get("satellite")
        for fn in (s.get("top_functions") or [])[:40]:
            add(fn.get("fm"), "satellite_call", name,
                f"called by satellite {name} — {fn.get('calls'):,} calls"
                if isinstance(fn.get("calls"), int) else f"called by satellite {name}",
                fn.get("domain") or "Integration")

    cen = load("brain_v2/fm_executed_census.json") or {}
    for bucket, label in (("rfc_bapi_calls", "RFC/BAPI"), ("dialog_tcodes", "dialog"),
                          ("reports", "report"), ("batch_programs", "batch job")):
        for name, meta in (cen.get(bucket) or {}).items():
            if not isinstance(meta, dict):
                continue
            users = ", ".join(meta.get("top_users") or [])[:90]
            add(name, "usage_census", bucket,
                f"executes as {label}: {meta.get('exec_count')} runs, "
                f"{meta.get('distinct_users')} distinct callers ({users})",
                None)

    ch = load("brain_v2/integration_channels.json") or {}
    for c in (ch.get("channels") or []):
        if isinstance(c, dict):
            for a in (c.get("artifacts") or c.get("writers") or []):
                if isinstance(a, str):
                    add(a, "write_channel", c.get("channel") or c.get("name"),
                        f"write channel {c.get('channel') or c.get('name')}", "Integration")

    bnd = load("brain_v2/interface_boundary.json") or {}
    for l in (bnd.get("live") or []):
        if isinstance(l, dict):
            add(l.get("destination") or l.get("rfcdest") or l.get("name"),
                "live_boundary", "F1",
                f"LIVE boundary destination — {l.get('calls', '?')} calls", "Integration")

    return idx


def build_co_readers(sections):
    """table -> objects that read it. 'who else cares about this table'."""
    co = defaultdict(set)
    for obj, o in (sections.get("objects") or {}).items():
        for s in o.get("sections", []):
            for t in s.get("reads_tables", []):
                co[t.upper()].add(obj)
    return co


# ------------------------------------------------------------------ interpretation

# OURS vs SAP STANDARD. A gap list dominated by SAP's own function modules is useless:
# we will never document HR_READ_INFOTYPE or DD_DOMVALUES_GET, and counting them as
# "not understood" hides the gaps that ARE ours to close. Ownership is decided by the
# namespace the object was authored in, the same rule the interface inventory uses
# ("ours is decided by author, never by prefix" applies to interfaces; for code objects
# the Y/Z customer namespace IS the authored-by-us signal).
RE_OURS = re.compile(r"^(Y|Z)[A-Z0-9_]|^/(?!SAP)", re.I)


def is_ours(term, known_universe=None):
    """Ownership is the CUSTOMER NAMESPACE, not 'the brain has seen it'.

    An earlier version also counted anything present in the known universe, which made
    T001P, T005T, HR_READ_INFOTYPE and ADDR_SELECT_ADRC_SINGLE 'ours' — they exist, but
    they are SAP's. That put SAP standard back at the top of the very list built to strip
    it out. UNESCO custom lives in Y*/Z* (the same rule the write-discipline enforces:
    own Z*/Y* objects only, never peer or standard).
    """
    return bool(RE_OURS.match(term.split("-")[0]))


def harvest_terms(sec):
    terms = set()
    for t in sec.get("reads_tables", []) + sec.get("writes_tables", []):
        terms.add(t.upper())
    for f in sec.get("sets_fields", []):
        terms.add(f.upper())
        if "-" in f:
            terms.add(f.split("-")[0].upper())
    for f in sec.get("calls_fms", []) + sec.get("performs", []):
        terms.add(f.upper())
    for g in sec.get("guards", []):
        for m in RE_TERM.finditer(g.upper()):
            tab, fld = m.group(1), m.group(2)
            terms.add(f"{tab}-{fld}" if fld else tab)
    return {t for t in terms
            if t not in NOISE and len(t) >= 3 and not RE_LOCAL.match(t)}


def narrate(sec, meanings, table_domain):
    """One sentence in UNESCO terms — assembled from resolved meaning, not from names."""
    role = sec["role"]
    bits = []
    verb = {"VALIDATION": "decides whether the document may post",
            "SUBSTITUTION": "overwrites document fields before posting",
            "DERIVATION": "derives values by reading configuration",
            "HELPER": "supports other routines"}[role]
    bits.append(f"{sec['routine']} {verb}")

    if sec.get("header_comment"):
        bits.append(f'author states: "{sec["header_comment"]}"')

    concepts = [m for m in meanings if m["explained"]][:3]
    if concepts:
        parts = []
        for m in concepts:
            src = m["sources"][0]
            parts.append(f'{m["term"]} = {src["text"][:110]} [{src["kind"]}:{src["id"]}]')
        bits.append("in UNESCO terms — " + " ; ".join(parts))

    if sec.get("guards"):
        bits.append("acts only when " + " and ".join(sec["guards"][:3]))
    if sec.get("can_block_posting"):
        bits.append("CAN STOP A POSTING")
    doms = sorted({table_domain[t] for t in sec.get("reads_tables", [])
                   if t.upper() in table_domain})
    if doms:
        bits.append("touches " + ", ".join(doms))
    return ". ".join(bits)


def detect_conflicts(obj, sections_of_obj, term_index, known_universe):
    """A claim naming this object whose asserted TECHNICAL terms are absent from its code.

    A term only counts as asserted if it exists in the brain's own universe of objects and
    tables. Without that anchor the detector fired on ordinary English written in caps for
    emphasis — 'EACH', 'EMPTY', 'DOCUMENTED', 'CANONICAL', 'BETWEEN' — and buried the real
    signal under prose. A claim is not contradicted by its own adjectives.
    """
    code_terms = set()
    for s in sections_of_obj:
        code_terms |= harvest_terms(s)
    conflicts = []
    seen = set()
    for t, entries in term_index.items():
        for e in entries:
            if e["kind"] != "claim" or (e["kind"], e["id"]) in seen:
                continue
            txt = (e["text"] or "").upper()
            if obj.upper() not in txt:
                continue
            seen.add((e["kind"], e["id"]))
            asserted = {m.group(1) for m in RE_TERM.finditer(txt)
                        if m.group(1) in known_universe and len(m.group(1)) >= 4}
            asserted -= {obj.upper()}
            # a table/object the claim names but the code never touches
            missing = sorted(a for a in asserted if a not in code_terms)[:6]
            if len(missing) >= 2:
                conflicts.append({
                    "claim": e["id"], "domain": e["domain"],
                    "claim_text": e["text"][:220],
                    "terms_asserted_but_absent_from_code": missing,
                    "note": "REVIEW — the claim names this object and asserts SAP objects or "
                            "tables that do not appear in its source. Either the claim is about "
                            "a different object, the source we hold is incomplete, or the claim "
                            "is wrong.",
                })
    return conflicts[:5]


def build():
    sections = load("brain_v2/code_sections.json")
    if not sections:
        print("code_sections.json missing — run build_code_sections.py first")
        return None
    inventory = load("brain_v2/code_inventory.json") or {"objects": {}}

    print("indexing what the brain already knows...")
    term_index = build_term_index()
    # NEST F1/F2/census into the same resolution surface — a called FM is not opaque.
    for t, entries in build_interface_index().items():
        term_index[t].extend(entries)
    table_domain = build_table_domain()
    co_readers = build_co_readers(sections)

    # The universe of things that ARE SAP objects/tables, used to keep the conflict
    # detector from firing on English prose written in capitals.
    known_universe = set(table_domain)
    known_universe |= {k.upper() for k in (inventory.get("objects") or {})}
    known_universe |= {k.upper() for k in (sections.get("objects") or {})}
    bs = load("brain_v2/brain_state.json") or {}
    known_universe |= {k.upper() for k in (bs.get("objects") or {})}
    for o in (sections.get("objects") or {}).values():
        for sec in o.get("sections", []):
            known_universe |= {t.upper() for t in sec.get("reads_tables", [])}
            known_universe |= {t.upper() for t in sec.get("calls_fms", [])}
    known_universe -= NOISE
    print(f"  {len(term_index)} terms the brain can explain · "
          f"{len(known_universe)} real SAP objects/tables known")

    out_objects = {}
    tot_terms = tot_explained = 0
    tot_ours = tot_ours_explained = 0
    gap_counter = defaultdict(int)
    ours_gap_counter = defaultdict(int)
    all_conflicts = []

    for obj, o in (sections.get("objects") or {}).items():
        inv = (inventory.get("objects") or {}).get(obj, {})
        secs_out = []
        for s in o.get("sections", []):
            terms = harvest_terms(s)
            meanings = []
            for t in sorted(terms):
                # a record that DECLARES the object beats one that merely mentions it,
                # and an active claim beats a superseded one
                entries = sorted(term_index.get(t, []),
                                 key=lambda e: (not e.get("direct"),
                                                "superseded" in (e["kind"] or "")))
                srcs = [{"kind": e["kind"], "id": e["id"], "text": e["text"],
                         "domain": e["domain"], "direct": e.get("direct", False)}
                        for e in entries[:3]]
                explained = bool(srcs) or t in table_domain
                if not explained:
                    gap_counter[t] += 1
                    if is_ours(t, known_universe):
                        ours_gap_counter[t] += 1
                if not srcs and t in table_domain:
                    srcs = [{"kind": "gold_table_registry", "id": t,
                             "text": f"table catalogued under domain {table_domain[t]}",
                             "domain": table_domain[t]}]
                meanings.append({"term": t, "explained": explained, "sources": srcs,
                                 "also_read_by": sorted(co_readers.get(t, set()) - {obj})[:6]})
            n = len(meanings)
            k = sum(1 for m in meanings if m["explained"])
            tot_terms += n
            tot_explained += k
            ours = [m for m in meanings if is_ours(m["term"], known_universe)]
            ours_ok = [m for m in ours if m["explained"]]
            tot_ours += len(ours)
            tot_ours_explained += len(ours_ok)
            secs_out.append({
                "routine": s["routine"],
                "lines": f'{s["start_line"]}-{s["end_line"]}',
                "role": s["role"],
                "can_block_posting": s["can_block_posting"],
                "interpretation": narrate(s, meanings, table_domain),
                "understood_pct": round(100.0 * k / n, 1) if n else None,
                "meanings": [m for m in meanings if m["explained"]][:12],
                "unexplained": [m["term"] for m in meanings if not m["explained"]][:12],
            })

        conflicts = detect_conflicts(obj, o.get("sections", []), term_index, known_universe)
        all_conflicts.extend({"object": obj, **c} for c in conflicts)
        scored = [s["understood_pct"] for s in secs_out if s["understood_pct"] is not None]
        out_objects[obj] = {
            "object": obj,
            "source": o.get("source"),
            "domains": o.get("domains", []),
            "processes": o.get("processes", []),
            "integrity": (inv.get("integrity") or {}).get("status"),
            "understood_pct": round(sum(scored) / len(scored), 1) if scored else None,
            "blocking_routines": o.get("blocking_sections", []),
            "conflicts": conflicts,
            "sections": secs_out,
        }

    gaps = sorted(gap_counter.items(), key=lambda x: -x[1])
    result = {
        "_meta": {
            "built_by": "brain_v2/interpret_code.py",
            "why": "code read THROUGH the brain; a reading that ignores prior analysis is weak",
            "objects": len(out_objects),
            "terms_seen": tot_terms,
            "terms_explained": tot_explained,
        },
        "_understanding_pct": round(100.0 * tot_explained / tot_terms, 1) if tot_terms else 0,
        "_understanding_pct_OURS": round(100.0 * tot_ours_explained / tot_ours, 1) if tot_ours else 0,
        "_ours_terms": tot_ours,
        "_ours_explained": tot_ours_explained,
        "_note_on_the_two_numbers": (
            "The headline percentage counts SAP standard identifiers we will never document. "
            "The OURS percentage counts only Y/Z custom objects and tables the brain is "
            "responsible for — that is the number worth moving."),
        "_conflicts": all_conflicts,
        "_top_gaps": [{"term": t, "seen_in_routines": c} for t, c in gaps[:60]],
        "_top_gaps_OURS": [{"term": t, "seen_in_routines": c}
                           for t, c in sorted(ours_gap_counter.items(),
                                              key=lambda x: -x[1])[:60]],
        "objects": out_objects,
    }
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(f"  objects interpreted:   {len(out_objects)}")
    print(f"  identifiers seen:      {tot_terms:,}")
    print(f"  explained by brain:    {tot_explained:,}  "
          f"({result['_understanding_pct']}%)  <- includes SAP standard we never document")
    print(f"  OF OUR OWN CODE:       {tot_ours_explained:,} of {tot_ours:,}  "
          f"({result['_understanding_pct_OURS']}%)  <- the number worth moving")
    print(f"  conflicts to review:   {len(all_conflicts)}")
    print(f"  top unexplained terms: {[t for t, _ in gaps[:8]]}")
    return result


def enrich(result):
    """Close the loop: what the reading understood goes BACK into the brain.

    Reading through the brain is only half of it — the half that makes the next reading
    better is writing the result back. Bounded on purpose: only routines that CAN STOP A
    POSTING become annotations. That is the control surface, it is 84 routines, and it is
    the set a support investigation actually needs. Annotating all 2,283 would be noise,
    and noise is how a brain stops being read.

    Idempotent: an annotation carrying the same routine + line is replaced, not duplicated.
    """
    path = BRAIN / "annotations" / "annotations.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    added = updated = 0

    for obj, o in result["objects"].items():
        blocking = [s for s in o["sections"] if s["can_block_posting"]]
        if not blocking:
            continue
        node = doc.setdefault(obj, {"annotations": []})
        anns = node.setdefault("annotations", [])
        for s in blocking:
            start = int(s["lines"].split("-")[0])
            new = {
                "tag": "CONTROL_POINT",
                "finding": s["interpretation"][:900],
                "impact": "This routine can STOP a posting. Any investigation into why a "
                          "document will not post must consider it.",
                "line": start,
                "session": "#099",
                "routine": s["routine"],
                "role": s["role"],
                "understood_pct": s["understood_pct"],
                "provenance": "brain_v2/interpret_code.py — code read through claims, "
                              "incidents, annotations and the gold table registry",
                "related": [m["term"] for m in s["meanings"]][:8],
            }
            existing = next((a for a in anns
                             if a.get("tag") == "CONTROL_POINT"
                             and a.get("routine") == s["routine"]
                             and a.get("line") == start), None)
            if existing:
                existing.update(new)
                updated += 1
            else:
                anns.append(new)
                added += 1

    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    back = json.loads(path.read_text(encoding="utf-8"))
    total = sum(1 for n in back.values()
                for a in (n.get("annotations") or [])
                if a.get("tag") == "CONTROL_POINT")
    assert total >= added, "enrichment did not land"
    print(f"\nENRICHED the brain: {added} new CONTROL_POINT annotations, {updated} updated "
          f"({total} total) across {len(back)} objects")
    return added, updated


if __name__ == "__main__":
    res = build()
    if res and "--enrich" in sys.argv:
        enrich(res)
