"""
curate.py — "Dreaming" emulation for Claude Code (B2, s079).
============================================================
The decision (decision_managed_agents_vs_claude_code.md): STAY on Claude Code, BORROW
the good. Managed Agents' "dreaming" = a scheduled curation pass that dedupes, resolves
contradictions (latest-wins), and surfaces insights. We emulate it here as a scheduled,
file-based job — no platform migration.

What it does (the curation pass):
  1. Rebuild the brain (structural curation: synthesize objects, blind-spots -> 0).
  2. Verify claims vs Gold DB (drift detection — contradictions/staleness).
  3. Regenerate the lean index + maturity.
  4. Emit a CURATION REPORT (what changed: drift, coverage, maturity, stale rules).

Run manually: python brain_v2/curate.py
Schedule (true "dreaming" cadence): weekly via a scheduled task.
FUTURE (the borrowed piece): the transcript-pattern-extraction half of dreaming can later
call the Managed Agents Dreaming API on session .jsonl transcripts — without leaving Claude Code.

DIAGNOSABILITY (T3a, 2026-07-25): a scheduled job you cannot date is not evidence. The
report now carries `timestamp` / `finished_at` / `duration_seconds`, and the rebuild's
stdout+stderr are persisted IN FULL — both into the report and appended to
`brain_v2/output/curation.log` — instead of the old `stderr[-400:]` console tail that
vanished with the terminal (and that was empty in ~12 of 27 failing runs, because the
real cause was in stdout). Children are forced to UTF-8 for the same reason as in
rebuild_all.py: several pipeline scripts print '→'/emoji, which explodes on the Windows
cp1252 default.
"""
import json, subprocess, sys, os, time, traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAIN = ROOT / "brain_v2"
REPORT = BRAIN / "curation_report.json"
LOG_PATH = BRAIN / "output" / "curation.log"

# stdio scope only — see the matching note in rebuild_all.py (no PYTHONUTF8).
CHILD_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _now():
    """ISO-8601 local timestamp with offset, second precision."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_print(text):
    """print() that cannot itself crash the curation pass on a cp1252 console/pipe."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        print(text.encode(enc, "replace").decode(enc, "replace"))


def _log(message):
    """Append to curation.log. Best-effort — never raises."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as fh:
            fh.write(message.rstrip("\n") + "\n")
    except Exception as exc:  # noqa: BLE001
        _safe_print(f"  (WARNING: could not write {LOG_PATH}: {exc})")


def _load(p):
    return json.load(open(p, encoding="utf-8")) if p.exists() else {}


def run():
    started_at = _now()
    t0 = time.monotonic()
    _log(f"\n\n{'*' * 78}\n* [{started_at}] CURATION PASS START (curate.py, pid {os.getpid()})\n{'*' * 78}")

    before_state = _load(BRAIN / "brain_state.json")
    before = {
        "claims": len(before_state.get("claims", [])),
        "coverage": before_state.get("_coverage", {}).get("pct_classified"),
        "drift": (before_state.get("_trust", {}) or {}).get("drift_needs_review"),
    }

    # 1-3: the structural curation (rebuild does graph+state+maturity+index+verify)
    _safe_print("=== DREAMING (emulated) — curation pass ===")
    cmd = [sys.executable, "brain_v2/rebuild_all.py"]
    launch_error = None
    try:
        r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=CHILD_ENV)
        rc, out, err = r.returncode, r.stdout or "", r.stderr or ""
    except Exception as exc:  # FileNotFoundError, OSError, ...
        launch_error = traceback.format_exc()
        rc, out, err = -1, "", f"could not launch {' '.join(cmd)}: {exc}\n{launch_error}"
    ok = rc == 0
    duration = round(time.monotonic() - t0, 1)
    finished_at = _now()
    _safe_print(f"rebuild_all: {'OK' if ok else 'FAILED'} (exit {rc}, {duration}s)")

    # Persist the WHOLE thing — the old code kept only stderr[-400:], on the console.
    _log(f"[{finished_at}] curate.py -> rebuild_all.py  exit={rc}  ({duration}s)\n"
         f"--- rebuild_all stdout ({len(out)} chars) ---\n{out}\n"
         f"--- rebuild_all stderr ({len(err)} chars) ---\n{err}\n"
         f"--- end: curate.py rebuild_all ---")

    after_state = _load(BRAIN / "brain_state.json")
    trust = after_state.get("_trust", {}) or {}
    after = {
        "claims": len(after_state.get("claims", [])),
        "coverage": after_state.get("_coverage", {}).get("pct_classified"),
        "drift": trust.get("drift_needs_review"),
        "drift_claim_ids": trust.get("drift_claim_ids", []),
    }

    # 4: curation report (what changed — the "insights surfaced")
    report = {
        "_design": "Curation/dreaming report. Drift = claims whose Gold-DB check no longer matches (contradiction/staleness). Review these — latest-data wins.",
        "timestamp": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration,
        "rebuild_ok": ok,
        "rebuild_exit_code": rc,
        "before": before, "after": after,
        "deltas": {
            "claims": after["claims"] - before["claims"],
            "coverage_pct": after.get("coverage"),
        },
        "ACTION_NEEDED": {
            "drift_claims_to_review": after.get("drift_claim_ids", []),
            "note": "Drift claims contradict current Gold DB — re-verify and update (latest-wins), or mark superseded.",
        },
        "rebuild_stdout": out,   # FULL, never truncated — the cause of a silent failure lives here
        "rebuild_stderr": err,   # FULL, never truncated
        "curation_log": str(LOG_PATH),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _safe_print(f"\nCURATION [{started_at}, {duration}s]: claims {before['claims']}->{after['claims']} | "
                f"coverage {after.get('coverage')}% | drift to review: {after.get('drift')}")
    _safe_print(f"report: {REPORT}")
    _safe_print(f"log:    {LOG_PATH}")
    if not ok:
        _safe_print(f"\nrebuild_all FAILED (exit {rc}) at {finished_at}.")
        _safe_print("--- stderr (full) ---")
        _safe_print(err.strip() if err.strip()
                    else "(stderr EMPTY — the cause is in rebuild_stdout / curation.log)")
        _safe_print(f"--- full stdout+stderr: {LOG_PATH} and {REPORT} ---")
        sys.exit(1)


if __name__ == "__main__":
    run()
