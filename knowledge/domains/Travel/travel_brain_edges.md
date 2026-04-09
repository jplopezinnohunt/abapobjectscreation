# Travel Domain — Brain Relationship Graph

**Purpose:** Define edges (relationships) between travel code, config, and data nodes for Brain v2 ingestion.
**Session:** #048 (2026-04-08)

## Node Inventory (69 files)

### SAP Standard Code Nodes (34)
All in `extracted_code/SAP_STANDARD/TV_TRAVEL/`:
- LHRTSF01.abap (3,526 lines — CORE: GSBER derivation, cross-company posting)
- LHRTSU01.abap (PTRV_TRANSLATE FM)
- LHRTSU02-08.abap (posting FMs)
- LHRTSTOP.abap (global data)
- LHRTSF02-06.abap (forms)
- SAPLHRTS.abap (include list)
- LHRTSUXX.abap (dispatch)
- RPRAPA00.abap + RPRAPADE_ALV + RPRAPAFO_ALV + RPRAPA00_PBO + RPRAPAEX + RPRAPAEX_001 + RPUMKC00 + TSKHINCL (A/P account creation)
- RPRTRV00/01/10/11.abap (posting)
- RPRTRVDT.abap (data types)
- RPRTB000.abap + RPRTB000_ALV.abap (batch)
- RPRTEC00.abap + RPRTEF00.abap (expense calc/form)

### UNESCO Custom Code Nodes (35)
All in `extracted_code/UNESCO_CUSTOM_LOGIC/TV_TRAVEL/`:
- ZCL_IM_TRIP_POST_FI_CP/CI/CM001-CM009/CM00A-CM00D.abap (14 BAdI methods)
- ZXTRVU05_RPY/v2.abap (travel exit)
- ZXTRVU03_RPY/v2.abap (validation exit)
- ZXTRVZZZ.abap (misc exit)
- YFI_YRGGBS00_EXIT.abap (GGB1 exit)
- YFI_RPRAPA00_COMPL.abap (posting wrapper)
- YFI_LFBK_TRAVEL_UPDATE.abap (vendor bank)
- YENH_FI_PRAA_TRAVEL_FLAGE.abap (enhancement)
- YPR_TRIP_*.abap (4 reporting programs)
- YRPR_TRIP_*.abap (3 reporting programs)
- ZPR_TRIP_HEADER_DATA.abap
- ZTV_FORMS_CLASSES.abap
- ZENH_UNES_CALL_TRIP_BAPI2E.abap + ZENH_UNES_GET_TRIP_BAPIE.abap (enhancements)

## Edge Definitions

### CALLS relationships (code → code)
```
RPRAPA00 --CALLS--> LHRTSU01 (PTRV_TRANSLATE)
LHRTSU01 --CALLS--> LHRTSF01 (form build_epk_from_ep)
LHRTSF01 --CALLS--> LHRTSU05 (PTRV_ACC_EMPLOYEE_PAY_POST)
LHRTSU05 --CALLS--> BAPI_ACC_EMPLOYEE_PAY_POST [external SAP FM]
RPRAPA00 --CALLS--> RPRAPAFO_ALV (forms)
RPRAPA00 --INCLUDES--> RPRAPADE_ALV (data declarations)
RPRAPA00 --INCLUDES--> RPRAPA00_PBO (screen PBO)
RPRAPA00 --INCLUDES--> RPRAPAEX (customer exit)
RPRAPAEX --INCLUDES--> RPRAPAEX_001
LHRTSU01 --INCLUDES--> LHRTSTOP (global data)
SAPLHRTS --INCLUDES--> LHRTSTOP, LHRTSU01-08, LHRTSF01-06, LHRTSUXX
RPRTRV00 --CALLS--> RPRTRV01 --CALLS--> RPRTRV10 --CALLS--> RPRTRV11
```

### IMPLEMENTS relationships (custom → standard)
```
ZCL_IM_TRIP_POST_FI --IMPLEMENTS--> IF_EX_TRIP_POST_FI [BAdI interface]
ZXTRVU05 --ENHANCES--> RPRAPA00 [user exit point 05]
ZXTRVU03 --ENHANCES--> RPRAPA00 [user exit point 03]
ZXTRVZZZ --ENHANCES--> RPRAPA00 [user exit point ZZZ]
ZENH_UNES_CALL_TRIP_BAPI2E --ENHANCES--> RPRTRV10 [implicit enhancement]
ZENH_UNES_GET_TRIP_BAPIE --ENHANCES--> RPRTEF00 [implicit enhancement]
YFI_RPRAPA00_COMPL --WRAPS--> RPRAPA00 [completion processing]
```

### READS relationships (code → data)
```
LHRTSF01:852 --READS--> PA0001.GSBER [employee business area]
LHRTSF01:852 --READS--> epk.bukst [employee home company code]
ZCL_IM_TRIP_POST_FI_CM00A:17 --READS--> PA0027 [cost distribution infotype]
ZCL_IM_TRIP_POST_FI_CM006:16 --READS--> PA0001 [org assignment]
ZCL_IM_TRIP_POST_FI_CM007:6 --READS--> PA0001.PERSG [employee group]
ZCL_IM_TRIP_POST_FI_CM008:5 --READS--> PA0001.BUKRS,WERKS
ZXTRVU03:12 --READS--> PA0017 [travel privileges infotype]
LHRTSU05 --READS--> PTRV_SCOS [trip cost assignment]
YFI_YRGGBS00_EXIT --READS--> LFBK.YYTRAVEL [vendor bank travel flag]
YFI_LFBK_TRAVEL_UPDATE --READS--> LFA1.KTOKK [vendor account group]
```

### DERIVES relationships (code → field)
```
LHRTSF01:854 --DERIVES--> BSEG.GSBER [from gsbst when bukst=bukrs]
LHRTSF01:1550 --DERIVES--> BSEG.GSBER [from bus_area_empl for cross-company tax]
LHRTSF01:1693 --CLEARS--> BSEG.GSBER [vendor lines koart=K, ktosl=HRP/HRV]
ZCL_IM_TRIP_POST_FI_CM00A:60 --DERIVES--> GSBER [from PA0027-02 KGB field]
ZCL_IM_TRIP_POST_FI_CM006:39-63 --DERIVES--> BLART [TV or TF by BUKRS/WERKS]
ZXTRVU05:53 --DERIVES--> GSBER [via FUND_BA_WBS_CC for UNES only]
```

### CONFIGURES relationships (config → behavior)
```
GB901.3IIEP###002 --CONFIGURES--> GGB1 [substitutes PAR for GL 2021042/2021061 in TV]
GB922.Step003 --CONFIGURES--> GGB1 [PAR unconditional for TV — runs inside BAPI]
GB901.2IIEP###001 --CONFIGURES--> GGB0 [ZFI020 validation: blocks DAE/GEF/MBF/OPF/PFF]
YTFI_BA_SUBST --CONFIGURES--> YCL_FI_ACCOUNT_SUBST_READ [range-based BusA lookup]
YBASUBST --CONFIGURES--> YCL_FI_ACCOUNT_SUBST_READ [legacy flat BusA lookup]
T100_ZFI.020 --CONFIGURES--> ZFI020 [message text: "For IIEP...only use PAR, IBA or FEL"]
```

### DETERMINES relationships (data → data)
```
LFA1.KTOKK --DETERMINES--> LFB1.AKONT [vendor account group → reconciliation GL]
LFB1.AKONT --DETERMINES--> BSEG.HKONT [reconciliation GL on vendor posting line]
PTRV_SCOS.COMP_CODE --DETERMINES--> same-company vs intercompany [posting structure]
PTRV_SCOS.BUS_AREA --DETERMINES--> BSEG.GSBER [for "home" company lines only]
PA0001.GEBER --DETERMINES--> PTRV_SCOS.FUND [employee fund → trip funding]
PA0027.KGB01 --DETERMINES--> GSBER [BAdI fallback path]
```

## Edge Count Summary

| Relationship Type | Count |
|---|---|
| CALLS | 13 |
| IMPLEMENTS/ENHANCES/WRAPS | 7 |
| READS | 10 |
| DERIVES/CLEARS | 6 |
| CONFIGURES | 6 |
| DETERMINES | 6 |
| **Total edges** | **48** |

## Ingestion Command

```bash
python sap_brain.py --ingest-domain Travel \
  --code-dir extracted_code/SAP_STANDARD/TV_TRAVEL/ \
  --code-dir extracted_code/UNESCO_CUSTOM_LOGIC/TV_TRAVEL/ \
  --edges knowledge/domains/Travel/travel_brain_edges.md \
  --knowledge knowledge/domains/Travel/README.md \
  --knowledge knowledge/domains/FI/INC-000006073_travel_busarea_analysis.md \
  --knowledge knowledge/domains/FI/travel_busarea_derivation.md
```
