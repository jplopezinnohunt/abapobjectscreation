---
name: PLAN — how to improve the algorithms, in order, and why that order
description: Derived from the improvement mechanism's own ranking rather than from judgement. The dominant term in every score is "no golden case", which changes what the first move is. Created s097.
type: project
---

# Improvement plan

**Derived, not decided.** `improve_algorithms.py` ranks 25 algorithms from five measured
signals. Reading its output, one term dominates every single entry:

```
25 algorithms · 3 guarded by a golden case
frontier: FLAT at 875,332 — a frontier that stops moving means discovery stopped

[10] A2_rolling_window_accumulation   FRAGILE   UNGUARDED
[ 8] A5_adaptive_learning_loop        UNDER_EXERCISED  UNGUARDED
[ 7] A4_ordered_classifier_ladder     WORKS     UNGUARDED
...every entry: NO GOLDEN CASE — it can regress silently
```

**That changes what the first move is.** The instinct is to improve the weakest algorithm.
The measurement says something else: **22 of 25 algorithms cannot be changed safely.** Any
improvement is a gamble, because a subtly wrong algorithm produces confident, plausible,
wrong output and never errors — which is precisely how a classifier filed 19,524 Project
System executions under Controlling for months.

So the first move is not improvement. It is making improvement *safe*.

---

## Step 0 — Protect A2. It cannot be fixed by code.

`A2_rolling_window_accumulation` ranks first at score 10: **FRAGILE and unguarded**. It is
the input to drift, to the operating model, to usage per domain — to every temporal claim
the model makes.

It writes to a 13.28 GB gitignored database with **no confirmed backup**, and its value is
the one thing that cannot be recovered by working harder later: a day not captured is gone.

Nothing below matters if this is lost. This is the only step that requires a decision
rather than code.

---

## Step 1 — Golden cases for the 22 unguarded algorithms

**The enabler.** Not glamorous, and it is what makes every later step possible.

A case is not a guess about what should happen — it is a fact established the hard way.
The 43 that exist all came from real defects. The pattern to repeat:

| algorithm | the case to write |
|---|---|
| A2 accumulator | a known day's row count must be reproducible from the history tables |
| A4 classifier | the CO/PS confusion is already covered by C1 — add a case per rung, so a rung failing is distinguishable from a mapping failing |
| A7 drift | the two defects it found in itself: unequal months must not produce a signal; a two-month baseline must not produce a z-score |
| F1 boundary | a destination known to be live must not be reported DEAD |
| F2 satellites | the MuleSoft fleet must be recovered as ONE satellite, not split by GUID truncation |
| B4 conformance | the measured P2P figures (38% conformant, 70 violations) must be reproducible |

**Rule to adopt:** a fix without a case is not a fix. Applies from now, not retroactively.

---

## Step 2 — The frontier is FLAT. Run A5 with the component signal.

`frontier: FLAT at 875,332` is the mechanism reporting that **discovery has stopped**. Not
that the remainder is small — that it is not moving.

`A5_adaptive_learning_loop` is the only algorithm that learns: it resolves unknowns,
**learns the resolution**, and re-classifies until it converges. It has not run since the
component chain existed, so it is learning blind to the strongest signal we now have.

Feed it the component and the custom overlay as inputs, run it, and measure whether the
frontier moves. If it does not, the frontier's remaining 875,332 executions are genuinely
opaque and that is worth knowing precisely.

---

## Step 3 — C3 static edges: 98 of 1,212 objects

`C3_static_edge_extraction` is WEAK and it is a **low layer**, which by the nesting DAG
means improving it lifts everything above:

- **impact analysis** — with 8% edge coverage, "nothing depends on this" is the most
  dangerous possible false negative;
- **the LLM overlay derivation in step 4** — its strongest signal is what an object reads
  and writes, and today that exists for 8% of objects;
- **domain discovery** — a domain's real footprint is what its objects touch.

---

## Step 4 — Derive the custom overlay. The portability blocker.

**Measured:** 22.7% of resolved executions are tenant-invariant. 2,617,419 executions rest
on 334 hand-curated entries that do **not** travel to installation #2.

Not a defect to delete — custom Z/Y objects have no SAP component *by definition*, and
they are where the differentiating processes live. The move is to **derive** the mapping
from each object's reads/writes, name, text, function group and callers, instead of
curating it.

**It has a ready-made test set:** the 334 curated entries. The derivation must reproduce
them before it is trusted anywhere. That is a rare luxury — most algorithms have no ground
truth at all.

Enters at confidence 0.60 or lower, never as an authoritative answer.

---

## Step 5 — The flow chain. This is the product.

Blocked at the first link, and each link unblocks the next:

```
event log definitions   (buried today as configs inside a script)
        ↓
B2C2A event log         (object-centric — the case notion is genuinely ambiguous:
                         one budget, many commitments, many actuals)
        ↓
DECLARE constraint mining   (mine candidates → rank → HUMAN confirms)
        ↓
conformance against the normative model   (already authored: 5 rules for B2C2A)
```

The normative models are written. The conformance algorithm is proven on P2P. **What is
missing is the event log** — and that is the whole reason the most important flow in the
tenant is unmined.

---

## Continuous — what turns the crank

- `run_analysis_cycle.py` runs every analysis algorithm in dependency order. It closes the
  "nobody demands it" hole — but the runner itself is still on demand. **Schedule it.**
- Watch the **frontier trend**, not its size. A frontier that stops moving means the
  discovery loop stopped, and nothing else detects that.
- Per close: `improve_algorithms` → take the top entry → move one state upward.

---

## The order, and the one sentence for why

**0 backup · 1 golden cases · 2 run A5 · 3 C3 edges · 4 derive the overlay · 5 the flow chain.**

Steps 1–3 are low in the nesting DAG and cheap; step 4 is the measured blocker on
portability; step 5 is where the product value is and it is blocked on a single missing
artifact.

**And the reason step 1 comes before any actual improvement:** you cannot improve
deliberately what you cannot change safely.
