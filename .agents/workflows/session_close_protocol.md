# Session Close Protocol — AGI-Discipline Edition

**Supersedes:** `session_retro.md` checklist (kept as Phase 1-7 reference)
**Author:** Session #036 (2026-04-05)
**Enforcement:** Mandatory. Main agent cannot commit without Phase 0 PASS.

---

## Phase 0 (NEW) — AGI Retro Audit

Before any of the legacy phases, the main agent MUST invoke `agi_retro_agent` as a fresh subagent.

### How
Use the Agent tool with `subagent_type=general-purpose`. The prompt must:
1. Point to `.agents/skills/agi_retro_agent/SKILL.md` as the agent's brief
2. Provide: current PMO_BRAIN diff, git diff since last commit, path to current retro draft
3. Ask for: PASS/FAIL verdict, per-principle scores, blockers list, recommended retro content

### Gate
- **PASS** → proceed to Phase 1
- **PASS WITH CONDITIONS** → fix conditions, re-run Phase 0
- **FAIL** → fix blockers, re-run Phase 0

**The main agent CANNOT skip this phase by self-audit. The audit must come from a fresh subagent with no narrative memory of the session.**

### Evidence
The audit produces `knowledge/session_retros/session_NNN_retro_audit.md`.
This file is committed alongside the retro file in Phase 6.

---

## Phase 0.5 — Run session_preflight.py

```bash
python scripts/session_preflight.py --mode close --strict
```

If exit code is non-zero, STOP. Fix the blockers. Re-run.

Expected final state: 0 FAIL, minimal WARN, documented SKIPs.

---

## Phase 1-7 (Legacy, kept verbatim)

See `.agents/workflows/session_retro.md` for the existing 7-phase checklist:
- Phase 1: Session Retro File
- Phase 1b: Verification Check (Principle 8)
- Phase 2: PMO Reconciliation
- Phase 3: Memory Update
- Phase 4: Skill & Workflow Updates
- Phase 5: Ecosystem Sync
- Phase 6: Commit
- Phase 7: Confirm Closed

**These phases remain mandatory and unchanged.** The AGI audit is additive.

---

## Why the change

Up to Session #035, the retro was authored by the same agent that worked the session. This produced structural bias:
- Net-zero closes labeled "productive"
- PMO counts wrong for 4+ sessions despite explicit reconciliation rules
- H13 ($1.7B BCM finding) sat untouched for 15 sessions while extractions piled up
- 39 backlog items went >10 sessions without movement, unchallenged
- Feedback rules existed as prose but had no enforcement gate

Phase 0 closes these gaps with a **fresh adversarial auditor**.

---

## Failure scenarios

### "The audit agent is being too harsh"
Not a valid reason to override. Adversarial audit is the point. If you think the agent is wrong on a specific finding, challenge the specific finding with evidence. Don't disable the audit.

### "I don't have time to fix blockers this session"
Add them to PMO as HIGH with a 1-session deadline. The session can close with blockers documented, but they must not disappear.

### "The same principle keeps failing session after session"
After 3 consecutive failures on the same principle, the agent escalates to user with a hard halt. This is by design.

---

## Success signal

A session closes clean when:
1. `agi_retro_agent` returns PASS
2. `session_preflight.py --strict` returns exit 0
3. `items_shipped >= items_added` (closure >= discovery)
4. Every extraction has a hypothesis.md
5. No zombie items >10 sessions old without a decision (ship/kill/rejustify)

---

## First use

Session #036 is the first session to use this protocol. The audit of #036 will happen when this session closes.
