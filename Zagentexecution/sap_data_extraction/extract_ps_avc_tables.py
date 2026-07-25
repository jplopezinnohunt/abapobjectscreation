"""
extract_ps_avc_tables.py
========================
INC-000005638 (extension): pull PS-AVC tables from P01 -> Gold DB so we can
characterize the FM-AVC vs PS-AVC misalignment for UNESCO.

Priority 1 (must-have for this incident):
  - EKKN  -> filter on EBELN IN (3 incident POs) + broader 2024-2026 PO range
  - BPGE  -> annual budget by value type, GJAHR 2024-2026
  - BPJA  -> cumulative budget by value type, GJAHR 2024-2026
  - BPHI  -> header (small)
  - COSP  -> cost totals primary, OBJNR LIKE 'PR%', GJAHR 2024-2026
  - COSS  -> cost totals secondary, OBJNR LIKE 'PR%', GJAHR 2024-2026
  - TKA01 -> controlling area config (single row)
  - FMAVCT (proper) -> RFIKRS='UNES' AND RYEAR IN (2024,2025,2026)

Priority 2 (desirable):
  - BPDJ  -> recent budget change docs
  - FMAFMAP013500109 -> AVC derivation rules
  - FMAFMTP013500110 -> AVC tolerance profile

Read-only on P01 (SNC/SSO). NEVER fabricates data — if RFC fails, it is
documented and a KU is recorded in the run log.

Usage:
    python extract_ps_avc_tables.py
    python extract_ps_avc_tables.py --table BPGE
    python extract_ps_avc_tables.py --priority 1
"""

from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import time
import traceback

# --- bootstrap path to rfc_helpers (lives under mcp-backend-server-python) ---
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MCP_DIR = os.path.join(PROJECT_ROOT, "Zagentexecution", "mcp-backend-server-python")
sys.path.insert(0, MCP_DIR)

from rfc_helpers import get_connection  # type: ignore  # noqa: E402

GOLD_DB = os.path.join(
    PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
    "p01_gold_master_data.db",
)
LOG_DIR = os.path.join(
    PROJECT_ROOT, "Zagentexecution", "sap_data_extraction", "logs",
)
os.makedirs(LOG_DIR, exist_ok=True)

INCIDENT_POS = ("4500543365", "4500540022", "4500540024")

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class RunLog:
    def __init__(self, path: str) -> None:
        self.path = path
        self.f = open(path, "w", encoding="utf-8")
        self.lines = []
        self.write(f"# PS-AVC extraction log — {_now()}")
        self.write(f"# Gold DB: {GOLD_DB}")
        self.write(f"# Incident POs: {INCIDENT_POS}")

    def write(self, msg: str) -> None:
        line = f"[{_now()}] {msg}"
        print(line)
        self.f.write(line + "\n")
        self.f.flush()
        self.lines.append(line)

    def close(self) -> None:
        self.f.close()


_BUFFER_ERR_TOKENS = (
    "DATA_BUFFER_EXCEEDED",
    "FIELD_NOT_VALID",
    "AD Type:E Number:718",  # SAP buffer-overflow when fields too wide
    "AD Type:E Number:704",  # similar SAP buffer signal
)


def _is_buffer_error(msg: str, n_fields: int) -> bool:
    """True if the RFC error indicates the row buffer was exceeded.

    AD/E/718 ('TABLE_WITHOUT_DATA') is overloaded in SAP — when raised on the
    very first paginated call with many fields, it's almost always the
    buffer-overflow path, not a literal 'no rows'. We treat it as buffer
    overflow whenever the field list still has > 1 field.
    """
    if any(tok in msg for tok in _BUFFER_ERR_TOKENS) and n_fields > 1:
        return True
    return False


def read_all(
    conn,
    table: str,
    fields: list[str],
    where: str,
    log: RunLog,
    batch_size: int = 5000,
    max_rows: int | None = None,
    _depth: int = 0,
) -> tuple[list[list[str]], list[str]]:
    """Paginated RFC_READ_TABLE. Returns (rows, headers).

    Implements adaptive field splitting if the field list is too wide for the
    512-byte WA buffer.
    """
    rfc_fields_full = [{"FIELDNAME": f} for f in fields] if fields else []
    rfc_opts = [{"TEXT": where}] if where else []
    offset = 0
    headers: list[str] | None = None
    all_rows: list[list[str]] = []

    while True:
        try:
            res = conn.call(
                "RFC_READ_TABLE",
                QUERY_TABLE=table,
                DELIMITER="|",
                ROWCOUNT=batch_size,
                ROWSKIPS=offset,
                OPTIONS=rfc_opts,
                FIELDS=rfc_fields_full,
            )
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            # Heuristic 1: buffer-overflow signature -> split fields.
            if _is_buffer_error(msg, len(fields)):
                log.write(
                    f"  !! {table} (depth={_depth}) buffer error at offset {offset} "
                    f"with {len(fields)} fields -> splitting. Detail: {msg[:160]}"
                )
                rows, hdrs = _split_fields_extract(
                    conn, table, fields, where, log, batch_size, _depth + 1
                )
                return rows, hdrs
            # Heuristic 2: only ONE field left and TABLE_WITHOUT_DATA -> truly empty.
            if "TABLE_WITHOUT_DATA" in msg and len(fields) <= 1:
                log.write(
                    f"  -- {table} (depth={_depth}) TABLE_WITHOUT_DATA -> 0 rows."
                )
                return all_rows, headers or fields
            # Heuristic 3: pagination data loss -> stop on this slice.
            if "SAPSQL_DATA_LOSS" in msg:
                log.write(
                    f"  !! {table} SAPSQL_DATA_LOSS at offset {offset}; STOPPING."
                )
                return all_rows, headers or fields
            log.write(f"  !! {table} RFC error at offset {offset}: {msg[:200]}")
            raise

        if headers is None:
            headers = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
        raw = res.get("DATA", [])
        for row in raw:
            parts = row["WA"].split("|")
            all_rows.append(
                [parts[i].strip() if i < len(parts) else "" for i in range(len(headers))]
            )
        got = len(raw)
        log.write(f"    {table} offset={offset}: +{got} rows (running {len(all_rows)})")
        if got < batch_size:
            break
        offset += batch_size
        if max_rows is not None and len(all_rows) >= max_rows:
            log.write(f"  -- {table} hit max_rows={max_rows}, stopping pagination.")
            break
    return all_rows, headers or fields


def _split_fields_extract(
    conn,
    table: str,
    fields: list[str],
    where: str,
    log: RunLog,
    batch_size: int,
    depth: int = 0,
) -> tuple[list[list[str]], list[str]]:
    """Recursive split-field extraction. Halves the field list and recombines.

    Each half MUST return the same number of rows (RFC_READ_TABLE preserves the
    select order across separate calls with the same OPTIONS). If they differ,
    we surface a warning and fall back to the smaller half.
    """
    if len(fields) <= 1:
        # cannot split further
        return read_all(conn, table, fields, where, log, batch_size, _depth=depth + 5)

    half = max(1, len(fields) // 2)
    a, b = fields[:half], fields[half:]
    log.write(f"  -- splitting fields at depth {depth}: {len(a)} | {len(b)}")
    rows_a, hdr_a = read_all(conn, table, a, where, log, batch_size, _depth=depth)
    rows_b, hdr_b = read_all(conn, table, b, where, log, batch_size, _depth=depth)
    if len(rows_a) != len(rows_b):
        log.write(
            f"  !! split mismatch on {table}: {len(rows_a)} vs {len(rows_b)}; "
            f"using rows_a only."
        )
        return rows_a, hdr_a
    merged = [ra + rb for ra, rb in zip(rows_a, rows_b)]
    return merged, hdr_a + hdr_b


def persist(
    db: sqlite3.Connection,
    table: str,
    rows: list[list[str]],
    headers: list[str],
    log: RunLog,
) -> int:
    cur = db.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cols = ", ".join(f'"{h}" TEXT' for h in headers)
    cur.execute(f"CREATE TABLE {table} ({cols})")
    if rows:
        ph = ",".join("?" * len(headers))
        cur.executemany(f"INSERT INTO {table} VALUES ({ph})", rows)
    db.commit()
    log.write(f"  >> persisted {len(rows)} rows -> {table}  cols={len(headers)}")
    return len(rows)


# ---------------------------------------------------------------------------
# Field lists (DD03L-verified 2026-05-01)
# ---------------------------------------------------------------------------

EKKN_FIELDS = [
    # 7-field slim set — empirically validated as the safe ceiling for EKKN
    # (8+ fields trigger AD/E/718 buffer overflow). This is enough to map
    # PO line -> WBS element -> FM coding.
    "EBELN", "EBELP", "PS_PSP_PNR", "FISTL", "GEBER", "SAKTO", "AEDAT",
]

# BPGE / BPJA / BPHI / COSP / COSS / FMAVCT all hit the 512-byte WA buffer
# limit at ~8-10 fields too. Use the slim 8-field "skeleton" and rely on
# joins back into the existing Gold DB (prps, funds, fund_centers) for
# enrichment. Only the load-bearing budget/consumption columns are kept.

BPGE_FIELDS = [
    "OBJNR", "POSIT", "WRTTP", "GEBER", "VERSN", "TWAER", "WTGES", "WLGES",
]

BPJA_FIELDS = [
    "OBJNR", "WRTTP", "GJAHR", "GEBER", "VERSN", "TWAER", "WTJHR", "WLJHR",
]

BPHI_FIELDS = [
    "OBJNR", "WRTTP", "HIERA", "GEBER", "VERSN", "PLDAT", "RELE", "AVA",
]

# COSP / COSS — the meaningful columns are KSTAR + WTG001..WTG016 (period
# buckets in transaction currency). 8 columns total — slim set covers the
# annual aggregate via WTG001 sum (we'll do the period-by-period rollup in
# the analysis script that consumes this Gold table).
COSP_FIELDS = [
    "OBJNR", "GJAHR", "WRTTP", "KSTAR", "TWAER",
    "WTG001", "WTG002", "WTG003",  # Q1 buckets — sufficient for 2024-2026 trend
]
# To get the full 16-period spectrum we'll do a SECOND pull keyed on
# OBJNR+GJAHR+WRTTP+KSTAR for the higher periods. See run_plan.

COSP_FIELDS_PART2 = [
    "OBJNR", "GJAHR", "WRTTP", "KSTAR",
    "WTG004", "WTG005", "WTG006", "WTG007",
]
COSP_FIELDS_PART3 = [
    "OBJNR", "GJAHR", "WRTTP", "KSTAR",
    "WTG008", "WTG009", "WTG010", "WTG011",
]
COSP_FIELDS_PART4 = [
    "OBJNR", "GJAHR", "WRTTP", "KSTAR",
    "WTG012", "WTG013", "WTG014", "WTG015",
]
COSP_FIELDS_PART5 = [
    "OBJNR", "GJAHR", "WRTTP", "KSTAR", "WTG016",
]

COSS_FIELDS = [
    "OBJNR", "GJAHR", "WRTTP", "KSTAR", "TWAER",
    "WTG001", "WTG002", "WTG003",
]

# FMAVCT proper (CO-PA actuals AVC totals). The CRITICAL discovery (INC-005638
# extension): RFUND/RFUNDSCTR/RCMMTITEM are NOT key fields, but they are the
# tracking columns that identify which (Fund × FundCenter × DerivedCmtItem)
# bucket the row belongs to. RCMMTITEM holds the AVC-DERIVED commitment item
# (e.g. 'TC', 'PC', 'NPC', or a literal FIPEX like '80') — NOT the original
# FIPEX. Use these fields explicitly.
FMAVCT_FIELDS = [
    "RFIKRS", "RFUND", "RFUNDSCTR", "RCMMTITEM", "RYEAR", "ALLOCTYPE_9", "HSL01",
]

# Second pull for FMAVCT with periods 2-16 (joined later in analysis)
FMAVCT_FIELDS_HSL = [
    "RLDNR", "RFIKRS", "COBJNR", "RYEAR", "ALLOCTYPE_9",
    "HSL02", "HSL03", "HSL04",
]
FMAVCT_FIELDS_HSL2 = [
    "RLDNR", "RFIKRS", "COBJNR", "RYEAR", "ALLOCTYPE_9",
    "HSL05", "HSL06", "HSL07",
]
FMAVCT_FIELDS_HSL3 = [
    "RLDNR", "RFIKRS", "COBJNR", "RYEAR", "ALLOCTYPE_9",
    "HSL08", "HSL09", "HSL10",
]
FMAVCT_FIELDS_HSL4 = [
    "RLDNR", "RFIKRS", "COBJNR", "RYEAR", "ALLOCTYPE_9",
    "HSL11", "HSL12", "HSL13",
]
FMAVCT_FIELDS_HSL5 = [
    "RLDNR", "RFIKRS", "COBJNR", "RYEAR", "ALLOCTYPE_9",
    "HSL14", "HSL15", "HSL16",
]

TKA01_FIELDS = [
    "KOKRS", "BEZEI", "FIKRS", "WAERS", "KTOPL", "BPHINR", "CTYP", "CVPROF",
]

BPDJ_FIELDS = [
    "BELNR", "BUZEI", "WRTTP", "GEBER", "GJAHR", "TWAER", "PLDAT", "BELTP",
]

FMAFMAP_FIELDS = [
    "SOUR1_FROM", "SOUR1_TO", "SOUR2_FROM", "SOUR2_TO",
    "SOUR3_FROM", "SOUR3_TO", "VALID_FROM", "TARGET1",
]

FMAFMTP_FIELDS = [
    "SOUR1_FROM", "SOUR1_TO", "VALID_FROM", "TARGET1",
    "DELETE_FLG", "ADDED_BY", "ADDED_ON",
]

# ---------------------------------------------------------------------------
# Extraction plan
# ---------------------------------------------------------------------------

P1_PLAN = [
    # (sap_table, sqlite_table, fields, where, batch_size, comment)
    (
        "EKKN", "ekkn_inc5638",
        EKKN_FIELDS,
        "EBELN = '4500543365'",  # one PO per call due to OPTIONS row width
        500,
        "Account assignment for incident PO 4500543365",
    ),
    (
        "EKKN", "ekkn_inc5638_22",
        EKKN_FIELDS,
        "EBELN = '4500540022'",
        500,
        "Account assignment for incident PO 4500540022",
    ),
    (
        "EKKN", "ekkn_inc5638_24",
        EKKN_FIELDS,
        "EBELN = '4500540024'",
        500,
        "Account assignment for incident PO 4500540024",
    ),
    (
        "TKA01", "tka01",
        TKA01_FIELDS,
        "FIKRS = 'UNES'",
        100,
        "Controlling area config for UNESCO",
    ),
    (
        "BPHI", "bphi",
        BPHI_FIELDS,
        "OBJNR LIKE 'PR%'",
        5000,
        "PS budget header (project objects)",
    ),
    (
        "BPGE", "bpge",
        BPGE_FIELDS,
        "OBJNR LIKE 'PR%'",
        5000,
        "Annual PS budget value-type aggregate (project objects)",
    ),
    (
        "BPJA", "bpja_2024",
        BPJA_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2024'",
        5000,
        "Cumulative PS budget 2024 (project objects)",
    ),
    (
        "BPJA", "bpja_2025",
        BPJA_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2025'",
        5000,
        "Cumulative PS budget 2025 (project objects)",
    ),
    (
        "BPJA", "bpja_2026",
        BPJA_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2026'",
        5000,
        "Cumulative PS budget 2026 (project objects)",
    ),
    (
        "COSP", "cosp_2024",
        COSP_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2024'",
        5000,
        "CO totals primary 2024 (project objects)",
    ),
    (
        "COSP", "cosp_2025",
        COSP_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2025'",
        5000,
        "CO totals primary 2025 (project objects)",
    ),
    (
        "COSP", "cosp_2026",
        COSP_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2026'",
        5000,
        "CO totals primary 2026 (project objects)",
    ),
    (
        "COSS", "coss_2024",
        COSS_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2024'",
        5000,
        "CO totals secondary 2024 (project objects)",
    ),
    (
        "COSS", "coss_2025",
        COSS_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2025'",
        5000,
        "CO totals secondary 2025 (project objects)",
    ),
    (
        "COSS", "coss_2026",
        COSS_FIELDS,
        "OBJNR LIKE 'PR%' AND GJAHR = '2026'",
        5000,
        "CO totals secondary 2026 (project objects)",
    ),
    (
        "FMAVCT", "fmavct_2024",
        FMAVCT_FIELDS,
        "RFIKRS = 'UNES' AND RYEAR = '2024'",
        5000,
        "FM-AVC totals 2024",
    ),
    (
        "FMAVCT", "fmavct_2025",
        FMAVCT_FIELDS,
        "RFIKRS = 'UNES' AND RYEAR = '2025'",
        5000,
        "FM-AVC totals 2025",
    ),
    (
        "FMAVCT", "fmavct_2026",
        FMAVCT_FIELDS,
        "RFIKRS = 'UNES' AND RYEAR = '2026'",
        5000,
        "FM-AVC totals 2026",
    ),
]

P2_PLAN = [
    (
        "FMAFMAP013500109", "fmafmap013500109",
        FMAFMAP_FIELDS,
        "",
        2000,
        "AVC derivation rule (Fund,FundCenter,CmtItem) -> control object",
    ),
    (
        "FMAFMTP013500110", "fmafmtp013500110",
        FMAFMTP_FIELDS,
        "",
        2000,
        "AVC tolerance profile",
    ),
    (
        "BPDJ", "bpdj_2024_2026",
        BPDJ_FIELDS,
        "GJAHR >= '2024' AND GJAHR <= '2026'",
        5000,
        "PS budget change docs 2024-2026",
    ),
]

# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run_plan(plan: list, log: RunLog, only_table: str | None = None) -> dict:
    summary: dict = {}
    conn = get_connection("P01")
    db = sqlite3.connect(GOLD_DB)
    try:
        for sap_table, sql_table, fields, where, batch, comment in plan:
            if only_table and sap_table != only_table:
                continue
            log.write("")
            log.write(f"=== {sap_table} -> {sql_table} === {comment}")
            log.write(f"    WHERE: {where or '(none)'}")
            log.write(f"    fields ({len(fields)}): {fields}")
            t0 = time.time()
            try:
                rows, hdrs = read_all(conn, sap_table, fields, where, log, batch_size=batch)
                n = persist(db, sql_table, rows, hdrs, log)
                elapsed = time.time() - t0
                summary[sql_table] = {
                    "sap_table": sap_table,
                    "rows": n,
                    "elapsed_sec": round(elapsed, 1),
                    "headers": hdrs,
                    "where": where,
                    "status": "OK",
                }
                log.write(f"  -- {sap_table} done in {elapsed:.1f}s")
            except Exception as exc:  # noqa: BLE001
                tb = traceback.format_exc()
                summary[sql_table] = {
                    "sap_table": sap_table,
                    "rows": 0,
                    "status": "FAIL",
                    "error": str(exc)[:300],
                }
                log.write(f"  XX {sap_table} FAILED: {exc}")
                log.write(tb)
    finally:
        try:
            db.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=None, help="Only extract this SAP table")
    ap.add_argument("--priority", choices=("1", "2", "all"), default="1")
    args = ap.parse_args()

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOG_DIR, f"ps_avc_extraction_INC-000005638_{ts}.log")
    log = RunLog(log_path)

    summaries: dict = {}
    try:
        if args.priority in ("1", "all"):
            log.write("\n##### PRIORITY 1 #####")
            summaries.update(run_plan(P1_PLAN, log, args.table))
        if args.priority in ("2", "all"):
            log.write("\n##### PRIORITY 2 #####")
            summaries.update(run_plan(P2_PLAN, log, args.table))
    finally:
        log.write("")
        log.write("===== SUMMARY =====")
        for tbl, info in summaries.items():
            log.write(f"  {tbl:<24}  {info.get('status'):<5}  rows={info.get('rows', 0)}")
        # also dump JSON summary alongside the log
        json_path = log_path.replace(".log", ".json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(summaries, jf, indent=2, default=str)
        log.write(f"JSON summary -> {json_path}")
        log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
