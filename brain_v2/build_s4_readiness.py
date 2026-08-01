"""build_s4_readiness.py — S/4 readiness as a SUBJECT, not only a column.

**A capability column with no subject stays empty in every domain.** `R_S4_READINESS` was the
only completely empty column across all 21 domains, and the reason was structural rather than
lazy: readiness was modelled as a question asked 21 times and owned by nobody. Security had the
identical shape — `E_AUTH` empty in 16 of 21 — and it filled the moment it got a subject.

So readiness becomes a cross-cutting subject with its own store, exactly like security and
integration:

    R_S4_READINESS (column)   is THIS domain ready? asked 21 times
    S/4 readiness (subject)   the factors, studied once, rolling up into all 21

**The factor that was missing, and why it was missing.** The sub-scorecard held six factors —
BP/CVI, simplification items, custom code, technical, readiness-check 2.0, finance — and every
one of them is TECHNICAL. Nothing in it could hold a commercial exposure, so when the digital-
access finding arrived it had nowhere to land. That is added here as a seventh factor, and it
may be the largest one for this tenant: an operating model that is 80% external means every
integration which is free today becomes metered API consumption on S/4HANA Cloud.

**Each factor reports what it needs and whether we hold it**, so the store says what it cannot
see rather than returning an empty section. An empty readiness report reads as "ready", which
is the most expensive misreading available here.

Emits: brain_v2/s4_readiness.json
Run:   python brain_v2/build_s4_readiness.py
"""
import json
import sys
from pathlib import Path

BRAIN = Path(__file__).resolve().parent
REPO = BRAIN.parent
MODEL = BRAIN / "capability_model" / "s4_readiness_model.json"
CAP = BRAIN / "capability_model" / "capability_model.json"
ATTRIB = BRAIN / "change_attribution.json"
OUT = BRAIN / "s4_readiness.json"

# The seventh factor. Kept here rather than edited into the model file so its provenance
# stays visible: it came from a conversation, not from the original research.
COMMERCIAL = {
    "factor": "DIGITAL_ACCESS_EXPOSURE",
    "kind": "COMMERCIAL — the only non-technical factor, and possibly the largest",
    "question": ("what does the current operating model COST once indirect use is metered?"),
    "why_it_was_missing": (
        "the sub-scorecard's six original factors are all technical, so a commercial exposure "
        "had nowhere to land. The column stayed empty while we looked for technical readiness."),
    "the_asymmetry": (
        "today a satellite calling over RFC under a technical account costs a system-user "
        "licence and nothing per call. On S/4HANA Cloud the same traffic is API consumption "
        "and Digital Access documents. With an 80%-external operating model this is not a "
        "migration detail — it is the SHAPE of the migration."),
    "measurable_now": (
        "SAP licenses indirect use by DOCUMENTS CREATED through non-dialog channels, and A8 "
        "already classifies every object class by write channel. The traffic half needs NO new "
        "extraction."),
    "blocked_on": "UNESCO's contract and SAP's Digital Access terms — we hold neither",
    "worst_case": (
        "the opaque accounts fail twice: MULESOFT 3,230,958 calls under one identity, "
        "BRIDGE-RFC 2,106,347 and UBO-RFC 324,390 with no caller field at all. Traffic that "
        "cannot be attributed can be neither excused as named-user activity nor apportioned to "
        "a business owner — and in a negotiation, traffic you cannot attribute is traffic you "
        "cannot defend."),
    "task": "AN-DIGITAL-ACCESS-EXPOSURE",
}


def main():
    if not MODEL.exists():
        print(f"missing {MODEL}", file=sys.stderr)
        return 1
    M = json.load(open(MODEL, encoding="utf-8"))
    factors = M.get("factors", {})

    rows = []
    for name, f in factors.items():
        e = {"factor": name, "kind": "TECHNICAL"}
        if isinstance(f, dict):
            for k in ("question", "status", "state", "evidence", "score", "verdict"):
                if f.get(k):
                    e[k] = f[k]
        e["state"] = e.get("status") or e.get("state") or "NOT_SCORED"
        rows.append(e)
    rows.append({**COMMERCIAL, "state": "MEASURABLE_NOW_BLOCKED_ON_CONTRACT"})

    # the column, for contrast — this is the point of the whole file
    col_empty = 0
    if CAP.exists():
        C = json.load(open(CAP, encoding="utf-8"))
        doms = (C.get("domains") or {})
        col_empty = sum(1 for d in doms.values()
                        if isinstance(d, dict) and str(d.get("R_S4_READINESS")) in
                        ("NONE", "None", "null", ""))
        total = len(doms)
    else:
        total = 0

    # what the traffic half already says, with no new extraction
    rfc_classes = 0
    if ATTRIB.exists():
        A = json.load(open(ATTRIB, encoding="utf-8"))
        rfc_classes = sum(1 for r in (A.get("classes") or {}).values()
                          if any(c["channel"] == "RFC_INBOUND"
                                 for c in r.get("channels_DERIVED_from_logs", [])))

    json.dump({
        "_generated_by": "brain_v2/build_s4_readiness.py",
        "_what_this_is": ("S/4 readiness as a cross-cutting SUBJECT. The column asks 21 times; "
                          "this owns the answer once."),
        "_why_the_column_was_empty": (
            f"R_S4_READINESS is NONE in {col_empty} of {total} domains. Not neglect — it was a "
            f"question owned by nobody. A capability column with no subject stays empty in "
            f"every domain, and SECURITY had the identical shape until it got one."),
        "_the_missing_factor": (
            "the six original factors are ALL technical, so a commercial exposure had nowhere "
            "to land. DIGITAL_ACCESS_EXPOSURE is added as the seventh and may be the largest "
            "for this tenant."),
        "_read_before_reporting": (
            "an empty readiness report reads as READY. Every factor below states whether it "
            "has been scored, and NOT_SCORED means we have not looked — never that it is fine."),
        "column_state": {"domains": total, "empty": col_empty},
        "traffic_half_already_measured": {
            "object_classes_written_over_RFC": rfc_classes,
            "note": ("these are the Digital Access counting candidates. Derived by A8, "
                     "available now, no extraction needed."),
        },
        "factors": rows,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[S/4 readiness] {len(rows)} factors — 6 technical + 1 commercial")
    for r in rows:
        print(f"  {r['factor']:32s} {r.get('kind','')[:11]:11s} {r['state']}")
    print(f"\n  the column it rolls into: R_S4_READINESS is NONE in {col_empty} of {total} "
          f"domains.")
    print(f"  {rfc_classes} object classes are written over RFC — the Digital Access "
          f"candidates, measurable now.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
