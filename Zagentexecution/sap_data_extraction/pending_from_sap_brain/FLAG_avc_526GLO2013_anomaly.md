---
# Bus header — contract C-4 v1.1 (sole owner: C0). Derived from the prose below; nothing invented.
msg_type: FLAG
request_id: avc_526GLO2013_anomaly
from_project: unesco-sap-brain        # "(S40 AVC validation)"
date: 2026-06-30
status: OPEN                          # asks abapobjectscreation to verify at source; no DONE/closure on disk
system_role: P01
why: "Fund 526GLO2013 nets to -$103.76M available in fmavct_2026, driven by two ROBJNR with no budget, actuals or commitments backing (real activity ~$0.45M). Likely a genuine negative-transfer posting or an extraction sign/scale artifact."
consumers:
  - "unesco-sap-brain/knowledge/45 (fund excluded: 163 net-negative funds = -$47.2M excl. 526GLO2013)"
resolve_via: "unesco-sap-brain/refs_external.json -> golden DB read-only"
---

# Data-quality FLAG: FMAVCT anomaly on fund 526GLO2013 (2026) — please verify at source

> **From:** `unesco-sap-brain` (S40 AVC validation) · **Date:** 2026-06-30
> **Re:** the FMAVCT wide re-extraction you landed 2026-06-30 10:24 (thank you — `fmavct_2024/25/26`, budget+consumption legs, `HSL01…16`/`HSLVT`/`ROBJNR`). It validated cleanly for normal funds, **except one outlier** flagged below.

## The anomaly
Fund **`526GLO2013`** (UNES, TYPE 105 "ALL-11321", biennium 42→43) nets to **−$103.76M available** in `fmavct_2026`, driven by **two ledger objects with no real backing**:

| ROBJNR | RRCTY | CI bucket | row total (HSLVT+ΣHSL01..16) |
|---|---|---|---:|
| `000000000003915703` | 1 | PC | **−$79.31M** |
| `000000000003915827` | 1 | 80 | **−$27.55M** |

But the fund's **real activity is ~$0.45M**: `fmifiit_full` actuals = $0.16M (2025) + $0.16M (2026); `fmioi` commitments = −$0.12M. In `fmavct_2025` the same fund netted **+$0.02M**; the −$103.76M appears **only in 2026**. No matching budget exists in `BPGE`/`BPJA` for this GEBER. A TYPE-105 earmarked allocation fund cannot legitimately carry a −$107M entry with no budget/actuals/commitments.

## Ask
Please verify these two `FMAVCT` records at source (transaction **FMAVCR01** / table `FMAVCT` for FM area UNES, fund 526GLO2013, FY2026, ledger 9H). Likely either (a) a one-off negative-budget/transfer-out posting that should be confirmed, or (b) an extraction/sign/scale artifact on those two `ROBJNR`. If (b), a corrected re-extract of FY2026 would fix it.

## Impact (contained)
unesco-sap-brain has **excluded** this single fund from the current-biennium AVC status (knowledge/45): reported as **163 net-negative current-biennium funds ≈ −$47.2M excl. 526GLO2013** (vs −$151M incl.). Nothing else depends on it. Resolve through `refs_external.json` → golden DB read-only.
