# Session #046 Retro — Upgrade 2026: Open Customizing Requests

**Date:** 2026-04-07 to 2026-04-08
**Duration:** Extended session (2 days)
**Previous:** #045 (Post-transport audit + treasury companion rewrite)

## What We Did

### 1. Problem Discovery
- User reported SAP upgrade pre-check error: "Open Data Extraction Requests" blocking transport import
- Identified SAP Notes 1081287, 1083709, 328181 as relevant
- Built `check_open_extraction_requests.py` — scans P01 for open requests across 6 table families (SCPR_CTRL, SCC_TMS_HDR, E070, T000, SCC3-related)

### 2. P01 Investigation (7 Open Requests Found)
- Built `analyze_open_transports.py` — deep extraction of E070/E071/E071K/E07T per transport
- All 7 are customizing requests (TRFUNCTION='W') with status D (Modifiable) in P01 client 350
- Owners: HIPER (4), A_SEFIANI (1), I_KONAKOV (1), FP_SPEZZANO (1)
- 19 total objects across HCM, PSM-FM, Workflow, FI-BANK, FI, MM, BASIS

### 3. D01 Cross-System Comparison
- Built `compare_open_transports_d01.py` — found 54 open requests in D01
- Detected 3 cross-system object conflicts (V_001_B, ADDRESS, ADDRESS_4.6) between P01K950279 and D01K9B0CBF

### 4. Landscape Violation Analysis (NEW PATTERN)
- All 7 P01 requests are landscape violations — customizing done directly in production
- Root cause classification: 2x CONFIGURATION_DRIFT, 2x PERIOD_SENSITIVE, 2x EMERGENCY, 1x AUDIT_DRIVEN
- HIPER has 4/7 P01 requests but 0 in D01 — works exclusively in production
- Updated `sap_transport_companion` skill with Step 1b (landscape violation detection)
- Created `feedback_p01_landscape_violation.md` memory

### 5. Live Data Comparison (P01 vs D01) — THE REAL VERIFICATION
- Built `compare_p01_d01_objects.py` — reads actual table values from both systems via RFC
- Built `compare_house_banks.py` — T012T text comparison
- Built `check_t77hrfpm.py` — resolved table name (T77HRFPM_CLOSING, not CLSNG)

**Results (7 tables compared):**

| Table | Verdict | Detail |
|-------|---------|--------|
| T77HRFPM_CLOSING | **IDENTICAL** | 2 rows match. Requests were junk. |
| VBWF15 | **IDENTICAL** | 9 rows match. Emergency WF fix never saved. |
| T163K | **DRIFT** | P01 has extra KNTTP='S' (service entry tolerance) |
| T100C | **INVERSE** | D01 has 4 extra rows. D01 ahead, no P01 risk. |
| T012T | **DRIFT** | 3 "CLOSED-----" bank labels in P01 not in D01 |
| T001 | **DRIFT** | XPROD flag on 4 company codes (ICTP/MGIE/UIL/ICBA) — audit fix |
| TABADRH | **DRIFT** | Biennium UNESCO2025-26 in P01 vs UNESCO2020 in D01 |

### 6. Companion Created
- `companions/upgrade_2026_v01_open_customizing_requests.html` — 8 tabs, standalone
- Tabs: Situation, Landscape Violations, Request Detail (7), Conflict Map, Resolution Plan, D01 Comparison, Data Comparison (P01 vs D01), Prevention Protocol
- Initially embedded as tab in treasury companion — user correctly directed it to its own root companion under Support & Maintenance

### 7. Skill Evolution
- `sap_transport_companion/SKILL.md` updated with Step 1b (landscape violation detection) and template section 2b

## Key Discoveries

1. **Transport request existence does NOT prove data drift.** 3 of 7 requests had zero actual data changes. Must always verify with live comparison.
2. **VBWF15 was the biggest scare — turned out to be nothing.** Original analysis rated it CRITICAL. Live data: identical.
3. **TABADRH biennium drift is the real bomb.** D01 has `UNESCO2020`, P01 has `UNESCO2025-26`. Upgrade would revert 6 years of biennium config.
4. **XPROD audit flag (T001) is a compliance risk.** 4 company codes marked productive per audit, not in D01.
5. **T77HRFPM_CLSNG is actually T77HRFPM_CLOSING.** SAP view names truncate table names.
6. **HIPER works only in P01** — systematic pattern, not one-off.

## Verification Check (Principle 8)
- **Assumption challenged:** "FP_SPEZZANO's payment workflow change (VBWF15) would be lost during upgrade" — **CORRECTED.** Live comparison proves zero drift.
- **Gap identified:** T012K (house bank accounts) could not be compared via RFC (TABLE_WITHOUT_DATA). Only T012T texts compared.
- **Claim probed:** "TABADRH biennium 2020 in D01 would be overwritten during upgrade" — **CONFIRMED.** Real and dangerous.

## Deliverables (10)

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | Upgrade 2026 Companion (8 tabs) | `companions/upgrade_2026_v01_open_customizing_requests.html` |
| 2 | P01 open request scanner | `Zagentexecution/mcp-backend-server-python/check_open_extraction_requests.py` |
| 3 | Transport deep analyzer | `Zagentexecution/mcp-backend-server-python/analyze_open_transports.py` |
| 4 | D01 cross-system comparator | `Zagentexecution/mcp-backend-server-python/compare_open_transports_d01.py` |
| 5 | Live data comparator (7 tables) | `Zagentexecution/mcp-backend-server-python/compare_p01_d01_objects.py` |
| 6 | House bank text comparator | `Zagentexecution/mcp-backend-server-python/compare_house_banks.py` |
| 7 | Table name resolver | `Zagentexecution/mcp-backend-server-python/check_t77hrfpm.py` |
| 8 | Transport companion skill update | `.agents/skills/sap_transport_companion/SKILL.md` (Step 1b) |
| 9 | Landscape violation memory | `memory/feedback_p01_landscape_violation.md` |
| 10 | Comparison results JSON | `Zagentexecution/mcp-backend-server-python/p01_d01_comparison_results.json` |

## Patterns Established

1. **Landscape violation detection** — P01K* + TRFUNCTION='W' = always a violation, classify root cause
2. **Live data verification** — never trust transport request existence alone
3. **Companion scoping** — upgrade readiness is cross-functional, not a sub-tab of domain companions
4. **Pre-upgrade checklist** — scan → classify → compare → sync → resolve → verify
5. **Root cause taxonomy** — EMERGENCY, PERIOD_SENSITIVE, AUDIT_DRIVEN, CONFIGURATION_DRIFT, SYSTEM_FORCED

## Pending → Next Session

1. **MANDATORY before upgrade:** Sync 4 tables to D01 (T001 XPROD, TABADRH biennium, T012T closed labels, T163K KNTTP='S')
2. **Delete safe requests:** P01K950265, P01K950267, P01K950275 (verified no drift)
3. **Coordinate with HIPER:** P01K950269 (CF complete?), P01K950277 (bank rename), P01K950279 (audit applied?)
4. **T012K comparison:** Retry with field splitting to compare house bank accounts
5. **Monthly P01 scan:** Schedule recurring check for new production customizing requests
