---
name: SAP Job Intelligence
description: >
  Deep analysis of SAP background jobs (SM37) over the last 2+ years. Extracts TBTCO/TBTCP
  to map all scheduled, periodic, and event-triggered jobs in UNESCO SAP (P01/D01).
  Identifies job chains, failure patterns, runtime anomalies, and job owners.
  Feeds brain with JOB_PATTERN nodes for operational intelligence.
---

# SAP Job Intelligence

## Purpose

Build a complete map of **what runs in background** across UNESCO SAP systems over the last 2 years:
1. **Inventory**: Every job that ran, who owns it, what program it executes
2. **Patterns**: Periodic jobs (daily/weekly/monthly), event-triggered, one-shot
3. **Failures**: Jobs that fail repeatedly, runtime anomalies, stuck jobs
4. **Chains**: Job sequences (Job A triggers Job B via events)
5. **Owners**: Which users/teams own which job families
6. **Obsolete**: Jobs scheduled but never running, or running but doing nothing

## NEVER Do This

1. NEVER cancel running jobs via RFC without user confirmation — production jobs may be in-flight
2. NEVER extract TBTCP (job steps) without TBTCO context — steps are meaningless without headers
3. NEVER assume SDLSTRTDT is execution date — it's *scheduled* start, actual start is STRTDATE
4. NEVER filter only STATUS='F' (finished) — you'll miss scheduled, aborted, and active jobs
5. NEVER ignore event-triggered jobs (BTCEVTJOB) — they don't have fixed schedules

## Key Tables

| Table | Purpose | Key Fields | Size Estimate |
|-------|---------|------------|---------------|
| `TBTCO` | Job overview (headers) | JOBNAME, JOBCOUNT, STATUS, SDLSTRTDT, STRTDATE, ENDDATE, AUTHCKNAM, PRDMINS, PRDHOURS | ~500K (2 years) |
| `TBTCP` | Job steps (programs) | JOBNAME, JOBCOUNT, STEPCOUNT, PROGNAME, VARIANT, AUTHCKNAM | ~800K (2 years) |
| `BTCEVTJOB` | Event-triggered jobs | JOBNAME, JOBCOUNT, EVENTID, EVENTPARM | ~10K |
| `TBTCS` | Job scheduling details | JOBNAME, SDLSTRTTM, PRDMINS, PRDHOURS, PRDDAYS, PRDWEEKS, PRDMONTHS | ~50K |

## Job Status Codes

| Status | Meaning | Icon | Action |
|--------|---------|------|--------|
| `S` | Scheduled | Clock | Waiting for start time |
| `R` | Released | Green | Ready to run |
| `P` | Running (active) | Spinning | Currently executing |
| `F` | Finished | Check | Completed successfully |
| `A` | Aborted | X | Failed — investigate |
| `Y` | Ready | Arrow | Intercepted, waiting |
| `Z` | Released (intercepted) | Arrow | Released but intercepted |

## Extraction Protocol

### Step 1: Extract TBTCO (Job Headers, 2 Years)

```python
# Use rfc_helpers.py with month-based checkpointing
from rfc_helpers import get_connection, rfc_read_paginated

conn = get_connection("P01")

fields = ["JOBNAME", "JOBCOUNT", "STATUS", "SDLSTRTDT", "STRTDATE",
          "STRTTIME", "ENDDATE", "ENDTIME", "AUTHCKNAM", "PROGNAME",
          "PRDMINS", "PRDHOURS", "PRDDAYS", "PRDWEEKS", "EVENTID"]

# Month-by-month extraction (2024-01 to 2026-03)
for year in [2024, 2025, 2026]:
    for month in range(1, 13):
        where = f"SDLSTRTDT >= '{year}{month:02d}01' AND SDLSTRTDT <= '{year}{month:02d}31'"
        rows = rfc_read_paginated(conn, "TBTCO", fields, where, batch_size=5000)
```

> [!CAUTION]
> Use SDLSTRTDT (scheduled start date) for filtering, NOT STRTDATE (actual start).
> STRTDATE may be blank for scheduled-but-not-yet-run jobs.

### Step 2: Extract TBTCP (Job Steps)

```python
# Extract steps for all jobs found in TBTCO
fields = ["JOBNAME", "JOBCOUNT", "STEPCOUNT", "PROGNAME", "VARIANT",
          "AUTHCKNAM", "TYP", "STATUS"]

# No date field — extract by JOBNAME ranges or full table
rows = rfc_read_paginated(conn, "TBTCP", fields, "", batch_size=5000)
```

### Step 3: Load into Gold DB

```python
# extraction_status.py --load TBTCO
# extraction_status.py --load TBTCP
```

### Step 4: Analyze

```sql
-- Top 20 most frequent jobs
SELECT JOBNAME, COUNT(*) as runs,
       SUM(CASE WHEN STATUS='A' THEN 1 ELSE 0 END) as failures,
       MIN(SDLSTRTDT) as first_run, MAX(SDLSTRTDT) as last_run
FROM tbtco
WHERE SDLSTRTDT >= '20240101'
GROUP BY JOBNAME
ORDER BY runs DESC
LIMIT 20;

-- Failed jobs in last 30 days
SELECT JOBNAME, STRTDATE, AUTHCKNAM, PROGNAME
FROM tbtco
WHERE STATUS = 'A' AND SDLSTRTDT >= '20260218'
ORDER BY STRTDATE DESC;

-- Periodic jobs (have period settings)
SELECT JOBNAME, PRDMINS, PRDHOURS, PRDDAYS, PRDWEEKS, COUNT(*) as runs
FROM tbtco
WHERE (PRDMINS > 0 OR PRDHOURS > 0 OR PRDDAYS > 0 OR PRDWEEKS > 0)
GROUP BY JOBNAME, PRDMINS, PRDHOURS, PRDDAYS, PRDWEEKS
ORDER BY runs DESC;

-- Job owners (who schedules what)
SELECT AUTHCKNAM, COUNT(DISTINCT JOBNAME) as unique_jobs, COUNT(*) as total_runs
FROM tbtco
WHERE SDLSTRTDT >= '20240101'
GROUP BY AUTHCKNAM
ORDER BY unique_jobs DESC;

-- Job step programs (what code actually runs)
SELECT t2.PROGNAME, COUNT(*) as job_count
FROM tbtco t1
JOIN tbtcp t2 ON t1.JOBNAME = t2.JOBNAME AND t1.JOBCOUNT = t2.JOBCOUNT
WHERE t1.SDLSTRTDT >= '20240101'
GROUP BY t2.PROGNAME
ORDER BY job_count DESC;
```

## Job Classification Framework

### By Schedule Pattern

| Pattern | Detection | Examples |
|---------|-----------|---------|
| **Daily** | PRDDAYS=1 or 24 runs/month | Payroll interface, BW extraction |
| **Weekly** | PRDWEEKS=1 or 4 runs/month | Reporting, reconciliation |
| **Monthly** | PRDMONTHS=1 or 12 runs/year | Period close, settlement |
| **Event-triggered** | EVENTID not blank | Workflow, interface response |
| **One-shot** | No period, runs once | Ad-hoc corrections, migrations |
| **Chained** | Job A ends → Job B starts | Settlement → Posting → Report |

### By Business Domain

| Domain | Job Name Patterns | Programs |
|--------|-------------------|----------|
| **HCM/Payroll** | *PAYROLL*, *PY_*, *PC00* | RPCALC*, PC00_M99_* |
| **FI/GL** | *SAPF*, *RFBILA*, *FAGL* | SAPF124, RFBILA00, FAGLB03 |
| **PSM/FM** | *FMFG*, *RFFM*, *YFM* | RFFMEP*, YFM1, FMRP_* |
| **MM/Procurement** | *RM06*, *ME_*, *RMMB* | RM06BIN0, RMMB1000 |
| **BW Extraction** | *RSM*, *BW_*, *BI_* | RSM13000, RSPROCESS |
| **Basis/System** | *SAP_*, *RSBTC*, *SM* | RSBTCREC, RSSNAPDL |

### By Criticality

| Tier | Criteria | Action on Failure |
|------|----------|-------------------|
| **CRITICAL** | Payroll, period close, BW loads | Page oncall immediately |
| **HIGH** | Daily interfaces, reconciliation | Investigate same day |
| **MEDIUM** | Weekly reports, cleanup | Fix within 3 days |
| **LOW** | Ad-hoc, test jobs | Log only |

## UNESCO-Specific Known Jobs

> [!IMPORTANT]
> This section should be populated after first extraction. Expected patterns:

| Expected Job | Program | Domain | Schedule |
|-------------|---------|--------|----------|
| PBC period close | ZPBC_PERIOD_CLS_EXEC | PSM | Monthly (January spike) |
| Payroll cross-posting | PC00_M99_CIPE | HCM→FI | Per payroll run |
| BW extraction | RSM13000 | BW | Daily |
| FM carryforward | RFFMCF* | PSM | January only |
| Payment run | F110 | FI | Periodic |

## Known Failures & Self-Healing

| Error | Cause | Fix |
|-------|-------|-----|
| `TBTCO returns 0 rows` | Wrong date field or no auth | Check SDLSTRTDT filter, verify S_BTCH_JOB auth |
| `TBTCP too large` | Full table scan | Filter by JOBCOUNT ranges from TBTCO |
| `VPN drop during extraction` | Long-running RFC | ConnectionGuard auto-reconnects |
| `Duplicate JOBCOUNT` | Same job rescheduled | Group by JOBNAME+JOBCOUNT+SDLSTRTDT |

## Integration Points

- **System Monitor**: `--report jobs` provides quick SM37 summary
- **Brain**: JOB_PATTERN nodes in sap_brain.py graph
- **BDC Intel**: Jobs spawned by BDC sessions (APQI → TBTCO cross-reference)
- **Process Mining**: Job execution events feed pm4py DFG
- **Transport Intel**: Job creation/modification tracked in CTS
- **CDHDR**: Job config changes tracked in change documents

## EXTRACTION DONE (Session #013)

**TBTCO**: 58,778 rows in Gold DB (P01 retains only ~14 days — cleanup active)
**TBTCP**: 84,975 rows in Gold DB

### Key Findings

| Job | Runs | Program | Domain |
|-----|------|---------|--------|
| SAPCONNECT INT SEND | 10,413 | RSCONN01 | Basis (email gateway) |
| RDDIMPDP | 4,205 | RDDIMPDP | Basis (transport import) |
| /SDF/SMON_WATCHDOG | 4,166 | /SDF/SMON_WATCHDOG | Basis (system monitoring) |
| PAYMENT STATUS REPORTS | 1,389 | RBNK_IMPORT_PAYM_STATUS_REPORT | FI (banking) |
| COUPA FI POSTING INTEGRATION | 348 | (custom) | FI/Procurement |
| EBS INTEGRATION | 348 | (custom) | External interface |

**Top programs**: RBDAPP01(18.7K), RSCONN01(10.4K), ZFI_SWIFT_UPLOAD_BCM(2.8K)

### CRITICAL: P01 Job Log Retention

P01 has **cleanup active** — TBTCO only retains ~14 days of history. Cannot get 2-year history from TBTCO directly. For historical analysis, would need BW or change the retention policy.

## Critical Limitation: P01 Job Log Retention

> [!CAUTION]
> P01 has **active cleanup** — TBTCO retains only **~14 days** of job history.
> The 58,778 rows extracted represent a snapshot, NOT 2 years of history.
> For historical job analysis, would need BW extraction or retention policy change.
> Runtime duration analysis is severely limited by this 14-day window.

## Pending Work

1. **Job source code extraction** — Use `sap_adt_api` skill to extract ABAP source for top custom programs (ZFI_SWIFT_UPLOAD_BCM, YFI_COUPA_POSTING_FILE, RBDAPP01) and classify by domain
2. **Build job family taxonomy** — group by naming pattern + program
3. **Runtime analysis** — job duration trends (limited by 14-day retention — see limitation above)
4. **Chain detection** — event-based job triggers (BTCEVTJOB)
5. **Brain integration** — create JOB_PATTERN nodes with domain/criticality edges

## You Know It Worked When

1. ~~TBTCO loaded~~ DONE (58K rows, 14-day window)
2. ~~TBTCP loaded~~ DONE (85K rows)
3. Top 20 job families identified with owner, schedule, and program
4. Job programs classified by domain (FI, HCM, PSM, Basis, Custom)
5. UNESCO-specific job list populated with actual data
