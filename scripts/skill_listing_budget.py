"""¿Cabe nuestro listado de skills en el presupuesto? s107.

La doc: «The listing always contains every skill name, but if you have many skills, Claude
Code shortens descriptions to fit the listing's character budget... The budget scales at 1% of
the model's context window. When the listing overflows, Claude Code drops descriptions
STARTING WITH THE SKILLS YOU INVOKE LEAST.»

Nuestras 50 de SAP tienen CERO invocaciones. Serian las primeras en perder su descripcion --
y sin descripcion el modelo no puede elegirlas, que es el problema del que acabamos de salir.
Por eso se mide ANTES, no cuando alguien note que una skill no se activa.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

TOPE_ENTRADA = 1536          # cap duro por entrada, de la doc
DIRS = [".claude/skills", os.path.expanduser("~/.claude/skills")]
FM = re.compile(r"^---\s*\n(.*?)\n---", re.S)

filas = []
for base in DIRS:
    if not os.path.isdir(base):
        continue
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d, "SKILL.md")
        if not os.path.exists(p):
            continue
        s = io.open(p, encoding="utf-8", errors="replace").read()
        m = FM.match(s)
        desc = wtu = ""
        if m:
            import yaml
            try:
                y = yaml.safe_load(m.group(1)) or {}
                desc = str(y.get("description") or "")
                wtu = str(y.get("when_to_use") or "")
            except Exception:
                desc = m.group(1)
        if not desc:
            cuerpo = FM.sub("", s).strip().split("\n\n")
            desc = cuerpo[0] if cuerpo else ""
        bruto = len(desc) + len(wtu)
        filas.append((min(bruto, TOPE_ENTRADA), bruto, d, base))

filas.sort(reverse=True)
efectivo = sum(f[0] for f in filas)
bruto = sum(f[1] for f in filas)
print("SKILLS EN EL LISTADO: %d" % len(filas))
print("  caracteres BRUTOS (description + when_to_use) : %d" % bruto)
print("  caracteres EFECTIVOS (tope 1.536 por entrada) : %d" % efectivo)
print("  recortadas por el tope de entrada             : %d"
      % sum(1 for a, b, _, _ in filas if b > TOPE_ENTRADA))
print()
for ctx, etiqueta in ((200_000, "200K"), (1_000_000, "1M")):
    # el presupuesto escala al 1% de la ventana; se compara en caracteres
    for frac, nom in ((0.01, "1% (por defecto)"), (0.02, "2% (skillListingBudgetFraction)")):
        pres = int(ctx * 4 * frac)   # ~4 caracteres por token
        veredicto = "CABE" if efectivo <= pres else "SE PASA -> recorta las menos invocadas"
        print("  ventana %-4s · %-32s presupuesto ~%7d car · %s"
              % (etiqueta, nom, pres, veredicto))
print()
print("LAS 12 ENTRADAS MAS CARAS (candidatas a recortar en origen):")
for a, b, d, base in filas[:12]:
    marca = "  <-- RECORTADA por el tope" if b > TOPE_ENTRADA else ""
    print("  %5d car  %-34s %s%s" % (b, d, "(usuario)" if "skills" in base and
                                     base.startswith(os.path.expanduser("~")) else "(proyecto)",
                                     marca))
