"""
build_master_data_companion.py — genera companions/master_data_governance.html

El companion es GENERADO, nunca se edita a mano: la fuente es
brain_v2/master_data_registry.json (los tipos de objeto y su estado MEDIDO) mas el proceso
de 7 pasos de knowledge/domains/Master_Data_Governance/gl_account_creation_process.md.

Se engancha en rebuild_all.py. Editar el builder, no el HTML.
"""
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
REG = os.path.join(REPO, "brain_v2", "master_data_registry.json")
OUT = os.path.join(REPO, "companions", "master_data_governance.html")

CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:#222;max-width:1000px;margin:30px auto;padding:0 20px;line-height:1.55}
h1{color:#08305f;font-size:21px;border-bottom:3px solid #08305f;padding-bottom:6px;margin:0 0 4px 0}
h2{color:#08305f;font-size:15px;margin:26px 0 6px 0;border-bottom:1px solid #d4d9e0;padding-bottom:3px}
h3{color:#08305f;font-size:13px;margin:16px 0 4px 0}
.tag{display:inline-block;background:#08305f;color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600;letter-spacing:.4px;margin-right:6px}
.sub{font-size:11px;color:#666;margin:4px 0 18px 0}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}
.kpi{background:#f4f5f7;padding:10px;border-radius:5px;border-left:3px solid #08305f}
.kpi.red{border-left-color:#c5283d}.kpi.amber{border-left-color:#ff9f1c}.kpi.green{border-left-color:#2a9d8f}
.kpi .v{font-size:19px;font-weight:700;color:#08305f}
.kpi.red .v{color:#c5283d}.kpi.amber .v{color:#a86c00}.kpi.green .v{color:#0a7e6e}
.kpi .l{font-size:10px;color:#666;text-transform:uppercase;letter-spacing:.4px;margin-top:2px}
table{width:100%;border-collapse:collapse;font-size:12px;margin:8px 0}
th{background:#e0ecf8;color:#08305f;text-align:left;padding:5px 8px;font-size:11px;text-transform:uppercase;letter-spacing:.3px}
td{padding:5px 8px;border-bottom:1px solid #eceff3;vertical-align:top}
tr:hover td{background:#fafbfc}
code{background:#eef1f5;padding:1px 4px;border-radius:3px;font-family:Consolas,Monaco,monospace;font-size:11px}
.pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:10px;font-weight:700;letter-spacing:.3px}
.p-ok{background:#d8f3ef;color:#0a7e6e}.p-mid{background:#ffeccc;color:#a86c00}
.p-no{background:#fadde1;color:#a01829}.p-na{background:#e8eaee;color:#5a6270}
.box{background:#f7f9fc;border-left:3px solid #08305f;padding:10px 14px;margin:12px 0;font-size:12.5px}
.box.warn{border-left-color:#c5283d;background:#fdf5f6}
.box.good{border-left-color:#2a9d8f;background:#f3fbfa}
.flow{font-family:Consolas,Monaco,monospace;font-size:11.5px;background:#0f2440;color:#d6e4f5;padding:12px 14px;border-radius:5px;white-space:pre;overflow-x:auto}
ol.steps{padding-left:0;list-style:none;counter-reset:s}
ol.steps li{counter-increment:s;position:relative;padding:8px 0 8px 40px;border-bottom:1px solid #eceff3;font-size:12.5px}
ol.steps li:before{content:counter(s);position:absolute;left:0;top:8px;width:24px;height:24px;background:#08305f;color:#fff;border-radius:50%;text-align:center;line-height:24px;font-size:11px;font-weight:700}
ol.steps li.zero:before{content:"0";background:#c5283d}
.small{font-size:11px;color:#666}
"""

PILL = {"MECANIZADO": ("p-ok", "MECANIZADO"),
        "CANAL_SIN_EJECUTOR": ("p-mid", "CANAL, SIN EJECUTOR"),
        "SIN_CANAL": ("p-no", "SIN CANAL"),
        "NO_APLICA": ("p-na", "NO APLICA")}


def esc(x):
    return (str(x) if x is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def nombre_corto(tool):
    """Acorta una RUTA, no la prosa que la acompaña.

    Aqui habia `os.path.basename(tool)`, y funcionaba mientras `tool` fuera solo una ruta.
    Cuando el registro paso a llevar texto rico -- «ob09_vs_variant_check.py (claim 599, A47
    state=DEFECTO_VIVO): NO VALIDO para cuenta ASOCIADA... BSID/BSIK» -- basename() corto por
    la ULTIMA barra y devolvio «BSIK...», comiendose el nombre del instrumento y dejando en su
    sitio un trozo del aviso. Un agente lo detecto al regenerar, vio que el resultado era PEOR
    y revirtio; el companion se quedo sin la advertencia.

    Regla: solo se acorta el PRIMER token si parece una ruta a fichero; el resto se conserva
    tal cual. Lo que el registro tenga que decir es exactamente lo que hay que enseñar.
    """
    s = str(tool or "").strip()
    if not s:
        return s
    cabeza, sep, resto = s.partition(" ")
    if ("/" in cabeza or "\\" in cabeza) and re.search(r"\.\w{1,4}$", cabeza):
        cabeza = os.path.basename(cabeza)
    return cabeza + sep + resto


def main():
    reg = json.load(io.open(REG, encoding="utf-8"))
    objs = reg["objects"]
    meta = reg["_meta"]
    n_mec = sum(1 for o in objs if o["status"] == "MECANIZADO")
    n_can = sum(1 for o in objs if o["status"] == "CANAL_SIN_EJECUTOR")
    n_sin = sum(1 for o in objs if o["status"] == "SIN_CANAL")

    h = []
    a = h.append
    a('<!DOCTYPE html>\n<html lang="es"><head><meta charset="utf-8">')
    a("<title>Master Data Governance — el registro de objetos y su proceso</title>")
    a("<style>%s</style></head><body>" % CSS)
    a('<h1>Master Data Governance</h1>')
    a('<div class="sub"><span class="tag">DOMINIO CROSS</span>'
      '<span class="tag">PROCESO P2D</span>'
      'Quien pide un dato maestro, quien lo crea, y — la parte que se pierde — '
      '<b>que tareas dispara despues</b>. Medido %s (sesion %s).</div>'
      % (esc(meta["measured_on"]), esc(meta["session"])))

    a('<div class="kpis">')
    a('<div class="kpi green"><div class="v">%d</div><div class="l">tipo mecanizado</div></div>' % n_mec)
    a('<div class="kpi amber"><div class="v">%d</div><div class="l">canal medido, sin ejecutor</div></div>' % n_can)
    a('<div class="kpi red"><div class="v">%d</div><div class="l">sin canal RFC</div></div>' % n_sin)
    a('<div class="kpi red"><div class="v">33</div><div class="l">cuentas de retraso en V01</div></div>')
    a("</div>")

    a('<div class="box warn"><b>El fallo estructural.</b> El usuario crea el dato maestro '
      '<b>directamente en P01</b> y solo avisa <b>cuando hace falta revaluar</b>. Las altas que no '
      'llevan revaluacion no generan aviso: nadie sabe que existen hasta que algo falla en dev. '
      'Las 33 cuentas de retraso de V01 son el sedimento de todas esas altas silenciosas. '
      '<b>Por eso el paso 0 no puede ser una notificacion: tiene que ser un barrido programado.</b></div>')

    a("<h2>La asimetria: maestro y configuracion viajan en sentidos opuestos</h2>")
    a('<div class="flow">MAESTRO  (SKA1/SKB1/SKAT)          P01  --&gt;  D01 . V01'
      '        nace en PRODUCCION, se rellena hacia atras\n'
      'CONFIG   (OB09 . variante . FSV)   D01  --&gt;  V01  --&gt;  P01   nace en DESARROLLO, '
      'sube por transporte</div>')
    a('<p class="small">Nadie los ve como un solo proceso porque tienen direcciones contrarias. '
      'Ahi es donde se pierde el trabajo posterior al alta.</p>')

    a("<h2>El proceso operativo — 7 pasos</h2>")
    gl = [o for o in objs if o["id"] == "GL_ACCOUNT"][0]
    a('<ol class="steps">')
    a('<li class="zero"><b>DETECTAR la deriva.</b> El aviso solo llega si hay revaluacion. '
      'Programado, no bajo demanda. &rarr; <code>%s</code></li>' % esc(gl["gap_check"]))
    for t in gl["post_creation_tasks"]:
        tool = t["tool"]
        a("<li><b>%s</b>%s</li>"
          % (esc(t["task"]),
             "" if tool == "-" else " &rarr; <code>%s</code>" % esc(nombre_corto(tool))))
    a("</ol>")
    a('<div class="box"><b>Los pasos 3 y 4 son los que se olvidan, y cada uno falla en silencio.</b> '
      'OB09 sin variante: la revaluacion no corre y no da error. Variante sin OB09: F.05 revienta. '
      'Y la cobertura de balance se asigna por <b>intervalo</b>, asi que una cuenta nueva entra sola '
      'o cae en <i>Not assigned</i> — y el balance cuadra igual.</div>')
    a('<div class="box good"><b>Prueba de que el tipo de cuenta NO decide si se revalua.</b> '
      '<code>4041018</code> y <code>4041019</code> son ambas de inversion, del mismo formulario y del '
      'mismo dia. La 18 revalua; la 19 no, porque esta en USD sobre una sociedad en USD. '
      'El tipo decide el <i>metodo</i> y las cuentas de contrapartida de <code>T030H</code>, '
      'no el <i>si</i>.</div>')
    a('<div class="box warn"><b>Prueba de que el paso 6 hace falta.</b> El barrido de la poblacion '
      'encontro <code>4041011</code>: 10 M EUR netos abiertos, <code>T030H</code> configurado, '
      '<b>en ninguna variante de F.05</b>. Nadie la habia pedido.</div>')

    a("<h2>Los objetos de datos maestros — estado medido</h2>")
    a('<p class="small">%s</p>' % esc(meta["evidence"]))
    a("<table><tr><th>Objeto</th><th>Tablas</th><th>Tx</th><th>Canal de escritura (medido)</th>"
      "<th>Ejecutor</th><th>Estado</th></tr>")
    order = {"MECANIZADO": 0, "CANAL_SIN_EJECUTOR": 1, "SIN_CANAL": 2, "NO_APLICA": 3}
    for o in sorted(objs, key=lambda x: (order.get(x["status"], 9), x["name"])):
        cls, lab = PILL.get(o["status"], ("p-na", o["status"]))
        w = (o.get("channel") or {}).get("write")
        a("<tr><td><b>%s</b></td><td><code>%s</code></td><td>%s</td><td>%s</td>"
          "<td>%s</td><td><span class='pill %s'>%s</span></td></tr>"
          % (esc(o["name"]), esc(" . ".join(o.get("tables", []) or ["-"])),
             esc(o.get("transaction", "-")),
             ("<code>%s</code>" % esc(w)) if w else "<i>ninguno</i>",
             ("<code>%s</code>" % esc(nombre_corto(o["executor"]))) if o.get("executor")
             else "<i>-</i>", cls, lab))
    a("</table>")

    notas = [o for o in objs if o.get("correction") or o.get("risk") or o.get("note")
             or (o.get("channel") or {}).get("note")]
    if notas:
        a("<h3>Lo que hay que saber de cada uno</h3><table><tr><th>Objeto</th><th>Nota</th></tr>")
        for o in notas:
            for txt in filter(None, [o.get("correction"), o.get("risk"), o.get("note"),
                                     (o.get("channel") or {}).get("note")]):
                a("<tr><td><b>%s</b></td><td>%s</td></tr>" % (esc(o["name"]), esc(txt)))
        a("</table>")

    a("<h2>Lo que este dominio todavia no sabe</h2><ul>")
    for u in ["Quien es el dueno de las tareas POSTERIORES al alta. Hoy llegan por correo a quien "
              "las reciba, y ese es el agujero.",
              "Que tareas posteriores dispara el alta de un centro de coste, un fondo o un "
              "proyecto. Solo esta medida la cadena de la cuenta de mayor.",
              "Si el formulario AM 3-11 se archiva en algun sitio consultable, o vive solo en la "
              "cadena de correo.",
              "Si FRA valida el campo <i>GL to be revaluated</i>, o solo el alta."]:
        a("<li>%s</li>" % u)
    a("</ul>")
    a('<p class="small">Generado por <code>scripts/build_master_data_companion.py</code> desde '
      '<code>brain_v2/master_data_registry.json</code>. No editar este HTML a mano.</p>')
    a("</body></html>")

    io.open(OUT, "w", encoding="utf-8").write("\n".join(h))
    print("companion generado: %s (%d tipos, %d bytes)"
          % (os.path.relpath(OUT, REPO), len(objs), os.path.getsize(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
