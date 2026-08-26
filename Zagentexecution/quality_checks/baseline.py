"""Give a standing population an honest verdict: fail when it GROWS, not when it exists.

THE PROBLEM THIS SOLVES
-----------------------
Three of the gate checks measure a known, large, standing condition -- 22 blocking FM/PS
misalignments, 1,232 at-risk AVC buckets, hundreds of Budget Rate line inconsistencies.
They printed all of it and exited 0, so the runner could not tell clean from dirty (UNGATED).

The obvious fix -- exit 1 whenever there is any finding -- is worse. Every rebuild would go
red forever, and a gate that is always red is a gate everyone learns to ignore. Alarm fatigue
is not rigour.

So the verdict is a DELTA against a recorded baseline, the same pattern
brain_v2/methods/unlanded_discoveries.py already uses: the leak failing when it grows, not
when it exists.

  count > baseline   FINDING (exit 1) -- it got worse, and by how much
  count < baseline   PASS, and the baseline RATCHETS DOWN so the improvement locks in
                     and cannot silently regress back to the old number
  count == baseline  PASS
  no baseline yet    exit 0, baseline recorded -- and printed as "recorded", never as
                     "clean", because a first run has nothing to compare against

Baselines live in brain_v2/quality_baselines.json, git-tracked, so the ratchet is a fact
about the repo rather than a fact about one machine.
"""
QUALITY_CHECK = {
    "tier": "library",
    "sobre": "datos_sap",  # datos_sap | conocimiento | herramientas
    "needs": "files",
    "what": "shared verdict helper - not a check, never run on its own",
}

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "brain_v2" / "quality_baselines.json"


def _load():
    if STORE.exists():
        try:
            return json.loads(STORE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save(data):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                     encoding="utf-8")


def verdict(name, count, unit="findings", note=""):
    """Compare `count` against the recorded baseline for `name`. Returns an exit code.

    Call it as the last thing a check does:  return verdict("my_check", len(rows))
    """
    # Write through the CALLER's sys.stdout. Wrapping sys.stdout.buffer in a second
    # TextIOWrapper here swallowed the entire report: the caller's wrapper still held its
    # lines unflushed, this one closed the shared buffer on the way out, and everything but
    # the verdict was discarded. The checks were hiding their own findings -- the exact
    # failure they exist to catch.
    w = sys.stdout

    data = _load()
    entry = data.get(name)
    print("\n" + "-" * 70, file=w)

    if entry is None:
        data[name] = {"baseline": count, "unit": unit, "note": note}
        _save(data)
        print(f"BASELINE RECORDED for {name}: {count:,} {unit}.", file=w)
        print("This is NOT a pass — a first run has nothing to compare against. The next "
              "run fails if this number grows.", file=w)
        w.flush()
        return 0

    base = entry.get("baseline", 0)
    if count > base:
        print(f"FINDING — {name} GREW: {base:,} -> {count:,} {unit} (+{count - base:,}).",
              file=w)
        if note:
            print(f"  {note}", file=w)
        w.flush()
        return 1

    if count < base:
        data[name] = {**entry, "baseline": count, "unit": unit,
                      "note": note or entry.get("note", ""),
                      "previous_baseline": base}
        _save(data)
        print(f"IMPROVED — {name}: {base:,} -> {count:,} {unit} ({count - base:,}). "
              f"Baseline ratcheted down; it cannot drift back up unnoticed.", file=w)
        w.flush()
        return 0

    print(f"PASS — {name} unchanged at {count:,} {unit}.", file=w)
    print("  Unchanged is not the same as fixed: this is a standing population, held flat.",
          file=w)
    w.flush()
    return 0
