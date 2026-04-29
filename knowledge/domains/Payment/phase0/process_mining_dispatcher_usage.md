# Process Mining: Country Dispatcher Usage Frequency
**Generated**: from P01 Gold DB REGUH 942K payments

## Goal

Validate active vs dead inventory of `CL_IDFI_CGI_CALL05_<country>` SAP-std dispatcher classes with REAL production traffic. A dispatcher fires when a vendor's bank is in the matching country. Zero traffic = zero dispatcher exercise.

## Top 20 vendor bank countries by payment volume

| Rank | Bank country | Payments | Dispatcher exercised | Status |
|---|---|---|---|---|
| 1 | (empty) | 430,517 | `-` | Empty (no LFBK record — likely one-time vendor or domestic SEPA) |
| 2 | FR | 148,644 | `CL_IDFI_CGI_CALL05_FR` | EXTRACTED |
| 3 | BR | 72,240 | `(no SAP-std class for BR — falls through to GENERIC)` | GENERIC fallback |
| 4 | US | 37,888 | `CL_IDFI_CGI_CALL05_US` | EXTRACTED |
| 5 | IT | 22,035 | `CL_IDFI_CGI_CALL05_IT` | EXTRACTED |
| 6 | DE | 19,889 | `CL_IDFI_CGI_CALL05_DE` | EXTRACTED |
| 7 | UA | 10,754 | `(no SAP-std class for UA — falls through to GENERIC)` | GENERIC fallback |
| 8 | GB | 9,168 | `CL_IDFI_CGI_CALL05_GB` | EXTRACTED |
| 9 | LB | 7,480 | `(no SAP-std class for LB — falls through to GENERIC)` | GENERIC fallback |
| 10 | BE | 7,174 | `CL_IDFI_CGI_CALL05_BE` | EXTRACTED |
| 11 | ES | 6,781 | `CL_IDFI_CGI_CALL05_ES` | EXTRACTED |
| 12 | MG | 5,140 | `(no SAP-std class for MG — falls through to GENERIC)` | GENERIC fallback |
| 13 | CA | 4,642 | `CL_IDFI_CGI_CALL05_CA` | EXTRACTED |
| 14 | EG | 4,195 | `(no SAP-std class for EG — falls through to GENERIC)` | GENERIC fallback |
| 15 | ZW | 3,569 | `(no SAP-std class for ZW — falls through to GENERIC)` | GENERIC fallback |
| 16 | KE | 3,157 | `(no SAP-std class for KE — falls through to GENERIC)` | GENERIC fallback |
| 17 | ZA | 2,898 | `(no SAP-std class for ZA — falls through to GENERIC)` | GENERIC fallback |
| 18 | TN | 2,734 | `(no SAP-std class for TN — falls through to GENERIC)` | GENERIC fallback |
| 19 | BA | 2,718 | `(no SAP-std class for BA — falls through to GENERIC)` | GENERIC fallback |
| 20 | CO | 2,605 | `(no SAP-std class for CO — falls through to GENERIC)` | GENERIC fallback |

## Country dispatchers — extracted vs traffic

| Class | Country | Payments to vendors with bank in this country | Verdict |
|---|---|---|---|
| `CL_IDFI_CGI_CALL05_FR` | FR | 148,644 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_US` | US | 37,888 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_IT` | IT | 22,035 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_DE` | DE | 19,889 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_GB` | GB | 9,168 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_BE` | BE | 7,174 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_ES` | ES | 6,781 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_CA` | CA | 4,642 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_CH` | CH | 2,463 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_CN` | CN | 2,262 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_AU` | AU | 1,667 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_MX` | MX | 1,620 | 🔥 HIGH usage |
| `CL_IDFI_CGI_CALL05_PL` | PL | 931 | ✅ Active |
| `CL_IDFI_CGI_CALL05_DK` | DK | 871 | ✅ Active |
| `CL_IDFI_CGI_CALL05_PT` | PT | 857 | ✅ Active |
| `CL_IDFI_CGI_CALL05_AT` | AT | 545 | ✅ Active |
| `CL_IDFI_CGI_CALL05_SE` | SE | 416 | ✅ Active |
| `CL_IDFI_CGI_CALL05_LT` | LT | 377 | ✅ Active |
| `CL_IDFI_CGI_CALL05_BG` | BG | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_CZ` | CZ | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_EE` | EE | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_HK` | HK | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_HR` | HR | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_IE` | IE | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_LU` | LU | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_RO` | RO | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_SK` | SK | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |
| `CL_IDFI_CGI_CALL05_TW` | TW | 0 | 💀 ZERO traffic (extracted but never exercised — DEAD) |

## Tree usage frequency (proxy — vendor LAND1 + payment method)

| Tree | Estimated payment volume |
|---|---|
| `/SEPA_CT_ICTP_ISO` | 3,527 |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA` | 560 |

## Top 30 (paying_co × payment_method) combinations

| Co code | Pay method | Payments |
|---|---|---|
| UNES | None | 415,496 |
| UNES | CJLNOSU | 205,084 |
| UNES | CHIJLNOSU | 72,553 |
| UBO | BCDGHJPRT | 62,899 |
| UNES | CJLNOSUX | 39,479 |
| UNES | CHIJLNS | 19,770 |
| UIL | MNS | 10,461 |
| ICTP | K | 6,954 |
| UBO | CDHJMORT | 6,118 |
| UBO | DHJMOPT | 3,534 |
| ICTP | S | 3,527 |
| IIEP | JNS | 2,944 |
| IIEP | CHIJLNOSU | 2,716 |
| UNES | CHIJLNOS | 2,586 |
| ICTP | E | 1,693 |
| UBO | CDFHJMPT | 1,667 |
| UNES | CHIJLNOSUX | 1,572 |
| UBO | BCDFGHJMPT | 1,458 |
| UIS | 3CKNOU | 774 |
| ICTP | J | 560 |
| IIEP | JNOSU | 406 |
| UNES | AK | 388 |

## Top 30 vendor countries by payment volume

| Rank | Vendor LAND1 | Payments |
|---|---|---|
| 1 | (empty) | 415,496 |
| 2 | FR | 164,198 |
| 3 | BR | 77,688 |
| 4 | IT | 23,588 |
| 5 | DE | 18,121 |
| 6 | US | 12,565 |
| 7 | UA | 10,754 |
| 8 | LB | 8,069 |
| 9 | GB | 7,897 |
| 10 | ES | 7,556 |
| 11 | ZW | 6,978 |
| 12 | MG | 5,140 |
| 13 | SN | 5,128 |
| 14 | KE | 4,885 |
| 15 | CA | 4,642 |
| 16 | EG | 4,615 |
| 17 | BE | 4,342 |
| 18 | MM | 3,684 |
| 19 | ZA | 2,898 |
| 20 | TN | 2,734 |
| 21 | BA | 2,718 |
| 22 | UG | 2,668 |
| 23 | CO | 2,605 |
| 24 | IN | 2,590 |
| 25 | AR | 2,448 |
| 26 | CN | 2,262 |
| 27 | ET | 2,179 |
| 28 | MA | 1,845 |
| 29 | NL | 1,832 |
| 30 | CH | 1,766 |

## Conclusions

- **DE/IT class retrofit value**: quantified by counting payments where vendor bank country = DE / IT (above)
- **Dead country dispatcher candidates**: classes with 0 traffic — extracted but never exercised in P01
- **Test matrix priority**: top 80% of (co × pay_method × vendor_country) combinations cover the realistic scenarios for V001 testing
