"""
p01_ytfm_biennium_sync.py
-------------------------
Land the 4 YTFM biennium-classification tables (C/5) into the canonical golden DB
as a faithful raw P01 extract, via the same RFC_READ_TABLE mechanism used by the
existing ytfm_fund_cpl / ytfm_wrttp_gr tables.

Domain: FM / Budget (Funds Management, PSM-FM). These are UNESCO's custom
public-sector C/5 (Programme & Budget biennium) classifier tables. Maintained by
the Y_FM_BAPI / Y_FM_FUND_MANAGEMENT custom solution (APP_DOMAIN='FM/Budget').

Tables:
  YTFM_FUND_C5   -> ytfm_fund_c5    fund x biennium classifier (backbone)
  YTFM_C5        -> ytfm_c5         C/5 biennium master (41/42/43)
  YTFM_OUTPUT    -> ytfm_output     C/5 Output (Expected Result) -> Functional Area
  YTFM_OUTPUT_T  -> ytfm_output_t   C/5 Output text

SOURCE = SAP P01 ONLY. No Excel, ever. (Golden DB single source of truth.)

Decisions (CP-003: precision, evidence, facts):
  * DATA IS P01. Full table stored (all FIKRS / no FM-area filter); consumers filter down.
  * NUMC columns (FM_OUTPUT, YEAR_*, ORANK) kept ZERO-PADDED exactly as RFC returns
    them, matching the existing golden-DB convention (e.g. ytfm_wrttp_gr.SEQNR='00').
    FM_OUTPUT NUMC(10) -> '0000000068', joinable across the three tables as-is.
  * YTFM_OUTPUT_T.ODESC is DDIC type STRG (string). RFC_READ_TABLE cannot read it,
    and the only SAP channels that could (RFC_ABAP_INSTALL_AND_RUN / ADT on P01) are
    not authorized for this user on P01 (prod is SNC/SSO, no S_DEVELOP). D01 is NOT a
    valid substitute (D01 YTFM_OUTPUT_T diverges from P01: different row count + text).
    => ODESC is intentionally NOT stored. The SAP-readable text columns ONAME (CHAR20)
       and OTEXT (CHAR40) ARE stored. If ODESC is needed later, it requires P01
       ADT/RFC_ABAP authorization or a custom RFC-enabled read FM (none exists today).

Run:  python scripts/extraction/p01_ytfm_biennium_sync.py
"""
import os
import sqlite3
from dotenv import load_dotenv
from pyrfc import Connection

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                       "p01_gold_master_data.db")
DOTENV_PATH = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python", ".env")


def get_p01_conn():
    load_dotenv(DOTENV_PATH)
    return Connection(
        ashost=os.getenv("SAP_P01_ASHOST"),
        sysnr=os.getenv("SAP_P01_SYSNR"),
        client=os.getenv("SAP_P01_CLIENT"),
        user=os.getenv("SAP_P01_USER"),
        lang=os.getenv("SAP_P01_LANG", "EN"),
        snc_mode=os.getenv("SAP_P01_SNC_MODE"),
        snc_partnername=os.getenv("SAP_P01_SNC_PARTNERNAME"),
        snc_qop=os.getenv("SAP_P01_SNC_QOP"),
    )


def read_rfc_table(rfc, sap_table, fields, options=""):
    """Return list of dicts {FIELDNAME: stripped_value} for the requested fields.

    P01's RFC_READ_TABLE is a secured wrapper (class SAIS) that rejects ROWSKIPS
    unless GET_SORTED is supplied, so we fetch the whole table in one call
    (ROWCOUNT=0). These YTFM tables are small (<=~16.5k narrow rows), well within
    the flat WA buffer limit.
    """
    res = rfc.call("RFC_READ_TABLE",
                   QUERY_TABLE=sap_table,
                   FIELDS=[{"FIELDNAME": f} for f in fields],
                   OPTIONS=([{"TEXT": options}] if options else []),
                   ROWCOUNT=0)
    meta = res.get("FIELDS", [])
    rows = []
    for row in res.get("DATA", []):
        wa = row.get("WA", "")
        rec = {}
        for f in meta:
            off = int(f["OFFSET"]); ln = int(f["LENGTH"])
            rec[f["FIELDNAME"]] = wa[off:off + ln].strip()
        rows.append(rec)
    return rows


# (sap_table, db_table, columns-in-order, create-sql)
SPECS = [
    ("YTFM_FUND_C5", "ytfm_fund_c5",
     ["FIKRS", "FINCODE", "C5_ID", "C5_SEL", "FM_OUTPUT"],
     """CREATE TABLE ytfm_fund_c5 (
            FIKRS TEXT, FINCODE TEXT, C5_ID TEXT, C5_SEL TEXT, FM_OUTPUT TEXT,
            PRIMARY KEY (FIKRS, FINCODE, C5_ID))"""),
    ("YTFM_C5", "ytfm_c5",
     ["C5_ID", "YEAR_FROM", "YEAR_TO", "YCHK_OUTPUT"],
     """CREATE TABLE ytfm_c5 (
            C5_ID TEXT, YEAR_FROM TEXT, YEAR_TO TEXT, YCHK_OUTPUT TEXT,
            PRIMARY KEY (C5_ID))"""),
    ("YTFM_OUTPUT", "ytfm_output",
     ["FM_OUTPUT", "ZZSECT", "ORANK", "OTYPE"],
     """CREATE TABLE ytfm_output (
            FM_OUTPUT TEXT, ZZSECT TEXT, ORANK TEXT, OTYPE TEXT,
            PRIMARY KEY (FM_OUTPUT))"""),
    # ODESC (STRG) deliberately omitted — not readable from P01 via authorized channels.
    ("YTFM_OUTPUT_T", "ytfm_output_t",
     ["SPRSL", "FM_OUTPUT", "ONAME", "OTEXT"],
     """CREATE TABLE ytfm_output_t (
            SPRSL TEXT, FM_OUTPUT TEXT, ONAME TEXT, OTEXT TEXT,
            PRIMARY KEY (SPRSL, FM_OUTPUT))"""),
]


def main():
    print(f"Golden DB: {DB_PATH}")
    rfc = get_p01_conn()
    print("Connected to P01.")
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    summary = {}
    for sap_table, db_table, cols, create_sql in SPECS:
        cur.execute(f"DROP TABLE IF EXISTS {db_table}")
        cur.execute(create_sql)
        recs = read_rfc_table(rfc, sap_table, cols)
        ph = ",".join("?" * len(cols))
        cur.executemany(f"INSERT OR REPLACE INTO {db_table} VALUES ({ph})",
                        [tuple(r[c] for c in cols) for r in recs])
        db.commit()
        summary[db_table] = len(recs)

    rfc.close()

    # ---- Verification -----------------------------------------------------------
    print("\n=== Landed row counts (P01-sourced) ===")
    for t, n in summary.items():
        actual = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:16s} extracted={n:>6}  in_db={actual:>6}")

    print("\n=== ytfm_c5 (full) ===")
    for r in cur.execute("SELECT * FROM ytfm_c5"):
        print("  ", r)

    print("\n=== Join sanity: fund_c5 -> output -> output_t (English) ===")
    q = """
        SELECT f.FIKRS, f.FINCODE, f.C5_ID, f.FM_OUTPUT, o.ZZSECT, t.ONAME, t.OTEXT
        FROM ytfm_fund_c5 f
        JOIN ytfm_output  o ON o.FM_OUTPUT = f.FM_OUTPUT
        LEFT JOIN ytfm_output_t t ON t.FM_OUTPUT = f.FM_OUTPUT AND t.SPRSL = 'E'
        WHERE f.FM_OUTPUT <> '' LIMIT 6"""
    for r in cur.execute(q):
        print("  ", r)
    unassigned = cur.execute(
        "SELECT COUNT(*) FROM ytfm_fund_c5 WHERE FM_OUTPUT='0000000000'").fetchone()[0]
    print(f"\n  fund_c5 rows with unassigned output (FM_OUTPUT=0000000000): {unassigned}")

    db.close()
    print("\nDONE. (No Excel used — P01 RFC only.)")


if __name__ == "__main__":
    main()
