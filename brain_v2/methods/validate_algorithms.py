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
