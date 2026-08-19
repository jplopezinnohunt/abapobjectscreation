#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
brain_state_enrichment_check.py -- lo que el rebuild anade DESPUES no puede perderse.

Por que existe
--------------
2026-08-19: tras un rebuild completo se lanzo `curate.py` y el fichero perdio
6.280 lineas sin que cambiara NINGUN conteo -- claims 517, reglas 214, objetos
1.791, cobertura 100%, todo igual. Lo que desaparecio fue un campo dentro de los
objetos: `knowledge_docs`, en los 1.256 que lo tenian.

No es inocuo. Ese campo es un salto obligatorio del recorrido que documenta
CLAUDE.md ("objetos[X] -> annotations, claims, knowledge_docs"): sin el, una
sesion que llega a un objeto ya no encuentra su documentacion.

La causa es de ORDEN, no de logica: `add_knowledge_links.py` es el paso 4/7 del
rebuild y enriquece el fichero DESPUES de construirlo. `curate.py` lo reconstruye
desde los stores y no arrastra ese enriquecimiento. Correr la curacion suelta tras
un rebuild deshace el paso 4/7 en silencio.

Un check de conteos no lo habria visto nunca. Este mira DENTRO.

    python Zagentexecution/quality_checks/brain_state_enrichment_check.py

Sale 1 si falta un enriquecimiento. Si salta: NO commitear brain_state.json --
`git checkout HEAD -- brain_v2/brain_state.json` y volver a lanzar el rebuild
entero en vez de la curacion suelta.
"""

from __future__ import annotations

import io
import json
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ESTADO = os.path.join(RAIZ, "brain_v2", "brain_state.json")

# campo dentro de objects[] -> (quien lo pone, minimo de objetos que deben tenerlo)
# El minimo es deliberadamente bajo: detecta la DESAPARICION, no vigila el volumen.
ENRIQUECIMIENTOS = {
    "knowledge_docs": ("brain_v2/add_knowledge_links.py (paso 4/7 del rebuild)", 500),
}
# claves de primer nivel que ninguna regeneracion puede dejar vacias
CAPAS = {"claims": 100, "rules": 100, "incidents": 5, "objects": 500,
         "capability_model": 1, "core_principles": 3}


def main():
    if not os.path.exists(ESTADO):
        print("brain_state.json no existe -- nada que comprobar")
        return 0
    b = json.load(io.open(ESTADO, encoding="utf-8"))
    objetos = b.get("objects") or {}
    vals = objetos.values() if isinstance(objetos, dict) else objetos

    print("=" * 76)
    print("ENRIQUECIMIENTOS DEL BRAIN STATE -- lo que se anade despues de construirlo")
    print("=" * 76)

    fallos = []
    pipe = b.get("_pipeline") or {}
    estado = pipe.get("status")
    print("\n  estado del pipeline: %s" % (estado or "(sin marca -- fichero anterior al arreglo)"))
    if estado == "INCOMPLETE":
        print("     !! el rebuild NO llego al final. Faltan: %s"
              % ", ".join(pipe.get("pending_steps") or ["?"]))
        fallos.append(("_pipeline.status", 0, 1, "brain_v2/add_knowledge_links.py"))

    print("\n  dentro de objects[]:")
    for campo, (quien, minimo) in ENRIQUECIMIENTOS.items():
        n = sum(1 for v in vals if isinstance(v, dict) and v.get(campo))
        ok = n >= minimo
        print("     %-18s %6d objetos   (minimo %d)   %s"
              % (campo, n, minimo, "OK" if ok else "!! PERDIDO"))
        if not ok:
            fallos.append((campo, n, minimo, quien))

    print("\n  capas de primer nivel:")
    for capa, minimo in sorted(CAPAS.items()):
        v = b.get(capa)
        n = len(v) if hasattr(v, "__len__") else 0
        ok = n >= minimo
        print("     %-18s %6d              (minimo %d)   %s"
              % (capa, n, minimo, "OK" if ok else "!! VACIA O CORTA"))
        if not ok:
            fallos.append((capa, n, minimo, "rebuild_all.py"))

    print("\n" + "-" * 76)
    if fallos:
        for campo, n, minimo, quien in fallos:
            print("!! %s: %d, se esperaban >= %d. Lo pone %s." % (campo, n, minimo, quien))
        print("\nNO commitear brain_state.json en este estado. Restaurar y rehacer:")
        print("   git checkout HEAD -- brain_v2/brain_state.json")
        print("   python brain_v2/rebuild_all.py        # el rebuild ENTERO, no curate.py suelto")
        return 1
    print("Todos los enriquecimientos presentes.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
