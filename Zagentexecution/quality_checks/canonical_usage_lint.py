"""
canonical_usage_lint.py — ¿quien resuelve alias A MANO teniendo canonical.py? s106.
===================================================================================

LA TERCERA MECANIZACION. `brain_v2/canonical.py` existe desde s097 y su docstring dice:

    "THE most repeated defect in this codebase. In session 097 alone the same bug appeared
     THREE times, in three different files, and was fixed three times separately...
     Fixing a recurring defect three times is not fixing it... the failure was never
     missing data, it was that every consumer re-implemented the lookup.
     This module is the lookup. Import it; do not re-derive it."

Tres veces en s097. **Y tres mas en s106**, por el agente que ese mismo dia predicaba no
reinventar lo que existe -- con dos hallazgos FALSOS publicados al dueno antes de
retirarlos ("5 referencias rotas en process_map" que eran alias declarados, y un
`parent: Treasury_EBS` correcto que estuvo a punto de "corregir").

Escribir el helper no basto. Documentarlo no basto. **Nada obligaba a usarlo y nada media
que se ignoraba** — el toolgraph mide si se leen los SKILLS, y un helper no es un skill,
asi que no tiene lector, asi que su abandono era invisible. Esto es el medidor que faltaba.

QUE MIDE — dos senales, la segunda es la humeante
    (A) lee tablas de alias (`aliases`, `canonical_key`, `subdomain_aliases`) y NO importa
        `canonical`  -> puede estar resolviendo por su cuenta
    (B) ademas usa el idioma `X.get(n, n)` -> esta construyendo un mapa alias->canonico a
        mano. Eso ya no es sospecha: es el defecto.

Medido en la primera corrida (s106): 10 ficheros leen tablas de alias, 6 importan
canonical, 8 no lo importan, y **4 traen el idioma humeante** — uno de ellos escrito ese
mismo dia por el agente que escribio este lint.

⛔ LO QUE NO PUEDE VER, para que su silencio no se lea como limpieza
    Solo mira ficheros que TOCAN las tablas de alias. Una comparacion de nombres que no
    lea `ontology.json` -- por ejemplo cruzar dos listas ya cargadas de otro sitio -- no
    aparece aqui. Ausencia de aviso NO es prueba de que se canonicalice bien.

EXENTOS, y por que (nunca por comodidad)
    canonical.py         es EL lookup; no puede importarse a si mismo
    validate_ontology.py es la AUTORIDAD de la ontologia: comprueba que el registro y lo
                         declarado cuadran, asi que tiene que leer las tablas en crudo. Si
                         importara el resolvedor estaria validando con lo validado.

Solo LECTURA. tier=analysis: informa y NO bloquea. Los 8 avisos son deuda preexistente y
convertirlos en puerta hoy bloquearia el repo sin haber decidido arreglarlos.

Uso:
    python canonical_usage_lint.py [--solo-humeantes]
"""

QUALITY_CHECK = {
    "tier": "analysis",       # informa; se sube a gate cuando la deuda este pagada
    "sobre": "herramientas",  # datos_sap | conocimiento | herramientas
    "needs": "nada",
    "what": "quien resuelve alias de dominio a mano teniendo brain_v2/canonical.py",
    "args": "[--solo-humeantes]",
}

import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAICES = ["brain_v2", "process_mining", "Zagentexecution", "scripts"]

EXENTOS = {
    "canonical.py": "es EL lookup: no puede importarse a si mismo",
    "validate_ontology.py": "es la AUTORIDAD: valida el registro, debe leerlo en crudo",
    "canonical_usage_lint.py": "este mismo lint: nombra las tablas para buscarlas",
}

RE_TABLAS = re.compile(r"""["']aliases["']|canonical_key|subdomain_aliases""")
RE_IMPORTA = re.compile(r"^\s*(from\s+canonical\s+import|import\s+canonical)\b", re.M)
RE_IDIOMA = re.compile(r"\.get\(\s*(\w+)\s*,\s*\1\s*\)")   # d.get(x, x) — el mapa a mano


def escanear():
    hallazgos = []
    for raiz in RAICES:
        base = os.path.join(ROOT, raiz)
        for dp, _, fs in os.walk(base):
            # EL DENOMINADOR SE DECLARA. La primera corrida marco tres ficheros de pip
            # dentro de un venv: codigo de TERCEROS contado como deuda nuestra. Un lint
            # cuyo denominador incluye lo que no controlamos miente en la direccion que mas
            # cansa -- avisa de lo que nadie va a arreglar y se deja de mirar.
            if any(x in dp for x in ("__pycache__", "node_modules", "venv",
                                     "site-packages", "_vendor", ".git")):
                continue
            for f in sorted(fs):
                if not f.endswith(".py") or f in EXENTOS:
                    continue
                ruta = os.path.join(dp, f)
                try:
                    src = open(ruta, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                if not RE_TABLAS.search(src):
                    continue
                if RE_IMPORTA.search(src):
                    continue
                rel = os.path.relpath(ruta, ROOT).replace("\\", "/")
                hallazgos.append((rel, bool(RE_IDIOMA.search(src))))
    return hallazgos


def main(argv):
    solo_hum = "--solo-humeantes" in argv
    h = escanear()
    hum = [r for r, s in h if s]
    tibios = [r for r, s in h if not s]

    print("=" * 74)
    print("USO DE canonical.py — quien resuelve alias por su cuenta")
    print("=" * 74)
    print("  🔥 IDIOMA HUMEANTE — construyen el mapa alias->canonico a mano (%d):" % len(hum))
    for r in hum:
        print("      %s" % r)
    if not solo_hum:
        print()
        print("  ⚠  leen tablas de alias y no importan canonical (%d):" % len(tibios))
        for r in tibios:
            print("      %s" % r)
    print()
    print("  exentos por diseno: %s" % ", ".join(sorted(EXENTOS)))
    print("-" * 74)
    if hum:
        print("ARREGLO: `from canonical import canonical, same, aliases_of` y borrar el mapa.")
        print("  `same(a, b)` compara dos nombres resolviendo AMBOS — es la funcion que")
        print("  habria evitado los dos hallazgos falsos de s106.")
        print("  NO se falla: es deuda preexistente. Sube a tier=gate cuando este pagada.")
    else:
        print("OK — nadie resuelve alias a mano.")
    print("  OJO: solo mira ficheros que TOCAN las tablas de alias. Ausencia de aviso NO")
    print("  prueba que se canonicalice bien en todas partes.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
