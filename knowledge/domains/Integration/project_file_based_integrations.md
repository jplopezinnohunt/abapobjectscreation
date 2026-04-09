---
name: File-based job integrations discovery
description: Third integration vector — SAP jobs reading/writing files for external systems (COUPA, SWIFT, EBS, SuccessFactors, TULIP, UNESDIR, Data Hub, MBF)
type: project
---

## File-Based Integration Pattern — Session #035 (2026-04-04)

Third integration tier discovered alongside RFC (334 FMs) and BDC (PRAA/COUPA batch).
SAP background jobs run ABAP programs that read/write files from shared directories.

### 5 Tiers Identified

**Tier 1 — High Volume (production critical):**
- `ZFI_SWIFT_UPLOAD_BCM` (2,778 runs) — SWIFT bank files → SAP BCM
- `RBNK_IMPORT_PAYM_STATUS_REPORT` (4,164 runs) — Payment status files → SAP
- `FEB_FILE_HANDLING` (347 runs) — MT940 bank statements → EBS
- `YFI_COUPA_POSTING_FILE` (348 runs) — **COUPA** files → FI postings
- `YFI_COUPA_POSTING_FILE_MAIL` (3 runs) — COUPA email notifications

**Tier 2 — SuccessFactors (HR export):**
- `YHR_SF_EXPORT_GEODIS` (16 runs) — SAP → SF geo distribution
- `YHR_SF_EXPORT_ORGANIZATION` (16 runs) — SAP → SF org structure
- `RH_SFI_SYNCHRONIZE_EMPL_DATA` (16 runs) — SAP → SF employee data
- **CRITICAL: ECPAO_OM_OBJECT_EXTRACTION** (43 jobs × 30 runs = 1,290) — OM extraction for EC Payroll
- **ECPAO_EMPL_EXTRACTION** (3 jobs × 17 runs) — Employee extraction for EC Payroll
- → SuccessFactors EC is ACTIVE, not "planned" as previously recorded

**Tier 3 — DBCON (TULIP/UNESDIR via SQL Server):**
- `YHR_MANAGER_FROM_TULIP_UPDATE` (15 runs, 93% failure) — TULIP → SAP HR managers
- `YHR_CREATE_MAIL_FROM_UNESDIR` (15 runs, 93% failure) — UNESDIR → SAP email
- `ZLFNA1_DOWNLOAD_FOR_UNESDIR` (15 runs) — SAP vendors → UNESDIR
- `ZLFNA1_DOWNLOAD_VENDOR_TABLE` (15 runs) — Vendor master export

**Tier 4 — Data Hub / BW:**
- `YFM_OUTPUT_INDIRECT_COSTS_DH` (11 runs, per company code) — FM indirect costs → Data Hub
- `YBW_EXTRACT_WBS_LTXT` (15 runs) — WBS long texts → BW
- `YHR_MBF_ELIGIBILITY_FILE` (3 runs) — SAP → Medical Benefits Fund
- `YFI_FILE_RATES_TMS` (1 run) — Treasury exchange rates file

**Tier 5 — Spool / Ad-hoc:**
- `ZSPOOL_TO_FILE` (50 runs) — Spool output → file system (HR staffing, FM monitoring)

### Key Discovery: COUPA Has TWO Integration Vectors
1. File-based: `YFI_COUPA_POSTING_FILE` (348 runs) — bulk FI postings from files
2. BDC: `COUPA0000282/283/284` via `RSBDCBTC_SUB` — batch data communication sessions

### Key Discovery: SuccessFactors EC is ACTIVE
- ECPAO_* programs = Employee Central Payroll extraction
- 43 parallel OM jobs + 3 employee jobs = massive data push
- Previously recorded as "planned, not live" (G41) — THIS IS WRONG, it IS live
- BizTalk middleware confirmed by ECPAO pattern (SAP standard EC Payroll connector)

### Integration Vector Summary
| Vector | Systems | Volume | Discovery Session |
|--------|---------|--------|-------------------|
| RFC (.NET) | SISTER, HR WF, CMT, UBO, Travel, Mouv, Procurement | 334 FMs | #032 |
| RFC (middleware) | MuleSoft→Core Mgr/Plnr | IDocs + RFC | #032 |
| BDC | PRAA (Allos), COUPA | 135+12 sessions/quarter | #012 |
| **File-based** | **SWIFT banks, COUPA, EBS/MT940, SuccessFactors, TULIP, UNESDIR, Data Hub, BW, MBF** | **~8,700 job runs** | **#035** |
| DBCON (SQL) | TULIP, UNESDIR | Direct SQL Server | #032 |

**How to apply:** Update connectivity diagram with file-based tier. Close G41 (SF EC is active). Update H10 with COUPA dual-vector finding. Add file-based integration as discovery vector in `sap_interface_intelligence` skill.
