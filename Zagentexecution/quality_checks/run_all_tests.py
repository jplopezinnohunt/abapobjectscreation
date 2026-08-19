#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_all_tests.py -- corre TODOS los tests offline de las herramientas del proyecto.

Sin este runner, la regla feedback_reusable_tools_carry_offline_tests es una nota:
el test existe y no lo ejecuta nadie. Con el, se ejecuta al cerrar sesion.

Descubre `test_*.py` en quality_checks/ y los corre. Ninguno necesita SAP: si un
test requiere conexion, no es un test offline y no pinta aqui.

    python Zagentexecution/quality_checks/run_all_tests.py

Salida 0 = todo verde. 1 = algo rojo, y dice cual.
"""

from __future__ import annotations

import glob
import io
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    tests = sorted(glob.glob(os.path.join(AQUI, "test_*.py")))
    if not tests:
        print("!! No hay ningun test_*.py en quality_checks/.")
        print("   Toda herramienta reutilizable deberia traer el suyo "
              "(feedback_reusable_tools_carry_offline_tests).")
        return 1
    print("=" * 72)
    print("TESTS OFFLINE -- %d fichero(s)" % len(tests))
    print("=" * 72)
    fallos = []
    for t in tests:
        nombre = os.path.basename(t)
        r = subprocess.run([sys.executable, t], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        salida = (r.stdout or "") + (r.stderr or "")
        resumen = ""
        for linea in salida.splitlines():
            if ">>>" in linea:
                resumen = linea.strip().lstrip("> ").strip()
        if r.returncode == 0:
            print("  OK     %-46s %s" % (nombre, resumen))
        else:
            fallos.append(nombre)
            print("  FALLA  %-46s %s" % (nombre, resumen))
            for linea in salida.splitlines():
                if "FALLA" in linea or "Error" in linea or "Traceback" in linea:
                    print("         " + linea.strip()[:100])
    print("-" * 72)
    if fallos:
        print("ROJO: %d de %d fichero(s) con fallos -> %s"
              % (len(fallos), len(tests), ", ".join(fallos)))
        return 1
    print("VERDE: %d fichero(s), todo pasa." % len(tests))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
