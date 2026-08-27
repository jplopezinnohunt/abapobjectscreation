# sap_transport_intelligence — referencia detallada

> Extraído de `SKILL.md` para que su cuerpo no ocupe contexto en cada turno.
> Lo carga quien lo necesite; el índice está en `SKILL.md`.

## Part 10 — AI Classification Pipeline (Scenario B — Bulk Mining)

### Step 1: Extract Full Transport Record from E07x

```python
# Confirmed working RFC pattern for UNESCO D01
SELECT a~trkorr, a~trfunction, a~trstatus, c~as4text,
       a~tarsystem, a~as4user, a~as4date,
       b~pgmid, b~object, b~obj_name,
       b~objfunc, b~lockflag,
       d~devclass
FROM e070 AS a
INNER JOIN e071 AS b ON a~trkorr = b~trkorr
INNER JOIN e07t AS c ON c~trkorr = a~trkorr
LEFT JOIN tadir AS d ON d~obj_name = b~obj_name
                     AND d~object = <TADIR_OBJECT_TYPE>  # Map obj_type → TADIR type!
INTO TABLE @DATA(et_transport)
WHERE a~as4date IN @s_date
AND b~object IN @s_obj.
```

> [!IMPORTANT]
> **TADIR object type mapping is mandatory**: `TABU → TABL`, `VDAT → VIEW`, `CLAS → CLAS`, `PROG → PROG`, `FUGR → FUGR`. Without the correct OBJECT type filter in the TADIR join, you get wrong packages.

### Step 2: Object Classification

For each E071 row, classify into:

```python
CATEGORY = {
    'DEV':          ['PROG', 'CLAS', 'FUGR', 'TABL', 'VIEW', 'DTEL', 'DOMA', 'ENQU', 'INTF', 'TRAN'],
    'CUSTOMIZING':  ['TABU', 'SOBJ'],
    'PLATFORM':     ['SICF', 'IWSG', 'IWOM', 'WAPA', 'SUCU'],
    'SECURITY':     ['SUCU', 'PROF'],  # + any AGR_* obj_name pattern
    'SCHEMA':       ['NROB', 'DEVC'],
    'ARTIFACT':     ['TDDAT'],         # + auto-FUGR Z*_MAINT pattern
    'DANGEROUS':    [],                # OBJFUNC in ('D', 'M')
    'EXECUTABLE':   ['XPRA'],
}

IMPACT_TIER = {
    'CRITICAL': ['T030', 'T001B', 'NROB', 'T043', 'T880', 'T512W', 'T549Q'],  # + OBJFUNC M/D
    'HIGH':     ['T011', 'SKA1', 'SKB1', 'TABL', 'DOMA', 'XPRA', 'T510'],
    'MEDIUM':   ['PROG', 'CLAS', 'FUGR', 'SICF', 'IWSG', 'T003', 'T004F'],
    'LOW':      ['TRAN', 'DEVC', 'DTEL', 'TVARVC'],
}

MODULE_MAP = {
    # HR
    'T511': 'HR', 'T512W': 'HR', 'T512Z': 'HR', 'T510': 'HR', 'T549A': 'HR',
    'T549Q': 'HR', 'T554S': 'HR', 'T554C': 'HR', 'T503': 'HR', 'T001P': 'HR',
    # PSM-FM
    'FMCI': 'PSM-FM', 'FM01': 'PSM-FM', 'FMZUOB': 'PSM-FM', 'T043': 'PSM-FM',
    # PS
    'OPST': 'PS', 'OPS_BUKRS': 'PS', 'T420': 'PS', 'PROJ': 'PS-ALARM', 'PRPS': 'PS-ALARM',
    # Bank
    'T012': 'BANK', 'T012K': 'BANK', 'T042': 'BANK', 'T042Z': 'BANK', 'T042I': 'BANK',
    # FI/GL
    'T030': 'FI-CRITICAL', 'T001B': 'FI-CRITICAL', 'T030R': 'FI-CRITICAL',
    'T001': 'FI', 'SKA1': 'FI', 'SKB1': 'FI', 'T011': 'FI', 'T003': 'FI',
    'T077S': 'FI', 'T880': 'FI', 'T004F': 'FI', 'T004': 'FI',
}
```

### Step 3: Is New vs Modified Detection

```python
def is_new_in_target(obj_name, object_type, tadir_target_cache):
    """Object is NEW if it doesn't exist in target TADIR."""
    key = (object_type, obj_name)
    return key not in tadir_target_cache

def signal_from_description(as4text):
    """Heuristic from transport description."""
    as4text_lower = as4text.lower()
    if any(w in as4text_lower for w in ['create', 'initial', 'new', 'baseline']):
        return 'NEW'
    if any(w in as4text_lower for w in ['fix', 'correction', 'patch', 'change', 'sprint']):
        return 'MODIFIED'
    return 'UNKNOWN'
```

### Step 4: LLM Prompt Pattern for Single Transport Review (Scenario A)

```
You are an SAP BASIS and functional transport expert.
Analyze the following transport request and provide:
1. Is each object NEW or MODIFIED in the target system?
2. Is each object an auto-generated artifact or intentional development?
3. Business impact of importing this transport to production.
4. CRITICAL risks: account determination, number ranges, deletions, payroll, budget.
5. Required sign-offs before production import.

Transport data: [E070+E071+E071K JSON]
Target TADIR snapshot: [relevant OBJ_NAME entries from target]
Module context: [FI | HR | PSM | Fiori | Security | ...]
OBJFUNC summary: [list any non-blank OBJFUNC values]
```

### Key AI Rules (Encoded from Experience)

- Never trust the object list alone — always cross-reference with export log RC code
- TABU entries require E071K key data to be meaningful
- Logical objects (AGR_\*, NROB) have empty E071K — different resolution logic
- OBJFUNC must always be explicitly checked — blank is NOT the same as safe
- FUGR requires comparison of ALL function modules in the group, not just the changed FM
- **Always flag these for human sign-off regardless of AI confidence**: T030, T030R, T001B, NROB, XPRA, OBJFUNC D/M, AGR_\* with SUCU, T512W during open payroll, PROJ/PRPS

---

## Part 11 — RFC Extraction Code (Confirmed Working on UNESCO D01)

```python
# Extract E071 with TADIR join for package — UNESCO pattern
from pyrfc import Connection
import os
from dotenv import load_dotenv

load_dotenv()
conn = Connection(
    ashost=os.getenv('SAP_HOST'),
    sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'),
    user=os.getenv('SAP_USER'),
    passwd=os.getenv('SAP_PASSWORD')
)

# E071 objects
result = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='E071',
    OPTIONS=[{'TEXT': "TRKORR LIKE 'D01K9%'"}],  # adjust pattern
    FIELDS=[
        {'FIELDNAME': 'TRKORR'}, {'FIELDNAME': 'PGMID'},
        {'FIELDNAME': 'OBJECT'}, {'FIELDNAME': 'OBJ_NAME'},
        {'FIELDNAME': 'OBJFUNC'}, {'FIELDNAME': 'LOCKFLAG'}
    ],
    ROWCOUNT=5000
)

# E071K for TABU keys
keys_result = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='E071K',
    OPTIONS=[{'TEXT': "TRKORR LIKE 'D01K9%' AND OBJECT = 'TABU'"}],
    FIELDS=[
        {'FIELDNAME': 'TRKORR'}, {'FIELDNAME': 'OBJ_NAME'},
        {'FIELDNAME': 'TABKEY'}
    ],
    ROWCOUNT=5000
)

# TADIR package lookup — OBJECT type filter is MANDATORY
# Map obj_type → TADIR OBJECT: TABU→TABL, VDAT→VIEW, PROG→PROG, CLAS→CLAS
TADIR_TYPE_MAP = {
    'TABU': 'TABL', 'CLAS': 'CLAS', 'PROG': 'PROG', 'FUGR': 'FUGR',
    'TABL': 'TABL', 'VIEW': 'VIEW', 'DTEL': 'DTEL', 'DOMA': 'DOMA',
    'TRAN': 'TRAN', 'DEVC': 'DEVC', 'SICF': 'SICF', 'IWSG': 'IWSG',
    'IWOM': 'IWOM', 'WAPA': 'WAPA', 'ENQU': 'ENQU', 'INTF': 'INTF',
}
# Skip: SOTR, VARX, LIMU (GUID keys or subobject — RFC_READ_TABLE fails with SAPSQL_DATA_LOSS)
SKIP_TADIR_TYPES = {'SOTR', 'VARX', 'LIMU', 'LANG', 'NROB'}
```

---
