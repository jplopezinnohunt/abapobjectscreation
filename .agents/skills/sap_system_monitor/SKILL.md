---
name: SAP System Monitor
description: >
  Operational intelligence dashboard for UNESCO SAP systems. Provides real-time
  and historical views of active users (SM04), transaction usage, batch inputs (SM35),
  background jobs (SM37), runtime dumps (ST22), obsolete programs, and system health.
  Dual-channel: Python RFC (SNC/SSO) + ADT REST (HTTP Basic).
---

# SAP System Monitor

## Purpose

Answer the 6 operational questions about UNESCO's SAP landscape:

| Question | Report | SAP Equivalent | Table |
|----------|--------|----------------|-------|
| WHO is connected? | `--report users` | SM04 | TH_USER_LIST RFC + USR02 |
| WHAT transactions run? | `--report transactions` | ST03/STAD | TSTC/TSTCT + TH_WPINFO |
| WHAT is obsolete? | `--report obsolete` | REPOSRC analysis | REPOSRC (last change dates) |
| WHAT batch inputs exist? | `--report bdc` | SM35 | APQI + TBTCO |
| WHAT errors/dumps? | `--report dumps` | ST22 | SNAP + ADT /runtime/dumps |
| HOW is the system? | `--report health` | various | RFC_SYSTEM_INFO + TADIR |

## NEVER Do This

1. NEVER run `--report all` on P01 during business hours (09:00-17:00 CET) — each report generates 3-5 RFC calls
2. NEVER assume SM04 data is complete — TH_USER_LIST may not return dialog-less sessions (RFC/batch)
3. NEVER use this for security auditing — USR02 login dates are approximate, use SM20/RSUSR200 instead
4. NEVER confuse BDC sessions with background jobs — APQI (SM35) != TBTCO (SM37)

## Script Location

```
Zagentexecution/mcp-backend-server-python/sap_system_monitor.py  (723 lines)
```

## Two-System Architecture

| System | Host | Auth | Use For |
|--------|------|------|---------|
| D01 (Dev) | 172.16.4.66:00 | Password or SNC | Code deploy, ADT API, testing |
| P01 (Prod) | 172.16.4.100:00 | SNC/SSO only | Users, jobs, dumps, BDC, monitoring |

## CLI Usage

```bash
cd Zagentexecution/mcp-backend-server-python

# All reports at once
python sap_system_monitor.py --report all

# Individual reports
python sap_system_monitor.py --report users              # SM04 - active sessions
python sap_system_monitor.py --report transactions        # Most-used tcodes
python sap_system_monitor.py --report bdc --days 30       # SM35 batch inputs
python sap_system_monitor.py --report jobs --days 7        # SM37 background jobs
python sap_system_monitor.py --report dumps --days 3       # ST22 runtime dumps
python sap_system_monitor.py --report obsolete --months 12 # Unused programs
python sap_system_monitor.py --report health              # System overview

# Switch system (default: P01)
python sap_system_monitor.py --report users --system D01
```

## Dual-Channel Design

### Channel 1: Python RFC (SNC/SSO)
- Used for: SM04, SM35, SM37, workload, user stats
- Auth: Kerberos SNC trust (no password for P01)
- Module: `rfc_helpers.py` → `get_connection("P01")`

### Channel 2: ADT REST (HTTP Basic)
- Used for: Runtime dumps (ST22), usage references, object last-change
- Endpoint: `http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80/sap/bc/adt`
- Auth: HTTP Basic with CSRF token

### Indirect RFC (Cross-System)
```python
# Connect to D01, query P01 via RFC destination
conn = rfc_connect_indirect(d01_cfg, p01_dest="P01CLNT350")
conn.call("RFC_READ_TABLE", ..., DESTINATION="P01CLNT350")
```

## Report Details

### Users Report (SM04)
- Primary: `TH_USER_LIST` RFC (real-time sessions)
- Fallback: `USR02` table (last login dates)
- Fields: USERNAME, TCODE, TERMINAL, LOGON_DATE

### Transaction Usage
- Tables: `TSTC` (tcode definitions) + `TSTCT` (descriptions)
- Enrichment: `TH_WPINFO` for active work process info
- Output: Transaction frequency, last-used dates

### BDC/Batch Input (SM35)
- Table: `APQI` — session queue
- Fields: GROUPID, CREATOR, CREDATE, QSTATE
- Status codes: ' '=NEW, 'E'=ERROR, 'P'=PROCESSING, 'F'=DONE, 'Z'=BACKGROUND
- Cross-reference: TBTCO for jobs spawned by BDC
- **Allos Detection**: Service users creating Excel-based BDC sessions

### Background Jobs (SM37)
- Table: `TBTCO` — job overview
- Fields: JOBNAME, STATUS, SDLSTRTDT, AUTHCKNAM
- Status codes: A=ACTIVE, F=FINISHED, S=SCHEDULED, P=RUNNING, Z=RELEASED
- See `sap_job_intelligence` skill for deep 2-year analysis

### Runtime Dumps (ST22)
- ADT endpoint: `/sap/bc/adt/runtime/dumps`
- Fallback: `SNAP` table via RFC
- Fields: dump type, timestamp, program, user

### Obsolete Programs
- Table: `REPOSRC` — source code repository
- Logic: programs with CDAT (last change) > N months ago
- Threshold: default 12 months, configurable via `--months`

## Companion Scripts

| Script | Purpose |
|--------|---------|
| `bdc_full_inventory.py` | Complete SM35 inventory (no limit) |
| `bdc_deep_analysis.py` | Deep dive into specific BDC sessions |
| `bdc_schema_probe.py` | APQI schema discovery |
| `check_all_users.py` | USR02 full scan |
| `check_people.py` | Specific user lookup |

## Known Failures & Self-Healing

| Error | Cause | Fix |
|-------|-------|-----|
| `TH_USER_LIST not found` | Missing auth for kernel RFC | Fall back to USR02 table |
| `connection closed` during report | VPN drop | Auto-reconnect via ConnectionGuard |
| `SNAP table empty` | No dumps in time window | Normal — system healthy |
| `0 users returned` | SNC ticket expired | Re-authenticate Kerberos |
| `RFC_SYSTEM_INFO returns ? for all fields` | Raw response parsing broken — field format unexpected | 🔴 OPEN BUG: Need raw response dump to debug. Health report shows `?` for kernel, DB, OS. Workaround: skip health report, use individual reports. |

## Integration Points

- **Brain**: Dump patterns feed ANOMALY nodes in sap_brain.py
- **Transport Intel**: BDC sessions correlate with transport deployment dates
- **Job Intel**: SM37 data feeds the `sap_job_intelligence` skill for 2-year analysis
- **Coordinator**: Routes "what's running" / "who's connected" / "any errors" queries here

## You Know It Worked When

1. User report shows active sessions with tcodes and terminals
2. BDC report identifies Allos-pattern sessions vs system-generated (Y1 payroll)
3. Dump report catches ST22 entries with program name and timestamp
4. Health report returns system info + custom object counts
