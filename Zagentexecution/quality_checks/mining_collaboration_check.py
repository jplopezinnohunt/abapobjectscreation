"""GATE: ¿los mineros COLABORAN de verdad, o solo publican en el mismo tablon?

LO QUE ESTE CHECK EXIGE, y por que
    El operador lo pidio asi: «necesitamos evidencias de colaboracion, si no, no aprendieron.
    Tiene que haber evidencia del foro, y de si deberia usarse y no se uso».

    Publicar no es colaborar. Un tablon donde 30 mineros dejan 307 hallazgos y nadie contesta
    las 14 preguntas es un tablon de anuncios, no un foro. Medido 2026-08-26: 14 preguntas, UNA
    respondida. Y la que si funciono demuestra que el mecanismo VALE: A31 llego al limite de su
    instrumento -- desde APQI no se distingue una cuenta borrada de un texto inventado --
    pregunto diciendo POR QUE no podia el, y A27, que tiene USR02 y el log cargados, contesto.
    De ahi salio que la herramienta escribe el CREATOR con guion bajo donde la cuenta real
    lleva guion (claim 590). Ninguno de los dos lo tenia por separado.

LO QUE DELATA, que es lo que faltaba
    1. EVIDENCIA: cuantas preguntas, cuantas respondidas, quien contesto a quien y que salio.
    2. SIN DESTINATARIO: una pregunta dirigida a CUALQUIERA no la contesta nadie, porque nadie
       es el responsable. Medido: 11 de las 14 son asi -- los limites que cada minero declara,
       lanzados al aire. El enrutador de capacidades (process_mining/ask.py) SABE quien puede
       contestar cada tema; no usarlo es tener el buzon y no repartir el correo.
    3. OCASION PERDIDA: alguien publico un hallazgo sobre el MISMO SUJETO por el que otro tenia
       una pregunta abierta, y no la contesto. Eso es «deberia usarse y no se uso», y es lo
       unico que distingue un foro vivo de uno decorativo.

Uso:  python Zagentexecution/quality_checks/mining_collaboration_check.py [--json]
Salida: exit 0 si hay colaboracion y sin ocasiones perdidas · exit 1 si no
"""
QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "herramientas",  # datos_sap | conocimiento | herramientas
    "needs": "files",
    "what": ("si los mineros se contestan de verdad, si hay preguntas sin destinatario y si "
             "alguien publico sobre un sujeto con pregunta abierta y no la contesto"),
}
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUS = os.path.join(ROOT, "process_mining", "mining_findings.json")


def main():
    try:
        d = json.load(open(BUS, encoding="utf-8"))
    except Exception as e:
        print(f"no se pudo leer el foro: {e}")
        return 1
    hall = d.get("hallazgos") or []
    preg = d.get("preguntas") or []
    h = []

    respondidas = [p for p in preg if p.get("respuestas")]
    sin_destinatario = [p for p in preg
                        if str(p.get("para", "")).upper() in ("CUALQUIERA", "", "TODOS")
                        and not p.get("respuestas")]

    # ---- 1. EVIDENCIA -----------------------------------------------------------------
    evidencia = []
    for p in respondidas:
        for r in p["respuestas"]:
            evidencia.append({
                "pregunto": p.get("de"), "sujeto": p.get("sujeto"),
                "contesto": r.get("de") or r.get("minero"),
                "que_dijo": str(r.get("respuesta") or r.get("texto"))[:200]})
    if not evidencia:
        h.append({"gravedad": "SIN_NINGUNA_COLABORACION",
                  "que_pasa": (f"{len(preg)} pregunta(s) en el foro y NINGUNA contestada. "
                               f"Publicar no es colaborar: {len(hall)} hallazgos en el mismo "
                               f"tablon no prueban que nadie lea a nadie")})

    # ---- 2. PREGUNTAS SIN DESTINATARIO --------------------------------------------------
    if sin_destinatario:
        h.append({"gravedad": "PREGUNTA_SIN_DESTINATARIO", "cuantas": len(sin_destinatario),
                  "sujetos": [p.get("sujeto") for p in sin_destinatario][:12],
                  "que_pasa": ("dirigidas a CUALQUIERA, o sea a nadie. Nadie es el responsable "
                               "y por eso siguen abiertas. El enrutador de capacidades "
                               "(process_mining/ask.py) sabe quien puede contestar cada tema"),
                  "como_se_arregla": ("python process_mining/mining_bus.py --repartir  -- "
                                      "asigna cada pregunta abierta al minero que declara esa "
                                      "capacidad, en vez de dejarla al aire")})

    # ---- 3. OCASION PERDIDA -------------------------------------------------------------
    # Alguien publico sobre el MISMO SUJETO por el que otro pregunta, y no contesto. Se cruza
    # por SUJETO exacto, no por palabras: cruzar por texto libre produce parejas plausibles y
    # falsas, que es el defecto que este repo lleva todo el dia corrigiendo.
    perdidas = []
    for p in preg:
        if p.get("respuestas"):
            continue
        suj = str(p.get("sujeto", "")).upper()
        # el sujeto de una pregunta de LIMITE es "LIMITE:<minero>": no nombra un objeto,
        # asi que no se le puede buscar hallazgo. Se cuenta aparte, en (2).
        if not suj or suj.startswith("LIMITE:"):
            continue
        quien = p.get("de")
        podrian = sorted({x.get("minero") for x in hall
                          if str(x.get("sujeto", "")).upper() == suj
                          and x.get("minero") and not str(x["minero"]).startswith(str(quien))})
        if podrian:
            perdidas.append({"pregunta_de": quien, "sujeto": p.get("sujeto"),
                             "podrian_contestar": podrian})
    if perdidas:
        h.append({"gravedad": "OCASION_PERDIDA", "cuantas": len(perdidas), "casos": perdidas,
                  "que_pasa": ("otro minero publico sobre EL MISMO SUJETO y no contesto la "
                               "pregunta abierta. Es literalmente 'deberia usarse y no se uso'"),
                  "como_se_arregla": "python process_mining/mining_bus.py --auto-resolver"})

    # ---- 4. ¿PASO POR EL FORO? ----------------------------------------------------------
    # Un minero que corre y NI MIRA las preguntas abiertas no colabora, aunque no hubiera nada
    # que contestar -- y sin registro no se puede distinguir «no habia nada» de «no miro».
    # colaborar.cerrar_colaborando() deja constancia; los que no aparecen es que no lo llaman.
    est = {}
    try:
        with open(os.path.join(ROOT, "process_mining", "colaboracion_state.json"),
                  encoding="utf-8") as fh:
            est = json.load(fh)
    except Exception:
        pass
    A = {}
    try:
        with open(os.path.join(ROOT, "brain_v2", "methods", "algorithms.json"),
                  encoding="utf-8") as fh:
            A = json.load(fh).get("algorithms") or {}
    except Exception:
        pass
    mineros = [k for k, v in A.items() if v.get("mining_kind")]
    nunca_pasaron = sorted(m for m in mineros if m not in est)
    dejaron_sin_contestar = sorted(m for m, v in est.items() if v.get("sin_contestar"))
    if nunca_pasaron:
        h.append({"gravedad": "NO_PASA_POR_EL_FORO", "cuantas": len(nunca_pasaron),
                  "sujetos": nunca_pasaron[:14],
                  "que_pasa": ("mineros registrados que nunca han llamado a "
                               "colaborar.cerrar_colaborando(): corren, publican y se van. Sin "
                               "esa llamada no se puede saber si no habia nada que contestar o "
                               "si no miraron -- y esa diferencia es la colaboracion"),
                  "como_se_arregla": ("al final del minero: from colaborar import "
                                      "cerrar_colaborando; cerrar_colaborando('<su id>')")})
    if dejaron_sin_contestar:
        h.append({"gravedad": "MIRO_Y_NO_CONTESTO", "cuantas": len(dejaron_sin_contestar),
                  "sujetos": dejaron_sin_contestar[:14],
                  "que_pasa": ("pasaron por el foro, vieron preguntas que SU capacidad "
                               "declarada cubre, y las dejaron abiertas"),
                  "como_se_arregla": "colaborar.contestar(minero, sujeto, respuesta, evidencia)"})

    # ---- 5. LOS OTROS TRES TIPOS: ¿participan en la red o son islas? --------------------
    # El operador lo pidio explicito: el control es de skills, agentes, algoritmos Y mineros.
    # Colaborar significa cosas distintas en cada uno, pero la pregunta es la misma: ¿este
    # artefacto esta CONECTADO a los demas, o trabaja solo?
    islas = {}
    try:
        with open(os.path.join(ROOT, "brain_v2", "toolgraph.json"), encoding="utf-8") as fh:
            T = json.load(fh)
        sal = T.get("salud") or {}
        islas = {
            "SKILL sin ningun lector": (sal.get("skills_sin_ningun_lector") or {}).get("cuantos"),
            "ALGORITMO que no lee ningun skill":
                (sal.get("algoritmos_que_no_leen_ningun_skill") or {}).get("cuantos"),
            "AGENTE sin instrumento declarado":
                (sal.get("agentes_sin_instrumento_declarado") or {}).get("cuantos"),
        }
        ar = sal.get("aristas_que_faltan_frente_a_las_que_hay") or {}
        if ar.get("DEBERIA_LEER", 0) > (ar.get("LEE", 0) or 0):
            h.append({"gravedad": "LA_RED_ESTA_MAS_VACIA_QUE_LLENA",
                      "cuantas": ar.get("DEBERIA_LEER"),
                      "que_pasa": (f"en el grafo de herramientas hay {ar.get('LEE')} arista(s) "
                                   f"LEE frente a {ar.get('DEBERIA_LEER')} DEBERIA_LEER: por "
                                   f"cada relacion que existe faltan mas. Colaborar entre tipos "
                                   f"-- un algoritmo que lee su skill, un agente que nombra su "
                                   f"instrumento -- es la misma cosa que un minero que contesta "
                                   f"una pregunta"),
                      "detalle": islas,
                      "como_se_arregla": ("python Zagentexecution/quality_checks/"
                                          "skill_binding_check.py da la lista concreta")})
    except Exception:
        pass

    rep = {"_que_es": ("si skills, agentes, algoritmos y mineros COLABORAN de verdad o cada uno "
                       "trabaja solo"),
           "hallazgos_en_el_foro": len(hall), "preguntas": len(preg),
           "respondidas": len(respondidas), "sin_destinatario": len(sin_destinatario),
           "mineros_que_pasaron_por_el_foro": len(est), "mineros_registrados": len(mineros),
           "islas_por_tipo": islas,
           "evidencia_de_colaboracion": evidencia, "hallazgos_del_check": h}
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if h else 0

    print(f"[foro] {len(hall)} hallazgo(s) · {len(preg)} pregunta(s) · "
          f"{len(respondidas)} respondida(s)")
    if evidencia:
        print("\n  EVIDENCIA DE COLABORACION (agente a agente):")
        for e in evidencia:
            print(f"    {e['pregunto']} preguntó por {e['sujeto']}")
            print(f"      -> contestó {e['contesto']}: {e['que_dijo'][:120]}")
    if not h:
        print("\n  OK - hay colaboracion y ninguna ocasion perdida")
        return 0
    for x in h:
        print(f"\n  [{x['gravedad']}] {x.get('cuantas', '')}")
        print(f"      {x['que_pasa']}")
        for c in (x.get("casos") or [])[:8]:
            print(f"      {c['pregunta_de']} pregunta por {c['sujeto']} y podrian contestar: "
                  f"{', '.join(c['podrian_contestar'][:4])}")
        for s in (x.get("sujetos") or [])[:8]:
            print(f"      {s}")
        if x.get("como_se_arregla"):
            print(f"      ARREGLO: {x['como_se_arregla']}")
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
