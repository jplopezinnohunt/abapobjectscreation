"""
whose_commits.py — "¿estos commits son MIOS o de otra sesion?" s106.
====================================================================

LA PREGUNTA QUE NO TENIA RESPUESTA. Un subagente que ve el repo moverse mientras trabaja
no puede saber si eso lo hizo su padre o un escritor ajeno: el autor de git es el mismo.
En s106 brain-steward levanto por eso una bandera de "sesion paralela" que era FALSA, y la
verificacion costo un cruce a mano de horas y mensajes de commit.

Esto responde en un comando, leyendo el trailer `Session:` que pone
`commit_session_stamp.py` via el hook prepare-commit-msg.

USO
    python brain_v2/whose_commits.py                 # desde el arranque de esta sesion
    python brain_v2/whose_commits.py <ref>           # desde un commit/ref concreto
    python brain_v2/whose_commits.py --desde-hace 60 # ultimos 60 minutos

SALIDA
    MIOS      commits con el mismo `Session:` que .session_start_ts
    AJENOS    commits con OTRA marca -> ahi si hay un escritor paralelo de verdad
    SIN SELLO commits anteriores al sello, o hechos sin el hook cableado

⛔ SIN SELLO NO ES AJENO. Todo lo anterior a s106 no lo lleva, y un commit hecho en una
maquina sin el hook tampoco. Se cuentan APARTE y se dice que no se puede decidir sobre
ellos: convertir "no lo se" en "es de otro" es exactamente la alarma falsa que este
instrumento existe para evitar.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
TS_MARKER = HERE / ".session_start_ts"
ROOT = HERE.parent
SEP = "\x1e"


def marca_actual():
    try:
        return (TS_MARKER.read_text(encoding="utf-8").strip() or None)
    except OSError:
        return None


def _git(*args):
    try:
        r = subprocess.run(["git", "-C", str(ROOT)] + list(args),
                           capture_output=True, text=True, timeout=60)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def main(argv):
    mia = marca_actual()
    rango = []
    if argv and argv[0] == "--desde-hace":
        mins = argv[1] if len(argv) > 1 else "60"
        rango = ["--since=%s minutes ago" % mins]
        desc = "ultimos %s minutos" % mins
    elif argv:
        rango = ["%s..HEAD" % argv[0]]
        desc = "desde %s" % argv[0]
    else:
        # sin ref: desde el ultimo commit ANTERIOR al arranque de esta sesion no se puede
        # saber sin el sello, asi que se usa una ventana amplia y se clasifica por sello.
        rango = ["--since=12 hours ago"]
        desc = "ultimas 12 horas"

    fmt = "%h" + SEP + "%ad" + SEP + "%s" + SEP + "%(trailers:key=Session,valueonly)"
    out = _git("log", "--pretty=" + fmt, "--date=format:%H:%M:%S", *rango)
    filas = [l for l in out.split("\n") if l.strip()]

    mios, ajenos, sin_sello = [], [], []
    for l in filas:
        p = l.split(SEP)
        if len(p) < 4:
            continue
        h, fecha, asunto, sesion = p[0], p[1], p[2], p[3].strip()
        if not sesion:
            sin_sello.append((h, fecha, asunto))
        elif mia and sesion == mia:
            mios.append((h, fecha, asunto))
        else:
            ajenos.append((h, fecha, asunto, sesion))

    print("=" * 74)
    print("DE QUIEN SON ESTOS COMMITS — %s" % desc)
    print("  mi marca de sesion: %s" % (mia or "(no hay .session_start_ts)"))
    print("=" * 74)
    print("  MIOS (misma sesion): %d" % len(mios))
    for h, f, s in mios[:12]:
        print("     %s  %s  %s" % (h, f, s[:52]))
    print()
    print("  AJENOS (otra marca): %d" % len(ajenos))
    for h, f, s, ses in ajenos[:12]:
        print("     %s  %s  %s   [sesion %s]" % (h, f, s[:40], ses[:16]))
    if not ajenos:
        print("     ninguno — NO hay escritor paralelo en esta ventana")
    print()
    print("  SIN SELLO (no decidible): %d" % len(sin_sello))
    for h, f, s in sin_sello[:6]:
        print("     %s  %s  %s" % (h, f, s[:52]))
    if sin_sello:
        print("     ^ anteriores al sello (s106) o hechos sin el hook cableado.")
        print("       SIN SELLO NO ES AJENO: no se puede decidir, y no se decide.")
    print("-" * 74)
    if ajenos:
        print("HAY OTRA SESION ESCRIBIENDO. Coordina antes de tocar stores compartidos")
        print("  (ADR-008: el mas preciso o el mas temprano gana; nunca se clobbera).")
        return 1
    print("Sin escritor paralelo detectado en esta ventana.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
