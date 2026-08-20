# -*- coding: utf-8 -*-
"""Genera companions/unesco_bank_operation_design.html — el diseno operativo de la banca.

POR QUE ES GENERADO Y NO ESCRITO A MANO
    Regla feedback_landing_page_is_generated: si la pagina se edita a mano se queda vieja
    en cuanto cambia un banco. Aqui la fuente es brain_v2/house_bank_roles.json, que a su
    vez se deriva de REGUH + LFBK + T042Z + T001 en cada rebuild. Se edita ESTE fichero.

QUE RESPONDE
    Que TIPOS de banco tenemos, que hace cada tipo, y en que tipo cae cada banco.
    Nace de la pregunta de JP tras cerrar Egipto: "faltaba entender como operan los bancos".

Nodo de conocimiento: knowledge/domains/Treasury/house_bank_operating_roles.md
Claims 530 · 531 · 532.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "brain_v2", "house_bank_roles.json")
OUT = os.path.join(ROOT, "companions", "unesco_bank_operation_design.html")

CSS = """body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:#222;max-width:1000px;margin:30px auto;padding:0 20px;line-height:1.55}
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
th{background:#e0ecf8;color:#08305f;text-align:left;padding:5px 8px;font-weight:600}
td{padding:5px 8px;border-bottom:1px solid #d4d9e0;vertical-align:top}
td.n{text-align:right;font-variant-numeric:tabular-nums}
code{background:#f1f3f6;padding:1px 5px;border-radius:3px;font-size:11.5px;font-family:"SF Mono",Consolas,monospace}
pre{background:#0f1b2b;color:#dfe7f0;padding:12px 14px;border-radius:5px;font-size:11.5px;overflow-x:auto;line-height:1.5}
pre .c{color:#7f9ab5}pre .h{color:#ff6b7a;font-weight:700}pre .g{color:#7fd18c}
.callout{background:#fff4d6;border-left:4px solid #ff9f1c;padding:10px 14px;margin:12px 0;border-radius:3px;font-size:13px}
.callout.red{background:#ffe4e6;border-left-color:#c5283d}
.callout.green{background:#d9f2ee;border-left-color:#2a9d8f}
.callout.navy{background:#e8eef6;border-left-color:#08305f}
.pill{display:inline-block;background:#e0ecf8;color:#08305f;padding:1px 7px;border-radius:10px;font-size:10.5px;font-weight:600;margin-right:4px}
.pill.red{background:#ffe4e6;color:#c5283d}.pill.green{background:#d9f2ee;color:#0a7e6e}.pill.amber{background:#fff4d6;color:#a86c00}
footer{margin-top:26px;font-size:10px;color:#666;border-top:1px solid #d4d9e0;padding-top:8px}"""

# Que ES cada tipo y que HACE. La regla de derivacion va al lado del significado a proposito:
# un tipo cuyo criterio no se ve es una etiqueta, no una clasificacion.
TYPES = [
    ("HUB GLOBAL", "green",
     "El concentrador. Paga a casi cualquier parte del mundo y para mas de una sociedad. "
     "Es el que produce el grueso del fichero y el unico cuya familia de pais selecciona la "
     "clase BAdI que despacha purpose codes.",
     "&ge;150 paises de destino distintos",
     "Todo requisito regulatorio sobre un corredor pasa casi seguro por aqui. Es el primer "
     "banco al que preguntar."),
    ("HUB REGIONAL", "",
     "Concentra un area o una divisa. Alcanza decenas de paises pero no el mundo entero, y "
     "normalmente sirve a una sola sociedad.",
     "entre 15 y 149 paises de destino",
     "Puede llevar una parte relevante de un corredor sin ser el dominante: mirar su cuota "
     "antes de descartarlo."),
    ("LOCAL (oficina de campo)", "amber",
     "La cuenta de una oficina sobre el terreno. Paga casi todo dentro de su propio pais, a "
     "beneficiarios con banco local.",
     "un destino se lleva &ge;70% y el domestico es &ge;60%",
     "<strong>Sus pagos son DOMESTICOS: no necesitan purpose code ni direccion estructurada "
     "transfronteriza.</strong> Todo requisito cross-border que les llegue es sobre-captura."),
    ("CORREDOR ESTRECHO", "",
     "Pocos destinos y sin dominar ninguno con claridad. Suelen ser cuentas de proposito "
     "acotado o en desuso.",
     "&lt;15 destinos y ninguno con &ge;70%",
     "Revisar si sigue vivo antes de construir nada para el."),
    ("SIN DESTINO CONOCIDO", "red",
     "Mueve dinero pero no sabemos hacia donde: sus beneficiarios no tienen registro de banco "
     "en <code>LFBK</code>.",
     "0 paises de destino resolubles",
     "No es que no pague: es que <strong>no lo vemos</strong>. Ningun control que dependa del "
     "pais del banco del beneficiario puede actuar aqui."),
]


def esc(x):
    return (str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build():
    if not os.path.exists(SRC):
        print("  falta %s -- ejecuta antes: python brain_v2/house_bank_roles.py" % SRC)
        return 2
    doc = json.load(io.open(SRC, encoding="utf-8"))
    banks = doc["banks"]
    live = [b for b in banks if b["lines"] >= 50]
    by_topo = {}
    for b in live:
        by_topo.setdefault(b["topology"], []).append(b)

    total_lines = sum(b["lines"] for b in banks)
    hubs = [b for b in live if b["topology"].startswith("HUB")]
    locals_ = by_topo.get("LOCAL (oficina de campo)", [])
    max_dest = max((b["destination_countries"] for b in banks), default=0)
    ppc_banks = [b for b in live if b["ppc"]["dispatches_ppc"]]

    h = []
    a = h.append
    a('<meta charset="utf-8"><title>UNESCO — Bank Operation Design</title><style>%s</style>' % CSS)
    a('<h1><span class="tag">MODELO</span>UNESCO &mdash; Bank Operation Design</h1>')
    a('<p class="sub">Que tipos de banco operamos, que hace cada tipo y en que tipo cae cada banco. '
      '<strong>Pagina GENERADA</strong> desde <code>brain_v2/house_bank_roles.json</code> '
      '&mdash; se edita <code>scripts/build_bank_operation_design.py</code>, nunca este HTML. '
      'Nodo de conocimiento: <code>knowledge/domains/Treasury/house_bank_operating_roles.md</code></p>')

    a('<div class="kpis">')
    a('<div class="kpi"><div class="v">%d</div><div class="l">bancos casa con actividad</div></div>' % len(live))
    a('<div class="kpi green"><div class="v">%d</div><div class="l">hubs concentradores</div></div>' % len(hubs))
    a('<div class="kpi amber"><div class="v">%d</div><div class="l">bancos locales de oficina</div></div>' % len(locals_))
    a('<div class="kpi"><div class="v">%d</div><div class="l">paises alcanzados por el hub global</div></div>' % max_dest)
    a('</div>')

    a('<div class="callout navy"><strong>De donde sale esto y por que existe.</strong> '
      'En agosto de 2026 se construyo y probo entero un requisito de Purpose of Payment para Egipto '
      'que resulto no hacer falta: el banco que lo pedia movia el 0,9% de ese corredor, en cheque. '
      'El dato estaba medido tres dias antes y disperso en prosa. Lo que faltaba no era una regla que '
      'recordar &mdash; era saber <strong>como opera cada banco</strong>. Esta pagina es ese modelo. '
      '<span class="pill red">claim 530</span></div>')

    # -------- 1. los tipos
    a('<h2>1 &middot; Los tipos de banco, y que hace cada uno</h2>')
    a('<p style="font-size:12.5px">Un concentrador no se distingue de una cuenta de oficina por el '
      '<em>volumen</em> sino por la <strong>diversidad de destinos</strong>. El hub global alcanza '
      '%d paises; una oficina de campo alcanza tres. El criterio va al lado del significado a '
      'proposito: un tipo cuyo criterio no se ve es una etiqueta, no una clasificacion.</p>' % max_dest)
    a('<table><tr><th style="width:17%">Tipo</th><th style="width:30%">Que es</th>'
      '<th style="width:18%">Como se deriva</th><th>Que implica operativamente</th>'
      '<th class="n">bancos</th></tr>')
    for name, cls, what, how, implies in TYPES:
        n = len(by_topo.get(name, []))
        pill = '<span class="pill %s">%s</span>' % (cls, esc(name)) if cls else \
               '<span class="pill">%s</span>' % esc(name)
        a('<tr><td>%s</td><td>%s</td><td><code>%s</code></td><td>%s</td><td class="n">%d</td></tr>'
          % (pill, what, how, implies, n))
    a('</table>')
    a('<div class="callout"><strong>Y una segunda dimension, independiente del tipo: PAPEL.</strong> '
      'Un banco cuyos metodos llevan <code>T042Z-XSCHK=\'X\'</code> emite cheque y <strong>no produce '
      'fichero SAP</strong>. No hay nada que corregir en un fichero que no existe &mdash; y eso, y no '
      'otra cosa, es lo que dejo fuera a la cuenta de Citibank Egipto.</div>')

    # -------- 2. los tres ejes
    a('<h2>2 &middot; Tres capas sobre el mismo pago, tres ejes distintos <span class="pill red">claim 532</span></h2>')
    a('<p style="font-size:12.5px">Esta es la parte que no estaba escrita en ningun sitio, y explica '
      'la mayoria de las sorpresas de este dominio.</p>')
    a('<table><tr><th>Capa</th><th>Se clava en</th><th>Consecuencia</th></tr>')
    a('<tr><td><strong>Captura</strong> &mdash; <code>u917</code> bloquea la contabilizacion</td>'
      '<td>el pais del banco del <strong>BENEFICIARIO</strong> (<code>LFBK-BANKS</code>)</td>'
      '<td>no mira por donde sale el dinero</td></tr>')
    a('<tr><td><strong>Fichero</strong> &mdash; BAdI &rarr; arbol DMEE</td>'
      '<td>el pais de <strong>NUESTRO</strong> banco casa (<code>FPAYHX-UBISO</code>)</td>'
      '<td>solo la familia FR despacha purpose codes</td></tr>')
    a('<tr><td><strong>Aprobacion</strong> &mdash; BCM</td>'
      '<td><code>ZBUKR</code> + techo de importe (y <code>ZLAND</code>/<code>ZBNKS</code> para agrupar el lote)</td>'
      '<td><strong>el banco casa no entra</strong>: <code>HBKID</code> no aparece ni en '
      '<code>bcm_grouping_rule_selop</code> ni en <code>bcm_node_selection_criteria</code></td></tr>')
    a('</table>')
    a('<div class="callout red"><strong>Lo que esto produce.</strong> Captura y fichero no coinciden: '
      'de 47.399 lineas capturadas en los nueve paises con purpose code, <strong>solo el 80% llega a un '
      'fichero</strong>. Casi 9.500 pagos obligan a rellenar un campo que se descarta. El caso mas puro '
      'son <strong>171 lineas domesticas</strong> &mdash; Jordania 150, Marruecos 21 &mdash; pagadas de un '
      'banco casa LOCAL a un beneficiario LOCAL: se les exige un codigo transfronterizo en un pago que no '
      'cruza ninguna frontera, y luego se tira.<br><br>'
      'Y la aprobacion es ciega a todo esto: un pago domestico desde una oficina de campo y uno '
      'transfronterizo desde el hub de Paris siguen la misma logica si coinciden sociedad e importe. '
      'Puede ser politica deliberada &mdash; pero hoy no es visible, asi que nadie la ha decidido a '
      'proposito. <span class="pill red">claim 531</span></div>')

    # -------- 3. la regla de negocio
    a('<h2>3 &middot; La regla que gobierna: domestico no, cross-border si</h2>')
    a('<p style="font-size:12.5px">El purpose code &mdash; y en general el requisito de informar sobre '
      'el pago &mdash; es <strong>transfronterizo</strong>. El banco local no lo pide. Y la clasificacion '
      '<em>ya estaba escrita en SAP</em>, en el texto del metodo de pago (<code>T042Z-TEXT1</code>, pais FR): '
      'llevabamos meses leyendo los metodos como claves de enrutado y nunca como lo que tambien son, una '
      'afirmacion sobre que clase de pago es cada uno.</p>')
    a('<table><tr><th>Metodo</th><th>Texto en SAP</th><th>Eje</th><th>Formato</th></tr>')
    for m, t, e, f in (("L", "Payments in US in USD only", "DOMESTICO US", "/CITI/XML/UNESCO/DC_V3_01"),
                       ("N", "Payments outside US non-EUR", "INTERNACIONAL", "/CGI_XML_CT_UNESCO"),
                       ("H", "Euro Payments France", "DOMESTICO FR", "/CMI101"),
                       ("I", "Euro Payment SEPA zone", "ZONA", "/CMI101"),
                       ("J", "Euro Payment outside SEPA-zone", "INTERNACIONAL", "/CGI_XML_CT_UNESCO"),
                       ("S", "SEPA Payment", "ZONA", "/SEPA_CT_UNES"),
                       ("3", "Manual cheque (Pre-Numbered)", "&mdash;", "ninguno &mdash; <code>XSCHK=&#39;X&#39;</code>")):
        a('<tr><td><code>%s</code></td><td>%s</td><td><strong>%s</strong></td><td><code>%s</code></td></tr>'
          % (m, t, e, f))
    a('</table>')
    a('<div class="callout green">La frase con la que BFM cerro el caso de Egipto &mdash; <em>&quot;USD '
      'payments through Citibank are only used for domestic, US, payments&quot;</em> &mdash; es literalmente '
      'el nombre del metodo <code>L</code>. Estaba en <code>T042Z</code> desde siempre.</div>')

    # -------- 4. cada banco
    a('<h2>4 &middot; Cada banco, clasificado</h2>')
    a('<p style="font-size:12.5px">Bancos con al menos 50 lineas ejecutadas. <code>dest</code> = paises de '
      'destino distintos; <code>dom</code> = %% de sus pagos donde el beneficiario banca en su mismo pais; '
      '<code>cheque</code> = %% por metodos sin fichero.</p>')
    order = {t[0]: i for i, t in enumerate(TYPES)}
    a('<table><tr><th>Banco</th><th>Pais</th><th class="n">Lineas</th><th class="n">dest</th>'
      '<th class="n">dom</th><th class="n">cheque</th><th>Tipo</th><th>Rol</th><th>PPC</th>'
      '<th>Sociedades</th><th>Destino principal</th></tr>')
    for b in sorted(live, key=lambda x: (order.get(x["topology"], 9), -x["lines"])):
        top = b["top_payee_countries"][0]["country"] if b["top_payee_countries"] else "&mdash;"
        ppc = '<span class="pill green">si</span>' if b["ppc"]["dispatches_ppc"] else '<span class="pill">no</span>'
        a('<tr><td><code>%s</code></td><td>%s</td><td class="n">%s</td><td class="n">%d</td>'
          '<td class="n">%.0f%%</td><td class="n">%.0f%%</td><td>%s</td><td>%s</td><td>%s</td>'
          '<td>%s</td><td>%s</td></tr>'
          % (esc(b["house_bank"]), esc(b["country"]), "{:,}".format(b["lines"]).replace(",", "."),
             b["destination_countries"], 100 * b["domestic_share"], 100 * b["cheque_share"],
             esc(b["topology"]), esc(b["role"]), ppc,
             ", ".join(esc(c) for c in b["company_codes"][:3]), esc(top)))
    a('</table>')

    # -------- 5. re-derivar
    a('<h2>5 &middot; Como re-derivar y como usarlo</h2>')
    a('<pre><span class="c">-- ante un requisito de un banco, ESTO va primero, antes de disenar nada</span>\n'
      'python brain_v2/house_bank_roles.py --country <span class="h">EG</span>\n\n'
      '<span class="c">-- el censo completo, la ficha de un banco, y la exposicion del purpose code</span>\n'
      'python brain_v2/house_bank_roles.py\n'
      'python brain_v2/house_bank_roles.py --bank <span class="h">CIT19</span>\n'
      'python brain_v2/house_bank_roles.py --ppc-exposure</pre>')
    a('<div class="callout"><strong>El protocolo, en una frase:</strong> si el banco que avisa no domina '
      'la fila del corredor, esa es la primera pregunta al negocio &mdash; <em>&iquest;nos vincula esto, y '
      'que dice el banco que lleva el resto?</em> &mdash; y no la ultima. '
      'Regla <code>feedback_a_regulatory_notice_binds_a_channel_not_a_country</code> (CRITICAL).</div>')
    a('<div class="callout red"><strong>Aplicacion inmediata:</strong> la rama de direccion estructurada '
      'del arbol CITI ramifica por <code>FPAYHX-UBISO</code> &mdash; el mismo eje &mdash; y '
      '<code>INC-PSTLADR-NOV2026</code> vence el <strong>2026-11-14</strong>. La pregunta que no se hizo '
      'para Egipto hay que hacerla aqui antes.</div>')

    a('<h3>Limites, dichos explicitos</h3>')
    a('<ul style="font-size:12.5px">'
      '<li>El join a <code>LFBK</code> no usa <code>BVTYP</code>: un proveedor con varias cuentas puede '
      'contarse en mas de un corredor. Afecta a los margenes, no al orden de magnitud.</li>'
      '<li><code>SIN DESTINO CONOCIDO</code> no significa que el banco no pague: significa que sus '
      'beneficiarios no tienen registro en <code>LFBK</code> y no lo vemos.</li>'
      '<li>El eje domestico/internacional del &sect;3 se lee del <em>texto</em> del metodo: es la intencion '
      'de quien lo configuro, no una propiedad que SAP imponga. Coincide con lo medido, pero son dos cosas.</li>'
      '</ul>')

    rev = "?"
    try:
        rev = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                      cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        pass
    a('<footer>Generado por <code>scripts/build_bank_operation_design.py</code> desde '
      '<code>brain_v2/house_bank_roles.json</code> &middot; %s lineas de pago analizadas &middot; '
      'commit %s &middot; Claims 530 &middot; 531 &middot; 532 &middot; '
      'Nodo: <code>knowledge/domains/Treasury/house_bank_operating_roles.md</code> &middot; '
      'UNESCO SAP Intelligence</footer>'
      % ("{:,}".format(total_lines).replace(",", "."), rev))

    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(h))
    print("  OK %s (%d KB, %d bancos, %d tipos)"
          % (os.path.relpath(OUT, ROOT), len("\n".join(h)) // 1024, len(live), len(by_topo)))
    return 0


if __name__ == "__main__":
    sys.exit(build())
