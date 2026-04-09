# Treasury Domain (BFM-TRS)

> **Owner:** BFM-TRS (Anssi Yli-Hietanen, Baizid Gazi, Marlies Spronk)  
> **Configurator:** Pablo Lopez (DBS)  
> **Company Code:** UNES (primary), plus IIEP, UBO, UIL, IBE, etc.  

---

## Domain Scope

Treasury manages ALL bank-related operations in UNESCO's SAP landscape. This domain covers the complete lifecycle from bank account opening to daily operations to account closure.

```
TREASURY (BFM-TRS)
│
├── 1. BANK ACCOUNT MANAGEMENT
│   ├── House Bank Configuration (create / modify / close)
│   ├── G/L Account Master Data (FS00)
│   ├── IBAN Management (TIBAN)
│   └── Bank Directory (BNKA)
│
├── 2. BANK STATEMENT PROCESSING (EBS)
│   ├── MT940 Import (FF_5 / FF.5)
│   ├── Electronic Bank Statement Config (T035D + T028B)
│   ├── Bank Statement Monitor (FTE_BSM_CUST)
│   ├── Automatic Posting (posting rules, account symbols)
│   └── Bank Reconciliation (FEBAN) — clearing on 11* sub-bank accounts
│
├── 3. PAYMENT EXECUTION
│   ├── Automatic Payment Program (F110)
│   ├── Bank Determination (T042I — which bank pays)
│   ├── Payment Methods (FBZP — A=wire, 3=check, S=SEPA, etc.)
│   ├── Payment File Generation (OBPM4 / SAPFPAYM variants)
│   ├── Payment Medium Formats (/GGI_XML_CT_UNESCO, /SEPA_CT_UNES, /CITI/XML)
│   ├── Bank Communication Management (BCM)
│   └── Receiving Bank Clearing (T018V)
│
├── 4. CASH MANAGEMENT & REPORTING
│   ├── Cash Position Reports (TRM5 — ZCASH / ZCASHFO / ZCASHFODET)
│   ├── Average Balance Interest Calculation (GS02 — YBANK_ACCOUNTS_ALL)
│   ├── Cash Management Account Names (FDSB)
│   ├── Cash Management Grouping (T038)
│   └── Liquidity Forecasting
│
├── 5. FX & REVALUATION
│   ├── Exchange Rate Differences (OBA1 / T030H)
│   ├── FX Revaluation (FAGL_FC_VAL — month-end)
│   └── Multi-currency bank accounts (USD, EUR, MZN, XAF, etc.)
│
└── 6. BUSINESS AREA & CONTROLS
    ├── Business Area Substitution (YFI_BASU_MOD — GEF for bank postings)
    └── Internal Transfers & Replenishment
```

---

## Knowledge Documents

| Document | Topic | Location |
|----------|-------|----------|
| [house_bank_configuration.md](house_bank_configuration.md) | Full 13-step house bank config procedure + ECO09 patterns | This folder |
| [bank_statement_ebs_architecture.md](bank_statement_ebs_architecture.md) | EBS architecture: MT940 → posting → clearing | This folder |
| [payment_full_landscape.md](payment_full_landscape.md) | Payment landscape: F110, BCM, FBZP, DMEE | This folder |

## Skills

| Skill | Domain Area | Location |
|-------|------------|----------|
| `sap_house_bank_configuration` | Bank Account Management | `.agents/skills/sap_house_bank_configuration/` |
| `sap_account_comparison` | G/L Account Validation | `.agents/skills/sap_account_comparison/` |
| `sap_bank_statement_recon` | Bank Statement / EBS | `.agents/skills/sap_bank_statement_recon/` |
| `sap_payment_bcm_agent` | Payment / BCM | `.agents/skills/sap_payment_bcm_agent/` |
| `sap_payment_e2e` | Payment Process Mining | `.agents/skills/sap_payment_e2e/` |
| `sap_master_data_sync` | G/L Sync P01→D01 | `.agents/skills/sap_master_data_sync/` |

## Companions (HTML Dashboards)

| Companion | Size | Domain Area | Location |
|-----------|------|------------|----------|
| `payment_bcm_companion.html` | 796KB | Payment / BCM / F110 | `Zagentexecution/mcp-backend-server-python/` |
| `bank_statement_ebs_companion.html` | 84KB | EBS / Bank Reconciliation | `Zagentexecution/mcp-backend-server-python/` |
| `epiuse_companion.html` | 32KB | Bank Data Migration | `Zagentexecution/mcp-backend-server-python/` |
| `payment_process_mining.html` | 680KB | Payment E2E Process Mining | `Zagentexecution/mcp-backend-server-python/` |

## Automation Scripts

| Script | Purpose | Location |
|--------|---------|----------|
| `house_bank_compliance_checker.py` | 15-check automated validation for any house bank | `Zagentexecution/mcp-backend-server-python/` |
| `ybank_setleaf_sync.py` | Sync YBANK GS02 sets P01→D01 | `Zagentexecution/mcp-backend-server-python/` |
| `uba01_final_report.py` | Cross-system D01 vs P01 comparison | `Zagentexecution/mcp-backend-server-python/` |
| `uba01_d01_fix.py` | RFC fixes for G/L master data | `Zagentexecution/mcp-backend-server-python/` |

## Configuration Reports

| Date | Bank | Ticket | Status | Location |
|------|------|--------|--------|----------|
| 2026-04-07 | UBA01 (UBA Mozambique) | INC-000005586 | D01 done, P01 pending | `knowledge/configuration_retros/` |

---

## SAP Tables — Treasury Map

### Bank Master Data
| Table | Transaction | Content |
|-------|-----------|---------|
| T012 | FI12 | House bank master (BUKRS + HBKID) |
| T012K | FI12 | Bank accounts (HKTID, BANKN, WAERS, HKONT) |
| T012T | FI12 | Account descriptions |
| BNKA | FI12 | Bank directory (name, address, SWIFT) |
| TIBAN | FI12 | IBAN entries |
| SKA1 | FS00 | G/L chart of accounts (KTOKS=BANK) |
| SKB1 | FS00 | G/L company code (HBKID, FDLEV, XOPVW, ZUAWA) |
| SKAT | FS00 | G/L texts (E/F/P) |

### Bank Statement Processing
| Table | Transaction | Content |
|-------|-----------|---------|
| T035D | SM30 V_T035D | Account symbol → G/L mapping (DISKB → BNKKO) |
| T028B | SM30 V_T035D | Bank key + bank acct → transaction type (XRT940) |
| FCLM_BSM_CUST | FTE_BSM_CUST | Bank statement monitor |
| FEBKO | FF_5 | Bank statement headers |
| FEBEP | FF_5 | Bank statement items |
| FEBRE | FEBAN | Reconciliation records |

### Payment
| Table | Transaction | Content |
|-------|-----------|---------|
| T042I | FBZP | Bank determination for F110 (house bank + clearing G/L) |
| T042IY | FBZP | Available amounts per bank |
| T018V | SM30 V_T018V | Receiving bank clearing accounts |
| T042E | FBZP | Payment methods per company code |

### Cash Management & Reporting
| Table | Transaction | Content |
|-------|-----------|---------|
| SETLEAF | GS02 | YBANK set entries (account lists by currency) |
| SETHEADER | GS02 | Set definitions |
| SETNODE | GS02 | Set hierarchy (parent→child) |
| FDSB | SPRO | Cash management account names |
| T038 | SM30 V_T038 | Cash management grouping |

### Exchange Rate
| Table | Transaction | Content |
|-------|-----------|---------|
| T030H | OBA1 | FX difference accounts per G/L (LKORR, LSREA, LHREA, LSBEW, LHBEW) |

### Business Area
| Table | Transaction | Content |
|-------|-----------|---------|
| Custom (YFI_BASU) | YFI_BASU_MOD | Business area substitution (GEF range 1M-1.2M) |

---

## End-to-End Flow

```
BANK OPENS ACCOUNT
    │
    ▼
1. HOUSE BANK CONFIG ──────────────────────────────────────────────┐
   G/L Accounts (10* bank + 11* clearing)                         │
   House Bank (T012/T012K)                                         │
   OBA1 for non-USD (T030H)                                        │
   EBS config (T035D + T028B)                                      │
   Payment config (T042I + T018V)                                  │
   GS02 sets + TRM5 reports                                        │
    │                                                               │
    ▼                                                               │
2. DAILY OPERATIONS                                                │
    │                                                               │
    ├── INCOMING: Bank Statement (MT940)                            │
    │   T028B → identifies bank                                     │
    │   T035D → maps to G/L                                         │
    │   → Posts to 10* bank account                                 │
    │   → FEBAN clears 11* sub-bank                                 │
    │                                                               │
    ├── OUTGOING: Payment Run (F110)                                │
    │   T042I → selects house bank                                  │
    │   → Posts to 11* clearing account                             │
    │   OBPM4 → generates payment file (XML/SEPA)                   │
    │   → Bank processes payment                                    │
    │   → MT940 confirms (loops back to incoming)                   │
    │                                                               │
    ├── REPORTING: Cash Position (TRM5)                             │
    │   ZCASH/ZCASHFO → bank balances, open items, book balances    │
    │                                                               │
    └── REPORTING: Average Balance (GS02)                           │
        YBANK_ACCOUNTS_ALL → average daily balances by currency     │
    │                                                               │
    ▼                                                               │
3. MONTH-END                                                       │
    FX Revaluation (FAGL_FC_VAL)                                   │
    T030H → posts exchange rate differences on non-USD accounts     │
    │                                                               │
    ▼                                                               │
4. BANK CLOSES ─────────────────────────────────────────────────────┘
   Reverse all config steps (mark as CLOSED, remove from sets/reports)
```

---

## UNESCO Bank Landscape

### House Banks (from T012 in P01)

| House Bank | Bank Name | Country | Currencies | Type |
|-----------|-----------|---------|-----------|------|
| NTB01 | Northern Trust | US | USD | HQ |
| NTB02 | Northern Trust | GB | EUR | HQ |
| CIC01 | CIC | FR | EUR, USD | HQ |
| CRA01 | Credit Agricole | FR | EUR | HQ |
| BNP01 | BNP Paribas | FR | EUR | HQ |
| SOG01 | Societe Generale | FR | EUR, USD | HQ |
| SOG03 | Societe Generale | FR | Multi (AUD,CHF,DKK,GBP,JPY) | HQ |
| CIT04 | Citibank | US | USD | HQ |
| SCB14 | Standard Chartered | — | USD | HQ |
| ECO09 | Ecobank Mozambique | MZ | USD, MZN | FO |
| **UBA01** | **UBA Mozambique** | **MZ** | **USD, MZN** | **FO (NEW)** |
| BST01 | BST (Maputo) | MZ | MZN, USD | FO |
| ECO08 | Ecobank Zimbabwe | ZW | USD, ZAR, ZWG | FO |
| SOG06 | Societe Generale Haiti | HT | USD, HTG | FO |
| + ~80 others | Various field office banks | Global | Multiple | FO |

### Account Numbering Convention
| Range | Type | Prefix | Example |
|-------|------|--------|---------|
| 10xxxxx | Bank account | BK | 1065421 |
| 11xxxxx | Sub-bank / clearing | S-BK | 1165421 |
| 12xxxxx | Additional clearing (rare) | — | 1295012 |
| 13xxxxx | Additional clearing (rare) | — | 1395012 |
| 404xxxx | Deposit accounts | — | 4041011 |

### Payment Methods
| Method | Description | Used By |
|--------|-----------|---------|
| A | Bank transfer (wire) | All HQ + most FO |
| 3 | Pre-numbered check | MZ local (ECO09, UBA01) |
| S | SEPA transfer | EUR payments (SOG01) |
| N | Wire (single payment) | Multi-currency (SOG03) |
| 5 | USD wire | Citibank (CIT04) |
| J | EUR wire | SOG01 |

### Payment Medium Formats
| Format | Usage |
|--------|-------|
| /GGI_XML_CT_UNESCO | All currencies, internal transfers |
| /SEPA_CT_UNES | Euro SEPA payments |
| /CITI/XML/UNESCO/DC_V3_01 | USD payments via Citibank |
