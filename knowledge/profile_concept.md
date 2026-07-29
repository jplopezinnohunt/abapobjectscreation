---
name: PROFILE — a first-class concept in the brain (Layer 16)
description: The PROFILE is what the TENANT IS (installed / configured / productive per module, org structure, operating model, add-ons, front-end, users). The capability model is what WE KNOW about it. The delta between the two is the backlog. Created s097 after a scope question the brain could not answer.
type: project
---

# PROFILE — Layer 16

**One line:** the capability model says *what we know*; the profile says *what the system is*.
Neither replaces the other, and **the delta between them is the work**.

## Why it exists

An external Business Process Review asked a question that should have been trivial:

> *Which SAP functional modules and components are currently implemented, and which are
> actively used in production?*

The brain could not answer it. It held the **HOW** — the operating model (80.6% of business
traffic orchestrated by external satellites), 37 integration flows, per-flow detail. It held
**our knowledge** — the capability model, domain × 11 capabilities. It did not hold the
**WHAT**: the tenant's own footprint.

So the answer was re-derived live from the component list and the audit log, and it was wrong
on six modules — RE-FX, SD, FI-AA, PM, TRM, PBC — plus an entire missing category, the
third-party add-ons. The user had to correct it twice.

**The diagnosis is the important part.** Those six were not *unknown*. They were *unaddressed*:

| Module | Where it already lived | Why it stayed invisible |
|---|---|---|
| PBC | described as an "engine" inside the operating-model doc | an *engine* is not a *module* — invisible to a module-shaped question |
| RE-FX | had its own `knowledge/domains/RE-FX/` folder | no module keyed on it |
| add-ons | had a companion (`epiuse_companion.html`) | not reachable from a scope question |
| SD, FI-AA, PM, TRM | measurable in one probe | nobody had ever asked |

> **A store you cannot query by the question you are asked is not knowledge. It is storage.**

A new concept earns its place when a whole *class* of question has no home.
*"What is this tenant?"* is that class.

## What a profile is

The measured reality of **one** tenant landscape, in three strata:

1. **Footprint** — installed / configured / productive per module, plus org structure.
   Cheap, factual, and what external parties always ask for first.
2. **Operation** — how it is actually run: channel mix, who orchestrates, read vs write.
   This is where the 80.6%-external headline lives.
3. **Periphery** — third-party add-ons, the digital front-end (OData/Fiori), users and
   licences, and every channel through which data **exits**. Systematically forgotten, and
   the richest material for a governance conversation.

Keyed on the **SAP application component** (`FI-AA-AA`, `PA-PM-PB`, `RE-FX-CN`…) — deliberately
a different axis from the capability model's canonical domain key. Component names are resolved
from the system (`TADIR → TDEVC → DF14L`), never from memory.

## Evidence tiers — the ambiguity that caused the failure

Every module carries a tier **and** its evidence. "Implemented" on its own is the ambiguity
that produced six wrong verdicts.

| Tier | Meaning |
|---|---|
| `INSTALLED` | present in the component list. Near-meaningless alone — 177 are installed and most ship by default |
| `CONFIGURED` | organisational structure exists |
| `PRODUCTIVE` | business documents exist and/or transactions execute |
| `NOT_USED` | probed, and zero. An **asserted negative** |
| `NOT_EVIDENCED` | no evidence either way. **Never** collapse this into `NOT_USED` |

Extent is a *separate* axis (`adoption`: FULL / PARTIAL / MARGINAL). The tier answers
*"how do we know?"*; adoption answers *"how far is it rolled out?"*. Collapsing them produced
statuses like "PARTIAL" that mean neither — caught by the invariant gate on its first run.

## The interrelations — why this is a spine, not a leaf

The profile's value is not the fact-sheet. It is the **crossing**, precomputed by
`build_profile_links.py`:

```
profile.module ──explicit lookup──▶ ontology.canonical_key ──▶ capability_model cells
      │                                                              │
      ├──▶ claims (evidence trail)                                   │
      ├──▶ knowledge/domains/<x>/ (prose layer)                      │
      ├──▶ companions/*.html (visual layer)                          │
      └──▶ technical component (TADIR→TDEVC→DF14L)                   │
                                                                     ▼
                                              PRODUCTIVE × no capability row
                                                          =
                                              SYSTEM-LEVEL BLIND SPOT
```

Every link is an explicit **lookup**, never a fuzzy token match — `ontology.json` already had
to correct that mistake once, and we do not repeat it.

### The gap it exposes

A **system-level blind spot** is a module the tenant runs *in production* that our operating
model has never examined. This is a different and more expensive animal than the object-level
blind spots of Layer 12, which are merely names mentioned without a graph node.

First run, unprompted, the crossing returned:

```
modules 21 · productive 16 · with capability row 10 · with knowledge doc 6
SYSTEM-LEVEL BLIND SPOTS (6): CO, FI_AA, PM, SD, TRM, PBC
```

**Those are exactly the six modules the conversation got wrong.** The mechanism reproduced the
failure independently, from structure alone. That is the test that the concept is real: it
finds the error without being told where to look.

## Invariants (gated — the rebuild fails loud)

- **I1** every module carries a tier *and* an evidence string
- **I2** `NOT_USED` requires an actual probe. Absence in the Gold DB or in the execution map is
  a **floor, never an inventory** → that yields `NOT_EVIDENCED`
- **I3** technical component names resolved from the system, never from memory
- **I4** the profile renders into `BRAIN_INDEX.md` at bootstrap. **If a session has to
  re-derive the footprint, the profile has failed** — fix the profile, don't answer from scratch
- **I5** the profile is tenant-scoped; the *concept* and the *scripts* are portable, the
  contents are not

## Where it lives

| Artifact | Role |
|---|---|
| `brain_v2/system_profile/profile_concept.json` | the concept, tiers, interrelations, invariants |
| `brain_v2/system_profile/unesco_system_profile.json` | the tenant instance (facts + evidence) |
| `brain_v2/system_profile/build_profile_links.py` | the crossing + the invariant gate |
| `brain_v2/system_profile/profile_links.json` | generated: links + gap report |
| `brain_state.system_profile` | **Layer 16**, with `_concept` and `_links` attached |
| `BRAIN_INDEX.md` | rendered at bootstrap — read before any scope answer |

**Query:** `python brain_v2/graph_queries.py profile [module]`
**Rebuild:** step 2c of `rebuild_all.py`, before `build_brain_state.py`.

## Rule

`feedback_profile_first_never_rederive_the_footprint` (#171) — read the profile before
answering any scope question. If it lacks the answer, probe read-only and **write the result
back into the profile**; never leave a new fact in the conversation.

Related: [[feedback_capability_model_is_the_operating_model]] ·
[[feedback_promote_conversational_knowledge_to_central_store]] ·
[[feedback_knowledge_becomes_useful_via_structured_records]]
