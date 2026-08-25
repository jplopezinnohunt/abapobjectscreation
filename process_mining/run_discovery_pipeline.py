"""LA CADENA DE DESCUBRIMIENTO — en el orden que imponen las dependencias, no el que apetezca.

POR QUE EXISTE
    Medido 2026-08-25: once algoritmos registrados no los llamaba nadie, y entre ellos estaba
    la familia B ENTERA de process mining -- DFG, variantes, cuellos de botella, conformidad,
    OCEL2. Capacidad construida que llevaba meses sin ejecutarse.

    Y no estaban muertos por olvido. El orden estaba escrito en el propio registro: A21 declara
    en su `lands_in` que la columna vertebral de casos es "insumo de B1-B5". Nadie llamaba a
    A21 tampoco, asi que la familia B habria corrido sobre una nocion de caso ausente -- que es
    literalmente su modo de fallo: "un DFG sobre la nocion de caso equivocada produce un mapa
    plausible de un proceso que no existe".

LA INGESTA VA APARTE, Y A PROPOSITO
    Traer log de P01 es un grifo: caro, lento y periodico. Lo rico no es extraer, es COMBINAR
    lo que ya hay con lo que descubrieron los demas. Por eso la fase 0 solo corre si se pide
    (`--con-ingesta`, pensada para una tarea semanal) y la cadena por defecto empieza en la 1.
    Sin esa separacion, cada vez que quisieras cruzar conocimiento pagarias una extraccion.

LO QUE LA HACE DESCUBRIR Y NO SOLO CALCULAR
    La ultima fase no ejecuta ningun algoritmo: CRUZA lo que las anteriores produjeron contra
    lo que el brain ya sabe -- objetos del grafo, claims, inventario de interfaces -- y separa
    lo NUEVO de lo YA CONOCIDO. Sin ese cruce, cada corrida vuelve a informar de lo mismo y el
    hallazgo de verdad se pierde entre el ruido de lo repetido.

Uso:
    python process_mining/run_discovery_pipeline.py                 # lo rico, sin ingesta
    python process_mining/run_discovery_pipeline.py --con-ingesta   # + traer log (semanal)
    python process_mining/run_discovery_pipeline.py --desde 3       # reanudar en una fase
    python process_mining/run_discovery_pipeline.py --dry           # solo decir que correria

Despues de esto va `python brain_v2/rebuild_all.py`, que es quien lleva todo al grafo.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SALIDA = REPO / "process_mining" / "discovery_delta.json"

FASES = [
    {
        "id": 0, "nombre": "ingesta (grifo, periodica)", "opcional": True,
        "por_que": "traer log nuevo de P01. Cara y lenta: no se paga por cruzar conocimiento",
        "pasos": [("A1+A2 acumular log",
                   "Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py", [])],
    },
    {
        "id": 1, "nombre": "realidad", "opcional": False,
        "por_que": ("que nombre es un OBJETO y cual es basura generada, y de quien es cada cosa. "
                    "Contar antes de esto infla cualquier cifra"),
        "pasos": [("A19 filtro de realidad", "process_mining/log_reality_filter.py", []),
                  ("A3 clasificador RFC", "process_mining/rfc_process_classifier.py", []),
                  ("A4 escalera de dominio", "process_mining/executed_objects_domain_map.py", [])],
    },
    {
        "id": 2, "nombre": "COLUMNA VERTEBRAL DE CASOS", "opcional": False,
        "por_que": ("A21. Que documento es el CASO. Es la puerta de toda la familia B: sin esto "
                    "un DFG dibuja un proceso que no existe"),
        "pasos": [("A21 case spine", "brain_v2/case_spine.py", [])],
    },
    {
        "id": 3, "nombre": "mineria de procesos (familia B)", "opcional": False,
        "por_que": "el flujo real: que sigue a que, cuantas formas hay de hacerlo, donde espera",
        "pasos": [("B1+B2+B3 DFG/variantes/cuellos",
                   "Zagentexecution/sap_data_extraction/scripts/sap_process_discovery.py", []),
                  ("B4 conformidad P2P", "process_mining/p2p_conformance.py", []),
                  ("B4 rayos X contra el estandar",
                   "Zagentexecution/sap_data_extraction/scripts/p2p_stdref_xray.py", []),
                  ("B5 OCEL2 multiobjeto",
                   "Zagentexecution/sap_data_extraction/scripts/ocel_build_p2p.py", [])],
    },
    {
        "id": 4, "nombre": "ciclo de vida y aprendizaje", "opcional": False,
        "por_que": ("A24 mide como vive un documento; A5 aprende del RESTO sin resolver, que es "
                    "donde esta lo que todavia no sabemos nombrar"),
        "pasos": [("A24 ciclo de vida documental", "process_mining/document_lifecycle.py", []),
                  ("A5 descubrimiento adaptativo", "process_mining/adaptive_discovery.py", []),
                  ("hallazgos sin aterrizar", "brain_v2/methods/unlanded_discoveries.py", [])],
    },
]


def correr(nombre, rel, args, dry, tope=3600):
    p = REPO / rel
    if not p.exists():
        return {"paso": nombre, "script": rel, "estado": "NO_EXISTE"}
    if dry:
        return {"paso": nombre, "script": rel, "estado": "DRY"}
    t = time.time()
    try:
        r = subprocess.run([sys.executable, str(p)] + args, cwd=str(REPO),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=tope)
    except subprocess.TimeoutExpired:
        return {"paso": nombre, "script": rel, "estado": "TIMEOUT",
                "segundos": round(time.time() - t)}
    cola = [l for l in (r.stdout or "").strip().splitlines() if l.strip()][-3:]
    return {"paso": nombre, "script": rel,
            "estado": "OK" if r.returncode == 0 else f"FALLO({r.returncode})",
            "segundos": round(time.time() - t), "ultimas_lineas": cola,
            "error": (r.stderr or "").strip()[-300:] if r.returncode else ""}


def cruzar_con_lo_conocido():
    """FASE 5 -- no ejecuta nada: SEPARA lo nuevo de lo que ya sabiamos.

    Es lo que convierte una corrida en un descubrimiento. Sin esto, cada pasada vuelve a
    informar de los mismos 4.900 nombres y el hallazgo de verdad se ahoga en lo repetido.
    """
    def carga(*p):
        try:
            return json.loads((REPO.joinpath(*p)).read_text(encoding="utf-8"))
        except Exception:
            return {}

    estado = carga("brain_v2", "brain_state.json")
    conocidos = {str(k).upper() for k in (estado.get("objects") or {})}
    claims = carga("brain_v2", "claims", "claims.json")
    texto_claims = json.dumps(claims, ensure_ascii=False).upper() if claims else ""

    # Se reusa el extractor agnostico de forma del constructor del brain en vez de escribir
    # otro aqui. La primera version de esta fase tenia su propia lectura, con supuestos sobre
    # la forma de cada store, y por eso encontro CERO nuevos en su estrena: leia 4 fuentes mal
    # y una ni se cargaba. El problema ya estaba resuelto dos horas antes en build_brain_state.
    sys.path.insert(0, str(REPO / "brain_v2"))
    try:
        from build_brain_state import _pares_nombre_hechos, STORES_AL_GRAFO  # type: ignore
    except Exception:
        _pares_nombre_hechos, STORES_AL_GRAFO = None, []

    fuentes = {s["key"]: (s["file"], s.get("at"), s.get("name_field"))
               for s in STORES_AL_GRAFO}
    # y los que produce esta cadena y todavia no estan en STORES_AL_GRAFO
    fuentes.setdefault("log_reality", ("log_reality.json", "classified", None))
    fuentes.setdefault("document_lifecycle", ("document_lifecycle.json", None, None))
    fuentes.setdefault("learned_rules", ("../process_mining/learned_rules.json", None, None))

    nuevos, resumen = {}, {}
    for clave, (rel, at, nf) in sorted(fuentes.items()):
        d = carga(*("brain_v2/" + rel).split("/")) or carga(*rel.split("/"))
        if not d or not _pares_nombre_hechos:
            continue
        nombres = {str(n).upper() for n, _ in _pares_nombre_hechos(d, at, nf)}
        nombres = {n for n in nombres if 2 < len(n) < 40 and not n.startswith("_")}
        if not nombres:
            resumen[clave] = {"nombres": 0, "ya_en_el_grafo": 0, "NUEVOS": 0,
                              "_aviso": "no se reconocio ninguna forma: revisa `at`/`name_field`"}
            continue
        fuera = sorted(n for n in nombres - conocidos if n not in texto_claims)
        resumen[clave] = {"nombres": len(nombres), "ya_en_el_grafo": len(nombres & conocidos),
                          "NUEVOS": len(fuera)}
        if fuera:
            nuevos[clave] = fuera[:60]

    delta = {
        "_que_es": ("lo que la cadena de descubrimiento encontro y el brain TODAVIA NO SABE. "
                    "Cada nombre de aqui es un candidato a claim, o a un objeto que falta"),
        "_como_se_lee": ("NUEVOS no significa 'importante': significa 'no lo teniamos'. El "
                         "trabajo es decidir cual de ellos merece un claim, y los que no, por que"),
        "_siguiente": "python brain_v2/rebuild_all.py  (lleva todo al grafo)",
        "objetos_en_el_grafo": len(conocidos),
        "resumen": resumen,
        "nuevos_por_fuente": nuevos,
    }
    SALIDA.write_text(json.dumps(delta, indent=2, ensure_ascii=False), encoding="utf-8")
    return delta


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--con-ingesta", action="store_true",
                    help="incluye la fase 0 (traer log de P01). Pensada para la tarea semanal")
    ap.add_argument("--desde", type=int, default=1, help="fase por la que empezar")
    ap.add_argument("--dry", action="store_true", help="decir que correria, sin correrlo")
    a = ap.parse_args()

    print("=" * 78)
    print("CADENA DE DESCUBRIMIENTO -- el orden lo imponen las dependencias")
    print("=" * 78)
    bitacora, t0 = [], time.time()
    for f in FASES:
        if f["opcional"] and not a.con_ingesta:
            print(f"\n[{f['id']}] {f['nombre']}  -- SALTADA (pasa --con-ingesta)")
            print(f"    {f['por_que']}")
            continue
        if f["id"] < a.desde:
            print(f"\n[{f['id']}] {f['nombre']}  -- saltada por --desde")
            continue
        print(f"\n[{f['id']}] {f['nombre'].upper()}")
        print(f"    {f['por_que']}")
        for nombre, rel, args in f["pasos"]:
            r = correr(nombre, rel, args, a.dry)
            bitacora.append(dict(r, fase=f["id"]))
            marca = {"OK": "  ok", "DRY": " dry", "NO_EXISTE": " ---"}.get(r["estado"], "FALLO")
            print(f"    [{marca}] {nombre:38s} {r.get('segundos','')}s")
            for l in r.get("ultimas_lineas") or []:
                print(f"           {l[:110]}")
            if r.get("error"):
                print(f"           ERR {r['error'][:160]}")

    print(f"\n[5] CRUCE CON LO QUE YA SABEMOS")
    print("    no ejecuta nada: separa lo NUEVO de lo repetido. Sin esto, cada corrida vuelve")
    print("    a informar de lo mismo y el hallazgo se ahoga en el ruido")
    if not a.dry:
        d = cruzar_con_lo_conocido()
        for k, v in (d.get("resumen") or {}).items():
            print(f"    {k:22s} {v['nombres']:>6} nombres · {v['ya_en_el_grafo']:>6} ya en el "
                  f"grafo · {v['NUEVOS']:>5} NUEVOS")
        print(f"    -> {SALIDA}")

    fallos = [b for b in bitacora if b["estado"].startswith(("FALLO", "TIMEOUT"))]
    print(f"\n{'=' * 78}")
    print(f"{len(bitacora)} paso(s) en {round(time.time() - t0)}s · {len(fallos)} fallo(s)")
    for b in fallos:
        print(f"  FALLO {b['paso']} ({b['script']})")
    print("SIGUIENTE: python brain_v2/rebuild_all.py")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
