---
description: Session OPEN protocol — mirrors session_close_protocol.md. Every phase at close has a counterpart here. Asymmetry was the bug that let H13 rot 15 sessions.
version: 2.0
supersedes: session_start.md v1 (4-phase, asymmetric with close)
author: Session #037 (2026-04-05)
---

# Session Open Protocol — AGI-Discipline Edition

**Run at the START of every conversation. Main agent cannot begin session work without Phase 0 PASS.**

---

## Why v2 exists

Up to Session #036, the open protocol had 4 phases (memory read, context load, plan, confirm). The close protocol had been upgraded in #036 with:
- Phase 0: `agi_retro_agent` audit (adversarial)
- Phase 0.5: `session_preflight.py --mode close --strict`
- Closure math: `shipped - added > 0`
- Hypothesis grounding for every extraction

**The close measured things the open never captured.** No baseline snapshot → no real closure math. No pre-declared hypothesis → retro-justifying extractions. No zombie review at open → zombies processed too late (at close).

Session #037 diagnosis: **the asymmetry itself was the bug that allowed H13 ($1.7B finding) to rot for 15 sessions.** If open doesn't declare "this session will ship H13", close has nothing to audit against.

This v2 closes the gap. Every phase at close has a counterpart here.

---

## Phase 0 — session_preflight.py --mode start

```bash
python scripts/session_preflight.py --mode start
```

Runs the 10 executable checks in "start" mode. Difference from close:
- Start: failures are WARN (not blockers). User sees them before planning.
- Close: failures are FAIL (blockers). Same checks, stricter gate.

**Gate:** No FAIL in start mode must be ignored. If PMO counts don't match, zombie items are piling up, or memory is inconsistent — **fix before planning the session**. Planning on broken state is how zombies accumulate.

---

## Phase 1 — Memory Restoration (parallel reads)

Read ALL in parallel:

- [ ] **MEMORY.md** — index + **every topic file** it references (`project_*.md`, `feedback_*.md`, `topic_*.md`).
  - Path: `~/.claude/projects/c--Users-jp-lopez-projects-abapobjectscreation/memory/MEMORY.md`
  - ⚠️ MEMORY.md is an INDEX. If you only read it, you miss most of the project's memory.
- [ ] **PMO_BRAIN.md** — current workstream + blockers. Path: `.agents/intelligence/PMO_BRAIN.md`
- [ ] **Last retro** — read the latest `knowledge/session_retros/session_NNN_retro*.md` file directly (not the SESSION_LOG index).
- [ ] **Last plan** (NEW) — read `knowledge/session_plans/session_NNN_plan.md` if it exists. Compare to retro: what did we say we'd ship vs. what actually shipped?
- [ ] **Ecosystem shared knowledge** (parallel):
  - `ecosystem-coordinator/.knowledge/way-of-working/session-start.md` (universal 7 steps)
  - `ecosystem-coordinator/.knowledge/way-of-working/collaboration-terms.md`
  - `ecosystem-coordinator/ecosystem/priority-actions.md` — check for `[BROADCAST]` items
- [ ] **GOVERNANCE.md** — `.agents/GOVERNANCE.md`

**Pass criteria:** You can answer: "What was the last session? What was planned vs. shipped? Any ecosystem broadcasts?"

---

## Phase 2 — State Snapshot (NEW, mirrors close Phase 2 reconciliation)

Write `.agents/intelligence/.session_state.json` with the baseline the close will audit against:

```json
{
  "session": "037",
  "start_ts": "2026-04-05T...",
  "git_head_start": "<sha>",
  "pmo_pending_start": {"blocking": N, "high": N, "backlog": N, "total": N},
  "gold_db_tables_start": N,
  "skills_count_start": N,
  "last_session_shipped": ["H13 D1", "G58", "G59"],
  "last_session_added": [],
  "last_session_net": "+3"
}
```

**Purpose:** closure math at close is now a trivial diff (`pmo_pending_end - pmo_pending_start = added - closed`), not an inferred narrative.

**Pass criteria:** `.session_state.json` exists, fields populated, git sha resolves.

---

## Phase 3 — Zombie Review (NEW, mirrors close Principle 6)

Run preflight Check 5 output and **act on it before planning**:

For each item flagged as zombie (>10 sessions old, no movement):
- **KILL** — strike through in PMO with reason ("superseded", "no business value", "already done but not closed")
- **SHIP** — promote to this session's top priority
- **REJUSTIFY** — add a 1-line evidence update ("still blocked on D01 password — retried #036")

**Hard rule:** No zombie survives a session without a decision. Accumulating zombies was what made PMO_BRAIN unreadable before #036 (67 items → purged to 34).

**Pass criteria:** Every zombie flagged by check 5 has a decision recorded in PMO_BRAIN.

---

## Phase 4 — Declare Session Hypothesis (NEW, mirrors close Principle 4)

Before touching any data/code, write `knowledge/session_plans/session_NNN_plan.md`:

```markdown
# Session #NNN Plan
**Date:** YYYY-MM-DD
**Auditor (at close):** agi_retro_agent

## Hypothesis (what this session will prove)
H1: <claim>
H2: <claim>

## Deliverables (shippable artifacts)
1. <file path> — <what it contains> — <how to test it>
2. <file path> — <what it contains> — <how to test it>

## Out of scope (declared, to prevent creep)
- <thing NOT doing>
- <thing NOT doing>

## Success criteria (testable at close)
- [ ] H1 reproduced ±5% against source
- [ ] Deliverable 1 exists and loads
- [ ] PMO net closure ≥ 0 (shipped ≥ added)
- [ ] Every new finding routed via skill_coordinator

## What a new CTO would ask to kill
<pre-emptive list of weak items for close audit>
```

**Pass criteria:** Plan file exists. Hypothesis is testable. Deliverables are named. Out-of-scope is declared.

**This is the single most important change in v2.** The close audit can now diff plan-vs-retro mechanically instead of inferring intent.

---

## Phase 5 — Confirm Ready

Single message to user:
```
Session #N — continuing from #(N-1) (date)
Preflight: <N PASS / N WARN / N FAIL>
Pending: <B blocking / H high / G backlog>
Zombies: <N flagged → decisions: X killed, Y rejustified, Z promoted>
Plan: session_plans/session_NNN_plan.md
Hypothesis: <1 sentence>
Deliverables: <count>
Ready.
```

---

## Symmetry Table (open ↔ close)

| Open Phase | Close Phase | Artifact |
|---|---|---|
| 0. `preflight.py --mode start` | 0.5. `preflight.py --mode close --strict` | Same 10 checks, stricter gate |
| 1. Memory restoration | 1. Memory update | MEMORY.md + topic files |
| 2. State snapshot (`.session_state.json`) | 2. PMO reconciliation | Closure math = diff |
| 3. Zombie review (pre-work) | 6. Principle 6 audit (stale detection) | Decisions, not reports |
| 4. Hypothesis declaration (plan file) | 4. Hypothesis grounding audit | Plan-vs-retro diff |
| — | 0. `agi_retro_agent` audit | Adversarial |
| — | 4. Skill & workflow updates (via `skill_coordinator`) | Every finding routed |
| 5. Confirm ready | 7. Confirm closed + commit | Symmetric handshake |

---

## Non-Negotiable Rules (memorize)

```
D01 = Development  → password + SNC → code deploy, BSP extract, ADT write
P01 = Production   → SNC/SSO ONLY  → data, monitoring, BDC, users
NEVER write code to P01. NEVER use D01 data for monitoring.
P01 password is blank in .env — SSO handles all prod auth.
```

---

## Anti-Patterns (DON'T)

- ❌ Skip Phase 0 preflight — you'll plan on broken state
- ❌ Skip Phase 2 state snapshot — close will have no baseline to diff against
- ❌ Skip Phase 3 zombie review — zombies will survive another session
- ❌ Skip Phase 4 plan file — close audit becomes narrative, not diff
- ❌ Read only MEMORY.md index without topic files — you'll miss 80% of memory
- ❌ Parrot back what you read — just confirm ready in the Phase 5 format
- ❌ Ask "what would you like to work on?" if PMO has Blocking/High items AND no zombies flagged

---

## Failure Escalation

If Phase 0 preflight fails:
1. Fix the blocker (count reconciliation, missing retro, etc.)
2. Re-run preflight
3. Only then proceed to Phase 1

If Phase 3 zombies >5:
1. Stop planning session work
2. Zombie triage session — kill/ship/rejustify each one
3. Commit the triage as its own session deliverable
4. Then run Phase 4 for remaining scope

If Phase 4 hypothesis feels forced:
- You probably don't have a session goal yet. Ask the user. Do NOT invent work.

---

## First use

Session #037 (2026-04-05) — this file's own creation is the first use.
The plan file for #037 is: `knowledge/session_plans/session_037_plan.md`.
At close, `agi_retro_agent` will diff this plan against the retro as its first real test.

---

## Promotion to Ecosystem

Principles from this file that are universal (not SAP-specific) will be promoted to `ecosystem-coordinator/.knowledge/way-of-working/session-start.md v3` at session close (#037). Universal: symmetry, state snapshot concept, zombie review, hypothesis declaration. Project-specific (stays here): `session_preflight.py` SAP checks, PMO_BRAIN format, D01/P01 rules.

See close Phase 6 (commit) for the promotion action item.
