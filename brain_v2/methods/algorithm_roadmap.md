---
name: ALGORITHM ROADMAP — what to build next, from the current state of the field
description: What the market has today that we do not, filtered by our MEASURED gaps rather than by novelty. Deduped against the closed research base; names what was already refuted so we do not chase it. Created s097.
type: project
---

# Algorithm roadmap

**Method.** Deduped against `brain_v2/research/` before writing a line — the project rule
is not to re-assert what was refuted nor to re-research what is closed. The
object-centric research (`w3t7ufrbg`) already covers OCEL (34 references), conformance
(30), alignments (9) and predictive monitoring (8). It covers **nothing** on declarative
constraint mining, concept drift, LLM-assisted labelling or trace clustering.

So the honest split: three genuinely new techniques, and one **open question we already
have** that matters more than any of them.

---

## Do not chase these — already refuted or out of product scope

| | why not |
|---|---|
| **HOEG / graph neural networks** on object-centric event data | in the refuted set: the claims did not survive verification. It is also predictive monitoring, which is a *different product* from conformance — chasing it dilutes the thesis. |
| **OCPM² 12-stage methodology** | refuted. We already have a method; adopting a competing one is churn. |
| Reinventing DFG discovery, variants, alignments | pm4py is the reference implementation. Rebuilding it is vanity. |

---

## 1 · Declarative constraint mining (DECLARE / MP-Declare) — the sharpest fit

**Not in our research base at all**, and it is the technique that most closely matches
what we actually do.

**The insight:** public-sector finance is **rule-governed, not sequence-governed**. An
imperative process model ("PO then GR then IR") fits procurement. It does *not* fit budget
control, where the truth is a constraint: *no commitment may exceed available budget*, at
any point, regardless of sequence.

Look at the normative models we authored: every one is already a **declarative
constraint** in shape. We wrote them in the right form without naming the formalism.

**What the field adds that we do not have:** miners that *discover* candidate constraints
from an event log. Today we author every normative model by hand, which is the bottleneck
on the entire conformance product — it exists for exactly one flow.

**The move:** mine candidate constraints from the log → rank by support and confidence →
**a human confirms or rejects** → confirmed constraints become normative models. Semi-
automated moat instead of hand-written moat.

**Why this is defensible rather than derivative:** commercial tools ship imperative
reference models for commercial flows. Nobody ships declarative constraint sets for budget
control, because nobody has the public-sector content. The *algorithm* is the field's; the
*constraints it discovers here* are ours.

**Honest caveat:** declarative miners generate many trivially-true constraints. The
ranking and the human gate are the hard part, not the mining.

---

## 2 · LLM-assisted derivation for the custom overlay — attacks the measured blocker

**The measured problem:** 22.7% portability. 2,617,419 executions rest on 334 hand-curated
entries mapping custom objects to domains. That map does not travel to installation #2.

**Why it cannot simply be deleted:** custom Z/Y objects have **no SAP component by
definition**, and they are exactly where the differentiating processes live.

**The move — derive it instead of curating it.** For each custom object, assemble the
evidence we already hold: the tables it reads and writes, its function group, its callers,
its name, its transaction text. Propose a domain **with a confidence**, and have a human
confirm the low-confidence ones only.

The 2025-2026 pattern for exactly this is LLM-assisted labelling with human confirmation —
and the reason it fits here is that the signal is *semantic*, not structural: `ZHRCA_POSTAL_CODE_CHECK`
is obviously HR to a reader and invisible to a taxonomy.

**What actually travels:** the derivation. On the next tenant the *content* is different
and the *procedure* is identical — which is the definition of portable.

**Honest caveat:** an LLM label is a *hypothesis*, and it must enter the model at
`curated_overlay` confidence (0.60) or lower, never as an authoritative answer. The
calibration work done this session is the precondition that makes this safe.

---

## 3 · Concept drift detection — makes the interpretation trigger principled

**Not in our research base.**

Our interpretation triggers today are **threshold heuristics** I chose: frontier grows 5%,
a new company code appears, 30 days of new log. They work, but the thresholds are
judgement, not measurement — a declared weakness in `check_triggers.py`.

Concept drift detection is the formal version: detect *when the process changed*, from the
log itself, without a threshold.

**Why it matters specifically here:** a biennium organisation has a real, expected drift
at the biennium boundary — and any *unexpected* drift is exactly the finding worth having.
We already have the accumulator building history; drift detection is what turns that
history from a longer log into a signal.

---

## 4 · The open question that outranks all three

From our own research base, still open:

> **Does SAP ship machine-consumable normative reference process models** — Signavio
> Process Insights reference flows, SAP Best Practices content — that can serve as the
> as-delivered baseline?

This determines whether we **author** normative content or **consume** it. It is the
binding constraint on the whole conformance product: `S_STANDARD_REF` is the only
method-GAP dimension in the capability model, empty for every domain.

If SAP ships them: our work is mapping and delta, and the public-sector gap narrows to
what SAP does not cover (BCS/PBC/GM — probably still nothing).
If SAP does not: authoring is the moat, and technique #1 above is how we scale it.

**Either way the answer changes the plan, and we do not have it.** That makes it worth
more than any new algorithm.

The other open questions from the same research, still unanswered and still relevant:
change-document coverage for Z-namespace objects; the scalability ceiling of
object-centric discovery on industrial SAP logs; and how to surface BDC, BAdI and the
RFC/.NET layer as object-centric event sources.

---

## Order, and why

1. **Answer open question #4** — it is cheap (research, not build) and it re-plans everything else.
2. **#2 LLM-assisted derivation** — attacks the one gap we have *measured* as blocking portability.
3. **#1 declarative constraint mining** — unblocks the conformance product beyond one flow.
4. **#3 drift detection** — makes the loop principled; valuable but not blocking.

**The discipline that applies to all four:** none of them enters the model as an
authoritative answer. Each produces hypotheses at declared confidence, and the golden-case
harness gets a case before the technique is trusted. We learned that the expensive way —
a classifier ran for months, wrong at scale, and never errored once.
