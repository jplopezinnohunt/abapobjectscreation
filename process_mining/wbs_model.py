"""ALGORITHM A19 — THE PROJECT / WBS MODEL, AND WHO WRITES IT.

WHAT IT ANSWERS
    What does this installation actually record about a project, who fills it in, and which
    of those fields carry information rather than merely being populated?

WHY IT EXISTS
    The WBS element is where a project meets money: it carries the account assignment every
    posting lands on. Its custom extension is the largest single block of pre-built capacity
    found anywhere in this installation — 31 YYE_* fields — and reading them one at a time
    gives a wrong answer three separate ways.

THE THREE READINGS IT EXISTS TO PREVENT
    1. FILL RATE ALONE LIES. A numeric or NUMC field is never blank — it defaults to zero —
       so a plain "not empty" test reported ten of the 31 as 100% filled when one of them is
       0.45% real. Emptiness depends on the TYPE.
    2. A FLAT RATE HIDES A CURVE. YYE_DONOR sits at 19% overall, which reads as "a field
       nobody adopted". Measured BY CREATION YEAR it is 82% in 2002 falling to 5% in 2026 —
       it was the practice, and something displaced it. A flat low number and a decaying one
       mean opposite things.
    3. POPULATED IS NOT INFORMATIVE. YYE_IMPL_AGENCY is filled on 92% of new elements and
       carries ONE distinct value. A field with a single value has a fill rate and no
       information. Cardinality is the second axis and without it the first is misleading.

    So every field is measured on three axes: fill (type-aware), trend (by creation year),
    and cardinality (distinct values). A field is only understood when all three agree.

WHAT IT ALSO ESTABLISHES
    WHO writes the master, from ERNAM by year — which dates an integration go-live to the day
    without any project document — and whether the identifier GRAMMAR converged when it did,
    which measures what the human hand was costing.

USAGE
    python process_mining/wbs_model.py [--out brain_v2/project_wbs_model.json]
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
OUT = os.path.join(ROOT, "brain_v2", "project_wbs_model.json")

# trim(X,'0.') strips zeros and dots from both ends, so '0.00' and '00000000' collapse to
# empty while '7.00' keeps its 7 and 'X' keeps its X. One expression, both kinds of empty.
NONEMPTY = "\"%s\" IS NOT NULL AND trim(trim(\"%s\"),'0.')<>''"


def shape(s):
    """digits -> D, letters -> A. The grammar of an identifier, from A10."""
    return "".join("D" if c.isdigit() else ("A" if c.isalpha() else "_") for c in s.strip())


def main(argv):
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else OUT
    cx = sqlite3.connect("file:%s?mode=ro" % GOLD.replace("\\", "/"), uri=True)
    cols = [d[0] for d in cx.execute("SELECT * FROM PRPS LIMIT 1").description]
    yy = [c for c in cols if c.startswith(("YYE_", "ZZ"))]
    total = cx.execute("SELECT COUNT(*) FROM PRPS").fetchone()[0]
    print("A19 — MODELO DE PROYECTO / WBS")
    print("=" * 70)
    print("  PRPS: %d elementos PEP, %d campos custom" % (total, len(yy)))

    fields = {}
    for c in yy:
        filled = cx.execute('SELECT COUNT(*) FROM PRPS WHERE ' + NONEMPTY % (c, c)).fetchone()[0]
        distinct = cx.execute('SELECT COUNT(DISTINCT "%s") FROM PRPS WHERE %s'
                              % (c, NONEMPTY % (c, c))).fetchone()[0]
        top = [r[0] for r in cx.execute(
            'SELECT "%s" FROM PRPS WHERE %s GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 5'
            % (c, NONEMPTY % (c, c)))]
        # the trend is the axis a single rate cannot show
        trend = {}
        for y, n, f in cx.execute(
                'SELECT substr(ERDAT,1,4) y, COUNT(*), SUM(CASE WHEN %s THEN 1 ELSE 0 END) '
                'FROM PRPS GROUP BY y HAVING COUNT(*)>200 ORDER BY y' % NONEMPTY % (c, c)):
            trend[y] = round(100.0 * (f or 0) / n, 1)
        yrs = sorted(trend)
        early = trend.get(yrs[0]) if yrs else None
        late = trend.get(yrs[-1]) if yrs else None
        verdict = "SIN DATOS"
        if filled == 0:
            verdict = "VACIO"
        elif distinct == 1:
            verdict = "SIN INFORMACION"      # populated and carries one value
        elif early is not None and late is not None:
            if early >= 40 and late <= early / 3.0:
                verdict = "EN ABANDONO"
            elif early <= 2 and late >= 20:
                verdict = "EN ADOPCION"
            elif max(trend.values()) >= 20 and late <= 2:
                verdict = "PILOTO TERMINADO"
            elif 100.0 * filled / total >= 15:
                verdict = "EN USO"
            else:
                verdict = "RESIDUAL"
        fields[c] = {"filled": filled, "pct": round(100.0 * filled / total, 2),
                     "distinct": distinct, "examples": top, "trend_by_creation_year": trend,
                     "verdict": verdict}
        print("  %-18s %6d (%5.2f%%)  %5d valores  %s"
              % (c, filled, fields[c]["pct"], distinct, verdict))

    # WHO writes the master. The first row a technical user ever wrote IS the go-live.
    writers = {}
    for y, n, m in cx.execute(
            "SELECT substr(ERDAT,1,4) y, COUNT(*), "
            "SUM(CASE WHEN trim(ERNAM)='MULESOFT' THEN 1 ELSE 0 END) "
            "FROM PRPS GROUP BY y HAVING COUNT(*)>100 ORDER BY y"):
        writers[y] = {"created": n, "by_interface": m, "pct": round(100.0 * m / n, 1)}
    first = cx.execute("SELECT MIN(ERDAT) FROM PRPS WHERE trim(ERNAM)='MULESOFT'").fetchone()[0]
    print("\n  primer PEP escrito por la interfaz: %s" % first)

    # Did the identifier grammar converge when the writer changed? That measures what the
    # human hand was costing in variance.
    gram = {}
    for y in sorted(writers):
        g = collections.Counter()
        for (v,) in cx.execute(
                "SELECT YYE_BENEF1 FROM PRPS WHERE trim(YYE_BENEF1)<>'' "
                "AND substr(ERDAT,1,4)=?", (y,)):
            g[shape(v)] += 1
        if g:
            gram[y] = {"shapes": len(g), "top": g.most_common(3)}

    rep = {
        "_algorithm": "A19 wbs_model.py",
        "_the_three_readings_it_prevents": {
            "fill_rate_alone": "a numeric field is never blank; it defaults to zero",
            "a_flat_rate_hides_a_curve": "measure BY CREATION YEAR — 19% flat and 82%->5% "
                                         "decaying are opposite findings",
            "populated_is_not_informative": "a field with ONE distinct value has a fill rate "
                                            "and no information"},
        "rows": total, "custom_fields": len(yy),
        "by_verdict": dict(collections.Counter(v["verdict"] for v in fields.values())),
        "fields": fields,
        "who_writes_the_master": {"first_interface_row": first, "by_year": writers},
        "grammar_convergence": gram,
    }
    json.dump(rep, io.open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n  veredictos: %s" % rep["by_verdict"])
    print("  escrito: %s" % os.path.relpath(out_path, ROOT))

    for c, v in fields.items():
        if v["verdict"] in ("EN ABANDONO", "EN ADOPCION", "SIN INFORMACION"):
            remember(subject="PRPS.%s" % c, kind="CARRIER", learned_by="A19_wbs_model",
                     session=98,
                     fact="%s — %d filled (%.2f%%), %d distinct values"
                          % (v["verdict"], v["filled"], v["pct"], v["distinct"]),
                     evidence="A19 trend by creation year: %s"
                              % json.dumps(v["trend_by_creation_year"]),
                     implication=("read fill, trend and cardinality together; any one of the "
                                  "three alone gives a wrong reading of this field"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
