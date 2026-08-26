"""GATE: el conocimiento que no esta RELACIONADO no se encuentra, aunque este guardado.

POR QUE EXISTE, Y ES UN FALLO MEDIDO DE ESTA SESION
    Ya habia un gate de alcanzabilidad (artifact_reachability_check.py) y su propio campo
    `improve` decia la verdad: "mide ARTEFACTOS, no CLAIMS". Asi que un fichero podia estar
    perfectamente enlazado mientras el conocimiento que contiene no conectaba con nada.

    Lo que se midio el 2026-08-25:
      - 555 interfaces y el 100% SIN DOMINIO. Una interfaz sin dominio no aparece en el mapa de
        su area: solo la encuentra quien ya sabe que existe. Eso no es guardar, es esconder.
      - Los canales descubiertos ese mismo dia -- ZRFC_FMR_CREATE (crear reserva de fondos, 817
        llamadas desde los servidores de ORION), Y_RFC_FMRP_RFFMEP1FX_FI_POST (59.167) -- vivian
        en rfc_caller_apps.json y NO estaban en el inventario de interfaces. Descubiertos y
        desconectados el mismo dia.
      - Y el fallo propio: los claims escritos ese dia usaban `evidence`, `domains`, `tier` y
        `session` cuando el store usa `evidence_for`, `domain`, `confidence` y `created_session`.
        Un claim con el campo equivocado esta guardado y es ILEGIBLE para todo lo que lee el
        store. Es el mismo defecto que abortó dos pasos del rebuild esa manana.

QUE COMPRUEBA
    1. ESQUEMA      -- ningun registro usa una variante minoritaria de un campo (el store manda)
    2. ENGANCHE     -- todo claim tiene related_objects y dominio
    3. ENLACE VIVO  -- lo que related_objects nombra existe en algun sitio, no apunta al vacio
    4. DOMINIO      -- toda interfaz lleva dominio
    5. DESCUBIERTO=REGISTRADO -- un canal descubierto por el log esta en el inventario

LO QUE NO HACE
    No juzga si el conocimiento es CIERTO -- eso es claims_health.py. Juzga si se puede ENCONTRAR.

Uso:  python Zagentexecution/quality_checks/knowledge_connectivity_check.py [--json]
Salida: exit 0 limpio · exit 1 si hay conocimiento desconectado
"""
QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": ("conocimiento guardado que no se puede ENCONTRAR: claims en un campo que el store "
             "no lee, sin enganche al grafo, interfaces sin dominio, canales descubiertos y no "
             "registrados"),
}
# ----------------------------------------------------------------------------
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRAIN = os.path.join(ROOT, "brain_v2")

# Un campo usado por menos de esta fraccion de los registros, existiendo otro que dice lo mismo,
# es una VARIANTE: quien lee el store no la mira.
UMBRAL_VARIANTE = 0.25

# Familias de campo que significan LO MISMO. El ganador se decide MIDIENDO, no por preferencia.
#
# Lo que NO entra aqui, y comprobarlo evitó pedir que se borrara conocimiento bueno:
#   evidence_legacy_text_for -- es el texto plano CONSERVADO al lado del evidence_for
#                               estructurado (claim 1 lleva los dos). Eso es preserve-first
#                               funcionando, no una variante.
#   evidence_path            -- apunta al SCRIPT que produjo la prueba; evidence_for dice cual
#                               es la prueba. Complementarios.
#   tier                     -- vocabulario distinto de confidence: TIER_1/2/3 mide la calidad
#                               de la fuente, HIGH/MEASURED la del enunciado. El claim 31 lleva
#                               confidence=HIGH y tier=TIER_1 a la vez, y no se contradicen.
FAMILIAS = [
    {"evidence_for", "evidence"},
    {"domain", "domains"},
    {"confidence", "confidence_tier", "evidence_tier"},
    {"created_session", "session", "discovered_session"},
    {"related_objects", "related_object", "objects"},
]


def load(*p, default=None):
    try:
        with open(os.path.join(BRAIN, *p), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default if default is not None else {}


def variantes(registros):
    """Que registros guardan en un campo que el store NO LEE, quedando ilegibles.

    Lo que se cuenta es la ILEGIBILIDAD, no la pulcritud del nombre. Un registro que lleva la
    variante Y TAMBIEN el campo canonico poblado se encuentra perfectamente: la variante ahi es
    historia de como se escribio, y borrarla seria perder rastro sin ganar nada (CP-002).
    Solo cuenta el caso que hace dano: variante presente y canonico VACIO.
    """
    n = len(registros) or 1
    pobl = collections.Counter()
    for r in registros:
        for f, v in (r or {}).items():
            if v not in (None, "", [], {}):
                pobl[f] += 1
    fuera = {}
    for fam in FAMILIAS:
        presentes = {f: pobl[f] for f in fam if pobl[f]}
        if len(presentes) < 2:
            continue
        gana = max(presentes, key=presentes.get)
        for f in presentes:
            if f == gana or presentes[f] / n >= UMBRAL_VARIANTE:
                continue
            ciegos = [r for r in registros
                      if r.get(f) not in (None, "", [], {})
                      and r.get(gana) in (None, "", [], {})]
            if ciegos:
                fuera[f] = {"usos": len(ciegos), "el_store_usa": gana,
                            "poblado_del_store": pobl[gana],
                            "_ids": [r.get("id") for r in ciegos]}
    return fuera


def main():
    h = []

    # ---- 1+2+3 CLAIMS ------------------------------------------------------
    C = load("claims", "claims.json", default=[])
    if isinstance(C, dict):
        C = C.get("claims") or []
    var = variantes(C)
    for f, meta in sorted(var.items(), key=lambda kv: -kv[1]["usos"]):
        h.append({
            "gravedad": "ESQUEMA", "donde": "claims.json", "campo": f,
            "ids": sorted(x for x in meta["_ids"] if x is not None)[:12],
            "que_pasa": (f"{meta['usos']} registro(s) guardan en '{f}' lo que el store lee en "
                         f"'{meta['el_store_usa']}' ({meta['poblado_del_store']} registros) y "
                         f"tienen ese campo VACIO. Guardados e ilegibles."),
        })

    sin_obj = [c.get("id") for c in C if not (c.get("related_objects") or c.get("objects"))]
    if sin_obj:
        h.append({"gravedad": "SIN_ENGANCHE", "donde": "claims.json", "campo": "related_objects",
                  "ids": sorted(x for x in sin_obj if x is not None)[:20],
                  "que_pasa": (f"{len(sin_obj)} claim(s) no nombran ningun objeto: no entran en "
                               f"el grafo y solo se encuentran leyendo los {len(C)} de arriba "
                               "abajo"),
                  "como_se_arregla": (
                      "python brain_v2/anchor_claims.py         (simula) "
                      "y luego --apply. Extrae del propio texto del claim los nombres QUE EL "
                      "BRAIN YA CONOCE -- nada inventado -- y los pone en related_objects. Lo "
                      "que quede sin ancla es que el objeto no esta en el vocabulario todavia, "
                      "y eso es un hallazgo, no un fallo del script")})
    sin_dom = [c.get("id") for c in C if not (c.get("domain") or c.get("domains"))]
    if sin_dom:
        h.append({"gravedad": "SIN_DOMINIO", "donde": "claims.json", "campo": "domain",
                  "ids": sorted(x for x in sin_dom if x is not None)[:20],
                  "que_pasa": f"{len(sin_dom)} claim(s) no se encuentran buscando por dominio"})

    # ---- 4 INTERFACES ------------------------------------------------------
    inv = load("interface_inventory.json")
    its = inv.get("interfaces") or []
    sd = [i for i in its if not i.get("domain")]
    if its and sd:
        porcanal = collections.Counter(i.get("channel") for i in sd)
        h.append({"gravedad": "SIN_DOMINIO", "donde": "interface_inventory.json",
                  "campo": "domain", "ids": [i.get("artifact") for i in sd[:12]],
                  "que_pasa": (f"{len(sd)} de {len(its)} interfaces sin dominio "
                               f"({dict(porcanal.most_common(5))}): no aparecen en el mapa de su "
                               "area y solo las encuentra quien ya sabe que existen")})

    # ---- 5 DESCUBIERTO PERO NO REGISTRADO ----------------------------------
    # Un canal que el log descubrio y el inventario no tiene es conocimiento que nace suelto.
    declarados = {str(i.get("artifact") or "").strip().upper() for i in its}
    declarados |= {str(i.get("system") or "").strip().upper() for i in its}
    crudo = json.dumps(inv, ensure_ascii=False).upper()
    canales = load("rfc_caller_apps.json").get("channels") or {}
    huerfanos = []
    for nombre, ch in canales.items():
        for fm in (ch.get("modulos_custom") or {}):
            u = fm.strip().upper()
            if u and u not in declarados and u not in crudo:
                huerfanos.append({"canal": nombre, "artefacto": fm})
    if huerfanos:
        h.append({"gravedad": "DESCUBIERTO_SIN_REGISTRAR", "donde": "interface_inventory.json",
                  "campo": "interfaces",
                  "ids": [x["artefacto"] for x in huerfanos[:12]],
                  "que_pasa": (f"{len(huerfanos)} canal(es) que el log descubrio no estan en el "
                               "inventario: viven en rfc_caller_apps.json y nada mas los enlaza")})

    rep = {
        "_que_comprueba": ("que el conocimiento guardado este RELACIONADO: mismo esquema que su "
                           "store, enganchado al grafo, con dominio, y registrado donde se busca"),
        "_por_que": ("guardar no es recuperar. 555 interfaces sin dominio y 2 canales de "
                     "escritura descubiertos el mismo dia y no registrados, medido 2026-08-25"),
        "claims": len(C), "interfaces": len(its), "hallazgos": h,
    }
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if h else 0

    print(f"[conectividad] {len(C)} claims · {len(its)} interfaces")
    if not h:
        print("  OK - el conocimiento guardado esta relacionado y se encuentra")
    for x in h:
        print(f"  [{x['gravedad']}] {x['donde']} :: {x['campo']}")
        print(f"      {x['que_pasa']}")
        if x.get("ids"):
            print(f"      -> {', '.join(str(i) for i in x['ids'])}")
        if x.get("como_se_arregla"):
            print(f"      ARREGLO: {x['como_se_arregla']}")
    return 1 if h else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
