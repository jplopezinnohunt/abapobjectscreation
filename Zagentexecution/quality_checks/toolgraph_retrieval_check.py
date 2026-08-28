# -*- coding: utf-8 -*-
"""toolgraph_retrieval_check.py — ¿la puerta de entrada encuentra al experto que YA existe?

El fallo mas caro de s108 no fue de conocimiento: fue de RECUPERACION. Preguntado en español
"el extracto bancario electronico de una cuenta dejo de procesarse", el toolgraph devolvia
braintoolbox y sap_log_forensics, y NO devolvia sap_bank_statement_recon -- que en ingles sale
el primero. Resultado: se re-derivo a mano un pipeline que el skill ya documentaba, 13 minutos,
el bloque mas caro de la sesion.

Esta puerta usa las PREGUNTAS REALES de esa sesion como bateria de regresion. Cada caso dice
que instrumento DEBERIA salir, y en que puesto como mucho. Si el glosario bilingue se rompe o
alguien renombra un skill, esto se pone rojo.

Un caso se anade cuando una pregunta REAL no encontro a su experto. No se inventan.

Solo LECTURA. No toca SAP.

Uso:
    python toolgraph_retrieval_check.py
    python toolgraph_retrieval_check.py --verbose
"""

QUALITY_CHECK = {
    "tier": "local",
    "sobre": "herramientas",
    "needs": "",
    "what": "la puerta de entrada (graph_queries tool para) encuentra al experto que ya existe, "
            "preguntando como preguntamos de verdad: en español",
    "args": "[--verbose]",
}

import json
import subprocess
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# (pregunta REAL, instrumento que debe salir, puesto maximo aceptable)
# Las preguntas son literales de s108 -- asi se hablo, con acentos y sin ellos.
CASOS = [
    ("el extracto bancario electronico de una cuenta dejo de procesarse",
     "sap_bank_statement_recon", 1),
    ("extracto bancario electronico", "sap_bank_statement_recon", 1),
    ("cambiar el numero de cuenta de un banco casa", "sap_house_bank_configuration", 3),
    ("el fichero del banco no se reconoce para procesar el extracto",
     "sap_bank_statement_recon", 3),
    ("configuracion de banco casa en UNESCO", "sap_house_bank_configuration", 3),
    ("que jobs y variantes procesan los extractos bancarios", "sap_variant_analysis", 5),
    ("analizar un incidente de soporte de SAP", "sap_incident_analyst", 3),
    ("conciliacion bancaria y compensacion de partidas", "sap_bank_statement_recon", 3),
    ("firmantes y autorizacion de pagos BCM", "sap_payment_bcm_agent", 3),
    ("revaluacion de moneda extranjera de cuentas", "sap_variant_analysis", 5),
    # control: el ingles NO puede empeorar con el puente bilingue
    ("electronic bank statement stopped processing", "sap_bank_statement_recon", 1),
    ("house bank configuration", "sap_house_bank_configuration", 3),
]


def consulta(q):
    r = subprocess.run([sys.executable, os.path.join(REPO, "brain_v2", "graph_queries.py"),
                        "tool", "para", q],
                       capture_output=True, text=True, encoding="utf-8", cwd=REPO)
    try:
        d = json.loads(r.stdout)
    except Exception:
        return None
    return [x["nombre"] for x in d.get("1_LEE_ESTO_PRIMERO", [])]


def main():
    verbose = "--verbose" in sys.argv
    print("=" * 88)
    print("PUERTA DE ENTRADA — ¿encuentra al experto que ya existe? (preguntas reales de s108)")
    print("=" * 88)
    fallan = []
    for q, esperado, tope in CASOS:
        got = consulta(q)
        if got is None:
            print("  ERROR   %-58s (no se pudo consultar)" % q[:58])
            fallan.append((q, esperado, "sin respuesta"))
            continue
        pos = (got.index(esperado) + 1) if esperado in got else 0
        ok = pos and pos <= tope
        print("  %-6s %-56s %s" % ("OK" if ok else "FALLA", q[:56],
                                   ("#%d" % pos) if pos else "NO SALE"))
        if verbose or not ok:
            print("         devuelve: %s" % (got[:5] or "NADA"))
            print("         esperado: %s en el puesto <=%d" % (esperado, tope))
        if not ok:
            fallan.append((q, esperado, "#%d" % pos if pos else "NO SALE"))

    print("\n" + "=" * 88)
    print("%d casos · %d OK · %d FALLAN" % (len(CASOS), len(CASOS) - len(fallan), len(fallan)))
    if fallan:
        print("\nLo que falla NO es el skill: es que nadie llega a el. Antes de escribir mas")
        print("conocimiento en un skill, comprueba que la pregunta real lo encuentra.")
        for q, e, p in fallan:
            print("   '%s' -> esperaba %s, obtuvo %s" % (q[:52], e, p))
    return 1 if fallan else 0


if __name__ == "__main__":
    sys.exit(main())
