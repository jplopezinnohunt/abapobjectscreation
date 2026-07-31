"""build_algorithm_companion.py — the algorithm map, per domain and versus the market.

Generated from the stores, never hand-edited: algorithms.json · domain_assets.json ·
portability.json · process_flows.json · executed_objects_domain_map.json.

Answers three questions visually:
  1. per DOMAIN — which algorithms actually serve it
  2. versus the MARKET — what we adopted, what we extended, what has no equivalent
  3. how far we are from installation #2 — the portability measure
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
B = REPO / "brain_v2"
OUT = REPO / "companions" / "algorithm_map_v1.html"


def load(p, d=None):
    p = Path(p)
    return json.load(open(p, encoding="utf-8")) if p.exists() else (d or {})


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    algos = load(B / "methods" / "algorithms.json")
    A = algos.get("algorithms", {})
    bundles = load(B / "methods" / "domain_assets.json").get("domains", {})
    port = load(B / "methods" / "portability.json")
    emap = load(B / "executed_objects_domain_map.json").get("by_domain", {})
    flows = load(B / "process_flows" / "process_flows.json").get("flows", {})
    nest = algos.get("_nesting", {}).get("layers", {})

    ORIGIN_LABEL = {
        "MARKET_STANDARD": ("adoptado", "#5b8def"),
        "MARKET_EXTENDED": ("extendido", "#b06fd8"),
        "OURS": ("propio", "#2fa37c"),
    }
    STATE_COLOR = {"STRONG": "#2fa37c", "WORKS": "#5b8def", "WEAK": "#d9822b",
                   "FRAGILE": "#d64545", "UNDER_EXERCISED": "#d9822b", "MISSING": "#d64545"}

    # ---- per-domain rows -------------------------------------------------
    rows = []
    for dom, b in sorted(bundles.items(),
                         key=lambda x: -(x[1].get("activity", {}).get("executions") or 0)):
        ex = b.get("activity", {}).get("executions") or 0
        if ex == 0 and not b.get("flows"):
            continue
        rows.append({
            "domain": dom, "execs": ex,
            "algorithms": b.get("algorithms", []),
            "flows": b.get("flows", []),
            "tables": b.get("tables", {}).get("count", 0),
            "cells": b.get("capability_cells_filled", 0),
            "missing": b.get("missing", []),
        })

    def chip(aid):
        a = A.get(aid, {})
        lbl, col = ORIGIN_LABEL.get(a.get("origin"), ("?", "#888"))
        return (f'<span class="chip" style="border-color:{col};color:{col}" '
                f'title="{esc(a.get("does",""))[:180]}">{esc(aid.split("_")[0])}</span>')

    dom_html = ""
    for r in rows:
        chips = " ".join(chip(a) for a in r["algorithms"])
        fl = " ".join(f'<span class="flow">{esc(f)}</span>' for f in r["flows"]) or "<i>—</i>"
        miss = ("<ul class='miss'>" + "".join(f"<li>{esc(m)}</li>" for m in r["missing"][:2])
                + "</ul>") if r["missing"] else ""
        dom_html += f"""<tr>
      <td class="dom">{esc(r['domain'])}{miss}</td>
      <td class="num">{r['execs']:,}</td>
      <td>{chips}</td><td>{fl}</td>
      <td class="num">{r['tables']}</td><td class="num">{r['cells']}/11</td></tr>"""

    # ---- market comparison ----------------------------------------------
    mkt = ""
    for aid, a in sorted(A.items(), key=lambda x: (x[1].get("origin", ""), x[0])):
        lbl, col = ORIGIN_LABEL.get(a.get("origin"), ("?", "#888"))
        sc = STATE_COLOR.get(a.get("state"), "#888")
        equiv = a.get("market_equivalent") or (
            "ninguno — no existe equivalente comercial" if a.get("origin") == "OURS" else "—")
        ext = a.get("why_extended") or a.get("why_it_matters") or ""
        mkt += f"""<tr>
      <td><b>{esc(aid)}</b><div class="sub">{esc(a.get('does',''))[:150]}</div></td>
      <td><span class="tag" style="background:{col}">{lbl}</span></td>
      <td><span class="tag" style="background:{sc}">{esc(a.get('state',''))}</span></td>
      <td class="sub">{esc(equiv)[:120]}</td>
      <td class="sub">{esc(ext)[:190]}</td>
      <td class="sub fail">{esc(a.get('failure_mode',''))[:170]}</td></tr>"""

    # ---- the nesting DAG -------------------------------------------------
    dag = ""
    for lname, l in nest.items():
        algs = " ".join(chip(a) if a in A else f'<span class="chip">{esc(a)}</span>'
                        for a in l.get("algorithms", []))
        dep = l.get("depends_on")
        dep = ", ".join(dep) if isinstance(dep, list) else str(dep or "")
        dag += (f'<div class="layer"><div class="lname">{esc(lname)}</div>'
                f'<div class="lalgs">{algs}</div>'
                f'<div class="ldep">depende de: {esc(dep)}</div>'
                f'<div class="lnote">{esc(l.get("note") or l.get("produces") or "")}</div></div>')

    p = port.get("portability", {})
    byrung = port.get("by_rung_objects", {})
    inv = p.get("invariant_share_of_resolved_executions", 0)

    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mapa de algoritmos — dominio, mercado y portabilidad</title><style>
:root{{--bg:#0f1218;--card:#171b23;--line:#262c38;--tx:#e6e9ef;--dim:#98a2b3}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:1400px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-size:24px;margin:0 0 6px}} h2{{font-size:17px;margin:34px 0 12px;color:#cbd5e1}}
.lead{{color:var(--dim);max-width:900px;margin-bottom:18px}}
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}}
th{{text-align:left;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--dim);
   padding:10px 12px;border-bottom:1px solid var(--line);background:#131720}}
td{{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
tr:last-child td{{border-bottom:0}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.dom{{font-weight:600;white-space:nowrap}}
.chip{{display:inline-block;border:1px solid;border-radius:5px;padding:1px 6px;margin:1px;font-size:11px;
      font-family:ui-monospace,Menlo,monospace;cursor:help}}
.flow{{display:inline-block;background:#20283a;border-radius:5px;padding:1px 7px;margin:1px;font-size:11px}}
.tag{{display:inline-block;border-radius:5px;padding:2px 8px;font-size:11px;color:#0d1117;font-weight:600}}
.sub{{color:var(--dim);font-size:12px}} .fail{{color:#e0a0a0}}
.miss{{margin:5px 0 0;padding-left:15px;color:#d9822b;font-size:11px;font-weight:400}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:14px 0}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}}
.kpi .v{{font-size:26px;font-weight:600}} .kpi .l{{color:var(--dim);font-size:12px;margin-top:3px}}
.layer{{background:var(--card);border:1px solid var(--line);border-left:3px solid #5b8def;
       border-radius:8px;padding:11px 14px;margin-bottom:8px}}
.lname{{font-family:ui-monospace,monospace;font-size:12px;color:#8ab4ff}}
.lalgs{{margin:5px 0}} .ldep,.lnote{{color:var(--dim);font-size:12px}}
.note{{background:#1a1410;border:1px solid #4a3520;border-left:3px solid #d9822b;
      border-radius:8px;padding:13px 16px;margin:16px 0;color:#e8d5b7}}
.legend{{color:var(--dim);font-size:12px;margin:8px 0 16px}}
@media(max-width:820px){{table{{display:block;overflow-x:auto}}}}
</style></head><body><div class="wrap">

<h1>Mapa de algoritmos</h1>
<p class="lead">Qué algoritmo sirve a cada dominio, qué tomamos del mercado y qué le
cambiamos, y cuánto de todo esto sobreviviría a la instalación #2. Generado desde los
stores — no se edita a mano.</p>

<div class="grid">
  <div class="kpi"><div class="v">{len(A)}</div><div class="l">algoritmos declarados</div></div>
  <div class="kpi"><div class="v" style="color:#2fa37c">{sum(1 for a in A.values() if a.get('origin')=='OURS')}</div>
    <div class="l">sin equivalente de mercado</div></div>
  <div class="kpi"><div class="v" style="color:#5b8def">{sum(1 for a in A.values() if a.get('origin','').startswith('MARKET'))}</div>
    <div class="l">adoptados o extendidos</div></div>
  <div class="kpi"><div class="v" style="color:{'#d64545' if inv<50 else '#2fa37c'}">{inv}%</div>
    <div class="l">de ejecuciones resueltas es invariante de tenant</div></div>
</div>

<div class="note"><b>La distancia al objetivo, medida.</b> Solo el {inv}% de las
ejecuciones resueltas se apoya en la taxonomía propia de SAP. El resto —
{p.get('executions_that_will_not_travel',0):,} ejecuciones sobre
{port.get('what_will_not_travel',{}).get('curated_overlay_entries',0):,} entradas curadas a
mano — descansa en un mapa que escribimos nosotros y que <b>no viaja</b>. No es un defecto
a borrar: los objetos custom no tienen componente SAP por definición, y son justo donde
viven los procesos que nos diferencian. El arreglo es <i>derivar</i> ese mapa de lo que
cada objeto lee y escribe, para que viaje la derivación aunque no viaje el contenido.</div>

<h2>1 · Por dominio — qué algoritmo lo sirve</h2>
<p class="legend">Color del chip = origen: <b style="color:#2fa37c">propio</b> ·
<b style="color:#5b8def">adoptado</b> · <b style="color:#b06fd8">extendido</b>.
Pasa el cursor por un chip para ver qué hace. En naranja, lo que al dominio le falta.</p>
<table><thead><tr><th>dominio</th><th class="num">ejecuciones</th><th>algoritmos</th>
<th>flujos</th><th class="num">tablas</th><th class="num">celdas</th></tr></thead>
<tbody>{dom_html}</tbody></table>

<h2>2 · Frente al mercado — qué adoptamos y qué le cambiamos</h2>
<p class="legend">El motor del campo es <b>pm4py</b> (linaje van der Aalst), el mismo
sustrato que Celonis y Signavio productizaron. Reinventar el descubrimiento de DFG sería
vanidad; el valor está en lo propio y en las extensiones. La última columna es el
<b>modo de fallo</b> — cómo miente cada uno. El mercado no lo publica.</p>
<table><thead><tr><th>algoritmo</th><th>origen</th><th>estado</th>
<th>equivalente de mercado</th><th>qué aporta / por qué se extendió</th>
<th>modo de fallo</th></tr></thead><tbody>{mkt}</tbody></table>

<h2>3 · Anidamiento — la salida de uno es la entrada de otro</h2>
<p class="legend">Un algoritmo no puede ser mejor que sus dependencias. Mejorar una capa
baja levanta todo lo de arriba: el arreglo de L0 llevó la frontera del 40% al 7,7% sin
tocar nada superior.</p>
{dag}

<h2>4 · Peldaños de resolución — y su confianza</h2>
<table><thead><tr><th>peldaño</th><th class="num">objetos</th><th>confianza</th>
<th>¿viaja a otra instalación?</th></tr></thead><tbody>
<tr><td>taxonomía SAP (componente)</td><td class="num">{byrung.get('sap_component',0)}</td>
<td>0.95</td><td style="color:#2fa37c">sí — invariante</td></tr>
<tr><td>taxonomía SAP vía grupo de funciones</td>
<td class="num">{byrung.get('sap_component_via_function_group',0)}</td><td>0.90</td>
<td style="color:#2fa37c">sí — invariante</td></tr>
<tr><td>overlay curado (objetos Z/Y del cliente)</td>
<td class="num">{byrung.get('curated_overlay',0)}</td><td>0.60</td>
<td style="color:#d64545">no — es del tenant</td></tr>
<tr><td>sin resolver</td><td class="num">{byrung.get('unresolved',0)}</td><td>0.00</td>
<td>—</td></tr></tbody></table>

<p class="lead" style="margin-top:26px">Las respuestas de baja confianza <b>son</b> el mapa
de lo que se rompe primero. No una estimación de fragilidad: la lista real.</p>
</div></body></html>"""

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html):,} bytes)")
    print(f"  {len(rows)} domains · {len(A)} algorithms · portability {inv}%")


if __name__ == "__main__":
    main()
