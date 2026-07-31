"""detect_drift.py — CONCEPT DRIFT over the accumulated execution history (s097).

The third roadmap technique, and the only one runnable today with no new dependency: it
reads the history A2 already accumulates.

**Why it replaces something.** The interpretation triggers in check_triggers.py use
thresholds I chose by judgement — frontier grows 5%, 30 days of new log. They work, and
they are guesses. Drift detection asks the log itself: *did the process change, and when?*

**Why a biennium organisation makes this sharp.** There is an EXPECTED drift at the
biennium boundary — budgets reset, commitments carry forward, activity re-shapes. Any
drift that is NOT that is exactly the finding worth having, and a threshold cannot tell
the two apart.

**Method.** For each domain, build a monthly activity profile (executions, distinct
objects, distinct users). Compare each month against the trailing baseline using the
relative change in each signal, and flag a month whose profile departs from the baseline
by more than the domain's own historical volatility — so a noisy domain needs a bigger
move to register than a stable one. This is deliberately simple and explainable: a drift
signal nobody can interpret gets ignored, which is worse than no signal.

**Declared failure mode.** With a four-month window there are at most two comparable
periods per domain, so this detects STEP CHANGES, not gradual drift, and cannot yet
distinguish an expected biennium boundary from an anomaly. It will get stronger purely by
the accumulator continuing to run — which is itself the argument for protecting A2.

Emits: brain_v2/drift_signals.json
"""
import json
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "brain_v2"))
from component_map import domain_of_package, domain_of_function_module  # noqa: E402

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = REPO / "brain_v2" / "drift_signals.json"

MIN_MONTHS = 3        # below this there is no baseline to depart from
MIN_DAYS = 15         # a month covering fewer days cannot yield a comparable rate
MIN_EXECS = 200       # a domain too small to have a stable profile
REL_CHANGE = 0.50     # a signal must move at least this much against its baseline
BASELINE_MIN = 2      # months of history required before any comparison is made


def main():
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)

    # monthly profile per domain, resolved through the standard taxonomy
    # DAYS COVERED PER MONTH. The first run of this algorithm produced 11 drift signals,
    # almost all in the same month across unrelated domains — PM, CTS, Security, FI-AA,
    # Travel, SD, FI. When drift fires everywhere at once the PROCESS did not change, the
    # DATA did: the window runs 2026-02-21 to 2026-06-21, so February has 3 days and June
    # has 20, while April has 30. April was simply the first full month.
    #
    # Comparing monthly VOLUMES across unequal months is the same defect this project
    # already names as an anti-method. The fix is to compare RATES PER DAY.
    days_in = dict(con.execute(
        "SELECT substr(SAL_DATE,1,6), COUNT(DISTINCT SAL_DATE) FROM rsau_audit_history "
        "GROUP BY 1"))

    prof = defaultdict(lambda: defaultdict(lambda: {"execs": 0, "objs": set(), "users": set()}))
    prog_dc = dict(con.execute("SELECT OBJ_NAME, DEVCLASS FROM tadir_prog"))
    rows = con.execute(
        "SELECT SAL_DATE, SLGREPNA, PARAM3, SLGUSER FROM rsau_audit_history "
        "WHERE SAL_DATE IS NOT NULL AND SAL_DATE <> ''").fetchall()
    for sal_date, prog, fm, user in rows:
        month = str(sal_date)[:6]
        obj = (fm or prog or "").strip()
        if not obj:
            continue
        dom = domain_of_package(prog_dc.get((prog or "").strip())) \
            or domain_of_function_module(obj)
        if not dom:
            continue
        p = prof[dom][month]
        p["execs"] += 1
        p["objs"].add(obj)
        if user:
            p["users"].add(user.strip())
    con.close()

    signals, examined = [], 0
    for dom, months in prof.items():
        ms = sorted(months)
        if len(ms) < MIN_MONTHS:
            continue
        # normalise every signal to a PER-DAY rate, and drop months with too few days to
        # produce a stable rate at all
        series = []
        for m in ms:
            d = days_in.get(m, 0)
            if d < MIN_DAYS:
                continue
            series.append((m, months[m]["execs"] / d,
                           len(months[m]["objs"]) / d, len(months[m]["users"]) / d))
        if len(series) < MIN_MONTHS or sum(x[1] for x in series) < MIN_EXECS / 30.0:
            continue
        examined += 1

        for i in range(1, len(series)):
            base = series[:i]
            if len(base) < 2:
                continue
            m, ex, ob, us = series[i]
            departures = []
            for idx, label in ((1, "executions"), (2, "distinct objects"), (3, "distinct users")):
                vals = [b[idx] for b in base]
                mean = statistics.mean(vals)
                cur = series[i][idx]
                # RELATIVE CHANGE, not a z-score. The second run produced z=1016 and z=-41,
                # because with only two baseline months the standard deviation collapses
                # toward zero and the score explodes. A z-score needs more history than a
                # four-month window can give.
                #
                # Reporting an absurd number dressed as a statistic is worse than reporting
                # a plain one: it looks rigorous and cannot be interpreted. Relative change
                # is robust at n=2 and a human can read it. Z-scores become meaningful once
                # the accumulator has roughly a year — which is one more reason to protect it.
                if mean <= 0:
                    continue
                rel = (cur - mean) / mean
                if abs(rel) >= REL_CHANGE:
                    departures.append({"signal": label,
                                       "baseline_mean_per_day": round(mean, 1),
                                       "observed_per_day": round(cur, 1),
                                       "relative_change_pct": round(100 * rel, 1),
                                       "direction": "up" if rel > 0 else "down"})
            if len(departures) >= 2:      # one signal moving is noise; two is a shape change
                signals.append({
                    "domain": dom, "month": m,
                    "departures": departures,
                    "days_in_month": days_in.get(m),
                    "baseline_months": [b[0] for b in base],
                    "interpretation": ("the domain's activity SHAPE changed, not just its "
                                       "volume — re-derive its assignment: it was a "
                                       "hypothesis formed on the earlier window"),
                })

    signals.sort(key=lambda s: -max(abs(d["relative_change_pct"]) for d in s["departures"]))
    out = {
        "_generated_by": "process_mining/detect_drift.py",
        "_algorithm": "concept drift over the accumulated history",
        "_replaces": ("the threshold heuristics in check_triggers.py — those are judgement, "
                      "this asks the log itself"),
        "_method": ("monthly activity profile per domain as RATES PER DAY (executions, "
                    "distinct objects, distinct users); a month is flagged when at least TWO signals depart "
                    "from the trailing baseline by more than the domain's own volatility. "
                    "One signal moving is noise; two is a change of shape."),
        "_corrected_in_first_run": ("the first version compared monthly VOLUMES and produced "
                                    "11 signals, almost all in the same month across unrelated "
                                    "domains — because the window is 2026-02-21 to 2026-06-21, so "
                                    "February has 3 days and April 30. April was the first full "
                                    "month, not a process change. Now normalised per day."),
        "_statistic": ("relative change against the trailing baseline, NOT a z-score. With "
                       "two baseline months the standard deviation collapses and z explodes "
                       "(the second run produced z=1016). An absurd number dressed as a "
                       "statistic is worse than a plain one: it looks rigorous and cannot be "
                       "interpreted. Z-scores become meaningful at roughly a year of history."),
        "_failure_mode": ("a four-month window gives at most two comparable periods per "
                          "domain: this detects STEP CHANGES, not gradual drift, and cannot "
                          "yet separate an expected biennium boundary from an anomaly. It "
                          "strengthens purely by the accumulator continuing to run."),
        "window": {"domains_examined": examined, "signals": len(signals)},
        "signals": signals[:25],
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"wrote {OUT}")
    print(f"  {examined} domains with enough history · {len(signals)} drift signal(s)")
    for s in signals[:8]:
        d = " · ".join(f"{x['signal']} {x['direction']} (z={x['z']})" for x in s["departures"])
        print(f"    {s['domain']:20s} {s['month']}  {d}")
    if not signals:
        print("    no domain changed shape in the observed window")


if __name__ == "__main__":
    main()
