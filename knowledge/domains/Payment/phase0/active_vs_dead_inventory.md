# Active vs Dead Inventory — P01 evidence anchored
**Generated**: from P01 snapshot 2026-04-29

## Principle

**P01 = source of truth.** An object is ACTIVE only if there is direct P01 runtime evidence that it gets exercised. D01 existence does NOT prove active status — D01 may carry stale or experimental code.

Evidence categories:
- DMEE tree active: `DMEE_TREE_HEAD.EX_STATUS='A'` (or recent VERS_USER)
- FM active via Event 05: registered in `TFPM042FB.FNAME` for our trees
- FM active via node hook: appears in `DMEE_TREE_NODE.MP_EXIT_FUNC` for our trees
- Class active: extracted from P01 + has ENHO/factory wiring evidence
- Customizing active: referenced by routed payment methods

## ACTIVE — DMEE trees (4)

| Tree | V | Last user | Last date | XSLT | Evidence |
|---|---|---|---|---|---|
| `/SEPA_CT_UNES` | 000 | M_SPRONK | 20211123 | (none) | DMEE_TREE_HEAD V000 active maintained recently |
| `/CITI/XML/UNESCO/DC_V3_01` | 000 | M_SPRONK | 20230131 | CGI_XML_CT_XSLT | DMEE_TREE_HEAD V000 active maintained recently |
| `/CGI_XML_CT_UNESCO` | 000 | FP_SPEZZANO | 20250320 | (none) | DMEE_TREE_HEAD V000 active maintained recently |
| `/CGI_XML_CT_UNESCO_1` | 000 | FP_SPEZZANO | 20250214 | (none) | DMEE_TREE_HEAD V000 active maintained recently |

## ACTIVE — Function modules registered Event 05 (2)

| FM | Trees using | Evidence |
|---|---|---|
| `/CITIPMW/V3_PAYMEDIUM_DMEE_05` | /CITI/XML/UNESCO/DC_V3_01 | Registered in TFPM042FB Event 05 for active trees |
| `FI_PAYMEDIUM_DMEE_CGI_05` | /CGI_XML_CT_UNESCO, /CGI_XML_CT_UNESCO_1, /CGI_XML_CT_UNESCO_BK | Registered in TFPM042FB Event 05 for active trees |

## ACTIVE — Function modules used at node level (EXIT_FUNC) (33)

| FM | Trees using | Evidence |
|---|---|---|
| `/CITIPMW/V3_CGI_BANK_NAME` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_CRED_PO_CITY` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_CRED_REGION` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_CRED_STREET` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_REGULATORY_INF` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_TAXAMT_TTLAMT` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_TAX_CATEGORY` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_TAX_CTGRY_DTLS` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_TAX_FORMS_CODE` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_CGI_TAX_METHOD` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_DMEE_EXIT_CGI_XML` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_DMEE_EXIT_INV_DESC` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_EXIT_CGI_CRED_CITY` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_EXIT_CGI_CRED_NAME` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_EXIT_CGI_CRED_NM2` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_EXIT_CGI_CRED_NM3` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_EXIT_CGI_CRED_NM4` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_EXIT_CGI_DEBT_NAME` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_EXIT_CGI_TAX_SQNB` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_EXIT_CGI_TP_WHT` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_GET_CDTR_BLDG` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_GET_CDTR_EMAIL` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_GET_CDTR_MOBILE` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_POSTALCODE` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_TAXAMT_TXBASEAMT` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `/CITIPMW/V3_WL949_BIC_OR_ID` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `DMEE_EXIT_SEPA_21` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |
| `DMEE_EXIT_SEPA_31` | /CITI/XML/UNESCO/DC_V3_01     , /SEPA_CT_UNES      | Used as MP_EXIT_FUNC in 2 tree(s) |
| `DMEE_EXIT_SEPA_41` | /CITI/XML/UNESCO/DC_V3_01     , /SEPA_CT_UNES      | Used as MP_EXIT_FUNC in 2 tree(s) |
| `DMEE_EXIT_SE_DATE` | /SEPA_CT_UNES                  | Used as MP_EXIT_FUNC in 1 tree(s) |
| `FI_CGI_DMEE_EXIT_W_BADI` | /CGI_XML_CT_UNESCO            , /CGI_XML_CT_UNESCO | Used as MP_EXIT_FUNC in 2 tree(s) |
| `ZDMEE_EXIT_SEPA_21` | /SEPA_CT_UNES                  | Used as MP_EXIT_FUNC in 1 tree(s) |
| `Z_DMEE_EXIT_TAX_NUMBER` | /CITI/XML/UNESCO/DC_V3_01      | Used as MP_EXIT_FUNC in 1 tree(s) |

## ACTIVE — UNESCO custom classes (5)

| Class | Role | Evidence |
|---|---|---|
| `YCL_IDFI_CGI_DMEE_FALLBACK` | BAdI default impl (always dispatched) | Source extracted active in P01 + classes DE/IT/FR are subclasses calling super-> |
| `YCL_IDFI_CGI_DMEE_FR` | BAdI impl for FR-bank vendors | Y_IDFI_CGI_DMEE_COUNTRY_FR ENHO + class extracted from P01 |
| `YCL_IDFI_CGI_DMEE_DE` | BAdI impl for DE-bank vendors | Y_IDFI_CGI_DMEE_COUNTRIES_DE ENHO + class extracted from P01 (P01_ONLY — needs retrofit to D01) |
| `YCL_IDFI_CGI_DMEE_IT` | BAdI impl for IT-bank vendors | Y_IDFI_CGI_DMEE_COUNTRIES_IT ENHO + class extracted from P01 (P01_ONLY) |
| `YCL_IDFI_CGI_DMEE_UTIL` | PPC customizing dispatcher (called by FR class CM002) | YCL_IDFI_CGI_DMEE_FR====CM002 calls UTIL->get_tag_value_from_custo |

## ACTIVE/CONDITIONAL — SAP-std country dispatcher classes (55)

| Class | Role | Evidence |
|---|---|---|
| `CL_IDFI_CGI_CALL05_GENERIC_CM003` | Country dispatcher for GENERIC_CM003 (fires only if vendor bank in GENERIC_CM003) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_DE_CCDEF` | Country dispatcher for DE_CCDEF (fires only if vendor bank in DE_CCDEF) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FR_CI` | Country dispatcher for FR_CI (fires only if vendor bank in FR_CI) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_DE_CO` | Country dispatcher for DE_CO (fires only if vendor bank in DE_CO) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FACTORY_CI` | Country dispatcher for FACTORY_CI (fires only if vendor bank in FACTORY_CI) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CCIMP` | Country dispatcher for GENERIC_CCIMP (fires only if vendor bank in GENERIC_CCIMP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FACTORY_CCMAC` | Country dispatcher for FACTORY_CCMAC (fires only if vendor bank in FACTORY_CCMAC) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CCMAC` | Country dispatcher for GENERIC_CCMAC (fires only if vendor bank in GENERIC_CCMAC) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CO` | Country dispatcher for GENERIC_CO (fires only if vendor bank in GENERIC_CO) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FR_CU` | Country dispatcher for FR_CU (fires only if vendor bank in FR_CU) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_IT_CO` | Country dispatcher for IT_CO (fires only if vendor bank in IT_CO) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CP` | Country dispatcher for GENERIC_CP (fires only if vendor bank in GENERIC_CP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FACTORY_CM001` | Country dispatcher for FACTORY_CM001 (fires only if vendor bank in FACTORY_CM001) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_IT_CCDEF` | Country dispatcher for IT_CCDEF (fires only if vendor bank in IT_CCDEF) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GB_CI` | Country dispatcher for GB_CI (fires only if vendor bank in GB_CI) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_DE_CCMAC` | Country dispatcher for DE_CCMAC (fires only if vendor bank in DE_CCMAC) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GB_CU` | Country dispatcher for GB_CU (fires only if vendor bank in GB_CU) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_DE_CI` | Country dispatcher for DE_CI (fires only if vendor bank in DE_CI) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CU` | Country dispatcher for GENERIC_CU (fires only if vendor bank in GENERIC_CU) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_IT_CP` | Country dispatcher for IT_CP (fires only if vendor bank in IT_CP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_DE_CU` | Country dispatcher for DE_CU (fires only if vendor bank in DE_CU) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CM008` | Country dispatcher for GENERIC_CM008 (fires only if vendor bank in GENERIC_CM008) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_DE_CP` | Country dispatcher for DE_CP (fires only if vendor bank in DE_CP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_IT_CI` | Country dispatcher for IT_CI (fires only if vendor bank in IT_CI) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CCDEF` | Country dispatcher for GENERIC_CCDEF (fires only if vendor bank in GENERIC_CCDEF) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GB_CCMAC` | Country dispatcher for GB_CCMAC (fires only if vendor bank in GB_CCMAC) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GB_CP` | Country dispatcher for GB_CP (fires only if vendor bank in GB_CP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CM007` | Country dispatcher for GENERIC_CM007 (fires only if vendor bank in GENERIC_CM007) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FACTORY_CCIMP` | Country dispatcher for FACTORY_CCIMP (fires only if vendor bank in FACTORY_CCIMP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FR_CM001` | Country dispatcher for FR_CM001 (fires only if vendor bank in FR_CM001) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CM002` | Country dispatcher for GENERIC_CM002 (fires only if vendor bank in GENERIC_CM002) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GB_CM001` | Country dispatcher for GB_CM001 (fires only if vendor bank in GB_CM001) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FACTORY_CU` | Country dispatcher for FACTORY_CU (fires only if vendor bank in FACTORY_CU) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_IT_CCMAC` | Country dispatcher for IT_CCMAC (fires only if vendor bank in IT_CCMAC) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CM004` | Country dispatcher for GENERIC_CM004 (fires only if vendor bank in GENERIC_CM004) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_IT_CM001` | Country dispatcher for IT_CM001 (fires only if vendor bank in IT_CM001) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_IT_CU` | Country dispatcher for IT_CU (fires only if vendor bank in IT_CU) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GB_CCDEF` | Country dispatcher for GB_CCDEF (fires only if vendor bank in GB_CCDEF) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FACTORY_CP` | Country dispatcher for FACTORY_CP (fires only if vendor bank in FACTORY_CP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CM005` | Country dispatcher for GENERIC_CM005 (fires only if vendor bank in GENERIC_CM005) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FACTORY_CO` | Country dispatcher for FACTORY_CO (fires only if vendor bank in FACTORY_CO) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FACTORY_CCDEF` | Country dispatcher for FACTORY_CCDEF (fires only if vendor bank in FACTORY_CCDEF) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FR_CCIMP` | Country dispatcher for FR_CCIMP (fires only if vendor bank in FR_CCIMP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CM006` | Country dispatcher for GENERIC_CM006 (fires only if vendor bank in GENERIC_CM006) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_DE_CM001` | Country dispatcher for DE_CM001 (fires only if vendor bank in DE_CM001) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FR_CP` | Country dispatcher for FR_CP (fires only if vendor bank in FR_CP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_DE_CCIMP` | Country dispatcher for DE_CCIMP (fires only if vendor bank in DE_CCIMP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GB_CCIMP` | Country dispatcher for GB_CCIMP (fires only if vendor bank in GB_CCIMP) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CM001` | Country dispatcher for GENERIC_CM001 (fires only if vendor bank in GENERIC_CM001) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FR_CCDEF` | Country dispatcher for FR_CCDEF (fires only if vendor bank in FR_CCDEF) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GB_CO` | Country dispatcher for GB_CO (fires only if vendor bank in GB_CO) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FR_CO` | Country dispatcher for FR_CO (fires only if vendor bank in FR_CO) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_GENERIC_CI` | Country dispatcher for GENERIC_CI (fires only if vendor bank in GENERIC_CI) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_FR_CCMAC` | Country dispatcher for FR_CCMAC (fires only if vendor bank in FR_CCMAC) | Conditionally active — depends on actual vendor traffic to that country |
| `CL_IDFI_CGI_CALL05_IT_CCIMP` | Country dispatcher for IT_CCIMP (fires only if vendor bank in IT_CCIMP) | Conditionally active — depends on actual vendor traffic to that country |

## NEEDS VERIFY — possibly dead FMs (2)

| FM | Verdict | Evidence |
|---|---|---|
| `/CITIPMW/V3_GET_BANKCODE` | NEEDS_VERIFY (may be SAP-std utility called indirectly, OR may be dead) | Not in TFPM042FB Event 05 nor MP_EXIT_FUNC for our 4 trees — UNCONFIRMED ACTIVE |
| `/CITIPMW/LPMWV3U31` | NEEDS_VERIFY (may be SAP-std utility called indirectly, OR may be dead) | Not in TFPM042FB Event 05 nor MP_EXIT_FUNC for our 4 trees — UNCONFIRMED ACTIVE |

## OPEN QUESTIONS

- **/CGI_XML_CT_UNESCO_BK** — Third CGI tree variant found in TFPM042FB but not in our 4-tree scope. Active or test?
- **YCL_IDFI_CGI_DMEE_FR====CM001 in D01** — D01 has CM001 method that P01 does not. P01 has CM002 instead. Method-level swap.
- **Z_DMEE_EXIT_TAX_NUMBER** — D01-only since 2019, no P01 evidence — dead?
- **CL_IDFI_CGI_CALL05_<country> for non-FR/DE/IT/GB countries** — 28 country dispatchers extracted. Only some get exercised by actual UNESCO traffic. Process mining can quantify which countries actually have vendor payments via CGI tree.
