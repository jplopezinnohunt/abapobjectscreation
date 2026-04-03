"""
company_code_reverse_engineer.py
================================
Reverse-engineer how the last company code was created in P01 (production).

Phase 1: RFC to P01 — E071K scan for T001 TABKEYs (identify which BUKRS has transports)
Phase 2: RFC to P01 — Full E071K + E070 + E07T for the target BUKRS
Phase 3: Gold DB — Master data created in first 3 months (vendors, cost centers, assets, etc.)
Phase 4: Generate blueprint report

Usage:
    python company_code_reverse_engineer.py
"""

import sys
import io
import os
import json
import sqlite3
from datetime import datetime, timedelta
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

GOLD_DB = os.path.join(os.path.dirname(__file__), "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "blueprint_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_json(name, data):
    path = os.path.join(OUTPUT_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved {path} ({len(data)} rows)")


# ============================================================
# PHASE 1: Identify company codes in transport history (RFC)
# ============================================================
def phase1_identify_newest(conn):
    print("=" * 70)
    print("PHASE 1: Scanning E071K for T001 entries in P01")
    print("=" * 70)

    # E071K stores table keys for customizing transports
    # T001 key = MANDT(3) + BUKRS(4)
    fields = ["TRKORR", "PGMID", "OBJECT", "OBJNAME", "TABKEY"]
    rows = rfc_read_paginated(conn, "E071K", fields, "OBJNAME = 'T001'", batch_size=5000, throttle=2.0)
    print(f"\n  E071K entries for T001: {len(rows)}")

    if not rows:
        print("  No T001 entries found in E071K. Trying with TABU...")
        # Sometimes stored differently
        rows = rfc_read_paginated(conn, "E071K", fields, "OBJNAME LIKE 'T001%'", batch_size=5000, throttle=2.0)
        print(f"  E071K entries for T001*: {len(rows)}")

    # Parse BUKRS from TABKEY
    bukrs_data = defaultdict(list)
    for r in rows:
        tabkey = r.get("TABKEY", "")
        # T001 TABKEY: MANDT(3) + BUKRS(4)
        if len(tabkey) >= 7:
            bukrs = tabkey[3:7].strip()
            if bukrs:
                bukrs_data[bukrs].append(r["TRKORR"])

    print(f"\n  Company codes found in T001 transports:")
    for bukrs in sorted(bukrs_data.keys()):
        transports = sorted(set(bukrs_data[bukrs]))
        print(f"    {bukrs:6s}: {len(transports)} transports -> {', '.join(transports)}")

    save_json("phase1_e071k_t001", rows)

    # Now get transport dates to find the newest
    all_transports = sorted(set(t for tlist in bukrs_data.values() for t in tlist))
    transport_info = {}

    print(f"\n  Fetching details for {len(all_transports)} transports...")
    for i in range(0, len(all_transports), 20):
        batch = all_transports[i:i + 20]
        in_clause = " OR ".join([f"TRKORR = '{t}'" for t in batch])

        fields_e070 = ["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE", "AS4TIME", "STRKORR"]
        try:
            rows_e070 = rfc_read_paginated(conn, "E070", fields_e070, in_clause, batch_size=500, throttle=1.0)
            for r in rows_e070:
                transport_info[r["TRKORR"]] = r
        except Exception as e:
            print(f"    E070 batch error: {e}")

        # Descriptions
        fields_e07t = ["TRKORR", "AS4TEXT"]
        try:
            rows_e07t = rfc_read_paginated(conn, "E07T", fields_e07t, in_clause, batch_size=500, throttle=1.0)
            for r in rows_e07t:
                if r["TRKORR"] in transport_info:
                    transport_info[r["TRKORR"]]["AS4TEXT"] = r.get("AS4TEXT", "")
        except Exception as e:
            print(f"    E07T batch error: {e}")

    # Determine newest company code by latest transport date
    print(f"\n  Company codes by latest transport date:")
    bukrs_dates = {}
    for bukrs, transports in bukrs_data.items():
        dates = []
        for t in transports:
            info = transport_info.get(t, {})
            d = info.get("AS4DATE", "")
            if d:
                dates.append(d)
        if dates:
            bukrs_dates[bukrs] = (min(dates), max(dates), len(transports))

    for bukrs, (first, last, count) in sorted(bukrs_dates.items(), key=lambda x: x[1][0], reverse=True):
        print(f"    {bukrs:6s}: First={first}, Last={last}, Transports={count}")

    save_json("phase1_transport_info", list(transport_info.values()))

    return bukrs_data, transport_info


# ============================================================
# PHASE 2: Deep-dive into target company code transports (RFC)
# ============================================================
def phase2_deep_dive(conn, bukrs, bukrs_data, transport_info):
    print(f"\n{'=' * 70}")
    print(f"PHASE 2: Full transport inventory for {bukrs}")
    print(f"{'=' * 70}")

    target_transports = sorted(set(bukrs_data.get(bukrs, [])))
    print(f"  Transports: {len(target_transports)}")

    # Get ALL E071K entries for these transports (not just T001)
    all_e071k = []
    for i in range(0, len(target_transports), 10):
        batch = target_transports[i:i + 10]
        in_clause = " OR ".join([f"TRKORR = '{t}'" for t in batch])
        fields = ["TRKORR", "PGMID", "OBJECT", "OBJNAME", "TABKEY"]
        try:
            rows = rfc_read_paginated(conn, "E071K", fields, in_clause, batch_size=5000, throttle=2.0)
            all_e071k.extend(rows)
        except Exception as e:
            print(f"    E071K batch error: {e}")

    print(f"  Total E071K entries across all transports: {len(all_e071k)}")

    # Also get E071 (object level)
    all_e071 = []
    for i in range(0, len(target_transports), 10):
        batch = target_transports[i:i + 10]
        in_clause = " OR ".join([f"TRKORR = '{t}'" for t in batch])
        fields_071 = ["TRKORR", "PGMID", "OBJECT", "OBJ_NAME", "OBJFUNC"]
        try:
            rows = rfc_read_paginated(conn, "E071", fields_071, in_clause, batch_size=5000, throttle=2.0)
            all_e071.extend(rows)
        except Exception as e:
            print(f"    E071 batch error: {e}")

    print(f"  Total E071 entries (objects): {len(all_e071)}")

    save_json(f"phase2_e071k_{bukrs}", all_e071k)
    save_json(f"phase2_e071_{bukrs}", all_e071)

    # === ANALYSIS ===

    # 1. Transport timeline
    print(f"\n  --- Transport Timeline ---")
    for t in target_transports:
        info = transport_info.get(t, {})
        status_map = {"R": "Released", "D": "Modifiable", "L": "Locked", "O": "Open", "N": "Released+Imported"}
        func_map = {"K": "Customizing", "W": "Workbench", "T": "ToC", "S": "Development", "R": "Repair"}
        status = status_map.get(info.get("TRSTATUS", ""), info.get("TRSTATUS", ""))
        func = func_map.get(info.get("TRFUNCTION", ""), info.get("TRFUNCTION", ""))
        text = info.get("AS4TEXT", "")
        e071k_count = sum(1 for r in all_e071k if r["TRKORR"] == t)
        e071_count = sum(1 for r in all_e071 if r["TRKORR"] == t)
        print(f"    {t} | {info.get('AS4DATE', ''):10s} | {info.get('AS4USER', ''):12s} | {status:12s} | {func:12s} | {e071_count} obj / {e071k_count} keys | {text}")

    # 2. Tables modified (from E071K)
    table_counts = Counter(r["OBJNAME"] for r in all_e071k)
    print(f"\n  --- Tables Modified (E071K, top 30) ---")
    for tbl, count in table_counts.most_common(30):
        # Which transports touch this table
        trs = sorted(set(r["TRKORR"] for r in all_e071k if r["OBJNAME"] == tbl))
        print(f"    {tbl:25s}: {count:5d} keys | Transports: {', '.join(trs[:3])}")

    # 3. Classify into Configuration vs Master Data
    config_tables = {
        "T001", "T001A", "T001B", "T001Q", "T001Z", "T001W",
        "SKB1", "SKA1",  # GL accounts
        "T012", "T012D", "T012K", "T012T",  # Banks
        "T042", "T042A", "T042B", "T042C", "T042E", "T042I", "T042T", "T042Z",  # Payments
        "T043G", "T043S", "T043T", "T043GT", "T043ST",  # Tolerances
        "T093B", "T093C", "T093D", "T093U", "T093V",  # Asset accounting
        "TKA00", "TKA01", "TKA02", "TKA07", "TKA09", "TKT09",  # Controlling
        "T169G", "T169P", "T169V",  # Invoice verification
        "T047",  # Dunning
        "T882",  # Consolidation
        "MARV", "ATPRA",  # MM
        "FM01", "FM01D", "FM01T",  # FM Area
        "FMHIVARNT", "FMHIVARNTT",  # FM Hierarchy
        "AAACC_OBJ",  # Account assignment
        "T035D", "T035U",  # Planning groups
        "CAREAMAINT",  # Credit
    }

    master_tables = {
        "CSKS", "CSKT",  # Cost centers
        "CSKA", "CSKB", "CSKU",  # Cost elements
        "CEPC", "CEPCT",  # Profit centers
        "FMCI", "FMCIT",  # Commitment items
        "FMFCTR", "FMFCTRT",  # Fund centers
        "FMFINCODE",  # Funds
        "LFA1", "LFB1",  # Vendors
        "KNA1", "KNB1",  # Customers
        "ANLA", "ANLZ",  # Assets
        "AUFK",  # Internal orders
        "PRPS", "PROJ",  # Projects / WBS
        "NRIV",  # Number ranges
    }

    print(f"\n  --- Classification ---")
    config_keys = 0
    master_keys = 0
    other_keys = 0
    config_detail = defaultdict(int)
    master_detail = defaultdict(int)
    other_detail = defaultdict(int)

    for r in all_e071k:
        tbl = r["OBJNAME"]
        if tbl in config_tables:
            config_keys += 1
            config_detail[tbl] += 1
        elif tbl in master_tables:
            master_keys += 1
            master_detail[tbl] += 1
        else:
            other_keys += 1
            other_detail[tbl] += 1

    print(f"    CONFIGURATION: {config_keys} keys across {len(config_detail)} tables")
    for tbl, cnt in sorted(config_detail.items(), key=lambda x: -x[1]):
        print(f"      {tbl:25s}: {cnt}")

    print(f"\n    MASTER DATA: {master_keys} keys across {len(master_detail)} tables")
    for tbl, cnt in sorted(master_detail.items(), key=lambda x: -x[1]):
        print(f"      {tbl:25s}: {cnt}")

    print(f"\n    OTHER/UNKNOWN: {other_keys} keys across {len(other_detail)} tables")
    for tbl, cnt in sorted(other_detail.items(), key=lambda x: -x[1])[:15]:
        print(f"      {tbl:25s}: {cnt}")

    # 4. Who did what
    print(f"\n  --- Who Did What ---")
    user_objects = defaultdict(lambda: defaultdict(int))
    for r in all_e071k:
        tr = r["TRKORR"]
        user = transport_info.get(tr, {}).get("AS4USER", "UNKNOWN")
        tbl = r["OBJNAME"]
        user_objects[user][tbl] += 1

    for user in sorted(user_objects.keys()):
        total = sum(user_objects[user].values())
        top_tables = sorted(user_objects[user].items(), key=lambda x: -x[1])[:5]
        top_str = ", ".join(f"{t}({c})" for t, c in top_tables)
        print(f"    {user:15s}: {total:5d} keys | Top: {top_str}")

    return all_e071k, all_e071, target_transports


# ============================================================
# PHASE 3: Gold DB master data analysis
# ============================================================
def phase3_gold_db(bukrs):
    print(f"\n{'=' * 70}")
    print(f"PHASE 3: Gold DB Master Data for {bukrs}")
    print(f"{'=' * 70}")

    db = sqlite3.connect(GOLD_DB)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    results = {}

    # Helper
    def query(label, sql, params=()):
        try:
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            print(f"  {label:40s}: {len(rows):6d} rows")
            return rows
        except Exception as e:
            print(f"  {label:40s}: ERROR - {e}")
            return []

    # --- FI Documents ---
    results["bkpf_first_docs"] = query(
        "FI Docs (BKPF) - first 3 months",
        "SELECT BUKRS, BELNR, BLART, BUDAT, BLDAT, USNAM, TCODE, WAERS FROM bkpf WHERE BUKRS = ? ORDER BY BUDAT LIMIT 100",
        (bukrs,)
    )

    results["bkpf_by_month"] = query(
        "FI Docs by month",
        "SELECT SUBSTR(BUDAT,1,6) as month, COUNT(*) as cnt, COUNT(DISTINCT BLART) as doc_types FROM bkpf WHERE BUKRS = ? GROUP BY month ORDER BY month",
        (bukrs,)
    )

    results["bkpf_by_tcode"] = query(
        "FI Docs by TCode (top 20)",
        "SELECT TCODE, COUNT(*) as cnt FROM bkpf WHERE BUKRS = ? GROUP BY TCODE ORDER BY cnt DESC LIMIT 20",
        (bukrs,)
    )

    results["bkpf_by_user"] = query(
        "FI Docs by User (top 20)",
        "SELECT USNAM, COUNT(*) as cnt FROM bkpf WHERE BUKRS = ? GROUP BY USNAM ORDER BY cnt DESC LIMIT 20",
        (bukrs,)
    )

    # --- GL Accounts (bsis/bsas = open/cleared items) ---
    for tbl in ["bsis", "bsas", "bsik", "bsak", "bsid", "bsad"]:
        results[f"{tbl}_count"] = query(
            f"{tbl.upper()} line items",
            f"SELECT COUNT(*) as cnt FROM {tbl} WHERE BUKRS = ?",
            (bukrs,)
        )

    # --- Vendors (bsik/bsak = vendor open/cleared) ---
    results["vendors_active"] = query(
        "Distinct vendors with postings (BSIK+BSAK)",
        """SELECT 'BSIK' as src, COUNT(DISTINCT LIFNR) as cnt FROM bsik WHERE BUKRS = ?
           UNION ALL
           SELECT 'BSAK', COUNT(DISTINCT LIFNR) FROM bsak WHERE BUKRS = ?""",
        (bukrs, bukrs)
    )

    # --- Customers (bsid/bsad) ---
    results["customers_active"] = query(
        "Distinct customers with postings (BSID+BSAD)",
        """SELECT 'BSID' as src, COUNT(DISTINCT KUNNR) as cnt FROM bsid WHERE BUKRS = ?
           UNION ALL
           SELECT 'BSAD', COUNT(DISTINCT KUNNR) FROM bsad WHERE BUKRS = ?""",
        (bukrs, bukrs)
    )

    # --- FM data ---
    results["fmifiit_count"] = query(
        "FM-FI Integration (FMIFIIT)",
        "SELECT COUNT(*) as cnt FROM fmifiit_full WHERE BUKRS = ?",
        (bukrs,)
    )

    results["fmifiit_by_month"] = query(
        "FMIFIIT by month",
        "SELECT SUBSTR(BUDAT,1,6) as month, COUNT(*) as cnt FROM fmifiit_full WHERE BUKRS = ? GROUP BY month ORDER BY month",
        (bukrs,)
    )

    # --- Projects ---
    results["proj_projects"] = query(
        "Projects (PROJ)",
        "SELECT PSPID, PSPNR, POST1, ERDAT, ERNAM, BUKRS FROM proj WHERE BUKRS = ?",
        (bukrs,)
    )

    results["prps_wbs"] = query(
        "WBS Elements (PRPS)",
        "SELECT COUNT(*) as cnt FROM prps WHERE BUKRS = ?",
        (bukrs,)
    )

    # --- Fund Centers ---
    results["fund_centers"] = query(
        "Fund Centers",
        "SELECT * FROM fund_centers LIMIT 5"
    )

    # --- Funds ---
    results["funds"] = query(
        "Funds",
        "SELECT * FROM funds LIMIT 5"
    )

    # --- Procurement ---
    results["ekko_po"] = query(
        "Purchase Orders (EKKO)",
        "SELECT COUNT(*) as cnt FROM ekko WHERE BUKRS = ?",
        (bukrs,)
    )

    # --- Banks ---
    results["t012_banks"] = query(
        "House Banks (T012)",
        "SELECT * FROM T012 WHERE BUKRS = ?",
        (bukrs,)
    )
    results["t012k_accounts"] = query(
        "Bank Accounts (T012K)",
        "SELECT * FROM T012K WHERE BUKRS = ?",
        (bukrs,)
    )

    # --- Payment config ---
    results["t042_payment"] = query(
        "Payment Config (T042)",
        "SELECT * FROM T042 WHERE ZBUKR = ?",
        (bukrs,)
    )
    results["t042i_ranking"] = query(
        "Bank Ranking (T042I)",
        "SELECT * FROM T042I WHERE ZBUKR = ?",
        (bukrs,)
    )

    # --- Assets (CDHDR as proxy - ANLA changes) ---
    results["asset_changes"] = query(
        "Asset changes (CDHDR OBJECTCLAS=ANLA)",
        "SELECT COUNT(*) as cnt FROM cdhdr WHERE OBJECTCLAS = 'ANLA' AND OBJECTID LIKE ?",
        (f"{bukrs}%",)
    )

    # --- Bank statement ---
    results["febep_count"] = query(
        "Bank Statement Items (FEBEP)",
        "SELECT COUNT(*) as cnt FROM FEBEP WHERE BUKRS = ?",
        (bukrs,)
    )

    results["febko_count"] = query(
        "Bank Statement Headers (FEBKO)",
        "SELECT COUNT(*) as cnt FROM FEBKO WHERE BUKRS = ?",
        (bukrs,)
    )

    # --- Payment runs (REGUH) ---
    results["reguh_payments"] = query(
        "Payment Run Items (REGUH)",
        "SELECT COUNT(*) as cnt FROM REGUH WHERE ZBUKR = ?",
        (bukrs,)
    )

    db.close()
    save_json(f"phase3_gold_db_{bukrs}", results)
    return results


# ============================================================
# PHASE 4: Generate report
# ============================================================
def phase4_report(bukrs, transport_info, all_e071k, all_e071, target_transports, gold_data):
    print(f"\n{'=' * 70}")
    print(f"PHASE 4: Blueprint Report for {bukrs}")
    print(f"{'=' * 70}")

    report = []
    report.append(f"{'=' * 80}")
    report.append(f"REVERSE ENGINEERING BLUEPRINT: Company Code {bukrs}")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"Source: P01 (Production) - RFC + Gold DB")
    report.append(f"{'=' * 80}")

    # Transport summary
    report.append(f"\n## CREATION TRANSPORTS")
    report.append(f"{'TRKORR':15s} | {'Date':10s} | {'User':12s} | {'Status':12s} | {'Type':12s} | {'Obj':5s} | {'Keys':5s} | Description")
    report.append("-" * 120)
    for t in target_transports:
        info = transport_info.get(t, {})
        e071k_count = sum(1 for r in all_e071k if r["TRKORR"] == t)
        e071_count = sum(1 for r in all_e071 if r["TRKORR"] == t)
        status_map = {"R": "Released", "D": "Modifiable", "L": "Locked", "N": "Rel+Import"}
        func_map = {"K": "Customizing", "W": "Workbench"}
        report.append(f"{t:15s} | {info.get('AS4DATE', ''):10s} | {info.get('AS4USER', ''):12s} | "
                       f"{status_map.get(info.get('TRSTATUS', ''), '?'):12s} | "
                       f"{func_map.get(info.get('TRFUNCTION', ''), '?'):12s} | "
                       f"{e071_count:5d} | {e071k_count:5d} | {info.get('AS4TEXT', '')}")

    # Tables summary
    report.append(f"\n## CONFIGURATION TABLES")
    config_tables_set = {"T001", "T001A", "T001B", "T001Q", "T001Z", "SKB1", "T012", "T012D", "T012K", "T012T",
                         "T042", "T042A", "T042B", "T042C", "T042E", "T042I", "T042T", "T042Z",
                         "T043G", "T043S", "T043T", "T093B", "T093C", "T093D", "FM01", "TKA01", "AAACC_OBJ"}
    for r in sorted(set((r["OBJNAME"], r["TRKORR"]) for r in all_e071k)):
        if r[0] in config_tables_set:
            count = sum(1 for x in all_e071k if x["OBJNAME"] == r[0] and x["TRKORR"] == r[1])
            user = transport_info.get(r[1], {}).get("AS4USER", "?")
            report.append(f"  {r[0]:20s}: {count:5d} keys | Transport: {r[1]} ({user})")

    # Gold DB summary
    report.append(f"\n## MASTER DATA FROM GOLD DB")
    for key, value in gold_data.items():
        if isinstance(value, list) and value:
            if len(value) == 1 and "cnt" in value[0]:
                report.append(f"  {key:40s}: {value[0]['cnt']}")
            else:
                report.append(f"  {key:40s}: {len(value)} rows")

    text = "\n".join(report)
    path = os.path.join(OUTPUT_DIR, f"blueprint_{bukrs}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\n  Report saved: {path}")
    print(text)
    return text


# ============================================================
# MAIN
# ============================================================
def main():
    print("Connecting to P01 (Production) via SNC/SSO...")
    conn = get_connection("P01")
    print("Connected.\n")

    # Phase 1: Identify
    bukrs_data, transport_info = phase1_identify_newest(conn)

    if not bukrs_data:
        print("\nNo company codes found in E071K. Check if E071K is accessible.")
        conn.close()
        return

    # Find the newest by transport date
    bukrs_dates = {}
    for bukrs, transports in bukrs_data.items():
        dates = [transport_info.get(t, {}).get("AS4DATE", "") for t in transports]
        dates = [d for d in dates if d]
        if dates:
            bukrs_dates[bukrs] = max(dates)

    if bukrs_dates:
        newest = max(bukrs_dates.items(), key=lambda x: x[1])
        target_bukrs = newest[0]
        print(f"\n  >>> NEWEST company code by transport date: {target_bukrs} (latest transport: {newest[1]})")
    else:
        # Fallback: pick the one with most transports
        target_bukrs = max(bukrs_data.items(), key=lambda x: len(x[1]))[0]
        print(f"\n  >>> Most active company code: {target_bukrs}")

    # Phase 2: Deep dive
    all_e071k, all_e071, target_transports = phase2_deep_dive(conn, target_bukrs, bukrs_data, transport_info)

    conn.close()
    print("\nRFC connection closed.")

    # Phase 3: Gold DB
    gold_data = phase3_gold_db(target_bukrs)

    # Phase 4: Report
    phase4_report(target_bukrs, transport_info, all_e071k, all_e071, target_transports, gold_data)

    print(f"\n{'=' * 70}")
    print(f"DONE. All output in: {OUTPUT_DIR}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
