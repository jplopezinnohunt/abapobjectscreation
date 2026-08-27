"""
process_circuit_check.py — el CIRCUITO declarado sigue cubierto, y sus juntas se ven. H137, s107.

QUE PROBLEMA RESUELVE
    El dueno recordaba "un companion que recorria el circuito completo de pagos" y no sabia
    donde estaba. No estaba perdido: estaba REPARTIDO EN CINCO PIEZAS, y el grafo de
    companions no conocia la cadena. Medido el 2026-08-27: de los 10 pares posibles entre
    esas piezas, SEIS no tienen arista, y `p2p_purpose_of_payment.html` no tiene ninguna
    con las otras cuatro.

POR QUE EL GRAFO NO PODIA ENCONTRARLA — y por que no era un umbral mal puesto
    `companion_graph.json` tiene UN SOLO tipo de arista: coseno IDF sobre vocabulario
    compartido. Eso mide PARECIDO. Dos etapas CONTIGUAS de un proceso comparten poco
    vocabulario precisamente porque son etapas distintas — EBAN/EKPO no se parece a
    BNK_BATCH_HEADER. La similitud no puede expresar SECUENCIA, por construccion. Bajar el
    umbral no habria cosido el circuito: habria metido ruido.
    Por eso la secuencia se DECLARA (`domains.json -> process_map.P2P.stages`) y lo que se
    MIDE es que la declaracion siga siendo cierta. Esta puerta es la mitad medible.

QUE COMPRUEBA (exit 1 si algo de esto falla)
    1. COBERTURA   — cada etapa declarada tiene al menos un companion que contiene de
                     verdad sus `evidence_tokens`. Una etapa sin cobertura = conocimiento
                     realmente perdido, que es lo unico que H137 temia.
    2. DECLARACION — cada companion NOMBRADO por una etapa la cubre de verdad. Un nombre
                     que ya no contiene los tokens es una declaracion podrida: el fichero
                     se reescribio y la etapa se quedo apuntando al sitio equivocado.
    3. ORDEN       — los `n` son consecutivos y unicos. Un circuito con dos etapas 7 no es
                     un circuito.

QUE REPORTA SIN FALLAR (es el mapa, no un defecto)
    - LAS JUNTAS SECAS: pares de etapas contiguas cuyos companions no comparten fichero NI
      tienen arista en el grafo. Es el hallazgo de H137 y se quiere VISIBLE cada corrida,
      no rojo permanente: un gate en rojo por deuda estructural es como se consigue que un
      check se ignore (misma leccion que H131).
    - CANDIDATOS: un companion que cubre una etapa MEJOR que el declarado. Es una pista de
      donde mirar, NO un veredicto — se abre el fichero antes de conectar (leccion de
      sap_transport_companion, braintoolbox seccion 1).

LO QUE ESTA PUERTA NO PUEDE VER (declarado, no descubierto por el siguiente)
    - Que el companion EXPLIQUE la etapa. Mide que el token APAREZCA. Un fichero que cita
      `BNK_MONI` en una tabla de inventario puntua igual que uno que narra el proceso. Es
      una senal de DONDE MIRAR, con el mismo limite que el `LEE` del toolgraph.
    - Si la etapa es cierta contra SAP. No lee P01. La verdad de la secuencia esta en los
      claims (623 BCM en medio, 624 el tercer consumidor de RM) y en la mineria, no aqui.
    - Los HTML fuera de `companions/`. El canonico es ese directorio; lo de fuera son
      copias (lo mide build_companion_graph.py, no esto).

Uso:
    python process_circuit_check.py                 # todos los circuitos declarados
    python process_circuit_check.py --proceso P2P
    python process_circuit_check.py --juntas        # solo el mapa de juntas secas
"""

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",
    "needs": "files",
    "what": "cada etapa del circuito declarado sigue cubierta por un companion que la contiene de verdad, y las juntas secas se ven",
    "args": "[--proceso P2P] [--juntas]",
}

import argparse
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DOMAINS = os.path.join(REPO, "brain_v2", "domains", "domains.json")
COMP_DIR = os.path.join(REPO, "companions")
GRAPH = os.path.join(REPO, "companions", "companion_graph.json")

SCRIPT_RE = re.compile(r"<script.*?</script>", re.S | re.I)

# No son nodos de contenido: son el indice generado y la vista del propio grafo. Mismo
# criterio que scripts/build_companion_graph.py, para que las dos herramientas cuenten igual.
# (La landing page cita TODA la cadena — por eso ganaba como "mejor candidato" en cada etapa:
#  un catalogo puntua como si narrara. Es el mismo falso positivo que mide la FORMA.)
SKIP = {"unesco_sap_landing.html", "companion_graph_v1.html"}


def cargar(p, defecto=None):
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return defecto if defecto is not None else {}


def texto_companions():
    """Lee UNA vez cada companion. El denominador se DERIVA del disco, no se supone."""
    out = {}
    if not os.path.isdir(COMP_DIR):
        return out
    for n in sorted(os.listdir(COMP_DIR)):
        if not n.endswith(".html") or n in SKIP:
            continue
        try:
            h = io.open(os.path.join(COMP_DIR, n), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        out[n] = SCRIPT_RE.sub("", h)
    return out


def cobertura(html, tokens):
    """Que tokens de la etapa aparecen de verdad en este companion."""
    return [t for t in tokens if re.search(re.escape(t), html, re.I)]


def circuitos(dom, solo=None):
    pm = (dom.get("process_map") or {})
    for clave, val in pm.items():
        if not isinstance(val, dict) or not val.get("stages"):
            continue
        if solo and clave != solo:
            continue
        yield clave, val


def aristas_del_grafo():
    g = cargar(GRAPH)
    pares = set()
    for e in (g.get("edges") or []):
        a, b = e.get("a"), e.get("b")
        if a and b:
            pares.add(frozenset((a, b)))
    return pares


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proceso", default=None)
    ap.add_argument("--juntas", action="store_true")
    a = ap.parse_args()

    dom = cargar(DOMAINS)
    if not dom:
        print("no se pudo leer brain_v2/domains/domains.json — nada que comprobar")
        return 0

    textos = texto_companions()
    if not textos:
        print("companions/ vacio o ilegible — la puerta NO PUEDE VER, no da verde")
        return 1
    pares = aristas_del_grafo()

    fallos, avisos, juntas = [], [], []
    n_circ = n_etapas = 0

    for clave, circ in circuitos(dom, a.proceso):
        n_circ += 1
        stages = circ["stages"]
        print(f"\n{'=' * 78}\nCIRCUITO {clave} — {circ.get('name', '')}  ({len(stages)} etapas)\n{'=' * 78}")

        # --- 3. ORDEN -------------------------------------------------------------
        ns = [s.get("n") for s in stages]
        if ns != sorted(ns) or len(set(ns)) != len(ns):
            fallos.append(f"{clave}: los `n` de las etapas no son unicos y ordenados: {ns}")

        cubre_por_etapa = []
        for s in stages:
            n_etapas += 1
            toks = s.get("evidence_tokens") or []
            declarados = s.get("companions") or []
            medido = {}
            for nombre, html in textos.items():
                hits = cobertura(html, toks)
                if hits:
                    medido[nombre] = hits
            # el mejor de todo el disco, declarado o no
            ranking = sorted(medido.items(), key=lambda kv: -len(kv[1]))
            mejor = ranking[0] if ranking else None
            umbral = max(1, (len(toks) + 1) // 2)      # al menos la mitad de los tokens

            # --- 1. COBERTURA ------------------------------------------------------
            cubridores = [n for n, h in medido.items() if len(h) >= umbral]
            if not cubridores:
                fallos.append(f"{clave}/{s['id']}: NINGUN companion cubre la etapa "
                              f"(umbral {umbral}/{len(toks)}) — conocimiento realmente ausente")
            cubre_por_etapa.append(set(declarados) & set(medido) or set(cubridores))

            # --- 2a. UNA ETAPA SIN COMPANION LO DICE, NO LO CALLA -------------------
            # Se anade al introducir `85_pago_manual_f53`, que no tiene companion ninguno: lo
            # descubrio la lectura de un skill, no un artefacto visual. Sin esto, una etapa con
            # `companions: []` pasaba en verde porque la lista de rotos venia vacia -- ausencia
            # leida como conformidad, que es el modo de fallo mas caro de este proyecto.
            if not declarados and not s.get("_sin_companion"):
                fallos.append(f"{clave}/{s['id']}: sin companions y sin `_sin_companion` que lo "
                              f"declare. Un hueco DICHO es informacion; un hueco callado pasa "
                              f"por cobertura")

            # --- 2b. EL SKILL QUE CUBRE LA ETAPA (s107) -----------------------------
            # POR QUE EXISTE ESTA COMPROBACION, y es el defecto mas caro de s107:
            # la etapa `60_wf_approval_rm` se declaro con CINCO tipos de documento (son 14),
            # diciendo que el metodo O "termina" el workflow (no termina: repone el bloqueo a
            # 'W' y QUEDA ESPERANDO un evento) y sin declarar que solo aplica a la sociedad
            # UNES. Las tres cosas estaban escritas, literalmente, en
            # `.claude/skills/sap_payment_bcm_agent/SKILL.md`. El coordinador
            # (`graph_queries.py tool para "<tarea>"`) puso ese skill como `1_LEE_ESTO_PRIMERO`
            # al empezar y NO SE LEYO. El modelo de la caja funciono; fallo el consumidor.
            # Un consejo que no cambia nada del flujo se lee como decoracion, asi que aqui deja
            # de ser consejo: la etapa DECLARA su skill y la puerta comprueba que ese skill
            # habla de verdad de lo que la etapa afirma. Es la unica forma de que "abre el
            # skill antes de declarar" sea comprobable y no una buena intencion.
            sk = s.get("skill")
            if sk:
                ruta = os.path.join(REPO, ".agents", "skills", sk, "SKILL.md")
                if not os.path.exists(ruta):
                    fallos.append(f"{clave}/{s['id']}: declara el skill `{sk}` y no existe en .claude/skills/")
                else:
                    txt = io.open(ruta, encoding="utf-8", errors="replace").read()
                    hay = [t for t in toks if re.search(re.escape(t), txt, re.I)]
                    if len(hay) < max(1, len(toks) // 3):
                        fallos.append(
                            f"{clave}/{s['id']}: declara el skill `{sk}` pero ese skill solo "
                            f"menciona {len(hay)}/{len(toks)} de sus objetos "
                            f"({', '.join(hay) or 'ninguno'}) — o el skill no es ese, o la "
                            f"etapa afirma cosas que ningun skill respalda")
            elif not s.get("_sin_skill"):
                fallos.append(f"{clave}/{s['id']}: sin `skill` y sin `_sin_skill` que explique "
                              f"por que no lo tiene. Una etapa declarada sin abrir su conocimiento "
                              f"curado es como se publicaron 3 errores en 60_wf_approval_rm")

            # --- 2. DECLARACION ----------------------------------------------------
            rotos = [d for d in declarados if len(medido.get(d, [])) < umbral]
            if rotos:
                for d in rotos:
                    existe = d in textos
                    fallos.append(
                        f"{clave}/{s['id']}: declara `{d}` y "
                        + ("no existe en companions/" if not existe
                           else f"solo contiene {len(medido.get(d, []))}/{len(toks)} tokens "
                                f"(umbral {umbral}) — declaracion podrida")
                    )

            # --- CANDIDATO MEJOR QUE EL DECLARADO (aviso, no veredicto) ------------
            if mejor and declarados:
                top_decl = max((len(medido.get(d, [])) for d in declarados), default=0)
                if len(mejor[1]) > top_decl and mejor[0] not in declarados:
                    avisos.append(f"{clave}/{s['id']}: `{mejor[0]}` cubre {len(mejor[1])}/{len(toks)} "
                                  f"y no esta declarado (declarado top {top_decl}) — ABRIR ANTES DE CONECTAR")

            s["_cubridores_medidos"] = set(cubridores)          # cualquiera que pase el umbral
            s["_declarados_que_cubren"] = {d for d in declarados if len(medido.get(d, [])) >= umbral}
            s["_umbral"] = umbral
            s["_medido"] = medido
            marca = "OK " if cubridores else "!! "
            print(f" {marca}{s['n']:>2}. {s['id']:<24} {len(medido.get(declarados[0], [])) if declarados else 0}"
                  f"/{len(toks)} tok  <- {', '.join(declarados) or '(sin declarar)'}"
                  + ("   [PARADA POSIBLE]" if s.get("can_stop_here") else "")
                  + ("   [CONDICIONAL]" if s.get("conditional") else ""))

        # --- LAS JUNTAS ------------------------------------------------------------
        # COMO SE DECIDE QUE UNA JUNTA ESTA COSIDA — y las dos formas de equivocarse, las dos
        # medidas en esta misma puerta el dia que se escribio:
        #   (a) usar `companions` tal cual: basta nombrar el mismo fichero en las dos etapas
        #       para que la junta PAREZCA cosida sin que nada la cosa. Es medir la FORMA de
        #       mi propia declaracion.
        #   (b) usar cualquier fichero que contenga los dos lados: la primera corrida dio la
        #       junta 40->45 como COSIDA por `transport_companion_D01K9B0CBF_v2.html` y la
        #       30->40 por `fm_ps_avc_temporal_forecast_v1.html` — un companion de TRANSPORTES
        #       y uno de AVC, que citan MIRO/BKPF de pasada. Una cita no es una narracion.
        # Lo que se usa: un fichero DECLARADO para una etapa (alguien lo abrio y lo juzgo) que
        # ademas MIDE cobertura de la contigua. Juicio Y medida; ninguno de los dos solo.
        print(f"\n JUNTAS entre etapas contiguas de {clave}  (declarado en un lado + medido en el otro):")
        for i in range(len(stages) - 1):
            A, B = stages[i], stages[i + 1]
            da, db = A.get("_declarados_que_cubren") or set(), B.get("_declarados_que_cubren") or set()
            ma, mb = A.get("_medido") or {}, B.get("_medido") or {}
            ua, ub = A.get("_umbral", 1), B.get("_umbral", 1)
            puente = ([d for d in da if len(mb.get(d, [])) >= ub]
                      + [d for d in db if len(ma.get(d, [])) >= ua])
            if puente:
                print(f"   COSIDA   {A['id']:<24} -> {B['id']:<24} cubre los dos lados: {puente[0]}")
                continue
            con_arista = [(x, y) for x in da for y in db if frozenset((x, y)) in pares]
            if con_arista:
                print(f"   ARISTA   {A['id']:<24} -> {B['id']:<24} {con_arista[0][0]} ~ {con_arista[0][1]}")
                continue
            # cita-sin-narracion: contiene los dos lados y nadie lo declaro para ninguna etapa
            citas = sorted((set(ma) & set(mb)) - da - db,
                           key=lambda f: -(len(ma[f]) + len(mb[f])))
            citas = [f for f in citas if len(ma[f]) >= ua and len(mb[f]) >= ub]
            juntas.append(f"{clave}: {A['id']} -> {B['id']}  "
                          f"({', '.join(sorted(da)[:2]) or 'SIN CUBRIDOR'} | {', '.join(sorted(db)[:2]) or 'SIN CUBRIDOR'})"
                          + (f"   [solo la CITAN: {', '.join(citas[:2])}]" if citas else ""))
            print(f"   SECA >>> {A['id']:<24} -> {B['id']:<24} ningun artefacto juzgado cubre los dos lados"
                  + (f"  (solo la citan: {citas[0]})" if citas else ""))

    # --- RESUMEN ------------------------------------------------------------------
    print(f"\n{'=' * 78}")
    print(f"{n_circ} circuito(s) · {n_etapas} etapas · {len(juntas)} junta(s) seca(s) · "
          f"{len(avisos)} candidato(s) · {len(fallos)} fallo(s)")

    if juntas:
        print("\nJUNTAS SECAS (mapa, NO fallo — es el trabajo abierto de H137):")
        for j in juntas:
            print(f"   - {j}")
        print("   Una junta seca no se arregla bajando el umbral del grafo: la similitud no")
        print("   puede expresar secuencia. Se cose declarandola aqui o escribiendo el tramo.")

    if avisos:
        print("\nCANDIDATOS (pista de donde mirar, no veredicto):")
        for w in avisos:
            print(f"   - {w}")

    if fallos:
        print("\nFALLOS:")
        for f in fallos:
            print(f"   X {f}")
        print("\nFALLO — el circuito declarado ya no coincide con lo que hay en companions/")
        return 1

    print("\nOK — todas las etapas declaradas siguen cubiertas por un companion que las contiene")
    return 0


if __name__ == "__main__":
    sys.exit(main())
