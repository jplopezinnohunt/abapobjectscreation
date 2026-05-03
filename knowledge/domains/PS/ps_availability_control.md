# PS-AVC at UNESCO — Availability Control on Project Budgets

> Established Session #66 (2026-05-01) following the INC-000005638 extension. Anchored in TIER_1 RFC pulls of BPGE/BPJA/COSP/COSS/FMAVCT/FMAFMAP013500109 against P01.

UNESCO runs PS-AVC (Project System Availability Control) **simultaneously** with FM-AVC. Both engines see PO/SES/invoice lines coded to a WBS-element-with-fund-link and both can refuse a posting. This document covers PS-AVC; the sibling document `knowledge/domains/PSM/fm_ps_connectivity_bw_bridge.md` §4 covers the two-engine misalignment.

## 1. Scope and core tables

PS-AVC operates on **project objects** (WBS elements). The WBS object number convention: `PR<8-digit-PSPNR>` (e.g. `PR00050949`). Cardinality at UNESCO: 58,516 WBS elements in `PRPS`, hard-linked to 13,878 projects in `PROJ`.

| Concern | Table | Key | UNESCO row count (2024-2026) |
|---|---|---|---:|
| Annual budget by value type | `BPGE` | OBJNR + WRTTP + GEBER + VERSN | 654 (sparse for projects) |
| Cumulative budget by value type and year | `BPJA` | OBJNR + WRTTP + GJAHR + GEBER + VERSN | 134,139 (heavy use) |
| Project header for PS-AVC | `BPHI` | OBJNR + WRTTP + HIERA + GEBER + VERSN | 0 for `PR%` (UNESCO uses fund headers `FK*` instead) |
| CO totals primary | `COSP` | OBJNR + GJAHR + WRTTP + KSTAR + HRKFT | 226,475 |
| CO totals secondary | `COSS` | OBJNR + GJAHR + WRTTP + KSTAR + HRKFT | **0** for `PR%` (UNESCO does not use secondary on projects) |
| Budget change docs | `BPDJ` | LEDNR + TRGKZ + WRTTP + BELNR + BUZEI | 0 for 2024-2026 (UNESCO uses fmbh/fmbl for budget changes) |
| Project hierarchy | `PRPS` / `PROJ` | PSPNR / PSPHI | 58,516 / 13,878 |

Source: `Zagentexecution/sap_data_extraction/extract_ps_avc_tables.py` (Session #66 RFC pulls).

## 2. Value types (WRTTP) used by PS-AVC

| WRTTP | Meaning | Used in (UNESCO) |
|---:|---|---|
| 41 | Current budget (after revisions) | BPJA, primary PS-AVC budget input |
| 42 | Original budget | BPJA |
| 51 | Plan | BPGE (rare on projects) |
| 54 | Annual budget release | (configured but rare) |
| 04 | Actuals primary | COSP |
| 22 | Commitments | COSP |
| 24 | Plan | COSP |
| 2A | Reservations | COSP |

The PS-AVC pool calculation at UNESCO uses primarily **BPJA WRTTP=41 cumulative** vs **COSP WRTTP=04+22 cumulative**.

## 3. Pool computation (TIER_1)

```sql
WITH proj_wbs AS (
  SELECT OBJNR FROM prps WHERE substr(POSID,1,10) = :fund
)
SELECT
  (SELECT SUM(signed(WTJHR)) FROM bpja_2024 WHERE WRTTP='41' AND OBJNR IN proj_wbs)
+ (SELECT SUM(signed(WTJHR)) FROM bpja_2025 WHERE WRTTP='41' AND OBJNR IN proj_wbs)
+ (SELECT SUM(signed(WTJHR)) FROM bpja_2026 WHERE WRTTP='41' AND OBJNR IN proj_wbs)
- (SELECT SUM(signed(WTG001..WTG003)) FROM cosp_2024+cosp_2025+cosp_2026 WHERE WRTTP IN ('04','22') AND OBJNR IN proj_wbs)
AS ps_pool_available;
```

`signed()` flips SAP's trailing-`-` minus convention into a numeric value. Period buckets WTG001..WTG016 hold transaction-currency amounts; UNESCO uses TWAER='USD' so WTG = USD directly.

## 4. AVC profile and tolerance — KU still open

The OPSV transaction (PS-AVC profile maintenance) and table T185I (PS-AVC tolerance limits) are not in P01 DD03L (probably renamed in S/4 versions or stored as SPRO transports). Without them we cannot empirically determine:

- Whether UNESCO's PS-AVC enforces annual-only, cumulative-only, or both.
- The exact % tolerance per project profile (60/80/95/100%?).
- Which value categories (T185F mapping) trigger which AVC group.

Inferred from data (TIER_2): PS-AVC at UNESCO appears to enforce **cumulative-only**, otherwise the 196EAR4042 project (with $13M of 2026 actuals against $3.5M of 2026 budget but $20.4M of cumulative budget) would have raised BP604 long ago. Open known unknown: `KU-2026-005638-04`.

## 5. Block messages

| Message | Engine | Trigger |
|---|---|---|
| `BP603` "Budget exceeded by 1,234.56 USD" | PS-AVC cumulative | Cumulative pool < 0 across the project + value-category combo |
| `BP604` "Annual project budget exceeded" | PS-AVC annual | BPJA WRTTP=41 for the year < cumulative consumption that year |
| `BP629` "Available amount exceeded by 1,234.56 USD in fiscal year 2026" | PS-AVC year-aware | Year-locked pool variant |

The reporter on INC-000005638 said "insuffisance de budget" (which is **ambiguous**) — but the empirical pool computation showed PS-AVC was NOT firing (project pool +$16.43M). The block was FM-AVC raising FMAVC005 against the AVC-derived TC bucket.

## 6. Cross-reference: when PS-AVC and FM-AVC desync

See `knowledge/domains/PSM/fm_ps_connectivity_bw_bridge.md` §4 for the misalignment class definition and the tier counts. Summary: at UNESCO, **PS-AVC at WBS-level** and **FM-AVC at AVC-derived-bucket level** measure different things and update on different schedules. Either can refuse a posting independently; both must pass for a transaction to commit.

## 7. Reference scripts (Session #66)

- `Zagentexecution/sap_data_extraction/extract_ps_avc_tables.py` — pulls all PS-AVC tables from P01.
- `Zagentexecution/quality_checks/inc5638_per_po_engine_analysis.py` — per-PO PS-pool computation, with FM-pool comparison.
- `Zagentexecution/quality_checks/inc5638_fm_ps_avc_misalignment.py` — UNESCO-wide classifier.

## 8. Known unknowns (PS-AVC specific)

- `KU-2026-005638-04` — OPSV / T185I configuration for UNESCO (PS-AVC tolerance profiles).
- `KU-2026-005638-06` — Anomalies in BPJA/COSP for outlier projects 410GLO1043 (-$107M PS pool) and 727MYA1002 (-$2.67B PS pool) — likely data quality issues.

---

## 9. Session 2026-05-01 schema discoveries (TIER_1)

Re-extraction Session 2026-05-01 confirmed the following empirical facts about UNESCO's PS-AVC at the schema level:

### 9.1 BPGE — extremely sparse for projects

Even after broadening `WHERE OBJNR LIKE 'PR%' AND WRTTP IN (41,42,51,54,60,61,01)` the table holds only **654 rows** total for projects:
- WRTTP=01 (released budget, project-aggregate snapshot): 651 rows
- WRTTP=41 (current budget): 3 rows
- WRTTP 42, 51, 54, 60, 61: **0 rows each**

Conclusion: UNESCO does NOT use BPGE as a primary PS-AVC pool source for PR-prefixed objects. The annual cumulative budget lives in **BPJA WRTTP=41** (134,139 rows for 2024-2026). BPGE on UNESCO is essentially a historical / planning-only artefact.

### 9.2 BPHI — empty for PR objects

`OBJNR LIKE 'PR%'` returns **0 rows** in BPHI. UNESCO's project hierarchy is held in `PRPS` / `PROJ`, not in BPHI. PS-AVC at UNESCO does **not** rely on BPHI for hierarchy roll-up; the cumulative pool is computed by walking PRPS.POSID prefixes (10-digit project root → ↑ to fund) directly.

### 9.3 COSS — empty for PR objects

`OBJNR LIKE 'PR%'` returns **0 rows** in COSS for 2024, 2025, 2026. UNESCO does not allocate to projects via secondary cost ledgers. All PS consumption is in **COSP** WRTTP=04 (actuals primary) and WRTTP=22 (commitments).

### 9.4 OPSV — TABLE_NOT_AVAILABLE in P01

`SELECT * FROM OPSV` raises `DA/E/131 TABLE_NOT_AVAILABLE` on P01. Either the table was renamed in this S/4 release or the PS-AVC profile is held in a different DD object (candidates: `OPSV_S4`, `BUTL_*`, transport-only customizing). New KU `KU-2026-005638-OPSV` opened to track this. The Session #66 inference that PS-AVC at UNESCO is "cumulative-only" remains TIER_2 until OPSV (or its successor) is read.

### 9.5 BP603 / BP604 / BP629 — confirmed as PS-AVC messages

The PS-AVC engine raises BP603 (cumulative deficit), BP604 (annual deficit), BP629 (year-locked variant). The reporter on INC-000005638 saw "notification en rouge" — but the empirical pool computation showed PS-AVC was NOT firing (project pool +$16.43M). The block was FM-AVC raising **FMAVC005** against the AVC-derived TC bucket. **Therefore, when an UNESCO user reports "insuffisance de budget", do NOT default to PS-AVC; the FM-AVC bucket-level pool must be checked first.**

### 9.6 FM-vs-PS misalignment class — re-confirmed 2026-05-01

| Tier | Definition | Count (2026-05-01) |
|---|---|---:|
| Tier 1 | BOTH FM and PS blocking | 488 |
| Tier 2 | FM blocking only — the INC-000005638 class | **1,517** |
| Tier 3 | PS blocking only | 90 |
| Tier 4 | Neither | 386 |
| no_ps_link | FM only, no project | 4,264 |

The Tier 2 footprint grew +60 buckets (+4.1%) in the 4 weeks since Session #66 → structural misalignment is **actively widening**, not isolated to one fund.

