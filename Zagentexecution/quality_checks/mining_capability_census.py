"""GATE: un script que MINA y no esta registrado es una capacidad que se pierde al cerrar sesion.

POR QUE EXISTE
    El censo anterior solo miraba `process_mining/`, y los mineros estan repartidos por todo el
    repo: `Zagentexecution/sap_data_extraction/scripts/`, `brain_v2/`, `scripts/`. Con esa
    ventana estrecha, un script que lee el log de auditoria y descubre como trabaja la casa
    podia existir durante meses sin figurar en ningun sitio.

    Y el caso que lo prueba: el metodo que encontro ALLOS -- una herramienta que llevaba mas de
    un ano sin identificar -- vivio como PROMPT de un agente, sin algoritmo. Un metodo que solo
    vive en un prompt no se puede repetir, ni programar, ni gatear, ni comparar con la corrida
    del mes pasado. El hallazgo se guardo; la forma de encontrarlo, no.

QUE CUENTA COMO MINAR
    Leer datos de EVENTO -- el log de auditoria, el log de cambios, la cola de batch input, la
    tabla de jobs -- para descubrir COMO SE TRABAJA. No cuenta leer una tabla de configuracion
    ni de maestros: eso es consultar el estado, no observar el comportamiento.

Uso:  python Zagentexecution/quality_checks/mining_capability_census.py [--json]
Salida: exit 0 limpio · exit 1 si hay mineros sin registrar
"""
QUALITY_CHECK = {
    "tier": "gate",
    "needs": "files",
    "what": ("scripts que leen datos de evento para descubrir como se trabaja y no estan "
             "registrados como algoritmo: capacidad de mineria que se pierde al cerrar"),
}
# ----------------------------------------------------------------------------
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALGOS = os.path.join(ROOT, "brain_v2", "methods", "algorithms.json")

# Tablas de EVENTO: guardan que PASO, con su momento y su actor.
#
# ⛔ NADA DE SUBCADENAS ANIDADAS. 'rsau_audit_history' contenia ademas 'rsau', y
# 'cdhdr_history' contenia 'cdhdr': una sola tabla mencionada puntuaba como DOS y anulaba el
# umbral anti-"de pasada". Medido: 3 de 23 candidatos pasaban solo por ese doble conteo. Se
# buscan con frontera de palabra y sin solapes.
EVENTO = ["rsau_audit_history", "cdhdr_history", "cdpos", "apqi", "apqd",
          "tbtco", "tbtcp", "edidc", "srt_monilog", "balhdr", "balm", "e070", "e071"]

# MINAR NO ES SOLO LEER EL LOG. La version anterior definia minar como "leer una tabla de
# EVENTO" y decia explicitamente que leer configuracion o maestros no cuenta. Eso contradice la
# taxonomia del propio registro, donde REALIDAD y CONFORMIDAD son tipos de mineria de pleno
# derecho: A33 (contenido de variantes) y A34 (clase de cuenta por estructura de balance) son
# mineros y NUNCA podrian aparecer en un censo que solo mira el log. Los dos se descubrieron a
# mano, que es exactamente lo que el censo existe para evitar.
ESTRUCTURA = ["vari", "varid", "tvarv", "fagl_011", "t011", "ska1", "skb1", "setleaf",
              "setnode", "tstc", "tadir", "tdevc", "df14l", "usr02", "agr_", "rfcdes",
              "t030h", "t030s", "fmderive", "t042"]
# Verbos de DESCUBRIMIENTO: no basta con leer el evento, hay que sacar un patron de el.
DESCUBRE = ["group by", "counter(", "defaultdict", "most_common", "discover", "descubr",
            "classif", "clasific", "pattern", "patron", "variant", "dfg", "conform",
            "distinct", "correlat", "agrupa"]

# Revisados y deliberadamente FUERA, con motivo. Una exclusion sin motivo es un hueco
# disfrazado, asi que el motivo es obligatorio para estar aqui.
FUERA = {
    "accumulate_logs.py": "es el grifo: trae el evento, no descubre patrones en el",
    "gold_refresh.py": "refresco de tablas, no observa comportamiento",
    "load_wide_tables.py": "carga",
    "p01_massive_extractor.py": "extraccion",
    "accumulate_problems.py": "acumulador",
    "build_p2p_log.py": "construye el log de eventos para que otros lo minen",
    "parse_syslog.py": "parser",
    "gold_ref.py": "helper de rutas",
    # CONSUMEN el grafo, no minan. Ingerir y consultar no es descubrir.
    "build_brain_state.py": "constructor del grafo: ingiere lo que los mineros produjeron",
    "graph_queries.py": "consulta el grafo, no lo descubre",
    "cli.py": "linea de comandos del brain",
    "rebuild_all.py": "orquestador del rebuild",
    "curate.py": "curacion estructural del grafo",
    "validate_artifacts.py": "validador de artefactos",
    "meta_capability.py": "mide nuestra propia madurez, no el sistema SAP",
}


def _kind_probable(texto, eventos):
    """Que TIPO de mineria parece hacer, para que la propuesta llegue medio rellena.

    Es una pista, no un veredicto: quien registre el algoritmo la confirma. Proponer un tipo
    ahorra trabajo; afirmarlo sin mirar el codigo seria inventar clasificacion.
    """
    t = texto
    if any(k in t for k in ("slguser", "terminal", "logon", "rfcdes", "destino", "canal")):
        return "CANAL_Y_ACTOR"
    if any(k in t for k in ("variant", "dfg", "secuencia", "transicion", "activity")):
        return "FLUJO_DE_CONTROL"
    if any(k in t for k in ("conform", "desviacion", "deviation", "estandar")):
        return "CONFORMIDAD"
    if "apqi" in eventos or "apqd" in eventos:
        return "CANAL_Y_ACTOR"
    if any(k in t for k in ("drift", "deriva", "tendencia", "por_mes")):
        return "DERIVA"
    if any(k in t for k in ("clasific", "classif", "es_objeto", "generado")):
        return "REALIDAD"
    return None


def _propuesta(c):
    """Borrador de alta -- Y ES SOLO EL ARRANQUE, NO EL ALTA.

    Dar de alta un minero no es rellenar `bound_in`: es reconstruir el PROCESO COMPLETO. Un
    script mecanizado se queda con la parte contable (agrupar, contar) y tira la interpretativa
    (que significa cada campo, que trampas tiene, que conclusion falsa permite), y la
    interpretativa ES el conocimiento. Medido dos veces el 2026-08-25: al mecanizar el metodo
    que encontro ALLOS se perdio el discriminador de canal a cuatro vias, la derivacion
    programa->transaccion por TSTC y la vuelta por rsau; y la primera version del minero de
    variantes volcaba pares campo/valor sin las tres clases de parametro, que es donde esta
    todo el criterio.

    Por eso esto emite el ESQUELETO y nombra quien lo completa: el agente `miner-onboarding`,
    que lee el script y TODO lo que lo rodea -- agentes, skills, docs de dominio, el
    learning_summary de la tarea donde nacio, los claims que lo citan, el commit que lo creo --
    lo corre si es seguro, y devuelve las cuatro capas. Los campos van marcados COMPLETAR a
    proposito: rellenarlos automaticamente seria inventarlos.
    """
    base = os.path.basename(c["script"])[:-3]
    return {
        "id": f"A??_{base}",
        "operates_on": ", ".join(c["tablas_de_evento"]),
        "origin": "OURS",
        "state": "REVISAR",
        "mining_kind": c.get("mining_kind_probable"),
        "does": "COMPLETAR: que DESCUBRE, en una frase que sirva a quien no lo escribio",
        "bound_in": [c["script"]],
        "failure_mode": ("COMPLETAR -- ES EL CAMPO QUE IMPORTA. Como puede este algoritmo dar "
                         "una respuesta VEROSIMIL Y FALSA? Si no lo sabes, CORRELO y averigualo. "
                         "Un modo de fallo inventado es peor que ninguno: parece pensado"),
        "lands_in": "COMPLETAR: en que store aterriza, o 'n/a - tecnica'",
        "_metodo": {
            "LEER": "COMPLETAR: que tabla, con que FM o SQL, con que limite conocido",
            "INTERPRETAR": ("COMPLETAR: que significa cada campo y en que CLASES se reparten "
                            "los valores. ESTA es la capa que se pierde al mecanizar"),
            "AGRUPAR": "COMPLETAR: por forma de trabajar, no por identificador",
            "CONTEXTO": "COMPLETAR: donde se uso de verdad -- cuantas veces, cuando, quien",
        },
        "_quien_lo_completa": ("el agente `miner-onboarding` (.claude/agents/). Reconstruye las "
                               "cuatro capas leyendo el script y sus fuentes de metodo, y lo "
                               "corre si es seguro"),
    }


def main():
    try:
        algos = json.load(open(ALGOS, encoding="utf-8")).get("algorithms") or {}
    except Exception:
        algos = {}
    registrados = set()
    for a in algos.values():
        for b in (a.get("bound_in") or []):
            registrados.add(os.path.basename(str(b)).lower())

    # Rutas que NO son capacidad viva. Sin este filtro el censo daba 55 candidatos e incluia un
    # lexer de pygments dentro de un venv, carpetas archivadas y su propio codigo: un gate que
    # grita en falso deja de leerse, y lo que se pierde con el son los hallazgos de verdad.
    MUERTAS = ("__pycache__", os.sep + "venv" + os.sep, "site-packages",
               os.sep + "_obsolete" + os.sep, os.sep + "_applied" + os.sep,
               os.sep + "tasks" + os.sep, os.sep + "incidents" + os.sep,
               os.sep + "node_modules" + os.sep, os.sep + ".git" + os.sep,
               # El servidor MCP NUNCA se ha conectado -- no corrio una sola vez -- y ademas
               # guarda 68 escritores de SAP sin ninguna puerta, la clase de herramienta que
               # causo INC-CLASS-LOSS. Lo que hay ahi no es capacidad viva: es un archivo que
               # no queremos resucitar por la puerta de atras de un censo de mineria.
               os.sep + "mcp-backend-server-python" + os.sep)
    YO = os.path.abspath(__file__)

    candidatos, revisados = [], 0

    # ---- LOS AGENTES TAMBIEN. Un metodo que vive en un PROMPT era estructuralmente
    # invisible para este censo, y ESE ES SU CASO FUNDACIONAL: el metodo que encontro ALLOS
    # vivio como prompt sin algoritmo. Barrer solo *.py permitia imprimir "todo lo que mina
    # esta registrado" con doce agentes sin mirar.
    for p in glob.glob(os.path.join(ROOT, ".claude", "agents", "*.md")):
        nom = os.path.basename(p)
        try:
            t = open(p, encoding="utf-8", errors="ignore").read().lower()
        except Exception:
            continue
        ev = [e for e in EVENTO + ESTRUCTURA
              if re.search(r"\b" + re.escape(e) + r"\b", t)]
        if len(set(ev)) < 2:
            continue
        if nom[:-3].lower() in registrados or nom[:-3].lower() in \
                json.dumps(algos, ensure_ascii=False).lower():
            continue
        candidatos.append({
            "script": os.path.relpath(p, ROOT).replace(os.sep, "/"),
            "tablas_de_evento": sorted(set(ev))[:4],
            "senales_de_descubrimiento": ["metodo descrito en un PROMPT de agente"],
            "lineas": t.count("\n"),
            "mining_kind_probable": _kind_probable(t, ev),
            "_por_que_grave": ("un metodo que solo vive en un prompt no se repite, no se "
                               "programa, no se gatea y no se compara con la corrida anterior")})

    for pat in ("process_mining/**/*.py", "brain_v2/**/*.py", "scripts/**/*.py",
                "Zagentexecution/**/*.py"):
        for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
            nom = os.path.basename(p)
            if nom in FUERA or any(m in p for m in MUERTAS) or os.path.abspath(p) == YO:
                continue
            revisados += 1
            try:
                t = open(p, encoding="utf-8", errors="ignore").read().lower()
            except Exception:
                continue
            # Frontera de palabra. Y las de ESTRUCTURA cuentan, pero NO igual: clasificar
            # cuentas por su nodo de balance o leer el contenido de una variante es minar, y
            # mencionar `usr02` de pasada no lo es. Se exige UNA de evento, o DOS de estructura.
            ev_e = {e for e in EVENTO if re.search(r"\b" + re.escape(e) + r"\b", t)}
            ev_s = {e for e in ESTRUCTURA if re.search(r"\b" + re.escape(e) + r"\b", t)}
            if not ev_e and len(ev_s) < 2:
                continue
            ev = sorted(ev_e | ev_s)
            desc = [v for v in DESCUBRE if v in t]
            if not desc:
                continue                 # lee el evento pero no saca patron: no es minero
            if nom.lower() in registrados:
                continue
            # Leer una tabla de evento de pasada no es minar. Se pide o VARIAS tablas de evento,
            # o varias senales de descubrimiento sobre una: la diferencia entre un script que
            # menciona cdhdr y uno que lo agrupa por actor para ver quien cambia que.
            if len(set(ev)) < 2 and len(set(desc)) < 3:
                continue
            candidatos.append({
                "script": os.path.relpath(p, ROOT).replace(os.sep, "/"),
                "tablas_de_evento": sorted(set(ev))[:4],
                "senales_de_descubrimiento": sorted(set(desc))[:4],
                "lineas": t.count("\n"),
                "mining_kind_probable": _kind_probable(t, ev),
            })

    candidatos.sort(key=lambda c: -len(c["tablas_de_evento"]) * 100 - c["lineas"])
    rep = {
        "_que_comprueba": ("scripts que leen datos de EVENTO y sacan patrones de ellos sin estar "
                           "registrados como algoritmo"),
        "_por_que": ("una capacidad de mineria sin registrar no se puede repetir, ni programar, "
                     "ni gatear, ni comparar con la corrida anterior. El metodo que encontro "
                     "ALLOS vivio un dia solo como prompt de un agente"),
        "_no_es_una_sentencia": ("algunos seran helpers de un algoritmo ya registrado. Lo que se "
                                 "pide es MIRARLOS, y que el que se quede fuera lo haga con "
                                 "motivo escrito en FUERA, no por silencio"),
        "scripts_revisados": revisados,
        "algoritmos_registrados": len(algos),
        "mineros_sin_registrar": candidatos,
    }
    if "--proponer" in sys.argv:
        # LA MECANIZACION DEL ALTA: emite el borrador de cada minero para que pase al grupo de
        # mineria y lo pueda usar todo el mundo. Deja el failure_mode a COMPLETAR a proposito.
        prop = {"_que_es": ("borradores de alta para los mineros sin registrar. Completa `does`, "
                            "`failure_mode` y `lands_in` y pegalos en algorithms.json"),
                "_regla": ("el failure_mode no se inventa: se averigua CORRIENDO el algoritmo. "
                           "Un modo de fallo fabricado es peor que ninguno porque parece pensado"),
                "propuestas": [_propuesta(c) for c in candidatos]}
        salida = os.path.join(ROOT, "brain_v2", "methods", "mining_candidates.json")
        with open(salida, "w", encoding="utf-8") as fh:
            json.dump(prop, fh, indent=2, ensure_ascii=False)
        print(f"{len(candidatos)} borrador(es) -> {salida}")
        return 1 if candidatos else 0

    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if candidatos else 0

    print(f"[censo de mineria] {revisados} scripts revisados · {len(algos)} algoritmos "
          f"registrados")
    if not candidatos:
        print("  OK - todo lo que mina esta registrado")
        return 0
    print(f"  {len(candidatos)} script(s) leen EVENTOS y sacan patrones sin estar registrados:\n")
    for c in candidatos:
        print(f"  {c['script']}")
        print(f"      eventos: {', '.join(c['tablas_de_evento'])}")
        print(f"      descubre: {', '.join(c['senales_de_descubrimiento'])}  "
              f"({c['lineas']} lineas)")
    print("\n  Cada uno: o se registra como algoritmo con su PROCESO COMPLETO -- las cuatro")
    print("  capas: leer, interpretar, agrupar y donde se uso -- o entra en FUERA con el motivo.")
    print("  El alta NO es rellenar bound_in: mecanizar solo la parte contable mata el criterio,")
    print("  que es lo unico que no se puede volver a derivar.")
    print("\n  python Zagentexecution/quality_checks/mining_capability_census.py --proponer")
    print("  y luego el agente `miner-onboarding` completa cada borrador leyendo sus fuentes.")
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
