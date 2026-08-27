"""EL BRAIN DEL BRAIN — un grafo de mis PROPIOS instrumentos, no seis listas que no se conocen.

POR QUE EXISTE
    Hay un brain de la DATA (objetos SAP, claims, incidentes, dominios) y no habia ninguno de
    las HERRAMIENTAS con las que se construye. Estaban en seis sitios que no se hablan:

        .agents/skills/*/SKILL.md      48 skills, cientos de KB de metodo curado
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

    # ---- DELEGA: la colaboracion REAL entre agentes ----------------------------------
    # Hasta 2026-08-26 el grafo publicaba 10 aristas AGENTE->AGENTE y las 10 eran BUCLES: un
    # agente recordando su propia leccion. La colaboracion no era escasa, era CERO. Aqui se
    # deriva de verdad: un agente que NOMBRA a otro en su prompt le esta pasando trabajo.
    _ag = [n for n, v in nodos.items() if v["tipo"] == "AGENTE"]
    for f in sorted(os.listdir(AGENTS)) if os.path.isdir(AGENTS) else []:
        if not f.endswith(".md"):
            continue
        yo = f[:-3]
        t = open(os.path.join(AGENTS, f), encoding="utf-8", errors="ignore").read()
        for otro in _ag:
            if otro != yo and re.search(r"\b%s\b" % re.escape(otro), t):
                arista(yo, "DELEGA", otro)

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
            "colaboracion_entre_agentes": {
                "delega": por_rel.get("DELEGA", 0),
                "agentes_que_no_delegan_en_nadie": sorted(
                    n for n, v in nodos.items() if v["tipo"] == "AGENTE"
                    and not any(x["rel"] == "DELEGA" and x["de"] == n for x in aristas)),
                "_que_significa": ("un agente que no nombra a ningun otro trabaja solo. Hasta "
                                   "2026-08-26 esto valia CERO y el grafo publicaba 10 por "
                                   "contar bucles de memoria como colaboracion")},
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
