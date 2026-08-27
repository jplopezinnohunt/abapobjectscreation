"""
agent_invocation_check.py — ¿que agentes NO han corrido nunca? s106.
====================================================================

EL LECTOR QUE FALTABA. `agent_trace_hook.py` lleva desde s099 escribiendo
`brain_v2/agent_invocations.jsonl` y su propio docstring declara: *"Reading it is
agent_invocation_check.py, which reports which agents have NEVER run and how long since
each last did"*. **Ese fichero no existia.** 556 filas escritas y ningun lector: el
huerfano propio, aplicado al instrumento que se creo justo para no tener puntos ciegos.

Escribir el trazador no era el trabajo. El trabajo era cerrarlo.

QUE CRUZA -- y por que necesita las DOS fuentes
    poblacion : la ULTIMA DECLARACION DE ROSTER (record_agent_roster.py). No
                `.claude/agents/*.md`: eso ve solo los PROPIOS y es ciego a Explore, Plan,
                general-purpose... que son del harness y no viven en disco. Medido s106:
                18 declarados = 14 propios + 6 solo-harness, y ademas 2 propios que esa
                sesion NO ofrecio. Contar contra el disco da la cifra equivocada en los
                dos sentidos.
    uso       : las filas `PostToolUse` del trace, que son las unicas atribuidas.

⛔ LO QUE ESTE CHECK NO PUEDE VER, declarado aqui para que nadie lea su silencio como dato
    (1) Las filas `SubagentStop` NO llevan el agente -- el payload del harness no lo trae
        (medido: 547 de 547 sin nombre). Desde s106 se escriben con `agent: null` y
        `attribution: UNAVAILABLE_IN_PAYLOAD` en vez de un "(unspecified)" que parecia un
        agente. Aqui se CUENTAN APARTE y no se atribuyen a nadie.
    (2) La mayoria de la actividad de subagentes NO PASA por la herramienta Task: hay dias
        con 128 paradas y CERO lanzamientos. Skills que corren en subagente y agentes
        internos del harness nunca la tocan. Por tanto "N lanzamientos" es un SUELO.
    (3) NUNCA HABER CORRIDO NO ES NUNCA HABER SERVIDO. Un agente sin lanzamientos puede ser
        tema dormido, no perdida -- la misma distincion que el claim 618 hizo para los
        skills sin lector. Este check RANKEA donde mirar; no dicta que retirar.
        Y nada se retira sin evidencia (feedback_never_retire_anything_without_evidence).

Solo LECTURA. Informa; no falla por que un agente no haya corrido -- eso seria convertir
una metrica de proximidad en una puerta, que es justo lo que la regla prohibe.

Uso:
    python agent_invocation_check.py
"""

QUALITY_CHECK = {
    "tier": "analysis",       # informa, no bloquea: un agente sin uso no es un defecto
    "sobre": "herramientas",  # datos_sap | conocimiento | herramientas
    "needs": "nada",
    "what": "que agentes del roster declarado no se han invocado nunca, y cuando fue la ultima vez",
    "args": "(ninguno)",
}

import datetime
import json
import os
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRACE = os.path.join(ROOT, "brain_v2", "agent_invocations.jsonl")
ROSTER = os.path.join(ROOT, "brain_v2", "agent_roster.jsonl")
AGENTS = os.path.join(ROOT, ".claude", "agents")


def _jsonl(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]
    except (OSError, ValueError):
        return []


def poblacion():
    """El roster DECLARADO manda; el disco es el fallback, y se dice cual se uso."""
    rs = _jsonl(ROSTER)
    if rs:
        ult = rs[-1]
        return sorted(ult.get("declarados") or []), "roster declarado %s" % ult.get("at", "")[:10]
    try:
        propios = sorted(f[:-3] for f in os.listdir(AGENTS) if f.endswith(".md"))
    except OSError:
        propios = []
    return propios, ("SOLO DISCO — nunca se declaro un roster, asi que los agentes del "
                     "harness (Explore, Plan...) NO estan contados")


def main():
    filas = _jsonl(TRACE)
    if not filas:
        print("no hay trace todavia (%s)" % TRACE)
        return 0

    pob, fuente = poblacion()
    # "(unspecified)" es el marcador LEGADO de las filas anteriores a s106: es una cadena,
    # o sea TRUTHY, asi que un `if r.get("agent")` a secas las cuenta como atribuidas y el
    # check reporta 0 no-atribuidas habiendo 547. Paso en la primera corrida de este mismo
    # fichero. Un centinela que no se declara ausente se cuela como dato.
    NO_ATRIBUIDO = (None, "", "(unspecified)")

    def atribuido(r):
        return r.get("agent") not in NO_ATRIBUIDO

    lanz = [r for r in filas if r.get("event") == "PostToolUse" and atribuido(r)]
    paradas = [r for r in filas if r.get("event") == "SubagentStop"]
    sin_atribuir = [r for r in paradas if not atribuido(r)]

    veces = Counter(r["agent"] for r in lanz)
    ultima = {}
    for r in sorted(lanz, key=lambda x: x.get("at", "")):
        ultima[r["agent"]] = r.get("at", "")

    hoy = datetime.date.today()

    def dias(iso):
        try:
            return (hoy - datetime.date.fromisoformat(iso[:10])).days
        except (ValueError, TypeError):
            return None

    print("=" * 74)
    print("INVOCACION DE AGENTES — poblacion: %d  (%s)" % (len(pob), fuente))
    print("=" * 74)
    print("  lanzamientos ATRIBUIDOS (PostToolUse): %d" % len(lanz))
    print("  paradas (SubagentStop)               : %d, de ellas SIN atribuir %d  <- el payload no lo trae"
          % (len(paradas), len(sin_atribuir)))
    print("     ^ no son la misma poblacion: NO dividir una por otra (ver docstring)")

    # TRES GRUPOS, no uno. La primera version publicaba "33% de cobertura" mezclandolos, y
    # esa cifra es tan inutil como lo era "27 skills sin lector" antes del claim 618: junta
    # poblaciones distintas y esconde la que importa.
    #   GENERICOS DEL HARNESS  no son instrumentos de dominio (Plan, claude, statusline...).
    #                          "nunca invocado" no significa nada para ellos: FUERA del %.
    #   PROPIOS CABLEADOS      les delegan y declaran instrumentos: estan integrados en el
    #                          grafo. Si no han corrido es la VENTANA, no abandono.
    #   AISLADOS               ni les delegan ni delegan. Ahi si hay algo que mirar.
    GENERICOS = {"Plan", "claude", "general-purpose", "claude-code-guide", "statusline-setup"}
    try:
        import json as _j
        _tg = _j.load(open(os.path.join(ROOT, "brain_v2", "toolgraph.json"), encoding="utf-8"))
        _ar = _tg.get("aristas") or []
        din = Counter(a["a"] for a in _ar if a.get("rel") == "DELEGA")
        dout = Counter(a["de"] for a in _ar if a.get("rel") == "DELEGA")
    except (OSError, ValueError, KeyError):
        din = dout = Counter()

    medibles = [a for a in pob if a not in GENERICOS]
    corridos = [a for a in medibles if a in veces]
    nunca = [a for a in medibles if a not in veces]
    aislados = [a for a in nunca if not din[a] and not dout[a]]
    cableados = [a for a in nunca if a not in aislados]
    genericos = [a for a in pob if a in GENERICOS]
    fuera = sorted(set(veces) - set(pob))

    fechas = sorted(r.get("at", "")[:10] for r in lanz if r.get("at"))
    ventana = ("%s -> %s" % (fechas[0], fechas[-1])) if fechas else "sin datos"

    print()
    print("  HAN CORRIDO (%d de %d medibles):" % (len(corridos), len(medibles)))
    for a in sorted(corridos, key=lambda x: -veces[x]):
        d = dias(ultima.get(a, ""))
        print("     %-28s %2d vez(ces)  ultima hace %s dia(s)"
              % (a, veces[a], d if d is not None else "?"))
    print()
    print("  NUNCA corrieron, PERO ESTAN CABLEADOS (%d) — les delegan y declaran"
          " instrumentos:" % len(cableados))
    for a in cableados:
        print("     %-26s le delegan %d · delega en %d" % (a, din[a], dout[a]))
    print("     ^ NO es abandono: es la VENTANA. Con %d lanzamientos trazados en %s sobre"
          % (len(lanz), ventana))
    print("       %d agentes medibles, la mayoria saldria a cero AUNQUE TODOS estuvieran"
          % len(medibles))
    print("       sanos. Concluir 'no se usa' de aqui es un error de denominador.")
    print()
    print("  AISLADOS — ni les delegan ni delegan, y nunca corrieron (%d):" % len(aislados))
    for a in aislados:
        print("     %s" % a)
    print("     ^ ESTOS si son el hallazgo: nadie los nombra y ellos no nombran a nadie.")
    print()
    print("  genericos del harness, FUERA del porcentaje (%d): %s"
          % (len(genericos), ", ".join(genericos) or "-"))
    print("     ^ no son instrumentos de dominio; 'nunca invocado' no les aplica.")

    if fuera:
        print()
        print("  invocados y NO en el roster declarado (%d): %s" % (len(fuera), ", ".join(fuera)))
        print("     ^ o el roster esta caduco, o son de otra sesion con otro harness")

    print("-" * 74)
    pct = (100.0 * len(corridos) / len(medibles)) if medibles else 0.0
    print("cobertura de invocacion: %.0f%% (%d de %d MEDIBLES) — informativo, no es una puerta"
          % (pct, len(corridos), len(medibles)))
    print("  denominador declarado: %d del roster menos %d genericos del harness."
          % (len(pob), len(genericos)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
