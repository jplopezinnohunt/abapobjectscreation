"""
cts_extract.py -- 5-Year SAP Transport Order Extractor
=======================================================
Reads ALL released transport requests from the last 5 years from D01.
Uses the established pyrfc + RFC_READ_TABLE SNC pattern.

PROBE FINDINGS (D01):
  E070   -> READABLE via RFC_READ_TABLE (one TRSTATUS per query, no IN clause)
  E071   -> READABLE via RFC_READ_TABLE (no restrictions)
  E070L  -> BLOCKED (TABLE_WITHOUT_DATA, cross-client restriction)
  STMSIQSTAT/TMSBUFFER -> tested, skipped if not readable
  Standard CTS FMs -> not remote-enabled on this system

Tables read:
  E070   -> Transport headers (TRKORR, type, owner, status, dates)
  E071   -> Object entries per transport (PGMID, OBJECT, OBJ_NAME, OBJFUNC)
  E070T  -> Short description texts
  TADIR  -> Object package/namespace
  TDEVC  -> Package domain/software component

Deployment status: inferred from TRSTATUS (R=Released, D=Task-only, L=In-queue, E=Exported)

Output: cts_5yr_raw.json

Usage:
    python cts_extract.py                          # Full 5-year extract
    python cts_extract.py --years 3                # Last 3 years
    python cts_extract.py --probe                  # Quick probe: 15 headers per status
    python cts_extract.py --out my_output.json     # Custom output file
    python cts_extract.py --skip-objects           # Headers only (fast)
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from collections import Counter
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# ─────────────────────────────────────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────────────────────────────────────

def env(*keys, default=""):
    for k in keys:
        v = os.getenv(k)
        if v:
            return v
    return default


def rfc_connect():
    """Connect to D01 using SNC (preferred) or basic auth."""
    import pyrfc
    params = {
        "ashost": env("SAP_D01_ASHOST", "SAP_HOST", default="HQ-SAP-D01.HQ.INT.UNESCO.ORG"),
        "sysnr":  env("SAP_D01_SYSNR",  "SAP_SYSNR",  default="00"),
        "client": env("SAP_D01_CLIENT", "SAP_CLIENT", default="350"),
    }
    snc_mode = env("SAP_D01_SNC_MODE", "SAP_SNC_MODE")
    snc_pn   = env("SAP_D01_SNC_PARTNERNAME", "SAP_SNC_PARTNERNAME")
    if snc_mode and snc_pn:
        params["snc_mode"]        = snc_mode
        params["snc_partnername"] = snc_pn
        params["snc_qop"]         = env("SAP_D01_SNC_QOP", "SAP_SNC_QOP", default="9")
        print("  [RFC] SNC connection to D01")
    else:
        params["user"]   = env("SAP_D01_USER", "SAP_USER")
        params["passwd"] = env("SAP_D01_PASSWORD", "SAP_PASSWORD")
        print("  [RFC] Basic auth to D01")
    return pyrfc.Connection(**params)


# ─────────────────────────────────────────────────────────────────────────────
# RFC_READ_TABLE UTILITY
# ─────────────────────────────────────────────────────────────────────────────

def parse_fixed(wa: str, fields: list) -> dict:
    result = {}
    p = 0
    for f in fields:
        w = int(f.get("LENGTH", 10))
        result[f["FIELDNAME"]] = wa[p: p + w].strip() if p < len(wa) else ""
        p += w + 1
    return result


def rfc_table(conn, table: str, field_names: list, where_clauses: list,
              max_rows: int = 5000, rowskips: int = 0) -> tuple:
    """Single RFC_READ_TABLE call with delimiter-based parsing."""
    fields  = [{"FIELDNAME": f} for f in field_names]
    options = [{"TEXT": t} for t in where_clauses]
    r = conn.call(
        "RFC_READ_TABLE",
        QUERY_TABLE=table,
        FIELDS=fields,
        OPTIONS=options,
        ROWCOUNT=max_rows,
        ROWSKIPS=rowskips,
        DELIMITER="|",
    )
    schema = r.get("FIELDS", [])
    rows   = []
    for row in r.get("DATA", []):
        wa    = row.get("WA", "")
        parts = wa.split("|")
        if len(parts) == len(field_names):
            rows.append({field_names[i]: parts[i].strip() for i in range(len(field_names))})
        else:
            rows.append(parse_fixed(wa, schema))
    return rows, schema


def rfc_table_paginated(conn, table: str, field_names: list,
                        where_clauses: list, page_size: int = 5000,
                        max_total: int = 500000, verbose: bool = True) -> list:
    """Paginated fetch until no more rows returned."""
    all_rows, skip, page = [], 0, 0
    while True:
        rows, _ = rfc_table(conn, table, field_names, where_clauses,
                             max_rows=page_size, rowskips=skip)
        if not rows:
            break
        all_rows.extend(rows)
        page += 1
        skip += len(rows)
        if verbose:
            print(f"    page {page}: {len(rows)} rows (total: {len(all_rows)})")
        if len(rows) < page_size or len(all_rows) >= max_total:
            break
    return all_rows


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 -- E070 HEADERS
# ─────────────────────────────────────────────────────────────────────────────

def extract_headers(conn, cutoff_date: str, probe: bool = False) -> list:
    """
    Read E070 transport request headers.
    IMPORTANT: RFC_READ_TABLE on E070 does NOT support IN() clauses.
    We run one query per TRSTATUS value and merge results.

    TRFUNCTION: K=Workbench, W=Customizing, T=Transport-of-Copies, S=Task, X=Deletion
    TRSTATUS:   D=Task-released, R=Released, L=In-queue, E=Exported
    """
    print(f"\n  [Phase 1] Reading E070 headers (from {cutoff_date})...")

    fields = ["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER",
              "AS4DATE", "AS4TIME", "STRKORR", "KORRDEV"]

    all_rows = []
    for status in ['R', 'D', 'L', 'E']:
        where = [
            f"AS4DATE >= '{cutoff_date}'",
            f"AND TRSTATUS = '{status}'",
        ]
        try:
            if probe:
                rows, _ = rfc_table(conn, "E070", fields, where, max_rows=15)
            else:
                rows = rfc_table_paginated(conn, "E070", fields, where,
                                           page_size=5000, verbose=False)
            print(f"    TRSTATUS='{status}': {len(rows)} rows")
            all_rows.extend(rows)
        except Exception as ex:
            print(f"    [WARN] E070 status={status}: {str(ex)[:80]}")

    # Deduplicate by TRKORR
    seen, deduped = set(), []
    for r in all_rows:
        k = r.get("TRKORR", "")
        if k and k not in seen:
            seen.add(k)
            deduped.append(r)

    print(f"    -> {len(deduped)} unique transport headers")
    return deduped


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 -- E070T DESCRIPTIONS
# ─────────────────────────────────────────────────────────────────────────────

def extract_descriptions(conn, trkorrs: list) -> dict:
    """
    Read E070T short descriptions. Returns dict: TRKORR -> text.
    NOTE: E070T may not be available cross-client on all systems.
    Falls back gracefully to empty descriptions.
    """
    print(f"\n  [Phase 2] Reading E070T descriptions ({len(trkorrs)} transports)...")
    descriptions = {}
    # Test availability first
    try:
        test, _ = rfc_table(conn, "E070T", ["TRKORR", "AS4TEXT"], [], max_rows=1)
    except Exception as ex:
        print(f"    [SKIP] E070T not available: {str(ex)[:60]}")
        return descriptions

    batch_size = 200
    for i in range(0, len(trkorrs), batch_size):
        batch     = trkorrs[i: i + batch_size]
        in_clause = ",".join(f"'{t}'" for t in batch)
        try:
            rows, _ = rfc_table(conn, "E070T",
                ["TRKORR", "AS4TEXT"],
                [f"TRKORR IN ({in_clause})", "AND LANGU = 'E'"],
                max_rows=len(batch) + 10,
            )
            for r in rows:
                descriptions[r.get("TRKORR", "")] = r.get("AS4TEXT", "")
        except Exception as ex:
            if i == 0:
                print(f"    [WARN] E070T batch 0: {str(ex)[:80]}")
    print(f"    -> {len(descriptions)} descriptions fetched")
    return descriptions


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 -- E071 OBJECTS
# ─────────────────────────────────────────────────────────────────────────────

OBJECT_TYPE_CATEGORY = {
    "PROG": "Code/Program",    "REPS": "Code/Program",    "REPT": "Code/Program",
    "CLAS": "Code/Class",      "INTF": "Code/Interface",  "ENHO": "Code/Enhancement",
    "FUGR": "Code/FunctionGroup", "FUNC": "Code/FunctionModule",
    "TABL": "DataModel/Table", "DTEL": "DataModel/DataElement",
    "DOMA": "DataModel/Domain", "VIEW": "DataModel/View",
    "INDX": "DataModel/Index", "TTYP": "DataModel/TableType",
    "TRAN": "UI/Transaction",  "CUAD": "UI/Screen",       "DYNT": "UI/Dynpro",
    "SYST": "Config/System",   "CUST": "Config/Customizing", "VDAT": "Config/ViewData",
    "IWSV": "Fiori/ODataService", "IWOM": "Fiori/ODataModel",
    "WAPA": "Fiori/BSPApp",    "W3MI": "Fiori/WebResource",
    "SWFP": "Workflow",        "DEVC": "Package",
    "SUSC": "Auth/CheckObject","SUSO": "Auth/Object", "PFCG": "Auth/Role",
    "SFPF": "Output/SmartForm","SSFO": "Output/SAPscript", "XSLT": "Code/XSLT",
}


def get_object_category(obj_type: str) -> str:
    return OBJECT_TYPE_CATEGORY.get(obj_type.strip().upper(), f"Other/{obj_type.strip()}")


def extract_objects(conn, trkorrs: list, probe: bool = False) -> dict:
    """
    Read E071 object entries.
    NOTE: E071 IN() clause also fails on this system (same restriction as E070).
    We query per-TRKORR using TRKORR = 'X' individual calls.
    """
    print(f"\n  [Phase 3] Reading E071 objects ({len(trkorrs)} transports)...")
    objects_by_trkorr = {t: [] for t in trkorrs}
    if probe:
        trkorrs = trkorrs[:20]

    fields        = ["TRKORR", "AS4POS", "PGMID", "OBJECT", "OBJ_NAME", "OBJFUNC"]
    total_objects = 0
    failed        = 0

    for i, trk in enumerate(trkorrs):
        try:
            rows, _ = rfc_table(conn, "E071", fields,
                [f"TRKORR = '{trk}'"],
                max_rows=500,
            )
            for r in rows:
                r["CHANGE_CATEGORY"] = get_object_category(r.get("OBJECT", ""))
                objects_by_trkorr[trk].append(r)
            total_objects += len(rows)
        except Exception as ex:
            failed += 1
            if failed <= 3:
                print(f"  [WARN] E071 {trk}: {str(ex)[:80]}")

        if (i + 1) % 100 == 0:
            print(f"    processed {i + 1}/{len(trkorrs)} transports, {total_objects} objects")

    print(f"    -> {total_objects} total objects across {len(trkorrs)} transports")
    return objects_by_trkorr


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 -- DEPLOYMENT STATUS (TRSTATUS heuristic, E070L not readable)
# ─────────────────────────────────────────────────────────────────────────────

TPSTAT_MAP = {"": "NOT_IMPORTED", "0": "SUCCESS", "4": "WARNING",
              "8": "ERROR", "12": "FATAL", "16": "FATAL"}


def extract_deployment_status(conn, trkorrs: list, probe: bool = False) -> dict:
    """
    Derive deployment status.
    E070L is not readable via RFC (cross-client table restriction).
    We try STMSIQSTAT / TMSBUFFER as alternatives; fall back to TRSTATUS heuristic.
    """
    print(f"\n  [Phase 4] Deployment status ({len(trkorrs)} transports)...")
    if probe:
        trkorrs = trkorrs[:20]

    stms_data = {}
    for alt_table, flds in [("STMSIQSTAT", ["TRKORR", "TSYSTEM", "TPSTAT"]),
                             ("TMSBUFFER",  ["TRKORR", "TARSYSTEM", "RETCODE"])]:
        try:
            test_rows, _ = rfc_table(conn, alt_table, flds[:2], [], max_rows=1)
            print(f"    [{alt_table}] accessible - reading import data...")
            all_rows = rfc_table_paginated(conn, alt_table, flds, [], verbose=False)
            for r in all_rows:
                trk  = r.get("TRKORR","").strip()
                sys_ = (r.get("TSYSTEM","") or r.get("TARSYSTEM","")).strip()
                rc   = (r.get("TPSTAT","") or r.get("RETCODE","")).strip()
                if trk and sys_:
                    stms_data.setdefault(trk, {})[sys_] = TPSTAT_MAP.get(rc, rc)
            break
        except Exception:
            pass

    if not stms_data:
        print("    E070L/STMS tables not readable. Using TRSTATUS as deployment proxy.")

    deployment = {}
    for trk in trkorrs:
        sys_map = stms_data.get(trk, {})
        in_prd  = "P01" in sys_map and sys_map["P01"] == "SUCCESS"
        in_qas  = "V01" in sys_map and sys_map["V01"] == "SUCCESS"
        has_err = any(v in ("ERROR", "FATAL") for v in sys_map.values())

        if has_err:
            level = "IMPORT_FAILED"
        elif in_prd:
            level = "FULLY_PROMOTED"
        elif in_qas:
            level = "IN_QUALITY"
        else:
            level = "STATUS_FROM_TRSTATUS"  # resolved in assemble_result()

        deployment[trk] = {
            "_level":           level,
            "_systems":         list(sys_map.keys()),
            "_e070l_available": bool(stms_data),
        }

    print(f"    -> {len(deployment)} entries ({'STMS data' if stms_data else 'TRSTATUS heuristic'})")
    return deployment


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 5 -- TADIR ENRICHMENT (Package + Domain)
# ─────────────────────────────────────────────────────────────────────────────

def extract_tadir_enrichment(conn, objects_by_trkorr: dict) -> tuple:
    """
    Look up TADIR (DEVCLASS, SRCSYSTEM) and TDEVC (PARENTCL, DLVUNIT) for all objects.
    Returns (tadir_cache dict, devclass_info dict).
    """
    print("\n  [Phase 5] TADIR enrichment (package + domain lookup)...")

    unique_objects = set()
    for objs in objects_by_trkorr.values():
        for o in objs:
            key = (o.get("PGMID",""), o.get("OBJECT",""), o.get("OBJ_NAME",""))
            if all(key):
                unique_objects.add(key)

    print(f"    Unique objects: {len(unique_objects)}")
    tadir_cache = {}
    batch_size  = 50
    obj_list    = list(unique_objects)

    for i in range(0, min(len(obj_list), 10000), batch_size):
        batch     = obj_list[i: i + batch_size]
        in_clause = ",".join(f"'{o[2][:40]}'" for o in batch)
        try:
            rows, _ = rfc_table(conn, "TADIR",
                ["PGMID", "OBJECT", "OBJ_NAME", "DEVCLASS", "SRCSYSTEM", "AUTHOR"],
                [f"OBJ_NAME IN ({in_clause})"],
                max_rows=len(batch) * 3,
            )
            for r in rows:
                k = (r.get("PGMID","").strip(), r.get("OBJECT","").strip(), r.get("OBJ_NAME","").strip())
                tadir_cache[k] = {
                    "devclass":  r.get("DEVCLASS","").strip(),
                    "srcsystem": r.get("SRCSYSTEM","").strip(),
                    "author":    r.get("AUTHOR","").strip(),
                }
        except Exception as ex:
            if i == 0:
                print(f"    [WARN] TADIR: {str(ex)[:80]}")

    devclasses    = {v["devclass"] for v in tadir_cache.values() if v.get("devclass")}
    devclass_info = {}
    for i in range(0, len(list(devclasses)), batch_size):
        batch     = list(devclasses)[i: i + batch_size]
        in_clause = ",".join(f"'{d}'" for d in batch)
        try:
            rows, _ = rfc_table(conn, "TDEVC",
                ["DEVCLASS", "PARENTCL", "DLVUNIT"],
                [f"DEVCLASS IN ({in_clause})"],
                max_rows=len(batch) + 5,
            )
            for r in rows:
                devclass_info[r.get("DEVCLASS","").strip()] = {
                    "parent":  r.get("PARENTCL","").strip(),
                    "dlvunit": r.get("DLVUNIT","").strip(),
                }
        except Exception:
            pass

    print(f"    -> {len(tadir_cache)} TADIR entries; {len(devclass_info)} package entries")
    return tadir_cache, devclass_info


# ─────────────────────────────────────────────────────────────────────────────
# ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

def assemble_result(headers, descriptions, objects_by_trkorr,
                    deployment, tadir_cache, devclass_info) -> dict:
    """Merge all phases into final JSON structure."""
    transports = []
    for h in headers:
        trkorr   = h.get("TRKORR", "")
        objs     = objects_by_trkorr.get(trkorr, [])
        deploy   = deployment.get(trkorr, {})
        desc     = descriptions.get(trkorr, "")
        fn       = h.get("TRFUNCTION", "")
        trstatus = h.get("TRSTATUS", "")
        fn_label = {"K": "Workbench", "W": "Customizing", "T": "Transport-of-Copies",
                    "S": "Task", "X": "Deletion", "Q": "Test"}.get(fn, fn)

        # Resolve deployment level
        raw_level = deploy.get("_level", "UNKNOWN")
        if raw_level == "STATUS_FROM_TRSTATUS":
            raw_level = {
                "R": "RELEASED",    # Exported from dev; likely in V01/P01 queue
                "D": "DEV_ONLY",    # Task scope only
                "L": "IN_QUEUE",    # In import queue
                "E": "EXPORTED",    # Export done, pending import
            }.get(trstatus, "UNKNOWN")

        # Enrich objects with TADIR data
        enriched_objs = []
        for o in objs:
            key   = (o.get("PGMID","").strip(), o.get("OBJECT","").strip(), o.get("OBJ_NAME","").strip())
            tadir = tadir_cache.get(key, {})
            dc    = tadir.get("devclass", "")
            tdevc = devclass_info.get(dc, {})
            enriched_objs.append({
                "pgmid":      o.get("PGMID","").strip(),
                "obj_type":   o.get("OBJECT","").strip(),
                "obj_name":   o.get("OBJ_NAME","").strip(),
                "change_cat": o.get("CHANGE_CATEGORY",""),
                "devclass":   dc,
                "dlvunit":    tdevc.get("dlvunit",""),
                "pkg_parent": tdevc.get("parent",""),
                "srcsystem":  tadir.get("srcsystem",""),
            })

        transports.append({
            "trkorr":         trkorr,
            "type":           fn_label,
            "type_code":      fn,
            "status":         trstatus,
            "owner":          h.get("AS4USER","").strip(),
            "date":           h.get("AS4DATE",""),
            "time":           h.get("AS4TIME",""),
            "parent_req":     h.get("STRKORR","").strip(),
            "description":    desc,
            "deploy_level":   raw_level,
            "deploy_systems": deploy.get("_systems",[]),
            "objects":        enriched_objs,
            "obj_count":      len(enriched_objs),
        })

    total_headers  = len(transports)
    total_objects  = sum(t["obj_count"] for t in transports)
    levels         = Counter(t["deploy_level"] for t in transports)
    type_dist      = Counter(t["type"] for t in transports)
    top_owners     = Counter(t["owner"] for t in transports).most_common(20)
    devclasses_cnt = Counter()
    obj_types_cnt  = Counter()
    for t in transports:
        for o in t["objects"]:
            devclasses_cnt[o["devclass"]] += 1
            obj_types_cnt[o["change_cat"]] += 1

    return {
        "meta": {
            "extracted_at":   datetime.now().isoformat(),
            "source_system":  "D01",
            "total_headers":  total_headers,
            "total_objects":  total_objects,
            "e070l_note":     "E070L not readable via RFC. Deploy level inferred from TRSTATUS.",
        },
        "summary": {
            "deployment_levels": dict(levels),
            "request_types":     dict(type_dist),
            "top_20_owners":     top_owners,
            "top_30_devclasses": devclasses_cnt.most_common(30),
            "change_cat_dist":   dict(obj_types_cnt),
        },
        "transports": transports,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="5-Year CTS Transport Order Extractor - D01")
    parser.add_argument("--years",        type=int,  default=5)
    parser.add_argument("--probe",        action="store_true", help="Quick probe: 15 rows per status")
    parser.add_argument("--skip-objects", action="store_true", help="Headers + deploy only")
    parser.add_argument("--skip-tadir",   action="store_true", help="Skip TADIR enrichment")
    parser.add_argument("--out",          type=str,  default=None)
    args = parser.parse_args()

    suffix  = "probe" if args.probe else f"{args.years}yr"
    outfile = args.out or f"cts_{suffix}_raw.json"
    cutoff  = (datetime.now() - timedelta(days=args.years * 365)).strftime("%Y%m%d")

    print("=" * 70)
    print(f"  CTS TRANSPORT ORDER EXTRACTOR -- UNESCO D01")
    print(f"  Period : Last {args.years} year(s) (from {cutoff})")
    print(f"  Mode   : {'PROBE' if args.probe else 'FULL EXTRACT'}")
    print(f"  Output : {outfile}")
    print("=" * 70)

    import pyrfc
    conn = rfc_connect()
    print(f"  [OK] Connected to D01\n")

    headers = extract_headers(conn, cutoff, probe=args.probe)
    if not headers:
        print("\n  [ERROR] No transport headers found.")
        conn.close()
        return

    trkorrs      = [h["TRKORR"] for h in headers if h.get("TRKORR")]
    descriptions = extract_descriptions(conn, trkorrs)

    if args.skip_objects:
        objects_by_trkorr = {t: [] for t in trkorrs}
        print("\n  [Phase 3] Skipped (--skip-objects)")
    else:
        objects_by_trkorr = extract_objects(conn, trkorrs, probe=args.probe)

    deployment = extract_deployment_status(conn, trkorrs, probe=args.probe)

    if args.skip_tadir or args.skip_objects:
        tadir_cache, devclass_info = {}, {}
        print("\n  [Phase 5] Skipped")
    else:
        tadir_cache, devclass_info = extract_tadir_enrichment(conn, objects_by_trkorr)

    conn.close()

    print("\n  [Assembly] Merging all phases...")
    result = assemble_result(headers, descriptions, objects_by_trkorr,
                             deployment, tadir_cache, devclass_info)

    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'=' * 70}")
    print(f"  [OK] EXTRACT COMPLETE")
    print(f"  Headers : {result['meta']['total_headers']}")
    print(f"  Objects : {result['meta']['total_objects']}")
    print(f"  Output  : {outfile}")
    print(f"\n  Deployment levels:")
    for level, count in sorted(result['summary']['deployment_levels'].items()):
        print(f"    {level:<22} {count:>6}")
    print(f"\n  Top 10 owners:")
    for owner, count in result['summary']['top_20_owners'][:10]:
        print(f"    {owner:<25} {count:>5} transports")
    print(f"\n  Top 10 packages (DEVCLASS):")
    for dc, count in result['summary']['top_30_devclasses'][:10]:
        if dc:
            print(f"    {dc:<30} {count:>5} objects")
    print(f"\n  Next step: python cts_analyze.py --input {outfile}")
    print("=" * 70)


if __name__ == "__main__":
    main()
