# Log accumulation schedule — TBTCO/TBTCP (and future logs)

**Why:** P01 prunes the job log (TBTCO/TBTCP) to ~14 days. To build the permanent
event history for process mining, we must pull the live window every ≤15 days and
UPSERT it into `tbtco_history` / `tbtcp_history` (PK-deduped, append-only).

**Status: ✅ ACTIVATED 2026-07-25.** The Windows scheduled task `SAP_AccumulateLogs`
is registered and enabled (see "Registered task" below). Before this date the schedule
was only documented, never registered — every accumulation ran by hand.

History tables created + seeded in s079 (tbtco_history 58,778 / tbtcp_history 84,975);
now at 108,122 / 143,184 plus cdhdr_history 12,029,963 and rsau_audit_history
(SM20/RSAU — the volatile stream that carries the 80.6% external-RFC finding).

## Run manually (P01 active)
```
cd Zagentexecution/sap_data_extraction/scripts
python accumulate_logs.py            # pull + accumulate, then coverage report
python accumulate_logs.py --verify   # coverage report only, no P01 needed
run_accumulate_logs.bat              # same, but sets PYTHONIOENCODING and tees to accumulate_logs_run.log
```
Idempotent: overlapping windows are deduped by the history-table PK. Run it any time;
running every 14 days guarantees no gap vs P01's ~14-day retention.

## The schedule — Windows Task Scheduler (every 14 days)
> ⚠️ P01 uses SNC/SSO. The task MUST run in the user's authenticated Kerberos/SNC
> context — i.e. as the logged-in user (not SYSTEM, not "run whether logged on or
> not" unless the SNC credential is available headless). `/RL LIMITED` + the default
> "run only when user is logged on" is exactly that. If SNC is unavailable headless,
> run it manually or keep a logged-on session.

### Registered task (exact command used, 2026-07-25)
```
schtasks /Create /TN "SAP_AccumulateLogs" /SC DAILY /MO 14 /ST 02:00 ^
  /TR "python \"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\scripts\accumulate_logs.py\"" ^
  /RL LIMITED /F
```
→ `SUCCESS: The scheduled task "SAP_AccumulateLogs" has successfully been created.`

Registered properties (from `schtasks /Query /TN "SAP_AccumulateLogs" /V /FO LIST`):

| Property | Value |
|---|---|
| TaskName | `\SAP_AccumulateLogs` |
| Schedule Type / Days | Daily, **every 14 day(s)**, start 02:00 |
| Start Date / Next Run | 2026-07-25 / **2026-08-08 02:00** |
| Status / State | Ready / Enabled |
| Logon Mode | **Interactive only** (needs the user logged on — required for SNC) |
| Run As User | `jp_lopez` |
| Task To Run | `python "…\scripts\accumulate_logs.py"` |
| Power Management | Stop on battery, no start on batteries |

### Verify / remove
```
schtasks /Query  /TN "SAP_AccumulateLogs" /V /FO LIST   # is it registered, when does it next run
schtasks /Run    /TN "SAP_AccumulateLogs"               # fire it now (needs an SNC session)
schtasks /Delete /TN "SAP_AccumulateLogs" /F            # remove it
```
Evidence that a run happened: a new line in `accumulate_logs_run_history.log`
(append-only, one line per run) and an updated `accumulate_logs_state.json`.

### ⚠️ Known limitation — SNC/SSO at 02:00 (blocking item H66)
`/RL LIMITED` + "interactive only" means the task **only fires while the user is logged
on**, and claim **#215** records that the interactive Kerberos/SNC ticket expires after
~10 h and does **not** survive an unattended/overnight run (two overnight runs already
failed this way, 2026-06-20 and 2026-06-21). So the 02:00 slot will fail whenever the
workstation is locked/logged-off or the ticket has aged out.

Treat the schedule as a **reminder + best-effort** run, not a guarantee:
- If it fires and SNC is alive → full unattended accumulation. Good.
- If it fires and SNC is dead → the run aborts at `get_connection("P01")`, nothing is
  written, and the fix is simply to run `run_accumulate_logs.bat` by hand that day
  (idempotent, PK-deduped — no data is lost as long as the gap stays under P01's window).
- The real fix is **H66** — a BASIS-provisioned **keytab / headless SNC credential**, which
  is the prerequisite for switching this task to "run whether user is logged on or not"
  (`/RU` + `/RP`, or a gMSA). Until H66 lands, `unattended_ready = 0.0` in the capability
  model and this task cannot be trusted to run alone.
- Because P01's real retention turned out to be **>4 months** for RSAU (claim #217, superseding
  #212), a missed 14-day slot is recoverable — but `RETENTION_MIN_DAYS = 183` still requires the
  cadence to hold for the shorter streams (TBTCO/TBTCP ≈ 14 days).

## Extending to other logs (the process-mining raw material)
Add an entry to `LOG_TABLES` in `accumulate_logs.py`. Candidates (all append-only event
streams that P01 prunes or that grow forever):
- **SNAP / ST22** — ABAP dumps (error events).
- **TST01/TSP01 / SP01** — spool/output log.
- **SM21 / SYSLOG** — system log.
- **CDHDR/CDPOS** — change documents (already extracted once; could accumulate deltas).
- **BALHDR/BALDAT (SLG1)** — application log.
Each needs: history table name, natural KEY (for PK dedup), field list, and an optional
date field + lookback to bound the pull. Same UPSERT-by-key pattern — nothing else changes.

## Process-mining payoff
`tbtco_history × tbtcp_history` is the JOB/BATCH event log: per job run we get program,
variant, scheduler (AUTHCKNAM), start/end, status, duration. Over time this becomes a
real process-mining event stream (the "how the batch landscape actually runs" view) that
hangs off the brain's PROCESS spine via STEP_USES_TCODE → program → job (RUNS_PROGRAM).
