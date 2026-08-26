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
Guarda una linea base (cuantos ficheros y cuantos bytes por corpus) y FALLA si
baja. Una bajada legitima existe (consolidar duplicados), asi que la salida no
es "prohibido" sino "decide": --sellar acepta el estado actual y limpia el gate.
Lo que NO puede pasar es que encoja sin que nadie se entere.

    Nota 2026-08-26: hasta hoy devolvia 0 SIEMPRE y ademas no declaraba
    QUALITY_CHECK, asi que el runner nunca lo ejecuto -- vigilaba sobre el papel.
    Declararlo `gate` dejando el 0 fijo habria sido peor que no declararlo: un
    verde permanente que ademas CERTIFICA. El veredicto vive ahora en el codigo
    de salida y la valvula de escape sigue siendo --sellar.

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

# El bloque va DESPUES del `from __future__`, no pegado al docstring: un __future__
# solo admite docstring y comentarios por delante, y una asignacion antes lo rompe
# con SyntaxError -- que el runner leeria como UNPARSEABLE.
QUALITY_CHECK = {
    # gate y no analysis: es offline, sin argumentos y tarda segundos, pero sobre todo
    # su valor ENTERO depende de correr en CADA ciclo. La linea base solo avanza cuando
    # el check corre; bajo demanda ("analysis") no correria nunca, la base se pudriria y
    # quedaria un cable trampa desarmado que encima parece puesto.
    "tier": "gate",
    "needs": "files",
    # `sobre` = conocimiento, no datos_sap: este check NO lee SAP ni lo compara con nada.
    # Vigila NUESTRO almacen. La regla que mecaniza lo dice literal --
    # feedback_extracted_code_is_brain_data: el codigo extraido ES dato del brain.
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "what": ("el corpus extraido de SAP (extracted_code / extracted_sap / extracted_sap_p01) "
             "no puede encoger sin que nadie se entere: cuenta ficheros y bytes contra una "
             "linea base y sale 1 si baja y no se sella"),
    "args": "--sellar (opcional: acepta una bajada deliberada como nueva linea base)",
    # ALCANCE HONESTO, para que nadie lea de mas en el verde:
    #   * mide TAMANO (ficheros + bytes), no contenido. Un fichero sustituido por otro de
    #     los mismos bytes pasa limpio: esto es un cable trampa de volumen, no un hash.
    #   * la linea base sube SOLA al crecer, asi que un crecimiento neto puede tapar una
    #     perdida parcial ocurrida en el mismo intervalo.
}

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
            # Sale 1 y, a proposito, NO actualiza la linea base: el gate sigue rojo
            # hasta que alguien recupere los ficheros o selle la bajada. Si guardase
            # aqui, la perdida quedaria absorbida y el siguiente ciclo saldria verde.
            return 1

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
