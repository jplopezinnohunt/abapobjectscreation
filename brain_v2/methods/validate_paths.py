"""validate_paths.py — a path field must hold a PATH, never prose (s097).

C3 was reported PROPOSED — an idea with no code — while `parse_abap_edges.py` sat on disk
running. The cause was one entry inside a list of paths:

    "bound_in": ["brain_v2/parse_abap_edges.py", "brain_v2 graph build"]
                                                  ^^^^^^^^^^^^^^^^^^^^^ prose

The binding check requires every declared tool to exist, so one sentence made the check
false and the catalogue reported a BUILT algorithm as unbuilt. The catalogue lying about
itself is the precise failure the catalogue exists to prevent.

Fixing that entry was not the fix. When I looked for others, the SAME prose had also been
copied into the asset registry — a second store, silently carrying the same defect. That is
the argument for a gate: the fault is not one bad value, it is that nothing ever checked
whether a path-typed field held a path.

Two classes of defect, both caught here:

    PROSE           a sentence where a path belongs — the field cannot be verified at all
    DEAD PATH       a real path shape pointing at a file that is not there

Schema documentation is excluded by design: `_fields` and `_legend` sections describe what
a field means and are prose on purpose.

Run: python brain_v2/methods/validate_paths.py     Exit 1 on any violation.
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

# store -> the fields inside it that are declared to hold paths
TARGETS = {
    "brain_v2/methods/algorithms.json": ["bound_in"],
    "brain_v2/methods/asset_registry.json": ["path", "bound_in", "produced_by_tool"],
    "brain_v2/methods/model_maturity_methods.json": ["scripted_as", "tool", "bound_in"],
    "brain_v2/installation/installation.json": ["path", "built_by"],
    "brain_v2/system_profile/profile_concept.json": ["path", "built_by"],
}
# sections that describe the SCHEMA rather than instances of it
SCHEMA_DOC = ("_fields", "_legend", "_schema", "_doctrine")
PATHLIKE = re.compile(r"\.(py|json|md|db|sqlite|html|jsonl|docx)\b")


def walk(node, keys, trail=""):
    """Yield (location, value) for every declared path field, skipping schema docs."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in SCHEMA_DOC:
                continue
            if k in keys:
                vals = [v] if isinstance(v, str) else (v if isinstance(v, list) else [])
                for x in vals:
                    if isinstance(x, str):
                        yield f"{trail}/{k}", x
            yield from walk(v, keys, f"{trail}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, keys, f"{trail}[{i}]")


def main():
    prose, dead, checked = [], [], 0
    for store, keys in TARGETS.items():
        f = REPO / store
        if not f.exists():
            continue
        data = json.load(open(f, encoding="utf-8"))
        for where, raw in walk(data, set(keys)):
            checked += 1
            # "path (note)" is an accepted form — the note follows the path
            val = raw.split(" (")[0].strip()
            if not PATHLIKE.search(val):
                prose.append((store, where, raw))
            elif not (REPO / val).exists():
                dead.append((store, where, val))

    print(f"[paths] {checked} declared path field(s) across {len(TARGETS)} store(s)")
    for store, where, raw in prose:
        print(f"  PROSE      {store}{where}\n             {raw!r}")
    for store, where, val in dead:
        print(f"  DEAD PATH  {store}{where}\n             {val}")

    if prose or dead:
        print(f"\n  FAIL — {len(prose)} prose, {len(dead)} dead. A path field that does not "
              f"hold a path makes every check over it silently wrong.")
        return 1
    print("  OK — every declared path holds a real path on disk")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
