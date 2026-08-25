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

    # ⛔ NO SE PUEDE PUBLICAR SIN VER LO QUE YA DIJERON LOS DEMAS.
    #
    # Medido 2026-08-25: 235 hallazgos de 9 mineros, y solo UNO llamaba a `consultar()` -- que
    # ademas tiraba el resultado con un `if otros: pass`. Cero preguntas en el foro. Era un
    # tablon de anuncios con una discusion, no una colaboracion.
    #
    # Pedirle a cada minero que se acuerde de consultar no funciona: se olvida, y el que lo
    # hace tira el resultado. Asi que la consulta va DENTRO de publicar: quien publica se
    # encuentra con lo que otros dijeron del mismo sujeto, adjunto a su propio hallazgo. La
    # colaboracion por construccion, no por disciplina.
    _fam = str(minero).split("/")[0]
    _otros = [h for h in H
              if h.get("sujeto") == str(sujeto).upper()
              and str(h.get("minero", "")).split("/")[0] != _fam]
    _contexto = None
    if _otros:
        _mejor = sorted(_otros, key=lambda h: -h.get("peso", 0))[:2]
        _contexto = [{"minero": h["minero"], "autoridad": h.get("autoridad"),
                      "dijo": str(h.get("hallazgo"))[:140]} for h in _mejor]

    clave = (str(minero), str(sujeto).upper(), asp)
    H[:] = [h for h in H
            if (h.get("minero"), str(h.get("sujeto", "")).upper(),
                str(h.get("aspecto") or h.get("mining_kind"))) != clave]
    H.append({"minero": minero, "mining_kind": tipo, "aspecto": asp,
              "sujeto": str(sujeto).upper(),
              "hallazgo": hallazgo, "evidencia": evidencia,
              "autoridad": autoridad, "peso": AUTORIDAD.get(autoridad, 1), "sesion": sesion,
              # Lo que OTROS ya dijeron de este sujeto, adjunto. Que el desacuerdo viaje con el
              # hallazgo es lo que hace que se vea donde alguien lo va a leer.
              "ya_dicho_por_otros": _contexto})
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


def preguntar(minero, sujeto, pregunta, para=None, porque=""):
    """DEJA UNA PREGUNTA ABIERTA para otro minero. Es la mitad que faltaba del bus.

    Publicar y leer hace un TABLON DE ANUNCIOS. Una conversacion necesita que A pueda decir "yo
    llego hasta aqui; esto lo sabe quien mire USR02" y que B lo vea y conteste. Sin esto, cada
    minero se para en su limite y el limite del vecino nunca se cruza con el suyo.

    `para` puede ser un minero concreto o un mining_kind ("CANAL_Y_ACTOR"): normalmente quien
    pregunta sabe QUE TIPO de mineria resuelve su duda, no quien la hace.
    """
    d = _cargar()
    P = d.setdefault("preguntas", [])
    clave = (minero, str(sujeto).upper(), pregunta[:80])
    P[:] = [q for q in P
            if (q.get("de"), str(q.get("sujeto", "")).upper(), str(q.get("pregunta"))[:80])
            != clave]
    P.append({"de": minero, "para": para or "CUALQUIERA", "sujeto": str(sujeto).upper(),
              "pregunta": pregunta, "porque_no_puedo_yo": porque, "respuestas": []})
    BUS.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(P)


def responder(minero, sujeto, respuesta, evidencia="", autoridad="MEDIDO_EN_DATOS"):
    """Contesta las preguntas abiertas sobre un sujeto. Devuelve cuantas contesto."""
    d = _cargar()
    s, n = str(sujeto).upper(), 0
    for q in d.get("preguntas", []):
        if q.get("sujeto") != s:
            continue
        if q.get("de") == minero:
            continue                      # no te contestas a ti mismo
        q.setdefault("respuestas", []).append(
            {"de": minero, "respuesta": respuesta, "evidencia": evidencia,
             "autoridad": autoridad, "peso": AUTORIDAD.get(autoridad, 1)})
        n += 1
    if n:
        BUS.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    return n


def pendientes(para=None):
    """Preguntas que NADIE ha contestado. Es la lista de trabajo del proximo minero."""
    out = []
    for q in _cargar().get("preguntas", []):
        if q.get("respuestas"):
            continue
        if para and q.get("para") not in (para, "CUALQUIERA"):
            continue
        out.append(q)
    return out


def auto_resolver():
    """Resuelve los choques que la JERARQUIA DE EVIDENCIA decide sola, y solo esos.

    Un campo que SAP declara vence a una heuristica sobre comportamiento: eso no es opinion, es
    regla, y una regla se puede aplicar. Pero DOS MEDIDAS DEL MISMO PESO no se votan -- se
    miran, y eso es juicio: se dejan marcadas para un humano o un agente.

    Nunca borra al perdedor. Un choque sin su version anterior no se puede auditar, y ademas el
    choque suele valer mas que cualquiera de los dos hallazgos por separado.
    """
    d = _cargar()
    resueltos, para_juicio = [], []
    por_sujeto = {}
    for h in d["hallazgos"]:
        por_sujeto.setdefault((h["sujeto"], h.get("aspecto") or h.get("mining_kind")), []).append(h)
    for (suj, asp), hs in por_sujeto.items():
        # UN MINERO HABLANDO CONSIGO MISMO NO ES UN DESACUERDO. La cadena publica bajo
        # A29_discovery_chain/<fuente>, asi que el mismo hallazgo visto por dos de sus fuentes
        # aparecia como 49 "choques para juicio" que no lo eran. Se compara por FAMILIA -- lo
        # que hay antes de la barra -- y se exige que sean dos mineros DISTINTOS.
        familias = {str(h["minero"]).split("/")[0] for h in hs}
        if len(familias) < 2:
            continue
        if len({h.get("hallazgo") for h in hs}) < 2:
            continue        # dicen LO MISMO: eso es una confirmacion, no un choque
        pesos = sorted({h.get("peso", 1) for h in hs}, reverse=True)
        if len(pesos) > 1:
            gana = max(hs, key=lambda h: h.get("peso", 1))
            for h in hs:
                if h is gana:
                    h["_arbitraje"] = "GANA: fuente mas autoritativa"
                else:
                    h["_arbitraje"] = (f"SUPERSEDED por {gana['minero']} "
                                       f"({gana['autoridad']}). Se conserva: un choque sin su "
                                       "version anterior no se puede auditar")
            resueltos.append({"sujeto": suj, "aspecto": asp, "gana": gana["minero"],
                              "autoridad": gana["autoridad"]})
        else:
            for h in hs:
                h["_arbitraje"] = ("EMPATE de autoridad: dos medidas del mismo peso NO se votan. "
                                   "Hace falta mirar, y eso es juicio")
            para_juicio.append({"sujeto": suj, "aspecto": asp,
                                "mineros": [h["minero"] for h in hs]})
    BUS.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    return resueltos, para_juicio


def colaborar():
    """ENSENAR A COLABORAR A TODOS, SIN QUE CADA UNO SE ACUERDE.

    Medido 2026-08-25: 235 hallazgos de 9 mineros y CERO preguntas. Publicar sale solo -- es
    el resultado del trabajo -- pero preguntar y contestar exige acordarse, y nadie se acuerda.

    La salida es que cada minero YA DECLARA lo que no puede hacer: `ask.py` guarda por minero
    un campo `lo_que_NO_puede` y una `trampa`. Eso es literalmente una pregunta abierta escrita
    en otro sitio. Aqui se convierte en pregunta del foro, dirigida al TIPO de mineria que
    podria contestarla, y con el "por que no puedo yo" que hace que otro la pueda tomar.

    Y del otro lado: quien declara que RESPONDE a algo, encuentra las preguntas que casan con
    lo que sabe. La colaboracion deja de depender de la disciplina de cada uno.
    """
    try:
        sys.path.insert(0, str(REPO / "process_mining"))
        from ask import CAPACIDADES  # type: ignore
    except Exception:
        return 0, 0

    sembradas = 0
    for c in CAPACIDADES:
        limite = str(c.get("lo_que_NO_puede") or "").strip()
        if not limite or limite == "-":
            continue
        # A quien va: al tipo de mineria del que la sabria contestar, no a un minero concreto
        # -- quien pregunta no tiene por que saber quien tiene la respuesta.
        sembradas += 1 if preguntar(
            c["algoritmo"], f"LIMITE:{c['algoritmo']}",
            f"lo que este minero NO puede: {limite[:220]}",
            para="CUALQUIERA",
            porque=f"limite declarado de su instrumento. Trampa asociada: "
                   f"{str(c.get('trampa'))[:150]}") else 0

    # Emparejar: quien declara que RESPONDE a algo, ve lo que le toca
    abiertas = pendientes()
    emparejadas = 0
    for q in abiertas:
        texto = (str(q.get("pregunta", "")) + " " + str(q.get("sujeto", ""))).lower()
        for c in CAPACIDADES:
            if c["algoritmo"] == q.get("de"):
                continue
            for r in c.get("responde", []):
                pal = [w for w in r.lower().split() if len(w) > 4]
                if pal and sum(1 for w in pal if w in texto) >= max(2, len(pal) // 3):
                    q.setdefault("_podria_contestar", [])
                    if c["algoritmo"] not in q["_podria_contestar"]:
                        q["_podria_contestar"].append(c["algoritmo"])
                        emparejadas += 1
                    break
    if emparejadas:
        d = _cargar()
        idx = {(x.get("de"), x.get("sujeto"), str(x.get("pregunta"))[:60]): x
               for x in d.get("preguntas", [])}
        for q in abiertas:
            k = (q.get("de"), q.get("sujeto"), str(q.get("pregunta"))[:60])
            if k in idx and q.get("_podria_contestar"):
                idx[k]["_podria_contestar"] = q["_podria_contestar"]
        BUS.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    return sembradas, emparejadas


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "colaborar":
        s, e = colaborar()
        print(f"{s} limite(s) declarados convertidos en preguntas del foro")
        print(f"{e} emparejamiento(s): una pregunta y quien podria contestarla\n")
        for q in pendientes():
            quien = ", ".join(q.get("_podria_contestar") or []) or "NADIE declara saberlo"
            print(f"  [{q['de']}] {str(q['sujeto'])[:30]}")
            print(f"      {str(q['pregunta'])[:100]}")
            print(f"      podria contestar: {quien}")
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "resolver":
        res, jui = auto_resolver()
        print(f"{len(res)} choque(s) resueltos por jerarquia de evidencia:")
        for r in res[:20]:
            print(f"  {r['sujeto']:24s} gana {r['minero'] if 'minero' in r else r['gana']:34s} "
                  f"({r['autoridad']})")
        print(f"\n{len(jui)} para JUICIO (dos medidas del mismo peso, no se votan):")
        for j in jui[:20]:
            print(f"  {j['sujeto']:24s} {', '.join(j['mineros'])[:80]}")
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "pendientes":
        ps = pendientes()
        print(f"{len(ps)} pregunta(s) sin contestar:")
        for q in ps[:25]:
            print(f"  [{q['de']} -> {q['para']}] {q['sujeto']}: {q['pregunta'][:90]}")
            if q.get("porque_no_puedo_yo"):
                print(f"      no puedo yo porque: {q['porque_no_puedo_yo'][:100]}")
        return 0
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
