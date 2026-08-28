---
name: sap_bank_statement_recon
description: Domain agent for SAP Electronic Bank Statement + Reconciliation at UNESCO. MT940 import via Coupa (job EBS INTEGRATION / FEB_FILE_HANDLING), FEBKO/FEBEP/FEBRE, clearing algorithms, T028B account wiring, Y-stack recon programs (YTR0-YTR3, YFI_BANK1). Knows the estate is NOT homogeneous: 120 electronic / 8 MANUAL (FF67) / 27 mixed / 12 without statement, split by company code, closed accounts marked CLOSED in the text. Use it when a statement stopped arriving, when a bank account number changes, when asking which accounts are manual or of investment nature, or before measuring anything over the bank account estate. 13 anti-pattern rules (INC-000006906, INC-000013624).
domains:
  functional: [Treasury]
  module: [FI]
  process: [T2R]
tier: project
maturity: production
origin_session: 29
last_updated_session: 58
triggers: [bank statements, EBS, FEBEP, FEBKO, FEBRE, FF_5, FEBAN, reconciliation, clearing accounts, MT940, Tag 86, posting rules, T028G, YTR3, YTBAE002, YTR0, YTBAI001, YFI_BANK1, Y-stack, field office reconciliation, Maputo, MZN, BDC clearing, UXR1, UXR2, XREF]
subtopics: [central_substitution_YRGGBS00, field_office_custom_clearing_y_stack, mt940_import, posting_rules_T028G]
---

# SAP Bank Statement & Reconciliation Domain Agent

## Metadata
- **Name**: sap_bank_statement_recon
- **Type**: Domain Agent (specialized)
- **Maturity**: Production
- **Origin**: Session #029-#030 — Full EBS configuration extraction + clearing analysis + Tag 86 forensics
- **Triggers**: Questions about bank statements, EBS, T028B, V_T028B, ABSND, EFART, manual bank statement, YBANK, GS02 sets, account nature, investment mandate, statement stopped arriving, house bank account number change, FEBEP, FEBKO, FEBRE, FF_5, FEBAN, reconciliation, clearing accounts, 11xxxxx open items, MT940, Tag 86, posting rules, T028G, search strings, bank sub-accounts, BSAS clearing, algorithm 015, ZUONR matching, Y-stack custom programs, YTR3, field office reconciliation

## Purpose

Specialized agent for all SAP Electronic Bank Statement (EBS) and reconciliation questions at UNESCO. This agent has complete knowledge of:
- Bank statement import chain (MT940 -> FF_5 -> FEBKO/FEBEP -> GL posting -> clearing)
- Three configuration tiers (HQ Detailed, Field Office Generic, Treasury Manual)
- Posting rule engine (T028G: 1,025 rules across 6 rule families)
- Five clearing algorithms (000, 001, 013, 015, 019) with algorithm 015 as dominant mechanism (85.5%)
- GL architecture (10xxxxx permanent bank vs 11xxxxx clearing vs 12/13xxxxx legacy)
- Tag 86 text forensics (FEBRE: 964K rows)
- BA determination chain (YTFI_BA_SUBST + YBASUBST + GGB1 substitution)
- Clearing speed and open item analysis across all bank accounts

## When to Route Here

The **coordinator** should route to this agent when the user asks about:
- Bank statement import (FF_5, FF67, FEBKO, statement headers)
- Bank statement items (FEBEP, posting status, BELNR assignment)
- Reconciliation and clearing (FEBAN, open items, BSAS AUGBL)
- MT940 format and Tag 86 text (FEBRE, VWEZW free-text)
- Posting rules and external transaction codes (T028G, T028E)
- Search strings and matching patterns (T028D)
- GL sub-bank accounts (11xxxxx clearing, 10xxxxx permanent)
- Clearing algorithms (000, 001, 013, 015, 019)
- ZUONR assignment matching and patterns
- Bank account configuration (T012K, house bank GL mapping)
- BA (Business Area) determination during EBS posting
- Statement format mapping (T028B, EFART, MT940 vs manual)
- Open item aging and dormant accounts

## NEVER Do This

1. **Never confuse 10xxxxx open items with "unreconciled"** -- 10xxxxx (BANK symbol) is the permanent bank ledger, NEVER cleared by design. 222,063 open items on 10xxxxx is normal and correct. Only 11xxxxx (BANK_SUB) open items represent items awaiting clearing.
2. **Never claim 102I clearing is 29.2%** -- That figure was WRONG. 82% of 102I items (7,577/9,206) have BELNR=`*` meaning no FI document was created. These are ACH returns, notifications of change, routing corrections from Citibank. Of items that DO post to 11xxxxx: **99.6% clear** (1,623/1,629). The system correctly filters unmatchable items.
3. **Never extract FEBRE without KUKEY filter** -- FEBRE table has 3.7M+ rows across all history. ALWAYS filter to the FEBEP KUKEY range for the period of interest. Extracting without filter will timeout or exhaust memory.
4. **Never use >8 fields with WHERE clause on FEBEP** -- Triggers SAPSQL_DATA_LOSS error. Use adaptive field splitting (2 chunks of fields with separate extractions, then merge by key).
5. **Never assume all bank accounts have the same config** -- Three fundamentally different tiers exist. HQ Detailed has 7+ distinct posting rules per account; Field Office Generic maps ALL 65 ext codes to SUBC/SUBD; Treasury Manual has 100% algo 000 (no auto-clearing).
6. **Never parse FEBRE.VWEZW for structured data** -- It is free-text MT940 Tag 86 content that varies by bank. SocGen uses `/` delimiters, Citibank uses space-delimited text, field office banks have no standard. Use search strings (T028D) for pattern matching instead.
7. **Never assume ZUONR=NONREF means "won't clear"** -- NONREF items (12,789) clear at 108% rate (cleared via other BSAS matching mechanisms, not ZUONR). The clearing happens through alternative algorithm paths.
8. **Never confuse EFART=E (electronic MT940) with EFART=M (manual entry)** -- EFART=M produces MXXD/MXXC posting rules with algorithm 000 (no auto-clearing). EFART=E produces the standard algorithmic rules. Mixing them corrupts clearing rate analysis.
9. **Never demand a `T028B` row from an account whose statement is MANUAL** (`EFART='M'`). Measured: `BTE01-USD01` imported 116 statements and `BTE01-IRR01` another 156, both with no `T028B` row ever. Requiring it publishes a defect that does not exist -- it was this skill's first false positive. Only 131 of the 143 accounts that receive statements are electronic.
10. **Never measure the account estate without cutting closed accounts** -- they are marked `CLOSED` in `T012T-TEXT1`, not by a field, and they are **237 of 411** in UNES. Skipping the cut made 2 of the first 4 "broken wiring" findings false.
11. **Never use YBANK to answer a question about the NATURE of an account.** It classifies geography x currency. The Northern Trust investment mandates sit in `YBANK_ACCOUNTS_HQ_USD` alongside HQ general-operations accounts. And it covers UNES only -- 32 live accounts are in no set.
12. **Never read FF67's header as configuration.** It is `FEBKO-ABSND`, the identity carried by the last imported file. After an account number change it keeps showing the old value, and that is correct behaviour, not a defect.
13. **Never trust `FEBKO.AZDAT` without an upper bound.** There are statements dated in the years 2201/2203/2207/2208 -- a mistyped 2022. One of them poisoned a max() and made 147 accounts look dead.
14. **Never write `CALL TRANSACTION ... MODE 'E'` inside an LDB / GET / recon loop.** MODE 'E' opens SAPGUI on BDC error. On slow WAN paths (field offices) the cumulative GUI handshake exceeds `rdisp/max_wprun_time` and TIME_OUTs the caller's fetch. Use MODE 'N' + `MESSAGES INTO <tab>` + post-loop error reporting. Canonical instance: YTBAE002 (INC-000006906, Claim 54). See "UNESCO Custom Recon Programs" below and the "When implementing custom recon programs" section further down.

## UNESCO Custom Recon Programs (Y-Stack) — full family

UNESCO maintains **three distinct custom bank-reconciliation program families** on P01. Full inventory: `knowledge/domains/Treasury/bank_reconciliation_program_inventory.md` (Session #057). Brief table here:

| Family | Executables | TCODEs | Role | Status | Known defects |
|---|---|---|---|---|---|
| **YTBAE / YTBAM** (original action stack) | YTBAE001, YTBAE001_HR, YTBAE002 + includes YTBAM001/2/3/4 (+ HR + _HR_UBO variants) | YTR1, YTR2, YTR2_HR, **YTR3** | Interactive bank-clearing via BDC chain to FB08 / F-04 / FBRA | YTBAE002 ACTIVE. YTBAE001 + YTBAE001_HR DORMANT | MODE 'E' + CALL TRANSACTION (Claim 54) on all three executables. Empty-range → unbounded-LDB-scan (Claim 53) on YTBAE002 ONLY. |
| **YTBAI** (file pipeline) | YTBAI001 | YTR0 | SMARTLINK CMI940 → MT940 format conversion | DORMANT (hardcoded `/usr/sap/D01/conversion/...` paths, no TBTCO runs) — KU-2026-057-01 | — |
| **YFI_BANK_RECONCILIATION** (modern reporting) | YFI_BANK_RECONCILIATION + DATA + SEL includes + YCL_FI_BANK_RECONCILIATION_BL class | YFI_BANK1 | Read-only ALV list/dashboard (OOP class-based) | ACTIVE interactive | None in the extracted includes; class not yet extracted (KU-2026-057-03) |

### Primary active action program: `YTR3 / YTBAE002`

- **TCODE**: `YTR3` → program `YTBAE002` (package `YA`, 3,422 lines, monolithic) — direct binding, no variant
- **Source**: `extracted_code/CUSTOM/YTBAE002/YTBAE002.abap` (Session #057)
- **Role**: NOT read-only. Decides from BSIS row content + PAYR/BKPF correlation whether each open sub-bank item needs reversal/clearing/reset-cleared, then drives 3 standard FI TCODEs via BDC:
  - `FB08` (reverse) at `YTBAE002.abap:723, :853`
  - `F-04` (post with clearing) at `:771`
  - `FBRA` (reset cleared items) at `:819`
- **Scope resolution**: `SELECT SAKNR XOPVW FROM SKB1 WHERE BUKRS+HBKID+HKTID` at `:1098-1101`, filter `SAKNR+3(2) IN ('11','13','15') AND XOPVW='X'` for open-item bank sub-bank GLs. **Does NOT use YBANK_* sets** (grep-confirmed). **Depends on `SKB1.XOPVW='X'` being set** on bank sub-bank GLs — else OI range is empty.
- **LDB call**: `CALL FUNCTION 'LDB_PROCESS' LDBNAME='SDF'` at `:1509-1517` feeds BSIS rows via callback.
- **Selection screen** (`:297-310`): `GP_BUKRS` (default UNES), `GP_HBKID`, `GP_HKTID`, `GP_BUDAT` (default SY-DATUM). Four mandatory PARAMETERS, no ranges.
- **Output**: classical list via `WRITE` + `CALL SCREEN 9000` (no ALV).
- **Known defects**:
  - **MODE 'E' BDC network coupling** (`:27`, severity HIGH) — INC-000006906, fix proposed at `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap`, Claim 54.
  - **Empty-range unbounded LDB scan** (`:1366-1370`, severity MED, latent) — Claim 53. Optional fix `FIX_C` in same file.
- **Dependencies on master data**: `SKB1.XOPVW='X'` must be maintained on every bank sub-bank GL that should be reconciled. Missing `XOPVW='X'` is a config-class source of latent bugs (program silently produces no output or, with the :1366 latent, triggers a full BSIS scan).

### Legacy action programs: `YTR1 / YTR2 / YTR2_HR`

- `YTR1` (variant `BK REC STATMT2`) → `YTBAE001` + includes YTBAM002/003/004
- `YTR2` (variant `BANK_RECONCIL`) → same `YTBAE001` (alternate variant)
- `YTR2_HR` (variant `BANK_RECONCIL`) → `YTBAE001_HR` + includes YTBAM002_HR/003_HR/004_HR
- **Both executables are DORMANT** (YTBAE001 has 1 TBTCO entry with STATUS=NULL / STRTDATE=NULL, YTBAE001_HR has zero entries).
- **Same MODE 'E' inherited pattern**: `C_MOD TYPE C VALUE 'E'` at `YTBAE001.abap:118` and `YTBAE001_HR.abap:122`, consumed by YTBAM002 / YTBAM002_HR's 4 `CALL TRANSACTION Y_TRANS USING BDCDTAB MODE C_MOD` sites.
- **Different selection mechanism vs YTBAE002**: iterates a config table `TSAKO` (`LOOP AT TSAKO WHERE Y_BQ_AC = ' '.` at `YTBAM003.abap:53-59`) — safe-by-construction against the empty-range bug. Claim 53 does NOT apply to this family.
- **Recommendation**: don't spend a transport slot today. File KU-2026-057-02 (check STAD for recent interactive usage of YTR1/YTR2/YTR2_HR); if zero, propose decommission. If non-zero, apply the same MODE 'E' → 'N' fix at `YTBAE001.abap:118` and `YTBAE001_HR.abap:122`.

### Modern reporting view: `YFI_BANK1 / YFI_BANK_RECONCILIATION`

- **TCODE**: `YFI_BANK1` → program `YFI_BANK_RECONCILIATION` (package `YA`, 34 LOC) — direct binding, no variant.
- **Source**: `extracted_code/CUSTOM/BANK_RECONCILIATION/YFI_BANK_RECONCILIATION/` (+ `_DATA/` + `_SEL/` includes).
- **Role**: **read-only** ALV report. Two output modes: `P_DETAIL` (detailed list) or `P_DASH` (dashboard). NO BDC. NO CALL TRANSACTION. NO LDB.
- **Delegation**: all selection + rendering logic lives in `YCL_FI_BANK_RECONCILIATION_BL` (OOP class, not yet extracted — KU-2026-057-03).
- **INITIALIZATION** (`YFI_BANK_RECONCILIATION_SEL.abap:17-41`) auto-populates `S_HKONT` via `YCL_FI_BANK_RECONCILIATION_BL=>INITIALIZE_HKONT( )` and sets `P_DATE_Z` = last day of previous month, `P_DATE_O` = last day of two months ago.
- **Not a replacement** for YTBAE002 — it's a reporting/dashboard companion, not an action program. The team runs YTR3 (YTBAE002) for clearing actions and YFI_BANK1 for visibility.

### File pipeline: `YTR0 / YTBAI001`

- **TCODE**: `YTR0` (variant `YTBAI001`) → `YTBAI001`.
- **Source**: `extracted_code/CUSTOM/BANK_RECONCILIATION/YTBAI001/YTBAI001.abap` (197 LOC).
- **Role**: converts SMARTLINK CMI940 bank-statement files to MT940 format. Reads `/usr/sap/D01/conversion/input/TITRBK03/sg2707.txt`, writes `/usr/sap/D01/conversion/output/TITRBK03/sg2707out.txt`. Filter header `C_SOG = ':25:SOGEFRPP/'`.
- **Status**: DORMANT. Authored A.ELMOUCH 2001-11-05, filesystem paths point to D01 (never promoted to P01 with updated paths). Open KU-2026-057-01 to confirm whether SMARTLINK is still incoming or has been superseded by the EBS MT940 direct-import pipeline.



---

## The estate is NOT homogeneous — three channels (s108, measured)

Any answer that assumes "the statement arrives as a file" is wrong for 35 of the 167 live
accounts. Measured live on P01, window 2025-2026, `FEBKO.EFART`:

| Channel | Live accts | Needs `T028B` | What breaks | Who notices today |
|---|---:|---|---|---|
| **ELECTRONIC** (`EFART='E'`) | 120 | **YES**, keyed on the CURRENT account number | account number changes -> silent stop | **nobody** |
| **MANUAL** (`EFART='M'`, typed in FF67) | 8 | **NO** — 116 statements imported with no row | the named person stops typing | **nobody** |
| **MIXED** | 27 | yes | mostly `JOBBATCH`, manual is 0-7% (the exception) | — |
| **NO STATEMENT** | 12 | — | can't tell "doesn't apply" from "was dropped" | never declared |

**Split by company code, always.** All the complexity is in UNES (144 live: 99/8/26/11); the
institutes are clean and automatic. And the same account behaves differently per company:
`CBE01-ETB02` gets 543 daily statements in ICBA and zero in UNES.

**Closed accounts are marked IN THE TEXT** — `T012T-TEXT1` starts with `CLOSED`, with arbitrary
dashes (`CLOSED-----UNESCO YAOUNDE`). **237 of 411** UNES accounts. There is no status field.
Any measurement over the estate that skips this cut is measuring a false denominator.

Instruments (run these, don't re-derive):
```bash
python Zagentexecution/quality_checks/bank_statement_channel_census.py      # canal + cadencia
python Zagentexecution/quality_checks/house_bank_ebs_wiring_check.py        # T028B vs T012K
python Zagentexecution/quality_checks/bank_account_nature_model.py          # soc -> banco -> cuenta
```

## `T028B` — the table that breaks when an account number changes

**`T028B` (*Transaction Type of Sender Bank*, SM30 `V_T028B`) is keyed on `BANKL + KTONR` — the
bank account NUMBER.** `FI12` writes `T012K` and does not carry over. Change the number and the
row is orphaned: the electronic statement stops arriving, with no error, while the house bank
record looks perfect and the `EBS INTEGRATION` job keeps finishing green.

Canonical instance: **INC-000013624** (NTB02/EUR01, 2026-08). Of the **41 customizing tables**
able to hold a bank account number, only **two** hold UNESCO's accounts: `T012K` and `T028B`.

⚠️ `T035D` is **NOT** this table. `T035D` = *Cash Management Account Names* (key `BUKRS+DISKB`,
unaffected by a number change). The house-bank procedure named the right SPRO node but pointed
at `V_T035D` for years — that mislabel is what let the incident through.

## `FEBKO-ABSND` — what FF67 actually shows

The "Bank Key | Account" header in FF67 is `FEBKO-ABSND`: **the sender identity carried by the
last file that was imported**. It is history, not configuration. After an account number change
FF67 keeps showing the OLD value forever, and that is not a defect. Format:

```
ABSND = "SP0000000MX7   UNO12EUR"
         └ bank key ┘   └ account as the bank names it (matches T012K-BNKN2) ┘
```

## YBANK — what it is, where it lives, what it does NOT classify

`YBANK_ACCOUNTS_*` is the set hierarchy everyone calls "the master list of bank accounts".
Measured: **Report Painter/Writer sets, `SETCLASS=0000` over `GLT0-RACCT`** (G/L totals,
account field). Maintained in **GS01/GS02/GS03**, stored in `SETHEADER`/`SETNODE`/`SETLEAF`.
15 sets, 3 levels, **158 values in 10 leaves**. Present in both P01 and D01.

**It IS transportable — but as whole-table contents, not as named sets.** The transport object
is `TDAT GRW_SET`: e.g. `D01K9B0F5F` (released, JP_LOPEZ, 2026-04-07) contains exactly one entry,
`TDAT GRW_SET`. Two consequences: **(1)** no search by object name will ever find it — `E071` has
zero rows for `YBANK%` or `0000YBANK%`, and that zero means *cannot see*, never *does not exist*;
**(2)** the transport carries the **FULL set, not a delta**, so **D01 and P01 must be aligned
before transporting** or the target loses whatever it had that the source lacks.

```
YBANK_ACCOUNTS_ALL
├── YBANK_ACCOUNTS_HQ
│   ├── YBANK_ACCOUNTS_HQ_CA ── HQ_EUR (9) · HQ_USD (9) · HQ_OTH (6)
│   ├── YBANK_ACCOUNTS_SIGHT ── SIGHT_EUR (5) · SIGHT_USD (2)
│   └── YBANK_ACCOUNTS_DEPOSIT (4)
└── YBANK_ACCOUNTS_FO ─────────  FO_USD (51) · FO_OTH (60) · FO_XAFXOF (8) · FO_EUR (4)
```

**What it classifies: GEOGRAPHY x CURRENCY. Not the nature of the account.** Do not reach for it
to answer "is this an investment account" — measured, the three Northern Trust mandates
(`MANDATE PIMCO`, `MANDATE JP MORGAN`, `RAMP`) sit in `YBANK_ACCOUNTS_HQ_USD`, the **same leaf**
as `SOG01-USDD1` and `CIT04-USD04`, which are HQ general-operations accounts.

Two nodes ARE about nature, and both are partial: `_SIGHT` (6 real house bank accounts —
reliable) and `_DEPOSIT` (4 G/L accounts in the `404xxxx` range, **none of which is a house bank
account** — it is a set of term-deposit G/Ls, not of bank accounts).

**Where it is actually used — measured, one consumer.** `SETUSE_REP` (the set-usage table for
Report Painter) has 7,693 rows across 894 reports. Exactly **one** references a YBANK set:

```
LIB  RNAME       SETID
0B1  ZAVERAGE    0000YBANK_ACCOUNTS_ALL      (+ &BUKRS and standard period variables)
```

`ZAVERAGE` is the average-balance report (library `0B1` = FI-GL totals, `GLT0`), run from GS02.
Two things follow:
- **Only the ROOT node is referenced.** The 10 leaves and the sub-nodes (`_HQ_CA`, `_SIGHT`,
  `_DEPOSIT`, `_HQ_EUR`…) are never named by any report — they exist purely to give `ZAVERAGE`
  its drill-down structure.
- **Zero uses in ABAP.** Grep over the whole extracted corpus (`extracted_code/`,
  `extracted_sap/`, `extracted_sap_p01/`): no custom program reads these sets. The only hit is
  `MYBANKDETAILS` in an HCM Fiori program — a substring false positive.

⚠️ The claim that `ZCASH` / `ZCASHFO` / `ZCASHFODET` use YBANK is **not supported**: no report
whose name contains `CASH` appears in `SETUSE_REP` at all. Those cash-position reports may exist
by another route, but they do not consume these sets.

**And it only covers UNES**: 32 of the 167 live accounts are in no set at all, nearly all of
them institute accounts (IBE, ICBA, ICTP, IIEP, MGIE, UBO).

**Of the three candidates, YBANK is the one that classifies best — by a distance** (135 of 167 accounts discriminated, 3 levels, and the only nature-bearing node, `_SIGHT`). `FDLEV` is binary and the FSV puts everything in one position. YBANK is also the right place to EXTEND: a single consumer means near-zero blast radius, and `_SIGHT` proves a nature node can live beside the geography ones. Caveats before touching it: UNES only (32 accounts outside), `_DEPOSIT` is a BAD precedent (it holds G/Ls, not house bank accounts), and it transports as whole-table contents so D01 and P01 must be aligned first.

**Nature is not modelled anywhere** — it lives in free text. 141 of 167 live accounts have no
signal at all. What does hold: the **4 investment-mandate accounts are exactly the 4 that
receive no statement**, while the same custodian's 4 cash accounts (PFF Nessim Habif, Cash Pool,
ASHI USD, ASHI EUR) get daily files. The cut is the account, not the bank.

**The balance sheet does not classify them either.** Measured on **FS10** (the version UNES
actually runs, derived from the `RFBILA00` variant, not `T011`): **all 352 UNES bank accounts fall
into one single position, `1.1.1.1 Cash with Banks`** — mandates, cash accounts, at-sight and
operating alike. The only exceptions are `UNDP` (`1.1.7.3`) and two CLOSED accounts with no
position. And the FSV **does have** `1.1.2.1 Short Term Deposits` and `1.2.1.1 Other Investments`
— they exist and no bank account uses them. Not asserted as an accounting error (a custody
account's cash leg legitimately is cash), but it is an open question for Finance: those four
accounts receive **no bank statement** and are presented as *Cash and Cash Equivalents*. Both
cannot be fine at once.

⚠️ **`ASHI` and `PFF` are NOT investment markers** though they look like it — they are funds
whose cash accounts receive daily statements. Treating them as such misclassifies four
operational accounts, including the one from the incident. Reliable markers are manager or
programme names: `MANDATE`, `PIMCO`, `MORGAN`, `RAMP`, `IMIP`.

## E2E Bank Statement Chain

```
                                  INBOUND
MT940 file from bank
    |
    v
FF_5 (import program)  -----> FEBKO (statement header, ASTAT lifecycle)
    |                              |
    |                              +---> FEBEP (line items, one per bank transaction)
    |                                        |
    |                                        +---> T028G lookup
    |                                        |     (VGTYP + VGEXT + VOZPM -> VGINT + INTAG)
    |                                        |
    |                                        +---> Posting Rule fires
    |                                        |     (101/102/111/201/999/SUBC/SUBD)
    |                                        |
    |                                        +---> GL Posting
    |                                        |     10xxxxx (BANK) = permanent ledger
    |                                        |     11xxxxx (BANK_SUB) = clearing account
    |                                        |
    |                                        +---> Algorithm runs
    |                                              (000/001/013/015/019)
    |                                              |
    |                                              +---> Match found -> BSAS (cleared)
    |                                              |
    |                                              +---> No match -> FEBAN queue
    |
    +---> FEBRE (Tag 86 raw text rows, linked by KUKEY)
```

### Statement Lifecycle (FEBKO.ASTAT)
| ASTAT | Meaning | Count | % |
|-------|---------|-------|---|
| 8 | Fully posted | 31,141 | 99.1% |
| 5 | Partially posted | 152 | 0.5% |
| 2 | Imported, not posted | 90 | 0.3% |
| 0 | New/error | 33 | 0.1% |

### Import Automation
- **JOBBATCH**: 31,102 statements (99.1%) -- automated background job import via SM37
- **K_ABDULLAH**: 217 (manual imports for 1 specific bank)
- **JN_SACKEY**: 25, **H_YAHIA**: 19, others: <10 each
- Manual imports are exceptions, not the norm

## Three Configuration Tiers

### Tier 1: HQ Detailed (12 accounts)
**Banks**: SOG_FR (Societe Generale), CIT04_US (Citibank USD), CIT21_CA (Citibank CAD)

| Characteristic | Value |
|---------------|-------|
| Ext codes mapped | 67-82% with specific clearing rules |
| Posting rules | 7+ distinct rules per account |
| Algorithms | 000, 001, 013, 015, 019 (all five) |
| Search strings | Bank-specific (SOG, CIT patterns in T028D) |
| Clearing strategy | Multi-algorithm: checks by number, DME by file, transfers by ZUONR |
| EFART | E (electronic MT940) |

**Example HQ rules (SOG_FR)**:
- Ext code 051 -> 102O (outgoing clearing) + algo 013 (check matching)
- Ext code 070 -> 102I (incoming clearing) + algo 001 (standard)
- Ext code 835 -> 102O + algo 019 (DME file matching, Worldlink)

### Tier 2: Field Office Generic (111 accounts)
**Format**: XRT940 (all field office banks)

| Characteristic | Value |
|---------------|-------|
| Ext codes mapped | ALL 65 codes -> SUBC (credit) / SUBD (debit) |
| Posting rules | 2 only (SUBC + SUBD) |
| Algorithms | 015 exclusively (clear by ZUONR assignment) |
| Search strings | FO_PAYM_DOC (`31########`) |
| Clearing strategy | ZUONR assignment matching only |
| EFART | E (electronic MT940) |
| Same-day clearing | 61% average |

**Why generic works**: Field office transactions are predominantly payment documents with reference numbers that map cleanly to ZUONR. No checks, no DME files, no complex instruments.

### Tier 3: Treasury Manual (18 accounts)
**Format**: TR_TRNF (treasury transfer)

| Characteristic | Value |
|---------------|-------|
| Ext codes mapped | 102I/102O only |
| Posting rules | 2 only (102I + 102O) |
| Algorithms | 000 exclusively (no auto-clearing) |
| Search strings | None |
| Clearing strategy | 100% manual via FEBAN |
| EFART | M (manual entry) |

**Why manual**: Treasury transfers between UNESCO's own accounts require human verification. Automated clearing would be inappropriate for inter-company fund movements.

## Posting Rules (T028G, 1,025 rules)

### Rule Families

| Rule | Direction | Behavior | GL Accounts | Doc Type | Auto-Clear |
|------|-----------|----------|-------------|----------|------------|
| 101I / 101O | In / Out | Simple post (no clearing) | BANK + BANK_SUB | Z1 | No |
| 102I / 102O | In / Out | Clearing on sub-bank | BANK + BANK_SUB | Z7 | Yes (if algo matches) |
| 111I / 111O | In / Out | Interest posting | Interest accounts | Z1 | No |
| 201I / 201O | In / Out | Customer posting | AR accounts | Z1 | No |
| 999I / 999O | In / Out | Unallocated | Suspense account | Z1 | No (FEBAN required) |
| SUBC / SUBD | Credit / Debit | Field office generic | BANK + BANK_SUB | Z7 | Yes (algo 015) |

### Posting Rule Selection Logic (T028G)
```
Input:  VGTYP (format group) + VGEXT (external transaction code) + VOZPM (payment indicator)
Output: VGINT (posting rule) + INTAG (algorithm)
```

- T028G has 1,025 entries mapping ext codes to internal posting rules
- Each bank format (T028B) defines which VGTYP to use
- VGEXT comes from MT940 field :61: subfield (transaction type code)
- VOZPM distinguishes credit vs debit when ext code is ambiguous

### Post Type (T028G.BUODO)
| Post Type | Meaning |
|-----------|---------|
| 1 | Debit bank, credit offset |
| 2 | Credit bank, debit offset |
| 4 | Debit bank, clear on sub-bank (outgoing clearing) |
| 5 | Credit bank, clear on sub-bank (incoming clearing) |

## Clearing Algorithms

### Algorithm 000 -- No Interpretation
- Posts to GL only, no automatic clearing attempt
- Items land in FEBAN queue for manual processing
- Used by: Treasury Manual tier, interest postings, unallocated items
- Volume: ~14.5% of items

### Algorithm 001 -- Standard Matching
- Matches by document number and amount
- Used for: incoming payments at HQ (SocGen, Citibank)
- Requires: BELNR or reference number in bank statement

### Algorithm 013 -- Check Number Matching
- Matches by check number from MT940 against PAYR table
- Used for: physical check clearing (ICTP mainly)
- Requires: check number in Tag 86 text, PAYR entry exists

### Algorithm 015 -- Clear by Assignment (ZUONR)
- **THE dominant mechanism: 85.5% of all cleared items**
- Matches bank statement reference to ZUONR field on open FI items
- Used by: ALL field office accounts (SUBC/SUBD), plus HQ for transfers
- Matching chain: MT940 reference -> search string extracts value -> compared to BSID/BSIK ZUONR
- Speed: 61% same-day clearing (XRT940 format)

### Algorithm 019 -- DME File Matching
- Matches bank statement to original DME payment file sent to bank
- Used for: Citibank Worldlink payments (HQ), SocGen bulk payments
- Requires: DME file reference in statement (PREF/01#### or EF/01########-)
- Search strings: SOG_DME, CIT_DME patterns in T028D

## GL Account Architecture

### Account Ranges and Symbols

| Range | Symbol | Purpose | Cleared? | Open Items (2024-2026) |
|-------|--------|---------|----------|----------------------|
| 10xxxxx | BANK | Permanent bank ledger | **NEVER** | 222,063 (normal) |
| 11xxxxx | BANK_SUB | Clearing (sub-bank) account | Yes | 2,996 (99.4% cleared) |
| 12xxxxx | BANK_TECH | Legacy technical | Phasing out | 28 |
| 13xxxxx | OFFSET_TECH | Legacy offset | Phasing out | 26 |

### Why 10xxxxx Is Never Cleared
- 10xxxxx represents the actual bank balance in SAP
- Every bank statement line creates a posting here (debit or credit)
- The balance of 10xxxxx should match the bank's own ledger
- Clearing would destroy the audit trail of bank movements
- "Open items" on 10xxxxx = every individual bank transaction ever posted (cumulative)

### 11xxxxx Clearing Health
- Total items posted to 11xxxxx: 536,541
- Cleared items: 533,545 (99.4%)
- Open items: 2,996
- Of open items: **87.8% are <30 days old** = current processing queue, NOT backlog
- True aged items (>90 days): <3% of open = genuinely stuck or timing differences

### 12xxxxx / 13xxxxx Legacy
- Being phased out
- 28 + 26 = 54 open items remaining
- No new postings expected
- Candidates for cleanup/write-off review

## Clearing Chain (from BSAS Analysis)

### AUGBL Prefix Distribution
| AUGBL Prefix | % of Clearings | Source |
|-------------|---------------|--------|
| 01xxxxxxxx | 64.5% | F110 payment documents (automatic payments that clear the sub-bank) |
| 35xxxxxxxx | 31.8% | Z7 clearing documents created during EBS import (algorithm-matched) |
| 20xxxxxxxx | 2.1% | Manual clearing (FEBAN / F-03) |
| Other | 1.6% | Reversals, corrections |

### Clearing Speed
| Timeframe | Cumulative % |
|-----------|-------------|
| Same day | 55.3% |
| Within 3 days | 76.4% |
| Within 7 days | 88.1% |
| Within 30 days | 99.3% |
| >30 days | 0.7% |

### Clearing Document Statistics
- Average items per clearing doc: 5.1
- Maximum items per clearing doc: 1,882 (batch clearing)
- Median items per clearing doc: 2

## Clearing Rates by Posting Rule (Verified)

| Rule | Total Items | Cleared | Rate | Notes |
|------|-------------|---------|------|-------|
| SUBD | 87,581 | 83,057 | 94.8% | FO debit, algo 015 |
| 102O | 16,589 | 15,994 | 96.4% | HQ outgoing clearing |
| SUBC | 6,354 | 6,028 | 94.9% | FO credit, algo 015 |
| TECD | 1,196 | 1,153 | 96.4% | Treasury debit |
| MXXD | 4,617 | 4,563 | 98.8% | Manual format, cleared via FEBAN post-processing |
| 102I | 9,206 total | 1,623/1,629 on 11xxx | 99.6%* | *Of items that post. 82% have BELNR=`*` (no FI doc) |

### 102I Root Cause (CRITICAL CORRECTION)

The initial analysis showed "29.2% clearing" for 102I which was **wrong**. The breakdown:
- 9,206 total 102I items
- 7,577 (82%) have BELNR=`*` = **no FI document created by design**
- These are ACH returns, notifications of change, incorrect routing numbers
- Tag 86 text confirms: "ACH CREDIT NOTIF. OF CHG.", "INCORRECT TRANSIT/ROUTING NO."
- Only 1,629 items actually post to 11xxxxx accounts
- Of those: **1,623 cleared = 99.6%**
- The system correctly identifies and filters unmatchable items

## Search Strings (T028D, 331 entries)

### Key Patterns

| Search String ID | Pattern | Purpose | Used By |
|-----------------|---------|---------|---------|
| FO_PAYM_DOC | `31########` | Field office payment document numbers | All XRT940 accounts |
| SOG03_PAYM_DOC | `(/2######/)` | F110 payment docs (SocGen format) | SOG_FR accounts |
| CIT_PAYM_DOC | `REF 0002######` | Citibank payment document reference | CIT04_US, CIT21_CA |
| SOG_DME | `PREF/01####` | DME file reference (SocGen bulk) | SOG_FR (algo 019) |
| CIT_DME | `EF/01########-` | DME file reference (Citibank Worldlink) | CIT04_US (algo 019) |
| SOG_CHK | `CHK######` | Check number (SocGen) | SOG_FR (algo 013) |

### How Search Strings Work
1. Algorithm receives Tag 86 text from MT940
2. Searches for pattern defined in T028D
3. Extracts the matched portion (e.g., payment doc number)
4. Uses extracted value to search against open items (BSID/BSIK ZUONR, BELNR, or PAYR check number)
5. If match found + amount matches -> clearing document created

## ZUONR Patterns (Assignment Field)

| ZUONR Pattern | Items | Clearing Rate | Description |
|--------------|-------|--------------|-------------|
| 3100x... | 9,338 | High | Field office payment docs |
| 2xxx... | 51,740 | 95% | Payment document numbers |
| NONREF | 12,789 | 108%* | No reference found |
| BANK CHARG | 4,658 | 32% | Bank charges (often no matching item) |
| CHECK##### | 2,341 | 89% | Check numbers |

*NONREF items clear at >100% because some get cleared by multiple mechanisms (BSAS matching finds them through alternative paths even without ZUONR).

## BA (Business Area) Determination

### Calling Chain
```
EBS posting triggers -> GGB1 (substitution framework)
    -> YRGGBS00 (substitution program)
        -> FORM U910 (substitution rule)
            -> YCL_FI_ACCOUNT_SUBST_READ (ABAP class)

EBS user exit:
    YTFBE001 (enhancement)
        -> EXIT_RFEBBU10_001
            -> ZXF01U01
                -> YTBAM001 (BA mapping table)
```

### BA Determination Tables

**YTFI_BA_SUBST** (129 entries) -- Modern range-based rules (post Oct-2022)
- Maps account ranges + cost center ranges to Business Area
- Takes priority over legacy YBASUBST
- Example: GL 5xxxxx + cost center 3xxx* -> BA = GEF

**YBASUBST** (752 entries) -- Legacy table
- Direct account -> BA mapping
- 9 entries still have BA=X (for IIEP/UBO special cases)
- Being gradually replaced by YTFI_BA_SUBST ranges

### BA Distribution (from FEBEP postings)
| Business Area | % |
|--------------|---|
| GEF | 82.3% |
| PFF | 13.0% |
| X (special) | 1.6% |
| OPF | 1.3% |
| Other | 1.8% |

## System Health Dashboard

### FEBEP (Bank Statement Items)
| Metric | Value |
|--------|-------|
| Total items (2024-2026) | 223,710 |
| Posted (BSTAT != blank) | 99.9% |
| With FI document (BELNR != `*`) | ~82% |
| BELNR=`*` (no posting by design) | ~18% |

### FEBKO (Statement Headers)
| Metric | Value |
|--------|-------|
| Total statements (2024-2026) | 31,416 |
| Fully posted (ASTAT=8) | 31,141 (99.1%) |
| Partially posted (ASTAT=5) | 152 (0.5%) |
| Not posted (ASTAT=2) | 90 (0.3%) |
| Error (ASTAT=0) | 33 (0.1%) |

### FEBRE (Tag 86 Text)
| Metric | Value |
|--------|-------|
| Total rows (2024-2026, KUKEY-filtered) | 964,055 |
| Fields | 4 (KUKEY, SESSION, SEESSION_ITEM, VWEZW) |
| Avg rows per FEBEP item | ~4.3 |

### 11xxxxx Clearing Account
| Metric | Value |
|--------|-------|
| Total items posted | 536,541 |
| Cleared | 533,545 (99.4%) |
| Open | 2,996 |
| Open <30 days | 87.8% (current queue) |
| Avg clearing time | 2.3 days |
| Same-day clearing (XRT940) | 61% |

## Referencia detallada

Lo que sigue vive en **[reference.md](reference.md)** y se carga sólo si hace
falta — una skill cargada se queda en contexto todo el turno, así que aquí
queda lo que se lee ANTES de actuar y allí el detalle:

- **Tables in Gold DB**
- **Companion & Knowledge Assets**
- **Key Transactions**
- **Relationship to Payment Domain**
- **Diagnostic Playbook**
- **When Implementing Custom Recon Programs (anti-patterns to avoid)**
- **Statement Format Mapping (T028B, 169 entries)**
- **Extraction Rules**
