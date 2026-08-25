"""
sap_process_discovery.py  —  L7 Process Intelligence engine (deterministic, pm4py)
=================================================================================
Builds event logs from the Gold DB (real data) and DISCOVERS processes:
DFG (process map), variants (paths), performance (cycle times/bottlenecks).
Capability #1 (UNDERSTAND) + calibration source for #3 (SIMULATE).

TWO event sources (the user's point: bkpf is only part — changes/logs are richer):
  * TRANSACTIONS — bkpf (FI documents).
  * CHANGES — cdhdr_history (change documents: object lifecycle, who changed what when).
    NOT `cdhdr`: verified 2026-07-31, that table is a strict SUBSET of cdhdr_history AND
    scope-filtered to 57 object classes of 72. Discovery run against it reports ZERO PBC
    activity where there are 3,449,049 change documents, and no Real Estate at all.
Cross many tables toward OCEL (object-centric) next.

Each config declares a SQL that returns columns: case_id, activity_raw, ddate, dtime, resource;
plus a label_map to make activity_raw readable. Generic engine, deterministic, auditable.

Usage:  python sap_process_discovery.py [config_name]
Configs: clearing_lifecycle | cdhdr_po | cdhdr_pr | cdhdr_vendor | cdhdr_entrysheet
"""
import os, sys, json, sqlite3
import pandas as pd
import pm4py

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
# La ruta se BUSCA subiendo hasta el directorio que CONTIENE process_mining; no se cuenta con
# dirname(). Contarla mal es como este bloque quedo ciego: dos dirname desde quality_checks/
# apuntan a Zagentexecution/process_mining, que no existe, el import fallaba en SILENCIO y el
# gate lo daba por bueno porque greppeaba la CADENA, no el efecto.
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d):
    if _os.path.isdir(_os.path.join(_d, "process_mining")):
        _sys.path.insert(0, _os.path.join(_d, "process_mining"))
        break
    _d = _os.path.dirname(_d)
try:
    # ImportError y no Exception: cubre "metodo.py no esta" sin tragarse un fallo REAL dentro
    # de metodo.py. Y AVISA: un minero que corre sin memoria tiene que decirlo, no callarlo.
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except ImportError as _e:
    print("  AVISO: corriendo SIN memoria de metodo (%s)" % _e)
    _aprendido = None

ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
OUTDIR = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "process_discovery")

BLART_LABEL = {
    "KR": "Vendor Invoice", "KG": "Vendor Credit Memo", "KZ": "Vendor Payment",
    "ZP": "Payment (Auto)", "ZV": "Payment Clearing", "RE": "Invoice Receipt (MM)",
    "WE": "Goods Receipt", "DZ": "Customer Payment", "DR": "Customer Invoice",
    "SA": "G/L Account Doc", "AB": "Clearing/Reset", "JV": "Journal Voucher",
    "PP": "Payroll Posting", "OP": "Opening/Recurring", "MF": "FX Valuation (FBB1)",
    "ZR": "Bank Statement Posting",
}
# Change-transaction codes -> readable activity (the lifecycle steps).
TCODE_LABEL = {
    "ME21N": "Create PO", "ME22N": "Change PO", "ME29N": "Release PO", "ME28": "Release PO (collective)",
    "ME23N": "Display PO", "ME51N": "Create PR", "ME52N": "Change PR", "ME54N": "Release PR", "ME55": "Release PR (collective)",
    "MIGO": "Goods/Invoice Movement", "MIRO": "Enter Invoice", "MIR7": "Park Invoice", "MRBR": "Release Invoice Block",
    "ML81N": "Create/Accept Service Entry", "ML85": "Release Service Entry",
    "XK01": "Create Vendor", "XK02": "Change Vendor", "XK05": "Block Vendor", "FK02": "Change Vendor (FI)",
    "MK01": "Create Vendor (Purch)", "MK02": "Change Vendor (Purch)",
    "FB01": "Post Document", "FB02": "Change Document", "FB08": "Reverse Document", "F-44": "Clear Vendor",
}


def _cdhdr_config(objectclass, label, where_extra=""):
    return {
        "label": label,
        "label_map": TCODE_LABEL,
        "sql": f"""
            SELECT OBJECTID AS case_id, TCODE AS activity_raw,
                   UDATE AS ddate, UTIME AS dtime, USERNAME AS resource
            FROM cdhdr_history
            WHERE OBJECTCLAS='{objectclass}' AND TCODE IS NOT NULL AND TCODE<>''
                  {where_extra}
        """,
    }


CONFIGS = {
    "clearing_lifecycle": {
        "label": "Invoice-to-Payment clearing lifecycle (case = clearing doc AUGBL)",
        "label_map": BLART_LABEL,
        "sql": """
            SELECT DISTINCT u.AUGBL AS case_id, b.BLART AS activity_raw,
                   b.BUDAT AS ddate, b.CPUTM AS dtime, b.USNAM AS resource
            FROM bseg_union u
            JOIN bkpf b ON u.BUKRS=b.BUKRS AND u.BELNR=b.BELNR AND u.GJAHR=b.GJAHR
            WHERE u.AUGBL IS NOT NULL AND u.AUGBL<>'' AND b.BUDAT >= '20250101'
        """,
    },
    "cdhdr_po":         _cdhdr_config("EINKBELEG", "Purchase Order lifecycle (CDHDR changes)"),
    "cdhdr_pr":         _cdhdr_config("BANF", "Purchase Requisition lifecycle (CDHDR changes)"),
    "cdhdr_vendor":     _cdhdr_config("KRED", "Vendor master change lifecycle (CDHDR)"),
    "cdhdr_entrysheet": _cdhdr_config("ENTRYSHEET", "Service Entry Sheet lifecycle (CDHDR)"),
    # JOBS — batch choreography: which programs run, in what order, each scheduling day.
    "jobs_batch": {
        "label": "Daily batch choreography (case = run day; activity = program)",
        "label_map": {},
        "sql": """
            SELECT o.STRTDATE AS case_id, p.PROGNAME AS activity_raw,
                   o.STRTDATE AS ddate, o.STRTTIME AS dtime, o.AUTHCKNAM AS resource
            FROM tbtco_history o
            JOIN tbtcp_history p ON o.JOBNAME=p.JOBNAME AND o.JOBCOUNT=p.JOBCOUNT
            WHERE o.STATUS='F' AND o.STRTDATE IS NOT NULL AND o.STRTDATE<>''
                  AND p.PROGNAME IS NOT NULL AND p.PROGNAME<>''
        """,
    },
    # PURCHASE-TO-PAY — PO lifecycle (case = PO). Events: PO Created (EKKO.AEDAT) +
    # EKBE history (VGABE 1=Goods Receipt, 2=Invoice Receipt; 9/3 left RAW — not SAP-
    # confirmed, flagged for classification, per never-infer rule). Resource = EKGRP
    # (EKKO/EKBE carry no user field). No intra-day time -> dtime 000000 (same-day order
    # arbitrary; PO/GR/IR usually differ by day). The AS-RUN P2P process for AN-G-P2P.
    "p2p_po_lifecycle": {
        "label": "Purchase-to-Pay PO lifecycle (case = PO; PO Created + GR/IR from EKBE)",
        "label_map": {"1": "Goods Receipt", "2": "Invoice Receipt",
                      "9": "EKBE VGABE=9 (unclassified)", "3": "EKBE VGABE=3 (unclassified)"},
        "sql": """
            SELECT EBELN AS case_id, 'PO Created' AS activity_raw,
                   AEDAT AS ddate, '000000' AS dtime, EKGRP AS resource
            FROM ekko WHERE AEDAT IS NOT NULL AND AEDAT<>''
            UNION ALL
            SELECT b.EBELN AS case_id, b.VGABE AS activity_raw,
                   b.BUDAT AS ddate, '000000' AS dtime, k.EKGRP AS resource
            FROM ekbe b LEFT JOIN ekko k ON b.EBELN=k.EBELN
            WHERE b.BUDAT IS NOT NULL AND b.BUDAT<>'' AND b.VGABE IN ('1','2','9','3')
        """,
    },
    # INTERFACES — IDoc flow per channel (message type + partner). EDIDC = current
    # state only (status history EDIDS not loaded); shows channel volume/status patterns.
    "interfaces_idoc": {
        "label": "IDoc interface patterns (case = message type; activity = status)",
        "label_map": {},
        "sql": """
            SELECT MESTYP AS case_id, ('IDoc '||IDOCTP||' status '||STATUS) AS activity_raw,
                   CREDAT AS ddate, CRETIM AS dtime, RCVPRN AS resource
            FROM edidc WHERE MESTYP IS NOT NULL AND MESTYP<>'' AND CREDAT IS NOT NULL AND CREDAT<>''
        """,
    },
}


def build_event_log(df, label_map):
    df = df.copy()
    df["activity"] = df["activity_raw"].map(lambda x: label_map.get(str(x).strip(), str(x).strip()))
    df["dtime"] = df["dtime"].fillna("000000").astype(str).str.replace(r"\D", "", regex=True).str.zfill(6).str[:6]
    df["ts"] = pd.to_datetime(df["ddate"].astype(str) + df["dtime"], format="%Y%m%d%H%M%S", errors="coerce")
    df = df.dropna(subset=["ts", "case_id"])
    df = df[df["case_id"].astype(str).str.strip() != ""]
    return pm4py.format_dataframe(df, case_id="case_id", activity_key="activity", timestamp_key="ts")


def run(config_name="clearing_lifecycle"):
    os.makedirs(OUTDIR, exist_ok=True)
    cfg = CONFIGS[config_name]
    print(f"=== DISCOVER: {cfg['label']} ===")
    con = sqlite3.connect(GOLD)
    df = pd.read_sql_query(cfg["sql"], con)
    con.close()
    print(f"raw rows: {len(df):,}")
    log = build_event_log(df, cfg["label_map"])
    n_cases = log["case:concept:name"].nunique()
    print(f"event log: {n_cases:,} cases, {len(log):,} events, {log['concept:name'].nunique()} activities")

    dfg, start, end = pm4py.discover_dfg(log)
    perf_dfg, _, _ = pm4py.discover_performance_dfg(log)
    traces = log.sort_values("time:timestamp").groupby("case:concept:name")["concept:name"].apply(lambda s: " -> ".join(s))
    variant_freq = traces.value_counts()

    # --- EVENT-LOG QUALITY (backlog #3): support threshold so we stop reporting
    # minimal-support noise/incomplete-case artifacts as 'bottlenecks'. ---
    MIN_SUPPORT = max(5, int(0.001 * n_cases))   # >=5 cases AND >=0.1% of cases
    dfg_supported = {e: c for e, c in dfg.items() if c >= MIN_SUPPORT}

    print(f"distinct variants: {variant_freq.shape[0]} | DFG edges {len(dfg)} -> {len(dfg_supported)} after support>={MIN_SUPPORT}")
    print("\nTOP 10 VARIANTS (real paths):")
    for trace, cnt in variant_freq.head(10).items():
        print(f"  {cnt:>7,}  {trace[:110]}")
    print("\nTOP DFG transitions:")
    for (a, b), cnt in sorted(dfg.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cnt:>8,}  {a} -> {b}")
    # bottlenecks ONLY among well-supported edges (no artifacts)
    perf_days = sorted(((v.get('mean', 0)/86400 if isinstance(v, dict) else v/86400, k)
                        for k, v in perf_dfg.items() if k in dfg_supported), reverse=True)
    print(f"\nSLOWEST transitions (support>={MIN_SUPPORT}) = REAL bottlenecks:")
    for days, (a, b) in perf_days[:6]:
        print(f"  {days:8.1f} d  ({dfg_supported.get((a,b),0):>6} cases)  {a} -> {b}")

    # --- REAL DISCOVERY ALGORITHM (backlog #4) + CONFORMANCE (backlog #1) ---
    # Inductive miner + token replay are heavy; at 600K events they don't finish in
    # budget (the documented OCPM scalability ceiling). SAMPLE the log for this step so
    # the NEW algorithms actually produce a result; the DFG above already used the full log.
    inductive = {}
    SAMPLE_CASES = 4000
    try:
        if n_cases > SAMPLE_CASES:
            log_s = pm4py.sample_cases(log, num_cases=SAMPLE_CASES)
            sampled_note = f"{SAMPLE_CASES} of {n_cases:,} cases"
        else:
            log_s = log
            sampled_note = f"all {n_cases:,} cases"
        net, im, fm = pm4py.discover_petri_net_inductive(log_s, noise_threshold=0.2)
        fit = pm4py.fitness_token_based_replay(log_s, net, im, fm)
        prec = pm4py.precision_token_based_replay(log_s, net, im, fm)
        inductive = {"places": len(net.places), "transitions": len(net.transitions),
                     "fitness": round(fit.get("average_trace_fitness", fit.get("log_fitness", 0)), 3),
                     "precision": round(prec, 3), "sampled": sampled_note}
        print(f"\nINDUCTIVE MINER model ({sampled_note}): {inductive['places']} places, {inductive['transitions']} transitions")
        print(f"CONFORMANCE (token replay): fitness={inductive['fitness']}  precision={inductive['precision']}")
        print("  -> fitness = how well reality fits the discovered model; the basis of as-is-vs-reference conformance.")
    except Exception as e:
        inductive = {"error": str(e)[:120]}
        print(f"\n(inductive/conformance skipped: {str(e)[:120]})")

    out = {"config": config_name, "label": cfg["label"], "cases": int(n_cases), "events": int(len(log)),
           "activities": int(log["concept:name"].nunique()), "distinct_variants": int(variant_freq.shape[0]),
           "top_variants": [{"trace": t, "count": int(c)} for t, c in variant_freq.head(25).items()],
           "dfg_edges": [{"from": a, "to": b, "count": int(c)} for (a, b), c in sorted(dfg.items(), key=lambda x: -x[1])[:60]],
           "start_activities": {str(k): int(v) for k, v in start.items()},
           "end_activities": {str(k): int(v) for k, v in end.items()},
           "bottlenecks_days": [{"from": a, "to": b, "mean_days": round(d, 2)} for d, (a, b) in perf_days[:20]],
           "inductive_conformance": inductive}
    path = os.path.join(OUTDIR, f"{config_name}.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nsaved: {path}")
    return out


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "clearing_lifecycle")
