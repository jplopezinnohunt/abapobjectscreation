# Travel Business Area Derivation — UNESCO SAP

**Discovered:** Session #047 (2026-04-08) during INC-000006073 investigation
**Source:** `extracted_code/UNESCO_CUSTOM_LOGIC/TV_TRAVEL/ZXTRVU05_RPY.abap`

## Overview

Travel posting Business Area (GSBER) derivation at UNESCO uses a **multi-layer chain**. The Travel module exit `ZXTRVU05` is the first layer — it runs BEFORE GGB1 substitutions.

## Layer 1: Travel Exit ZXTRVU05

The include `ZXTRVU05` is a SAP user exit called during travel posting (PRRW/RPRAPA00). It loops through posting line items (`KONTI`) and derives Business Area per company code.

### Code (from extracted_code)

```abap
LOOP AT KONTI ASSIGNING <KONTI>.
  CASE <KONTI>-BUKRS.
    WHEN 'UNES'.
      PERFORM INIT_CHECK USING <KONTI>-BUKRS <KONTI>-GEBER <KONTI>-FIPOS
                               SPACE SPACE SPACE SPACE
                               TRIP_PERIOD-PDATV TRIP_PERIOD-ABRJ1
                               <KONTI>-GSBER TRIP_HEADER 'X'
                         CHANGING W_CHECK_STATUS.
      CHECK W_CHECK_STATUS = SPACE.
      PERFORM COMPARE_FUND_WBS USING <KONTI>-POSNR <KONTI>-GEBER SPACE.
      PERFORM FUND_BA_WBS_CC USING <KONTI>-GEBER SPACE SPACE SPACE
                                   <KONTI>-KOSTL <KONTI>-POSNR
                                   <KONTI>-GSBER 'X'.
    WHEN 'UBO'.
      " Empty — no BusA derivation for UBO
    WHEN OTHERS.
*     perform inst_fund_ba_wbs_cc using <KONTI>-bukrs
*                                       <KONTI>-geber space space space
*                                       <KONTI>-kostl <KONTI>-posnr
*                                       <KONTI>-gsber 'X'.
  ENDCASE.
ENDLOOP.
```

### Key Findings

| Company Code | BusA Derivation | Status |
|---|---|---|
| **UNES** | `FUND_BA_WBS_CC` — derives from fund/WBS/cost center | **ACTIVE** |
| **UBO** | Nothing — empty WHEN block | **NO DERIVATION** |
| **IIEP** (WHEN OTHERS) | `inst_fund_ba_wbs_cc` — similar derivation | **COMMENTED OUT** |
| **IBE, ICBA, ICTP, MGIE, UIL, UIS** (WHEN OTHERS) | Same commented-out code | **COMMENTED OUT** |

### Impact

- For **UNES** travel lines: BusA is derived from the fund by `FUND_BA_WBS_CC`
- For **ALL other company codes**: the institute-specific derivation (`inst_fund_ba_wbs_cc`) is **disabled**
- These company codes rely on:
  - **GGB1 substitutions** (layer 2) — e.g., rule `3IIEP###002` covers GL 2021042/2021061
  - **Trip master data** — the Travel module may pass BusA from PA0001 GSBER field
  - If neither provides BusA, the line stays empty

### The Comment

The code was commented out by someone (possibly I_KONAKOV based on the comment style `***I_KONAKOV 04/2018` in the same file). The reason is unknown — possibly to avoid conflicts with GGB1 substitution or because institute-specific derivation was moved elsewhere.

## Layer 2: GGB1 Substitution (Form U910 / YCL_FI_ACCOUNT_SUBST_READ)

After the Travel exit, GGB1 substitution rules fire:
- `3IIEP###002`: Substitutes BusA for GL 2021042/2021061 in TV/TF docs with empty GSBER
- `3IIEP###004`: Condition for TV/TF general (result unknown)
- `3IIEP###006`: Condition for vendor lines KOART='K' (result unknown)
- `YTFI_BA_SUBST`: Zero global rules for IIEP (only Z1 doc type entries)

## Layer 3: GGB0 Validation (ZFI020)

After substitution, validation fires:
- `2IIEP###001`: Checks GSBER <> DAE/GEF/MBF/OPF/PFF — **allows empty BusA**
- ZFI020 message is displayed but does NOT block empty BusA

## Relevance to INC-000006073

The commented-out `inst_fund_ba_wbs_cc` for non-UNES company codes means:
1. In IIEP same-company travel: BusA comes from GGB1 substitution (GL 2021042→PAR) or trip data
2. In intercompany travel (IIEP traveler on UNES fund): the UNES line gets BusA from `FUND_BA_WBS_CC`, but the IIEP counterpart line gets NOTHING from this exit
3. If GGB1 doesn't cover the IIEP line's GL account (e.g., 2021011), BusA stays empty

## PERFORMs to Investigate

| PERFORM | Purpose | Location |
|---|---|---|
| `FUND_BA_WBS_CC` | Derives BusA from fund/WBS/cost center (UNES only) | Unknown include — needs extraction |
| `inst_fund_ba_wbs_cc` | Institute-specific version (commented out) | Unknown include — needs extraction |
| `INIT_CHECK` | Validates fund/fipos combination | Unknown include |
| `COMPARE_FUND_WBS` | Compares fund with WBS element | Unknown include |

These PERFORMs likely live in an include within the Travel module's function group or in a custom include referenced by ZXTRVU05.

## Custom Travel Objects Discovered (TADIR search, Session #047)

**180 Z/Y objects** related to Travel found in P01. Key objects for BusA derivation investigation:

### Classes (BAdI implementations)

| Object | Package | Purpose |
|---|---|---|
| **`ZCL_IM_TRIP_POST_FI`** | YV-STEPS-TRAVEL | **BAdI for Trip FI Posting — most likely contains GSBER logic** |
| `ZCL_IM_TRIP_UNESCO` | YV-STEPS-TRAVEL | BAdI for Trip UNESCO customization |
| `ZCL_EX_TRIP_UNESCO` | YV-STEPS-TRAVEL | Exit class for Trip UNESCO |
| `ZCL_TRIP` | YV-STEPS-TRAVEL | Custom Trip class |
| `ZCL_TV_T9TVACC` | YV-STEPS-TRAVEL | Trip account determination |
| `YCL_TV_TRAVEL_SUSPENSE_BL` | YV | Travel suspense account logic |
| `YCL_TV_DASHBOARD_1_BL` | YV | Travel dashboard |

### Enhancements

| Object | Package | Purpose |
|---|---|---|
| **`ZENH_UNES_CALL_TRIP_BAPI2`** | YV | **Enhancement to Travel BAPI call** |
| **`ZENH_UNES_GET_TRIP_BAPI`** | YV | **Enhancement to get Trip BAPI data** |
| `YENH_FI_PRAA_TRAVEL_FLAG` | YV | FI posting travel flag |
| `YTRIP_INACTIVE_EMPLOYEE` | YV | Inactive employee check |

### Function Groups

| Object | Package | Purpose |
|---|---|---|
| **`YHRTRV_IF`** | YV | **HR Travel Interface — custom function group** |
| `YTVXML` | YV | Travel XML processing |
| `YTV_DASHBOARD` | YV | Travel dashboard functions |
| `ZT9TVACC` | YV-STEPS-TRAVEL | Trip account determination |
| `ZRFC_TRAVEL_DELETE` | YUBO | Travel deletion RFC |

### Programs (includes)

| Object | Package | Purpose |
|---|---|---|
| **`YPR_TRIP_COST_ASSIGNMENT_DATA2`** | YV | **Trip cost assignment data — likely has GSBER logic** |
| `YPR_TRIP_DATA_FORM_ROUTINES` | YV | Trip data form routines |
| `YPR_TRIP_DATA_TOP` | YV | Trip data declarations |
| `YPR_TRIP_ROUT_1_4` | YV | Trip routines 1-4 |
| `ZPR_TRIP_HEADER_DATA` | YV | Trip header data |
| `ZTV_FORMS_CLASSES` | YV-STEPS-TRAVEL | Trip forms/classes |
| `ZXTRVU05` | YV | **Travel exit — BusA derivation (analyzed)** |
| `ZXTRVU03` | YV-STEPS-TRAVEL | Travel exit — validation |
| `ZXTRVZZZ` | YA | Travel exit — other |

### BAdI Registrations

| Object | Package |
|---|---|
| `ZTRIP_POST_FI` (SXCI) | YV-STEPS-TRAVEL |
| `ZTRIP_UNESCO` (SXCI/SXSD) | YV-STEPS-TRAVEL |

### Source Code Extracted (Session #047)

All extracted via `RPY_PROGRAM_READ` from P01:

| Program | Lines | GSBER? | Content |
|---|---|---|---|
| `ZCL_IM_TRIP_POST_FI` (14 methods) | ~300 total | **CM00A: YES** | BAdI — `EX_ZWEP_ACCOUNT2` reads PA0027-02 for BusA |
| `ZXTRVU05` | 78 | YES | Travel exit — BusA derivation per company code |
| `YFI_YRGGBS00_EXIT` | 29 | No | Bank data for travel payments (BVTYP) |
| `YFI_RPRAPA00_COMPL` | 87 | No | Travel posting run completion |
| `YFI_LFBK_TRAVEL_UPDATE` | 146 | No | Vendor bank travel update |
| `ZENH_UNES_GET_TRIP_BAPI` | 446 | No | Enhancement for trip form data (PDF) |
| `ZENH_UNES_CALL_TRIP_BAPI2` | 21 | No | Enhancement for trip form call |
| `YPR_TRIP_COST_ASSIGNMENT_DATA2` | 576 | No | Trip cost assignment data |
| `YPR_TRIP_DATA_FORM_ROUTINES` | 490 | No | Trip form routines |

**Only two custom code points touch GSBER:** `ZCL_IM_TRIP_POST_FI::CM00A` and `ZXTRVU05`.

### Trip Cost Assignment Table (PTRV_SCOS) — Key Discovery

The trip cost assignment in PTRV_SCOS determines the company code and BusA for the posting:

| Field | Purpose |
|---|---|
| COMP_CODE | Company code assigned to the trip → determines which company code the expense posts to |
| BUS_AREA | Business Area → propagated to the posting lines of that company code |
| FUND | Fund → determines budget source |
| FUNDS_CTR | Fund Center |
| WBS_ELEMT | WBS Element |

**When COMP_CODE differs from the employee's home company code, the posting becomes intercompany.** The IIEP counterpart clearing line does NOT receive the BUS_AREA from the cost assignment (it belongs to a different company code).

### Priority for Next Session

1. **Extract PTRV_SCOS for 2024-2026** into Gold DB — enables travel domain analysis across all company codes
2. **Extract PTRV_SHDR for 2024-2026** — trip header summaries
3. **Create Travel domain knowledge** — new domain under `knowledge/domains/Travel/`
4. **Investigate:** Can ZXTRVU05 `inst_fund_ba_wbs_cc` be safely uncommented for IIEP?
