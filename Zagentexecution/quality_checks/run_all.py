"""Run every recurring quality check, and make the ones that cannot run say so.

WHY THIS EXISTS
---------------
Sixteen check scripts lived in this folder and NOTHING called any of them. They were written
after real incidents, to catch the next occurrence of a class of defect -- and then ran once,
by hand, on the day they were written. A check nobody runs is a comment.

Discovery is by GLOB, not by a list in this file. A central registry is a list someone forgets
to update, which is exactly how sixteen scripts ended up uncabled. Each script declares its own
tier in a module-level QUALITY_CHECK dict, read here WITHOUT importing it -- importing would
run it. A script with no declaration is UNCLASSIFIED and fails this runner loudly; it cannot
slip through by being new.

TIERS
  gate         recurring, offline, gives a real verdict   -> runs in every rebuild
  live         needs an RFC session to P01                 -> --tier live, never in a rebuild
  analysis     produces a report, not a pass/fail          -> on demand; scheduling proves nothing
  library      a shared helper imported by checks          -> never run on its own
  quarantined  the METHOD is refuted                       -> never run; the reason is printed

EXIT CODES
  0  every gate ran and came back clean
  1  a gate reported a finding, or errored, or is UNCLASSIFIED, or cannot gate at all
  3  no findings, but at least one gate could not run (missing Gold DB, timeout)
     -- a check that did not run is NOT evidence that what it looks for is absent
     (rule feedback_a_skipped_check_must_never_report_pass)

A crash is classified ERROR, never FINDING: a script that died did not
check anything, and calling its death a finding would claim it ran.

UNGATED
  Several of these scripts print their findings and then exit 0 regardless. Their exit code
  cannot distinguish clean from dirty, so this runner refuses to count them as PASS: they are
  reported as UNGATED and their output is kept. Fixing them one by one is real work; hiding
  the problem behind a green tick is not.
"""

# REGLAS QUE APLICAN AQUI (citadas para que existan en su punto de uso, no solo en el JSON):
#   feedback_a_gate_that_can_go_silent_is_worse_than_none
#     -> el momento es cuando un check se salta: el runner es quien lo ve
import argparse
import ast
import io
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STATE = REPO / "brain_v2" / "quality_checks_state.json"
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
TIMEOUT = 300


def declaration(path):
    """Read QUALITY_CHECK from the source without executing the module."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as e:
        return {"tier": "UNPARSEABLE", "what": f"{type(e).__name__}: {e}"}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "QUALITY_CHECK":
                    try:
                        return ast.literal_eval(node.value)
                    except ValueError:
                        return None
    return None


def can_gate(path):
    """Does this script have any path to a non-zero exit? If not, its 0 means nothing."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "exit":
            for a in node.args:
                if isinstance(a, ast.Constant) and a.value in (0, None):
                    continue
                return True
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, int) and node.value.value != 0:
                return True
    return False


def main():
    ap = argparse.ArgumentParser(description="Run the recurring quality checks.")
    ap.add_argument("--tier", default="gate",
                    choices=["gate", "live", "analysis", "all"],
                    help="which tier to run (default: gate)")
    ap.add_argument("--timeout", type=int, default=TIMEOUT, help="seconds per check")
    args = ap.parse_args()

    scripts = sorted(p for p in HERE.glob("*.py") if p.name != "run_all.py")
    print("=" * 78)
    print("quality checks - tier '{}' - {} script(s) discovered".format(args.tier, len(scripts)))
    print("=" * 78)

    unclassified, quarantined, selected = [], [], []
    for p in scripts:
        d = declaration(p)
        if not d or "tier" not in d:
            unclassified.append((p, d))
        elif d["tier"] == "quarantined":
            quarantined.append((p, d))
        elif d["tier"] == "library":
            continue                       # a helper module, not a check -- nothing to run
        elif args.tier == "all" or d["tier"] == args.tier:
            selected.append((p, d))

    for p, d in quarantined:
        print("  [QUARANTINED] {}".format(p.name))
        print("      {}".format(d.get("what", "")))
    for p, d in unclassified:
        print("  [UNCLASSIFIED] {} - no QUALITY_CHECK declaration. Add one; do not let it "
              "run unlabelled.".format(p.name))
    if quarantined or unclassified:
        print()

    results, findings, errors, skipped, ungated = [], 0, 0, 0, 0
    for p, d in selected:
        if d.get("needs") == "gold_db" and not GOLD.exists():
            print("  [SKIPPED] {} - needs the Gold DB, not present".format(p.name))
            results.append({"script": p.name, "tier": d["tier"], "outcome": "SKIPPED",
                            "why": "Gold DB not present"})
            skipped += 1
            continue

        gates = can_gate(p)
        t0 = time.time()
        try:
            r = subprocess.run([sys.executable, str(p)], cwd=str(REPO),
                               capture_output=True, timeout=args.timeout)
            code = r.returncode
            out = (r.stdout + r.stderr).decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            code, out = None, ""
        dt = time.time() - t0

        if code is None:
            outcome = "TIMEOUT"
            skipped += 1
        elif not gates:
            outcome = "UNGATED"
            ungated += 1
        elif code == 0:
            outcome = "PASS"
        elif code == 3:
            outcome = "PARTIAL"
            skipped += 1
        elif "Traceback (most recent call last)" in out:
            # a crash is not a finding -- calling it one would claim the check RAN
            outcome = "ERROR"
            errors += 1
        elif code == 1:
            outcome = "FINDING"
            findings += 1
        else:
            outcome = "ERROR"
            errors += 1

        tail = [ln for ln in out.strip().splitlines() if ln.strip()][-3:]
        results.append({"script": p.name, "tier": d["tier"], "outcome": outcome,
                        "exit": code, "seconds": round(dt, 1), "gates": gates,
                        "what": d.get("what", ""), "tail": tail})
        print("  [{:7}] {}  ({:.1f}s, exit={})".format(outcome, p.name, dt, code))
        if outcome in ("FINDING", "ERROR", "UNGATED", "TIMEOUT"):
            for ln in tail:
                print("            {}".format(ln[:110]))

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({
        "tier": args.tier, "discovered": len(scripts), "ran": len(results),
        "unclassified": [p.name for p, _ in unclassified],
        "quarantined": [p.name for p, _ in quarantined],
        "results": results,
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\n" + "-" * 78)
    print("ran {} | findings {} | errors {} | could-not-run {} | ungated {} | "
          "quarantined {} | unclassified {}".format(
              len(results), findings, errors, skipped, ungated,
              len(quarantined), len(unclassified)))
    print("state -> {}".format(STATE.relative_to(REPO)))

    if findings or errors or unclassified or ungated:
        return 1
    if skipped:
        print("\nNOT a full pass: something could not run. That is not evidence it is clean.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
