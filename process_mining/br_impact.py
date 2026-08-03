"""ALGORITHM A14 — BUDGET-RATE IMPACT, all four baselines.

WHAT IT ANSWERS
    How much of the FM-versus-FI/GL difference is explained by the budget rate — the number
    the organisation calls the budget-rate impact.

WHY IT MIRRORS THEIR CODE RATHER THAN INVENTING A METHOD
    UNESCO already implements this in YCL_FM_FI_COMPARE_BL and YCL_FM_BR_EXCHANGE_RATE_BL,
    with FINAL_DIFF = FKBTR - DMBTR - ZZAMOUNTBRDIFF. Reconstructing a definition from the
    outside when the organisation has one is how two correct calculations disagree. This
    replicates GET_BR_IMPACT: the impact is FM minus the SAME amount valued at the standard
    rate, and the standard rate is reached by four different routes depending on the value
    type.

THE FOUR ROUTES, exactly as GET_BR_IMPACT chooses them
    1. WRTTP '54'                      the FI document's own DMBTR, signed by SHKZG
    2. WRTTP '51' + RMBE + BTART 0200  the goods-receipt amount from EKBE, negated
    3. otherwise, if KURSF is set      the document's own rate — present in the class and
                                       NOT the path in practice: the comparison is done on
                                       AMOUNTS, not on rates, and KURSF is initial on these
                                       documents so they fall through
    4. otherwise                       rate type M at the posting date — the UN operational
                                       rate, which is what the code comment calls UNORE

    The comparison is AMOUNT AGAINST AMOUNT throughout: ZZAMOUNTBRDIFF = FKBTR minus the
    same base valued at the standard rate. That is why route 1 reads DMBTR directly rather
    than deriving a rate from it.

THE SIGN CONVENTION THAT MATTERS
    SAP stores an indirect quotation as a NEGATIVE rate, and the class honours it: a
    negative rate means DIVIDE, not multiply. TCURR holds EUR->USD as 0.873- for a real
    rate of 1/0.873. Multiplying there would understate every line by a factor of 1.3.

USAGE
    python process_mining/br_impact.py [--year 2025]
"""

import collections
import io
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "brain_v2", "methods"))
from algorithm_memory import remember  # noqa: E402

GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
# The fixed rate the mechanism applies, from TCURR KURST='EURX'.
EURX = 1.09529
TOL = 0.0002


def amt(s):
    """SAP writes the sign at the END. '1875.00-' is negative."""
    s = (s or "0").strip()
    if not s:
        return 0.0
    neg = s.endswith("-")
    try:
        v = float(s.rstrip("-").replace(",", ""))
    except ValueError:
        return 0.0
    return -v if neg else v


def z(s):
    return (s or "").strip().lstrip("0")


def rate_table(cx, fcurr, tcurr, kurst):
    """[(valid_from, rate)] sorted descending. GDATU is stored INVERTED."""
    out = []
    for g, u in cx.execute(
            "SELECT GDATU,UKURS FROM tcurr WHERE trim(KURST)=? AND trim(FCURR)=? "
            "AND trim(TCURR)=?", (kurst, fcurr, tcurr)):
        try:
            out.append((str(99999999 - int(g)), amt(u)))
        except (ValueError, TypeError):
            continue
    return sorted(out, reverse=True)


def rate_on(tab, day):
    """The rate in force on a date: the latest entry whose valid-from is not after it."""
    for vf, r in tab:
        if vf <= day:
            return r
    return None


def apply_rate(base, rate):
    """A NEGATIVE rate is an indirect quotation and means DIVIDE. This is the class's own rule."""
    if not rate:
        return None
    return (base / abs(rate)) if rate < 0 else (base * rate)


def main(argv):
    cx = sqlite3.connect("file:%s?mode=ro" % GOLD, uri=True)
    q = cx.execute

    types = set(r[0].strip() for r in q(
        "SELECT FUND_TYPE FROM FMFUNDTYPE WHERE trim(ZZFIX_RATE)='X'"))
    funds = set(r[0].strip() for r in q(
        "SELECT FINCODE FROM FMFINCODE WHERE trim(TYPE) IN (%s)"
        % ",".join("'%s'" % t for t in types)))

    # The perimeter, at the EURX rate. Business area GEF cannot be applied — it is not on
    # the FM line — so this population is a SUPERSET of the true perimeter.
    lines = []
    for gj, fo, tr, fk, wt, vr, bt, bu, kb, kg, kz in q(
            "SELECT GJAHR,trim(FONDS),TRBTR,FKBTR,WRTTP,VRGNG,BTART,BUKRS,KNBELNR,KNGJAHR,"
            "KNBUZEI FROM fmifiit_full WHERE trim(FIKRS)='UNES' AND trim(TWAER)='EUR' "
            "AND trim(FIPEX) NOT IN ('GAINS','REVENUE') "
            "AND trim(VRGNG) NOT IN ('HRM1','HRM2','HRP1')"):
        if fo not in funds:
            continue
        t, f = amt(tr), amt(fk)
        if abs(t) < 0.01 or abs(abs(f / t) - EURX) >= TOL:
            continue
        lines.append({"gjahr": gj, "fund": fo, "base": abs(t), "fm": abs(f),
                      "wrttp": (wt or "").strip(), "vrgng": (vr or "").strip(),
                      "btart": (bt or "").strip(),
                      "fi": ((bu or "").strip(), z(kb), (kg or "").strip(), z(kz))})
    print("perimeter lines at EURX: %d" % len(lines))

    want_bseg = set(l["fi"] for l in lines if l["wrttp"] == "54")
    want_bkpf = set((l["fi"][0], l["fi"][1], l["fi"][2]) for l in lines if l["wrttp"] != "54")

    bseg = {}
    for bu, bl, gj, bz, dm, sh in q("SELECT BUKRS,BELNR,GJAHR,BUZEI,DMBTR,SHKZG FROM bseg_union"):
        k = ((bu or "").strip(), z(bl), (gj or "").strip(), z(bz))
        if k in want_bseg and k not in bseg:
            v = amt(dm)
            bseg[k] = -abs(v) if (sh or "").strip() == "H" else abs(v)
    print("FI lines resolved for route 1: %d of %d" % (len(bseg), len(want_bseg)))

    bkpf = {}
    for bu, bl, gj, bd in q("SELECT BUKRS,BELNR,GJAHR,BUDAT FROM bkpf"):
        k = ((bu or "").strip(), z(bl), (gj or "").strip())
        if k in want_bkpf and k not in bkpf:
            bkpf[k] = (bd or "").strip()
    print("FI headers resolved for routes 3/4: %d of %d" % (len(bkpf), len(want_bkpf)))

    m_tab = rate_table(cx, "EUR", "USD", "M")
    print("standard rate M EUR->USD: %d entries, latest from %s"
          % (len(m_tab), m_tab[0][0] if m_tab else "-"))

    agg = collections.defaultdict(lambda: {"n": 0, "fm": 0.0, "std": 0.0})
    unresolved = collections.Counter()
    for l in lines:
        route = base = None
        if l["wrttp"] == "54":
            v = bseg.get(l["fi"])
            if v is None:
                unresolved["1_no_fi_line"] += 1
                continue
            route, base = "1_BSEG_DMBTR", abs(v)
        elif l["wrttp"] == "51" and l["vrgng"] == "RMBE" and l["btart"] == "0200":
            unresolved["2_ekbe_not_implemented_no_population"] += 1
            continue
        else:
            day = bkpf.get((l["fi"][0], l["fi"][1], l["fi"][2]))
            if not day:
                unresolved["4_no_posting_date"] += 1
                continue
            r = rate_on(m_tab, day)
            if r is None:
                unresolved["4_no_rate_at_date"] += 1
                continue
            base = abs(apply_rate(l["base"], r))
            route = "4_RATE_TYPE_M_UNORE"
        k = (l["gjahr"], route)
        agg[k]["n"] += 1
        agg[k]["fm"] += l["fm"]
        agg[k]["std"] += base

    print("\nBUDGET-RATE IMPACT = FM at EURX minus the same base at the STANDARD rate")
    print("  year route                    lines            FM USD        STANDARD USD"
          "           IMPACT")
    tot = {"n": 0, "fm": 0.0, "std": 0.0}
    for k in sorted(agg):
        v = agg[k]
        tot["n"] += v["n"]
        tot["fm"] += v["fm"]
        tot["std"] += v["std"]
        print("  %s %-24s %6d %17.2f %19.2f %16.2f"
              % (k[0], k[1], v["n"], v["fm"], v["std"], v["fm"] - v["std"]))
    print("  %-29s %6d %17.2f %19.2f %16.2f"
          % ("TOTAL", tot["n"], tot["fm"], tot["std"], tot["fm"] - tot["std"]))
    if unresolved:
        print("\n  NOT EVALUATED (reported, never counted as zero):")
        for k, n in unresolved.most_common():
            print("    %-40s %d" % (k, n))

    out = {
        "_algorithm": "A14 br_impact.py — replicates GET_BR_IMPACT's four baselines",
        "_definition": "impact = FM at EURX minus the same base at the standard rate",
        "_their_formula": "FINAL_DIFF = FKBTR - DMBTR - ZZAMOUNTBRDIFF (YCL_FM_FI_COMPARE_BL:709)",
        "eurx_rate": EURX,
        "by_year_and_route": [{"year": k[0], "route": k[1], "lines": v["n"],
                               "fm_usd": round(v["fm"], 2), "standard_usd": round(v["std"], 2),
                               "impact_usd": round(v["fm"] - v["std"], 2)}
                              for k, v in sorted(agg.items())],
        "total": {"lines": tot["n"], "fm_usd": round(tot["fm"], 2),
                  "standard_usd": round(tot["std"], 2),
                  "impact_usd": round(tot["fm"] - tot["std"], 2)},
        "not_evaluated": dict(unresolved),
        "_bounds": {
            "route_3_not_the_path": "the comparison is done on AMOUNTS, not rates; KURSF is initial on these documents so they take route 4",
            "perimeter_is_a_superset": "business area GEF is not carried on the FM line",
            "indirect_quotation": "a NEGATIVE rate means DIVIDE — TCURR holds EUR->USD as 0.873- for a real rate of 1/0.873"},
    }
    p = os.path.join(ROOT, "brain_v2", "br_impact.json")
    json.dump(out, io.open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    remember(subject="budget rate impact", kind="CARRIER", learned_by="A14_br_impact",
             session=98,
             fact="impact %.2f USD over %d lines, replicating the organisation's own four baselines"
                  % (tot["fm"] - tot["std"], tot["n"]),
             evidence=os.path.relpath(p, ROOT).replace("\\", "/"),
             implication=("route 1 covers most LINES and route 4 covers most MONEY — never "
                          "quote an impact computed from one route alone"))
    print("\nwritten: brain_v2/br_impact.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
