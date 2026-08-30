# -*- coding: utf-8 -*-
"""cycle_progress.py — por que paso va el ciclo de analisis, y si de verdad avanza.

EL HUECO (JP, 2026-08-30: «mide lo que hace el ciclo para saber que no se pierde»)
    `run_analysis_cycle.py` escribe `cycle_state.json` UNA SOLA VEZ, al arrancar. El progreso
    sale por `say()` a stdout -- y cuando lo lanza un disparador, esa salida no la ve nadie.
    Asi que durante horas lo unico observable es la palabra RUNNING: ni por que paso va, ni
    cuantos quedan, ni si sigue vivo.

    Eso convierte "esta corriendo" y "se colgo hace dos horas" en el MISMO sintoma. Y con un
    ciclo que bloquea a todo lo demas por ser el unico escritor, no poder distinguirlos es caro.

COMO LO MIDE SIN TOCAR EL CICLO
    Cada paso deja HUELLA: los ficheros que escribe. Se lee la lista de pasos del propio
    `run_analysis_cycle.py` -- no una copia a mano, que envejeceria -- y se mira que ficheros
    del repo se han modificado DESPUES de que el ciclo arrancara. El ultimo escrito dice por
    donde va; el hueco desde entonces dice si avanza o esta parado.

    Es una inferencia, y se dice: un paso que lee mucho y escribe poco parece parado sin
    estarlo. Por eso el veredicto mira TAMBIEN si el proceso vive.
"""

QUALITY_CHECK = {
    "tier": "repo",
    "sobre": "brain_v2/methods/cycle_state.json + huella de ficheros",
    "needs": "nada",
    "what": "por que paso va el ciclo de analisis y si avanza o esta parado",
    "args": "[--minutos N]",
}

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CICLO = os.path.join(REPO, "brain_v2", "methods", "run_analysis_cycle.py")
ESTADO = os.path.join(REPO, "brain_v2", "methods", "cycle_state.json")


def pasos():
    """La lista de pasos, leida del PROPIO ciclo. Copiarla aqui seria garantizar que envejece."""
    try:
        with open(CICLO, encoding="utf-8") as fh:
            src = fh.read()
    except OSError:
        return []
    return re.findall(r'\(\s*"([^"]+\.py[^"]*)"\s*,\s*\n?\s*"([^"]+)"', src)


def vivo():
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "(Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" | "
                            "Where-Object { $_.CommandLine -like '*run_analysis_cycle*' } | "
                            "Measure-Object).Count"],
                           capture_output=True, text=True, timeout=60)
        return int((r.stdout or "0").strip() or 0)
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutos", type=int, default=15,
                    help="sin escribir mas de esto = sospechoso")
    a = ap.parse_args()

    try:
        with open(ESTADO, encoding="utf-8") as fh:
            est = json.load(fh)
    except (OSError, ValueError) as e:
        print("cycle_state ilegible: %s" % str(e)[:60])
        return 2
    status = est.get("status")
    ini = est.get("started_utc") or ""
    try:
        t_ini = datetime.datetime.fromisoformat(ini).timestamp()
    except ValueError:
        t_ini = os.path.getmtime(ESTADO)

    ps = pasos()
    ahora = time.time()
    print("=" * 92)
    print("CICLO DE ANALISIS · status=%s · arrancado %s (hace %.0f min)"
          % (status, time.strftime("%H:%M", time.localtime(t_ini)), (ahora - t_ini) / 60))
    print("=" * 92)
    print("  pasos declarados en run_analysis_cycle.py: %d" % len(ps))

    # huella: ficheros del repo escritos DESPUES del arranque
    tocados = []
    for raiz in ("brain_v2", "process_mining", "Zagentexecution/sap_data_extraction"):
        base = os.path.join(REPO, raiz)
        for dp, _, fs in os.walk(base):
            if ".git" in dp:
                continue
            for f in fs:
                if not f.endswith((".json", ".md", ".db")):
                    continue
                p = os.path.join(dp, f)
                try:
                    m = os.path.getmtime(p)
                except OSError:
                    continue
                if m > t_ini + 5:
                    tocados.append((m, os.path.relpath(p, REPO)))
    tocados.sort()
    print("  ficheros escritos desde que arranco: %d" % len(tocados))
    if tocados:
        print("\n  los ultimos 8, que es por donde va:")
        for m, p in tocados[-8:]:
            print("    %s  %s" % (time.strftime("%H:%M:%S", time.localtime(m)), p))
        quieto = (ahora - tocados[-1][0]) / 60
    else:
        quieto = (ahora - t_ini) / 60

    n = vivo()
    print("\n  procesos del ciclo vivos: %s" % ("no se pudo mirar" if n < 0 else n))
    print("  sin escribir nada desde hace: %.0f min" % quieto)

    print("\n" + "-" * 92)
    if status != "RUNNING":
        print("VEREDICTO: el ciclo NO esta corriendo (status=%s). Se puede escribir." % status)
        return 0
    if n == 0:
        print("VEREDICTO: la marca dice RUNNING y NO HAY PROCESO. El ciclo murio sin cerrar su")
        print("  estado, y esa marca bloquea a cualquier otro escritor indefinidamente.")
        print("  Comprueba tu antes de forzar nada: un falso positivo aqui rompe el unico")
        print("  mecanismo que protege los stores.")
        return 1
    if quieto > a.minutos:
        print("VEREDICTO: vivo pero sin escribir desde hace %.0f min. Puede ser un paso que LEE"
              % quieto)
        print("  mucho y escribe al final -- o puede estar colgado. No se puede distinguir desde")
        print("  fuera, y esa es justamente la carencia: el ciclo no dice por que paso va.")
        return 0
    print("VEREDICTO: vivo y AVANZANDO (ultimo fichero hace %.0f min)." % quieto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
