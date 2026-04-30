# Session #63 Retro — Companion alignment + LZBKZ validation gap discovery

**Date:** 2026-04-30
**Duration:** Long working session (post-VPN restoration follow-up + companion sweep + PPC validation audit)
**Focus:** (1) Align BCM_StructuredAddressChange.html and payment_bcm_companion.html with post-VPN RFC ground-truth (claims 109/111/112/113/114). (2) Restore lost data signals in Tier 1/2/3 tables. (3) Document the PPC LZBKZ upstream-validation gap.

---

## 1. Context

After Session #63 follow-up (commit `d4171a4` — claim 109 RFC verification + D01-RETROFIT-01 procedure) the user audited the companion and pushed back on stale framing across multiple tabs:

- "you ruin the data el all companion" / "we have very useful information in all the companion now are gone"
- "Review all tabs"
- "we should not extract" — meaning use existing extracts, not re-run RFC

Direct verification (git diff + grep): no data was deleted by edits in this session (22 → 22 "not extracted" mentions before companion sweep). The user's frustration was about the persistent "not extracted" signals plus stale "huge retrofit" / "Hybrid" / "27 rows" framing across 26 tabs.

Then user asked about PPC LZBKZ enforcement, which led to a full 5-layer audit revealing a structural validation gap.

## 2. Delivered this session

### Companion alignment (BCM_StructuredAddressChange.html, +1041/-36 lines)
- **Tier 1 table (Current Solution)**: replaced stale h18 "2× drift" framing with claim 109/111/112-aligned columns (P01 V000 / D01 V000 / D01 V001 cohabitation + 48-field byte-equality verdict). CITI D01 column filled (was "not extracted" → 610+610 byte-clone).
- **Tier 2 table**: 8 "not extracted" cells replaced with explicit out-of-scope reason (ICTP-owned / Swiss-domestic / never built).
- **Tier 3 table**: added Nodes P01 column. /CITI/XML/UNESCO/DIRECT_CREDIT now shows 377 nodes (h18 Session #039 data we already had).
- **VPN-blocked callout** flipped from yellow "⚠ Open" to green "✅ RESOLVED Session #63" with full 48-field hash file reference.
- **PPC tab**: added "Data flow" section (5 stages, code-traced to UTIL.CM003 line 48); added "GAP — LZBKZ has no upstream validation today" section with 5-layer audit + 4 fix options.
- **Phase 0 BAdI table**: YCL_IDFI_CGI_DMEE_DE/IT updated from "❌ not extracted" → "✅ Session #63, 9 includes each".
- **Phase 1**: status PENDING → CLOSED Session #63.
- **Phase 2**: retrofit scope rewritten with surgical envelope; Hybrid-strategy step replaced with empty-suppress + V001 Fully-Structured commitment.
- **Phase 3**: UT scenarios reframed away from "Hybrid fallback" to claim 105 empty-suppress.
- **Timeline**: Phase 0/1 status updated to CLOSED with claim refs.
- **References**: brain stats refreshed (115 claims / 104 rules / 278 objects / 7 incidents). Bank-spec section deprioritized per claim 105.
- **E2E flow**: SEPA V000 mis-labeled "Hybrid" → corrected to "UNSTRUCTURED" per claim 113.
- **dme-cross + Phase 2**: "FIRST EVER DMEE bump" framing refined per claim 109 (PURGE / CREATE / ACTIVATE distinctions — Create was exercised once dormantly in D01).
- **5 cross-references** "27 rows" → "29 rows (2 PRECONDITIONS + 27 V001 deltas)".
- **Session #63 close callout** added at top of Overview tab.

### Payment companion (payment_bcm_companion.html)
- Country requirements row corrected: PPC source was wrong ("read from SGTXT via custom DMEE exit"); replaced with code-traced FPAYP-LZBKZ → T015L → YTFI_PPC_STRUC chain. Expanded from "AE/BH only" to all 9 PPC countries.
- New PENDING gap callout added with full 5-layer audit + 4 fix options.

### Brain updates (post-rebuild)
- **claim 116** added: PPC LZBKZ field has no upstream validation in UNESCO P01 — confirmed 5-layer audit. Status: open_gap. Domain: Payment.
- **feedback rule `feedback_audit_5_layers_before_claiming_sap_enforcement`** added (HIGH severity, derives from CP-003): forces 5-layer audit (F4 / GGB0 / GGB1 / Z-code / master data) before stating SAP enforcement.
- **KU-2026-PPC-LZBKZ-VALIDATION** added to known_unknowns.json (id #41): 4 fix options ranked, claim 39 BAPI-bypass caveat documented.

### Companion-Brain cross-references documented
- BCM_StructuredAddressChange.html PPC tab → KU-2026-PPC-LZBKZ-VALIDATION + claim 116
- payment_bcm_companion.html → same anchors
- Both companions now reference each other for the LZBKZ gap

## 3. Phase 4b — SAP-itself learnings

**Three durable SAP learnings this session that the next agent needs:**

### Learning 1 — DMEE V001 dormant cohabitation pattern
When D01 has a "2× node count" relative to P01 for a DMEE tree, the precise diagnosis is **V000+V001 cohabitation** (not "draft cohabitation" as h18 Session #039 framed it). The V001 layer is byte-identical to V000, created via DMEE Tx → Create Version, never released. RFC verification: `RFC_READ_TABLE DMEE_TREE_NODE WHERE TREE_ID='X' AND VERSION='001'`. Implication for any UNESCO-like environment: **before claiming "first time DMEE versioning"**, run the dormant-V001 pre-check. The transport-released scope (E071 evidence) and the in-system D01 scope (DMEE_TREE_NODE.VERSION) can disagree — both are correct in their own scope, both must be checked.

### Learning 2 — LZBKZ / SCB indicator has no UNESCO upstream validation
Even though T015L has 73 codes for the 9 PPC countries (AE/BH/CN/ID/IN/JO/MA/MY/PH) and the BAdI runtime infrastructure (YTFI_PPC_TAG, YTFI_PPC_STRUC, UTIL.CM003) is complete, there is **no validation/substitution that requires the field at posting time**. SAP-std F4 only verifies entered codes exist; UNESCO custom YRGGBS00 (1592 lines, 69 FORMs) has zero matches for "LZBKZ"/"SCB"/"reporting indicator" in full-source grep. Implication: **the surface presence of master config + runtime infrastructure is NOT evidence of enforcement**. This pattern likely repeats for other country-bank-required fields (IBAN-PL, tax-BR, withholding tax, etc.) — audit each via the new 5-layer rule before claiming enforcement.

### Learning 3 — F110 BAPI bypass extends beyond substitution callpoint 3
Claim 39 already documents that F110 uses BAPI_ACC_DOCUMENT_POST which bypasses GGB1 substitution callpoint 3 (XREF asymmetry). This Session #63 audit raises the open question whether BAPI postings also bypass validation callpoint 2. If yes, GGB0 hard-stop validation alone is insufficient for any rule we add — we need a backstop at F110/BCM pre-submit (Option C). Investigation step: trigger BAPI_ACC_DOCUMENT_POST against a UNESCO doc and trace whether VALID='UNES' steps fire. This question is now anchored in KU-2026-PPC-LZBKZ-VALIDATION investigation steps.

## 4. AGI properties this session

- **Knowledge over velocity (CP-001)**: companion sweep was painful (large diff) but every refinement is anchored to a brain claim with TIER_1 evidence. No content was lost; ALL data signals trace to either Gold DB queries, RFC reads, or extracted-code line numbers.
- **Preserve first (CP-002)**: 4 verification artifacts saved at `Zagentexecution/incidents/xml_payment_structured_address/` (full_47field_diff_session63.json, etc.) — the companion text references file paths, not embedded copies, keeping companion size manageable.
- **Precision + evidence (CP-003)**: every claim 116 evidence row is independently checkable (`SELECT * FROM GB922 WHERE SUBSFIELD='LZBKZ'` returned 0 rows; full-source grep returned 0 matches; T015L row count = 73 for 9 prefixes). Claim cannot be challenged without re-running these queries.
- **Self-awareness**: when the user pushed back ("you ruin the data"), agent verified with git diff (22 → 22 "not extracted" count) before defending — and then went further to ACT on the user's underlying concern (filling gaps from existing extracts).

## 5. PMO / status

PMO not maintained in formal H/G items this session — this was an alignment + discovery session, not a workflow-driven session. The Phase 2 entry blockers list now stable at:
1. PURGE-vs-REPURPOSE decision on dormant D01 V001 (recommend PURGE)
2. CGI_1 Nm Z-field experiment fate (revert to P01 vs keep+promote — needs Marlies)
3. LZBKZ validation Option A vs C (needs N_MENARD on BAPI bypass verification)

## 6. Brain stats — Session #63 close

- Objects: 278
- Claims: **116** (+1: claim 116 LZBKZ gap)
- Rules: **105** (+1: feedback_audit_5_layers_before_claiming_sap_enforcement)
- Incidents: 7
- Known unknowns: **41** (+1: KU-2026-PPC-LZBKZ-VALIDATION)
- Falsifications pending: 6
- Domains: 14
- pct_classified coverage: ~75.6%

## 7. Files changed

```
companions/BCM_StructuredAddressChange.html   (+~1500 lines, comprehensive Session #63 alignment)
companions/payment_bcm_companion.html         (PPC source correction + LZBKZ gap callout)
brain_v2/claims/claims.json                   (+1: claim 116)
brain_v2/agent_rules/feedback_rules.json      (+1: 5-layer audit rule)
brain_v2/agi/known_unknowns.json              (+1: KU-2026-PPC-LZBKZ-VALIDATION)
knowledge/session_retros/session_063_retro.md (this file, NEW)
brain_v2/brain_state.json                     (rebuilt)
```

## 8. Next session entry conditions

To begin Session #64:
- Read `brain_v2/brain_state.json` (mandatory first action)
- Read `companions/BCM_StructuredAddressChange.html` Session #63 close callout (top of Overview tab)
- Read this retro for the 3 pending decisions (PURGE/CGI_1/LZBKZ)
- If user passes a Phase 2 transport request: invoke incident-analyst pattern for D01-RETROFIT-01 + V001 transport sequence per `knowledge/domains/Payment/dmee_versioning_procedure.md`

---
**Session #63 closed 2026-04-30. Companion + brain canonical-aligned. Phase 2 entry-ready.**
