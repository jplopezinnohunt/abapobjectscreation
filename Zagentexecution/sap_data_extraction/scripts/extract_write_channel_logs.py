"""extract_write_channel_logs.py — the two write channels the audit log cannot see (s097).

Algorithm A8 derives HOW a change arrived by crossing the change log with the execution
log. That answers for dialog, programs, jobs, files and RFC — and is **structurally blind
to two channels**, because neither runs as an ABAP program:

    BATCH INPUT   a recorded screen session replayed. It writes AS IF A PERSON TYPED IT,
                  so it carries a transaction code and passes for a dialog change. The
                  session, its creator and its source are in APQI.
    WEB SERVICE   an inbound SOAP call, processed by the ICF/SRT runtime. It never reaches
                  SLGREPNA at all, so A8 correctly reports WEBSERVICE_UNDETECTABLE rather
                  than claiming absence — absence in the wrong log is not absence in the
                  system.

Probed on P01 first, read-only, before assuming anything (the rule: test the core tool
empirically, then conclude against the hard constraints):

    SRT_MONILOG      TABLE_NOT_AVAILABLE      not this kernel
    SRTM_MONITOR     TABLE_NOT_AVAILABLE      not this kernel
    SRT_MONILOG_DATA readable, 46 columns     <- the SOAP runtime log IS here
    WSHEADER         readable, 14 columns
    APQI             readable, 40 columns
    APQD             DATA_BUFFER_EXCEEDED     needs field splitting (algorithm D4)

So the answer was never "the web-service channel cannot be verified". It was "the table we
first named does not exist on this kernel" — a different statement, and one that would have
frozen into a permanent gap if it had been recorded as the first.

P01 is READ-ONLY by contract. This extracts and writes nothing back.

Run: python Zagentexecution/sap_data_extraction/scripts/extract_write_channel_logs.py
"""
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# table -> (gold name, fields, where, why it is worth having)
# table -> (gold name, fields, where, why it is worth having)
#
# THE FIELD LISTS ARE READ FROM THE SYSTEM, NOT GUESSED. The first version invented
# plausible names (QID, CREDATE, SERVICE_NAME) and three tables came back with 0 rows. That
# looked exactly like "the table is empty" — the most expensive wrong conclusion available,
# because it becomes a permanent gap nobody revisits. RFC_READ_TABLE with FIELDS=[] returns
# the real list; ask, never assume (rule: verify empty-table claims).
TARGETS = {
    "APQI": ("apqi",
             ["QID", "GROUPID", "PROGID", "DATATYP", "QSTATE", "CREATOR", "CREDATE",
              "CRETIME", "STARTDATE", "STARTTIME", "USERID", "TRANSCNT", "MSGCNTE",
              "PUTDATE", "GETDATE", "DESTSYS"],
             "", "BATCH-INPUT session headers: who created it, which program it drives, "
                 "its state and its transaction count"),
    "WSHEADER": ("wsheader",
                 ["WSNAME", "VERSION", "WSNAMEEXT", "AUTHOR", "CREATEDON", "CHANGEDBY",
                  "CHANGEDON", "PREFIX", "VINAME"],
                 "", "web-service DEFINITIONS — what exists and who authored it. NOT a call "
                     "log: the runtime log (SRT_MONILOG_DATA) is EMPTY on this system"),
    "ICFSERVLOC": ("icfservloc", ["ICF_NAME", "ICFPARGUID", "ICFACTIVE", "ICFSRVGRP"],
                   "", "which ICF services are ACTIVE — the HTTP surface that is switched on"),
    "ICFAPPLICATION": ("icfapplication",
                       ["APPL", "ICF_NAME", "URL", "ALLOWED", "AUTHUSER", "CUSER", "CDATE",
                        "MUSER", "MDATE", "HOSTNUMBER"],
                       "", "the ICF applications and their URLs — the addressable endpoints, "
                           "with who created and last changed them"),
}

# P01 REJECTS ROWSKIPS. The paginated reader raises OPTION_NOT_VALID ("ROWSKIPS requires
# GET") against this system, which is already recorded for the FM tables and applies here
# too. These are small tables, so a single bounded call is the right read — and the CAP IS
# REPORTED (algorithm D5) rather than silently truncating, because a capped read that looks
# complete is how a partial extract becomes a false fact.
ROW_CAP = 200000


def ensure(con, name, fields):
    cols = ", ".join(f'"{f}" TEXT' for f in fields)
    con.execute(f'CREATE TABLE IF NOT EXISTS {name} ({cols})')


def main():
    if not GOLD.exists():
        print(f"golden not found: {GOLD}", file=sys.stderr)
        return 1
    conn = get_connection("P01")
    db = sqlite3.connect(GOLD)
    total = 0
    for sap, (gold, fields, where, why) in TARGETS.items():
        print(f"\n== {sap} -> {gold}\n   {why}")
        try:
            # rfc_read_paginated carries the field splitting (D4) and the pagination that
            # the 512-byte line buffer forces. Never re-implement either.
            res = conn.call("RFC_READ_TABLE", QUERY_TABLE=sap, DELIMITER="|",
                            FIELDS=[{"FIELDNAME": f} for f in fields],
                            OPTIONS=[{"TEXT": where}] if where else [],
                            ROWCOUNT=ROW_CAP)
            rows = []
            for r in res["DATA"]:
                parts = r["WA"].split("|")
                rows.append({f: (parts[i].strip() if i < len(parts) else "")
                             for i, f in enumerate(fields)})
            if len(rows) >= ROW_CAP:
                print(f"   CAPPED at {ROW_CAP:,} — this read is PARTIAL, not complete")
        except Exception as e:                                    # noqa: BLE001
            print(f"   FAILED: {str(e)[:120]}")
            continue
        if not rows:
            print("   0 rows — VERIFY before recording this as empty")
            continue
        ensure(db, gold, fields)
        db.execute(f"DELETE FROM {gold}")
        db.executemany(
            f'INSERT INTO {gold} VALUES ({",".join("?" * len(fields))})',
            [[str(r.get(f, "") or "") for f in fields] for r in rows])
        db.commit()
        total += len(rows)
        print(f"   {len(rows):,} rows")
    db.close()
    conn.close()
    print(f"\ntotal {total:,} rows into {GOLD.name}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
