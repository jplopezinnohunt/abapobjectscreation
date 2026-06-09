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
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAIN = ROOT / "brain_v2"
REPORT = BRAIN / "curation_report.json"


def _load(p):
    return json.load(open(p, encoding="utf-8")) if p.exists() else {}


def run():
    before_state = _load(BRAIN / "brain_state.json")
    before = {
        "claims": len(before_state.get("claims", [])),
        "coverage": before_state.get("_coverage", {}).get("pct_classified"),
        "drift": (before_state.get("_trust", {}) or {}).get("drift_needs_review"),
    }

    # 1-3: the structural curation (rebuild does graph+state+maturity+index+verify)
    print("=== DREAMING (emulated) — curation pass ===")
    r = subprocess.run([sys.executable, "brain_v2/rebuild_all.py"], cwd=str(ROOT),
                       capture_output=True, text=True)
    ok = r.returncode == 0
    print("rebuild_all:", "OK" if ok else "FAILED")

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
        "rebuild_ok": ok,
        "before": before, "after": after,
        "deltas": {
            "claims": after["claims"] - before["claims"],
            "coverage_pct": after.get("coverage"),
        },
        "ACTION_NEEDED": {
            "drift_claims_to_review": after.get("drift_claim_ids", []),
            "note": "Drift claims contradict current Gold DB — re-verify and update (latest-wins), or mark superseded.",
        },
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nCURATION: claims {before['claims']}->{after['claims']} | coverage {after.get('coverage')}% | "
          f"drift to review: {after.get('drift')}")
    print(f"report: {REPORT}")
    if not ok:
        print("STDERR tail:", r.stderr[-400:])
        sys.exit(1)


if __name__ == "__main__":
    run()
