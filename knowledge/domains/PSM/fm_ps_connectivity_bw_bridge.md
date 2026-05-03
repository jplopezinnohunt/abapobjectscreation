# UNESCO SAP FM-PS Connectivity & BW Bridge

This document details the "System Glue" that ensures data integrity between Fund Management (FM), the Project System (PS), and the Business Warehouse (BW).

## 1. The FM-PS "10-Digit" Hard Link
The fundamental rule connecting Funds to WBS Elements is enforced in the **FM Account Assignment Validation** logic.

*   **Logic File**: [`ZXFMYU22`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMYU22_RPY.abap)
*   **Target Scope**: Fund Types **101 to 112** (Extra-Budgetary / Donor Projects).
*   **The Rule**: The **first 10 characters** of the WBS element (PRPS-POSID) **MUST** exactly match the Fund ID (FMFINCODE-GEBER).

### Technical Enforcement
```abap
362:   CLEAR PRPS.
363:   SELECT SINGLE *
364:         FROM PRPS
365:         WHERE PSPNR = I_COBL-PS_PSP_PNR.
366:   IF PRPS-POSID(10) <> I_COBL-GEBER.
367:     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
368:            WITH 'Incorrect WBS-element or Fund!' ' Please check.'.
369:   ENDIF.
```

---

## 2. The BI/BW Reporting Bridge
While the 10-digit rule ensures transactional integrity, the **BW Extraction Logic** manipulates these fields to provide accurate financial metrics (Converted to USD).

*   **Extraction Logic**: [`ZXRSAU01`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/BI_REPORTING/ZXRSAU01_RPY.abap)
*   **Master Data Logic**: [`ZXRSAU02`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/BI_REPORTING/ZXRSAU02_RPY.abap)

### Key BW Manipulations:
1.  **USD Normalization**: Forces conversion to `BKPF-HWAE2` (Secondary Local Currency) for UNESCO's global reports.
2.  **Date Alignment**: Recalculates the "Real" Posting Date to ensure fiscal periods in BW match the actual transaction time, regardless of when the document was parked or posted.
3.  **Project State Enrichment**: Attaches custom attributes from `ZXRSAU02` to the Project Hierarchy, enabling BI users to filter reports by UNESCO-specific metadata (Sectors, Divisions) not present in standard SAP.

---

## 3. Governance & Bypass (The Control Key)
The integrity of this entire model depends on the **`YXUSER`** table.

*   **Exception Type**: `XTYPE = 'FM'` or `XTYPE = 'FRTL'`.
*   **Impact**: Users listed in this table bypass the 10-digit validation and the hardware tolerance caps (2%).
*   **Audit Risk**: An unauthorized entry in `YXUSER` can break the FM-PS link for any project, allowing budget to be misaligned between the Project and its associated Fund.

---

## 4. FM-AVC vs PS-AVC: the two-engine truth (added Session #66, INC-000005638 extension)

UNESCO runs **two independent availability engines** at the same time. They look at "the same money" but they measure different things and use different schedules. A budget incident is only fully diagnosed when BOTH pools have been computed.

| Engine | Scope | Pool source | Granularity (UNESCO) | Tolerance | Block message |
|---|---|---|---|---|---|
| **FM-AVC** | Fund Management | Live: `FMIFIIT` (revenue) − `FMAVCT` (consumption KBFC). UNESCO's FMAVCT has only KBFC entries — no static budget. | (Fund × FundCenter × **AVC-derived bucket** × Year). Bucket comes from `FMAFMAP013500109` step 0007 strategy AFMA, env `9HZ00001`. | `FMAFMTP013500110` profile, e.g. Z100 strict 100% block | `FMAVC005` "Annual budget exceeded" |
| **PS-AVC** | Project System | `BPJA` cumulative (WRTTP=41 current, 42 original) vs `COSP` (WRTTP=04 actuals, 22 commitments, 24 plan). UNESCO does NOT use COSS on projects. | (Project × value-category × cumulative-or-annual). Project is identified by 10-digit prefix matching the GEBER fund. | `OPSV` profile (not in DD03L; SPRO transports). UNESCO PS-AVC profile not yet captured. | `BP603/604/629` |

### 4.1 The misalignment class (INC-000005638 root)

UNESCO loads donor cash inflow (WRTTP=66) entirely on the FIPEX=`REVENUE` placeholder. The AVC derivation rule for any donor fund (e.g. `196EAR4042` mapped (UNES, 196EAR4042, "10'..50") → TC) does NOT include the REVENUE placeholder in its range. Result: the AVC-derived **TC bucket** sees $0 revenue while consumption fully lands. Pool depth goes negative → FMAVC005 → user blocked. **Yet the fund-level pool says +$11.83M of headroom and the PS-AVC project pool says +$16.43M** — both engines look healthy at fund/project level. Only the AVC-bucket level shows the deficit.

The class detector `Zagentexecution/quality_checks/inc5638_fm_ps_avc_misalignment.py` ranks every (Fund × FundCenter × AVC-bucket × Year) triple by the misalignment signature:

| Tier | Definition | Count (2026 snapshot) |
|---|---|---:|
| **1** — BOTH FM+PS blocking | Critical | **457** |
| **2** — FM blocking only (the INC-000005638 class) | High | **1,330** |
| 3 — PS blocking only | Medium | 63 |
| 4 — Neither (healthy) | OK | 248 |
| no_ps_link (FM only, no project) | n/a | 3,601 |

INC-000005638 ranks as `196EAR4042/WHC/TC` Tier 2 at -$1,561,651.78. The new biennium fund `196EAR4043/WHC/TC` is also Tier 2 — proving the class is **structural to UNESCO config**, not biennium-specific.

### 4.2 Mandatory data pulls before any FM/PS-AVC root-causing

Per rule `feedback_pull_both_avc_engines_before_root_cause` (HIGH severity, established Session #66):

1. **EKKN** for each PO line → resolve `PS_PSP_PNR`.
2. **PRPS** for the WBS → resolve OBJNR and project key.
3. **BPJA** WRTTP=41 cumulative across 2024-2026 for that project's WBS family → PS budget side.
4. **COSP** WRTTP=04+22 across 2024-2026 for the same OBJNR set → PS consumption side.
5. **FMAFMAP013500109** for the fund → identify the AVC-derived bucket.
6. **FMIFIIT** WRTTP=66 with FIPEX in the derivation range → FM revenue side.
7. **FMAVCT** with `(RFIKRS, RFUND, RFUNDSCTR, RCMMTITEM=bucket, RYEAR, ALLOCTYPE_9='KBFC')` → FM consumption side.
8. Compute both pool depths. The engine that fires is the one with negative pool. If both negative → BOTH; if neither → check next-level granularity (custom validation, BTE, BAdI).

### 4.3 Fix patterns

- **Class fix**: extend `FMAFMAP013500109` derivation to include `FIPEX=REVENUE` in the rule's range, OR refactor the MuleSoft donor-revenue posting to apportion across operational FIPEX. Either resolves all 1,330 Tier-2 buckets at once.
- **Per-incident fix**: load supplementary 2026 budget on the operational FIPEX of the affected (Fund × FundCenter) via `FMBB` / `FMX1`. Local but does not prevent recurrence.
- **`FMAVCREINIT` does NOT fix the class**: it only re-derives existing consumption into AVC buckets; it does not redistribute revenue from the placeholder to operational FIPEX.

### 4.4 Reference scripts and tables (Session #66)

- Extraction: `Zagentexecution/sap_data_extraction/extract_ps_avc_tables.py`
- Per-PO analysis: `Zagentexecution/quality_checks/inc5638_per_po_engine_analysis.py`
- Class detector: `Zagentexecution/quality_checks/inc5638_fm_ps_avc_misalignment.py`
- New Gold DB tables: `bpge`, `bpja_2024/25/26`, `cosp_2024/25/26`, `coss_2024/25/26`, `fmavct_2024/25/26`, `fmafmap013500109`, `fmafmtp013500110`, `tka01`, `bphi`, `ekkn_inc5638*`
