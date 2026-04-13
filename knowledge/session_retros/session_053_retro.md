# Session #053 Retro — INC-BUDGETRATE-EQG full analysis: Budget Rate Solution Enhancement (15-member composite)

**Date**: 2026-04-13
**Driver**: User passed FMAVC005 incident from EqG ticket reimbursement (Vonthron / Konakov / Lopez thread). Goal: identify ROOT cause, scope the population at risk, propose preventive control. Closed with executive brief + Excel inventory + agreed preventive validation as fix path.

---

## 1. What the session delivered

### Executive deliverables
| File | Purpose |
|------|---------|
| `knowledge/incidents/INC-BUDGETRATE-EQG_executive_brief.md` | One-page brief for business with link to Excel |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx` | 64-row inventory with 19 columns (frozen panes, Vonthron + zero-available rows highlighted) |

### Knowledge artifacts updated
| File | Change |
|------|--------|
| `knowledge/incidents/INC-BUDGETRATE-EQG_budget_rate_usd_posting.md` | Status: RE-OPENED → ROOT CAUSE CONFIRMED. New §5.0 (empirical chain of evidence), §5.B-bis (system-wide blast radius P01), §5.C (mechanism end-to-end), §5.D (why same-year posting "works" until pool exhausted), §5.E (live gate values), §5.F (recommended fix) |
| `knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md` | Replaced 8-member view with **15-member 3-camp asymmetry analysis** (Camp A FR-anchored, Camp B posting-anchored, Camp C filters/exclusions). Added trace-confirmed mechanism narrative. Documented CHECK_CONS SAVE/RESTORE pattern that was previously misunderstood. |

### Quality-check / data extraction scripts (reusable)
| File | Purpose |
|------|---------|
| `Zagentexecution/quality_checks/budget_rate_consumption_audit.py` | Per-FR audit. Classifies each FR position as APPLICABLE / BYPASSED / DRIFT_RESIDUAL. CLI: `--fr <REFBN> --fund <FONDS> --out <json>` |
| `Zagentexecution/quality_checks/br_line_level_inconsistency_check.py` | Line-level scan of all P01 BR-applicable open FR lines. Identifies AT_RISK_OPEN, AFFECTED, DRIFT_RESIDUAL classes |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_consumption_audit.json` + reports | Per-line and fund-level audit outputs |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL_table.md` | 64-line wide markdown table (input to xlsx) |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/p01_systemwide_at_risk_funds.txt` | 70 fund landing list (Vonthron-class latent risk) |

### Source code newly extracted from P01/D01
| Object | Type | Where |
|--------|------|-------|
| `ZFIX_EF_FUND_RESERVATION` | ENHO | `extracted_code/ENHO/ZFIX_EXCHANGERATE/ZFIX_EF_FUND_RESERVATION======E.abap` (117 lines) |
| `ZFIX_BR_REVALUATION` | ENHO | `ZFIX_BR_REVALUATION===========E.abap` (49 lines) |
| `ZFIX_BR_REVAL_RESFUND` | ENHO | `ZFIX_BR_REVAL_RESFUND=========E.abap` (31 lines) |
| `ZFIX_BR_AVC_EXCLUSIONS` | BAdI class (CCDEF/CCIMP/CM001/CM002/CO/CU/CI/CP/CT) | `extracted_code/ENHO/ZFIX_EXCHANGERATE/AVC_EXCLUSIONS/` |
| `ZFIX_FM_BR_POST_FROM_PY_AUTO` | ENHO | `ZFIX_FM_BR_POST_FROM_PY_AUTO==E.abap` (27 lines) |
| `ZFIX_BR_BAPI_EMPLOYEE_POST` | ENHO | `ZFIX_BR_BAPI_EMPLOYEE_POST====E.abap` (6 lines) |

---

## 2. The big finding — 15-member composite, not 8

The `ENHC ZFIX_EXCHANGERATE` composite has **15 active members + 1 BAdI implementation**, organized in 3 camps:

| Camp | Anchor | Members | Behavior on USD-against-EUR-FR |
|------|--------|---------|--------------------------------|
| **A — FR-currency** | `kblk-waers` (FR header) | EF_FUND_RESERVATION (Enh2+3), CHECK_CONS (Enh1+2 SAVE/RESTORE), FUNDBLOCK (Enh2+3) | Fires correctly → FR side persisted at BR consistently |
| **B — Posting-currency** | per-row `twaer` | PAYCOMMIT, NEW_ITEM, AVC (Enh1+3), KBLEW, FI | **Skips silently** → standard SAP persists at identity / M-rate |
| **C — Filter / exclusion** | tcode / hard-coded | BR_REVALUATION (Enh2+3, FMN4N), BR_REVAL_RESFUND (FMZZ, testlauf=X), BR_AVC_EXCLUSIONS BAdI | Exclude non-EUR rows from cleanup tools; AVC-skip patch is dead code (D01+V01 only) |
| **D — Auxiliary** | — | FM_BR_POST_FROM_PY_AUTO, BR_BAPI_EMPLOYEE_POST | Payroll plumbing (out of scope for cross-currency bug) |

**The bug is the asymmetry between Camp A (always BR for EUR FR) and Camp B (skips when posting is non-EUR).** Camp A keeps the FR ledger pristine; Camp B silently lets identity values into the AVC pool. The two views diverge fund-by-fund until cover-group hits zero.

---

## 3. Critical correction: BR_AVC_EXCLUSIONS is dead code (D01+V01 only)

User flagged "I do not see it in TS3" → cross-system check confirmed:
- `ZFIX_BR_AVC_EXCLUSIONS` BAdI (implementing `FMAVC_ENTRY_FILTER`) exists in **D01 + V01 only**
- TADIR & REPOSRC absent from TS1, TS3, **P01 (production)**
- Created 2025-05-14 by JP_LOPEZ (transports D01K9B0D4Z + D50, "BR - AVC Exlclusion MIRO F110")
- **Deactivated next day** (transports D01K9B0D54 + D55, "BR Deactivate AVC exclusion")
- One-day life cycle, never promoted

This corrected my earlier (wrong) story that said "MIRO/F110 are silenced, FB60 is the visible surface". In production, AVC fires for **all** tcodes equally — the surface is wider than FB60.

Logged in PMO_BRAIN.md as **H38** (cleanup pending). Lesson: tcode-blacklist mute on AVC is the wrong approach; cross-currency drift must be fixed at persistence layer.

---

## 4. Empirical population at risk (P01, ledger 9H, 2026)

- **64 open EUR Fund Reservation LINES** (TWAER=EUR + GSBER=GEF + authorized fund-type) on **26 distinct funds**
- **35 lines** sit on (FONDS, FIPEX) cover groups with active non-EUR consumption draining the pool
- **~10 lines have AVC available ≤ $0** today — Vonthron-class latent failures on funds 3110111021 (5 lines), 3110111061 (3), 3230311031, 3230411011, 3230311021
- Lifetime USD-bypass volume across the 458 funds with EUR FR + USD activity history: **$375M** (theoretical ~$35.7M drift exposure)

The 64 BR-applicable open FR lines have line-level commitment 0 (carried-forward, not yet directly consumed). The drift comes from **other consumption postings on the same cover group**. The bug is fund-level (cover-group level), not FR-line-level.

---

## 5. Recommended fix (agreed with business owner)

**Preventive validation in `CL_FM_EF_POSITION->CHECK_CONSUMPTION`**:
- IF `check_br_is_active( ) = abap_true` AND FR header WAERS=EUR AND GSBER=GEF AND fund_type ∈ `mr_fund_type` AND consumption_doc-WAERS ≠ EUR
- THEN `MESSAGE 'Z_BR_001' TYPE 'E'` "Cannot consume in &1 against EUR Budget Rate Fund Reservation &2/&3. Please post in EUR."

Stops drift at user-input layer. After deploy: one-time `FMAVCREINIT` cleanup of the 26 already-drifted funds.

Alternatives evaluated and dismissed:
- **Activate `convert_to_currency_2` (Staff logic)** in Camp B → touches 5 enhancement bodies; double-hop rounding behavior needs testing; doesn't clean existing drift
- **Cleanup-only via FMN4N extension** → permits ongoing drift; only periodic reconciliation

---

## 6. New SAP knowledge captured this session

### Tables / data sources discovered
| Object | What we learned |
|--------|----------------|
| **KBLE / KBLEW** (cluster) | Cannot read via `RFC_READ_TABLE`. RFC-enabled wrapper FM `/SAPPSPRO/PD_GM_FMR2_READ_KBLE` returns both T_KBLE (consumption history with RBELNR/RBUZEI link to FI doc) and T_KBLEW (per-currency split CURTP=00 transaction / CURTP=10 local). Critical for FR↔FI consumption traceability without BSEG.KBLNR access. |
| **FMAVCT** | Wide table (>512-byte row), `RFC_READ_TABLE` rejects with `DATA_BUFFER_EXCEEDED` if FIELDS=[]. Workaround: pass narrow FIELDS list; split WHERE clause across multiple OPTIONS entries (the SAP parser rejects single-clause complex booleans with `OPTION_NOT_VALID`). For UNESCO ledger 9H + ALLOCTYPE_9='KBFC' = carryforward budget allotment (the actual AVC ceiling). HSL01-HSL16 are per-period local-currency values; HSLVT is yearly total. **Caveat**: rows can be duplicated by `RVERS` / `RPMAX` — dedup before summing. |
| **FMAVCT vs FMBDT** | FMAVCT = AVC totals (the BCS pool the engine guards). FMBDT = budget posting line items (planning input). Available = FMAVCT.allotment − sum(FMIOI commitments) − sum(FMIFIIT actuals). |
| **FMIOI WRTTP=81 +/- pairs** | Earmarked-fund commitment rows come in pairs: original creation, period reductions, and year-end period-016 reversals + period-000 carryforward-in. Net signed sum ≠ "what's open" naively — must filter by GJAHR or trace by BUDAT to interpret correctly. SAP rounding plugs of $0.01-0.02 appear at ratio 1.0 alongside BR rows — these are NOT cross-currency consumption signatures. |
| **DDIF_FIELDINFO_GET** | Use this to introspect wide tables when `RFC_READ_TABLE FIELDS=[]` fails. Returns `DFIES_TAB` with all column names, types, lengths. |

### ABAP enhancement / BAdI extraction patterns
| Pattern | Notes |
|---------|-------|
| ENHO source extraction | Each ENHO has a TRDIR include named `<ENHNAME>==========E` (padded to 30 chars with `=`). Read via `SIW_RFC_READ_REPORT`. Multi-include classes (BAdI implementations) have CCDEF/CCIMP/CCMAC/CO/CU/CI/CP/CT/CM00x includes — list via TRDIR `LIKE '<NAME>%'`. |
| `cl_enh_factory=>get_enhancement` failures | Some ENHOs (POPOST, FM_POS_UPD, REDUCE) appear in TADIR but `cl_enh_factory` returns "cannot be read" → orphaned, no runtime effect. Don't waste time analyzing them. |
| Composite ENHC structure | The composite is a TADIR ENHC entry. Its members are listed in SE19 GUI (composite tab) but not directly via TADIR. To enumerate members, query `TADIR` for `ENHO` objects with naming convention `<COMPOSITE>_*` (UNESCO pattern). For ZFIX_EXCHANGERATE composite, members include `ZFIX_EF_*` and `ZFIX_BR_*` — the prefix is not always literal-match to composite name. **Lesson**: always confirm composite contents via SE19 screenshot before assuming the list is complete. |

### Custom code / class architecture
| Object | What we learned |
|--------|----------------|
| `YCL_FM_BR_EXCHANGE_RATE_BL` | The singleton class behind every BR enhancement. Constructor (CM00A) loads the perimeter ranges. CM004 `check_conditions` is the gate (`mr_waers=['EUR']` is the line that excludes USD). CM005 `convert_to_currency` is the BR call (`type_of_rate='EURX'`). CM002 `convert_to_currency_2` is the cross-currency double-hop USD UNORE → EUR @ M → USD @ EURX — exists, complete, but only called from `IF 1=2` Staff-logic dead branches. CM007 `fmavc_reinit_on_event` is the post-COMMIT_WORK reinit handler that fires ONLY when `mt_avc_fund` is populated (which requires Camp B gate to PASS, which it doesn't for non-EUR). |
| **CHECK_CONS SAVE/RESTORE pattern** | Two-block enhancement: Enh1 saves m_t_addref, recalcs at BR; standard CHECK_CONSUMPTION sees BR values; Enh2 restores original. **Nothing persisted** — the BR view is a temporary in-memory override only for the EF check. The user's debugger captured this in flight (100.00 USD M-rate → 96.06 USD BR-rate during Enh1, restored to 100.00 by Enh2). |
| **Camp split clarified** | Earlier sessions documented "8 enhancements with mr_waers=['EUR'] gate" — incomplete. Real picture: gate is the same singleton method, but `iv_waers` source differs per call site. FR-anchored callers (Camp A) feed FR's own EUR → gate passes. Posting-anchored callers (Camp B) feed posting's USD → gate fails. The asymmetry, not the gate, is the bug surface. |

---

## 7. Brain updates needed (committed in this session)

### New feedback rules (to append to `brain_v2/agent_rules/feedback_rules.json`)

1. **`feedback_br_camp_asymmetry`** (HIGH) — When analyzing UNESCO BR custom solution, always classify enhancements by gate-input source (Camp A FR-currency vs Camp B posting-currency vs Camp C filter), not by member count. The "8 enhancements" framing is incomplete; the composite has 15 members + 1 BAdI. Reason: incomplete framing led to wrong root-cause story in earlier sessions.

2. **`feedback_check_landscape_before_root_cause`** (CRITICAL) — Before claiming a custom object affects production behavior, confirm it exists in P01 via TADIR/REPOSRC query against the production system. D01 is dev — many objects there never reach prod (e.g., `ZFIX_BR_AVC_EXCLUSIONS` lived 1 day in D01 before deactivation, never transported). Reason: wrong claim about MIRO/F110 being silenced was based on D01 source.

3. **`feedback_kble_via_pspro_wrapper`** (MEDIUM) — KBLE/KBLEW are cluster tables → `RFC_READ_TABLE` errors with `TABLE_WITHOUT_DATA`. Use `/SAPPSPRO/PD_GM_FMR2_READ_KBLE` wrapper FM with `I_BELNR=<FR_doc>`. Returns T_KBLE (consumption events with RBELNR/RBUZEI = consumer FI doc/line) + T_KBLEW (per-currency split). Critical for FR↔FI traceability without BSEG access.

4. **`feedback_fmavct_query_pattern`** (MEDIUM) — `FMAVCT` is wide (>512 bytes). To read via `RFC_READ_TABLE`: pass narrow FIELDS list (max 10-15 cols), split WHERE clauses into multiple OPTIONS entries. Single complex boolean WHERE rejected with `OPTION_NOT_VALID`. Dedup result rows by full-row signature (RVERS/RPMAX duplicates).

5. **`feedback_fmioi_carryforward_pairs`** (MEDIUM) — FMIOI WRTTP=81 rows for an FR include creation + period-016 year-end reversal + period-000 carryforward-in. Naive sign sum doesn't equal "open balance". For "open" → filter by current GJAHR + signed sum; for "lifetime consumed" → use KBLE not FMIOI. Rows with ratio=1.0 and tiny amounts ($0.01-0.02) are SAP rounding plugs, NOT cross-currency consumption signatures.

### New claims (to append to `brain_v2/claims/claims.json`)

1. **The bug is gate asymmetry**: Camp A FR-anchored gates always pass for EUR FRs; Camp B posting-anchored gates fail for non-EUR consumption. The persisted FMIOI/FMIFIIT then carries identity values for non-EUR while the FR side is at BR. (TIER_1 — extracted source code + production data confirmation)

2. **`BR_AVC_EXCLUSIONS` is dead code in D01+V01**: never promoted to TS1/TS3/P01. PMO H38 to clean up. (TIER_1 — TADIR cross-system check)

3. **AVC available is fund-level, not FR-line-level**: all FR lines on the same (fund, funds-center, control-object) draw from one shared AVC pool. Failure is determined by pool exhaustion, not by individual FR line balance. (TIER_1 — FMAVCT structure + Vonthron's case)

### Update incident `INC-BUDGETRATE-EQG`

Change `status` from `RE-OPENED` to `ROOT_CAUSE_CONFIRMED`. Append:
- `analysis_doc`: `knowledge/incidents/INC-BUDGETRATE-EQG_budget_rate_usd_posting.md`
- `executive_brief`: `knowledge/incidents/INC-BUDGETRATE-EQG_executive_brief.md`
- `inventory_xlsx`: `Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx`
- `recommended_fix`: preventive validation in `CL_FM_EF_POSITION->CHECK_CONSUMPTION`
- `population_at_risk`: 64 open BR FR lines / 26 funds / ~10 lines with available ≤ 0
- `related_objects`: full 15-member ZFIX_EXCHANGERATE list + YCL_FM_BR_EXCHANGE_RATE_BL + ZFIX_BR_AVC_EXCLUSIONS

### New brain blind-spots cleared
The 6 newly-extracted enhancements (`ZFIX_EF_FUND_RESERVATION`, `ZFIX_BR_REVALUATION`, `ZFIX_BR_REVAL_RESFUND`, `ZFIX_BR_AVC_EXCLUSIONS`, `ZFIX_FM_BR_POST_FROM_PY_AUTO`, `ZFIX_BR_BAPI_EMPLOYEE_POST`) should now be promoted from `blind_spots` (if present) to first-class objects in `brain_state.objects[]`.

---

## 8. PMO_BRAIN updates

- **H38**: Cleanup `ZFIX_BR_AVC_EXCLUSIONS` landscape inconsistency (D01+V01 only) — added in session
- **H39 (new)**: Implement preventive validation in `CL_FM_EF_POSITION->CHECK_CONSUMPTION` per business agreement
- **H40 (new)**: Run one-time `FMAVCREINIT` on 26 affected funds for 2026 GJAHR ledger 9H after H39 deploys

---

## 9. What we did better than prior sessions

- **Read all 15 enhancement source files**, not just 8 (catches like FUNDBLOCK Enh3, BR_REVALUATION's FMN4N filter, BR_AVC_EXCLUSIONS BAdI)
- **Cross-system landscape check** before claiming an object is active in production (caught the BAdI dead-code state)
- **Used RFC wrapper for cluster tables** (`/SAPPSPRO/PD_GM_FMR2_READ_KBLE`) instead of giving up on KBLE
- **User-led precision**: every iteration tightened the analysis (per-FR vs per-fund, EUR vs non-EUR, KBLE vs FMIFIIT, fund-pool vs FR-line)

## 10. What we did WORSE this session (for next session to avoid)

- **Removed columns when adding new ones** — twice. Frustrated the user. Lesson: when extending a table, NEVER drop existing columns; use a single canonical script that all queries extend.
- **Misinterpreted FMIOI sign convention** twice (took absolute sums and confused signed open with naïve subtraction). Lesson: always sample 3 raw rows of FMIOI WRTTP=81 before computing per-line metrics.
- **Over-claimed about BR_AVC_EXCLUSIONS** before checking landscape. Lesson: P01 TADIR check is one RFC call away — do it FIRST.
- **Counted the pool ($170K) as if it were per-line consumption**. Lesson: any aggregation column must explicitly state its filter (per-FR vs per-fund vs per-FONDS+FIPEX).

---

## 11. Knowledge graph updates needed

### New objects to register in `brain_state.objects[]`
- `ZFIX_EF_FUND_RESERVATION` (ENHO, Camp A)
- `ZFIX_BR_REVALUATION` (ENHO, Camp C — FMN4N filter)
- `ZFIX_BR_REVAL_RESFUND` (ENHO, Camp C — FMZZ filter, testlauf only)
- `ZFIX_BR_AVC_EXCLUSIONS` (BAdI implementation, Camp C, **DEAD in P01**)
- `ZFIX_FM_BR_POST_FROM_PY_AUTO` (ENHO, Camp D — payroll bridge)
- `ZFIX_BR_BAPI_EMPLOYEE_POST` (ENHO, Camp D)
- `KBLK / KBLP / KBLE / KBLEW` (FR cluster tables) with reference to the wrapper FM
- `FMAVCT` table with allotment + ALLOCTYPE_9 documentation
- `/SAPPSPRO/PD_GM_FMR2_READ_KBLE` (RFC wrapper FM)

### New edges to maintain
- All 15 ZFIX_* members → `MEMBER_OF` → ENHC `ZFIX_EXCHANGERATE`
- All members → `CALLS_CLASS` → `YCL_FM_BR_EXCHANGE_RATE_BL`
- Camp A members → `READS_FIELD` → `m_r_doc->m_f_kblk-waers`
- Camp B members → `READS_FIELD` → `<ls_*>-twaer` (per-row currency)
- `ZFIX_BR_AVC_EXCLUSIONS` → `IMPLEMENTS_BADI` → `FMAVC_ENTRY_FILTER` (annotated DEAD_CODE_IN_PROD)
- `INC-BUDGETRATE-EQG` → `AFFECTS_OBJECTS` → 64 FR LINES + 26 FUNDS + 6 ZFIX members (Camp B) + YCL_FM_BR_EXCHANGE_RATE_BL.check_conditions
- `INC-BUDGETRATE-EQG` → `RECOMMENDED_FIX_LOCATION` → `CL_FM_EF_POSITION->CHECK_CONSUMPTION`

---

## 12. Phase 4b — SAP-itself learnings (mandatory checklist)

| Topic | Learning |
|-------|---------|
| **BCS / AVC architecture** | Available = Allotment − Commitments − Actuals. AVC is at fund/cover-group level (FONDS + FUNDSCTR + CMMTITEM-rolled-up-to-control-object), NOT at FR line level. Multiple FR lines on same fund/CMMTITEM share one pool. |
| **Cluster tables in pyrfc** | KBLE/KBLEW must use `/SAPPSPRO/PD_GM_FMR2_READ_KBLE` wrapper. Keep this in the standard "extraction toolkit" alongside RFC_READ_TABLE for transparent tables. |
| **TCURR rate types in UNESCO** | `EURX` = Budget Rate (1.09529 EUR→USD, fixed since 2024-01-01 per TVARVC.Y_FM_FIXED_RATE_START). `M` = OB08 daily. The BR solution wraps `CONVERT_TO_LOCAL_CURRENCY` with `type_of_rate='EURX'` to override SAP standard `M`. |
| **BAdI vs Enhancement Implementation** | BAdI implementations have a class structure (CCDEF/CCIMP/CO/CU/CI/CP/CT/CM00x) and implement `IF_EX_*` interface from a SAP-defined BAdI definition. Plain ENHOs are simpler — just an `*=========E.abap` include with `ENHANCEMENT N. ... ENDENHANCEMENT.` blocks. |
| **Enhancement composite patterns** | One ENHC can have heterogeneous member naming: at UNESCO, `ZFIX_EXCHANGERATE` composite includes both `ZFIX_EXCHANGERATE_*`, `ZFIX_EF_*`, and `ZFIX_BR_*` prefixed members. Don't filter by literal prefix match. |
| **Enhancement spot-life** | Some ENHOs are created and deactivated within a day, transports released but never promoted (`ZFIX_BR_AVC_EXCLUSIONS` case). TADIR shows them as active but they don't run. Always check ENHLOG history + cross-system landscape before assuming a custom object affects production. |

---

## 13. Closing notes

User explicitly closed the session: business has the executive brief + Excel, agreed on preventive validation as fix path, and asked for full brain preservation. Open follow-ups:

- **PMO H38**: Delete or repurpose `ZFIX_BR_AVC_EXCLUSIONS` from D01+V01
- **PMO H39 (new)**: Build the preventive validation enhancement
- **PMO H40 (new)**: One-time FMAVCREINIT cleanup on 26 affected funds
- Consider building a **`sap_fm_avc_intelligence`** skill to encapsulate FMAVCT/FMIOI/KBLE/KBLEW extraction patterns + BR perimeter detection logic for re-use

Stored at `knowledge/session_retros/session_053_retro.md`.
