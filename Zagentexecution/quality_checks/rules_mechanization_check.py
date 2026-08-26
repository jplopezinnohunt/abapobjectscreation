#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rules_mechanization_check.py -- cuantas reglas del brain son EJECUTABLES.

Por que existe
--------------
2026-08-19: hay 213 feedback rules y en una sola sesion se fallo contra cinco,
incluida una CRITICAL escrita por el propio agente TRES HORAS antes de volver a
violarla. Lo unico que si funciono fue lo que estaba dentro de una herramienta:
el validador cazo el error de orden, el mapa cazo el nodo que no emitia, el test
cazo el detector roto.

**Una regla que exige recordarla no es un mecanismo: es una nota.** Y anadir la
regla 214 no mejora nada.

Este check hace MEDIBLE la regla feedback_one_rule_in_one_rule_out: mide que
porcentaje del corpus tiene algo ejecutable detras y nombra las CRITICAL que no
lo tienen, que son las candidatas a mecanizar.

Una regla cuenta como MECANIZADA si su id aparece citado en:
  - un check de Zagentexecution/quality_checks/
  - un hook de brain_v2/*_hook.py
  - un generador que la aplique

    python Zagentexecution/quality_checks/rules_mechanization_check.py
    python Zagentexecution/quality_checks/rules_mechanization_check.py --solo-criticas

Nunca sale distinto de 0: informa, no bloquea. Bloquear por esto pararia el
trabajo real, y el objetivo es que el numero suba sesion a sesion.
"""

from __future__ import annotations

# El bloque va DESPUES del `from __future__`: una asignacion por delante lo rompe con
# SyntaxError, y el runner leeria el fichero como UNPARSEABLE.
QUALITY_CHECK = {
    # analysis y no gate: esto es una MEDIDA SIN UMBRAL, y una puerta necesita un
    # veredicto, no una tendencia. El propio docstring dice que el numero "deberia SUBIR
    # cada sesion" -- eso es una serie temporal, no un pasa/falla. MEDIDO 2026-08-26:
    # 243 reglas, 41 con algo ejecutable detras (16%), 56 CRITICAL en solo prosa.
    # No hay linea defendible que separe 16% de 15%.
    # Ademas sale 0 siempre: llamarlo `gate` seria un verde permanente que certifica.
    # PARA ASCENDERLO haria falta un ratchet contra el porcentaje anterior, y eso exige
    # estado persistido que hoy no existe.
    "tier": "analysis",
    "needs": "files",
    # conocimiento: lo que enumera y juzga son las REGLAS (lo que hemos escrito). El
    # codigo solo aparece como evidencia de que una regla tiene mecanismo. Si el sujeto
    # fuese el codigo, seria `herramientas`; aqui el codigo es el testigo, no el acusado.
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "what": ("censo del corpus de feedback rules: que porcentaje tiene algo EJECUTABLE "
             "detras y que CRITICAL siguen siendo solo prosa; metrica, no veredicto"),
    "args": "--solo-criticas   --top N   (ambos opcionales)",
    # CAVEAT MEDIDO, y no es menor: cuenta como MECANIZADA cualquier regla cuyo id APAREZCA
    # en el texto de un .py -- aunque ese .py no lo ejecute nadie. El 2026-08-26, 5 reglas
    # CRITICAL (never_delete_extracted_code, never_reextract_released_transports,
    # never_trust_old_anchors, no_correlated_subquery, extracted_code_is_brain_data) mas
    # una HIGH (one_rule_in_one_rule_out) tenian su UNICO mecanismo en los tres ficheros
    # que el runner sacaba como UNCLASSIFIED y por tanto nunca corria. CITAR NO ES CORRER:
    # este porcentaje es un techo, no una garantia.
}

import argparse
import collections
import glob
import io
import json
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
REGLAS = os.path.join(RAIZ, "brain_v2", "agent_rules", "feedback_rules.json")

# Donde puede vivir el mecanismo de una regla.
FUENTES = [
    os.path.join(RAIZ, "Zagentexecution", "quality_checks", "*.py"),
    os.path.join(RAIZ, "brain_v2", "*_hook.py"),
    os.path.join(RAIZ, "brain_v2", "*.py"),
    os.path.join(RAIZ, "scripts", "*.py"),
]


def cargar_reglas():
    d = json.load(io.open(REGLAS, encoding="utf-8"))
    return d["rules"] if isinstance(d, dict) and "rules" in d else d


def cuerpo_del_codigo():
    """Todo el codigo del proyecto donde una regla podria estar citada."""
    trozos = {}
    for patron in FUENTES:
        for f in glob.glob(patron):
            try:
                trozos[f] = io.open(f, encoding="utf-8", errors="replace").read()
            except OSError:
                pass
    return trozos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-criticas", action="store_true")
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()

    reglas = cargar_reglas()
    codigo = cuerpo_del_codigo()

    mecanizadas, huerfanas = [], []
    for r in reglas:
        rid = str(r.get("id", ""))
        if not rid:
            continue
        donde = [os.path.basename(f) for f, txt in codigo.items() if rid in txt]
        (mecanizadas if donde else huerfanas).append((r, donde))

    tot = len(reglas)
    pct = 100 * len(mecanizadas) // tot if tot else 0
    print("=" * 78)
    print("MECANIZACION DEL CORPUS DE REGLAS")
    print("=" * 78)
    print("\n  reglas totales      : %d" % tot)
    print("  con algo EJECUTABLE : %d  (%d%%)" % (len(mecanizadas), pct))
    print("  solo prosa          : %d" % len(huerfanas))

    sev = collections.Counter(r.get("severity", "?") for r, _ in huerfanas)
    print("\n  las de solo prosa, por severidad: %s"
          % ", ".join("%s=%d" % kv for kv in sev.most_common()))

    print("\n  MECANIZADAS -- la regla vive dentro de algo que corre:")
    for r, donde in sorted(mecanizadas, key=lambda x: x[0].get("severity", ""))[:a.top]:
        print("    %-10s %-52s %s" % (r.get("severity", "?"), r["id"],
                                      ", ".join(sorted(set(donde))[:2])))
    if len(mecanizadas) > a.top:
        print("    ... y %d mas" % (len(mecanizadas) - a.top))

    criticas = [(r, d) for r, d in huerfanas if r.get("severity") == "CRITICAL"]
    print("\n  CANDIDATAS A MECANIZAR -- CRITICAL sin nada ejecutable detras (%d):"
          % len(criticas))
    for r, _ in criticas[:a.top]:
        print("    %s" % r["id"])
        print("      %s" % (r.get("rule", "")[:110]))

    if not a.solo_criticas and huerfanas:
        otras = [r for r, d in huerfanas if r.get("severity") != "CRITICAL"]
        print("\n  (otras %d reglas de solo prosa; --solo-criticas para ocultarlas)"
              % len(otras))

    print("\n" + "-" * 78)
    print("Regla feedback_one_rule_in_one_rule_out: por cada regla nueva, mecanizar")
    print("una vieja o retirarla. El numero de arriba deberia SUBIR cada sesion.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
