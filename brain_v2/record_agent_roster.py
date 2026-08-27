"""
record_agent_roster.py — la sesion DECLARA que agentes le ofrecieron. s106.
==========================================================================

POR QUE ESTO NO ES UN HOOK

    Porque no puede serlo. El roster de agentes lo entrega el harness al CONTEXTO DEL
    MODELO, no al disco y no al payload de ningun hook: `session_start_hook.py` hace
    `sys.stdin.read()` y lo tira, y aunque lo parseara, ahi no viene. Medido s106.

    Consecuencia dura: un minero que enumere `.claude/agents/*.md` encuentra los PROPIOS y
    es estructuralmente ciego al resto. En s106 eran SEIS invisibles -- Explore, Plan,
    general-purpose, claude, claude-code-guide, statusline-setup -- y `Explore` fue, medido
    por consumo, el agente que MAS trabajo hizo ese dia (~301K tokens, mas que ninguno).
    El instrumento que mide nuestra colaboracion era ciego al que mas colaboro.

    El unico observador posible es la SESION. Por eso esto se llama desde la sesion, y por
    eso el `session_start_hook` pide que se haga: es el mismo patron que el gate del
    steward -- una peticion que el modelo cumple, no una funcion que se ejecuta sola.

Y POR QUE NO BASTA CON ESCRIBIRLO EN PROSA

    Porque ya se hizo, el mismo dia, en `braintoolbox.yaml`, y es exactamente la
    enumeracion mantenida a mano que este proyecto lleva dos casos demostrando que se
    degrada (`DEMASIADO_COMUNES`, `cubre_tablas`). Una lista en prosa no se puede diffear
    contra la de ayer. Esta si: cada declaracion se compara con la anterior y el CAMBIO es
    el hallazgo -- un agente que aparece o desaparece del harness es un cambio de
    capacidad de la instalacion, y hoy pasaria inadvertido.

LO QUE ESCRIBE
    brain_v2/agent_roster.jsonl, append-only, una linea por declaracion:
        {"at": iso, "session_ts": marca, "declarados": [...], "propios": [...],
         "solo_harness": [...], "propios_no_ofrecidos": [...],
         "nuevos_vs_anterior": [...], "desaparecidos_vs_anterior": [...]}

    `propios` se MIDE de `.claude/agents/*.md`. `declarados` es lo unico declarado por la
    sesion, y va marcado como tal: es la unica linea del store que no es recalculable.

USO
    python brain_v2/record_agent_roster.py Explore Plan general-purpose ...
    python brain_v2/record_agent_roster.py --estado      # ultima declaracion y su edad
"""
import datetime
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "agent_roster.jsonl"
AGENTS = HERE.parent / ".claude" / "agents"
TS_MARKER = HERE / ".session_start_ts"


def propios():
    try:
        return sorted(f[:-3] for f in os.listdir(AGENTS) if f.endswith(".md"))
    except OSError:
        return []


def session_ts():
    try:
        return TS_MARKER.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


def anterior():
    try:
        lineas = [l for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
        return json.loads(lineas[-1]) if lineas else None
    except (OSError, ValueError):
        return None


def estado():
    prev = anterior()
    if not prev:
        print("NUNCA se ha declarado un roster.")
        print("  Corre:  python brain_v2/record_agent_roster.py <nombre> <nombre> ...")
        print("  con la lista EXACTA de agentes que esta sesion tiene disponibles.")
        return 1
    misma = prev.get("session_ts") == session_ts()
    print("ultima declaracion: %s  (%s)" % (prev["at"], "ESTA sesion" if misma
                                            else "OTRA sesion — vuelve a declararlo"))
    print("  declarados %d · propios %d · solo del harness %d · propios no ofrecidos %d"
          % (len(prev.get("declarados") or []), len(prev.get("propios") or []),
             len(prev.get("solo_harness") or []), len(prev.get("propios_no_ofrecidos") or [])))
    if prev.get("solo_harness"):
        print("  solo del harness: %s" % ", ".join(prev["solo_harness"]))
    return 0 if misma else 1


def main(argv):
    if not argv or argv[0] in ("--estado", "--status"):
        return estado()

    decl = sorted({a.strip() for a in argv if a.strip()})
    mios = propios()
    prev = anterior()
    prev_decl = set((prev or {}).get("declarados") or [])

    rec = {
        "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "session_ts": session_ts(),
        "_declarados_es_lo_unico_no_recalculable": True,
        "declarados": decl,
        "propios": mios,
        "solo_harness": sorted(set(decl) - set(mios)),
        "propios_no_ofrecidos": sorted(set(mios) - set(decl)),
        "nuevos_vs_anterior": sorted(set(decl) - prev_decl) if prev else [],
        "desaparecidos_vs_anterior": sorted(prev_decl - set(decl)) if prev else [],
    }
    try:
        with OUT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:
        print("no pude escribir: %s" % e)
        return 1

    print("roster declarado: %d agentes" % len(decl))
    print("  propios (medidos en disco) : %d" % len(mios))
    # H140/s107 — la palabra tiene que ser UNOBSERVABLE, no 'solo del harness'.
    # Son lo mismo para un humano y NO para el resto de instrumentos: `UNOBSERVABLE` es el
    # termino que este proyecto fijo (claim 620, destinos HTTP) para 'no se puede ver', frente
    # a 'no hay'. Decirlo de otra forma deja a quien lea esta salida sin la unica senal que
    # distingue un CERO MEDIDO de un CERO CIEGO -- y este es un cero ciego POR CONSTRUCCION:
    # el harness entrega esa lista al contexto del modelo, no al disco.
    print("  UNOBSERVABLE desde disco   : %d  %s"
          % (len(rec["solo_harness"]), ", ".join(rec["solo_harness"]) or "-"))
    print("      ^ solo del harness: no versionados, no enumerables. Un minero que cuente")
    print("        `.claude/agents/*.md` y diga 'hay %d' comete el defecto de H134."
          % len(mios))
    print("  propios NO ofrecidos hoy   : %d  %s"
          % (len(rec["propios_no_ofrecidos"]), ", ".join(rec["propios_no_ofrecidos"]) or "-"))
    print("      ^ existen en disco y NO son invocables hoy: ser propio no es ser invocable")
    if prev:
        if rec["nuevos_vs_anterior"] or rec["desaparecidos_vs_anterior"]:
            print("  ⚠ CAMBIO DE CAPACIDAD frente a la declaracion anterior:")
            if rec["nuevos_vs_anterior"]:
                print("      aparecen  : %s" % ", ".join(rec["nuevos_vs_anterior"]))
            if rec["desaparecidos_vs_anterior"]:
                print("      desaparecen: %s" % ", ".join(rec["desaparecidos_vs_anterior"]))
        else:
            print("  sin cambios frente a la declaracion anterior")
    else:
        print("  (primera declaracion — no hay con que comparar todavia)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
