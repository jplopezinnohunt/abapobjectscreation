#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extracted_corpus_integrity_check.py -- el codigo extraido de SAP no puede encoger.

Mecaniza feedback_never_delete_extracted_code, que hasta ahora era prosa. El
corpus de `extracted_code/`, `extracted_sap/` y `extracted_sap_p01/` es
IRREEMPLAZABLE: parte de el son objetos que ya no existen en el sistema, y otra
parte solo se puede recuperar con una extraccion larga contra P01 -- cuando P01
responde, que hoy no lo hacia.

Que hace
--------
Guarda una linea base (cuantos ficheros y cuantos bytes por corpus) y avisa si
baja. No bloquea nunca: informa, porque una bajada legitima existe (consolidar
duplicados) y bloquear el cierre por eso solo ensena a ignorar el check. Lo que
NO puede pasar es que encoja sin que nadie se entere.

    python Zagentexecution/quality_checks/extracted_corpus_integrity_check.py
    python Zagentexecution/quality_checks/extracted_corpus_integrity_check.py --sellar

La linea base vive en brain_v2/.extracted_corpus_baseline.json y se actualiza
sola cuando el corpus CRECE. Para aceptar una bajada hay que sellarla a mano con
--sellar, que es justo la friccion que se quiere.
"""

# REGLAS QUE APLICAN AQUI (citadas para que existan en su punto de uso, no solo en el JSON):
#   feedback_extracted_code_is_brain_data
#     -> el momento es cuando se toca el corpus extraido: este check lo vigila

from __future__ import annotations

import argparse
import io
import json
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BASE = os.path.join(RAIZ, "brain_v2", ".extracted_corpus_baseline.json")

CORPUS = ["extracted_code", "extracted_sap", "extracted_sap_p01"]


def medir(rel):
    d = os.path.join(RAIZ, rel)
    if not os.path.isdir(d):
        return None
    n = b = 0
    for raiz, _, ficheros in os.walk(d):
        for f in ficheros:
            try:
                b += os.path.getsize(os.path.join(raiz, f))
                n += 1
            except OSError:
                pass
    return {"ficheros": n, "bytes": b}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sellar", action="store_true",
                    help="aceptar el estado actual como nueva linea base, "
                         "incluso si encogio")
    a = ap.parse_args()

    ahora = {c: medir(c) for c in CORPUS}
    previo = {}
    if os.path.exists(BASE):
        try:
            previo = json.load(io.open(BASE, encoding="utf-8")).get("corpus", {})
        except (OSError, ValueError):
            previo = {}

    print("=" * 74)
    print("INTEGRIDAD DEL CODIGO EXTRAIDO (irreemplazable)")
    print("=" * 74)
    print("\n  %-22s %9s %14s   %s" % ("corpus", "ficheros", "MB", "vs linea base"))

    encogio = []
    for c in CORPUS:
        m = ahora[c]
        if m is None:
            print("  %-22s %9s %14s   NO EXISTE" % (c, "-", "-"))
            continue
        p = previo.get(c)
        if not p:
            delta = "(primera medida)"
        else:
            df, db = m["ficheros"] - p["ficheros"], m["bytes"] - p["bytes"]
            if df < 0 or db < 0:
                delta = "!! ENCOGIO  %+d ficheros  %+.1f MB" % (df, db / 1e6)
                encogio.append((c, df, db))
            elif df or db:
                delta = "crecio  %+d ficheros  %+.1f MB" % (df, db / 1e6)
            else:
                delta = "igual"
        print("  %-22s %9d %14.1f   %s" % (c, m["ficheros"], m["bytes"] / 1e6, delta))

    if encogio:
        print("\n  !! EL CORPUS ENCOGIO. Estos ficheros no se regeneran solos:")
        for c, df, db in encogio:
            print("     %-22s %+d ficheros, %+.1f MB" % (c, df, db / 1e6))
        print("\n  Si la bajada es deliberada (consolidar duplicados), sellala:")
        print("     python %s --sellar" % os.path.relpath(__file__, RAIZ).replace("\\", "/"))
        print("  Si no lo es, recuperala del ultimo commit ANTES de seguir:")
        print("     git log --diff-filter=D --name-only -- extracted_code/ | head")
        if not a.sellar:
            return 0          # informa, no bloquea

    guardar = a.sellar or not encogio
    if guardar:
        io.open(BASE, "w", encoding="utf-8").write(
            json.dumps({"_que_es": "linea base de feedback_never_delete_extracted_code",
                        "corpus": {k: v for k, v in ahora.items() if v}},
                       indent=1, ensure_ascii=False))
        print("\n  linea base actualizada -> %s" % os.path.relpath(BASE, RAIZ).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
