"""
UN DESCUBRIMIENTO NO ES UN DATO QUE SE ARCHIVA: ES UN EVENTO QUE INTERROGA AL RESTO.

EL MODELO (JP, 2026-08-26)
    «Un nuevo conocimiento o descubrimiento agrega aristas, que pueden llevar a nuevas
    preguntas de todos. Basicamente es la naturaleza de la evolucion del conocimiento humano.»

    Un hallazgo no crece el grafo por el nodo -- crece por las ARISTAS. Y cada arista nueva
    puede invalidar, confirmar o poner en duda lo que otro instrumento daba por sabido. Ese
    segundo efecto es el que se pierde: el hallazgo se guarda en su store, y quien deberia
    repreguntarse algo no se entera nunca.

QUE HACIA FALTA Y QUE NO
    `process_mining/mining_bus.py` YA tiene `preguntar()` y `pendientes()`: los mineros pueden
    hablarse. Pero es MANUAL -- alguien tiene que acordarse. Esto es lo otro: dado un
    descubrimiento, DERIVA a quien le afecta y publica la pregunta en ese mismo bus. No crea un
    registro paralelo; usa el que hay.

COMO SE DERIVA "A QUIEN LE AFECTA"
    Por SUJETO COMPARTIDO, que es lo unico que se puede medir sin adivinar:
      * los instrumentos que operan sobre las mismas tablas o stores que el hallazgo
      * los claims que afirman algo sobre el mismo objeto
      * los mineros de la misma clase de mineria
    Y con una regla de honestidad: si no se puede derivar a nadie, NO se inventa un destinatario
    -- se dice que el hallazgo no tiene vecinos conocidos, que es en si un dato.

LOS TRES CASOS QUE LO MOTIVAN (2026-08-26, ninguno disparo pregunta alguna)
    * SBP es la cuarta maquina  -> "¿que otros destinos apuntan a maquinas que no estan en el
      paisaje?" para todo minero que lea rfcdes.
    * A61: el log es CIEGO al render Adobe -> "¿que otras cosas damos por muertas sin haber
      comprobado si dejan huella?" para TODO claim que diga 'no se usa'.
    * Las variantes por LISTA se degradan y las de RANGO no -> "¿que otra configuracion se
      mantiene a mano?" para DMEE, OB09 y los paneles BCM.
    Las tres preguntas las formulo un humano cuatro dias despues. Eso es lo que no escala.

Uso:
    python knowledge_propagation.py --claim 617
    python knowledge_propagation.py --nodo A61_capability_footprint_in_log
    python knowledge_propagation.py --pendientes
"""
import argparse
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)


def cargar(p, d=None):
    fp = os.path.join(REPO, p)
    try:
        return json.load(io.open(fp, encoding="utf-8"))
    except Exception:
        return d if d is not None else {}


# Un descubrimiento cambia lo que otros dan por sabido de tres maneras, y cada una tiene su
# pregunta. No son plantillas de adorno: cada una nacio de un caso real que NO se pregunto.
FORMAS = {
    "EXISTE_ALGO_QUE_NO_ESTABA": (
        "¿que otros {clase} hay que tampoco esten registrados?",
        "un objeto nuevo en un registro implica que el registro estaba incompleto, y casi nunca "
        "por uno solo"),
    "EL_INSTRUMENTO_ES_CIEGO": (
        "¿que otras cosas damos por {conclusion} sin haber comprobado si el instrumento las ve?",
        "una frontera del instrumento invalida TODA conclusion sacada de su silencio, no solo "
        "la del caso"),
    "UN_MODO_SE_DEGRADA": (
        "¿que otra cosa se mantiene del mismo modo y por tanto se degrada igual?",
        "un modo de mantenimiento no es propiedad del objeto que lo destapo: es una clase"),
}


# Un claim esta escrito en prosa CON ENFASIS EN MAYUSCULAS, asi que "toda palabra en mayuscula
# es un objeto SAP" es falso y ruidoso: la primera version saco CERO, SOLO, DATOS y PARA como si
# fueran tablas, y con eso 47 instrumentos salian "afectados" casi todos por ruido. Un sujeto
# tiene FORMA: lleva digito, guion bajo, barra o punto -- como SKB1, T030H, RFC_READ_TABLE,
# A61_capability_footprint_in_log, /CGI_XML_CT_UNESCO. Una palabra en mayusculas sin ninguna de
# esas marcas es enfasis, no objeto.
_ENFASIS = re.compile(r"^[A-ZÁÉÍÓÚÑ]+$")


def _parece_objeto(x):
    if len(x) < 3 or _ENFASIS.match(x):
        return False
    return bool(re.search(r"[0-9_/.]", x))


def sujetos_del_claim(c):
    """De que habla un claim. `related_objects` es la fuente declarada y manda; del texto solo
    se aceptan tokens CON FORMA de objeto."""
    s = {x for x in (c.get("related_objects") or []) if isinstance(x, str)}
    txt = c.get("claim", "")
    s |= {x for x in re.findall(r"\b[A-Z][A-Z0-9_]{3,}\b", txt) if _parece_objeto(x)}
    s |= set(re.findall(r"\b[A-Z]\d{1,3}_[a-z_]+\b", txt))         # algoritmos
    s |= set(re.findall(r"\b[a-z_]+\.py\b", txt))                  # instrumentos
    return {x for x in s if _parece_objeto(x)}


def afectados(sujetos):
    """Quien mas habla de esos sujetos. Solo evidencia: aparecer en su definicion."""
    out = {}
    algos = cargar("brain_v2/methods/algorithms.json").get("algorithms", {})
    for k, v in algos.items():
        t = json.dumps(v, ensure_ascii=False)
        comun = sorted(x for x in sujetos if re.search(r"\b%s\b" % re.escape(x), t))
        if comun:
            out[k] = comun
    tg = cargar("brain_v2/toolgraph.json")
    for n in (tg.get("nodos") or {}).values():
        if not isinstance(n, dict) or n.get("tipo") not in ("AGENTE", "GATE", "SKILL"):
            continue
        t = json.dumps(n, ensure_ascii=False)
        comun = sorted(x for x in sujetos if re.search(r"\b%s\b" % re.escape(x), t))
        if comun:
            out.setdefault(n["nombre"], comun)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim", type=int)
    ap.add_argument("--nodo")
    ap.add_argument("--forma", choices=sorted(FORMAS), default=None)
    ap.add_argument("--publicar", action="store_true",
                    help="publicar de verdad en el bus (por defecto solo muestra)")
    ap.add_argument("--pendientes", action="store_true")
    a = ap.parse_args()

    if a.pendientes:
        from mining_bus import pendientes
        pendientes()
        return 0

    if a.claim:
        cl = cargar("brain_v2/claims/claims.json", [])
        c = next((x for x in cl if str(x.get("id")) == str(a.claim)), None)
        if not c:
            print("no existe el claim %s" % a.claim)
            return 2
        origen, sujetos = "claim %s" % a.claim, sujetos_del_claim(c)
        titulo = c["claim"][:120]
    elif a.nodo:
        tg = cargar("brain_v2/toolgraph.json")
        n = (tg.get("nodos") or {}).get(a.nodo)
        if not n:
            print("no existe el nodo %s" % a.nodo)
            return 2
        origen, titulo = a.nodo, str(n.get("tipo"))
        sujetos = {a.nodo} | set(re.findall(r"\b[A-Z][A-Z0-9_]{3,}\b",
                                            json.dumps(n, ensure_ascii=False)))
    else:
        ap.error("da --claim o --nodo")

    print("DESCUBRIMIENTO: %s" % origen)
    print("   %s\n" % titulo)
    print("SUJETOS DE LOS QUE HABLA: %s\n" % ", ".join(sorted(sujetos)[:12]))

    vecinos = afectados(sujetos)
    vecinos.pop(a.nodo, None)
    if not vecinos:
        print("SIN VECINOS CONOCIDOS. No se inventa destinatario: que un hallazgo no toque a")
        print("nadie es en si un dato -- o el sujeto es nuevo del todo, o esta mal nombrado.")
        return 0

    print("A QUIEN LE AFECTA — %d instrumentos comparten sujeto:" % len(vecinos))
    for k, comun in sorted(vecinos.items(), key=lambda x: -len(x[1]))[:15]:
        print("   %-42s por: %s" % (k, ", ".join(comun[:4])))

    if a.forma:
        pregunta, porque = FORMAS[a.forma]
        print("\nPREGUNTA QUE PROPAGA (%s):" % a.forma)
        print("   %s" % pregunta)
        print("   porque: %s" % porque)
        if a.publicar:
            from mining_bus import preguntar
            for k in sorted(vecinos)[:15]:
                preguntar("knowledge_propagation", origen, pregunta, para=k, porque=porque)
            print("\n   publicada a %d instrumentos en el bus" % min(15, len(vecinos)))
        else:
            print("\n   (no publicada — anade --publicar)")
    else:
        print("\nDa --forma para propagar la pregunta: %s" % ", ".join(sorted(FORMAS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
