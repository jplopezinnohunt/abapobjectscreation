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
| **RSAU / SAL** (SM20 Security Audit Log) | `rsau_audit_history` ✅ built | Security audit events (logon, tcode/report start, RFC calls, sensitive changes) | **THE volatile system log.** Read via FM `RSAU_API_GET_LOG_DATA(IS_INTERVAL)`, **chunked ≤6h** (a 2-day call hangs on volume; the conn poisons every ~12 calls → recycle; transient `partner not reached` → resilient reconnect). Dedup by MD5 row-hash PK. **Retention is ≥4 months, NOT 15/61** (full volume back to the Feb-21 window edge; true boundary not yet hit — 15.6M rows captured). | 28 cols incl. SLGUSER/SLGTC/SLGREPNA/TXSUBCLSID/SEVERITY/SAL_DATA | volatile → accumulate ≤14d |

### RSAU triage — 4-month sample (15,605,644 rows, 2026-02-21→06-21, 108 days, verified 2026-06-21)
~150K rows/day. **By event class:** RFC Function Call 3.81M (45%) · Report Start 2.20M (26%) · RFC/CPIC Logon 1.31M (15%) · **Dialog Logon 514K (6%)** · **Transaction Start 362K (4%)** · Other 272K · **User Master Changes 27K** · System Events 135. **Severity:** Low 7.85M (92%) · Medium 611K · High 35,681. **Real human top users** (Dialog+Tcode, excl. technical): P_IKOUNA 17K, MP_ANCUTA 14K, V.VAURETTE 11K, T_COLLOCA 11K, A_VASAS, N_MENARD, M_JOSHI, F_DERAKHSHAN.
**Retention filter (how we use it):** KEEP always = **Dialog Logon + Transaction Start (human "way of working") + User Master Changes (security) + SEVERITY=High**. SAMPLE/DROP = RFC Function Call + RFC/CPIC Logon (machine/MULESOFT/BRIDGE noise, ~60% of volume). That cuts ~60-75% and keeps the signal.
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

## Extraction method — how to read any SAP object
The **method registry** (`process_mining/method_registry.py` + `brain_v2/method_registry.json`, built S-087) is the resolver: given ANY SAP object name, it returns (extract_method, constraint, analyze_method, retention) by looking up DD02L.TABCLASS + element-specific overrides. Before extracting a new table, run: `python process_mining/method_registry.py <TABLE>`. This prevents per-session rediscovery of extraction paths (claim #241, rule `feedback_use_method_registry_before_extracting`).

## FM/BCS + PS master-data backbone (refreshed 2026-06-22 from P01)
> Refresher: **`scripts/extraction/p01_fm_ps_bcs_masterdata_refresh.py`** (ONE idempotent script,
> P01 LIVE → canonical golden DB). Supersedes `refresh_funds_from_live.py` (used ROWSKIPS — now broken)
> + `p01_proj_prps_sync.py` (wrote to the STALE `knowledge/domains/PSM/` path). Reading rule: the P01
> secured RFC_READ_TABLE wrapper (class SAIS) **REJECTS ROWSKIPS** (`OPTION_NOT_VALID`) → cannot page;
> read **`ROWCOUNT=0` partitioned by FIKRS** (there is NO ~60k platform ceiling — BPGE returned 390,707
> rows in one ROWCOUNT=0 call; partition for memory/latency only, not a hard limit — claim #244 corrected S-089).

| SAP source | Gold DB table | What it is | Key | Notes |
|---|---|---|---|---|
| **FMFINCODE** | `funds` | Fund master (BCS dim) | FIKRS+FINCODE | 67,408 (UNES 56,639). 100% have EN text. |
| **FMFINT** | `FMFINT` | Fund text (EN) | FIKRS+FINCODE+SPRAS | 67,410 — ALL 9 institutes (was 820/3 only). |
| **FMFCTR** | `fund_centers` | Funds Center master (BCS dim) | FIKRS+FICTR | 787 |
| **FMFCTRT** | `fund_centers_text` ✅NEW | Funds Center text (EN) | FIKRS+FICTR+SPRAS | 787 |
| **FMCI** | `commitment_items` ✅NEW | Commitment Item master (BCS dim, **GJAHR='0000'** year-indep) | FIKRS+GJAHR+FIPEX | 205 total (UNES~26). One DQ curiosity: UNES FIPEX `10'` (apostrophe, faithful to P01). |
| **FMCIT** | `commitment_items_text` ✅NEW | Commitment Item text (EN) | FIKRS+FIPEX+SPRAS | 205 |
| **TFKB** | `functional_areas` ✅NEW | Functional Area (BCS dim) | FKBER | 9 (0001..0980) |
| **TFKBT** | `functional_areas_text` ✅NEW | Functional Area text (EN) | FKBER+SPRAS | 9 |
| **PROJ** | `proj` | PS Project definition | PSPID | 13,976 (max ERDAT=2026-06-22, fresh). |
| **PRPS** | `prps` | PS WBS element | POSID | 59,749 (fresh). OBJNR → status (jest). |
| **PRHI** | `proj_hierarchy` ✅NEW | PS project hierarchy (UP/DOWN/LEFT/RIGHT; cols renamed LEFTND/RIGHTND, reserved words) | POSNR | 59,751 — 100% of PRPS.PSPNR links here. |
| **YTFM_FUND_C5 / YTFM_C5 / YTFM_OUTPUT(_T)** | `ytfm_fund_c5` (17,598) etc. | UNESCO custom C/5 biennium BCS model (fund×biennium→Output) | see `p01_ytfm_biennium_sync.py` | bienio 43 (2026-2027) active. |

**Verified NOT used by UNESCO (don't re-extract):** `FMMEASURE` (Funded Program) = **0 rows on P01** —
UNESCO models "projects" via **PS (PROJ/PRPS)**, not the FM Funded-Program dimension. `FMFPO` ≈ empty (19).
The BCS budget *documents/totals* (`fmbh`/`fmbl`/`bpge`/`bpja`) are transactional, already present, and are
NOT master data — out of scope of this refresher.

## TODO (extend this catalog)
Started with the log/change/job/upgrade/audit tables + the FM/BCS+PS master-data backbone above.
**Not yet catalogued: the remaining ~270 of 311 tables** (FI bsX, FM fmavc*/fmifiit*/fmioi, BCM bcm_*,
config T0*, etc.). Extend incrementally; each table gets: real SAP name, what it is, how we use it, key,
provenance. Companion of capability-model dimension **D_DATA**.
