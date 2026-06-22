"""
PROBLEMS accumulator — ST22 short dumps + SM21 syslog (the FAILURE side of the operating model).
RSAU captures activity; this captures what BREAKS. Both come from ONE RFC-enabled, P01-safe FM:
`/USE/BL_GET_SHORTDUMPS(I_FROM_DATE/I_TO_DATE) -> EIT_SHORT_DUMP + EIT_SYSLOG` (ST-PI usage addon; works on
P01 read-only — unlike RFC_ABAP_INSTALL_AND_RUN/SNAP). Volatile (dumps/syslog rotate) -> accumulate. Chunk by
date window; dedup by row-hash. In an 80%-external system these are the INTEGRATION failures (e.g. 10054 resets).

Run:  python process_mining/accumulate_problems.py [lookback_days]
"""
import os, sys, sqlite3, hashlib, datetime
sys.path.insert(0, os.path.abspath("Zagentexecution/mcp-backend-server-python"))
from rfc_helpers import get_connection
GOLD = r"Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
DUMP_F = ["ON_DATE", "ON_TIME", "USER_NAME", "ERROR_CLASS", "OBJECT", "MESSAGE", "HOST"]
SYS_F = ["SENDER_ID", "TS", "AREA", "SUBID", "CLASID", "CENTDATA"]


def _ensure(db):
    db.execute(f'CREATE TABLE IF NOT EXISTS st22_dumps_history ({",".join(f+" TEXT" for f in DUMP_F)}, _first_seen TEXT, _hash TEXT PRIMARY KEY)')
    db.execute(f'CREATE TABLE IF NOT EXISTS sm21_syslog_history ({",".join(f+" TEXT" for f in SYS_F)}, _first_seen TEXT, _hash TEXT PRIMARY KEY)')


def _dump_row(d):
    f = {}
    for x in d.get("IT_FIELDS", []):
        f.setdefault(x["ID"], x["VALUE"])          # first occurrence of each field id
    return [d.get("ON_DATE", ""), d.get("ON_TIME", ""), d.get("USER_NAME", ""),
            f.get("FC", ""), f.get("P2", ""), (f.get("P4") or f.get("SM") or "")[:200], f.get("EI", "")]


def main():
    lookback = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    run = datetime.datetime.now().strftime("%Y-%m-%d")
    db = sqlite3.connect(GOLD, timeout=60); _ensure(db); db.commit()
    conn = get_connection("P01")
    today = datetime.date.today(); cur = today - datetime.timedelta(days=lookback)
    nd, ns = 0, 0
    while cur <= today:
        nxt = min(cur + datetime.timedelta(days=14), today)
        try:
            res = conn.call("/USE/BL_GET_SHORTDUMPS", I_FROM_DATE=cur.strftime("%Y%m%d"),
                            I_TO_DATE=nxt.strftime("%Y%m%d"), I_FROM_TIME="000000", I_TO_TIME="235959")
        except Exception as e:
            print(f"  {cur} ERR {str(e)[:70]}"); cur = nxt + datetime.timedelta(days=1); continue
        for d in res.get("EIT_SHORT_DUMP", []):
            r = _dump_row(d); h = hashlib.md5("|".join(map(str, r)).encode("utf-8", "replace")).hexdigest()
            db.execute(f'INSERT OR IGNORE INTO st22_dumps_history ({",".join(DUMP_F)},_first_seen,_hash) VALUES ({",".join("?"*(len(DUMP_F)+2))})', r + [run, h]); nd += db.total_changes and 0
        for s in res.get("EIT_SYSLOG", []):
            r = [s.get("SENDER_ID", ""), s.get("RECEVIVE_T", ""), s.get("AREA", ""), s.get("SUBID", ""), str(s.get("CLASID", "")), (s.get("CENTDATA") or "")[:300]]
            h = hashlib.md5(f'{s.get("FILE_NO","")}|{s.get("POS","")}'.encode()).hexdigest()
            db.execute(f'INSERT OR IGNORE INTO sm21_syslog_history ({",".join(SYS_F)},_first_seen,_hash) VALUES ({",".join("?"*(len(SYS_F)+2))})', r + [run, h])
        db.commit(); cur = nxt + datetime.timedelta(days=1)
    conn.close()
    nd = db.execute("SELECT COUNT(*) FROM st22_dumps_history").fetchone()[0]
    ns = db.execute("SELECT COUNT(*) FROM sm21_syslog_history").fetchone()[0]
    print(f"st22_dumps_history: {nd:,} | sm21_syslog_history: {ns:,}")
    print("top dump error classes:")
    for r in db.execute("SELECT ERROR_CLASS,COUNT(*) c FROM st22_dumps_history GROUP BY ERROR_CLASS ORDER BY c DESC LIMIT 6"):
        print(f"   {r[1]:>4}  {r[0]}")
    print("top syslog AREA:")
    for r in db.execute("SELECT AREA,COUNT(*) c FROM sm21_syslog_history GROUP BY AREA ORDER BY c DESC LIMIT 6"):
        print(f"   {r[1]:>6}  {r[0]}")
    db.close()


if __name__ == "__main__":
    main()
