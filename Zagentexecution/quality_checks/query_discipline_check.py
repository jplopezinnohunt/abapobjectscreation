#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
query_discipline_check.py -- las tres reglas de consulta que eran solo prosa.

Escanea el codigo del proyecto buscando los patrones que las reglas prohiben.
Cada hallazgo cita la regla que incumple, para que se pueda ir a leer el porque.

  feedback_no_correlated_subquery
      Subconsulta correlacionada sobre la Gold DB: `WHERE col = (SELECT ... FROM
      la_misma_tabla WHERE ...)`. En tablas de millones de filas SQLite la
      ejecuta una vez POR FILA y la consulta no termina nunca.

  feedback_never_reextract_released_transports
      Leer E071/E071K sin filtrar por transportes NO liberados. SAP vacia esas
      tablas al liberar: se gasta una extraccion larga para traer cero filas y se
      concluye que "no hay datos".

  feedback_never_trust_old_anchors
      Un numero de filas cableado en el codigo como si fuera el tamano de una
      tabla. Los recuentos de sesiones anteriores caducan; hay que sondear el
      count antes de planificar la extraccion.

    python Zagentexecution/quality_checks/query_discipline_check.py
    python Zagentexecution/quality_checks/query_discipline_check.py --regla no_correlated

Informa, no bloquea: hay falsos positivos legitimos (un ejemplo en un docstring,
un filtro que ya excluye liberados). Lo que importa es que nadie los introduzca
sin verlos.
"""

from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ZONAS = ["Zagentexecution/**/*.py", "scripts/**/*.py", "brain_v2/**/*.py"]
IGNORA = ("query_discipline_check.py", "__pycache__", "/node_modules/", "/.git/")

# Subconsulta correlacionada: un SELECT anidado que vuelve a nombrar una tabla
# dentro de un WHERE de comparacion.
RE_CORRELADA = re.compile(
    r"WHERE[^;]{0,120}?[=<>]\s*\(\s*SELECT\b[^)]{0,200}?\bFROM\b", re.I | re.S)
# E071/E071K sin ninguna senal de que se filtren los liberados.
RE_E071 = re.compile(r"\bE071K?\b")
RE_FILTRO_LIBERADO = re.compile(
    r"TRSTATUS|TARSYSTEM|E070|no[_ ]?released|sin[_ ]?liberar|NOT\s+RELEASED", re.I)
# Un recuento cableado: numeros grandes junto a palabras de tamano.
# OJO: COUNT=999999 / ROWCOUNT=0 son LIMITES de lectura de RFC_READ_TABLE, no
# anclajes caducados. Incluirlos llenaba el informe de falsos positivos, y un
# check con ruido se ignora entero -- que es peor que no tenerlo.
RE_ANCLA = re.compile(
    r"(?<!ROW)(?<!\w)(?:expected_rows?|filas_esperadas|total_rows?|"
    r"row_count|n_filas|approx_rows?)\s*[=:]\s*(\d[\d_,]{5,})", re.I)


def ficheros():
    vistos = set()
    for z in ZONAS:
        for f in glob.glob(os.path.join(RAIZ, z), recursive=True):
            n = os.path.normpath(f)
            if n in vistos or any(x in n.replace("\\", "/") for x in IGNORA):
                continue
            vistos.add(n)
            yield n


def linea_de(txt, pos):
    return txt.count("\n", 0, pos) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regla", choices=["no_correlated", "transports", "anchors"],
                    help="ejecutar solo una")
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()

    hall = {"no_correlated": [], "transports": [], "anchors": []}
    for f in ficheros():
        try:
            txt = io.open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        rel = os.path.relpath(f, RAIZ).replace("\\", "/")
        for m in RE_CORRELADA.finditer(txt):
            hall["no_correlated"].append((rel, linea_de(txt, m.start()),
                                          " ".join(m.group(0).split())[:88]))
        if RE_E071.search(txt) and not RE_FILTRO_LIBERADO.search(txt):
            m = RE_E071.search(txt)
            hall["transports"].append((rel, linea_de(txt, m.start()),
                                       "lee E071/E071K sin filtrar liberados"))
        for m in RE_ANCLA.finditer(txt):
            hall["anchors"].append((rel, linea_de(txt, m.start()),
                                    " ".join(m.group(0).split())[:88]))

    TITULOS = {
        "no_correlated": ("feedback_no_correlated_subquery",
                          "subconsulta correlacionada -- no termina en tablas grandes"),
        "transports": ("feedback_never_reextract_released_transports",
                       "E071/E071K sin filtrar liberados -- SAP ya las vacio"),
        "anchors": ("feedback_never_trust_old_anchors",
                    "recuento cableado -- sondear el count antes de planificar"),
    }
    print("=" * 78)
    print("DISCIPLINA DE CONSULTA")
    print("=" * 78)
    total = 0
    for k, (regla, desc) in TITULOS.items():
        if a.regla and a.regla != k:
            continue
        h = hall[k]
        total += len(h)
        print("\n  %s" % regla)
        print("  %s" % desc)
        if not h:
            print("     limpio")
            continue
        print("     %d hallazgo(s):" % len(h))
        for rel, ln, frag in h[:a.top]:
            print("       %s:%d" % (rel, ln))
            print("         %s" % frag)
        if len(h) > a.top:
            print("       ... y %d mas" % (len(h) - a.top))
    print("\n" + "-" * 78)
    print("%d hallazgo(s). Informa, no bloquea: puede haber falsos positivos "
          "legitimos." % total)
    print("Revisar antes de dar por bueno un script que toque la Gold DB o E071.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
