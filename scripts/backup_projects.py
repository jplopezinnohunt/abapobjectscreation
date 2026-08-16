"""Back up EVERY project's git history — especially the seven with no remote.

WHY THIS EXISTS
    Measuring the ecosystem found something worse than the 16 GB database: SEVEN of eleven
    projects have NO REMOTE AT ALL. `ecosystem-coordinator` — where the universal standards
    live, including the durability one — `FINCLOSSING`, `unescore20-PPM-brain` and four more
    exist only on this disk, history and all. A repo without a remote is 100% local, and no
    amount of committing changes that.

WHY `git bundle` AND NOT "create a remote"
    A bundle is a SINGLE FILE holding the full history, restorable with `git clone`. It needs
    no network, no account, and no decision about publishing UNESCO material to a personal
    GitHub. Creating remotes is a choice for the owner; taking a backup is not.

    And it is genuinely incremental: `git bundle create --since` or a marker revision means
    the second bundle carries only what is new. That is real incrementality, unlike a
    monolithic database where half a file restores to nothing.

WHAT ABOUT THE MEMORIES
    Already covered. ~/.claude/projects/*/memory/ holds the memory of ALL 13 projects and
    backup_golden.py zips it whole — one file, 1.6 MB, every project. It is not per-project
    work and must not be duplicated per project.

USAGE
    python scripts/backup_projects.py --dest "D:/claude_backups"
    python scripts/backup_projects.py --dest "D:/..." --status
"""
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECTS = Path(r"C:\Users\jp_lopez\projects")
STATE = "projects_backup_state.json"


LAST_ERROR = [""]


def git(args, cwd, retries=1):
    """Run git and KEEP THE REASON when it fails.

    The first version returned None and discarded stderr, so `unescrp` reported "FALLO al
    crear el bundle" with nothing to act on — and the same command run by hand succeeded in
    16 seconds. A wrapper that hides the error turns a transient USB hiccup into a mystery.
    Retries once for the same reason: writing 200 MB bundles to an external disk back to
    back does occasionally stall.
    """
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True,
                               timeout=900)
            if r.returncode == 0:
                return r.stdout.strip()
            LAST_ERROR[0] = (r.stderr or r.stdout or "").strip()[-200:]
        except Exception as e:
            LAST_ERROR[0] = str(e)[:200]
        if attempt < retries:
            time.sleep(3)
    return None


def repos():
    out = []
    for d in sorted(os.listdir(PROJECTS)):
        p = PROJECTS / d
        if p.is_dir() and (p / ".git").is_dir() and not d.startswith("_"):
            out.append(p)
    return out


def head_of(p):
    """The tip we are backing up. If it has not moved, the bundle is still current."""
    return git(["rev-parse", "HEAD"], p)


def load(dest):
    try:
        return json.loads((Path(dest) / STATE).read_text(encoding="utf-8"))
    except Exception:
        return {"_what_this_is": "que repo esta copiado, hasta que commit, y si se movio",
                "repos": {}}


def save(dest, st):
    (Path(dest) / STATE).write_text(json.dumps(st, indent=1, ensure_ascii=False),
                                    encoding="utf-8")


def status(dest):
    st = load(dest)
    print("HISTORIAL DE PROYECTOS COPIADO EN %s" % dest)
    print("=" * 78)
    print("%-28s %-8s %-10s %s" % ("proyecto", "remoto", "estado", "bundle"))
    print("-" * 78)
    pend = 0
    for p in repos():
        rec = st["repos"].get(p.name, {})
        remote = "si" if git(["remote"], p) else "NO"
        head = head_of(p)
        if not rec:
            state, pend = "SIN COPIA", pend + 1
        elif rec.get("head") == head:
            state = "al dia"
        else:
            state, pend = "DESFASADO", pend + 1
        print("%-28s %-8s %-10s %s" % (p.name[:28], remote, state,
                                       rec.get("file", "-")))
    print("-" * 78)
    print("%d repo(s) pendientes" % pend if pend else "todos al dia")
    return 0


def bundle(p, dest, st):
    """One file, whole history. Verified before it is trusted — `git bundle verify` is the
    only thing that separates a real bundle from a file that merely has the extension."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    head = head_of(p)
    rec = st["repos"].get(p.name, {})
    if rec.get("head") == head:
        print("  %-28s sin cambios" % p.name[:28])
        return False
    out = dest / ("%s_%s.bundle" % (p.name, time.strftime("%Y%m%d_%H%M")))
    if git(["bundle", "create", str(out), "--all"], p) is None:
        print("  %-28s FALLO: %s" % (p.name[:28], LAST_ERROR[0] or "sin detalle"))
        return False
    if git(["bundle", "verify", str(out)], p) is None:
        out.unlink(missing_ok=True)
        print("  %-28s bundle CORRUPTO, borrado" % p.name[:28])
        return False
    old = rec.get("file")
    st["repos"][p.name] = {
        "file": out.name, "head": head, "when": time.strftime("%Y-%m-%d %H:%M"),
        "bytes": out.stat().st_size,
        "has_remote": bool(git(["remote"], p)),
    }
    if old and old != out.name:
        try:
            (dest / old).unlink()      # one bundle per repo: --all always carries everything
        except OSError:
            pass
    print("  %-28s %7.1f MB  %s" % (p.name[:28], out.stat().st_size / 1e6, out.name))
    return True


def main(argv):
    dest = argv[argv.index("--dest") + 1] if "--dest" in argv else None
    if not dest:
        print("hace falta --dest")
        return 2
    if "--status" in argv:
        return status(dest)
    st = load(dest)
    print("COPIA DEL HISTORIAL DE CADA PROYECTO -> %s" % dest)
    print("=" * 78)
    n = 0
    for p in repos():
        if bundle(p, dest, st):
            n += 1
    save(dest, st)
    print("=" * 78)
    print("%d bundle(s) escritos o actualizados" % n)
    print("Restaurar cualquiera:  git clone <fichero>.bundle <carpeta>")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
