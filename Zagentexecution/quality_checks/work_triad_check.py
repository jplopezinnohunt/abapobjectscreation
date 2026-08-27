"""
work_triad_check.py — de cada trabajo quedan TRES cosas, y hay que comprobar las tres.

EL MODELO (JP, 2026-08-26). Todo trabajo que descubre algo deja tres piezas distintas, y se
pierden por separado:

    1. EL OBJETO   lo que descubriste          -> ¿esta clasificado donde PERTENECE?
    2. EL PROCESO  como funciona eso           -> ¿hay doc de proceso y companion?
    3. EL METODO   como lo descubriste         -> ¿esta registrado como minero/algoritmo?

POR QUE HACEN FALTA LAS TRES. Medido sobre INC-000016471 (la caida de ADS, s105): el PROCESO
quedo completo -- `document_output_model.md` + su companion -- porque era el entregable. El
OBJETO quedo a medias: `hq-sap-sbp` esta en `interface_inventory.json` como el otro extremo de
un destino, pero NO en el perfil de instalacion como SISTEMA, asi que el paisaje sigue creyendo
que solo hay D01/V01/P01 cuando por esa cuarta maquina sale todo PDF de la casa. Y el METODO
casi se pierde entero: los tres scripts que midieron la ventana de la caida llevaban un dia
existiendo solo en disco, sin commitear y sin registrar.

**Lo que se nota se guarda; lo que no se nota, no.** Este check hace que se note.

DOS EJES QUE NO HAY QUE CONFUNDIR
  * Un OBJETO puede ser varias cosas a la vez. Solution Manager es una INTERFAZ (por donde
    hablamos con el) y un SISTEMA (una maquina del paisaje). Registrarlo como lo primero no lo
    registra como lo segundo, y el hueco no se ve mirando el sitio donde dolio.
  * Un METODO de EXPLORACION (un minero: descubre lo que no sabias que existia) no es lo mismo
    que un ALGORITMO de CALCULO (contesta lo que ya sabes preguntar). Hoy el toolgraph los
    colapsa en `ALGORITMO`, y por eso "comparar tablas entre sistemas" no esta registrado como
    nada: no es un algoritmo, es un minero que nadie declaro.

Solo LECTURA de ficheros del repo. No toca SAP.

Uso:
    python work_triad_check.py                    # todos los incidentes con hallazgo
    python work_triad_check.py --incident INC-000016471
"""

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",
    "needs": "files",
    "what": "de cada trabajo quedan tres cosas -- objeto, proceso y metodo -- y comprueba las tres",
    "args": "[--incident INC-xxxx]",
}

import argparse
import glob
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

PROCESO = ("process", "proceso", "method", "metodo", "model", "modelo", "runsheet", "calendar",
           "governance", "procedure", "procedimiento", "workflow", "lifecycle", "rules",
           "reglas", "design", "diseno", "runbook", "protocol", "protocolo")


def load(p):
    fp = os.path.join(REPO, p)
    return json.load(io.open(fp, encoding="utf-8")) if os.path.exists(fp) else None


def texto(p):
    fp = os.path.join(REPO, p)
    return io.open(fp, encoding="utf-8", errors="ignore").read() if os.path.exists(fp) else ""


def objetos_del_incidente(inc):
    """Los nombres que el incidente dice haber tocado. Es lo que hay que poder localizar."""
    out = set()
    for k in ("related_objects", "objects", "systems"):
        v = inc.get(k)
        if isinstance(v, list):
            out |= {x for x in v if isinstance(x, str) and len(x) > 2}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--incident", default="")
    a = ap.parse_args()

    inc = load("brain_v2/incidents/incidents.json") or []
    dom = (load("brain_v2/domains/domains.json") or {}).get("domains", {})
    onto = load("brain_v2/capability_model/ontology.json") or {}
    alias = {}
    for d in onto.get("domains", []):
        alias[d["canonical_key"]] = d["canonical_key"]
        for x in (d.get("aliases") or []):
            alias[x] = d["canonical_key"]

    # DONDE puede aterrizar un objeto. La primera version de este check miraba SOLO los tres
    # registros de infraestructura y marcaba como "sin sitio" cuentas de mayor y clases ABAP que
    # viven en el indice de entidades: denominador incompleto, el mismo fallo que este check
    # existe para cazar. Un objeto esta aterrizado si aparece en CUALQUIERA de sus casas posibles.
    perfil = texto("brain_v2/system_profile/model_graph.json")
    interf = texto("brain_v2/interface_inventory.json") + texto("brain_v2/interface_boundary.json")
    algos = texto("brain_v2/methods/algorithms.json")
    entidades = texto("brain_v2/entity_index.json")
    codigo = texto("brain_v2/code_inventory.json")
    CASAS = perfil + interf + algos + entidades + codigo

    casos = [x for x in inc if not a.incident or x.get("id") == a.incident]
    if not casos:
        print("no hay incidente %s" % a.incident)
        return 2

    print("DE CADA TRABAJO QUEDAN TRES COSAS: objeto · proceso · metodo\n")
    print("%-24s %-9s %-9s %-9s %s" % ("INCIDENTE", "OBJETO", "PROCESO", "METODO", "QUE FALTA"))
    incompletos = []
    for x in sorted(casos, key=lambda z: z["id"]):
        canon = alias.get((x.get("domain") or "").strip(), (x.get("domain") or "").strip())
        rec = dom.get(canon) or {}

        # 2 · PROCESO: doc de proceso en el dominio + companion
        docs = rec.get("knowledge_docs", []) or []
        proc = [d for d in docs if any(k in d.lower() for k in PROCESO)]
        comp = rec.get("companions", []) or []
        n_proc = "OK" if (proc and comp) else ("a medias" if (proc or comp) else "NO")

        # 3 · METODO: el incidente declara el instrumento, o hay un task folder con scripts
        tasks = glob.glob(os.path.join(REPO, "Zagentexecution", "tasks",
                                       "*%s*" % x["id"].replace("INC-", "").lower(), "*.py"))
        declara = bool(x.get("instruments") or x.get("recurring_checks")
                       or rec.get("recurring_checks"))
        registrado = any(os.path.basename(t)[:-3] in algos for t in tasks) if tasks else False
        n_met = "OK" if (registrado or declara) else ("script sin registrar" if tasks else "NO")

        # 1 · OBJETO: cada nombre del incidente, ¿esta en algun registro?
        objs = objetos_del_incidente(x)
        perdidos = []
        for o in objs:
            if not re.search(re.escape(o.lstrip("0") or o), CASAS, re.I):
                perdidos.append(o)
        n_obj = "OK" if objs and not perdidos else ("%d sin sitio" % len(perdidos) if perdidos
                                                   else "sin objetos")

        falta = []
        if n_obj.endswith("sin sitio"):
            falta.append("objeto: " + ", ".join(sorted(perdidos)[:3]))
        if n_proc != "OK":
            falta.append("proceso: " + ("falta companion" if proc else "falta doc de proceso"))
        if n_met != "OK":
            falta.append("metodo: " + ("registrar el minero" if tasks else "sin instrumento"))
        if falta:
            incompletos.append((x["id"], falta))
        print("%-24s %-9s %-9s %-9s %s"
              % (x["id"], n_obj, n_proc, n_met, " · ".join(falta)[:60]))

    print("\n" + "=" * 78)
    print("%d trabajos · %d con alguna de las tres piezas sin aterrizar"
          % (len(casos), len(incompletos)))
    print("=" * 78)
    for i, f in incompletos:
        print("\n  %s" % i)
        for x in f:
            print("     - %s" % x)
    if incompletos:
        print("\nUn trabajo no esta cerrado cuando el entregable existe: lo esta cuando las TRES")
        print("piezas viven donde alguien las va a encontrar sin saber que existen.")
    return 1 if incompletos else 0


if __name__ == "__main__":
    sys.exit(main())
