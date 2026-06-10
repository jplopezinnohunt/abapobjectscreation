# FX Revaluation — Closing Calendar & Timing Analysis (2025 Production)

**Domain**: Closing Activities  
**Activity**: FX Revaluation (F.05 / SAPF100)  
**Data source**: P01 BKPF / BSIS (11,793 F.05 docs 2025)  
**Session**: #078 — 2026-06-05  
**Companion**: `companions/closing_activities_v1.html`  
**Prior deep research**: `knowledge/domains/Treasury/fx_revaluation_2025_agi_research.md`

---

## 1. Process Architecture (confirmed from production)

All FX revaluation at UNESCO is **100% manual**. No SAPF100 background jobs exist. Accountants post directly via FBB1 (manual GL posting). The F.05 SAPF100 program exists and is configured (T044A, T030H, OBA1) but is not scheduled in SM36.

**Pattern**: Every institute runs a two-step monthly cycle:
- **Last day of month** (BUDAT = last day): Post FX valuation — unrealized gain/loss to accounts 0006045011 / 0007045011
- **Day 1 of following month** (BUDAT = 1st): Reverse prior month valuation

Both steps are posted manually via FBB1.

SAPF124 (automatic clearing) **does** run as a background job daily — infrastructure and JOBBATCH user exist. SAPF100 should follow the same pattern.

---

## 2. Responsible Users per Institute

| Institute | Primary User | Backup | TCODE | Coverage |
|-----------|-------------|--------|-------|----------|
| UNES (HQ) | J_LA | I_WETTIE, EZ_MOYO (year-end) | FBB1 / FB50 | All months 2025 |
| UIL | DB_ABDI | None identified | FBB1 | All months 2025 |
| IBE | V_KOHEMUN | None identified | FBB1 | All months 2025 |
| ICBA | A_MULUGETA | E_GEBREMARIA | FBB1 | All months 2025 |
| ICTP | M_VENUTI | **NONE — SINGLE POINT OF FAILURE** | FBB1 | 10/12 months (July+Nov missed) |
| IIEP | F_CADIO | S_COURONNAUD | FBB1 | All months 2025 |
| MGIE | P_ARORA | K_BHATIA | FBB1 | All months — ANOMALOUS pattern |
| UBO | P_TUCKER | None identified | FBB1 | All months 2025 |
| UIS | N_MOUSSA | L_SANNEH (year-end only) | FBB1 | All months 2025 |

---

## 3. Valuation Timing — Days After Month-End

**Definition**: CPUDT (actual computer entry date) minus BUDAT month-end (last day of month). Positive = entered N days after month closed. Zero = entered on last day.

| Institute | User | Avg Lag (d) | Min (d) | Max (d) | Typical Pattern | Status |
|-----------|------|------------|---------|---------|----------------|--------|
| ICBA | E_GEBREMARIA | 1.6 | 0 | 5 | Day 0-2 | ✅ Best |
| ICBA | A_MULUGETA | 3.7 | 0 | 5 | Day 1-4 | ✅ Good |
| UIS | N_MOUSSA | 3.7 | 0 | 8 | Day 1-5 | ✅ Good |
| IIEP | S_COURONNAUD | 3.9 | 1 | 8 | Day 1-5 | ✅ Good |
| IIEP | F_CADIO | 5.1 | 0 | 12 | Day 1-6 | ✅ Acceptable |
| MGIE | P_ARORA | 5.1 | -15 | 20 | Mid-month entries | ⚠️ Anomalous |
| UNES | J_LA | 6.7 | 0 | 62 | Day 5-22, large variance | ⚠️ Variable |
| ICTP | M_VENUTI | 7.6 | 2 | 55 | Day 2-8, spikes | ⚠️ Spikes |
| UIL | DB_ABDI | 8.0 | 1 | 20 | Day 1-3 | ✅ Consistent |
| IBE | V_KOHEMUN | 9.0 | 2 | 18 | Day 2-7 | ✅ Acceptable |
| UBO | P_TUCKER | 24.3 | 4 | 62 | Day 4-30+ | 🔴 Chronic late |
| UIS | L_SANNEH | 50.7 | 10 | 90 | Year-end only | ⚠️ Actuarial |
| UNES | EZ_MOYO | 56.0 | 30 | 90 | Year-end actuarial | ⚠️ Year-end |

---

## 4. Reversal Timing — Days After Day-1 BUDAT

**Definition**: CPUDT of reversal posting minus BUDAT (which = 1st of month). Measures how late the reversal is entered after the new period opens.

| Institute | User | Avg Lag (d) | Max (d) | Status |
|-----------|------|------------|---------|--------|
| ICBA | E_GEBREMARIA | 0.5 | 2 | ✅ Near real-time |
| IIEP | F_CADIO | 3.4 | 8 | ✅ Good |
| IBE | V_KOHEMUN | 4.6 | 12 | ✅ Acceptable |
| UBO | P_TUCKER | 4.2 | 15 | ✅ OK |
| ICTP | M_VENUTI | 4.7 | 33 | ⚠️ Spikes |
| UNES | J_LA | 11.8 | 40 | 🔴 Systematically late — reversal entered mid-month, not day-1 |

The UNES reversal lag of 11.8 days means the prior month's unrealized FX exposure sits in the books for nearly 2 weeks of the new period. Given UNES has the largest FX volume and 1,014 T030H rows, this is the most significant process gap.

---

## 5. Flags and Critical Issues

### 🔴 ICTP — 2 missed months (July + November 2025)

- M_VENUTI posted day-1 reversals for both months (10 reversal documents each)
- Zero corresponding month-end valuation documents found for either month
- Consequence: 2 months of FX exposure not recognized; reversals posted with nothing to reverse
- Root cause: M_VENUTI was absent/unavailable; no backup user
- Risk: will recur in 2026 if no backup is assigned

### 🔴 UBO — Chronic late posting (avg 24d lag)

- P_TUCKER routinely enters revaluation 3-4 weeks after month-end
- Worst case: 62 days (over 2 months late)
- No backup user for UBO
- UBO financial statements reflect FX exposure with significant delay

### 🔴 UNES — Reversal systematically delayed (avg 11.8d)

- J_LA's day-1 reversals average 11.8 days into the new month
- For the largest co-code by volume, 2 weeks of exposure overlap creates reporting risk
- Max observed: 40 days late on a reversal

### 🟡 MGIE — Mid-month posting pattern (not standard month-end)

- P_ARORA shows negative lag values — FX entries are sometimes posted mid-month, before month-end
- This does not match the standard last-day valuation / day-1 reversal pattern
- K_BHATIA (avg 14d lag) handles some months
- MGIE is the smallest co-code by FX volume (3 blocked accounts in SKB1); risk is lower but pattern is unclear and should be documented

### 🟡 No formal closing gate

- SAP period lock (OB52 / MMPV) does not wait for FX revaluation sign-off
- A period can close with revaluation missing — this is exactly how ICTP's July/November gaps occurred silently

---

## 6. T030H Configuration Defects (Root Cause of "Blocked for Posting" Errors)

From OBA1 / T030H analysis (1,014 rows in KTOPL=UNES):

| Issue | Count | Impact |
|-------|-------|--------|
| Empty LSBEW / LHBEW / LKORR (defective rows) | 200 rows | F.05 cannot post — skips silently |
| Blocked LKORR accounts | 383 T030H rows | 290 distinct blocked accounts used as LKORR |
| Active HKONTs with blocked LKORR (live error generators) | 17 HKONTs | "Account XXXX is blocked for posting" error at runtime |

**Specific error (session trigger)**: Account 0001109574 is LKORR for active HKONTs 0001010574 and 0001110574. Account 0001109574 = closed Banco de Chile CLP account (XSPEB=X, labelled "CLOSED S-BK BANCO DE CHILE-UNESCO SANTIAGO CLP").

**Fix**: OBA1 → KDF procedure → update LKORR for the 17 active HKONTs. Either point to a valid active account or clear LKORR (if balance-sheet adjustment posting is not required).

---

## 7. Proposed Month-End Close Calendar

```
DAY          ACTIVITY                        CURRENT STATE        TARGET STATE
─────────────────────────────────────────────────────────────────────────────────────
Day 1        REVERSE prior month FX          Manual via FBB1      SM36 job: SAPF100
(new month)  SAPF100 reversal variant        0-40d lag            reversal, 06:00 AM

Day 25-28    REVALUE open FX positions       Manual via FBB1      SM36 job: SAPF100
(same month) SAPF100 valuation variant       4-62d lag (varies)   last biz day, 23:00

Day 28-31    FX SIGN-OFF                     NO GATE EXISTS       Controller sign-off
             Controller confirms reval        Period can close     required before
             is complete before period lock   without FX done      OB52 period lock

Day last     PERIOD LOCK                     OB52 / MMPV         After FX gate only
             FI period closed
─────────────────────────────────────────────────────────────────────────────────────
SAPF124 (automatic clearing) already runs daily via JOBBATCH — infrastructure exists.
SM36 SAPF100 jobs follow the same pattern: JOBBATCH + per-BUKRS variants.
```

---

## 8. Automation Roadmap

| # | Action | Owner | Effort | Blocks |
|---|--------|-------|--------|--------|
| 1 | Create SM36 jobs for SAPF100 — 9 BUKRS × 2 variants (reval + reversal) | BASIS + Treasury | Medium | Eliminates all manual lag |
| 2 | Fix T030H LKORR — 17 active HKONTs pointing to blocked accounts (OBA1 → KDF) | FI Config | Low | Stops "blocked for posting" errors |
| 3 | Assign backup users for ICTP and UBO | Treasury Controller | Low | Eliminates single-point-of-failure |
| 4 | Add FX sign-off gate before OB52 period lock | Finance Controller | Low | Prevents silent missed months |
| 5 | Extract VARI/VARID to Gold DB — audit which GL ranges each variant covers | Agent | Low | Currently unknown (KU-2026-070-02) |
| 6 | Investigate MGIE P_ARORA posting pattern | Treasury + MGIE | Low | Clarify mid-month logic |

---

## 9. Known Unknowns (inherited from fx_revaluation_2025_agi_research.md)

- **KU-2026-070-01**: Which valuation method (T044A) is used per variant per BUKRS — unknown
- **KU-2026-070-02**: VARI/VARID not in Gold DB — F.05 variant content cannot be audited
- **KU-2026-070-03**: 0001111194 (Banco do Brasil BRL) and 0001144715 (Commercial BK Ethiopia ETB) — blocked but no "CLOSED" label — reason unknown
- **KU-2026-070-04**: MGIE P_ARORA mid-month pattern — not standard month-end; reason unknown

---

## Falsifiable Predictions

- **FALS-CA-001**: If SM36 SAPF100 jobs are created per BUKRS with existing variants, revaluation lag drops to <1h. Test: create one job for ICTP (smallest), monitor for 1 month.
- **FALS-CA-002**: ICTP will miss at least 1 more month in 2026 if M_VENUTI has no backup. Test: monitor BKPF monthly.
- **FALS-CA-003**: T030H fix for 17 active HKONTs will eliminate "blocked for posting" errors in next F.05 run. Test: run F.05 simulation (EVR method) after fix.
