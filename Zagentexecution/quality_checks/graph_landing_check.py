"""GATE: un store que no llega al GRAFO es un JSON al lado, no conocimiento.

QUE CONTROLA, Y POR QUE NO LO CUBRIA NINGUNO DE LOS OTROS
    Ya habia tres puertas y cada una mira otra cosa:
      artifact_wiring_check      -- quien INVOCA el artefacto
      artifact_reachability_check-- se llega a el desde el indice de entrada
      knowledge_connectivity_check-- el conocimiento esta en el campo que su store lee
    Ninguna preguntaba lo unico que hace que el process mining pueda ACTUAR: si lo que el store
    sabe esta en `brain_state.objects`, o sea si se puede RECORRER.

    Medido 2026-08-25: interface_inventory.json tenia 656 interfaces con dominio, naturaleza y
    marca de segregacion de funciones, y build_brain_state.py ni lo abria. MULESOFT, UBO-RFC y
    MP_ANCUTA estaban en el grafo como NOMBRES sueltos -- los sintetizaba algun claim -- pero
    sin nada de lo que se sabia de ellos. Preguntarle al grafo "quien escribe datos maestros en
    este dominio" devolvia vacio teniendo la respuesta a un fichero de distancia. Las tres
    puertas anteriores daban verde.

LAS TRES COMPROBACIONES
    1. STORE -> GRAFO   cada JSON que un algoritmo declara en `lands_in` deja rastro en
                        brain_state: o lo ingiere build_brain_state.py, o sus nombres estan
                        en objects[]
    2. ALGORITMO VIVO   todo algoritmo registrado tiene su script invocado por alguien
                        (delega el detalle en artifact_wiring_check: aqui solo se cuenta)
    3. AGENTE COORDINADO cada agente nombra al menos una herramienta que ejecuta y un sitio
                        donde deja lo que descubre. Un agente que no llama a nada ni deja nada
                        es una forma de explorar que muere con la conversacion

Uso:  python Zagentexecution/quality_checks/graph_landing_check.py [--json]
Salida: exit 0 limpio · exit 1 si hay conocimiento que no llega al grafo
"""
QUALITY_CHECK = {
    "tier": "gate",      # gate | live | analysis | quarantined
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": ("stores que no llegan a brain_state (JSON al lado del grafo), algoritmos sin "
             "llamador y agentes que no ejecutan ni depositan nada"),
}
# ----------------------------------------------------------------------------
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRAIN = os.path.join(ROOT, "brain_v2")
STATE = os.path.join(BRAIN, "brain_state.json")
ALGOS = os.path.join(BRAIN, "methods", "algorithms.json")
BUILDER = os.path.join(BRAIN, "build_brain_state.py")
AGENTS = os.path.join(ROOT, ".claude", "agents")

# Stores que por diseno NO van al grafo, con el motivo. Una exclusion sin motivo es un hueco
# disfrazado, asi que el motivo es obligatorio para estar aqui.
FUERA = {
    "algorithms.json": "es el registro de METODO; su sitio es methods, no objects[]",
    "algorithm_memory.json": "memoria de metodo: habla de como exploramos, no del sistema",
    "feedback_rules.json": "es la capa 3 del brain, ya entra por su propio camino",
    "claims.json": "entra como capa 4 y ademas sintetiza objetos",
    "incidents.json": "entra como capa 11",
    "capability_model.json": "entra como capa 15",
    "quality_checks_state.json": "estado de las puertas, no conocimiento del sistema",
    "cycle_state.json": "estado del ciclo",
    "trigger_state.json": "estado de disparadores",
    "discovery_delta.json": ("es el PARTE de una corrida -- que encontro la cadena que el brain "
                             "aun no sabia -- y se reescribe entera en la siguiente. Lo que de "
                             "ese parte merezca quedarse se promueve a claim; el parte no"),
}


def load(p, d=None):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return d if d is not None else {}


def nombres_de(obj, tope=400):
    """Nombres que un store dice conocer -- claves de primer nivel y campos que nombran algo."""
    out = set()
    def add(v):
        if isinstance(v, str) and 2 < len(v) < 40:
            out.add(v.strip().upper())
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            add(k)
            if isinstance(v, dict):
                for kk in list(v)[:tope]:
                    add(kk)
            elif isinstance(v, list):
                for it in v[:tope]:
                    if isinstance(it, dict):
                        for f in ("artifact", "object", "name", "table", "tcode", "program",
                                  "actor", "user", "id"):
                            add(it.get(f))
                    else:
                        add(it)
    elif isinstance(obj, list):
        for it in obj[:tope]:
            if isinstance(it, dict):
                for f in ("artifact", "object", "name", "id"):
                    add(it.get(f))
    return {n for n in out if n}


def main():
    algos = (load(ALGOS).get("algorithms") or {})
    state = load(STATE)
    objetos = {str(k).upper() for k in (state.get("objects") or {})}
    try:
        builder = open(BUILDER, encoding="utf-8").read()
    except Exception:
        builder = ""
    try:
        consultas = open(os.path.join(BRAIN, "graph_queries.py"), encoding="utf-8").read()
    except Exception:
        consultas = ""

    h = []

    # ---- 1. STORE -> GRAFO -------------------------------------------------
    stores = {}
    for aid, a in algos.items():
        li = a.get("lands_in")
        for m in re.findall(r"[\w/\\.-]+\.json", str(li or "")):
            stores.setdefault(os.path.basename(m), set()).add(aid)

    for fichero, duenos in sorted(stores.items()):
        if fichero in FUERA:
            continue
        ruta = None
        for base in ("brain_v2", "process_mining", "Zagentexecution", "companions"):
            for p in glob.glob(os.path.join(ROOT, base, "**", fichero), recursive=True):
                ruta = p
                break
            if ruta:
                break
        if not ruta:
            continue                      # que exista lo vigila artifact_reachability_check
        # TRES caminos valen, porque los tres dejan RECORRER el conocimiento:
        #   a) build_brain_state lo ingiere -> vive dentro de objects[]
        #   b) graph_queries tiene un comando que lo sirve -> se recorre por su propia puerta
        #      (code_inventory.json es asi: `graph_queries.py code <nombre>`)
        #   c) sus nombres ya estan en objects[] por otra via
        # Exigir solo (a) habria marcado en rojo stores perfectamente alcanzables, y un gate que
        # grita en falso deja de leerse -- que es la leccion escrita en el failure_mode de A25.
        ingerido = fichero in builder
        servido = fichero in consultas
        nombres = nombres_de(load(ruta))
        if not nombres:
            continue
        dentro = len(nombres & objetos)
        cobertura = 100.0 * dentro / len(nombres)
        if not (ingerido or servido) and cobertura < 25:
            h.append({
                "gravedad": "NO_LLEGA_AL_GRAFO", "store": fichero,
                "algoritmos": sorted(duenos),
                "que_pasa": (f"ni build_brain_state.py lo abre, ni graph_queries.py tiene un "
                             f"comando que lo sirva, y solo {dentro} de {len(nombres)} nombres "
                             f"suyos ({cobertura:.0f}%) estan en objects[]. Es un JSON al lado "
                             f"del grafo: no se puede recorrer, asi que nada razona con el")})

    # ---- 2. ALGORITMOS MUERTOS --------------------------------------------
    # El detalle (quien invoca que) lo da artifact_wiring_check. Aqui solo se cuenta, para que
    # el numero aparezca junto a los otros dos y no haya que acordarse de correr la otra puerta.
    # Se guarda POR FICHERO, no concatenado. Contar apariciones sobre un pegote asumia que el
    # propio script estaba dentro y exigia count>1; sap_process_discovery.py vive en
    # Zagentexecution/sap_data_extraction/, que no se barre, asi que aparecia UNA vez -- en la
    # cadena que si lo llama -- y salia muerto teniendo llamador. Lo correcto no es contar: es
    # preguntar si lo nombra ALGUIEN QUE NO SEA EL MISMO.
    fuentes_por_fichero = {}
    for pat in ("brain_v2/**/*.py", "scripts/**/*.py", "process_mining/**/*.py",
                "Zagentexecution/**/*.py", ".claude/agents/*.md"):
        for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
            try:
                fuentes_por_fichero[os.path.abspath(p)] = open(
                    p, encoding="utf-8", errors="ignore").read()
            except Exception:
                pass
    muertos = []
    for aid, a in algos.items():
        binds = a.get("bound_in") or []
        if not binds:
            continue
        vivo = False
        for b in binds:
            nom = os.path.basename(str(b))
            # Un modulo se invoca por su NOMBRE DE FICHERO cuando lo ejecutas, pero por su
            # NOMBRE DE MODULO cuando lo importas: `from mining_bus import publicar` no contiene
            # la cadena "mining_bus.py". Buscando solo el fichero, un modulo bien usado sale
            # muerto -- tercera vez que esta misma puerta confunde la forma con el efecto.
            mod = nom[:-3] if nom.endswith(".py") else nom
            propio = os.path.abspath(os.path.join(ROOT, str(b).replace("/", os.sep)))
            if any(nom in t or f" {mod} import" in t or f"import {mod}" in t
                   for f, t in fuentes_por_fichero.items() if f != propio):
                vivo = True
                break
            # ...o si vive en un directorio que un runner recorre por GLOB. Las puertas de
            # quality_checks las descubre run_all.py sin nombrarlas una a una, asi que exigir
            # una mencion literal las marcaba a todas como muertas estando todas vivas. Un gate
            # que grita en falso deja de leerse, y este casi empieza gritando en falso de si
            # mismo: A26 salio en su propia lista de muertos.
            if os.sep + "quality_checks" + os.sep in str(b).replace("/", os.sep):
                vivo = True
                break
        if not vivo:
            muertos.append(aid)
    # UN ALGORITMO ROTO **DEBE** NO TENER LLAMADOR: enchufarlo seria el error, no el arreglo.
    #
    # A41_extract_fund_center_hierarchy es codigo que NUNCA ha corrido -- muere en un NameError
    # antes del primer RFC, y su manifiesto en el Gold esta vacio, lo que lo confirma. Que nadie
    # lo llame es lo correcto. Pero esto NO es una exclusion silenciosa: sigue apareciendo, con
    # su estado y su motivo, porque un roto que se calla se queda roto para siempre. La unica
    # diferencia es que no rompe la puerta.
    rotos = [x for x in muertos if str(algos.get(x, {}).get("state", "")).upper()
             in ("ROTO", "MUERTO", "QUARANTINED")]
    muertos = [x for x in muertos if x not in rotos]
    if rotos:
        h.append({"gravedad": "AVISO_ALGORITMO_ROTO", "store": "algorithms.json",
                  "algoritmos": sorted(rotos),
                  "que_pasa": (f"{len(rotos)} algoritmo(s) declarados ROTOS y sin llamador. Eso "
                               "es COHERENTE -- enchufar codigo que no corre seria el error -- "
                               "pero siguen contados: arreglarlos o retirarlos con motivo. No "
                               "rompen la puerta")})
    if muertos:
        h.append({"gravedad": "ALGORITMO_SIN_LLAMADOR", "store": "algorithms.json",
                  "algoritmos": sorted(muertos)[:12],
                  "que_pasa": (f"{len(muertos)} algoritmo(s) registrados cuyo script no nombra "
                               "nadie mas: no se ejecutan solos, asi que no son capacidad. "
                               "Detalle en artifact_wiring_check.py")})

    # ---- 3. AGENTES AISLADOS ----------------------------------------------
    solos = []
    for p in sorted(glob.glob(os.path.join(AGENTS, "*.md"))):
        try:
            t = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        nombre = os.path.basename(p)[:-3]
        ejecuta = bool(re.search(r"\.py\b|graph_queries|load_domain|rebuild_all", t))
        deposita = bool(re.search(r"claims\.json|incidents\.json|\.json`|knowledge/|"
                                  r"brain_v2/|companions/", t))
        # Encadenar con otro agente cuenta tanto como ejecutar una herramienta: hay agentes que
        # LEEN -- authority-doc-reader convierte PDFs en hechos -- y no corren ningun script.
        # Exigirles un .py los marcaba de aislados estando perfectamente coordinados. Lo que de
        # verdad no puede faltar es DEPOSITAR: un agente que no dice donde deja lo que encuentra
        # explora bien una vez y no deja nada.
        otros = [os.path.basename(q)[:-3] for q in glob.glob(os.path.join(AGENTS, "*.md"))]
        encadena = any(o != nombre and o in t for o in otros)
        if not (deposita and (ejecuta or encadena)):
            solos.append({"agente": nombre, "ejecuta_algo": ejecuta,
                          "encadena_con_otro_agente": encadena, "deja_algo": deposita})
    if solos:
        h.append({"gravedad": "AGENTE_AISLADO", "store": ".claude/agents",
                  "algoritmos": [s["agente"] for s in solos],
                  "detalle": solos,
                  "que_pasa": ("agente(s) que no nombran ninguna herramienta que ejecutar o "
                               "ningun sitio donde dejar lo que descubren: su forma de explorar "
                               "muere con la conversacion")})

    rep = {"_que_comprueba": ("que el conocimiento generado llegue al GRAFO, que los algoritmos "
                              "tengan quien los llame, y que los agentes ejecuten y depositen"),
           "_por_que": ("interface_inventory.json tenia 656 interfaces con dominio y naturaleza "
                        "y build_brain_state.py ni lo abria: las otras tres puertas daban verde"),
           "stores_vigilados": len([s for s in stores if s not in FUERA]),
           "objetos_en_el_grafo": len(objetos),
           "hallazgos": h}

    # UN AVISO_ SE CUENTA Y SE IMPRIME, PERO NO ROMPE LA PUERTA.
    #
    # Son situaciones COHERENTES que hay que seguir viendo: un algoritmo declarado ROTO y sin
    # llamador lo es -- enchufar codigo que no corre seria el error, no el arreglo. Si un aviso
    # rompiera, la unica forma de dejar la puerta en verde seria dejar de declarar el estado, y
    # asi es como se hueca un gate: no quitandolo, sino haciendo que mienta el que lo rellena.
    rompen = [x for x in h if not str(x.get("gravedad", "")).startswith("AVISO_")]

    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if rompen else 0

    print(f"[grafo] {rep['stores_vigilados']} stores vigilados · "
          f"{len(objetos):,} objetos en el grafo")
    if not rompen:
        print("  OK - lo generado llega al grafo, los algoritmos tienen llamador, "
              "los agentes ejecutan y depositan" +
              (f"  ({len(h)} aviso(s), no rompen)" if h else ""))
    for x in h:
        print(f"  [{x['gravedad']}] {x['store']}")
        print(f"      {x['que_pasa']}")
        if x.get("algoritmos"):
            print(f"      -> {', '.join(x['algoritmos'])}")
    return 1 if rompen else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
