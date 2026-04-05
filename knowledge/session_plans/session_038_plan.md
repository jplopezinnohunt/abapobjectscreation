# Session #038 Plan
**Date:** 2026-04-05
**Previous:** #037 (PASS WITH CONDITIONS 78/100, committed as `e25a0f7`)
**Baseline:** `.session_state.json` pmo_pending_start = B=0 H=10 G=22 total=32

---

## Diagnosis that frames this session

Session #037 shipped the start-close symmetry control, H13 Deliverable 1, and a partial preflight hardening (regex fix + `--strict` escalation in commit `e25a0f7`) after the agi_retro_agent audit. Two loose ends remained open at close:

1. **Tech-debt verification** — the regex and `--strict` logic landed in code but were never re-run post-fix against a test harness. "Code exists" ≠ "code works".
2. **BROADCAST-003 acknowledgment** — 4-locus search + provenance discipline was mandated for all Tier 1 projects. #037 was the project that *triggered* the broadcast, so the retro was written before the broadcast existed. #038 is the first session that must ack it.

Plus: three zero-risk data/code deliverables that had been blocked:
- **H29** — 510 SKAT texts differ P01↔D01, needs UPDATE (pattern proven #034, 880 records, zero failures)
- **H11+H14+H18** — D01 ADT password now unblocked per user, 3 code extractions can run together
- **G60 (new #038)** — personal monitor bundle (BCM + Basis), user-run, no deployment

---

## Hypothesis (testable at close)

**H1 — Tech-debt is actually closed, not just coded.**
Re-running `python scripts/session_preflight.py --mode close --strict` after sync should show: Check 1 regex handles `**H13** 🔥` markup (verified via synthetic test row), S1/S2/S3/SYM escalate to FAIL when plan/state/symmetry missing. Starting state: 1 FAIL (count mismatch from G60 added this session — expected, trivially fixable by MEMORY.md sync).

**H2 — H29 SKAT diff produces exactly 510 rows (±5%) or the #034 note is stale.**
Query `sync_compare` pattern from `sap_master_data_sync` skill: `SELECT SAKNR, SPRAS, TXT20, TXT50 FROM skat_p01 FULL JOIN skat_d01 USING (SAKNR, SPRAS) WHERE p01.TXT20 != d01.TXT20 OR p01.TXT50 != d01.TXT50`. Expected: ~510 rows, majority with `CLOSED-BK` prefix in P01. If the count diverges >25%, the #034 assumption ("mostly closed accounts") is outdated and needs re-analysis before UPDATE.

**H3 — H11 + H14 + H18 D01 ADT extraction succeeds with refreshed password.**
All three targets resolve via ADT REST API without auth errors. Specifically:
- H11: Benefits BSP name extractable from `ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT` manifest reference + HCM Z-report source downloadable (≥5 files)
- H14: YWFI package contains `Z_GET_CERTIF_OFFICER_UNESDIR` and `Z_WF_GET_CERTIFYING_OFFICER` (at least these two function modules extractable)
- H18: `YCL_IDFI_CGI_DMEE_AE` and `YCL_IDFI_CGI_DMEE_BH` both readable; XML `<Purp><Cd>` literal value locatable in the source (answers the "AE5 vs SAL" question raised #026)

**H4 — G60 personal monitor bundle runs end-to-end as an on-demand tool.**
`python Zagentexecution/my_monitors/run_my_monitors.py` (new) produces `my_monitors_dashboard.html` with two tabs (BCM + Basis), both populated from live queries, self-contained (no CDN, per `feedback_visjs_inline`), opens in browser locally. No cron, no SMTP, no daemon. User runs it when they want the report.

---

## Deliverables (shippable artifacts)

### Block 1 — Tech-debt closure
1. MEMORY.md pending count synced 31 → 32 (G60 added this session)
2. `scripts/test_session_preflight.py` — synthetic test harness verifying Check 1 regex handles `**H13** 🔥` pattern AND `--strict` escalates S1/S2/S3/SYM from WARN → FAIL (pure-Python test, no SAP dependency)
3. BROADCAST-003 acknowledgment section in `session_038_retro.md` — evidence of 4-locus search for any ecosystem edits (expect zero edits this session, so the ack documents the discipline was consulted)

### Block 2 — H29 SKAT sync
4. `Zagentexecution/mcp-backend-server-python/h29_skat_diff.py` — extractor + formatter script
5. `Zagentexecution/mcp-backend-server-python/h29_skat_diff.csv` — full 510-row diff (SAKNR/SPRAS/TXT20_P01/TXT20_D01/TXT50_P01/TXT50_D01/CHANGE_TYPE)
6. **GATE** — present sample + classification to user for explicit approval before step 7
7. `Zagentexecution/mcp-backend-server-python/h29_skat_update.py` — RFC_ABAP_INSTALL_AND_RUN executor (UPDATE only, no INSERT), batched like #034
8. `knowledge/domains/FI/h29_skat_sync_log.md` — post-run gap=0 verification report

### Block 3 — D01 ADT extraction (H11+H14+H18)
9. `extracted_code/HCM/BSP/` — Benefits BSP application source files (discovery from manifest + extract)
10. `extracted_code/HCM/Z_Reports/` — HCM namespace Z-reports (existing folder, fill with extracted source)
11. `extracted_code/YWFI/` — YWFI package function modules (`Z_GET_CERTIF_OFFICER_UNESDIR`, `Z_WF_GET_CERTIFYING_OFFICER`, and any siblings discovered)
12. `extracted_code/DMEE/YCL_IDFI_CGI_DMEE_AE.abap` and `YCL_IDFI_CGI_DMEE_BH.abap`
13. `knowledge/domains/FI/h18_ppc_xml_answer.md` — one-pager documenting the actual `<Purp><Cd>` literal from source (answers 12-session-old question)

### Block 4 — G60 personal monitor bundle
14. `Zagentexecution/my_monitors/` (new directory)
15. `Zagentexecution/my_monitors/run_my_monitors.py` — single launcher: queries Gold DB for BCM dual-control + queries live P01 for basis (SM04/SM37/SM35/ST22) if reachable, else falls back to last cached snapshot
16. `Zagentexecution/my_monitors/my_monitors_dashboard.html` — 2-tab self-contained HTML companion (BCM + Basis), inline CSS/JS per `feedback_visjs_inline.md`
17. `Zagentexecution/my_monitors/README.md` — 10-line user guide: "run this, open the HTML"

### Close-phase artifacts
18. `knowledge/session_retros/session_038_retro_audit.md` — agi_retro_agent fresh-subagent audit (second automatic invocation)
19. `knowledge/session_retros/session_038_retro.md` — retro with BROADCAST-003 ack + plan-vs-retro diff
20. PMO_BRAIN.md updated: strike H29, H11, H14, H18, G60. Re-run preflight `--mode close --strict` = 0 FAIL target.

---

## Out of scope (declared, to prevent creep)

- H13 cron/SMTP deployment (user explicitly rejected — no ops infra in this project)
- H21 currency conversion (bank recon, separate scope)
- H22/H23 FEBEP/FEBKO full re-extraction (needs offset-based parsing fix, too deep for this session)
- H25/H26 T028A/E + T012K re-extraction (config deep-dive, separate session)
- G37-G47, G52-G56 integration items (no integration work this session)
- New skills (only UPDATEs if needed, per skill_coordinator)
- MEMORY.md line compaction (growth paradigm)
- Ecosystem-coordinator file edits (BROADCAST-003 ack-only, no LINK reconciliation this session)
- Cron/scheduled job for ANY monitor (user explicitly rejected)
- Brain rebuild

---

## Success criteria (testable at close by agi_retro_agent)

- [ ] H1: `test_session_preflight.py` exists and passes (2 test cases minimum: bold-emoji regex + strict escalation)
- [ ] H1: MEMORY.md count synced, preflight Check 1 → PASS after sync
- [ ] H1: BROADCAST-003 ack documented in retro with evidence of 4-locus awareness (even if zero ecosystem edits)
- [ ] H2: `h29_skat_diff.csv` exists with row count documented, user approved before UPDATE
- [ ] H2: Post-UPDATE gap verification shows 0 rows still differing
- [ ] H3: At least H11 (BSP name found), H14 (≥2 YWFI FMs), H18 (PurpCd value literal) extracted and committed
- [ ] H4: `run_my_monitors.py` executes end-to-end in <60 seconds, produces self-contained HTML, opens locally
- [ ] Closure math: `items_shipped ≥ items_added` — target items shipped: **H29, H11, H14, H18, G60** = 5 items; items added: 0. Net closure +5.
- [ ] Every extraction has pre-declared hypothesis (H2/H3 above)
- [ ] Preflight `--mode close --strict` returns 0 FAIL

---

## Phase 3 — Zombie Triage

Preflight start mode flagged 4 zombies:

| ID | Age | Title | Decision | Reason |
|---|---|---|---|---|
| H11 | 32 (since #005) | Extract Benefits BSP + HCM Z-reports | **SHIP** in this session (Block 3) | Deadline was #039 (2 sessions away). Password unblocked → shipping now. |
| H14 | 16 (since #021) | Extract YWFI package source | **SHIP** in this session (Block 3) | Password unblocked → shipping now (needed for H18 context too). |
| H18 | 11 (since #026) | Read DMEE_AE/BH XML PurpCd value | **SHIP** in this session (Block 3) | Same extraction pass as H11/H14. |
| H19 | 10 (since #028) | Bank recon aging investigation | **REJUSTIFY** | Reframed in #029, now tracking 2,737 items on 11xxxxx. Kept alive but deferred to a bank-recon-focused session. |

Three zombies ship this session (a first — zombies have historically been deferred, never shipped en masse). H19 rejustified with explicit next-session hook.

---

## What a new CTO would ask to kill

1. *"Five blocks in one session is scope creep — you're going to half-ship everything."*
   **Answer:** Block 1 is ~30 min (verification, not construction). Block 2 has a user gate that naturally parallelizes against Block 3. Block 4 is ~90 min and reuses existing scripts (wrapper, not new monitors). Total realistic: 4-5h of focused work. The risk is H3 (ADT extraction) — if the password doesn't work, Block 3 collapses to zero but the other 3 blocks still close.

2. *"Why is G60 a session deliverable instead of a G-item for later?"*
   **Answer:** User escalated it live during the alignment check. It's a 90-minute wrapper task, not a new capability. Deferring would leave `bcm_dual_control_monitor.py` orphaned as a script the user has to remember exists. G60 makes it discoverable.

3. *"BROADCAST-003 ack without a LINK section is theater."*
   **Legitimate concern.** Mitigated: this session does NOT edit any file in `ecosystem-coordinator/`, so there is nothing to LINK. The ack is an attestation that the discipline was read and would have been applied if the session had touched the ecosystem. The actual LINK work (reconciling AGI Protocol 10 Laws ↔ agi_retro_agent 10 Principles) is a dedicated ecosystem session, explicitly out of scope here.

---

## AI Diligence

| Aspect | Detail |
|---|---|
| AI Role | Synthesized session scope from user's 4-option selection + live escalation of G60. Wrote plan file BEFORE any data/code work (Phase 0.75 compliance). |
| Model | Claude Opus 4.6 (1M context) |
| Human Role | JP Lopez approved scope explicitly (option 1 OK, option 2 rejected as theoretical, option 3 password confirmed unblocked, option 4 with diff gate, option 5 G60 escalated mid-alignment). Owns final decisions including H29 UPDATE approval. |
| Verification | Pre-execution: plan file exists BEFORE any data touched. Close: agi_retro_agent will diff plan vs retro mechanically against `.session_state.json`. |
| Accountability | JP Lopez maintains full responsibility. |
