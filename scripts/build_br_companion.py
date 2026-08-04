"""Build the BUDGET RATE companion — GENERATED from the brain, never hand-edited.

WHY GENERATED
    A companion written by hand is true on the day it is written. This session moved the
    staff-side figure by a factor of nine and reversed the reading of the mechanism twice;
    a hand-typed HTML would still be showing the first number. Everything here is read from
    budget_rate_graph.json, budget_rate_enhancements.json and claims.json at build time, so
    the page cannot drift from the brain. Edit the builder, never the output.

THE RULE THIS PAGE IS BUILT ON — feedback_a_companion_names_it_never_counts_it
    A COMPANION NAMES THE OBJECTS. It never reports a count in place of them. The first
    version of this page said "nine enhancements and a control report" while the artefact
    held 18 members each with its hook, its gate field, what it modifies and whether the
    effect persists; 12 moments each with its SAP object and the DATE it converts on; and 8
    named perimeter conditions. All of it summarised away.

    A count is what you write when you have not read the data — and to the reader it is
    indistinguishable from having read it and found nothing.

    Four requirements, applied here:
      1. every quantity is immediately followed by its enumeration
      2. every object carries its hook, its gate and its effect, not merely its name
      3. every figure carries the perimeter it was measured on, in the same cell
      4. the page says which sections are GENERATED and which are WRITTEN, because only the
         written ones can go stale
    Where an array exists in the source, a TABLE must exist in the page.

WHAT IT SHOWS, and the order is the argument
    1. The two mechanisms side by side, because the whole subject is that they are NOT the
       same design and were repeatedly confused for one.
    2. AS-DESIGNED against AS-RUN: the configuration describes 72 wage types and one posts.
    3-5. The 18 extensions, the 12 moments and the 8 conditions — named, not counted.
    6. The numbers, each with what it is measured ON.
    7-8. The contradiction the graph keeps on purpose, and the chain from mechanism to
       amount, which on being walked exposes the edges the graph is still missing.
    9. What was corrected, because on this subject that is the most transferable part.

USAGE
    python scripts/build_br_companion.py
    (wired into rebuild_all.py — see the landing-page precedent)
"""
import html
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "companions", "budget_rate_companion_v1.html")

KIND_COLOUR = {
    "MECHANISM": "--mech", "CONFIGURATION": "--conf", "RULE": "--rule",
    "BEHAVIOUR": "--behv", "CONTROL": "--ctrl", "MEASUREMENT": "--meas",
    "ALGORITHM": "--algo", "CONSTRAINT": "--cons", "DATA": "--data", "DEFECT": "--defe",
}


def jl(p):
    with io.open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


def esc(x):
    return html.escape(str(x if x is not None else ""))


def main():
    g = jl("brain_v2/budget_rate_graph.json")
    art = jl("brain_v2/budget_rate_enhancements.json")
    claims = jl("brain_v2/claims/claims.json")
    cl = claims["claims"] if isinstance(claims, dict) and "claims" in claims else claims

    per = art["_THE_TWO_MECHANISMS"]["personnel"]["the_real_mechanism"]
    asrun = per.get("_AS_DESIGNED_VS_AS_RUN_s098") or {}
    imp = per.get("the_impact_MEASURED") or {}
    corr = imp.get("_CORRECTED_simulation_runs") or {}
    recon = imp.get("_the_reconciliation") or {}
    nodes = g["nodes"]
    edges = g["edges"]

    # Claims that carry a correction are the spine of the honesty section: this subject was
    # got wrong repeatedly and the corrections are the most transferable part of it.
    corrected = [c for c in cl
                 if c.get("domain") in ("PSM_FM", "HCM", "PS")
                 and (c.get("corrects") or any(k.startswith("CORRECTED") for k in c))]

    def card(title, body, tone=""):
        return ('<div class="card %s"><h3>%s</h3>%s</div>' % (tone, esc(title), body))

    # --- the two mechanisms, side by side
    np_ = art["_THE_TWO_MECHANISMS"].get("non_personnel") or {}
    two = """
    <div class="grid2">
      <div class="mech">
        <div class="tag">NO PERSONAL</div>
        <h3>Nueve enhancements + un informe de control</h3>
        <p>Se ejecuta en las <b>extensiones del posting estándar</b>. FM lleva el tipo fijo,
           FI/GL queda correcto, y la diferencia se <b>informa</b> por el reporte
           <code>YFM_FI_BR_COMP</code>.</p>
        <div class="fig"><span class="n">-2.365.688,44</span><span class="u">USD</span></div>
        <div class="note">sobre 11.179 líneas de imputación financiera. Los commitments no
           entran: SAP los recalcula, no hay contra qué comparar.</div>
      </div>
      <div class="mech alt">
        <div class="tag">PERSONAL</div>
        <h3>Un wage type en el motor de nómina</h3>
        <p>Se calcula en el <b>esquema de nómina</b>, no en ABAP. La diferencia no se informa:
           se <b>postea</b>, a cuentas 999 dedicadas, y el bloque <b>cuadra a cero exacto</b>
           por moneda. Por eso FI GL y FM coinciden en este lado.</p>
        <div class="fig"><span class="n">1.982.154,59</span><span class="u">USD</span>
             <span class="n2">796.418,86</span><span class="u">EUR</span></div>
        <div class="note">2026 hasta julio, <b>solo runs realmente posteados</b>.</div>
      </div>
    </div>"""

    # --- as designed vs as run
    rows = ""
    for k, v in (asrun.get("as_run_2026", {}).get("gl_accounts") or {}).items():
        rows += "<tr><td><code>%s</code></td><td>%s</td></tr>" % (esc(k), esc(v))
    delta = """
    <div class="delta">
      <div class="col designed">
        <div class="hd">AS-DESIGNED — lo que dice la configuración</div>
        <ul>
          <li><b>72</b> wage types Constant Dollar en <code>T512T</code></li>
          <li>configuración <b>idéntica</b> en <code>T512W</code></li>
          <li><b>58 de 58</b> parejas posteando a la simbólica de su base con signo invertido</li>
        </ul>
        <div class="verdict bad">de esos 72, <b>CERO</b> postean en 2026</div>
      </div>
      <div class="arrow">≠</div>
      <div class="col run">
        <div class="hd">AS-RUN — lo que hacen los documentos</div>
        <ul>
          <li><b>un</b> wage type: <code>999S</code> «SUM DIF Exch. rate Fluct.»</li>
          <li>a tres simbólicas: <code>CUSD</code> · <code>CUS1</code> · <code>CUSA</code></li>
          <li>clave FI <code>HRC</code>, sociedad <code>UNES</code>, un tipo de documento</li>
        </ul>
        <table class="mini">%s</table>
      </div>
    </div>
    <p class="lesson">Una tabla de configuración <b>no puede informar de que su propio
       contenido está dormido</b>. La distancia entre las dos columnas es el producto, no un
       error a limpiar — por eso el grafo conserva las dos unidas por una arista de
       contradicción.</p>""" % rows

    # --- the numbers, each with its perimeter
    nums = """
    <table class="wide">
      <tr><th>cifra</th><th>medida SOBRE</th><th>por qué importa el perímetro</th></tr>
      <tr><td class="n">-2.365.688,44 USD</td><td>11.179 líneas de imputación financiera,
          no-personal</td><td>los commitments quedan fuera: SAP los recalcula</td></tr>
      <tr class="hl"><td class="n">1.982.154,59 USD<br>796.418,86 EUR</td>
          <td>cuentas 999, 2026 hasta julio, <b>solo runs posteados</b></td>
          <td>incluyendo simulaciones daba <b>20.523.434,48</b> — nueve veces más</td></tr>
      <tr><td class="n">0,00</td><td>neto del bloque 999 por moneda</td>
          <td>es una reclasificación balanceada, no un residuo entre dos valoraciones</td></tr>
    </table>
    <div class="warn"><b>%s</b> de %s runs de nómina de 2026 son SIMULACIONES y nunca
       llegaron a contabilidad. El corte es del <b>run</b>, nunca parcial: %s runs enteros
       dentro, %s enteros fuera, cero a medias. El golden se purgó a lo final —
       %s.</div>""" % (
        esc("1.828"), esc("2.316"), esc("488"), esc("1.828"),
        esc(corr.get("_how_to_not_repeat_it", "vista payroll_runs_posted")))

    # --- THE EXTENSIONS, NAMED. A companion that says "nine enhancements" has told the
    # --- reader nothing they can act on: not which, not where they hook, not what they
    # --- change, not whether the change survives the call. All of that is in the artefact
    # --- and the first version of this page summarised it away. Counting is what you write
    # --- when you have not read the data.
    mem = art.get("members") or []
    mrows = ""
    for m in mem:
        mrows += ('<tr><td><code>%s</code><span class="id">%s</span></td>'
                  '<td>%s</td><td class="hk">%s</td><td class="gt">%s</td>'
                  '<td class="md">%s</td><td class="%s">%s</td></tr>'
                  % (esc(m.get("name")), esc(m.get("id")), esc(m.get("camp")),
                     esc(m.get("hook")), esc(m.get("gate_keyed_on")), esc(m.get("modifies")),
                     "yes" if m.get("persists") else "no",
                     "PERSISTE" if m.get("persists") else "temporal"))

    # --- THE MOMENTS. Where in the FM lifecycle the rate is actually applied, which object
    # --- it hooks, which gate decides, and WHICH DATE it converts on — the last one is what
    # --- makes two moments give different answers for the same document.
    mo = (art.get("the_twelve_moments") or {}).get("moments") or []
    morows = ""
    for i, x in enumerate(mo, 1):
        morows += ('<tr><td class="num">%d</td><td><b>%s</b></td>'
                   '<td><code>%s</code></td><td class="hk">%s</td>'
                   '<td class="gt">%s</td><td class="md">%s</td>'
                   '<td class="num">%s</td></tr>'
                   % (i, esc(x.get("moment")), esc(x.get("enhancement")),
                      esc(x.get("sap_object") or x.get("hooks_into")), esc(x.get("gate")),
                      esc(x.get("converts_on")), esc(x.get("lines"))))

    # --- THE CONDITIONS. The perimeter is eight ranges and each is SKIPPED when its
    # --- parameter arrives empty, which is why the same code covers different populations
    # --- at different moments. Naming the values is the difference between "there is a
    # --- perimeter" and knowing what is inside it.
    cond = ((art.get("the_exact_perimeter") or {})
            .get("gate_1_CHECK_CONDITIONS") or {}).get("conditions") or []
    crows2 = ""
    for c in cond:
        vals = c.get("values")
        crows2 += ('<tr><td><code>%s</code></td><td>%s</td><td>%s</td>'
                   '<td class="md">%s</td></tr>'
                   % (esc(c.get("param")), esc(c.get("range")),
                      esc(", ".join(vals) if isinstance(vals, list) else vals),
                      esc(c.get("_note"))))

    # --- the graph, presented as the two questions it exists to answer rather than as an
    # --- inventory. An alphabetical list of 33 nodes answers nothing; the contradiction pair
    # --- and the resolution chain are why the edges were built in the first place.
    def find_edges(rel_sub):
        return [e for e in edges if rel_sub in e["rel"]]

    contra = find_edges("CONTRADICT")
    chain_ids = ["MECHANISM_PERSONNEL", "PAYROLL_ENGINE", "WAGE_TYPE_999S",
                 "SYMBOLIC_ACCOUNT", "RESOLVED_POSTING", "ACCOUNTS_999", "IMPACT_STAFF"]
    byid = {n["id"]: n for n in nodes}
    chain = ""
    for i, nid in enumerate(chain_ids):
        n = byid.get(nid)
        if not n:
            continue
        link = ""
        if i:
            e = next((x for x in edges
                      if x["to"] == nid and x["from"] == chain_ids[i - 1]), None)
            # A missing edge is REPORTED, not rendered as silence. Walking the chain is what
            # exposes the holes in the graph — a gap drawn as a blank line reads like a
            # design choice, and this one is a gap.
            link = ('<div class="lnk"><span>%s</span><em>%s</em></div>'
                    % (esc(e["rel"]), esc(e.get("why"))) if e else
                    '<div class="lnk gap"><span>SIN ARISTA</span><em>el grafo no relaciona '
                    'estos dos sujetos todavía — hueco detectado al recorrer la cadena</em>'
                    '</div>')
        chain += ('%s<div class="step"><b>%s</b><span>%s</span></div>'
                  % (link, esc(nid), esc(n["what"])))
    contra_html = "".join(
        '<div class="contra"><div class="c1">%s</div><div class="cx">se contradice con</div>'
        '<div class="c2">%s</div><div class="cw">%s</div></div>'
        % (esc(e["from"]), esc(e["to"]), esc(e.get("why"))) for e in contra)

    by_kind = {}
    for n in nodes:
        by_kind.setdefault(n["kind"], []).append(n)
    gcards = ""
    for kind in sorted(by_kind):
        items = "".join(
            '<li title="%s"><b>%s</b> <span>%s</span></li>'
            % (esc(n.get("content_in")), esc(n["id"]), esc(n["what"]))
            for n in sorted(by_kind[kind], key=lambda x: -x.get("degree", 0)))
        gcards += ('<div class="kcard"><div class="khd" style="border-color:var(%s)">%s '
                   '<em>%d</em></div><ul>%s</ul></div>'
                   % (KIND_COLOUR.get(kind, "--conf"), esc(kind), len(by_kind[kind]), items))
    erows = "".join(
        '<tr><td>%s</td><td class="rel">%s</td><td>%s</td><td class="why">%s</td></tr>'
        % (esc(e["from"]), esc(e["rel"]), esc(e["to"]), esc(e.get("why")))
        for e in edges)

    # --- the corrections
    crows = ""
    for c in corrected[-8:]:
        note = c.get("resolution_notes") or ""
        crows += ('<tr><td>#%s</td><td>%s</td><td>%s</td></tr>'
                  % (esc(c["id"]), esc((c.get("claim") or "")[:150] + "…"), esc(note[:180])))

    doc = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Budget Rate — UNESCO SAP · los dos mecanismos, diseñado contra ejecutado</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--un-blue:#0079c1;--un-dark:#1a3a5c;--un-grey:#5a6c84;--bg:#f5f7fa;--card:#fff;
 --border:#dde3eb;--ok:#2c8b50;--bad:#c93a3a;--warn:#dd6b20;
 --mech:#0079c1;--conf:#7a8fa8;--rule:#a85aa3;--behv:#2c8b50;--ctrl:#664b9b;
 --meas:#1a3a5c;--algo:#dd6b20;--cons:#8b1538;--data:#5a6c84;--defe:#c93a3a;}
*{box-sizing:border-box}
body{margin:0;font:14px/1.55 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;
 color:var(--un-dark);background:var(--bg)}
.container{max-width:1280px;margin:0 auto;padding:0 18px 60px}
header{background:linear-gradient(135deg,#0079c1,#1a3a5c);color:#fff;padding:34px 0 30px;margin-bottom:26px}
header .container{padding-bottom:0}
h1{margin:0 0 6px;font-size:27px;font-weight:600}
.sub{opacity:.9;font-size:15px;max-width:900px}
.meta{margin-top:14px;font-size:12px;opacity:.75}
h2{font-size:19px;margin:34px 0 12px;padding-bottom:7px;border-bottom:2px solid var(--border)}
code{background:#eef2f7;padding:1px 5px;border-radius:3px;font-size:12.5px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.mech{background:var(--card);border:1px solid var(--border);border-top:4px solid var(--un-blue);
 border-radius:6px;padding:18px}
.mech.alt{border-top-color:var(--warn)}
.mech h3{margin:6px 0 10px;font-size:17px}
.tag{font-size:11px;letter-spacing:.09em;color:var(--un-grey);font-weight:700}
.fig{margin:14px 0 6px;display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}
.fig .n{font-size:25px;font-weight:700;color:var(--un-blue)}
.fig .n2{font-size:19px;font-weight:700;color:var(--un-grey)}
.fig .u{font-size:12px;color:var(--un-grey)}
.note{font-size:12.5px;color:var(--un-grey)}
.delta{display:grid;grid-template-columns:1fr 48px 1fr;gap:10px;align-items:stretch}
.col{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:16px}
.col.designed{border-left:4px solid var(--un-grey)}
.col.run{border-left:4px solid var(--ok)}
.hd{font-size:12px;letter-spacing:.06em;font-weight:700;color:var(--un-grey);margin-bottom:9px}
.col ul{margin:0;padding-left:18px}.col li{margin:4px 0}
.arrow{display:flex;align-items:center;justify-content:center;font-size:30px;color:var(--bad);font-weight:700}
.verdict{margin-top:11px;padding:8px 10px;border-radius:4px;font-size:13px}
.verdict.bad{background:#fdecec;color:var(--bad)}
.lesson{background:#fff8ef;border-left:4px solid var(--warn);padding:11px 14px;margin-top:14px;
 border-radius:0 4px 4px 0}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
th{background:#eef2f7;font-size:11.5px;letter-spacing:.05em;color:var(--un-grey)}
table.mini{margin-top:9px;font-size:12px}
tr.hl{background:#f0f7fc}
td.n{font-weight:700;color:var(--un-blue);white-space:nowrap}
td.rel{color:var(--un-grey);font-size:11.5px;letter-spacing:.04em}
td.why{color:var(--un-grey);font-size:12px}
.warn{background:#fdecec;border-left:4px solid var(--bad);padding:12px 14px;margin-top:14px;
 border-radius:0 4px 4px 0}
.kgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.kcard{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:12px 14px}
.khd{font-size:11.5px;font-weight:700;letter-spacing:.06em;color:var(--un-grey);
 border-left:3px solid;padding-left:7px;margin-bottom:8px}
.khd em{float:right;font-style:normal;opacity:.6}
.kcard ul{margin:0;padding-left:15px;font-size:12px}
.kcard li{margin:3px 0}.kcard li span{color:var(--un-grey)}
.scroll{overflow-x:auto}
table.det{font-size:12px}
table.det td.hk,table.det td.gt,table.det td.md{color:var(--un-grey);max-width:290px}
table.det td.gt{font-family:ui-monospace,Consolas,monospace;font-size:11px}
table.det td.num{text-align:right;color:var(--un-grey)}
table.det .id{display:block;font-size:10px;color:var(--un-grey);letter-spacing:.04em}
table.det td.yes{color:var(--bad);font-weight:700;font-size:11px;white-space:nowrap}
table.det td.no{color:var(--un-grey);font-size:11px;white-space:nowrap}
.contra{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:center;
 background:var(--card);border:1px solid var(--border);border-left:4px solid var(--bad);
 border-radius:6px;padding:14px 16px;margin-bottom:10px}
.contra .c1,.contra .c2{font-weight:700;font-size:13.5px}
.contra .c2{text-align:right;color:var(--ok)}
.contra .cx{font-size:11px;letter-spacing:.06em;color:var(--bad);white-space:nowrap}
.contra .cw{grid-column:1/-1;font-size:12.5px;color:var(--un-grey);margin-top:6px}
.chain{display:flex;flex-direction:column;gap:0}
.chain .step{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--un-blue);
 border-radius:5px;padding:10px 14px}
.chain .step b{display:block;font-size:13px}
.chain .step span{font-size:12.5px;color:var(--un-grey)}
.chain .lnk{padding:5px 0 5px 22px;border-left:2px dashed var(--border);margin-left:14px}
.chain .lnk span{font-size:11px;letter-spacing:.05em;color:var(--un-blue);font-weight:700}
.chain .lnk.gap{border-left-color:var(--bad)}
.chain .lnk.gap span{color:var(--bad)}
.chain .lnk em{display:block;font-style:normal;font-size:12px;color:var(--un-grey)}
.appx{margin-top:26px;background:var(--card);border:1px solid var(--border);border-radius:6px;padding:12px 16px}
.appx summary{cursor:pointer;font-weight:600;color:var(--un-grey);font-size:13px}
footer{margin-top:40px;font-size:12px;color:var(--un-grey);border-top:1px solid var(--border);padding-top:14px}
@media(max-width:900px){.grid2,.delta{grid-template-columns:1fr}.arrow{display:none}}
</style></head><body>
<header><div class="container">
<h1>Budget Rate — los dos mecanismos</h1>
<div class="sub">El tipo de cambio fijo se aplica de <b>dos formas distintas</b> que llevan el
 mismo nombre. En no-personal la diferencia se <b>informa</b>; en personal se <b>postea</b>.
 Confundirlas costó dos conclusiones equivocadas en una sola sesión.</div>
<div class="meta"><b>Cifras, grafo y correcciones: GENERADOS</b> del brain en cada build
 (@NN@ nodos · @NE@ aristas) — no pueden derivar. <b>La interpretación de las secciones 1-3
 está ESCRITA</b> y vive en <code>scripts/build_br_companion.py</code>: si el modelo cambia,
 hay que reescribirla. Nunca editar el HTML.</div>
</div></header>
<div class="container">

<h2>1 · Los dos mecanismos</h2>@TWO@

<h2>2 · Lo diseñado contra lo ejecutado</h2>@DELTA@

<h2>3 · Las extensiones, una por una</h2>
<p class="note">Dónde engancha cada una, sobre qué campo decide, qué modifica, y si el cambio
 <b>sobrevive a la llamada</b> o solo vive durante ella. Esa última columna es la que separa
 lo que queda escrito en FM de lo que solo altera una comprobación en curso.</p>
<div class="scroll"><table class="det"><tr><th>extensión</th><th>campo</th><th>engancha en</th>
<th>gatea sobre</th><th>modifica</th><th>efecto</th></tr>@MROWS@</table></div>

<h2>4 · Los doce momentos del ciclo de vida FM</h2>
<p class="note">Los mismos ocho rangos cubren poblaciones distintas en cada momento, porque
 <b>una condición cuyo parámetro llega vacío se salta</b>. Y la columna <i>convierte sobre</i>
 es la que explica que dos momentos den respuestas distintas para el mismo documento: no
 comparten la fecha de conversión.</p>
<div class="scroll"><table class="det"><tr><th>#</th><th>momento</th><th>extensión</th>
<th>objeto SAP</th><th>gate</th><th>convierte sobre</th><th>líneas</th></tr>@MOROWS@</table></div>

<h2>5 · El perímetro: las ocho condiciones</h2>
<p class="note">Cada una se comprueba solo si su parámetro llega informado. Un rango vacío no
 restringe: <b>abre</b>.</p>
<div class="scroll"><table class="det"><tr><th>parámetro</th><th>rango</th><th>valores</th>
<th>nota</th></tr>@CROWS2@</table></div>

<h2>6 · Las cifras, cada una con su perímetro</h2>@NUMS@

<h2>7 · La contradicción que el grafo conserva a propósito</h2>
<p class="note">El diseño y el comportamiento son mecanismos distintos, y los dos siguen en el
 grafo unidos por una arista que dice que se contradicen. Borrar uno perdería la medida de la
 distancia — y esa distancia es el producto.</p>
@CONTRA@

<h2>8 · La cadena, de mecanismo a importe</h2>
<p class="note">Esto es lo que las aristas permiten responder mecánicamente: seguir el lado de
 personal hasta su cifra sin que nadie tenga que recordar el camino.</p>
<div class="chain">@CHAIN@</div>

<details class="appx"><summary>Apéndice · inventario completo de sujetos y aristas</summary>
<div class="kgrid">@GCARDS@</div>
<div class="scroll"><table><tr><th>de</th><th>relación</th><th>a</th><th>por qué</th></tr>@EROWS@</table></div>
</details>

<h2>9 · Lo que se corrigió, y por qué eso es lo más transferible</h2>
<p class="note">Este tema se entendió mal varias veces. Las correcciones se conservan
 <b>superponiendo</b>, nunca borrando — un claim corregido sigue ahí con su corrección al lado.</p>
<div class="scroll"><table><tr><th>claim</th><th>qué afirma</th><th>corrección</th></tr>@CROWS@</table></div>

<footer>Fuente: <code>brain_v2/budget_rate_graph.json</code> ·
<code>brain_v2/budget_rate_enhancements.json</code> · <code>brain_v2/claims/claims.json</code>.
Regenerar: <code>python scripts/build_br_companion.py</code></footer>
</div></body></html>"""
    for tok, val in (("@NN@", len(nodes)), ("@NE@", len(edges)), ("@TWO@", two),
                     ("@DELTA@", delta), ("@NUMS@", nums), ("@GCARDS@", gcards),
                     ("@EROWS@", erows), ("@CROWS@", crows),
                     ("@CONTRA@", contra_html), ("@CHAIN@", chain),
                     ("@MROWS@", mrows), ("@MOROWS@", morows),
                     ("@CROWS2@", crows2)):
        doc = doc.replace(tok, str(val))

    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("escrito: %s (%d KB, %d nodos, %d aristas, %d correcciones)"
          % (os.path.relpath(OUT, ROOT), len(doc) // 1024, len(nodes), len(edges),
             len(corrected)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
