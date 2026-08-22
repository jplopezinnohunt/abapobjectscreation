"""
rebuild_lock.py — un solo escritor sobre brain_state, comprobado y no recordado.

POR QUE EXISTE. La regla de un solo escritor decia "no lances dos rebuilds", y el 2026-08-22 se
violo sin que nadie lanzara dos a sabiendas: un `rebuild_all.py` arrancado a las 23:17 SOBREVIVIO
AL SUSPEND del PC y seguia vivo nueve horas despues, cuando al reanudar arranco otro por
`curate.py`. Dos escritores concurrentes sobre `brain_state.json` durante horas; el fichero quedo
en 5.337.221 bytes cuando la version verificada de la noche anterior tenia 5.639.898. Una regla que
depende de que el operador se acuerde no cubre el caso en que el sistema se acuerda por el.

QUE HACE
  * `acquire()` escribe un lock con PID, host, hora de arranque y un HEARTBEAT que se refresca.
  * Si hay un lock y su PID SIGUE VIVO -> se niega a arrancar y dice quien manda.
  * Si el PID esta muerto -> lock HUERFANO: lo reclama y lo dice (crash o apagon).
  * Si el PID vive pero el heartbeat lleva parado mas de STALE_MIN -> COLGADO: lo dice y deja
    decidir; no mata procesos por su cuenta.
  * `--status` para consultar, `--force` para reclamar a proposito.

QUE NO HACE
  * No mata nada. Matar un escritor a medias es peor que el problema.
  * No sirve de guard al commitear: para eso esta `is_rebuild_running()`, que importan los hooks.

Uso:
    python brain_v2/rebuild_lock.py --status
    python brain_v2/rebuild_lock.py --release        # soltar a mano tras un crash
"""
import argparse
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "brain_v2" / "output" / ".rebuild.lock"
STALE_MIN = 15          # heartbeat parado mas de esto = sospechoso de colgado
MAX_MINUTES = 45        # un rebuild que pasa de aqui esta colgado, no lento


def _alive(pid):
    """¿Vive ese PID? En Windows no hay signal 0 fiable, asi que se pregunta al SO."""
    if pid is None:
        return False
    try:
        if os.name == "nt":
            import subprocess
            out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid],
                                 capture_output=True, text=True, timeout=20).stdout
            return str(pid) in out
        os.kill(pid, 0)
        return True
    except Exception:
        # No poder comprobarlo NO es prueba de que este muerto: se asume vivo.
        return True


def read():
    if not LOCK.exists():
        return None
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except Exception:
        return {"corrupt": True}


def _write(d):
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def state():
    """(estado, lock). estado: FREE | HELD | ORPHAN | HUNG | CORRUPT"""
    d = read()
    if d is None:
        return "FREE", None
    if d.get("corrupt"):
        return "CORRUPT", d
    if not _alive(d.get("pid")):
        return "ORPHAN", d
    quieto = (time.time() - d.get("heartbeat", 0)) / 60.0
    corriendo = (time.time() - d.get("started", 0)) / 60.0
    if quieto > STALE_MIN or corriendo > MAX_MINUTES:
        d["_quieto_min"] = round(quieto, 1)
        d["_corriendo_min"] = round(corriendo, 1)
        return "HUNG", d
    return "HELD", d


def acquire(force=False):
    """Devuelve True si se puede arrancar. Imprime SIEMPRE por que si dice que no."""
    st, d = state()
    if st == "HELD" and not force:
        print("NO ARRANCO: ya hay un rebuild vivo.")
        print("   pid=%s host=%s desde %s (%.1f min)"
              % (d.get("pid"), d.get("host"), d.get("started_at"),
                 (time.time() - d.get("started", 0)) / 60.0))
        print("   Espera a que termine. Si sabes que esta colgado: --force, o mata ese PID.")
        return False
    if st == "HUNG" and not force:
        print("NO ARRANCO: hay un rebuild que parece COLGADO, y no lo mato yo.")
        print("   pid=%s corriendo %.1f min · heartbeat parado %.1f min (tope %d/%d)"
              % (d.get("pid"), d.get("_corriendo_min"), d.get("_quieto_min"),
                 MAX_MINUTES, STALE_MIN))
        print("   Decide tu: mata ese PID, o relanza con --force si sabes que es un fantasma.")
        return False
    if st == "ORPHAN":
        print("Lock HUERFANO de pid=%s (%s) — el proceso ya no existe. Lo reclamo."
              % (d.get("pid"), d.get("started_at")))
    if st == "CORRUPT":
        print("Lock ilegible — lo reclamo.")
    if st in ("HELD", "HUNG") and force:
        print("--force: reclamo el lock de pid=%s. Que no haya dos escribiendo es cosa tuya."
              % d.get("pid"))
    _write({"pid": os.getpid(), "host": socket.gethostname(),
            "started": time.time(), "heartbeat": time.time(),
            "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "cmd": " ".join(sys.argv[:2])})
    return True


def beat():
    """Refresca el heartbeat. Llamalo entre pasos: un rebuild sin latido es un rebuild colgado."""
    d = read()
    if d and d.get("pid") == os.getpid():
        d["heartbeat"] = time.time()
        _write(d)


def release():
    d = read()
    if d and d.get("pid") in (os.getpid(), None):
        LOCK.unlink(missing_ok=True)
    elif d:
        LOCK.unlink(missing_ok=True)


def is_rebuild_running():
    """Para los hooks: ¿hay un rebuild vivo AHORA? Nunca commitees generados si esto es True —
    el 2026-08-21 se commiteo un brain_state a medio construir por no preguntarlo."""
    return state()[0] in ("HELD", "HUNG")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--release", action="store_true")
    a = ap.parse_args()
    if a.release:
        release()
        print("lock liberado")
        return 0
    st, d = state()
    print("estado del lock: %s" % st)
    if d:
        for k in ("pid", "host", "started_at", "cmd"):
            if k in d:
                print("   %-10s %s" % (k, d[k]))
        if "started" in d:
            print("   %-10s %.1f min" % ("corriendo", (time.time() - d["started"]) / 60.0))
        if "heartbeat" in d:
            print("   %-10s %.1f min" % ("sin latir", (time.time() - d["heartbeat"]) / 60.0))
    return 1 if st in ("HUNG", "CORRUPT") else 0


if __name__ == "__main__":
    sys.exit(main())
