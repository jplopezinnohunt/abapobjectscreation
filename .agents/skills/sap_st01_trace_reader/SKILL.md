---
name: sap_st01_trace_reader
domains:
  functional: [Support]
  module: [BASIS]
  process: []
---

# SAP ST01 Trace Reader — Skill Reference

## Purpose

Read and parse SAP ST01 (System Trace) data programmatically via RFC, without needing the SAP GUI. Covers all ST01 trace categories: Authorization Check, Kernel Functions, General Kernel, DB access (SQL trace), Table Buffer, RFC Calls, HTTP Calls, APC/AMC Calls, Lock Operations.

Also covers adjacent kernel trace files: work process dev traces (`dev_w*`), RFC traces (`dev_rfc*`), dispatcher (`dev_disp`), and security audit logs (`*.AUD`).

## When to use

- Debug a SAP transaction execution path (which programs/forms/methods were called)
- Audit authorization check failures
- Capture SQL statements executed by a transaction
- Trace RFC calls between systems
- Investigate kernel-level events for a specific user/transaction
- Verify whether a custom enhancement actually fires during a transaction

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  ST01 trace data lives in 3 places on the SAP app server:       │
│                                                                  │
│  1. KERNEL RING BUFFER (live, in-memory)                         │
│     Read via: SAP GUI ST01 "Active Trace File" mode              │
│     Programmatic access: limited (kernel-internal)              │
│                                                                  │
│  2. WORK PROCESS DEV TRACES                                      │
│     Files: /usr/sap/<SID>/<INST>/work/dev_w<N>                   │
│     Content: kernel diagnostics + DB events + RFC events         │
│     Format: ASCII text, timestamped lines                        │
│     Read via: RZL_READ_FILE_LOCAL                                │
│                                                                  │
│  3. SECURITY AUDIT LOG (auth checks)                             │
│     Files: /usr/sap/<SID>/<INST>/log/<YYYYMMDD>.AUD              │
│     Content: authorization checks (granted/denied) + login/out   │
│     Format: SAP audit binary                                     │
│     Read via: RSAU_API_GET_LOG_DATA / RSAU_READ_FILE             │
│                                                                  │
│  4. SAVED ST01 EXPORT FILE (if user did "Save As")               │
│     Files: user-named, anywhere on app server filesystem         │
│     Content: structured trace records                            │
│     Read via: RZL_READ_FILE_LOCAL                                │
└─────────────────────────────────────────────────────────────────┘
```

## How to use

```bash
cd Zagentexecution/mcp-backend-server-python
python ../../.agents/skills/sap_st01_trace_reader/read_st01_trace.py \
    --system TS3 \
    --user JP_LOPEZ \
    --since 2026-04-13T00:00:00 \
    --output ../../Zagentexecution/incidents/<incident>/trace_<user>.txt
```

Or as a Python module:
```python
from agents.skills.sap_st01_trace_reader import read_st01_trace as st01

# Discover available trace sources for the system
sources = st01.discover_traces(system='TS3')
# → {'work_traces': [list of dev_w*], 'audit_logs': [list of *.AUD], 'st01_exports': [...]}

# Read recent activity for a user
records = st01.read_audit_log(system='TS3', user='JP_LOPEZ', date='20260413')
# → [{'timestamp': ..., 'event': 'AU1', 'authobj': 'S_TCODE', 'tcode': 'FB60', 'result': 'OK'}, ...]

# Read RFC trace for a session
rfc_calls = st01.read_rfc_trace(system='TS3', work_process=5)

# Get all kernel events from a work process within a time window
events = st01.read_work_process_trace(
    system='TS3', wp=5,
    from_time='2026-04-13T09:55:00',
    to_time='2026-04-13T10:00:00'
)
```

## Connection pattern

Uses the standard UNESCO pyrfc SNC pattern:
```python
from pyrfc import Connection
conn = Connection(
    ashost=<host>, sysnr='00', client='350', lang='EN',
    snc_mode='1', snc_partnername='p:CN=<SID>', snc_qop='9',
    config={'rstrip': True}
)
```

Hosts defined in `.env` of mcp-backend-server-python:
- D01 = 172.16.4.66
- P01 = 172.16.4.100
- TS1 = hq-sap-ts1.hq.int.unesco.org
- TS3 = hq-sap-ts3
- V01 = hq-sap-v01

## Key SAP RFC functions used

| Function | Purpose | Notes |
|---|---|---|
| `RZL_READ_DIR_LOCAL` | List files in a server directory | Use `NAME=` (path), `NRLINES=` (limit), `FROMLINE=` (offset) |
| `RZL_READ_FILE_LOCAL` | Read file content | Use `NAME=` (filename), `DIRECTORY=` (path), `LINE_TBL=` (output) |
| `RSAU_API_GET_LOG_DATA` | Read security audit log with filters | Modern API for `*.AUD` files |
| `RSAU_LIST_AUDIT_FILES` | List audit log files available | |
| `RSAU_READ_FILE` | Read raw audit log file | |
| `RSAU_API_GET_PROFILE` | Get audit profile (what's being captured) | |

## Standard file locations on SAP app server

| Path alias | Typical absolute path | Content |
|---|---|---|
| `DIR_HOME` | `/usr/sap/<SID>/<INST>/work` | Work process dev traces |
| `DIR_DATA` | `/usr/sap/<SID>/<INST>/data` | stat.DAT*, runtime data |
| `DIR_LOGGING` | `/usr/sap/<SID>/<INST>/log` | `<YYYYMMDD>.AUD` audit log |
| `DIR_TEMP` | `/usr/sap/<SID>/<INST>/work` (often) | Temp files |
| `DIR_GLOBAL` | `/usr/sap/<SID>/SYS/global` | Global config + traces |
| `DIR_TRACE` | (varies) | Older kernel traces |

## Limitations

- **Active Trace File** mode in ST01 GUI reads the kernel ring buffer, which is NOT directly readable via RFC. To capture this data programmatically, the user must do "Save As" → file, then this skill reads the saved file.
- **dev_w<N>** files contain kernel/DB/RFC diagnostics but NOT ST01 application trace records (those need the active buffer or saved export).
- **Authority check trace** with full detail is captured in `STAUTHTRACE` (newer transaction) which writes to dedicated tables (USR_AUTH_TRACE_*).
- **Binary audit log** files (`*.AUD`) need parsing via `RSAU_*` APIs — raw read returns binary.

## ST01 Trace Record — Canonical Structure

**Each trace record has TWO views:**

### View 1 — Compact line (list view)

One line per event, columns:
```
HH:MM:SS,microseconds | TYPE | duration(µs) | object | program info + extras
```

Real example lines (from JP_LOPEZ FB60 trace TS3):
```
09:58:00,538 BUFF        1 VBWF16     Prog: SAPLF051 Row: 2,600 Buffer: I SearchString
09:58:00,539 SQL       317 RFDT       Prog: SAPLF051 Row: 2,844 ReturnCode 0
09:58:00,539 SQL         9 RFDT       Prog: SAPLF051 Row: 2,844 ReturnCode 0
09:58:00,539 BUFF        3 T8A_BILANZ Prog: SAPLPC62 Row: 3,712 Buffer: I SearchString 3503
```

Trace type catalog:

| TYPE | Meaning | Object field | Extras |
|---|---|---|---|
| `SQL` | DB operation (SELECT/UPDATE/INS/DEL) | DB table | Prog, Row (source line), ReturnCode |
| `BUFF` | Table buffer operation | DB table | Prog, Row, Buffer state, SearchString (key) |
| `AUTH` | Authorization check | Auth object | Result OK/FAIL, fields checked |
| `KERN` | Kernel function call | Function name | Args |
| `RFC` | RFC call | FM name | Destination, direction |
| `HTTP` | HTTP request | URL/endpoint | Method, status |
| `APC` / `AMC` | APC/AMC channel call | Channel | Direction |
| `LOCK` | Enqueue/Dequeue | Lock object | Mode, owner |

### View 2 — Full detail record

Common header (every record type):
```
Date            : DD.MM.YYYY
Time            : HH:MM:SS,microseconds
Work Process    : <wp number>
Process ID      : <PID>
Client          : <client>
User            : <username>
Transaction     : <tcode>
Transaction ID  : <16-byte hex GUID>
EPP Full Context ID    : <hex>
EPP Connection ID      : <hex>
EPP Call Counter       : <int>
```

Type-specific body (varies by TYPE):

**SQL** record body:
```
Call            : 03
Class           : 03
Operation       : 0A | 0B | ... (SELECT=0A, INSERT=06, UPDATE=05, DELETE=09 etc.)
Table           : <DB table name>
Program         : <ABAP program/include>
Line            : <source line number>
Duration        : <microseconds>
Rows            : <rowcount affected>
Return Code     : <0 = OK, non-zero = error>
SQL Command     : <multi-line SAP-encoded SQL with WHERE bindings>
Answer from DB  : <result info>
```

**BUFF** record body:
```
Call            : 03
Class           : 04 (buffer)
Operation       : <op code>
Table           : <DB table name>
Program         : <ABAP program>
Line            : <source line>
Duration        : <µs>
Buffer State    : I (insert) | R (read hit) | M (miss) | D (delete)
Search String   : <buffer key>
```

**AUTH** record body:
```
Object          : <auth object name>
Field=Value     : <field-value pairs being checked>
Class           : <result class>
Result          : OK | FAIL
```

**RFC** record body:
```
Function Module : <FM name>
Destination     : <RFC destination>
Direction       : in | out
Duration        : <µs>
Return Code     : <0 OK / non-zero error>
```

### Storage / file formats

The kernel writes the binary trace to:
- `/usr/sap/<SID>/<INST>/work/dev_w<N>` — partial info (DB connection events)
- Kernel ring buffer (live, only readable via SAP GUI ST01 in "Active Trace File" mode)
- When user does "Save As" in ST01 → ASCII export with the two-view structure above

The skill PARSES the ASCII export. To produce the export:
1. tx ST01 → start trace
2. Run target transaction
3. tx ST01 → stop trace
4. tx ST01 → "Analyze trace" → set filters → Display
5. From trace display → menu Trace File → Save As → choose path on app server

Then:
```python
from agents.skills.sap_st01_trace_reader import read_st01_trace as st01

records = st01.parse_export_file(
    system='TS3',
    server_path='/usr/sap/TS3/D00/work/jp_lopez_fb60_trace.txt'
)
# returns list of TraceRecord dataclass instances
```

## Output format

The skill writes results in two forms:
1. **Raw extract** — the file contents preserved as-is (for human review)
2. **Structured JSON** — parsed records with timestamp, event type, payload, identifiers

```json
{
  "system": "TS3",
  "user": "JP_LOPEZ",
  "trace_window": {"start": "2026-04-13T09:55:00", "end": "2026-04-13T10:00:00"},
  "sources": ["dev_w5", "20260413.AUD", "saved_st01_export.txt"],
  "records": [
    {
      "ts": "2026-04-13T09:57:54.269491",
      "type": "AUTH",
      "wp": 5,
      "pid": 8504,
      "tcode": "FB60",
      "authobj": "F_BKPF_BUK",
      "fields": {"BUKRS": "UNES", "ACTVT": "01"},
      "result": "OK"
    },
    {
      "ts": "2026-04-13T09:57:54.269700",
      "type": "DB",
      "wp": 5,
      "table": "FMIOI",
      "operation": "SELECT",
      "rowcount": 46
    }
  ]
}
```

## Related skills / artifacts

- `sap_data_extraction` — for transparent table reads (RFC_READ_TABLE)
- `sap_adt_api` — for source code reads (SIW_RFC_READ_REPORT, SVRS_*)
- `sap_class_deployment` — for ABAP class deployment via RFC_ABAP_INSTALL_AND_RUN

## Source / implementation

`.agents/skills/sap_st01_trace_reader/read_st01_trace.py`
