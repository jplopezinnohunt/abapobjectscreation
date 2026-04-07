---
name: SAP House Bank Configuration (Create / Modify / Close)
description: >
  End-to-end house bank configuration for UNESCO SAP (company code UNES).
  Covers 13 configuration steps across FS00, FI12, FBZP, OBA1, GS02, TRM5,
  electronic bank statement, cash management, and payment program.
  Includes automated compliance checker, cross-system comparison (D01 vs P01),
  and ECO09-proven configuration patterns.
  Discovered Session 2026-04-07 from 45-page handover procedure + real UBA01 config.
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

## Account Structure

Every house bank account creates a **pair** of G/L accounts:

| Type | Range | Prefix | Purpose | Example |
|------|-------|--------|---------|---------|
| Bank account | 10xxxxx | BK | Main bank account, receives postings | 1065421 |
| Sub-bank / clearing | 11xxxxx | S-BK | Clearing for payments, reconciliation | 1165421 |

The last 5 digits are always the same between the pair. Some banks have 4 G/L accounts (10*, 11*, 12*, 13*).

## Configuration Patterns (from ECO09 benchmark)

These patterns were discovered by extracting the full configuration of ECO09 (Ecobank Maputo) from P01 production and validated across multiple house banks.

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
| XINTB (Post Auto Only) | X | X |
| XOPVW (Open Item Management) | **—** | **X** |
| FIPOS (Commitment Item) | BANK | BANK |
| HBKID (House Bank) | {HBKID} | {HBKID} |
| HKTID (Account ID) | {AcctID} | {AcctID} |

**Key differences between bank and sub-bank:**
- FDLEV: B0 (bank) vs B1 (sub-bank)
- ZUAWA: 027 vs Z01
- XOPVW: empty vs X (Open Item Management only on sub-bank)

### House Bank Master (FI12)

| Field | Rule |
|-------|------|
| DME Instruction Key | **B2** (except DNB01 = B4) |
| Bank Country | From bank confirmation letter |
| Bank Key | SAP bank directory key for the bank |
| SWIFT | From bank confirmation letter |

### OBA1 — Exchange Rate Differences (T030H)

**Rule:** Only **non-USD clearing accounts (11xxxxx)** strictly need entries.

| Account Type | Currency | T030H Entry Needed? |
|-------------|----------|-------------------|
| Bank (10*) | USD | No |
| Bank (10*) | Non-USD | Optional (conservative) |
| Sub-bank (11*) | USD | No |
| Sub-bank (11*) | Non-USD | **YES — Required** |

When creating entries, ALL 3 sections must be filled (not just Realized):

| T030H Field | OBA1 Screen Field | Value |
|-------------|------------------|-------|
| CURTP | Currency Type | 10 |
| LKORR | Bal.sheet adj.1 / Correction acct | **The account itself** (e.g., 1165424) |
| LSREA | Exchange rate diff realized — Loss | 6045011 |
| LHREA | Exchange rate diff realized — Gain | 7045011 |
| LSBEW | Valuation — Val.loss 1 | 6045011 |
| LHBEW | Valuation — Val.gain 1 | 7045011 |

**CRITICAL:** Do NOT skip the Valuation section (LSBEW/LHBEW) or LKORR. Missing these causes incomplete FX revaluation during month-end closing. The OBA1 screen has 3 sections — all must be filled.

**Lesson from UBA01 (2026-04-07):** Initial configuration only filled LSREA/LHREA (Realized section). LKORR, LSBEW, LHBEW were blank. Discovered by comparing against ECO09 reference field-by-field. Fixed via RFC update.

### Electronic Bank Statement (T035D + T028B)

EBS configuration has **two tables** in the same SPRO screen — both must be configured:

**T035D — Account Symbol to G/L mapping (dialog node: various)**

| Field | Pattern |
|-------|---------|
| DISKB (CM Account Name) | `{HBKID}-{CUR}1` (e.g., UBA01-USD1) |
| BNKKO (G/L Account) | The bank account (10xxxxx) |

**T028B — Bank Accounts to Transaction Types (dialog node: last one)**

| Field | Pattern |
|-------|---------|
| BANKL (Bank Key) | From T012 (e.g., SP0000001YCB) |
| KTONR (Bank Account Number) | From T012K.BANKN (e.g., 070040004663) |
| VGTYP (Transaction Type) | XRT940 (MT940 format) — verify per bank |
| BNKKO (CM Account Name) | `{HBKID}-{CUR}1` — links to T035D |
| BUKRS (Company Code) | UNES |

**CRITICAL:** T028B is keyed by **bank key + bank account number**, NOT by house bank ID. The compliance checker must search by BANKL, not HBKID. Without T028B, MT940 files from the bank will not be processed — SAP cannot link the incoming file to the correct cash management account.

**Lesson from UBA01 (2026-04-07):** T035D was configured but T028B was missed. The compliance checker initially reported WARN because it searched T028B by HBKID (wrong field). Fixed to search by BANKL.

### Payment Configuration

| Table | What | Pattern |
|-------|------|---------|
| T018V | Receiving bank clearing | Pmt Method A, Currency, AcctID, Clearing=11xxxxx |
| T042I | Payment bank determination | Pmt Method per bank (3=local check, A=wire), Currency, AcctID, Clearing=11xxxxx |

### YBANK Account Sets (GS02)

| Currency | Set Name |
|----------|----------|
| USD | YBANK_ACCOUNTS_FO_USD (field office) or YBANK_ACCOUNTS_HQ_USD (HQ) |
| EUR | YBANK_ACCOUNTS_HQ_EUR or YBANK_ACCOUNTS_FO_EUR |
| Other | YBANK_ACCOUNTS_FO_OTH or YBANK_ACCOUNTS_HQ_OTH |

**Important:** Sets use exact match (EQ), not ranges. Each G/L must be added individually. Maintained manually in each system (D01, V01, P01).

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

### ADD — New House Bank Account

| Step | Transaction | Table | Description | Transport |
|------|------------|-------|-------------|-----------|
| 1 | FS00 | SKA1, SKB1, SKAT | Create G/L accounts (bank + sub-bank pairs) | MD team in PRD |
| 2 | FI12 (SPRO) | T012, T012K, T012T | Create house bank + account IDs | Customizing |
| 3 | FTE_BSM_CUST | FCLM_BSM_CUST | Add to bank statement monitor | Customizing |
| 4 | OBA1 | T030H | Add exchange rate diff (non-USD clearing only) | Customizing |
| 5 | SPRO | FDSB | Add cash management account name | Customizing |
| 6 | SM30 V_T035D | T035D, T028B | Add to electronic bank statement integration | Customizing |
| 7 | YFI_BASU_MOD | Custom | Business area substitution (verify range covers) | N/A |
| 8 | SM30 V_T018V | T018V | Add receiving account for payment requests | Customizing |
| 9a | FBZP / V_T042IY0 | T042I | Bank determination for payment (if paying bank) | Customizing |
| 9b | SPRO | — | Add to payment method (internal transfer) | Customizing |
| 9c | SE38 + OBPM4 | — | Create SAPFPAYM variant + link (if paying bank) | V01 + P01 |
| 10 | GS02 | SETLEAF | Add to YBANK account sets | Manual per system |
| 11 | TRM5 | — | Add to cash position reports (after TRS confirmation) | Customizing |
| 12 | SM30 V_T038 | T038 | Verify grouping (usually N/A — pattern-based) | N/A |
| 13 | FI12 / TIBAN | TIBAN | Generate IBAN | Workbench |

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
| 9 | T042I: Remove (if exists). OBPM4: Do not remove (risk). |
| 10 | GS02: Remove from YBANK sets (transport risk — different config in DS1/PS1) |
| 11 | TRM5: Remove from cash position reports + update formulas |

### MODIFY — Existing Account

Common modifications:
- New IBAN: Update in FI12, regenerate TIBAN
- Address change: Update BNKA via FI12
- Currency change: Rare — may require new account ID

---

## Compliance Checker

### Single-System Check

**Script:** `Zagentexecution/mcp-backend-server-python/house_bank_compliance_checker.py`

```python
# Change these 4 constants to check any house bank
SYSTEM = "D01"    # D01 or P01
BUKRS  = "UNES"
KTOPL  = "UNES"
HBKID  = "UBA01"  # Any house bank ID
```

**Checks performed (15 checks):**

| # | Table | What |
|---|-------|------|
| 1 | T012 | House bank exists |
| 2 | BNKA | Bank directory (name, address, SWIFT) |
| 3 | T012K | Bank accounts (auto-discovers AcctIDs, derives clearing G/Ls) |
| 4 | T012T | Account descriptions |
| 5 | SKA1 | KTOKS=BANK, XBILK=X |
| 6 | SKB1 | FDLEV, ZUAWA, XOPVW, HBKID, FSTAG, XKRES, XGKON, FIPOS |
| 7 | SKAT | Texts exist (E/F/P languages) |
| 8 | TIBAN | IBAN entries |
| 9 | T030H | OBA1 exchange rate config (non-USD clearing required) |
| 10 | FDSB | Cash management account names |
| 11 | T035D | Electronic bank statement assignment |
| 12 | T028B | Bank statement posting rules |
| 13 | T018V | Receiving bank clearing accounts |
| 14 | T042I | Payment bank determination |
| 15 | SETLEAF | YBANK account sets (GS02) |

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

## Transport Requests

Every house bank configuration generates **2 transport requests**:

| Type | Content | Created When |
|------|---------|-------------|
| Customizing | T012, T012K, T012T, T035D, T018V, T042I, FTE_BSM_CUST, OBA1, Cash Mgmt | Steps 2-9 |
| Workbench | IBAN generation | Step 13 |

**G/L accounts** (Step 1) are created by MD team in PRD and copied to D01/V01 — separate process.

**GS02 sets** (Step 10) are maintained manually per system — no transport.

**TRM5 reports** (Step 11) generate their own transport when saved.

**OBPM4 variants** (Step 9c) must be created in V01 AND P01 — not transportable.

---

## Common Issues and Pitfalls

| Issue | Cause | Detection | Fix |
|-------|-------|-----------|-----|
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

## Related Skills

| Skill | Relationship |
|-------|-------------|
| `sap_account_comparison` | Compare and adjust G/L accounts between D01 and P01 |
| `sap_master_data_sync` | Bulk sync missing G/L accounts P01 → D01 |
| `sap_payment_bcm_agent` | Full payment domain (F110, BCM, FBZP, DMEE) |
| `sap_bank_statement_recon` | Bank statement E2E (MT940 import, EBS posting, FEBAN) |
| `sap_company_code_copy` | EC01 company code copy (includes house bank setup) |

---

## Session Log

| Date | Bank | Action | Result |
|------|------|--------|--------|
| 2026-04-07 | UBA01 (UBA Mozambique) | Full creation + compliance check | 27 PASS / 1 FAIL / 3 WARN. P01 HBKID wrong on 4 accounts. |
