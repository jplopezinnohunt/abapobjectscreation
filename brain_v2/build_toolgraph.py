"""EL BRAIN DEL BRAIN — un grafo de mis PROPIOS instrumentos, no seis listas que no se conocen.

POR QUE EXISTE
    Hay un brain de la DATA (objetos SAP, claims, incidentes, dominios) y no habia ninguno de
    las HERRAMIENTAS con las que se construye. Estaban en seis sitios que no se hablan:

        .claude/skills/*/SKILL.md      48 skills, cientos de KB de metodo curado
        .claude/agents/*.md            13 agentes
        brain_v2/methods/algorithms.json   75 algoritmos
        brain_v2/methods/algorithm_memory.json  156 memorias de metodo
        Zagentexecution/quality_checks/*.py     las puertas
        brain_v2/*.json                los stores que todo eso produce

    Cada una es una lista. Ninguna dice QUIEN USA A QUIEN. Y eso no es estetico: medido el
    2026-08-26, 40 de 48 skills NO TIENEN NI UN LECTOR -- `sap_payment_bcm_agent` son 106 KB de
    metodo de banca con CERO lectores y 16 artefactos trabajando sobre sus mismas tablas. El
    caso que lo destapo: `config_transport_prerelease_check` se escribio y se arreglo DOS VECES
    sin abrir `sap_transport_intelligence`, que documenta que OBJFUNC=M borra la tabla ENTERA
    en destino y que E071K vacio tambien significa ROL.

    El operador lo nombro: «tiene que haber un grafo de tus propias herramientas, un gestor de
    ellas. Asi como tienes un brain de la data, tienes que tener un brain del brain».

QUE ES, Y QUE NO ES
    NO duplica los stores: cada uno sigue siendo la fuente de su tipo de nodo. Esto construye
    las ARISTAS, que es lo que no existia en ningun sitio, y las mide.

    NODOS      SKILL · AGENTE · ALGORITMO · MINERO · GATE · STORE · MEMORIA · CLASE_MINERIA
               MINERO se separa de ALGORITMO porque EXPLORAR no es CALCULAR: un minero
               descubre lo que no sabias que existia. Sin la distincion, "¿que parte del
               paisaje no ha mirado nadie?" no es una pregunta que el grafo pueda contestar.
    ARISTAS    LEE            agente/algoritmo -> skill  (existe)
               DEBERIA_LEER   opera sobre sus tablas y no lo nombra  (LA QUE FALTA)
               ATERRIZA_EN    algoritmo -> store
               VIGILA         gate -> store
               RECUERDA       memoria -> algoritmo
               INVOCA         cualquiera -> el script de otro
               DELEGA         agente -> AGENTE que nombra en su prompt (la colaboracion)
               DESCUBRE       minero -> clase de mineria que cubre

Uso:  python brain_v2/build_toolgraph.py [--json]
Aterriza en: brain_v2/toolgraph.json  ·  drill: graph_queries.py tool <nombre>
"""
import ast
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(ROOT, "brain_v2", "toolgraph.json")
REG_SKILLS = os.path.join(ROOT, "brain_v2", "skills", "skill_registry.json")
ALGOS = os.path.join(ROOT, "brain_v2", "methods", "algorithms.json")
MEM = os.path.join(ROOT, "brain_v2", "methods", "algorithm_memory.json")
AGENTS = os.path.join(ROOT, ".claude", "agents")
GATES = os.path.join(ROOT, "Zagentexecution", "quality_checks")


def cargar(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d if d is not None else {}


def main():
    nodos, aristas = {}, []

    def nodo(tipo, nombre, **kw):
        nodos[nombre] = dict({"tipo": tipo, "nombre": nombre}, **kw)

    def arista(origen, rel, destino, **kw):
        aristas.append(dict({"de": origen, "rel": rel, "a": destino}, **kw))

    # ---- SKILLS + las aristas que el registro ya midio -------------------------------
    reg = cargar(REG_SKILLS)
    for s, r in (reg.get("por_skill") or {}).items():
        nodo("SKILL", s, bytes=r.get("bytes"), fichero=r.get("fichero"),
             de_que_habla=r.get("de_que_habla"), cubre_tablas=len(r.get("cubre_tablas") or []))
        for tipo in ("agentes", "algoritmos"):
            for q in (r.get("leido_por") or {}).get(tipo, []):
                arista(q, "LEE", s)
        for d in (r.get("deberia_leerlo") or []):
            arista(d["quien"], "DEBERIA_LEER", s, tablas_en_comun=d.get("tablas_en_comun"),
                   n=d.get("n"))

    # ---- ALGORITMOS ------------------------------------------------------------------
    A = (cargar(ALGOS).get("algorithms") or {})
    for k, v in A.items():
        nodo("ALGORITMO", k, state=v.get("state"), mining_kind=v.get("mining_kind"),
             bound_in=v.get("bound_in"), lands_in=v.get("lands_in"),
             tiene_defecto_vivo=bool(v.get("_defecto_vivo")))
        for m in re.findall(r"[\w/\\.-]+\.json", str(v.get("lands_in") or "")):
            store = os.path.basename(m)
            nodos.setdefault(store, {"tipo": "STORE", "nombre": store})
            arista(k, "ATERRIZA_EN", store)

    # ---- MINEROS: explorar NO es calcular ---------------------------------------------
    # Un MINERO descubre lo que no sabias que existia; un ALGORITMO contesta lo que ya sabes
    # preguntar. Colapsados en un solo tipo, la pregunta "¿que parte del paisaje no ha mirado
    # nadie?" no se puede hacer -- y por eso "comparar tablas entre sistemas" no estaba
    # registrado como nada. Se distinguen por `tipo_mineria`/`mining_kind`, que ya viven en
    # algorithms.json y hasta ahora solo eran una etiqueta que nadie leia.
    for k, v in A.items():
        tm = v.get("tipo_mineria") or v.get("mining_kind")
        tm = [tm] if isinstance(tm, str) else (tm or [])
        if not tm:
            continue
        nodos[k]["tipo"] = "MINERO"
        nodos[k]["mina"] = tm
        nodos[k]["generaliza"] = bool(v.get("generaliza"))
        for t in tm:
            clase = "clase:" + t
            nodos.setdefault(clase, {"tipo": "CLASE_MINERIA", "nombre": clase})
            arista(k, "DESCUBRE", clase)

    # ---- AGENTES ---------------------------------------------------------------------
    for f in sorted(os.listdir(AGENTS)) if os.path.isdir(AGENTS) else []:
        if not f.endswith(".md"):
            continue
        t = open(os.path.join(AGENTS, f), encoding="utf-8", errors="ignore").read()
        nodo("AGENTE", f[:-3], bytes=len(t))
        # que instrumentos INVOCA: scripts nombrados en su prompt
        for m in set(re.findall(r"([\w/\\.-]+\.py)", t)):
            base = os.path.basename(m)
            for k, v in A.items():
                if any(base in str(b) for b in (v.get("bound_in") or [])):
                    arista(f[:-3], "INVOCA", k, via=base)

    # ---- DELEGA: la colaboracion entre agentes ---------------------------------------
    # Hasta 2026-08-26 el grafo publicaba 10 aristas AGENTE->AGENTE y las 10 eran BUCLES: un
    # agente recordando su propia leccion. La colaboracion no era escasa, era CERO.
    #
    # s107 — Y LA CORRECCION SIGUIENTE: NOMBRAR NO ES ENTREGAR. La version anterior daba por
    # hecho que "un agente que NOMBRA a otro le esta pasando trabajo". Medido sobre las 26
    # aristas: la mayoria SI son entregas -- casi todos los agentes usan la misma convencion,
    # una tabla `| agente | cuando le pasas el trabajo |` -- pero DOS son menciones de estilo.
    # `bank-process-discovery -> process-guardian` sale de "No anades ceremonia. Preferencia
    # fija, como el process-guardian"; e `incident-analyst -> bcm-signatory-panel`, de una
    # frase narrativa sobre lo que ese agente no sabia. Contarlas igual infla la unica cifra
    # que dice si colaboramos -- el mismo defecto que el `LEE`, que cuenta una CITA como una
    # lectura. Aqui la arista se sigue creando (no se pierde la senal) pero LLEVA SU EVIDENCIA
    # y queda clasificada, para que `salud` pueda publicar las dos cifras y no solo la alegre.
    _ag = [n for n, v in nodos.items() if v["tipo"] == "AGENTE"]
    for f in sorted(os.listdir(AGENTS)) if os.path.isdir(AGENTS) else []:
        if not f.endswith(".md"):
            continue
        yo = f[:-3]
        lineas = open(os.path.join(AGENTS, f), encoding="utf-8", errors="ignore").read().split("\n")
        for otro in _ag:
            if otro == yo:
                continue
            hits = [l for l in lineas if re.search(r"\b%s\b" % re.escape(otro), l)]
            if not hits:
                continue
            # una ENTREGA se declara: fila de tabla `| agente | cuando |`, o vineta con
            # disparador ("si ...", "cuando ...", "->", "para ..."). Lo demas es MENCION.
            entrega = any(l.strip().startswith("|") and l.count("|") >= 3 for l in hits) or \
                      any(re.search(r"^\s*[-*].*\b(si|cuando|para|→|->)\b", l, re.I) for l in hits)
            arista(yo, "DELEGA", otro,
                   entrega=bool(entrega),
                   evidencia=next((l.strip()[:160] for l in hits
                                   if l.strip().startswith("|")), hits[0].strip()[:160]))

    # ---- GATES -----------------------------------------------------------------------
    for f in sorted(os.listdir(GATES)) if os.path.isdir(GATES) else []:
        if not f.endswith(".py") or f.startswith("_"):
            continue
        t = open(os.path.join(GATES, f), encoding="utf-8", errors="ignore").read()
        if "QUALITY_CHECK" not in t:
            continue
        tier = (re.search(r'"tier":\s*"(\w+)"', t) or [None, "?"])[1]
        nodo("GATE", f[:-3], tier=tier)
        for m in set(re.findall(r"([\w-]+\.json)", t)):
            if m in nodos:
                arista(f[:-3], "VIGILA", m)

    # ---- HELPERS (H142, s107) --------------------------------------------------------
    # EL AGUJERO QUE ESTE BLOQUE TAPA. El toolgraph medía si se LEEN los skills. Un helper no
    # es un skill: no aparecía como nodo, luego no podía tener lector, luego que se ignorara
    # era invisible. Y la diferencia importa mas de lo que parece: un skill no leido es
    # conocimiento que no se aplica; un HELPER no usado es una FUNCION QUE YA RESUELVE EL
    # PROBLEMA y que alguien reescribe peor. El segundo produce hallazgos FALSOS.
    # El caso: `brain_v2/canonical.py` se escribio en s097 porque el mismo defecto aparecio
    # TRES veces en tres ficheros. Su docstring dice "Import it; do not re-derive it". En s106
    # el agente resolvio alias a mano tres veces mas y publico dos hallazgos falsos. Escribir
    # el helper no basto; documentarlo no basto; nada MEDIA que se ignoraba.
    #
    # Se DERIVA lo derivable y se DECLARA solo lo que no: el nodo y `USA` salen de los
    # imports reales (2+ importadores = helper compartido, no un script suelto); la arista
    # DEBERIA_USAR necesita saber QUE PROBLEMA resuelve, y eso lo declara el propio modulo en
    # un dict `HELPER` -- misma convencion que `QUALITY_CHECK` en las puertas.
    DIRS_HELPER = [os.path.join(ROOT, d) for d in ("brain_v2", "scripts", "process_mining")]
    fuentes = []          # (ruta_rel, texto)
    for d in (os.path.join(ROOT, x) for x in
              ("brain_v2", "scripts", "process_mining", "Zagentexecution/quality_checks")):
        for raiz, subs, fs in os.walk(d):
            subs[:] = [s for s in subs if s != "__pycache__"]
            for f in fs:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(raiz, f)
                try:
                    fuentes.append((os.path.relpath(p, ROOT).replace("\\", "/"),
                                    open(p, encoding="utf-8", errors="ignore").read()))
                except OSError:
                    pass

    # ⛔ RECURSIVO, Y ESTO ES UN ARREGLO DEL MISMO DIA. La primera version listaba con
    # `os.listdir` NO recursivo, asi que `brain_v2/methods/algorithm_memory.py` -- la API del
    # store de memoria de metodo, con 4+ importadores -- NO PODIA SER NODO HELPER JAMAS, ni
    # nada bajo `scripts/extraction/`. El censo de "10 helpers" era un SUELO presentado como
    # total: DENOMINADOR INCOMPLETO, el modo de fallo numero uno de braintoolbox, cometido en
    # la herramienta escrita ese mismo dia para medir denominadores. Lo encontro un agente
    # leyendo este codigo, no yo corriendolo.
    candidatos = {}
    for d in DIRS_HELPER:
        for raiz, subs, fs in os.walk(d) if os.path.isdir(d) else []:
            subs[:] = [x for x in subs if x != "__pycache__"]
            for f in sorted(fs):
                if f.endswith(".py") and not f.startswith("_"):
                    rel = os.path.relpath(os.path.join(raiz, f), ROOT).replace("\\", "/")
                    candidatos.setdefault(f[:-3], rel)

    for mod, ruta in candidatos.items():
        pat = re.compile(r"^\s*(?:from|import)\s+.*\b%s\b" % re.escape(mod), re.M)
        usan = [r for r, t in fuentes if r != ruta and pat.search(t)]
        if len(usan) < 2:                      # 0 o 1 importador: no es un helper compartido
            continue
        propio = next((t for r, t in fuentes if r == ruta), "")
        decl = re.search(r"^HELPER\s*=\s*(\{.*?\n\})", propio, re.S | re.M)
        ficha = {}
        if decl:
            try:
                ficha = ast.literal_eval(decl.group(1))
            except (ValueError, SyntaxError):
                ficha = {}
        nodo("HELPER", "helper:" + mod, fichero=ruta, usuarios=len(usan),
             resuelve=ficha.get("resuelve"), declarado=bool(ficha))
        for r in usan:
            arista(r, "USA", "helper:" + mod)
        # DEBERIA_USAR: opera sobre el mismo problema (una senal declarada) y NO lo importa
        for senal in (ficha.get("senales") or []):
            try:
                sre = re.compile(senal)
            except re.error:
                continue
            for r, t in fuentes:
                if r == ruta or r in usan or r in (ficha.get("exentos") or []):
                    continue
                if sre.search(t):
                    arista(r, "DEBERIA_USAR", "helper:" + mod, por=senal)

    # ---- MEMORIAS DE METODO ----------------------------------------------------------
    # Una memoria es una LECCION que un instrumento aprendio. Modelarla como arista de un nodo
    # a SI MISMO no dice nada: no hay travesia posible. Se modela como nodo MEMORIA propio, y
    # las 94 aristas dejan de ser bucles.
    for i, m in enumerate((cargar(MEM).get("memories") or [])):
        quien = m.get("learned_by")
        if not (quien and quien in nodos):
            continue
        mid = "mem:%s#%d" % (quien, i)
        nodo("MEMORIA", mid, kind=m.get("kind"), de=quien,
             hecho=str(m.get("fact"))[:160])
        arista(quien, "RECUERDA", mid, kind=m.get("kind"))

    # ---- SALUD: lo que el grafo DELATA ------------------------------------------------
    por_rel = Counter(a["rel"] for a in aristas)
    grado = defaultdict(lambda: {"entra": 0, "sale": 0})
    for a in aristas:
        grado[a["de"]]["sale"] += 1
        grado[a["a"]]["entra"] += 1

    skills_sin_lector = sorted(
        n for n, v in nodos.items() if v["tipo"] == "SKILL"
        and not any(a["rel"] == "LEE" and a["a"] == n for a in aristas))
    alg_sin_skill = sorted(
        n for n, v in nodos.items() if v["tipo"] == "ALGORITMO"
        and not any(a["rel"] == "LEE" and a["de"] == n for a in aristas))
    agentes_sin_instrumento = sorted(
        n for n, v in nodos.items() if v["tipo"] == "AGENTE"
        and not any(a["rel"] == "INVOCA" and a["de"] == n for a in aristas))
    rotos = sorted(n for n, v in nodos.items() if v["tipo"] == "ALGORITMO"
                   and str(v.get("state", "")).upper() in ("DEFECTO_VIVO", "ROTO", "MUERTO"))

    doc = {
        "_que_es": ("el grafo de mis PROPIOS instrumentos: skills, agentes, algoritmos, "
                    "puertas, stores y memorias, con QUIEN USA A QUIEN. Un brain del brain"),
        "_por_que": ("cada tipo vivia en su lista y ninguna decia quien usa a quien. Sin eso, "
                     "48 skills con cientos de KB de metodo pueden estar sin leer y nadie se "
                     "entera: el conocimiento no se pierde por borrarse, se pierde por no ser "
                     "alcanzable"),
        "_no_duplica": ("cada store sigue siendo la fuente de su tipo de nodo. Esto construye y "
                        "mide las ARISTAS, que es lo que no existia"),
        "_medido_utc": "2026-08-26",
        "resumen": {
            "nodos": dict(Counter(v["tipo"] for v in nodos.values())),
            "aristas": dict(por_rel),
        },
        "salud": {
            "skills_sin_ningun_lector": {
                "cuantos": len(skills_sin_lector), "cuales": skills_sin_lector,
                "_que_significa": ("metodo curado que nadie alcanza. No siempre es defecto -- "
                                   "puede ser de un tema dormido -- pero hay que saberlo")},
            "algoritmos_que_no_leen_ningun_skill": {
                "cuantos": len(alg_sin_skill), "muestra": alg_sin_skill[:20]},
            "agentes_sin_instrumento_declarado": {
                "cuantos": len(agentes_sin_instrumento), "cuales": agentes_sin_instrumento,
                "_que_significa": ("no nombran ningun script registrado: su metodo vive en su "
                                   "prompt y muere con el")},
            "instrumentos_rotos_o_con_defecto_vivo": {"cuantos": len(rotos), "cuales": rotos},
            "aristas_que_faltan_frente_a_las_que_hay": {
                "LEE": por_rel.get("LEE", 0), "DEBERIA_LEER": por_rel.get("DEBERIA_LEER", 0),
                "conectividad_pct": round(100.0 * por_rel.get("LEE", 0)
                                          / max(1, por_rel.get("LEE", 0)
                                                + por_rel.get("DEBERIA_LEER", 0)), 1),
                "_que_significa": ("de todo el conocimiento que un instrumento DEBERIA leer, "
                                   "que porcentaje lee de verdad. Es el termometro del bucle: "
                                   "si una sesion no lo sube, conecto menos de lo que solto")},
            "helpers": {
                "cuantos": sum(1 for v in nodos.values() if v["tipo"] == "HELPER"),
                "con_ficha_HELPER": sum(1 for v in nodos.values()
                                        if v["tipo"] == "HELPER" and v.get("declarado")),
                "usa": por_rel.get("USA", 0),
                "deberia_usar": por_rel.get("DEBERIA_USAR", 0),
                "sin_ficha_no_pueden_tener_DEBERIA_USAR": sorted(
                    v["fichero"] for v in nodos.values()
                    if v["tipo"] == "HELPER" and not v.get("declarado")),
                "_que_significa": (
                    "H142. Un HELPER no era nodo, luego no podia tener lector, luego que se "
                    "ignorara era INVISIBLE. Y la diferencia con un skill importa: un skill no "
                    "leido es conocimiento que no se aplica; un helper no usado es una funcion "
                    "que YA resuelve el problema y que alguien reescribe PEOR -- produce "
                    "hallazgos FALSOS, no solo pobres."),
                "_lo_derivado_y_lo_declarado": (
                    "el nodo y USA se DERIVAN de los imports reales (2+ importadores = helper "
                    "compartido). DEBERIA_USAR necesita saber QUE PROBLEMA resuelve, y eso no "
                    "se deriva: lo declara el modulo en un dict `HELPER` con sus `senales`, "
                    "misma convencion que `QUALITY_CHECK`. Un helper sin ficha aparece igual, "
                    "pero su abandono sigue sin medirse -- por eso se listan."),
                "_limite": (
                    "USA cuenta un IMPORT, no una llamada. Importar y no llamar cuenta igual "
                    "que usarlo bien -- mismo techo que el LEE. Y las senales solo alcanzan "
                    "a ficheros de brain_v2/, scripts/, process_mining/ y quality_checks/."),
            },
            "colaboracion_entre_agentes": {
                "delega": por_rel.get("DELEGA", 0),
                "delega_ENTREGA_declarada": sum(
                    1 for x in aristas if x["rel"] == "DELEGA" and x.get("entrega")),
                "delega_solo_MENCION": sum(
                    1 for x in aristas if x["rel"] == "DELEGA" and not x.get("entrega")),
                "menciones_que_no_son_entrega": [
                    f"{x['de']} -> {x['a']}: {x.get('evidencia', '')[:90]}"
                    for x in aristas if x["rel"] == "DELEGA" and not x.get("entrega")],
                "agentes_que_no_delegan_en_nadie": sorted(
                    n for n, v in nodos.items() if v["tipo"] == "AGENTE"
                    and not any(x["rel"] == "DELEGA" and x["de"] == n for x in aristas)),
                "agentes_AISLADOS_en_los_dos_sentidos": sorted(
                    n for n, v in nodos.items() if v["tipo"] == "AGENTE"
                    and not any(x["rel"] == "DELEGA" and (x["de"] == n or x["a"] == n)
                                for x in aristas)),
                "_que_significa": ("un agente que no nombra a ningun otro trabaja solo. Hasta "
                                   "2026-08-26 esto valia CERO y el grafo publicaba 10 por "
                                   "contar bucles de memoria como colaboracion"),
                "_y_nombrar_no_es_entregar": ("s107: NOMBRAR a otro agente no es PASARLE "
                                              "trabajo. Se separan las dos cifras porque "
                                              "contar una mencion de estilo como colaboracion "
                                              "es el mismo defecto que el LEE, que cuenta una "
                                              "cita como una lectura. La cifra que vale es "
                                              "delega_ENTREGA_declarada"),
                "_y_no_delegar_no_es_estar_aislado": ("un agente sin salida puede estar "
                                                      "perfectamente integrado si OTROS le "
                                                      "delegan. El aislamiento real es no "
                                                      "tener ninguna arista en NINGUN sentido "
                                                      "-- eso es lo que mide H141")},
            "exploracion": {
                "mineros": sum(1 for v in nodos.values() if v["tipo"] == "MINERO"),
                "clases_de_mineria_cubiertas": sorted(
                    v["nombre"].split(":", 1)[1] for v in nodos.values()
                    if v["tipo"] == "CLASE_MINERIA"),
                "declaran_que_generalizan": sum(1 for v in nodos.values()
                                                if v["tipo"] == "MINERO" and v.get("generaliza")),
                "_ojo_con_esa_cifra": ("`generaliza` es un campo NUEVO (s105): un 1 aqui NO "
                                       "significa que los otros 58 esten atados a su caso, "
                                       "significa que nadie lo ha declarado todavia. Es adopcion "
                                       "del campo, no genericidad medida. Confundirlo seria "
                                       "publicar una alarma inventada."),
                "_que_significa": ("un minero atado a su caso muere con el caso. Declarar que "
                                   "generaliza obliga a formular la PREGUNTA sin nombrar el "
                                   "caso, que es donde se ve si hay metodo o solo un script")},
        },
        "nodos": nodos,
        "aristas": aristas,
    }
    with open(SALIDA, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)

    if "--json" in sys.argv:
        print(json.dumps(doc["resumen"] | doc["salud"], ensure_ascii=False, indent=2))
        return 0
    print("[brain del brain] nodos:", dict(Counter(v["tipo"] for v in nodos.values())))
    print("                  aristas:", dict(por_rel))
    print(f"\n  skills sin NINGUN lector          : {len(skills_sin_lector)} de "
          f"{sum(1 for v in nodos.values() if v['tipo'] == 'SKILL')}")
    print(f"  algoritmos que no leen ningun skill: {len(alg_sin_skill)}")
    print(f"  agentes sin instrumento declarado  : {len(agentes_sin_instrumento)}")
    print(f"  instrumentos rotos o con defecto   : {len(rotos)}")
    print(f"\n  LEE {por_rel.get('LEE', 0)}  frente a  DEBERIA_LEER "
          f"{por_rel.get('DEBERIA_LEER', 0)}")
    print(f"\n-> {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
