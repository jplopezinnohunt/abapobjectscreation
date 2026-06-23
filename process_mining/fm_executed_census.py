"""
fm_executed_census.py — the AS-RUN executed-objects census for PSM-FM.
----------------------------------------------------------------------
Answers: "do we have ALL reports/transactions that actually EXECUTE — by users,
batch, or calls?" The static TSTC catalog says what CAN run; this fuses the real
EXECUTION evidence from every channel:

  channel        source                       object field
  dialog tcode   rsau 'Transaction Start'      PARAM1 (tcode)
  report run     rsau 'Report Start'           SLGREPNA (program)
  RFC/BAPI call  rsau 'RFC Function Call'       PARAM3 (function module)
  batch job      tbtcp                          PROGNAME (+ VARIANT)
  batch input    apqi/apqd (BDC) if present     -

For each executed FM object: exec_count, distinct_users, top users, channel(s).
Cross-references the static catalog (d01_tstc / tfdir_custom) to flag
EXECUTED vs CATALOG-ONLY. Emits brain_v2/fm_executed_census.json.

DATA IS P01 (rsau_audit_history = SM20/RSAU 15.6M rows, ~4-month window).
Run: python process_mining/fm_executed_census.py
"""
import re
import json
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = REPO / "brain_v2" / "fm_executed_census.json"

# FM / PSM-FM object-name matcher (tcodes, reports, FMs, BAPIs).
FM_RE = re.compile(
    r"^(FM[0-9A-Z]|YFM|YPS|ZFM|ZPS|ZICTP|ZPK00|YEBUR|YBBUR|Y_RFFM|RFFM|ZRFFM|ZFFM|"
    r"BPCARR|BPDIST|BPCOPY|BPINDX|SAPMKBU|SAPLFM|SAPMFM|SAPLKBP|"
    r"Y_BAPI_FUND|Y_BAPI_BUDGET|Y_BAPI_YFM|Y_RFC_YFM|Y_FMKU|ZRFC_FMR|ZRFC_FRESERV|"
    r"ZRFC_ICTP|ZRFC_CONVERT_WBS|ZBAPI_FUNDSCENTER|BAPI_0050|BAPI_FUNDS|YFMAVCR|"
    r"YVFM|Y_FI_POSTINGS|Y_COMMITMENTS_FUNDS|Z_T9FUND|Z_ALR_8701|Z_FM_FMAA|Z_KBLK)",
    re.I)
# obvious non-FM that the prefix would over-catch (FMx system tcodes we don't want)
DENY = re.compile(r"^(FMOD|FMOA_SYS)", re.I)


def grouped(c, where, obj_field, user_field="SLGUSER"):
    """GROUP BY object in SQL (collapses millions of events to distinct objects),
    then FM-filter in Python."""
    rows = c.execute(
        f"SELECT {obj_field} AS o, COUNT(*) n, COUNT(DISTINCT {user_field}) u "
        f"FROM rsau_audit_history WHERE {where} AND {obj_field} <> '' "
        f"GROUP BY {obj_field}").fetchall()
    out = {}
    for o, n, u in rows:
        if o and FM_RE.match(o) and not DENY.match(o):
            out[o] = {"exec_count": n, "distinct_users": u}
    return out


def enrich_top_users(c, where, obj_field, objs, k=5):
    """ONE GROUP BY (object,user) over the channel, restricted to the FM object set.
    Avoids N per-object scans. Returns {obj: ['user(n)', ...]}."""
    if not objs:
        return {}
    ph = ",".join("?" * len(objs))
    rows = c.execute(
        f"SELECT {obj_field} o, SLGUSER u, COUNT(*) n FROM rsau_audit_history "
        f"WHERE {where} AND {obj_field} IN ({ph}) GROUP BY {obj_field}, SLGUSER",
        list(objs)).fetchall()
    agg = {}
    for o, u, n in rows:
        agg.setdefault(o, []).append((u, n))
    return {o: [f"{u}({n})" for u, n in sorted(v, key=lambda x: -x[1])[:k]] for o, v in agg.items()}


def main():
    con = sqlite3.connect(GOLD)
    c = con.cursor()

    print("Scanning rsau_audit_history (15.6M) for FM execution evidence ...")
    tx = grouped(c, "TXSUBCLSID='Transaction Start'", "PARAM1")     # dialog tcodes
    rep = grouped(c, "TXSUBCLSID='Report Start'", "SLGREPNA")        # report runs
    rfc = grouped(c, "TXSUBCLSID='RFC Function Call'", "PARAM3")     # RFC/BAPI calls

    # batch jobs (tbtcp)
    batch = {}
    for prog, n, j in c.execute(
            "SELECT PROGNAME, COUNT(*) n, COUNT(DISTINCT JOBNAME||JOBCOUNT) j "
            "FROM tbtcp WHERE PROGNAME <> '' GROUP BY PROGNAME").fetchall():
        if prog and FM_RE.match(prog) and not DENY.match(prog):
            batch[prog] = {"job_steps": n, "distinct_jobs": j}

    # batch input (BDC) — apqi/apqd present?
    bdc_tables = [r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'apq%' OR name LIKE '%bdc%')").fetchall()]

    # enrich top users — one GROUP BY per channel (restricted to the FM object set)
    print(f"  enriching top users ({len(tx)} tcodes, {len(rep)} reports, {len(rfc)} rfcs) ...")
    for o, tu in enrich_top_users(c, "TXSUBCLSID='Transaction Start'", "PARAM1", set(tx)).items():
        tx[o]["top_users"] = tu
    for o, tu in enrich_top_users(c, "TXSUBCLSID='Report Start'", "SLGREPNA", set(rep)).items():
        rep[o]["top_users"] = tu
    for o, tu in enrich_top_users(c, "TXSUBCLSID='RFC Function Call'", "PARAM3", set(rfc)).items():
        rfc[o]["top_users"] = tu

    # static catalog for executed-vs-catalog-only
    cat_tc = {r[0] for r in c.execute("SELECT TCODE FROM d01_tstc").fetchall()}
    cat_fm = {r[0] for r in c.execute("SELECT FUNCNAME FROM tfdir_custom").fetchall()}

    census = {
        "_meta": {"source": "rsau_audit_history (SM20/RSAU ~4mo) + tbtcp + d01_tstc/tfdir_custom",
                  "window": "P01 ~2026-02-21..06-21", "domain": "PSM_FM"},
        "dialog_tcodes": dict(sorted(tx.items(), key=lambda kv: -kv[1]["exec_count"])),
        "reports": dict(sorted(rep.items(), key=lambda kv: -kv[1]["exec_count"])),
        "rfc_bapi_calls": dict(sorted(rfc.items(), key=lambda kv: -kv[1]["exec_count"])),
        "batch_programs": dict(sorted(batch.items(), key=lambda kv: -kv[1]["job_steps"])),
        "bdc_tables_present": bdc_tables,
    }
    OUT.write_text(json.dumps(census, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- report
    def show(title, d, k=25):
        print(f"\n=== {title} — {len(d)} distinct FM objects executed ===")
        for o, v in list(d.items())[:k]:
            cnt = v.get("exec_count") or v.get("job_steps")
            extra = f"users={v.get('distinct_users','')}" if "distinct_users" in v else f"jobs={v.get('distinct_jobs','')}"
            tu = " ".join(v.get("top_users", [])[:3])
            print(f"  {o:34s} runs={cnt:>8,}  {extra:11s}  {tu}")

    show("DIALOG tcodes (users)", census["dialog_tcodes"])
    show("REPORTS run", census["reports"])
    show("RFC / BAPI calls", census["rfc_bapi_calls"])
    show("BATCH programs (jobs)", census["batch_programs"])

    # coverage: executed but NOT in catalog, and catalog-FM tcodes never executed
    exec_tc = set(census["dialog_tcodes"])
    catalog_fm_tc = {t for t in cat_tc if FM_RE.match(t) and not DENY.match(t)}
    print(f"\n=== COVERAGE ===")
    print(f"  FM tcodes in static catalog (d01_tstc): {len(catalog_fm_tc):,}")
    print(f"  FM tcodes ACTUALLY executed (dialog):   {len(exec_tc):,}")
    print(f"  -> executed/catalog ratio: {100*len(exec_tc & catalog_fm_tc)/max(len(catalog_fm_tc),1):.1f}% of the catalog is live")
    print(f"  executed tcodes NOT in catalog (custom/new): {len(exec_tc - cat_tc)}  e.g. {sorted(exec_tc - cat_tc)[:8]}")
    print(f"  FM RFC/BAPI executed: {len(census['rfc_bapi_calls'])}  (of {len([f for f in cat_fm if FM_RE.match(f)])} custom-FM in tfdir_custom)")
    print(f"  BDC tables present: {bdc_tables or 'none in Gold DB (BDC via sap_bdc_intelligence skill)'}")
    print(f"\nEmitted: {OUT}")
    con.close()


if __name__ == "__main__":
    main()
