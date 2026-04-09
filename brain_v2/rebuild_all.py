"""
Rebuild EVERYTHING in one command.

Order:
1. brain_v2 build          — rebuild NetworkX graph from code + Gold DB
2. build_active_db         — rebuild SQLite active DB (PMO, claims, sessions, incidents)
3. generate_index / brain_state — rebuild brain_state.json from graph + annotations + claims
4. add_knowledge_links     — link objects to their deep reasoning docs

Run this: after any annotation, claim, or PMO change.
Run this: at session start if graph is stale.
Run this: on a new machine after git clone.

Usage: python brain_v2/rebuild_all.py
"""
import subprocess, sys
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


def main():
    print("=" * 60)
    print("Brain v3 Full Rebuild")
    print("=" * 60)

    run(["python", "-m", "brain_v2", "build"], "Step 1/4: Rebuild NetworkX graph")
    run(["python", "brain_v2/build_active_db.py"], "Step 2/4: Rebuild SQLite active DB")
    run(["python", "brain_v2/build_brain_state.py"], "Step 3/4: Rebuild brain_state.json")
    run(["python", "brain_v2/add_knowledge_links.py"], "Step 4/4: Link knowledge docs")

    print("\n" + "=" * 60)
    print("Rebuild complete.")
    print("=" * 60)
    print("\nValidation:")
    run(["python", "brain_v2/graph_queries.py", "stats"], "Brain stats")


if __name__ == "__main__":
    main()
