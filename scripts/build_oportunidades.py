# -*- coding: utf-8 -*-
"""build_oportunidades.py — el registro VIVO de lo que los mineros encuentran.

Genera dos cosas de una sola fuente, el bus `process_mining/mining_findings.json`:

  .agents/intelligence/PMO_OPORTUNIDADES.md   para leer y decidir
  companions/oportunidades_y_desafios.html    para enseñar

**Se GENERA, no se escribe a mano.** Un registro de pendientes escrito a mano envejece: el
minero corre cada semana y el documento se queda en la semana en que alguien lo escribio. Aqui
cada corrida de un minero REEMPLAZA lo suyo, asi que lo que desaparece del documento es lo que
dejo de encontrarse -- y eso tambien es informacion.

**Lo que este registro tiene y los otros cinco del proyecto no: DESDE CUANDO.** El arranque de
sesion lo dice sin rodeos -- PMO 111 items, bus 4, known_unknowns 55, data_quality 39, backlog
132, y NINGUNO dice desde cuando lleva parado un pendiente; todos dicen que falta. Con esa
cifra de items, esa es la diferencia entre una lista viva y un cementerio. Por eso el emisor
sella `visto_primero` y `visto_ultima`, y aqui se ordena por ANTIGUEDAD.

Solo lectura sobre el bus. No toca SAP.

Uso:
    python scripts/build_oportunidades.py
"""

import collections
import datetime
import io
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
BUS = os.path.join(REPO, "process_mining", "mining_findings.json")
MD = os.path.join(REPO, ".agents", "intelligence", "PMO_OPORTUNIDADES.md")
HTML = os.path.join(REPO, "companions", "oportunidades_y_desafios.html")

ORDEN = ["RIESGO", "DESAFIO", "OPORTUNIDAD", "DATO"]
ICONO = {"RIESGO": "🔴", "DESAFIO": "🟠", "OPORTUNIDAD": "🟢", "DATO": "⚪"}
QUE_ES = {
    "RIESGO": "puede hacer daño si nadie actúa · va a quien responde del control",
    "DESAFIO": "no cuadra y el minero no puede resolverlo solo · **necesita que alguien conteste**",
    "OPORTUNIDAD": "se puede mejorar · va a quien decide dónde invertir esfuerzo",
    "DATO": "un hecho relevante que no es ninguna de las tres · va al conocimiento",
}


def cargar():
    if not os.path.exists(BUS):
        return []
    try:
        d = json.load(io.open(BUS, encoding="utf-8"))
    except Exception:
        return []
    h = d.get("hallazgos") if isinstance(d, dict) else d
    # solo lo que trae el contrato: clase + minero. El bus lleva 340 entradas de formato
    # anterior y mezclarlas seria inventar una serie que no existe.
    return [x for x in (h or []) if isinstance(x, dict) and x.get("clase") and x.get("minero")]


def dias(desde, hoy):
    try:
        a = datetime.date.fromisoformat(desde)
        b = datetime.date.fromisoformat(hoy)
        return (b - a).days
    except Exception:
        return None


def main():
    hoy = datetime.date.today().isoformat()
    items = cargar()
    if not items:
        print("el bus no tiene hallazgos con el contrato nuevo -- corre los mineros primero")
        return 1

    for x in items:
        x["_dias"] = dias(x.get("visto_primero") or hoy, hoy)
    items.sort(key=lambda x: (ORDEN.index(x["clase"]) if x["clase"] in ORDEN else 9,
                              -(x.get("_dias") or 0)))
    por_clase = collections.Counter(x["clase"] for x in items)
    por_minero = collections.Counter(x["minero"] for x in items)
    abiertos = [x for x in items if x["clase"] == "DESAFIO"]

    # ---------------- MARKDOWN ----------------------------------------------------
    L = []
    L.append("# Oportunidades, riesgos y desafíos — lo que los mineros encuentran\n")
    L.append("> **GENERADO.** No editar a mano: `python scripts/build_oportunidades.py` lo "
             "reescribe del bus `process_mining/mining_findings.json`. "
             "Última generación: **%s**.\n" % hoy)
    L.append("> Cada corrida de un minero **reemplaza lo suyo**, así que lo que desaparece de "
             "aquí es lo que dejó de encontrarse — y eso también es información.\n")
    L.append("**%d hallazgos vivos** de %d mineros: %s\n"
             % (len(items), len(por_minero),
                " · ".join("%s %s %d" % (ICONO.get(c, ""), c, por_clase[c])
                           for c in ORDEN if por_clase.get(c))))
    if abiertos:
        L.append("\n⚠️ **%d desafíos esperan que alguien conteste.** Un desafío no es un fallo "
                 "ni una mejora: es una pregunta que el minero no puede resolver solo, y el "
                 "minero es quien mejor puede formularla porque tiene los datos delante.\n"
                 % len(abiertos))

    for clase in ORDEN:
        g = [x for x in items if x["clase"] == clase]
        if not g:
            continue
        L.append("\n---\n\n## %s %s (%d)\n" % (ICONO.get(clase, ""), clase, len(g)))
        L.append("*%s*\n" % QUE_ES.get(clase, ""))
        for x in g:
            d = x.get("_dias")
            edad = ("**hoy**" if not d else
                    "**%d días abierto**" % d if d < 30 else
                    "🕰️ **%d días abierto**" % d)
            L.append("\n### %s\n" % x["que"])
            L.append("- **Tamaño:** %s" % x.get("tamano", "—"))
            if x.get("evidencia"):
                L.append("- **Evidencia:** %s" % x["evidencia"])
            if x.get("limite"):
                L.append("- **No se puede ver:** %s" % x["limite"])
            if x.get("accion"):
                L.append("- **Acción:** %s" % x["accion"])
            if x.get("quien_puede_contestar"):
                L.append("- **Puede contestarlo:** %s" % x["quien_puede_contestar"])
            L.append("- *%s · lo encuentra `%s` · %s · %s*"
                     % (edad, x["minero"], x.get("sistema", ""), x.get("ventana", "")))
            if x.get("denominador"):
                L.append("- <sub>denominador: %s</sub>" % x["denominador"])

    L.append("\n---\n\n## De dónde sale cada uno\n")
    L.append("| Minero | Hallazgos |")
    L.append("|---|---:|")
    for m, n in por_minero.most_common():
        L.append("| `%s` | %d |" % (m, n))
    L.append("\n> Un minero que no aparece aquí **no está limpio: está mudo**. O no busca, o "
             "no publica. Las dos cosas hay que arreglarlas.\n")

    io.open(MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("escrito %s (%d hallazgos)" % (os.path.relpath(MD, REPO), len(items)))

    # ---------------- COMPANION ----------------------------------------------------
    def esc(t):
        return (str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    C = ["<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         "<title>Oportunidades y desafíos — mineros</title><style>",
         """
:root{--bg:#0f1518;--card:#182126;--line:#26343a;--tx:#e6edef;--tx2:#a8b8bd;--tx3:#75898f;
--rojo:#e07a6b;--naranja:#d9a15c;--verde:#6fc2a0;--gris:#7f9196;--acc:#5fb6b8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);
font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;line-height:1.6}
.w{max-width:1000px;margin:0 auto;padding:40px 22px 80px}
h1{font-size:2.1rem;margin:0 0 8px;letter-spacing:-.02em}
h2{font-size:1.3rem;margin:34px 0 6px;border-bottom:1px solid var(--line);padding-bottom:8px}
.sub{color:var(--tx2);margin:0 0 22px;max-width:70ch}
.kpis{display:flex;flex-wrap:wrap;gap:12px;margin:22px 0}
.k{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px;min-width:120px}
.k b{display:block;font-size:1.7rem;line-height:1.2;font-variant-numeric:tabular-nums}
.k span{font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;color:var(--tx3)}
.f{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--gris);
border-radius:5px;padding:16px 18px;margin:12px 0}
.f.RIESGO{border-left-color:var(--rojo)} .f.DESAFIO{border-left-color:var(--naranja)}
.f.OPORTUNIDAD{border-left-color:var(--verde)}
.f h3{margin:0 0 10px;font-size:1.02rem;font-weight:600}
.f dl{margin:0;display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;font-size:.92rem}
.f dt{color:var(--tx3);font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;padding-top:3px}
.f dd{margin:0;color:var(--tx2)}
.meta{margin-top:12px;font-size:.78rem;color:var(--tx3);font-family:"IBM Plex Mono",monospace}
.edad{color:var(--naranja);font-weight:600}
code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.9em;color:var(--acc)}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin-top:10px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line)}
th{color:var(--tx3);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;font-weight:500}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.nota{background:#1a2329;border:1px solid var(--line);border-radius:5px;padding:14px 18px;
color:var(--tx2);font-size:.92rem;margin:18px 0}
""",
         "</style></head><body><div class='w'>"]
    C.append("<h1>Oportunidades, riesgos y desafíos</h1>")
    C.append("<p class='sub'>Lo que los mineros del dominio <b>encuentran</b> cuando corren — no "
             "lo que miden. Generado del bus <code>mining_findings.json</code> el %s. "
             "Cada corrida reemplaza lo suyo: lo que desaparece de aquí es lo que dejó de "
             "encontrarse.</p>" % hoy)
    C.append("<div class='kpis'>")
    for c in ORDEN:
        if por_clase.get(c):
            C.append("<div class='k'><b>%d</b><span>%s</span></div>" % (por_clase[c], c))
    C.append("<div class='k'><b>%d</b><span>mineros</span></div>" % len(por_minero))
    C.append("</div>")
    if abiertos:
        C.append("<div class='nota'>⚠ <b>%d desafíos esperan respuesta.</b> Un desafío no es un "
                 "fallo ni una mejora: es una pregunta que el minero no puede cerrar solo. Y el "
                 "minero es quien mejor puede formularla, porque es el único que tiene los datos "
                 "delante en el momento en que la contradicción aparece.</div>" % len(abiertos))
    for clase in ORDEN:
        g = [x for x in items if x["clase"] == clase]
        if not g:
            continue
        C.append("<h2>%s %s <span style='color:var(--tx3);font-weight:400'>(%d)</span></h2>"
                 % (ICONO.get(clase, ""), clase, len(g)))
        C.append("<p class='sub' style='margin:0 0 10px'>%s</p>" % esc(QUE_ES.get(clase, "")))
        for x in g:
            d = x.get("_dias") or 0
            C.append("<div class='f %s'><h3>%s</h3><dl>" % (clase, esc(x["que"])))
            for et, cl in (("Tamaño", "tamano"), ("Evidencia", "evidencia"),
                           ("No se ve", "limite"), ("Acción", "accion"),
                           ("Contesta", "quien_puede_contestar")):
                if x.get(cl):
                    C.append("<dt>%s</dt><dd>%s</dd>" % (et, esc(x[cl])))
            C.append("</dl><div class='meta'>%s · lo encuentra <code>%s</code> · %s · %s</div></div>"
                     % ("<span class='edad'>%d días abierto</span>" % d if d else "detectado hoy",
                        esc(x["minero"]), esc(x.get("sistema", "")), esc(x.get("ventana", ""))))
    C.append("<h2>De dónde sale cada uno</h2><table><tr><th>Minero</th><th>Hallazgos</th></tr>")
    for m, n in por_minero.most_common():
        C.append("<tr><td><code>%s</code></td><td class='n'>%d</td></tr>" % (esc(m), n))
    C.append("</table><div class='nota'>Un minero que no aparece aquí <b>no está limpio: está "
             "mudo</b>. O no busca, o no publica. Las dos cosas hay que arreglarlas.</div>")
    C.append("</div></body></html>")
    io.open(HTML, "w", encoding="utf-8").write("\n".join(C))
    print("escrito %s" % os.path.relpath(HTML, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
