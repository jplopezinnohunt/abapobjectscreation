---
name: PS Project Replication (P01→D01) + KI235 / WBS-as-cost-object model
description: Empirically verified (s093 2026-06-29) method to replicate SAP PS projects + WBS structures P01→D01 via BAPI_PROJECT_MAINTAIN, the KI235 root-cause model (WBS element IS the cost object, not OKB9), and the 3-layer chain (CO object → FM derivation → AVC disponible) for cost-recovery test postings.
type: project
domain: PSM / Project_System / Cost_Recovery
evidence_tier: TIER_1
created_session: s-2026-06-29
cross_links:
  - knowledge/domains/PSM/cost_recovery_avc_disponible_model.md
  - knowledge/domains/PSM/fund_management_sync_playbook.md
  - Zagentexecution/tasks/2026_06_29_fm_model_sync/ps_project_sync.py
---

# PS Project Replication + KI235 model

## KI235 root cause — the WBS element IS the cost object
KI235 ("account requires an assignment to a CO object") for cost elements **0006046013 / 0006046014 /
0007046013** (verified CSKA in both P01 and D01 → legitimately require a CO object). **OKB9 is NOT the
cause:** TKA3A (170) + TKA3C (158) are IDENTICAL P01=D01, and these 3 cost elements have NO OKB9 entry in
EITHER system. In P01 the CO object comes from the **project WBS** (COEP: WBS PR00028292=000CRP9000,
PR00022163=633CRP9003, PR00032001=504PAK1000.4.4 — `PRxxxxxxxx` is the WBS OBJNR, not POSID). A **WBS
element is itself a valid CO object** — so once the WBS exists in D01, KI235 is satisfied (no cost center /
no OKB9 entry needed).

## 3-layer chain for a cost-recovery test posting to succeed in D01
1. **CO object** — the WBS must exist + be RELEASED (REL). → fixes KI235.
2. **FM derivation** — posting to the WBS derives fund/fundcenter/commitment item (FMDERIVE, already config in D01).
3. **AVC disponible** — that derived FM address needs disponible (ENTR/B1, see cost_recovery_avc_disponible_model.md).
All three are required; creating the WBS alone only clears layer 1.

## PS replication recipe — BAPI_PROJECT_MAINTAIN
Read source from P01: `BAPI_PROJECTDEF_GETDETAIL` (def + profile) + PRPS (`POSID LIKE 'PROJ%'`, fields
POSID/STUFE/BELKZ/PLAKZ/PRART). PROJ/PRPS direct RFC reads are partly restricted; the BAPI getdetail is the
clean path. Note PRPS has **PSPHI** (project internal no.), not PSPID; `PRxxxxxxxx` codes are OBJNRs.

**Create (flat WBS — VERIFIED, 000CRP9000):**
- `I_PROJECT_DEFINITION` {PROJECT_DEFINITION, DESCRIPTION, COMP_CODE, CONTROLLING_AREA, BUS_AREA,
  PROJECT_CURRENCY, PROJECT_PROFILE, RESPONSIBLE_NO, APPLICANT_NO}
- `I_WBS_ELEMENT_TABLE` {WBS_ELEMENT, PROJECT_DEFINITION, DESCRIPTION, COMP_CODE, BUS_AREA, CO_AREA,
  CURRENCY, WBS_ACCOUNT_ASSIGNMENT_ELEMENT='X', WBS_PLANNING_ELEMENT='X', RESPONSIBLE_NO, APPLICANT_NO}
- `I_METHOD_PROJECT` [{Create ProjectDefinition}, {Create WBS-Element}*, {Save, REFNUMBER='000000'}]
- then `BAPI_TRANSACTION_COMMIT(WAIT=X)`.
**Release (so the WBS is postable — VERIFIED):** `I_WBS_ELEMENT_TABLE`=[{WBS_ELEMENT, PROJECT_DEFINITION}]
(keys) + method [{Release WBS-Element}*, {Save}]. Status CRTD(I0001)→REL(I0002).

**Gotchas (all hit empirically):**
- `RESPONSIBLE_NO` is validated against **TCJ04**, `APPLICANT_NO` against **TCJ05** — DIFFERENT tables, and
  P01's HR numbers usually don't exist in the target. Use a valid target value (s093: responsible 10133238,
  applicant 00000001). Profile-dependent: Z000012 needed only responsible; Z000002 needed both.
- BAPI **auto-commits** the save — a rollback does NOT undo it; there is no TESTRUN. Verify by re-read.
- Method table must be **consistent with the data tables** (every method object must be in its data table).
- `REFNUMBER` is NUMC; the Save row = '000000'.
- Method 'Delete' is NOT supported for ProjectDefinition (can't delete via this BAPI).

## ⚠️ CORRECTION — `Y_RFC_CREATE_PROJECT_SISTER` is an EXPORT (SAP→Salesforce), NOT the SAP creator
An earlier note (commit d259a71) called this "THE real creation path". **That was WRONG — corrected here.**
Reading the report behind it (`YEBPROJ_CREATE_PROJECT_SISTER`, 208 lines) shows it `SELECT`s from PROJ +
PRPS WHERE ERDAT BETWEEN dates and fills the output table `IT_PROJ_PRPS` (+ reads status via
STATUS_TEXT_EDIT and long text via READ_TEXT). It **READS SAP projects and pushes them to the SISTER system
(Salesforce)** — i.e. "create the project record IN the sister system FROM SAP". It is the OUTBOUND sync,
it does NOT create projects/WBS in SAP. Companions `Y_RFC_MODIFY_PROJECT_SISTER`, `Y_RFC_WBS` are likewise
SAP-side readers/exports.

**The REAL creation path WAS ALREADY DOCUMENTED** — see `knowledge/system_operating_model_rfc.md`
(MuleSoft↔PPM sync, 2026-06-21). I should have loaded it instead of reverse-engineering (CLAUDE.md rule #1).

**E2E: PPM (Salesforce/Core Planner) is the MASTER for projects + funds; MuleSoft writes them INTO SAP.**
Inbound MuleSoft→SAP create FMs:
- **Project + WBS structure → `BAPI_PROJECT_MAINTAIN`** (yes — the same BAPI; production uses it, so the WBS
  HIERARCHY *is* creatable via this BAPI — my RFC attempts just didn't construct I_WBS_HIERARCHIE_TABLE
  correctly; it is NOT a BAPI limitation. Revisit the exact construction vs the MuleSoft payload.)
- WBS text + custom fields → `Y_BAPI_WBS_TEXT_MAINTAIN` + `Y_BAPI_WBS_CUS_FIELD_UPDATE`.
- **Fund → `Y_FMKU_0050_CREATE_WITH_COMMIT`**; **fund→C5 biennium → `Y_BAPI_FUND_C5_ASSIGNMENT`**;
  fund change → `FM_FUND_CHANGE_RFC`.
- Out (SAP→PPM financials): `Y_BAPI_WBS_FINANCIAL_DATA_1`, `Y_BAPI_YPS8`.
- "When a Project is created, a corresponding Fund is provisioned" (FINCODE=PSPID linkage; psm_initial_analysis.md).

So the **CJ20N hypothesis above is RETRACTED** — the production creator is MuleSoft via BAPI_PROJECT_MAINTAIN,
not CJ20N. CJ20N indent is still a valid *manual* shortcut for one test WBS, but the faithful/automated path
is the BAPI (get the I_WBS_HIERARCHIE_TABLE construction right, matching MuleSoft).

## THE RAW-BAPI PROCESS (BAPI_PROJECT_MAINTAIN) — corrected & verified (fallback / learnings)

### #1 fix — REFNUMBER is a per-data-table ROW INDEX (not a global sequence)
The biggest blocker ("WBS element X already exists" on the LAST WBS, even on a clean slate) was a REFNUMBER
mistake. In `I_METHOD_PROJECT`, **REFNUMBER points to the row index inside the method's OWN data table**:
ProjectDefinition Create → `000001` (row 1 of `I_PROJECT_DEFINITION`); each WBS Create → its **1-based index
in `I_WBS_ELEMENT_TABLE`**; Save → `000000`. Numbering globally (def=1, wbs=2,3,…) makes the last WBS point
past its table → the misleading "already exists". Fixed in `ps_project_sync.py`.

### Verified create recipe (def + single-level-1 WBS)
ONE clean call on a project that does NOT yet exist: full `I_PROJECT_DEFINITION` + `I_WBS_ELEMENT_TABLE`
(WBS_ACCOUNT_ASSIGNMENT_ELEMENT=X, WBS_PLANNING_ELEMENT=X) + `I_METHOD_PROJECT` [Create ProjectDefinition,
Create WBS-Element* with REFNUMBER=row-index, Save=000000] → commit → Release. RESPONSIBLE_NO→TCJ04,
APPLICANT_NO→TCJ05 (distinct tables; valid target persons). BAPI auto-commits (no TESTRUN) — verify by re-read.

### Dates left OPEN intentionally
P01 finish dates are in the past (504PAK1000=2024-01-31, 000CRP9000=2020-12-31) → copying them would block a
2026 test posting. START/FINISH/FCST_* are NOT copied (left open). Everything else is replicated faithfully
(verified field-by-field on 000CRP9000: only FINISH differed; all profile-driven fields — BUDGET/PLAN/NETWORK/
INT/WBS_SCHED/CSH profiles, OBJECTCLASS, CALENDAR — identical because PROJECT_PROFILE defaults them).

### KNOWN LIMITATION — WBS hierarchy NESTING (unsolved by RFC)
Single level-1 create works. **Nesting children under a parent does NOT work via this BAPI by RFC.** With no
coding mask (MASK_ID empty) the POSID dots don't auto-nest, AND `I_WBS_HIERARCHIE_TABLE` (UP/DOWN) is **not
honored at create** → "Several WBS elements on level 1 not allowed" (a project allows only one level-1 WBS).
Verified across one-call / incremental / UP-only / UP+DOWN, on a CLEAN slate with REFNUMBER fixed.
**For a multi-level WBS structure: create def + root with the script, then INDENT children in CJ20N (Project
Builder).** Only the indent is manual; def/root/profiles/responsible-applicant/release are correct via BAPI.

### ANTI-PATTERN (do NOT repeat) — delete-to-retry
Iterating with `METHOD='Delete'` to "retry" sets the **deletion flag (system status DLFL/I0076)**, which has
**no clean RFC reset** (STATUS_CHANGE_EXTERN=user-status only; STATUS_CHANGE_INTERN=NOT_FOUND/DA300; no public
PS BAPI) — only CJ20N "reset deletion indicator". This corrupted 504PAK1000 mid-session. If a create fails:
fix the input and re-run the single clean call on a non-existing project; never delete-to-retry.

## Result P01→D01 (s093) — KI235 culprits
- 000CRP9000 (1 flat WBS): created + REL ✓
- 633CRP9003: pre-existing in D01 ✓
- 504PAK1000: project def + root WBS recreated CLEAN (full def, dates open, released) ✓; children
  **504PAK1000.4 / .4.4 PENDING — do the indent in CJ20N** (BAPI nesting limitation above)
→ 2 of 3 KI235 WBS fully available; 504PAK1000.4.4 needs the CJ20N indent.

## What still remains (to a working test posting)
1. **504PAK1000.4 / .4.4** — CJ20N indent (hierarchy nesting; BAPI-RFC limitation).
2. **FM derivation** — confirm the WBS posting derives the right fund/fundcenter/commitment item (FMDERIVE).
3. **AVC disponible on the derived address** — disponible was loaded for the 5 CR FUNDS (ENTR/B1, 2025+2026);
   confirm/assign for the address the WBS actually derives.
4. **E2E test posting** — post the CR document; confirm it clears KI235 + derivation + AVC.
Deferred (not blocking): ~98 funds WRTTP43 budget (~212M); YTFM Z for old biennia; field reconcile outside C5/43.

## OPEN — layer-2 FM-derivation gap on a DIFFERENT WBS (218BDI2000.1, 2026-07-07)
Item 2 above ("confirm the WBS posting derives...") is not yet a solved general case — a new project/fund
outside the KI235 set hit it directly: coding-block error `No funds center entered/derived in item 00001
(UNES/6046013/218BDI2000.1)` for WBS 218BDI2000.1 / fund 218BDI2000. Layer 1 (CO object) appears satisfied
but layer 2 (FM derivation → FISTL) fails. Not yet root-caused: FMDERIVE rule gap vs incomplete target
replication (fund-center address not yet loaded for this fund) vs genuine standard-config gap. The
mechanism to replicate project+WBS+fund assignment already exists but was not run to completion for this
fund: `Zagentexecution/tasks/2026_06_29_fm_model_sync/replicate_project_fund.py` (A fund · B C5 ·
C project+WBS · D WBS attrs · E budget-fund · F budget-project). Tracked as
`KU-2026-WBS-FISTL-DERIVATION-218BDI` (`brain_v2/agi/known_unknowns.json`) — pick up next session before
generalizing this doc's 3-layer chain beyond the KI235 fund set.

**UPDATE 2026-07-08 (claims #351/#352) — target address CONFIRMED, root cause still open:** the real P01
Funds Center for fund 218BDI2000 is **YAO** — verified via `fmifiit_full` (P01 Gold DB): `SELECT DISTINCT
FISTL, COUNT(*) FROM fmifiit_full WHERE FONDS LIKE '218BDI2000%' GROUP BY FISTL` returns exactly ONE row,
FISTL=YAO, 283/283 line items. YAO is a valid, long-standing center for UNES (fund_centers master, active
since 2002-01-07) — NOT to be confused with the fund code itself (Fund `218BDI2000` and Funds Center `YAO`
are separate master-data code spaces — see claim #351). This gives step (1)/(4) of the KU's
`how_to_resolve` a confirmed target value: `replicate_project_fund.py` step E ("budget-fund") should load
FISTL=YAO for this fund. It does NOT resolve why the target-system (D01/V01) posting still fails "No funds
center entered/derived" — that remains a config-gap-vs-replication-incomplete open question.
