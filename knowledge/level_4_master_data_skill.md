# Level 4: Master Data Reconstruction & Pattern discovery

This skill level focuses on the extraction and analysis of SAP Master Data (Funds, Projects, Funds Centers, etc.) to understand the structure of UNESCO's business entities.

## 1. Tactical Objective
Identify patterns in master data creation and relationships (e.g., Fund -> Project -> WBS) by analyzing high-quality, recent data (2024+) from Dev (D01) or Production (P01) systems.

## 2. Core Master Data Entities (The "Pattern" Tables)

| Domain | Entity | Table | Creation Date Field | Key Identifying Field |
| :--- | :--- | :--- | :--- | :--- |
| **PSM-FM** | **Fund** | `FMFINCODE` | `ERFDAT` | `FINCODE` |
| **PSM-FM** | **Funds Center** | `FMFCTR` | `ERFDAT` | `FICTR` |
| **PS** | **Project Def.** | `PROJ` | `ERDAT` | `PSPID` |
| **PS** | **WBS Element** | `PRPS` | `ERDAT` | `POSID` |
| **HCM** | **Employee** | `PA0001` | `AEDTM` (Last mod) | `PERNR` |

## 3. Extraction Protocol (Level 4)

### Phase A: Date-Filtered Discovery (RFC_READ_TABLE)
To avoid "noise" from 20+ years of legacy data, **always** filter by creation date >= 2024.
```python
# Rule: Create Date >= 2024-01-01
query_table.py FMFINCODE --options "ERFDAT >= '20240101'"
```

### Phase B: Cross-System Master Data Read (D01 <-> P01)
If the Dev system (D01) has cluttered or non-representative data:
1.  **Remote Read**: Use the specialized `sap_utils.py` with `system_id='P01'`.
2.  **Target System**: P01 contains the "Golden Copy" of master data patterns. Use this ONLY for reading (Master Data Reference).

### Phase C: Pattern Mapping (Bridge Discovery)
Identify how IDs connect. Example pattern discovered:
- `PROJ-PSPID` (10 chars) matches `FMFINCODE-FINCODE` (10 chars).
- `PRPS-POSID` (WBS) contains `PROJ-PSPID` as a prefix (Hierarchical link).

## 4. Master Data Audit Checklist
- [ ] **Creation User Scan**: Identify if data is created by System Users (e.g., `MULESOFT`) vs. Functional Users (e.g., `N_MENARD`).
- [ ] **Status Audit**: Check `STAT` or `OBJNR` in `JEST` table to see the typical lifecycle status for new items.
- [ ] **Custom Fields**: Scan for `ZZ*` fields that store UNESCO-specific metadata (Donors, Regions).

---
> [!IMPORTANT]
> **Level 4 is for Data Structure understanding**, not transaction auditing. Focus on the *Definition* and *Configuration* of the entities.
