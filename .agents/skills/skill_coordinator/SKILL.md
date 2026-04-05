---
name: skill_coordinator
description: Meta-agent that guards and grows the skill arsenal. Reasons about where new knowledge belongs — routes it into the correct existing skill (preferred) or proposes a new specialized skill (fallback). NEVER merges skills. Skills are memory; merging is lossy compression. The AGI's job is to make each skill progressively more expert, not fewer.
type: meta
maturity: 4
owner: AGI-discipline
trigger: new knowledge discovered, new pattern identified, skill creation or update needed
author: Session #036 (2026-04-05)
supersedes: .agents/SKILLS_CONSOLIDATION_PLAN.md (REJECTED)
---

# skill_coordinator — The Skill Arsenal Guardian

## Why this exists

Session #036 proposed merging 38 skills into 6 archetypes. JP Lopez rejected it:

> "No podemos perder conocimiento. Lo que tenemos que hacer es crear skills
> cada vez más específicos y expertos. La AGI debe razonar cómo ajustar cada
> skill cuando haya algo relevante para el skill."

This changes the paradigm entirely:

| Old (rejected) | New (this skill) |
|----------------|------------------|
| Skills should consolidate | Skills should specialize |
| Fewer skills = less drift | More expert skills = more capability |
| Merge reduces navigation cost | Growth increases precision |
| Target: 6 archetypes | Target: N highly-expert skills where N grows with knowledge |
| Delete duplicates | Differentiate duplicates into sub-skills |

**Core belief:** Skills are the long-term memory of the project. Losing skill
content to a merge is the same error as losing data to a re-extraction — both
are lossy compression of hard-won knowledge.

---

## The skill_coordinator's job

When new knowledge arrives (pattern, bug, protocol, finding, edge case), this
agent answers three questions in order:

### Question 1 — Does an existing skill OWN this knowledge?
- Read all candidate skill SKILL.md files
- Determine the best topical fit
- If fit is clear: **update that skill** with the new knowledge
- If fit is partial: go to Question 2

### Question 2 — Should an existing skill be SPLIT into sub-skills?
- If a skill is accumulating disparate topics under one name, split it
- Example: `sap_payment_bcm_agent` could split into:
  - `sap_payment_bcm_config` (FBZP, house banks, workflow 90000003)
  - `sap_payment_bcm_forensics` (dual-control audit, user patterns, H13)
  - `sap_payment_bcm_dmee` (XML formats, PPC, AE/BH variants)
- Splits create MORE specialized skills, not fewer
- Each split preserves 100% of the original content — never summarize

### Question 3 — Does this justify a NEW specialized skill?
- Criteria (ALL must be true):
  1. No existing skill has topical ownership
  2. The knowledge will be queried independently 3+ times
  3. It has a clear invocation trigger (not just "sometimes useful")
  4. It will grow over time (has a roadmap of what might be added)
- If yes: create new skill via `skill_creator` protocol, register in `SKILL_MATURITY.md`

---

## Growth principles (the 7 rules)

### 1. Skills grow, they do not merge
- Adding content to a skill is cheap (markdown)
- Merging skills loses unique content, examples, edge cases
- Navigation cost of "too many skills" is low
- Rediscovery cost of "lost skill content" is high

### 2. Specialization beats generalization
- `sap_payment_bcm_agent` > `payment_generic_helper`
- `sap_company_code_copy` > `deployment_patterns`
- The more specific the skill, the more load-bearing its knowledge

### 3. Splits are celebrated, merges are forbidden
- When a skill grows past ~1000 lines OR covers 3+ distinct sub-topics, split it
- Each split inherits 100% of relevant content verbatim
- Splits are logged with rationale in `SKILL_MATURITY.md`

### 4. Dormancy is not a reason to delete
- A skill unused for 30 sessions may still encode knowledge needed on session 31
- Only delete if BOTH: (a) dormant 30+ sessions AND (b) knowledge is fully
  captured elsewhere or genuinely obsolete
- Default action for dormancy: PROMOTE (add a cross-reference to it from
  active skills so future sessions find it)

### 5. Every new finding MUST land somewhere
- Findings must not live only in retro files or memory/
- The skill_coordinator's session-close check: "Is every non-trivial finding
  from this session now in a SKILL.md?"
- If not, route it

### 6. Cross-references over copies
- If two skills need the same fact, one OWNS it and the other LINKS
- Ownership is chosen by "which skill would be invoked when this fact matters"
- Prevents drift between copies

### 7. The coordinator never holds content itself
- This skill is a router. It contains PRINCIPLES, not domain knowledge.
- When in doubt, route to a more specific skill, not into this one.

---

## Routing Protocol (invoked when new knowledge arrives)

```
Input: a new fact, pattern, bug, finding, edge case, or protocol
Output: updated SKILL.md(s) + rationale

Step 1: Identify the knowledge type
   - Data finding → sap_data_extraction or a Miner skill
   - Code behavior → sap_class_deployment, sap_adt_api, or a domain skill
   - Config pattern → sap_expert_core or a domain skill
   - Failure mode → the skill most likely to encounter it
   - Process insight → a domain agent (psm/hcm/fi) or a miner
   - Meta-discipline → agi_retro_agent, skill_creator, skill_coordinator itself

Step 2: Find the best-fit skill
   - grep SKILL.md files for topical keywords
   - Rank by topical density (not just mention count)
   - Consider the invocation trigger: when would someone read this skill?

Step 3: Decide the action
   a) UPDATE  — add section to existing skill
   b) SPLIT   — existing skill is too broad, split and place content
   c) CREATE  — new specialized skill needed
   d) LINK    — fact belongs in skill A, but skill B should reference it

Step 4: Execute
   - Write the update/split/create
   - Update SKILL_MATURITY.md if maturity changed
   - Update SESSION_LOG with "Knowledge routed: <fact> → <skill>"

Step 5: Verify
   - Re-grep to confirm the knowledge is now findable from the obvious search
   - If not findable, the routing was wrong — reconsider
```

---

## Anti-patterns the coordinator prevents

### ❌ "Let's merge redundant skills"
Response: Redundancy between two skills means you have two distinct use cases
with a shared concept. Factor the shared concept as a LINK, keep both skills.

### ❌ "Delete unused skills"
Response: Evaluate knowledge uniqueness before deletion. If the knowledge
is captured elsewhere, delete. If not, MARK DORMANT but keep.

### ❌ "Add the finding to MEMORY.md or a feedback file"
Response: MEMORY.md is an index, feedback files are lessons. Domain findings
belong in SKILL files where they will be invoked during relevant work.

### ❌ "This is a one-off, no need to update any skill"
Response: One-offs accumulate. If a fact surprised you once, it will surprise
a future session unless it's in a skill. Route it.

### ❌ "Create a new skill for every finding"
Response: New skills require the 4-criteria test (Question 3). Most findings
update existing skills.

---

## Examples — how the coordinator reasons

### Example 1: "BSEG is not a table, it's a JOIN (Session #035)"
- Not a bug, a structural insight
- Affects: anyone querying BSEG
- Best-fit skills: `sap_data_extraction` (extraction-time guidance), `fi_domain_agent` (FI join patterns)
- Decision: **Update both**. sap_data_extraction gets the "how to query bseg_union" section, fi_domain_agent gets the "golden query joins" section. Cross-link.

### Example 2: "H13 BCM dual-control finding, 3,394 batches"
- Domain-specific forensic finding
- Affects: BCM audit workflows
- Best-fit: `sap_payment_bcm_agent` (existing, 728 lines)
- Decision: **Update sap_payment_bcm_agent** with a new "Dual Control Audit" section. If it grows past 1000 lines, consider split into `sap_payment_bcm_forensics` as a separate skill.

### Example 3: "File-based integration vector (Session #035)"
- Cross-cutting pattern touching jobs, interfaces, external systems
- Best-fit: `sap_interface_intelligence` (primary), `sap_job_intelligence` (secondary)
- Decision: **Update sap_interface_intelligence** with the new vector. Link from sap_job_intelligence. Do NOT create a new "file_integration" skill — not specific enough, not 3+ invocations expected.

### Example 4: "agi_retro_agent workflow"
- Meta-discipline, not a domain fact
- Best-fit: none existing before #036
- Decision: **Create new skill** `agi_retro_agent` (done in #036)

### Example 5: "VPN drops cause extraction loss (recurring)"
- Cross-cutting infrastructure pattern
- Best-fit: `sap_data_extraction` (where it manifests)
- Decision: **Update sap_data_extraction** with "VPN Resilience" section (period-by-period extraction pattern) + add to its Known Failures list.

---

## Relationship to other meta-skills

- **`skill_creator`** — creates NEW skills (invoked by skill_coordinator Step 3c)
- **`agi_retro_agent`** — audits that findings were routed (Principle 7: Rule Enforcement)
- **`skill_coordinator`** (this one) — decides WHERE findings go
- **`preflight_enforcer`** (future) — owns `session_preflight.py`

The three meta-skills are siblings, NOT merged into a "MetaAgent". Each has
a distinct role. `agi_retro_agent` audits, `skill_creator` creates, `skill_coordinator`
routes.

---

## Invocation triggers

Invoke `skill_coordinator` when:
1. A session produces a finding that doesn't obviously belong to one skill
2. A skill grows past ~1000 lines (consider split)
3. A skill has been dormant 30+ sessions (decide: dormant/delete/promote)
4. The retro agent flags "finding not routed to a skill" (Principle 7)
5. The user asks "where should this knowledge live?"
6. A new session starts and there's uncommitted knowledge from the previous session

---

## Success metrics

- **Skill count trends UP over time** (specialization growth)
- **No skill merges** (ever)
- **Every retro finding lands in a SKILL.md** (100% routing)
- **Split events logged** (evidence of deliberate specialization)
- **Zero "orphan findings"** (knowledge in memory/ or retros that never reached a skill)

---

## First invocation

Session #036 — this SKILL.md itself. First tests:

1. Route the H13 BCM hypothesis into `sap_payment_bcm_agent` (not a new skill — update existing)
2. Route the integration map findings into `sap_interface_intelligence` (update)
3. Route the session_preflight.py pattern into a new skill OR into `agi_retro_agent` (decision pending)

---

## The single-sentence charter

**Every piece of knowledge the project earns must live in a skill, and the skill_coordinator is the agent that decides which skill, and makes sure the knowledge actually lands there.**
