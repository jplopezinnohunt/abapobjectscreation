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

## ⭐ THE REAL UNESCO CREATION PATH — `Y_RFC_CREATE_PROJECT_SISTER` (use THIS, not raw BAPI)
UNESCO/PPM (Salesforce, the "SISTER" system) creates projects + WBS daily via a **custom RFC**, NOT raw
BAPI_PROJECT_MAINTAIN:
```
Salesforce → Y_RFC_CREATE_PROJECT_SISTER (RFC) → SUBMIT report YEBPROJ_CREATE_PROJECT_SISTER → project + WBS hierarchy
```
- Input `IT_PROJ_PRPS` (table `YRFC_PROJ_PRPS_CREATE_SISTER`) is **BUSINESS-level**, ONE row per project:
  PSPID, FUND_TYPE, RESPON, APPLIC, DIVISION, SECTOR, REGION, COUNTRY, CCAQ, VALID_FROM/TO, CREATION_DATE,
  SISTER_CODE, APPROVED, YE_TYP_SOU, YE_EXEC, DONOR, TITLE, STATUS_TXT. + RFC_FROM_DATE/RFC_TO_DATE. Returns BAPIRETURN.
- It does **NOT** take explicit WBS — the report **GENERATES the WBS hierarchy internally** from the business
  attributes (UNESCO C/5 sector→output model). This is why the WBS nesting "just works" for Salesforce.
- Companions: `Y_RFC_MODIFY_PROJECT_SISTER` (change), `Y_RFC_WBS` (WBS read by fund).
- **Implication:** to replicate a UNESCO project faithfully, call `Y_RFC_CREATE_PROJECT_SISTER` with the
  project's PPM business attributes — do NOT hand-build WBS via BAPI_PROJECT_MAINTAIN. The raw-BAPI section
  below documents what was learned (REFNUMBER, nesting limit) but the SISTER RFC is the sanctioned tool.
  Open: capture YRFC_PROJ_PRPS_CREATE_SISTER field mapping for 504PAK1000 + read report YEBPROJ_CREATE_PROJECT_SISTER
  WBS-generation logic (blocked when D01 RFC connectivity dropped overnight 2026-06-29/30).

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
