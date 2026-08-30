# -*- coding: utf-8 -*-
"""Rellena el campo `script` de las fichas de algoritmo que no dicen donde vive su codigo.

EL DEFECTO, medido el 2026-08-30
    De 112 algoritmos registrados, solo SIETE declaraban su `script`. Sin ese campo, un
    algoritmo con codigo perfectamente sano aparece en cualquier recuento como implementacion
    ausente -- y eso manda a construir de nuevo algo que ya existe, que es justo lo que el
    registro deberia impedir.

Y UN ERROR MIO QUE ESTE FICHERO CORRIGE
    Publique "4 algoritmos registrados y su fichero NO EXISTE". Falso: ninguno tenia siquiera
    campo `script`, y A72 SI tiene codigo -- `house_bank_ebs_wiring_check.py`. Mi busqueda por
    nombre no contemplaba el sufijo `_check`, asi que acuse al repositorio de un fallo de mi
    lookup. Es el mismo error de medir el proxy en vez del efecto, por tercera vez hoy.

LO QUE NO HACE, Y ES DELIBERADO
    No inventa rutas. Solo rellena cuando existe un fichero cuyo nombre coincide con el del
    algoritmo (con o sin el prefijo `A12_`, con o sin sufijo `_check`). Lo que no casa se
    DECLARA sin tocar: muchos de esos no son scripts sino TECNICAS -- `A1_chunked_temporal_read`
    es una forma de leer, no un programa -- y a esos no les falta un fichero: les falta decir
    que no lo tienen.
"""

import glob
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

P = "brain_v2/methods/algorithms.json"


def main():
    d = json.load(io.open(P, encoding="utf-8"))
    A = d["algorithms"]
    todos = {}
    for x in glob.glob("**/*.py", recursive=True):
        todos[os.path.basename(x).rsplit(".", 1)[0]] = x.replace(os.sep, "/")

    puestos, sin = 0, []
    for k, v in A.items():
        if v.get("script"):
            continue
        base = re.sub(r"^[A-Z]\d+_", "", k)
        c = todos.get(base) or todos.get(base + "_check") or todos.get(k)
        if not c:
            sin.append(k)
            continue
        v["script"] = c
        v["_script_derivado"] = (
            "anadido en s110: la ficha no decia donde vivia su codigo y el fichero se encontro "
            "por el nombre. Sin este campo, un algoritmo sano aparece como implementacion "
            "ausente y manda a construir de nuevo lo que ya existe")
        puestos += 1

    json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    ok = sum(1 for v in A.values() if v.get("script") and os.path.exists(v["script"]))
    print("algoritmos: %d" % len(A))
    print("  `script` anadido ahora            : %d" % puestos)
    print("  declaran su codigo Y existe       : %d (eran 7)" % ok)
    print("  sin fichero que case por el nombre: %d" % len(sin))
    print("\n  esos %d hay que MIRARLOS uno a uno: muchos son TECNICAS, no programas." % len(sin))
    print("  Ejemplos: %s" % ", ".join(sin[:6]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
