"""build_audit_slots.py — the expensive scan, done ONCE and indexed (s097).

Every algorithm that asks a behavioural question of this tenant scans the same two tables:
`rsau_audit_history` (15.6M rows) and `cdhdr_history` (12M). Neither carries a usable index
— only its key autoindex — so every question pays a full table scan, and each algorithm paid
it separately. A8 alone was paying it four times in one run.

**Why the golden cannot simply be indexed.** Not style: the golden database is ~13 GB, it is
gitignored, and it has NO BACKUP (the measured durability of this project is 0.10). Creating
an index rewrites the file. A failure mid-write costs an extraction that cannot be
reproduced — the source systems no longer hold the purged audit history. The read-only
contract exists to protect an asset nothing else protects.

**So the aggregate lives outside it.** One pass collapses 15.6M audit rows into ~987K
`(user, program, day, hour)` slots carrying the signals the algorithms actually ask for, and
12M change rows into `(class, user, day, hour, tcode)` counts. That derived database IS
indexed, because losing it costs one rebuild.

    15,605,644 audit rows  ->  987,322 slots       (16x)
    12,029,963 change rows ->  aggregated counts

**The lesson this encodes, which is about HOW to apply algorithms, not about SQL.** An
expensive derivation shared by many algorithms is an ASSET, not a step inside whichever
algorithm happened to need it first. Computing it per-algorithm means paying it N times and,
worse, letting N implementations of the same aggregation drift apart. Compute once, index,
and let every algorithm read it. The cost model is part of the algorithm's design — a slow
algorithm gets skipped, and a skipped algorithm is documentation.

Rebuild when the audit log grows: the stored watermark is `MAX(SAL_DATE)`, so a re-run with
no new data exits immediately.

    python brain_v2/build_audit_slots.py            # rebuild if stale
    python brain_v2/build_audit_slots.py --force    # rebuild regardless
"""
import sqlite3
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SQLITE = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite"
GOLD = SQLITE / "p01_gold_master_data.db"
OUT = SQLITE / "derived_audit_slots.db"

FILE_LIKE = ("PARAM3 LIKE '%/%' OR PARAM3 LIKE '%.XLS%' OR PARAM3 LIKE '%.CSV%' "
             "OR PARAM3 LIKE '%.TXT%' OR PARAM3 LIKE '%.DAT%'")


def _watermark(con):
    row = con.execute("SELECT MAX(SAL_DATE), MAX(UDATE) FROM rsau_audit_history, "
                      "(SELECT MAX(UDATE) UDATE FROM cdhdr_history)").fetchone()
    return f"{row[0]}|{row[1]}"


def main():
    force = "--force" in sys.argv
    if not GOLD.exists():
        print(f"golden not found: {GOLD}", file=sys.stderr)
        return 1
    src = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
    mark = _watermark(src)

    if OUT.exists() and not force:
        try:
            chk = sqlite3.connect(f"file:{OUT}?mode=ro", uri=True)
            have = chk.execute("SELECT value FROM meta WHERE key='watermark'").fetchone()
            chk.close()
            if have and have[0] == mark:
                print(f"[audit slots] up to date ({mark}) — nothing to rebuild")
                src.close()
                return 0
        except sqlite3.Error:
            pass

    t0 = time.time()
    tmp = OUT.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    dst = sqlite3.connect(tmp)
    dst.executescript("""
        CREATE TABLE slots(user TEXT, prog TEXT, day TEXT, hh TEXT,
                           is_rfc INT, is_file INT);
        CREATE TABLE changes(objectclas TEXT, username TEXT, day TEXT, hh TEXT,
                             tcode TEXT, n INT);
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
    """)

    print("  pass 1/2 — audit log ...")
    rows = src.execute(
        "SELECT SLGUSER, SLGREPNA, SAL_DATE, substr(SAL_TIME,1,2), "
        "       MAX(CASE WHEN PARAM3 <> '' THEN 1 ELSE 0 END), "
        f"      MAX(CASE WHEN {FILE_LIKE} THEN 1 ELSE 0 END) "
        "FROM rsau_audit_history WHERE SAL_DATE <> '' GROUP BY 1,2,3,4")
    dst.executemany("INSERT INTO slots VALUES (?,?,?,?,?,?)", rows)
    n_slots = dst.execute("SELECT COUNT(*) FROM slots").fetchone()[0]

    print("  pass 2/2 — change log ...")
    rows = src.execute(
        "SELECT OBJECTCLAS, USERNAME, UDATE, substr(UTIME,1,2), TCODE, COUNT(*) "
        "FROM cdhdr_history WHERE UDATE <> '' GROUP BY 1,2,3,4,5")
    dst.executemany("INSERT INTO changes VALUES (?,?,?,?,?,?)", rows)
    n_chg = dst.execute("SELECT COUNT(*) FROM changes").fetchone()[0]
    src.close()

    # indexed HERE, where an index is safe: losing this database costs one rebuild,
    # losing the golden costs an extraction that cannot be reproduced
    print("  indexing ...")
    dst.executescript("""
        CREATE INDEX ix_slots_user_slot ON slots(user, day, hh);
        CREATE INDEX ix_slots_prog      ON slots(prog);
        CREATE INDEX ix_chg_class       ON changes(objectclas);
        CREATE INDEX ix_chg_user_slot   ON changes(username, day, hh);
    """)
    dst.execute("INSERT OR REPLACE INTO meta VALUES ('watermark', ?)", (mark,))
    dst.execute("INSERT OR REPLACE INTO meta VALUES ('built_from', ?)", (str(GOLD.name),))
    dst.commit()
    dst.close()

    OUT.unlink(missing_ok=True)
    tmp.rename(OUT)
    mb = OUT.stat().st_size / 1024 / 1024
    print(f"[audit slots] {n_slots:,} slots · {n_chg:,} change groups · "
          f"{mb:.0f} MB · {time.time() - t0:.0f}s")
    print(f"  watermark {mark} — a re-run with no new data exits immediately")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
