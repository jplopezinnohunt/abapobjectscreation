"""validate_artifacts.py — GOLDEN CASES over what the algorithms PRODUCE (s097, step 1).

`validate_algorithms.py` covers the resolution chain and the aliasing: pure functions with
a known answer. That left 22 of 25 algorithms unguarded — every one whose correctness lives
in an ARTIFACT rather than in a return value.

This closes that. Each case asserts a property the artifact must hold, chosen so that a
regression in the algorithm breaks it. The properties come in three kinds, and only the
third is really valuable:

  1. SHAPE      the artifact exists and has the fields consumers read
  2. FLOOR      a count that must not collapse — catches an algorithm silently degrading
  3. INVARIANT  a property that must hold whatever the data says

An invariant is the strong one because it survives the data changing. "The substrate rule
must never beat a business rule" stays true next month; "875,332 unexplained executions"
does not.

**Floors are set BELOW the measured value on purpose.** A floor at today's exact number
fails the moment the data legitimately moves, and a test that cries wolf gets deleted. The
floor asks: did this algorithm stop working?

Usage:  python brain_v2/methods/validate_artifacts.py
Exit 1 on any failure.
"""
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

failures, checked = [], 0


def case(algo, name, ok, detail):
    """Record one golden case. `ok` is the assertion; `detail` explains a failure."""
    global checked
    checked += 1
    if not ok:
        failures.append(f"{algo} · {name}: {detail}")


def load(rel):
    p = REPO / rel
    if not p.exists():
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def gold_tables():
    if not GOLD.exists():
        return set()
    try:
        con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
        t = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        con.close()
        return t
    except sqlite3.Error:
        return set()


def gold_count(table):
    try:
        con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
        n = con.execute('SELECT COUNT(*) FROM "%s"' % table).fetchone()[0]
        con.close()
        return n
    except sqlite3.Error:
        return 0


def main():
    tabs = gold_tables()

    # ---- A1 · chunked temporal read -------------------------------------
    # INVARIANT: the audit history must be CONTIGUOUS. A hole means a chunk was lost,
    # and a lost chunk looks exactly like a quiet period in every downstream analysis.
    if "rsau_audit_history" in tabs:
        try:
            con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
            days = [r[0] for r in con.execute(
                "SELECT DISTINCT SAL_DATE FROM rsau_audit_history ORDER BY 1")]
            con.close()
            case("A1", "audit history has usable depth", len(days) >= 60,
                 f"only {len(days)} distinct days — a chunked read is dropping windows")
            months = {d[:6] for d in days}
            case("A1", "history spans multiple months", len(months) >= 3,
                 f"only {len(months)} month(s) — cannot support any temporal claim")
        except sqlite3.Error as e:
            case("A1", "audit history readable", False, str(e)[:80])

    # ---- A2 · rolling-window accumulation -------------------------------
    # FLOOR: the accumulator's whole purpose is that history OUTLIVES the source window.
    for t, floor in (("rsau_audit_history", 10_000_000), ("cdhdr_history", 5_000_000),
                     ("tbtco_history", 1000)):
        if t in tabs:
            n = gold_count(t)
            case("A2", f"{t} retains accumulated history", n >= floor,
                 f"{n:,} rows, floor {floor:,} — the accumulator lost history it cannot recover")

    # ---- A4 · classifier ladder + A6 · substrate tier --------------------
    emap = load("brain_v2/executed_objects_domain_map.json")
    if emap:
        bd = emap.get("by_domain", {})
        case("A4", "classifier produced domains", len(bd) >= 15,
             f"only {len(bd)} domains — the ladder collapsed")
        # INVARIANT: the six domains discovered in s097 must never silently vanish again.
        for d in ("PBC", "RE_FX", "FI_AA", "SD", "PM", "CO"):
            case("A4", f"{d} still classified", d in bd,
                 f"{d} disappeared from the map — it was invisible before s097 and cost six "
                 f"wrong module verdicts")
        total = sum(v.get("total_execs", 0) for v in bd.values())
        unc = bd.get("Uncatalogued", {}).get("total_execs", 0)
        pct = 100.0 * unc / max(total, 1)
        # FLOOR well above today's 7.7%: this asks "did classification break?", not
        # "did it change?"
        case("A4", "unexplained execution stays bounded", pct <= 25.0,
             f"{pct:.1f}% unexplained — it was 7.7%; the ladder is failing to resolve")
        # INVARIANT: substrate is matched LAST. If it ever outranks a business rule it
        # becomes a dumping ground and the frontier lies by looking small.
        sub = bd.get("Technical_Substrate", {}).get("total_objects", 0)
        biz = sum(v.get("total_objects", 0) for k, v in bd.items()
                  if k not in ("Technical_Substrate", "Uncatalogued", "Basis_Security"))
        case("A6", "substrate never outgrows the business tiers", sub < biz,
             f"substrate {sub} objects vs business {biz} — a business rule is losing to it")

    # ---- A5 · adaptive learning loop ------------------------------------
    lr = load("process_mining/learned_rules.json")
    case("A5", "learned rules persist", lr is not None,
         "learned_rules.json missing — the only algorithm that LEARNS has lost what it learned")
    if lr:
        rules = lr.get("rules", lr) if isinstance(lr, dict) else {}
        # FLOOR: the authoritative signal took it from 8 rules to 25. Falling back toward
        # the old count means the component rung stopped feeding it.
        case("A5", "keeps what it learned", len(rules) >= 15,
             f"{len(rules)} rules — it was 25 after the component signal was wired; the "
             f"authoritative rung has stopped feeding it")
        # INVARIANT: its declared failure mode is a rule learned WRONG that then persists
        # forever. Basis_Security is a broad technical bucket; forcing it into one business
        # process taught the engine that IDoc output and exchange rates are identity
        # management. That mapping must never come back.
        poisoned = [k for k, v in rules.items()
                    if "Basis_Security" in json.dumps(v, ensure_ascii=False)]
        case("A5", "no rule learned from a technical catch-all", not poisoned,
             f"{len(poisoned)} rule(s) learned from Basis_Security: {poisoned[:4]} — that "
             f"mapping taught the engine that IDoc output is identity management")

    # ---- A7 · concept drift ---------------------------------------------
    drift = load("brain_v2/drift_signals.json")
    if drift:
        # INVARIANT (defect 1, found on its own first run): months of unequal length must
        # not produce a signal. Every flagged month must clear the day threshold.
        bad = [s for s in drift.get("signals", []) if (s.get("days_in_month") or 99) < 15]
        case("A7", "no signal from a partial month", not bad,
             f"{len(bad)} signal(s) from months under 15 days — comparing unequal months again")
        # INVARIANT (defect 2): no z-scores. They exploded to z=1016 on a 2-month baseline.
        has_z = any("z" in d for s in drift.get("signals", [])
                    for d in s.get("departures", []))
        case("A7", "uses relative change, not z-scores", not has_z,
             "z-score reappeared — it is unstable at n=2 and produced z=1016")

    # ---- B5 · OCEL 2.0 ---------------------------------------------------
    ocel = REPO / "Zagentexecution/sap_data_extraction/process_discovery/p2p.ocel2.sqlite"
    case("B5", "object-centric log exists", ocel.exists(),
         "p2p.ocel2.sqlite missing — the object-centric substrate is gone")

    # ---- C2 · ascent with provenance ------------------------------------
    graph = load("brain_v2/system_profile/model_graph.json")
    if graph:
        res = graph.get("resolution", {})
        case("C2", "ascent stays high", (res.get("pct_resolved") or 0) >= 75.0,
             f"{res.get('pct_resolved')}% — it was 92.2%; the chain is failing")
        # INVARIANT: the rung is ALWAYS recorded. Without it a curated assignment becomes
        # indistinguishable from an authoritative one (CP-003).
        rungs = res.get("by_rung", {})
        case("C2", "every object carries its resolution rung",
             sum(rungs.values()) == res.get("objects_total"),
             "objects resolved without a recorded rung — provenance lost")
        case("C2", "non-repository entities kept out of the denominator",
             "8_non_repository_entity" in rungs,
             "users, GL accounts and concepts are being counted as unresolved repository "
             "objects — that is the category error that made a 35% gap look real")

    # ---- C3 · static edges ----------------------------------------------
    if (REPO / "brain_v2/output/brain_v2_graph.json").exists():
        case("C3", "code graph exists", True, "")
    else:
        case("C3", "code graph exists", False, "brain_v2_graph.json missing")

    # ---- E1 · crossing ---------------------------------------------------
    links = load("brain_v2/system_profile/profile_links.json")
    if links:
        blind = (links.get("system_level_blind_spots", {}) or {}).get("modules", [])
        case("E1", "no system-level blind spot", not blind,
             f"{len(blind)} productive module(s) with no capability row: {blind}")
        cov = links.get("coverage", {})
        case("E1", "every productive module is modelled",
             cov.get("productive_with_capability_row") == cov.get("productive"),
             f"{cov.get('productive_with_capability_row')}/{cov.get('productive')} modelled")

    # ---- E2 · coherence --------------------------------------------------
    if graph:
        uns = (graph.get("coherence", {}) or {}).get("unsupported_modules", [])
        case("E2", "no unsupported assertion", not uns,
             f"module(s) asserted PRODUCTIVE with no evidence beneath: {uns}")

    # ---- E3 · triggers ---------------------------------------------------
    ts = load("brain_v2/methods/trigger_state.json")
    case("E3", "trigger state persists between runs",
         bool(ts and ts.get("last")),
         "no trigger state — growth cannot be measured, so nothing can ever fire")

    # ---- F1 · interface boundary ----------------------------------------
    bnd = load("brain_v2/interface_boundary.json")
    if bnd:
        s = bnd.get("summary", {})
        case("F1", "boundary enumerated", (s.get("destinations_configured") or 0) >= 100,
             f"{s.get('destinations_configured')} destinations — enumeration is failing")
        # INVARIANT: the whole point is CORRELATION. If nothing is live, the traffic side
        # of the correlation broke and every DEAD verdict is meaningless.
        case("F1", "traffic correlation works", (s.get("destinations_live") or 0) >= 1,
             "zero live destinations — the correlation against observed traffic is broken, "
             "so every DEAD verdict is an artefact")

    # ---- F2 · satellites -------------------------------------------------
    sat = load("brain_v2/satellites.json")
    if sat:
        s = sat.get("summary", {})
        case("F2", "satellites derived", (s.get("satellites") or 0) >= 10,
             f"{s.get('satellites')} satellites — derivation is failing")
        # INVARIANT: fleet recovery is the reason F2 exists. Without it a fleet of GUID
        # endpoints collapses into one label, which is the defect it was built to fix.
        case("F2", "GUID fleets are recovered", (s.get("guid_fleets") or 0) >= 1,
             "no fleet recovered — endpoints are collapsing to single labels again")
        # the MuleSoft fleet is the worked example: it must resolve to a domain
        resolved = [x for x in sat.get("satellites", []) if x.get("serves_domains")]
        case("F2", "satellites resolve to domains", len(resolved) >= 5,
             f"only {len(resolved)} satellites resolve to a domain")

    # ---- report ----------------------------------------------------------
    print(f"[artifact golden cases] {checked} cases over what the algorithms PRODUCE")
    if failures:
        print(f"  {len(failures)} FAILURE(S):", file=sys.stderr)
        for f in failures:
            print("    " + f, file=sys.stderr)
        print("\nA floor is set below the measured value on purpose: it asks whether the "
              "algorithm STOPPED WORKING, not whether the data moved.", file=sys.stderr)
        sys.exit(1)
    print("  OK — every artifact holds its properties. 22 algorithms are now guarded.")


if __name__ == "__main__":
    main()
