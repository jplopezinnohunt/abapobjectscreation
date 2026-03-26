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

## Phase 2: PMO Tracker Update

- [ ] **Mark completed items** with ✅ in `knowledge/pmo_tracker.md`
- [ ] **Add new pending items** discovered during session
- [ ] **Update blockers** — resolved or new ones found?
- [ ] **Update "Last Updated" line** with session number and date

**Pass criteria**: PMO tracker reflects actual project state.

---

## Phase 3: Memory Update

- [ ] **Update MEMORY.md** — Session history section (1-2 lines per session)
- [ ] **Update pending work list** in MEMORY.md — remove completed, add new
- [ ] **Save new feedback memories** — for any mistakes made or corrections received
- [ ] **Update/create project memories** — for new discoveries that affect future sessions

**Pass criteria**: Next session's open checklist will have accurate context.

---

## Phase 4: Skill Updates (NON-NEGOTIABLE)

> Per `feedback_session_close_protocol.md`: If only MEMORY.md is updated but skills are not,
> the next session will repeat the same mistakes.

- [ ] **List all skills used or affected** this session
- [ ] **For each affected skill**, update SKILL.md with:
  - New data (table counts, extraction status, row counts)
  - Bugs discovered and workarounds
  - New Known Failures entries
  - Completed pending items marked done
- [ ] **Apply skill quality gate** before saving:
  - Contains at least one tested working example
  - Has confirmed endpoint/table/field name (not theoretical)
  - Documents at least 2 known failure modes
  - States success criteria ("you know it worked when...")

**Pass criteria**: Every skill touched this session has updated SKILL.md.

---

## Phase 5: Confirm Closed

Tell the user:
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
- ❌ Don't sync to external systems (Gemini brain, etc.) unless user confirms path exists
