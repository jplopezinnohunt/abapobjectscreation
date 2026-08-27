"""
commit_session_stamp.py — cada commit dice DE QUE SESION sale. s106.
====================================================================

EL PROBLEMA, medido s106
    brain-steward corrio un rebuild de 56 min y al terminar levanto una bandera: "7
    commits de otro hilo activo aterrizaron durante mi ventana; confirmad si era una
    sesion paralela autorizada". NO lo era: eran del agente PRINCIPAL de su propia sesion.

    No fue un error de juicio suyo. UN SUBAGENTE NO PUEDE DISTINGUIR A SU PADRE DE UN
    EXTRANO: desde dentro, el trabajo de quien lo lanzo y el de un escritor ajeno se ven
    identicos -- commits apareciendo en un repo -- y el autor de git es el mismo en los dos
    casos. La pregunta "¿esto es mio?" NO TENIA RESPUESTA CONSULTABLE.

    Y la primera "solucion" fue escribir en el braintoolbox que hay que verificar con
    `git log` antes de creerse la alarma. Eso es PROSA: depende de que alguien se acuerde,
    y este proyecto lleva dos casos demostrando que lo que depende de acordarse no pasa.
    Esto es el mecanismo.

QUE HACE
    Anade un trailer `Session: <marca>` a cada mensaje de commit, con la marca de
    `.session_start_ts` -- el mismo fichero que ya usan el hook de arranque y el de
    durabilidad. Un subagente comparte el sistema de ficheros con su padre, asi que LEE LA
    MISMA MARCA: misma marca = mi sesion; marca distinta = otra sesion de verdad.

    Idempotente: si el mensaje ya trae `Session:`, no toca nada.
    Fail-safe: cualquier error -> exit 0 sin tocar el mensaje. Un sello que impide
    commitear es peor que no tener sello.

CABLEADO (no viaja solo: .git/hooks no se versiona)
    .git/hooks/prepare-commit-msg  ->  python brain_v2/commit_session_stamp.py "$1"
    El LOGICA vive aqui y si viaja; el cableado es local y esta documentado en este
    docstring a proposito, para que se pueda rehacer en otra maquina.

LO LEE
    brain_v2/whose_commits.py — responde "de estos N commits, cuantos son de ESTA sesion".
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
TS_MARKER = HERE / ".session_start_ts"
TRAILER = "Session"


def marca():
    try:
        v = TS_MARKER.read_text(encoding="utf-8").strip()
        return v or None
    except OSError:
        return None


def main():
    if len(sys.argv) < 2:
        return 0
    ruta = Path(sys.argv[1])
    m = marca()
    if not m:
        return 0
    try:
        txt = ruta.read_text(encoding="utf-8")
    except OSError:
        return 0
    if ("\n%s:" % TRAILER) in txt or txt.startswith("%s:" % TRAILER):
        return 0                      # ya sellado — idempotente
    # el trailer va al final del cuerpo, antes de los comentarios que git anade con '#'
    lineas = txt.split("\n")
    corte = len(lineas)
    for i, l in enumerate(lineas):
        if l.startswith("#"):
            corte = i
            break
    cuerpo = lineas[:corte]
    while cuerpo and not cuerpo[-1].strip():
        cuerpo.pop()
    cuerpo += ["", "%s: %s" % (TRAILER, m)]
    try:
        ruta.write_text("\n".join(cuerpo + lineas[corte:]) + "\n", encoding="utf-8")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:      # noqa: BLE001 — jamas romper un commit
        sys.exit(0)
