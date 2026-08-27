"""EL MECANISMO DE COLABORACION — obligatorio, dentro de la corrida de cada minero.

POR QUE EXISTE
    El foro existia desde hace dias: 307 hallazgos publicados y 14 preguntas. UNA contestada.
    El operador lo corto en seco: «esto no sirve... ¡deben colaborar! O sea, tienes que crear
    el MECANISMO de colaboracion. Si no, no colaboraran. Ellos tienen que SABER que deben
    colaborar».

    Y tiene razon en las dos mitades:

    (1) UNA PREGUNTA A "CUALQUIERA" ES UNA PREGUNTA A NADIE. 11 de las 14 estaban dirigidas al
        aire, y ninguna se contesto. El enrutador de capacidades (ask.py) ya sabia quien podia
        contestar cada tema: teniamos el buzon y no repartiamos el correo.

    (2) PUBLICAR NO ES COLABORAR, Y LEER TAMPOCO SI ES OPCIONAL. `pendientes()` existia y
        ningun minero la llamaba al terminar. Un mecanismo que depende de que alguien se
        acuerde no es un mecanismo: es una costumbre, y las costumbres se pierden entre
        sesiones. Por eso esto NO es una funcion que se puede llamar: es una que hay que
        llamar, y una puerta que falla si no se llamo.

LO QUE HACE, EN LA CORRIDA DE CADA MINERO
    cerrar_colaborando(minero, puedo_contestar) — se llama AL TERMINAR, siempre:
      1. REPARTE sus propias preguntas sin destinatario al minero que declara esa capacidad.
      2. Le enseña las preguntas ABIERTAS que EL puede contestar, segun lo que ask.py dice que
         sabe -- no segun lo que crea.
      3. Registra que este minero PASO por el foro. Sin ese registro, la puerta
         mining_collaboration_check no puede distinguir «no habia nada que contestar» de
         «no miro».

    La respuesta la da el minero con SUS datos: aqui no se contesta por el. Un enrutado sin
    respuesta seria teatro, y una respuesta automatica sin mirar datos seria peor.

Uso desde un minero:
    from colaborar import cerrar_colaborando
    cerrar_colaborando("A33_variant_content_mining",
                       puedo_contestar=lambda p: mi_respuesta_o_None(p))
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUS = os.path.join(REPO, "process_mining", "mining_findings.json")
PASO = os.path.join(REPO, "process_mining", "colaboracion_state.json")

_TOPE = {"the", "que", "una", "los", "las", "por", "con", "del", "para", "este", "esta",
         "como", "mas", "sobre", "puede", "hace", "solo", "todo", "cada", "sin", "son"}


def _tok(t):
    return {w for w in re.split(r"\W+", str(t or "").lower())
            if len(w) > 3 and w not in _TOPE}


def _capacidades():
    """QUIEN SABE DE QUE — del GRAFO ENTERO, no de los once del catalogo.

    ⛔ ARREGLADO 2026-08-26. `ask.py` cataloga 11 mineros a mano, y el repartidor solo miraba
    ahi. El grafo de herramientas tiene 226 nodos: 79 algoritmos y 13 agentes. Por esa mirilla,
    DOS preguntas llevaban semanas sin destinatario teniendo la respuesta escrita:

      A19 pregunto «no puedo decir QUE HACE un objeto» -- y la capa de codigo del brain
          (code_interpretation.json, graph_queries.py code, A9_business_rules_from_source)
          contesta justo eso. Ninguno de los 11 lee fuente.
      A30 pregunto «no puedo arbitrar» -- y la respuesta NO ES UN MINERO: es el agente
          `mining-arbiter`, que existe para exactamente eso. El repartidor no sabia que
          existieran agentes.

    Las dos se quedaron abiertas por como buscabamos, no por lo que sabemos. El catalogo a mano
    se queda corto en cuanto alguien registra algo nuevo -- que es lo que pasa cada sesion.
    """
    caps = {}
    # 1) el catalogo a mano: sigue valiendo, dice lo que cada minero responde EN CRISTIANO
    sys.path.insert(0, os.path.join(REPO, "process_mining"))
    try:
        from ask import CAPACIDADES
        caps.update({c["algoritmo"]: " ".join(str(x) for x in c.get("responde", [])).lower()
                     for c in CAPACIDADES if c.get("algoritmo")})
    except Exception:
        pass
    # 2) TODOS los algoritmos registrados: su `does` es su capacidad declarada
    try:
        with open(os.path.join(REPO, "brain_v2", "methods", "algorithms.json"),
                  encoding="utf-8") as fh:
            for k, v in (json.load(fh).get("algorithms") or {}).items():
                if k in caps:
                    continue
                caps[k] = " ".join(str(v.get(x) or "") for x in
                                   ("does", "operates_on", "lands_in")).lower()
    except Exception:
        pass
    # 3) y los AGENTES: hay preguntas cuya respuesta no es un minero. Arbitrar es una.
    ag = os.path.join(REPO, ".claude", "agents")
    if os.path.isdir(ag):
        for f in sorted(os.listdir(ag)):
            if f.endswith(".md") and f[:-3] not in caps:
                try:
                    with open(os.path.join(ag, f), encoding="utf-8", errors="ignore") as fh:
                        caps[f[:-3]] = fh.read()[:4000].lower()
                except Exception:
                    pass
    return caps


def _cargar():
    try:
        with open(BUS, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {"hallazgos": [], "preguntas": []}


def _guardar(d):
    with open(BUS, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)


def repartir(silencioso=False):
    """De CUALQUIERA al que DECLARA saber. Devuelve las repartidas."""
    d = _cargar()
    saben = _capacidades()
    hechas = []
    for p in d.get("preguntas") or []:
        if p.get("respuestas") or str(p.get("para", "")).upper() not in ("CUALQUIERA", "", "TODOS"):
            continue
        quien = str(p.get("de") or "")
        necesita = _tok(p.get("pregunta")) | _tok(p.get("porque_no_puedo_yo"))
        cand = []
        for mid, texto in saben.items():
            if not mid or mid == quien:
                continue                      # nadie se pregunta a si mismo
            n = sum(1 for w in necesita if w in texto)
            if n >= 2:
                cand.append((n, mid))
        if not cand:
            continue
        cand.sort(reverse=True)
        p["para"] = cand[0][1]
        p["_repartida"] = {
            "cuando": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "por_que_a_el": (f"declara responder a {cand[0][0]} de los terminos que la "
                             f"pregunta necesita"),
            "otros_candidatos": [m for _, m in cand[1:3]],
            "_ojo": ("el reparto NO es la respuesta: contestar exige mirar datos. Un enrutado "
                     "sin respuesta es teatro"),
        }
        hechas.append((quien, p.get("sujeto"), cand[0][1]))
    if hechas:
        _guardar(d)
    if not silencioso:
        for q, s, a in hechas:
            print(f"  [reparto] {q} --[{s}]--> {a}")
    return hechas


def resolver_id(quien):
    """De nombre de FICHERO a id de ALGORITMO, por `bound_in` de algorithms.json.

    metodo.avisar() deduce quien llama mirando el fichero -- `account_classes` -- y el
    catalogo de capacidades usa el id -- `A34_account_behaviour_classes`. Sin traducir, el
    foro no le enseñaba nada a nadie y parecia que no habia preguntas para el: un mecanismo
    que falla en silencio es peor que no tenerlo, porque da la impresion de estar puesto.
    """
    if not quien:
        return quien
    try:
        with open(os.path.join(REPO, "brain_v2", "methods", "algorithms.json"),
                  encoding="utf-8") as fh:
            A = json.load(fh).get("algorithms") or {}
    except Exception:
        return quien
    if quien in A:
        return quien
    base = str(quien).replace("\\", "/").split("/")[-1]
    base = base[:-3] if base.endswith(".py") else base
    for k, v in A.items():
        for b in (v.get("bound_in") or []):
            if str(b).replace("\\", "/").split("/")[-1] in (base, base + ".py"):
                return k
    return quien


def para_mi(minero):
    """Preguntas ABIERTAS que este minero deberia contestar.

    Dos motivos para que una pregunta sea suya: se la dirigieron, o su capacidad declarada
    cubre lo que la pregunta necesita. Lo segundo importa mas: un minero que solo mira su
    buzon no colabora, espera.
    """
    minero = resolver_id(minero)
    d = _cargar()
    saben = _capacidades()
    mio = saben.get(minero, "")
    out = []
    for p in d.get("preguntas") or []:
        if p.get("respuestas") or str(p.get("de") or "") == minero:
            continue
        dirigida = str(p.get("para", "")) == minero
        necesita = _tok(p.get("pregunta")) | _tok(p.get("porque_no_puedo_yo"))
        cubre = sum(1 for w in necesita if w in mio)
        if dirigida or cubre >= 2:
            out.append(dict(p, _por_que_es_tuya=("te la dirigieron" if dirigida else
                                                 f"tu capacidad declarada cubre {cubre} de sus "
                                                 f"terminos")))
    return out


def marcar_visita(minero, podia, contesto):
    """Deja constancia de que este minero PASO por el foro.

    Sin este registro no se puede distinguir «no habia nada que contestar» de «no miro», y
    esa diferencia es exactamente la colaboracion. Lo llama metodo.avisar() solo, para que
    no dependa de que cada minero se acuerde -- un mecanismo opcional no es un mecanismo.
    """
    if not minero:
        return
    try:
        est = json.load(open(PASO, encoding="utf-8")) if os.path.exists(PASO) else {}
    except Exception:
        est = {}
    prev = est.get(minero) or {}
    est[minero] = {
        "cuando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "preguntas_que_podia_contestar": sorted(set(podia)),
        "contestadas": sorted(set((prev.get("contestadas") or []) + list(contesto))),
        "sin_contestar": sorted(set(podia) - set((prev.get("contestadas") or [])) - set(contesto)),
    }
    try:
        with open(PASO, "w", encoding="utf-8") as fh:
            json.dump(est, fh, indent=2, ensure_ascii=False)
    except OSError:
        pass


def contestar(minero, sujeto, respuesta, evidencia="", para=None, a_todas=False):
    """Deja una respuesta REAL en el foro. Exige evidencia: sin ella no es una respuesta.

    H139 — EL SUJETO NO IDENTIFICA UNA PREGUNTA, Y ELEGIR LA PRIMERA EN SILENCIO DEJABA EL
    RESTO ABIERTAS PARA SIEMPRE.
        Medido el 2026-08-27 sobre el bus: 47 preguntas, y CUATRO sujetos repetidos.
        `CLAIM 616` son **15 preguntas** con el mismo sujeto, **15 destinatarios distintos** y
        **texto distinto cada una** (A30_mining_bus, F1_interface_boundary_analysis,
        A49_tier2_sod, sap_interface_intelligence...). La version anterior recorria la lista,
        casaba por `sujeto`, contestaba la PRIMERA y hacia `return True`. Las otras 14 quedaban
        abiertas sin que nadie lo supiera, y el foro decia "contestada" -- que es peor que
        decir nada, porque parece cerrado.

    LA IDENTIDAD DE UNA PREGUNTA ES (sujeto, para). Ahora:
        - un solo candidato  -> se contesta.
        - varios y `para`    -> se contesta el de ese destinatario.
        - varios y `a_todas` -> se contestan TODAS (respuesta de nivel sujeto, el caso 616).
        - varios y ninguno de los dos -> SE NIEGA y dice cuantas hay y a quien.
          NUNCA elegir en silencio: un silencio parece una respuesta.
    """
    if not str(respuesta or "").strip():
        raise ValueError("una respuesta vacia no es una respuesta")
    d = _cargar()
    cand = [p for p in (d.get("preguntas") or []) if str(p.get("sujeto")) == str(sujeto)]
    if not cand:
        return False
    if para is not None:
        cand = [p for p in cand if str(p.get("para")) == str(para)]
        if not cand:
            return False
    if len(cand) > 1 and not a_todas:
        destinos = ", ".join(sorted({str(p.get("para")) for p in cand}))
        raise ValueError(
            f"el sujeto '{sujeto}' tiene {len(cand)} preguntas abiertas, para: {destinos}.\n"
            f"Una respuesta no las cierra todas por casualidad: pasa para='<destinatario>' si\n"
            f"es especifica de uno, o a_todas=True si vale para los {len(cand)}.")
    sello = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for p in cand:
        p.setdefault("respuestas", []).append({
            "de": minero, "respuesta": respuesta,
            "evidencia": evidencia or "(sin declarar -- una respuesta sin evidencia vale poco)",
            "cuando": sello,
            **({"alcance": f"respuesta de nivel SUJETO, aplicada a las {len(cand)}"} if len(cand) > 1 else {})})
    _guardar(d)
    return len(cand)


def cerrar_colaborando(minero, puedo_contestar=None):
    """LO QUE TODO MINERO HACE AL TERMINAR. No es opcional.

    `puedo_contestar` es una funcion que recibe una pregunta y devuelve (respuesta, evidencia)
    o None. Si el minero no la pasa, esto AVISA de lo que podria haber contestado y no
    contesto -- y deja constancia, que es lo que la puerta mira.
    """
    repartir(silencioso=True)
    mias = para_mi(minero)
    contestadas = []
    for p in mias:
        r = puedo_contestar(p) if puedo_contestar else None
        if r:
            resp, ev = (r if isinstance(r, tuple) else (r, ""))
            # `para=minero`: estas son SUS preguntas. Sin esto, un sujeto compartido por
            # varios destinatarios (CLAIM 616 lo esta por 15) haria que contestar() se
            # negara -- o, antes de H139, que este minero contestara la de OTRO.
            if contestar(minero, p["sujeto"], resp, ev, para=minero):
                contestadas.append(p["sujeto"])
    # DEJAR CONSTANCIA DE QUE PASO POR EL FORO. Sin esto no se puede distinguir "no habia nada
    # que contestar" de "no miro", y esa diferencia es justo lo que la puerta necesita.
    try:
        est = json.load(open(PASO, encoding="utf-8")) if os.path.exists(PASO) else {}
    except Exception:
        est = {}
    est[minero] = {"cuando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "preguntas_que_podia_contestar": [p["sujeto"] for p in mias],
                   "contestadas": contestadas,
                   "sin_contestar": [p["sujeto"] for p in mias if p["sujeto"] not in contestadas]}
    with open(PASO, "w", encoding="utf-8") as fh:
        json.dump(est, fh, indent=2, ensure_ascii=False)

    if mias:
        print(f"\n[foro] {len(mias)} pregunta(s) abiertas que TU puedes contestar:")
        for p in mias:
            marca = "CONTESTADA" if p["sujeto"] in contestadas else "SIN CONTESTAR"
            print(f"   [{marca}] {p['sujeto']}  (de {p['de']}) -- {p['_por_que_es_tuya']}")
            if p["sujeto"] not in contestadas:
                print(f"      {str(p.get('pregunta'))[:150]}")
        if len(contestadas) < len(mias):
            print("   ⛔ dejar una pregunta abierta que puedes contestar es la ocasion perdida")
            print("      que mide mining_collaboration_check. Contesta con "
                  "colaborar.contestar(...)")
    return contestadas


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--repartir" in sys.argv:
        h = repartir()
        print(f"\n{len(h)} pregunta(s) repartidas")
    elif "--para" in sys.argv:
        m = sys.argv[sys.argv.index("--para") + 1]
        for p in para_mi(m):
            print(f"  {p['sujeto']}  (de {p['de']}) -- {p['_por_que_es_tuya']}")
            print(f"     {str(p.get('pregunta'))[:160]}")
    else:
        print(__doc__)
