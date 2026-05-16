# DMEE `/SEPA_CT_UNES` V001 — Tabla comparativa de mapping

Sample run: D01 LAUFD=20260507 LAUFI=10001B vendor 0010008305 (Simona BERTOLDINI)
UNES paying co address (T001/ADRC): Place de Fontenoy 7, 75007 PARIS, FR
Vendor 0010008305 address (ADRC): Place de Fontenoy 7, 75007 PARIS, FR

## Leyenda
- **Tree mapping**: `MP_SC_TAB-MP_SC_FLD` configurado en DMEE_TREE_NODE
- **Tree exit**: `MP_EXIT_FUNC` (FM que el motor llama para computar el value)
- **CGI BAdI post-process**: lo que `YCL_IDFI_CGI_DMEE_FALLBACK_CM001->GET_CREDIT` hace AL c_value DESPUÉS de que el árbol lo populó
- **Y_FI_DMEE_ADR (propuesta)**: lo que devolvería si lo migráramos al FM unificado


## Dbtr

| Nodo | Tree mapping | Tree exit | CGI BAdI post-process | Sample actual | Y_FI_DMEE_ADR (propuesta) | Estado |
|---|---|---|---|---|---|---|
| `Dbtr` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `Nm` | `FPAYHX-NAMEZ` | `—` | (no redefinition — passthrough) | `` | `ADRC-NAME1 = 'UNESCO'` | ✅ |
| `PstlAdr` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `AdrLine` | `FPAYHX-ORT1Z` | `—` | (no redefinition — passthrough) | `` | `` | ✅ |
| `BldgNb` | `—` | `Y_FI_DMEE_ADR` | (no redefinition — passthrough) | `7` | `ADRC-HOUSE_NUM1 = '7'` | ✅ |
| `Ctry` | `—` | `Y_FI_DMEE_ADR` | (no redefinition — passthrough) | `` | `ADRC-COUNTRY = 'FR'` | ❌ FM no maneja |
| `CtrySubDvsn` | `—` | `Y_FI_DMEE_ADR` | (no redefinition — passthrough) | `` | `ADRC-REGION = ''` | ❌ FM no maneja |
| `Dept` | `—` | `Y_FI_DMEE_ADR` | (no redefinition — passthrough) | `` | `` | ❌ FM no maneja |
| `PstCd` | `—` | `Y_FI_DMEE_ADR` | (no redefinition — passthrough) | `75007` | `ADRC-POST_CODE1 = '75007'` | ✅ |
| `StrtNm` | `—` | `Y_FI_DMEE_ADR` | (no redefinition — passthrough) | `Place de Fontenoy` | `ADRC-STREET = 'Place de Fontenoy'` | ✅ |
| `SubDept` | `—` | `Y_FI_DMEE_ADR` | (no redefinition — passthrough) | `` | `` | ❌ FM no maneja |
| `TwnNm` | `—` | `Y_FI_DMEE_ADR` | (no redefinition — passthrough) | `PARIS` | `ADRC-CITY1 = 'PARIS'` | ✅ |

## DbtrAgt

| Nodo | Tree mapping | Tree exit | CGI BAdI post-process | Sample actual | Y_FI_DMEE_ADR (propuesta) | Estado |
|---|---|---|---|---|---|---|
| `DbtrAgt` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `FinInstnId` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `BIC` | `FPAYHX-USWIF` | `—` | (no redefinition — passthrough) | `` | `` | ✅ |

## DbtrAcct

| Nodo | Tree mapping | Tree exit | CGI BAdI post-process | Sample actual | Y_FI_DMEE_ADR (propuesta) | Estado |
|---|---|---|---|---|---|---|
| `DbtrAcct` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `Ccy` | `FPAYHX-UBWAE` | `—` | (no redefinition — passthrough) | `` | `` | ✅ |
| `Id` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `IBAN` | `FPAYHX-UIBAN` | `—` | (no redefinition — passthrough) | `` | `` | ✅ |

## Cdtr

| Nodo | Tree mapping | Tree exit | CGI BAdI post-process | Sample actual | Y_FI_DMEE_ADR (propuesta) | Estado |
|---|---|---|---|---|---|---|
| `Cdtr` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `Nm` | `—` | `—` | if item.origin=TR-CM-BT → c_value=fpayp-sgtxt; truncate to 3 | `` | `ADRC-NAME1 = 'Simona BERTOLDINI'` | ❌ FALTA |
| `PstlAdr` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `AdrLine` | `FPAYHX-ZPFST` | `—` | (no redefinition — passthrough) | `` | `` | ✅ |
| `AdrLine` | `FPAYHX-ZPLOR` | `—` | (no redefinition — passthrough) | `` | `` | ✅ |
| `BldgNb` | `FPAYP-REF01` | `—` | (no redefinition — passthrough) | `` | `ADRC-HOUSE_NUM1 = '7'` | ✅ |
| `Ctry` | `FPAYHX-ZLISO` | `—` | (no redefinition — passthrough) | `` | `ADRC-COUNTRY = 'FR'` | ✅ |
| `PstCd` | `FPAYH-ZPSTL` | `—` | (no redefinition — passthrough) | `75007` | `ADRC-POST_CODE1 = '75007'` | ✅ |
| `StrtNm` | `FPAYH-ZSTRA` | `—` | prepend mv_cdtr_name+35 (name overflow) if same fpayh; trunc | `BFM/FAS/PAY` | `ADRC-STREET = 'Place de Fontenoy'` | ❌ WRONG (BFM/FAS/PAY) |
| `TwnNm` | `FPAYH-ZORT1` | `—` | (no redefinition — passthrough) | `Paris` | `ADRC-CITY1 = 'PARIS'` | ✅ |

## CdtrAgt

| Nodo | Tree mapping | Tree exit | CGI BAdI post-process | Sample actual | Y_FI_DMEE_ADR (propuesta) | Estado |
|---|---|---|---|---|---|---|
| `CdtrAgt` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `FinInstnId` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `BIC` | `FPAYH-ZSWIF` | `—` | (no redefinition — passthrough) | `INGBFR21` | `` | ✅ |

## CdtrAcct

| Nodo | Tree mapping | Tree exit | CGI BAdI post-process | Sample actual | Y_FI_DMEE_ADR (propuesta) | Estado |
|---|---|---|---|---|---|---|
| `CdtrAcct` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `Id` | `—` | `—` | (no redefinition — passthrough) | `` | `` | ❌ FALTA |
| `IBAN` | `FPAYH-ZIBAN` | `—` | (no redefinition — passthrough) | `FR7630438001004000018993262` | `` | ✅ |