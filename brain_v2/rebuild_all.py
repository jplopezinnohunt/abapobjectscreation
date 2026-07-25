"""
Rebuild EVERYTHING in one command.

Order:
0. validate_ontology       — GATE: the canonical vocabulary (contract C-1). No rebuild
                             on an inconsistent domain vocabulary.
1. brain_v2 build          — rebuild NetworkX graph from code + Gold DB
2. build_active_db         — rebuild SQLite active DB (PMO, claims, sessions, incidents)
3. generate_index / brain_state — rebuild brain_state.json from graph + annotations + claims
4. add_knowledge_links     — link objects to their deep reasoning docs
5. regenerate dynamic      - rebuild companions from scripts
6. validate_companions     - validate HTML companions
7. build_landing_page      - build landing page

Run this: after any annotation, claim, or PMO change.
Run this: at session start if graph is stale.
Run this: on a new machine after git clone.

Usage: python brain_v2/rebuild_all.py
"""
import subprocess, sys, json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def run(cmd, description):
    print(f"\n[{description}]")
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR (exit {result.returncode}):")
        print(result.stderr)
        sys.exit(1)
    # Print last few lines of output
    for line in result.stdout.strip().split("\n")[-5:]:
        print(f"  {line}")


def regenerate_dynamic_companions():
    print("\n[Step 5/7: Regenerate dynamic companions]")
    registry_path = PROJECT_ROOT / "companions" / "companions.json"
    if not registry_path.exists():
        print("WARNING: Registry not found. Skipping dynamic companion regeneration.")
        return

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    except Exception as e:
        print(f"ERROR reading companions.json: {e}")
        return

    for entry in registry:
        if entry.get("type") == "dynamic" and "build_command" in entry:
            cmd_str = entry["build_command"]
            print(f"$ {cmd_str}")
            cmd = cmd_str.split()
            result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ERROR running {cmd_str}: {result.stderr}")
            else:
                print(f"  Successfully regenerated {entry.get('file')}")


def main():
    print("=" * 60)
    print("Brain v3 Full Rebuild")
    print("=" * 60)

    # STEP 0 — the vocabulary GATE (contract C-1). Every `domain` in claims /
    # domains.json / capability_model must resolve to a canonical_key in
    # brain_v2/capability_model/ontology.json. If it doesn't, the rebuild STOPS:
    # materializing brain_state on an inconsistent vocabulary is what forced the
    # fuzzy token-matching this gate replaces.
    run(["python", "brain_v2/validate_ontology.py"], "Step 0: Validate canonical ontology (contract C-1)")
    run(["python", "-m", "brain_v2", "build"], "Step 1: Rebuild NetworkX graph")
    run(["python", "brain_v2/build_active_db.py"], "Step 2: Rebuild SQLite active DB")
    run(["python", "brain_v2/verify_claims.py"], "Step 2b: Verify claims vs Gold DB (Layer 3 trust)")
    run(["python", "brain_v2/build_brain_state.py"], "Step 3: Rebuild brain_state.json")
    run(["python", "brain_v2/capability_model/maturity_score.py"], "Step 3b: Score capability maturity (Layer 15)")
    run(["python", "brain_v2/build_brain_index.py"], "Step 3c: Rebuild LEAN bootstrap index (tiered loading)")
    run(["python", "brain_v2/add_knowledge_links.py"], "Step 4/7: Link knowledge docs")
    
    # Regenerate dynamic companions
    regenerate_dynamic_companions()
    
    run(["python", "scripts/validate_companions.py"], "Step 6/7: Validate HTML companions")
    # Companion relationship graph BEFORE the landing — it injects `related`/`attachments` into
    # companions.json, which the landing renders as the per-card Related chips. Order matters.
    run(["python", "scripts/build_companion_graph.py", "--write-related"], "Step 7a/7: Rebuild companion knowledge graph")
    run(["python", "scripts/build_landing_page.py"], "Step 7/7: Rebuild landing page dashboard")

    print("\n" + "=" * 60)
    print("Rebuild complete.")
    print("=" * 60)
    print("\nValidation:")
    run(["python", "brain_v2/graph_queries.py", "stats"], "Brain stats")


if __name__ == "__main__":
    main()
