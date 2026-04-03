"""
company_code_blueprint.py
=========================
Identify the last company code created in P01 (production) and extract:
  1. All company codes (T001) to find the most recently created
  2. Transport orders related to that company code creation
  3. Master data created in the first 3 months (cost centers, cost elements,
     commitment items, fund centers, vendors, customers, GL accounts)

Purpose: Build a reference blueprint for the STEM company code copy.

Usage:
    python company_code_blueprint.py
"""

import sys
import io
import os
import json
from datetime import datetime

# UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "blueprint_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_json(name, data):
    path = os.path.join(OUTPUT_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved {path} ({len(data)} rows)")

def save_report(name, text):
    path = os.path.join(OUTPUT_DIR, f"{name}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  -> Saved {path}")


# ============================================================
# PHASE 1: Identify all company codes and find the newest
# ============================================================
def phase1_company_codes(conn):
    print("\n=== PHASE 1: Company Codes (T001) ===")

    fields = ["BUKRS", "BUTXT", "ORT01", "LAND1", "WAERS", "KTOPL", "PERIV", "ADRNR"]
    rows = rfc_read_paginated(conn, "T001", fields, "", batch_size=500, throttle=1.0)

    print(f"  Total company codes in P01: {len(rows)}")
    for r in sorted(rows, key=lambda x: x.get("BUKRS", "")):
        print(f"    {r['BUKRS']:6s} | {r.get('BUTXT',''):40s} | {r.get('LAND1','')} | {r.get('WAERS','')} | CoA={r.get('KTOPL','')}")

    save_json("t001_all_company_codes", rows)
    return rows


# ============================================================
# PHASE 2: Transport history for a given company code
# ============================================================
def phase2_transports(conn, bukrs):
    print(f"\n=== PHASE 2: Transports for company code {bukrs} ===")

    # Search E071K for TABKEY containing the company code
    # E071K stores table keys - the company code appears in TABKEY
    print(f"  Searching E071K for TABKEY containing '{bukrs}'...")

    fields_e071k = ["TRKORR", "PGMID", "OBJECT", "OBJNAME", "TABKEY"]
    where_clause = f"TABKEY LIKE '%{bukrs}%'"
    rows_e071k = rfc_read_paginated(conn, "E071K", fields_e071k, where_clause, batch_size=5000, throttle=2.0)

    print(f"  E071K entries referencing {bukrs}: {len(rows_e071k)}")

    # Get unique transport numbers
    transport_ids = sorted(set(r["TRKORR"] for r in rows_e071k))
    print(f"  Unique transports: {len(transport_ids)}")

    # Get transport details from E070
    transport_details = []
    if transport_ids:
        # Query in batches of 20
        for i in range(0, len(transport_ids), 20):
            batch = transport_ids[i:i+20]
            in_clause = " OR ".join([f"TRKORR = '{t}'" for t in batch])
            fields_e070 = ["TRKORR", "TRFUNCTION", "TRSTATUS", "TARSYSTEM", "AS4USER", "AS4DATE", "AS4TIME", "STRKORR"]
            rows_e070 = rfc_read_paginated(conn, "E070", fields_e070, in_clause, batch_size=500, throttle=1.0)
            transport_details.extend(rows_e070)

    # Get transport descriptions from E07T
    transport_texts = {}
    if transport_ids:
        for i in range(0, len(transport_ids), 20):
            batch = transport_ids[i:i+20]
            in_clause = " OR ".join([f"TRKORR = '{t}'" for t in batch])
            fields_e07t = ["TRKORR", "AS4TEXT"]
            try:
                rows_e07t = rfc_read_paginated(conn, "E07T", fields_e07t, in_clause, batch_size=500, throttle=1.0)
                for r in rows_e07t:
                    transport_texts[r["TRKORR"]] = r.get("AS4TEXT", "")
            except Exception as e:
                print(f"  Warning: E07T query failed: {e}")

    # Merge details + texts
    for td in transport_details:
        td["AS4TEXT"] = transport_texts.get(td["TRKORR"], "")

    # Sort by date
    transport_details.sort(key=lambda x: x.get("AS4DATE", "") + x.get("AS4TIME", ""))

    print(f"\n  Transport details:")
    for td in transport_details:
        status_map = {"R": "Released", "D": "Modifiable", "L": "Locked", "O": "Open", "N": "Released+Imported"}
        status = status_map.get(td.get("TRSTATUS", ""), td.get("TRSTATUS", ""))
        func_map = {"K": "Customizing", "W": "Workbench", "T": "ToC", "S": "Development"}
        func = func_map.get(td.get("TRFUNCTION", ""), td.get("TRFUNCTION", ""))
        print(f"    {td['TRKORR']} | {td.get('AS4DATE','')} | {td.get('AS4USER',''):12s} | {status:12s} | {func:12s} | {td.get('AS4TEXT','')}")

    save_json(f"transports_{bukrs}", transport_details)
    save_json(f"e071k_{bukrs}", rows_e071k)

    # Count objects per transport
    print(f"\n  Objects per transport:")
    from collections import Counter
    tr_counts = Counter(r["TRKORR"] for r in rows_e071k)
    for tr, count in tr_counts.most_common():
        text = transport_texts.get(tr, "")
        print(f"    {tr}: {count:5d} keys | {text}")

    # Count unique tables
    table_counts = Counter(r["OBJNAME"] for r in rows_e071k)
    print(f"\n  Tables modified (top 20):")
    for tbl, count in table_counts.most_common(20):
        print(f"    {tbl:20s}: {count:5d} keys")

    return transport_details, rows_e071k


# ============================================================
# PHASE 3: Master data created for a company code
# ============================================================
def phase3_master_data(conn, bukrs, start_date=None, end_date=None):
    print(f"\n=== PHASE 3: Master Data for {bukrs} ===")

    results = {}

    # 3a. GL Accounts (SKB1) - company code segment
    print(f"\n  [3a] GL Accounts (SKB1) for {bukrs}...")
    try:
        fields = ["BUKRS", "SAKNR", "WAERS", "MWSKZ", "MITKZ", "XOPVW", "FSTAG"]
        rows = rfc_read_paginated(conn, "SKB1", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      GL accounts: {len(rows)}")
        results["skb1_gl_accounts"] = rows
        save_json(f"skb1_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3b. Cost Centers (CSKS) - master data
    print(f"\n  [3b] Cost Centers (CSKS) for controlling area {bukrs}...")
    try:
        fields = ["KOKRS", "KOSTL", "DATBI", "DATAB", "BUKRS", "KOSAR", "VERAK", "KTEXT"]
        rows = rfc_read_paginated(conn, "CSKS", fields, f"KOKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        if not rows:
            # Try with BUKRS instead of KOKRS
            rows = rfc_read_paginated(conn, "CSKS", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Cost centers: {len(rows)}")
        results["csks_cost_centers"] = rows
        save_json(f"csks_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3c. Cost Elements (CSKA) - primary cost elements at controlling area level
    print(f"\n  [3c] Cost Elements (CSKA) for controlling area {bukrs}...")
    try:
        fields = ["KSTAR", "KOKRS", "DATBI", "DATAB", "KATYP", "KTEXT"]
        rows = rfc_read_paginated(conn, "CSKA", fields, f"KOKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Cost elements: {len(rows)}")
        results["cska_cost_elements"] = rows
        save_json(f"cska_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3d. Commitment Items (FMCI) - FM commitment items
    print(f"\n  [3d] Commitment Items (FMCI) for FM area...")
    try:
        fields = ["FIKRS", "FIPEX", "FIVOR", "DATAB", "DATBI", "BEZEI"]
        # Try with FM area = bukrs first, then with common FM areas
        rows = rfc_read_paginated(conn, "FMCI", fields, f"FIKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        if not rows:
            # UNESCO uses shared FM areas like '01' or 'UNES'
            for fm_area in ["01", "UNES"]:
                rows = rfc_read_paginated(conn, "FMCI", fields, f"FIKRS = '{fm_area}'", batch_size=5000, throttle=2.0)
                if rows:
                    print(f"      (Found under FM area '{fm_area}')")
                    break
        print(f"      Commitment items: {len(rows)}")
        results["fmci_commitment_items"] = rows
        save_json(f"fmci_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3e. Fund Centers (FMFCTR)
    print(f"\n  [3e] Fund Centers (FMFCTR) for {bukrs}...")
    try:
        fields = ["FIKRS", "FICTR", "DATAB", "DATBI", "BEZEICH"]
        rows = rfc_read_paginated(conn, "FMFCTR", fields, f"FICTR LIKE '{bukrs}%'", batch_size=5000, throttle=2.0)
        if not rows:
            # Try FM area
            for fm_area in [bukrs, "01", "UNES"]:
                rows = rfc_read_paginated(conn, "FMFCTR", fields, f"FIKRS = '{fm_area}'", batch_size=5000, throttle=2.0)
                if rows:
                    print(f"      (Found under FM area '{fm_area}', filtering by naming convention)")
                    break
        print(f"      Fund centers: {len(rows)}")
        results["fmfctr_fund_centers"] = rows
        save_json(f"fmfctr_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3f. Vendors extended to this company code (LFB1)
    print(f"\n  [3f] Vendors in {bukrs} (LFB1)...")
    try:
        fields = ["LIFNR", "BUKRS", "AKONT", "ZTERM", "ZWELS", "LNRZE", "ERDAT"]
        rows = rfc_read_paginated(conn, "LFB1", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Vendors: {len(rows)}")
        results["lfb1_vendors"] = rows
        save_json(f"lfb1_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3g. Customers extended to this company code (KNB1)
    print(f"\n  [3g] Customers in {bukrs} (KNB1)...")
    try:
        fields = ["KUNNR", "BUKRS", "AKONT", "ZTERM", "ZWELS", "ERDAT"]
        rows = rfc_read_paginated(conn, "KNB1", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Customers: {len(rows)}")
        results["knb1_customers"] = rows
        save_json(f"knb1_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3h. Profit Centers (CEPC)
    print(f"\n  [3h] Profit Centers (CEPC) for {bukrs}...")
    try:
        fields = ["PRCTR", "KOKRS", "DATBI", "DATAB", "BUKRS", "KTEXT"]
        rows = rfc_read_paginated(conn, "CEPC", fields, f"KOKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        if not rows:
            rows = rfc_read_paginated(conn, "CEPC", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Profit centers: {len(rows)}")
        results["cepc_profit_centers"] = rows
        save_json(f"cepc_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3h2. Internal Orders (AUFK)
    print(f"\n  [3h2] Internal Orders (AUFK) for {bukrs}...")
    try:
        fields = ["AUFNR", "AUART", "BUKRS", "KOKRS", "KTEXT", "ERDAT", "ERNAM", "USER0", "PHAS0", "PHAS1", "PHAS2", "PHAS3"]
        rows = rfc_read_paginated(conn, "AUFK", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Internal orders: {len(rows)}")
        results["aufk_internal_orders"] = rows
        save_json(f"aufk_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3h3. WBS Elements / Projects (PRPS)
    print(f"\n  [3h3] WBS Elements (PRPS) for {bukrs}...")
    try:
        fields = ["POSID", "PSPNR", "PSPHI", "BUKRS", "ERDAT", "ERNAM", "POST1", "PRART", "PKOKR", "PRCTR"]
        rows = rfc_read_paginated(conn, "PRPS", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      WBS elements: {len(rows)}")
        results["prps_wbs_elements"] = rows
        save_json(f"prps_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3h4. Project Definitions (PROJ)
    print(f"\n  [3h4] Project Definitions (PROJ) for {bukrs}...")
    try:
        fields = ["PSPID", "PSPNR", "BUKRS", "ERDAT", "ERNAM", "POST1", "VBUKR"]
        rows = rfc_read_paginated(conn, "PROJ", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Projects: {len(rows)}")
        results["proj_projects"] = rows
        save_json(f"proj_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3h5. Funds (FMFINT - FM Fund master)
    print(f"\n  [3h5] Funds / Grants (FMFINCODE)...")
    try:
        fields = ["FINCODE", "FIKRS", "DATAB", "DATBI", "BEZEICH"]
        rows = rfc_read_paginated(conn, "FMFINCODE", fields, f"FIKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        if not rows:
            for fm_area in ["01", "UNES"]:
                rows = rfc_read_paginated(conn, "FMFINCODE", fields, f"FIKRS = '{fm_area}'", batch_size=5000, throttle=2.0)
                if rows:
                    print(f"      (Found under FM area '{fm_area}')")
                    break
        print(f"      Funds: {len(rows)}")
        results["fmfincode_funds"] = rows
        save_json(f"fmfincode_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3h6. Assets (ANLA - Asset master)
    print(f"\n  [3h6] Assets (ANLA) for {bukrs}...")
    try:
        fields = ["BUKRS", "ANLN1", "ANLN2", "ANLKL", "ERDAT", "ERNAM", "TXT50", "AKTIV"]
        rows = rfc_read_paginated(conn, "ANLA", fields, f"BUKRS = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Assets: {len(rows)}")
        results["anla_assets"] = rows
        save_json(f"anla_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3i. Number Ranges (NRIV) - to compare against STEM
    print(f"\n  [3i] Number Ranges (NRIV) for {bukrs}...")
    try:
        fields = ["OBJECT", "SUBOBJECT", "NRRANGENR", "FROMNUMBER", "TONUMBER", "NRLEVEL"]
        rows = rfc_read_paginated(conn, "NRIV", fields, f"SUBOBJECT = '{bukrs}'", batch_size=5000, throttle=2.0)
        print(f"      Number range intervals: {len(rows)}")
        results["nriv_number_ranges"] = rows
        save_json(f"nriv_{bukrs}", rows)
    except Exception as e:
        print(f"      Error: {e}")

    # 3j. House Banks (T012 + T012K)
    print(f"\n  [3j] House Banks (T012/T012K) for {bukrs}...")
    try:
        fields_t012 = ["BUKRS", "HBKID", "BANKS", "BANKL", "BANKN", "BANKA"]
        rows_t012 = rfc_read_paginated(conn, "T012", fields_t012, f"BUKRS = '{bukrs}'", batch_size=500, throttle=1.0)
        print(f"      House banks: {len(rows_t012)}")

        fields_t012k = ["BUKRS", "HBKID", "HKTID", "BANKN", "WAESSION", "HKONT"]
        # T012K might have different field names, try common ones
        try:
            rows_t012k = rfc_read_paginated(conn, "T012K", fields_t012k, f"BUKRS = '{bukrs}'", batch_size=500, throttle=1.0)
        except:
            fields_t012k = ["BUKRS", "HBKID", "HKTID", "BANKN", "HKONT"]
            rows_t012k = rfc_read_paginated(conn, "T012K", fields_t012k, f"BUKRS = '{bukrs}'", batch_size=500, throttle=1.0)
        print(f"      Bank accounts: {len(rows_t012k)}")

        results["t012_house_banks"] = rows_t012
        results["t012k_bank_accounts"] = rows_t012k
        save_json(f"t012_{bukrs}", rows_t012)
        save_json(f"t012k_{bukrs}", rows_t012k)
    except Exception as e:
        print(f"      Error: {e}")

    return results


# ============================================================
# SUMMARY REPORT
# ============================================================
def generate_summary(bukrs, company_codes, transports, e071k_rows, master_data):
    report = []
    report.append(f"=" * 80)
    report.append(f"COMPANY CODE BLUEPRINT: {bukrs}")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"Source: P01 (Production)")
    report.append(f"=" * 80)

    # Company code info
    cc_info = next((r for r in company_codes if r["BUKRS"] == bukrs), {})
    report.append(f"\nCompany Code: {bukrs}")
    report.append(f"  Name:     {cc_info.get('BUTXT', 'N/A')}")
    report.append(f"  City:     {cc_info.get('ORT01', 'N/A')}")
    report.append(f"  Country:  {cc_info.get('LAND1', 'N/A')}")
    report.append(f"  Currency: {cc_info.get('WAERS', 'N/A')}")
    report.append(f"  CoA:      {cc_info.get('KTOPL', 'N/A')}")

    # Transport summary
    report.append(f"\n{'='*60}")
    report.append(f"TRANSPORTS: {len(transports)} orders")
    report.append(f"{'='*60}")
    for td in transports:
        report.append(f"  {td['TRKORR']} | {td.get('AS4DATE','')} | {td.get('AS4USER',''):12s} | {td.get('AS4TEXT','')}")

    # Master data summary
    report.append(f"\n{'='*60}")
    report.append(f"MASTER DATA COUNTS")
    report.append(f"{'='*60}")
    labels = {
        "skb1_gl_accounts": "GL Accounts (SKB1)",
        "csks_cost_centers": "Cost Centers (CSKS)",
        "cska_cost_elements": "Cost Elements (CSKA)",
        "fmci_commitment_items": "Commitment Items (FMCI)",
        "fmfctr_fund_centers": "Fund Centers (FMFCTR)",
        "fmfincode_funds": "Funds / Grants (FMFINCODE)",
        "lfb1_vendors": "Vendors (LFB1)",
        "knb1_customers": "Customers (KNB1)",
        "cepc_profit_centers": "Profit Centers (CEPC)",
        "aufk_internal_orders": "Internal Orders (AUFK)",
        "prps_wbs_elements": "WBS Elements (PRPS)",
        "proj_projects": "Projects (PROJ)",
        "anla_assets": "Assets (ANLA)",
        "nriv_number_ranges": "Number Ranges (NRIV)",
        "t012_house_banks": "House Banks (T012)",
        "t012k_bank_accounts": "Bank Accounts (T012K)",
    }
    for key, label in labels.items():
        count = len(master_data.get(key, []))
        report.append(f"  {label:35s}: {count:6d}")

    text = "\n".join(report)
    save_report(f"blueprint_{bukrs}", text)
    print(f"\n{'='*60}")
    print(text)
    return text


# ============================================================
# MAIN
# ============================================================
def main():
    print("Connecting to P01 (Production) via SNC/SSO...")
    conn = get_connection("P01")
    print("Connected.")

    # Phase 1: Get all company codes
    company_codes = phase1_company_codes(conn)

    # Ask user or auto-detect newest
    # For now, print all and let the output guide us
    # The "newest" is hard to determine from T001 alone (no creation date field)
    # We'll look at which ones have recent transport activity

    # Let's also check CDHDR for T001 changes to find creation dates
    print("\n=== Bonus: T001 Change Documents (CDHDR) to find creation dates ===")
    try:
        fields_cdhdr = ["OBJECTCLAS", "OBJECTID", "CHANGENR", "USERNAME", "UDATE", "UTIME", "TCODE", "CHANGE_IND"]
        # CDHDR for T001 changes - look for recent ones (2023-2026)
        rows_cdhdr = rfc_read_paginated(
            conn, "CDHDR", fields_cdhdr,
            "OBJECTCLAS = 'BUKRS' AND UDATE >= '20230101'",
            batch_size=5000, throttle=2.0
        )
        if rows_cdhdr:
            print(f"  Company code changes since 2023: {len(rows_cdhdr)}")
            # Group by OBJECTID (company code)
            from collections import defaultdict
            by_cc = defaultdict(list)
            for r in rows_cdhdr:
                by_cc[r.get("OBJECTID", "").strip()].append(r)

            print(f"\n  Company codes with changes since 2023:")
            for cc, changes in sorted(by_cc.items(), key=lambda x: min(c.get("UDATE","") for c in x[1])):
                dates = sorted(set(c.get("UDATE","") for c in changes))
                users = sorted(set(c.get("USERNAME","") for c in changes))
                tcodes = sorted(set(c.get("TCODE","") for c in changes))
                print(f"    {cc:6s} | First: {dates[0]} | Last: {dates[-1]} | Changes: {len(changes)} | Users: {', '.join(users)} | TCodes: {', '.join(tcodes)}")

            save_json("cdhdr_bukrs_changes", rows_cdhdr)
        else:
            print("  No CDHDR entries found for OBJECTCLAS='BUKRS'")
    except Exception as e:
        print(f"  CDHDR query error (trying alternate): {e}")
        # Try CDPOS approach or skip

    # Based on the output, we'll identify the newest company code
    # For now, let's extract for ALL recent ones and compare
    print("\n" + "="*60)
    print("PHASE 1 COMPLETE - Review the company codes above.")
    print("The script will now extract master data for the most recent ones.")
    print("="*60)

    # Extract master data for company codes that look recent
    # We'll extract for the ones with CDHDR activity
    # But first, let's do a targeted extraction for common UNESCO codes
    # to find which one was created last

    # Get ALL company codes sorted, skip very old standard ones
    recent_candidates = [r for r in company_codes if r.get("BUKRS","") not in ("", "0001")]

    print(f"\n  Total non-standard company codes: {len(recent_candidates)}")
    print("  Extracting transport history for all to find the newest...")

    # Quick scan: check E071K for T001 entries per company code
    print("\n  Scanning E071K for T001 entries by company code...")
    fields_scan = ["TRKORR", "TABKEY"]
    try:
        rows_t001_keys = rfc_read_paginated(conn, "E071K", fields_scan, "OBJNAME = 'T001'", batch_size=5000, throttle=2.0)
        print(f"  Total T001 transport keys: {len(rows_t001_keys)}")

        # Extract BUKRS from TABKEY (format: 350BUKRS...)
        from collections import Counter
        bukrs_in_transports = Counter()
        bukrs_transport_map = {}
        for r in rows_t001_keys:
            tabkey = r.get("TABKEY", "")
            # T001 key is MANDT(3) + BUKRS(4)
            if len(tabkey) >= 7:
                extracted_bukrs = tabkey[3:7].strip()
                if extracted_bukrs:
                    bukrs_in_transports[extracted_bukrs] += 1
                    if extracted_bukrs not in bukrs_transport_map:
                        bukrs_transport_map[extracted_bukrs] = []
                    bukrs_transport_map[extracted_bukrs].append(r["TRKORR"])

        print(f"\n  Company codes found in T001 transport keys:")
        for cc, count in bukrs_in_transports.most_common():
            transports = sorted(set(bukrs_transport_map.get(cc, [])))
            print(f"    {cc:6s}: {count:3d} keys, transports: {', '.join(transports[:5])}")

        save_json("e071k_t001_scan", rows_t001_keys)
    except Exception as e:
        print(f"  E071K scan error: {e}")

    # Now extract detailed data for the user to review
    # The user will tell us which company code to deep-dive into
    print("\n" + "="*60)
    print("SCAN COMPLETE")
    print("Review the output above to identify the most recently created")
    print("company code, then we'll do a deep extraction for that one.")
    print("="*60)

    conn.close()
    print("\nConnection closed.")


if __name__ == "__main__":
    main()
