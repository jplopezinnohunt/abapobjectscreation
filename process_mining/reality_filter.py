"""ALGORITHM A18 — THE REALITY FILTER.

WHAT IT ANSWERS
    How far apart are what the system RECORDS and what actually HAPPENED — in both
    directions:

    BACKWARD  which recorded rows never became real. Simulations, test runs, reversed and
              parked documents all sit in operational tables looking exactly like the real
              thing, because they ARE the real thing minus the last step.

    FORWARD   which configured entries never produce anything. Wage types, rules, sets and
              symbolic accounts that exist in customising and appear in no document.

    They are the same question from two ends, which is why they belong in one algorithm: the
    distance between the model and the world.

WHY IT EXISTS, AND IT IS NOT A HYPOTHETICAL
    Session 98 measured the staff budget-rate impact at USD 20.5 million. The real figure is
    USD 1.98 million. The other 90% was SIMULATION RUNS — 1,828 of 2,316 payroll posting runs
    that never reached accounting, holding documents with the same numbers, the same amounts
    and the same account assignments as the real ones. Nothing in the row said which was
    which.

    In the same session and the same subject, the mirror error: 72 'Constant Dollar' wage
    types, all configured, all identically set up, described as THE mechanism. Zero of them
    post. One undescribed wage type carries the whole thing.

    Both errors were confident, both were evidenced, and both were wrong in the same way.
    That is what makes this an algorithm rather than a lesson.

THE TWO SIGNALS IT IS BUILT ON
    A SUSPICIOUSLY UNIFORM RATIO across unrelated groupings means a filter is missing from
    the query, not that the data is strange. The payroll-to-FI ratio was 10-14% in every
    company code, every document type and every month of three different years. An incidental
    gap varies; a systematic one does not.

    WHOLE-OR-NOTHING AT THE PROCESS UNIT is what identifies the right unit. Grouped by
    document the cut looked like attrition; grouped by RUN, 488 were entirely present and
    1,828 entirely absent, and not one was partial. When a grouping makes the partials
    disappear, that grouping is the unit the process actually works in.

WHAT IT DOES NOT DO
    It does not decide what to delete. It reports the distance and names the discriminator;
    purging is a separate, deliberate act with its own script.

    And it refuses to apply a discriminator outside the window where the EVIDENCE table has
    coverage — the check that stopped session 98 from destroying every pre-2024 payroll run
    as if it were a simulation, because BKPF in the golden starts at 2024.

USAGE
    python process_mining/reality_filter.py [--spec reality_spec.json] [--out report.json]
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
from algorithm_memory import recall, remember  # noqa: E402

GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
SPEC = os.path.join(HERE, "reality_spec.json")
# Below this spread, a ratio is "the same everywhere" and therefore systematic.
UNIFORM_SPREAD = 0.06


def q1(cx, sql, args=()):
    r = cx.execute(sql, args).fetchone()
    return r[0] if r else None


def table_exists(cx, t):
    """Case-INSENSITIVE on purpose: the golden holds both conventions.

    Tables loaded by load_wide_tables.py keep their uppercase SAP names (PPDHD, FMIOI,
    PPOIX) while older extracts are lowercase (bkpf, fmifiit_full). An exact-match check
    reported every one of this algorithm's probes as 'not in the golden' on its first run —
    a silent SKIP, which is the worst possible failure for a tool whose whole job is to
    notice what is missing. SQLite resolves the name case-insensitively in the query itself,
    so only the existence check needed fixing.
    """
    return q1(cx, "select count(*) from sqlite_master where lower(name)=lower(?) "
                  "and type in ('table','view')", (t,)) > 0


def backward(cx, p):
    """Which recorded rows never became real — and at which unit is the cut clean?"""
    d, u = p["detail"], p["unit"]
    ev, ek, ef = p["evidence"], p["evidence_key"], p.get("evidence_where")
    link = p["detail_key"]
    for t in (d, ev):
        if not table_exists(cx, t):
            return {"skipped": "%s not in the golden" % t}
    where = (" AND " + ef) if ef else ""
    out = {"detail": d, "unit": u, "evidence": ev}

    # The COVERAGE GUARD comes first. A discriminator is only meaningful where its evidence
    # table has data; outside that window every row looks unreal, and acting on it destroys
    # good data. This check is the reason the algorithm exists as code and not as a habit.
    g = p.get("coverage_guard")
    if g:
        span = cx.execute('select min(%s), max(%s) from "%s"' % (g["column"], g["column"], ev)
                          ).fetchone()
        out["evidence_coverage"] = {"column": g["column"], "from": span[0], "to": span[1]}
        out["_guard"] = ("this verdict is ONLY valid where %s has coverage. Applying it "
                         "outside that window marks real records as unreal" % ev)

    total = q1(cx, 'select count(distinct "%s") from "%s"' % (u, d))
    real = q1(cx, 'select count(distinct t."%s") from "%s" t join "%s" e on e."%s"=t."%s"%s'
              % (u, d, ev, ek, link, where))
    out["units_total"], out["units_real"] = total, real
    out["pct_real"] = round(100.0 * real / total, 1) if total else None

    # Is the cut clean at this unit? If some units are partly evidenced, the unit is wrong.
    rows = cx.execute(
        'select t."%s", count(*) n, sum(case when e."%s" is not null then 1 else 0 end) r '
        'from "%s" t left join "%s" e on e."%s"=t."%s"%s group by t."%s"'
        % (u, ek, d, ev, ek, link, where, u)).fetchall()
    whole = sum(1 for _, n, r in rows if r == n and n)
    none_ = sum(1 for _, n, r in rows if r == 0)
    part = len(rows) - whole - none_
    out["at_this_unit"] = {"wholly_real": whole, "wholly_absent": none_, "partial": part}
    out["_verdict"] = (
        "CLEAN CUT — the unit is right, and the absent ones are a KIND of record rather than "
        "a failure" if part == 0 else
        "NOT THE UNIT — %d units are partly evidenced, so the real process unit is finer or "
        "coarser than %s" % (part, u))

    # The uniformity signal, measured rather than eyeballed.
    for gcol in p.get("uniformity_over") or []:
        try:
            gr = cx.execute(
                'select t."%s" g, count(distinct t."%s") n, '
                'count(distinct case when e."%s" is not null then t."%s" end) r '
                'from "%s" t left join "%s" e on e."%s"=t."%s"%s group by g having n>20'
                % (gcol, u, ek, u, d, ev, ek, link, where)).fetchall()
        except sqlite3.Error:
            continue
        if len(gr) < 2:
            continue
        pcts = [r / float(n) for _, n, r in gr if n]
        spread = max(pcts) - min(pcts)
        out.setdefault("uniformity", {})[gcol] = {
            "groups": len(gr), "min": round(min(pcts), 3), "max": round(max(pcts), 3),
            "spread": round(spread, 3),
            "_reading": ("SYSTEMATIC — the same ratio everywhere means a filter is missing "
                         "from the query, not that the data is odd" if spread < UNIFORM_SPREAD
                         else "varies by group, so it is not one systematic filter")}
    return out


def backward_flag(cx, p):
    """The second shape of 'never became real': the row's OWN flag says so.

    Not every unreal record needs a second table to expose it. A commitment carries a
    deletion and a completion indicator; a reversed FI document points at its reversal.
    Those are cheaper to check than a join and just as easy to forget in a SUM — which is
    the only thing that matters here.
    """
    d = p["detail"]
    if not table_exists(cx, d):
        return {"skipped": "%s not in the golden" % d}
    total = q1(cx, 'select count(*) from "%s"' % d)
    out = {"detail": d, "rows": total, "flags": {}}
    unreal = []
    for f in p["flags"]:
        col, test, why = f["column"], f["means_unreal"], f.get("_why", "")
        try:
            n = q1(cx, 'select count(*) from "%s" where %s' % (d, test))
        except sqlite3.Error as e:
            out["flags"][col] = {"error": str(e)[:70]}
            continue
        kind = f.get("meaning", "NEVER_REAL")
        out["flags"][col] = {"rows": n, "pct": round(100.0 * n / total, 1) if total else None,
                             "_means": why, "meaning": kind}
        # ONLY never-real rows invalidate a sum of what happened. A completed commitment is
        # the most real kind of record there is — it became an actual. Folding it in with
        # simulations was the mistake this distinction exists to prevent, and it would have
        # thrown away a correct figure rather than saved a wrong one.
        if n and kind == "NEVER_REAL":
            unreal.append(test)
    out["_reading"] = ("'never real' is what invalidates a sum of WHAT HAPPENED. "
                       "'no longer live' only invalidates a sum of WHAT IS OUTSTANDING")
    if unreal:
        out["any_flag_set"] = q1(cx, 'select count(*) from "%s" where %s'
                                 % (d, " or ".join("(%s)" % t for t in unreal)))
        out["pct_unreal"] = round(100.0 * out["any_flag_set"] / total, 1) if total else None
    else:
        out["any_flag_set"], out["pct_unreal"] = 0, 0.0
    return out


def forward(cx, p):
    """Which configured entries never appear in a document — designed but dormant."""
    cfg, ck, doc, dk = p["config"], p["config_key"], p["document"], p["document_key"]
    for t in (cfg, doc):
        if not table_exists(cx, t):
            return {"skipped": "%s not in the golden" % t}
    cw = (" where " + p["config_where"]) if p.get("config_where") else ""
    keys = [r[0] for r in cx.execute('select distinct "%s" from "%s"%s' % (ck, cfg, cw))]
    if not keys:
        return {"config": cfg, "skipped": "no configured entries matched"}
    used = set()
    # Pull the document side ONCE and intersect in Python. A NOT IN against a big table per
    # key is the correlated-subquery trap (D6) and turns a second into an hour.
    for r in cx.execute('select distinct "%s" from "%s"' % (dk, doc)):
        used.add(r[0])
    dormant = [k for k in keys if k not in used]
    return {"config": cfg, "document": doc, "configured": len(keys),
            "dormant": len(dormant), "pct_dormant": round(100.0 * len(dormant) / len(keys), 1),
            "examples": sorted(dormant)[:15],
            # DORMANT IS RELATIVE TO WHAT THE DOCUMENT TABLE HOLDS, and saying so is not a
            # footnote. ppoix in this golden covers 2026 and posted runs only, so "dormant"
            # here means "unused in that window" — not "never used". Reporting 82% dormant
            # without that sentence would be the same class of overstatement this algorithm
            # was written to catch.
            "_window": p.get("document_covers") or
                       "UNSTATED — the spec does not say what %s covers, so read the "
                       "percentage as 'unused within whatever is loaded'" % doc,
            "_reading": ("configured entries that produce nothing. Pre-built capacity a future "
                         "design could use — or evidence that the mechanism described in the "
                         "configuration is NOT the mechanism that runs")}


def main(argv):
    spec = json.load(io.open(argv[argv.index("--spec") + 1] if "--spec" in argv else SPEC,
                             encoding="utf-8"))
    cx = sqlite3.connect("file:%s?mode=ro" % GOLD.replace("\\", "/"), uri=True)
    known = recall(kind="TRAP") or []
    print("A18 REALITY FILTER — la distancia entre lo registrado y lo ocurrido")
    print("=" * 74)
    print("   %d trampas ya conocidas por otros algoritmos consultadas" % len(known))

    rep = {"_algorithm": "A18 reality_filter.py", "backward": [], "backward_flag": [],
           "forward": []}
    print("\nHACIA ATRAS — filas registradas que nunca ocurrieron")
    for p in spec.get("backward") or []:
        r = backward(cx, p)
        rep["backward"].append(r)
        if r.get("skipped"):
            print("   %-14s omitido: %s" % (p["detail"], r["skipped"]))
            continue
        print("   %-14s %s reales de %s (%s%%)  %s"
              % (p["detail"], r["units_real"], r["units_total"], r["pct_real"],
                 r["_verdict"].split(" —")[0]))
        for g, u in (r.get("uniformity") or {}).items():
            if u["spread"] < UNIFORM_SPREAD:
                print("      ratio uniforme sobre %s (%d grupos, dispersion %.3f) -> "
                      "FALTA UN FILTRO" % (g, u["groups"], u["spread"]))

    print("\nHACIA ATRAS (bandera) — filas que su propio indicador declara no vivas")
    for p in spec.get("backward_flag") or []:
        r = backward_flag(cx, p)
        rep["backward_flag"].append(r)
        if r.get("skipped"):
            print("   %-14s omitido: %s" % (p["detail"], r["skipped"]))
            continue
        print("   %-14s %d filas, %d NUNCA REALES (%s%%)"
              % (r["detail"], r["rows"], r["any_flag_set"], r["pct_unreal"]))
        for col, v in r["flags"].items():
            if v.get("rows"):
                print("      %-10s %8d (%s%%)  [%s] %s"
                      % (col, v["rows"], v["pct"], v.get("meaning", "?"), v["_means"]))
            elif v.get("error"):
                print("      %-10s no medible: %s" % (col, v["error"]))

    print("\nHACIA DELANTE — configuracion que no produce nada")
    for p in spec.get("forward") or []:
        r = forward(cx, p)
        rep["forward"].append(r)
        if r.get("skipped"):
            print("   %-14s omitido: %s" % (p["config"], r["skipped"]))
            continue
        print("   %-14s %d configurados, %d DORMIDOS (%s%%)  %s"
              % (p["config"], r["configured"], r["dormant"], r["pct_dormant"],
                 ", ".join(r["examples"][:6])))
        print("      ventana: %s" % r["_window"])

    out = argv[argv.index("--out") + 1] if "--out" in argv else \
        os.path.join(ROOT, "brain_v2", "reality_filter.json")
    json.dump(rep, io.open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\nescrito: %s" % os.path.relpath(out, ROOT))

    for r in rep["backward"]:
        if r.get("pct_real") is not None and r["pct_real"] < 90:
            remember(subject=r["detail"], kind="TRAP", learned_by="A18_reality_filter",
                     session=spec.get("session", 0),
                     fact=("only %s%% of %s in %s are evidenced in %s — the rest are recorded "
                           "but never happened"
                           % (r["pct_real"], r["unit"], r["detail"], r["evidence"])),
                     evidence="A18: %d wholly real, %d wholly absent, %d partial"
                              % (r["at_this_unit"]["wholly_real"],
                                 r["at_this_unit"]["wholly_absent"],
                                 r["at_this_unit"]["partial"]),
                     implication=("filter through the evidence table before summing anything "
                                  "from %s" % r["detail"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
