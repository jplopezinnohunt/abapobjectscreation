# Phase 2 Readiness Checklist · UNESCO BCM Structured Address V001

**Created**: 2026-04-30 (Session #63 close) · **Owner**: Pablo + Marlies · **Brain anchor**: claims 99/96/101/102/103, plan §Open architectural decisions L1098-1107, KU-2026-063-* series

**Purpose**: single-page status before Phase 2 (May 2026) begins. Every row is one decision, deliverable, or open item with explicit owner + status + brain anchor.

---

## A · Plan §Open architectural decisions (5 originally — 4 closed by Session #63 close)

| # | Decision | Owner | Status | Anchor / next step |
|---|---|---|---|---|
| A1 | ~~Per-bank strictness (Hybrid vs Fully-Structured per receiving bank)~~ | — | **CLOSED Session #63 (2026-04-30)** | V001 ships Fully-Structured (5 tags + empty-suppress conds for missing data). Fully-Structured strictly satisfies any CBPR+ bank strictness ≥ Hybrid by ISO 20022 schema definition. Simulator 794/794 PASS on .03+.09 schemas confirms. Brain claim 105 TIER_1. TRM emails reduced from 9-question gating to 1-page logistics (sample-attached + cutover-window + PPC FYI). |
| A2 | BAdI overflow logic fate (keep / deprecate / refactor) | N_MENARD | **OPEN** — Phase 3 dependent | Decision deferred to Phase 3 unit-test results. Pattern A guard (claim 96 SocGen-mandated) preserves V000 behavior; longer-term refactor only if SocGen relaxes the requirement (Q3 in simplified SocGen TRM logistics email). |
| A3 | D01 draft purge on CGI trees (2× node delta vs P01) | Pablo + Francesco | **PARTIAL** — Francesco audit done | Francesco's 5 transports (2025 Q1) classified ASSIST/IRRELEVANT (PMF variants only, never SEPA/CITI). Pre-Phase-2 alignment call still recommended (per `feedback_propagate_q_resolution_to_all_sections`). KU-063-01 (AE/BH classes in P01) remains for direct verification when VPN is up. |
| A4 | ~~UltmtCdtr Worldlink data source~~ | — | **CLOSED Session #62** | Q3 RESOLVED system-driven (claim 99). 7 active source fields confirmed via DMEE_TREE_NODE analysis. UltmtCdtr unified into V001. |
| A5 | ~~Separate PMW formats per entity (IIEP/UIL/UBO/UIS)~~ | — | **CLOSED Session #63** | Gold DB query confirmed T042Z has no ZBUKR column; per-entity differentiation is in T042A (HBKID per ZBUKR). No separate Event 05 work needed. Brain claim 103 TIER_1. |

**Pattern across A1+A4+A5 closures**: third instance of system-internal evidence superseding external SME ask. Captured as new feedback rule `feedback_prefer_system_internal_to_external_sme` HIGH (Session #63).

---

## B · Phase 1 deliverables (per plan §Phase 1 L731-784)

| # | Deliverable | Owner | Status | Path / next step |
|---|---|---|---|---|
| B1 | Change matrix signed (0 UNKNOWN rows) | Pablo (drafter) + Marlies (sign) + N_MENARD (sign for ABAP row) | **DRAFT READY** — needs sign-off | `knowledge/domains/Payment/v001_change_matrix.csv` (27 rows, all rationale-anchored). Companion tab "V001 Change Matrix" renders it. |
| B2 | ~~Bank specs received per receiving bank~~ | Marlies | **DOWNGRADED to logistics (claim 105)** | Per A1 closure — V001 Fully-Structured eliminates spec-gathering need. TRM emails reduced to 1-page logistics (sample-attached ack + cutover-window + PPC FYI). Send when ready; non-blocking for Phase 2 start. |
| B3 | D01 retrofit transport (5 P01-only objects synced D01 ← P01) | Pablo | **NOT STARTED** — VPN-blocked 2026-04-30 | Per Phase 2 §Step 0 D01-RETROFIT-01. Needs VPN + extraction → diff → transport. Upstream of all Phase 2 work. |
| B4 | Q3 UltmtCdtr resolved | — | **DONE Session #62** | claim 99. |
| B5 | Vendor DQ: 5 vendors fixed | Master Data team | **NOT STARTED** | Row 27 of change matrix. LIFNRs: 0000020171, 0000020731, 0000020815, 0000020843, 0000059828. Manual fix CITY1+COUNTRY in ADRC OR set LOEVM='X'. |
| B6 | N_MENARD alignment call (BAdI Pattern A review) | Pablo + N_MENARD | **NOT STARTED** | Pre-Phase-2 prerequisite. Reviewer for transport `D01K-BADI-FIX-01`. |
| B7 | Francesco alignment call (CGI tree V001 disclosure) | Pablo + Francesco | **NOT STARTED** | Pre-Phase-2 prerequisite per plan §line 1080. Disclose V001 CdtrAgt fix doesn't overwrite his PMF variant work. |

---

## C · Phase 2 prerequisites (must close before May 2026 start)

| # | Item | Status | Why it matters |
|---|---|---|---|
| C1 | DMEE versioning dry-run completed | **NOT STARTED** | First ever DMEE version bump at UNESCO (claim 102). Needs SAP GUI auth check + step rehearsal. Procedure: `knowledge/domains/Payment/dmee_versioning_procedure.md`. |
| C2 | Transport ID assignment confirmed | **DRAFT READY** | 8 transports planned (see V001 Change Matrix tab "Transport packaging" table). M_SPRONK + Pablo confirm naming convention. |
| C3 | Z-payment method created for V001 routing (test isolation) | **NOT STARTED** | Per plan §Phase 2 sequencing line 569. Phase 3 test scenarios route via Z-method to V001; production runs via standard methods to V000. |
| C4 | Phase 1 deliverables B1-B7 closed | **MIXED** | Hard prerequisite. Track via this table. |
| C5 | VPN + RFC connection to D01 + P01 verified working | **BLOCKED 2026-04-30** | Both 172.16.4.66:00 (D01) and 172.16.4.100:00 (P01) unreachable today. Per `feedback_auto_reconnect_vpn` recovery path. |

---

## D · Open KUs / Data Quality (V001-relevant only)

| ID | Priority | Question | Resolution path |
|---|---|---|---|
| KU-2026-063-01 | LOW (downgraded) | AE/BH classes in P01 (TADIR present?) | Gold DB cts_objects: only 1 entry each (D01K9B0BN9 2024-03-26). Direct RFC TADIR probe pending VPN. Not blocking V001. |
| KU-2026-063-03 | LOW | DMEE node-level forensics for historical transports | Not blocking V001. Open only if Phase 4 regression needs deeper history. |
| KU-007 | ? | PurposeCode XML output value confirmation | Phase 3 test — read REGUC.VARDATA or DTA file for AE/BH/CN/ID/IN/JO/MA/MY/PH country payments and verify PPC tag content matches YTFI_PPC_STRUC + T015L expected algorithm output. |
| KU-009 | ? | Which method in YCL_IDFI_CGI_DMEE_FR handles PurposeCode | **PARTIALLY ANSWERED** — claim 96 + transport D01K9B0BYP (2024-07-03, GET_TAG_VALUE_FROM_CUSTO method) is the dispatcher entry. Method = CM002 in P01, CM001 in D01 (D01-RETROFIT-01 closes). |
| KU-011 | — | T042Z DMEE_ASSIGNMENT_TABLE column missing | **CLOSED Session #63** as DQ-2026-063-04. The hypothetical column doesn't exist in standard SAP T042Z schema. |

---

## E · Concrete artifacts produced this session (Session #63 close)

| Artifact | Path | Purpose |
|---|---|---|
| V001 Change Matrix CSV | `knowledge/domains/Payment/v001_change_matrix.csv` | Phase 1 deliverable B1 (signed change matrix). 27 rows. |
| Companion tab "V001 Change Matrix" | `companions/BCM_StructuredAddressChange.html` (new tab `tab-matrix`) | Visual rendering of CSV + transport packaging table |
| DMEE Versioning Procedure | `knowledge/domains/Payment/dmee_versioning_procedure.md` | Phase 2 Week 1 operational steps (first ever version bump) |
| TRM email drafts (3 banks) | `Zagentexecution/incidents/xml_payment_structured_address/trm_outreach_drafts/` | A1 prerequisite material |
| Phase 2 Readiness Checklist | this file | Single-page status (you are reading it) |
| Transport classification CSV | `Zagentexecution/incidents/xml_payment_structured_address/transport_classification_44.json` | Brain claim 101 evidence — 44-transport E071 breakdown |
| Transport detail E071 CSV | `Zagentexecution/incidents/xml_payment_structured_address/transport_detail_e071.json` | Per-transport object-level "what changed" |

---

## F · Brain state at Phase 1 close (for handoff)

- **103 claims** TIER_1 (latest: 102 surgical+versioning, 103 per-entity routing)
- **100 feedback rules** (latest: `feedback_companion_edits_must_be_brain_anchored` CRITICAL, `feedback_propagate_q_resolution_to_all_sections` HIGH)
- **35 open KUs** (most unrelated to V001; the 5 V001-relevant ones in section D above)
- **6 falsification predictions pending**
- **15 superseded claims** (anti-regression)
- **0 open user_questions**
- **8 data quality items** (1 closed Session #63: DQ-063-04 T042Z column)

Brain status: FRESH (rebuilt 2026-04-30).

---

## G · What stops V001 ship today (gating blockers — TOP item escalated 2026-04-30)

**Per claim 108 (D01 2× cohabitation drift TIER_1) + new CRITICAL rule `feedback_p01_source_of_truth_retrofit_first_then_adjust`** — the gating order is reshaped:

0. **D01-RETROFIT-01 (P01 source-of-truth → D01 byte-alignment)** — **TOP GATING (CRITICAL)**. ~~h18 Session #039 indicated 2× cohabitation pattern interpreted as "draft V001+ never transported".~~ **REVISED 2026-04-30 post-VPN RFC verification (claims 109 + 111)**: the 2× pattern is precise V000+V001 cohabitation — D01 has explicit `DMEE_TREE_NODE.VERSION=001` rows on all 4 trees as byte-identical clones of V000. P01 has only V000. Someone ran DMEE Tx → Create Version then never edited or released. **Net retrofit work**: SEPA / CITI / CGI all D01 V000 byte-equal to P01 V000 (zero deltas) — no work. Only CGI_1 needs 12-node surgical fix (1 ONLY_D01 SCB purge + 8 ONLY_P01 AdrLine restore + 3 CHANGED with 2 BROTHER_ID consequential + 1 substantive Nm Z-field experiment to revert). Plus: dormant D01 V001 cleanup (delete + recreate fresh) on all 4 trees. **Total effort ~1-2 hours**. Single transport `D01K-RETROFIT-01`. **Reference**: companion Current Solution tab (refined RISK callout), `dmee_retrofit_procedure.md` (revised surgical procedure), `d01_p01_v000_diff_session63.json` (12-delta detail).
1. **VPN/RFC connectivity** to D01+P01 — **STILL GATING (enabler for #0)**. Unreachable as of 2026-04-30. Without VPN, retrofit cannot execute. But VPN alone is not enough — even with VPN, retrofit is the actual blocker.
2. **Master Data team execution of B5** — **STILL GATING (parallel)**. 5 vendor fixes (LIFNRs known; trivial work, parallel to retrofit).

**Downgraded to coordination (not gating)**:

3. ~~Bank TRM responses (A1)~~ → CLOSED via V001 Fully-Structured commitment + simulator validation (claim 105). 1-page logistics emails sent FYI; Phase 2 proceeds without responses.
4. ~~N_MENARD alignment call (B6)~~ → coordination only. Pattern A 3-line guard is reviewer-trivial (transport `D01K-BADI-FIX-01` carries 1 method + 3 lines). Schedule before Phase 2 W2 transport landing, not before Phase 2 W1 V001 tree work.
5. ~~Francesco alignment call (B7)~~ → coordination only. His 5 PMF-variant transports (2025 Q1) don't overlap V001 tree CdtrAgt fix; courtesy disclosure is enough.

**If blockers 1+2 close, Phase 2 starts.** No external response wait.

---

## H · Decision log (snapshot per CP-001 preserve-first)

- 2026-04-24 · Hybrid coexistence rejected · 2-file + DMEE versioning adopted · plan §line 502
- 2026-04-29 · Q3 RESOLVED system-driven · UltmtCdtr unified into V001 · claim 99
- 2026-04-29 · Pattern A SocGen-mandated confirmed · 3-line guard locked · claim 96
- 2026-04-29 · Q1bis RESOLVED · CM002 = PPC dispatcher entry, retrofit needed in D01-RETROFIT-01
- 2026-04-30 · A5 closed · per-entity routing uniform · claim 103
- 2026-04-30 · DQ-063-04 closed · T042Z extraction complete (no missing column)
- 2026-04-30 · KU-063-01 priority downgraded MEDIUM → LOW · Gold DB cts_objects evidence
- 2026-04-30 · A1 closed · V001 Fully-Structured commitment + simulator 794/794 PASS · claim 105
- 2026-04-30 · `feedback_prefer_system_internal_to_external_sme` HIGH rule added · pattern from A1+A4+A5 closures
- 2026-04-30 · TRM emails reduced from 9-question gating to 1-page logistics (3 banks) · sample-attached ack + cutover + PPC FYI
- 2026-04-30 · Phase 2 gating blockers reduced 5 → 2 (VPN + Master Data 5-vendor fix only)
- 2026-04-30 · D01 2× cohabitation drift escalated to TOP gating blocker · claim 108 TIER_1 + new CRITICAL rule `feedback_p01_source_of_truth_retrofit_first_then_adjust`. Step 0 D01-RETROFIT-01 scope expanded from "5 P01-only ABAP objects" (Finding I) to "full byte-alignment of all 4 DMEE trees + 5 ABAP objects". Recommended Option A: purge D01 + re-import from P01.
- 2026-04-30 · VPN restored mid-session · RFC verification on D01+P01 DMEE_TREE_NODE · claim 108 SUPERSEDED by claim 109 + 111: D01 has explicit V000+V001 cohabitation (V001 dormant clone of V000), not random drift. 3 of 4 trees byte-equal D01 V000 = P01 V000; only CGI_1 has 12 deltas. Retrofit scope reduced from "huge multi-tree" to "~1-2 hours surgical (CGI_1 + dormant V001 cleanup)". Companion Current Solution + Evolution Pattern 2 + retrofit procedure refreshed.
- 2026-04-30 · Marlies Excel `BCM_StructuredAddress_Analysis.xlsx` (19 sheets) role formalized as historical snapshot 2026-04-24 + sign-off-format · claim 110 TIER_1.
- 2026-04-30 · CBPR+ ISO 20022 PstlAdr classification methodology established · claim 113 TIER_1. Per-tree per-party V000 state derived from system-data leaf inventory (not Marlies-comments). Companion Change Strategy tab updated with "Understanding the problem" section.
- 2026-04-30 · Methodology rule: Truth = System Data + Bank Requirements (CBPR+) · Marlies file = sample validation · claim 114 TIER_1.
- 2026-04-30 · Hard-stop rejection-risk parties identified under V000 today: 4 (SEPA Cdtr · SEPA Dbtr · CITI Dbtr-altMor · CGI CdtrAgt). Hybrid+ at future-proof risk: 3 (CITI Dbtr-primary · CITI UltmtCdtr · CITI CdtrAgt). V001 lifts all 7 to Fully Structured.
- 2026-04-30 · V001 Change Matrix updated with Step-0 PRECONDITION rows (0a + 0b): retrofit + dormant V001 purge + fresh Create Version BEFORE matrix rows 1-25 apply. CSV now 29 rows total (was 27).
- 2026-04-30 · DMEE versioning procedure Step A revised: PURGE dormant D01 V001 first + CREATE fresh — recovers clean transport-trail.

---

**Sign-off block** (to be filled when ready):

- [ ] Pablo Lopez (SAP config) · date __________ · signature __________
- [ ] Marlies Spronk (Treasury, DMEE SME) · date __________ · signature __________
- [ ] Nicolas Ménard (BAdI code, ABAP review) · date __________ · signature __________ (row 26 only)
- [ ] DBS (technical readiness) · date __________ · signature __________
