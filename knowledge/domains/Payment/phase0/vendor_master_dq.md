# Vendor Master Data Quality — ADRC Compliance Audit

**Phase 0 deliverable** · Session #62 · 2026-04-24 · Evidence tier: TIER_1 (SQL against Gold DB `p01_gold_master_data.db`)

## Query — handoff doc §7.2 (adapted to Gold DB)

```sql
SELECT COUNT(*)
FROM LFA1 l
JOIN ADRC a ON l.ADRNR = a.ADDRNUMBER
WHERE (a.CITY1 IS NULL OR a.CITY1 = '' OR a.COUNTRY IS NULL OR a.COUNTRY = '')
  AND (l.LOEVM IS NULL OR l.LOEVM = '')
```

## Results — as of P01 snapshot Apr 2026

| Metric | Count | % of active |
|---|---|---|
| Total active LFA1 vendors (LOEVM blank) | 111,241 | 100% |
| Active vendors with valid ADRC join | 111,238 | 99.997% |
| **Missing CITY1 OR COUNTRY** | **5** | **0.005%** |
| Missing CITY1 | 1 | 0.001% |
| Missing COUNTRY | 4 | 0.004% |
| Missing STREET | 5,570 | 5.01% |
| Missing POST_CODE1 | 1,153 | 1.04% |
| Missing HOUSE_NUM1 | 76,574 | 68.84% |

## CBPR+ compliance impact

Per handoff doc §2.1 and §7.2, **only `TwnNm` (=CITY1) and `Ctry` (=COUNTRY) are MANDATORY** under ISO 20022 structured or hybrid address. All other fields (StrtNm/BldgNb/PstCd) are recommended but their absence only downgrades to Hybrid mode, which is still CBPR+-valid through 2026 (and beyond, with stricter bank spec).

| Compliance level | Vendor count ready | Vendor count blocked |
|---|---|---|
| **Survival (Hybrid minimum: TwnNm+Ctry)** | 111,236 (99.995%) | **5** |
| Preferred (full structured: all 5 fields) | ~32,000 | ~79,000 (missing BldgNb/StrtNm/PstCd) |

## [VERIFIED] conclusion

**Compliance survival is secured.** Only 5 vendors need manual cleanup of CITY1/COUNTRY before go-live. This is a **hard-fail-if-missing** fix, not a systemic cleanup.

The BldgNb (HOUSE_NUM1) 68.8% miss is cosmetic — under Hybrid mode, missing BldgNb does not reject the file. Some banks may push for fully-structured stricter compliance post-2026; in that case, vendor master cleanup becomes a separate project (out of scope here).

## Implications for the plan

1. **Phase 1**: request the 5 specific vendor IDs from Master Data team; fix by manual LFA1/ADRC update before V01 UAT
2. **Phase 2**: no data-cleanup blocker for config start
3. **Phase 3-4**: Hybrid-mode tests will pass for 99.995% of vendors; the 5 are the known edge cases
4. **Post-go-live**: monitor ADRC data quality; new vendors must have CITY1+COUNTRY populated or F110 rejects the item

## Risk level: **LOW**

Previously in the plan this was flagged as a potential major risk gating Phase 3. This audit downgrades it to LOW.

## Query for the 5 vendors (execute in Phase 1 for cleanup)

```sql
SELECT l.LIFNR, l.NAME1, a.CITY1, a.COUNTRY, a.STREET, a.POST_CODE1, a.HOUSE_NUM1
FROM LFA1 l
JOIN ADRC a ON l.ADRNR = a.ADDRNUMBER
WHERE (a.CITY1 IS NULL OR a.CITY1 = '' OR a.COUNTRY IS NULL OR a.COUNTRY = '')
  AND (l.LOEVM IS NULL OR l.LOEVM = '')
ORDER BY l.LIFNR;
```

(Pending execution — will populate this doc with vendor list.)

## Data source

- Database: `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`
- Tables: LFA1 (111,241 active) + ADRC (joined via LFA1.ADRNR = ADRC.ADDRNUMBER)
- ADRC has additional temporal filter available (DATE_FROM/DATE_TO) — handoff SQL omits it but Gold DB snapshot was single point-in-time so the simple join is representative
