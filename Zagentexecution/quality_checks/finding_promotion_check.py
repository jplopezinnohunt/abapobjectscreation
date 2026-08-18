"""Did what the algorithms discovered ever reach the brain, or did it stop in its own JSON?

WHY THIS EXISTS
---------------
s099 made every algorithm declare `lands_in` -- the dataset it computes AND the store its
findings have to reach. That closed the silence. It did not close the loop, because a
DECLARATION IS NOT AN EXECUTION: brain_v2/drift_signals.json can hold forty flagged months
and the brain can hold zero claims explaining any of them, and nothing today notices.

That is the discovery-without-landing failure in its final hiding place. The algorithm ran,
the dataset is fat, the field says where the findings belong, and no finding ever went there.
Every earlier check would pass.

So this measures the distance between the two:

    dataset volume        how much the algorithm found
    promotion references  how many claims cite that dataset or that algorithm

A fat dataset with zero citations is a discovery that never became knowledge. It is not proof
of neglect on its own -- a dataset can legitimately be an input to another step -- which is
why the finding names the algorithm and lets a human judge, and why it ratchets instead of
going red forever.

Deliberately NOT measured: whether the claims are good. Only whether the path from finding to
store was ever walked.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

QUALITY_CHECK = {
    "tier": "gate",      # gate | live | analysis | quarantined
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": "a fat dataset with no claim citing it is a discovery that never landed",
}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline import verdict  # noqa: E402  (sibling module)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
ALGOS = REPO / "brain_v2" / "methods" / "algorithms.json"
CLAIMS = REPO / "brain_v2" / "claims" / "claims.json"

# below this a dataset is too thin to expect a claim from it
FAT = 5


def volume(path):
    """How many findings does this dataset hold? None if it cannot be read."""
    p = REPO / path
    if not p.exists() or p.suffix != ".json":
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        # the biggest list or dict inside is the payload; metadata keys are small
        best = 0
        for v in data.values():
            if isinstance(v, (list, dict)):
                best = max(best, len(v))
        return best or len(data)
    return None


def datasets_of(algo):
    """The dataset paths named in lands_in, before the '-> store' arrow."""
    land = str(algo.get("lands_in") or "")
    if algo.get("lands_in_kind") != "discovery" or "->" not in land:
        return []
    head = land.split("->")[0]
    head = head.replace("(dataset)", "")
    out = []
    for part in head.split("+"):
        part = part.strip().rstrip("/").strip()
        if part.endswith(".json"):
            out.append(part)
    return out


def main():
    if not ALGOS.exists() or not CLAIMS.exists():
        print("SKIPPED - algorithms.json or claims.json missing. Not a pass: nothing verified.")
        return 3

    raw = json.loads(ALGOS.read_text(encoding="utf-8"))
    container = raw.get("algorithms", raw)
    algos = (container if isinstance(container, list)
             else [{"id": k, **v} for k, v in container.items() if isinstance(v, dict)])

    claims_blob = CLAIMS.read_text(encoding="utf-8").lower()

    print("=" * 76)
    print("finding promotion - did the discoveries reach the brain, or stop in their JSON?")
    print("=" * 76)

    stranded, thin, promoted, unreadable = [], 0, 0, 0
    for a in algos:
        for ds in datasets_of(a):
            n = volume(ds)
            if n is None:
                unreadable += 1
                continue
            # cited by filename, by full path, or by the algorithm's own id
            name = Path(ds).name.lower()
            cited = (name in claims_blob or ds.lower() in claims_blob
                     or str(a.get("id", "")).lower() in claims_blob)
            if cited:
                promoted += 1
            elif n >= FAT:
                stranded.append((a.get("id"), ds, n))
            else:
                thin += 1

    print("datasets cited by at least one claim: {}".format(promoted))
    print("datasets too thin to expect a claim (<{} findings): {}".format(FAT, thin))
    print("datasets that could not be read: {}".format(unreadable))
    print("STRANDED - findings with no claim citing them: {}".format(len(stranded)))

    if stranded:
        print()
        for aid, ds, n in sorted(stranded, key=lambda x: -x[2]):
            print("  [STRANDED] {:34} {:>6} findings  {}".format(aid, n, ds))
        print()
        print("Each ran, produced findings, and nothing was promoted to a claim. Either")
        print("promote what matters, or say in lands_in why this dataset is an input to")
        print("another step rather than a source of knowledge.")

    return verdict("stranded_discovery_datasets", len(stranded), "stranded datasets",
                   "A declaration of where findings land is not evidence they landed.")


if __name__ == "__main__":
    sys.exit(main())
