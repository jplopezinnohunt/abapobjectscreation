"""EL CIRCULO SE CIERRA: un minero produce la evidencia que un claim abierto estaba esperando.

EL HUECO
    Todo el camino de ida existe: minero -> hallazgo -> bus -> grafo -> companion. Y el de
    vuelta no. Un claim que dice "no sabemos que hace ZSPOOL_TO_FILE" sigue abierto el dia
    despues de que A33 haya medido que escribe en \\\\hq-sapitf\\itf\\_PROD\\FM. La evidencia
    esta en el sistema y el claim no se entera.

    Eso no es un detalle de higiene: un claim abierto es una PREGUNTA VIVA que orienta el
    trabajo. Si no se cierra cuando se contesta, la lista de preguntas deja de decir en que
    estamos y pasa a ser un archivo. Y lo contrario tambien pasa: un claim que un minero
    CONTRADICE se queda ahi enseñando lo que ya no es verdad.

LO QUE HACE, Y LO QUE NO
    Cruza cada claim ABIERTO contra lo que los mineros han publicado, y propone tres cosas:

      RESUELVE      un minero midio justo lo que el claim preguntaba
      CONTRADICE    un minero midio lo CONTRARIO -- y eso vale mas que resolverlo
      REFUERZA      un minero midio algo que lo confirma por otro camino

    ⛔ PROPONE, NO CIERRA. Cerrar un claim es un juicio: hay que leer si la evidencia contesta
    la pregunta o solo se le parece. Un cierre automatico por coincidencia de palabras daria
    por sabido lo que no lo esta, que es peor que dejarlo abierto -- un claim abierto se mira,
    uno cerrado en falso no se vuelve a mirar nunca.

Uso:  python process_mining/claim_resolution.py [--json]
Aterriza en: brain_v2/claim_resolution_proposals.json
Quien decide: el agente `mining-arbiter` o `brain-steward`
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "process_mining"))
try:
    # Lo aprendido de este instrumento, ANTES de cruzar nada. En particular la trampa que este
    # mismo algoritmo estreno: buscar palabras de negacion hace que "No ES batch input" cuente
    # como una contradiccion cuando solo describe el canal.
    from metodo import lo_que_ya_aprendimos as _aprendido
except Exception:
    _aprendido = None

CLAIMS = REPO / "brain_v2" / "claims" / "claims.json"
BUS = REPO / "process_mining" / "mining_findings.json"
SALIDA = REPO / "brain_v2" / "claim_resolution_proposals.json"

# Palabras que marcan una pregunta ABIERTA dentro del texto de un claim.
PREGUNTA = ("no sabemos", "no se sabe", "sin verificar", "pendiente", "por confirmar",
            "habria que", "falta medir", "no esta claro", "desconocido", "sin medir",
            "unverified", "unknown", "to be confirmed")
# Palabras que marcan que el hallazgo NIEGA algo.
NIEGA = ("no es", "falso", "refutad", "al contrario", "en realidad", "no existe", "cero",
         "ninguna", "nunca")


# Lo que el filtro de polaridad TIRA. Un "0 contradicciones" con la red estrechada hoy no es
# el mismo que un "0" con la red de ayer: si no se publica lo descartado, el detector puede
# dejar de disparar para siempre y el store seguira pareciendo tranquilo.
DESCARTADOS = []


def _niega_lo_mismo(texto, terminos):
    """¿Este texto NIEGA estos terminos? Se usa para mirar la polaridad de los DOS lados."""
    t = " " + re.sub(r"\s+", " ", (texto or "").lower()) + " "
    for n in NIEGA:
        i = t.find(n)
        while i >= 0:
            if tokens(t[i + len(n): i + len(n) + 60]) & terminos:
                return True
            i = t.find(n, i + 1)
    return False


def _contradice(hallazgo, terminos_del_claim, texto_del_claim=""):
    """UNA PALABRA DE NEGACION NO ES UNA CONTRADICCION: hay que ver QUE niega.

    Medido 2026-08-25: esta funcion no existia y bastaba con que el hallazgo contuviera "no
    es" para publicar CONTRADICE. Asi salieron dos falsos sobre ZRFC_FMR_CREATE -- el hallazgo
    decia "817 llamadas desde HQ-ORION-EAI01/03/04. No es batch input", que niega el CANAL
    batch input, no el claim; de hecho lo CONFIRMA. Publicado como CONTRADICE, el hallazgo mas
    valioso del store ("un minero niega un claim") queda enterrado bajo ruido.

    Es el mismo defecto que A34 acababa de corregir el mismo dia -- decidir un veredicto por
    coincidencia de subcadena -- y por eso aqui hay funcion y no un `any(...)` en linea: lo
    inline no se puede gatear.

    Solo cuenta como contradiccion si lo negado es algo que el claim AFIRMA: se mira la ventana
    de palabras que sigue a la negacion y se exige que toque el vocabulario del claim.
    Devuelve (bool, que_niega) para que la propuesta pueda decir en que se apoya.
    """
    t = " " + re.sub(r"\s+", " ", (hallazgo or "").lower()) + " "
    for n in NIEGA:
        i = t.find(n)
        while i >= 0:
            ventana = tokens(t[i + len(n): i + len(n) + 60])
            comun = ventana & terminos_del_claim
            if comun:
                # HAY QUE MIRAR LA POLARIDAD DE LOS DOS LADOS. Si el claim niega LO MISMO, los
                # dos estan de acuerdo y llamarlo contradiccion es exactamente al reves.
                # Medido: el claim 581 dice que ORION escribe por RFC "y no es batch input", y
                # el hallazgo dice "817 llamadas... No es batch input". Coinciden. Con la
                # ventana sola seguia saliendo CONTRADICE, que es el hallazgo mas valioso del
                # store enterrado bajo su propio ruido.
                if _niega_lo_mismo(texto_del_claim, comun):
                    DESCARTADOS.append(f"'{n}' + {sorted(comun)[:3]}: el claim niega lo mismo")
                    return False, None
                return True, f"'{n}' seguido de {sorted(comun)[:4]}, que el claim afirma"
            i = t.find(n, i + 1)
    return False, None


def cargar(p, d=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return d if d is not None else {}


def tokens(t):
    return {w for w in re.split(r"\W+", (t or "").upper())
            if len(w) > 3 and not w.isdigit()}


def proponer():
    """El camino de vuelta, COMO FUNCION — no atrapado dentro de main().

    Mientras esto vivia solo en `main()`, la unica forma de usarlo era lanzar el script a mano.
    El gate lo midio: A38 estaba registrado como capacidad y ningun otro artefacto nombraba su
    script, asi que la fase 5 de la cadena lo declaraba en `orchestration.json` y no lo llamaba.
    Una capacidad que nadie puede invocar desde codigo no es una capacidad, es un recordatorio.

    Devuelve el documento de propuestas (y lo escribe), o None si faltan insumos.
    """
    C = cargar(CLAIMS, [])
    if isinstance(C, dict):
        C = C.get("claims") or []
    H = (cargar(BUS) or {}).get("hallazgos") or []
    if not C or not H:
        return None

    # Indice por SUJETO: un hallazgo habla de un objeto concreto, y un claim que lo nombra en
    # `related_objects` es candidato. Cruzar por texto libre daria ruido; cruzar por objeto es
    # lo que el grafo ya sabe hacer.
    por_sujeto = {}
    for h in H:
        por_sujeto.setdefault(str(h.get("sujeto", "")).upper(), []).append(h)

    props = []
    for c in C:
        if str(c.get("status") or "").upper() not in ("OPEN", "", "NONE"):
            continue
        objs = [str(o).upper() for o in (c.get("related_objects") or [])]
        golpes = []
        for o in objs:
            golpes.extend(por_sujeto.get(o, []))
        if not golpes:
            continue
        texto = str(c.get("claim") or "")
        tc = tokens(texto)
        abierto = any(p in texto.lower() for p in PREGUNTA)
        for h in golpes:
            th = tokens(h.get("hallazgo"))
            solape = len(tc & th)
            if solape < 3:
                continue
            niega, niega_a = _contradice(str(h.get("hallazgo")), tc, texto)
            props.append({
                "claim_id": c.get("id"),
                "claim": texto[:180],
                "sujeto": h.get("sujeto"),
                "minero": h.get("minero"),
                "hallazgo": str(h.get("hallazgo"))[:180],
                "autoridad": h.get("autoridad"),
                "solape_de_terminos": solape,
                "propuesta": ("CONTRADICE" if niega else
                              "RESUELVE" if abierto else "REFUERZA"),
                "_en_que_se_apoya": (
                    f"NEGACION QUE TOCA EL CLAIM: {niega_a}" if niega else
                    "el claim contiene una marca de pregunta abierta y el hallazgo la solapa"
                    if abierto else
                    f"solape de {solape} termino(s) con el hallazgo -- solo eso"),
                "_hay_que_leerlo": ("una coincidencia de terminos NO es una respuesta: hay que "
                                    "leer si el hallazgo contesta la pregunta del claim o solo "
                                    "se le parece"),
            })

    props.sort(key=lambda p: (-{"CONTRADICE": 2, "RESUELVE": 1, "REFUERZA": 0}[p["propuesta"]],
                              -p["solape_de_terminos"]))
    doc = {
        "_que_es": ("claims ABIERTOS para los que un minero ya publico evidencia. El camino de "
                    "ida -- minero, bus, grafo, companion -- existia entero; este es el de "
                    "vuelta, que no existia"),
        "_propone_no_cierra": (
            "cerrar un claim es un JUICIO: hay que leer si la evidencia contesta la pregunta o "
            "solo se le parece. Un cierre automatico por coincidencia de palabras da por sabido "
            "lo que no lo esta, y eso es peor que dejarlo abierto: un claim abierto se mira, uno "
            "cerrado en falso no se vuelve a mirar nunca"),
        "_lo_mas_valioso_es_CONTRADICE": (
            "un claim que un minero NIEGA vale mas que uno que confirma: es conocimiento que "
            "esta enseñando lo que ya no es verdad, y nadie lo sabe"),
        "claims_abiertos": sum(1 for c in C
                               if str(c.get("status") or "").upper() in ("OPEN", "", "NONE")),
        "hallazgos_en_el_bus": len(H),
        "por_tipo": dict(Counter(p["propuesta"] for p in props)),
        "_lo_que_el_filtro_de_polaridad_descarto": {
            "_que_es": ("cruces que la version anterior habria publicado como CONTRADICE y que "
                        "no lo son: el hallazgo niega LO MISMO que el claim niega, o sea que "
                        "estan de acuerdo"),
            "_por_que_se_publica": ("un '0 contradicciones' con la red estrechada hoy no es el "
                                    "mismo que un '0' de ayer. Sin esta cuenta el detector "
                                    "podria dejar de disparar para siempre sin que se note"),
            "n": len(DESCARTADOS),
            "casos": DESCARTADOS[:10],
        },
        "propuestas": props[:80],
        "_quien_decide": "el agente `mining-arbiter`, o `brain-steward` al promover",
    }
    SALIDA.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return doc


def main():
    doc = proponer()
    if doc is None:
        print("faltan claims o hallazgos")
        return 1
    props, H = doc["propuestas"], range(doc["hallazgos_en_el_bus"])

    if "--json" in sys.argv:
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        return 0
    print(f"[circulo] {doc['claims_abiertos']} claims abiertos · {len(H)} hallazgos en el bus")
    print(f"  {len(props)} cruce(s): {doc['por_tipo']}")
    for p in props[:12]:
        print(f"\n  [{p['propuesta']}] claim {p['claim_id']} · {p['sujeto']} "
              f"({p['minero'].split('/')[0]})")
        print(f"      claim   : {p['claim'][:110]}")
        print(f"      hallazgo: {p['hallazgo'][:110]}")
    print(f"\n-> {SALIDA}")
    print("  PROPONE, no cierra: leer si contesta la pregunta o solo se le parece.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
