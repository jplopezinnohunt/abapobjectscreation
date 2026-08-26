"""TODO LO PENDIENTE, DE TODAS LAS FUENTES A LA VEZ — no de una auditoria de un tier.

POR QUE EXISTE
    El operador pregunto «¿esa es toda la lista?» despues de que le diera los pendientes de
    `run_all --tier gate`. Y no lo era: esa auditoria descubre 50 checks y corre 24. Los otros
    26 son de otro tier y NO SE MIRARON. Ademas, lo pendiente vive en seis sitios que nadie
    junta: la auditoria, el PMO, el grafo de herramientas, los claims abiertos, los algoritmos
    con trabajo declarado y los stores que aun no aterrizan.

    Dar una lista parcial como si fuera completa es la misma clase de error que este proyecto
    persigue todo el rato: un numero que parece un total y es un trozo.

Uso:  python brain_v2/methods/pending_inventory.py [--json]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(ROOT, "brain_v2")


def carga(*p, d=None):
    try:
        with open(os.path.join(*p), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return d if d is not None else {}


def main():
    out = {}

    # ---- 1. AUDITORIA: lo corrido Y lo NO corrido -------------------------------------
    S = carga(B, "quality_checks_state.json")
    corridos = {r["script"] for r in (S.get("results") or [])}
    todos = set()
    qd = os.path.join(ROOT, "Zagentexecution", "quality_checks")
    if os.path.isdir(qd):
        todos = {f for f in os.listdir(qd) if f.endswith(".py") and not f.startswith("_")}
    hallazgos = [r["script"] for r in (S.get("results") or [])
                 if r.get("outcome") in ("FINDING", "ERROR", "UNGATED", "TIMEOUT")]
    out["auditoria"] = {
        "_ojo": (f"la ultima corrida fue tier='{S.get('tier')}': descubrio "
                 f"{S.get('discovered')} y corrio {S.get('ran')}. LO NO CORRIDO NO ES LIMPIO, "
                 f"es NO MIRADO"),
        "con_hallazgo": sorted(hallazgos),
        "sin_declarar_no_corren_nunca": sorted(S.get("unclassified") or []),
        "en_cuarentena": sorted(S.get("quarantined") or []),
        "NO_CORRIDOS_EN_LA_ULTIMA": sorted(todos - corridos - {"run_all.py"}),
    }

    # ---- 2. GRAFO DE HERRAMIENTAS ------------------------------------------------------
    T = carga(B, "toolgraph.json")
    out["herramientas"] = T.get("salud") or {}

    # ---- 3. ALGORITMOS con trabajo declarado -------------------------------------------
    A = (carga(B, "methods", "algorithms.json").get("algorithms") or {})
    out["algoritmos"] = {
        "sin_aterrizar": sorted(k for k, v in A.items()
                                if "PENDIENTE" in str(v.get("lands_in") or "").upper()),
        "con_defecto_abierto": sorted(k for k, v in A.items() if v.get("_sigue_abierto")),
        "estado_no_sano": sorted(k for k, v in A.items()
                                 if str(v.get("state", "")).upper()
                                 in ("DEFECTO_VIVO", "ROTO", "MUERTO", "FRAGILE")),
    }

    # ---- 4. CLAIMS que piden algo -------------------------------------------------------
    C = carga(B, "claims", "claims.json", d=[])
    out["claims"] = {
        "needs_review": sorted(c["id"] for c in C if c.get("needs_review")),
        "con_deuda_de_medida": sorted(c["id"] for c in C
                                      if c.get("_para_re_medir")
                                      and "HECHO" not in str(c.get("_para_re_medir"))),
        "abiertos": sum(1 for c in C if str(c.get("status") or "").upper() == "OPEN"),
    }

    # ---- 5. PMO: el registro humano de pendientes ---------------------------------------
    pmo = os.path.join(ROOT, ".agents", "intelligence", "PMO_BRAIN.md")
    items = []
    if os.path.isfile(pmo):
        for ln in open(pmo, encoding="utf-8", errors="ignore"):
            m = re.match(r"^\s*[-*]?\s*\*?\*?(H\d+)\b[^\n]{0,150}", ln)
            if m:
                items.append(m.group(0).strip()[:150])
    out["pmo"] = {"_fuente": ".agents/intelligence/PMO_BRAIN.md", "cuantos": len(items),
                  "items": items[:40]}

    # ---- 6. HALLAZGOS SIN ATERRIZAR ------------------------------------------------------
    U = carga(B, "methods", "unlanded_discoveries.json")
    # La clave es `items`, no `identifiers`. La primera version adivino el nombre y devolvio
    # CERO donde hay 37 -- un cero que se lee como "nada pendiente" es peor que no medirlo.
    # Se lee la clave de verdad y, si no esta, se DICE en vez de dar un numero.
    items = U.get("items")
    out["hallazgos_sin_aterrizar"] = (
        {"cuantos": len(items), "de_ellos_HIGH": U.get("_high"),
         "_que_es": "identificadores propios que el codigo toca y el brain no explica",
         "_ojo": "los HIGH gatean rutinas que pueden BLOQUEAR una contabilizacion"}
        if isinstance(items, list) else
        {"cuantos": None, "_no_se_pudo_leer": f"claves presentes: {sorted(U)[:8]}"})

    if "--json" in sys.argv:
        print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
        return 0

    print("=" * 78)
    print("TODO LO PENDIENTE — de las seis fuentes, no de una")
    print("=" * 78)
    a = out["auditoria"]
    print(f"\nAUDITORIA  {a['_ojo']}")
    print(f"  con hallazgo ................ {len(a['con_hallazgo'])}")
    print(f"  NO CORRIDOS en la ultima .... {len(a['NO_CORRIDOS_EN_LA_ULTIMA'])}  "
          f"<- no mirados, no limpios")
    print(f"  sin declarar (nunca corren) . {len(a['sin_declarar_no_corren_nunca'])}")
    print(f"  en cuarentena ............... {len(a['en_cuarentena'])}")
    h = out["herramientas"]
    print("\nHERRAMIENTAS")
    for k in ("skills_sin_ningun_lector", "algoritmos_que_no_leen_ningun_skill",
              "agentes_sin_instrumento_declarado", "instrumentos_rotos_o_con_defecto_vivo"):
        v = h.get(k) or {}
        print(f"  {k:38s} {v.get('cuantos', '?')}")
    ar = h.get("aristas_que_faltan_frente_a_las_que_hay") or {}
    print(f"  aristas LEE {ar.get('LEE')} frente a DEBERIA_LEER {ar.get('DEBERIA_LEER')}")
    al = out["algoritmos"]
    print("\nALGORITMOS")
    print(f"  sin aterrizar ............... {len(al['sin_aterrizar'])}  {al['sin_aterrizar']}")
    print(f"  con defecto abierto ......... {len(al['con_defecto_abierto'])}  "
          f"{al['con_defecto_abierto']}")
    print(f"  estado no sano .............. {len(al['estado_no_sano'])}  {al['estado_no_sano']}")
    cl = out["claims"]
    print("\nCLAIMS")
    print(f"  marcados needs_review ....... {len(cl['needs_review'])}  {cl['needs_review']}")
    print(f"  con deuda de medida ......... {len(cl['con_deuda_de_medida'])}  "
          f"{cl['con_deuda_de_medida']}")
    print(f"  abiertos .................... {cl['abiertos']}")
    print(f"\nPMO ............................ {out['pmo']['cuantos']} item(s)")
    u = out["hallazgos_sin_aterrizar"]
    print(f"HALLAZGOS SIN ATERRIZAR ........ {u.get('cuantos')}  "
          f"(HIGH, gatean rutina que puede BLOQUEAR: {u.get('de_ellos_HIGH')})")
    print("\n" + "=" * 78)
    print("LO NO CORRIDO EN LA ULTIMA AUDITORIA (por si se lee como limpio):")
    for n in a["NO_CORRIDOS_EN_LA_ULTIMA"]:
        print("   ", n)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
