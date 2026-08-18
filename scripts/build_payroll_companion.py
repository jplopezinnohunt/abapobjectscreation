"""Build the PAYROLL END-TO-END companion — GENERATED from the brain.

THE RULE THIS PAGE IS BUILT ON — feedback_a_companion_names_it_never_counts_it
    Applied from the first line this time, rather than after the user had to point out that
    the budget-rate page said "nine enhancements" while the artefact held eighteen members
    with their hooks. Here: the 45 custom schemas are named, the 19 custom features are
    named, the 12 largest custom rules are named, the 11 posting enhancements are named,
    and every figure carries the perimeter it was measured on.

WHY PAYROLL NEEDS A COMPANION AT ALL
    It computes staff cost — the largest spend category — in a layer that is neither ABAP
    nor data: schemas, rules, wage types and features. A code search does not reach it. A
    table search does not recognise it. It was invisible in this brain until a budget-rate
    question forced the door.

WHAT IT SHOWS
    0     orientation: what this layer IS, and why nothing you normally grep finds it
    0b    the four traps, each one learned by falling into it this session
    1-4   the engine, the logic, the output and the gates — named, not counted
    5     the master data and HOW it is maintained, which is the governance finding
    6-7   the posting path and the chain from wage type to GL account
    8     the simulations: 89% of the detail was test data
    9     how to reproduce every figure, each query executed before publishing

USAGE
    python scripts/build_payroll_companion.py
"""
import html
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "companions", "payroll_end_to_end_companion_v1.html")


def jl(p):
    with io.open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


def esc(x):
    return html.escape(str(x if x is not None else ""))


def main():
    d = jl("brain_v2/payroll_discovery.json")
    s = d["summary"]
    eng, logic, out_, gates, md = d["engine"], d["logic"], d["output"], d["gates"], d["master_data"]
    post, res = d["posting"], d.get("resolved_posting") or {}

    # --- 1. THE ENGINE. Naming the schemas is the whole point: a schema calls other schemas
    # --- and the call list IS the flow. Sorted by active steps, because size is where the
    # --- logic actually sits.
    rows = sorted(eng.items(), key=lambda x: -x[1].get("active", 0))
    erows = ""
    for name, v in rows[:24]:
        calls = v.get("calls") or []
        erows += ('<tr class="%s"><td><code>%s</code></td><td class="num">%s</td>'
                  '<td class="num">%s</td><td class="num">%s</td><td class="md">%s</td></tr>'
                  % ("cust" if v.get("custom") else "", esc(name), esc(v.get("active")),
                     esc(v.get("steps")), len(calls),
                     " ".join('<code>%s</code>' % esc(c) for c in calls[:14])
                     + (" …" if len(calls) > 14 else "")))

    # --- 2. THE LOGIC. 307 custom rules of 11,742 — but the twelve largest are where the
    # --- custom mass concentrates, and a rule with 224 lines is a program in disguise.
    lrows = "".join('<tr><td><code>%s</code></td><td class="num">%s</td></tr>'
                    % (esc(a), esc(b)) for a, b in (logic.get("largest_custom") or []))

    # --- 3. THE OUTPUT. Families sharing a stem AND a phrase in their text are mechanisms
    # --- the schema layer never mentions. This is how BR for Staff was found at all.
    fam = out_.get("families_with_a_named_mechanism") or {}
    frows = ""
    for stem in sorted(fam):
        v = fam[stem]
        ph = ", ".join("%s %d" % (k, n) for k, n in (v.get("phrases") or {}).items())
        frows += ('<tr><td><code>%s*</code></td><td class="num">%s</td><td>%s</td></tr>'
                  % (esc(stem), esc(v.get("members")), esc(ph)))

    # --- 4. THE GATES. A feature is a perimeter no code or table search finds, and it is
    # --- NOT invisible — it compiles to a readable program. Naming the 19 is the point.
    gnames = " ".join('<code>%s</code>' % esc(x) for x in (gates.get("custom_names") or []))

    # --- 5. HOW THE MASTER DATA IS MAINTAINED. The finding is not the volume, it is the
    # --- share of changes with NO TRANSACTION: those did not come from a person at a screen.
    mrows = ""
    # payroll_discovery keys `maintenance` by the log it read, and it reads BOTH when
    # both exist. Prefer the current one: "cdhdr" is SUPERSEDED by "cdhdr_history"
    # and is a strict subset (7.8M rows against 12.0M), so taking it renders a
    # confident section built on 4.2M changes it never saw.
    _maint = md.get("maintenance", {})
    _log = _maint.get("cdhdr_history") or _maint.get("cdhdr") or {}
    for obj, v in sorted(_log.items(),
                         key=lambda x: -(x[1].get("pct_no_transaction") or 0)):
        tops = " · ".join("%s %s" % (esc(t[0]), esc(t[1]))
                          for t in (v.get("top_transactions") or [])[:4])
        pct = v.get("pct_no_transaction") or 0
        mrows += ('<tr class="%s"><td><code>%s</code></td><td class="num">%s</td>'
                  '<td class="num">%s</td><td class="n">%s%%</td><td class="md">%s</td></tr>'
                  % ("bad" if pct > 40 else "", esc(obj), esc(v.get("with_a_transaction")),
                     esc(v.get("with_NO_transaction")), esc(pct), tops))

    # --- 6. THE POSTING PATH, named.
    prows = ""
    seen = set()
    for e in (post.get("enhancements_on_the_posting_path") or []):
        k = (e.get("enhancement"), e.get("hooked_object"))
        if k in seen:
            continue
        seen.add(k)
        prows += ('<tr><td><code>%s</code></td><td>%s</td><td><code>%s</code></td></tr>'
                  % (esc(e.get("enhancement")), esc(e.get("type")),
                     esc(e.get("hooked_object"))))

    # --- 7. the resolved posting: which FI transaction key reaches which GL accounts
    krows = ""
    for k, v in sorted((res.get("transaction_keys") or {}).items()):
        krows += ('<tr><td><code>%s</code></td><td class="num">%d</td><td class="md">%s</td></tr>'
                  % (esc(k), len(v), " ".join('<code>%s</code>' % esc(a) for a in v[:8])))

    doc = io.open(os.path.join(HERE, "_payroll_companion.tpl"), encoding="utf-8").read()
    for tok, val in (
        ("@SCHEMAS@", s["schemas"]), ("@CUSTSCHEMAS@", s["custom_schemas"]),
        ("@RULES@", "{:,}".format(s["rules"]).replace(",", ".")),
        ("@CUSTRULES@", s["custom_rules"]),
        ("@WT@", "{:,}".format(s["wage_types"]).replace(",", ".")),
        ("@FEAT@", "{:,}".format(s["features"]).replace(",", ".")),
        ("@CUSTFEAT@", s["custom_features"]),
        ("@RULELINES@", "{:,}".format(logic["rule_lines"]).replace(",", ".")),
        ("@EROWS@", erows), ("@LROWS@", lrows), ("@FROWS@", frows),
        ("@GNAMES@", gnames), ("@MROWS@", mrows), ("@PROWS@", prows), ("@KROWS@", krows),
        ("@HOWREAD@", esc(gates.get("_how_to_read_one", ""))),
        ("@LESSON@", esc(out_.get("_the_lesson", ""))),
        ("@PA0001@", "{:,}".format(
            (md.get("in_the_golden") or [{}])[0].get("rows", 0)).replace(",", ".")),
        ("@RESROWS@", "{:,}".format(res.get("rows", 0)).replace(",", ".")),
        ("@RESACC@", res.get("accounts_total", "?")),
        ("@RESONE@", res.get("accounts_with_one_key", "?")),
    ):
        doc = doc.replace(tok, str(val))
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    assert "@" not in "".join(x for x in doc.split() if x.startswith("@")), "token sin sustituir"
    print("escrito: %s (%d KB, %d esquemas, %d features custom nombradas)"
          % (os.path.relpath(OUT, ROOT), len(doc) // 1024, s["schemas"], s["custom_features"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
