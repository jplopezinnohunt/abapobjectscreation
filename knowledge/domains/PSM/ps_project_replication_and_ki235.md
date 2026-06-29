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

## THE GOOD PROCESS (hierarchical WBS) — and what NOT to do
Hierarchy is **not** derived from the POSID dots; it must be given explicitly in **`I_WBS_HIERARCHIE_TABLE`**
(WBS_ELEMENT/PROJECT_DEFINITION/UP/DOWN/LEFT/RIGHT — set `UP` = parent POSID for each node). The good process
is **ONE clean call on a project that does NOT yet exist in the target**:
`I_PROJECT_DEFINITION` + `I_WBS_ELEMENT_TABLE` (all WBS, parents-before-children) + `I_WBS_HIERARCHIE_TABLE`
(UP=parent) + `I_METHOD_PROJECT` [Create ProjectDefinition, Create WBS-Element*, Save] → commit → Release all.
Script: `ps_project_sync.py` (has a precondition guard that ABORTS if the project already has WBS).

**ANTI-PATTERN that corrupted 504PAK1000 (do NOT repeat):** iterating with `METHOD='Delete'` to "retry" a
failed create. A delete on a WBS sets the **deletion flag (system status DLFL / I0076)**, which has **NO
clean RFC reset** (STATUS_CHANGE_EXTERN = user-status only; STATUS_CHANGE_INTERN = NOT_FOUND/DA300; no
public PS BAPI). The only reset is **CJ20N → "reset deletion indicator"**. So: never delete-to-retry; if a
create fails, fix the input and re-run the single clean call against a non-existing project.

**504PAK1000 current state:** root WBS exists but deletion-flagged (DLFL) from delete-to-retry attempts.
To finish it: reset its deletion flag in CJ20N (one status op), delete it there, then run `ps_project_sync.py
D01 504PAK1000 10133238 00000001` (clean one-call create). The recipe itself is sound; the blocker is the
self-inflicted DLFL, not a BAPI limitation.

## Result P01→D01 (s093) — KI235 culprits
- 000CRP9000 (1 flat WBS): created + REL ✓
- 633CRP9003: pre-existing in D01 ✓
- 504PAK1000: project def + root WBS created + REL ✓; children 504PAK1000.4 / .4.4 PENDING (hierarchy issue)
→ 2 of 3 KI235 WBS fully available; the 504PAK1000.4.4 line still needs the hierarchical WBS (CJ20N).
