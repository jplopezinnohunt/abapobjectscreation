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


UNATTRIBUTED_CLASSES = 5   # below this it is a tail, not a gap
CYCLE_STALE_DAYS = 8       # weekly schedule + one day of slack


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

    # HAS THE LOOP TURNED? measured, not assumed
    cs = _load(HERE / "cycle_state.json")
    if cs.get("last_run_utc"):
        try:
            import datetime
            last = datetime.datetime.fromisoformat(cs["last_run_utc"])
            m["cycle_days_since_run"] = (
                datetime.datetime.now(datetime.timezone.utc) - last).days
            m["cycle_last_run"] = cs["last_run_utc"]
            m["cycle_steps_failed"] = cs.get("steps_failed")
        except (ValueError, TypeError):
            pass
    # A run that STARTED and never recorded a completion is not the same thing as a run
    # that never happened, and the two send you to different places to look.
    m["cycle_status"] = cs.get("status")
    m["cycle_started"] = cs.get("started_utc")

    # audit history depth — the evidence window every domain assignment rests on
    if GOLD.exists():
        try:
            con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
            row = con.execute("SELECT MIN(SAL_DATE), MAX(SAL_DATE), COUNT(*) "
                              "FROM rsau_audit_history").fetchone()
            m["audit_from"], m["audit_to"], m["audit_rows"] = row

            # WRITE PATHS. An object class that changes and whose writer we cannot name is
            # behaviour we do not hold — and the transaction-code field frequently CANNOT
            # answer, because a BAPI/RFC leaves it empty by design. This is the measurement
            # that makes algorithm A8 fire on evidence instead of on someone remembering.
            classes = {r[0] for r in con.execute(
                "SELECT DISTINCT OBJECTCLAS FROM cdhdr_history WHERE OBJECTCLAS <> ''")}
            m["change_classes"] = len(classes)
            attributed = _load(REPO / "brain_v2" / "change_attribution.json")
            known = set((attributed.get("classes") or {}))
            m["classes_unattributed"] = len(classes - known)
            m["classes_no_write_path"] = sorted(classes - known)[:12]
            con.close()
        except sqlite3.Error as e:
            # was `pass`. A swallowed error here reads as "nothing to measure", which is
            # exactly how a trigger silently stops firing — the failure this file exists
            # to prevent, committed inside the file itself.
            print(f"  [triggers] measurement incomplete: {e}")

        # THE ADDRESS CHAIN (algorithm A10). Three things can change underneath it, and
        # each one silently invalidates every query built on the last run.
        try:
            con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
            n = con.execute("SELECT count(*) FROM fmifiit_full").fetchone()[0]
            f = con.execute("SELECT count(*) FROM fmifiit_full WHERE MEASURE IS NOT NULL "
                            "AND trim(MEASURE) <> ''").fetchone()[0]
            # Whether the DESIGNED work carrier is populated at all. Crossing zero in
            # either direction means the designed chain just started or stopped running.
            m["chain_designed_carrier_pct"] = round(100.0 * f / n, 2) if n else 0.0
            m["chain_fm_lines"] = n
            m["chain_funds"] = con.execute("SELECT count(*) FROM funds").fetchone()[0]
            m["chain_wbs"] = con.execute("SELECT count(*) FROM prps").fetchone()[0]
            # How many distinct minting rules exist for the root identifier. A new one
            # appearing means someone started issuing codes by a rule no filter knows.
            import re as _re
            shapes = set()
            for (v,) in con.execute("SELECT DISTINCT FINCODE FROM funds"):
                if v:
                    shapes.add(_re.sub("[0-9]", "D", _re.sub("[A-Za-z]", "A", v.strip())))
            m["chain_fund_grammars"] = len(shapes)
            con.close()
        except sqlite3.Error as e:
            print(f"  [triggers] chain measurement incomplete: {e}")

    lin = _load(REPO / "brain_v2" / "chain_lineage.json")
    if lin:
        m["chain_hops_walked"] = (lin.get("summary") or {}).get("hops_walked")
        m["chain_substituted"] = len((lin.get("summary") or {}).get("substituted") or [])
        m["chain_blind_objects"] = len((lin.get("summary") or {}).get("blind_objects") or [])
    return m


def evaluate(now, prev):
    fired = []

    # A trigger reports EVIDENCE and the KIND of response it needs. It never names a
    # script, because naming a script is a decision taken on demand, and on-demand
    # decisions are precisely the ones that stop being taken — the hole this whole file
    # exists to close. The ORDER lives in run_analysis_cycle.py; adding an algorithm means
    # placing it in that chain, not remembering to call it here.
    RESPONSE = {
        "CYCLE": ("python brain_v2/methods/run_analysis_cycle.py",
                  "the analysis cycle runs it in dependency order"),
        "EXTRACTION": ("an extraction pass — needs a connection",
                       "deliberately outside the cycle: it depends on a VPN and on someone "
                       "deciding it is time"),
        "AUTHORING": ("a human writes it",
                      "no algorithm produces a domain doc or a capability row"),
    }

    def fire(family, what, why, needs, detail=""):
        cmd, note = RESPONSE[needs]
        fired.append({"family": family, "trigger": what, "why": why,
                      "needs": needs, "run": cmd, "_why_that": note,
                      "scope": detail or None})

    if not prev:
        return fired, "baseline established — nothing to compare against yet"

    # ---- THE LOOP ITSELF ------------------------------------------------
    # "Run it weekly" is only real if a missed week is DETECTED. A scheduled task that stops
    # firing produces no error and no artifact, and the absence of fresh artifacts reads as
    # "nothing changed" — the most expensive kind of silence. This fires so the next session
    # catches it up instead of inheriting stale answers without knowing.
    stale = now.get("cycle_days_since_run")
    if stale is None:
        fire("MAINTENANCE",
             ("the analysis cycle STARTED AND NEVER FINISHED"
              if now.get("cycle_status") == "RUNNING"
              else "the analysis cycle has NEVER recorded a run"),
             (f"a run began at {now.get('cycle_started')} and recorded no completion — it "
              f"died, and a died run reads as a never-run unless the two are separated"
              if now.get("cycle_status") == "RUNNING" else
              "no cycle_state.json — either it has not run since this check existed, or the "
              "schedule was never registered"),
             "CYCLE")
    elif stale > CYCLE_STALE_DAYS:
        fire("MAINTENANCE", "the analysis cycle is stale",
             f"last run {stale} days ago, expected weekly — a missed schedule produces no "
             f"error, so this is the only thing that notices", "CYCLE")

    # ---- WRITE PATH ----------------------------------------------------
    # NOTE ON WHAT A TRIGGER MAY SAY. Every `run` below points at the CYCLE, never at an
    # individual script. A trigger that names one algorithm is an on-demand decision, and
    # on-demand decisions are the ones that stop being taken — which is the hole this whole
    # trigger file exists to close. The trigger's job is to report EVIDENCE; the ORDER lives
    # in run_analysis_cycle.py, so adding an algorithm means placing it in the chain.
    # A NEW object class appearing in the change log is new behaviour, and until its writer
    # is named the domain that owns it is listed rather than understood. This fires on the
    # evidence, which is the whole point: nobody has to remember to ask.
    pa, pb = prev.get("change_classes", 0), now.get("change_classes", 0)
    if pa and pb > pa:
        fire("WRITE_PATH", "new object classes are changing",
             f"change classes {pa} -> {pb} — something began writing that was not writing "
             f"before, and no writer is named for it",
             "CYCLE")
    un = now.get("classes_unattributed", 0)
    if un >= UNATTRIBUTED_CLASSES:
        fire("WRITE_PATH", "object classes with no known writer",
             f"{un} class(es) change with no attributed write path"
             + (f" — e.g. {', '.join(now.get('classes_no_write_path', [])[:5])}"
                if now.get("classes_no_write_path") else "")
             + ". An empty transaction code is not an answer: it usually means a BAPI/RFC "
               "whose design never set one, so the channel is the finding",
             "CYCLE")

    # ---- ACCUMULATION -------------------------------------------------
    a, b = prev.get("frontier_objects", 0), now.get("frontier_objects", 0)
    if a and b > a:
        growth = 100.0 * (b - a) / a
        if growth >= FRONTIER_GROWTH_PCT or (b - a) >= NEW_OBJECTS_ABSOLUTE:
            fire("ACCUMULATION", "frontier grew",
                 f"unresolved objects {a:,} -> {b:,} (+{growth:.1f}%) — new behaviour appeared",
                 "CYCLE", "classification + adaptive discovery")

    for k, label in [("company_codes", "company codes"), ("plants", "plants"),
                     ("switches_on", "activated business functions")]:
        if prev.get(k) is not None and now.get(k) is not None and now[k] != prev[k]:
            fire("ACCUMULATION", f"{label} changed",
                 f"{prev[k]} -> {now[k]} — the FOOTPRINT DRIFTED",
                 "EXTRACTION", "footprint probe")

    if prev.get("audit_to") and now.get("audit_to") and now["audit_to"] > prev["audit_to"]:
        try:
            d0, d1 = str(prev["audit_to"]), str(now["audit_to"])
            days = (int(d1[:4]) - int(d0[:4])) * 365 + \
                   (int(d1[4:6]) - int(d0[4:6])) * 30 + (int(d1[6:8]) - int(d0[6:8]))
            if days >= AUDIT_DAYS_FOR_REBUILD:
                fire("ACCUMULATION", "audit window extended",
                     f"{days} days of new execution history since the last check",
                     "CYCLE", "the operating model")
        except (ValueError, TypeError):
            pass

    # ---- MATURITY -----------------------------------------------------
    if prev.get("ascent_pct") and now.get("ascent_pct", 0) < prev["ascent_pct"] - 0.5:
        fire("MATURITY", "ascent REGRESSED",
             f"{prev['ascent_pct']}% -> {now['ascent_pct']}% — objects arrived the chain "
             f"cannot resolve",
             "EXTRACTION", "component hierarchy TADIR->TDEVC->DF14L")
    if now.get("unsupported", 0) > 0:
        fire("MATURITY", "coherence broke",
             f"{now['unsupported']} module(s) asserted PRODUCTIVE with no evidence beneath",
             "EXTRACTION", "footprint probe for those modules")
    if now.get("blind_spots", 0) > 0:
        fire("MATURITY", "system-level blind spot",
             f"{now['blind_spots']} module(s) running with no capability row",
             "AUTHORING", "capability row + domain doc")

    # ---- INTERPRETATION -----------------------------------------------
    # Not "more data arrived" but "the MEANING of a domain may have changed".
    if prev.get("domains_with_activity") is not None and \
            now.get("domains_with_activity", 0) > prev["domains_with_activity"]:
        fire("INTERPRETATION", "a domain became active that was not",
             f"{prev['domains_with_activity']} -> {now['domains_with_activity']} domains "
             f"show execution — a previously silent domain is now real",
             "CYCLE", "re-derive that domain — its assignment was a hypothesis on an older window")

    doc_gap = now.get("productive", 0) - now.get("productive_documented", 0)
    if doc_gap > 0:
        fire("INTERPRETATION", "productive module without a domain doc",
             f"{doc_gap} module(s) run in production with no prose layer — nobody can read "
             f"what they do",
             "AUTHORING", "domain doc")

    # ---- THE ADDRESS CHAIN (A10) -------------------------------------------------
    # This chain is held together by identifier conventions and custom tables rather than
    # by foreign keys, which makes it unusually easy to invalidate without anyone noticing.
    if now.get("chain_hops_walked") is None:
        fire("MAINTENANCE", "the address chain has never been reconstructed",
             "no chain_lineage.json exists, so how funding reaches work is unmeasured",
             "CYCLE")
    else:
        was, isnow = prev.get("chain_designed_carrier_pct"), now.get("chain_designed_carrier_pct")
        if was is not None and isnow is not None and (was == 0) != (isnow == 0):
            fire("INTERPRETATION", "the DESIGNED work carrier crossed zero",
                 f"Funded Program population moved {was}% -> {isnow}%. Either the designed "
                 f"chain has started running or it has stopped, and every join that "
                 f"reconstructs work by identifier grammar is now answering the wrong way",
                 "CYCLE")
        wasg, isg = prev.get("chain_fund_grammars"), now.get("chain_fund_grammars")
        if wasg and isg and isg > wasg:
            fire("INTERPRETATION", "a new identifier grammar appeared",
                 f"fund code shapes went {wasg} -> {isg}. Someone is minting identifiers by a "
                 f"rule none of the existing filters or groupings know about, so any "
                 f"population selected by code pattern is now silently incomplete",
                 "CYCLE")
        for k, label in (("chain_funds", "the fund master"), ("chain_wbs", "the WBS population")):
            a, b = prev.get(k), now.get(k)
            if a and b and a > 0 and (100.0 * (b - a) / a) >= FRONTIER_GROWTH_PCT:
                fire("ACCUMULATION", f"{label} grew materially",
                     f"{a:,} -> {b:,} ({100.0*(b-a)/a:.1f}%) — the chain's coverage and its "
                     f"orphan set both move with it", "CYCLE")
        if now.get("chain_blind_objects"):
            fire("WRITE_PATH", "objects in the chain nobody can watch change",
                 f"{now['chain_blind_objects']} object(s) in the address chain have no change "
                 f"document coverage, so 'who changed this' is unanswerable for them — A8 "
                 f"attribution against the execution log is the only instrument left",
                 "CYCLE")

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
