"""
store_write_guard_hook.py — PreToolUse. No escribas un store con el rebuild corriendo. s106.
============================================================================================

LA VIOLACION REAL DE s106, Y FUE DEL AGENTE PRINCIPAL, no de ningun subagente:
escribi `claims.json` con `rebuild_all` EN CURSO. Lo admiti en el commit cuando paso
(b8f9c40) y no corrompio nada -- la escritura es atomica -- pero el brain_state
materializado pudo quedar con un claim de diferencia hasta el siguiente rebuild. Es
exactamente la regla ADR-008 que llevaba toda la sesion exigiendole a los agentes.

POR QUE NO LO PARO NADA
    `rebuild_lock.py` EXISTE y sabe decir HELD/ORPHAN/HUNG. Pero protege REBUILD CONTRA
    REBUILD: impide arrancar un segundo rebuild. No mira las escrituras sueltas a los
    stores que el rebuild esta leyendo. El candado estaba puesto en la otra puerta.

    Y la "defensa" que yo mismo escribi despues fue prosa en un commit. Lo que depende de
    acordarse no pasa: este proyecto lleva tres casos hoy demostrandolo.

QUE HACE
    PreToolUse sobre Write/Edit/MultiEdit. Si el fichero destino es un STORE del cerebro
    y el candado del rebuild esta HELD, AVISA con el PID y los minutos que lleva.

    AVISA, NO BLOQUEA -- y es deliberado. Hay escrituras legitimas durante un rebuild (un
    doc de dominio, un skill, este mismo fichero), y un guardia que impide trabajar se
    desactiva a la semana. Lo que mata no es escribir: es escribir SIN SABERLO. Esto lo
    convierte en una decision consciente.

    Si el candado esta HUNG u ORPHAN tambien lo dice: un rebuild colgado es peor que uno
    vivo, porque nadie lo esta mirando.

CONTRATO
    Fail-safe: cualquier error -> exit 0 mudo. Un guardia que rompe la sesion es peor que
    ningun guardia.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent

# Los ficheros que el rebuild LEE para materializar. Escribir aqui mientras corre es lo que
# produce un brain_state desalineado con su fuente.
STORES = (
    "brain_v2/claims/claims.json",
    "brain_v2/incidents/incidents.json",
    "brain_v2/annotations/annotations.json",
    "brain_v2/agent_rules/feedback_rules.json",
    "brain_v2/domains/domains.json",
    "brain_v2/methods/algorithms.json",
    "brain_v2/agi/known_unknowns.json",
    "brain_v2/agi/data_quality_issues.json",
    "brain_v2/capability_model/capability_model.json",
    "brain_v2/capability_model/ontology.json",
)
HERRAMIENTAS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    if (payload.get("tool_name") or "") not in HERRAMIENTAS:
        return 0
    destino = ((payload.get("tool_input") or {}).get("file_path") or "").replace("\\", "/")
    if not destino:
        return 0
    tocado = next((s for s in STORES if destino.endswith(s)), None)
    if not tocado:
        return 0

    sys.path.insert(0, str(HERE))
    try:
        from rebuild_lock import state          # noqa: PLC0415
        est, lock = state()
    except Exception:                            # noqa: BLE001
        return 0
    if est == "FREE":
        return 0

    d = lock or {}
    detalle = "pid %s" % d.get("pid", "?")
    if d.get("_corriendo_min") is not None:
        detalle += ", %s min corriendo, %s quieto" % (d["_corriendo_min"], d.get("_quieto_min"))
    aviso = {
        "HELD": ("UN REBUILD ESTA CORRIENDO (%s) y vas a escribir en %s, que es una de sus "
                 "FUENTES. No corrompe (la escritura es atomica) pero el brain_state que "
                 "salga puede quedar desalineado con este fichero hasta el siguiente "
                 "rebuild. Es la regla de un-solo-escritor (ADR-008). Si es a proposito, "
                 "DILO en el commit; si no, espera a que termine: "
                 "python brain_v2/rebuild_progress.py"),
        "HUNG": ("EL REBUILD ESTA COLGADO (%s) y vas a escribir en %s. Peor que uno vivo: "
                 "nadie lo esta mirando y no se sabe por donde se quedo. Mira "
                 "rebuild_progress.py antes de tocar nada."),
        "ORPHAN": ("HAY UN CANDADO DE REBUILD HUERFANO (%s) sobre %s: el proceso ya no "
                   "existe. Probablemente seguro, pero el candado miente -- limpialo en "
                   "vez de ignorarlo."),
        "CORRUPT": ("EL CANDADO DEL REBUILD ESTA CORRUPTO (%s) y vas a escribir en %s. No "
                    "se puede saber si hay un rebuild vivo."),
    }.get(est)
    if not aviso:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "⛔ STORE-WRITE GUARD — " + (aviso % (detalle, tocado)),
        }
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:      # noqa: BLE001 — un guardia jamas rompe la sesion
        sys.exit(0)
