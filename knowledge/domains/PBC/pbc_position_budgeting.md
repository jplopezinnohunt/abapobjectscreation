---
name: PBC — Position Budgeting and Control (the payroll-to-budget bridge)
description: How UNESCO commits staff posts against Funds Management. Component PA-PM-PB — it sits under Personnel Management, not PSM, which is why an FM-shaped search never found it. 68 users, 6.4M funds-reservation change documents. Discovered s097 as a system-level blind spot.
type: project
module: PA-PM-PB
capability_domain: PBC
status: PRODUCTIVE
claims: [358]
---

# PBC — Position Budgeting and Control

**Technical component:** `PA-PM-PB` (Personnel Management → Position Budgeting and Control)
**Capability row:** `capability_model.domains.PBC` · **Profile:** `graph_queries.py profile PBC`

## What it is

The bridge between **staff posts and budget**. Every established post carries a cost that must be
committed against Funds Management *before* payroll runs. PBC is the machinery that turns an
org-management position into an FM commitment (`FMRESERV`) and keeps the two reconciled across the
biennium.

For a UN agency this is not a technical detail — **staff cost is the single largest budget line**,
and PBC is where it is controlled.

## Why it was invisible until s097

PBC was already in the brain — as an *"engine"* inside the operating-model document
(`ZPBC_PERIOD_CLS_EXEC → FMRESERV`). It was never a **module**. A question shaped like *"which
modules are implemented?"* could not reach a thing filed as a process.

The component code compounds it: `PA-PM-PB` sits under **Personnel Management**, not under PSM.
Searching the FM neighbourhood for a budget capability never arrives here.

> Lesson recorded in claim #358: a thing described as an *engine* or a *process* in one artifact is
> invisible to a question keyed on another axis.

## Measured evidence (audit window Feb–Jun 2026; documents 2024–2026)

| Signal | Measurement |
|---|---|
| `HRFPM_PBCDOC_DISP` — PBC document display | 2,881 executions / **68 users** |
| PBC engine `HRPBC_ENGINE_PNP` | daily: `RHRFPM_ENGINE_PERSON`, `RHRFPM_ENGINE_PNP`, `RHRFPM_ENGINE_MASS_PROC_PNP`, `HUNCALC0` (1,515), `RHHCP_DC_EMPLOYEE` (940), `RPCIPE00_OLD` (677) |
| `HRFPM_VACANCY_DISP` — vacancy display | 25 executions |
| `FMRESERV` funds reservations | **6,415,467** change-document headers, 2024-01-01 → 2026-03-16 |

**68 users is the widest dialog user base measured anywhere in this installation.** More people
touch PBC directly than any other single transaction we have measured — worth holding against the
headline that UNESCO barely uses dialog.

## Custom layer

| Object | Volume | What it suggests |
|---|---|---|
| `Y_KBLP_PBC_OPEN_N` (tcode `YKBLP_N`) | 1,399 execs / 1 user | open-commitment worklist — high volume, single operator |
| `YPBC` → `RFFMEPGAX` | 258 execs / 5 users | standard FM report driven from a custom tcode |
| `YPS8_PBC` | 60 execs / **26 users** | wide audience — likely a reporting/enquiry view |
| `YBBUR001_PBC` | 57 execs / 8 users | custom budget report |

The pattern — one heavy single-operator worklist plus several wide-audience read views — says the
**maintenance is concentrated and the consumption is broad**. That asymmetry is a key-person risk
worth naming.

## Data access constraint

`HRFPM_*` tables return `TABLE_NOT_AVAILABLE` over RFC. **This is an access restriction, not
absence** — `FMBH` behaves identically yet holds 294,098 rows in the Gold DB. Evidence for PBC
therefore comes from the audit log and from `CDHDR` (object class `FMRESERV`), not from direct
table reads. Any future extraction must plan for that.

## Open questions

1. **The period/biennium cycle.** We see the engine run daily but not the *calendar*: when are
   commitments rebuilt, and what happens at biennium roll-over?
2. **Reconciliation with actual payroll.** PBC commits; payroll posts. Where is the variance
   measured, and by whom? (The EPI-USE Variance Monitor add-on is active on HCM — likely related,
   unverified.)
3. **The 68 users.** Which roles, in which offices? This is the widest dialog audience we have and
   we do not know who they are.
4. **`YPS8_PBC` vs `Y_BAPI_YPS8`.** A MuleSoft interface calls `Y_BAPI_YPS8` 461K times. The name
   collision with the PBC report is unexplained and may link position budgeting to the corporate
   planning platform.

## Relations

- **Capability:** `PBC` (U_USAGE HAVE · A_PROCESS/B_CODE/D_DATA PARTIAL · rest NONE)
- **Parent domain:** `PSM_FM` — functionally the budget side of the bridge
- **Module axes:** HCM + FM · **Process axes:** B2R, H2R
- **Adjacent:** [[PSM]] (funds & budget) · [[HCM]] (positions, org management) · [[PY-Finance]]
- **Claim:** #358 (TIER_1, measured)
