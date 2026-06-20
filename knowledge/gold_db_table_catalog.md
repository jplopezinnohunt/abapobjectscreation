---
name: Gold DB Table Catalog — what each table is for and how we use it
description: Per-table registry of the P01 Gold DB (canonical p01_gold_master_data.db). For every table: real SAP name, what it is, how we use it, key, provenance, and any analysis-rename mapping. Started 2026-06-20 (user directive). Convention: use REAL SAP table names to avoid the CDPOS/CDHDR-style confusion.
type: project
---

# Gold DB Table Catalog

**Canonical DB:** `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db` (~6.4GB, gitignored, LOCAL-ONLY).

## Naming convention (user directive 2026-06-20)
1. **Use the REAL SAP table name** as the Gold DB table name. Analysis-purpose suffixes (`*_upgrades`, `*_2026_jobs`, `*_inc5638`) caused confusion (we couldn't find "CDPOS" because data was renamed) — avoid them. If a table is a *scoped subset*, keep the real name and record the scope in this catalog, don't bake the scope into the table name.
2. **Provenance by prefix** (rule [[feedback_gold_db_is_p01_provenance]]): bare name = **P01** data; `d01_`/`v01_` prefix = that system. A P01 *data* fact must be verified against P01.
3. **Accumulators** (rolling history of logs P01 purges) carry the `_history` suffix on the real SAP name (e.g. `tbtco_history`).

## Logs / event streams (the "way of working" raw material)
| SAP source | Gold DB table | What it is | How we use it | Key | Se borra en P01? |
|---|---|---|---|---|---|
| **TBTCO** | `tbtco` + `tbtco_history` | Background job headers (status, start/end, scheduler) | Job/batch process mining: who ran which program, when, status, duration | JOBNAME+JOBCOUNT | ~14d → accumulate |
| **TBTCP** | `tbtcp` + `tbtcp_history` | Job step list incl. **VARIANT** | Job INTENT via variant (program + targeted scope) | JOBNAME+JOBCOUNT+STEPCOUNT | with TBTCO → accumulate |
| **CDHDR** | `cdhdr` + `cdhdr_history` | Change-document **headers** (who/when/object/tcode) | Audit-trail event log; base of `cdhdr_activity_mapping.py` (OBJECTCLAS+TCODE→activity). **This is the PM base, not CDPOS.** | OBJECTCLAS+OBJECTID+CHANGENR | headers persist; accumulate deltas |
| **CDPOS** | *(not extracted)* | Change-document **detail** (field, value old→new) | Would give field-level change events. DEFERRED — no value now ([[project-cdpos-extraction-deferred]]). Only `INC-000005240_cdpos_a_hizkia.json` = 2 docs. | OBJECTCLAS+OBJECTID+CHANGENR+TABNAME+FNAME | n/a |
| **RSAU / SAL** (SM20 Security Audit Log) | `rsau_audit` + `rsau_audit_history` *(to create)* | Security audit events (logon, tcode start, report start, sensitive changes) | **THE volatile system log that purges** (~236K rows/day, ~3.5M / 15d). Read via FM `RSAU_API_GET_LOG_DATA`, **chunked by ≤6h** (a 2-day call hangs). Active on P01 (verified 2026-06-20). | DATE+TIME+USER+TCODE+... | **YES ~15d → MUST accumulate** |
| **SYSLOG** (SM21 system log) | `syslog` + `syslog_history` *(to create)* | System messages (starts, errors, locks, dumps) | Read via FM `SALC_MSC_READ_SYSLOG` (START/END_TIMESTAMP). Custom `Z_READ_SYSLOG` is BROKEN (SYNTAX_ERROR SAPLZSLD). Returned 0 lines last-24h test — verify ONLY_LOCAL / per-server / window. | timestamp+host+user | YES (circular) → accumulate |
| **SNAP** (ST22 dumps) | *(blocked via RFC)* | ABAP runtime-error dumps | Error-event stream. P01 returns TABLE_NOT_AVAILABLE via RFC_READ_TABLE → needs ST22/dump FM. | DATUM+UZEIT+AHOST+UNAME+MODNO+SEQNO | YES → FM path pending |

## Upgrade / lifecycle logs (already in Gold DB — these PERSIST, don't purge)
> ⚠️ These carry analysis-suffix names — flagged for rename to real SAP names per the convention above.
| SAP table | Current Gold DB name | → rename to | What it is | How we use it |
|---|---|---|---|---|
| **SMODILOG** | `smodilog` ✓ | (ok) | Modification adjustment log (SPAU/SPDD) | Measure SPAU effort per upgrade; HR/Payroll = #1 modified domain |
| **PAT03** | `pat03` ✓ | (ok) | Applied support-package/patch log | Patch history per component/upgrade |
| **TPALOG** | `tpalog_upgrades` | **`tpalog`** (scope=upgrade windows in catalog) | Transport step execution log | Import timing/return codes during upgrades |
| **CVERS** | `cvers` ✓ | (ok) | Installed component releases | Current SP-stack level |
| **UVERS** | `uvers` ✓ | (ok) | Upgrade/put version history | When each component was upgraded |
| **TBTCO** (upgrade cut) | `tbtco_upgrade2026_jobs` | merge into **`tbtco`/`tbtco_history`** (scope=2026 upgrade) | Jobs around the 2026 upgrade | Upgrade-window job activity |
| (SPAU objects) | `spau_2024_objects` | **`smodilog`-derived** (SPAU is a tcode, not a table) | Objects flagged in SPAU 2024 | UNESCO mods vs SAP-delivered split |

## Provenance/system-variant tables (correctly prefixed)
`d01_tstc`/`d01_tstct`/`d01_tstcp` (tcode→program map, system-invariant, pulled from D01), `d01_seo_*` (class anatomy from D01), `d01_t028*`/`d01_t033*` (config compare), `p01_*` vs `d01_*` master-data pairs (GL/cost-element sync). Rule: never assert a P01 fact from a `d01_` table.

## TODO (extend this catalog)
Started with the log/change/job/upgrade/audit tables (the active topic). **Not yet catalogued: the remaining ~280 of 306 tables** (FI bsX, FM fmavc*/fmifiit*, BCM bcm_*, config T0*, etc.). Extend incrementally; each table gets: real SAP name, what it is, how we use it, key, provenance. Companion of capability-model dimension **D_DATA**.
