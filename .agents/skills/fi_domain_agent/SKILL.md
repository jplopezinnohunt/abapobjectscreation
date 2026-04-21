---
name: FI Domain Agent (Financial Accounting)
description: >
  Domain specialist for UNESCO's Financial Accounting. Knows GL postings,
  validations (OB28), substitutions (OBBH/YRGGBS00), account determination,
  and the FM-FI bridge (FMIFIIT.KNBELNR = BKPF.BELNR). Key for cross-domain
  analysis: every FM posting has a corresponding FI document.
domains:
  functional: [FI]
  module: [FI]
  process: [B2R, P2P, T2R]
---

# FI Domain Agent — Financial Accounting Specialist

## Domain Scope

This agent answers questions about:
- **GL postings**: BKPF (document header) + BSEG (line items) structure
- **Account validation**: Why was a posting rejected? (OB28 validation rules)
- **Account substitution**: Why did the posting land on a different account? (OBBH/YRGGBS00)
- **FM-FI bridge**: Linking FM documents (FMIFIIT) to FI documents (BKPF)
- **Account determination**: Which GL account gets hit for which posting type?
- **Year-end**: Special periods 13-16, closing procedures

---

## NEVER Do This

> **BKPF IS in the Gold DB** (1.67M rows). bseg_union VIEW (4.7M rows, 32 cols) provides
> all GL line items. FMIFIIT links at line level via BUZEI=KNBUZEI. Use the Golden Query
> (see sap_data_extraction SKILL.md) for complete FI+FM+WBS analysis.
>
> **NEVER modify OBBH substitution rules directly** — they affect ALL financial
> postings. Any change to YRGGBS00 must go through CTS with peer review.
>
> **NEVER ignore special periods (13-16)** — UNESCO year-end adjustments use
> periods 13-16 in both FMIFIIT and BKPF. These are real postings, not errors.

---

## The UNESCO FI Entity Model

```
Company Code (UNESCO = one company code, BUKRS)
│
├── GL Account (SKB1/SKAT)
│   ├── Balance Sheet accounts (assets, liabilities)
│   └── P&L accounts (revenue, expense by commitment item)
│
├── FI Document (BKPF — document header)
│   ├── BELNR: document number (referenced by FMIFIIT.KNBELNR)
│   ├── BLART: document type (SA, KR, RE, ZP...)
│   ├── BUDAT: posting date
│   ├── GJAHR: fiscal year
│   └── MONAT: posting period (1-12 normal, 13-16 special)
│
├── FI Line Item (BSEG — document line)
│   ├── BELNR+BUZEI: composite key
│   ├── HKONT: GL account
│   ├── DMBTR: amount in document currency
│   ├── KOSTL: cost center (HCM link)
│   └── PROJK: WBS element (PS link)
│
├── Validation Rules (OB28 → YJWB001 enhancement)
│   ├── Purpose: Reject postings that violate UNESCO rules
│   └── UNESCO custom: validates FM account assignment completeness
│
└── Substitution Rules (OBBH → YRGGBS00 BAdI exit)
    ├── Purpose: Automatically modify posting fields before save
    ├── YCL_FI_ACCOUNT_SUBST_BL: business logic class
    ├── YCL_FI_ACCOUNT_SUBST_READ: reads substitution config
    └── Custom tables: YTFI_BA_SUBST (substitution rules)
```

---

## Cost Recovery Posting Schema (Session #016)

UNESCO personal cost recovery = 2-line journal entries. 3 streams:

| Stream | BUKRS | BLART | DR GL | CR GL | CR FONDS |
|--------|-------|-------|-------|-------|----------|
| STAFF COST RECOVERY | IIEP | JV | 6046013/6046014 | 7034011 | P3638PSF99/638PSF9000 |
| ITF/COST RECOVERY | IIEP | R1 | 6046013/6046014 | 7022020 | 1143PRVxxx |
| Cost Recovery (field) | UNES | R1 | 6046013/6046014 | 7046013 | 633CRP9003 |

- FIPEX 11 = staff costs, FIPEX 13 = consultants
- UNES GSBER: PFF (debit) → OPF (credit)
- UNES field offices: same FISTL on both DR and CR lines (99%)
- IIEP: TEC/KMM/TRA/RND charge → ADM receives revenue
- 633CRP9003 is the shared CRP pool (87 field offices book to it)

See `project_cost_recovery_analysis.md` for full detail.

---

## FM-FI Bridge (THE KEY CROSS-DOMAIN LINK)

```
FMIFIIT (FM document)          BKPF (FI document)
─────────────────────          ──────────────────
FIKRS  = IBE                   BUKRS  = company code
GJAHR  = fiscal year    ←──→   GJAHR  = fiscal year
FMBELNR = FM doc number        BELNR  = FI doc number
KNBELNR = FI doc number ───→   BELNR  ✅ (bridge field!)
PERIO  = FM period      ←──→   MONAT  = FI period
FKBTR  = FM amount      ≈      DMBTR  = FI amount (may differ by rounding)
```

**Bridge query** (execute AFTER BKPF is extracted):
```python
# Link FM posting to its FI document
conn.execute("""
    SELECT f.FONDS, f.FISTL, f.FKBTR,
           b.BELNR, b.BLART, b.BUDAT
    FROM fmifiit_full f
    JOIN bkpf b ON f.KNBELNR = b.BELNR AND f.GJAHR = b.GJAHR
    WHERE f.GJAHR = 2025
      AND f.FONDS = 'AAFRA2023'
    LIMIT 50
""").fetchall()
```

**Status**: ✅ BKPF EXTRACTED (1.67M rows in Gold DB, Session #012). bseg_union VIEW created (4.7M rows, 32 cols). FM-FI bridge is ACTIVE. Use the Golden Query in `sap_data_extraction` SKILL.md for complete FI+FM+WBS analysis.

---

## Substitution Architecture

The UNESCO substitution system is 3-layer:

```
Layer 1: Standard SAP OBBH
         → calls substitution exit
Layer 2: YRGGBS00 (BAdI: FI_SUBSTITUTION_BTE)
         → SAP standard exit for substitutions
Layer 3: YCL_FI_ACCOUNT_SUBST_BL (UNESCO class)
         → actual business logic
         → reads rules from YTFI_BA_SUBST
         → can redirect GL account, add FM assignment, etc.
```

**Expert seed available**: `YRGGBS00_SOURCE.txt` (105 KB) + `YCL_FI_ACCOUNT_SUBST_BL_METHODS.txt`
→ Load these via brain: `python sap_brain.py --node SEED_YRGGBS00_SOURCE`

---

## Key ABAP Objects (Code Layer)

| Object | Type | Purpose | Seed Available? |
|--------|------|---------|----------------|
| `YRGGBS00` | Enhancement | BAdI FI_SUBSTITUTION_BTE exit | ✅ YRGGBS00_SOURCE.txt (105KB) |
| `YCL_FI_ACCOUNT_SUBST_BL` | Class | Substitution business logic | ✅ BL_METHODS.txt (11KB) |
| `YCL_FI_ACCOUNT_SUBST_READ` | Class | Reads substitution configuration | ✅ READ_METHODS.txt |
| `YFI_ACCOUNT_SUBSTITUTION` | Program | FI account substitution program | ✅ YFI_ACCOUNT_SUBSTITUTION.txt |
| `YJWB001` | Enhancement | FM/FI validation exit (OB28) | Not extracted |
| `YENH_FI_DMEE` | Enhancement | DMEE payment format enhancement | Not extracted |
| `YENH_RFBIBL00` | Enhancement | FI document posting enhancement | Not extracted |
| `ZFIX_EXCHANGERATE` | Enhancement | Exchange rate fix | Not extracted |
| `YCEI_FI_SUPPLIERS_PAYMENT` | Enhancement | Supplier payment | Not extracted |

---

## Analytical Patterns

### 1. Find substituted postings (why did account change?)
```python
# Check substitution log via CDHDR (change documents)
conn.execute("""
    SELECT OBJECTCLAS, OBJECTID, UDATE, USERNAME, CHANGENR
    FROM cdhdr  -- needs extraction
    WHERE OBJECTCLAS = 'BKPF'
      AND UDATE BETWEEN '20250101' AND '20251231'
    LIMIT 100
""")
```

### 2. Identify validation failures (from system logs — not yet in DB)
```python
# When SM21 system logs extracted:
# Look for message class: FU (FI validation messages)
# Or query BKPF for documents that were "parked" (not fully posted)
```

### 3. Special period analysis
```python
conn.execute("""
    SELECT MONAT, COUNT(*) as docs, SUM(DMBTR) as total
    FROM bkpf  -- needs extraction
    WHERE GJAHR = 2025
    GROUP BY MONAT
    ORDER BY MONAT
""")
# Periods 13-16 = year-end adjustments — normal at UNESCO
```

---

## Known Failures & Self-Healing

| Error | Cause | Fix |
|-------|-------|-----|
| FM-FI join returns 0 | BKPF not yet in SQLite | Extract BKPF/BSEG first (pending task) |
| Substitution logic not clear | YRGGBS00 is complex multi-layer | Start with YRGGBS00_SOURCE.txt expert seed |
| Validation error in OB28 | YJWB001 exits needs extraction | Extract YJWB001 source via ADT before debugging |
| Amount mismatch FM vs FI | Rounding or currency conversion | Check TWAER (transaction currency) in FMIFIIT |

---

## Extraction Status (Session #016)

| Object | Status | Rows | Notes |
|--------|--------|------|-------|
| BKPF (FI doc headers) | ✅ Done | 1,677,531 | FM-FI bridge ACTIVE |
| bseg_union (6-table VIEW) | ✅ Done | 4,735,764 | BSIS+BSAS+BSIK+BSAK+BSID+BSAD |
| BSIS/BSAS enriched | ✅ Done | 3,771,961 | +13 fields (KOSTL, AUFNR, PRCTR, FKBER, SGTXT, etc.) |
| CDHDR+CDPOS (change docs) | ✅ Done | 7,810,913 | Config change audit trail |
| T001B (posting periods) | 🟡 Pending | — | Explains open/closed periods |

### BSEG Direct Access (Session #016 Discovery)
BSEG has been **declustered** in P01 — readable via RFC_READ_TABLE. Do NOT include MANDT in WHERE clause. Use for PROJK (WBS internal key) extraction. The Celonis UNION pattern remains primary for bulk data.

---

## Living Knowledge Updates

After analyzing FI data, update this file when:
- **Substitution rule decoded** → Add to substitution architecture section
- **New validation discovered** → Add to ABAP Objects table
- **Year-end pattern confirmed** → Document special period volumes
- **BSEG PROJK extracted** → Update WBS recovery section

---

## You Know It Worked When

- FM-FI bridge query returns rows ✅ (BKPF extracted, bridge ACTIVE)
- Golden Query works: bseg_union → BKPF → FMIFIIT → PRPS (WBS element)
- You can trace: FM posting → GL account → cost center → fund center chain
- Substitution rules explained: why posting X ended up on GL account Y
- Validation failures identified: which OB28 rule blocked which document type
