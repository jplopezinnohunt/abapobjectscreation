"""
Rebuild EVERYTHING in one command.

Order:
0.  validate_ontology       — GATE: the canonical vocabulary (contract C-1). No rebuild
                              on an inconsistent domain vocabulary.
1.  brain_v2 build          — rebuild NetworkX graph from code + Gold DB
2.  build_active_db         — rebuild SQLite active DB (PMO, claims, sessions, incidents)
2b. verify_claims           — verify claims vs Gold DB (Layer 3 trust / drift)
2c. claims_health           — NON-BLOCKING evidence-independence gate -> claims_health.json
3.  generate_index / brain_state — rebuild brain_state.json from graph + annotations + claims
4.  add_knowledge_links     — link objects to their deep reasoning docs
5.  regenerate dynamic      - rebuild companions from scripts
6.  validate_companions     - validate HTML companions
7.  build_landing_page      - build landing page

Run this: after any annotation, claim, or PMO change.
Run this: at session start if graph is stale.
Run this: on a new machine after git clone.

Usage: python brain_v2/rebuild_all.py

--------------------------------------------------------------------------------
DIAGNOSABILITY (T3a, 2026-07-25) — why this file writes a log
--------------------------------------------------------------------------------
The curation pass was failing ~12 of 27 runs with an EMPTY stderr: the only trace
was a console `print()` that died with the terminal. Three fixes live here:

 1. EVERY step appends its FULL stdout + stderr, with an ISO-8601 timestamp, the
    step name, the exit code and the duration, to `brain_v2/output/curation.log`
    (append; rotated at LOG_MAX_BYTES; the dir is gitignored). When stderr is
    empty the cause is almost always in stdout — so stdout is kept in full,
    never truncated to a tail.
 2. Children are forced to speak UTF-8 (`PYTHONIOENCODING`) and the
    parent decodes UTF-8 with `errors="replace"`. Several pipeline scripts print
    '→', '⛔' and emoji; under the Windows cp1252 default those raise
    UnicodeEncodeError INSIDE the child (or UnicodeDecodeError in the parent) —
    a prime suspect for the silent failures. `_safe_print` protects the console
    side of the same problem.
 3. A step whose executable cannot even be launched (FileNotFoundError on
    `python`, bad path) is caught and logged instead of dying as a bare traceback.

Control flow is UNCHANGED: pipeline steps still `sys.exit(1)` on failure; the
dynamic-companion regeneration still only warns. Only Step 2c is new, and it is
declared `fatal=False` on purpose — see the comment at its call site.
"""
import subprocess, sys, json, os, time, traceback
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LOG_PATH = PROJECT_ROOT / "brain_v2" / "output" / "curation.log"
LOG_MAX_BYTES = 5 * 1024 * 1024

# Force UTF-8 on both ends of every pipe. See DIAGNOSABILITY note (2) above.
# PYTHONIOENCODING only (stdio scope) — deliberately NOT PYTHONUTF8=1, which would also
# flip the children's default file-I/O encoding and thus change semantics beyond logging.
CHILD_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _now():
    """ISO-8601 local timestamp with offset, second precision."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_print(text):
    """print() that cannot itself crash the rebuild on a cp1252 console/pipe."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        print(text.encode(enc, "replace").decode(enc, "replace"))


def log(message, echo=False):
    """Append to curation.log. Never raises — a broken logger must not break the rebuild."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > LOG_MAX_BYTES:
            rotated = LOG_PATH.with_suffix(".log.1")
            if rotated.exists():
                rotated.unlink()
            LOG_PATH.rename(rotated)
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as fh:
            fh.write(message.rstrip("\n") + "\n")
    except Exception as exc:  # noqa: BLE001 — logging must be best-effort
        _safe_print(f"  (WARNING: could not write {LOG_PATH}: {exc})")
    if echo:
        _safe_print(message)


def _log_streams(description, returncode, elapsed, stdout, stderr):
    status = "OK" if returncode == 0 else "FAILED"
    log(f"[{_now()}] {status}  {description}  exit={returncode}  ({elapsed:.1f}s)\n"
        f"--- stdout ({len(stdout or '')} chars) ---\n{stdout or ''}\n"
        f"--- stderr ({len(stderr or '')} chars) ---\n{stderr or ''}\n"
        f"--- end: {description} ---")


def run(cmd, description, fatal=True):
    """Run one pipeline step.

    Persists the step name, an ISO-8601 timestamp, the exit code, the duration and
    the COMPLETE stdout + stderr to curation.log — on success and on failure.
    `fatal=True` (default) keeps the historical semantics: a non-zero exit aborts
    the rebuild with sys.exit(1). Returns the CompletedProcess (None if the process
    could not be launched at all).
    """
    cmd_str = " ".join(str(c) for c in cmd)
    _safe_print(f"\n[{description}]")
    _safe_print(f"$ {cmd_str}")
    log(f"\n{'=' * 78}\n[{_now()}] START  {description}\n$ {cmd_str}")

    started = time.monotonic()
    try:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                env=CHILD_ENV)
    except Exception as exc:  # FileNotFoundError, OSError, ...
        elapsed = time.monotonic() - started
        log(f"[{_now()}] LAUNCH-FAILED  {description}  ({elapsed:.1f}s)\n"
            f"$ {cmd_str}\n--- traceback ---\n{traceback.format_exc()}"
            f"--- end: {description} ---")
        _safe_print(f"ERROR: could not launch step '{description}': {exc}")
        _safe_print(f"  full traceback -> {LOG_PATH}")
        if fatal:
            sys.exit(1)
        return None

    elapsed = time.monotonic() - started
    _log_streams(description, result.returncode, elapsed, result.stdout, result.stderr)

    if result.returncode != 0:
        _safe_print(f"ERROR (exit {result.returncode}) in {description} after {elapsed:.1f}s:")
        _safe_print(result.stderr.strip() if (result.stderr or "").strip()
                    else "  (stderr EMPTY — the cause is in stdout, captured in full in the log)")
        _safe_print(f"  full stdout+stderr -> {LOG_PATH}")
        if fatal:
            sys.exit(1)
        return result

    # Print last few lines of output
    for line in result.stdout.strip().split("\n")[-5:]:
        _safe_print(f"  {line}")
    return result


def regenerate_dynamic_companions():
    _safe_print("\n[Step 5/7: Regenerate dynamic companions]")
    log(f"\n{'=' * 78}\n[{_now()}] START  Step 5/7: Regenerate dynamic companions")
    registry_path = PROJECT_ROOT / "companions" / "companions.json"
    if not registry_path.exists():
        msg = "WARNING: Registry not found. Skipping dynamic companion regeneration."
        _safe_print(msg)
        log(f"[{_now()}] SKIPPED  Step 5/7: {msg} ({registry_path})")
        return

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    except Exception as e:
        _safe_print(f"ERROR reading companions.json: {e}")
        log(f"[{_now()}] FAILED  Step 5/7: reading {registry_path}\n"
            f"--- traceback ---\n{traceback.format_exc()}--- end: Step 5/7 ---")
        return

    for entry in registry:
        if entry.get("type") == "dynamic" and "build_command" in entry:
            cmd_str = entry["build_command"]
            description = f"Step 5/7: companion '{entry.get('file')}'"
            # Non-fatal by design (unchanged): a broken companion must not block the brain.
            # run() already persists the full stdout+stderr+timestamp of the failure.
            result = run(cmd_str.split(), description, fatal=False)
            if result is not None and result.returncode == 0:
                _safe_print(f"  Successfully regenerated {entry.get('file')}")


def main():
    _safe_print("=" * 60)
    _safe_print("Brain v3 Full Rebuild")
    _safe_print("=" * 60)
    log(f"\n\n{'#' * 78}\n# [{_now()}] REBUILD START  (pid {os.getpid()}, root {PROJECT_ROOT})\n{'#' * 78}")
    run_started = time.monotonic()

    # STEP 0 — the vocabulary GATE (contract C-1). Every `domain` in claims /
    # domains.json / capability_model must resolve to a canonical_key in
    # brain_v2/capability_model/ontology.json. If it doesn't, the rebuild STOPS:
    # materializing brain_state on an inconsistent vocabulary is what forced the
    # fuzzy token-matching this gate replaces.
    run(["python", "brain_v2/validate_ontology.py"], "Step 0: Validate canonical ontology (contract C-1)")
    # THE GUARANTEE (s097): every durable thing a session produced must be declared,
    # present, and traceable to the method that made it. Fails on a declared asset that
    # vanished or a method pointing at a tool that does not exist; warns on Gold DB
    # tables nobody declared. Discipline is not a mechanism — this is.
    # Golden cases for the algorithms. Fails the rebuild on a regression, because an
    # algorithm that silently changes its answer is the most expensive defect we have.
    # A path field holding PROSE makes every check over it silently wrong. C3 was published
    # as an unimplemented idea while its tool ran, because one entry in its list of tools was
    # a sentence — and the same sentence had been copied into a second store. Twice = gate.
    run(["python", "brain_v2/methods/validate_paths.py"],
        "Step 0a3: Path gate — a path field must hold a path, never prose")
    run(["python", "brain_v2/methods/validate_algorithms.py"],
        "Step 0a: Algorithm golden cases — no silent regressions")
    # The artifacts the algorithms PRODUCE. Non-fatal on purpose: a floor can trip because
    # the tenant legitimately changed, and blocking a rebuild on that would get the harness
    # deleted. It must be LOUD, not obstructive — the function-level gate above is the fatal one.
    run(["python", "brain_v2/methods/validate_artifacts.py"],
        "Step 0a2: Artifact golden cases — did any algorithm stop working?", fatal=False)
    run(["python", "brain_v2/methods/verify_assets.py"],
        "Step 0b: Asset gate — knowledge produced must be knowledge registered")
    # Is the portable skill still the machine we actually have? Non-fatal: a newly added
    # tool legitimately shows up as orphaned until someone places it in a phase.
    run(["python", "brain_v2/methods/audit_skill_coverage.py"],
        "Step 0c: Skill coverage audit — orphaned tools, phantom refs, missing cadences",
        fatal=False)
    # Is our capability where the work is, and is the DIFFERENTIATOR tier actually our
    # strongest? Measured, not asserted — the thesis has to survive its own numbers.
    run(["python", "brain_v2/methods/build_domain_capability_matrix.py"],
        "Step 0d: Domain x capability matrix — coverage inversion + thesis health",
        fatal=False)
    # Invert the asset index: what does each DOMAIN have — tables, extraction, algorithms,
    # knowledge, flows — and what is it missing? Assets catalogued by kind cannot answer that.
    run(["python", "brain_v2/methods/build_domain_assets.py"],
        "Step 0e: Domain asset bundles — what each domain has and lacks", fatal=False)
    # s099 — code is a first-class brain layer. Runs BEFORE the graph so the source
    # inventory (physical integrity + multi-domain linkage) is current for everything
    # downstream. Born from YRGGBS00: the canonical path held a 29-line stub while the
    # 1,593-line body sat outside the corpus in UTF-16, and a TIER_1 claim was published
    # saying a production control did not exist because the grep found nothing.
    run(["python", "brain_v2/build_code_inventory.py"],
        "Step 0f: Code inventory — source integrity + multi-domain linkage", fatal=False)
    run(["python", "brain_v2/build_code_sections.py"],
        "Step 0g: Code sections — the routine is the unit of behaviour", fatal=False)
    run(["python", "brain_v2/interpret_code.py", "--enrich"],
        "Step 0h: Interpret code THROUGH the brain, and write back what it learned",
        fatal=False)
    run(["python", "brain_v2/methods/unlanded_discoveries.py"],
        "Step 0i: Unlanded discoveries — what the code touches and the brain cannot "
        "explain", fatal=False)
    run(["python", "-m", "brain_v2", "build"], "Step 1: Rebuild NetworkX graph")
    run(["python", "brain_v2/build_active_db.py"], "Step 2: Rebuild SQLite active DB")
    run(["python", "brain_v2/verify_claims.py"], "Step 2b: Verify claims vs Gold DB (Layer 3 trust)")
    # Step 2c — NON-BLOCKING on purpose (fatal=False). claims_health.py is a *scorer*,
    # not a gate: it reads brain_v2/claims/claims.json, buckets each live claim as
    # STRONG/WEAK/UNSUPPORTED by evidence-type independence and emits
    # brain_v2/claims_health.json (consumed by the meta-capability VERIFY dimension and
    # quoted by session_start_hook.py). NOTHING downstream in this pipeline reads that
    # file, so a missing/malformed claims.json — or any scoring hiccup — must NOT abort
    # a structural rebuild. It takes no arguments and runs in ~2s (claims.json only, it
    # never touches the 14 GB Gold DB). Its failure is still logged in full to curation.log.
    run(["python", "brain_v2/claims_health.py"],
        "Step 2c: Claims-health gate (evidence independence -> claims_health.json)", fatal=False)
    # PROFILE (L16) must be crossed BEFORE brain_state is assembled — build_brain_state
    # attaches profile_links.json as system_profile._links. This step also GATES the
    # profile invariants (tier + evidence per module), so a malformed profile stops the
    # rebuild instead of silently shipping a fact-sheet nobody can trust.
    run(["python", "brain_v2/system_profile/build_profile_links.py"],
        "Step 2c: Cross the PROFILE (L16) against L14/L15/claims + gate invariants")
    # BIDIRECTIONAL model (s097): bottom-up ascent + coherence + cross-cutting overlay.
    # Non-fatal: it READS brain_state (previous run) to compute the ascent, so on a
    # first-ever build it simply has less to chew on. Its output is attached as L16
    # system_profile._model_graph on the NEXT line's rebuild.
    run(["python", "brain_v2/system_profile/build_model_graph.py"],
        "Step 2d: Bidirectional model graph (ascent + coherence + cross-cutting)", fatal=False)
    run(["python", "brain_v2/build_brain_state.py"], "Step 3: Rebuild brain_state.json")
    run(["python", "brain_v2/capability_model/maturity_score.py"], "Step 3b: Score capability maturity (Layer 15)")
    # Steps 3b3/3b4 — the two SELF-ASSESSMENT instruments. They were NOT in this pipeline
    # (measured 2026-07-26: 0 references), so nothing refreshed them: gold_extractor_maturity.json
    # sat 19 days stale (2026-07-07) and meta_capability.json was read as fresh while frozen.
    # Consequence: the model-state curve recorded meta_maturity=62.4 for 6 consecutive runs when
    # the real re-measured value was 60.8 — the instrument that measures how we work was itself
    # unmaintained. Both run in ~0.2s. They go BEFORE the snapshot so the curve records live values.
    run(["python", "brain_v2/gold_extractor_maturity.py"],
        "Step 3b3: Score extractor maturity (per domain x table ladder L0..L4)", fatal=False)
    run(["python", "brain_v2/meta_capability.py"],
        "Step 3b4: Self-assess our way of working (meta-capability, 7 dimensions)", fatal=False)

    # Step 3b2 — MUST run after 3b/3b3/3b4, never before. maturity_score.py (3b) overwrites
    # maturity.json in place; snapshotting before it would silently capture the PREVIOUS
    # rebuild's measurement — a permanent, invisible off-by-one-rebuild in the curve.
    # Appends one row per run to the model-state history DB: the time series of the
    # understanding IS the product deliverable, and it used to be destroyed every rebuild.
    # Non-fatal: losing a measurement point must not abort a structural rebuild.
    run(["python", "brain_v2/capability_model/snapshot_model_state.py"],
        "Step 3b2: Snapshot model state -> history DB (the curve)", fatal=False)
    run(["python", "brain_v2/build_brain_index.py"], "Step 3c: Rebuild LEAN bootstrap index (tiered loading)")
    # The loop fires on EVIDENCE, not on someone remembering. Compares the model's state
    # against declared thresholds and says what to re-run and why.
    run(["python", "brain_v2/methods/check_triggers.py"],
        "Step 3d: Trigger check — what needs re-running on current evidence", fatal=False)
    # Step 3e — the recurring quality checks. They existed for months and NOTHING called
    # them: 16 scripts written after real incidents to catch the next occurrence of a class
    # of defect, each run once by hand on the day it was written. A check nobody runs is a
    # comment. run_all.py discovers them by GLOB and reads each script's own QUALITY_CHECK
    # declaration, so a new check is wired the moment it is written and an UNDECLARED one is
    # reported loudly instead of skipped. Only tier 'gate' runs here (offline, real verdict);
    # 'live' needs an RFC session, 'analysis' produces reports, 'quarantined' is refuted.
    # NON-FATAL on purpose: a finding in the data must not abort a structural rebuild of the
    # brain. It is recorded in brain_v2/quality_checks_state.json and surfaced at close.
    run(["python", "Zagentexecution/quality_checks/run_all.py", "--tier", "gate"],
        "Step 3e: Recurring quality checks (gate tier)", fatal=False)
    run(["python", "brain_v2/add_knowledge_links.py"], "Step 4/7: Link knowledge docs")

    # Regenerate dynamic companions
    regenerate_dynamic_companions()

    run(["python", "scripts/validate_companions.py"], "Step 6/7: Validate HTML companions")
    # Companion relationship graph BEFORE the landing — it injects `related`/`attachments` into
    # companions.json, which the landing renders as the per-card Related chips. Order matters.
    run(["python", "scripts/build_companion_graph.py", "--write-related"], "Step 7a/7: Rebuild companion knowledge graph")
    run(["python", "scripts/build_landing_page.py"], "Step 7/7: Rebuild landing page dashboard")

    _safe_print("\n" + "=" * 60)
    _safe_print("Rebuild complete.")
    _safe_print("=" * 60)
    _safe_print("\nValidation:")
    run(["python", "brain_v2/graph_queries.py", "stats"], "Brain stats")

    log(f"\n{'#' * 78}\n# [{_now()}] REBUILD COMPLETE  "
        f"({time.monotonic() - run_started:.1f}s total)\n{'#' * 78}")
    _safe_print(f"\nfull run log: {LOG_PATH}")


if __name__ == "__main__":
    main()
