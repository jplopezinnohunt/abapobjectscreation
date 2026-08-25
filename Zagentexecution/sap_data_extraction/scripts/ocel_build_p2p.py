"""
ocel_build_p2p.py  —  AN-OCEL2: build the OCEL 2.0 object-centric substrate.
============================================================================
Applies the #1 verified finding (OCEL 2.0, research w3t7ufrbg): one event references
MULTIPLE object types — no forced single case notion. Built from P2P (Gold DB), the
verified canonical SQLite format. Object types: PurchaseOrder, Vendor, PurchasingGroup.
Events: PO Created (EKKO), Goods Receipt / Invoice Receipt (EKBE VGABE 1/2).

This is the substrate the field calls object-centric process mining (OCPM) — we only
ever did flat single-case DFG. Output: p2p.ocel2.sqlite + object-centric DFG summary.
"""
import os, sqlite3, json
from pathlib import Path
import pandas as pd
import pm4py
from pm4py.objects.ocel.obj import OCEL

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "process_mining"))
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None

ROOT = Path(r"c:\Users\jp_lopez\projects\abapobjectscreation")
GOLD = ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUTDIR = ROOT / "Zagentexecution" / "sap_data_extraction" / "process_discovery"
OCEL_SQLITE = OUTDIR / "p2p.ocel2.sqlite"
SUMMARY = OUTDIR / "p2p_ocel2_summary.json"

SINCE = "20240101"   # bound the first store; scales by widening this


def run():
    con = sqlite3.connect(GOLD)
    po = pd.read_sql_query(
        f"SELECT EBELN,AEDAT,LIFNR,EKGRP FROM ekko WHERE AEDAT>='{SINCE}' AND AEDAT<>''", con)
    poset = set(po["EBELN"])
    ekbe = pd.read_sql_query(
        "SELECT EBELN,EBELP,GJAHR,BELNR,BUZEI,VGABE,BUDAT FROM ekbe "
        "WHERE VGABE IN ('1','2') AND BUDAT IS NOT NULL AND BUDAT<>''", con)
    con.close()
    ekbe = ekbe[ekbe["EBELN"].isin(poset)]

    vend = dict(zip(po["EBELN"], po["LIFNR"]))
    pgrp = dict(zip(po["EBELN"], po["EKGRP"]))

    rows = []  # (eid, activity, ddate, oid, otype, qualifier)
    def emit(eid, act, ddate, ebeln):
        rows.append((eid, act, ddate, f"PO:{ebeln}", "PurchaseOrder", "po"))
        v = vend.get(ebeln)
        if v and str(v).strip():
            rows.append((eid, act, ddate, f"VEND:{v}", "Vendor", "vendor"))
        g = pgrp.get(ebeln)
        if g and str(g).strip():
            rows.append((eid, act, ddate, f"PG:{g}", "PurchasingGroup", "purch_group"))

    for r in po.itertuples(index=False):
        emit(f"POC-{r.EBELN}", "PO Created", r.AEDAT, r.EBELN)
    LAB = {"1": "Goods Receipt", "2": "Invoice Receipt"}
    for r in ekbe.itertuples(index=False):
        eid = f"{r.VGABE}-{r.EBELN}-{r.EBELP}-{r.GJAHR}-{r.BELNR}-{r.BUZEI}"
        emit(eid, LAB[r.VGABE], r.BUDAT, r.EBELN)

    rel = pd.DataFrame(rows, columns=["ocel:eid", "ocel:activity", "ddate",
                                      "ocel:oid", "ocel:type", "ocel:qualifier"])
    rel["ocel:timestamp"] = pd.to_datetime(rel["ddate"], format="%Y%m%d", errors="coerce")
    rel = rel.dropna(subset=["ocel:timestamp"]).drop(columns=["ddate"]).reset_index(drop=True)

    events = (rel[["ocel:eid", "ocel:activity", "ocel:timestamp"]]
              .drop_duplicates("ocel:eid").reset_index(drop=True))
    objects = (rel[["ocel:oid", "ocel:type"]]
               .drop_duplicates("ocel:oid").reset_index(drop=True))

    ocel = OCEL(events=events, objects=objects, relations=rel)
    if OCEL_SQLITE.exists():
        OCEL_SQLITE.unlink()
    pm4py.write_ocel2_sqlite(ocel, str(OCEL_SQLITE))

    otypes = pm4py.ocel_get_object_types(ocel)
    ot_acts = pm4py.ocel_object_type_activities(ocel)
    obj_counts = objects["ocel:type"].value_counts().to_dict()
    act_counts = events["ocel:activity"].value_counts().to_dict()

    summary = {
        "_design": "OCEL 2.0 object-centric store for P2P (AN-OCEL2). One event references multiple object types — no single case notion (the verified OCEL 2.0 model).",
        "since": SINCE, "store": str(OCEL_SQLITE.name),
        "events": int(len(events)), "objects": int(len(objects)), "relations": int(len(rel)),
        "object_types": list(otypes),
        "objects_per_type": {k: int(v) for k, v in obj_counts.items()},
        "activities": {k: int(v) for k, v in act_counts.items()},
        "object_type_activities": {k: list(v) for k, v in ot_acts.items()},
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"=== OCEL 2.0 store built (since {SINCE}) ===")
    print(f"events {len(events):,} | objects {len(objects):,} | relations {len(rel):,}")
    print(f"object types: {list(otypes)}")
    print(f"objects/type: {obj_counts}")
    print(f"activities: {act_counts}")
    print(f"\nwrote OCEL 2.0 SQLite: {OCEL_SQLITE}")
    print(f"summary: {SUMMARY}")

    # object-centric DFG — the algorithm we never used (one event, many objects)
    try:
        ocdfg = pm4py.discover_ocdfg(ocel)
        n_edges = sum(len(v) for v in ocdfg.get("edges", {}).get("event_couples", {}).values()) \
            if isinstance(ocdfg.get("edges"), dict) else 0
        print(f"\nOBJECT-CENTRIC DFG discovered: {len(ocdfg.get('activities', []))} activities, "
              f"{n_edges} object-typed edges (per-object-type flows, not flattened).")
    except Exception as e:
        print(f"\n(ocdfg note: {str(e)[:100]})")


if __name__ == "__main__":
    run()
