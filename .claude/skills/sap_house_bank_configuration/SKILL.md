---
name: SAP House Bank Configuration (Create / Modify / Close)
description: >
  End-to-end house bank configuration for UNESCO SAP (company code UNES).
  Covers 13 configuration steps across FS00, FI12, FBZP, OBA1, GS02, TRM5,
  electronic bank statement, cash management, and payment program.
  Includes automated compliance checker, cross-system comparison (D01 vs P01),
  and ECO09-proven configuration patterns.
  Discovered Session 2026-04-07 from 45-page handover procedure + real UBA01 config.
domains:
  functional: [Treasury]
  module: [FI]
  process: [T2R]
tier: project
maturity: production
origin_session: 46
last_updated_session: 48
triggers: [house bank, T012, T012K, FI12, FS00, FBZP, UBA01, ECO09, NTB01, HBKID, BKVID, IBAN, bank key, payment program, cash management]
subtopics: [13_config_steps, compliance_checker, cross_system_comparison_D01_P01, ECO09_benchmark]
---

# SAP House Bank Configuration — Create / Modify / Close

## When to Use This Skill

- New bank account request arrives (email from TRS/BFM)
- Existing bank account needs modification (new IBAN, address change, currency change)
- Bank account closure request
- Compliance audit of existing house bank configuration

## Input Documents

Every house bank request arrives with these documents:

| Document | Content | Who Provides |
|----------|---------|-------------|
| Email chain | Request + approval from TRS | TRS (Anssi/Baizid) |
| Bank confirmation PDF/letter | Account numbers, IBAN, SWIFT, address | The bank |
| House bank form (.xls) | 1 per account ID: house bank details, replenishment, EBS flag | TRS |
| G/L creation form (Form AM3-11, .xls) | 1 per G/L account: account number, reference, texts, currency | TRS |

**Naming convention for forms:**
- `{HBKID}-{AcctID}.xls` — House bank form (e.g., UBA01-USD01.xls)
- `Form AM3-11 - {GL}-{HBKID}-{AcctID}.xls` — G/L form (e.g., Form AM3-11 - 1065421-UBA01-USD01.xls)

### House Bank Form Fields (Excel — 1 per account ID)

| Field | Values | Drives Step | Notes |
|-------|--------|-------------|-------|
| Company Code | UNES | All | Always UNES |
| House Bank | {HBKID} (e.g., UBA01) | 2 (FI12) | 5-char code, bank abbreviation + sequence |
| Account ID | {AcctID} (e.g., USD01, MZN01) | 2 (FI12) | Currency code + sequence |
| Account Description | Free text (e.g., "UNESCO MAPUTO - USD") | 2 (T012T) | Used in T012T |
| Bank Account Number | From bank letter | 2 (T012K) | BANKN field in T012K |
| Control Key | Usually blank | 2 (T012K) | REFZL |
| IBAN (if available) | From bank letter | 13 (TIBAN) | May be generated later |
| Currency | USD, EUR, MZN, etc. | Multiple | **KEY FIELD: if non-USD, OBA1 required** |
| G/L Account number | 10xxxxx | 1 (FS00) | Bank account GL |
| Bank Country | 2-char ISO | 2 (T012/BNKA) | From bank letter |
| Bank Key | SAP bank key | 2 (T012) | From bank directory (BANKL) |
| Bank Name | From bank letter | 2 (BNKA) | |
| Street / Location | From bank letter | 2 (BNKA) | |
| SWIFT Code | From bank letter | 2 (BNKA) | |
| **Replenishment Settings?** | **Yes / No** | **9.2** | **Yes → needs internal transfer config (step 9.2)** |
| G/L account for replenishment | 11xxxxx (clearing GL) | 9.2 | Only if replenishment=Yes |
| Currency for replenishment | Same as account currency | 9.2 | |
| **Cash Management Account Name** | {HBKID}-{HKTID} | **5** | DISKB key from T012K account ID (e.g., UBA01-MZN1). NOT currency |
| **Bank statement electronically uploaded?** | **Yes / No** | **3, 5, 6** | **KEY FIELD: Yes → needs FTE_BSM_CUST + T035D + T028B** |
| **New G/L accounts to be created?** | **Yes / No** | **1** | Yes → MD team creates in P01 first |
| Comments | Free text | — | May contain: "Alternative account: UNO17", bank type hints |

### G/L Creation Form Fields (Form AM3-11 — 1 per G/L account)

| Field | Values | Drives | Notes |
|-------|--------|--------|-------|
| CREATE GL / BLOCK GL A/C / MODIFY DESCRIPTION | Checkbox | 1 (FS00) | Action type |
| Company Codes | UNES | 1 | |
| Account number | 10xxxxx or 11xxxxx | 1 | New GL number |
| **GL account to use as reference** | Existing GL (e.g., 1095012) | 1 | **Copy field values from this account — determines FDLEV, ZUAWA, FSTAG etc.** |
| Account group | Bank a/c / Other balance sheet a/c | 1 (SKA1) | **Must be "Bank a/c" → KTOKS=BANK. "Other balance sheet" = KTOKS=OTHR (wrong for bank GLs)** |
| GL account long text | Free text | 1 (SKAT) | TXT50 |
| Comments | "short name: {TXT20}" | 1 (SKAT) | Short text not always in form — must be shortened manually |
| Account Currency (other than USD) | EUR, MZN, etc. or blank=USD | 1 (SKB1) | **If non-USD → OBA1 required (step 4)** |
| Tax category | Usually blank | 1 | |
| House bank ID | {HBKID} | 1 (SKB1) | HBKID field — **MD team often copies reference and forgets to change this** |
| Bank account ID | {AcctID} | 1 (SKB1) | HKTID field |
| Cost element | 1 (Expenses) / 11 (Revenue) / blank | 1 | Blank for bank accounts |
| GL to be revaluated | **YES** / NO | **4 (OBA1)** | **YES + non-USD → OBA1 required** |

### Decision Flow: Form → Bank Type → Steps

```
READ FORMS
    |
    +-- "Bank statement electronically uploaded?" = Yes?
    |       |
    |       YES → EBS_CONFIG (steps 3, 5, 6a, 6b required)
    |       NO  → BASIC (skip 3, 5, 6)
    |
    +-- "Replenishment Settings?" = Yes?
    |       |
    |       YES → needs step 9.2 (internal transfer)
    |       NO  → skip 9.2
    |
    +-- Comments say "for payments" / TRS confirms F110 usage?
    |       |
    |       YES → PAYING (steps 9.1 + 9.2 + 9.3 all required)
    |       NO  → skip 9.1, 9.3
    |
    +-- Account Currency != USD?
    |       |
    |       YES → OBA1 REQUIRED for clearing GL (step 4)
    |       NO  → OBA1 optional for USD clearing
    |
    +-- "GL to be revaluated" = YES + non-USD?
            |
            YES → confirms OBA1 with all 3 sections
```

## Account Structure

Every house bank account creates a **pair** of G/L accounts:

| Type | Range | Prefix | Purpose | Example |
|------|-------|--------|---------|---------|
| Bank account | 10xxxxx | BK | Main bank account, receives postings | 1065421 |
| Sub-bank / clearing | 11xxxxx | S-BK | Clearing for payments, reconciliation | 1165421 |

The last 5 digits are always the same between the pair. Some banks have 4 G/L accounts (10*, 11*, 12*, 13*).

## Configuration Patterns (from Gold DB analysis of 211 banks + ECO09 benchmark)

> Source: Gold DB analysis of 211 house banks (Session #044, 2026-04-07).
> 117 closed, 67 active, 3 legacy. Patterns validated against ECO09 benchmark
> and cross-referenced with handover PDF + house bank Excel forms.
> Data: T012(211), T012K(402), T012T(1049), T028B(169), T030H(1014),
> T035D(151), T018V(108), T042I(76), P01_SKA1(2491), P01_SKB1(9249).

### Bank Classification (from reality — validated Session #044)

Determined by which config tables have entries + form fields:

| Category | Count | Form Indicators | Config Steps Required |
|----------|-------|-----------------|----------------------|
| **HQ_PAYING** | ~9 (SOG01, SOG03, CIT04, CIT21, SOG02, SOG05, BRA01, CIT01, UNI01) | "Bank is also paying account"=Yes + T042A DMEE routing + OBPM4 variants | ALL 13 steps: T042I + T042A + OBPM4 + SAPFPAYM variant |
| **FO_LOCAL_DISBURSEMENT** | ~1 (ECO09) | T042I with local method (3=check) but NO T042A. Pays locally, replenished from HQ centrally | Steps 1-8, 9.1 (T042I only), 10. No 9.3/OBPM4 |
| **EBS_CONFIG** | 56 | "Bank statement electronically uploaded?"=Yes in form | Steps 1-8, 10, 13. No 9.1/9.3 |
| **INVESTMENT/COUPON** | 2 (BKT01, JPS01) | KTOKS=OTHR, SKAT="BLOCKED - Coupons". Not regular bank accounts | No standard bank config — managed by Treasury for bond coupon payments |
| **INTER_AGENCY** | 1 (UNDP) | KTOKS=OTHR, "UNDP OFS account". UN inter-agency clearing | Separate process — not standard bank creation |
| **PENDING/DORMANT** | 5 (CIB01, CIB02, PCO01, SGL01, BKN01) | T012K exists but no GL assigned (HKONT empty) | Awaiting setup or abandoned — verify with TRS before configuring |
| **MISCLASSIFIED** | 1 (BSU02) | SKAT says "CLSD" (abbreviation, not "CLOSED") — missed by closed detection | Should be CLOSED. OBA1 gap is moot |
| **CLOSED** | 117 | SKAT text contains "CLOSED" | Closure process only |

**Note:** Some HQ_PAYING banks (CIT04, SOG01, SOG03) have partially blocked G/L accounts (XSPEB=X) but their T042I/T042A config remains active — they are in a mixed state, not formally deactivated.

**How to determine bank type from the Excel form:**

| Form Field | Value | Means |
|-----------|-------|-------|
| Bank statement electronically uploaded? | **Yes** | EBS_CONFIG — needs steps 3, 5, 6 (T035D + T028B) |
| Bank statement electronically uploaded? | **No** | BASIC — skip EBS config |
| Replenishment Settings? | **Yes** | Internal transfer — needs step 9.2 |
| Comments: "Account is for payments" / TRS says F110 | **Yes** | PAYING — needs 9.1 + 9.2 + 9.3 + OBPM4 |
| Account Currency (other than USD) | Any non-USD | OBA1 REQUIRED (step 4) for clearing account |

### Step Requirement Matrix (from Gold DB — validated by 3 independent agents)

| Step | HQ_PAYING (~9) | FO_LOCAL (ECO09) | EBS_CONFIG (56) | How Verified |
|------|---------------|------------------|-----------------|-------------|
| 1. FS00 | REQ | REQ | REQ | P01_SKA1/SKB1: 343 KTOKS=BANK, 10 OTHR. FSTAG=UN03 100% standard |
| 2. FI12 | REQ | REQ | REQ | T012(211), T012K(402), T012T(1049) |
| 3. FTE_BSM | REQ | REQ | REQ | FCLM_BSM_CUST not readable via RFC |
| 4. OBA1 | REQ (non-USD 11*) | REQ (non-USD 11*) | REQ (non-USD 11*) | T030H: 1,014 entries. 814 complete, 200 partial. **~75 active non-USD accounts missing — systemic gap, revaluation risk** |
| 5. CM Name | REQ | REQ | REQ | T035D: 151 entries. DISKB key = {HBKID}-{HKTID} (T012K account ID) |
| 6a. T035D | REQ | REQ | REQ | T035D: 151 entries |
| 6b. T028B | REQ | REQ | REQ | T028B: 169 entries. 77% XRT940, 11% TR_TRNF, 5% SOG_FR, 7% custom |
| 7. BASU | N/A | N/A | N/A | Range 1000000-1199999 covered by Z1 |
| 8. T018V | REQ | REQ | REQ | T018V: 108 entries, 100% method A. **Multi-currency: 69% USD, 20% EUR, 11% other (CHF/JPY/GBP/etc.)** |
| 9.1 T042I | REQ | REQ (local method) | N/A | T042I: **10 banks** configured. HQ: SOG01(4/J/N/S), SOG03(N), CIT04(5/L/N/X), CIT21(C). FO local: ECO09(3) |
| 9.2 Acct Det | REQ | OPT | N/A | Account Determination for G/L Account Payments: 11 banks |
| 9.3 OBPM4 | REQ (V01+P01) | N/A | N/A | Only HQ paying banks. ECO09 pays locally — no DMEE file needed |
| 10. GS02 | REQ | REQ | REQ | SETLEAF: 158 entries in 10 YBANK sets, D01=P01 aligned |
| 11. TRM5 | N/A | N/A | N/A | **No longer required** (2026-04-07) |
| 12. T038 | N/A | N/A | N/A | Grouping is pattern-based (+++10++0++, +++11++9++), not per-account |
| 13. TIBAN | OPT | OPT | OPT | TIBAN not readable via RFC (auth restricted) |

### Discovered Patterns from 67 Active Banks

**Pattern P1: T018V is multi-currency, method A only**
- **Evidence:** 108 entries, 100% method A. 69% USD, 20% EUR, 11% other (CHF, JPY, GBP, DKK, CAD, AUD, ZWG, HTG). SOG03 alone has 6 non-USD currencies.
- **PDF says:** "Add account as receiving account for payment requests" — copy from reference.
- **Reality:** Local FO currencies (MZN, XAF, KHR) mostly don't have T018V, but EUR/CHF/JPY accounts DO. Pattern: T018V needed for any account that receives wire transfers, regardless of currency.
- **CONTROL C1:** After step 8, verify: `SELECT * FROM T018V WHERE BUKRS='UNES' AND HBKID='{HBKID}'`. Each account that receives external transfers must have an entry. Clearing GL must match derived 11* pattern.

**Pattern P2: ZUAWA (Sort Key) variation**
- **Evidence:** Bank (10*): 97% use 027. Clearing (11*): Z01 standard for new FO banks, 027 legacy (~16 active HBKIDs), Z03 (NTB02), 001 (UNDP/special).
- **PDF says:** Not specified — inherited from reference account during creation.
- **Reality:** All variants are operational. The sort key determines how line items are sorted in account statements. 027=by document number, Z01=by assignment field (custom UNESCO).
- **CONTROL C2:** For new banks, verify clearing accounts have ZUAWA=Z01: `SELECT SAKNR, ZUAWA FROM SKB1 WHERE BUKRS='UNES' AND SAKNR='{clearing_GL}'`. Bank accounts (10*) should have 027. If the reference GL had a different ZUAWA, it will be copied — check and correct after creation.

**Pattern P3: XINTB (Post Automatically Only)**
- **Evidence:** 1,005 KTOKS=BANK accounts: 1,003 empty (99.8%), 2 with X (0.2% — NTB02 IMIP only)
- **PDF says:** Not mentioned in the handover procedure or forms
- **Reality:** XINTB=X exists on 2 types of accounts: (a) NTB02 IMIP investment accounts — special purpose, intentional. (b) 73 field office CASH accounts (190xxxx petty cash) — also intentional, blocks external postings on cash boxes.
- **INCIDENT 2026-04-07:** UBA01 configured with XINTB=X following ECO09 benchmark. User Ingrid Wettie reported SAP error F5562 ("Account can only be posted to internally") on 1165421. XINTB=X blocks ALL manual postings including EBS clearing, payment postings, and manual journal entries.
- **Root cause:** ECO09 itself does NOT have XINTB=X — the benchmark extraction was wrong or misread.
- **CONTROL C3:** For every new bank account, verify XINTB is empty BEFORE going live. If XINTB=X, SAP will block F5562 on first posting. Check: `SELECT XINTB FROM SKB1 WHERE BUKRS='UNES' AND SAKNR='{GL}'` — must return empty.
- **RULE: NEVER set XINTB=X on bank accounts (10*/11*). Only CASH accounts (190*) and special investment accounts may have it.**

**Pattern P4: T028B transaction types**
- **Evidence:** 169 entries. 77% XRT940 (standard MT940), 11% TR_TRNF (HQ treasury), 5% SOG_FR (SocGen custom), 7% other custom (CIT24_GA, SCB19_IQ, CIT01_BR, CIT04_US, UBOBSBB).
- **PDF says:** "Copy from similar type of account and assign Transaction type" — check if bank requires electronic bank statement.
- **Reality:** FO banks always use XRT940. HQ banks may use TR_TRNF or custom. The form field "Bank statement electronically uploaded?" determines if T028B is needed at all.
- **CONTROL C4:** After step 6b, verify: `SELECT * FROM T028B WHERE BANKL='{bank_key}'`. Each bank account number (BANKN from T012K) must have a T028B entry. BNKKO must match the CM account name from step 5. If form says "EBS=No", T028B is not needed.

**Pattern P5: T030H (OBA1) SYSTEMIC GAP — CRITICAL FINDING**

> **THIS IS THE #1 FINDING OF SESSION #044.**
> 213 of 219 non-USD bank accounts (10*) have NO T030H valuation entry.
> 48 of 204 non-USD clearing accounts (11*) are also missing.
> Impact: FAGL_FC_VAL skips these accounts at month-end — FX gains/losses on
> real cash balances in 80+ currencies at 80+ field offices are NOT in the
> financial statements. Material financial reporting gap.

- **Evidence:** 1,014 entries total (not just bank GLs — also receivables, clearing, VAT accounts). 814 complete, 200 partial. Two patterns by CURTP:
  - CURTP=10 (foreign currency): Loss=6045011, Gain=7045011 — **579 entries (71%)**
  - CURTP=30 (presentation currency): Loss=5022012, Gain=5022012 — **235 entries (29%)**
  - LKORR = account itself in 72% of cases. 28% point to shadow/clearing account.
- **PDF says:** "Add 11* account to OBA1. Only in case account is in other currency as USD. Copy from Reference. ALL 3 sections must be filled (Realized + Valuation + Correction)."
- **Reality:** ~75 active non-USD UNES accounts are missing T030H entirely (SOG01/EUR, SOG03 multi-currency, CBE01/ETB, BNP01/EUR, all ECO0x FO FX accounts). 200 entries have only Realized section filled (LKORR+LSBEW+LHBEW empty). **Revaluation risk is real** — these accounts carry EUR/BRL/XOF/XAF postings.
- **CONTROL C5 — CRITICAL:** After step 4, verify ALL non-USD GLs (BOTH 10* bank AND 11* clearing):
  - `SELECT * FROM T030H WHERE KTOPL='UNES' AND HKONT='{GL}'`
  - Must return a row with ALL 5 fields non-empty (LKORR, LSREA, LHREA, LSBEW, LHBEW)
  - If LKORR/LSBEW/LHBEW are empty → Valuation+Correction sections were skipped → **FAGL_FC_VAL will skip this account at month-end**
  - If NO row exists → account has NO OBA1 config at all → **both clearing AND valuation will fail**
  - **SYSTEMIC CHECK:** Run `house_bank_pattern_discovery.py` to audit ALL 219 non-USD bank accounts. Current production: only 3% have T030H. This is a material gap.
  - **Bank accounts (10*) MUST have T030H** — they hold real cash balances that must be revalued. Previous rule "optional for 10*" was WRONG.

**Pattern P6: 4-account banks**
- **Evidence:** NTB02 has 10*, 11*, 12*, 13* GL pairs. Cash position form (ZCASHFODET) shows all 4 GLs per element definition.
- **PDF says:** "Special Case — When you copy a bank account with 4 accounts instead of 1" — reference 1095012→1095022, 1195012→1195022, plus 12*/13* pairs.
- **Reality:** Rare pattern — mostly HQ investment banks (Northern Trust). FO banks use standard 2-account pairs.
- **CONTROL C6:** After step 1, count GLs per house bank: `SELECT COUNT(*) FROM T012K WHERE BUKRS='UNES' AND HBKID='{HBKID}'`. If >2 accounts, verify all pairs are configured in steps 4-6-8 (not just the first pair).

**Pattern P7: T038 Grouping (Cash Management)**
- **Evidence:** T038 uses wildcard selections (+++10++0++, +++11++9++), not individual accounts. Groups: ALL HQS (10*/11*/16*/17*/19*/C+/C2/V+), ATSIGHT HQ (specific NTB/SOG accounts).
- **PDF says:** "SM30 V_T038 — Verify whether the new account is correctly represented in the grouping." Step 12 in procedure.
- **Reality:** Standard 10*/11* bank accounts are automatically captured by wildcards. Only exceptions (specific GLs like 1068713) are added individually. Step 12 is N/A for standard FO banks.
- **CONTROL C7:** After step 12 (or as verification), confirm the new GL falls within existing wildcard ranges. Only flag if the GL is outside 10*/11* standard range (e.g., 19* cash, 20* investment).

**Pattern P8: HQ Paying vs FO Local Disbursement**
- **Evidence:** T042I: 10 banks. T042A: 10 banks (overlapping but not identical). ECO09 in T042I but NOT T042A. BNP01 in T042A but NOT T042I.
- **PDF says:** "Step 9 — Only if Bank is also a paying bank account." Three sub-steps: 9.1 (T042I bank determination), 9.2 (internal transfer), 9.3 (OBPM4 payment file).
- **Reality:** Two distinct types:
  - **HQ Paying** (SOG01, SOG03, CIT04, CIT21, etc.): T042A + T042I + OBPM4. Generate DMEE payment files for F110 runs.
  - **FO Local** (ECO09): T042I method 3 (local check) but NO T042A. Pays locally, replenished from HQ centrally. No DMEE file needed.
  - Some HQ banks partially wound down: CIT04 (3/5 GLs blocked), SOG01 (1/7), SOG03 (6/14 GLs XSPEB=X).
- **CONTROL C8:** For paying banks, verify both T042I AND T042A: `SELECT * FROM T042I WHERE ZBUKR='UNES' AND HBKID='{HBKID}'` + `SELECT * FROM T042A WHERE ZBUKR='UNES' AND HBKID='{HBKID}'`. HQ paying banks must have both. FO local banks need only T042I. If T042I exists without T042A, confirm it's a local disbursement bank (not a missing routing config).

**Pattern P9: XOPVW (Open Item Management) on clearing accounts**
- **Evidence:** 341/346 clearing accounts (98.5%) have XOPVW=X. Only 5 exceptions.
- **PDF says:** Not explicitly mentioned in procedure, but FS00 screenshots show Open Item Management checked on clearing accounts.
- **Reality:** Near-universal. XOPVW=X enables clearing (FEBAN) on sub-bank accounts. Without it, bank statement clearing fails — items cannot be matched and cleared.
- **CONTROL C9:** After step 1, verify ALL clearing GLs: `SELECT SAKNR, XOPVW FROM SKB1 WHERE BUKRS='UNES' AND SAKNR='{clearing_GL}'`. XOPVW must be X. If empty, FEBAN clearing will fail on this account.

### Known Issues (from Gold DB audit — validated by 3 independent agents)

| Issue | Banks Affected | Severity | Notes |
|-------|---------------|----------|-------|
| **T030H SYSTEMIC GAP — #1 FINDING** | **213 of 219 non-USD bank accounts (10*) have NO T030H. 48 of 204 non-USD clearing accounts (11*) also missing.** Affects SOG01/03, CIC01, BNP01, all ECO, all CIT, all SCB, NTB02 — 80+ field offices, 80+ currencies | **CRITICAL** | **FAGL_FC_VAL skips these accounts at month-end. FX gains/losses on real cash balances are NOT in financial statements. Material reporting gap. Requires mass T030H creation for all non-USD bank + clearing accounts.** |
| UBA01 XINTB=X blocks postings | All 4 UBA01 GLs in P01 | **HIGH — RESOLVED** | Fixed: D01 via RFC, P01 by MD team. F5562 error reported by Ingrid Wettie. Pattern P3 confirmed: NEVER set XINTB=X on bank accounts. |
| **ECO09 missing from T042A** | ECO09 has T042I method 3 but no T042A routing | **MEDIUM** | Probably works because ECO09 pays locally (method 3=check), not via DMEE file. Verify with TRS |
| HBKID mismatch | CIT10→CIT20, BNL01→BLN01, BOF01→BKC01, CAF01→CAF02, DEU01→_UIL | MEDIUM | MD team copied reference GL and forgot to update HBKID |
| KTOKS=OTHR on active EBS banks | ECO04, SCB12 | MEDIUM | Should be BANK — fix via FS00 |
| KTOKS=OTHR on special accounts | BKT01 (investment), JPS01 (investment), UNDP (inter-agency) | LOW | Correct for their purpose — OTHR is intentional |
| T028B: bank account not mapped | CIC01 (3 EUR accts), DEU02, NTB02 | MEDIUM | These bank account numbers not in T028B — verify if they receive MT940 |
| DEU02: T018V clearing GL mismatch | T018V=5098019 vs derived=1150792 | MEDIUM | Non-standard clearing GL — investigate purpose |
| BSU02 misclassified | SKAT says "CLSD" not "CLOSED" — missed by closed detection | LOW | Actually closed, OBA1 gap is moot |
| HQ paying banks partially blocked | CIT04 (3/5 GLs), SOG01 (1/7), SOG03 (6/14) have XSPEB=X | INFO | Winding down but T042I still active |

### G/L Account Master Data (FS00)

| Field | Bank Account (10*) | Sub-bank Account (11*) |
|-------|-------------------|----------------------|
| KTOKS (Account Group) | BANK | BANK |
| XBILK (Balance Sheet) | X | X |
| FDLEV (Planning Level) | **B0** | **B1** |
| FSTAG (Field Status Group) | UN03 | UN03 |
| ZUAWA (Sort Key) | **027** | **Z01** |
| XKRES (Line Item Display) | X | X |
| XGKON (Cash Flow Relevant) | X | X |
| XINTB (Post Auto Only) | **— (NEVER X)** | **— (NEVER X)** |
| XOPVW (Open Item Management) | **—** | **X** |
| FIPOS (Commitment Item) | BANK | BANK |
| HBKID (House Bank) | {HBKID} | {HBKID} |
| HKTID (Account ID) | {AcctID} | {AcctID} |

**Key differences between bank and sub-bank:**
- FDLEV: B0 (bank) vs B1 (sub-bank) — **100% consistent** across 346 bank GLs
- ZUAWA: 027 (bank) vs Z01 (sub-bank) — ECO09 pattern. 18 legacy banks use 027 on clearing (operational, not a failure)
- XOPVW: empty (bank) vs X (sub-bank, Open Item Management) — **85% compliance** (50 clearing GLs not in SKB1)
- XINTB: **NOT required** — Gold DB shows only 1 of 353 bank G/Ls has XINTB=X. Production standard is empty despite ECO09 having X. Do not flag as failure.

### House Bank Master (FI12)

| Field | Rule |
|-------|------|
| DME Instruction Key | **B2** (except DNB01 = B4) |
| Bank Country | From bank confirmation letter |
| Bank Key | SAP bank directory key for the bank |
| SWIFT | From bank confirmation letter |

### OBA1 — Exchange Rate Differences (T030H)

#### Why OBA1 exists — 3 FX scenarios

OBA1 configures how SAP handles foreign currency differences on G/L accounts. The OBA1 screen has **3 sections**, each for a different scenario:

**Section 1: Exchange Rate Difference Realized (LSREA / LHREA)**
- **When:** An open item is **cleared** (e.g., FEBAN clears a bank statement item against a payment posting)
- **What happens:** The item was posted at exchange rate X, cleared at rate Y. The difference is a **realized** FX gain or loss.
- **Posts to:** 6045011 (realized loss) / 7045011 (realized gain)
- **Example:** Payment posted in MZN at 63.5 MZN/USD. Bank statement arrives, clears at 64.0 MZN/USD. The 0.5 difference per unit is posted as realized FX loss.
- **Needed for:** ALL non-USD accounts that are cleared (11* clearing accounts always, 10* bank accounts if they have clearing activity)

**Section 2: Valuation (LSBEW / LHBEW)**
- **When:** Month-end / year-end **FAGL_FC_VAL** (foreign currency revaluation program) runs
- **What happens:** Open items AND balances in foreign currency are revalued at the closing exchange rate. The difference is an **unrealized** valuation gain or loss.
- **Posts to:** 6045011 (unrealized valuation loss) / 7045011 (unrealized valuation gain)
- **These entries are reversed** at the start of the next period (temporary adjustment).
- **Example:** Bank account holds 10M MZN. At end of March, rate is 63.5. At end of April, rate is 65.0. The USD equivalent changed — FAGL_FC_VAL posts the difference as unrealized valuation.
- **Needed for:** ALL non-USD accounts that hold balances — **this includes bank accounts (10*) because they hold real cash.**
- **Without this:** FAGL_FC_VAL skips the account entirely. The FX position in the balance sheet is wrong.

**Section 3: Balance Sheet Adjustment (LKORR)**
- **When:** SAP needs to know **where to post the balance sheet side** of the valuation entry
- **What it is:** The correction account that receives the offsetting entry for the valuation posting.
- **Pattern:** LKORR = the account itself (e.g., 1165421). This means the valuation adjustment stays on the same account.
- **Without this:** SAP cannot complete the valuation posting — the balance sheet side has no target account.

#### Requirement Matrix (CORRECTED Session #044)

| Account Type | Currency | Realized (LSREA/LHREA) | Valuation (LSBEW/LHBEW) | Bal.sheet adj (LKORR) | Why |
|-------------|----------|------------------------|-------------------------|-----------------------|-----|
| **Bank (10*)** | **Non-USD** | **YES** | **YES** | **YES** | **Holds real cash balances in foreign currency — MUST be revalued at month-end** |
| **Clearing (11*)** | **Non-USD** | **YES** | **YES** | **YES** | Carries open items in foreign currency — both clearing and revaluation |
| Bank (10*) | USD | No | No | No | USD is local currency — no FX difference |
| Clearing (11*) | USD | Optional | Optional | Optional | USD — no FX difference, but conservative to add |

> **PREVIOUS RULE WAS WRONG:** The skill previously said 10* bank accounts only need "Optional (conservative)" valuation. This is incorrect. Bank accounts hold cash — cash in foreign currency MUST be revalued. The Gold DB audit confirmed **only 6 of 219 non-USD bank accounts (3%) have T030H entries**. This is a systemic gap.

#### Standard Values

| T030H Field | OBA1 Screen Field | Standard Value (CURTP=10) |
|-------------|------------------|---------------------------|
| CURTP | Currency Type | 10 (company code currency) |
| LKORR | Bal.sheet adj.1 | **The account itself** (e.g., 1165424) |
| LSREA | Loss (Realized) | **6045011** |
| LHREA | Gain (Realized) | **7045011** |
| LSBEW | Val.loss 1 (Valuation) | **6045011** |
| LHBEW | Val.gain 1 (Valuation) | **7045011** |

**CRITICAL:** ALL 3 sections must be filled. Do NOT fill only Realized and skip Valuation+Correction. The OBA1 screen shows all 3 sections on one page — fill every field.

#### Systemic Gap Discovered (Session #044)

**Gold DB audit of ALL 211 house banks revealed:**

| Account Type | Total Non-USD | With T030H | Missing | Coverage |
|---|---|---|---|---|
| Bank accounts (10*) | 219 | 6 | **213** | **3%** |
| Clearing accounts (11*) | 204 | 156 | **48** | 76% |

**213 non-USD bank accounts have NO valuation config.** This affects:
- SOG01 (3 EUR HQ accounts), SOG03 (AUD/CHF/DKK/GBP/JPY), SOG05 (EUR)
- CIC01 (2 EUR), BNP01 (2 EUR), CRA01 (2 EUR), DEU02 (EUR)
- All 10 ECO banks (XAF/XOF/MZN/BIF/SSP/ZAR)
- All 20+ CIT field offices (local currencies)
- All 18 SCB field offices (local currencies)
- NTB02 (2 EUR investment accounts)

**Impact:** Every month-end, FAGL_FC_VAL skips these accounts. FX gains/losses on real cash balances in 80+ foreign currencies across 80+ field offices are NOT reflected in the financial statements. This is a material financial reporting gap.

**Action required:** Mass T030H creation for all non-USD bank accounts (10*). Values are standard (6045011/7045011/account itself). Can be automated via OBA1 or RFC.

#### Lesson from UBA01 (2026-04-07)

Initial configuration only filled LSREA/LHREA (Realized section). LKORR, LSBEW, LHBEW were blank in V01 and P01. Discovered by 3-system comparison D01 vs V01 vs P01. Transport D01K9B0F5K carries the fix.

### Electronic Bank Statement (T035D + T028B)

EBS configuration has **two tables** in the same SPRO screen — both must be configured:

**T035D — Account Symbol to G/L mapping (dialog node: various)**

| Field | Pattern |
|-------|---------|
| DISKB (CM Account Name) | `{HBKID}-{HKTID}` (e.g., UBA01-MZN1 where MZN1 = T012K account ID) |
| BNKKO (G/L Account) | The bank account G/L (10xxxxx) |

**DISKB key construction rule:** DISKB = `{HBKID}-{HKTID}` where HKTID comes from T012K. Example: house bank UBA01, account ID MZN01 in T012K → DISKB = UBA01-MZN1. The HKTID naming convention in T012K is typically `{CUR}{NN}` (e.g., MZN01), and the DISKB may use a shortened form (MZN1 vs MZN01) — always verify against T012K.

**T028B — Bank Accounts to Transaction Types (dialog node: last one)**

| Field | Pattern |
|-------|---------|
| BANKL (Bank Key) | From T012 (e.g., SP0000001YCB) |
| KTONR (Bank Account Number) | From T012K.BANKN (e.g., 070040004663) |
| VGTYP (Transaction Type) | XRT940 (MT940 format) — verify per bank |
| BNKKO (CM Account Name) | `{HBKID}-{HKTID}` — links to T035D DISKB key |
| BUKRS (Company Code) | UNES |

**CRITICAL:** T028B is keyed by **bank key + bank account number**, NOT by house bank ID. The compliance checker must search by BANKL, not HBKID. Without T028B, MT940 files from the bank will not be processed — SAP cannot link the incoming file to the correct cash management account.

**Lesson from UBA01 (2026-04-07):** T035D was configured but T028B was missed. The compliance checker initially reported WARN because it searched T028B by HBKID (wrong field). Fixed to search by BANKL.

### Payment Configuration

| Table | What | Pattern |
|-------|------|---------|
| T018V | Receiving bank clearing | Pmt Method A, Currency, AcctID, Clearing=11xxxxx |
| T042I | Payment bank determination | Pmt Method per bank (3=local check, A=wire), Currency, AcctID, Clearing=11xxxxx |

### YBANK Account Sets (GS02) — Step 10

YBANK sets control which bank G/L accounts appear in cash management reports and bank statement processing. Only **bank accounts (10*)** go into sets — NEVER clearing accounts (11*).

#### The 10 YBANK Sets (SETLEAF, SETCLASS=0000)

| Set Name | Currency | Location | When to Use |
|----------|----------|----------|-------------|
| `YBANK_ACCOUNTS_HQ_USD` | USD | HQ (Paris) | SOG01, SOG03, CIT04, CIT21, BRA01, UNI01 — HQ paying banks |
| `YBANK_ACCOUNTS_HQ_EUR` | EUR | HQ (Paris) | SOG01-EUR, SOG02-EUR, SOG05-EUR, BNP01-EUR, CRA01-EUR, NTB01/NTB02-EUR |
| `YBANK_ACCOUNTS_HQ_OTH` | Other | HQ (Paris) | SOG01-BRL/CHF/GBP/JPY, SOG03 multi-currency, BRA01-BRL |
| `YBANK_ACCOUNTS_FO_USD` | USD | Field Office | **All field office USD bank accounts** (e.g., UBA01-USD01 → GL 1065421) |
| `YBANK_ACCOUNTS_FO_EUR` | EUR | Field Office | Field office EUR bank accounts (rare — most FOs use USD + local) |
| `YBANK_ACCOUNTS_FO_OTH` | Other | Field Office | **All field office local currency accounts** (e.g., UBA01-MZN01 → GL 1065424, ECO09-MZN → GL 1065120) |
| `YBANK_ACCOUNTS_INVEST` | — | Special | Investment/coupon accounts (BKT01, JPS01) |
| `YBANK_ACCOUNTS_UNDP` | — | Special | Inter-agency clearing (UNDP) |
| `YBANK_ACCOUNTS_ALL_USD` | USD | Aggregate | Union of HQ_USD + FO_USD |
| `YBANK_ACCOUNTS_ALL_OTH` | Other | Aggregate | Union of HQ_OTH + FO_OTH |

**Total: 158 entries across 10 sets** (as of 2026-04-08, D01=P01 aligned).

#### Decision Logic: Which Set for a New Bank Account?

```
INPUT: Bank G/L account (10*) + Currency from T012K

Step 1: Is the currency USD?
  YES → Is it an HQ paying bank (T042I exists with method A/J/N/S/X)?
    YES → YBANK_ACCOUNTS_HQ_USD
    NO  → YBANK_ACCOUNTS_FO_USD

Step 2: Is the currency EUR?
  YES → Is it HQ?
    YES → YBANK_ACCOUNTS_HQ_EUR
    NO  → YBANK_ACCOUNTS_FO_EUR

Step 3: Any other currency (MZN, XAF, XOF, CHF, JPY, GBP, etc.)
  Is it HQ?
    YES → YBANK_ACCOUNTS_HQ_OTH
    NO  → YBANK_ACCOUNTS_FO_OTH
```

**Example — UBA01 (Mozambique, FO local disbursement):**
- GL 1065421 (USD01) → currency = USD, field office → `YBANK_ACCOUNTS_FO_USD`
- GL 1065424 (MZN01) → currency = MZN (not USD, not EUR) → `YBANK_ACCOUNTS_FO_OTH`

**Common mistakes:**
- Putting non-EUR currencies (MZN, XAF) into FO_EUR instead of FO_OTH
- Adding clearing accounts (11*) — NEVER add sub-bank G/Ls to YBANK sets
- Forgetting to add the account at all — compliance checker catches this

#### How to Add in GS02

1. Transaction GS02
2. Set name: `YBANK_ACCOUNTS_FO_USD` (or whichever set from decision logic above)
3. Set class: `0000` (G/L accounts)
4. Click "Change"
5. Position at end of value list
6. Add row: VALOPTION = `EQ`, VALFROM = bank G/L number (e.g., `1065421`)
7. Save → assigned to customizing transport request

**Important:** Sets use **exact match (EQ)**, not ranges. Each G/L must be added individually.

#### Transport Process (GRW_SET Workbench Object)

GS02 changes are transported via **GRW_SET workbench transport** (not customizing). The transport carries the **FULL set definition** — it OVERWRITES the target system's set completely.

**Process:**
1. **Before any change:** Verify D01 and P01 sets are already in sync
   - Run `ybank_sets_full_comparison.py` to compare entry-by-entry
   - If out of sync, align first via RFC or manual GS02 in P01
2. **Make changes in D01** via GS02 (add new bank G/L to correct set)
3. **All changes go into ONE transport** — include GS02 in the same customizing transport as the other bank config (T012, T030H, T035D, etc.)
4. **Release transport** — imports to P01, overwrites the full set
5. **Post-import:** Run compliance checker on P01 to verify G/L is in correct set

**Risk:** If P01 has entries that D01 doesn't (e.g., manual P01 additions), the transport will DELETE those P01-only entries. Always sync before transporting.

**Verification scripts:**
- `ybank_sets_full_comparison.py` — entry-by-entry D01 vs P01 comparison
- `ybank_consistency_check.py` — SETHEADER/SETNODE/SETLEAF/SETLINE consistency
- `ybank_setleaf_sync.py` — RFC-based sync P01→D01 (safety rails: D01 target only, batch size 10, 2s throttle)

#### SETHEADER Audit Trail

When syncing via RFC (INSERT into SETLEAF), the SETHEADER audit fields (UPDUSER, UPDDATE, SETLINES count) are NOT automatically updated. The `ybank_setleaf_sync.py` script handles this in Phase 4 by updating SETHEADER after the SETLEAF sync.

### Business Area (YFI_BASU_MOD)

G/L range 1000000-1199999 is covered by Z1 AUTOMATIC BANK STAT / GEF rule. No per-account action needed.

### Payment Medium Formats (OBPM4)

| Format | Usage |
|--------|-------|
| /GGI_XML_CT_UNESCO | All currencies, internal transfers |
| /SEPA_CT_UNES | Euro payments |
| /CITI/XML/UNESCO/DC_V3_01 | USD payments via Citibank |

Variant naming: `UNE_TRE_{CURRENCY}{HBKID}` (e.g., UNE_TRE_EURNTB)

---

## 13-Step Process

> Source: `1 New or changed house bank account steps.pdf` (45 pages, Marlies Spronk)
> This section covers ALL steps from the handover document. Even if a step does not apply
> to a specific bank (e.g., field office banks don't need OBPM4), the step must be
> explicitly evaluated and documented as N/A with reason — never silently skipped.

### Bank Account Types

| Type | Description | Needs Payment Config (9.1-9.3)? |
|------|-------------|-------------------------------|
| Regular FO | Field office payments, outside SAP | NO — no payment method needed |
| Treasury / Paying | HQ banks that run F110 payment proposals | YES — full 9.1 + 9.2 + 9.3 |
| Internal Transfer | Replenishment between UNESCO accounts | YES — 9.2 required |

### ADD — New House Bank Account (13 Steps — Full Detail)

---

**Step 1 — FS00: G/L Account Creation**

| Field | Table | Bank Account (10*) | Clearing Account (11*) |
|-------|-------|--------------------|------------------------|
| Account Number | SKA1.SAKNR | 10xxxxx (e.g., 1065421) | 11xxxxx (e.g., 1165421) — same last 5 digits |
| Account Group | SKA1.KTOKS | **BANK** (never OTHR) | **BANK** |
| Balance Sheet | SKA1.XBILK | X | X |
| Planning Level | SKB1.FDLEV | **B0** (bank) | **B1** (sub-bank) |
| Sort Key | SKB1.ZUAWA | **027** | **Z01** (new banks) or 027 (legacy) |
| Field Status Group | SKB1.FSTAG | **UN03** | **UN03** |
| Line Item Display | SKB1.XKRES | X | X |
| Cash Flow Relevant | SKB1.XGKON | X | X |
| Open Item Mgmt | SKB1.XOPVW | — (empty) | **X** (required for clearing) |
| Post Auto Only | SKB1.XINTB | **— (empty)** | **— (empty)** — empty IS the standard (only 1/353 exceptions) |
| Commitment Item | SKB1.FIPOS | BANK | BANK |
| House Bank | SKB1.HBKID | {HBKID} | {HBKID} |
| Account ID | SKB1.HKTID | {AcctID} | {AcctID} |
| Currency | SKB1.WAERS | From form | Same as bank account |
| Short Text | SKAT.TXT20 | BK {BANK} {CITY} {CUR} | S-BK {BANK} {CITY} {CUR} |
| Long Text | SKAT.TXT50 | BK {BANK NAME} - UNESCO {CITY} {CUR} | S-BK {BANK NAME} - UNESCO {CITY} {CUR} |
| Languages | SKAT.SPRAS | E, F, P (English, French, Portuguese) | E, F, P |

**Form source:** Form AM3-11 (.xls). Field "GL account to use as reference" = existing GL to copy from.
**Who creates:** MD team creates in **P01 first**, then copies to D01/V01.
**Common mistake:** MD team copies from reference GL and forgets to update HBKID/HKTID → wrong house bank assignment. 5 known mismatches in P01.
**Transport:** NOT transported — created directly in each system.
**Checker:** Checks 5-7.

---

**Step 2 — FI12: House Bank Master + Account IDs**

| Field | Table.Field | Value | Source |
|-------|------------|-------|--------|
| Company Code | T012.BUKRS | UNES | Always |
| House Bank | T012.HBKID | 5-char code (e.g., UBA01) | Form: "House Bank" field |
| Bank Country | T012.BANKS | 2-char ISO (e.g., MZ) | Bank letter |
| Bank Key | T012.BANKL | SAP bank key (e.g., SP0000001YCB) | Bank directory (BNKA) |
| Account ID | T012K.HKTID | {CUR}{NN} (e.g., MZN01, USD01) | Form: "Account ID" field |
| Bank Account Number | T012K.BANKN | Physical acct# (e.g., 070040004663) | Bank letter |
| Currency | T012K.WAERS | MZN, USD, EUR, etc. | Form: "Currency" field |
| G/L Account | T012K.HKONT | 10xxxxx (e.g., 0001065421) | Form: "G/L Account number" |
| DME Key | T012K.DTAWS | **B2** (standard) or B4 (DNB01 exception) | PDF standard |
| Description EN | T012T.TEXT1 | "UNESCO {CITY} - {CUR}" | Form: "Account Description" |
| Bank Name | BNKA.BANKA | Full name | Bank letter |
| SWIFT | BNKA.SWIFT | BIC code | Bank letter |

**Transaction:** FI12 via SPRO path.
**Transport:** Customizing request.
**Checker:** Checks 1-4.

---

**Step 3 — FTE_BSM_CUST: Bank Statement Monitor**

**Required for:** EBS_CONFIG and HQ_PAYING banks (form: "Bank statement electronically uploaded?" = Yes).

| Setting | Value |
|---------|-------|
| Process Status | Copy from similar bank |
| Difference Status | Copy from similar bank |
| Serial No. Status | Copy from similar bank |
| Reconciliation Status | Copy from similar bank |
| Interval | 1 Calendar Days |

**Transaction:** FTE_BSM_CUST. Copy from a similar account (same bank type).
**Table:** FCLM_BSM_CUST — NOT readable via RFC (special authorization required).
**Transport:** Customizing request.
**Checker:** Manual verification required (Check 16 — not automated).

---

**Step 4 — OBA1: Exchange Rate Differences (T030H)**

**Required for:** ALL non-USD G/L accounts — both bank (10*) AND clearing (11*). Form trigger: "Account Currency != USD" AND "GL to be revaluated = YES".

**ALL 5 fields must be filled in a single pass** (UBA01 lesson: filling only Realized fields caused 2 correction transports):

| T030H Field | OBA1 Screen Label | CURTP=10 Value | CURTP=30 Value |
|-------------|-------------------|----------------|----------------|
| LKORR | Bal.sheet adj.1 (Correction) | **The account itself** (e.g., 1165424) | — |
| LSREA | Exch.rate diff.realized — Loss | **6045011** | 5022012 |
| LHREA | Exch.rate diff.realized — Gain | **7045011** | 5022012 |
| LSBEW | Valuation — Val.loss 1 | **6045011** | — |
| LHBEW | Valuation — Val.gain 1 | **7045011** | — |

**Two currency type entries per account:** CURTP=10 (foreign currency) + CURTP=30 (presentation currency).

**What each section does:**
- **Realized (LSREA/LHREA):** When an open item is cleared at a different exchange rate → book the realized FX gain/loss
- **Valuation (LSBEW/LHBEW):** Month-end FAGL_FC_VAL revalues balances at closing rate → unrealized FX gain/loss (reversed next period). **WITHOUT THIS: FAGL_FC_VAL silently skips the account**
- **Correction (LKORR):** Offsetting entry for balance sheet adjustment. **WITHOUT THIS: SAP cannot complete the posting at all**

**Transport:** Customizing request. Include in SAME transport as other config.
**Checker:** Check 9.

---

**Step 5 — SM30 V_T035D: Cash Management Account Name**

| T035D Field | Value | Source |
|-------------|-------|--------|
| BUKRS | UNES | Always |
| DISKB | `{HBKID}-{HKTID}` (e.g., UBA01-MZN1) | **Constructed from T012K account ID** — NOT currency code |
| BNKKO | Bank G/L (10xxxxx) (e.g., 0001065424) | From T012K.HKONT |
| TEXTL | Description (e.g., "UNESCO MAPUTO - MZN") | Free text |

**DISKB key construction:** `{HBKID}-{HKTID}` where HKTID = T012K account ID. Example: UBA01 with account MZN01 → DISKB = UBA01-MZN1. DISKB naming may use shortened form (MZN1 vs MZN01) — verify against T012K.

**Transaction:** SM30 → V_T035D (also accessible via SPRO path for EBS config).
**Transport:** Customizing request.
**Checker:** Check 10 (validates DISKB exists per bank G/L via BNKKO match).

---

**Step 6 — SM30 V_T035D: EBS Integration (T035D + T028B)**

**Two parts in the same SPRO screen — both required for EBS to work:**

**Part (a): T035D — Account Symbols → G/L mapping** (same screen as step 5, different dialog node)

Already covered in step 5. Verify the DISKB→BNKKO mapping is correct.

**Part (b): T028B — Bank Accounts → Transaction Types**

| T028B Field | Value | Source |
|-------------|-------|--------|
| BANKL | Bank key from T012 (e.g., SP0000001YCB) | **NOT HBKID** — this is the bank directory key |
| KTONR | Physical bank account number (e.g., 070040004663) | From T012K.BANKN |
| VGTYP | Statement format: **XRT940** (default MT940), TR_TRNF (HQ treasury), SOG_FR (SocGen custom) | Confirm with bank team |
| BNKKO | DISKB key (e.g., UBA01-MZN1) | Links to T035D.DISKB — **must match exactly** |

**CRITICAL:** T028B is keyed by **BANKL + KTONR** (bank key + physical account number), NOT by HBKID. UBA01 lesson: compliance checker initially missed T028B because it searched by HBKID.

**Without T028B:** MT940 files arriving from the bank cannot be processed — SAP cannot link the incoming file to the correct cash management account.

**Transaction:** SM30 → V_T035D (second dialog node in same view).
**Transport:** Customizing request.
**Checker:** Checks 11-12.

---

**Step 7 — YFI_BASU_MOD: Business Area Substitution**

**Usually N/A.** G/L range 1000000-1199999 is covered by Z1 AUTOMATIC BANK STAT / GEF rule. No per-account action needed.

Only add specific entries for:
- IIEP: 10* accounts → Business Area **PDK**, 11* accounts → **PAR**
- UBO: 10* accounts → **PFF**

All other banks (including UBA01) are auto-covered by the wildcard range.

---

**Step 8 — SM30 V_T018V: Receiving Bank Clearing**

**Required for:** Accounts that receive wire transfer payments (method A).

| T018V Field | Value | Source |
|-------------|-------|--------|
| BUKRS | UNES | Always |
| HBKID | {HBKID} (e.g., UBA01) | From T012 |
| HKTID | {AcctID} (e.g., USD01) | From T012K — usually only USD account needs T018V |
| ZLSCH | **A** (wire transfer) | Standard payment method for incoming |
| WAERS | Currency (e.g., USD) | From T012K.WAERS |
| GEHVK | Clearing G/L (11xxxxx) (e.g., 0001165421) | Derived from bank G/L: 10→11 |

**Not USD-only:** T018V covers multi-currency (69% USD, 20% EUR, 11% other: CHF/JPY/GBP/DKK/CAD/AUD/ZWG/HTG). SOG03 alone has 6 non-USD entries.

**Transport:** Customizing request.
**Checker:** Check 13.

---

**Step 9.1 — FBZP / T042I: Payment Bank Determination (Paying Banks Only)**

**Required for:** HQ_PAYING and FO_LOCAL banks only. Skip for EBS_CONFIG-only banks.

Three sub-configurations in FBZP:

| Sub-config | Table | Fields | Notes |
|------------|-------|--------|-------|
| (a) T042I basic | T042I | ZBUKR=UNES, ZLSCH=pay method, HBKID, HKTID, WAERS | Pay methods: A=wire, 3=local check, C/J/N/S/X=specific |
| (b) Bank Accts Enhanced | — | Sub-account (11*), ranking order | For failover when primary balance is insufficient |
| (c) Available Amounts | — | Daily/total limits per currency | Prevents overdraft on payment run |

**ECO09 example (FO_LOCAL):** T042I method=3 (local check), MZN01, NO T042A (correct — pays locally by check, no DMEE file needed). ECO09 missing from T042A is INTENTIONAL.

**Transport:** Customizing request.
**Checker:** Check 14.

---

**Step 9.2 — SPRO: Account Determination for G/L Account Payments**

**Required for:** HQ_PAYING banks and banks with "Replenishment Settings? = Yes".

SPRO path: Bank Accounting → Payment Transactions → Payment Handling → Bank Clearing Account Determination → Define Account Determination.

Add entry: payment method A + correct currency + clearing G/L (11xxxxx).

**Transport:** Customizing request.

---

**Step 9.3 — SE38 + OBPM4: Payment Medium Format Variants (HQ Paying Only)**

**Required for:** HQ_PAYING banks that generate DMEE payment files via F110. NOT needed for FO_LOCAL (ECO09 pays by check).

| DMEE Format | Usage | Variant Naming |
|-------------|-------|----------------|
| /GGI_XML_CT_UNESCO | All currencies, internal transfers | UNE_TRE_{CUR}{HBKID} |
| /SEPA_CT_UNES | Euro payments (SEPA) | UNE_TRE_EUR{HBKID} |
| /CITI/XML/UNESCO/DC_V3_01 | USD payments via Citibank | UNE_TRE_USD{HBKID} |

**Process:** (1) SE38 → SAPFPAYM → copy existing variant → change house bank/currency/account in dynamic selections. (2) OBPM4 → link variant to house bank under correct Payment Medium Format.

**CRITICAL:** Must be done in **V01 AND P01** — NOT transportable. Without this, F110 generates no payment file.

**Checker:** Check 18 (manual verification).

---

**Step 10 — GS02: YBANK Account Sets**

**Required for:** ALL bank types. Add bank G/L (10* only, NEVER 11*) to correct YBANK set.

**Decision logic — which set:**

| Account Currency | Bank Location | YBANK Set to Use |
|-----------------|---------------|-----------------|
| USD | Field Office | `YBANK_ACCOUNTS_FO_USD` |
| USD | HQ (paying) | `YBANK_ACCOUNTS_HQ_USD` |
| EUR | Field Office | `YBANK_ACCOUNTS_FO_EUR` |
| EUR | HQ | `YBANK_ACCOUNTS_HQ_EUR` |
| Other (MZN, XAF, XOF, CHF, JPY, GBP...) | Field Office | `YBANK_ACCOUNTS_FO_OTH` |
| Other | HQ | `YBANK_ACCOUNTS_HQ_OTH` |

**UBA01 example:** GL 1065421 (USD01) → `FO_USD`. GL 1065424 (MZN01) → `FO_OTH`.

**How to add:** GS02 → set name → set class 0000 → Change → add row: VALOPTION=EQ, VALFROM={bank GL number}. Uses **exact match (EQ)**, not ranges — each GL added individually.

**Transport:** GRW_SET workbench object — carries **FULL set** (overwrites target). D01 and P01 must be aligned BEFORE transport. Include in same transport as other config — do NOT create separate transport.

**Checker:** Check 15 (validates G/L found in correct set by currency).

---

**Step 11 — ~~TRM5: Cash Position Reports~~ — ELIMINATED**

**NO LONGER REQUIRED** as of 2026-04-07. Previously involved Report Painter forms (ZCASH/ZCASHFO/ZCASHFODET) with G/L pairs + formula updates. Do NOT perform for new banks.

---

**Step 12 — SM30 V_T038: Statement Grouping**

**Usually N/A.** Grouping uses wildcards `+++10++0++` and `+++11++9++` that auto-cover all bank/clearing G/Ls in the 10*/11* range. Per-account action only for exceptions (e.g., GL 1068713/1168713 added individually).

---

**Step 13 — FI12 / TIBAN: IBAN Generation**

Generate IBAN from bank account details. Requires bank letter with IBAN or IBAN can be derived from country+bank key+account number.

**Transport:** Workbench transport (separate from customizing by nature).
**Checker:** Check 8.

### CLOSE — House Bank Account

House banks are **NEVER deleted**. The closure process:

| Step | Action |
|------|--------|
| 2 | FI12: Add "CLOSED" to description, put alternative account number |
| 3 | FTE_BSM_CUST: Remove entry |
| 4 | OBA1: Remove entry |
| 5 | Cash Mgmt Account Name: Remove entry |
| 6 | T035D: Remove entry |
| 7 | YFI_BASU_MOD: No action (range-based) |
| 8 | T018V: Remove entry |
| 9.1 | T042I: Remove (if exists). |
| 9.2 | Account Determination: Not available to remove (per PDF). |
| 9.3 | OBPM4: Do not remove (risk — "Not executed as per doubt and risk" per PDF). |
| 10 | GS02: Remove bank G/L (10*) from YBANK set. Transport carries FULL set (GRW_SET) — risk of overwriting target. Align D01↔P01 before transport. |
| 11 | ~~TRM5~~: No longer required (2026-04-07). |

### MODIFY — Existing Account

#### Scenario: Account Name / Description Change

**When:** Treasury renames an account (e.g., NTB01/USD02 "PFF GTF" → "CASH POOL").

**Tables affected:**

| Table | What Changes | Transaction | Transport |
|-------|-------------|-------------|-----------|
| T012T | Account description text (TEXT1) | FI12 | Customizing (VC_T012N) |
| T035D | Cash management text (TEXTL) — if DISKB entry exists | SM30 V_T035D | Customizing (V_T035D) |
| T035U | T035D text table — language-dependent text for DISKB | SM30 V_T035D | Customizing |
| SKAT | G/L account texts (TXT20/TXT50) — if GL name also changes | FS00 | MD team in P01 |

**What does NOT change:** T012K (bank account number, currency, GL mapping), SKA1/SKB1 (GL master data), T030H (OBA1), T028B (EBS format mapping), T042I (payment determination), SETLEAF (YBANK sets).

**Steps for a name-only change:**
1. FI12: Change T012T text (all 3 languages: E, F, P)
2. SM30 V_T035D: Update T035D.TEXTL if DISKB entry exists (also updates T035U)
3. If G/L account long text also needs updating: FS00 → SKAT (MD team in P01)
4. Create ONE customizing transport with T012T + T035D changes
5. Release to P01

**Real example — Transport D01K9B0F5U (2026-04-08):**
- Bank: NTB01 (Northern Trust)
- Account: USD02 (bank account 17-18206, GL 1095021)
- Change: T012T text "UNESCO PFF GTF" → "UNESCO CASH POOL" (English)
- Also: T035D DISKB=NTB01-USD1 entry added (was missing in P01 — a gap fix bundled with the rename)
- Tables in transport: T012K, T012T, T035D, T035U
- French/Portuguese texts: should also be updated to match English rename

**Lesson:** Name changes often reveal config gaps. NTB01 had no T035D entries in P01 at all — this was a pre-existing EBS gap that was only noticed during the rename. Always check T035D when touching any account config.

#### Other Common Modifications

| Change | Tables | Transaction | Notes |
|--------|--------|-------------|-------|
| New IBAN | TIBAN | FI12 | Regenerate IBAN. Workbench transport |
| Address change | BNKA | FI12 | Bank street/city/postal code. Customizing transport |
| Bank account number change | T012K.BANKN, T028B.KTONR | FI12 + SM30 V_T035D | Also update T028B (EBS key uses BANKN). Rare — usually means bank reissued the account |
| Currency change | — | — | Rare. Usually requires NEW account ID (new T012K entry + new GL pair). Cannot change currency on existing GL |
| SWIFT/BIC change | BNKA.SWIFT | FI12 | Update bank directory. May affect T028B.BANKL if bank key changes |

---

## Pre-Close Checklist (before declaring ANY config complete)

Run these checks BEFORE writing the report or updating companions. Do NOT skip.

```
1. python house_bank_compliance_checker.py D01 {HBKID}     → must be 0 FAIL
2. python house_bank_compliance_checker.py P01 {HBKID}     → must be 0 FAIL
3. python uba01_3system_comparison.py                       → must show ALL IDENTICAL
4. grep -r "{HBKID}" companions/                           → update EVERY companion that mentions this bank
5. grep -r "{HBKID}" knowledge/                            → update EVERY report that mentions this bank
```

If step 4 or 5 finds stale references, fix them BEFORE closing. A closed report with stale data in another file is not closed.

---

## Compliance Checker

### Usage (CLI arguments — no file editing needed)

**Script:** `Zagentexecution/mcp-backend-server-python/house_bank_compliance_checker.py`

```bash
# Single system
python house_bank_compliance_checker.py D01 UBA01
python house_bank_compliance_checker.py P01 NTB01

# Both D01 and P01 in one run
python house_bank_compliance_checker.py D01 UBA01 --both
```

**Checks performed (18 checks — maps 1:1 to the 13-step process):**

| # | Step | Table | What |
|---|------|-------|------|
| 1 | 2 | T012 | House bank exists |
| 2 | 2 | BNKA | Bank directory (name, address, SWIFT) |
| 3 | 2 | T012K | Bank accounts (auto-discovers AcctIDs, derives clearing G/Ls) |
| 4 | 2 | T012T | Account descriptions |
| 5 | 1 | SKA1 | KTOKS=BANK, XBILK=X |
| 6 | 1 | SKB1 | FDLEV, ZUAWA, XOPVW, HBKID, FSTAG, XKRES, XGKON, FIPOS, XINTB |
| 7 | 1 | SKAT | Texts exist (E/F/P languages) |
| 8 | 13 | TIBAN | IBAN entries |
| 9 | 4 | T030H | OBA1 exchange rate config — ALL 3 sections (Realized + Valuation + Correction) |
| 10 | 5 | Cash Mgmt | Cash management account names (V_T035D) |
| 11 | 6a | T035D | Electronic bank statement — account symbol assignment |
| 12 | 6b | T028B | Electronic bank statement — bank accounts to transaction types |
| 13 | 8 | T018V | Receiving bank clearing accounts |
| 14 | 9.1 | T042I | Payment bank determination (if paying bank) |
| 15 | 10 | SETLEAF | YBANK account sets (GS02) |
| 16 | 3 | FCLM_BSM_CUST | FTE_BSM_CUST bank statement monitor entries |
| 17 | 9.2 | Acct Determination | G/L Account Payments — internal transfer config |
| 18 | 9.3 | SAPFPAYM/OBPM4 | Payment file variant exists and linked (if paying bank) |

**Output:** PASS / FAIL / WARN per check, summary count, fail item list.

### Cross-System Comparison (D01 vs P01)

**Script:** `Zagentexecution/mcp-backend-server-python/uba01_final_report.py`

Extracts ALL configuration from both systems and compares field-by-field. Detects:
- Missing accounts in either system
- Wrong HBKID assignment (e.g., G/L pointing to old bank)
- Configuration that exists in D01 but not yet in P01 (pre-transport)
- Pattern violations (FDLEV, ZUAWA, XOPVW mismatches)

### How to Generate a Configuration Report

1. Parse the email and Excel forms to extract requested values
2. Run compliance checker against D01: `python house_bank_compliance_checker.py`
3. Run cross-system comparison: `python uba01_final_report.py` (rename for new bank)
4. Generate report with:
   - Request summary (from forms)
   - Per-step status (D01 + P01)
   - Issues found with severity
   - Remaining tasks checklist
   - Transport request status

---

## Transport Strategy — Target: 3 Transports Max

### Lesson from UBA01 (2026-04-07): 6 transports for 1 bank is excessive

UBA01 generated 6 transports because OBA1 was configured incorrectly 3 times (learning by trial and error) and GS02 sets were done as an afterthought:

| # | Transport | Description | Should Have Been |
|---|-----------|-------------|-----------------|
| D01K9B0F56 | C — New house bank and accounts | OK — initial config | Combined into 1 |
| D01K9B0F59 | C — New mozambike bank OBA1 | Incomplete T030H | Combined into 1 |
| D01K9B0F5B | C — OBA1 Correction | Still wrong | Unnecessary if done right |
| D01K9B0F5F | C — Sets YBANK | Late addition | Combined into 1 |
| D01K9B0F5K | C — OBA1 Correction #2 | Finally correct | Unnecessary if done right |
| D01K9B0F58 | W — IBAN New bank | Separate by nature | OK |

### Target for Next Bank: 3 Transports

| # | Type | Content | Rule |
|---|------|---------|------|
| 1 | **C (Customizing)** | ALL config in ONE request: T012/T012K/T012T + T030H (OBA1 — all 5 fields!) + T035D + T028B + T018V + T042I + SETLEAF (GS02) | **Do NOT release until compliance checker shows 0 FAIL** |
| 2 | **W (Workbench)** | IBAN (TIBAN) | Separate by nature — workbench object |
| 3 | **C (optional)** | Only if TRS requests post-config changes | Should be rare |

### How to Avoid Rework Transports

1. **Run compliance checker BEFORE creating transport** — fix all FAIL items first
2. **OBA1 (T030H):** Fill ALL 5 fields in one pass: LKORR + LSREA + LHREA + LSBEW + LHBEW. Use the template from this skill, not trial and error
3. **GS02 sets:** Add to same customizing transport — not a separate request
4. **Verify in D01 with checker** → fix → THEN release to P01. Never release a transport you haven't verified

**G/L accounts** (Step 1) are created by MD team in PRD and copied to D01/V01 — separate process.

**GS02 sets** (Step 10) are transported via GRW_SET workbench object. The transport carries the **full set** (not delta), so D01 and P01 must be aligned before the first transport. Run `ybank_sets_full_comparison.py` to verify alignment. Established 2026-04-07 with transport D01K9B0F5F.

**TRM5 reports** (Step 11) — **NO LONGER REQUIRED** as of 2026-04-07.

**OBPM4 variants** (Step 9c) must be created in V01 AND P01 — not transportable. Without this, F110 produces no payment file. CRITICAL for paying banks.

---

## Common Issues and Pitfalls

| Issue | Cause | Detection | Fix |
|-------|-------|-----------|-----|
| SETHEADER audit stale after RFC sync | RFC INSERT into SETLEAF doesn't update SETHEADER (UPDUSER/UPDDATE/SETLINES) | SETHEADER probe shows old user/date | UPDATE SETHEADER in same RFC batch — `ybank_setleaf_sync.py` Phase 4 does this automatically |
| HBKID wrong in P01 | MD team copies reference G/L and keeps old HBKID | Cross-system SKB1 comparison | FS00 in P01 |
| KTOKS = OTHR instead of BANK | Created with wrong account group | SKA1 check | FS00 change account group |
| XOPVW missing on sub-bank | Not set during creation | SKB1 check | FS00 change |
| OBA1 missing for non-USD clearing | Skipped during config | T030H check | OBA1 add entry |
| IBAN not generated | Forgotten step | TIBAN check | FI12 IBAN generation |
| YBANK set missing | Forgotten or assumed range-based | SETLEAF check | GS02 manual add |
| T018V missing | Clearing account not configured | T018V check | SM30 V_T018V |
| OBPM4 not in V01/P01 | Only created in D01 | Manual check | Create in V01 + P01 |
| Bank address outdated in BNKA | BNKA from old bank directory entry | BNKA vs form comparison | Update via FI12 |

---

## Two-System Rule

| System | Role | What to Do |
|--------|------|-----------|
| D01 | Development | All configuration steps 2-13. Test and validate. |
| P01 | Production | G/L accounts created here first (Step 1). Config arrives via transport. Fix HBKID if wrong. GS02/TRM5 maintained manually. |
| V01 | Pre-production | OBPM4 variants created here. Transport testing. |

---

## File Organization

```
UNESCO/DBS Team - FAM/Documentation/Handover FI/Day-by-Day/House Bank/
├── 1 New or changed house bank account steps.pdf    (45-page master procedure)
├── 1 New or changed house bank account steps.docx   (editable)
├── 3 Steps 08182025.xlsx                             (tracking template)
└── {YEAR}/
    └── {Email Subject}/
        ├── {HBKID}-{AcctID}.xls                     (house bank forms)
        ├── Form AM3-11 - {GL}-{HBKID}-{AcctID}.xls  (G/L forms)
        ├── {Bank Letter}.pdf                          (bank confirmation)
        └── CONFIGURATION_REPORT.md                    (generated report)
```

---

## Related Skills & Companions

| Skill / Companion | Relationship | How Connected |
|-------------------|-------------|---------------|
| `sap_account_comparison` | Compare and adjust G/L accounts between D01 and P01 | SKA1/SKB1/SKAT field validation |
| `sap_master_data_sync` | Bulk sync missing G/L accounts P01 → D01 | INSERT/UPDATE via RFC |
| `sap_payment_bcm_agent` | Full payment domain (F110, BCM, FBZP, DMEE) | T042I bank determination feeds F110 payment runs |
| `sap_bank_statement_recon` | Bank statement E2E (MT940 import, EBS posting, FEBAN) | T035D+T028B config enables EBS; 11* sub-bank accounts are cleared in FEBAN |
| `sap_company_code_copy` | EC01 company code copy (includes house bank setup) | New company codes need house banks |
| **payment_bcm_companion.html** | Payment domain companion (796KB) | Shows F110→BCM→DMEE flow that uses house bank config |
| **bank_statement_ebs_companion.html** | Bank statement companion (84KB) | Shows MT940→EBS→clearing flow that depends on T035D+T028B |
| **epiuse_companion.html** | EpiUse companion (32KB) | Bank account data migration |

## End-to-End Flow: How House Bank Config Connects

```
REQUEST (Email + Forms)
    │
    ▼
STEP 1: G/L Accounts (FS00) ──────────────────────────────┐
    │  SKA1 + SKB1 + SKAT                                  │
    │  Bank (10*) + Sub-bank (11*)                         │
    ▼                                                       │
STEP 2: House Bank (FI12) ─────────────────────────────┐   │
    │  T012 + T012K + BNKA                              │   │
    ▼                                                    │   │
STEP 4: OBA1 (T030H) ──── FX Revaluation ─────────┐   │   │
    │  Non-USD clearing accounts only               │   │   │
    ▼                                                │   │   │
STEP 6: EBS Config ────── Bank Statement Flow ──┐  │   │   │
    │  T035D (symbol→GL) + T028B (bankkey→type) │  │   │   │
    │                                            │  │   │   │
    │  MT940 file arrives from bank              │  │   │   │
    │  → T028B maps bank key + acct to format   │  │   │   │
    │  → T035D maps to G/L account              │  │   │   │
    │  → Posts to 10* bank account              │  │   │   │
    │  → Clears against 11* sub-bank (FEBAN)    │  │   │   │
    ▼                                            │  │   │   │
STEP 8-9: Payment Config ── Payment Flow ───┐   │  │   │   │
    │  T018V (receiving clearing)            │   │  │   │   │
    │  T042I (F110 bank determination)       │   │  │   │   │
    │                                        │   │  │   │   │
    │  F110 payment run                      │   │  │   │   │
    │  → T042I selects house bank + account  │   │  │   │   │
    │  → Posts to 11* clearing account       │   │  │   │   │
    │  → OBPM4 generates payment file (XML)  │   │  │   │   │
    │  → Bank processes payment              │   │  │   │   │
    │  → MT940 confirms → EBS posts back     │   │  │   │   │
    ▼                                        ▼   ▼  ▼   ▼   ▼
STEP 10: GS02 Sets ───── Treasury Reporting
    │  YBANK_ACCOUNTS_* hierarchy
    │  → Average Balance Interest Calc
    │  → Cash Position (ZCASH/ZCASHFO)
    │  → Treasury dashboard
    ▼
OPERATIONAL: Bank account is LIVE
```

---

## Session Log

| Date | Bank | Action | Result |
|------|------|--------|--------|
| 2026-04-07 | UBA01 (UBA Mozambique) | Full creation + compliance check | Session #043: 27 PASS / 1 FAIL / 3 WARN. P01 HBKID wrong on 4 accounts. |
| 2026-04-07 | UBA01 (UBA Mozambique) | Session #044: Full PDF review + D01/P01 cross-check + Gold DB pattern discovery | D01: 30 PASS / 0 FAIL / 2 WARN. P01: 28 PASS / 2 FAIL / 2 WARN. GS02 aligned and transported (D01K9B0F5F). **Gold DB analysis of ALL 211 banks:** 117 closed, 67 active (2 PAYING, 56 EBS_CONFIG, 9 BASIC). 7 patterns discovered (P1-P7). T018V=USD-only pattern confirmed (not a gap). XINTB=empty is production standard (ECO09 was outlier). Form field→bank type decision flow documented. SKILL.md rewritten: 18 checks, full form fields, step requirement matrix, known issues from audit. Extracted T030H(1014), T035D(151), T018V(108), T012T(1049) into Gold DB. |
