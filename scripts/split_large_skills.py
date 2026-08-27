"""split_large_skills.py — una skill cargada SE QUEDA EN CONTEXTO: parte las grandes. s107.

POR QUE
    La doctrina oficial de Claude Code: «Keep SKILL.md under 500 lines. Move detailed
    reference material to separate files», y la razon esta escrita al lado: «Once a skill
    loads, its content stays in context across turns, so every line is a recurring token
    cost». Un fichero de apoyo, en cambio, «loads only when needed».

    Medido tras migrar las 50: DIEZ pasan de 500 lineas. `sap_payment_bcm_agent` son 1.725
    lineas / 106 KB. Invocarla cuesta eso EN CADA TURNO del resto de la conversacion.

COMO PARTE, y por que asi
    SKILL.md se queda con: el front-matter, lo que hay antes de la primera seccion, y las
    secciones CRITICAS -- las que un lector necesita ANTES de actuar (proposito, cuando
    entrar, lo que NUNCA se hace, el metodo). El resto va a `reference.md`.

    Y SKILL.md conserva un INDICE de lo movido, con el titulo de cada seccion. Sin ese
    indice la particion seria una perdida: la doctrina dice «Reference supporting files from
    SKILL.md so Claude knows what each file contains and when to load it». Mover sin indexar
    es esconder.

    NO SE PIERDE UNA LINEA: se comprueba que la suma de las dos partes reproduce el original.

Uso:  python scripts/split_large_skills.py [--dry-run] [--limite 500]
"""
import argparse
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, ".claude", "skills")

# Titulos que se quedan SIEMPRE en SKILL.md: son los que se leen antes de actuar.
CRITICA = re.compile(
    r"never|nunca|no hagas|prohib|when to (use|route)|cuando (usar|entrar|correr)|"
    r"purpose|proposito|metadata|quick|start|first|primero|contrato|contract|"
    r"limit|limite|trampa|gotcha|warning|aviso|checklist|protocol|protocolo", re.I)


def secciones(lineas):
    """Corta por encabezados de nivel 2. Devuelve (cabecera, [(titulo, lineas)])."""
    idx = [i for i, l in enumerate(lineas) if l.startswith("## ")]
    if not idx:
        return lineas, []
    cab = lineas[:idx[0]]
    out = []
    for j, i in enumerate(idx):
        fin = idx[j + 1] if j + 1 < len(idx) else len(lineas)
        out.append((lineas[i][3:].strip(), lineas[i:fin]))
    return cab, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limite", type=int, default=500)
    a = ap.parse_args()

    hechas = []
    for d in sorted(os.listdir(SK)):
        p = os.path.join(SK, d, "SKILL.md")
        ref = os.path.join(SK, d, "reference.md")
        if not os.path.exists(p) or os.path.exists(ref):
            continue
        original = io.open(p, encoding="utf-8", errors="replace").read()
        lineas = original.split("\n")
        if len(lineas) <= a.limite:
            continue

        cab, secs = secciones(lineas)
        if not secs:
            print("  !! %s pasa de %d lineas y NO tiene secciones `## ` — no se parte a ciegas"
                  % (d, a.limite))
            continue

        quedan, mueven, usado = [], [], len(cab)
        for titulo, cuerpo in secs:
            critica = bool(CRITICA.search(titulo))
            # Critica SI, pero no a cualquier precio: si ya se paso del limite, hasta una
            # seccion critica se va a reference -- INDEXADA, que es lo que la hace
            # recuperable. Guardar todo lo critico dejaba seis skills por encima de 500 y
            # el limite existe por una razon medida: lo cargado se queda en contexto.
            cabe = usado + len(cuerpo) <= a.limite - 40
            if cabe or (critica and usado < a.limite - 40):
                quedan.append((titulo, cuerpo))
                usado += len(cuerpo)
            else:
                mueven.append((titulo, cuerpo))
        if not mueven:
            continue

        indice = ["", "## Referencia detallada", "",
                  "Lo que sigue vive en **[reference.md](reference.md)** y se carga sólo si hace",
                  "falta — una skill cargada se queda en contexto todo el turno, así que aquí",
                  "queda lo que se lee ANTES de actuar y allí el detalle:", ""]
        for t, _ in mueven:
            indice.append("- **%s**" % t)
        indice.append("")

        nuevo = "\n".join(cab + [l for _, c in quedan for l in c] + indice)
        refdoc = "\n".join(
            ["# %s — referencia detallada" % d, "",
             "> Extraído de `SKILL.md` para que su cuerpo no ocupe contexto en cada turno.",
             "> Lo carga quien lo necesite; el índice está en `SKILL.md`.", ""]
            + [l for _, c in mueven for l in c])

        # ASERCION: ni una linea de contenido perdida
        orig_sinvacias = [l for l in lineas if l.strip()]
        nuevas = [l for l in (nuevo + "\n" + refdoc).split("\n") if l.strip()]
        perdidas = [l for l in orig_sinvacias if l not in nuevas]
        if perdidas:
            print("  !! %s: %d lineas se perderian — NO se parte" % (d, len(perdidas)))
            continue

        if a.dry_run:
            print("  [dry] %-32s %4d -> %4d + ref %4d  (%d secciones movidas)"
                  % (d, len(lineas), len(nuevo.split("\n")), len(refdoc.split("\n")), len(mueven)))
        else:
            io.open(p, "w", encoding="utf-8").write(nuevo)
            io.open(ref, "w", encoding="utf-8").write(refdoc)
            hechas.append((d, len(lineas), len(nuevo.split("\n")), len(refdoc.split("\n")),
                           len(mueven)))

    print("\nPARTIDAS: %d" % len(hechas))
    for d, o, n, r, m in hechas:
        print("  %-32s %4d -> SKILL %3d + reference %4d   (%d secciones)" % (d, o, n, r, m))


if __name__ == "__main__":
    main()
