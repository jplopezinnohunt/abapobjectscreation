# House Bank Configuration — Support & Maintenance Procedure

> **Domain:** FI — Bank Accounting  
> **Category:** Support & Maintenance (S&M)  
> **Source:** Handover documentation + real configuration examples (NTB02/EUR02, Sogebank Haiti)  
> **Last Updated:** 2026-04-07  
> **Owner:** DBS Team — FAM  

---

## 1. Process Overview

House bank configuration is a **multi-step, cross-module** SAP configuration activity triggered when UNESCO opens a new bank account or closes an existing one. It touches:

- **G/L Accounting** (FS00)
- **Bank Accounting** (FI12 / SPRO)
- **Cash Management** (TRM5, GS02)
- **Payment Program** (FBZP / OBPM4)
- **Bank Statement Processing** (FTE_BSM_CUST, V_T035D)
- **Business Area Substitution** (YFI_BASU_MOD)

### Two Types of Bank Accounts
| Type | Description | Payment Method Needed? |
|------|-------------|----------------------|
| **Regular / Field Office** | Field office payments, outside SAP | No |
| **Treasury** | Internal bank accounts only, no vendor payments | No (very rare extra flow) |

### Key Principle
> You can create the house bank **before** the G/L account exists — SAP will show a **warning** ("Field Account ID: Value XXX not allowed") but allows you to save. The account creation is not a prerequisite.

---

## 2. Configuration Steps — ADD New House Bank Account

### Overview Table

| Step | Description | Transaction/Table | ADD | CLOSE |
|------|-------------|-------------------|-----|-------|
| 1 | Check/Create G/L Account | FS00 | X | — |
| 2 | Add House Bank + Account ID | FI12 (SPRO) | X | X (modify text + alt account) |
| 3 | Bank Statement Monitor | FTE_BSM_CUST | X | X removes |
| 4 | OBA1 Exchange Rate Differences | OBA1 (11* accounts) | X (non-USD only) | X removes |
| 5 | Cash Management Account Name | SPRO | X | X removes |
| 6 | Bank Statement Integration | V_T035D (SM30) | X (if electronic) | X removes |
| 7 | Business Area for Electronic Integration | YFI_BASU_MOD | X | No need (per range) |
| 8 | Receiving Account for Payment Requests | V_T018V (SM30) | X | X removes |
| 9 | Payment Configuration (if paying bank) | V_T042IY0, OBPM4, FBZP | X | X removes (partial) |
| 10 | Average Balance Report Sets | GS02 | X | X removes |
| 11 | Cash Position Reports | TRM5 (ZCASH/ZCASHFO/ZCASHFODET) | X (after TRS confirmation) | X removes |
| 12 | Verify Grouping | V_T038 (SM30) | X | Not needed (symbolic) |

### Transport Orders Required
The process requires **2 transport orders**:
1. **Customizing Request** — Table maintenance configuration
2. **Workbench Request** — IBAN generation

---

### Step 1: G/L Account (FS00)

**Rule:** Accounts are created **only in Production (P01)**. Then copied to D01 and V01.

**Input:** Excel form "Request for Creation or Modification of an Account" containing:
- Company Code (e.g., UNES)
- Account Number (e.g., 1095022)
- GL account to use as reference (e.g., 1095012)
- Account Group: "Bank accounts" → Balance sheet account
- Currency (e.g., EUR)
- House Bank ID (e.g., NTB02)
- Bank Account ID (e.g., EUR02)
- GL to be revaluated: YES/NO

**How to create:**
1. Go to FS00, enter new G/L account number and company code
2. Menu: G/L Account → **Create with reference**
3. Enter reference account (e.g., 1095012) and company code UNES
4. **Type/Description tab:**
   - Account Group: Bank accounts
   - Balance sheet account: checked
   - Short Text: (shorten from long text — form doesn't provide short text)
   - G/L Acct Long Text: from form
5. **Control Data tab:**
   - Account Currency: as specified
   - Line Item Display: checked
   - Sort key: 027
6. **Create/bank/interest tab:**
   - Field status group: UN03 (Bank accounts)
   - Planning Level: B0 (CASH AT BANK)
   - Relevant to cash flow: checked
   - Commitment Item: BANK
   - House Bank: from form
   - Account ID: from form (will show warning if bank doesn't exist yet — continue)
7. Save

**Account Pairs:** Accounts are ALWAYS created in pairs:
- `10xxxxx` — Bank account (10* range)
- `11xxxxx` — Contra/clearing account (11* range)

**D01/V01:** Account IDs created by MD team using excel forms in PRD.

---

### Step 2: House Bank / Account ID (FI12)

**Path:** SPRO → Financial Accounting → Bank Accounting → Bank Accounts → Define House banks

**Input:** Excel template with:
- Company Code, House Bank ID, Account ID, Description
- Bank Account Number, IBAN, Currency, G/L Account
- Bank Country, Bank Key, Bank Name, Street, Location, SWIFT Code
- Replenishment settings (Y/N), G/L for replenishment, Currency for replenishment
- Comments (e.g., Alternative account: UNO17)

**How to configure:**
1. Navigate to Company Codes → UNES → House Banks
2. If house bank already exists: select it → Bank Accounts → New Entries
3. If new house bank: New Entries at House Banks level first
4. Fill: Account ID, Description, Bank Account Number, Alternative acct no., G/L, Currency
5. Fill House Bank Data: Bank Country, Bank Key, Address, SWIFT Code
6. **DME instruction key:** Set to **B2** (except for DNB01 which uses **B4**)
7. Save → Transport request

**Close/Delete:** House bank is NEVER deleted. Just add the word "deleted" to description/text. Put closed account in alternative account number field.

---

### Step 3: Bank Statement Monitor (FTE_BSM_CUST)

All active bank accounts should be listed in the bank statement monitor.

**ADD:** Copy from existing similar account (e.g., EUR01 → EUR02)
- Company Code, House Bank, Account ID
- Check: Process Status, Difference Sts, Serial No. Sts, Reconcil. Sts
- Interval: 1, Interval Unit: Calendar Days
- Currency: as per account

**REMOVE:** Select the House Bank and account → Delete icon

---

### Step 4: OBA1 — Exchange Rate Differences

**Only needed for non-USD currency accounts.**

Add 2 accounts (10* and 11* pair) for the new bank account. Copy from reference:

| New | Reference |
|-----|-----------|
| 10xxxxx (new) | 10xxxxx (ref) |
| 11xxxxx (new) | 11xxxxx (ref) |

If no reference exists in OBA1, use any G/L starting with 11 and ending with 2 (EUR sub-bank accounts, e.g., 1175012).

**Configuration:** OBA1 → Group FWA → Transaction KDF (Exchange Rate Dif.: Open Items/GL Acct)
- Exchange rate difference realized: Loss 6045011 / Gain 7045011
- Valuation: Val.loss 1: 6045011 / Val.gain 1: 7045011
- Bal.sheet adj.1: 1175012 (or similar)

---

### Step 5: Cash Management Account Name

**Path:** SPRO → Financial Supply Chain Management → Cash and Liquidity Management → Cash Management → Structuring → Define Cash Management Account Name

**ADD:** Copy EUR01 → EUR02, change G/L account to new values.

Format: `{HouseBank}-{AcctID}` (e.g., NTB02-EUR2)

| New | Reference |
|-----|-----------|
| 1095022 | 1095012 |
| 1195022 | 1195012 |

**REMOVE:** Delete entry.

---

### Step 6: Automatic Bank Statement Integration (V_T035D)

**Path:** SPRO → Financial Accounting → Bank Accounting → Business Transactions → Payment Transactions → Electronic Bank Statement → Make Global Settings for Electronic Bank Statement

**SM30 V_T035D**

Copy from similar account type, assign Transaction type.

**Only "Assign Bank Accounts to Transaction Types"** is configured (not Account Symbols, Posting Rules, etc.)

**Note:** Before adding, change the account as currency may differ. Check if bank requires electronic bank statement — if no, skip this step.

**REMOVE:** SPRO same path → delete entry.

---

### Step 7: Business Area for Electronic Integration (YFI_BASU_MOD)

**Transaction:** YFI_BASU_MOD — Business area substitution for posting

All cash accounts in UNES maintained with business area **GEF** (General Fund).

Postings with business area **X** are valid for IIEP and UBO — G/L accounts to be added:

| CC | DT | Account | BA |
|----|----|---------|----|
| IIEP | Z1 | 10xxx | PDK |
| IIEP | Z1 | 11xxxx | PAR |
| UBO | Z1 | 10xxxx | PFF |

**Filters are per range — no need to change when closing.** Closed accounts remain in the list.

---

### Step 8: Receiving Account for Payment Requests (V_T018V)

**Path:** SPRO → Financial Accounting → Bank Accounting → Business Transactions → Payment Transactions → Payment Request → Define Clearing Accounts for Receiving Bank Acct. Transfer

**SM30 V_T018V**

Copy from reference type of account. Example:

| CoCode | House Bk | Country | Pmt Method | Currency | Account ID | Clrg acct |
|--------|----------|---------|------------|----------|------------|-----------|
| UNES | NTB02 | — | A | EUR | EUR02 | 1195022 |

**REMOVE:** Search by House Bank + Account ID → Delete.

---

### Step 9: Payment Configuration (If Paying Bank)

Only if the bank account is used for paying 3rd parties (vendors) or internal transfers.

#### 9.1 Bank Determination for Payment Transactions (V_T042IY0)

**Path:** SPRO → Financial Accounting → Accounts Receivable and Accounts Payable → Business Transactions → Outgoing Payments → Automatic Outgoing Payments → Payment Method/Bank Selection → Set Up Bank Determination for Payment Transactions

**SM30 V_T042IY0**

Dialog Structure: Bank Selection → Bank Accounts (Enhanced)
- Add new entry with House Bank, Payment method, Currency, Ranking Order, Acct ID, Bank subacct (119xxxx)
- Also configure: Available Amounts (if needed)

**Treasury transfer:** Payment method A always.

#### 9.2 Internal Transfer and Replenishment

**Path:** SPRO → Financial Accounting → Bank Accounting → Business Transactions → Payment Transaction → Payment Handling → Bank Clearing Account Determination → Define Account Determination

Add new bank account to payment method A with correct currency and account.

**In FI12:** Add instruction key **B2** in the "Data Medium Exchange" tab.

**Removal:** Not available to remove (only add).

#### 9.3 Payment File Creation Settings (OBPM4) — CRITICAL

**Must be done in V01 AND P01.** Without this, the payment program will NOT generate the bank transfer file.

**Steps:**
1. **Create payment variant for SAPFPAYM** (SE38):
   - Select existing variant as example (e.g., UNE_TRE_USDNTB)
   - Change Dynamic Selections: Paying Company Code, House Bank, Account ID, Currency
   - Save variant with naming convention: `UNE_TRE_{CURRENCY}{HOUSEBANK}` (e.g., UNE_TRE_EURNTB)
   - Description: `UNES TREAS XML {HouseBank} {AcctID}` (e.g., UNES TREAS XML NTB02 EUR02)

2. **Link variant to house bank** (OBPM4):
   - Select Payment Medium Format:
     - `/GGI_XML_CT_UNESCO` — Other currencies + internal transfers (all currencies)
     - `/SEPA_CT_UNES` — Euro payments
     - `/CITI/XML/UNESCO/DC_V3_01` — USD payments via Citibank
   - Select the House Bank → assign the variant created above

3. **Multi-currency house banks:** If a house bank has accounts in different currencies, create **separate variants** per currency (e.g., UIL_INT_EUR, UIL_INT_USD).

---

### Step 10: Average Balance Report Sets (GS02)

**Set:** YBANK_ACCOUNTS_ALL (hierarchy: HQ & FO Accounts Total)

Hierarchy structure:
```
YBANK_ACCOUNTS_ALL
├── YBANK_ACCOUNTS_HQ (HQ Accounts Total)
│   ├── YBANK_ACCOUNTS_HQ_CA (HQ Current Accounts Total)
│   │   ├── YBANK_ACCOUNTS_HQ_EUR (HQ Current Accounts EUR)
│   │   ├── YBANK_ACCOUNTS_HQ_USD (HQ Current Accounts USD)
│   │   └── YBANK_ACCOUNTS_HQ_OTH (HQ Current Accounts Other)
│   ├── YBANK_ACCOUNTS_SIGHT (HQ At Sight Accounts)
│   │   ├── YBANK_ACCOUNTS_SIGHT_EUR
│   │   └── YBANK_ACCOUNTS_SIGHT_USD
│   └── YBANK_ACCOUNTS_DEPOSIT (HQ Deposits Capital Account)
├── YBANK_ACCOUNTS_FO (FO Current Accounts Total)
│   ├── YBANK_ACCOUNTS_FO_USD
│   ├── YBANK_ACCOUNTS_FO_EUR
│   └── YBANK_ACCOUNTS_FO_OTH
```

**Maintained manually in each system** (D01, V01, P01). Only the bank account G/L is added to the appropriate subset.

**REMOVE:** Select Hierarchy Maintenance → expand all → Find account → select → Mark and remove.

---

### Step 11: Cash Position Reports (TRM5)

**After TRS (Treasury) confirmation.**

3 Report Painter forms may need changes:
- **ZCASH** — HQ Cash position form
- **ZCASHFO** — HQ Field Office Cash position form  
- **ZCASHFODET** — FO Cash position detail form

Each form element uses:
- Key figure: Amount in display currency
- Selected characteristics: G/L accounts (10xxxx and 11xxxx pair)

**ADD:** Add new element with the new G/L accounts. Add to relevant total formula (e.g., Total EUR Accounts, Total loca).

**REMOVE (complex):**
1. Cannot simply delete if element is used in a formula (e.g., "Total Mapu")
2. First: identify the formula component ID (e.g., Y110, Y111)
3. Remove the ID from the FormulaLine
4. Then delete the element row
5. Check ALL dependent formulas (Total Mapu → Total loca → Total USD)

**Special Case:** When reference account has 4 G/L accounts instead of 2 (e.g., 10xxxxx, 11xxxxx, 12xxxxx, 13xxxxx), all 4 must be added.

Save form → Transport (with Form/layout + Key figures subobjects, Transport all languages).

---

### Step 12: Verify Grouping (V_T038)

**Path:** SPRO → Financial Supply Chain Management → Cash and Liquidity Management → Cash Management → Structuring → Grouping → Maintain Structure

**SM30 V_T038**

Groupings: ALL HQS, ATSIGHT HQ (with selections using G/L patterns like `+++10++9++`, `+++11++9++`)

Verify those related to Savings/At Sight accounts.

**No needed when closing** — it is symbolic/pattern-based.

---

## 3. Close/Delete House Bank Account

House banks are **NEVER deleted** from SAP. The closure process involves:

1. **FI12:** Modify description text to include "CLOSED" + put closed alternative account number
2. **Steps 3-11:** Remove entries from each configuration point (see CLOSE column in overview table)
3. **Step 9.2:** Not available to remove (add-only)
4. **Step 9.3 (OBPM4):** Not executed — "as per doubt and risk"
5. **Step 10 (GS02):** Remove — but transport needed (risk of different config in DS1/PS1)

---

## 4. Configuration Data Patterns

### G/L Account Numbering Convention
| Range | Type | Example |
|-------|------|---------|
| 10xxxxx | Bank account (main) | 1095022 |
| 11xxxxx | Clearing/contra account | 1195022 |
| 12xxxxx | Additional clearing (some banks) | 1295012 |
| 13xxxxx | Additional clearing (some banks) | 1395012 |

### House Bank ID Convention
Format: `{BankAbbrev}{Seq}` — e.g., NTB01, NTB02, SOG01, CIC01, BNP01, SCB14

### Account ID Convention
Format: `{Currency}{Seq}` — e.g., EUR01, EUR02, USD01, USDD1, HTG01, ZWG01

### Payment Medium Formats
| Format | Usage |
|--------|-------|
| `/GGI_XML_CT_UNESCO` | All currencies, internal transfers |
| `/SEPA_CT_UNES` | Euro payments |
| `/CITI/XML/UNESCO/DC_V3_01` | USD payments via Citibank |

### Known House Banks (from configuration screenshots)
| House Bank | Bank Name | Country |
|-----------|-----------|---------|
| NTB01 | Northern Trust Company | US |
| NTB02 | Northern Trust Company | GB |
| BNP01 | BNP Paribas | — |
| BPP01 | BPP | — |
| CIC01 | CIC | — |
| CRA01 | Credit Agricole | — |
| SOG01 | Societe Generale | — |
| SOG03 | Societe Generale | — |
| SOG06 | Societe Generale (Haiti) | — |
| SCB14 | Standard Chartered Bank | — |
| BST01 | BST (Maputo) | — |
| ECO08 | Ecobank | ZW |
| ECO09 | Ecobank | — |

---

## 5. Digital Form Design Opportunity

The current process uses **Excel forms** emailed between teams. A digital form could:

### Current Pain Points
1. Manual Excel forms passed via email (.msg files)
2. Short text not provided in form — configurator must shorten manually
3. No validation of G/L reference account existence
4. No automated checklist tracking across 12 steps
5. Configuration done across 3 systems (D01/V01/P01) manually
6. TRM5 cash position forms require complex formula editing

### Proposed Digital Form Fields
```
=== SECTION 1: Request Type ===
- Action: [ADD] / [CLOSE] / [MODIFY]
- Request Date, Requestor, Urgency

=== SECTION 2: Bank Information ===
- Bank Name, Bank Country, Bank Key, SWIFT Code
- Street, City, Branch Office

=== SECTION 3: Account Information ===
- Company Code (dropdown: UNES, IIEP, UBO, UIL, etc.)
- House Bank ID (auto-suggest or new)
- Account ID (auto-suggest or new)
- Bank Account Number, IBAN
- Currency
- G/L Account Number (10xxxxx)
- G/L Reference Account (for "Create with reference")

=== SECTION 4: Payment Configuration ===
- Is this a paying account? [Y/N]
- Payment types: [3rd Party Vendors] [Internal Transfer] [Replenishment]
- Replenishment G/L Account, Currency

=== SECTION 5: Reporting ===
- Electronic Bank Statement? [Y/N]
- Cash Position Report Group: [HQ EUR] [HQ USD] [HQ Other] [FO USD] [FO EUR] [FO Other]
- GS02 Subset: (auto-determined from currency + HQ/FO)

=== SECTION 6: Checklist (auto-generated) ===
□ Step 1: FS00 — G/L Account created
□ Step 2: FI12 — House Bank configured
□ Step 3: FTE_BSM_CUST — Bank Statement Monitor
□ Step 4: OBA1 — Exchange Rate (if non-USD)
□ Step 5: Cash Management Account Name
□ Step 6: V_T035D — Bank Statement Integration (if electronic)
□ Step 7: YFI_BASU_MOD — Business Area Substitution
□ Step 8: V_T018V — Receiving Account
□ Step 9: Payment Config (if paying bank)
□ Step 10: GS02 — Average Balance Sets
□ Step 11: TRM5 — Cash Position Reports (after TRS)
□ Step 12: V_T038 — Verify Grouping
□ Transport 1: Customizing Request created & released
□ Transport 2: Workbench Request created & released
```

### Automation Potential
| Step | Automation Level | Method |
|------|-----------------|--------|
| 1 (FS00) | Semi-auto | RFC via `BAPI_GL_ACCOUNT_CREATE` or WebGUI |
| 2 (FI12) | Semi-auto | SM30 table maintenance via RFC |
| 3-8 | Semi-auto | SM30 table maintenance via RFC |
| 9 (FBZP) | Manual | Complex multi-screen config |
| 10 (GS02) | Manual | Hierarchy manipulation |
| 11 (TRM5) | Manual | Report Painter forms |
| 12 | Verify only | Read-only check |

---

## 6. Real Examples

### Example 1: Northern Trust NTB02/EUR02 (HQ, EUR)
- G/L: 1095022 (ref: 1095012)
- Bank: Northern Trust Company, The — 50 Bank Street, Canary Wharf, London UK
- Bank Country: GB, Bank Key: SP0000000MX7, SWIFT: CNORGB22
- IBAN: GB76CNOR23286317846293
- Replenishment: Yes, G/L 1195022, Currency EUR
- Alternative account: UNO17
- Cash Management: NTB02-EUR2, G/L 1095022, Bank Account 11939389
- Bank Statement: Not electronic (No)

### Example 2: Sogebank Haiti SOG06 (Field Office, USD + HTG)
- Referenced in email: "New Bank accounts Sogebank Haiti- UNESCO Port au Prince USD HTG"
- Multi-currency: requires separate Account IDs (USD01, HTG01)
- Payment config: G/L Account Payments view shows SOG06 with HTG01 (1175524) and USD01 (1175521)

---

## 7. Source Documents Location

```
C:\Users\jp_lopez\UNESCO\DBS Team - FAM\Documentation\Handover FI\Day-by-Day\House Bank\
├── 1 New or changed house bank account steps.pdf    (45 pages, full procedure)
├── 1 New or changed house bank account steps.docx   (editable version)
├── 2FW New Bank accounts Sogebank Haiti*.msg         (example: field office bank)
├── 3 Re_ New Bank account HQ Northern Trust*.msg     (example: HQ bank)
└── 3 Steps 08182025.xlsx                             (tracking checklist)
```
