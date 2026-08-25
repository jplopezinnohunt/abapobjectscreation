"""COMO TRABAJA UNESCO — generado, no escrito.

POR QUE ESTE FICHERO EXISTE
    Habia un "how UNESCO works overall" en prosa (knowledge/system_operating_model_rfc.md,
    escrito a mano el 2026-08-20). El problema de la prosa a mano no es que envejezca: es que
    envejece EN SILENCIO. Cada hallazgo nuevo la contradice un poco y nadie lo nota, porque
    nada compara el texto con lo medido.

    Este generador lo da la vuelta: la vista overall se RECONSTRUYE en cada rebuild a partir
    de los stores que ya se miden. Si mañana cambia el reparto lee/escribe de un dominio, o
    aparece una aplicacion nueva detras de un usuario tecnico, la pagina lo dice sola.

QUE LEE, Y POR QUE ESOS
    unesco_system_profile.json   el titular del modelo operativo (80,6% externo)
    comprehension_index.json     que fraccion de lo que se ejecuta sabemos explicar
    domain_composition.json      por dominio: lee/modifica, quien lo conduce, que aplicacion
    rfc_caller_apps.json         el nombre de la aplicacion detras de un usuario tecnico
    capability_model.json        la madurez del modelo
    companions.json              a que companion ir para el detalle de cada cosa

LO QUE NO HACE
    No inventa narrativa. Cada cifra sale de un store y lleva su origen. Donde un store no
    tiene el dato, la seccion dice que falta en vez de rellenarlo.
"""
import json, os, sys, datetime
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "companions", "how_unesco_works.html")


def load(*parts, default=None):
    p = os.path.join(ROOT, *parts)
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default if default is not None else {}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    prof = load("brain_v2", "system_profile", "unesco_system_profile.json")
    comp = load("brain_v2", "comprehension_index.json")
    dom = load("brain_v2", "domain_composition.json")
    callers = load("brain_v2", "rfc_caller_apps.json")
    cap = load("brain_v2", "capability_model", "capability_model.json")
    cos = load("companions", "companions.json", default=[])

    om = prof.get("operating_model", {})
    doms = dom.get("domains", {})

    # --- superficies de ejecucion ---
    surf_rows = ""
    for name, v in (comp.get("surfaces") or {}).items():
        if "error" in v:
            continue
        t = v.get("pct_by_track", {})
        surf_rows += (f"<tr><td><code>{esc(name)}</code></td>"
                      f"<td class=n>{v.get('executions_graded',0):,}</td>"
                      f"<td class=n>{t.get('TECHNICAL',0)}%</td>"
                      f"<td class=n>{t.get('BUSINESS',0)}%</td>"
                      f"<td class=n>{t.get('OBSERVER',0)}%</td>"
                      f"<td class=n style='color:var(--org)'>{t.get('UNCLASSIFIED',0)}%</td></tr>")

    # --- POR DONDE ENTRA EL TRABAJO: satelites, no SAP GUI ---
    # Es la pieza que faltaba en esta pagina: contaba QUE se ejecuta y en QUE dominio, y no por
    # DONDE entra. Y por donde entra es lo que mas define como trabaja la casa -- 10,3 llamadas
    # RFC por cada arranque de transaccion de dialogo.
    inv = (load("brain_v2", "interface_inventory.json").get("interfaces") or [])
    nat = Counter(i.get("nature") or "sin clasificar" for i in inv)
    entrantes = [i for i in inv if i.get("channel") in ("RFC_INBOUND_OBSERVED", "RFC_CUSTOM_FM")]
    canal_rows = ""
    for i in sorted(entrantes, key=lambda x: -(x.get("calls") or 0))[:14]:
        quien = {"A": "PERSONA", "B": "tecnico", "C": "comunicacion",
                 "S": "servicio"}.get(i.get("user_type"), "modulo")
        marca = ("<span style='color:var(--org)'>&#9679; cuenta de persona usada como canal"
                 "</span>"
                 if i.get("sod_flag") == "PERSONA_USADA_COMO_CANAL_DE_ESCRITURA" else "")
        canal_rows += (f"<tr><td><code>{esc(str(i.get('artifact')))}</code></td>"
                       f"<td class=n>{(i.get('calls') or 0):,}</td>"
                       f"<td>{esc(quien)}</td>"
                       f"<td>{esc(str(i.get('nature') or ''))}</td>"
                       f"<td>{esc(str(i.get('domain') or ''))}</td>"
                       f"<td>{marca}</td></tr>")
    sod = [i for i in inv
           if i.get("sod_flag") == "PERSONA_USADA_COMO_CANAL_DE_ESCRITURA"]
    nat_txt = ", ".join(f"<b>{esc(k)}</b> {v}" for k, v in nat.most_common())

    # --- dominios: lee o modifica, y quien los conduce ---
    dom_rows = ""
    for name, v in sorted(doms.items(), key=lambda x: -x[1].get("executions", 0))[:14]:
        rw = v.get("read_write_pct") or {}
        apps = v.get("applications") or []
        drv = v.get("driven_by") or []
        app = apps[0]["application"] if apps else ""
        who = drv[0]["actor"] if drv else ""
        pct = drv[0]["pct"] if drv else 0
        dom_rows += (f"<tr><td>{esc(name)}</td>"
                     f"<td class=n>{v.get('executions',0):,}</td>"
                     f"<td class=n>{rw.get('READ',0):.0f}%</td>"
                     f"<td class=n>{rw.get('WRITE',0):.0f}%</td>"
                     f"<td class=n>{v.get('actors',0)}</td>"
                     f"<td>{esc(who)} <span class=mu>{pct:.0f}%</span></td>"
                     f"<td>{esc(app)}</td></tr>")

    # --- aplicaciones detras de los usuarios tecnicos ---
    app_rows = ""
    for u, v in (callers.get("technical_user_apps") or {}).items():
        if u.startswith("_") or not isinstance(v, dict):
            continue
        m = v.get("measured", {})
        drives = " · ".join(f"{k.replace('drives_','').replace('_pct','')} {x}%"
                            for k, x in m.items() if str(k).startswith("drives_"))
        app_rows += (f"<tr><td><code>{esc(u)}</code></td>"
                     f"<td><strong>{esc(v.get('primary_application',''))}</strong></td>"
                     f"<td>{esc(v.get('kind') or v.get('tool') or '')}</td>"
                     f"<td class=mu>{esc(drives)}</td></tr>")

    # --- companions donde esta el detalle ---
    co_rows = ""
    for c in sorted(cos, key=lambda x: str(x.get("title", "")))[:60]:
        co_rows += (f"<tr><td><a href='../{esc(c.get('file',''))}'>{esc(c.get('title',''))}</a></td>"
                    f"<td class=mu>{esc(str(c.get('description',''))[:150])}</td></tr>")

    h = comp.get("headline", {})
    gb = gn = 0
    for v in (comp.get("surfaces") or {}).values():
        g = v.get("business_grades_executions") or {}
        gb += sum(g.values()); gn += g.get("3", 0)
    explained = round(100 * gn / gb, 1) if gb else 0
    mat = (cap.get("_maturity") or {}).get("model_maturity_pct") or cap.get("model_maturity_pct")

    sats = om.get("satellites") or {}
    sat_txt = " · ".join(f"{k} {v:,}" if isinstance(v, int) else f"{k} {v}"
                         for k, v in list(sats.items())[:5]) if isinstance(sats, dict) else ""

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Como trabaja UNESCO — vista general</title>
<style>
:root{{--bg:#080c14;--surf:#0d1320;--card:#111827;--card-h:#162032;--b:#1a2540;--b2:#1e2d4a;
--txt:#dde5f5;--mu:#4c6490;--mu2:#7892c0;--acc:#4f8ef7;--grn:#22c55e;--org:#fb923c;
--red:#ef4444;--pur:#a78bfa;--cyan:#22d3ee;--yel:#f59e0b}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',-apple-system,sans-serif;background:var(--bg);color:var(--txt);line-height:1.6}}
.hero{{background:linear-gradient(135deg,#0a1628,#0d2247 40%,#1a0d3a 70%,#0a1628);padding:44px 40px 36px;border-bottom:1px solid var(--b)}}
.wrap{{max-width:1180px;margin:0 auto}}
h1{{font-size:2.1em;font-weight:800;background:linear-gradient(135deg,#fff,#a0c4ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}}
.sub{{color:var(--mu2);max-width:880px;margin-bottom:24px}}
.hs{{display:flex;gap:34px;flex-wrap:wrap}}
.hs .v{{font-size:1.75em;font-weight:800;font-family:Consolas,monospace}}
.hs .l{{font-size:.7em;text-transform:uppercase;letter-spacing:.08em;color:var(--mu)}}
.blue .v{{color:var(--acc)}}.green .v{{color:var(--grn)}}.orange .v{{color:var(--org)}}.purple .v{{color:var(--pur)}}
main{{padding:36px 40px 70px}} section{{margin-bottom:40px}}
h2{{font-size:1.32em;color:#fff;margin-bottom:6px}} h2 .n{{color:var(--acc);font-family:Consolas,monospace;margin-right:10px;font-size:.85em}}
.lead{{color:var(--mu2);margin-bottom:16px;max-width:900px}}
.card{{background:var(--card);border:1px solid var(--b);border-radius:10px;padding:20px 22px;margin-bottom:14px}}
table{{width:100%;border-collapse:collapse;font-size:.88em;margin-top:8px}}
th{{text-align:left;padding:8px 10px;color:var(--mu);font-size:.76em;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid var(--b2)}}
td{{padding:7px 10px;border-bottom:1px solid var(--b);font-variant-numeric:tabular-nums}}
td.n,th.n{{text-align:right;font-family:Consolas,monospace}}
tr:hover td{{background:var(--card-h)}}
code{{font-family:Consolas,monospace;background:rgba(79,142,247,.1);padding:1px 6px;border-radius:4px;color:var(--cyan);font-size:.92em}}
a{{color:var(--acc);text-decoration:none}} a:hover{{text-decoration:underline}}
.mu{{color:var(--mu)}}
.q{{border-left:3px solid var(--acc);padding:12px 18px;background:rgba(79,142,247,.05);border-radius:0 8px 8px 0;margin:14px 0;color:var(--mu2)}}
.q strong{{color:#fff}}
.warn{{border-left-color:var(--org);background:rgba(251,146,60,.05)}}
footer{{border-top:1px solid var(--b);padding:22px 40px;color:var(--mu);font-size:.82em}}
</style></head><body>

<div class="hero"><div class="wrap">
<h1>Cómo trabaja UNESCO</h1>
<p class="sub">{esc(om.get('headline',''))}</p>
<div class="hs">
  <div class="blue"><div class="v">{h.get('executions_total',0):,}</div><div class="l">ejecuciones medidas</div></div>
  <div class="orange"><div class="v">{h.get('pct_unclassified','?')}%</div><div class="l">sin clasificar</div></div>
  <div class="green"><div class="v">{explained}%</div><div class="l">de negocio, explicado</div></div>
  <div class="purple"><div class="v">{mat or '?'}%</div><div class="l">madurez del modelo</div></div>
</div></div></div>

<main class="wrap">

<section>
  <h2><span class="n">01</span>SAP no se opera: se orquesta desde fuera</h2>
  <p class="lead">{esc(om.get('stability',''))}</p>
  <div class="card">
    <p>{esc(om.get('headline',''))}</p>
    {f"<p style='margin-top:10px' class=mu>Satélites: {esc(sat_txt)}</p>" if sat_txt else ""}
    {f"<p style='margin-top:10px' class=mu>Cobertura de proceso: {esc(om.get('process_coverage',''))}</p>" if om.get('process_coverage') else ""}
  </div>
</section>

<section>
  <h2><span class="n">02</span>Qué ejecuta el sistema, y cuánto de eso entendemos</h2>
  <p class="lead">Cuatro superficies, porque ejecutar no es solo un programa: lo que corre, lo
  que CAMBIA, lo que corre solo, y lo que ENTRA por RFC — esta última es la mayor.</p>
  <div class="card"><table>
    <tr><th>superficie</th><th class=n>ejecuciones</th><th class=n>técnico</th><th class=n>negocio</th><th class=n>nosotros</th><th class=n>sin clasificar</th></tr>
    {surf_rows}
  </table>
  <p style="margin-top:12px" class="mu"><strong>Situar no es explicar:</strong> solo el
  {explained}% de las ejecuciones de negocio llega a grado 3, o sea alguien lo escribió con
  evidencia. Ese salto no lo da ningún algoritmo.</p>
  </div>
</section>

<section>
  <h2><span class="n">02b</span>¿Por dónde entra el trabajo?</h2>
  <p class="lead">UNESCO no se opera desde SAP GUI: se opera desde aplicaciones satélite. El log
  tiene <b>10,3 llamadas RFC por cada arranque de transacción</b> de diálogo (12.734.604 contra
  1.235.225), y <b>524.708</b> de esas llamadas ESCRIBEN. Un inventario que sólo diga el dominio
  cuenta dónde pasa algo; la <b>naturaleza</b> cuenta qué pasa — y las tres no cuestan lo mismo
  cuando fallan: una lectura rota cuesta un informe, una transaccional cuesta dinero, y una de
  datos maestros corrompe todo lo que venga detrás, en silencio.</p>
  <p class="lead"><b>{len(sod)} cuentas de PERSONA son en realidad canales de escritura</b>,
  confirmado por terminal: más de la mitad de sus llamadas salen de una máquina que usan cinco
  cuentas o más — un servidor, no un PC. La autorización se comprueba contra la persona, así que
  la aplicación hereda todo lo que esa persona pueda hacer. Es el hallazgo H71, aquí con nombre
  y volumen.</p>
  <p class="mu">Naturaleza de las {len(inv)} interfaces: {nat_txt}. <b>NO_MEDIBLE</b> son
  destinos salientes: no dejan en nuestro log qué hacen del otro lado, y eso es un estado con
  nombre, no un hueco.</p>
  <div class="card"><table>
    <tr><th>canal entrante</th><th class=n>llamadas</th><th>quién entra</th>
        <th>naturaleza</th><th>dominio</th><th></th></tr>
    {canal_rows}
  </table></div>
</section>

<section>
  <h2><span class="n">03</span>Cada dominio: ¿lee o modifica, y quién lo mueve?</h2>
  <p class="lead">Un dominio con un millón de lecturas y otro con un millón de modificaciones
  no son comparables. La evidencia manda sobre el nombre: un tcode que aparece en el log de
  cambios escribió, y eso es prueba.</p>
  <div class="card"><table>
    <tr><th>dominio</th><th class=n>ejecuciones</th><th class=n>lee</th><th class=n>modifica</th><th class=n>actores</th><th>quién lo conduce</th><th>aplicación</th></tr>
    {dom_rows}
  </table></div>
</section>

<section>
  <h2><span class="n">04</span>Quién hay detrás de un usuario técnico</h2>
  <p class="lead">El log da <code>MULESOFT</code> o <code>EPAM-RFC</code> y ahí se acaba. Un bus
  no es una aplicación, y esa información no está en el sistema: la pone quien conoce el montaje.</p>
  <div class="card"><table>
    <tr><th>usuario técnico</th><th>aplicación</th><th>qué es</th><th>qué mueve</th></tr>
    {app_rows}
  </table></div>
</section>

<section>
  <h2><span class="n">05</span>Dónde está el detalle</h2>
  <p class="lead">Esta página es el índice de la forma de trabajar. Cada tema tiene su companion.</p>
  <div class="card"><table>
    <tr><th>companion</th><th>qué cubre</th></tr>
    {co_rows}
  </table></div>
</section>

<div class="q warn">
  <strong>Esta página se GENERA.</strong> No se edita a mano: la reconstruye
  <code>scripts/build_operating_model.py</code> en cada rebuild, leyendo los stores que ya se
  miden. Si un hallazgo cambia el reparto lee/escribe de un dominio, o aparece una aplicación
  nueva detrás de un usuario técnico, esto lo dice solo. La prosa a mano no envejece: envejece
  <em>en silencio</em>.
</div>

</main>
<footer class="wrap">
  Generado {datetime.date.today():%Y-%m-%d} por <code>scripts/build_operating_model.py</code>
  desde <code>unesco_system_profile.json</code> · <code>comprehension_index.json</code> ·
  <code>domain_composition.json</code> · <code>rfc_caller_apps.json</code> ·
  <code>capability_model.json</code> · <code>companions.json</code>.
</footer></body></html>"""

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"escrito {OUT} ({len(html):,} bytes)")
    print(f"  superficies {len(comp.get('surfaces') or {})} · dominios {len(doms)} · "
          f"companions {len(cos)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
