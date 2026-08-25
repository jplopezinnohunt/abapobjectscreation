"""EL SITIO DONDE LOS MINEROS SE HABLAN.

POR QUE EXISTE
    Cada minero escribia su hallazgo en su propio JSON y ninguno leia el del vecino. Con eso,
    dos cosas se perdian: la CONFIRMACION -- dos mineros distintos llegando a lo mismo por
    caminos distintos es mucho mas fuerte que uno solo -- y sobre todo la CONTRADICCION.

    Y la contradiccion es donde estaba el hallazgo grande del 2026-08-25. A23, que descubre
    canales por trafico, concluyo que `E_SILVA` era un canal y no una persona. `USR02-USTYP`
    decia tipo A: una PERSONA. Las dos observaciones eran correctas. Lo que las reconcilia
    -- la cuenta de una persona conducida por una aplicacion, que hereda todos sus permisos --
    es el hallazgo H71, y no lo produjo ningun minero: lo produjo el CHOQUE entre dos.

    Sin un sitio comun, ese choque solo ocurre si la misma conversacion casualmente mira las
    dos cosas a la vez. Eso no es un metodo, es suerte.

COMO SE USA, DESDE CUALQUIER MINERO

    from mining_bus import publicar, consultar

    # antes de concluir sobre un sujeto, pregunta que saben los demas
    for otro in consultar("E_SILVA"):
        print(otro["minero"], otro["hallazgo"])

    # y publica lo tuyo, con la evidencia
    publicar("A23_channel_discovery_by_traffic", "CANAL_Y_ACTOR", "E_SILVA",
             "entra por RFC desde HQ-ORION-EAI01: es un canal",
             evidencia="rsau_audit_history: 11.767 logons RFC vs 603 de dialogo")

REGLA DE ORO
    Publicar NO es concluir. Un hallazgo publicado es una observacion de UN minero con SU
    evidencia. Cuando dos chocan, gana el que tiene la fuente mas AUTORITATIVA -- un campo que
    SAP declara vence a una heuristica sobre comportamiento -- y el choque se guarda, porque
    normalmente el choque vale mas que cualquiera de los dos por separado.
"""
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUS = REPO / "process_mining" / "mining_findings.json"

# Que fuente vence cuando dos mineros se contradicen. No es jerarquia de algoritmos: es
# jerarquia de EVIDENCIA.
AUTORIDAD = {
    "DECLARADO_POR_SAP": 4,     # un campo de una tabla estandar: USR02-USTYP, TADIR, TDEVC
    "MEDIDO_EN_DATOS": 3,       # contado sobre filas reales
    "DERIVADO": 2,              # calculado a partir de lo anterior
    "HEURISTICA": 1,            # deducido del comportamiento o del nombre
}


def _cargar():
    try:
        return json.loads(BUS.read_text(encoding="utf-8"))
    except Exception:
        return {"_que_es": ("hallazgos de los mineros, en un sitio comun para que puedan "
                            "confirmarse y contradecirse. La contradiccion suele valer mas "
                            "que cualquiera de los dos hallazgos por separado"),
                "_lee_esto_antes_de_concluir": "consultar(sujeto)",
                "hallazgos": []}


def publicar(minero, tipo, sujeto, hallazgo, evidencia="", autoridad="MEDIDO_EN_DATOS",
             sesion=None, aspecto=None):
    """Deja un hallazgo en el bus.

    Sustituye el anterior del MISMO minero sobre el MISMO sujeto Y EL MISMO ASPECTO -- un minero
    se corrige a si mismo -- pero nunca el de otro minero: ahi lo que hay es un choque, y el
    choque se conserva porque suele valer mas que los dos hallazgos por separado.

    El `aspecto` hizo falta al primer uso: A27 publico sobre MULESOFT que es una cuenta de
    SISTEMA y que el 89,9% de lo que mueve es PS. Son dos cosas distintas del mismo sujeto y la
    segunda borro a la primera, dejando el choque con A23 apuntando al hallazgo equivocado.
    Sin aspecto, un minero solo puede saber UNA cosa de cada sujeto.
    """
    d = _cargar()
    H = d["hallazgos"]
    asp = str(aspecto or tipo)
    clave = (str(minero), str(sujeto).upper(), asp)
    H[:] = [h for h in H
            if (h.get("minero"), str(h.get("sujeto", "")).upper(),
                str(h.get("aspecto") or h.get("mining_kind"))) != clave]
    H.append({"minero": minero, "mining_kind": tipo, "aspecto": asp,
              "sujeto": str(sujeto).upper(),
              "hallazgo": hallazgo, "evidencia": evidencia,
              "autoridad": autoridad, "peso": AUTORIDAD.get(autoridad, 1), "sesion": sesion})
    BUS.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(H)


def consultar(sujeto):
    """Que saben YA los demas mineros de este sujeto. Llamalo ANTES de concluir."""
    s = str(sujeto).upper()
    return sorted([h for h in _cargar()["hallazgos"] if h.get("sujeto") == s],
                  key=lambda h: -h.get("peso", 0))


def choques():
    """Sujetos sobre los que dos mineros dicen cosas distintas.

    No se resuelven aqui automaticamente: se SACAN A LA LUZ. Un choque entre una heuristica y
    un campo declarado por SAP se resuelve solo -- gana el campo -- pero un choque entre dos
    medidas es una pregunta de verdad, y responderla suele ser el hallazgo.
    """
    por_sujeto = {}
    for h in _cargar()["hallazgos"]:
        por_sujeto.setdefault(h["sujeto"], []).append(h)
    out = []
    for s, hs in por_sujeto.items():
        if len({h["minero"] for h in hs}) < 2:
            continue
        pesos = {h.get("peso", 1) for h in hs}
        out.append({
            "sujeto": s,
            "mineros": [h["minero"] for h in hs],
            "hallazgos": [{"minero": h["minero"], "dice": h["hallazgo"],
                           "autoridad": h["autoridad"]} for h in hs],
            "resolucion": ("GANA LA FUENTE MAS AUTORITATIVA" if len(pesos) > 1
                           else "DOS MEDIDAS DEL MISMO PESO: hay que decidirlo mirando, no votando"),
        })
    return out


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "choques":
        c = choques()
        print(f"{len(c)} sujeto(s) con mas de un minero opinando")
        for x in c:
            print(f"\n  {x['sujeto']}  [{x['resolucion']}]")
            for h in x["hallazgos"]:
                print(f"    {h['minero']:34s} ({h['autoridad']:18s}) {h['dice'][:80]}")
        return 0
    if len(sys.argv) > 1:
        for h in consultar(sys.argv[1]):
            print(f"  {h['minero']:34s} ({h['autoridad']}) {h['hallazgo'][:90]}")
        return 0
    d = _cargar()
    H = d["hallazgos"]
    print(f"{len(H)} hallazgo(s) de {len({h['minero'] for h in H})} minero(s)")
    print(f"{len(choques())} sujeto(s) con mas de un minero opinando")
    print("uso: mining_bus.py <sujeto> | mining_bus.py choques")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
