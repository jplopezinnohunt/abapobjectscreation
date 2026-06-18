"""
extract_sapf100_variants.py
============================
Forensic extraction of all SAPF100 (F.05) variants from P01.
Cross-references variant account ranges with T030H defects and SKB1 blocks.

USAGE:
    python extract_sapf100_variants.py

OUTPUT:
    Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db
        Tables: sapf100_vari, sapf100_varid
    companions/fx_variant_forensic.json  (summary for companion)
"""

import os, sys, json, sqlite3
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = r"C:\Users\jp_lopez\projects\abapobjectscreation"
sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import get_connection, rfc_read_paginated

GOLD_DB = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction",
                       "sqlite", "p01_gold_master_data.db")

# SAP program name for F.05 / FX Revaluation
PROGRAM = "SAPF100"

VARI_FIELDS  = ["MANDT","REPORT","VARIANT","VTEXT","ENAME","CDATE","CTIME",
                "AENAME","ADATE","ATIME","VARI_FLAG"]
VARID_FIELDS = ["MANDT","REPORT","VARIANT","SELNAME","KIND","SIGN","OPTION",
                "LOW","HIGH"]


def main():
    print(f"[{datetime.now():%H:%M:%S}] Connecting to P01...")
    conn = get_connection("P01")
    print(f"[{datetime.now():%H:%M:%S}] P01 connected")

    # 1. Extract VARI header
    print(f"[{datetime.now():%H:%M:%S}] Extracting VARI for {PROGRAM}...")
    vari_rows = rfc_read_paginated(conn, "VARI", VARI_FIELDS,
                                   f"REPORT = '{PROGRAM}'", batch_size=500, throttle=1.0)
    print(f"  -> {len(vari_rows)} variants found")

    # 2. Extract VARID selection parameters
    print(f"[{datetime.now():%H:%M:%S}] Extracting VARID for {PROGRAM}...")
    varid_rows = rfc_read_paginated(conn, "VARID", VARID_FIELDS,
                                    f"REPORT = '{PROGRAM}'", batch_size=2000, throttle=1.0)
    print(f"  -> {len(varid_rows)} VARID rows found")

    conn.close()

    # 3. Store to SQLite
    db = sqlite3.connect(GOLD_DB)
    db.execute("DROP TABLE IF EXISTS sapf100_vari")
    db.execute(f"CREATE TABLE sapf100_vari ({', '.join(f'{f} TEXT' for f in VARI_FIELDS)})")
    placeholders = ",".join(["?"] * len(VARI_FIELDS))
    db.executemany(f"INSERT INTO sapf100_vari VALUES ({placeholders})",
                   [tuple(r.get(f,"") for f in VARI_FIELDS) for r in vari_rows])

    db.execute("DROP TABLE IF EXISTS sapf100_varid")
    db.execute(f"CREATE TABLE sapf100_varid ({', '.join(f'{f} TEXT' for f in VARID_FIELDS)})")
    placeholders2 = ",".join(["?"] * len(VARID_FIELDS))
    db.executemany(f"INSERT INTO sapf100_varid VALUES ({placeholders2})",
                   [tuple(r.get(f,"") for f in VARID_FIELDS) for r in varid_rows])
    db.commit()
    print(f"[{datetime.now():%H:%M:%S}] Saved to Gold DB: {len(vari_rows)} VARI + {len(varid_rows)} VARID rows")

    # 4. Forensic cross-reference
    print(f"\n[{datetime.now():%H:%M:%S}] === FORENSIC ANALYSIS ===")

    # Variants per company code / user
    print("\n--- Variants by company code ---")
    cur = db.cursor()
    cur.execute("""
        SELECT v.VARIANT, v.VTEXT, v.ENAME, v.ADATE,
               GROUP_CONCAT(CASE WHEN d.SELNAME='BUKRS' THEN d.LOW END) as bukrs_values,
               GROUP_CONCAT(CASE WHEN d.SELNAME='STIDA' THEN d.LOW END) as stida,
               GROUP_CONCAT(CASE WHEN d.SELNAME='HKONT' THEN d.LOW||'-'||d.HIGH END) as hkont_range
        FROM sapf100_vari v
        LEFT JOIN sapf100_varid d ON d.VARIANT = v.VARIANT AND d.REPORT = v.REPORT
        WHERE v.REPORT = ?
        GROUP BY v.VARIANT
        ORDER BY v.ENAME, v.VARIANT
    """, (PROGRAM,))
    rows = cur.fetchall()
    print(f"  Total variants: {len(rows)}")
    for r in rows:
        print(f"  {r[0]:20s} | {(r[1] or '')[:35]:35s} | user={r[2]:12s} | modified={r[3]}"
              f" | BUKRS={r[4]} | STIDA={r[5]} | HKONT={r[6]}")

    # Per-variant: which HKONTs are in scope vs blocked
    print("\n--- HKONT coverage per variant ---")
    cur.execute("""
        SELECT VARIANT, SELNAME, KIND, SIGN, OPTION, LOW, HIGH
        FROM sapf100_varid
        WHERE REPORT = ? AND SELNAME IN ('HKONT','BUKRS','STIDA','BKTOPL')
        ORDER BY VARIANT, SELNAME
    """, (PROGRAM,))
    for r in cur.fetchall():
        print(f"  {r[0]:20s} {r[1]:8s} {r[2]} {r[3]}{r[4]} LOW={r[5]} HIGH={r[6]}")

    # Summary JSON for companion
    summary = {
        "extracted_at": datetime.now().isoformat(),
        "program": PROGRAM,
        "total_variants": len(vari_rows),
        "total_varid_rows": len(varid_rows),
        "variants": [
            {
                "variant": r["VARIANT"],
                "text": r["VTEXT"],
                "owner": r["ENAME"],
                "modified": r["ADATE"],
            }
            for r in vari_rows
        ]
    }
    out_json = os.path.join(PROJECT_ROOT, "companions", "fx_variant_forensic.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n[{datetime.now():%H:%M:%S}] Summary written: {out_json}")
    print(f"[{datetime.now():%H:%M:%S}] DONE")


if __name__ == "__main__":
    main()
