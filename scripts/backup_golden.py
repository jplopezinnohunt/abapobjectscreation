"""SNAPSHOT THE GOLDEN DB — the one asset git does not protect.

WHY THIS EXISTS, AND WHY IT DID NOT UNTIL NOW
    The golden holds 16.33 GB across 369 tables and it is gitignored. Every session close
    has RESTATED that git does not protect it. Restating a risk is not managing one: at the
    time this was written there were ZERO copies of it anywhere and no script to make one.

WHAT A LOCAL SNAPSHOT DOES AND DOES NOT PROTECT AGAINST — read this before trusting it
    IT DOES protect against the failures that actually happen: a loader with a bad WHERE, a
    purge that deletes the wrong side, a crashed write leaving a half-table, a DROP in the
    wrong order. Session 98 alone purged 18.8 million rows deliberately and an earlier
    session duplicated FMIOI when a lock interrupted a post-INSERT DROP.

    IT DOES NOT protect against the disk failing. A copy on the same volume dies with the
    volume. For that the destination must be a DIFFERENT device or offsite, which is what
    --dest is for — and moving SAP production data (payroll at PERNR level) to another
    system is a decision for the data owner, not for this script.

WHY `VACUUM INTO` AND NOT A FILE COPY
    Copying a live SQLite file can capture it mid-write and produce a snapshot that opens
    fine and is subtly wrong. `VACUUM INTO` takes a read lock and writes a consistent,
    compacted database — it is the supported way to snapshot without stopping the world.

USAGE
    python scripts/backup_golden.py                 # local snapshot, same volume
    python scripts/backup_golden.py --dest "D:/..." # another device or a synced folder
    python scripts/backup_golden.py --verify <file> # integrity + row counts of a snapshot
"""
import io
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
DEFAULT_DEST = REPO.parent / "_golden_backups"
MANIFEST = REPO / "Zagentexecution" / "sap_data_extraction" / "golden_manifest.json"

# Tables whose content is NOT a plain extract — they carry a rule applied at load or purge
# time. A restore that reloads these from P01 without re-applying the rule is WRONG, so the
# manifest records what makes each one special rather than only its row count.
RULED = {
    "ppdit": "purged to runs that produced an FI document (see purge_simulation_runs.py)",
    "ppdix": "purged to posted runs only",
    "ppoix": "purged to posted runs only",
    "ppdhd": "NOT purged on purpose — it is the evidence the simulations existed",
}


def counts(con):
    out = {}
    for (t,) in con.execute("select name from sqlite_master where type='table' order by name"):
        if t.startswith("sqlite_"):
            continue
        try:
            out[t] = con.execute('select count(*) from "%s"' % t).fetchone()[0]
        except sqlite3.Error:
            out[t] = None
    return out


def write_manifest(con):
    """The manifest is the cheap half of the insurance.

    Restoring 16 GB is one problem; knowing WHAT was in it and under which rules is a
    different and worse one, because that knowledge lives in a conversation. Row counts and
    the rules that shaped them cost a few hundred kilobytes and bound the worst case.
    """
    c = counts(con)
    views = [r[0] for r in con.execute("select name from sqlite_master where type='view'")]
    man = {
        "_what_this_is": "what the golden held, so a rebuild can be checked rather than hoped",
        "_source": "P01, read-only over SNC/SSO. Bare table name = P01 provenance",
        "_taken": time.strftime("%Y-%m-%d %H:%M"),
        "file_bytes": GOLD.stat().st_size,
        "tables": len(c), "rows_total": sum(v or 0 for v in c.values()),
        "views_carrying_rules": views,
        "tables_with_a_rule_applied": RULED,
        "row_counts": c,
    }
    MANIFEST.write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")
    return man


def snapshot(dest_dir):
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M")
    out = dest_dir / ("p01_gold_%s.db" % stamp)
    same_volume = str(dest_dir.resolve())[:2].lower() == str(GOLD.resolve())[:2].lower()

    con = sqlite3.connect("file:%s?mode=ro" % GOLD.as_posix(), uri=True)
    man = write_manifest(con)
    print("golden: %.2f GB · %d tablas · %d filas · vistas con regla: %s"
          % (man["file_bytes"] / 1e9, man["tables"], man["rows_total"],
             ", ".join(man["views_carrying_rules"]) or "-"))
    print("manifiesto: %s" % MANIFEST.relative_to(REPO))
    free = os.statvfs(str(dest_dir)).f_bavail * os.statvfs(str(dest_dir)).f_frsize \
        if hasattr(os, "statvfs") else None
    if free and free < man["file_bytes"] * 1.1:
        print("ABORTADO: no hay espacio suficiente en el destino")
        return 2
    t0 = time.time()
    print("copiando con VACUUM INTO (consistente, no una copia de fichero)...")
    con.execute("VACUUM INTO ?", (out.as_posix(),))
    con.close()
    print("escrito: %s · %.2f GB · %.0f min"
          % (out, out.stat().st_size / 1e9, (time.time() - t0) / 60))
    if same_volume:
        print("\n  AVISO: el destino esta en el MISMO volumen que el original.")
        print("  Esto protege de un script defectuoso, una purga mal dirigida o una")
        print("  escritura interrumpida. NO protege de un fallo de disco. Para eso el")
        print("  destino tiene que ser otro dispositivo, y mover datos de produccion de")
        print("  SAP a otro sistema lo decide el dueno del dato.")
    return 0


def verify(path):
    con = sqlite3.connect("file:%s?mode=ro" % Path(path).as_posix(), uri=True)
    ok = con.execute("pragma integrity_check").fetchone()[0]
    print("integrity_check: %s" % ok)
    have = counts(con)
    con.close()
    if not MANIFEST.exists():
        print("sin manifiesto con el que comparar")
        return 0 if ok == "ok" else 1
    want = json.loads(MANIFEST.read_text(encoding="utf-8"))["row_counts"]
    miss = [t for t in want if t not in have]
    diff = [(t, want[t], have[t]) for t in want if t in have and want[t] != have[t]]
    print("tablas ausentes: %s" % (miss or "ninguna"))
    print("conteos distintos: %s" % (diff[:8] or "ninguno"))
    return 0 if ok == "ok" and not miss and not diff else 1


def main(argv):
    if "--verify" in argv:
        return verify(argv[argv.index("--verify") + 1])
    dest = argv[argv.index("--dest") + 1] if "--dest" in argv else DEFAULT_DEST
    return snapshot(dest)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
