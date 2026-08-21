"""
incident_domain_knowledge_check.py — ¿cada incidente dejó CONOCIMIENTO DE PROCESO, o solo un caso?

Un incidente es la OCASION; el proceso que hay detras es el producto. Si un incidente se cierra
con su documento de caso y nada mas, el proximo igual vuelve a costar lo mismo: el conocimiento
esta en un expediente, no en el dominio.

Medido el 2026-08-21: **11 de 13 incidentes no tenian documento de proceso en su dominio**. Los
dos que si lo tenian son los dos que se tocaron ese dia, y solo porque JP lo pidio explicitamente.
Dos de los huerfanos -- INC-000011781 y INC-000006313, autorizaciones bancarias de BCM, anadir y
quitar personas -- son el mismo patron que el alta de cuentas: dos casos del mismo proceso, sin
el proceso escrito en ninguna parte.

Comprueba TRES cosas, y las tres fallan distinto:
  1. El dominio del incidente EXISTE en el registro (domains.json). Un incidente apuntando a una
     etiqueta sin registro es conocimiento colgando de nada -- le paso a Closing_Activities
     durante cinco sesiones.
  2. Ese dominio tiene al menos un documento de PROCESO, no solo docs de caso.
  3. El documento de proceso MENCIONA al incidente, o el incidente lo declara en
     `generates_process_knowledge`. Un doc que no cita el caso que lo origino no es trazable.

Solo LECTURA de ficheros del repo. No toca SAP.

Uso:
    python incident_domain_knowledge_check.py            # exit 1 si hay huerfanos
    python incident_domain_knowledge_check.py --strict   # exit 1 tambien por el punto 3
"""

QUALITY_CHECK = {
    "tier": "gate",   # gate | live | analysis | quarantined
    "needs": "files",
    "what": "todo incidente tiene dominio con registro y doc de PROCESO; avisa si hay 2+ del mismo tipo sin el",
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

# Un doc es de PROCESO si su nombre lo declara. Deliberadamente conservador: preferimos pedir un
# nombre explicito a adivinar por el contenido, porque un falso "si" aqui esconde el hueco.
PROCESO = ("process", "proceso", "method", "metodo", "runsheet", "calendar", "governance",
           "procedure", "procedimiento", "workflow", "lifecycle")


def load(p):
    return json.load(io.open(os.path.join(REPO, p), encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="exigir tambien que el doc de proceso cite al incidente")
    a = ap.parse_args()

    inc = load("brain_v2/incidents/incidents.json")
    dom = load("brain_v2/domains/domains.json")["domains"]
    onto = load("brain_v2/capability_model/ontology.json")
    alias = {}
    for d in onto["domains"]:
        alias[d["canonical_key"]] = d["canonical_key"]
        for x in (d.get("aliases") or []):
            alias[x] = d["canonical_key"]
    cross = {x["key"] for x in onto.get("cross_cutting_keys", [])}

    sin_registro, sin_proceso, sin_cita = [], [], []
    print("INCIDENTE -> DOMINIO -> CONOCIMIENTO DE PROCESO\n")
    print("%-24s %-12s %-22s %s" % ("INCIDENTE", "TIPO", "DOMINIO", "DOC DE PROCESO"))
    for i in sorted(inc, key=lambda z: (z.get("incident_type") or "", z["id"])):
        d = (i.get("domain") or "").strip()
        canon = alias.get(d, d)
        rec = dom.get(canon) or dom.get(d)
        if not rec:
            nota = ("clave transversal, no dominio" if d in cross else "SIN REGISTRO")
            sin_registro.append((i["id"], d, nota))
            print("%-24s %-12s %-22s *** %s ***"
                  % (i["id"], i.get("incident_type") or "-", d[:22], nota))
            continue
        docs = rec.get("knowledge_docs", []) or []
        proc = [x for x in docs if any(k in x.lower() for k in PROCESO)]
        if not proc:
            sin_proceso.append((i["id"], i.get("incident_type") or "-", canon))
            print("%-24s %-12s %-22s *** NINGUNO de %d docs es de proceso ***"
                  % (i["id"], i.get("incident_type") or "-", canon[:22], len(docs)))
            continue
        # ¿alguno de esos docs cita al incidente?
        cita = bool(i.get("generates_process_knowledge"))
        for p in proc:
            fp = os.path.join(REPO, p)
            if os.path.exists(fp):
                try:
                    if re.search(re.escape(i["id"]), io.open(fp, encoding="utf-8").read()):
                        cita = True
                        break
                except Exception:
                    pass
        if not cita:
            sin_cita.append((i["id"], canon, os.path.basename(proc[0])))
        print("%-24s %-12s %-22s %s%s"
              % (i["id"], i.get("incident_type") or "-", canon[:22],
                 os.path.basename(proc[0])[:40], "" if cita else "   (no cita el incidente)"))

    n = len(inc)
    print("\n" + "=" * 78)
    print("%d incidentes · %d sin registro de dominio · %d sin doc de proceso · %d sin cita"
          % (n, len(sin_registro), len(sin_proceso), len(sin_cita)))
    print("=" * 78)
    if sin_registro:
        print("\nSIN REGISTRO DE DOMINIO — el incidente cuelga de una etiqueta que no existe:")
        for i, d, nota in sin_registro:
            print("   %-24s domain=%-18s %s" % (i, d, nota))
    if sin_proceso:
        print("\nSIN CONOCIMIENTO DE PROCESO — hay caso, no hay proceso. Al SEGUNDO incidente del")
        print("mismo tipo esto deja de ser deuda y pasa a ser coste recurrente:")
        agr = {}
        for i, t, d in sin_proceso:
            agr.setdefault((d, t), []).append(i)
        for (d, t), ids in sorted(agr.items(), key=lambda x: -len(x[1])):
            marca = "   <== DOS O MAS: el proceso ya se puede escribir" if len(ids) > 1 else ""
            print("   %-22s %-12s %s%s" % (d, t, ", ".join(ids), marca))
    if sin_cita:
        print("\nSIN TRAZA — el doc de proceso existe pero no cita al incidente que lo origino:")
        for i, d, p in sin_cita:
            print("   %-24s %-20s %s" % (i, d, p))

    rc = 1 if (sin_registro or sin_proceso) else 0
    if a.strict and sin_cita:
        rc = 1
    print("\n%s" % ("OK — todo incidente tiene dominio con proceso" if rc == 0 else
                    "HAY INCIDENTES QUE NO DEJARON PROCESO — el conocimiento se queda en el caso"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
