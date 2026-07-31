"""
SAP METHOD REGISTRY — the fix for our weak method layer (retro 2026-06-21).
NOT a static list of 306 tables — a RESOLVER: given ANY SAP object, return how to EXTRACT it and how to
ANALYZE it, so we stop rediscovering "how do I read X" every session. Built from the elements we already have:
  DD02L (table class -> extraction method)  +  the element-specific methods discovered this session  +  the
  analysis-method-by-role mapping. Mirrors the capability model (domain × capability) as object × (extract, analyze).

resolve("EKKO")  -> transparent -> RFC_READ_TABLE (P01 ROWSKIPS-free, date-chunked)  | analyze: process-mining/SQL
resolve("CDPOS") -> cluster     -> ABAP FOR ALL ENTRIES                              | analyze: blind-spot RESULT×METHOD
resolve("SNAP")  -> override    -> FM /USE/BL_GET_SHORTDUMPS                          | analyze: failure-pattern

Run:  python process_mining/method_registry.py            # demo + emit brain_v2/method_registry.json
      python process_mining/method_registry.py EKKO CDPOS SNAP RSAU AGR_USERS
"""
import os, sys, json, sqlite3

# 1) Table-CLASS -> extraction method (covers ANY table via its DD02L.TABCLASS — no enumeration needed)
TYPE_RULE = {
    "TRANSP":  ("RFC_READ_TABLE", "P01-secured: NO ROWSKIPS (read ROWSKIPS-free, date-chunked); split wide fields"),
    "POOL":    ("RFC_READ_TABLE (KEY only) -> FM", "pool table: RFC returns the key field only; values via a content FM (e.g. RS_VARIANT_CONTENTS)"),
    "CLUSTER": ("ABAP FOR ALL ENTRIES", "cluster behind e.g. CDCLS/RFBLG: RFC_READ_TABLE cannot read it; sometimes declustered on EhP8 — probe first"),
    "VIEW":    ("RFC_READ_TABLE", "DB/projection view — read like a transparent table"),
    "INTTAB":  ("n/a", "structure/append — not a data container"),
}

# 2) Element-specific OVERRIDES (non-table or special — the hard-won methods of this session)
OVERRIDE = {
    "RSAU":        ("FM RSAU_API_GET_LOG_DATA(IS_INTERVAL)", "chunk <=6h (2-day call hangs); conn poisons ~every 12 calls -> reconnect; transient 'partner not reached' -> resilient reconnect", "audit / 2-axis classification + self-adapting", "~4 months"),
    "SM21":        ("FM /USE/BL_GET_SHORTDUMPS -> EIT_SYSLOG", "SALC_MSC_READ_SYSLOG returns 0; Z_READ_SYSLOG broken; RFC_READ_TABLE n/a", "failure-pattern (decode CENTDATA before concluding!)", "~7 days"),
    "ST22":        ("FM /USE/BL_GET_SHORTDUMPS -> EIT_SHORT_DUMP", "SNAP TABLE_NOT_AVAILABLE; RFC_ABAP_INSTALL_AND_RUN no auth on P01", "failure-pattern", "~7-30 days"),
    "SNAP":        ("FM /USE/BL_GET_SHORTDUMPS", "the SNAP table is not RFC-readable; use the dump FM", "failure-pattern", "~7-30 days"),
    "STAD":        ("FM SAPWL_STATREC_READ_FILE", "workload stats, not a table; kernel-verify; date/time/host params", "tcode-usage mining", "short (days)"),
    "SWNCMONI":    ("FM SAPWL_* (SWNC)", "workload monitor aggregates", "tcode-usage mining", "config'd"),
    "CDPOS":       ("ABAP FOR ALL ENTRIES (CDCLS)", "cluster; pair with CDHDR by OBJECTCLAS+OBJECTID+CHANGENR; declustered sometimes on EhP8 -> probe", "blind-spot RESULT×METHOD (field-level old->new)", "persists"),
    "RFC_STREAM":  ("RSAU 'RFC Function Call' events; parse PARAMX host/dest/user", "the call stream lives in the audit log, not a table; ORIGIN axis = host/dest/user", "2-axis classification + self-adapting discovery", "~4 months"),
    "DF14L":       ("RFC_READ_TABLE, FCTR_ID EQ only, <=40 OR-terms per call", "s097: full read AND 'LIKE' both return TABLE_WITHOUT_DATA -- only EQ works, so ask for the ids TDEVC references. The table has NO field PARENT_ID: requesting it raises TABLE_WITHOUT_DATA, i.e. a FIELD error wearing the costume of an empty table (3 runs returned 0 rows silently). OPTIONS has a length cap: 40 OR-terms OK, more returns nothing without error.", "object -> application component (the bottom-up rung)", "static"),
    "TADIR":       ("RFC_READ_TABLE per OBJECT type, ROWCOUNT 40000", "s097: P01 rejects ROWSKIPS so paging is impossible -- each object type caps at 40K rows. Chunk by name range if more is needed. PROG alone covers only ~4% of graph objects; span TABL/FUGR/CLAS/TRAN/VIEW/DTEL/ENHO/SXCI too.", "object -> package -> component", "static"),
    "SOAMANAGER_GUID": ("NOT resolvable", "the dest GUIDs are external connection IDs, not SAP-named ports (not in RFCDES; SRT_* are SOAP, calls are RFC)", "n/a — host names the system", "n/a"),
}

# 3) Analysis method by ROLE (when not overridden): infer from the object's role
ANALYSIS_BY_ROLE = [
    (("EKKO", "EKPO", "EKBE", "VBFA", "VBAK", "RBKP", "RSEG", "ESSR", "ESLL"), "process mining (OCEL / inductive / conformance)"),
    (("CDHDR", "CDPOS", "JCDS", "JEST"), "blind-spot RESULT×METHOD (changes, channel via TCODE)"),
    (("AGR_", "USR", "USOBX", "UST12"), "SoD declared-vs-actual reconciliation"),
    (("BKPF", "BSEG", "GLT0", "FMIFIIT", "FMIOI"), "SQL aggregation / golden query"),
]


def _analysis_for(name):
    u = name.upper()
    for keys, method in ANALYSIS_BY_ROLE:
        if any(u.startswith(k) or u == k for k in keys):
            return method
    return "SQL aggregation (default)"


def resolve(name, conn=None):
    u = name.upper()
    # overrides first (logs / special)
    for k, v in OVERRIDE.items():
        if u == k or u.startswith(k):
            return {"object": name, "kind": "override", "extract": v[0], "constraint": v[1], "analyze": v[2], "retention": v[3]}
    # table -> class via DD02L (live) -> type rule
    tabclass = None
    if conn is not None:
        try:
            r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD02L", DELIMITER="|", ROWCOUNT=1,
                          OPTIONS=[{"TEXT": f"TABNAME = '{u}'"}], FIELDS=[{"FIELDNAME": "TABCLASS"}])
            if r.get("DATA"): tabclass = r["DATA"][0]["WA"].strip()
        except Exception:
            pass
    method, constraint = TYPE_RULE.get(tabclass, ("RFC_READ_TABLE (assumed transparent — verify class)", "DD02L class unknown; default"))
    return {"object": name, "kind": tabclass or "table?", "extract": method, "constraint": constraint,
            "analyze": _analysis_for(name), "retention": "persists (master/txn)"}


def main():
    out = os.path.join("brain_v2", "method_registry.json")
    conn = None
    try:
        sys.path.insert(0, os.path.abspath("Zagentexecution/mcp-backend-server-python"))
        from rfc_helpers import get_connection
        conn = get_connection("P01")
    except Exception as e:
        print(f"(no P01 — table-class lookup skipped: {str(e)[:50]})")
    objs = sys.argv[1:] or ["EKKO", "CDHDR", "CDPOS", "VARI", "RSAU", "SM21", "ST22", "AGR_USERS", "BSEG", "SOAMANAGER_GUID"]
    reg = [resolve(o, conn) for o in objs]
    for r in reg:
        print(f"  {r['object']:18} [{r['kind']:8}] extract: {r['extract']}")
        print(f"  {'':18}            analyze: {r['analyze']}  | {r['constraint'][:70]}")
    if conn:
        try: conn.close()
        except Exception: pass
    json.dump({"_doc": "object -> (extract, analyze, constraint, retention). TYPE_RULE covers any table via DD02L class; OVERRIDE = special/non-table elements.",
               "type_rules": TYPE_RULE, "overrides": OVERRIDE, "resolved_examples": reg}, open(out, "w"), indent=1, default=list)
    print(f"\nregistry emitted: {out}  (resolve(object) returns the method — no more rediscovery)")


if __name__ == "__main__":
    main()
