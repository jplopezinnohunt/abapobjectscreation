# Travel Domain — UNESCO SAP Intelligence

**Created:** 2026-04-08 (Session #048)
**Trigger:** INC-000006073 — intercompany travel posting failure

## Domain Scope

UNESCO Travel Management: trip creation (PR01/PR02), travel posting (PRRW/RPRAPA00), travel advances, expense settlements, intercompany postings, Business Area derivation chain.

## Key Processes

| Process | TCodes | SAP Program | Custom Code |
|---|---|---|---|
| Trip Creation | PR01, PR02 | — | — |
| Trip Display | PR05 | — | YPR_TRIP_COST_ASSIGNMENT_DATA2 |
| Travel Posting Run | PRRW | RPRAPA00 → PTRV_TRANSLATE (FM group HRTS) | ZXTRVU05, ZXTRVU03, ZCL_IM_TRIP_POST_FI |
| A/P Account Creation | — | RPRAPA00 | YFI_RPRAPA00_COMPL |
| BusA Substitution | GGB1 | — | YRGGBS00 → YCL_FI_ACCOUNT_SUBST_READ |
| BusA Validation | GGB0 | — | ZFI020 message |

## Business Area Derivation Chain (5 Layers)

```
Layer 1: SAP Standard (LHRTSF01.abap:848-860)
   → IF epk-bukst = epk-bukrs → copies GSBER from employee master
   → ONLY works for same-company postings

Layer 2: BAdI ZCL_IM_TRIP_POST_FI (CM00A.abap:12-82)
   → Reads PA0027 subtype 02 → derives GSBER from KGB field
   → Fallback when Layer 1 doesn't fill GSBER

Layer 3: Travel Exit ZXTRVU05 (ZXTRVU05_v2.abap:23-73)
   → CASE BUKRS: UNES active, WHEN OTHERS commented out (Konakov 2018)

Layer 4: GGB1 Substitution (inside FI BAPI simulation)
   → Rules from GB901/GB922 config
   → YTFI_BA_SUBST / YBASUBST range-based lookup

Layer 5: GGB0 Validation (inside FI BAPI simulation)
   → ZFI020: company-code-specific BusA restrictions
```

## Extracted Code Assets

### SAP Standard (34 files, 24,559 lines)
Location: `extracted_code/SAP_STANDARD/TV_TRAVEL/`

| File | Lines | Content |
|---|---|---|
| **LHRTSF01.abap** | 3,526 | Core GSBER/BUKST logic — line 852 same-company check, line 1693 vendor GSBER clear |
| **LHRTSU01.abap** | 304 | PTRV_TRANSLATE function module |
| **LHRTSU05.abap** | 257 | PTRV_ACC_EMPLOYEE_PAY_POST — RW609 wrapper |
| **LHRTSU04-08.abap** | ~900 | Other posting FMs |
| **LHRTSTOP.abap** | 253 | Global data (gsber_a/gsber_g flags) |
| **LHRTSF02-06.abap** | ~2,970 | Additional forms (tax, splitting, clearing) |
| **RPRAPA00 + includes** | ~6,300 | Travel A/P Account Creation |
| **RPRTRV00-11.abap** | ~2,750 | Travel posting programs |
| **RPRTB000*.abap** | ~5,340 | Travel batch processing |
| **RPRTRVDT.abap** | 440 | Travel data types (PSREF structure) |

### UNESCO Custom (35 files)
Location: `extracted_code/UNESCO_CUSTOM_LOGIC/TV_TRAVEL/`

| File | Content |
|---|---|
| **ZCL_IM_TRIP_POST_FI_CM00A.abap** | BAdI: PA0027-02 GSBER derivation |
| **ZCL_IM_TRIP_POST_FI_CM006.abap** | BAdI: Doc type TV/TF by BUKRS/WERKS |
| **ZCL_IM_TRIP_POST_FI_CM007.abap** | BAdI: Travel user code from PERSG |
| **ZCL_IM_TRIP_POST_FI_CM008.abap** | BAdI: Doc type from PA0001 |
| **ZXTRVU05_v2.abap** | Exit: BusA derivation (UNES active, others commented out) |
| **ZXTRVU03_v2.abap** | Exit: Period overlap validation |
| **YFI_YRGGBS00_EXIT.abap** | GGB1 exit: BVTYP for travel vendors |
| **YFI_RPRAPA00_COMPL.abap** | Wrapper: Vendor bank data update |

## Gold DB Tables

| Table | Content | Rows |
|---|---|---|
| PTRV_SCOS | Trip cost assignment (company code, BusA, fund) | TBD |
| PTRV_SHDR | Trip header summary (amounts, dates) | TBD |
| GB901 | GGB0/GGB1 conditions | 583 |
| GB922 | GGB1 substitution results | TBD |
| GB02C | GGB error messages | 10 |
| GB903 | GGB field sets | 3 |
| T100_ZFI | ZFI message texts | 36 |
| YBASUBST | Legacy BusA substitution | 752 |
| YTFI_BA_SUBST | Range-based BusA substitution | 129 |
| LFB1 | Vendor master company code (AKONT) | TBD |
| LFA1 | Vendor master general (KTOKK) | TBD |

## Key Relationships (Brain Edges)

```
LHRTSF01.abap:852 --READS--> PA0001.GSBER (employee BusA)
LHRTSF01.abap:852 --CHECKS--> epk-bukst = epk-bukrs (same company)
LHRTSF01.abap:1693 --CLEARS--> epk-gsber (vendor line)
ZCL_IM_TRIP_POST_FI_CM00A --READS--> PA0027 subtype 02 (cost distribution)
ZCL_IM_TRIP_POST_FI_CM00A --DERIVES--> GSBER from KGB field
ZXTRVU05 --CALLS--> FUND_BA_WBS_CC (for UNES only)
ZXTRVU05 --DISABLED--> inst_fund_ba_wbs_cc (for IIEP, commented out)
LHRTSU05 --CALLS--> BAPI_ACC_EMPLOYEE_PAY_POST
BAPI --RUNS--> GGB1 substitution (GB901/GB922)
BAPI --RUNS--> GGB0 validation (ZFI020)
GGB1 rule 3IIEP###002 --COVERS--> GL 2021042, 2021061 (NOT 2021011)
GGB1 Step 003 --SETS--> GSBER='PAR' unconditional for TV docs
LFB1.AKONT --DETERMINED_BY--> LFA1.KTOKK (vendor account group)
KTOKK=UNES --MAPS_TO--> AKONT=2021042
KTOKK=SCSA --MAPS_TO--> AKONT=2021011
PTRV_SCOS.COMP_CODE --DRIVES--> same-company vs intercompany posting
```

## Incidents

| Ticket | Date | Root Cause | Status |
|---|---|---|---|
| INC-000006073 | 2026-04-08 | Intercompany + wrong KTOKK → empty GSBER | Analysis complete, fix pending |

## References

- [INC-000006073 Analysis](../../incidents/INC-000006073_travel_busarea.md)
- [BusA Derivation Chain](../FI/travel_busarea_derivation.md)
- [Session #048 Retro](../../knowledge/session_retros/session_048_retro.md)
