"""UNLANDED DISCOVERIES — the leak detector. Finding something and not recording it is loss.

WHY (s099, JP)
--------------
"Descubrir y no aterrizar es una perdida enorme. Debe ser parte fundamental de todos los
algoritmos, agentes, rebuild."

Every session discovers things. In s099 alone the code reading surfaced YXUSER — a table
that switches OFF two blocking validations and three field-forcing substitutions for any
user listed in it — and YVENDOR_PAYM_REF, the maintained list that decides the text a bank
sees on a payment. Both sat inside the posting perimeter. Neither had a single brain record.
They were found by reading code, reported in a conversation, and would have evaporated when
the conversation ended. That is the loss.

A promise not to forget is not a control. This is the control: it MEASURES the leak, names
every leaking item, and runs inside the pipeline so it cannot be skipped.

WHAT IT MEASURES
----------------
An UNLANDED DISCOVERY is a custom (Y*/Z*) object or table that:
  * the code demonstrably touches — it appears in N parsed routines, and
  * the brain cannot explain — no claim, incident, annotation or registry entry names it.

The code proves it matters. The brain proves we never wrote it down. The gap between the
two IS the leak, and it is countable.

THE RULE IT ENFORCES
--------------------
Every algorithm that produces findings must declare `lands_in` — the store where those
findings become durable. An algorithm that only prints is a leak by construction.

Output: brain_v2/methods/unlanded_discoveries.json
Exit code 1 when the leak GREW against the recorded baseline — not when a leak merely
exists, because naming a gap is progress and punishing it would teach the wrong lesson.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
BRAIN = HERE.parent
REPO = BRAIN.parent
OUT = HERE / "unlanded_discoveries.json"

MIN_ROUTINES = 2   # touched once could be incidental; twice is a pattern


def load(rel):
    p = REPO / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def main():
    interp = load("brain_v2/code_interpretation.json")
    if not interp:
        print("code_interpretation.json missing — run brain_v2/interpret_code.py first")
        return 0

    gaps = {g["term"]: g["seen_in_routines"]
            for g in (interp.get("_top_gaps_OURS") or [])
            if g["seen_in_routines"] >= MIN_ROUTINES}

    # Where each leaking term is touched, so the finding is actionable and not a bare name.
    secs = load("brain_v2/code_sections.json") or {}
    where = {}
    for obj, o in (secs.get("objects") or {}).items():
        for s in o.get("sections", []):
            for t in set(s.get("reads_tables", []) + s.get("writes_tables", [])
                         + s.get("calls_fms", [])):
                if t in gaps:
                    where.setdefault(t, []).append({
                        "object": obj, "routine": s["routine"],
                        "lines": f'{s["start_line"]}-{s["end_line"]}',
                        "role": s["role"], "blocks": s["can_block_posting"],
                    })

    items = []
    for term, n in sorted(gaps.items(), key=lambda x: -x[1]):
        sites = where.get(term, [])
        blocking = [s for s in sites if s["blocks"]]
        items.append({
            "term": term,
            "seen_in_routines": n,
            "touched_by": sites[:8],
            "gates_a_blocking_routine": bool(blocking),
            "severity": "HIGH" if blocking else ("MEDIUM" if n >= 4 else "LOW"),
            "lands_in": "brain_v2/claims/claims.json (a claim naming it), or "
                        "brain_v2/gold_table_registry.json if it is a table worth extracting",
        })

    high = [i for i in items if i["severity"] == "HIGH"]
    prev = load("brain_v2/methods/unlanded_discoveries.json") or {}
    baseline = prev.get("_count")

    doc = {
        "_generated_by": "brain_v2/methods/unlanded_discoveries.py",
        "_what_this_is": (
            "custom Y*/Z* objects the CODE touches that the BRAIN cannot explain — the "
            "measurable form of 'discovered and never written down'"),
        "_why": (
            "a promise not to forget is not a control; this counts the leak, names every "
            "item, and runs inside rebuild_all so it cannot be skipped"),
        "_the_rule": (
            "every algorithm that produces findings declares `lands_in`. An algorithm that "
            "only prints is a leak by construction."),
        "_count": len(items),
        "_high": len(high),
        "_baseline_previous_run": baseline,
        "_min_routines_to_count": MIN_ROUTINES,
        "items": items,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[unlanded discoveries] {len(items)} custom identifiers the code touches "
          f"and the brain cannot explain")
    for i in items[:12]:
        flag = "  <== gates a BLOCKING routine" if i["gates_a_blocking_routine"] else ""
        site = i["touched_by"][0] if i["touched_by"] else {}
        print(f"   [{i['severity']:6}] {i['term']:24} {i['seen_in_routines']:>2} routines"
              f"  e.g. {site.get('object','?')}::{site.get('routine','?')}{flag}")
    if len(items) > 12:
        print(f"   (+{len(items) - 12} more in {OUT.name})")

    if baseline is not None and len(items) > baseline:
        print(f"\nLEAK GREW: {baseline} -> {len(items)}. Something was discovered this "
              f"session and not written down. Land it in a claim before closing.",
              file=sys.stderr)
        return 1
    if baseline is None:
        print(f"\n  baseline recorded at {len(items)}; a future run that exceeds it fails")
    else:
        print(f"\n  OK — leak did not grow ({baseline} -> {len(items)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
