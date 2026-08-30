# -*- coding: utf-8 -*-
"""La cadena de cierre de s110: esperar al ciclo -> aplicar -> rebuild COMPLETO -> comprobar.

POR QUE ENCADENADO Y NO A MANO
    Los tres pasos escriben en los mismos stores, y el ciclo de analisis lleva 2h40 corriendo.
    Lanzar el rebuild encima seria el doble escritor que ADR-008 prohibe -- y que esta sesion
    ha visto dos veces ya, una de ellas mia.

LA COMPROBACION FINAL ES EL PUNTO, no el rebuild
    JP: «vuelve a hacer esas preguntas». Medido ANTES: de cuatro preguntas en lenguaje natural
    sobre instrumentos que existen, dos devolvian NADA -- uno porque no estaba registrado
    (A85, huerfano mio del mismo dia) y otro porque el indice del toolgraph solo se reconstruye
    en el rebuild COMPLETO, no en --rapido.

    Si tras el rebuild siguen saliendo vacias, el mecanismo antiduplicacion no sirve por mucho
    que el algoritmo este registrado. Esa es la prueba, y por eso corre aqui y no de palabra.
"""

import json
import io
import os
import subprocess
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
os.chdir(REPO)
PY = sys.executable
ESTADO = "brain_v2/methods/cycle_state.json"
PREGUNTAS = [
    "refrescar una tabla del golden por delta",
    "saber que campos usa de verdad una tabla",
    "saber si el ciclo de analisis sigue corriendo",
    "completar los campos de clave que faltan",
]


def di(t):
    print("%s  %s" % (time.strftime("%H:%M:%S"), t))
    sys.stdout.flush()


def preguntar():
    for q in PREGUNTAS:
        try:
            r = subprocess.run([PY, "brain_v2/graph_queries.py", "tool", "para", q],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=300)
            d = json.loads(r.stdout)
            a = d.get("2_YA_EXISTE_ESTE_ALGORITMO") or []
            n = [x.get("nombre") for x in a[:3]] if isinstance(a, list) else []
            print("   %-46s -> %s" % (q[:46], ", ".join(x for x in n if x) or "NADA"))
        except Exception as e:
            print("   %-46s -> error %s" % (q[:46], str(e)[:40]))
    sys.stdout.flush()


def main():
    di("esperando a que el ciclo cierre (hasta 3 h)")
    for i in range(360):
        try:
            st = json.load(io.open(ESTADO, encoding="utf-8")).get("status")
        except Exception:
            st = "ILEGIBLE"
        if st != "RUNNING":
            di("EL CICLO CERRO: status=%s" % st)
            break
        if i and i % 20 == 0:
            di("  sigue RUNNING (+%d min de espera)" % (i // 2))
        time.sleep(30)
    else:
        di("el ciclo sigue RUNNING tras 3 h -- NO se aplica ni se reconstruye")
        return 3

    di("aplicando lo del steward")
    r = subprocess.run([PY, "Zagentexecution/tasks/2026_08_29_febko_delta/aplicar_steward_s110.py"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout or "")
    if r.returncode:
        di("APLICACION FALLIDA rc=%d -- no se reconstruye sobre stores a medias" % r.returncode)
        print((r.stderr or "")[:500])
        return r.returncode

    di("REBUILD COMPLETO (~56 min medidos; si pasa mucho de ahi, algo va mal)")
    t0 = time.time()
    b = subprocess.run([PY, "brain_v2/rebuild_all.py"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    mins = (time.time() - t0) / 60
    di("rebuild terminado en %.0f min (rc=%d)" % (mins, b.returncode))
    for ln in (b.stdout or "").splitlines():
        if any(k in ln.lower() for k in ("complete", "fail", "error", "coverage", "blind")):
            print("   " + ln.strip()[:120])

    di("LA PRUEBA: las mismas cuatro preguntas, despues del rebuild")
    preguntar()
    di("fin de la cadena")
    return 0


if __name__ == "__main__":
    sys.exit(main())
