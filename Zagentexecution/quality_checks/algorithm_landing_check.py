"""Every algorithm that produces findings must say where they land.

WHY THIS EXISTS
---------------
`lands_in` was added to the algorithm registry in s099, for the rule that discovering
something and not landing it is a total loss. It reached 3 of 43 algorithms. The other 40
were SILENT -- and silence hid two very different situations:

  a read technique produces DATA, there is nothing to land          -> fine
  a detector produces FINDINGS and nobody said where they go        -> the loss

You could not tell them apart, so neither could be acted on. Classifying each by its own
`does` text gave: 8 techniques (declared n/a), 5 landings derivable from `bound_in`, and
**27 discovery algorithms with no store named**. That is the real debt, now explicit.

It is deliberately NOT a hard red. 27 permanent failures would train everyone to ignore this
check, which is how a gate becomes furniture. So it ratchets like the other standing
populations: it fails when the number GROWS. A new algorithm cannot be registered without
declaring its landing, and every one that gets declared locks the baseline lower.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "datos_sap",  # datos_sap | conocimiento | herramientas
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": "every discovery algorithm must name the store its findings land in",
}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline import verdict  # noqa: E402  (sibling module)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
ALGOS = REPO / "brain_v2" / "methods" / "algorithms.json"
UNDECLARED = "UNDECLARED"


def main():
    if not ALGOS.exists():
        print("SKIPPED - algorithms.json not found. Not a pass: nothing was verified.")
        return 3

    raw = json.loads(ALGOS.read_text(encoding="utf-8"))
    container = raw.get("algorithms", raw)
    items = (container if isinstance(container, list)
             else [{"id": k, **v} for k, v in container.items() if isinstance(v, dict)])

    silent, undeclared = [], []
    for it in items:
        land = it.get("lands_in")
        if not land:
            silent.append(it.get("id"))
        elif UNDECLARED in str(land):
            undeclared.append(it.get("id"))

    print("=" * 74)
    print("algorithm landing - can what each one discovers actually go somewhere?")
    print("=" * 74)
    print("algorithms: {}".format(len(items)))
    print("  silent (no lands_in at all): {}".format(len(silent)))
    print("  explicitly UNDECLARED:       {}".format(len(undeclared)))

    for a in silent:
        print("  [SILENT] {} - no lands_in. Classify it: technique (n/a) or discovery "
              "(name the store).".format(a))
    if undeclared:
        print()
        print("  discovery algorithms still owing a store:")
        for a in undeclared:
            print("    - {}".format(a))

    # A silent one is worse than an UNDECLARED one: UNDECLARED is a decision recorded,
    # silence is a decision never made. Both count, silence is reported separately.
    total = len(silent) + len(undeclared)
    return verdict("algorithms_without_a_landing", total, "algorithms owing a landing",
                   "A discovery with nowhere to go is a discovery lost (CP-001).")


if __name__ == "__main__":
    sys.exit(main())
