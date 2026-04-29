# N_MENARD DMEE specs decoded — email 2026-04-29

**Source**: email DMEE.eml from `n.menard@unesco.org` 2026-04-29 12:00 UTC, 3 attachments

**Files saved**: `C:/tmp/dmee_attachments/`
- `TS DMEE CGI modifications 20240229.docx` (29/02/2024 — code in production today)
- `FS Payment Purpose code XML.docx` (01/03/2024 — functional spec PPC)
- `TS Payment Purpose code XML.docx` (18/03/2024 — technical spec PPC)

---

## Document 1 — TS DMEE CGI modifications (Pattern A confirmed as bank-mandated)

### Modification 1: Bank number `<MmbId>` clearing

**Tag**: `<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>`

**Issue**: SAP standard added the bank KEY (internal ID) when bank NUMBER was missing → bank rejected because key is meaningless to bank.

**Fix**: clear value if no bank number — leave empty.

**Implementation**: Country classes `YCL_IDFI_CGI_DMEE_DE / IT` (and FR via FALLBACK) override the node and CLEAR if `i_fpayh-zbnkl IS INITIAL`.

### Modification 2: Beneficiary name overflow → StrtNm (Pattern A — BANK-MANDATED)

**Tags**:
- `<PmtInf><CdtTrfTxInf><Cdtr><Nm>` (35 chars max)
- `<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>` (overflow goes here)

**Logic**:
- Vendor `Name1` (40 chars) + `Name2` (40 chars) → up to 80 chars total
- `<Nm>` keeps first 35 of Name1
- `<StrtNm>` prepends positions 36-40 of Name1 + Name2 (1-40) IF NOT EMPTY
- Then real street follows

**Bank source**: Société Générale request, documented after multiple discussions. N_MENARD explicit quote:
> "I don't think that this is a very 'clean' solution but we asked confirmation by giving examples and they insist."

**Class**: `YCL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT` (called via extension point at end of SAP-std `CL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT`).

### → Q1 RESOLVED for our project

| Option | Verdict |
|---|---|
| **A1 — Remove logic entirely** | ❌ NOT ACCEPTABLE — bank-mandated, would break SocGen production |
| **A2 — Guard with `c_value IS INITIAL` check for V001** | ✅ CORRECT — preserves V000 behavior, ensures V001 structured StrtNm not corrupted |

Pattern A2 is the only valid path. Update plan + companion accordingly.

---

## Document 2 + 3 — Payment Purpose Code (PPC) for /CGI_XML_CT_UNESCO

### Background

USD payments via Société Générale require PPC for many countries. Without PPC → bank rejection.

### 9 countries with PPC requirements

| LAND1 | Country | Tag location | Example |
|---|---|---|---|
| AE | UAE | `<InstrForCdtrAgt><InstrInf>` | `/REC/FIS` |
| BH | Bahrein | `<RmtInf><Ustrd>` | `/STR/Travel` |
| CN | China | `<InstrForCdtrAgt><InstrInf>` | `/REC/CSTRDR` |
| ID | Indonesia | `<RmtInf><Ustrd>` | `/PURP/2490/Consulting 03 04` |
| IN | India | `<RmtInf><Ustrd>` | `P0301;Purchases towards travel;INV;6523486 Jones` |
| JO | Jordan | `<RmtInf><Ustrd>` | `/PURP/801/Consulting 03 04` |
| MA | Morocco | `<RmtInf><Ustrd>` | `/PURP/510/Consulting 03 04` |
| MY | Malaysia | `<RmtInf><Ustrd>` | `/PURP/16510/Consulting 03 04` |
| PH | Philippines | `<RmtInf><Ustrd>` | `/PURP/SUPP/Consulting 03 04` |

### Payment type detection (REGUP-LAUF1 suffix)

| Suffix | Type |
|---|---|
| `+++++R` | Replenishment / payment request |
| `+++++P` | Payroll |
| Other | Third-party payment |

### Tables (production-active in both P01 and D01)

#### YTFI_PPC_TAG — 11 rows

Routes (LAND1, TAG_ID) → XML tag location:

| LAND1 | TAG_ID | DEB_CRE | TAG_FULL |
|---|---|---|---|
| AE | -INSTRINF | C | `<PmtInf><CdtTrfTxInf><-InstrForCdtrAgt>` (negative = clear) |
| AE | INSTRINF | C | `<PmtInf><CdtTrfTxInf><InstrForCdtrAgt><InstrInf>` |
| BH | USTRD | C | `<PmtInf><CdtTrfTxInf><RmtInf><Ustrd>` |
| CN | -INSTRINF | C | (negative tag) |
| CN | INSTRINF | C | `<PmtInf><CdtTrfTxInf><InstrForCdtrAgt><InstrInf>` |
| ID | USTRD | C | `<PmtInf><CdtTrfTxInf><RmtInf><Ustrd>` |
| IN | USTRD | C | idem |
| JO | USTRD | C | idem |
| MA | USTRD | C | idem |
| MY | USTRD | C | idem |
| PH | USTRD | C | idem |

#### YTFI_PPC_STRUC — 133 rows

Builds tag value via positional building blocks. Per (LAND1, TAG_ID, PAY_TYPE, CODE_ORD):

| Domain YD_FI_PPC_CODE value | Meaning |
|---|---|
| `SEPARATOR` | Literal separator like `/` |
| `FIXED_VAL` | Fixed string (e.g., REC, SAL) |
| `PPC_VAR` | Variable PPC from T015L.LZBKZ |
| `PPC_DESCR` | PPC description from T015L.ZWCK1 |
| `PAY_FIELD` | Field from FPAY structure (e.g., REGUH-XBLNR) |

**Sample for AE**:

```
PAY_TYPE=O (third-party):
  ORD=01: SEPARATOR /
  ORD=02: FIXED_VAL REC
  ORD=03: SEPARATOR /
  ORD=04: PPC_VAR  (vendor's SCB indicator)
  → Output: /REC/<PPC>     (e.g., /REC/FIS)

PAY_TYPE=P (payroll):
  ORD=01-04: / REC / SAL
  → Output: /REC/SAL (fixed)

PAY_TYPE=R (replenishment):
  ORD=01-04: / REC / IGT
  → Output: /REC/IGT (fixed)
```

### PPC structure rows per country

| LAND1 | Rows |
|---|---|
| IN | 21 |
| ID | 18 |
| JO | 18 |
| MA | 18 |
| AE | 13 |
| CN | 13 |
| MY | 12 |
| PH | 12 |
| BH | 8 |

### Source PPC in vendor invoice

- **Field**: `T015L.LZBKZ` (SCB Indicator) — entered by user on invoice
- **Description**: `T015L.ZWCK1` (first chars before space = code, rest = description)
- **Validation**: rule forces user to fill PPC for AE/BH/CN/ID/IN/JO/MA/MY/PH vendors

### Code chain (production-active)

```
F110 traversal of /CGI_XML_CT_UNESCO
  ↓ at each node, BAdI FI_CGI_DMEE_EXIT_W_BADI fires
  ↓ filter on flt_val_country
  ↓ for FR co code:
     ↓ YCL_IDFI_CGI_DMEE_FR_CM002 (P01-only — RETROFIT NEEDED)
       ↓ NEW ycl_idfi_cgi_dmee_util( )
       ↓ lo_cgi_util->get_tag_value_from_custo(
           iv_land1=i_fpayh-zbnks,    "vendor's bank country
           iv_deb_cre=flt_val_debit_or_credit,
           iv_tag_full=i_node_path,
           is_fpayh, is_fpayhx, is_fpayp )
         ↓ YCL_IDFI_CGI_DMEE_UTIL_CM003.get_tag_value_from_custo
            ↓ READ T015L for SCB indicator
            ↓ LOOP YTFI_PPC_STRUC WHERE land1+pay_type+tag_full match
            ↓ Build cv_value_c via positional concat
            ↓ RETURN populated o_value
       ↓ DMEE writes o_value into <InstrForCdtrAgt><InstrInf> or <RmtInf><Ustrd>
```

---

## Critical implications for our V001 project

### 1. Pattern A fix path is CONFIRMED (Q1 resolved)

**Use Option A2 (guard with IS INITIAL check) for V001**. The overflow logic is bank-required for V000 production. Pattern A fix:

```abap
WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'.
  IF i_fpayh = mv_fpayh
     AND mv_cdtr_name+35 IS NOT INITIAL
     AND c_value IS INITIAL.                   "← V001 guard: only prepend if StrtNm empty
    c_value = mv_cdtr_name+35.
  ELSEIF i_fpayh = mv_fpayh
     AND mv_cdtr_name+35 IS NOT INITIAL.
    c_value = |{ mv_cdtr_name+35 } { c_value }|.   "V000 legacy preserved
  ENDIF.
  IF c_value+70 IS NOT INITIAL.
    CLEAR c_value+70.
  ENDIF.
```

### 2. PPC integration must be PRESERVED in V001

The CGI tree V001 changes (CdtrAgt structured nodes) must NOT break:
- `<InstrForCdtrAgt><InstrInf>` (used by AE/CN PPC)
- `<RmtInf><Ustrd>` (used by BH/ID/IN/JO/MA/MY/PH PPC)

**Test matrix MUST include** payments to vendors with banks in these 9 countries to verify PPC tags survive V001 changes:

| Test ID | LAND1 vendor bank | Pay type | Expected PPC tag content |
|---|---|---|---|
| PPC-T01 | AE | O | `/REC/<vendor.LZBKZ.PPC>` in `<InstrInf>` |
| PPC-T02 | BH | O | `/STR/<description>` in `<Ustrd>` |
| PPC-T03 | CN | O | `/REC/<PPC>` in `<InstrInf>` |
| PPC-T04 | ID | O | `/PURP/<PPC>/<description>` in `<Ustrd>` |
| PPC-T05 | IN | O | `<PPC>;<desc>;INV;<XBLNR>` in `<Ustrd>` |
| PPC-T06 | JO | O | `/PURP/<PPC>/<description>` in `<Ustrd>` |
| PPC-T07 | MA | O | idem |
| PPC-T08 | MY | O | idem |
| PPC-T09 | PH | O | idem |
| PPC-T10 | AE/CN/IN | P | Fixed payroll PPC (SAL or country-specific) |
| PPC-T11 | AE/CN/IN | R | Fixed replenishment PPC (IGT or country-specific) |

### 3. Q1bis RESOLVED: FR class CM001/CM002 swap explained

The "method swap" between D01 (CM001) and P01 (CM002) is NOT a swap — it's the **PPC integration that was added to P01 in 2024 but never came back to D01**:

- D01's `YCL_IDFI_CGI_DMEE_FR====CM001` = older method (pre-PPC, possibly empty or different logic)
- P01's `YCL_IDFI_CGI_DMEE_FR====CM002` = the PPC dispatcher (calls UTIL->get_tag_value_from_custo)

**Retrofit decision**: bring P01's CM002 to D01 (replacing CM001 if needed). Decision **(a)** of Q1bis — align D01 to P01 — is correct.

### 4. Updated retrofit transport scope

`D01-RETROFIT-01` now has clearer rationale:

| Object | Why |
|---|---|
| YCL_IDFI_CGI_DMEE_DE | Bank `<MmbId>` clearing for German vendors |
| YCL_IDFI_CGI_DMEE_IT | Bank `<MmbId>` clearing for Italian vendors |
| YCL_IDFI_CGI_DMEE_FR_CM002 | PPC dispatcher for FR (replaces D01's older CM001) |
| Y_IDFI_CGI_DMEE_COUNTRIES_DE/FR/IT (3 ENHO) | BAdI wire-up to dispatch the country classes |

### 5. Custom development map (updated)

CGI tree has TWO custom development streams from N_MENARD:

| Stream | Scope | Status | Touched in V001? |
|---|---|---|---|
| **Stream A: Pattern A overflow** (Doc 1, 29/02/2024) | Bank `<MmbId>` clearing + Name overflow → StrtNm | Production-active P01 + D01 (FALLBACK identical) | YES — Pattern A2 guard for V001 |
| **Stream B: PPC infrastructure** (Doc 2+3, 01-18/03/2024) | 9-country PPC tags via YTFI_PPC_* tables + UTIL/CM003 + FR/CM002 dispatcher | Production-active P01 only (D01 missing FR/CM002 entry) | NO direct change — must PRESERVE |

---

## Cross-reference

- Brain claim 96 (Pattern A bank-mandated)
- Brain claim 97 (PPC infrastructure decoded)
- Source: `C:/tmp/dmee_attachments/` (3 docx)
- Tables in Gold DB: YTFI_PPC_TAG (11) + YTFI_PPC_STRUC (133) + T015L
- Code references: `extracted_code/FI/DMEE/YCL_IDFI_CGI_DMEE_UTIL_CM003.abap`, `extracted_code/FI/DMEE_p01_canonical/YCL_IDFI_CGI_DMEE_FR==========CM002.abap`
- N_MENARD questions: Q1 RESOLVED (A2), Q1bis RESOLVED (align D01 to P01 = retrofit FR/CM002)
