"""split_golden_by_system.py — ONE GOLDEN DB PER SYSTEM (KIT).

The provenance rule "a bare table name means PROD; anything else carries a d01_/v01_
prefix" is a CONVENTION. It depends on every writer remembering it, and it was not
remembered:

  * 24 `d01_*` tables live inside a file called p01_gold_master_data.db
  * `SKB1` (bare, therefore "PROD") holds 2,312 rows for ONE company code, while
    `P01_SKB1` holds 9,249 for all NINE. Anyone reading `SKB1` as production GL data
    silently gets an eighth of it.
  * `_gold_sync_log` records domain, table and strategy — but never the SYSTEM.

Making provenance STRUCTURAL fixes the class of defect: one database file per SAP
system, so the file IS the environment and no prefix has to be trusted. Same reasoning
as a gate versus a promise.

SAFETY — the Golden DB is ~13.6 GB, gitignored, and its offsite backup is UNCONFIRMED
(meta_capability: assets_backed_up = 0.00). This tool therefore:
  * COPIES into the per-system database, never moves;
  * VERIFIES row counts on both sides before reporting success;
  * NEVER drops anything from the source. Retiring the originals is a separate,
    explicit decision to be taken once a backup exists.

Usage:
    python scripts/extraction/split_golden_by_system.py --dry-run
    python scripts/extraction/split_golden_by_system.py --sid D01
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SQLITE_DIR = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite"
MANIFEST = REPO / "golden_manifest.json"
SOURCE = SQLITE_DIR / "p01_gold_master_data.db"


def tables_for(con, sid):
    """Tables carrying an explicit prefix for this SID (case-insensitive)."""
    pat = re.compile(r"^%s_" % re.escape(sid), re.I)
    return sorted(r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'") if pat.match(r[0]))


def ambiguous(con):
    """Bare tables whose PROD-prefixed twin exists with a DIFFERENT row count.

    These are the dangerous ones: the name promises production, the content is
    something else. Reported, never touched — resolving them needs a human decision
    about which extract is authoritative.
    """
    names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    bare = {n.upper(): n for n in names if not re.match(r"^(d01_|v01_|p01_|_)", n, re.I)}
    out = []
    for n in names:
        if not n.upper().startswith("P01_"):
            continue
        stem = n[4:].upper()
        if stem in bare:
            try:
                a = con.execute('SELECT COUNT(*) FROM "%s"' % n).fetchone()[0]
                b = con.execute('SELECT COUNT(*) FROM "%s"' % bare[stem]).fetchone()[0]
                if a != b:
                    out.append((bare[stem], b, n, a))
            except sqlite3.Error:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sid", default="D01", help="SID to split out (default D01)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sid = args.sid.upper()

    if not SOURCE.exists():
        print("source golden not found:", SOURCE, file=sys.stderr)
        sys.exit(2)

    src = sqlite3.connect(str(SOURCE))
    tabs = tables_for(src, sid)
    amb = ambiguous(src)

    print(f"source : {SOURCE.name} ({SOURCE.stat().st_size/1024**3:.2f} GB)")
    print(f"{sid} tables found inside it: {len(tabs)}")
    for t in tabs:
        n = src.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
        print(f"    {t:28s} {n:>9,d}")

    if amb:
        print(f"\nAMBIGUOUS PROVENANCE — {len(amb)} bare table(s) disagree with their "
              f"P01_ twin. NOT touched; these need a decision on which extract is "
              f"authoritative:")
        for bare, bn, pref, pn in amb:
            print(f"    {bare} = {bn:,}  vs  {pref} = {pn:,}")

    if args.dry_run or not tabs:
        print("\n(dry run — nothing written)" if args.dry_run else "\nnothing to split")
        src.close()
        return

    target = SQLITE_DIR / f"{sid.lower()}_gold_master_data.db"
    print(f"\ntarget : {target.name}")
    src.execute("ATTACH DATABASE ? AS tgt", (str(target),))
    copied, failed = [], []
    for t in tabs:
        # keep the prefix in the copy: a table's name is part of how existing code
        # finds it, and a rename here would break every consumer at once
        try:
            src.execute('DROP TABLE IF EXISTS tgt."%s"' % t)
            src.execute('CREATE TABLE tgt."%s" AS SELECT * FROM main."%s"' % (t, t))
            a = src.execute('SELECT COUNT(*) FROM main."%s"' % t).fetchone()[0]
            b = src.execute('SELECT COUNT(*) FROM tgt."%s"' % t).fetchone()[0]
            (copied if a == b else failed).append((t, a, b))
        except sqlite3.Error as e:
            failed.append((t, -1, str(e)[:60]))
    src.commit()
    src.execute("DETACH DATABASE tgt")
    src.close()

    print(f"copied {len(copied)} table(s), verified row-for-row")
    for t, a, b in failed:
        print(f"  MISMATCH {t}: source={a} target={b}", file=sys.stderr)
    print("\nSOURCE UNCHANGED — nothing dropped. Retiring the originals from the P01 "
          "database is a separate decision, and should wait until the Golden DB has a "
          "confirmed backup (assets_backed_up is currently 0.00).")

    if MANIFEST.exists():
        m = json.load(open(MANIFEST, encoding="utf-8"))
        known = {s.get("sap_sid") for s in m.get("systems", [])}
        if sid not in known:
            print(f"\nNOTE: {sid} is not yet declared in golden_manifest.json — "
                  f"rebuild it so consumers can resolve the new database.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
