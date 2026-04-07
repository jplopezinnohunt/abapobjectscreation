# House Bank Configuration Report: UBA01 — UNESCO Maputo (Mozambique)

**Report Date:** 2026-04-07  
**Last Updated:** 2026-04-07 (after compliance fixes)  
**Ticket:** INC-000005586  
**Requestor:** Anssi Yli-Hietanen (TRS), validated by Baizid Gazi  
**Configurator:** Pablo Lopez (DBS)  
**Bank:** United Bank for Africa Mozambique S.A. (UBA)  
**Reference Bank:** ECO09 (Ecobank Maputo — same city, same dual-currency pattern)  
**Compliance Score (D01):** 29 PASS / 1 FAIL / 2 WARN  

---

## 1. Request Summary

### Source Documents
| Document | Content |
|----------|---------|
| Email (2026-03-31) | Request to create house bank UBA01 with USD01/MZN01 in UNES |
| UNESCO DETALHES BANCARIOS.PDF | Bank confirmation letter from UBA (2026-03-13) |
| UBA01-USD01.xls | House bank form for USD account |
| UBA01-MZN01.xls | House bank form for MZN account |
| Form AM3-11 - 1065421 | G/L creation form (bank USD) |
| Form AM3-11 - 1165421 | G/L creation form (sub-bank USD) |
| Form AM3-11 - 1065424 | G/L creation form (bank MZN) |
| Form AM3-11 - 1165424 | G/L creation form (sub-bank MZN) |

### Requested Configuration
| Field | USD Account | MZN Account |
|-------|------------|------------|
| House Bank ID | UBA01 | UBA01 |
| Account ID | USD01 | MZN01 |
| Description | UNESCO MAPUTO - USD | UNESCO MAPUTO - MZN |
| Bank Account Number | 070340000190 | 070040004663 |
| IBAN | MZ59004206077034000019028 | MZ59004206077004000466345 |
| Currency | USD | MZN |
| G/L Account (bank) | 1065421 | 1065424 |
| G/L Account (sub-bank) | 1165421 | 1165424 |
| G/L Reference (bank) | 1094421 (ECO09) | 1094424 (ECO09) |
| G/L Reference (sub-bank) | 1194421 (ECO09) | 1194424 (ECO09) |
| Bank Country | MZ | MZ |
| Bank Key | SP0000001YCB | SP0000001YCB |
| SWIFT | UNAFMZMA | UNAFMZMA |
| Replenishment | Yes (G/L 1165421, USD) | No |
| Electronic Bank Statement | Yes | Yes |
| Business Area | GEF | GEF |

---

## 2. Configuration Steps — Status per System

### STEP 1: G/L Account Creation (FS00)

**Responsibility:** MD Team creates in PRD, copies to D01/V01.

| Account | Type | Description | D01 | P01 | Issues |
|---------|------|-------------|-----|-----|--------|
| 1065421 | Bank (10*) | BK UBA MOZAMBIQUE - UNESCO MAPUTO USD | PASS | FAIL | P01: HBKID=ECO09 (wrong) |
| 1165421 | Sub-bank (11*) | S-BK UBA MOZAMBIQUE - UNESCO MAPUTO USD | PASS | FAIL | P01: HBKID=ECO09 (wrong) |
| 1065424 | Bank (10*) | BK UBA MOZAMBIQUE - UNESCO MAPUTO MZN | PASS | FAIL | P01: HBKID=ECO09 (wrong) |
| 1165424 | Sub-bank (11*) | S-BK UBA MOZAMBIQUE - UNESCO MAPUTO MZN | PASS | FAIL | P01: HBKID=ECO09 (wrong) |

**D01 field-level validation (all 4 accounts):**

| Field | Expected (bank 10*) | Expected (sub-bank 11*) | D01 Status |
|-------|--------------------|-----------------------|------------|
| KTOKS (Account Group) | BANK | BANK | PASS |
| XBILK (Balance Sheet) | X | X | PASS |
| FDLEV (Planning Level) | B0 | B1 | PASS |
| FSTAG (Field Status) | UN03 | UN03 | PASS |
| ZUAWA (Sort Key) | 027 | Z01 | PASS |
| XKRES (Line Item Display) | X | X | PASS |
| XGKON (Cash Flow Relevant) | X | X | PASS |
| XINTB (Post Auto Only) | X | X | PASS |
| XOPVW (Open Item Mgmt) | — | X | PASS |
| FIPOS (Commitment Item) | BANK | BANK | PASS |
| HBKID (House Bank) | UBA01 | UBA01 | PASS (D01) / **FAIL (P01 = ECO09)** |
| SKAT texts (E/F/P) | 3 languages | 3 languages | PASS |

**Issues found & fixed during this configuration:**

| Issue | When Found | Fix Applied | Status |
|-------|-----------|-------------|--------|
| 1165421 + 1165424 missing in D01 | Initial check | INSERT via RFC | **FIXED** |
| KTOKS = OTHR instead of BANK | Initial check | UPDATE SKA1 via RFC | **FIXED** |
| XINTB flag missing | Initial check | UPDATE SKB1 via RFC | **FIXED** |
| P01: HBKID = ECO09 on all 4 accounts | Cross-system check | **PENDING — fix in P01 via FS00** | **OPEN** |
| TXT20 short text differs D01 vs P01 | Cross-system check | No action (cosmetic) | ACCEPTED |

---

### STEP 2: House Bank and Account IDs (FI12)

**Path:** SPRO > Financial Accounting > Bank Accounting > Bank Accounts > Define House Banks

| Field | USD01 | MZN01 | D01 | P01 |
|-------|-------|-------|-----|-----|
| House Bank | UBA01 | UBA01 | PASS | MISSING (transport) |
| Account ID | USD01 | MZN01 | PASS | MISSING (transport) |
| Bank Account Number | 070340000190 | 070040004663 | PASS | — |
| Currency | USD | MZN | PASS | — |
| G/L Account | 1065421 | 1065424 | PASS | — |
| Bank Country | MZ | MZ | PASS | — |
| Bank Key | SP0000001YCB | SP0000001YCB | PASS | — |
| SWIFT | UNAFMZMA | UNAFMZMA | PASS | — |
| DME Instruction Key | B2 | B2 | To verify | — |

**D01 Status:** DONE  
**P01 Status:** Arrives via transport  

**Note:** BNKA bank directory has old address ("PRACA 16 DE JUNHO") vs form ("Av. Zedequias Manganhela, 267"). Update when creating in P01.

---

### STEP 3: Bank Statement Monitor (FTE_BSM_CUST)

| Account | Interval | Unit | Currency | D01 | P01 |
|---------|----------|------|----------|-----|-----|
| UBA01/USD01 | 1 | Calendar Days | USD | PASS | MISSING (transport) |
| UBA01/MZN01 | 1 | Calendar Days | MZN | PASS | MISSING (transport) |

**D01 Status:** DONE  
**P01 Status:** Arrives via transport  

---

### STEP 4: OBA1 — Exchange Rate Differences (T030H)

**ECO09 reference (1194424 in P01):** Complete entry with all 5 fields filled.

| T030H Field | Screen Field | UBA01 1165424 | UBA01 1165421 | ECO09 1194424 | Match |
|-------------|-------------|---------------|---------------|---------------|-------|
| LKORR | Bal.sheet adj / Correction | 1165424 | 1165421 | 1194424 | PASS |
| LSREA | Realized FX loss | 6045011 | 6045011 | 6045011 | PASS |
| LHREA | Realized FX gain | 7045011 | 7045011 | 7045011 | PASS |
| LSBEW | Valuation loss | 6045011 | 6045011 | 6045011 | PASS |
| LHBEW | Valuation gain | 7045011 | 7045011 | 7045011 | PASS |

| Account | Type | Currency | D01 | Needed? |
|---------|------|----------|-----|---------|
| 1065421 | Bank | USD | No entry | No — USD bank account |
| 1165421 | Sub-bank | USD | PASS (complete) | Optional (conservative) |
| 1065424 | Bank | MZN | No entry | No — bank accounts not revalued |
| 1165424 | Sub-bank | MZN | PASS (complete) | **Required** — non-USD clearing |

**D01 Status:** DONE  
**P01 Status:** Arrives via transport  

**Issue found & fixed:** Initial config only had LSREA/LHREA. Missing LKORR, LSBEW, LHBEW. Fixed 2026-04-07.

---

### STEP 5: Cash Management Account Name

**Path:** SPRO > Financial Supply Chain Management > Cash and Liquidity Management > Cash Management > Structuring > Define Cash Management Account Name

| CM Account | G/L Account | Bank Account | D01 | P01 |
|-----------|------------|-------------|-----|-----|
| UBA01-USD1 | 1065421 | 070340000190 | PASS | MISSING (transport) |
| UBA01-MZN1 | 1065424 | 070040004663 | PASS | MISSING (transport) |

**D01 Status:** DONE  
**P01 Status:** Arrives via transport  

---

### STEP 6: Electronic Bank Statement (T035D + T028B)

**Two tables in the same SPRO screen — both required:**

**T035D — Account Symbol to G/L mapping:**

| DISKB | G/L (BNKKO) | D01 | P01 |
|-------|-------------|-----|-----|
| UBA01-MZN1 | 1065424 | PASS | MISSING (transport) |
| UBA01-USD1 | 1065421 | PASS | MISSING (transport) |

**T028B — Bank Accounts to Transaction Types (bank key + bank acct → format):**

| Bank Key | Bank Account | Trans. Type | CM Account | D01 | P01 |
|----------|-------------|-------------|------------|-----|-----|
| SP0000001YCB | 070040004663 | XRT940 | UBA01-MZN1 | PASS | MISSING |
| SP0000001YCB | 070340000190 | XRT940 | UBA01-USD1 | PASS | MISSING |

**ECO09 reference (T028B):**

| Bank Key | Bank Account | Trans. Type | CM Account |
|----------|-------------|-------------|------------|
| XX001877 | 557500018002 | XRT940 | ECO09-MZN1 |
| XX001877 | 557500018003 | XRT940 | ECO09-USD1 |

**D01 Status:** DONE (both T035D and T028B)  
**P01 Status:** Arrives via transport  

**Issue found & fixed:** T028B entries were initially missing. T028B is keyed by bank key + bank account number (not HBKID), so the compliance checker initially missed it. Fixed 2026-04-07.

---

### STEP 7: Business Area Substitution (YFI_BASU_MOD)

Z1 AUTOMATIC BANK STAT / GEF rule uses G/L range **1000000 to 1199999**. All 4 accounts covered.

**D01 Status:** N/A — covered by range  
**P01 Status:** N/A — covered by range  

---

### STEP 8: Receiving Account for Payment Requests (V_T018V)

**Path:** SPRO > Financial Accounting > Bank Accounting > Business Transactions > Payment Transactions > Payment Request > Define Clearing Accounts for Receiving Bank Acct. Transfer

| CoCode | House Bk | Pmt Method | Currency | Account ID | Clrg Acct | D01 | P01 |
|--------|----------|-----------|----------|------------|-----------|-----|-----|
| UNES | UBA01 | A | USD | USD01 | 1165421 | PASS | MISSING |

**ECO09 reference:** ECO09 / A / USD / USD01 / Clrg=1194421 (same 10→11 pattern)

**D01 Status:** DONE  
**P01 Status:** Arrives via transport  

**TO REVIEW:** Only USD entry. ECO09 also has only USD. Confirm with TRS if MZN receiving is needed.

---

### STEP 9: Payment Configuration (FBZP)

#### 9.1 Bank Determination (T042I)

| House Bk | Pmt Method | Currency | Account ID | Clearing G/L | D01 | P01 |
|----------|-----------|----------|------------|-------------|-----|-----|
| UBA01 | 3 | MZN | MZN01 | 1165424 | PASS | MISSING |

**ECO09 reference:** ECO09 / 3 / MZN / MZN01 / 1194424 (same pattern)

Payment method 3 = pre-numbered check (Y110_PRENUM_CHCK) for local MZN payments.

**D01 Status:** DONE  
**P01 Status:** Arrives via transport  

**TO REVIEW:** No USD payment entry. ECO09 also has none. Confirm with TRS.

#### 9.2 Internal Transfer / Replenishment
Replenishment = YES for USD01 (G/L 1165421). Verify payment method A + instruction key B2 in FI12 "Data Medium Exchange" tab.

#### 9.3 Payment File Creation (OBPM4)
**TO VERIFY:** If paying bank, SAPFPAYM variant needed in V01 AND P01 (not transportable).

---

### STEP 10: Average Balance Report Sets (GS02)

| Account | Expected Set | D01 | P01 |
|---------|-------------|-----|-----|
| 1065424 (MZN) | YBANK_ACCOUNTS_FO_OTH | PASS | MISSING |
| **1065421 (USD)** | **YBANK_ACCOUNTS_FO_USD** | **FAIL** | **MISSING** |

**ISSUE — ACTION REQUIRED:** Account 1065421 is NOT in YBANK_ACCOUNTS_FO_USD.  
**ACTION:** GS02 > YBANK_ACCOUNTS_ALL > YBANK_ACCOUNTS_FO > YBANK_ACCOUNTS_FO_USD > Insert at Same Level > add 1065421. Repeat in D01, V01, P01 (maintained manually per system).

---

### STEP 11: Cash Position Reports (TRM5)

**Status:** Pending TRS confirmation.  
**Forms:** ZCASH and/or ZCASHFODET (field office).  
**ACTION:** After TRS confirms placement, add UBA01 accounts and update total formulas.

---

### STEP 12: Verify Grouping (V_T038)

Grouping uses pattern-based selections. New accounts covered by existing patterns.

**D01 Status:** N/A  
**P01 Status:** N/A  

---

### STEP 13: IBAN Generation (TIBAN)

| Account | IBAN (from form) | D01 | P01 |
|---------|-----------------|-----|-----|
| USD01 | MZ59004206077034000019028 | **MISSING** | **MISSING** |
| MZN01 | MZ59004206077004000466345 | **MISSING** | **MISSING** |

**ISSUE — ACTION REQUIRED:** IBAN not generated.  
**ACTION:** Generate via FI12 or IBAN maintenance. Creates Workbench transport.

---

## 3. Transport Requests

| Transport Type | Content | Status |
|---------------|---------|--------|
| Customizing | T012, T012K, T012T, T035D, T028B, T018V, T042I, FTE_BSM_CUST, T030H, Cash Mgmt | Created in D01 |
| Workbench | IBAN generation | **NOT YET CREATED** |

---

## 4. Summary of All Issues

| # | Severity | Step | System | Issue | Status |
|---|----------|------|--------|-------|--------|
| 1 | **CRITICAL** | 1 (FS00) | P01 | All 4 G/L accounts have HBKID=ECO09 instead of UBA01 | **OPEN — fix in P01 after transport** |
| 2 | RESOLVED | 1 (FS00) | D01 | 1165421/1165424 missing, KTOKS=OTHR, XINTB missing | **FIXED** via RFC 2026-04-07 |
| 3 | RESOLVED | 4 (OBA1) | D01 | T030H missing LKORR, LSBEW, LHBEW fields | **FIXED** via RFC 2026-04-07 |
| 4 | RESOLVED | 6 (T028B) | D01 | T028B entries missing for bank key SP0000001YCB | **FIXED** 2026-04-07 |
| 5 | **ACTION** | 10 (GS02) | D01 | 1065421 missing from YBANK_ACCOUNTS_FO_USD | **OPEN** |
| 6 | **ACTION** | 13 (TIBAN) | Both | IBAN not generated | **OPEN** |
| 7 | MINOR | 2 (FI12) | D01 | BNKA bank address outdated | **OPEN** — update when creating in P01 |
| 8 | TO REVIEW | 8 (T018V) | — | No MZN clearing entry, only USD | Confirm with TRS |
| 9 | TO REVIEW | 9 (T042I) | — | No USD payment entry, only MZN method 3 | Confirm with TRS |
| 10 | TO REVIEW | 9 (OBPM4) | — | Payment variant needed? | Confirm with TRS |
| 11 | MINOR | 1 (FS00) | D01/P01 | TXT20 short text abbreviation differs | ACCEPTED — cosmetic |

---

## 5. Remaining Tasks

### Before Transport (D01)
- [ ] **GS02:** Add 1065421 to YBANK_ACCOUNTS_FO_USD
- [ ] **TIBAN:** Generate IBAN entries for both accounts
- [ ] **OBPM4:** Verify/create SAPFPAYM variant (if paying bank)
- [ ] **FI12:** Verify DME instruction key = B2

### After Transport (P01)
- [ ] **FS00:** Change HBKID from ECO09 to UBA01 on all 4 G/L accounts
- [ ] **BNKA:** Update bank name and address
- [ ] **GS02:** Add accounts to YBANK sets (maintained manually per system)
- [ ] **TRM5:** Add to Cash Position reports (after TRS confirmation)

### Confirmations Needed from TRS
- [ ] Is MZN receiving account entry needed in T018V?
- [ ] Is USD payment method entry needed in T042I?
- [ ] Which ZCASH/ZCASHFODET form elements should include UBA01?
- [ ] Is OBPM4 payment variant needed?

---

## 6. Issues Discovered & Fixed During Configuration

These issues were found by the automated compliance checker and cross-system comparison, then fixed:

| # | What Was Wrong | How Discovered | How Fixed | Lesson for Future |
|---|---------------|----------------|-----------|-------------------|
| 1 | G/L 1165421/1165424 missing in D01 | RFC SKA1/SKB1 comparison P01 vs D01 | INSERT via RFC_ABAP_INSTALL_AND_RUN | Always verify clearing accounts exist before configuring house bank |
| 2 | KTOKS=OTHR instead of BANK | RFC SKA1 comparison | UPDATE SKA1 via RFC | MD team copies reference — verify account group after copy |
| 3 | XINTB flag missing in D01 | RFC SKB1 comparison | UPDATE SKB1 via RFC | Check all flags, not just currency and house bank |
| 4 | OBA1 incomplete — LKORR/LSBEW/LHBEW blank | Field-by-field T030H comparison vs ECO09 | UPDATE T030H via RFC | OBA1 has 3 sections — ALL must be filled: Realized + Valuation + Correction |
| 5 | T028B missing — bank key not mapped | Deep table investigation (T028B keyed by BANKL, not HBKID) | Manual entry via SPRO | T035D and T028B are in same screen but different tables — both required for EBS |
| 6 | P01 G/L accounts have HBKID=ECO09 | Cross-system SKB1 comparison | **PENDING** — fix via FS00 in P01 | MD team copies reference HBKID — always verify after G/L creation |

---

## 7. Compliance Check Tools

### Single-System Checker
**Script:** `Zagentexecution/mcp-backend-server-python/house_bank_compliance_checker.py`

```python
SYSTEM = "D01"    # or "P01"
BUKRS  = "UNES"
KTOPL  = "UNES"
HBKID  = "UBA01"  # change to any house bank
```

15 checks: T012, BNKA, T012K, T012T, SKA1, SKB1, SKAT, TIBAN, T030H (with LKORR/LSBEW/LHBEW), FDSB, T035D, T028B, T018V, T042I, SETLEAF.

### Cross-System Comparison
**Script:** `Zagentexecution/mcp-backend-server-python/uba01_final_report.py`

Extracts ALL config from D01 and P01, compares field-by-field, flags wrong HBKID assignments.

### ECO09 Benchmark Extraction
**Script:** `Zagentexecution/extract_eco09_benchmark.py`

Full extraction of ECO09 from P01 — the gold standard reference.

---

## 8. ECO09 Benchmark Patterns (for future house banks)

| Pattern | Rule |
|---------|------|
| G/L numbering | Bank = 10xxxxx, Sub-bank = 11xxxxx (same last 5 digits) |
| Account Group (KTOKS) | Always BANK |
| Planning Level (FDLEV) | Bank = B0, Sub-bank = B1 |
| Field Status (FSTAG) | UN03 for all |
| Sort Key (ZUAWA) | Bank = 027, Sub-bank = Z01 |
| Open Item Mgmt (XOPVW) | Only on sub-bank accounts |
| Post Auto Only (XINTB) | X on all |
| Cash Flow (XGKON) | X on all |
| Commitment Item (FIPOS) | BANK for all |
| OBA1 (T030H) | Non-USD clearing accounts: fill ALL fields (LKORR=itself, LSREA, LHREA, LSBEW, LHBEW) |
| T035D (EBS) | Naming: {HBKID}-{CUR}1 (e.g., UBA01-USD1) → G/L bank account |
| T028B (EBS) | Bank Key + Bank Acct → XRT940 + CM Account name. MUST be configured. |
| T018V clearing | Pmt Method A, 10xxxxx bank → 11xxxxx clearing |
| T042I payment | Method 3 for MZN local checks, Method A for USD transfers |
| DME instruction key | B2 (except DNB01 = B4) |
| YBANK sets | FO banks → YBANK_ACCOUNTS_FO_{USD/OTH/EUR}. Exact match, not ranges. |
| Business Area | GEF via YFI_BASU_MOD range 1000000-1199999 (automatic) |
