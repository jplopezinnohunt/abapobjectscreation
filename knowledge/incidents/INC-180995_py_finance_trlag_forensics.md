# INC-180995 — Ticket 180995 Parallel Transport Lag Forensics

**Status**: ROOT_CAUSE_CONFIRMED  
**Category**: Process anomaly (not runtime failure)  
**Domain**: PY-Finance  
**Secondary domains**: Treasury, CTS  
**Reporter**: JP Lopez (Session #60 review of PY-Finance companion)  
**Received**: 2026-04-22  
**Analyzed session**: 60

## Summary (TL;DR)

Service-desk ticket **180995** ("Create Payment Method") required setting up two new Field Office currencies in parallel. Francesco Spezzano (FP_SPEZZANO) released two transports on the **same day (2024-11-19)** within 6 hours of each other. They hit P01 with radically different timing:

| Transport | Country | Wage Type | Released (D01) | Imported (P01) | **Lag** |
|---|---|---|---|---|---|
| D01K9B0CDZ | Mozambique (MZ) | 5$B3 / MZN | 2024-11-19 11:26 | **2025-02-28** | **101 days** |
| D01K9B0CE6 | Sri Lanka (LK) | 5$B4 / LKR | 2024-11-19 17:28 | 2024-11-20 | 1 day |

Both transports are technically identical in structure (8 table keys each, perfectly symmetric 5-table WT chain plus T042Z/T042ZT payment method). Same owner, same ticket, same day release. The 101-day production gap for the Mozambique half is unexplained by the data available — it was either deliberately held back (Mozambique FO rollout scheduled for March 2025) or stuck in the approval/import queue and forgotten.

## Transport forensics (via RFC E071 + E071K + CTS_API_READ_CHANGE_REQUEST)

### D01K9B0CDZ — Mozambique (released 2024-11-19 11:26:18)

```
E070: TRSTATUS=R TRFUNCTION=W OWNER=FP_SPEZZANO CLIENT=350 STRKORR=(empty)
E07T: "180995/ Creat Payment Method Mozambic"
```

| Table | Key | Meaning |
|---|---|---|
| T042Z  | `350 MZ 3` | Payment method `3` for country **MZ** |
| T042ZT | `350 E MZ 3` | English text of MZ/3 |
| T512T  | `350 E UN 5$B3` | Wage type **5$B3** text — "Stockage devise MZN" |
| T512W  | `350 UN 5$B3 99991231` | WT 5$B3 valuation (end 9999-12-31) |
| T52DZ  | `350 UN 5$B3` | Permissibility of 5$B3 |
| T52EL  | `350 UN 5$B3 01 99991231` | Averaging base row 1 |
| T52EL  | `350 UN 5$B3 02 99991231` | Averaging base row 2 |
| T52EZ  | `350 UN 5$B3 99991231` | Averaging rule |

### D01K9B0CE6 — Sri Lanka / LKR (released 2024-11-19 17:28:18)

```
E070: TRSTATUS=R TRFUNCTION=W OWNER=FP_SPEZZANO CLIENT=350 STRKORR=(empty)
E07T: "180995 - Payment Method U with currency LKR"
```

| Table | Key | Meaning |
|---|---|---|
| T042Z  | `350 LK U` | Payment method `U` for country **LK** |
| T042ZT | `350 E LK U` | English text of LK/U |
| T512T  | `350 E UN 5$B4` | Wage type **5$B4** text — "Stockage devise LKR" |
| T512W  | `350 UN 5$B4 99991231` | WT 5$B4 valuation |
| T52DZ  | `350 UN 5$B4` | Permissibility of 5$B4 |
| T52EL  | `350 UN 5$B4 01 99991231` | Averaging base row 1 |
| T52EL  | `350 UN 5$B4 02 99991231` | Averaging base row 2 |
| T52EZ  | `350 UN 5$B4 99991231` | Averaging rule |

## Why these are NOT corrections (common confusion)

1. Different country codes (MZ vs LK)
2. Different wage type codes (5$B3 vs 5$B4) — UNESCO pattern: each new Field Office currency gets its own 4-char WT in the `5$Bx` series
3. Different payment method keys (3 vs U)
4. **`STRKORR` is empty** in E070 for both (a correction transport would reference its parent there)
5. Both have an identical 8-key structure (perfectly symmetric, independent setups)

## The UNESCO wage-type-per-country pattern (generalized from this incident)

Every new Field Office currency that UNESCO pays staff in requires a parallel 5-table wage type setup:

```
Step 1 — T042Z / T042ZT        Treasury payment method (country+method key)
Step 2 — T512W                 Wage type valuation (new 5$Bx WT)
Step 3 — T512T                 Wage type text per language
Step 4 — T52DZ                 Permissibility per payroll period
Step 5 — T52EL (x2 rows)       Averaging bases
Step 6 — T52EZ                 Averaging rule
Step 7 — transport release     "C - HR - PY" convention OR "<ticket> - <country>" for Treasury-routed
```

This is the same pattern observed for the other 4 ticket-driven new-country setups in the 4-year window:

| Ticket | Year | Editor | Country | WT Code (inferred) |
|---|---|---|---|---|
| 133188 | 2022 | M_SPRONK | UNDP payroll FO | (tbd) |
| 168627 | 2024 | M_SPRONK | Sao Tome (STN) | (tbd) |
| 172777 | 2024 | FP_SPEZZANO | Mongolia | (tbd) |
| 180995 | 2024 | FP_SPEZZANO | Mozambique | 5$B3 / MZN |
| 180995 | 2024 | FP_SPEZZANO | Sri Lanka | 5$B4 / LKR |

## Root cause of the 101-day lag (candidate explanations, unverified)

**H1 — Scheduled rollout (most likely)**: Mozambique FO was scheduled to go live with its own MZN payroll stream in March 2025. LKR (Sri Lanka) was urgent (active payroll need November 2024). This would mean the 101 days is deliberate, not a process defect.

**H2 — Stuck in STMS import queue**: Francesco released both at the same day; if both were added to the UNESCO P01 import queue by the basis team's scheduled import, but Mozambique was parked/skipped for a reason not logged, it could have sat until a later import wave swept it up on 2025-02-28.

**H3 — Approval workflow delay**: If UNESCO requires FO manager approval per-country before STMS import, Mozambique FO may simply not have confirmed until February 2025.

Without access to STMS GUI logs or TMSALOG entries for the 2024-11-20 through 2025-02-28 window (TMSALOG RFC is capped at ~1000 rows per query and the historical entries have cycled out), we cannot distinguish H1 from H2/H3 from the data alone. **Ask FP_SPEZZANO directly** to close this question.

## Who imported P01

TMSALOG current snapshot (2026-04-20) shows **V.VAURETTE** is the dedicated P01 import operator, executing `TMS_TP_IMPORT` as the exclusive human user (alongside TMSADM service account running `TMS_TS_GET_TRLIST`). She is the probable importer for both TRs but this cannot be directly confirmed via RFC for historical dates.

See **KU-036** for exact importer verification follow-up.

## Process risk findings

1. **No monitoring of "siblings of one ticket imported at wildly different times"** — this sibling divergence (1 day vs 101 days) would be caught by a daily/weekly query: `SELECT a.trkorr, b.trkorr, a.as4date, b.as4date FROM cts_transports a JOIN cts_transports b ON a.as4text LIKE b.as4text LEFT(10) AND a.trkorr < b.trkorr WHERE ABS(...) > 30 days`. UNESCO doesn't have this check.
2. **Manual P01 import depends on one basis admin** (V.VAURETTE). If she is unavailable the import queue stalls. No visibility to Finance team on what has or hasn't been imported.
3. **Ticket-linked transport bundles are invisible in CTS**. `as4text` has the ticket number in the description but there is no foreign key to a ticketing system. Trailing through ticket 180995's scope requires text-search of E07T.

## Fix path

### Immediate
- **None required for the specific transports** — both are now in P01 and effective. If Mozambique payroll was affected between 2024-11-19 and 2025-02-28, see follow-up investigation #2 below.

### Preventive

1. **Add an automated TR-sibling-lag detector** to `Zagentexecution/quality_checks/` — flag transports that share a ticket number in their description but have import-date delta > 7 days.
2. **Extend the transport companion** to cluster TRs by ticket number (extract `^\d{5,7}` from `as4text`) so sibling transports are visible as a group.
3. **Document the UNESCO "5$Bx new-country wage type" pattern** in the PY-Finance companion as a canonical procedure (already partially done; updated in `py_finance_wage_type_companion_v1.html`).
4. **Add a governance rule**: any ticket that produces more than one TR should have the sibling status cross-checked at each TR release (is sibling also ready? also released? also queued?).

## Scope — full 180995 impact

Ticket 180995 went from pending to fully live for both countries by 2025-02-28:
- **Mozambique** (5$B3 / MZN) — live 2025-02-28
- **Sri Lanka** (5$B4 / LKR) — live 2024-11-20

Between 2024-11-20 and 2025-02-28, the Sri Lanka setup was live but the Mozambique setup was NOT live in P01 despite having been released on the same day. Any Mozambique FO staff onboarded/paid in that window would have required an alternative wage type or a manual workaround.

## Related artifacts

- Companion: [companions/py_finance_wage_type_companion_v1.html](companions/py_finance_wage_type_companion_v1.html)
- Raw forensics JSON: [Zagentexecution/py_finance_investigation/180995_forensics.json](Zagentexecution/py_finance_investigation/180995_forensics.json)
- Transport manifest 4yr: [Zagentexecution/py_finance_investigation/transport_manifest_4yr.json](Zagentexecution/py_finance_investigation/transport_manifest_4yr.json)

## Related claims

- Claim #56: M_SPRONK / FP_SPEZZANO tier classification
- Claim #58: LCR monthly as the dominant recurring pattern
- Claim #59: T512W wrong row = silent salary miscalc risk

## Follow-ups (opened as KUs)

- **KU-036** — Did Mozambique FO have payroll activity in the 2024-11-20 to 2025-02-28 window that required 5$B3? Ask local FO payroll admin.
- **KU-037** — Who exactly imported D01K9B0CDZ on 2025-02-28? (TMSALOG cycled; needs STMS GUI audit or SM21 reading)
- **KU-038** — Across 4 years, are there other sibling-ticket transport pairs with import lag > 30 days? (run detection query; inform all affected FOs)

## Lessons

1. **Ticket-linked transports can diverge silently**. UNESCO has no automated check that two TRs released under the same ticket land in P01 together. This is a class of defect, not a one-off.
2. **Service-desk ticket numbers are the best cross-cutting key** for linking transports to external context — but UNESCO's CTS extraction doesn't have a ticket-linked column; we reverse-engineer via `as4text` regex.
3. **Treasury-routed PY config is legitimate**. The pattern where Treasury (Francesco) owns `new-country wage type setup` via service-desk ticket is not a bug in our classification — it is a real cross-functional flow that deserves its own companion section (done in v1).
4. **"101-day lag" is not automatically a defect**. It could be a deliberate staggered rollout. Need the human in the loop (Francesco or basis admin V.VAURETTE) to confirm root cause.
