"""
stop_integrity_hook.py — Stop hook (s098). The INTEGRITY GATE, and it CHECKS rather than asks.
==============================================================================================
The three hooks that existed before this one all TELL the agent to do something: commit your
source, run the steward. None of them verifies anything. That is the exact failure rule
`feedback_a_stated_discipline_is_not_a_control` was written about — and the evidence for it
is that rule #180 existed and was violated four times in one session by the agent that wrote
it.

So this one runs the checks and stays SILENT unless something is actually wrong.

WHY IT IS READ-ONLY, which is the design decision that matters
    The obvious implementation re-runs every builder and compares. It must not: a builder
    writes its output in place, so a hook that ran them would silently REPAIR any drift and
    destroy the very signal it exists to raise. Regenerate-and-compare stays an explicit
    command (`python scripts/verify_generated.py`). The hook only reads.

WHAT IT CHECKS — each one is a failure that happened, not a hypothetical
  1. TOKEN OR FORMAT LEAK in a published companion. Four times in s098 a template
     substitution missed its anchor, the builder printed OK because the Python still parsed,
     and the page shipped with a raw @TOKEN@ or a stray %s.
  2. THE GOLDEN SNAPSHOT IS OLDER THAN THE GOLDEN. The backup script and one snapshot exist;
     nothing ever said when it went stale. Silence here is the default state of a backup.
  3. WORK IN A SIBLING PROJECT THAT NO COPY COVERS. Measured s098: seven of eleven projects
     have NO git remote and nine hold uncommitted work. A bundle carries only committed
     history, so uncommitted files in a remote-less repo exist on exactly one disk — and a
     green backup report cannot see them. Narrow on purpose: mid-session edits are normal
     and only the two genuinely exposed shapes are reported.
  4. A SCRIPT THAT IS NOT IN THE ARSENAL. A19 was written and nearly went unregistered; an
     algorithm nobody can find is an algorithm nobody reuses. This one PROPOSES rather than
     asserting, because the hook cannot tell a helper from an algorithm and claiming a
     defect it cannot prove is how a gate starts crying wolf.

Contract, copied from stop_durability_hook.py deliberately:
  * NON-BLOCKING — additionalContext only, never decision:block.
  * stop_hook_active guard, so it can never loop.
  * dedup'd on the finding set, so a standing problem is stated once and not every turn.
  * fail-safe — ANY error exits 0 silently. A broken gate must never break a session.
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
MARKER = HERE / ".last_integrity_nudge"

GOLD = ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
POINTER = ROOT / "Zagentexecution" / "sap_data_extraction" / "backup_location.json"
COMPANIONS = ROOT / "companions"
ALGOS = ROOT / "brain_v2" / "methods" / "algorithms.json"
PM = ROOT / "process_mining"

TOKEN = re.compile(r"@[A-Z][A-Z_0-9]*@")
FMT = re.compile(r"%[sdf](?![\w%])")
STALE_DAYS = 7


def check_leaks():
    out = []
    for p in sorted(COMPANIONS.glob("*.html")):
        try:
            s = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        t = sorted(set(TOKEN.findall(s)))
        f = sorted(set(FMT.findall(s)))
        if t or f:
            out.append("%s lleva %s sin sustituir"
                       % (p.name, (t + f)[:3]))
    return out


def check_backup():
    try:
        if not GOLD.exists():
            return []
        # Follow the pointer the backup script leaves. Guessing a fixed folder is how
        # this check reported "the golden has NO copy" the moment the destination moved
        # to an external disk — a false alarm that trains the reader to skip the gate.
        try:
            dest = Path(json.loads(POINTER.read_text(encoding="utf-8"))["dest"])
        except Exception:
            dest = ROOT.parent / "_golden_backups"
        # UNREACHABLE IS NOT MISSING. An external disk spends most of its life unplugged —
        # that is what makes it an external backup. Reporting "no copy exists" every time it
        # is disconnected would fire on the normal case and teach the reader to skip the
        # gate, which is the failure this hook was written to avoid.
        if not dest.exists():
            try:
                last = json.loads(POINTER.read_text(encoding="utf-8"))
                return ["el destino de las copias (%s) no esta accesible — disco "
                        "desconectado. Ultima copia: %s. No es un fallo, pero mientras siga "
                        "desconectado el golden solo existe aqui"
                        % (dest, last.get("when", "?"))]
            except Exception:
                return []
        snaps = sorted(dest.glob("*.db"), key=lambda x: x.stat().st_mtime)
        if not snaps:
            return ["el GOLDEN (%.1f GB) no tiene NINGUNA copia en %s — "
                    "python scripts/backup_golden.py --dest ..."
                    % (GOLD.stat().st_size / 1e9, dest)]
        newest = snaps[-1]
        age_d = (time.time() - newest.stat().st_mtime) / 86400.0
        if GOLD.stat().st_mtime > newest.stat().st_mtime + 3600:
            return ["el GOLDEN cambio DESPUES del ultimo snapshot (%s, hace %.1f dias) — "
                    "la copia ya no refleja lo que hay" % (newest.name, age_d)]
        if age_d > STALE_DAYS:
            return ["el ultimo snapshot del golden tiene %.0f dias (%s)"
                    % (age_d, newest.name)]
    except Exception:
        return []
    return []


# REVIEWED AND DELIBERATELY NOT ALGORITHMS. Without this list the gate would report the same
# ten scripts every session forever, and a gate that repeats a finding nobody will act on
# becomes noise — the exact degradation this hook was designed to avoid. Triaged s098: all
# are pipeline steps or helpers of 54-135 lines, none declares itself an algorithm, and none
# is reusable on another installation, which is the bar for the arsenal. A NEW unregistered
# script will still be reported, which is the point.
#
# ⛔ ESTA LISTA CADUCA, Y CADUCO. Revisada 2026-08-26: tres de sus diez -- fm_executed_census,
# semantic_activity_map y tier2_sod -- se REGISTRARON como algoritmos (A42, A48, A49) y
# seguian excluidos aqui, asi que el hook los daba por triados para siempre. Una exclusion
# escrita a mano no se entera de que el mundo cambio: al registrar un algoritmo hay que
# mirar si estaba en esta lista.
NOT_ALGORITHMS = {
    "accumulate_problems.py", "attach_object_text.py", "build_p2p_log.py",
    "gold_ref.py", "method_registry.py", "parse_syslog.py",
    "tier0_1_pipeline.py", 
}


PROJECTS = ROOT.parent


def _git(args, cwd):
    try:
        r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True,
                           timeout=8)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def check_sibling_exposure():
    """Work in OTHER projects that no copy covers.

    Deliberately narrow, because uncommitted files mid-session are NORMAL and a gate that
    flags them every turn is noise. Only two shapes are reported, and both are real
    exposure that a green backup report cannot see:

      · uncommitted work in a repo with NO REMOTE — a bundle carries only committed
        history, so this exists on exactly one disk and nowhere else;
      · commits that were never pushed, in a repo that HAS a remote — the one case where
        pushing costs nothing and is simply forgotten.

    THIS repo is excluded: stop_durability_hook.py already owns it, and two gates naming
    the same files is how a reader learns to skim both.
    """
    out = []
    try:
        dirs = [p for p in sorted(PROJECTS.iterdir())
                if p.is_dir() and (p / ".git").is_dir()
                and not p.name.startswith("_") and p.resolve() != ROOT.resolve()]
    except Exception:
        return []
    naked, unpushed = [], []
    for p in dirs:
        st = _git(["status", "--porcelain"], p)
        if st is None:
            continue
        dirty = len([x for x in st.splitlines() if x.strip()])
        remote = _git(["remote"], p)
        if dirty and not remote:
            naked.append("%s(%d)" % (p.name, dirty))
        if remote:
            br = _git(["rev-parse", "--abbrev-ref", "HEAD"], p)
            cnt = _git(["rev-list", "--count", "origin/%s..HEAD" % br], p) if br else None
            if cnt and cnt != "0":
                unpushed.append("%s(%s)" % (p.name, cnt))
    if naked:
        out.append("SIN remoto y con cambios sin commitear — solo existen en este disco: %s"
                   % ", ".join(naked[:5]))
    if unpushed:
        out.append("commits sin subir a origin: %s" % ", ".join(unpushed[:5]))
    return out


def check_algorithms():
    try:
        reg = json.loads(ALGOS.read_text(encoding="utf-8"))
        bound = json.dumps(reg).lower()
        missing = []
        for p in sorted(PM.glob("*.py")):
            if p.name.startswith("_") or p.name in NOT_ALGORITHMS:
                continue
            if p.name.lower() not in bound:
                missing.append(p.name)
        if missing:
            # PROPOSE, do not sentence. Some of these are helpers and some are real
            # algorithms, and the hook cannot tell — asserting a defect it cannot prove is
            # how a gate starts crying wolf, and a gate that cries wolf gets ignored.
            return ["%d script(s) de process_mining no aparecen en el arsenal — revisa si "
                    "alguno deberia estar: %s"
                    % (len(missing), ", ".join(missing[:5]))]
    except Exception:
        return []
    return []


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if data.get("stop_hook_active"):
        sys.exit(0)

    findings = []
    for fn in (check_leaks, check_backup, check_sibling_exposure, check_algorithms):
        try:
            findings.extend(fn())
        except Exception:
            pass          # a check that breaks is silent; it never breaks the session
    if not findings:
        sys.exit(0)

    sig = hashlib.sha1("\n".join(sorted(findings)).encode("utf-8")).hexdigest()
    # TWO separate try blocks, not one. Merged, the first run's FileNotFoundError on the read
    # abandons the whole block and the write NEVER happens — so the marker is never created
    # and the gate nudges every single turn. stop_durability_hook.py already splits them;
    # copying the contract but merging the blocks reintroduced the bug it had avoided.
    try:
        if MARKER.read_text(encoding="utf-8").strip() == sig:
            sys.exit(0)
    except Exception:
        pass
    try:
        MARKER.write_text(sig, encoding="utf-8")
    except Exception:
        pass

    msg = ("INTEGRITY GATE — comprobado, no supuesto. %d hallazgo(s):\n  - %s"
           "\nVerificacion completa (regenera y compara): "
           "`python scripts/verify_generated.py`"
           % (len(findings), "\n  - ".join(findings)))
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": msg}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
