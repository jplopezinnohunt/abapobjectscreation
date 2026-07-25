"""
extract_v01_actor_grounding.py
==============================
Extract V01 master tables for the unescrp actor-chain grounding probe.

WHY: unescrp's scripts/probes/check_actor_chain.py scores whether a staff member
is usable for an E2E test (eligible + a complete actor chain whose officers EXIST
as real users on the target SAP system). It was grounded on D01; it now needs V01.
The interactive user only has SSO to V01 (no Basic password) and V01's ADT endpoint
challenges Basic (realm "V01/350") — so live extraction from the unescrp side is
blocked. THIS project owns the RFC/SNC service path, so we pull the data here.

READ-ONLY (RFC_READ_TABLE / SELECT). No writes to V01.

Tables (priority order):
  1. USR02  — BNAME, UFLAG (lock), USTYP (type). FULL table. PRIMARY NEED:
              lets the probe check whether an officer BNAME exists + its lock state.
  2. PA0001 — PERNR, PERSK, GSBER, BUKRS, ANSVH, BEGDA, ENDDA. GEF-eligible pool.
  3. PA0105 — PERNR, SUBTY, USRID_LONG where SUBTY='0010' (staff work emails).

Output: v01_gold_master_data.db (per-system, mirrors p01_gold_master_data.db).
Tables written: v01_usr02, v01_pa0001, v01_pa0105.
"""
import os
import sys
import sqlite3
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRACT_DIR = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
MCP = os.path.abspath(os.path.join(EXTRACT_DIR, "..", "mcp-backend-server-python"))
if MCP not in sys.path:
    sys.path.insert(0, MCP)

from rfc_helpers import ConnectionGuard  # noqa: E402
from pyrfc import RFCError  # noqa: E402

DB_PATH = os.path.join(EXTRACT_DIR, "sqlite", "v01_gold_master_data.db")
SYSTEM = "V01"

# V01 (like P01) runs a SECURED RFC_READ_TABLE that rejects ROWSKIPS
# ("ROWSKIPS requires GET_SORTED"). So we read ROWSKIPS-FREE with ROWCOUNT=0
# and, on DATA_BUFFER_EXCEEDED, split the key space by a PERNR prefix instead
# of paginating. (Same pattern as accumulate_logs._read_window.)

# table -> (fields, base_where, sqlite_name, pernr_field | None)
SPEC = {
    "USR02": (["BNAME", "UFLAG", "USTYP"], "", "v01_usr02", None),
    "PA0001": (["PERNR", "PERSK", "GSBER", "BUKRS", "ANSVH", "BEGDA", "ENDDA"], "", "v01_pa0001", "PERNR"),
    "PA0105": (["PERNR", "SUBTY", "USRID_LONG"], "SUBTY = '0010'", "v01_pa0105", "PERNR"),
}


def _read(conn, table, fields, where):
    """One ROWSKIPS-free RFC_READ_TABLE call. Returns list of dicts.
    Raises RFCError so caller can split further on DATA_BUFFER_EXCEEDED."""
    opts = [{"TEXT": where}] if where else []
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=0, FIELDS=rfc_fields, OPTIONS=opts)
    hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        out.append({h: (parts[i].strip() if i < len(parts) else "")
                    for i, h in enumerate(hdrs)})
    return out


def read_all(conn, table, fields, base_where, pernr_field):
    """Read whole table ROWSKIPS-free; split by PERNR first-digit on buffer overflow."""
    try:
        return _read(conn, table, fields, base_where)
    except RFCError as e:
        msg = str(e)
        if "TABLE_WITHOUT_DATA" in msg:
            return []
        if "DATA_BUFFER_EXCEEDED" not in msg or not pernr_field:
            raise
    # Buffer too big for a single call -> partition by PERNR leading digit.
    rows = []
    for d in "0123456789":
        w = f"{pernr_field} LIKE '{d}%'"
        if base_where:
            w = f"{base_where} AND {w}"
        try:
            chunk = _read(conn, table, fields, w)
        except RFCError as e:
            if "TABLE_WITHOUT_DATA" in str(e):
                chunk = []
            else:
                raise
        rows += chunk
        time.sleep(0.3)
    return rows


def write_table(cur, sqlite_name, fields, rows):
    cols = ", ".join(f'"{f}" TEXT' for f in fields)
    cur.execute(f'DROP TABLE IF EXISTS "{sqlite_name}"')
    cur.execute(f'CREATE TABLE "{sqlite_name}" ({cols})')
    placeholders = ", ".join("?" for _ in fields)
    cur.executemany(
        f'INSERT INTO "{sqlite_name}" VALUES ({placeholders})',
        [tuple(r.get(f, "") for f in fields) for r in rows],
    )


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    print(f"[connect] {SYSTEM} (SNC/SSO)...", flush=True)
    t0 = time.time()
    g = ConnectionGuard(SYSTEM)
    g.connect()
    print(f"[connect] OK in {time.time()-t0:.1f}s -> {DB_PATH}", flush=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    summary = []

    for table, (fields, where, sqlite_name, pernr_field) in SPEC.items():
        print(f"[{table}] reading {fields} where={where!r} ...", flush=True)
        t0 = time.time()
        rows = read_all(g, table, fields, where, pernr_field)
        write_table(cur, sqlite_name, fields, rows)
        conn.commit()
        dt = time.time() - t0
        print(f"[{table}] {len(rows):,} rows -> {sqlite_name} ({dt:.1f}s)", flush=True)
        summary.append((table, sqlite_name, len(rows)))

    # Provenance stamp
    cur.execute('DROP TABLE IF EXISTS _extraction_meta')
    cur.execute('CREATE TABLE _extraction_meta (k TEXT, v TEXT)')
    cur.executemany('INSERT INTO _extraction_meta VALUES (?,?)', [
        ("system", "V01"),
        ("host", "hq-sap-v01.hq.int.unesco.org"),
        ("client", "350"),
        ("channel", "RFC_READ_TABLE over SNC/SSO (abapobjectscreation service path)"),
        ("purpose", "unescrp actor-chain grounding (check_actor_chain.py)"),
        ("tables", ", ".join(s[1] for s in summary)),
    ])
    conn.commit()
    conn.close()
    g.close()

    print("\n=== DONE ===")
    for table, sqlite_name, n in summary:
        print(f"  {table:8s} -> {sqlite_name:12s} {n:>8,} rows")
    print(f"  DB: {DB_PATH}")


if __name__ == "__main__":
    main()
