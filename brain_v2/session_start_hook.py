"""
session_start_hook.py — SessionStart hook (s079).
=================================================
Two jobs, every session start:
  1. ONCE-PER-DAY brain curation ("dreaming" emulation) — on the FIRST session of the day,
     spawn curate.py in the BACKGROUND (non-blocking, detached). Guarded by a date marker so it
     runs at most once per active day. This replaces the OS scheduled task (no OS permission;
     native Claude Code hook; travels with settings.json).
  2. Inject the bootstrap context: read the LEAN index first (tiered loading), the model EXISTS,
     do not re-invent.

Fast (<1s): it only SPAWNS the background job and prints JSON. The heavy rebuild runs detached.
"""
import json, sys, subprocess, datetime, time
from pathlib import Path

HERE = Path(__file__).parent
MARKER = HERE / ".last_curation"
LOG = HERE / "curation.log"
TS_MARKER = HERE / ".session_start_ts"          # consumed by stop_durability_hook.py
NUDGE_MARKER = HERE / ".last_durability_nudge"   # reset each session so leftovers re-nudge once


def stamp_session():
    """Record session-start epoch (so the Stop durability hook scopes to THIS session's
    files) and reset the durability dedup marker so any leftover uncommitted source from a
    prior session gets one fresh nudge."""
    try:
        TS_MARKER.write_text(str(time.time()), encoding="utf-8")
        if NUDGE_MARKER.exists():
            NUDGE_MARKER.unlink()
    except Exception:
        pass


def meta_headline():
    """Read the cached meta-capability self-assessment (instant — no recompute) and return the
    one-line headline. This makes our OWN way-of-working maturity 'considered at every session start'
    (user directive 2026-06-22): every session opens knowing its weakest lever to improve."""
    try:
        m = json.loads((HERE / "meta_capability.json").read_text(encoding="utf-8"))
        weak = m.get("weakest", "?")
        ws = m.get("dimensions", {}).get(weak, {}).get("score", 0)
        return (f" SELF-ASSESSMENT (meta-capability, measured): {m.get('meta_maturity_pct','?')}% maturity in "
                f"OUR way of working; weakest capability = {weak} ({ws}). Run `python brain_v2/meta_capability.py` "
                f"for the sub-lever scorecard and `python brain_v2/claims_health.py` for the claim-verification "
                f"worklist. Pick ONE weak sub-lever and move it this session; that is how we evolve.")
    except Exception:
        return " (meta_capability.json missing — run python brain_v2/meta_capability.py to self-assess)"


def maybe_curate():
    """First session of the day -> spawn curate.py detached. Returns a note for the context."""
    try:
        today = datetime.date.today().isoformat()
        last = MARKER.read_text(encoding="utf-8").strip() if MARKER.exists() else ""
        if last == today:
            return ""  # already curated today
        MARKER.write_text(today, encoding="utf-8")
        flags = 0
        if sys.platform == "win32":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        with open(LOG, "a", encoding="utf-8") as lf:
            subprocess.Popen([sys.executable, str(HERE / "curate.py")],
                             cwd=str(HERE.parent), stdout=lf, stderr=subprocess.STDOUT,
                             creationflags=flags, close_fds=True)
        return " | daily brain curation (dreaming) started in background — see brain_v2/curation.log"
    except Exception as e:
        return f" | (curation skip: {str(e)[:60]})"


def cycle_headline():
    """Has the loop turned? Surfaced at session start, because DETECTION IS NOT ACTION.

    The cycle is scheduled weekly. A scheduled task that stops firing produces no error and
    no artifact, and the absence of fresh artifacts reads as 'nothing changed' — the most
    expensive kind of silence. check_triggers can MEASURE the gap, but nothing acts on a
    measurement nobody reads, so the instruction has to reach the agent at the one moment it
    is guaranteed to look: the start of a session.
    """
    import datetime
    st = HERE / "methods" / "cycle_state.json"
    if not st.exists():
        return (" | LOOP: the analysis cycle has NEVER recorded a run — RUN IT NOW: "
                "python brain_v2/methods/run_analysis_cycle.py")
    try:
        d = json.loads(st.read_text(encoding="utf-8"))
        last = datetime.datetime.fromisoformat(d["last_run_utc"])
        days = (datetime.datetime.now(datetime.timezone.utc) - last).days
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return " | LOOP: cycle_state.json is unreadable — run the cycle and let it rewrite it"
    if days > 8:
        return (f" | LOOP STALE: the analysis cycle last ran {days} days ago (weekly expected). "
                f"A missed schedule is silent — RUN IT NOW: "
                f"python brain_v2/methods/run_analysis_cycle.py")
    if d.get("steps_failed"):
        return (f" | LOOP: last cycle {days}d ago had {d['steps_failed']} FAILED step(s): "
                f"{', '.join(d.get('failed') or [])[:80]} — fix before trusting its artifacts")
    return f" | loop healthy: cycle ran {days}d ago, {d.get('steps_ran')} steps, 0 failed"


def _golden_size():
    """El tamano del golden se MIDE, no se lleva a fuego.

    s107: el aviso decia «15.2GB measured 2026-08-17» cuando son 21,25 GB. Una cifra
    mantenida a mano se degrada -- es lo que este proyecto documenta de UNES_DEPOSIT,
    aplicado a su propio aviso de arranque. Si no se puede medir, se dice.
    """
    try:
        p = (HERE.parent / "Zagentexecution" / "sap_data_extraction" / "sqlite"
             / "p01_gold_master_data.db")
        gb = p.stat().st_size / (1024 ** 3)
        return "%.2f GB medido ahora" % gb
    except OSError:
        return "tamano NO MEDIBLE ahora mismo — el fichero no responde"


def pendiente_al_abrir():
    """Saca el bloque PENDIENTE AL ABRIR del PMO, si lo hay.

    El bloque OPEN WORK del BRAIN_INDEX saca INCIDENTES. Los items del PMO -- y las
    decisiones que quedan en manos del dueno -- no aparecen por ningun lado, asi que una
    sesion nueva no los encuentra. Es el defecto medido en s099: guardar no es recuperar,
    y si no se llega desde los puntos de entrada, no existe.
    """
    try:
        import re                                    # noqa: PLC0415
        pmo = (HERE.parent / ".agents" / "intelligence" / "PMO_BRAIN.md")
        txt = pmo.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^> ## (PENDIENTE AL ABRIR[^\n]*)$", txt, re.M)
        if not m:
            return ""
        cab = m.group(1).strip()
        # ⛔ ACOTAR AL BLOQUE EN CURSO. Sin esto la busqueda se derrama al bloque de la
        # sesion ANTERIOR: medido el 28-ago, la cabecera decia S107 y el aviso terminaba en
        # «EMPIEZA POR H137», cerrado el dia antes, porque el bloque nuevo no traia ningun
        # «PRIMERO» y el regex siguio leyendo hacia abajo. Un arranque que manda empezar por
        # trabajo terminado es peor que no decir nada.
        resto = txt[m.end():]
        sig = re.search(r"^> ## PENDIENTE AL ABRIR", resto, re.M)
        if sig:
            resto = resto[:sig.start()]
        prim = re.search(r"^> 1\. \*\*([^*]+)\*\*", resto, re.M)
        h = re.search(r"^> - \*\*(H\d+)[^\n]*PRIMERO", resto, re.M)
        extra = ""
        if h:
            extra += " EMPIEZA POR %s." % h.group(1)
        if prim:
            extra += " Del dueno, sin tocar: %s" % prim.group(1).strip()
        return (" ⛔ HAY TRABAJO REGISTRADO AL CERRAR LA SESION ANTERIOR: \"%s\" — esta al "
                "PRINCIPIO de .agents/intelligence/PMO_BRAIN.md y NO sale en el OPEN WORK "
                "del indice, que solo lista incidentes. LEELO ANTES DE PROPONER NADA.%s"
                % (cab, extra))
    except Exception:
        return ""


def pedir_titulo_de_sesion():
    """PIDE que la sesion se renombre con su numero. El hook no puede hacerlo.

    Peticion del dueno (s108). El titulo lo pone el cliente, no el disco: ningun hook puede
    renombrar la sesion. Pero SI puede calcular cual toca -- la ultima retro que hay en
    knowledge/session_retros/ mas uno -- y pedirlo, igual que se hace con el roster de
    agentes. Sin numero, una sesion no se puede citar en un commit ni en un claim, y este
    proyecto cita la sesion en cada uno.
    """
    try:
        import re as _re                             # noqa: PLC0415
        d = HERE.parent / "knowledge" / "session_retros"
        ns = [int(m.group(1)) for f in d.iterdir()
              for m in [_re.search(r"session_(\d+)", f.name)] if m]
        if not ns:
            return ""
        return (" TITULO DE LA SESION: renombrala a s%d mas dos palabras de lo que hagas "
                "(set_session_title, o /rename). La ultima retro es la s%d. Sin numero, la "
                "sesion no se puede citar en un commit ni en un claim -- y aqui se cita en "
                "cada uno." % (max(ns) + 1, max(ns)))
    except Exception:
        return ""


def registros_pendientes():
    """Los SEIS registros de lo pendiente, contados AHORA.

    Pedido del dueno (s107): que lo relevante salga como alerta al arrancar, igual que la
    peticion del roster. Lo relevante aqui es que lo pendiente esta repartido en seis sitios
    y nadie los mira todos -- y que uno de ellos esta a CERO teniendo el resto lleno.

    Se cuenta, no se declara. La cifra del golden llevaba once dias mal en este mismo hook
    por ir escrita a mano.
    """
    try:
        import json as _j                            # noqa: PLC0415
        import re as _re                             # noqa: PLC0415
        raiz = HERE.parent
        n = {}

        def _n(p, campos=()):
            try:
                d = _j.loads((raiz / p).read_text(encoding="utf-8", errors="replace"))
            except Exception:
                return None
            if isinstance(d, list):
                return len(d)
            for c in campos:
                if isinstance(d.get(c), list):
                    return len(d[c])
            return len(d) if isinstance(d, dict) else None

        try:
            t = (raiz / ".agents" / "intelligence" / "PMO_BRAIN.md").read_text(
                encoding="utf-8", errors="replace")
            n["PMO"] = len(set(_re.findall(r"\*\*(H\d+)", t)))
        except OSError:
            n["PMO"] = None
        try:
            b = _j.loads((raiz / "process_mining" / "mining_findings.json").read_text(
                encoding="utf-8", errors="replace"))
            n["bus"] = len([q for q in (b.get("preguntas") or []) if not q.get("respuestas")])
        except Exception:
            n["bus"] = None
        n["known_unknowns"] = _n("brain_v2/agi/known_unknowns.json", ("known_unknowns",))
        n["data_quality"] = _n("brain_v2/agi/data_quality_issues.json", ("issues",))
        # ⛔ SUMAR LAS LISTAS, no adivinar la clave. La primera version busco "tasks" y
        # "backlog", que ese fichero NO TIENE, y devolvio 0 -- y ese cero se publico como
        # "registro muerto, nadie lo alimenta". Falso: las tareas viven en extraction_tasks,
        # analysis_tasks_no_extraction y research_tasks_followups. Adivinar la forma de un
        # dato en vez de leerla produjo un hallazgo inventado sobre un registro sano.
        try:
            _b = _j.loads((raiz / "brain_v2" / "capability_model"
                           / "execution_backlog.json").read_text(
                              encoding="utf-8", errors="replace"))
            n["backlog"] = sum(len(v) for k, v in _b.items()
                               if isinstance(v, list) and not k.startswith("_"))
        except Exception:
            n["backlog"] = None

        partes = " · ".join("%s %s" % (k, "?" if v is None else v) for k, v in n.items())
        aviso = (" LO PENDIENTE VIVE EN SEIS REGISTROS y ninguna sesion los mira todos: %s. "
                 % partes)
        vacios = [k for k, v in n.items() if v == 0]
        if vacios:
            aviso += ("⛔ %s a CERO teniendo el resto lleno: un registro vacio que deberia "
                      "tener contenido es INDISTINGUIBLE de uno sano si nadie lo mira -- "
                      "comprueba si alguien lo alimenta ANTES de leerlo como 'no hay trabajo'. "
                      % ", ".join(vacios))
        aviso += ("Y NINGUNO dice DESDE CUANDO esta parado un pendiente: todos dicen QUE "
                  "falta. Con esa cifra de items, es la diferencia entre una lista viva y un "
                  "cementerio.")
        return aviso
    except Exception:
        return ""


def roster_request():
    """PIDE que la sesion declare que agentes le ofrecieron. No puede medirlo el hook.

    El harness entrega el roster al CONTEXTO DEL MODELO, no al disco ni al payload de
    ningun hook (comprobado s106: este mismo hook lee stdin y ahi no viene). Asi que la
    unica forma de observarlo es que la sesion lo diga -- mismo patron que el gate del
    steward: una peticion que el modelo cumple, no una funcion que corre sola.

    Por que importa: enumerar `.claude/agents/*.md` ve los PROPIOS y es ciego al resto. En
    s106 habia SEIS invisibles, y `Explore` -- uno de ellos -- fue el agente que mas
    trabajo hizo ese dia. Ademas DOS propios no fueron ofrecidos: el roster cambia en los
    dos sentidos, y sin declaracion ese cambio de capacidad pasa inadvertido.
    """
    try:
        from record_agent_roster import anterior, session_ts as _sts  # noqa: PLC0415
        prev = anterior()
        if prev and prev.get("session_ts") == _sts():
            return ""
        edad = (" La ultima es de %s." % prev["at"][:10]) if prev else " NUNCA se ha declarado."
        return (" ROSTER DE AGENTES — DECLARALO: ningun hook puede ver que agentes te ofrecio "
                "el harness; solo tu los ves.%s Corre `python brain_v2/record_agent_roster.py "
                "<nombre> <nombre> ...` con la lista EXACTA de tu system prompt. Enumerar "
                ".claude/agents/ ve solo los PROPIOS y es ciego a Explore/Plan/general-purpose; "
                "y hay propios que algunas sesiones NO ofrecen. El diff contra la declaracion "
                "anterior es el hallazgo: un agente que aparece o desaparece es un cambio de "
                "capacidad." % edad)
    except Exception:
        return ""


def main():
    # Implementa, inyectandolas en cada arranque:
    #   feedback_load_the_domain_before_you_reason
    #   feedback_build_the_map_before_answering
    #   feedback_declare_the_cuts_before_measuring
    # No son notas: el agente las recibe antes de su primera decision.
    try:
        sys.stdin.read()
    except Exception:
        pass
    stamp_session()
    note = maybe_curate()
    meta = meta_headline()
    loop = cycle_headline()
    roster = roster_request()
    pend = pendiente_al_abrir()
    regs = registros_pendientes()
    titulo = pedir_titulo_de_sesion()
    ctx = (
        "MANDATORY FIRST ACTION (TIERED LOADING): read brain_v2/BRAIN_INDEX.md FIRST (~800 tokens, lean L1 "
        "index) — NOT the full 400K brain_state.json. Then DRILL on demand: python brain_v2/graph_queries.py "
        "capability_gaps | capability <dom> | domain <name> | incident <id> | what_reads <table> | stats. "
        "Read full brain_v2/brain_state.json ONLY when you need depth the index lacks. CRITICAL: this project "
        "ALREADY HAS an operating model — Layer 15 capability_model (domain x 10 capabilities; AS-DESIGNED + "
        "AS-RUN; G=delta=product). DO NOT re-invent it, propose a new framework, or redesign brain_state.json "
        "schema — EXTEND it. Model: brain_v2/capability_model/. Verified research: brain_v2/research/ (8 closed; "
        "dedupe vs sources_index.json; never re-assert findings_registry refuted). If stale (graph_queries.py "
        "stats): python brain_v2/rebuild_all.py. See STOP block at top of CLAUDE.md. "
        "EN CUANTO SE NOMBRE UN TEMA (DMEE, PPC, AVC, una transaccion, un area de incidencia): "
        "python brain_v2/load_domain.py <tema> y LEER TODAS LAS PARTES, antes de proponer, diagnosticar o "
        "responder. El indice ORIENTA, no da competencia. Y si el tema es un SISTEMA CONFIGURADO (arboles "
        "DMEE, customizing, jerarquias): construir o refrescar su MAPA COMPLETO antes de responder la "
        "primera pregunta — no solo la parte que la pregunta toca. Medido 2026-08-19: una sonda por "
        "pregunta dejo el 62%% de un arbol invisible y 3 de 6 formatos vivos sin mirar; el mapa entero "
        "tardo 90 segundos. Mapa de formatos de pago: python Zagentexecution/quality_checks/dmee_tree_map.py. "
        "Y TODA medida sobre una tabla transaccional declara PRIMERO sus cortes discriminantes — en pagos "
        "(REGUH) son DORIGIN (quien cobra), T042Z (FORMI=fichero / XSCHK=cheque) y el rail (que regla "
        "aplica): omitir uno inventa un problema o esconde otro, paso 3 veces el mismo dia. "
        "OPERATING GATES (apply AT the decision point, NOT from memory — this is the working model, not intuition): "
        "(1) BLOCKED — when a read/method fails, STOP: test the CORE tool empirically (reads = RFC_READ_TABLE over SNC SSO; "
        "verify, never assume), then conclude against the HARD CONSTRAINTS [P01 = READ-ONLY via RFC/SSO ONLY; NO ADT against "
        "prod; NO new objects/transports in P01; Excel is NEVER a source]. Park the gap as an execution_backlog task. Do NOT "
        "invent exotic channels (ADT-HTTP, SPNEGO/password, deploy-to-P01) — that re-litigates settled constraints (rule #156). "
        "(2) CLOSE — commit SOURCE changes FOCUSED (never 'git add -A'; brain_state.json is GENERATED, don't commit it entangled) "
        "AND ALWAYS flag the 2 assets that are LOCAL-ONLY, not in git: the Golden DB (" + _golden_size() + ", gitignored) + ~/.claude memory "
        "(git does NOT protect them — a disk/offsite backup does); then capture SAP learnings." + note + meta + loop + roster + pend + regs + titulo
    )
    print(json.dumps({
        "systemMessage": "Brain v3 — read brain_v2/BRAIN_INDEX.md first (lean). MODEL EXISTS (Layer 15) — do NOT re-invent." + note + meta + loop + roster + pend,
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx},
    }))


if __name__ == "__main__":
    main()
