# Definitive HBKID × Tree mapping — CONFIG-derived (no inference)
**Generated**: from P01 Gold DB JOIN REGUH_FAST × T001 × T042Z

## Method

For each F110 payment in REGUH_FAST:
1. Lookup paying co code country: `T001.BUKRS = REGUH.ZBUKR → T001.LAND1`
2. Lookup actual payment method: `REGUH.RZAWE`
3. Config lookup: `T042Z WHERE LAND1=co_country AND ZLSCH=RZAWE → FORMI`
4. FORMI = the actual DMEE tree used at runtime

## Tree usage (REAL config-derived)

| Tree (FORMI) | Payments | Total amount | In scope? |
|---|---|---|---|
| `/SEPA_CT_UNES` | 175,904 | 1,098,596,861 | 🎯 IN SCOPE |
| `NO_T042Z_MATCH` | 166,022 | 9,197,570,548 | ❓ unmapped |
| `/CITI/XML/UNESCO/DC_V3_01` | 84,772 | 2,333,534,442 | 🎯 IN SCOPE |
| `/CGI_XML_CT_UNESCO` | 76,161 | 1,237,274,634 | 🎯 IN SCOPE |
| `` | 51,004 | 646,389,254,291 | ⚪ Out of scope |
| `/SEPA_CT_ICTP_ISO` | 11,192 | 128,105,955 | ⚪ Out of scope |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA` | 2,000 | 3,901,014 | ⚪ Out of scope |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA_I` | 4 | 7,774 | ⚪ Out of scope |

## HBKID × Tree (CONFIG-derived) — top 15 HBKIDs

| HBKID | Tree | Payments |
|---|---|---|
| SOG01 | `/SEPA_CT_UNES` 🎯 | 167,407 |
| SOG01 | `/CGI_XML_CT_UNESCO` 🎯 | 70,539 |
| SOG01 | ``  | 48,123 |
| SOG01 | `NO_T042Z_MATCH`  | 8,355 |
|  | `NO_T042Z_MATCH`  | 157,316 |
| CIT01 | `/CITI/XML/UNESCO/DC_V3_01` 🎯 | 45,799 |
| CIT01 | ``  | 6 |
| CIT04 | `/CITI/XML/UNESCO/DC_V3_01` 🎯 | 36,414 |
| CIT04 | `NO_T042Z_MATCH`  | 218 |
| UNI01 | `/SEPA_CT_ICTP_ISO`  | 11,192 |
| UNI01 | `/SEPA_CT_ICTP_ISO_EXTRASEPA`  | 2,000 |
| UNI01 | ``  | 394 |
| UNI01 | `/SEPA_CT_ICTP_ISO_EXTRASEPA_I`  | 4 |
| SOG03 | `/CGI_XML_CT_UNESCO` 🎯 | 5,007 |
| SOG03 | `NO_T042Z_MATCH`  | 108 |
| SOG05 | `/SEPA_CT_UNES` 🎯 | 4,728 |
| SOG05 | `/CGI_XML_CT_UNESCO` 🎯 | 386 |
| SOG02 | `/SEPA_CT_UNES` 🎯 | 3,769 |
| SOG02 | `/CGI_XML_CT_UNESCO` 🎯 | 68 |
| CIT21 | `/CITI/XML/UNESCO/DC_V3_01` 🎯 | 2,559 |
| CIT21 | `NO_T042Z_MATCH`  | 25 |
| BRA01 | ``  | 792 |
| AIB01 | ``  | 335 |
| BTE01 | ``  | 324 |
| ECO02 | ``  | 138 |
| BMN01 | ``  | 105 |
| CIT07 | ``  | 95 |

## Per-year breakdown (HBKID × Tree × Year)

### Total payments per HBKID per year

| HBKID | 2025 | 2026 |
|---|---|---|
| SOG01 | 228,648 | 65,776 |
|  | 117,906 | 39,410 |
| CIT01 | 34,683 | 11,122 |
| CIT04 | 28,329 | 8,303 |
| UNI01 | 10,261 | 3,329 |
| SOG03 | 3,995 | 1,120 |
| SOG05 | 4,137 | 977 |
| SOG02 | 3,039 | 798 |
| CIT21 | 1,977 | 607 |
| BRA01 | 564 | 228 |
| AIB01 | 287 | 48 |
| BTE01 | 292 | 32 |
| ECO02 | 118 | 20 |
| BMN01 | 84 | 21 |
| CIT07 | 74 | 21 |

### Top (HBKID, Tree) × Year (in-scope only)

| HBKID | Tree | 2025 | 2026 | Total |
|---|---|---|---|---|
| SOG01 | `/SEPA_CT_UNES` | 129,722 | 37,685 | **167,407** |
| SOG01 | `/CGI_XML_CT_UNESCO` | 54,998 | 15,541 | **70,539** |
| CIT01 | `/CITI/XML/UNESCO/DC_V3_01` | 34,677 | 11,122 | **45,799** |
| CIT04 | `/CITI/XML/UNESCO/DC_V3_01` | 28,139 | 8,275 | **36,414** |
| SOG03 | `/CGI_XML_CT_UNESCO` | 3,893 | 1,114 | **5,007** |
| SOG05 | `/SEPA_CT_UNES` | 3,783 | 945 | **4,728** |
| SOG02 | `/SEPA_CT_UNES` | 2,976 | 793 | **3,769** |
| CIT21 | `/CITI/XML/UNESCO/DC_V3_01` | 1,954 | 605 | **2,559** |
| SOG05 | `/CGI_XML_CT_UNESCO` | 354 | 32 | **386** |
| SCB14 | `/CGI_XML_CT_UNESCO` | 56 | 20 | **76** |
| CIC01 | `/CGI_XML_CT_UNESCO` | 52 | 21 | **73** |
| SOG02 | `/CGI_XML_CT_UNESCO` | 63 | 5 | **68** |
| CRA01 | `/CGI_XML_CT_UNESCO` | 7 | 4 | **11** |
| BNP01 | `/CGI_XML_CT_UNESCO` | 0 | 1 | **1** |

## Test matrix (CONFIG-derived priorities)

Tier 1 (mandatory: combinations >1000 payments routing to in-scope trees):

| # | HBKID | Tree | Volume |
|---|---|---|---|
| T01 | SOG01 | `/SEPA_CT_UNES` | 167,407 |
| T02 | SOG01 | `/CGI_XML_CT_UNESCO` | 70,539 |
| T03 | CIT01 | `/CITI/XML/UNESCO/DC_V3_01` | 45,799 |
| T04 | CIT04 | `/CITI/XML/UNESCO/DC_V3_01` | 36,414 |
| T05 | SOG03 | `/CGI_XML_CT_UNESCO` | 5,007 |
| T06 | SOG05 | `/SEPA_CT_UNES` | 4,728 |
| T07 | SOG02 | `/SEPA_CT_UNES` | 3,769 |
| T08 | CIT21 | `/CITI/XML/UNESCO/DC_V3_01` | 2,559 |
