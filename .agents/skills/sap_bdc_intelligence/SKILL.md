---
name: SAP BDC Intelligence
description: >
  Batch Data Communication (BDC/SM35) forensic analysis for UNESCO SAP.
  Identifies Allos tool sessions vs system-generated payroll postings (Y1),
  traces session creators, decodes PROGID/FORMID patterns, and supports
  Allos replacement strategy with Fiori + BAPI alternatives.
---

# SAP BDC Intelligence

## Purpose

Forensic analysis of SAP Batch Input (SM35) sessions to answer:
1. **Who** creates BDC sessions? (Allos tool users vs system accounts vs payroll engine)
2. **What** transactions do they automate? (PA30, FB01, FMBB, etc.)
3. **Where** do they originate? (Local Excel/Allos vs cross-system Y1 payroll)
4. **Why** — business purpose classification (data upload, mass execution, cross-system posting)
5. **Replace with what?** — Fiori Upload App + BAPI, or direct RFC automation

## NEVER Do This

1. NEVER assume all BDC sessions are Allos — system Y1 payroll postings (MSSY1) look similar but are SAP-native tRFC
2. NEVER delete APQI/APQD records — they are the audit trail
3. NEVER replay BDC sessions without understanding the target transaction — some sessions modify payroll results
4. NEVER confuse APQI (queue index) with TBTCO (background jobs) — different mechanisms

## Script Location

```
Zagentexecution/mcp-backend-server-python/
  bdc_full_inventory.py       # Complete SM35 inventory (no limit, 90 days)
  bdc_deep_analysis.py        # Deep forensic analysis of specific sessions
  bdc_schema_probe.py         # APQI table schema discovery
  decode_numeric_bdc.py       # Numeric BDC session ID decoder
  sap_system_monitor.py       # report_batch_inputs() function (lines 349-507)
```

## Key Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `APQI` | BDC session queue index | GROUPID, CREATOR, CREDATE, QSTATE, QID, PROGID, FORMID |
| `APQD` | BDC session detail (screens/fields) | QID, SCREEN, FIELDNAME, FIELDVAL |
| `TBTCO` | Background jobs (some spawned by BDC) | JOBNAME, STATUS, SDLSTRTDT, AUTHCKNAM |

## Session Status Codes (QSTATE)

| Code | Meaning | Action |
|------|---------|--------|
| ` ` (blank) | NEW — waiting to be processed | Can replay |
| `E` | ERROR — failed during processing | Investigate errors |
| `P` | PROCESSING — currently running | Wait |
| `F` | DONE — completed successfully | Audit only |
| `Z` | BACKGROUND — queued for batch | Will run in next batch |

## CLI Usage

```bash
cd Zagentexecution/mcp-backend-server-python

# Full inventory (last 90 days, no limit)
python bdc_full_inventory.py

# Filter by creator
python bdc_full_inventory.py --creator MSSY1

# Extended output with PROGID/FORMID
python bdc_full_inventory.py --extended

# JSON output for downstream analysis
python bdc_full_inventory.py --json

# Deep analysis of specific session
python bdc_deep_analysis.py --qid <QID>

# Via system monitor (top-level summary)
python sap_system_monitor.py --report bdc --days 30
```

## Critical Discovery: Y1 Payroll Postings

> [!IMPORTANT]
> Most BDC sessions in UNESCO P01 are NOT Allos. They are **payroll postings from SAP system Y1** (HCM Payroll Backend).

### How to Identify Y1 Payroll Sessions

| Field | Value | Meaning |
|-------|-------|---------|
| CREATOR | `MSSY1` | Message Server System Y1 |
| PROGID | `MSSY1` or `PC00_M99_CIPE` | Payroll cross-posting engine |
| FORMID | `2026` | Year of payroll run |
| GROUPID pattern | `10155259V901` | PERNR + payroll-area + run-counter |

### Session Naming Decode
```
GROUPID: 10155259V901
  10155259  = Personnel number (PERNR)
  V9        = Payroll area code
  01        = Run counter
```

These are **tRFC/ALE** postings from Y1 → D01/P01, NOT Allos Excel uploads.

## Allos Detection Patterns

Real Allos sessions have different signatures:

| Indicator | Allos Session | Y1 Payroll |
|-----------|---------------|------------|
| CREATOR | Named user (e.g., J_SMITH) | MSSY1 (system) |
| PROGID | SAPMF05A, SAPMM06E, etc. | MSSY1, PC00_M99_CIPE |
| GROUPID | Descriptive name | PERNR-based |
| Volume | 10-500 per batch | 1000+ per run |
| Transaction | FB01, ME21N, PA30, PA40 | PCP0, PC00_M99_CIPE |

## Allos Replacement Strategy

| Pattern | Current (Allos) | Replace With |
|---------|-----------------|--------------|
| Data Upload (Excel → SAP table) | VBA macro → SM35 BDC | Fiori Upload App + BAPI backend |
| Mass Transaction Execution | BDC recording playback | Direct BAPI/RFC calls |
| Cross-system Extraction | Excel download → upload | OData service + Fiori app |

## Known Transaction Codes in BDC

| TCODE | Description | Domain |
|-------|-------------|--------|
| PA30 | Maintain HR Master Data | HCM |
| PA40 | Personnel Actions | HCM |
| PA20 | Display HR Master Data | HCM |
| PR05 | Personal Calendar | HCM |
| TRIP | Travel Management | Travel |
| FMBB | FM Budget Management | PSM |
| FB01 | Post Document | FI |
| FB60 | Enter Incoming Invoice | FI |
| F110 | Payment Run | FI |
| ME21N | Create Purchase Order | MM |
| PC00_M99_CIPE | Cross-posting payroll | HCM→FI |
| PCP0 | Payroll Processing | HCM |

## Known Failures & Self-Healing

| Error | Cause | Fix |
|-------|-------|-----|
| `APQI returns 0 rows` | CREDATE filter too narrow | Widen date range |
| `APQD empty for QID` | Session processed and purged | Normal for old sessions |
| `Timeout on APQI read` | Too many sessions | Add CREATOR or CREDATE filter |
| `MSSY1 not recognized` | Cross-system RFC user | It's the Y1 message server — not a bug |

## Integration Points

- **System Monitor**: `--report bdc` provides top-level BDC summary
- **Job Intelligence**: Background jobs (TBTCO) may be triggered by BDC sessions
- **Transport Intel**: BDC sessions often correlate with transport deployment dates
- **HCM Agent**: Payroll BDC sessions feed HCM domain analysis

## You Know It Worked When

1. Inventory distinguishes Allos sessions from Y1 payroll postings
2. CREATOR breakdown shows human users vs system accounts
3. GROUPID decode correctly extracts PERNR and payroll area
4. Extended mode shows PROGID/FORMID for cross-system tracing
