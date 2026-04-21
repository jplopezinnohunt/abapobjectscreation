---
name: SAP Change Audit (CDHDR/CDPOS)
description: >
  Configuration and master data change audit trail using CDHDR (Change Document Headers)
  and CDPOS (Change Document Items). Maps SAP transaction codes to human-readable activities
  via 100+ rules. Foundation for process mining event logs and compliance auditing.
  Gold DB: CDHDR 7.8M rows (2024-2026).
domains:
  functional: [Support, FI]
  module: [*]
  process: []
---

# SAP Change Audit — CDHDR/CDPOS Intelligence

## Purpose

Answer: **Who changed what, when, and from which transaction?**

CDHDR/CDPOS is the SAP audit trail for ALL configuration and master data changes.
This skill maps raw change documents to process activities for:
1. **Compliance auditing** — Who modified GL accounts, fund rules, vendor masters?
2. **Process mining** — CDHDR events feed pm4py for DFG/variant analysis
3. **Transport correlation** — Cross-reference config changes with CTS deployments
4. **Root cause analysis** — "Why did posting behavior change after March 15?"

---

## NEVER Do This

> [!CAUTION]
> - **NEVER query CDHDR without date filter** — 7.8M rows will exhaust memory
> - **NEVER assume OBJECTCLAS maps 1:1 to a table** — OBJECTCLAS is a semantic grouping (e.g., 'BELEG' = multiple doc types)
> - **NEVER ignore CDPOS** — CDHDR is headers only; CDPOS has the actual field-level changes (old value → new value)
> - **NEVER use CDHDR for transactional document changes** — CDHDR tracks MASTER DATA/CONFIG changes, not posting events. Use BKPF for posting audit.

---

## Key Tables

| Table | Rows | Purpose | Key Fields |
|-------|------|---------|------------|
| `cdhdr` | 7,810,913 | Change document headers | OBJECTCLAS, OBJECTID, CHANGENR, USERNAME, UDATE, UTIME, TCODE |
| `cdpos` | (loaded with CDHDR) | Change document items (field-level) | OBJECTCLAS, OBJECTID, CHANGENR, TABNAME, FNAME, VALUE_OLD, VALUE_NEW |

## CDHDR Object Classes (Most Common at UNESCO)

| OBJECTCLAS | SAP Object | Domain | Example TCODEs |
|------------|-----------|--------|----------------|
| BELEG | FI Documents | FI | FB01, FB02, MIRO |
| KRED | Vendor Master | MM | MK01, MK02, XK01 |
| DEBI | Customer Master | SD | FD01, FD02 |
| EINKBELEG | Purchase Documents | MM | ME21N, ME22N, ME23N |
| BANF | Purchase Requisitions | MM | ME51N, ME52N |
| MATERIAL | Material Master | MM | MM01, MM02 |
| PREL | HR Master Data | HCM | PA30, PA40 |
| PFCG | Role/Auth | Basis | PFCG |
| FMMD | FM Master Data | PSM | FMSA, FMCI |

---

## Activity Mapping (100+ Rules)

The `cdhdr_activity_mapping.py` script maps TCODE → human-readable activity name:

```python
TCODE_ACTIVITY_MAP = {
    # Procurement (P2P)
    'ME21N': 'Create Purchase Order',
    'ME22N': 'Change Purchase Order',
    'ME23N': 'Display Purchase Order',
    'ME51N': 'Create Purchase Requisition',
    'MIRO':  'Invoice Receipt',
    'MIGO':  'Goods Receipt',

    # Finance (FI)
    'FB01':  'Post FI Document',
    'FB02':  'Change FI Document',
    'F110':  'Payment Run',
    'F-28':  'Incoming Payment',
    'F-53':  'Outgoing Payment',

    # Fund Management (PSM)
    'FMBB':  'Budget Entry',
    'FR50':  'Funds Reservation',
    'FMZA':  'FM Account Assignment',
    'FMZ1':  'FM Master Data Change',

    # HR (HCM)
    'PA30':  'Maintain HR Master Data',
    'PA40':  'Personnel Actions',
    'PA20':  'Display HR Master Data',
    # ... 60+ more rules
}
```

### Mapping Logic

```python
def get_activity(row):
    """Map CDHDR row to activity name."""
    tcode = row.get('TCODE', '')
    objectclas = row.get('OBJECTCLAS', '')

    # 1. Try exact TCODE match
    if tcode in TCODE_ACTIVITY_MAP:
        return TCODE_ACTIVITY_MAP[tcode]

    # 2. Fall back to OBJECTCLAS-based activity
    if objectclas == 'BELEG':
        return f'FI Document Change ({tcode})'
    elif objectclas == 'EINKBELEG':
        return f'Procurement Change ({tcode})'

    # 3. Unknown — log for future mapping
    return f'Unknown ({objectclas}/{tcode})'
```

---

## Analytical Queries

### 1. Who changed configuration recently?
```sql
SELECT USERNAME, TCODE, COUNT(*) as changes,
       MIN(UDATE) as first_change, MAX(UDATE) as last_change
FROM cdhdr
WHERE UDATE >= '20260301'
  AND OBJECTCLAS IN ('FMMD', 'PFCG', 'TABL')
GROUP BY USERNAME, TCODE
ORDER BY changes DESC
LIMIT 20;
```

### 2. FM master data changes (fund/fund center modifications)
```sql
SELECT c.USERNAME, c.TCODE, c.UDATE, c.OBJECTID,
       p.TABNAME, p.FNAME, p.VALUE_OLD, p.VALUE_NEW
FROM cdhdr c
JOIN cdpos p ON c.OBJECTCLAS = p.OBJECTCLAS
             AND c.OBJECTID = p.OBJECTID
             AND c.CHANGENR = p.CHANGENR
WHERE c.OBJECTCLAS = 'FMMD'
  AND c.UDATE >= '20250101'
ORDER BY c.UDATE DESC
LIMIT 50;
```

### 3. Vendor master changes (compliance audit)
```sql
SELECT c.USERNAME, c.UDATE, c.OBJECTID AS VENDOR,
       p.FNAME AS FIELD_CHANGED, p.VALUE_OLD, p.VALUE_NEW
FROM cdhdr c
JOIN cdpos p ON c.OBJECTCLAS = p.OBJECTCLAS
             AND c.OBJECTID = p.OBJECTID
             AND c.CHANGENR = p.CHANGENR
WHERE c.OBJECTCLAS = 'KRED'
  AND c.UDATE BETWEEN '20250101' AND '20251231'
ORDER BY c.UDATE DESC;
```

### 4. Generate process mining event log
```python
# Feed to pm4py via sap_process_discovery.py
import pandas as pd

events = conn.execute("""
    SELECT OBJECTCLAS || '-' || OBJECTID AS case_id,
           TCODE AS activity,
           UDATE || UTIME AS timestamp,
           USERNAME AS resource
    FROM cdhdr
    WHERE UDATE >= '20250101'
    ORDER BY UDATE, UTIME
""").fetchall()

df = pd.DataFrame(events, columns=['case:concept:name', 'concept:name',
                                     'time:timestamp', 'org:resource'])
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `extract_cdhdr.py` | RFC extraction with checkpoint/merge (7.8M rows) |
| `cdhdr_activity_mapping.py` | 100+ TCODE→activity rules |
| `sap_process_discovery.py` | pm4py engine (consumes CDHDR events) |

---

## Compliance Report Template

Run this query to generate a compliance-ready change audit report for a given period:

```sql
-- Compliance Report: Config & Master Data Changes (UNESCO SAP)
-- Scope: High-risk object classes (vendor master, roles, FM config, FI docs)
-- Period: Adjust dates as needed

SELECT
    c.UDATE          AS change_date,
    c.UTIME          AS change_time,
    c.USERNAME        AS user_id,
    c.OBJECTCLAS      AS object_class,
    c.OBJECTID        AS object_id,
    c.TCODE           AS transaction,
    p.TABNAME         AS table_changed,
    p.FNAME           AS field_changed,
    p.VALUE_OLD       AS old_value,
    p.VALUE_NEW       AS new_value
FROM cdhdr c
JOIN cdpos p
    ON  c.OBJECTCLAS = p.OBJECTCLAS
    AND c.OBJECTID   = p.OBJECTID
    AND c.CHANGENR   = p.CHANGENR
WHERE c.UDATE BETWEEN '20260101' AND '20260331'  -- adjust period
  AND c.OBJECTCLAS IN (
      'KRED',      -- Vendor master
      'PFCG',      -- Roles & authorizations
      'FMMD',      -- FM master data
      'BELEG',     -- FI documents
      'EINKBELEG'  -- Purchase documents
  )
ORDER BY c.UDATE DESC, c.UTIME DESC;
```

### Compliance Report Variants

**Segregation of Duties — same user created + changed within 24h**:
```sql
SELECT c1.USERNAME, c1.OBJECTCLAS, c1.OBJECTID,
       MIN(c1.UDATE) as created, MAX(c2.UDATE) as modified,
       COUNT(*) as change_count
FROM cdhdr c1
JOIN cdhdr c2 ON c1.OBJECTID = c2.OBJECTID
             AND c1.OBJECTCLAS = c2.OBJECTCLAS
             AND c1.USERNAME = c2.USERNAME
             AND c1.CHANGENR <> c2.CHANGENR
WHERE c1.UDATE >= '20260101'
  AND c1.OBJECTCLAS IN ('KRED', 'FMMD')
GROUP BY c1.USERNAME, c1.OBJECTCLAS, c1.OBJECTID
HAVING COUNT(*) > 1
ORDER BY change_count DESC;
```

**Vendor master changes — high-value fields** (bank account, IBAN, payment terms):
```sql
SELECT c.USERNAME, c.UDATE, c.OBJECTID AS vendor,
       p.FNAME AS field, p.VALUE_OLD, p.VALUE_NEW
FROM cdhdr c
JOIN cdpos p ON c.OBJECTCLAS = p.OBJECTCLAS
             AND c.OBJECTID = p.OBJECTID
             AND c.CHANGENR = p.CHANGENR
WHERE c.OBJECTCLAS = 'KRED'
  AND p.FNAME IN ('BANKL','BANKN','IBAN','ZTERM','SPERR','LOEVM')
  AND c.UDATE >= '20260101'
ORDER BY c.UDATE DESC;
```

**After-hours or weekend changes** (risk indicator):
```sql
SELECT c.USERNAME, c.UDATE, c.UTIME, c.OBJECTCLAS, c.OBJECTID, c.TCODE,
       CASE CAST(strftime('%w', substr(c.UDATE,1,4)||'-'||substr(c.UDATE,5,2)||'-'||substr(c.UDATE,7,2)) AS INTEGER)
           WHEN 0 THEN 'Sunday'
           WHEN 6 THEN 'Saturday'
           ELSE 'Weekday'
       END AS day_type
FROM cdhdr c
WHERE c.UDATE >= '20260101'
  AND c.OBJECTCLAS IN ('KRED','FMMD','PFCG')
  AND (
      CAST(strftime('%w', substr(c.UDATE,1,4)||'-'||substr(c.UDATE,5,2)||'-'||substr(c.UDATE,7,2)) AS INTEGER) IN (0,6)
      OR CAST(substr(c.UTIME,1,2) AS INTEGER) NOT BETWEEN 7 AND 19
  )
ORDER BY c.UDATE DESC;
```

## Integration Points

- **Process Mining**: CDHDR events → pm4py DFG/variants (via `sap_process_mining` skill)
- **Transport Intel**: Correlate config changes with CTS transport dates
- **FI Domain**: OBJECTCLAS='BELEG' traces FI document modifications
- **PSM Domain**: OBJECTCLAS='FMMD' traces fund/fund center changes
- **Brain**: CDHDR nodes feed CHANGE_PATTERN edges in knowledge graph

---

## Known Failures

| Error | Cause | Fix |
|-------|-------|-----|
| CDPOS JOIN returns 0 | CHANGENR mismatch or CDPOS not loaded | Verify both tables loaded with same extraction scope |
| CDHDR extraction DATA_LOSS | Pagination bug on large months | Use day-by-day extraction (see `sap_data_extraction` skill) |
| Activity mapping returns 'Unknown' | TCODE not in mapping | Add new rule to `cdhdr_activity_mapping.py` |
| UDATE/UTIME format inconsistent | SAP date = YYYYMMDD, time = HHMMSS | Concatenate as string, parse with `datetime.strptime('%Y%m%d%H%M%S')` |

---

## You Know It Worked When

1. CDHDR query returns rows filtered by OBJECTCLAS and date range
2. Activity mapping converts 90%+ of TCODEs to readable names
3. Process mining event log generates valid DFG with pm4py
4. You can answer "who changed fund X's budget rules last month?"
