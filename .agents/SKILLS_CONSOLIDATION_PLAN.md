# Skills Consolidation — REJECTED

**Status:** REJECTED by user — Session #036 (2026-04-05)
**Decision owner:** JP Lopez

---

## Decision

**No merging of skills.** Knowledge preservation outweighs consolidation benefits.

## Why this plan was rejected

The original plan proposed merging 38 skills into 6 archetypes. A loss analysis
(Session #036) found unacceptable knowledge erosion risks:

1. **BCM domain knowledge** (`sap_payment_bcm_agent`, 728 lines: 13 PDFs, SAP Notes,
   FBZP chain, DMEE, workflow 90000003) would be diluted inside a generic "Miner"
   archetype — exactly when H13 needs it to ship.

2. **Company code copy runbook** (`sap_company_code_copy`, 41-task checklist,
   12 NR objects, copy inconsistency detection) is an operational protocol, not
   a generic deployment pattern. Flat-merging risks reinvention (as happened
   with STEM in #019).

3. **Domain routing semantics** — `coordinator` routes by UNESCO process
   (B2R/H2R/P2P/T2R/P2D). Flatten-merging the 3 domain agents + `sap_expert_core`
   into a monolithic "DomainExpert" loses this routing intent.

4. **Transport companion + integration diagram templates** are "explain SAP to
   humans" capabilities — a different intention than "deploy to SAP". Merging
   them into Deployer conflates intentions.

5. **CRP 19 open items** live inside `crp_fiori_app` SKILL.md. Deleting the
   skill without migrating these items = silent knowledge loss.

6. **Debugging vs Monitoring** are two distinct intentions. Debugging is forensic
   on a single failure (SU53, ST22 dumps, SM21 logs). Monitoring is state-over-time
   (SM04, SM37 backlog). Merging them degrades both.

7. **SKILL.md bodies contain unique knowledge** — code examples, known failures,
   edge case workarounds — that exists nowhere else. A verbatim merge would bloat
   each archetype; a summary merge would lose this content.

## What we do instead

### Principle: Skills grow — we do not force-shrink them
- Skills are the **memory** of what we learned. Merging them is lossy compression.
- The cost of having "too many skills" is navigation friction, not storage.
- The cost of losing a skill is an expensive rediscovery or a repeated bug.

### Adjustments to `session_preflight.py`
- Check 8 (skill count) relaxed: **40+ is WARN, 60+ is FAIL**, not 30+.
- Rationale: the bound should prevent runaway, not force consolidation.

### Governance (kept)
- New skills still require `skill_creator` rubric before creation.
- `SKILL_MATURITY.md` still scores each skill.
- Stubs that are truly unused (`abapgit_integration`, `notion_integration` — both
  29 sessions dormant) can be **individually deleted** with PMO entries, not
  bulk-merged.

### What stays in the PMO
- G55 (Skills Consolidation Execution) — **KILLED #036** (see PMO_BRAIN.md)
- Optional future item: "Individually evaluate 4 truly-unused skills for deletion"
  — only if they've been dormant 30+ sessions AND have zero knowledge unique to
  them. This is cleanup, not consolidation.

## What a new CTO would say

> "You're hoarding skills the same way you hoarded data." — The AGI retro agent

Fair critique. Counter-argument: **skill hoarding is cheap** (markdown files),
**data hoarding is expensive** (Gold DB bloat + extraction time). The cost
model is different. Skills are the cheap memory. Losing skill knowledge is
the expensive failure mode.

The H13 shipping failure is not caused by having 38 skills. It is caused by
not invoking `sap_payment_bcm_agent` to generate the report. The solution is
to **use** the skills, not to **merge** them.

---

## Decision log

| Date | Author | Decision |
|------|--------|----------|
| 2026-04-05 | Session #036 AI proposal | Proposed 38→6 merge |
| 2026-04-05 | JP Lopez | REJECTED — knowledge loss unacceptable |
| 2026-04-05 | Session #036 | Plan archived as rejected, `session_preflight.py` Check 8 relaxed, G55 killed |
