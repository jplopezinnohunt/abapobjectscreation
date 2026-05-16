# Session #74 Retro — Multi-format SEPA closure + DFPAYG/DFPAYV reverse engineering + drift forecast

**Date:** 2026-05-09 → 2026-05-11
**Duration:** Multi-day spanning context compression
**Focus:** (1) Close `/SEPA_CT_UNES` validation across all KTOKKs via SQL replay. (2) Extract `DFPAYG` (execution evidence) + `DFPAYV` (config matrix) to Gold DB. (3) Map per-format address-resolution path for the 5 active SEPA/CGI/CITI trees. (4) Quantify the staff-address bug surface across the full UNESCO payment landscape. (5) Capture 6 TIER_1 claims, 9 annotations, 5 feedback rules.

---

## 1. Context

User asked to close out `/SEPA_CT_UNES` empirically (not just BERTOLDINI live test) and then evaluate the OTHER formats for the same structured-address bug. The session pivoted into a full payment-landscape reverse-engineering exercise — what tables prove what was paid, what formats configured, what addresses actually emitted per leaf per party.

Key inflection points driven by user:
- "**Podemos hacer una comparación de donde y como guarda adress**" — initiated the per-format Cdtr vs Dbtr address source comparison.
- "**Whith that we can know exact the esnarios to test for each foramt**" — DFPAYG promoted from grep-output to canonical scope tool.
- "**OK but are you sure that this all all format used?**" — caught me presenting 7 active formats from a 2-year window when older history (2017-2019) had 4-5 retired formats (CMI101, DIRECT_CREDIT). Pushed to verify scope.
- "**Tomemos 2025 2026 entonces**" — narrowed window from 2-year rolling to calendar 2025-2026 for cleaner status snapshot.
- "**A esto agreaga compania medio de pago banco cuenta y columnad de vendors no staff**" — demanded full per-tuple breakdown by ZBUKR×HBKID×HKTID×RZAWE.
- "**O faltan las columnas, Company code, house bank bank Account, and mediunm payment please**" — explicit ask for business column names (not technical abbreviations).
- "**Now I need to test /CITI/XML/UNESCO/DC_V3_01**" → "**Now give me a test for /CGI_XML_CT_UNESCO**" → "**no payment were selected**" — testing infrastructure hit a XVORL='X' proposal-mode block in D01. Escalated to options: DMEE Test Mode vs patch ZSAPFPAYM_REPLAY.
- "**no cambien nunca estos formatos como peude ser que funcione**" — caught me reporting drift for ICTP formats that don't even wire `Y_FI_DMEE_ADR`. Forced theoretical-vs-in-scope separation in the simulator output.
- "**a que se denomina staff drift**" → "**O sea son las cantidades de pagos staff que se hacen para ese formato**" — exposed ambiguity between "distinct staff vendors" and "REGUH payment lines" (5-30x factor).

---

## 2. Delivered this session

### Gold DB extensions
- **`DFPAYG`** — 9,848 rows (LAUFD >= 2024-05-09). F110 payment medium grouping. Joined with `REGUH` it becomes the audit trail of "which payment format was actually used for which run for which vendor."
- **`DFPAYV`** — 84 rows (full config). Static matrix mapping (FORMI, ZBUKR, BANKS, HBKID, HKTID, CRDEB, RZAWE) → VARI selection variant.
- New indexes: `idx_reguh_run` on REGUH(LAUFD,LAUFI,ZBUKR); `idx_dfpayg_formi`; `idx_dfpayg_zbukr`.
- **`sim_v6_results`** — `/SEPA_CT_UNES UNES` simulation: 14,636 LIFNRs, 1,813 drift, 0 theory violators.
- **`sim_sepa_all`** — all SEPA formats: 21,507 tuples, 1,986 drift, 0 violators.
- **`sim_all_formats`** — full landscape drift forecast: 61,476 tuples, 5,686 drift forecast across 7 formats.

### Knowledge docs
- `knowledge/domains/Payment/vendor_address_routing_by_ktokk.md` — extended with empirical closure section (15,305 vendors / 1,905 drift) and ICTP scope clarification.
- `knowledge/domains/Payment/e2e_vendor_payment_to_medium.md` (NEW) — 8-step E2E chain from vendor master → payment medium output, with Gold DB anchors per step.

### Companion `BCM_StructuredAddressChange.html`
- New tab "🆕 Vendor Address Routing (KTOKK / PA0006)" with full closure table (UNES + IIEP + UIL cocodes), tree-wiring scope table, 6 sample drift rows (BERTOLDINI-like cases), ICTP out-of-scope note. Sidebar entry added between Tree 4 and Matrix.

### Brain updates

**6 new TIER_1 claims (184-189):**
- **184** — Multi-format drift forecast: 5,686 staff drift cases system-wide; v6 covers 33.5% (1,905); 3,781 remain unfixed across CGI / CITI / ICTP. Theory violators: 0 across 21,507-tuple universe.
- **185** — Per-format DMEE_TREE_NODE address-leaf inventory (line-by-line bindings for 5 active formats).
- **186** — True bug surface: SAP std `FI_PAYMEDIUM_DMEE_CGI_05` Event 05 populates FPAYHX-REF01 from ADRC blindly. Nicolas `YCL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT` only handles Nm overflow — NOT address override.
- **187** — PPC framework status: dispatched from FR class but DORMANT (zero FR rows; only narrative tags configured).
- **188** — Alt-payee resolution semantics: `FPAYH-GPA1R` holds resolved payee LIFNR; v6 handles correctly by construction. ICVS VS90* NUMC8 cast risk is theoretical only.
- **189** — 7 active formats over last 2 years; 6 lapsed configs in DFPAYV (CMI101, DIRECT_CREDIT, CITI_XML_MASTER, DTAZV, SEPA_CT, SETIF, Z_SEPA_CT_DB_XML).

**9 new annotations:**
- `DMEE_TREE_NODE` — topology table semantics + RFC_READ_TABLE quirks.
- `FI_PAYMEDIUM_DMEE_CGI_05` — SAP std Event 05 (the bug root).
- `FI_CGI_DMEE_EXIT_W_BADI` — BAdI dispatcher (passes through to Nicolas's class).
- `YCL_IDFI_CGI_DMEE_FALLBACK` — Nicolas's fallback (read-only per rule).
- `YCL_IDFI_CGI_DMEE_UTIL` — PPC framework dispatcher.
- `YTFI_PPC_TAG` — 11 rows for 9 non-UNESCO countries.
- `YCL_IDFI_CGI_DMEE_FR` — FR country class that calls PPC.
- `/CITIPMW/V3_GET_CDTR_BLDG` — Citi proprietary FM (cannot modify).
- `FPAYHX-REF01` — byte-structured buffer populated from ADRC.

**5 new feedback rules:**
- `feedback_verify_dmee_tree_wiring_before_assuming_fix_scope` (HIGH) — Y_FI_DMEE_ADR scope is bounded by tree wiring, not FM availability.
- `feedback_dfpayg_dfpayv_are_payment_audit_trail` (HIGH) — canonical source for any payment scope/coverage question.
- `feedback_label_distinct_vendors_vs_payment_lines` (MEDIUM) — always label which scale you're reporting.
- `feedback_use_explicit_business_column_labels` (LOW) — use Company Code not ZBUKR when audience is finance ops.
- `feedback_rfc_read_table_quirks` (MEDIUM) — no IN clauses, leading-space continuation, DATA_BUFFER_EXCEEDED on wide tables.

---

## 3. Open follow-ups (carry to next session)

1. **CGI test pending** — D01 has no posted CGI run with staff. Next steps: either (a) DMEE Test Mode (tx DMEE → /CGI_XML_CT_UNESCO → Functional test) with synthetic FPAYH for KAWAKAMI, or (b) patch `ZSAPFPAYM_REPLAY` to accept XVORL='X' proposal mode (run 20230622/XML/UNES has KAWAKAMI in proposal state).
2. **CITI test pending** — same situation. Run 20220725/CITI/UNES has BISTA Min in posted CITI but the test never executed because XVORL=='X' for some lines (need to disambiguate posted vs proposal in that mixed run).
3. **CGI/CITI fix path decision** — 3,781 staff drift cases unfixed. Three options on the table:
   - Wire `Y_FI_DMEE_ADR` into CGI + CITI trees (config-only; replaces FI_CGI_DMEE_EXIT_W_BADI on address leaves).
   - Add Z BAdI impl with higher priority than `YCL_IDFI_CGI_DMEE_FALLBACK` that overrides address tags with PA0006-first detection.
   - Extend PPC framework: add FR rows to `YTFI_PPC_TAG` + new PPC_CODE value `PA0006_PAY` requires UTIL extension.
4. **`/CITIPMW/V3_*` code extraction** — Citi proprietary FMs not in Z-namespace; need to extract source to see if they read FPAYHX-REF01 or have their own ADRC path.
5. **Master data coverage gap** — 7,534 LIFNRs in CGI/CITI universe not in `_sim_univ` cache (mostly UBO cocode vendors). Drift count is therefore a lower bound. Next P01 fetch should top this up.
6. **DMEE_TREE_NODE missing from Gold DB** — currently P01 RFC only. Extracting full table to Gold DB would unlock SQL-level tree analysis without P01 round-trips.

---

## 4. Phase 4b — SAP learnings captured this session

**What did we learn about SAP itself this session that the next agent needs to know?**

1. **DFPAYG = the audit trail of medium creation.** One row per F110 group output. Every XML file produced has a DFPAYG row. Cross-references LAUFD/LAUFI/ZBUKR/HBKID/HKTID/FORMI/GRPNO and counters ANZ_ERZ/ANZ_ERL. (Claim 183, 189.)

2. **DFPAYV = the routing matrix.** Static config: every (FORMI, ZBUKR, BANKS, HBKID, HKTID, CRDEB, RZAWE) tuple → VARI selection variant. Configs that are lapsed (in DFPAYV but never in DFPAYG) are housekeeping debt, not bug surface. (Claim 183, 189.)

3. **DMEE_TREE_NODE.MP_EXIT_FUNC IS the determinant of whether a Z FM gets called for a leaf.** Direct field binding (MP_SC_TAB/FLD) and exit FM (MP_EXIT_FUNC) can coexist — when both present, exit FM wins. When exit FM blank, direct binding emits. When both blank, value stays initial. (Claim 185.)

4. **SAP std `FI_PAYMEDIUM_DMEE_CGI_05` (Event 05) is the bug origin.** It populates FPAYHX-REF01/REF02 buffers from ADRC blindly at every medium creation, for EVERY payment format. Every downstream DMEE tree that reads these buffers inherits the dept-code-for-staff defect. The fix isn't tree-specific — it's buffer-specific. (Claim 186.)

5. **`FI_CGI_DMEE_EXIT_W_BADI` is a SAP-std dispatcher, NOT a fix.** It calls country-class GET_VALUE which falls through to `YCL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT` for tags with no country override. Nicolas's FALLBACK only handles `<Cdtr><Nm>` overflow into `<StrtNm>` — does NOT read PA0006 or ADRC. Tree leaves marked as having this exit FM are effectively unprotected for staff addresses. (Claim 186.)

6. **PPC framework status (Nicolas's design).** Dispatched from `YCL_IDFI_CGI_DMEE_FR::CM002::GET_VALUE` via `YCL_IDFI_CGI_DMEE_UTIL::GET_TAG_VALUE_FROM_CUSTO`. Resolves via `YTFI_PPC_TAG` + `YTFI_PPC_STRUC` + `T015L`. Today: 11 rows in YTFI_PPC_TAG for 9 non-UNESCO countries (AE/BH/CN/ID/IN/JO/MA/MY/PH); ZERO rows for FR/DE/IT/GB/US/BR. Tags handled are narrative (<InstrInf>, <Ustrd>) — NOT address tags. PPC cannot solve the bug without (a) FR config rows AND (b) extending YD_FI_PPC_CODE domain. (Claim 187.)

7. **Alt-payee resolution lands in `FPAYH-GPA1R`** (the resolved payee LIFNR after LFA1.LNRZA / LFB1.LNRZB). v6 uses GPA1R for both PA0006 cast AND ADRC fallback — handles alt-payees correctly by construction. UNESCO has 16 vendor-level + 9 cocode-level alt-payees configured; 2 fired in sampled REGUH. (Claim 188.)

8. **ICVS VS90* LIFNRs and NUMC8 cast** — ABAP CHAR(10)→NUMC(8) extracts trailing digits cleanly (VS90033973 → 90033973). Empirically never collides with real PERNR ranges. Risk is theoretical; a `CO '0123456789'` guard is preventive but not required. (Claim 188.)

9. **`/SEPA_CT_UNES` tree in D01 is HYBRID after V001 deployment** — V0 unstructured AdrLine nodes (FPAYHX-ZPFST/ZPLOR/ORT1Z) coexist with V001 structured PstlAdr leaves (Y_FI_DMEE_ADR exit). XML output emits BOTH PstlAdr blocks until V0 nodes are explicitly deleted. The BERTOLDINI test exploited this: legacy block = control, V001 block = treatment, side-by-side visible. (Claim 184, 185.)

10. **RFC_READ_TABLE quirks for DMEE_TREE_NODE** — table is wide (>512 byte row); requires narrow FIELDS lists; OPTIONS rejects IN clauses; multi-condition WHERE must use multiple OPTIONS rows with leading-space continuation. (Rule `feedback_rfc_read_table_quirks`.)

---

## 5. Reproducibility

Scripts written this session (all under `Zagentexecution/`):
- `sepa_simulator_step1.py` — universe builder for `/SEPA_CT_UNES UNES`.
- `sepa_simulator_step2.py` — bulk PA0006 + ADRC extract from P01.
- `sepa_simulator_step3.py` — V6 simulation + drift report.
- `sepa_simulator_all.py` — all SEPA formats simulation.
- `sim_all_formats.py` — full landscape (SEPA + CGI + CITI) drift forecast.
- `session074_brain_claims.py` — claim insertion.
- `session074_annotations.py` — object annotations.
- `session074_feedback_rules.py` — feedback rules.

Total session impact: **Brain 9 annotations + 6 claims + 5 rules + 1 knowledge doc + 1 companion section. Gold DB +2 tables (DFPAYG, DFPAYV) + 3 simulation result tables. Reproducibility 100% via SQL replay.**
