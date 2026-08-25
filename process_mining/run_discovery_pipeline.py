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
BASE = REPO / "process_mining" / "baseline_objects.json"


def tomar_foto_de_base():
    """Los nombres que el grafo YA tenia ANTES de correr la cadena.

    Sin esto el cruce final es CIRCULAR y no puede descubrir nada: compara lo que los mineros
    acaban de escribir contra un brain_state que ya ingirio esos mismos stores en el rebuild
    anterior. Medido en su estrena -- 17 fuentes, 0 NUEVOS en todas salvo learned_rules, que es
    justo el unico store que no se ingiere. Parecia que no habia nada nuevo y lo que pasaba es
    que la pregunta estaba mal hecha.

    La foto se guarda en disco con su fecha para que una corrida parcial (--desde) siga
    comparando contra el estado PREVIO a la cadena, no contra el de hace un minuto.
    """
    try:
        estado = json.loads((REPO / "brain_v2" / "brain_state.json").read_text(encoding="utf-8"))
        nombres = sorted({str(k).upper() for k in (estado.get("objects") or {})})
    except Exception:
        return None
    BASE.write_text(json.dumps({
        "_que_es": ("los nombres que el grafo tenia ANTES de esta corrida. El cruce final compara "
                    "contra esto, no contra el grafo de despues, que ya contiene lo recien "
                    "escrito"),
        "tomada": time.strftime("%Y-%m-%d %H:%M:%S"),
        "objetos": len(nombres), "nombres": nombres,
    }, ensure_ascii=False), encoding="utf-8")
    return len(nombres)

# El ORDEN y sus invariantes viven ademas como CONOCIMIENTO en
# brain_v2/methods/orchestration.json: que produce cada fase, que necesita, y que pasa si se
# salta. Aqui esta la ejecucion; alli el porque, que es lo que se puede consultar, mejorar y
# replicar en otra instalacion sin tocar este fichero.
ORQUESTACION = REPO / "brain_v2" / "methods" / "orchestration.json"

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
                  ("A4 escalera de dominio", "process_mining/executed_objects_domain_map.py", []),
                  # POR DONDE entra el trabajo que NO pasa por una transaccion de dialogo.
                  # Este es el metodo que encontro ALLOS y que vivio un dia solo como prompt.
                  ("A31 canal batch input", "process_mining/bdc_channel_mining.py", []),
                  # QUE le anadimos nosotros al modelo estandar. Estaban registrados y sin
                  # llamador: un algoritmo que no corre no es capacidad, es documentacion.
                  ("A13 campos custom del modelo", "process_mining/harvest_custom_fields.py",
                   []),
                  ("A19 campos custom de un maestro, en 3 ejes", "process_mining/wbs_model.py",
                   [])],
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
        "pasos": [("A22 composicion de dominio", "brain_v2/domain_composition.py", []),
                  ("A24 ciclo de vida documental", "process_mining/document_lifecycle.py", []),
                  ("A5 descubrimiento adaptativo", "process_mining/adaptive_discovery.py", []),
                  ("hallazgos sin aterrizar", "brain_v2/methods/unlanded_discoveries.py", [])],
    },
]


def la_columna_vertebral_aguanta():
    """A21 ES UNA PUERTA, NO UN ORDEN. Y hasta ahora estaba implementada solo como orden.

    Nada leia case_spine.json: la familia B corria igual si A21 fallaba, agotaba el timeout o
    concluia que ninguna clase alcanza documento. Eso permite exactamente la conclusion falsa
    que A21 documenta en su modo de fallo: un DFG, unas variantes y unos cuellos de botella
    PLAUSIBLES de un proceso que no existe, presentados como resultado OK de la cadena.

    Devuelve (pasa, motivo, detalle).
    """
    p = REPO / "brain_v2" / "case_spine.json"
    if not p.exists():
        return False, "no existe case_spine.json: A21 no ha corrido o fallo", {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"case_spine.json ilegible ({type(e).__name__})", {}

    texto = json.dumps(d, ensure_ascii=False).upper()
    combinan = texto.count("COMBINA") - texto.count("NO_COMBINA")
    cob = None
    for k in ("cobertura", "coverage", "pct_alcanzable", "reachable_pct"):
        v = d.get(k)
        if isinstance(v, (int, float)):
            cob = float(v)
            break
    if combinan <= 0:
        return False, "NINGUNA clase de documento alcanza su tabla: no hay nocion de caso", \
            {"clases_que_combinan": combinan}
    return True, f"{combinan} clase(s) alcanzan documento", \
        {"clases_que_combinan": combinan, "cobertura": cob}


def correr(nombre, rel, args, dry, tope=3600):
    p = REPO / rel
    if not p.exists():
        return {"paso": nombre, "script": rel, "estado": "NO_EXISTE"}
    if dry:
        return {"paso": nombre, "script": rel, "estado": "DRY"}
    t = time.time()
    # PROGRESO EN VIVO. Capturar toda la salida hacia que un paso de dos minutos pareciera
    # colgado -- pasa con B5 (128s) y con A5 (56s). Se emite un latido para que se vea que
    # avanza sin ensuciar la salida.
    # LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO, ANTES DE CORRERLO.
    #
    # 22 de 32 mineros no leen algorithm_memory.json, asi que pueden repetir un error ya medido
    # -- y mecanizado, corre solo cada semana. Que la cadena lo IMPRIMA no cambia lo que el
    # script hace: eso solo lo arregla que el script lo lea. Pero al menos el error deja de ser
    # invisible para quien mira la corrida, y la lista de los 22 esta en el PMO.
    try:
        from metodo import lo_que_ya_aprendimos  # type: ignore
        _m = lo_que_ya_aprendimos(os.path.basename(rel).replace(".py", ""), nombre)
        for _x in _m.trampas()[:2]:
            print(f"           ! ya aprendido: {str(_x.get('implication'))[:100]}", flush=True)
    except Exception:
        pass
    print(f"           . corriendo {rel} ...", flush=True)
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

    # Contra la FOTO DE BASE, no contra el grafo de ahora. Si no hay foto se avisa y se usa el
    # grafo actual, diciendo claramente que en ese caso el resultado es circular y no vale.
    base = carga("process_mining", "baseline_objects.json")
    if base.get("nombres"):
        conocidos = {str(n).upper() for n in base["nombres"]}
        fecha_base = base.get("tomada")
        circular = False
    else:
        estado = carga("brain_v2", "brain_state.json")
        conocidos = {str(k).upper() for k in (estado.get("objects") or {})}
        fecha_base, circular = None, True
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
    # La clave real es `delta_vs_model.worklist_custom`, no 'classified' -- que no existe. Con
    # la clave equivocada el extractor caia en su fallback silencioso, contaba 4 nombres de
    # CONTENEDOR (rows/programs/actors/delta_vs_model) y publicaba "0 NUEVOS" mientras el
    # fichero llevaba `unexplained: 1318` y una lista de nombres concretos. El aviso "no se
    # reconocio ninguna forma" NO saltaba, porque el fallback siempre encuentra algo.
    # Nada aqui: `variant_content.json` y `bdc_channel.json` ya estan en STORES_AL_GRAFO, y
    # declararlos otra vez los contaba DOS VECES en el delta con dos nombres distintos
    # (variante/variantes, bdc/bdc_generador). Un duplicado con dos nombres parece dos
    # hallazgos.
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

    # PUBLICAR EN EL BUS lo que esta corrida vio y el brain no sabia. Sin este paso la cadena
    # escribia un parte que nadie mas leia -- exactamente el defecto que el bus vino a arreglar,
    # cometido por la propia cadena que lo estrena.
    try:
        from mining_bus import publicar  # type: ignore
        for clave, lista in nuevos.items():
            for nombre in lista[:20]:
                publicar(f"A29_discovery_chain/{clave}", "RESTO_SIN_EXPLICAR", nombre,
                         f"lo vio {clave} en esta corrida y el grafo no lo tenia",
                         evidencia=f"process_mining/discovery_delta.json :: {clave}",
                         autoridad="MEDIDO_EN_DATOS", aspecto="visto_sin_conocer")
    except Exception as e:
        print(f"    AVISO: no se pudo publicar en el bus de mineros ({type(e).__name__})")

    # SACAR LOS CHOQUES. El final de la cadena es el unico instante en que todos los mineros
    # acaban de opinar sobre los mismos sujetos: es cuando los choques son detectables y
    # frescos. La version anterior solo PUBLICABA en el bus y nunca lo consultaba, asi que el
    # metodo que produjo el hallazgo grande -- E_SILVA canal contra E_SILVA persona -- no se
    # ejercitaba nunca.
    choques_vistos = []
    try:
        from mining_bus import choques  # type: ignore
        choques_vistos = choques()
    except Exception:
        pass

    delta = {
        "_que_es": ("lo que la cadena de descubrimiento encontro y el brain TODAVIA NO SABE. "
                    "Cada nombre de aqui es un candidato a claim, o a un objeto que falta"),
        "_como_se_lee": ("NUEVOS no significa 'importante': significa 'no lo teniamos'. El "
                         "trabajo es decidir cual de ellos merece un claim, y los que no, por que"),
        "_siguiente": "python brain_v2/rebuild_all.py  (lleva todo al grafo)",
        "_base_de_comparacion": (
            f"foto tomada {fecha_base}, antes de correr la cadena" if not circular else
            "SIN FOTO DE BASE: se comparo contra el grafo ACTUAL, que ya contiene lo que los "
            "mineros acaban de escribir. El resultado es circular y no vale como descubrimiento"),
        "objetos_en_la_base": len(conocidos),
        "choques_entre_mineros": {
            "_que_son": ("sujetos sobre los que dos mineros dicen cosas distintas. Suele valer "
                         "mas que cualquiera de los dos hallazgos por separado: asi salio H71"),
            "n": len(choques_vistos),
            "casos": [{"sujeto": c["sujeto"], "mineros": c["mineros"],
                       "resolucion": c["resolucion"]} for c in choques_vistos[:20]]},
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
    # Las invariantes se IMPRIMEN al arrancar. Un orden que solo vive en el codigo se cumple y
    # no se entiende, y el que venga detras no sabe cual puede tocar.
    try:
        _o = json.loads(ORQUESTACION.read_text(encoding="utf-8"))
        print("\nlas reglas que este orden respeta:")
        for _i in _o.get("invariantes", []):
            print(f"  · {_i['regla']}")
            print(f"      {_i['por_que'][:104]}")
    except Exception:
        pass
    bitacora, t0 = [], time.time()
    # La foto SOLO se renueva si de verdad se va a minar. En una corrida de solo-cruce
    # (--desde 5) retomarla aqui la dejaria identica al grafo de ahora y volveria a ser
    # circular: hay que seguir comparando contra el estado previo a la ULTIMA mineria.
    va_a_minar = any(not f["opcional"] and f["id"] >= a.desde and f["id"] < 5 for f in FASES)
    if not a.dry and va_a_minar:
        n = tomar_foto_de_base()
        print(f"\nfoto de base: {n:,} objetos en el grafo ANTES de empezar" if n else
              "\nAVISO: no se pudo tomar foto de base -- el cruce final sera circular")
    elif not a.dry:
        print("\nfoto de base: se conserva la anterior (esta corrida no mina, solo cruza)")
    for f in FASES:
        if f["opcional"] and not a.con_ingesta:
            print(f"\n[{f['id']}] {f['nombre']}  -- SALTADA (pasa --con-ingesta)")
            print(f"    {f['por_que']}")
            continue
        if f["id"] < a.desde:
            print(f"\n[{f['id']}] {f['nombre']}  -- saltada por --desde")
            continue
        # ---- LA PUERTA. La familia B no corre sin columna vertebral de casos ----
        if f["id"] == 3 and not a.dry:
            pasa, motivo, det = la_columna_vertebral_aguanta()
            if not pasa:
                print(f"\n[3] MINERIA DE PROCESOS -- NO SE CORRE")
                print(f"    PUERTA CERRADA: {motivo}")
                print("    A21 declara en su modo de fallo que un DFG sobre la nocion de caso")
                print("    equivocada produce un mapa PLAUSIBLE de un proceso que no existe.")
                print("    Correr la familia B ahora no daria cero: daria algo verosimil y falso.")
                bitacora.append({"fase": 3, "paso": "PUERTA A21", "estado": "BLOQUEADA",
                                 "motivo": motivo})
                continue
            print(f"\n[3] {f['nombre'].upper()}   [puerta A21 abierta: {motivo}]")
            print(f"    {f['por_que']}")
            for nombre, rel, args in f["pasos"]:
                r = correr(nombre, rel, args, a.dry)
                bitacora.append(dict(r, fase=3))
                marca = {"OK": "  ok", "DRY": " dry", "NO_EXISTE": " ---"}.get(r["estado"],
                                                                               "FALLO")
                print(f"    [{marca}] {nombre:38s} {r.get('segundos','')}s")
                for l in r.get("ultimas_lineas") or []:
                    print(f"           {l[:110]}")
                if r.get("error"):
                    print(f"           ERR {r['error'][:160]}")
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
            aviso = "  <- FORMA NO RECONOCIDA" if v.get("_aviso") else ""
            print(f"    {k:26s} {v['nombres']:>6} nombres · {v['ya_en_el_grafo']:>6} ya en el "
                  f"grafo · {v['NUEVOS']:>5} NUEVOS{aviso}")
        ch = (d.get("choques_entre_mineros") or {})
        print(f"\n    CHOQUES entre mineros: {ch.get('n', 0)}")
        for c in (ch.get("casos") or [])[:8]:
            print(f"      {c['sujeto']:22s} {', '.join(c['mineros'])[:70]}")
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
