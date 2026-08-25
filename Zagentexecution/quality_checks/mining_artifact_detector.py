"""GATE DE CIERRE: ¿construiste un MINERO esta sesion y no te diste cuenta?

EL PROBLEMA, DICHO POR EL OPERADOR Y MEDIDO EL MISMO DIA
    "Ese tipo de mineria es la que vas generando en cada sesion y no eres capaz de entender que
    la generaste."

    Es exacto. El 2026-08-25 se construyeron CUATRO artefactos que minan -- el minero del canal
    batch input, el de naturaleza de interfaces, el bus de mineros y el propio censo -- y ninguno
    se reconocio como tal hasta que el operador lo señalo. Y hay mas, mas viejos: el metodo que
    identifico ALLOS vivio como prompt; saber que VARIANTE se ejecuta vive dentro de un quality
    check; el mapa cuenta -> nodo de balance se deriva en vivo y no se guarda; y de los quince
    scripts que analizan transportes solo uno esta registrado.

    El censo de capacidad (A32) barre el repo entero y contesta "que hay suelto por ahi". Esta
    puerta contesta otra pregunta, que es la que se olvida: **que acabo de crear YO, y lo
    registre?** La primera se puede posponer; la segunda caduca al cerrar la sesion.

QUE DETECTA
    1. SCRIPT MINERO NUEVO   -- fichero .py añadido o tocado en esta sesion que lee datos de
                                EVENTO y saca patrones, sin algoritmo que lo declare
    2. CLASIFICADOR NUEVO    -- store nuevo que asigna cosas a GRUPOS (x -> clase). Es el caso
                                que mas se escapa porque no parece codigo: parece un resultado
    3. AGENTE QUE MINA       -- .md de agente nuevo o tocado que describe un metodo de mineria
                                sin algoritmo que lo pueda repetir sin el

POR QUE IMPORTA MAS QUE PERDER UN DATO
    Un dato perdido se nota al dia siguiente. Un MINERO perdido no se nota nunca: el siguiente
    analisis simplemente vuelve a derivarlo, tarda mas, y a veces llega a otra respuesta.

Uso:  python Zagentexecution/quality_checks/mining_artifact_detector.py [--desde <ref-git>]
      por defecto mira los commits de hoy y lo que este sin commitear
"""
QUALITY_CHECK = {
    "tier": "gate",
    "needs": "files",
    "what": ("mineros construidos EN ESTA SESION y no registrados como algoritmo: la capacidad "
             "se pierde al cerrar y nadie se entera"),
}
# ----------------------------------------------------------------------------
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALGOS = os.path.join(ROOT, "brain_v2", "methods", "algorithms.json")

# Nombres de tabla de EVENTO. Se buscan con FRONTERA DE PALABRA, no como subcadena: 'vari'
# suelto casaba con "varias", "variable" y "varios", y marco de minero a tres generadores que
# no leen una sola tabla de evento. Es el mismo defecto que este gate existe para cazar --
# medir la forma en vez del efecto -- cometido por el gate en su primera corrida.
EVENTO = ["rsau_audit_history", "cdhdr_history", "cdhdr", "cdpos", "apqi", "apqd", "e070",
          "e071", "tbtco", "tbtcp", "edidc", "varid", "tvarv", "balhdr", "sapf100_vari"]

# Generados por diseño: el grafo y sus derivados no son "un clasificador sin promover", son EL
# sitio donde aterrizan los clasificadores. Marcarlos convertiria el gate en ruido permanente.
NO_SON_HALLAZGO = {
    "brain_state.json": "es el grafo: el sitio donde ATERRIZAN los clasificadores, no uno mas",
    "brain_v2_graph.json": "derivado del grafo",
    "entity_index.json": "indice derivado",
    "build_brain_state.py": ("es el CONSTRUCTOR del grafo: ingiere lo que los mineros "
                             "produjeron. Ingerir no es minar"),
    "rebuild_all.py": "orquestador del rebuild",
}
DESCUBRE = ["group by", "counter(", "defaultdict", "most_common", "discover", "descubr",
            "classif", "clasific", "pattern", "patron", "variant", "conform", "agrupa"]
# Un store que asigna cosas a GRUPOS es un clasificador aunque no lo parezca.
CLASIFICA = ["dominio", "domain", "clase", "class", "kind", "tipo", "categoria", "grupo",
             "cluster", "naturaleza", "nature"]


def git(*args):
    try:
        return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace").stdout
    except Exception:
        return ""


def tocados(desde):
    out = set()
    for linea in git("diff", "--name-only", desde, "HEAD").splitlines():
        if linea.strip():
            out.add(linea.strip())
    for linea in git("status", "--porcelain").splitlines():
        p = linea[3:].strip()
        if p:
            out.add(p)
    return sorted(out)


def main():
    desde = "HEAD~12"
    if "--desde" in sys.argv:
        desde = sys.argv[sys.argv.index("--desde") + 1]
    try:
        algos = json.load(open(ALGOS, encoding="utf-8")).get("algorithms") or {}
    except Exception:
        algos = {}
    registrados = {os.path.basename(str(b)).lower()
                   for a in algos.values() for b in (a.get("bound_in") or [])}
    texto_reg = json.dumps(algos, ensure_ascii=False).lower()

    h = []
    for rel in tocados(desde):
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.isfile(p) or any(x in rel for x in ("__pycache__", "venv/", "_obsolete/")):
            continue
        nom = os.path.basename(rel)
        try:
            t = open(p, encoding="utf-8", errors="ignore").read().lower()
        except Exception:
            continue

        if nom in NO_SON_HALLAZGO:
            continue
        if rel.endswith(".py"):
            ev = {e for e in EVENTO if re.search(r"\b" + re.escape(e) + r"\b", t)}
            ds = {v for v in DESCUBRE if v in t}
            if ev and ds and not (len(ev) < 2 and len(ds) < 3):
                if nom.lower() not in registrados:
                    h.append({"que": "SCRIPT MINERO SIN REGISTRAR", "artefacto": rel,
                              "senales": sorted(ev)[:4],
                              "por_que": ("lee datos de EVENTO y saca patrones de ellos. Si no "
                                          "se registra, al cerrar la sesion nadie sabra que "
                                          "existe ni como se corre")})
        elif rel.endswith(".json") and rel.startswith(("brain_v2/", "process_mining/")):
            campos = {c for c in CLASIFICA if f'"{c}"' in t}
            if len(campos) >= 2 and nom.lower() not in texto_reg:
                h.append({"que": "CLASIFICADOR SIN PROMOVER", "artefacto": rel,
                          "senales": sorted(campos)[:4],
                          "por_que": ("asigna cosas a GRUPOS y ningun algoritmo lo declara en "
                                      "lands_in. Es el caso que mas se escapa porque no parece "
                                      "codigo: parece un resultado")})
        elif rel.endswith(".md") and "/agents/" in rel.replace(os.sep, "/"):
            if sum(1 for e in EVENTO if e in t) >= 2 and nom[:-3].lower() not in texto_reg:
                h.append({"que": "AGENTE QUE MINA SIN ALGORITMO", "artefacto": rel,
                          "senales": ["describe mineria sobre datos de evento"],
                          "por_que": ("su metodo solo vive en el prompt: no se puede repetir, "
                                      "programar, gatear ni comparar con la corrida anterior")})

    rep = {"_que_comprueba": "mineros construidos en esta sesion y no registrados",
           "_por_que": ("un dato perdido se nota manana; un minero perdido no se nota nunca, "
                        "porque el siguiente analisis vuelve a derivarlo sin saberlo"),
           "desde": desde, "hallazgos": h}
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if h else 0

    print(f"[minero nuevo?] revisando lo tocado desde {desde}")
    if not h:
        print("  OK - todo lo que mina de esta sesion esta registrado")
        return 0
    print(f"  {len(h)} artefacto(s) que minan y no estan registrados:\n")
    for x in h:
        print(f"  [{x['que']}] {x['artefacto']}")
        print(f"      {x['por_que']}")
        print(f"      senales: {', '.join(x['senales'])}")
    print("\n  Registralo en brain_v2/methods/algorithms.json con su modo de fallo -- que es el")
    print("  campo que vale -- o di por que no es un minero. Ahora, no en la proxima sesion:")
    print("  esto caduca al cerrar.")
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
