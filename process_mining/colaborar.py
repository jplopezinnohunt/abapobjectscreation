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


def _qid(p):
    """Identidad ESTABLE de una pregunta: quien pregunta + sujeto + su texto.

    NO incluye el destinatario a proposito: `para` cambia cuando se re-enruta, y usar el par
    (sujeto, para) como identidad fue lo que dejo a `variant-intelligence` sin poder contestar
    su propia pregunta con la API. Es H139 por el otro lado.
    """
    import hashlib
    base = "|".join([str(p.get("de") or ""), str(p.get("sujeto") or ""),
                     str(p.get("pregunta") or "")[:400]])
    return "q" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def _guardar(d):
    """Atomico y FUNDIENDO lo que otro haya escrito mientras tanto.

    Lo encontro `mining-arbiter` trabajando: el bus hacia read-modify-write del fichero
    entero sin control de concurrencia, y mientras contestaba «otro proceso volco su copia y
    desaparecio `_reenrutada_s107` de las cuatro preguntas de ADS». Sus respuestas
    sobrevivieron POR ORDEN DE ESCRITURA, NO POR DISENO.

    Es ADR-008 -- un solo escritor -- incumplido justo donde dos mineros trabajan a la vez
    POR DISENO. Y el sintoma es el peor de todos: no da error, borra.
    """
    import os as _os
    import tempfile as _tf

    # RELEER Y FUNDIR: las respuestas de otro no se pisan. Se funden por qid; lo que no
    # este en memoria se conserva tal cual.
    try:
        with open(BUS, encoding="utf-8") as fh:
            disco = json.load(fh)
        mias = {_qid(p): p for p in (d.get("preguntas") or [])}
        fundidas, vistas = [], set()
        for p in (disco.get("preguntas") or []):
            k = _qid(p)
            vistas.add(k)
            if k not in mias:
                fundidas.append(p)          # pregunta que otro anadio: se conserva
                continue
            mia = mias[k]
            # las respuestas se UNEN, nunca se sustituyen
            ya = {(str(r.get("de")), str(r.get("respuesta"))[:120])
                  for r in (mia.get("respuestas") or [])}
            for r in (p.get("respuestas") or []):
                if (str(r.get("de")), str(r.get("respuesta"))[:120]) not in ya:
                    mia.setdefault("respuestas", []).append(r)
            fundidas.append(mia)
        for k, p in mias.items():
            if k not in vistas:
                fundidas.append(p)          # pregunta nueva mia
        d["preguntas"] = fundidas
        # los hallazgos son append-only: se conserva la union por (minero, sujeto, hallazgo)
        hd = {(str(h.get("minero")), str(h.get("sujeto")), str(h.get("hallazgo"))[:120]): h
              for h in (disco.get("hallazgos") or [])}
        for h in (d.get("hallazgos") or []):
            hd[(str(h.get("minero")), str(h.get("sujeto")), str(h.get("hallazgo"))[:120])] = h
        d["hallazgos"] = list(hd.values())
    except Exception:
        pass                                # si no se puede releer, se escribe lo que hay

    # ⛔ CONSECUENCIA DECLARADA: al fundir con el disco, el bus es APPEND-ONLY. Una
    # respuesta no se puede BORRAR por esta via -- si la quitas en memoria, la fusion la
    # recupera del disco. Es deliberado: para un foro donde dos mineros escriben a la vez,
    # perder una respuesta ajena es peor que arrastrar una de mas. Borrar exige escritura
    # directa y consciente, no un descuido.
    for p in (d.get("preguntas") or []):
        p.setdefault("qid", _qid(p))

    fd, tmp = _tf.mkstemp(dir=_os.path.dirname(BUS), suffix=".tmp")
    try:
        with _os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2, ensure_ascii=False)
        _os.replace(tmp, BUS)               # atomico: nadie ve un fichero a medias
    except Exception:
        try:
            _os.unlink(tmp)
        except OSError:
            pass
        raise


def _mineros_ejecutables():
    """Quien puede CORRER: registrado en algorithms.json y con su fichero en disco.

    s107. Un publicador del bus no es necesariamente un minero: puede ser un analisis de una
    tarde que nadie declaro -- patron H118. Enrutarle una pregunta la deja en un limbo que
    parece atendido.
    """
    import os as _os
    try:
        with open(_os.path.join(REPO, "brain_v2", "methods", "algorithms.json"),
                  encoding="utf-8") as fh:
            A = json.load(fh).get("algorithms") or {}
    except Exception:
        return set()
    out = set()
    for k, v in A.items():
        for b in (v.get("bound_in") or []):
            r = str(b).split(" ")[0]
            if r and _os.path.exists(_os.path.join(REPO, r)):
                out.add(k)
                break
    return out


def repartir(silencioso=False):
    """De CUALQUIERA al que DECLARA saber. Devuelve las repartidas."""
    d = _cargar()
    saben = _capacidades()
    hechas = []
    for p in d.get("preguntas") or []:
        if p.get("respuestas") or str(p.get("para", "")).upper() not in ("CUALQUIERA", "", "TODOS"):
            continue
        quien = str(p.get("de") or "")
        suj = str(p.get("sujeto") or "").strip().lower()
        necesita = _tok(p.get("pregunta")) | _tok(p.get("porque_no_puedo_yo"))

        # ---- 1) EVIDENCIA: ¿alguien PUBLICO ya sobre ese sujeto? --------------------
        # H126, arreglado s107. El repartidor mandaba a A68 cuatro preguntas sobre ADS
        # «porque su capacidad cubre 4 terminos». A68 mina el ciclo del PAGO y no tiene nada
        # que decir de ADS: comparte 'jobs', 'salida', 'programas'. COMPARTIR PALABRAS NO ES
        # PODER CONTESTAR, y el IDF no lo salva -- se midio: ninguno de esos terminos es
        # ubicuo. La senal que SI vale es haber publicado sobre el sujeto, que es prueba y no
        # proximidad, y es la misma que usa `_respuesta_desde_lo_publicado` para contestar.
        # ⛔ Y TIENE QUE PODER CORRER. Publicar en el bus no basta: la primera version de
        # esto mando las cuatro preguntas de ADS a `inc16471_ads_log_mining`, que publico y
        # NO ESTA REGISTRADO -- sin ficha y sin script. Enrutar a quien no se puede ejecutar
        # es enrutar a un fantasma: la pregunta parece atendida y no lo esta.
        por_evidencia = None
        if suj:
            _ejecutables = _mineros_ejecutables()
            for h in (d.get("hallazgos") or []):
                m = str(h.get("minero") or "")
                if (m and m != quien and m in _ejecutables
                        and str(h.get("sujeto") or "").strip().lower() == suj):
                    por_evidencia = m
                    break

        cand = []
        if por_evidencia:
            cand = [("EVIDENCIA", por_evidencia)]
            motivo = ("YA PUBLICO un hallazgo sobre este mismo sujeto: puede contestar con lo "
                      "que ya midio, no por parecido de vocabulario")
        else:
            # ---- 2) PALABRAS, pero pesadas y exigiendo una RARA ---------------------
            import math as _math
            _df = {}
            for _t in saben.values():
                for _w in _tok(_t):
                    _df[_w] = _df.get(_w, 0) + 1
            _N = max(len(saben), 1)

            def _idf(w):
                dd = _df.get(w, 0)
                return 0.0 if dd < 1 or dd > 0.25 * _N else _math.log(_N / dd)

            _RARO = _math.log(_N / max(1.0, 0.08 * _N))
            for mid, texto in saben.items():
                if not mid or mid == quien:
                    continue                      # nadie se pregunta a si mismo
                comunes = [w for w in necesita if w in texto]
                if not comunes:
                    continue
                raros = [w for w in comunes if _idf(w) >= _RARO]
                if not raros or len(comunes) < 3:
                    continue          # sin un termino RARO no hay tema compartido
                cand.append((round(sum(_idf(w) for w in comunes), 2), mid))
            cand.sort(reverse=True)
            motivo = None

        if not cand:
            # ---- 3) NADA: se deja sin repartir Y SE DICE ---------------------------
            # Antes se asignaba al menos malo. Eso es peor que no asignar: el destinatario
            # equivocado no contesta Y el gate lo cuenta como ocasion perdida SUYA.
            p["_sin_destinatario"] = {
                "cuando": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "por_que": ("nadie ha publicado sobre este sujeto y ningun candidato comparte "
                            "un termino RARO con la pregunta. Repartir al menos malo culpa a "
                            "quien no podia contestar"),
                "que_haria_falta": ("que alguien mine el sujeto, o que el que pregunta nombre "
                                    "la tabla o el objeto concreto en vez del tema"),
            }
            continue

        p["para"] = cand[0][1]
        p["_repartida"] = {
            "cuando": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "por_que_a_el": motivo or (
                f"solape pesado por IDF ({cand[0][0]}) con al menos un termino RARO -- es un "
                f"PROXY de capacidad, no una prueba de que pueda contestar"),
            "senal": "EVIDENCIA" if por_evidencia else "PALABRAS_PESADAS",
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


def contestar(minero, sujeto, respuesta, evidencia="", para=None, a_todas=False, qid=None):
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
    # `qid` manda: es la identidad ESTABLE. El par (sujeto, para) deja de identificar en
    # cuanto la pregunta se re-enruta -- le paso a variant-intelligence con su propia
    # pregunta y tuvo que abrir el fichero a mano.
    if qid:
        cand = [p for p in (d.get("preguntas") or []) if p.get("qid") == qid]
        if not cand:
            return False
        a_todas = True                      # un qid identifica una sola pregunta
    else:
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


def _respuesta_desde_lo_publicado(minero, pregunta, d=None):
    """LA RESPUESTA POR DEFECTO: lo que este minero ACABA DE PUBLICAR sobre ese sujeto.

    s107. Medido antes de escribirla: de 72 mineros, 49 PUBLICAN en el bus y UNO pasa
    `puedo_contestar`. 47 preguntas, 14 respuestas. El foro era un megafono.

    La causa no era desgana: era que la tarea estaba mal definida. «Implementa una funcion que
    reciba una pregunta y decida» obliga a cada minero a inventar su criterio, asi que ninguno
    lo hizo -- es el fallo de DESCRIPCION DE TAREA VAGA que Anthropic midio como el numero uno
    de la delegacion orquestador->subagente.

    Aqui no hay criterio nuevo que inventar: si el minero YA emitio un hallazgo sobre ese
    sujeto, ese hallazgo ES su respuesta. Solo hay que dejar de tirarlo.

    NO RAZONA, y por eso es segura: si no publico nada del sujeto, devuelve None y el minero
    queda registrado como «pudo y no contesto». Un foro que responde por responder miente.
    """
    d = d or _cargar()
    suj = str(pregunta.get("sujeto") or "").strip().lower()
    if not suj:
        return None
    mios = [h for h in (d.get("hallazgos") or [])
            if str(h.get("minero")) == str(minero)]
    if not mios:
        return None

    # 1) mismo sujeto, que es el caso limpio
    exactos = [h for h in mios if str(h.get("sujeto") or "").strip().lower() == suj]
    # 2) si no, el sujeto de la pregunta aparece en lo que publico
    if not exactos:
        exactos = [h for h in mios
                   if suj in str(h.get("hallazgo") or "").lower()
                   or suj in str(h.get("sujeto") or "").lower()]
    if not exactos:
        return None

    h = max(exactos, key=lambda x: len(str(x.get("hallazgo") or "")))
    resp = ("RESPUESTA AUTOMATICA desde lo que este minero publico en su ultima corrida "
            "(no es un juicio nuevo, es su hallazgo sobre ese sujeto): %s"
            % str(h.get("hallazgo"))[:900])
    ev = "%s · aspecto=%s · autoridad=%s · %s" % (
        minero, h.get("aspecto"), h.get("autoridad"),
        str(h.get("evidencia") or "")[:200])
    return resp, ev


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
        # POR DEFECTO SE CONTESTA. Antes, sin `puedo_contestar` esto valia None y el
        # minero pasaba de largo -- de 72, uno solo la pasaba. Ahora el silencio hay que
        # ganarselo: si publicaste algo del sujeto, contestas.
        r = puedo_contestar(p) if puedo_contestar else _respuesta_desde_lo_publicado(minero, p)
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
