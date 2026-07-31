"""improve_algorithms.py — the continuous-improvement mechanism for ALGORITHMS (s097).

A catalogue tells you what exists. Golden cases stop regressions. Neither answers the
question that actually matters: **which algorithm should I improve next, and why that one?**

Without an answer, improvement goes wherever attention happens to fall — which is how
Treasury ended up with fifteen assets for 98K executions while the busiest domain had none.

Five measured signals, each mapping to a different kind of decay:

  1. FRONTIER TREND      is the algorithm explaining MORE over time? A frontier that stops
                         moving means the discovery loop stopped running. This is the only
                         signal that detects an algorithm quietly ceasing to learn.
  2. STALE LEVER         an `improve` line unchanged for many sessions is either finished
                         or abandoned. Both need a decision; neither should sit.
  3. UNGUARDED           an algorithm with no golden case can regress silently. The
                         classifier ran for months, wrong at scale, and never errored.
  4. UNEXERCISED         declared, bound to a tool, and the tool is not run. A5 (the only
                         algorithm that LEARNS) has not run since the strongest signal it
                         could consume came into existence.
  5. FAILURE-MODE DEBT   an algorithm whose declared failure mode has actually occurred and
                         whose fix has not been made structural.

The output is a ranked worklist, not a score. A score invites admiring the number.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent

ALGOS = HERE / "algorithms.json"
VALIDATORS = [HERE / "validate_algorithms.py", HERE / "validate_artifacts.py"]
EMAP = BRAIN / "executed_objects_domain_map.json"
STATE = HERE / "algorithm_improvement_state.json"

# state -> how urgently it wants attention. FRAGILE outranks MISSING deliberately: a
# fragile algorithm is load-bearing NOW, a missing one is a gap we already survived.
STATE_WEIGHT = {"FRAGILE": 5, "MISSING": 4, "WEAK": 4, "UNDER_EXERCISED": 3,
                "WORKS": 2, "STRONG": 1}


def _load(p, d=None):
    return json.load(open(p, encoding="utf-8")) if p.exists() else (d if d is not None else {})


def main():
    algos = _load(ALGOS).get("algorithms", {})
    hist = _load(STATE, {})
    prev = hist.get("last", {})

    # Which algorithms are guarded by a golden case. BOTH harnesses count: one guards the
    # pure functions, the other the artifacts they produce. Reading only the first is why
    # this reported 3 guarded when 17 were — and an improvement mechanism that misreads its
    # own coverage sends you to fix the wrong thing.
    guarded = set()
    text = "".join(v.read_text(encoding="utf-8", errors="replace")
                   for v in VALIDATORS if v.exists())
    for aid in algos:
        token = aid.split("_")[0]                          # A4, C1, E4 ...
        if re.search(r"\b" + re.escape(token) + r"\b", text):
            guarded.add(aid)

    # frontier trend — the only signal that catches an algorithm that stopped learning
    emap = _load(EMAP)
    frontier = (emap.get("by_domain", {}).get("Uncatalogued", {}) or {}).get("total_execs", 0)
    prev_frontier = prev.get("frontier")
    if prev_frontier is None:
        trend = "baseline"
    elif frontier < prev_frontier:
        trend = f"shrinking ({prev_frontier:,} -> {frontier:,})"
    elif frontier > prev_frontier:
        trend = f"GROWING ({prev_frontier:,} -> {frontier:,}) — the system changed or the algorithm decayed"
    else:
        trend = f"FLAT at {frontier:,} — a frontier that stops moving means discovery stopped"

    prev_levers = prev.get("levers", {})
    work = []
    for aid, a in algos.items():
        score, reasons = STATE_WEIGHT.get(a.get("state"), 2), []
        st = a.get("state")
        if st in ("FRAGILE", "MISSING", "WEAK", "UNDER_EXERCISED"):
            reasons.append(f"state {st}")

        if aid not in guarded:
            score += 3
            reasons.append("NO GOLDEN CASE — it can regress silently")

        lever = a.get("improve")
        seen = prev_levers.get(aid, {})
        if lever and seen.get("lever") == lever:
            n = seen.get("unchanged_for", 0) + 1
            if n >= 3:
                score += 2
                reasons.append(f"lever unchanged for {n} runs — finished or abandoned, decide")
        else:
            n = 0

        if a.get("operates_on") == "logs" and trend.startswith("FLAT"):
            score += 2
            reasons.append("operates on logs and the frontier is flat")

        if not a.get("failure_mode"):
            score += 2
            reasons.append("NO DECLARED FAILURE MODE — cannot be reviewed")

        work.append({"algorithm": aid, "priority": score, "state": st,
                     "operates_on": a.get("operates_on"), "origin": a.get("origin"),
                     "guarded": aid in guarded, "lever": lever,
                     "lever_unchanged_for": n, "reasons": reasons})

    work.sort(key=lambda x: (-x["priority"], x["algorithm"]))

    out = {
        "_generated_by": "brain_v2/methods/improve_algorithms.py",
        "_question_it_answers": "which algorithm do I improve next, and why that one?",
        "frontier_trend": trend,
        "coverage": {"algorithms": len(algos), "with_golden_case": len(guarded),
                     "unguarded": sorted(set(algos) - guarded)},
        "worklist": work,
    }
    json.dump(out, open(HERE / "algorithm_improvement.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    hist.setdefault("history", []).append({"frontier": frontier})
    hist["history"] = hist["history"][-20:]
    hist["last"] = {"frontier": frontier,
                    "levers": {w["algorithm"]: {"lever": w["lever"],
                                                "unchanged_for": w["lever_unchanged_for"]}
                               for w in work}}
    json.dump(hist, open(STATE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[algorithm improvement] {len(algos)} algorithms · "
          f"{len(guarded)} guarded by a golden case")
    print(f"  frontier: {trend}")
    print("\n  NEXT TO IMPROVE:")
    for w in work[:6]:
        print(f"    [{w['priority']:>2}] {w['algorithm']:34s} {w['state'] or '?':16s} "
              f"{'guarded' if w['guarded'] else 'UNGUARDED'}")
        for r in w["reasons"][:2]:
            print(f"         - {r}")


if __name__ == "__main__":
    main()
