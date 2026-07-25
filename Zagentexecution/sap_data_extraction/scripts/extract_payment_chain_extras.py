"""extract_payment_chain_extras.py
Extract the 3 small tables that close the E2E payment chain:
  T042Y  — DMEE tree / payment format per (country, payment method)
  TZBZ   — payment program variants (F110 variant config, 45 fields)
  REGUA  — F110 run admin (links run -> variant)

Output: extracted_data/payment_process_full/{table}_full.json
"""
import sys, os, time, json
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
MCP = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "..", "mcp-backend-server-python"))
if MCP not in sys.path: sys.path.insert(0, MCP)

from rfc_helpers import ConnectionGuard, rfc_read_paginated

OUT_DIR = os.path.join(SCRIPTS_DIR, "..", "extracted_data", "payment_process_full")
os.makedirs(OUT_DIR, exist_ok=True)

# T042Y — DME format per (LAND1, ZLSCH). Fields per SAP DDIC.
T042Y_FIELDS = [
    "LAND1", "ZLSCH", "DTAFD", "DTAXY", "DTADR",  # DMEE-related
    "PRIOR", "HBKID", "ZANZAH", "DTAFORM", "ZRETN",
]

# TZBZ — F110 variant config (very wide — 45 fields). Extract core set.
TZBZ_FIELDS = [
    "ZBUKR", "LAUFI", "LAUFK", "XAEND", "CRNAM", "CRDAT",
    "TRENN", "ZKBZP", "WRTOF", "WRTON", "FDEBI", "FKRED",
    "LISTZ", "SPERR", "XRENU", "ZCODE", "ZVARI",
]

# REGUA — F110 run admin (small record per run)
REGUA_FIELDS = [
    "LAUFD", "LAUFI", "XSTAR", "XENDE", "XAEND", "USNAM", "DATUM", "UZEIT",
]


def extract_full(guard, table, fields, throttle=3.0):
    out = os.path.join(OUT_DIR, f"{table}_full.json")
    if os.path.exists(out) and os.path.getsize(out) > 2:
        with open(out, encoding="utf-8") as f:
            rows = json.load(f)
        print(f"  [SKIP] {table}: {len(rows)} rows already extracted")
        return len(rows)
    t0 = time.time()
    try:
        rows = rfc_read_paginated(guard, table, fields, "", batch_size=5000, throttle=throttle)
    except Exception as e:
        print(f"  [ERROR] {table}: {type(e).__name__}: {e}")
        return 0
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    print(f"  {table}: {len(rows)} rows in {time.time()-t0:.1f}s -> {out}")
    return len(rows)


def extract_partitioned(guard, table, fields, date_field, year_from=2024, year_to=2026):
    """For REGUA: partition by LAUFD year-month."""
    from datetime import date
    from calendar import monthrange
    total = 0
    out_dir = os.path.join(OUT_DIR, table)
    os.makedirs(out_dir, exist_ok=True)
    for y in range(year_from, year_to+1):
        for m in range(1, 13):
            if y == year_to and m > 4: break
            fn = os.path.join(out_dir, f"{table}_{y:04d}_{m:02d}.json")
            if os.path.exists(fn) and os.path.getsize(fn) > 2:
                with open(fn, encoding="utf-8") as f:
                    existing = json.load(f)
                print(f"  [SKIP] {table} {y}-{m:02d}: {len(existing)} rows already extracted")
                total += len(existing)
                continue
            d1 = date(y, m, 1)
            d2 = date(y, m, monthrange(y, m)[1])
            where = f"{date_field} BETWEEN '{d1:%Y%m%d}' AND '{d2:%Y%m%d}'"
            t0 = time.time()
            try:
                rows = rfc_read_paginated(guard, table, fields, where, batch_size=5000, throttle=3.0)
            except Exception as e:
                print(f"  [ERROR] {table} {y}-{m:02d}: {type(e).__name__}: {e}")
                continue
            with open(fn, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False)
            print(f"  {table} {y}-{m:02d}: {len(rows)} rows in {time.time()-t0:.1f}s")
            total += len(rows)
    return total


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", help="just this table")
    args = ap.parse_args()

    g = ConnectionGuard("P01")
    g.connect()
    print("[OK] Connected to P01", flush=True)

    if not args.table or args.table.upper() == "T042Y":
        print("\n-- T042Y --")
        extract_full(g, "T042Y", T042Y_FIELDS)

    if not args.table or args.table.upper() == "TZBZ":
        print("\n-- TZBZ --")
        extract_full(g, "TZBZ", TZBZ_FIELDS)

    if not args.table or args.table.upper() == "REGUA":
        print("\n-- REGUA (2024-2026 monthly) --")
        extract_partitioned(g, "REGUA", REGUA_FIELDS, "LAUFD")

    if not args.table or args.table.upper() == "REGUV":
        print("\n-- REGUV (run parameters, 2024-2026 monthly) --")
        REGUV_FIELDS = ["LAUFD", "LAUFI", "XVORE", "XVORB", "XECHT", "XBELG",
                        "XDELE", "ANZER", "ANZGB", "X_DD_PRENOTIF", "X_WF_ACTIVE"]
        extract_partitioned(g, "REGUV", REGUV_FIELDS, "LAUFD")

    if not args.table or args.table.upper() == "REGUS":
        print("\n-- REGUS (vendor PM offerings, 2024-2026 monthly) --")
        REGUS_FIELDS = ["KOART", "BUKRS", "KONKO", "LAUFD", "LAUFI", "UMSKL"]
        extract_partitioned(g, "REGUS", REGUS_FIELDS, "LAUFD")

    g.close()
    print("\n[DONE]")

if __name__ == "__main__":
    main()
