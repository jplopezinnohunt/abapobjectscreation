"""
agent_trace_hook.py — PostToolUse + SubagentStop. THE INVOCATION TRACE (s099).
=============================================================================
Records that a subagent actually RAN.

WHY THIS EXISTS
    Measured at s099: this project has four trigger layers and they are not equally
    reliable.

        hooks (4)          fired by the harness, always            MECHANICAL
        quality checks     fired by the rebuild, by glob           MECHANICAL
        agents (3)         fired only if the model chooses to      NOT
        skills (48)        fired only if the model chooses to      NOT

    stop_steward_hook.py cannot invoke the brain-steward. It prints a request asking the
    model to. If the model does not comply, nothing runs — and NOTHING RECORDS THAT
    NOTHING RAN. That is the disease of the 13 quality checks that sat idle for months,
    one floor up: what depends on somebody remembering does not happen.

    This session proved it. The steward gate fired twice; both times the pass was done by
    the main agent directly (which is correct per the project rule — the main agent
    executes, it does not delegate the protocol). But the `brain-steward` subagent ran
    zero times, and no artifact anywhere would tell you that.

    You cannot gate what you cannot measure. This is the measurement.

WHAT IT WRITES
    brain_v2/agent_invocations.jsonl — one line per event, append-only:
        {"at": iso, "event": "PostToolUse"|"SubagentStop", "agent": name|null,
         "session_ts": marker, "description": short}
    and, when the agent could NOT be attributed:
        "attribution": "UNAVAILABLE_IN_PAYLOAD", "payload_keys": [...]

⛔ WHAT THIS TRACE CAN AND CANNOT SEE — measured s106, read before citing any count
    PostToolUse   9 rows, 9 with a real agent name.  The launch side WORKS.
    SubagentStop  547 rows, 0 with a name.           The payload does not carry it.

    Two consequences, and the second is the one that misleads:

    (1) `agent: null` + `attribution: UNAVAILABLE_IN_PAYLOAD` is now written instead of a
        fake "(unspecified)". Those rows are NOT an agent called "(unspecified)"; they are
        the absence of an answer. `payload_keys` records what the harness DID offer, so the
        next session can extend the key list from data instead of guessing — guessing one
        key and recording nothing is exactly how this sat broken.

    (2) THE TWO COUNTS ARE NOT THE SAME POPULATION. 547 stops against 9 launches is not a
        9:547 attribution rate: there are whole days with dozens of stops and ZERO launches
        (128 on 2026-08-25, 118 on 2026-08-26, 94 on 2026-08-18). Most subagent activity
        does not arrive through the Task tool at all — skills that run in a subagent, and
        the harness's own internal agents, never touch it. So the launch trace, even
        working perfectly, sees only a slice, and "9 launches ever" is a floor, not a total.
        Do not divide one by the other.

    Append-only on purpose: a trace that can be rewritten is not a trace. Reading it is
    agent_invocation_check.py, which reports which agents have NEVER run and how long
    since each last did.

CONTRACT
    Fail-safe. Any error -> exit 0 silently. A trace that breaks the session is worse
    than no trace, and this one is not load-bearing for anything the user is doing.
"""
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
TRACE = HERE / "agent_invocations.jsonl"
TS_MARKER = HERE / ".session_start_ts"

# The Agent tool is surfaced under more than one name depending on the client; match any
# of them rather than guessing one and silently recording nothing.
AGENT_TOOLS = {"Task", "Agent"}


def session_ts():
    try:
        return TS_MARKER.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        sys.exit(0)

    event = payload.get("hook_event_name") or payload.get("hookEventName") or ""
    record = None

    if event == "PostToolUse":
        tool = payload.get("tool_name") or ""
        if tool not in AGENT_TOOLS:
            sys.exit(0)
        inp = payload.get("tool_input") or {}
        record = {
            "event": "PostToolUse",
            "agent": inp.get("subagent_type") or "(unspecified)",
            "description": str(inp.get("description") or "")[:120],
        }
        # El PROMPT es la otra mitad: sin el, el resultado no se puede juzgar contra nada.
        # Anthropic lo midio en produccion y es su fallo numero uno de delegacion: «sin
        # descripciones de tarea detalladas, los agentes duplicaban trabajo o dejaban huecos
        # criticos de informacion». Guardar su LONGITUD y su principio permite medir despues
        # si el encargo era detallado -- que es la variable que ellos senalan como causa.
        pr = inp.get("prompt")
        if isinstance(pr, str) and pr.strip():
            record["prompt_len"] = len(pr)
            record["prompt_ini"] = pr.strip()[:400]
        if inp.get("model"):
            record["model"] = inp.get("model")

    elif event == "SubagentStop":
        # MEDIDO s106: de 547 filas SubagentStop, CERO traian `subagent_type`. El payload de
        # este evento no lo lleva. Escribir "(unspecified)" como si fuera un agente era peor
        # que no escribir: 547 filas anonimas ahogaban a las 9 buenas (98,4% de ruido) y
        # cualquiera que abriera el fichero concluia que la atribucion estaba rota, cuando
        # el lado del LANZAMIENTO funciona perfecto (9 de 9 con nombre real).
        #
        # Se prueban varios nombres de clave porque el contrato del harness puede cambiar y
        # adivinar UNO y no registrar nada es como llegamos aqui.
        agente = None
        for k in ("subagent_type", "subagentType", "agent_type", "agentType",
                  "agent", "agent_name", "name"):
            v = payload.get(k)
            if isinstance(v, str) and v.strip():
                agente = v.strip()
                break
        record = {
            "event": "SubagentStop",
            "agent": agente,                      # None, NUNCA un nombre falso
            "description": "",
        }

        # --- LO QUE HACE ANOTABLE LA TRAZA, y llevabamos tirando (s107) ----------------
        # La investigacion sobre como se mide la colaboracion multi-agente
        # (brain_v2/research/wc0llab07) concluye que se mide sobre TRAZAS, no sobre lo que los
        # agentes declaran de si mismos. Y al mirar el payload en vez de disenar un medidor
        # aparecio que ya venia todo: `agent_transcript_path` es la traza completa del
        # subagente y `last_assistant_message` es su resultado. Sin el resultado no se puede
        # juzgar DERIVA DE TAREA, INFORMACION RETENIDA ni TERMINACION PREMATURA -- los tres
        # modos de MAST que este sustrato si alcanza. El puntero no ocupa; del mensaje se
        # guarda un extremo, que basta para saber si contesto a lo que se le pidio.
        for clave, destino in (("agent_id", "agent_id"),
                               ("agent_transcript_path", "traza"),
                               ("session_id", "sesion"),
                               ("prompt_id", "prompt_id"),
                               ("effort", "effort")):
            v = payload.get(clave)
            if isinstance(v, str) and v.strip():
                record[destino] = v.strip()
        msg = payload.get("last_assistant_message")
        if isinstance(msg, str) and msg.strip():
            record["resultado_len"] = len(msg)
            record["resultado_ini"] = msg.strip()[:400]
            record["resultado_fin"] = msg.strip()[-400:] if len(msg) > 800 else ""
        if agente is None:
            # LA PARTE QUE SE MECANIZA: si no se puede atribuir, registrar QUE HABIA
            # DISPONIBLE. Un trazador que no anota lo que vio no se puede mejorar -- hubo
            # que leer el codigo para descubrir que solo se intentaba UNA clave.
            record["attribution"] = "UNAVAILABLE_IN_PAYLOAD"
            record["payload_keys"] = sorted(payload.keys())[:25]

            # s107 — LA CLAVE EXISTE Y VIENE VACIA, QUE NO ES LO MISMO QUE NO EXISTIR.
            # `payload_keys` ya listaba `agent_type`, asi que el diagnostico "el payload no lo
            # lleva" era FALSO: lo lleva y esta vacio. Distinguir las dos cosas es la
            # diferencia entre "el harness cambio el contrato" y "este evento no es de un
            # agente". Y la segunda hipotesis tiene evidencia: el 2026-08-27 esta sesion
            # registro CUATRO SubagentStop habiendo lanzado CERO agentes, mientras corria
            # varias tareas de fondo. Si `SubagentStop` tambien se dispara por una tarea de
            # fondo, el 96% de filas anonimas no es un fallo de atribucion: es que la mayoria
            # NO SON AGENTES. Sin este campo no se puede separar, y una metrica de
            # colaboracion construida sobre eso mide otra cosa.
            record["claves_presentes_pero_vacias"] = [
                k for k in ("subagent_type", "agent_type", "agentType", "agent", "agent_name")
                if k in payload and not (isinstance(payload.get(k), str) and payload[k].strip())
            ]
            record["trae_background_tasks"] = "background_tasks" in payload
            record["_hipotesis_abierta"] = (
                "si trae background_tasks y agent_type vacio, puede ser el fin de una TAREA DE "
                "FONDO y no de un agente. NO VERIFICADO: hace falta correlacionar una corrida "
                "con agentes contra otra sin ellos.")

    if record is None:
        sys.exit(0)

    record["at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    record["session_ts"] = session_ts()

    try:
        with TRACE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:          # noqa: BLE001 - a trace must never break a session
        sys.exit(0)
