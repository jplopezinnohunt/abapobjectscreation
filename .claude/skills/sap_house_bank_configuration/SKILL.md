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
- **The ACCOUNT NUMBER of an existing account changes** — its own path, not "a modification in
  FI12". FI12 is step 1 of 6; see `house_bank_configuration.md` §2b and the Pre-Close Checklist
  step 4. Skipping it silently kills the electronic bank statement (INC-000013624)
- Bank account closure request
- Compliance audit of existing house bank configuration
- **The bank statement of an account stopped arriving** — start at the wiring gate, not at FI12

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

## Pre-Close Checklist (before declaring ANY config complete)

Run these checks BEFORE writing the report or updating companions. Do NOT skip.

```
1. python house_bank_compliance_checker.py D01 {HBKID}     → must be 0 FAIL
2. python house_bank_compliance_checker.py P01 {HBKID}     → must be 0 FAIL
3. python uba01_3system_comparison.py                       → must show ALL IDENTICAL
4. python Zagentexecution/quality_checks/house_bank_ebs_wiring_check.py --bukrs {BUKRS}
                                                            → must be LIMPIO (exit 0)
5. grep -r "{HBKID}" companions/                           → update EVERY companion that mentions this bank
6. grep -r "{HBKID}" knowledge/                            → update EVERY report that mentions this bank
```

If step 5 or 6 finds stale references, fix them BEFORE closing. A closed report with stale data in another file is not closed.

### ⛔ Step 4 is MANDATORY when an ACCOUNT NUMBER changed (added s108, INC-000013624)

**Changing a bank account number orphans every configuration keyed on that number.** FI12
writes `T012K` and does **not** carry over to **`T028B`** (*Transaction Type of Sender Bank* —
SM30 `V_T028B`), whose key is `BANKL + KTONR`. When the number changes, that row stops
matching and **the electronic bank statement silently stops arriving**: the house bank record
looks perfect, the `EBS INTEGRATION` job keeps finishing green every hour, and nobody notices
for weeks.

Measured on P01: of the **41 customizing tables** able to hold a bank account number, only
**two** hold UNESCO's accounts — `T012K` and `T028B`. There is no third thing to fix, and
there is no way to skip the second.

The `house_bank_ebs_wiring_check.py` gate compares, account by account across the whole
estate, the number in `T012K` against the one in `T028B`.

**Two denominators it declares — the measure is false without them:** (1) closed accounts are
marked **in the text**, `T012T-TEXT1` starting with `CLOSED` (237 of 411 in UNES); (2) the
`T028B` row is only required where the statement is **electronic** (`FEBKO.EFART='E'` — 131 of
the 143 accounts that receive statements). `BTE01-USD01` imported 116 **manual** statements
with no `T028B` row at all. Without those two cuts the first run reported 4 broken accounts and
**3 were false** — 2 closed for years, 1 manual.

Full procedure for an account-number change: `knowledge/domains/Treasury/house_bank_configuration.md` §2b.

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


## Referencia detallada

Lo que sigue vive en **[reference.md](reference.md)** y se carga sólo si hace
falta — una skill cargada se queda en contexto todo el turno, así que aquí
queda lo que se lee ANTES de actuar y allí el detalle:

- **Configuration Patterns (from Gold DB analysis of 211 banks + ECO09 benchmark)**
- **13-Step Process**
