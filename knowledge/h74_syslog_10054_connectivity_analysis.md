---
name: H74 — SM21 10054 deep analysis (the 272 resets are NOT satellite drops)
description: Deepened H74 analysis. Decoding SM21 CENTDATA + temporal correlation REFUTES the prior verdict that the 272 "10054" resets are satellite integration failures. 269/272 are end-user SAP GUI frontend disconnects (human diurnal, weekday); only 3 are the SAP↔SQL Server link (one Sunday maintenance window). Zero gateway/RFC-server resets. 2026-06-22.
type: project
---

# H74 — The 272 "10054" resets, decoded (PMO H74)

**Window analysed:** `sm21_syslog_history` (2,402 rows) + `st22_dumps_history` (1) in the Golden DB,
covering **2026-06-15 12:29 → 2026-06-22 13:39** (~7 days, the full SM21 retention). Parser:
`process_mining/parse_syslog.py` (decodes the fixed CENTDATA format + classifies each row by channel).

## Headline — the prior hypothesis is REFUTED
The prior PROBLEMS analysis (claim #232, 2026-06-21) read the raw count "272 × 10054" and concluded the
**#1 failure mode is the SATELLITE CONNECTIONS (MuleSoft / ORION / SQL Server)**. Decoding the CENTDATA and
correlating by channel, host and time shows that is **wrong**:

| What the 272 "10054" actually are | n | What it is |
|---|---:|---|
| **`frontend_DIAG_reset`** (Q0/I `recv 10054`, WP=`DP`) | **269** | End-user **SAP GUI native** sockets reset by the user's PC (laptop sleep / VPN drop / GUI killed). The dispatcher's `recv` returns WSAECONNRESET (Win err 10054). **Benign, user-side.** |
| **`db_connection_reset`** (BY/M `dbsh 10054`) | **3** | The real **SAP↔SQL Server** library reset — all three at **Sun 2026-06-21 02:53**, one maintenance window. Matches the lone dump. |

**Not one of the 272 is a satellite (MuleSoft/ORION) RFC connection drop.**

## Three independent proofs it's the GUI frontend, not the satellites
1. **Process that logged it.** 264/269 were logged by **`DP` (the dispatcher)**, which manages **SAP GUI
   native (DIAG, port 3200) frontend** connections — **not** the RFC gateway (port 3300, where MuleSoft/ORION
   inbound calls land). The recv error is on the dispatcher's *frontend-facing* socket.
2. **Companion stream names workstations, not servers.** The paired `Q0/4 dpTermin` stream (280 rows) names the
   disconnecting endpoint, and every one is an **end-user workstation** — `HRM-L-21018218`, `DAK-LAP-097`,
   `ICB-LAP-007`, `BRZ-WKS-8767`, `mac-krizmancic.ictp.it`, `teh-wks-030` (HQ laptops, ICTP Trieste, field
   offices). **No `synctrigger`, no `HQ-ORION`, no satellite host.**
3. **Temporal signature is human, not automated.** The 269 resets are **86% in business hours (06–19h)** with a
   two-hump diurnal curve (peaks 11–13h + 16–18h, a lunch dip) and **collapse on the weekend** (Mon-Thu 44–82/day,
   **Sat = 1, Sun = 8**). The MuleSoft synctrigger fleet and ORION run **24/7** — they cannot produce a
   business-hours, weekday-only curve. This is a dialog-user pattern.

**Clincher:** a full token search of the syslog found **zero** gateway/RFC-server reset markers
(`gwrd`, `reg_info`, `sec_info`, `synctrigger`, `MULESOFT`, `Y_BAPI`). If the satellite RFC connections were
TCP-resetting, the *gateway* would log it. It doesn't. The satellite RFC links are **not** dropping at TCP.

## WHICH connection drops, and WHEN (the task's question, answered)
- **The dominant "drop" = end-user SAP GUI sessions, business hours, weekdays** — the WAN/VPN frontend, one
  reset per user-PC network blip. **Not a single satellite; not the gateway.**
- **The only backend TCP reset = SAP↔SQL Server**, and it is **one Sunday 02:53 maintenance window** (3 resets +
  the lone `DBIF_REPO_SQL_ERROR` dump on `MDS_CTRL_STRATEGY`). **Episodic, not chronic.**
- The task's three candidate causes, scored against evidence:
  - *Firewall idle-timeout* → **NOT** the cause of the 272 (they are abrupt resets *during active business hours*,
    not idle drops). Idle-timeout DOES explain the 28 `http_idle_logout` — a different, **expected** signal.
  - *MuleSoft/ORION endpoint cycling* → **NOT supported** (zero gateway resets; ORION shows 3 *app-level* errors,
    not connection drops).
  - *SQL Server maintenance window* → **CONFIRMED**, for the 3 `dbsh` resets only.

## The genuine integration/infra failure tail (small, distinct)
Separating the benign frontend churn leaves the real integration signal — ~24 events in 7 days:

| Channel | n | Note |
|---|---:|---|
| `db_connection_reset` (SAP↔SQL Server) | 3 | Sun 02:53 maintenance window. Matches the dump. |
| `batch_sql_error` (`DBSQL_*_ERROR`) | 3 | All inside batch job **`RFFMAVC_OVERALL_VIEW`** (FM Availability-Control overall-view rebuild), early-morning batch (00:00 / 05:00 / 07:30). Recurring — likely a program/data/lock issue, worth its own look. |
| `orion_app_error` (`HQ-ORION` E0/A) | 3 | App-level errors in ORION-EAI-originated RFC sessions (`SAPMSSY1`, "Error Message [Error/Core]"). Not TCP. |
| `rfc_cpic_error` (R4/R5 `RfcHand CPIC-Er`) | 13 | Genuine RFC/CPIC channel hiccups, spread across hours. Minor. |

## Recommendations (monitoring + remediation) — evidence-targeted
The originally-requested "TCP keepalive to MuleSoft/ORION/SQL Server" is **largely not indicated** by the data:
those RFC links are not resetting. Do this instead:

1. **Reclassify the signal — stop counting frontend churn as failures.** The syslog noise filter should bucket
   `frontend_DIAG_reset` + `frontend_session_term` (549 rows) as **"frontend session churn"**, not "network
   errors". This was the root of the misdiagnosis. `parse_syslog.py` does this split.
2. **SQL Server link — make alerting window-aware, then verify the window.** Confirm with BASIS/DBA that a
   backup/maintenance ran ~**Sun 02:53** on the `MDS_CTRL_STRATEGY` / master-data SQL Server. Suppress
   DB-reset alerts inside the known maintenance slot (02:00–06:00 Sun) so the 3 resets don't page anyone. This
   is the **only** backend TCP reset and it is episodic.
3. **`RFFMAVC_OVERALL_VIEW` batch SQL errors — investigate as a separate item.** Recurring `DBSQL_*_ERROR` in
   the AVC overall-view rebuild at 00:00/05:00/07:30 is the one *repeating* integration-adjacent fault. It is
   not the network — check the job's SQL / locking / data volume.
4. **GUI frontend churn — UX, not system health.** If a specific subnet/field-office/VPN concentrator
   over-represents in the `dpTermin` workstation list over a longer window, raise it with the network team (a
   WAN/VPN issue degrading SAP GUI UX). SAP-side `rdisp/keepalive*` can reclaim orphaned sessions but **will not
   stop the resets** — the user's PC is the side closing the socket.
5. **HTTP idle auto-logout (28) is expected.** `rdisp/plugin_auto_logout` / `icm/keep_alive_timeout` already
   working as designed; tune only if Fiori users complain about premature logout.
6. **Build the baseline — a 7-day window is too short.** Keep `accumulate_problems.py` on the **weekly** schedule
   (H78). SM21 retains only ~7 days; only a multi-week accumulation can tell *episodic* (the Sunday SQL window)
   from *chronic* and surface the rare genuine integration failures against the frontend-churn floor. The current
   data is already fresh to today (max TS 2026-06-22 13:39) — the value is the recurring cadence, not a re-pull now.

## Net for the operating model
The failure side still **mirrors** the operating model — but the mirror is sharper than first read: the system is
**application-healthy** (1 dump in 7 days), the noise is **frontend session churn** (benign), and the genuine
integration faults are a **small, episodic tail** dominated by one Sunday SQL-Server maintenance blip plus a
recurring AVC-batch SQL error — **not** a satellite TCP-stability problem. Feed this corrected A_PROCESS /
F_INTERFACE reality into the capability model. Tools: `process_mining/parse_syslog.py` (decoder/classifier),
`process_mining/accumulate_problems.py` (weekly accumulator).
