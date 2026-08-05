"""Build the PROJECT / WBS companion — GENERATED from brain_v2/project_wbs_model.json (A19).

WHAT IT SHOWS, and in which order
    The MODEL first: what a WBS element is, the three readings the analysis exists to
    prevent, then all 31 custom fields grouped by the verdict that fill + trend +
    cardinality produce together, then who writes the master, then where the donor actually
    lives.

    The TEMPORAL EVOLUTION is a CLOSING COMMENT, not the spine. It earns its place at the
    end because by then the reader has seen the fields and can recognise that the current
    state is not a design but a sediment: four decisions twenty years apart, none of which
    withdrew the one before it.

    Each field still carries a sparkline of its fill BY CREATION YEAR, because a rate
    without its curve is the second of the three wrong readings.

THE RULE IT IS BUILT ON — feedback_a_companion_names_it_never_counts_it
    All 31 custom fields are named with their fill, their cardinality, their trend and the
    verdict those three produce together. No counts standing in for the objects.
"""
import html
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "companions", "project_wbs_companion_v1.html")

VERDICT_ORDER = ["EN ABANDONO", "EN ADOPCION", "SIN INFORMACION", "EN USO", "RESIDUAL", "VACIO"]
VERDICT_CSS = {"EN ABANDONO": "aban", "EN ADOPCION": "adop", "SIN INFORMACION": "noinfo",
               "EN USO": "uso", "RESIDUAL": "resid", "VACIO": "vacio"}
VERDICT_WHAT = {
 "EN ABANDONO": "empezó alto y cae. FUE la práctica, y algo lo desplazó — hay que saber qué",
 "EN ADOPCION": "empezó vacío y sube. Es el borde vivo del modelo, no un residuo",
 "SIN INFORMACION": "poblado y con UN solo valor distinto. Tiene tasa de llenado y no informa "
                    "de nada — el caso que solo la cardinalidad detecta",
 "EN USO": "llenado sostenido y con variedad real de valores",
 "RESIDUAL": "unos pocos registros y nunca despegó",
 "VACIO": "construido y nunca escrito",
}


def esc(x):
    return html.escape(str(x if x is not None else ""))


def spark(trend, lo=2002):
    """A sparkline of fill-rate by creation year. The shape IS the argument."""
    yrs = sorted(trend)
    if not yrs:
        return ""
    bars = ""
    for y in yrs:
        v = trend[y]
        h = max(2, int(round(v * 0.28)))
        cls = "hi" if v >= 50 else ("mid" if v >= 15 else "lo")
        bars += ('<i class="%s" style="height:%dpx" title="%s: %.1f%%"></i>' % (cls, h, y, v))
    return ('<div class="spark">%s</div><div class="sparklab">%s → %s '
            '<b>%.0f%% → %.0f%%</b></div>'
            % (bars, yrs[0], yrs[-1], trend[yrs[0]], trend[yrs[-1]]))


def main():
    m = json.load(io.open(os.path.join(ROOT, "brain_v2", "project_wbs_model.json"),
                          encoding="utf-8"))
    f = m["fields"]

    groups = ""
    for v in VERDICT_ORDER:
        names = [k for k, x in f.items() if x["verdict"] == v]
        if not names:
            continue
        names.sort(key=lambda k: -f[k]["filled"])
        rows = ""
        for k in names:
            x = f[k]
            ex = ", ".join(str(e)[:22] for e in (x["examples"] or [])[:3])
            rows += ('<tr><td><code>%s</code></td><td class="n">%s</td>'
                     '<td class="num">%s%%</td><td class="num">%s</td>'
                     '<td class="sp">%s</td><td class="md">%s</td></tr>'
                     % (esc(k), "{:,}".format(x["filled"]).replace(",", "."), esc(x["pct"]),
                        esc(x["distinct"]), spark(x["trend_by_creation_year"]), esc(ex)))
        groups += ('<h3 class="vh %s">%s <em>%d campos</em></h3>'
                   '<p class="note">%s</p>'
                   '<div class="scroll"><table class="det"><tr><th>campo</th><th>llenos</th>'
                   '<th>%%</th><th>valores</th><th>por año de creación</th><th>ejemplos</th>'
                   '</tr>%s</table></div>'
                   % (VERDICT_CSS[v], esc(v), len(names), esc(VERDICT_WHAT[v]), rows))

    w = m["who_writes_the_master"]
    wrows = ""
    for y in sorted(w["by_year"]):
        v = w["by_year"][y]
        if int(y) < 2018:
            continue
        bar = int(round(v["pct"] * 0.9))
        wrows += ('<tr><td>%s</td><td class="num">%s</td><td class="num">%s</td>'
                  '<td><div class="hbar" style="width:%dpx"></div> %s%%</td></tr>'
                  % (esc(y), "{:,}".format(v["created"]).replace(",", "."),
                     "{:,}".format(v["by_interface"]).replace(",", "."), bar, esc(v["pct"])))

    grows = ""
    for y in sorted(m.get("grammar_convergence") or {}):
        g = m["grammar_convergence"][y]
        if int(y) < 2019:
            continue
        top = " · ".join("<code>%s</code> %d" % (esc(a), b) for a, b in g["top"])
        grows += ('<tr><td>%s</td><td class="num">%s</td><td>%s</td></tr>'
                  % (esc(y), esc(g["shapes"]), top))

    tpl = io.open(os.path.join(HERE, "_wbs_companion.tpl"), encoding="utf-8").read()
    for tok, val in (
        ("@ROWS@", "{:,}".format(m["rows"]).replace(",", ".")),
        ("@NFIELDS@", m["custom_fields"]),
        ("@GROUPS@", groups), ("@WROWS@", wrows), ("@GROWS@", grows),
        ("@FIRST@", w["first_interface_row"]),
        ("@VERDICTS@", " · ".join("%s <b>%d</b>" % (k, v)
                                  for k, v in sorted(m["by_verdict"].items(),
                                                     key=lambda x: -x[1]))),
    ):
        tpl = tpl.replace(tok, str(val))
    io.open(OUT, "w", encoding="utf-8").write(tpl)
    left = [t for t in tpl.split() if t.startswith("@") and t.endswith("@")]
    assert not left, "token sin sustituir: %s" % left[:3]
    print("escrito: %s (%d KB, %d campos, veredictos %s)"
          % (os.path.relpath(OUT, ROOT), len(tpl) // 1024, m["custom_fields"], m["by_verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
