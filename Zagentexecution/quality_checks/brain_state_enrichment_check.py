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

# --- self-declaration, la lee Zagentexecution/quality_checks/run_all.py -------------
# Va DESPUES del `from __future__` a proposito, no por descuido: un future statement solo
# admite delante el docstring, comentarios y lineas en blanco -- una asignacion antes es
# SyntaxError. run_all.declaration() recorre todo el cuerpo del modulo, asi que la posicion
# no cambia nada para el runner.
#
# POR QUE gate: solo lee brain_v2/brain_state.json (sin RFC, sin Gold) y devuelve 1 con
#   veredicto binario. Es el gate PREVIO A COMMITEAR el brain: el fallo que lo origino
#   (curate.py suelto tras un rebuild) borro un campo en 1.256 objetos sin mover NINGUN
#   conteo. Correrlo solo "cuando alguien se acuerde" es justo como paso.
# POR QUE conocimiento y NO herramientas: la causa esta en la tuberia, pero lo que se mide
#   es el CONTENIDO de lo que hemos escrito -- que objects[].knowledge_docs sigue ahi y que
#   claims/rules/incidents/objects no se han quedado vacios. Mide el store, no el script.
#
# !! CONFLICTO DE ORDEN EN EL REBUILD -- MEDIDO 2026-08-26, y no lo arregla este fichero.
#   Dentro de `rebuild_all.py` este gate NO puede salir verde nunca, por construccion:
#       build_brain_state.py:1057-1063  escribe SIEMPRE _pipeline.status = "INCOMPLETE"
#                                       con pending_steps = [add_knowledge_links (knowledge_docs)]
#       rebuild_all.py:374              Step 3e -> quality_checks/run_all.py --tier gate
#       rebuild_all.py:377              Step 4/7 -> add_knowledge_links.py
#       add_knowledge_links.py:52-55    recien AQUI pasa a "COMPLETE" y repuebla knowledge_docs
#   Es decir: el runner mide el brain en el unico punto del ciclo en que el campo esta vacio
#   a proposito. Corrida del 2026-08-26 sobre el fichero vivo (mtime 10:33:37): status
#   INCOMPLETE, knowledge_docs en 0 objetos de 4.382, exit 1. Las 6 capas de primer nivel OK.
#   FUERA del rebuild -- que es el momento para el que se escribio, justo antes de commitear
#   brain_state.json -- el veredicto si es real.
#
#   SE QUEDA EN `gate` A SABIENDAS, y esto es una decision, no un descuido:
#     - bajarlo a `analysis` lo saca del ciclo y deja otra vez SIN vigilar la perdida
#       silenciosa que lo origino (6.280 lineas, 1.256 objetos, cero conteos movidos). Seria
#       ponerlo en verde quitandole lo que comprueba, con otro nombre.
#     - no se toca su logica para "no disparar si INCOMPLETE": ese estado ES su caso primario
#       (un rebuild que no llego al final). Silenciarlo lo dejaria ciego.
#     - el arreglo REAL es de ORDEN y es de una linea, en rebuild_all.py: correr el Step 3e
#       DESPUES del 4/7, o sacar este check al cierre. Mientras no se haga, aqui saldra
#       FINDING en cada rebuild -- y el runner es fatal=False, asi que lo anota en
#       brain_v2/quality_checks_state.json sin abortar nada.
#   PENDIENTE PARA QUIEN TENGA EL REMIT DE brain_v2/: mover el Step 3e detras del Step 4/7.
QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "needs": "files",
    "what": ("brain_state.json sin los enriquecimientos que se anaden DESPUES del build: "
             "objects[].knowledge_docs perdido, o una capa de primer nivel vacia"),
}
# ------------------------------------------------------------------------------------

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
