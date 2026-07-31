"""check_triggers.py — the loop fires on EVIDENCE, not on someone remembering (s097).

A cadence written in a document is a wish. This evaluates the actual state of the model
against declared thresholds and returns WHAT TO RE-RUN AND WHY.

Three families of trigger, and the third is the one that matters most:

  ACCUMULATION   enough new evidence has arrived that a capability's answer may have
                 changed. Frontier growth, new org units, new audit history.
  MATURITY       a score moved the wrong way. Ascent fell, coherence broke, a blind spot
                 opened. The model detecting its own regression.
  INTERPRETATION new logs or new interfaces can CHANGE THE MEANING of a domain, not just
                 add to it. A domain assignment is a HYPOTHESIS carried with the evidence
                 window it was derived from; extend the window materially and the
                 hypothesis is due for re-derivation.

State is kept in trigger_state.json so growth can be measured between runs — the first
run establishes the baseline and fires nothing, which is correct and not a failure.

Usage:  python brain_v2/methods/check_triggers.py [--json]
"""
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
STATE = HERE / "trigger_state.json"
EMAP = BRAIN / "executed_objects_domain_map.json"
GRAPH = BRAIN / "system_profile" / "model_graph.json"
LINKS = BRAIN / "system_profile" / "profile_links.json"
PROFILE = BRAIN / "system_profile" / "unesco_system_profile.json"
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# Thresholds. Stated here so they can be argued with, rather than buried in a condition.
FRONTIER_GROWTH_PCT = 5.0     # below this, new unresolved objects are noise
NEW_OBJECTS_ABSOLUTE = 50     # a step change in behaviour regardless of percentage
AUDIT_DAYS_FOR_REBUILD = 30   # shortest window where the channel mix is stable


def _load(p, d=None):
    return json.load(open(p, encoding="utf-8")) if p.exists() else (d if d is not None else {})


def measure():
    """Everything the triggers compare against, in one shot."""
    m = {}
    emap = _load(EMAP)
    bd = emap.get("by_domain", {})
    m["frontier_objects"] = bd.get("Uncatalogued", {}).get("total_objects", 0)
    m["frontier_execs"] = bd.get("Uncatalogued", {}).get("total_execs", 0)
    m["domains_with_activity"] = sum(1 for k, v in bd.items() if v.get("total_execs", 0) > 0)

    g = _load(GRAPH)
    m["ascent_pct"] = (g.get("resolution", {}) or {}).get("pct_resolved", 0)
    m["unsupported"] = len((g.get("coherence", {}) or {}).get("unsupported_modules", []) or [])

    l = _load(LINKS)
    m["blind_spots"] = len((l.get("system_level_blind_spots", {}) or {}).get("modules", []) or [])
    cov = l.get("coverage", {}) or {}
    m["productive"] = cov.get("productive", 0)
    m["productive_documented"] = cov.get("productive_with_knowledge_doc", 0)

    p = _load(PROFILE)
    org = p.get("org_structure", {}) or {}
    m["company_codes"] = org.get("company_codes")
    m["plants"] = org.get("plants")
    m["switches_on"] = (p.get("switch_framework", {}) or {}).get("switches_ON")

    # audit history depth — the evidence window every domain assignment rests on
    if GOLD.exists():
        try:
            con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
            row = con.execute("SELECT MIN(SAL_DATE), MAX(SAL_DATE), COUNT(*) "
                              "FROM rsau_audit_history").fetchone()
            con.close()
            m["audit_from"], m["audit_to"], m["audit_rows"] = row
        except sqlite3.Error:
            pass
    return m


def evaluate(now, prev):
    fired = []

    def fire(family, what, why, action):
        fired.append({"family": family, "trigger": what, "why": why, "run": action})

    if not prev:
        return fired, "baseline established — nothing to compare against yet"

    # ---- ACCUMULATION -------------------------------------------------
    a, b = prev.get("frontier_objects", 0), now.get("frontier_objects", 0)
    if a and b > a:
        growth = 100.0 * (b - a) / a
        if growth >= FRONTIER_GROWTH_PCT or (b - a) >= NEW_OBJECTS_ABSOLUTE:
            fire("ACCUMULATION", "frontier grew",
                 f"unresolved objects {a:,} -> {b:,} (+{growth:.1f}%) — new behaviour appeared",
                 "process_mining/executed_objects_domain_map.py + adaptive_discovery.py")

    for k, label in [("company_codes", "company codes"), ("plants", "plants"),
                     ("switches_on", "activated business functions")]:
        if prev.get(k) is not None and now.get(k) is not None and now[k] != prev[k]:
            fire("ACCUMULATION", f"{label} changed",
                 f"{prev[k]} -> {now[k]} — the FOOTPRINT DRIFTED",
                 "brain_v2/system_profile/probes/probe_footprint.py")

    if prev.get("audit_to") and now.get("audit_to") and now["audit_to"] > prev["audit_to"]:
        try:
            d0, d1 = str(prev["audit_to"]), str(now["audit_to"])
            days = (int(d1[:4]) - int(d0[:4])) * 365 + \
                   (int(d1[4:6]) - int(d0[4:6])) * 30 + (int(d1[6:8]) - int(d0[6:8]))
            if days >= AUDIT_DAYS_FOR_REBUILD:
                fire("ACCUMULATION", "audit window extended",
                     f"{days} days of new execution history since the last check",
                     "process_mining/rfc_process_classifier.py (operating model)")
        except (ValueError, TypeError):
            pass

    # ---- MATURITY -----------------------------------------------------
    if prev.get("ascent_pct") and now.get("ascent_pct", 0) < prev["ascent_pct"] - 0.5:
        fire("MATURITY", "ascent REGRESSED",
             f"{prev['ascent_pct']}% -> {now['ascent_pct']}% — objects arrived the chain "
             f"cannot resolve",
             "brain_v2/system_profile/probes/extract_component_hierarchy.py")
    if now.get("unsupported", 0) > 0:
        fire("MATURITY", "coherence broke",
             f"{now['unsupported']} module(s) asserted PRODUCTIVE with no evidence beneath",
             "brain_v2/system_profile/probes/probe_footprint.py for those modules")
    if now.get("blind_spots", 0) > 0:
        fire("MATURITY", "system-level blind spot",
             f"{now['blind_spots']} module(s) running with no capability row",
             "add the capability row, then a domain doc")

    # ---- INTERPRETATION -----------------------------------------------
    # Not "more data arrived" but "the MEANING of a domain may have changed".
    if prev.get("domains_with_activity") is not None and \
            now.get("domains_with_activity", 0) > prev["domains_with_activity"]:
        fire("INTERPRETATION", "a domain became active that was not",
             f"{prev['domains_with_activity']} -> {now['domains_with_activity']} domains "
             f"show execution — a previously silent domain is now real",
             "re-derive that domain: its assignment was a hypothesis on an older window")

    doc_gap = now.get("productive", 0) - now.get("productive_documented", 0)
    if doc_gap > 0:
        fire("INTERPRETATION", "productive module without a domain doc",
             f"{doc_gap} module(s) run in production with no prose layer — nobody can read "
             f"what they do",
             "write the domain doc")

    return fired, None


def main():
    now = measure()
    prev = _load(STATE, {}).get("last", {})
    fired, note = evaluate(now, prev)

    if "--json" in sys.argv:
        print(json.dumps({"now": now, "fired": fired, "note": note}, indent=1))
    else:
        print("[triggers] evidence state:")
        for k in ("frontier_objects", "frontier_execs", "ascent_pct", "blind_spots",
                  "unsupported", "productive", "productive_documented", "audit_to"):
            if now.get(k) is not None:
                v = now[k]
                print(f"    {k:26s} {v:,}" if isinstance(v, int) else f"    {k:26s} {v}")
        if note:
            print(f"\n  {note}")
        elif not fired:
            print("\n  nothing fired — no capability needs re-running on current evidence")
        else:
            print(f"\n  {len(fired)} TRIGGER(S) FIRED:")
            for f in fired:
                print(f"    [{f['family']}] {f['trigger']}")
                print(f"        why : {f['why']}")
                print(f"        run : {f['run']}")

    hist = _load(STATE, {})
    hist.setdefault("history", []).append(now)
    hist["history"] = hist["history"][-20:]
    hist["last"] = now
    json.dump(hist, open(STATE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
