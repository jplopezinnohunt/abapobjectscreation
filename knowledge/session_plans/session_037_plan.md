# Session #037 Plan
**Date:** 2026-04-05
**Previous:** #036 (AGI-discipline rebuild — **never committed, never indexed in SESSION_LOG**. Perfect irony: the session that invented the close protocol failed to execute it on itself.)
**Auditor (at close):** agi_retro_agent (first automatic gate test)

---

## Diagnosis that frames this session

The user observed: *"el cierre de sesión no fue igual a la apertura."*

Session #036 upgraded `session_close_protocol.md` with Phase 0 (agi_retro_agent) and Phase 0.5 (preflight --strict) but **did not touch `session_start.md`**. Result: close measures state that open never captured — no baseline snapshot, no pre-declared hypothesis, no zombie review at entry. That asymmetry is structurally the same bug that let H13 ($1.7B finding) rot for 15 sessions.

**This session fixes the protocol FIRST, then applies it to H13 as the first real test.** Fixing H13 before the protocol would leave the protocol broken and the next H-item would rot the same way.

---

## Hypothesis (testable at close)

**H1 — Protocol symmetry is implementable without breaking existing close gate.**
`session_start.md` v2 with 6 phases (Phase 0 preflight, Phase 1 memory, Phase 2 state snapshot, Phase 3 zombie review, Phase 4 plan declaration, Phase 5 confirm) will run end-to-end on this session. Preflight in `--mode start` will return 0 FAIL.

**H2 — H1 BCM data hypothesis reproduces.**
Querying `BNK_BATCH_HEADER` filtering `CRUSR = CHUSR AND STATUS IN ('COMPLETED','SENT')` reproduces the 3,394 same-user batches figure from `h13_remediation_hypothesis.md` within ±5%. Top 10 users cumulative sum exceeds 70% of total $ exposure.

**H2 — CORRECTION mid-session (2026-04-05):** H2 as literally written was **FALSIFIED**. Two errors in the hypothesis as drafted:
  1. **STATUS filter wrong** — Gold DB `BNK_BATCH_HEADER.STATUS` contains GUID references to SAP state objects, not text like `'COMPLETED'`/`'SENT'`. The semantic short code is `CUR_STS` (IBC15 = primary active state, 78.5% of same-user rows). The original filter never could have run against Gold DB.
  2. **Number magnitude** — with no STATUS filter at all, the actual reproduction is **4,760 same-user batches all-time / 3,359 in scope 2024-2026**, not 3,394. The original 3,394 figure (from Session #027) was measured ~10 sessions ago; the gap widened by +1,366 during the 15-session inaction window. **H2 is falsified at the ±5% tolerance, but the underlying finding is STRONGER, not weaker**: the gap is growing.
**Reframe accepted:** the executive summary documents both the STATUS correction and the magnitude delta honestly. Per Principle 9 (Brutal Honesty), this falsification is logged here rather than quietly overwritten.

**H3 — skill_coordinator router works for its first real invocation.**
G58 (H13 finding → `sap_payment_bcm_agent`) and G59 (file integration → `sap_interface_intelligence`) update the named skills with verifiable diffs. Neither creates new skills.

**H4 — agi_retro_agent runs as fresh subagent and produces the audit file.**
At close, invoking `agi_retro_agent` via Task tool with `subagent_type=general-purpose` produces `knowledge/session_retros/session_037_retro_audit.md` containing PASS/FAIL verdict, 10 principle scores, closure math, and evidence-cited claims. The audit file itself is the first end-to-end test of the protocol invented in #036.

**H5 — The project-level upgrade is promotable to ecosystem.**
The universal parts (symmetry principle, state snapshot, plan file, closure math as mechanical diff) can be copied to `ecosystem-coordinator/.knowledge/way-of-working/session-start.md` v3 without SAP-specific contamination. The SAP-specific parts (preflight Check 5 zombie regex, Gold DB checks, D01/P01 rules) stay in project.

---

## Deliverables (shippable artifacts)

### Protocol fix (must ship before H13)
1. `.agents/workflows/session_start.md` v2 — 6-phase symmetric protocol ✅ **DONE** (first artifact of this session)
2. `scripts/session_preflight.py` — `--mode start` branch with 3 new checks (S1 plan file, S2 state snapshot, S3 zombie decisions) ✅ **DONE**
3. `knowledge/session_plans/session_037_plan.md` — THIS FILE (Phase 4 of start protocol)
4. `.agents/intelligence/.session_state.json` — baseline snapshot for closure diff
5. `knowledge/session_plans/` folder exists as the mirror of `knowledge/session_retros/`

### H13 Deliverable 1 (BCM monitoring report end-to-end)
6. `Zagentexecution/bcm_dual_control_monitor.py` — Python script querying Gold DB, outputs CSV + prints summary
7. `Zagentexecution/mcp-backend-server-python/bcm_dual_control_audit.html` — Interactive companion: summary cards, 3,394-row table with filters, top-10 users chart, UNES_AP_EX highlight, monthly timeline
8. `knowledge/domains/BCM/h13_executive_summary.md` — One-pager for Finance Director / CFO

### Knowledge routing (G58, G59)
9. `.agents/skills/sap_payment_bcm_agent/SKILL.md` — add "Dual Control Audit" section with H13 findings, query, reproduction steps (G58)
10. `.agents/skills/sap_interface_intelligence/SKILL.md` — add "File-Based Integration Vector" section documenting 8,700 file-based job runs + COUPA channel (G59)

### Close-phase artifacts
11. `knowledge/session_retros/session_037_retro_audit.md` — produced by `agi_retro_agent` subagent (first real invocation)
12. `knowledge/session_retros/session_037_retro.md` — retro written by main agent after audit passes
13. `knowledge/session_retros/session_036_retro.md` — **backfill**: close #036 retroactively (SESSION_LOG indexing, commit of untracked #036 work)

### Meta promotion (last action before commit)
14. `ecosystem-coordinator/.knowledge/way-of-working/session-start.md` v3 — promoted universal principles (asymmetry was the bug)
15. `ecosystem-coordinator/ecosystem/priority-actions.md` — `[PENDING ⏳]` entry documenting the promotion + rationale

---

## Out of scope (declared, to prevent creep)

- **H13 Deliverable 2 path (b) — workflow 90000003 modification.** Needs D01 dev access + Finance director signoff. Add as H13a in backlog.
- **H13 Deliverable 2 path (c) — BCM config change for UNES_AP_EX.** Same. Add as H13b.
- **H14 YWFI package source extraction.** Bound to H13 but requires D01 ADT password refresh. Zombie will be rejustified in Phase 3, not shipped.
- **Skill creator invocation for new sub-skills.** `skill_coordinator` will UPDATE existing skills (G58/G59), not create new ones. Split/create decisions deferred.
- **MEMORY.md line compaction.** MEMORY.md is 239 lines (over old 200 limit) but growth paradigm = no limit. NOT touching.
- **`session_preflight.py` Check 10 hypothesis scanning of session_plans/ folder.** Nice-to-have, defer to next session.
- **Zombie H11, H14, G22 full resolution.** Phase 3 will rejustify with evidence, not ship.

---

## Success criteria (testable at close by agi_retro_agent)

- [ ] H1: `python scripts/session_preflight.py --mode start` returns 0 FAIL (WARNs acceptable if explained)
- [ ] H2: `bcm_dual_control_monitor.py` executes, outputs CSV with ≥3,225 and ≤3,563 same-user batches (3,394 ±5%)
- [ ] H3: Both `sap_payment_bcm_agent/SKILL.md` and `sap_interface_intelligence/SKILL.md` have new sections with timestamps from this session
- [ ] H4: `session_037_retro_audit.md` exists, contains PASS verdict OR explicit FAIL with blockers enumerated
- [ ] H5: `ecosystem-coordinator/.knowledge/way-of-working/session-start.md` v3 exists OR `[PENDING ⏳]` entry explains why deferred
- [ ] Closure math: `items_shipped ≥ items_added` (target: +3 net closure — H13, G58, G59)
- [ ] Every extraction has pre-declared hypothesis (H2 above is the pre-declaration)
- [ ] Every finding routed via `skill_coordinator` (G58, G59 explicit)
- [ ] Zombies H11, H14, G22 have decisions recorded in PMO_BRAIN (kill/ship/rejustify)

---

## Phase 3 — Zombie Triage (mandatory before planning, executed now)

Preflight flagged 4 zombies (>10 sessions old without movement):

| ID | Age | Title | Decision | Reason |
|---|---|---|---|---|
| H11 | 30 (since #005) | Extract Benefits BSP + HCM Z-reports | **REJUSTIFY** | Deadline set #036 ("3 sessions or KILL" = kill by #039). Still legit work, blocked on D01 ADT password. Hard deadline active. |
| H14 | 14 (since #021) | Extract YWFI package source | **REJUSTIFY** | Bound to H13 path (b). Kill alongside H13 if path (b) never executes. Mark as H13-dependent. |
| G22 | 30 (since #005) | SAP MCP Server build | **KILL** | MCP server already exists: `Zagentexecution/mcp-backend-server-python/sap_mcp_server.py`. This item is done-but-never-closed, same pattern as H10 killed in #036. |
| (4th zombie, truncated in preflight output) | — | — | **TBD after full list** | Re-run check 5 with full evidence list |

Decisions recorded in `.agents/intelligence/PMO_BRAIN.md` during Phase 6.

---

## What a new CTO would ask to kill

- *"You spent half the session fixing a protocol document instead of shipping H13."* — **Answer:** The protocol was the reason H13 hadn't shipped for 15 sessions. Fixing the protocol first is the minimum durable win; fixing H13 first leaves the next H-item to rot the same way. Both ship this session, but in that order.
- *"Why do you need a plan file AND a retro audit file? That's ceremony."* — **Answer:** The diff between the two IS the closure math. Without both, closure is narrative and self-reported, which was the #001-#035 pattern.
- *"Promoting to meta the same day you invent it is reckless."* — **Legitimate challenge.** Mitigated: the promotion is a `[PENDING ⏳]` marker, not a full copy. Full copy to ecosystem happens only if #038 and #039 also run the new protocol cleanly.

---

## AI Diligence

| Aspect | Detail |
|---|---|
| AI Role | Synthesized the symmetry diagnosis from user observation ("el cierre no fue igual a la apertura"). Authored v2 protocol, preflight extension, plan file, and execution order. |
| Model | Claude Opus 4.6 (1M context) |
| Human Role | JP Lopez diagnosed the asymmetry, rejected ship-H13-first order, requested meta promotion at session close. Owns ecosystem promotion decision. |
| Verification | Pre-execution: this plan file exists BEFORE any H13 data work. Close: `agi_retro_agent` will diff plan vs. retro. |
| Accountability | JP Lopez maintains full responsibility. |

---

## Promotion plan (to ecosystem, at session close)

Universal principles to promote:
1. **Symmetry principle** — every close phase must have an open counterpart
2. **State snapshot concept** — `.session_state.json` with baseline for mechanical closure diff
3. **Plan file concept** — `session_plans/session_NNN_plan.md` mirrors `session_retros/session_NNN_retro.md`
4. **Closure math as diff, not narrative** — `pending_end - pending_start = added - closed`
5. **Zombie review at open, not close** — decisions before work, not after

Project-specific (NOT promoted):
- `session_preflight.py` SAP-specific checks (Gold DB PRAGMA, PMO_BRAIN regex, D01/P01 rules)
- The three meta-skills (`agi_retro_agent`, `skill_coordinator`, `skill_creator`) — need 2+ sessions of real use before promotion
- BCM/H13/SAP-specific content in this plan

Promotion mechanism: edit `ecosystem-coordinator/.knowledge/way-of-working/session-start.md` to v3 + add `[PENDING ⏳]` in `ecosystem/priority-actions.md` for the project-to-project broadcast.
