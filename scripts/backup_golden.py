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

THE SECOND ASSET: ~/.claude
    The project memory has always named TWO things git does not protect, and only one of
    them was ever scripted. ~/.claude holds the accumulated memory of every session across
    every project — 474 files, 1.5 MB — plus the hand-written CLAUDE.md, the skills and the
    permission settings. It is the smaller asset and the more irreplaceable one: the golden
    can be re-extracted from P01 over hours, and nothing anywhere can reconstruct a note
    about why a decision was made.

    Both go to the same --dest, because two assets that are always named together should
    not need two commands and two destinations to remember.

WHAT IS DELIBERATELY LEFT OUT OF THE ~/.claude COPY
    THE TRANSCRIPTS. 1,836 MB of .jsonl against 1.5 MB of memory — 99.9% of the size and
    the part that is NOT the knowledge. Backing them up would make the copy 600x larger and
    slow enough that it stops being run, which is how a backup quietly dies.

    THE CREDENTIALS. .credentials.json is an OAuth token and mcp-needs-auth-cache.json can
    carry auth state. A token is RE-OBTAINABLE by logging in again; memory is not. So the
    copy excludes them and VERIFIES the exclusion afterwards rather than trusting the
    filter — an external disk can be lost, and a lost disk holding a live token is a
    different kind of incident than a lost disk holding notes.

USAGE
    python scripts/backup_golden.py                 # local snapshot, same volume
    python scripts/backup_golden.py --dest "D:/..." # another device — both assets
    python scripts/backup_golden.py --claude-only --dest "D:/..."   # just ~/.claude (3 MB)
    python scripts/backup_golden.py --verify <file> # integrity + row counts
    python scripts/backup_golden.py --status --dest "D:/..."  # que hay y que esta desfasado

DOS COPIAS, Y CUAL ES CUAL
    Solo se guardan ACTUAL y ANTERIOR: una tercera no protege de nada que la segunda
    no cubra. backup_state.json en el destino declara el ROL de cada fichero y la
    huella del origen del que salio, asi que --status responde de un vistazo que esta
    al dia y que no. Un directorio de ficheros con fecha no puede decir si el mas
    nuevo sigue vigente.
"""
import fnmatch
import hashlib
import io
import json
import os
import sqlite3
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
DEFAULT_DEST = REPO.parent / "_golden_backups"
MANIFEST = REPO / "Zagentexecution" / "sap_data_extraction" / "golden_manifest.json"
# Where the last backup actually went. The destination is an argument, so the
# integrity gate cannot guess it — and a gate that reports "no copy exists"
# because the copy MOVED is a gate that teaches you to ignore it.
POINTER = REPO / "Zagentexecution" / "sap_data_extraction" / "backup_location.json"

CLAUDE_HOME = Path(os.path.expanduser("~")) / ".claude"
# What to take. Everything else in ~/.claude is cache, telemetry, file-history or
# transcripts — regenerable, and 99.9% of the bytes.
# NOTE the trailing /*: pathlib's `skills/**` matches DIRECTORIES, not files recursively.
# Written without it, the first run of this script captured 4 files and ZERO memory — and
# wrote the zip anyway. Hence the assertion in snapshot_claude: a backup of the memory that
# contains no memory must fail loudly, not succeed quietly.
CLAUDE_INCLUDE = [
    "CLAUDE.md", "settings.json", "AGI-EXCELLENCE-PROTOCOL.md", "SKILL-COORDINATOR.md",
    "skills/**/*", "plans/**/*", "memory-backups/**/*", "projects/*/memory/**/*",
]
# What must never travel, verified after the fact rather than trusted to the filter.
CLAUDE_SECRETS = [".credentials.json", "mcp-needs-auth-cache.json", "*.key", "*token*"]

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


STATE = "backup_state.json"
KEEP = 2      # current + previous. A third copy protects against nothing the second does not.


def fingerprint(path):
    """Cheap 'did this change' signature. Hashing 16 GB costs what copying it costs, so this
    reads size, mtime and the first and last megabyte — enough to catch any write to a SQLite
    file, whose header page changes on every commit."""
    p = Path(path)
    st = p.stat()
    h = hashlib.sha1()
    with io.open(p, "rb") as f:
        h.update(f.read(1 << 20))
        if st.st_size > (2 << 20):
            f.seek(-(1 << 20), os.SEEK_END)
            h.update(f.read(1 << 20))
    return {"bytes": st.st_size, "mtime": int(st.st_mtime), "edges": h.hexdigest()[:16]}


def load_state(dest):
    p = Path(dest) / STATE
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"_what_this_is": "que hay copiado, de que estado del origen, y si sigue al dia",
                "assets": {}}


def save_state(dest, state):
    POINTER.write_text(json.dumps(
        {"_what_this_is": "donde escribio el ultimo backup, para que el "
                          "gate lo encuentre aunque el destino cambie",
         "dest": str(dest), "when": time.strftime("%Y-%m-%d %H:%M")},
        indent=1, ensure_ascii=False), encoding="utf-8")
    (Path(dest) / STATE).write_text(json.dumps(state, indent=1, ensure_ascii=False),
                                    encoding="utf-8")


def rotate(dest, asset, new_file, fp, state):
    """Promote the new copy to CURRENT, demote the old one to PREVIOUS, delete the rest."""
    a = state["assets"].setdefault(asset, {"copies": []})
    a["copies"].insert(0, {"file": Path(new_file).name, "when": time.strftime("%Y-%m-%d %H:%M"),
                           "source": fp})
    for old in a["copies"][KEEP:]:
        try:
            (Path(dest) / old["file"]).unlink()
            print("     retirada la copia vieja: %s" % old["file"])
        except OSError:
            pass
    a["copies"] = a["copies"][:KEEP]
    for i, c in enumerate(a["copies"]):
        c["role"] = "ACTUAL" if i == 0 else "ANTERIOR"
    save_state(dest, state)


def status(dest):
    """What is protected, how old, and what the source has done since. This is the whole
    point of keeping a state file: a directory of timestamped files cannot tell you whether
    the newest one is still current."""
    state = load_state(dest)
    print("ESTADO DE LAS COPIAS EN %s" % dest)
    print("=" * 74)
    if not state["assets"]:
        print("  sin copias todavia")
        return 0
    stale = 0
    for asset, a in state["assets"].items():
        src = {"golden": GOLD}.get(asset)
        now = None
        if src and Path(src).exists():
            now = fingerprint(src)
        print("\n  %s" % asset.upper())
        for c in a["copies"]:
            print("    %-9s %-34s %s" % (c.get("role", "?"), c["file"], c["when"]))
        cur = a["copies"][0]["source"] if a["copies"] else None
        if now and cur:
            same = now["edges"] == cur.get("edges") and now["bytes"] == cur.get("bytes")
            print("    origen: %s" % ("SIN CAMBIOS desde la copia ACTUAL"
                                      if same else "HA CAMBIADO — la copia esta desfasada"))
            if not same:
                stale += 1
        elif not src:
            print("    origen: no comprobable desde aqui (copia externa)")
    print("\n" + "=" * 74)
    print("%d activo(s) pendientes de actualizar" % stale if stale
          else "todo al dia")
    return 0


def is_secret(rel):
    name = Path(rel).name
    return any(fnmatch.fnmatch(name, pat) for pat in CLAUDE_SECRETS)


def claude_files():
    """The durable subset of ~/.claude, resolved to real paths."""
    out = []
    for pat in CLAUDE_INCLUDE:
        for p in CLAUDE_HOME.glob(pat):
            if p.is_file():
                out.append(p)
    return sorted(set(out))


def snapshot_claude(dest_dir):
    """Zip the memory and the hand-written config. Small enough to run every time."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / ("claude_home_%s.zip" % time.strftime("%Y%m%d_%H%M"))
    files = claude_files()
    if not files:
        print("  ~/.claude: nada que copiar (ruta inesperada?)")
        return None
    skipped = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            rel = p.relative_to(CLAUDE_HOME).as_posix()
            if is_secret(rel):
                skipped.append(rel)
                continue
            z.write(p, rel)

    # VERIFY the exclusion instead of trusting the filter. A backup that quietly carries a
    # token is worse than no backup, because it is carried off-site and forgotten about.
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        leaked = [n for n in names if is_secret(n)]
    if leaked:
        out.unlink()
        raise SystemExit("ABORTADO: el zip contenia secretos (%s). Borrado." % leaked[:3])

    # A backup of the memory that contains no memory is not a backup. Refuse to leave it on
    # disk looking like one — the first version of this function wrote exactly that.
    mem = [n for n in names if "/memory/" in n]
    if len(mem) < 50:
        out.unlink()
        raise SystemExit("ABORTADO: solo %d ficheros de memoria en el zip (se esperan >=50). "
                         "Los patrones de CLAUDE_INCLUDE no estan capturando nada. Borrado."
                         % len(mem))
    print("  ~/.claude -> %s" % out.name)
    print("     %d ficheros, %.1f MB · %d de memoria · %d secretos excluidos y VERIFICADOS"
          % (len(names), out.stat().st_size / 1e6, len(mem), len(skipped)))
    # 1.6 MB is cheap enough to rewrite every run, so the fingerprint here is of the
    # RESULT rather than the source — it still drives rotation and the status view.
    rotate(dest_dir, "claude_home", out, fingerprint(out), load_state(dest_dir))
    return out


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
    # SKIP IF UNCHANGED. The golden only moves when something extracts or purges; on every
    # other day copying 16 GB for 15 minutes buys nothing. This is where the incremental
    # saving actually lives — a monolithic SQLite file cannot be copied in parts, so the
    # useful question is not "which blocks changed" but "did anything change at all".
    state = load_state(dest_dir)
    fp = fingerprint(GOLD)
    prev = (state["assets"].get("golden", {}).get("copies") or [{}])[0].get("source")
    if (prev and "--force" not in sys.argv
            and prev.get("edges") == fp["edges"]
            and prev.get("bytes") == fp["bytes"]):
        con.close()
        print("SIN CAMBIOS desde la copia ACTUAL — no se copia nada.")
        print("  (el golden solo cambia al extraer o purgar; forzar con --force)")
        return 0

    t0 = time.time()
    print("copiando con VACUUM INTO (consistente, no una copia de fichero)...")
    con.execute("VACUUM INTO ?", (out.as_posix(),))
    con.close()
    print("escrito: %s · %.2f GB · %.0f min"
          % (out, out.stat().st_size / 1e9, (time.time() - t0) / 60))
    rotate(dest_dir, "golden", out, fp, state)
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


def restore_claude(zip_path, to_dir):
    """Restore ~/.claude to a STAGING directory — never over the live one.

    A restore that writes straight into ~/.claude is a restore nobody dares rehearse, and a
    backup nobody rehearses is a hypothesis. Extracting beside it costs one `move` and makes
    the drill safe to run on a normal Tuesday.
    """
    zip_path, to_dir = Path(zip_path), Path(to_dir)
    if to_dir.exists() and any(to_dir.iterdir()):
        raise SystemExit("ABORTADO: %s ya existe y no esta vacio. Elige otro destino." % to_dir)
    to_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        bad = [n for n in z.namelist()
               if n.startswith("/") or ".." in Path(n).parts]   # zip-slip
        if bad:
            raise SystemExit("ABORTADO: rutas peligrosas en el zip: %s" % bad[:3])
        z.extractall(to_dir)
        names = z.namelist()

    got = sum(1 for _ in to_dir.rglob("*") if _.is_file())
    mem = list(to_dir.glob("projects/*/memory/*"))
    print("RESTAURADO en %s" % to_dir)
    print("  %d ficheros del zip, %d en disco, %d de memoria" % (len(names), got, len(mem)))
    ok = got == len(names) and len(mem) >= 50
    print("  verificacion: %s" % ("OK" if ok else "FALLA — cuentas no cuadran"))
    if ok:
        print("\n  Siguiente paso MANUAL (a proposito):")
        print("    1. renombra ~/.claude a ~/.claude.old")
        print("    2. mueve %s a ~/.claude" % to_dir)
        print("    3. vuelve a iniciar sesion — .credentials.json NO esta en la copia")
    return 0 if ok else 1


# Flags the script understands. Anything else is a question it cannot answer, and the
# answer to a question it cannot answer is NOT "run the most expensive action I have".
KNOWN_FLAGS = {
    "--help", "-h", "--status", "--restore", "--to", "--verify",
    "--dest", "--claude-only", "--force",
}


def usage():
    print(__doc__.strip() if __doc__ else "backup_golden.py")
    print()
    print("Flags: " + "  ".join(sorted(KNOWN_FLAGS)))
    print()
    print("Sin --dest copia a %s, que puede estar en el MISMO volumen que el" % DEFAULT_DEST)
    print("origen. Eso protege de un script roto o una escritura interrumpida; NO")
    print("protege de un fallo de disco, que es de lo que va este backup.")
    return 0


def main(argv):
    if "--help" in argv or "-h" in argv:
        return usage()

    unknown = [a for a in argv if a.startswith("-") and a not in KNOWN_FLAGS]
    if unknown:
        print("Flag no reconocida: %s" % ", ".join(unknown))
        print("Paro aqui a proposito. Antes, cualquier flag desconocida caia al backup")
        print("por defecto y escribia 16 GB sin que nadie lo pidiera.")
        print()
        usage()
        return 2

    if "--status" in argv:
        return status(argv[argv.index("--dest") + 1] if "--dest" in argv
                      else DEFAULT_DEST)
    if "--restore" in argv:
        z = argv[argv.index("--restore") + 1]
        to = argv[argv.index("--to") + 1] if "--to" in argv else \
            str(Path(z).parent / "_restore_test")
        return restore_claude(z, to)
    if "--verify" in argv:
        return verify(argv[argv.index("--verify") + 1])
    dest = argv[argv.index("--dest") + 1] if "--dest" in argv else DEFAULT_DEST
    print("LOS DOS ACTIVOS QUE GIT NO PROTEGE -> %s" % dest)
    print("=" * 74)
    snapshot_claude(dest)
    if "--claude-only" in argv:
        print("\n  (--claude-only: el golden no se ha tocado)")
        return 0
    print()
    return snapshot(dest)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
