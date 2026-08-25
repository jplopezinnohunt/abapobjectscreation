"""PREGUNTALE A LOS MINEROS. Cada minero es una CAPACIDAD, no un script que escribe un JSON.

POR QUE EXISTE
    Un minero que sabe leer variantes sirve para muchas mas cosas que para su propia corrida:
    lo necesita el analisis de una incidencia ("¿esta cuenta entra en alguna variante o no se
    procesa nunca?"), el de bancos ("¿que formato DMEE usa esa corrida?"), el alta de un maestro
    ("¿que sociedades cubre este job?"). Pero si la unica forma de usarlo es ejecutar un script
    y parsear su JSON, nadie lo llama: se vuelve a derivar a mano.

    Esto convierte los mineros en un servicio: se pregunta por TEMA y contesta quien sabe, con
    la llamada exacta y con lo que ya hay medido -- sin volver a minar si el dato esta fresco.

USO
    python process_mining/ask.py variantes
    python process_mining/ask.py "quien escribe datos maestros"
    python process_mining/ask.py --listar          # todas las capacidades
    python process_mining/ask.py --sujeto MULESOFT # que dicen los mineros de un sujeto

DESDE OTRO SCRIPT O AGENTE
    from ask import capacidades_para, responder
    for c in capacidades_para("variante"):
        print(c["algoritmo"], c["como_se_llama"])
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ALGOS = REPO / "brain_v2" / "methods" / "algorithms.json"
sys.path.insert(0, str(REPO / "process_mining"))

# QUE SE PUEDE PREGUNTAR Y QUIEN CONTESTA. Cada entrada dice la pregunta en el idioma en que
# la hace quien la necesita -- no en el idioma del algoritmo -- porque quien busca no sabe que
# existe A33: sabe que necesita saber donde deja los ficheros un job.
CAPACIDADES = [
    {
        "algoritmo": "A33_variant_content_mining",
        "responde": [
            "que hace REALMENTE este job o report periodico",
            "donde deja los ficheros una interfaz que corre por job",
            "que sociedades, cuentas o rangos cubre una corrida",
            "esta configuracion se EJECUTA alguna vez o esta fuera de toda variante",
            "que formato o arbol usa esta corrida",
            "que variantes trabajan igual entre si",
        ],
        "store": "brain_v2/variant_content.json",
        "como_se_llama": "python process_mining/variant_content_mining.py [--desde-cache]",
        "como_se_importa": ("from variant_content_mining import clase_de, mecanismo, "
                            "del_gold, contenido"),
        "lo_que_NO_puede": ("solo cubre las variantes DISENADAS (127 de 29.190 pares); las de "
                            "un solo uso no se leen y no dicen nada"),
        "trampa": ("una configuracion EXISTE para todos y se EJECUTA para algunos: quien sabe "
                   "cual corre es la VARIANTE, nunca la tabla de configuracion"),
    },
    {
        "algoritmo": "A31_bdc_channel_mining",
        "responde": [
            "de donde sale esta sesion de batch input",
            "que herramienta externa escribe en produccion sin estar declarada",
            "que transaccion ejecuta un programa generador",
            "quien ejecuta sesiones (SM35) frente a quien mira jobs (SM37)",
            "esta cuenta que crea sesiones es una persona o un texto",
        ],
        "store": "brain_v2/bdc_channel.json",
        "como_se_llama": "python process_mining/bdc_channel_mining.py [--desde AAAAMMDD]",
        "como_se_importa": ("from bdc_channel_mining import transacciones_de, forma, "
                            "prueba_objeto_de_negocio, lo_que_de_verdad_se_ejecuto"),
        "lo_que_NO_puede": ("decir que hizo una sesion concreta: APQD.VARDATA es LCHR y "
                            "RFC_READ_TABLE lo rechaza. Y la cola BORRA lo que se procesa bien"),
        "trampa": "el reparto de QSTATE NO es una tasa de fallo",
    },
    {
        "algoritmo": "A27_interface_nature",
        "responde": [
            "quien escribe DATOS MAESTROS y por que canal",
            "esta cuenta tecnica es una persona o un sistema",
            "por donde entra el trabajo en este dominio",
            "que le hace al sistema este canal: lee, transacciona o toca maestros",
            "hay alguna cuenta de persona usada como canal de escritura (H71)",
        ],
        "store": "brain_v2/interface_inventory.json",
        "como_se_llama": ("python brain_v2/build_interface_inventory.py  ·  consulta: "
                          "python brain_v2/graph_queries.py channels [dominio|writers|"
                          "master_data|sod]"),
        "como_se_importa": ("from build_interface_inventory import _naturaleza_fm, "
                            "_tipos_de_usuario, _desde_donde_llama"),
        "lo_que_NO_puede": ("saber que hace un destino SALIENTE del otro lado: eso se mide en "
                            "el otro extremo"),
        "trampa": ("quien entra lo dice USR02-USTYP, NO el log: dos heuristicas sobre logons "
                   "fallaron por los dos lados"),
    },
    {
        "algoritmo": "A21_case_spine",
        "responde": [
            "que documento es el CASO de este proceso",
            "esta clase de cambio alcanza su tabla de documento",
            "puedo hacer mineria de flujo sobre esta clase",
        ],
        "store": "brain_v2/case_spine.json",
        "como_se_llama": "python brain_v2/case_spine.py",
        "como_se_importa": "-",
        "lo_que_NO_puede": "nada de flujo por si mismo: es la PUERTA de B1-B5",
        "trampa": ("sin nocion de caso, un DFG dibuja un proceso PLAUSIBLE que no existe. No es "
                   "opcional"),
    },
    {
        "algoritmo": "A34_account_behaviour_classes",
        "responde": [
            "de que TIPO es esta cuenta de mayor (banco, deposito, inversion)",
            "esta cuenta tiene que revaluar",
            "que cuentas se quedan fuera del alcance de un proceso",
        ],
        "store": "PENDIENTE - hoy se deriva en vivo y no se guarda",
        "como_se_llama": ("python Zagentexecution/quality_checks/fsv_coverage_check.py "
                          "<cuenta...> | --sweep"),
        "como_se_importa": "from fsv_coverage_check import versions_in_use, read",
        "lo_que_NO_puede": "todavia no persiste: cada analisis lo re-deriva",
        "trampa": ("una version de balance EXISTE para todas las sociedades y se EJECUTA para "
                   "algunas: la elige la VARIANTE de RFBILA00 (BILAVERS), nunca T011. Usar la "
                   "equivocada invento un hueco de 144 M EUR"),
    },
    {
        "algoritmo": "B1_B2_B3_flujo",
        "responde": [
            "que sigue a que en este proceso",
            "cuantas formas distintas hay de hacer lo mismo",
            "donde espera un proceso, donde estan los cuellos de botella",
            "cuanto se parece lo real al modelo descubierto (fitness)",
            "nada de flujo por si mismo: es lo que A21 no puede",
        ],
        "store": "Zagentexecution/sap_data_extraction/process_discovery/",
        "como_se_llama": ("python Zagentexecution/sap_data_extraction/scripts/"
                          "sap_process_discovery.py"),
        "como_se_importa": "-",
        "lo_que_NO_puede": ("nada sin NOCION DE CASO: necesita que A21 haya probado que la "
                            "clase alcanza su tabla de documento"),
        "trampa": ("un DFG sobre la nocion de caso equivocada produce un mapa PLAUSIBLE de un "
                   "proceso que no existe, y variantes sobre un log truncado parecen "
                   "simplicidad de proceso"),
    },
    {
        "algoritmo": "B4_conformidad",
        "responde": [
            "cuanto se aparta lo real de la norma",
            "hay facturas antes de la recepcion, o recepciones sin factura",
            "que porcentaje sale del camino feliz",
        ],
        "store": "Zagentexecution/sap_data_extraction/process_discovery/p2p_conformance.json",
        "como_se_llama": "python process_mining/p2p_conformance.py",
        "como_se_importa": "-",
        "lo_que_NO_puede": "juzgar un proceso que no sea P2P: el modelo de referencia es de compras",
        "trampa": ("aplicar un modelo normativo de mercado sin comprobar la forma real del "
                   "tenant da 100% de no conformidad sin que nada este mal"),
    },
    {
        "algoritmo": "A19_log_reality_filter",
        "responde": [
            "este nombre es un OBJETO o una instancia generada",
            "cuantos objetos ejecutan de verdad, sin contar basura",
            "que actor es el mismo con dos grafias",
        ],
        "store": "brain_v2/log_reality.json",
        "como_se_llama": "python process_mining/log_reality_filter.py",
        "como_se_importa": "from log_reality_filter import normalize_actor",
        "lo_que_NO_puede": "decir QUE HACE un objeto: solo si es un objeto y de quien es",
        "trampa": ("contar antes de clasificar infla cualquier cifra: 576 'programas nuevos' "
                   "eran 95% instancias generadas"),
    },
    {
        "algoritmo": "A23_channel_discovery_by_traffic",
        "responde": [
            "que satelites entran por RFC sin estar declarados",
            "que cuenta tecnica trae trafico y desde que terminal",
        ],
        "store": "brain_v2/rfc_caller_apps.json",
        "como_se_llama": "-",
        "como_se_importa": "-",
        "lo_que_NO_puede": ("decir si una cuenta es una PERSONA o un sistema: eso lo declara "
                            "USR02-USTYP y lo contesta A27"),
        "trampa": ("la proporcion de logons RFC contra dialogo NO separa personas de sistemas: "
                   "fallo por los dos lados con BRIDGE-RFC, JOBBATCH, MULESOFT y WF-BATCH"),
    },
    {
        "algoritmo": "A24_document_lifecycle",
        "responde": [
            "cuantas veces se modifica un documento y en cuanto tiempo",
            "se arrastra de un ejercicio a otro",
            "que hizo una sesion concreta -- no, pero si que se toco ese dia",
        ],
        "store": "brain_v2/document_lifecycle.json",
        "como_se_llama": "python process_mining/document_lifecycle.py",
        "como_se_importa": "-",
        "lo_que_NO_puede": "por ahora solo sabe de KBLK/FMIOI; el metodo es generico y no esta abierto",
        "trampa": "un documento con 51 modificaciones en 0 dias no es un ciclo de vida: es una correccion en caliente",
    },
    {
        "algoritmo": "A30_mining_bus",
        "responde": [
            "que saben YA los demas mineros de este sujeto",
            "hay algun desacuerdo entre mineros sobre esto",
        ],
        "store": "process_mining/mining_findings.json",
        "como_se_llama": "python process_mining/mining_bus.py <sujeto> | choques",
        "como_se_importa": "from mining_bus import consultar, publicar, choques",
        "lo_que_NO_puede": "arbitrar: saca los choques y no los resuelve",
        "trampa": ("gana la fuente mas AUTORITATIVA -- un campo declarado por SAP vence a una "
                   "heuristica -- pero dos medidas del mismo peso no se votan: se miran"),
    },
]


def capacidades_para(texto):
    """Que mineros pueden contestar a esto. Busca en el idioma de QUIEN PREGUNTA."""
    t = (texto or "").lower().strip()
    if not t:
        return CAPACIDADES
    pal = [p for p in re.split(r"\W+", t) if len(p) > 2]
    out = []
    for c in CAPACIDADES:
        blob = json.dumps(c, ensure_ascii=False).lower()
        puntos = sum(1 for p in pal if p in blob)
        if puntos:
            out.append((puntos, c))
    return [c for _p, c in sorted(out, key=lambda x: -x[0])]


def responder(sujeto):
    """Lo que los mineros YA dijeron de un sujeto, sin volver a minar."""
    try:
        from mining_bus import consultar  # type: ignore
        return consultar(sujeto)
    except Exception:
        return []


def main():
    if "--listar" in sys.argv:
        for c in CAPACIDADES:
            print(f"\n{c['algoritmo']}")
            for r in c["responde"]:
                print(f"   · {r}")
            print(f"   llamada: {c['como_se_llama']}")
        return 0
    if "--sujeto" in sys.argv:
        s = sys.argv[sys.argv.index("--sujeto") + 1]
        hs = responder(s)
        print(f"{len(hs)} hallazgo(s) sobre {s}:")
        for h in hs:
            print(f"  [{h['autoridad']:18s}] {h['minero']:34s} {h['hallazgo'][:90]}")
        return 0

    q = " ".join(a for a in sys.argv[1:] if not a.startswith("--"))
    cs = capacidades_para(q)
    if not cs:
        print(f"ningun minero declara responder a '{q}'.")
        print("Prueba --listar, o registra la capacidad que falta con el agente "
              "`miner-onboarding`.")
        return 1
    print(f"{len(cs)} minero(s) pueden responder a '{q}':\n")
    for c in cs[:4]:
        print(f"  {c['algoritmo']}")
        for r in c["responde"][:4]:
            print(f"     · {r}")
        print(f"     llamada : {c['como_se_llama']}")
        print(f"     importar: {c['como_se_importa']}")
        print(f"     store   : {c['store']}")
        print(f"     NO puede: {c['lo_que_NO_puede']}")
        print(f"     TRAMPA  : {c['trampa']}\n")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
