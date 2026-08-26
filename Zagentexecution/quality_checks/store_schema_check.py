#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
store_schema_check.py -- un registro nuevo tiene que tener la forma de los viejos.

Por que existe
--------------
2026-08-19: se anadieron 15 claims con un esquema INVENTADO -- `statement` en vez
de `claim`, `evidence` en vez de `evidence_for`, `created` en vez de
`created_session`, y `confidence='high'` donde el store usa TIER_1/2/3. El
rebuild del brain se cayo en el paso 2 con `KeyError: 'claim'`, y los 15 claims
—incluido el que cierra el rechazo bancario del 21-07— estaban en el fichero
pero no en el estado agregado. Nadie se habria enterado hasta el siguiente
rebuild, que puede ser dias despues.

El error de fondo no es tipografico: es escribir en un store sin leer antes como
escriben los que ya estan. Este check lo convierte en un fallo inmediato.

Que hace
--------
Para cada store, deduce el esquema por MAYORIA (las claves que tiene el 80%+ de
los registros) y avisa de los que se desvian: claves obligatorias que faltan,
claves inventadas que nadie mas usa, y valores fuera del vocabulario observado en
los campos enumerados.

No hay esquema declarado en ninguna parte, asi que la mayoria ES el contrato.
Cuando el store cambie a proposito, el aviso saldra sobre los registros VIEJOS y
eso es correcto: obliga a migrar, no a divergir.

    python Zagentexecution/quality_checks/store_schema_check.py
    python Zagentexecution/quality_checks/store_schema_check.py --store claims

Sale 1 si hay registros que romperian el rebuild (les falta una clave obligatoria).
"""

# REGLAS QUE APLICAN AQUI (citadas para que existan en su punto de uso, no solo en el JSON):
#   feedback_always_utf8_encoding
#     -> el momento es escribir un fichero de store: este check ya gatea esa escritura

from __future__ import annotations

# --- self-declaration, la lee Zagentexecution/quality_checks/run_all.py -------------
# Va DESPUES del `from __future__` a proposito: un future statement solo admite delante el
# docstring, comentarios y lineas en blanco -- una asignacion antes es SyntaxError.
# run_all.declaration() recorre todo el cuerpo del modulo, asi que la posicion le da igual.
#
# POR QUE gate: lee tres ficheros del repo, nada mas (sin RFC, sin Gold), y main() devuelve
#   1 cuando hay registros rotos. El fallo que lo origino tumbo el rebuild en el paso 2 con
#   KeyError: 'claim' y dejo 15 claims escritos pero fuera del estado agregado -- eso no se
#   descubre "al proximo rebuild", que puede ser dias despues.
# POR QUE gate y NO analysis, aun sabiendo que hoy sale ROJO: analysis es "produce informe,
#   no veredicto", y este si lo da. Bajarlo de tier para que el ciclo se vea verde seria
#   certificar un store divergente. El propio docstring ya asume que el aviso caiga sobre
#   registros VIEJOS: "obliga a migrar, no a divergir". Medido 2026-08-26: 93 registros
#   desviados (76 claims sin status/resolved_session, 1 incidente sin process, 16 reglas sin
#   created_session). Es un backlog real de migracion, no un falso positivo.
# POR QUE conocimiento: los tres stores -- claims, incidents, feedback_rules -- son lo que
#   hemos escrito nosotros. No toca SAP ni mide un instrumento.
QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "needs": "files",
    "what": ("registros de claims/incidents/rules que se desvian del esquema mayoritario de "
             "su store: la clave que falta es la que rompe el rebuild"),
    "args": "--store <claims|incidents|rules> para acotar a un store (opcional)",
}
# ------------------------------------------------------------------------------------

import argparse
import collections
import io
import json
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# store -> (fichero, clave de la lista si el json es un dict, campos enumerados)
STORES = {
    "claims":    ("brain_v2/claims/claims.json", "claims",
                  ["claim_type", "confidence", "status"]),
    "incidents": ("brain_v2/incidents/incidents.json", "incidents",
                  ["status", "domain"]),
    "rules":     ("brain_v2/agent_rules/feedback_rules.json", "rules",
                  ["severity"]),
}
UMBRAL = 0.80          # una clave es obligatoria si la tiene el 80%+ de los registros

# Formato canonico de cada store: con que indent lo escribe SU generador. Escribir
# a mano con otro indent hace que el siguiente rebuild reformatee el fichero entero
# y produzca un diff donde una edicion real es invisible. Paso el 2026-08-19: se
# edito claims.json con indent=1 y verify_claims.py lo devolvio a indent=2 ->
# 48.168 lineas de diff con CERO claims cambiados.
INDENT_CANONICO = {
    "claims": (2, "brain_v2/verify_claims.py"),
    "rules": (2, "brain_v2/scripts/backfill_domain_axes.py"),
    "incidents": (2, "brain_v2/scripts/backfill_domain_axes.py"),
}

# Implementa feedback_read_the_store_before_writing_to_it.


def cargar(rel, clave):
    d = json.load(io.open(os.path.join(RAIZ, rel), encoding="utf-8"))
    if isinstance(d, dict) and clave in d:
        return d[clave]
    return d if isinstance(d, list) else []


def revisar(nombre, rel, clave, enums):
    registros = cargar(rel, clave)
    if not registros:
        print("\n  %-10s vacio o ilegible" % nombre)
        return 0
    n = len(registros)
    frec = collections.Counter(k for r in registros for k in r)
    obligatorias = {k for k, c in frec.items() if c >= n * UMBRAL}
    raras = {k for k, c in frec.items() if c <= max(2, n * 0.02)}
    vocab = {e: collections.Counter(str(r.get(e)) for r in registros if r.get(e) is not None)
             for e in enums}

    print("\n  %s  (%d registros, %s)" % (nombre, n, rel))
    esperado, quien = INDENT_CANONICO.get(nombre, (None, ""))
    if esperado is not None:
        try:
            # El parametro `indent` es la sangria del PRIMER nivel: la llave que
            # abre cada registro dentro de la lista. Medir la primera clave
            # entrecomillada da el doble, porque esa ya esta un nivel mas dentro.
            lineas = io.open(os.path.join(RAIZ, rel), encoding="utf-8").read().splitlines()
            real = next((len(l) - len(l.lstrip(" ")) for l in lineas[1:60]
                         if l.startswith(" ") and l.strip() in ("{", "[")), None)
            if real is not None and real != esperado:
                print("     !! indent %d, el canonico es %d (lo escribe %s)."
                      % (real, esperado, quien))
                print("        El proximo rebuild reformateara el fichero entero y el "
                      "diff sera ilegible.")
        except OSError:
            pass
    print("     esquema por mayoria (>=%d%%): %s"
          % (UMBRAL * 100, ", ".join(sorted(obligatorias))))

    rotos, sospechosos = [], []
    for r in registros:
        rid = r.get("id", "?")
        faltan = obligatorias - set(r)
        if faltan:
            rotos.append((rid, "faltan " + ", ".join(sorted(faltan))))
        inventadas = (set(r) & raras) - obligatorias
        if inventadas:
            sospechosos.append((rid, "claves que casi nadie usa: "
                                + ", ".join(sorted(inventadas))))
        for e in enums:
            v = r.get(e)
            if v is None:
                continue
            c = vocab[e]
            if c[str(v)] <= max(1, n * 0.005) and len(c) > 1:
                sospechosos.append((rid, "%s=%r fuera del vocabulario "
                                         "(usado %d vez/veces)" % (e, v, c[str(v)])))

    if rotos:
        print("     %d registro(s) SE DESVIAN del esquema mayoritario:" % len(rotos))
        for rid, q in rotos[:10]:
            print("        %-14s %s" % (rid, q))
        if len(rotos) > 10:
            print("        ... y %d mas" % (len(rotos) - 10))
    else:
        print("     sin registros rotos")
    if sospechosos:
        print("     %d aviso(s) -- puede ser divergencia o puede ser deliberado:"
              % len(sospechosos))
        for rid, q in sospechosos[:8]:
            print("        %-14s %s" % (rid, q))
        if len(sospechosos) > 8:
            print("        ... y %d mas" % (len(sospechosos) - 8))
    return len(rotos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", choices=sorted(STORES))
    a = ap.parse_args()
    print("=" * 78)
    print("ESQUEMA DE LOS STORES -- un registro nuevo con forma propia rompe el rebuild")
    print("=" * 78)
    rotos = 0
    for nombre, (rel, clave, enums) in sorted(STORES.items()):
        if a.store and a.store != nombre:
            continue
        try:
            rotos += revisar(nombre, rel, clave, enums)
        except (OSError, ValueError) as exc:
            print("\n  %-10s NO SE PUDO LEER: %s" % (nombre, str(exc)[:80]))
    print("\n" + "-" * 78)
    if rotos:
        print("%d registro(s) se desvian del esquema mayoritario de su store." % rotos)
        print("NO todos rompen el rebuild: solo lo rompe la clave que su consumidor lee")
        print("sin get() -- fue el caso de 'claim' en claims.json el 2026-08-19. El resto")
        print("son divergencias silenciosas que acaban costando lo mismo.")
        print("Antes de escribir en un store, LEER como escriben los que ya estan.")
        return 1
    print("Todos los registros siguen el esquema de su store.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
