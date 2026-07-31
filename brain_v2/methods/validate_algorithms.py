"""validate_algorithms.py — GOLDEN CASES. The regression harness for algorithms (s097).

The hardest lesson of this session: **running without error is not validation.**

The classifier ran for months and was wrong at scale — 19,524 executions of a Project
System cost report filed under Controlling because a greedy `^KA` regex matched its
package. It never errored. Nothing failed. The output was confident, plausible and wrong.

An algorithm needs cases with KNOWN CORRECT ANSWERS, and every defect found must become
one. That is the only mechanism that stops a fix from silently regressing.

Every case below is a real finding from this session, with its evidence. A case is not a
guess about what should happen — it is a fact that was established the hard way.

Usage:  python brain_v2/methods/validate_algorithms.py
Exit 1 on any regression.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "brain_v2"))

from component_map import (  # noqa: E402
    component_of_package, domain_of_package, domain_of_function_module,
    component_to_domain)
from canonical import canonical, aliases_of  # noqa: E402


# ---------------------------------------------------------------------------
# C1 · component resolution — the authoritative chain
# Each of these was established by asking SAP, after a regex had guessed differently.
# ---------------------------------------------------------------------------
COMPONENT_CASES = [
    ("KAP1", "PS-IS-REP-ACC", "PS",
     "RKPDEMO2 (19,524 execs) sat under Controlling for months: '^KA' matched the package. "
     "It is Project System cost reporting."),
    ("FTBB", "FIN-FSCM-TRM-MR", "TRM",
     "hand-corrected to Treasury_EBS by me, which was ALSO a guess. DF14L settles it: "
     "Transaction Manager, Market Risk."),
    ("FTE", "FIN-FSCM-CLM-CM-CM", "Treasury_EBS",
     "the bank-statement side — distinct from FTA/FTBB deal management"),
    ("FTA", "FIN-FSCM-TRM-TM", "TRM", "Transaction Manager proper"),
    ("PAOC_FPM_COM_ENGINE", "PA-PM-PB", "PBC",
     "PBC sits under PERSONNEL MANAGEMENT, not PSM — which is why an FM-shaped search "
     "never found the tenant's largest staff-budget capability"),
    ("FMBPA_E", "PSM-FM-BCS-BU", "PSM_FM", "Budget Control System, budgeting"),
    ("AA", "FI-AA-AA", "FI_AA", "Asset Accounting — reported 'not evidenced' before s097"),
    ("IEQM", "PM-EQM-EQ", "PM", "equipment — 19,313 records, previously invisible"),
    ("VA", "SD-SLS", "SD", "Sales — reported 'not implemented' before s097"),
    ("RE_CN_CN", "RE-FX-CN", "RE_FX", "Real Estate contracts — the original user-flagged miss"),
    ("CN_PSP_OPR", "PS-ST-OPR", "PS", "WBS structures"),
    ("ME", "MM-PUR", "Procurement_P2P", "purchasing"),
    ("MB", "MM-IM", "Procurement_P2P", "inventory management"),
    ("PTRA", "FI-TV-COS", "Travel", "trip costs"),
    ("FBZ", "FI-AP-AP-PT", "Payment_BCM", "the automatic payment program"),
]

# ---------------------------------------------------------------------------
# C1b · function modules — resolved through their FUNCTION GROUP
# These dominated the frontier precisely because the chain skipped that hop.
# ---------------------------------------------------------------------------
FM_CASES = [
    ("BAPI_PR_GETDETAIL", "Procurement_P2P", "48,918 execs sat unclassified"),
    ("BAPI_PR_CHANGE", "Procurement_P2P", "37,247 execs — a WRITE call, unclassified"),
    ("BAPI_PO_GETDETAIL1", "Procurement_P2P", "21,591 execs"),
    ("BAPI_TRIP_CHECK_STATUS", "Travel", "46,437 execs — plainly Travel, invisible"),
]

# ---------------------------------------------------------------------------
# E4 · canonicalisation — the defect that appeared three times in one session
# ---------------------------------------------------------------------------
# C1c · custom Z/Y function modules — no SAP component exists for them BY DEFINITION.
# These are the objects the product thesis rests on: no commercial tool can label them.
CUSTOM_FM_CASES = [
    ("Y_BAPI_WBS_FINANCIAL_DATA_1", "PS",
     "974,868 calls — the highest-volume business function module in the tenant, and it "
     "resolved to NOTHING until the custom overlay rung existed"),
    ("Y_BAPI_YPS8", "PS", "460,003 calls, the MuleSoft project-financials sync"),
    ("Y_BAPI_YFM1", "PSM_FM", "the FM/Budget side of the same satellite"),
]

ALIAS_CASES = [
    ("PSM", "PSM_FM", "domain docs live in PSM/, the canonical key is PSM_FM"),
    ("Payment", "Payment_BCM", "registry alias"),
    ("BCM", "Payment_BCM", "the SECOND alias for the same domain — counted twice before s097"),
    ("Treasury", "Treasury_EBS", "docs live in Treasury/"),
    ("Procurement", "Procurement_P2P", "docs live in Procurement/"),
    ("RE-FX", "RE_FX", "hyphen/underscore must resolve to the same domain"),
    ("co", "CO", "case must not matter"),
]

# ---------------------------------------------------------------------------
# component_to_domain · longest prefix must win
# This is the property that an ORDERED rule ladder cannot promise, and the reason the
# lookup replaced the regex as the primary rung.
# ---------------------------------------------------------------------------
PREFIX_CASES = [
    ("FI-BL-PT-BS-EL", "Treasury_EBS",
     "must beat FI-BL and FI — electronic bank statement is not generic banking"),
    ("FI-AP-AP-PT", "Payment_BCM", "must beat FI-AP and FI"),
    ("PA-PM-PB", "PBC", "must beat PA — otherwise position budgeting reads as generic HR"),
    ("PSM-FM-BCS-BU", "PSM_FM", "must beat PSM"),
    ("FI-GL", "FI", "plain FI is correct here"),
]


def main():
    failures, checked = [], 0

    for pkg, want_comp, want_dom, why in COMPONENT_CASES:
        checked += 1
        got_comp = component_of_package(pkg)
        got_dom = domain_of_package(pkg)
        if got_comp != want_comp:
            failures.append(f"C1 package {pkg}: component {got_comp!r} != {want_comp!r} — {why}")
        elif got_dom != want_dom:
            failures.append(f"C1 package {pkg}: domain {got_dom!r} != {want_dom!r} — {why}")

    for fm, want, why in FM_CASES:
        checked += 1
        got = domain_of_function_module(fm)
        if got != want:
            failures.append(f"C1b function module {fm}: {got!r} != {want!r} — {why}")

    for fm, want, why in CUSTOM_FM_CASES:
        checked += 1
        got = domain_of_function_module(fm)
        if got != want:
            failures.append(f"C1c custom FM {fm}: {got!r} != {want!r} — {why}")

    for spelling, want, why in ALIAS_CASES:
        checked += 1
        got = canonical(spelling)
        if got != want:
            failures.append(f"E4 alias {spelling!r}: {got!r} != {want!r} — {why}")

    for comp, want, why in PREFIX_CASES:
        checked += 1
        got, pref = component_to_domain(comp)
        if got != want:
            failures.append(f"prefix {comp}: {got!r} != {want!r} (matched {pref!r}) — {why}")

    # a declared alias must round-trip: every spelling resolves back to its key
    for key in ("PSM_FM", "Payment_BCM", "Treasury_EBS", "Procurement_P2P"):
        for a in aliases_of(key):
            checked += 1
            if canonical(a) != key:
                failures.append(f"E4 round-trip: alias {a!r} of {key} does not resolve back")

    # ---- A3 · two-axis classification ------------------------------------
    # The ORIGIN axis is the finding this project keeps returning to: the same BAPI called
    # by MULESOFT and by a named user are DIFFERENT FACTS, and a classifier that reports
    # only the function module cannot tell them apart. These cases hold the axis in place.
    sys.path.insert(0, str(REPO / "process_mining"))
    try:
        import rfc_process_classifier as a3
    except ImportError:
        a3 = None
    if a3 is not None:
        for user, want, why in [
            ("MULESOFT", "MuleSoft (external bus)", "the bus must never read as a person"),
            ("BRIDGE-RFC", "BRIDGE-RFC (external portal)", "portal-as-user is its own origin"),
            ("SMTMSBP", "SolMan (external monitor)", "monitoring traffic is not business traffic"),
            ("JOBBATCH", "internal batch/system", "internal batch is not an external satellite"),
            ("JP_LOPEZ", "us (JP_LOPEZ extraction)",
             "OUR OWN extraction must be excluded, or we measure ourselves as the business"),
            ("MARIA.ROSSI", "named user (dialog/portal-as-user)", "the default is a person"),
        ]:
            checked += 1
            got = a3.classify_origin(user)
            if got != want:
                failures.append(f"A3 origin {user}: {got!r} != {want!r} — {why}")

        for fm, want, why in [
            ("BAPI_ACC_DOCUMENT_POST", ("KNOWN", "FI-Posting"), "the canonical posting BAPI"),
            ("BAPI_PO_CREATE1", ("KNOWN", "P2P-PO"), "purchase order creation is P2P"),
            ("RFC_PING", ("_technical", "_technical"),
             "technical chatter must not inflate a business process"),
            ("RFC_READ_TABLE", ("_ours", "_ours"),
             "our own reader must be excluded whoever calls it — it is how WE extract"),
        ]:
            checked += 1
            got = a3.classify(fm, "SOMEUSER")
            if got != want:
                failures.append(f"A3 classify {fm}: {got!r} != {want!r} — {why}")

    # ---- D4 · field splitting --------------------------------------------
    # RFC_READ_TABLE has a 512-byte line buffer, so a wide table is read in field chunks and
    # merged BY ROW POSITION. Position is the only join key available — which makes a
    # chunking that drops or reorders a field silently corrupt every merged row afterwards.
    sys.path.insert(0, str(REPO / "Zagentexecution" / "mcp-backend-server-python"))
    try:
        from rfc_helpers import plan_field_chunks, merge_chunks_by_position
    except ImportError:
        plan_field_chunks = None
    if plan_field_chunks is not None:
        flds = [f"F{i:02d}" for i in range(23)]
        plan = plan_field_chunks(flds, 8)
        checked += 1
        if [f for c in plan for f in c] != flds:
            failures.append("D4 chunking lost or reordered a field — every row merged by "
                            "position afterwards is corrupt, and it looks valid")
        checked += 1
        if any(len(c) > 8 for c in plan):
            failures.append("D4 a chunk exceeds the 512-byte buffer limit — the read fails "
                            "at runtime, not here")
        checked += 1
        if plan_field_chunks([], 8) != []:
            failures.append("D4 empty field list must plan no chunks")
        checked += 1
        merged = merge_chunks_by_position([{"A": 1}, {"A": 2}], [[{"B": 9}, {"B": 8}]])
        if merged != [{"A": 1, "B": 9}, {"A": 2, "B": 8}]:
            failures.append(f"D4 positional merge is wrong: {merged}")
        checked += 1
        # a short chunk must not shift the rows that follow it
        short = merge_chunks_by_position([{"A": 1}, {"A": 2}], [[{"B": 9}]])
        if short != [{"A": 1, "B": 9}, {"A": 2}]:
            failures.append(f"D4 a short chunk shifted the merge: {short}")

    # ---- D6 · drift over an accumulated history --------------------------
    # Both of this algorithm's real defects are cases here. Neither was caught by a check:
    # they were caught by reading the output, because the statistic lived inside main().
    try:
        import detect_drift as d6
    except ImportError:
        d6 = None
    if d6 is not None:
        checked += 1
        # DEFECT 1 — raw monthly VOLUMES across months of unequal length. February against
        # a 31-day month differs by 10% before anything real happens: 11 false signals.
        flat = [("202601", 100.0, 10.0, 5.0), ("202602", 100.0, 10.0, 5.0),
                ("202603", 100.0, 10.0, 5.0)]
        if d6.departures_for(flat):
            failures.append("D6 flagged drift on a CONSTANT per-day rate — the volume/rate "
                            "defect is back, and it produced 11 false signals last time")
        checked += 1
        jump = [("202601", 100.0, 10.0, 5.0), ("202602", 100.0, 10.0, 5.0),
                ("202603", 300.0, 30.0, 15.0)]
        got = d6.departures_for(jump)
        if not got or got[0][0] != "202603":
            failures.append("D6 missed a 3x jump — a detector that never fires is not safe, "
                            "it is useless")
        checked += 1
        # DEFECT 2 — a z-score over a 2-month baseline: sigma collapses and the score
        # explodes. The run produced z=1016. Relative change stays legible at n=2.
        if got and any(abs(d["relative_change_pct"]) > 1000 for d in got[0][1]):
            failures.append("D6 produced an absurd magnitude — the z-score defect is back. "
                            "A number that looks rigorous and cannot be read is worse than "
                            "a plain one")
        checked += 1
        # the baseline must travel WITH the finding, or it cannot be judged
        if got and got[0][2] != ["202601", "202602"]:
            failures.append(f"D6 baseline lost: {got[0][2] if got else None}")
        checked += 1
        # one month of history cannot support a baseline — it must stay silent
        if d6.departures_for([("202601", 100.0, 10.0, 5.0), ("202602", 900.0, 90.0, 45.0)]):
            failures.append("D6 signalled with a single baseline month — a departure needs "
                            "something to depart FROM")

    # ---- A8 · change-to-executor attribution ------------------------------
    # Every case here is one of the three scorings that were WRONG before one was right.
    try:
        from attribute_changes_to_programs import phi as a8_phi, _channel as a8_channel
    except ImportError:
        a8_phi = None
    if a8_phi is not None:
        checked += 1
        # DEFECT 1 — the daily dispatcher. It runs in every slot, so d=0, a margin
        # collapses, and it must score NOTHING. Raw coincidence gave it a perfect score and
        # named it the writer of every object class.
        if abs(a8_phi(100, 50, 0, 0)) > 1e-9:
            failures.append("A8 a program present in every slot must score 0 — the "
                            "dispatcher would be named the writer of everything")
        checked += 1
        # DEFECT 2 — LIFT buried the real engine for being frequent. A program that runs in
        # nearly every slot the class changes and rarely otherwise is the ENGINE, and must
        # score HIGH. Lift capped it at 1.19 and a 1.5 threshold deleted it.
        engine = a8_phi(89, 2, 2, 15)
        if engine < 0.5:
            failures.append(f"A8 an engine covering nearly every change slot scored "
                            f"{engine:.2f} — frequency is being punished again")
        checked += 1
        # a program that runs only when the class does NOT change is negative association
        if a8_phi(0, 40, 40, 28) >= 0:
            failures.append("A8 anti-correlated program must score negative")
        checked += 1
        # INVARIANT: an empty transaction code is a POINTER, not a gap. When the writes carry
        # no tcode and a dispatcher is among the top associates, the channel is INTERFACE —
        # a BAPI/RFC whose design never set one. Reading it as "batch" loses the interface.
        ch, _ = a8_channel({"": 930, "PA30": 70},
                           [{"program": "SAPMSSY1"}, {"program": "HUNCALC0"}])
        if ch != "INTERFACE":
            failures.append(f"A8 channel {ch!r} != 'INTERFACE' — an empty tcode plus a "
                            f"dispatcher is a BAPI/RFC write, not a batch job")
        checked += 1
        ch, _ = a8_channel({"ME22N": 800, "": 200}, [{"program": "RM_MEPO_GUI"}])
        if ch != "DIALOG":
            failures.append(f"A8 channel {ch!r} != 'DIALOG' when most changes carry a tcode")
        checked += 1
        ch, _ = a8_channel({"": 950}, [{"program": "HUNCALC0"}, {"program": "RHHCP_DC_EMPLOYEE"}])
        if ch != "PROGRAM":
            failures.append(f"A8 channel {ch!r} != 'PROGRAM' when no tcode and named programs "
                            f"lead — that is a report or engine writing directly")

    print(f"[algorithm validation] {checked} golden cases")
    if failures:
        print(f"  {len(failures)} REGRESSION(S):", file=sys.stderr)
        for f in failures:
            print("    " + f, file=sys.stderr)
        print("\nEvery case here is a real defect found the hard way. A failure means a fix "
              "regressed, not that the case is wrong — check the change, not the expectation.",
              file=sys.stderr)
        sys.exit(1)
    print("  OK — no regressions. Running without error is not validation; these cases are.")


if __name__ == "__main__":
    main()
