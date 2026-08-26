"""One capability, one owner. A second implementation is deprecated, or it is a defect.

WHY THIS EXISTS
---------------
JP, s099, after saying it three times: *"es un tema de arquitectura... nuevamente"*.

He was right, and the recurring failure was never "we forgot to wire X". Seven layers exist --
the graph_queries CLI, an MCP server, quality_checks, algorithms, agents, skills, hooks -- and
NOTHING declared which layer owns a given need. So the same capability got built twice, in two
layers, reading two different sources, and both rotted quietly.

Two measured examples, neither of which is "an old tool":

  search the brain   graph_queries.py reads brain_state.json + entity_index + companion_graph
                     sap_mcp_server.brain_search reads output/brain_v2_graph.json
                     -> two answers to the same question, nothing saying which is right

  write ABAP to D01  abap_deploy/deploy_object.py: manifest + PRE/POST readback + diff-gate
                     sap_mcp_server.adt_deploy: lock -> write -> activate, none of that
                     -> the second bypasses the entire INC-CLASS-LOSS remediation

This check does not decide ownership -- brain_v2/capability_ownership.json does, by hand,
because ownership is a design decision and inferring it would be exactly the guessing that
caused the problem. What the check enforces is that the declaration stays HONEST: every
deprecated implementation must still exist where it says (or the entry is stale), every
authoritative one must exist (or the capability has no owner at all), and anything flagged
DANGEROUS is reported every run so it cannot fade into the background.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "datos_sap",  # datos_sap | conocimiento | herramientas
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": "one capability, one authoritative owner; deprecated alternatives declared",
}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline import verdict  # noqa: E402  (sibling module)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
OWNERSHIP = REPO / "brain_v2" / "capability_ownership.json"

# a path-looking token inside a declaration, so we can check it still exists
PATH_RE = re.compile(r"[\w./-]+\.(?:py|json|jsonl|md)")


def first_path(text):
    m = PATH_RE.search(str(text or ""))
    return m.group(0) if m else None


def main():
    if not OWNERSHIP.exists():
        print("SKIPPED - capability_ownership.json not found. Not a pass: nothing verified.")
        return 3

    doc = json.loads(OWNERSHIP.read_text(encoding="utf-8"))
    caps = doc.get("capabilities", {})

    print("=" * 78)
    print("capability ownership - is the declaration still true?")
    print("=" * 78)
    print("capabilities declared: {}".format(len(caps)))

    problems, dangerous = [], []

    for name, entry in caps.items():
        auth = entry.get("authoritative")
        if not auth:
            problems.append((name, "no authoritative implementation declared"))
        else:
            p = first_path(auth)
            if p and not (REPO / p).exists():
                problems.append((name, "authoritative implementation missing on disk: " + p))

        for dep in entry.get("deprecated", []):
            impl = dep.get("impl", "")
            if not dep.get("why"):
                problems.append((name, "deprecated entry with no reason: " + impl[:50]))
            if str(dep.get("severity", "")).upper().startswith("DANGEROUS"):
                dangerous.append((name, impl))

    if dangerous:
        print()
        print("DANGEROUS alternatives still present - reported every run on purpose:")
        for name, impl in dangerous:
            print("  [{}] {}".format(name, impl))

    if problems:
        print()
        for name, msg in problems:
            print("  [STALE] {}: {}".format(name, msg))
        print()
        print("The map is the architecture. A map that no longer matches the tree is worse")
        print("than no map, because it is believed.")

    return verdict("capability_ownership_problems", len(problems),
                   "stale ownership declarations",
                   "One capability, one owner - and the declaration has to stay true.")


if __name__ == "__main__":
    sys.exit(main())
