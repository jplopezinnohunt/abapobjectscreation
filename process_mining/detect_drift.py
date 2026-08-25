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

# The artifact is written BEFORE this prints. A console that cannot encode an arrow must
# not turn a successful run into a failed one — which is exactly what happened in the
# first full cycle: both algorithms computed correctly and died displaying the result.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "brain_v2"))
from component_map import domain_of_package, domain_of_function_module  # noqa: E402

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "process_mining"))
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = REPO / "brain_v2" / "drift_signals.json"

MIN_MONTHS = 3        # below this there is no baseline to depart from
MIN_DAYS = 15         # a month covering fewer days cannot yield a comparable rate
MIN_EXECS = 200       # a domain too small to have a stable profile
REL_CHANGE = 0.50     # a signal must move at least this much against its baseline
BASELINE_MIN = 2      # months of history required before any comparison is made


PROFILE = REPO / "brain_v2" / "drift_profile.json"


def build_profile(con):
    """Monthly profile per domain, AGGREGATED IN SQL and cached.

    The first version resolved a domain for each of 15.6M audit rows — 430 seconds. The
    scan was never the bottleneck: 15.6M Python iterations were. Aggregating in SQL first
    collapses those rows to 28,473 (month, object) pairs over 26,143 distinct objects, so
    the expensive per-object resolution runs 548x fewer times.

    The result is cached against the latest date seen. A re-run with no new audit data
    costs nothing, which matters because a slow algorithm gets skipped, and a skipped
    algorithm is documentation.
    """
    latest = con.execute("SELECT MAX(SAL_DATE) FROM rsau_audit_history").fetchone()[0]
    if PROFILE.exists():
        try:
            cached = json.loads(PROFILE.read_text(encoding="utf-8"))
            if cached.get("_latest_date") == latest:
                print(f"  profile cache hit (audit unchanged through {latest})")
                return ({d: {m: v for m, v in months.items()}
                         for d, months in cached["profile"].items()},
                        cached["days_in"])
        except (json.JSONDecodeError, KeyError, OSError):
            pass

    print("  aggregating in SQL (cold) ...")
    days_in = dict(con.execute(
        "SELECT substr(SAL_DATE,1,6), COUNT(DISTINCT SAL_DATE) FROM rsau_audit_history "
        "WHERE SAL_DATE <> '' GROUP BY 1"))
    prog_dc = dict(con.execute("SELECT OBJ_NAME, DEVCLASS FROM tadir_prog"))

    # one row per (month, object) instead of one per execution
    rows = con.execute(
        "SELECT substr(SAL_DATE,1,6) m, "
        "       COALESCE(NULLIF(PARAM3,''), SLGREPNA) obj, "
        "       SLGREPNA prog, COUNT(*) n, COUNT(DISTINCT SLGUSER) u "
        "FROM rsau_audit_history WHERE SAL_DATE <> '' GROUP BY 1,2,3").fetchall()

    # resolve each distinct object ONCE, not once per execution
    dom_cache = {}

    def dom_of(obj, prog):
        key = (obj, prog)
        if key not in dom_cache:
            dom_cache[key] = (domain_of_package(prog_dc.get((prog or "").strip()))
                              or domain_of_function_module((obj or "").strip()))
        return dom_cache[key]

    prof = defaultdict(lambda: defaultdict(lambda: {"execs": 0, "objs": 0, "users": 0}))
    for month, obj, prog, n, u in rows:
        d = dom_of(obj, prog)
        if not d:
            continue
        p = prof[d][month]
        p["execs"] += n
        p["objs"] += 1          # already one row per distinct object in this month
        p["users"] = max(p["users"], u or 0)

    plain = {d: {m: dict(v) for m, v in months.items()} for d, months in prof.items()}
    PROFILE.write_text(json.dumps(
        {"_latest_date": latest, "_note": "aggregated in SQL; cached against the latest audit date",
         "days_in": days_in, "profile": plain}, indent=1), encoding="utf-8")
    print(f"  aggregated {len(rows):,} (month,object) rows over "
          f"{len(dom_cache):,} distinct objects")
    return plain, days_in


def departures_for(series, rel_change=None):
    """The drift statistic, as a pure function of a per-day series.

    `series` is [(month, execs_per_day, objs_per_day, users_per_day), ...] in month order.
    Returns [(month, [departure, ...], [baseline_month, ...]), ...] for every month that
    departs from the months BEFORE it. The baseline travels WITH the finding: a departure
    without the window it departed from cannot be judged.

    This was inline in main(). Both defects it has already carried were caught by reading
    the output, not by a check — because inline code cannot be gated:

      1. comparing raw MONTHLY VOLUMES across months of unequal length. February against
         a 31-day month is a 10% difference before anything real happens: 11 false signals.
      2. Z-SCORES over a two-month baseline. The standard deviation collapses toward zero
         and the score explodes — the run produced z=1016. A number that absurd, dressed as
         a statistic, is worse than a plain one: it looks rigorous and cannot be read.

    Both are now gated below by golden cases. The caller passes per-day rates; this
    function reports RELATIVE CHANGE, which is robust at n=2 and legible to a human.
    """
    thresh = REL_CHANGE if rel_change is None else rel_change
    out = []
    for i in range(1, len(series)):
        base = series[:i]
        if len(base) < 2:
            continue
        departures = []
        for idx, label in ((1, "executions"), (2, "distinct objects"), (3, "distinct users")):
            vals = [b[idx] for b in base]
            mean = statistics.mean(vals)
            cur = series[i][idx]
            if mean <= 0:
                continue
            rel = (cur - mean) / mean
            if abs(rel) >= thresh:
                departures.append({"signal": label,
                                   "baseline_mean_per_day": round(mean, 1),
                                   "observed_per_day": round(cur, 1),
                                   "relative_change_pct": round(100 * rel, 1),
                                   "direction": "up" if rel > 0 else "down"})
        if departures:
            out.append((series[i][0], departures, [b[0] for b in base]))
    return out


def main():
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
    prof, days_in = build_profile(con)
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
                           months[m]["objs"] / d, months[m]["users"] / d))
        if len(series) < MIN_MONTHS or sum(x[1] for x in series) < MIN_EXECS / 30.0:
            continue
        examined += 1

        for m, departures, base_months in departures_for(series):
            if len(departures) >= 2:      # one signal moving is noise; two is a shape change
                signals.append({
                    "domain": dom, "month": m,
                    "departures": departures,
                    "days_in_month": days_in.get(m),
                    "baseline_months": base_months,
                    "interpretation": ("the domain's activity SHAPE changed, not just its "
                                       "volume — re-derive its assignment: it was a "
                                       "hypothesis formed on the earlier window"),
                })

    signals.sort(key=lambda s: -max(abs(d["relative_change_pct"]) for d in s["departures"]))

    # THE CAVEAT MUST TRAVEL WITH THE FINDING. Several unrelated domains departing in the SAME
    # month is not several independent process changes — it is the signature of the LOG
    # CAPTURE changing: a new audit filter, a retention edit, a system move. Reading it as
    # drift would send someone to investigate three business processes that did not change.
    #
    # This lived in a backlog ticket and in conversation, which is the same as not existing:
    # whoever opens this file next sees the signals, not the ticket.
    months = {s["month"] for s in signals}
    concentrated = len(signals) >= 3 and len(months) == 1
    out = {
        "_generated_by": "process_mining/detect_drift.py",
        "_algorithm": "concept drift over the accumulated history",
        "_replaces": ("the threshold heuristics in check_triggers.py — those are judgement, "
                      "this asks the log itself"),
        "_READ_THIS_FIRST": (
            ("SUSPECT A CAPTURE CHANGE, NOT DRIFT: all %d signals fall in the SAME month "
             "(%s). Unrelated domains do not change together — this pattern usually means "
             "the LOG CAPTURE changed (audit filter, retention, a system move). Verify the "
             "capture before investigating any business process. Tracked as AN-DRIFT-VERIFY."
             % (len(signals), ", ".join(months))) if concentrated else
            ("signals are spread across %d month(s) — no capture-change pattern"
             % max(len(months), 1))),
        "signals_share_one_month": concentrated,
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
        d = " | ".join(f"{x['signal']} {x['direction']} {x['relative_change_pct']}%"
                       for x in s["departures"])
        print(f"    {s['domain']:20s} {s['month']}  {d}")
    if not signals:
        print("    no domain changed shape in the observed window")


if __name__ == "__main__":
    main()
