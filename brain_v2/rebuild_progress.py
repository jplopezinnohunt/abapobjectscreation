"""¿Por donde va el rebuild? — responde en un comando, sin adivinar por mtimes.
================================================================================================
POR QUE EXISTE

    `rebuild_all.py` tarda entre 15 y 45 minutos y escribe su log EN VIVO en
    `brain_v2/output/curation.log`, con marcas `[<ts>] START Step N/7: ...` y `[<ts>] OK Step ...`.
    La informacion estaba ahi todo el tiempo; lo que no habia era una forma de PREGUNTARLO.

    Medido s104 (2026-08-26): el rebuild se lanzo en background con `| tail -30`, que TAMPONA toda
    la salida hasta que el proceso sale, asi que el fichero de captura se quedo en 0 bytes. Durante
    ~40 minutos la unica respuesta fue "sigue corriendo", comprobando a mano el `mtime` de
    `brain_state.json` y sabiendose de memoria que artefacto produce cada paso. Eso no es saber.

    ANOTARLO NO HABRIA BASTADO. Una nota que diga "grepea [Step en el curation.log" exige que
    alguien la lea, se acuerde del fichero y conozca el formato.

POR QUE ES TAN SIMPLE — y por que la primera version se tiro

    La v1 intentaba reconstruir "la corrida completa" cortando el log por la marca de Step 0. El
    log SE ACUMULA entre ejecuciones, el corte fallaba y MEZCLABA corridas: reporto "TERMINADO 7/7,
    148 minutos" mientras el proceso seguia vivo en el paso 4. Es exactamente el defecto que este
    proyecto tiene reglado -- una puerta que canta exito sin medir el efecto -- y casi se reporta
    como hecho.

    Esta version no reconstruye nada. Lee **la ultima linea de paso del fichero** y **si el log se
    mueve**. Con eso contesta las dos unicas preguntas que importan: ¿por donde va? ¿esta vivo?
    Si el ultimo marcador no permite decidir, **lo dice** en vez de inventar un porcentaje.

LA REGLA QUE MECANIZA
    `feedback_a_long_process_must_be_able_to_report_its_own_progress` — un proceso largo tiene que
    poder decir por donde va SIN abrirlo, y no se lanza con una tuberia que tampone (usar `-u`).

USO
    python brain_v2/rebuild_progress.py              # donde va y si esta vivo
    python brain_v2/rebuild_progress.py --tail 15    # ademas las ultimas marcas de paso
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = ROOT / "brain_v2" / "output" / "curation.log"

# [2026-08-26T17:54:11+04:00] START  Step 4/7: Link knowledge docs
# [2026-08-26T17:41:02+04:00] OK     Step 0: Validate canonical ontology  exit=0  (0.2s)
RE_MARK = re.compile(
    r"^\[(?P<ts>[0-9T:+\-]{19,25})\]\s+(?P<kind>START|OK|ERROR|FAIL)\s+"
    r"(?P<name>Step\s+(?P<num>[\w.]+)(?:/(?P<tot>\d+))?:[^\n]*)$")
RE_DONE = re.compile(r"^Rebuild complete\.?\s*$")
STALE_SECS = 600


def human(td):
    if td is None:
        return "?"
    s = int(td.total_seconds())
    return f"{s // 60}m {s % 60:02d}s" if s >= 60 else f"{s}s"


def main():
    ap = argparse.ArgumentParser(description="Avance del rebuild, leido del log en vivo")
    ap.add_argument("--log", default=str(DEFAULT_LOG))
    ap.add_argument("--tail", type=int, default=0, help="ultimas N marcas de paso")
    a = ap.parse_args()

    log = Path(a.log)
    if not log.exists():
        print(f"no existe el log: {log}")
        return 2

    marks, saw_complete_after_last_mark = [], False
    for raw in log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        m = RE_MARK.match(line)
        if m:
            ts = None
            try:
                ts = datetime.fromisoformat(m.group("ts"))
            except ValueError:
                pass
            marks.append({"ts": ts, "kind": m.group("kind"), "name": m.group("name").strip(),
                          "num": m.group("num"), "tot": m.group("tot")})
            saw_complete_after_last_mark = False
        elif RE_DONE.match(line):
            saw_complete_after_last_mark = True

    if not marks:
        print("el log no tiene marcas '[<ts>] START/OK Step N/M'.")
        print("  (¿se lanzo con una tuberia que tampona? usar `python -u` y sin `| tail`)")
        return 2

    last = marks[-1]
    now = datetime.now(last["ts"].tzinfo) if last["ts"] else datetime.now()
    mtime = datetime.fromtimestamp(log.stat().st_mtime, tz=now.tzinfo)
    quieto = now - mtime

    # FIN DE CORRIDA: 'Rebuild complete.' va a stdout y NO siempre llega al curation.log
    # (medido s104: solo 2 ocurrencias en 80k lineas, ambas de corridas viejas). El marcador
    # fiable es que la ULTIMA marca sea un OK sobre el paso final (num == tot).
    num_limpio = re.sub(r"\D", "", last["num"] or "")
    terminado = (saw_complete_after_last_mark or
                 (last["kind"] == "OK" and last["tot"] and num_limpio == last["tot"]))

    print("=" * 70)
    if terminado:
        print(f"REBUILD TERMINADO — ultimo paso {last['num']}/{last['tot']} cerrado con OK")
        print(f"  ultima marca : {last['name'][:60]}")
        if last["ts"]:
            print(f"  a las        : {last['ts'].strftime('%H:%M:%S')}  (hace {human(now - last['ts'])})")
    else:
        cabeza = f"paso {last['num']}" + (f" de {last['tot']}" if last["tot"] else "")
        estado = "EN CURSO" if last["kind"] == "START" else f"entre pasos (ultimo {last['kind']})"
        print(f"{estado} — {cabeza}")
        print(f"  ahora  : {last['name'][:62]}")
        if last["ts"]:
            print(f"  desde  : {last['ts'].strftime('%H:%M:%S')}  ({human(now - last['ts'])} en este paso)")
        if last["tot"]:
            try:
                pct = round(100 * (int(re.sub(r"\D", "", last["num"]) or 0) - 0.5) / int(last["tot"]))
                print(f"  aprox  : ~{max(0, pct)}%  (los pasos NO duran lo mismo: el 3 y el 4 son los largos)")
            except (TypeError, ValueError):
                pass
        marca = "   <-- SIN MOVIMIENTO, comprobar si esta colgado" if quieto.total_seconds() > STALE_SECS else ""
        print(f"  log    : escrito hace {human(quieto)}{marca}")
    print("=" * 70)

    if a.tail:
        for m in marks[-a.tail:]:
            t = m["ts"].strftime("%H:%M:%S") if m["ts"] else "  ?     "
            print(f"  {t}  {m['kind']:5}  {m['name'][:58]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
