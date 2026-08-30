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


TIEMPOS = os.path.join(REPO, "brain_v2", "methods", "cycle_timings.json")


def informe_tiempos():
    """CUANTO DURA NUESTRO PROCESO, PASO A PASO, Y QUE SE TIRA.

    JP: «tenemos que medir todo, para saber cuanto dura nuestro proceso, saber que tiramos y
    los tiempos». Hasta s110 el ciclo no dejaba NI UNA cifra: el tiempo se infería del hueco
    entre fechas de fichero -- y asi le atribui 68 minutos a un paso que tarda 1,8.

    Aqui no se infiere nada: se lee lo que el propio ciclo escribio de si mismo."""
    try:
        with open(TIEMPOS, encoding="utf-8") as fh:
            t = json.load(fh)
    except (OSError, ValueError):
        print("\n  (aun no hay cycle_timings.json: lo escribe el ciclo a partir de s110)")
        return
    if not t:
        return
    ult = t[-1]["utc"][:10]
    corrida = [x for x in t if x["utc"][:10] == ult]
    tot = sum(x["seg"] for x in corrida)
    ok = [x for x in corrida if x.get("rc") == 0]
    mal = [x for x in corrida if x.get("rc") != 0]
    print("\n" + "=" * 92)
    print("CUANTO DURA NUESTRO PROCESO — ultima corrida (%s)" % ult)
    print("=" * 92)
    print("  %d pasos cronometrados · %.1f min en total · %d OK · %d con fallo"
          % (len(corrida), tot / 60.0, len(ok), len(mal)))
    print("\n  %6s  %5s  %-7s %s" % ("seg", "%", "pesado", "paso"))
    print("  " + "-" * 88)
    acum = 0
    for x in sorted(corrida, key=lambda z: -z["seg"]):
        pct = 100.0 * x["seg"] / max(1, tot)
        acum += pct
        marca = "  <- aqui esta el tiempo" if acum <= 80 and pct >= 10 else ""
        print("  %6d  %4.0f%%  %-7s %s%s" % (x["seg"], pct, "SI" if x.get("pesado") else "",
                                             x["paso"][:52], marca))
    if mal:
        print("\n  PASOS QUE FALLARON — el resultado esta INCOMPLETO por ellos:")
        for x in mal:
            print("    rc=%s  %s (%s)" % (x.get("rc"), x["paso"][:60], x["script"]))
    cinco = sorted(corrida, key=lambda z: -z["seg"])[:5]
    print("\n  los 5 mas caros son el %.0f%% del tiempo. Ahi, y solo ahi, compensa mirar."
          % (100.0 * sum(x["seg"] for x in cinco) / max(1, tot)))
    print("  Y antes de optimizar cualquiera: comprobar que el trabajo es REAL y no REPETIDO.")
    print("  El unico que lo era, log_reality, paso de 22 min a 7 s con delta por _first_seen.")


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
        informe_tiempos()
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
