---
description: Mandatory session close checklist — preserve learnings, update skills, sync state
---

# Session Close Checklist

**Run at the END of every significant session. Do NOT skip steps.**
Mark each checkbox as you complete it. A skipped step = knowledge loss.

---

## Phase 1: Session Retro File

- [ ] **Create retro file** at `knowledge/session_retros/session_NNN_retro.md`
  - Template: accomplishments table, key discoveries, blockers, pending → next session
  - Include: session number, date, duration, systems used, type (analysis/extraction/dev/audit)
- [ ] **Verify retro is complete** — Can someone reading ONLY this file understand what happened?

**Pass criteria**: Retro file exists and is self-contained.

---

## Phase 1b: Verification Check (Principle 8)

> Pick the session's most "polished-looking" output and challenge it.

- [ ] **Assumption challenged**: What did the AI assume? Identify at least ONE
- [ ] **Gap identified**: What did the AI NOT check? Identify at least ONE
- [ ] **Claim probed**: Probe ONE factual claim → result: [CONFIRMED / CORRECTED / FLAGGED]

Record the result in SESSION_LOG under "Verification Check."

**Pass criteria**: At least one assumption was challenged. If you can't find any, the output wasn't scrutinized enough.

---

## Phase 2: PMO Tracker Update

- [ ] **Mark completed items** with ✅ in `.agents/intelligence/PMO_BRAIN.md`
- [ ] **Add new pending items** discovered during session
- [ ] **Update blockers** — resolved or new ones found?

**Pass criteria**: PMO_BRAIN reflects actual project state.

---

## Phase 3: Memory Update

- [ ] **Update MEMORY.md** — Session history section (1-2 lines per session)
- [ ] **Update pending work list** in MEMORY.md — remove completed, add new
- [ ] **Save new feedback memories** — for any mistakes made or corrections received
- [ ] **Update/create project memories** — for new discoveries that affect future sessions

**Pass criteria**: Next session's open checklist will have accurate context.

---

## Phase 4: Skill & Workflow Updates (NON-NEGOTIABLE)

> Per `feedback_session_close_protocol.md`: If only MEMORY.md is updated but skills are not,
> the next session will repeat the same mistakes.

### 4a: Skills
- [ ] **List all skills used or affected** this session
- [ ] **For each affected skill**, update SKILL.md with:
  - New data (table counts, extraction status, row counts)
  - Bugs discovered and workarounds
  - New Known Failures entries
  - Completed pending items marked done
- [ ] **Update SKILL_MATURITY.md** if any skill changed maturity level

### 4b: Workflows
- [ ] **Review session_start.md** — Does it still reflect how sessions actually open? Update if not.
- [ ] **Review session_retro.md (this file)** — Does it still reflect how sessions close? Update if not.
- [ ] **If a new anti-pattern was discovered**, add it to the relevant workflow's anti-patterns list.

**Pass criteria**: Every skill touched this session has updated SKILL.md. Workflows reflect reality.

---

## Phase 5: Ecosystem Sync

- [ ] **Update ecosystem priority-actions.md** — Mark completed items, add new pendings
- [ ] **Add AI Diligence Statement** to qualifying outputs (companions, evaluations, skill files)

**Pass criteria**: Ecosystem knows what changed in this project.

---

## Phase 6: Commit

- [ ] `git add` specific files (not -A blindly on first commit of session)
- [ ] `git commit` with descriptive message
- [ ] Verify `git status` is clean

**Pass criteria**: All session work is committed. "If it's not committed, it didn't happen."

---

## Phase 7: Confirm Closed

Show the user the retro file (Read tool, not regenerate from memory).

Then tell the user:
```
Session #N closed — [date] (~duration)
Next: [top 3 Critical tasks]
Skills updated: [list]
Brain: [node count if rebuilt]
```

---

## Discovery Analysis (answer each session)

| Question | Answer |
|----------|--------|
| New SAP table/BAPI/endpoint confirmed working? | |
| Failure mode encountered and fixed? | → Add to skill Known Failures |
| Pattern repeated 3+ times? | → Candidate for new skill |
| Architecture rule changed? | → Update MEMORY.md |

---

## Anti-Patterns (DON'T)

- ❌ Don't close without updating skills — this is the #1 cause of repeated mistakes
- ❌ Don't write retro from memory — re-read what you actually did
- ❌ Don't leave PMO tracker stale — it's the source of truth for priorities
- ❌ Don't forget feedback memories — corrections are the most valuable memory type
- ❌ Don't regenerate the retro for the user — use Read tool to SHOW the actual file
- ❌ Don't skip workflow updates — if session_start or session_retro need changes, update them NOW
- ❌ Don't use subagents for direct update work — Read + Edit, not Explore agent
