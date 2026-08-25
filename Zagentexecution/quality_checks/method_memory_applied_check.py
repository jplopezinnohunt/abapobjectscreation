"""GATE: un minero que no LEE la memoria de metodo repite errores ya medidos, mecanizados.

EL CASO QUE LO OBLIGA
    La memoria "APQI.CREATOR no es una identidad: es un parametro que quien llama a
    BDC_OPEN_GROUP escribe, y SAP no comprueba que el usuario exista" se escribio el
    2026-08-24. Al dia siguiente se mecanizo un minero de ese mismo canal que contaba
    CREATOR como si fueran actores y lo publicaba al bus.

    La memoria existia. El minero no la leyo. Y el error quedo MECANIZADO, que es peor que
    cometerlo a mano: ahora corre solo, cada semana, sin que nadie lo relea.

LA TERCERA PIEZA DE LA COLABORACION
    El bus (blackboard) hace que los mineros se HABLEN. Las preguntas abiertas (contract net)
    hacen que se PIDAN cosas. Esta es la que faltaba: que lo aprendido CAMBIE la forma de
    explorar. Sin ella, los otros dos mecanismos reparten conocimiento entre agentes que
    siguen equivocandose igual.

    `algorithm_memory.json` tiene 145 memorias y cada una lleva `implication`: literalmente
    QUE DEBEN HACER DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
    aprender y no aprender a la vez.

QUE COMPRUEBA
    1. Todo minero registrado con `mining_kind` IMPORTA `metodo` o lee algorithm_memory
    2. Toda memoria tiene `implication` -- sin ella es una nota, no cambia nada
    3. Toda memoria dice QUIEN la aprendio (`learned_by`), para poder preguntarle
    4. Hay memorias que NADIE puede leer: su tema no lo toca ningun minero registrado

Uso:  python Zagentexecution/quality_checks/method_memory_applied_check.py [--json]
Salida: exit 0 limpio · exit 1 si un minero corre a ciegas
"""
QUALITY_CHECK = {
    "tier": "gate",
    "needs": "files",
    "what": ("mineros que corren sin leer la memoria de metodo: repiten errores ya medidos, y "
             "ahora mecanizados"),
}
# ----------------------------------------------------------------------------
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALGOS = os.path.join(ROOT, "brain_v2", "methods", "algorithms.json")
MEM = os.path.join(ROOT, "brain_v2", "methods", "algorithm_memory.json")

# Los que por su naturaleza no consumen memoria de instrumento, con motivo.
FUERA = {
    "A30_mining_bus": "es el foro; no mina, transporta lo que otros concluyen",
    "A36_mining_capability_router": "enruta preguntas; no lee datos",
    "A26_knowledge_connectivity": "puerta sobre los stores, no sobre SAP",
    "A28_graph_landing": "puerta sobre los stores",
    "A32_mining_capability_census": "censo de codigo, no de datos",
    "A35_mining_artifact_detector": "detector sobre ficheros del repo",
    "A11_shared_algorithm_memory": "ES el store de memoria",
    "A29_discovery_chain": "orquesta; la memoria la leen sus pasos",
}


def main():
    try:
        A = json.load(open(ALGOS, encoding="utf-8")).get("algorithms") or {}
        M = json.load(open(MEM, encoding="utf-8")).get("memories") or []
    except Exception as e:
        print(f"no se pudo leer el registro: {e}")
        return 1

    h = []

    # ---- 1. mineros que corren a ciegas ----
    ciegos = []
    for aid, a in A.items():
        if not a.get("mining_kind") or aid in FUERA:
            continue
        lee = False
        for b in (a.get("bound_in") or []):
            p = os.path.join(ROOT, str(b).replace("/", os.sep))
            if not os.path.isfile(p):
                continue
            try:
                t = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if ("from metodo import" in t or "import metodo" in t
                    or "algorithm_memory" in t or "lo_que_ya_aprendimos" in t):
                lee = True
                break
        if not lee:
            ciegos.append(aid)
    if ciegos:
        h.append({"gravedad": "CORRE_A_CIEGAS", "cuantos": len(ciegos), "ids": sorted(ciegos),
                  "que_pasa": ("minan sin leer lo que este proyecto ya aprendio de sus propios "
                               "instrumentos. Cada uno puede repetir un error ya medido, y "
                               "mecanizado corre solo cada semana"),
                  "como_se_arregla": ("from metodo import lo_que_ya_aprendimos; "
                                      "m = lo_que_ya_aprendimos('<tema>', ...); m.avisar()")})

    # ---- 1b. ¿LA SALIDA OBEDECE? Leer no es obedecer, y hasta ahora esta puerta media el
    # import -- o sea la FORMA. Ahora corre las comprobaciones ejecutables de `metodo` contra
    # el fichero que cada minero produce de verdad.
    sys.path.insert(0, os.path.join(ROOT, "process_mining"))
    desobedecen = []
    try:
        from metodo import obedece  # type: ignore
        for aid, a in A.items():
            if not a.get("mining_kind") or aid in FUERA:
                continue
            li = str(a.get("lands_in") or "")
            m = re.search(r"[\w/\\.-]+\.json", li)
            if not m:
                continue
            p = os.path.join(ROOT, m.group(0).replace("/", os.sep))
            if not os.path.isfile(p):
                continue
            try:
                doc = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            temas = (aid + " " + str(a.get("operates_on") or "") + " " +
                     str(a.get("does") or "")).lower()
            for f in obedece(doc, temas=(temas,)):
                desobedecen.append({"algoritmo": aid, "store": m.group(0), **f})
    except Exception as e:
        print(f"  AVISO: no se pudieron correr las comprobaciones ({type(e).__name__}: {e})")
    if desobedecen:
        h.append({"gravedad": "LA_SALIDA_DESOBEDECE", "cuantos": len(desobedecen),
                  "ids": [f"{d['algoritmo']}: {d['regla']}" for d in desobedecen[:8]],
                  "detalle": desobedecen[:12],
                  "que_pasa": ("el minero LEE la memoria y su salida la incumple. Esta es la "
                               "comprobacion que importa: hasta ahora esta puerta media que "
                               "importaran el modulo, que es la FORMA")})

    # ---- 2. memorias que no cambian nada ----
    sin_impl = [m for m in M if not str(m.get("implication") or "").strip()]
    if sin_impl:
        h.append({"gravedad": "MEMORIA_SIN_IMPLICACION", "cuantos": len(sin_impl),
                  "ids": [str(m.get("fact"))[:60] for m in sin_impl[:6]],
                  "que_pasa": ("una memoria sin implicacion es una NOTA: no dice que deben "
                               "hacer distinto los demas, asi que no cambia nada")})

    # ---- 3. memorias sin dueno ----
    sin_dueno = [m for m in M if not str(m.get("learned_by") or "").strip()]
    if sin_dueno:
        h.append({"gravedad": "MEMORIA_SIN_DUENO", "cuantos": len(sin_dueno),
                  "ids": [str(m.get("fact"))[:60] for m in sin_dueno[:6]],
                  "que_pasa": ("no se sabe que algoritmo la aprendio, asi que no se le puede "
                               "preguntar ni verificar con que evidencia")})

    # ---- 4. memorias que nadie puede alcanzar ----
    corpus = ""
    for aid, a in A.items():
        for b in (a.get("bound_in") or []):
            p = os.path.join(ROOT, str(b).replace("/", os.sep))
            if os.path.isfile(p):
                try:
                    corpus += open(p, encoding="utf-8", errors="ignore").read().lower()
                except Exception:
                    pass
    huerfanas = []
    for m in M:
        objs = m.get("related_objects") or []
        temas = [str(o).lower() for o in objs if len(str(o)) > 3]
        if temas and not any(t in corpus for t in temas):
            huerfanas.append(str(m.get("fact"))[:70])
    if huerfanas:
        h.append({"gravedad": "MEMORIA_INALCANZABLE", "cuantos": len(huerfanas),
                  "ids": huerfanas[:6],
                  "que_pasa": ("habla de objetos que ningun minero registrado toca: esta "
                               "guardada y nadie la va a leer nunca")})

    rep = {"_que_comprueba": ("que lo aprendido CAMBIE la forma de explorar, no solo que se "
                              "guarde"),
           "_por_que": ("el bus hace que los mineros se hablen y las preguntas abiertas que se "
                        "pidan cosas; esta es la tercera pieza. Sin ella se reparte conocimiento "
                        "entre agentes que siguen equivocandose igual"),
           "mineros": sum(1 for a in A.values() if a.get("mining_kind")),
           "memorias": len(M), "hallazgos": h}
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if h else 0

    print(f"[memoria aplicada] {rep['mineros']} mineros · {len(M)} memorias")
    if not h:
        print("  OK - los mineros leen lo aprendido y cada memoria cambia algo")
        return 0
    for x in h:
        print(f"  [{x['gravedad']}] {x['cuantos']}")
        print(f"      {x['que_pasa']}")
        print(f"      -> {', '.join(str(i) for i in x['ids'][:6])}")
        if x.get("como_se_arregla"):
            print(f"      ARREGLO: {x['como_se_arregla']}")
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
