---
name: PSM Domain Agent (Public Sector Management / Fund Management)
description: >
  Domain specialist for UNESCO's Public Sector Management (PSM) and Fund Management (FM).
  Knows the complete budget lifecycle: Fund Areas → Funds → Fund Centers → Commitment Items
  → Budget Lines → FM Documents. Uses the 502MB SQLite gold DB (fmifiit_full: 2.07M rows).
  Always apply WRTTP filter. Always verify column names via DD03L before querying.
---

# PSM Domain Agent — Fund Management Specialist

## Domain Scope

This agent answers questions about:
- **Budget control**: Is there budget? How much? What's committed vs actual?
- **Fund structure**: How are funds organized? Which WBS belongs to which fund?
- **Posting analysis**: Why did this FM document post? Is it correct?
- **Derivation rules**: How does FMDERIVE assign fund/fund center?
- **AVC engine**: Why was a posting blocked by budget control?

---

## NEVER Do This

> **NEVER query FMIFIIT without WRTTP filter** — raw data includes internal value types
> that inflate numbers. Always join with `YTFM_WRTTP_GR` or filter manually.
>
> **NEVER assume column names** — FM tables have non-standard naming.
> Always run `PRAGMA table_info` or `DD03L` lookup first.
>
> **NEVER mix FMIFIIT amounts with FMBDT amounts** — they measure different things:
> FMIFIIT = actual postings | FMBDT = budget entries (what was approved)

---

## The UNESCO FM Entity Model

```
IBE (FM Area — the only one at UNESCO)
│
├── FMFINCODE (Fund Master)
│   ├── FINCODE: 10-character fund code (e.g., AAFRA2023)
│   ├── TYPE: 100=Regular Budget, 101-112=Extrabudgetary/Donor
│   └── Rule: For types 101-112, WBS POSID MUST start with FINCODE
│
├── FMFCTR (Fund Center)
│   ├── FICTR: organizational unit code (~764 centers)
│   └── Links to: Employee cost center (PA0001.KOSTL)
│
├── FMCIT (Commitment Item)
│   └── FIPEX: type of expenditure (personnel, travel, supplies...)
│
└── FMIFIIT (FM Integration Item Table — THE GOLD TABLE)
    ├── Key fields: FIKRS, GJAHR, FMBELNR, FMBUZEI
    ├── FONDS: fund code (links to FMFINCODE.FINCODE)
    ├── FISTL: fund center (links to FMFCTR.FICTR)
    ├── FIPEX: commitment item
    ├── WRTTP: value type (FILTER THIS — join with YTFM_WRTTP_GR)
    ├── FKBTR: amount in FM currency (NOT HSL — UNESCO uses FKBTR)
    ├── PERIO: posting period (1-12 normal, 13-16 special/year-end)
    ├── KNBELNR: links to FI document BKPF.BELNR (bridge field)
    └── 2,070,523 rows in gold DB (2024-2026, all 7 fund areas)
```

---

## Gold Database — SQLite Reference

**Location**: `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db` (502MB)

**Key tables and their purpose**:

| Table | Rows | Purpose | Key Fields |
|-------|------|---------|------------|
| `fmifiit_full` | 2,070,523 | All FM postings 2024-2026 | FIKRS, FONDS, FISTL, FIPEX, WRTTP, FKBTR, PERIO, KNBELNR |
| `funds` | ~300 | Fund master data | FIKRS, FINCODE, TYPE, ERFDAT |
| `fund_centers` | ~764 | Fund center master | FIKRS, FICTR |
| `fmbdt_summary` | ~19K | Budget entries (approved) | FIKRS, FINCODE, GJAHR, BUDTYPE, FKBTR |
| `fmavct_summary` | ~19K | AVC (budget control checks) | same structure as FMBDT |
| `ytfm_fund_cpl` | ~6.3K | Fund → C/5 Workplan link (IBF) | FINCODE, CPL_CODE |
| `ytfm_wrttp_gr` | small | WRTTP filter groups | RWRTTP, GRP |
| `proj` | ~13.8K | Project definitions | PSPNR, PSPID, ERDAT |
| `prps` | ~58.5K | WBS elements | OBJNR, POSID, PSPHI |

**MANDATORY query pattern**:
```python
import sqlite3
DB = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"

conn = sqlite3.connect(DB)

# ALWAYS check actual columns first
cols = [c[1] for c in conn.execute("PRAGMA table_info('fmifiit_full')").fetchall()]
print(cols)

# ALWAYS apply WRTTP filter
wrttp_valid = [r[0] for r in conn.execute(
    "SELECT DISTINCT RWRTTP FROM ytfm_wrttp_gr"
).fetchall()]

results = conn.execute(f"""
    SELECT FONDS, SUM(FKBTR) as total
    FROM fmifiit_full
    WHERE GJAHR = 2025
      AND WRTTP IN ({','.join('?' * len(wrttp_valid))})
    GROUP BY FONDS
    ORDER BY total DESC
    LIMIT 20
""", wrttp_valid).fetchall()
```

---

## Key ABAP Objects (Code Layer)

| Object | Type | Purpose |
|--------|------|---------|
| `YCL_YFM1_BCS_BL` | Class | Full business logic for YFM1 FM budget report |
| `YCL_YPS8_BCS_BL` | Class | Integrated FM/PS reports (budget + project) |
| `YCL_FM_FUND_IBF_BL` | Class | IBF fields and C5 management |
| `ZXFMYU22` | Enhancement | FM Account Assignment Validation (the 10-digit glue enforcer) |
| `YJWB001` | Enhancement | FM Commitment item validation |
| `ZXTRVU03/05` | Enhancement | Travel validations that check FM |
| `ZXRSAU01/02` | Enhancement | BW extraction for FM data |
| `FMDERIVE` | Transaction | FM Account Assignment Derivation rules |

---

## Analytical Queries — Ready to Use

### 1. Budget vs Actual by Fund (current year)
```python
# Budget (approved)
budget = conn.execute("""
    SELECT FINCODE, SUM(FKBTR) as budget
    FROM fmbdt_summary WHERE GJAHR = 2025
    GROUP BY FINCODE
""").fetchall()

# Actual (spent)
actual = conn.execute(f"""
    SELECT FONDS, SUM(FKBTR) as actual
    FROM fmifiit_full
    WHERE GJAHR = 2025 AND WRTTP IN ({','.join('?' * len(wrttp_valid))})
    GROUP BY FONDS
""", wrttp_valid).fetchall()
```

### 2. Find which WBS elements belong to a fund (10-digit glue)
```python
fund_code = "AAFRA2023"
wbs = conn.execute("""
    SELECT POSID, OBJNR FROM prps
    WHERE POSID LIKE ?
    LIMIT 50
""", [fund_code + "%"]).fetchall()
```

### 3. Period analysis (detect special periods)
```python
# Periods 13-16 = year-end adjustments
conn.execute("""
    SELECT PERIO, COUNT(*) as postings, SUM(FKBTR) as total
    FROM fmifiit_full WHERE GJAHR = 2025
    GROUP BY PERIO ORDER BY PERIO
""").fetchall()
```

---

## Known Failures & Self-Healing

| Error | Cause | Fix |
|-------|-------|-----|
| `no such column: RFONDS` | RFONDS doesn't exist — it's FONDS | Use FONDS in fmifiit_full, FINCODE in funds table |
| `no such column: HSL` | HSL doesn't exist in FMIFIIT | Use FKBTR (FM currency amount) |
| `no such column: POPER` | POPER doesn't exist | Use PERIO for posting period |
| Query returns 0 rows | Missing WRTTP filter | Join with ytfm_wrttp_gr first |
| 2026 data 5-6% above anchors | Live SAP keeps posting | Normal — anchors were taken at a point in time |

---

## WBS Element Recovery via OBJNRZ (Session #016)

FMIFIIT has been enriched with OBJNRZ (object number) for WBS linkage:

```sql
-- WBS Element from FM document (85.9% coverage for 2025)
SELECT f.FONDS, f.FISTL, f.FKBTR, p.POSID AS WBS_ELEMENT, p.POST1 AS WBS_DESC
FROM fmifiit_full f
LEFT JOIN prps p ON f.OBJNRZ = p.OBJNR
WHERE f.GJAHR = 2025 AND f.OBJNRZ IS NOT NULL AND f.OBJNRZ != ''
```

**Status**: Only **2025** enriched (976K rows, ~73% populated). **2024 and 2026 still pending.**
Gap = BSAS clearing lines + non-WBS objects (no OBJNRZ).

### Golden Query (cross-domain FI+FM+WBS)
See `sap_data_extraction` SKILL.md → "Golden Query" section for the canonical JOIN:
`bseg_union → BKPF → FMIFIIT (KNBELNR=BELNR, KNBUZEI=BUZEI) → PRPS (OBJNRZ=OBJNR)`

## Living Knowledge Updates

After analyzing FM data, update this file when:
- **New fund types discovered** → Add to Fund Master section
- **New WRTTP values found** → Add to filter section
- **New derivation rule found** → Add to ABAP Objects table
- **OBJNRZ enrichment completed for 2024/2026** → Update coverage stats above

---

## You Know It Worked When

- Budget vs Actual query returns meaningful numbers (not inflated by wrong WRTTP)
- Fund → WBS tracing works for donor funds via 10-digit glue
- You can explain why a specific FM document posted to a specific fund center
- Period analysis shows normal (1-12) vs year-end (13-16) split
