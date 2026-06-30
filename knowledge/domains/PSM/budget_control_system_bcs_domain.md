---
name: Budget Control System (BCS) — UNESCO domain synthesis + reusable toolset
description: Canonical synthesis of the UNESCO SAP Budget Control System (Funds Management BCS + PS integration) — the model (master data, budget addressing, AVC/disponible, RIB cost-recovery, C/5 biennium, FM-PS link), the two operations (ALIGN a system P01→target, CREATE via the PPM→SAP flow), the reusable tool catalog, and the session deep-analysis (findings, corrections, gotchas). Built across s093 (2026-06-29/30), verified by live RFC on D01/P01.
type: domain
domain: PSM / Fund_Management / BCS / Project_System
evidence_tier: TIER_1
cross_links:
  - knowledge/domains/PSM/ppm_sap_project_fund_e2e_flow.md
  - knowledge/domains/PSM/fund_management_sync_playbook.md
  - knowledge/domains/PSM/cost_recovery_avc_disponible_model.md
  - knowledge/domains/PSM/ps_project_replication_and_ki235.md
  - knowledge/system_operating_model_rfc.md
  - knowledge/gold_db_table_catalog.md
---

# Budget Control System (BCS) — UNESCO domain synthesis

> One home for everything the FM/BCS+PS work produced. Two things you can DO in this domain: **ALIGN**
> (replicate a system's master+budget P01→D01/V01) and **CREATE** (stand up a project+fund the way PPM does).

## 1. The model (what BCS is at UNESCO)

**Three budget master dimensions + addressing:**
| Dim | SAP table | Key | Note |
|-----|-----------|-----|------|
| Fund | FMFINCODE (+FMFINT) | FIKRS+FINCODE | **FINCODE = PSPID** (twin of the PS project) |
| Fund Center | FMFCTR (+FMFCTRT) | FIKRS+FICTR | hierarchical (FMHIVARNT) |
| Commitment Item | FMCI (+FMCIT) | FIKRS+GJAHR+FIPEX | budget CIs = FP-series + control CIs (TC, 10'/11/13/20-80) |
| Functional Area | TFKB | FKBER | |

**Budget is stored in BPGE (overall) / BPJA (annual)** addressed by **(Fund GEBER, Object OBJNR, Commitment
Item POSIT, WRTTP, VERSN)**. Two object levels carry budget (verified): **fund center (`OBJNR FS*`)** and
**WBS / project (`OBJNR PR*`)**. Budget is posted via the **BCS budget entry document** (`BAPI_0050_CREATE`,
UNESCO wrapper `Y_FMKU_0050_CREATE_WITH_COMMIT`).

**Availability Control (AVC)** — ledger **9H**, totals in **FMAVCT**, controls consumption at a **control
address** (e.g. fund center NAI + control commitment items), not at the posting leaf. Availability MUST come
from the standard (FMAVCT/FMAVCR/FMAVC read FMs), never hand-rolled.

**Disponible / cost recovery (RIB)** — for cost-recovery projects the spendable budget is created by
**Revenues Increasing the Budget (RIB)**: the assignment is `PROCESS=ENTR / VALTYPE=B1 / BUDTYPE=3000` on
commitment item TC (control fund center), DISTINCT from the recovery movements (`COSD`/`CORV`/BUDTYPE 4000).
Budget is **annual** (each FY needs its own; carryforward rolls residual). Cover funds = `633CRP9*`.

**C/5 biennium** — `YTFM_FUND_C5` (fund × C5_ID × output; C5_ID 43 = 2026-27) via `Y_BAPI_FUND_C5_ASSIGNMENT`.

**FM↔PS integration** — FINCODE=PSPID; the WBS is the CO object (satisfies KI235 — a WBS *is* a cost object;
OKB9 is NOT the mechanism for these). PS=source of truth for project structure; FM holds the budget.

## 2. Capability-model placement (PSM_FM)
- **D_DATA** — the master tables above + budget totals (BPGE/BPJA) + AVC (FMAVCT) + C5 (YTFM_*).
- **C_CONFIG** — OKB9 (TKA3A/TKA3C), project profiles (Z000002/Z000012), AVC ledger 9H, derivation FMDERIVE.
- **A_PROCESS** — the create/budget E2E (§3) + the recovery process (RIB).
- **F_INTERFACE** — PPM↔SAP via MuleSoft (the synctrigger fleet); FINCODE=PSPID linkage.
- **G_CONFORMANCE** — gap-based ALIGN (P01→target) is the delta engine.

## 3. The two operations

### 3a. CREATE — the PPM→SAP flow (canonical; how every project+fund is born)
PPM (Salesforce/Core Planner) = master → MuleSoft writes into SAP, in order:
**A** fund `Y_FMKU_0050_CREATE_WITH_COMMIT` · **B** fund→C5 `Y_BAPI_FUND_C5_ASSIGNMENT` ·
**C** project+WBS `BAPI_PROJECT_MAINTAIN` · **D** WBS attrs `Y_BAPI_WBS_TEXT_MAINTAIN`/`Y_BAPI_WBS_CUS_FIELD_UPDATE` ·
**E** budget→fund (BAPI_0050, FS* addr) · **F** budget→project (BAPI_0050, PR* addr / ENTR-B1).
Back: `Y_BAPI_WBS_FINANCIAL_DATA_1`, `Y_BAPI_YPS8`. Full flow: ppm_sap_project_fund_e2e_flow.md.

### 3b. ALIGN — replicate master+budget P01 → D01/V01 (gap-based)
Read both LIVE (ROWCOUNT=0 by FIKRS — both P01 & D01 reject ROWSKIPS), diff by key, write ONLY the delta via
the standard create FMs, verify gap=0 by re-read. Scope biennium-linked dims to C5/43; non-biennium dims to
full current-master diff. Result s093: C5/43 fund model gap=0 (funds/centers/Z); disponible 2025+2026 for 5 CR funds.

## 4. Reusable toolset (`Zagentexecution/tasks/2026_06_29_fm_model_sync/`)
| Tool | Operation | Status |
|------|-----------|--------|
| `fund_sync.py <TGT>` | ALIGN funds (FMFINCODE+FMFINT, C5/43) via FM_FUND_CREATE_RFC | ✅ proven |
| `fund_center_sync.py <TGT>` | ALIGN fund centers + hierarchy (topological) via FM_FUNDS_CTR_CREATE_RFC | ✅ proven |
| `fund_reconcile.py <TGT>` | ALIGN field-level (make funds identical to P01) via FM_FUND_CHANGE_RFC | ✅ proven |
| `fund_family_sync.py <TGT> <prefix>` | ALIGN a fund family by prefix (e.g. 633CRP9 credits) | ✅ proven |
| `z_tables_sync.py <TGT> <which>` | ALIGN UNESCO Z (YTFM_FUND_C5/CPL/OUTPUT) via INSERT | ✅ proven |
| `budget_assign_entr.py <TGT> commit [FUND] [YEAR]` | budget→project (ENTR/B1/3000) via BAPI_0050 | ✅ proven |
| `ps_project_sync.py <TGT> <PSPID> [resp] [appl]` | CREATE project def + (flat) WBS + release via BAPI_PROJECT_MAINTAIN | ✅ proven (nested→CJ20N) |
| `replicate_project_fund.py <PSPID> <TGT> dry\|run` | ORCHESTRATOR — full A→F for one project+fund | ✅ A/C/F proven; B/D/E wire-up |
| `scripts/extraction/gold_refresh.py PSM_FM [type]` | refresh the gold (P01 source of truth), delta-aware | ✅ proven |
All target-parameterized (D01 or V01; add `SAP_V01_*` to .env). Source always P01 (read-only).

## 5. Session deep-analysis — findings, corrections, gotchas (s093)
**Verified facts:** FINCODE=PSPID · two budget levels (FS*/PR*) · CR disponible = RIB/B1/ENTR-3000 · AVC control
at NAI+control-CIs · OKB9 identical P01=D01 and NOT the KI235 fix (WBS *is* the cost object) · gold `funds` is
key-only (not a write source).

**Verified channel gotchas (each cost real time):**
- FM create FMs default `I_FLG_TESTRUN='X'` → must pass `' '`; ET_MESSAGES empty even on real create → **verify by re-read**.
- Both P01 & D01 reject ROWSKIPS (SAIS) → read `ROWCOUNT=0` partitioned by FIKRS.
- SAP amounts use **trailing minus** (`75695.67-`).
- `BAPI_PROJECT_MAINTAIN`: **REFNUMBER = per-data-table row index** (def=000001, WBS=1-based index, Save=000000) —
  global numbering causes the misleading "WBS already exists". RESPONSIBLE_NO→TCJ04, APPLICANT_NO→TCJ05. Auto-commits.
- `FM_FUND_CHANGE_RFC` blocks budget-scope change once budget exists (justified exception).
- `BAPI_0050` budget: omit PSTNG_DATE (ledger inactive→FMKU020), DOCSTATE='1', DISTKEY='1', ITEM_NUM string, then BAPI_TRANSACTION_COMMIT.

**Corrections made this session (superseded):**
- `Y_RFC_CREATE_PROJECT_SISTER` is an OUTBOUND export (SAP→Salesforce), NOT the creator (commit d259a71 was wrong).
- The CJ20N-creator hypothesis was retracted — the real creator is MuleSoft via `BAPI_PROJECT_MAINTAIN` (already
  documented in system_operating_model_rfc.md; should have been loaded first — CLAUDE.md rule #1).

**Open:** WBS hierarchy NESTING via BAPI by RFC (works for MuleSoft → reproduce its `I_WBS_HIERARCHIE_TABLE`
payload); wire-up+verify B/D/E in the orchestrator; the ~98 funds WRTTP43 fund-budget (~212M) replication.

## 6. Cross-project
Broadcast sent to `unesco-sap-brain` (ADR-007). Other side of the create flow = `unescore20-PPM-brain`
(Salesforce/Core Planner). Gold DB is this project's owned source of truth.
