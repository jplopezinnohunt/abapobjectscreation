---
description: Mandatory session open checklist — restore memory, identify priorities, confirm ready
---

# Session Open Checklist

**Run at the START of every conversation. Do NOT skip steps.**
Mark each checkbox as you complete it. Report failures immediately.

---

## Phase 1: Memory Restoration (parallel reads)

Read ALL of these in parallel — do not read sequentially:

- [ ] **MEMORY.md** — Read index + ALL topic files it points to
  - Path: `C:\Users\jp_lopez\.claude\projects\c--Users-jp-lopez-projects-abapobjectscreation\memory\MEMORY.md`
  - ⚠️ MEMORY.md is an INDEX. You MUST read every `project_*.md` and `feedback_*.md` it references
- [ ] **SESSION_LOG.md** — Last session entry (date, accomplishments, pending)
  - Path: `.agents/intelligence/SESSION_LOG.md`
- [ ] **PMO_BRAIN.md** — Current workstream status + blockers
  - Path: `.agents/intelligence/PMO_BRAIN.md`
- [ ] **Ecosystem shared knowledge** (parallel with above):
  - `ecosystem-coordinator/.knowledge/way-of-working/collaboration-terms.md`
  - `ecosystem-coordinator/.knowledge/way-of-working/session-start.md`
  - `ecosystem-coordinator/ecosystem/priority-actions.md` — check for [BROADCAST] items
- [ ] **GOVERNANCE.md** — Internal coordinator index, two-tier model, skill maturity summary
  - Path: `.agents/GOVERNANCE.md`

**Pass criteria**: You can answer: "What was the last session? What are the top 3 pending items? Any ecosystem broadcasts?"

---

## Phase 2: Context Loading (parallel, only if needed)

Only read these if the session involves the relevant domain:

- [ ] **Brain stats** — `python sap_brain.py --stats` (if doing intelligence work)
- [ ] **Gold DB schema** — `PRAGMA table_list` on Gold DB (if doing extraction/query work)
- [ ] **Relevant SKILL.md** — Read the skill for today's domain (if doing domain work)

**Pass criteria**: You know the current state of the tools you'll use today.

---

## Phase 3: Session Plan

- [ ] **Identify session number** — Increment from last SESSION_LOG entry
- [ ] **Identify top 3 priorities** — From PMO Tracker Critical tier + MEMORY.md pending
- [ ] **Check blockers** — Any unresolved blockers from PMO Tracker?
- [ ] **Propose session plan** to user — 1-3 sentences, not a wall of text

**Pass criteria**: User confirms plan or redirects.

---

## Phase 4: Confirm Ready

Tell the user in ONE message:
```
Session #N — continuing from #(N-1) (date)
Plan: [1-3 priorities]
Brain: [node count if checked]
Ready.
```

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

- ❌ Don't read 6+ architecture files at session start — wastes context
- ❌ Don't spawn explore agents for info already in MEMORY.md
- ❌ Don't parrot back what you read — just confirm ready
- ❌ Don't ask "what would you like to work on?" if PMO has Critical items
- ❌ Don't skip ecosystem priority-actions — you'll miss [BROADCAST] alerts
- ❌ Don't skip GOVERNANCE.md — it has the two-tier model and maturity scores
