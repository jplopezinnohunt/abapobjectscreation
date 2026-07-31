"""run_analysis_cycle.py — actually RUN the on-demand algorithms (s097).

"On demand" is a euphemism for "never runs" when nobody demands it. The status check found
twelve algorithms in that state: real code, bound to real tools, producing nothing because
no trigger fires them.

That is a structural hole, not a detail. An algorithm that does not run is documentation.

This runs the analysis algorithms — the ones that need no SAP connection, only the golden
data we already hold — **in dependency order**, because the nesting is real: the boundary
must be discovered before satellites can be derived from it, and objects must resolve to
components before anything can be attributed to a domain.

**The order IS the knowledge.** A trigger must never name a script to run — that is a
decision taken on demand, and on-demand decisions are exactly what stops being taken. A
trigger reports EVIDENCE; this file holds what to run and in which sequence, so adding an
algorithm means placing it in the chain, not remembering to call it. Write-path attribution
sits at L2 for a concrete reason: when it classifies a class as INTERFACE it names the
calling function modules, and those functions are what the satellite derivation groups on
— so attribution has to precede boundary discovery, not follow it.

Deliberately NOT included: anything requiring RFC. Extraction depends on a VPN and on
someone deciding it is time; those stay explicit. This runs what can always run.

    python brain_v2/methods/run_analysis_cycle.py            # the full cycle
    python brain_v2/methods/run_analysis_cycle.py --quick    # skip the slow log scans
"""
import json
import subprocess
import sys
import time
from pathlib import Path

# A child's output can carry characters the Windows console encoding cannot print, and an
# UnicodeEncodeError here would abort the whole cycle over a cosmetic detail.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def say(text):
    """print() that cannot kill the run."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        print(text.encode(enc, "replace").decode(enc, "replace"))

REPO = Path(__file__).resolve().parents[2]
STATE = Path(__file__).parent / "cycle_state.json"

# (script, label, needs_full_log_scan) — ORDER IS THE DEPENDENCY ORDER.
CYCLE = [
    ("process_mining/executed_objects_domain_map.py",
     "L1 classify every executed object", True),
    ("process_mining/attach_object_text.py",
     "L1 attach readable text — makes the frontier reviewable", False),
    ("brain_v2/parse_abap_edges.py",
     "L0 code edges from extracted source", False),
    ("process_mining/derive_object_roles.py",
     "L1 what each object is FOR", False),
    ("process_mining/attribute_changes_to_programs.py",
     "L2 what WRITES each object class, and through which channel", True),
    ("brain_v2/build_interface_inventory.py",
     "L2 every interface as a RECORD — prose is not queryable knowledge", False),
    ("process_mining/interface_boundary.py",
     "L2 discover the boundary: live / dead / undeclared", True),
    ("process_mining/derive_satellites.py",
     "L3 derive satellites -> origin -> flow", True),
    ("process_mining/detect_drift.py",
     "L3 concept drift over the accumulated history", True),
    ("process_mining/extract_business_rules.py",
     "L2 the rules that live in code, not in configuration", False),
    ("brain_v2/system_profile/build_profile_links.py",
     "L6 cross the profile against the model", False),
    ("brain_v2/system_profile/build_model_graph.py",
     "L6 ascent + coherence + cross-cutting", False),
    ("brain_v2/methods/build_domain_assets.py",
     "L6 asset bundle per domain", False),
    ("brain_v2/methods/build_domain_capability_matrix.py",
     "L6 is capability where the work is?", False),
    ("brain_v2/methods/measure_portability.py",
     "L6 what survives installation #2", False),
    ("brain_v2/methods/validate_paths.py",
     "the path gate — a path field must hold a path, never prose", False),
    ("brain_v2/methods/algorithm_status.py",
     "L6 which algorithms are real", False),
    ("brain_v2/methods/improve_algorithms.py",
     "L6 which algorithm to improve next", False),
    ("brain_v2/build_channel_registry.py",
     "L2 lift the DECLARED channel taxonomy out of prose so A8 can check against it", False),
    ("brain_v2/methods/audit_prose_classifications.py",
     "L6 which analysis is trapped in prose, where no algorithm can reach it", False),
    ("brain_v2/methods/audit_agent_freshness.py",
     "L6 do the agents still know what the model knows?", False),
    ("brain_v2/methods/check_triggers.py",
     "L6 what needs re-running on current evidence", False),
]


def main():
    quick = "--quick" in sys.argv
    say(f"[analysis cycle] {len(CYCLE)} steps, dependency order"
          f"{' (quick: skipping full log scans)' if quick else ''}\n")
    ok, failed, skipped = 0, [], 0

    # Stamp STARTED before anything runs. Two reasons, and the second is the better one:
    #   1. the path gate runs INSIDE this cycle, and on a fresh machine it would fail on
    #      cycle_state.json not existing yet — a chicken-and-egg of my own making;
    #   2. a cycle that STARTED AND NEVER FINISHED is now visible. Writing only on
    #      completion makes a crashed run indistinguishable from one that never began.
    import datetime
    _started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    try:
        json.dump({"status": "RUNNING", "started_utc": _started,
                   "_why": "a run that starts and dies must not look like a run that never began"},
                  open(STATE, "w", encoding="utf-8"), indent=1)
    except OSError:
        pass

    for script, label, heavy in CYCLE:
        if quick and heavy:
            say(f"  SKIP  {label}")
            skipped += 1
            continue
        p = REPO / script
        if not p.exists():
            say(f"  MISS  {label}  ({script} not found)")
            failed.append(script)
            continue
        t0 = time.monotonic()
        r = subprocess.run([sys.executable, str(p)], cwd=str(REPO),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        dt = time.monotonic() - t0
        if r.returncode == 0:
            ok += 1
            tail = [x for x in (r.stdout or "").strip().split("\n") if x.strip()]
            head = tail[1] if len(tail) > 1 else (tail[0] if tail else "")
            say(f"  OK    {label}  ({dt:.0f}s)")
            if head:
                say(f"        {head.strip()[:110]}")
        else:
            failed.append(script)
            err = (r.stderr or r.stdout or "").strip().split("\n")
            say(f"  FAIL  {label}  ({dt:.0f}s)")
            say(f"        {(err[-1] if err else '')[:110]}")

    print(f"\n  {ok} ran · {len(failed)} failed · {skipped} skipped")
    # RECORD THAT IT RAN — before the exit, and whether or not steps failed.
    #
    # Written even on failure ON PURPOSE. A cycle that ran and failed half its steps is WORSE
    # than one that did not run, because its artifacts look fresh; recording only successes
    # would hide exactly that case. And it is written before sys.exit(1), because the run
    # happened regardless of how it ended.
    #
    # Without this file, "run it weekly" cannot be verified and "it did not run" cannot be
    # detected — the loop would go back to depending on someone remembering, which is the
    # hole this file exists to close.
    try:
        json.dump({
            "status": "COMPLETE",
            "started_utc": _started,
            "_what_this_is": "when the cycle last ran, and how it went",
            "_why": ("a schedule that fails silently is worse than no schedule: the absence "
                     "of fresh artifacts reads as 'nothing changed'. This makes it visible."),
            "last_run_utc": datetime.datetime.now(
                datetime.timezone.utc).isoformat(timespec="seconds"),
            "steps_ran": ok, "steps_failed": len(failed), "steps_skipped": skipped,
            "failed": failed,
        }, open(STATE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    except OSError as e:
        say(f"  could not record the run: {e}")

    if failed:
        say("  failed: " + ", ".join(failed))
        sys.exit(1)
    say("  Every analysis algorithm ran. 'On demand' now has a demander.")


if __name__ == "__main__":
    main()
