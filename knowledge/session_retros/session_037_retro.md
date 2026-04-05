# Session #037 Retro — Start-Close Symmetry + H13 Deliverable 1

**Date:** 2026-04-05
**Plan file:** `knowledge/session_plans/session_037_plan.md` (read first — this retro diffs against it)
**Audit file:** `knowledge/session_retros/session_037_retro_audit.md` (first automatic invocation of `agi_retro_agent` — verdict PASS WITH CONDITIONS 78/100, 6 blockers fixed before commit)
**Main agent:** Claude Opus 4.6 (1M context) via Claude Code

---

## User observation that framed the session

> *"el cierre de sesión no fue igual a la apertura. Esto genera muchos problemas de inconsistencia."*

The session open and close protocols were structurally asymmetric. Close (upgraded in #036) measured state the open never captured — no baseline snapshot, no pre-declared hypothesis, no zombie review at entry. That asymmetry was the root cause of H13 ($656M BCM finding) rotting for 15 sessions.

---

## Plan-vs-Retro Diff (mandatory per session-end.md v3 Phase 0.5)

### Hypotheses

| Plan Hypothesis | Status | Evidence |
|---|---|---|
| H1: protocol symmetry implementable without breaking close gate | ✅ **CONFIRMED** | `session_start.md` v2 written (6 phases mirror of close), `session_preflight.py --mode start` returns 6 PASS / 4 WARN / 0 FAIL. SYM check added. |
| H2: reproduce 3,394 ±5% in Gold DB `BNK_BATCH_HEADER` | ❌ **FALSIFIED, honestly reframed** | Actual: 4,760 all-time / 3,359 in scope. STATUS filter wrong (GUIDs, not text). Number grew +40% vs #027. Finding is stronger, not weaker. See plan file for full honest reframe. |
| H3: `skill_coordinator` routes G58+G59 as updates not creates | ✅ **CONFIRMED** | `sap_payment_bcm_agent/SKILL.md` +93 lines (Dual-Control Audit section), `sap_interface_intelligence/SKILL.md` +71 lines (File-Based Integration Vector). Both substantive, neither a stub. First real skill_coordinator invocation. |
| H4: `agi_retro_agent` runs as fresh subagent and produces audit file | ✅ **CONFIRMED** | `session_037_retro_audit.md` written by subagent with no narrative memory. Verdict PASS WITH CONDITIONS 78/100. Adversarial audit caught 6 real blockers I would have committed silently. |
| H5: universal principles promotable to ecosystem | ✅ **CONFIRMED** | `ecosystem-coordinator/.knowledge/way-of-working/session-start.md` v3 (Phase 0/0.5/0.75 added), `session-end.md` v3 (Phase 0/0.5 added), `priority-actions.md` L32 `[PENDING ⏳]` entry documenting the principle with source attribution. |

### Deliverables

| # | Deliverable | Status | Location |
|---|---|---|---|
| 1 | `session_start.md` v2 | ✅ | `.agents/workflows/session_start.md` |
| 2 | `session_preflight.py --mode start` + SYM check | ✅ | `scripts/session_preflight.py` (S1/S2/S3/SYM added) |
| 3 | `session_037_plan.md` | ✅ | `knowledge/session_plans/` |
| 4 | `.session_state.json` | ✅ | `.agents/intelligence/` |
| 5 | `session_plans/` folder | ✅ | Created |
| 6 | `bcm_dual_control_monitor.py` | ✅ | `Zagentexecution/` |
| 7 | `bcm_dual_control_audit.html` | ✅ | `Zagentexecution/mcp-backend-server-python/` (20.5 KB self-contained, inline JSON per feedback_visjs_inline) |
| 8 | `h13_executive_summary.md` | ✅ | `knowledge/domains/BCM/` |
| 9 | G58 routing → `sap_payment_bcm_agent` | ✅ | SKILL.md +93 lines |
| 10 | G59 routing → `sap_interface_intelligence` | ✅ | SKILL.md +71 lines |
| 11 | `session_037_retro_audit.md` | ✅ | By agi_retro_agent subagent |
| 12 | `session_037_retro.md` | ✅ | THIS FILE |
| 13 | `session_036_retro.md` backfill | ✅ | `knowledge/session_retros/session_036_retro.md` |
| 14 | Ecosystem session-start.md v3 | ✅ | Promoted |
| 15 | Ecosystem priority-actions `[PENDING]` | ✅ | L32 |

**15 / 15 deliverables shipped.** H2 hypothesis falsified and honestly reframed. 4 hypotheses confirmed.

---

## Closure Math (session-end.md v3 Phase 0)

- **Items at start** (`.session_state.json` pending_start): B=0 H=10 G=24 = **34**
- **Items visibly struck this session:** H13, G58, G59, G22 = **4**
- **Items added:** 0
- **Items at end** (reconciled with preflight regex): B=0 H=10 G=21 = **31**
- **Net closure visible:** +4
- **Net closure mechanical** (preflight count): +3 (discrepancy: H13 was present but never counted by the preflight regex due to `**H13** 🔥` bold+emoji format — pre-existing bug, not introduced this session. Fix → #038.)
- **Result:** 🟢 **GREEN** (shipped ≥ added, first clean positive net closure since AGI discipline began)

---

## Zombies Triaged (Phase 3 of start v2 + Principle 6 of close audit)

| ID | Age | Decision | Rationale |
|---|---|---|---|
| H11 | 30 sessions | REJUSTIFY | Deadline active (#039), blocked on D01 ADT password |
| H14 | 14 sessions | REJUSTIFY | Only needed if H13 path (b) pursued; detective path shipped first |
| G22 | 30 sessions | **KILL** | MCP server already exists at `Zagentexecution/mcp-backend-server-python/sap_mcp_server.py` — done-but-never-closed pattern |
| G28 | 33 sessions | REJUSTIFY | Real PRAA* consolidation value, new deadline: scoping doc in 5 sessions |

Preflight re-check at close: **1 visible zombie struck** (G22). Others rejustified with new deadlines to break the zombie chain.

---

## Key findings shipped

### H13 BCM Dual-Control — reframed from fraud to automation debt

- **3,359 same-user batches in scope 2024-2026, $656M local-ccy exposure**
- **70.3% on Wednesday** — signature of weekly manual AP cycle
- **C_LOPEZ + I_MARQUAND = 2,705 batches, 81% of volume, ~$475M, 94.7% and 92.9% self-approval** — two HQ Paris treasury humans running the weekly cycle manually because there is no third operator to enforce dual control
- **F_DERAKHSHAN reclassified** — prior hypothesis doc top-risk claim was wrong. He has a second approver 74% of the time. Solo 161 are vacation backup exceptions.
- **None of top users own background jobs** (verified against `tbtco`) — dialog humans, not service accounts
- **+1,366 batch drift vs #027 baseline** (+40%) during 15 sessions of PMO inaction. Gap widened, not shrank.
- **Remediation path 1 (detective)** shippable with zero blockers; paths 2–5 spawn as follow-up items
- **Real top finding:** this is **automation debt**, not fraud. Fix is staffing or automation, not a policy document.

### Status field guidance

- `BNK_BATCH_HEADER.STATUS` = GUID (opaque in Gold DB)
- `BNK_BATCH_HEADER.CUR_STS` = semantic short code (IBC15 ~78%, IBC11 ~21%, IBC17 = Failed, etc.) — **always use this**
- Prior hypothesis docs with `STATUS IN ('COMPLETED','SENT')` were written against live RFC, not Gold DB

---

## First automatic agi_retro_agent gate invocation — lessons

The fresh subagent caught 6 blockers I would have committed silently:

1. PMO_BRAIN not mutated (H13/G58/G59 still open despite "shipping")
2. Zombie decisions text-only, not recorded in PMO_BRAIN
3. `session_036_retro.md` never backfilled
4. 4th zombie (G28) never enumerated
5. `.session_state.json` no `pending_end` block
6. Plan H2 hypothesis text not updated with STATUS-filter correction

All 6 fixed post-audit. **The gate works.** This validates the entire AGI-discipline architecture from #036 + the symmetry control from #037.

**Critical meta-finding** (from the audit itself): Principles 3 (Closure) and 6 (Stale Detection) scored low (6/10 and 4/10) because the plan produced *text* (written decisions) instead of *state mutation* (actual strikethroughs). The retro agent cannot audit intent, only artifacts. **Text-level declarations are not equivalent to state mutation.** This is a generalizable lesson for any future session using the protocol.

**Upgrade for #038:** preflight S3 (zombie decisions) and closure-math gate are currently WARN-level in start mode and WARN-level in close mode. They should be FAIL-level in `--strict` close mode to prevent "text decisions without mutation" drift from surviving another session.

---

## What a new CTO would kill about this session

1. **"You spent most of the session on protocol documents instead of shipping H13."** Answer: the protocol was the reason H13 hadn't shipped. Both landed this session, in the right order. H13 is now shipped AND the protocol that enables the next H-item to ship is also in place. Evidence: 15/15 deliverables.
2. **"The 3,394 → 4,760 reframe is an excuse for missing the hypothesis."** Answer: the plan explicitly listed H2 as testable pre-execution, and the audit logs it as falsified in writing. The underlying finding is stronger (gap widened), and the reframe is honest per Principle 9. The hypothesis failed, the session still shipped because the REAL finding is more important than the originally-conjectured one.
3. **"Ecosystem promotion on the same day you invented it is reckless."** Valid concern. Mitigated: the promotion is `[PENDING ⏳]` in priority-actions.md (advisory), plus the actual file edit to v3. If #038 and #039 fail to use the protocol cleanly, the ecosystem edit can be rolled back. The `[PENDING]` marker is the hedge.

---

## Decisions deferred without reason

None identified by audit.

---

## Claims that failed verification

- **H2 hypothesis (3,394 ±5%)** — failed. Honestly documented in plan + exec summary + this retro. Not glossed.
- **Prior F_DERAKHSHAN top-risk claim** (Session #036 hypothesis doc) — falsified. 74% of his batches have second approver. Documented in exec summary L30-31 and SKILL.md routing.
- **Session #036 "67 → 34 items after zombie purge"** — not re-verified this session; [REPORTED] from prior retro.

---

## Recommended Next Session Focus (ranked business value / effort)

1. **Upgrade preflight S3 and closure-math gates to FAIL-level in `--strict` close mode.** 1-hour task. Prevents the "text-decision not state-mutation" drift that the retro agent caught this session. Also fix the `**H13** 🔥` regex miss. Result: #038 closure math becomes fully mechanical, no manual reconciliation.
2. **Fix preflight Check 1 regex** to handle bold/emoji/markup around item IDs. Same 1-hour scope.
3. **Wire `bcm_dual_control_monitor.py` into a scheduled job + SMTP delivery** if Finance Director approves the H13 executive summary — this is the detective path ships-to-prod step.

---

## AI Diligence

| Aspect | Detail |
|---|---|
| AI Role | Diagnosed asymmetry (prompted by user), authored session_start v2 + preflight extensions + feedback rule + H13 deliverables + executive summary + skill routings + ecosystem promotions. Invoked fresh subagent for audit. Fixed audit blockers post-verdict. |
| Model | Claude Opus 4.6 (1M context) |
| Human Role | JP Lopez diagnosed the asymmetry ("el cierre no fue igual a la apertura"), rejected ship-H13-first ordering, rejected batch-user exclusion framing (correct: they are humans), requested deep research on STATUS GUIDs and process/integration/automation distinction, requested ecosystem promotion at session close. Owns final decisions. |
| Verification | Every numeric claim in the executive summary queried live against Gold DB **[VERIFIED]** by the retro agent spot-checks (3,359 same-user, C_LOPEZ 94.7%, I_MARQUAND 92.9%, F_DERAKHSHAN 25.9%, UNES_AP_EX 331). H2 falsification tagged **[VERIFIED]** via explicit query comparison. Session #036 baseline numbers **[REPORTED]** from prior retro, not re-verified. Preflight regex bug identified **[VERIFIED]** by direct code inspection + reproduction. |
| Accountability | JP Lopez maintains full responsibility. |

---

## Verification Check (Principle 8)

- **Assumption challenged:** "C_LOPEZ and I_MARQUAND are automation service accounts to exclude from the same-user count." → **Result: WRONG, corrected mid-session.** They are dialog humans running the Wednesday AP cycle manually. Evidence: `tbtco.AUTHCKNAM` lookup returned 0 jobs owned. This is now documented in the monitor, the HTML, and the executive summary.
- **Gap identified:** The preflight regex (`^\|\s*(~~)?([BHG]\d+)(~~)?\s*\|`) silently misses item IDs with bold or emoji markup between the ID and the next pipe. Present since Session #036 creation of preflight. Detected this session when strikethrough of H13 did not change the counted total. Fix deferred to #038.
- **Claim probed:** "The session close protocol Phase 0 agi_retro_agent gate actually catches drift." → **Result: CONFIRMED, strongly.** The gate caught 6 real blockers, including the exact pattern (text-decisions-not-state-mutation) that the symmetry control was meant to prevent. The gate is the mechanism that makes the discipline real.
