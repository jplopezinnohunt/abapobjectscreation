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
| **CDHDR** | `cdhdr_history` ✅ **READ THIS ONE** · `cdhdr` ⚠️ stale subset | Change-document **headers** (who/when/object/tcode) | Audit-trail event log; base of `cdhdr_activity_mapping.py` (OBJECTCLAS+TCODE→activity). **This is the PM base, not CDPOS.** **BOTH GOLD TABLES ARE CDHDR** — verified 2026-07-31: all 7,810,913 keys of `cdhdr` are contained in `cdhdr_history` (INTERSECT = 100%), so `cdhdr` is a superseded snapshot (cut 20260316) and `cdhdr_history` accumulates (to 20260620). **`cdhdr` is not merely older, it is SCOPE-FILTERED and therefore misleading:** it holds 57 object classes against 72, and reading it concludes that **PBC has ZERO change activity when it has 3,449,049** — plus Real Estate (REBD_*/REBP_*/RETM_*), the custom HR infotypes Y_HR_IT1080/1081/9080/9081 (5,330) and YFMFUNDC5 (2,221), all invisible. Its window covers 20260220–20260316, when PBC changes had already started, so this is a CLASS FILTER and not a date cut. | OBJECTCLAS+OBJECTID+CHANGENR | headers persist; accumulate deltas into `cdhdr_history` ONLY |
| **CDPOS** | *(not extracted)* | Change-document **detail** (field, value old→new) | Would give field-level change events. DEFERRED — no value now ([[project-cdpos-extraction-deferred]]). Only `INC-000005240_cdpos_a_hizkia.json` = 2 docs. | OBJECTCLAS+OBJECTID+CHANGENR+TABNAME+FNAME | n/a |
| **REGUH** | `reguh` ✅ 3,707,737 | Payment-run **header**: one row per payee per payment run (F110) — house bank, method, amount, currency, payee name/address | The payment domain's spine. Joins the AP invoice to the bank file: `REGUH` → `REGUP` (items) → DMEE/`ZSAPFPAYM_REPLAY`. Serves **BOTH Payment_BCM and FI-AP** — it is where an AP open item becomes a disbursement, so an AP analysis that skips it stops at the invoice. | LAUFD+LAUFI+ZBUKR+LIFNR+**KUNNR**+EMPFG+VBLNR | 20160104–20260512 (**predates the 2024–2026 scope — 10 years present**) |
| **FMIOI** | `fmioi` ✅ 2,190,893 | FM **commitment** line items (open items): the money PROMISED but not yet spent — reservations, requisitions, purchase orders | The commitment leg of budget→commitment→actual (flow B2C2A). 8,380 funds, 9 company codes, GJAHR 2017–2026. `REFBT` gives the committing document: 110 funds reservation (1,381,250) · 020 purchase order (588,255) · 040 purchase requisition (172,517) · 010 (42,746) · 060 (6,125). | REFBN+REFBT+RFPOS+GJAHR (+PERIO) | 2017–2026 |
| **RSAU / SAL** (SM20 Security Audit Log) | `rsau_audit_history` ✅ built | Security audit events (logon, tcode/report start, RFC calls, sensitive changes) | **THE volatile system log.** Read via FM `RSAU_API_GET_LOG_DATA(IS_INTERVAL)`, **chunked ≤6h** (a 2-day call hangs on volume; the conn poisons every ~12 calls → recycle; transient `partner not reached` → resilient reconnect). Dedup by MD5 row-hash PK. **Retention is ≥4 months, NOT 15/61** (full volume back to the Feb-21 window edge; true boundary not yet hit — 15.6M rows captured). | 28 cols incl. SLGUSER/SLGTC/SLGREPNA/TXSUBCLSID/SEVERITY/SAL_DATA | volatile → accumulate ≤14d |


### REGUH and FMIOI — two traps that produce confident wrong numbers

**REGUH · a PROPOSAL is not a PAYMENT.** `XVORL = 'X'` marks an F110 *proposal* run. Measured
2026-07-31: **358,106 of 3,707,737 rows (9.7%) are proposals**, not disbursements. Counting
REGUH rows as payments overstates by that much, and the error is invisible because every row
looks like a payment. Always filter `XVORL <> 'X'` (3,349,631 real).

**REGUH · KUNNR was not extracted, and it is part of the key.** The SAP key is
`LAUFD+LAUFI+ZBUKR+LIFNR+KUNNR+EMPFG+VBLNR`; the gold table has no `KUNNR` column, and
**1,748 key collisions** are the direct consequence — customer refunds collapsing onto the
same key as vendor payments. Enrich by key, never re-extract ([[feedback_missing_fields_by_key]]).

**REGUH · a third of it is not vendors.** `PERNR` is populated on **1,195,826 rows (32%)** —
payments to EMPLOYEES (travel claims, payroll). That makes REGUH an **HCM↔Payment bridge**, not
a pure AP table, and any "vendor payment" metric computed over the whole table is wrong by a
third. Remember to label DISTINCT payees vs REGUH LINES ([[feedback_distinct_vs_lines]]).

**FMIOI · never hand-roll availability from WRTTP.** The value types present (65: 776,201 ·
51: 588,255 · 82: 415,403 · 81: 176,300 · 52: 172,517 · 50: 42,746) invite an
`available = budget − commitment − actual` formula. That approach is **REFUTED** — AVC
availability comes from the STANDARD (`FMAVCT`/`FMAVCR`, or the AVC read FM), never from
arithmetic over FM document tables ([[feedback_avc_real_from_standard_not_handrolled]]).
FMIOI answers *what is committed and against which document*, not *what is left*.

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
> + `p01_proj_prps_sync.py` (wrote to the STALE `knowledge/domains/PSM/` path). Reading rule: the
> **P01 AND D01** secured RFC_READ_TABLE wrapper (class SAIS) **REJECTS ROWSKIPS** (`OPTION_NOT_VALID`)
> → cannot page; read **`ROWCOUNT=0` partitioned by FIKRS** (there is NO ~60k platform ceiling — BPGE
> returned 390,707 rows in one ROWCOUNT=0 call; partition for memory/latency only, not a hard limit —
> claim #244 corrected S-089). **D01 ROWSKIPS rejection confirmed empirically s093 (2026-06-29) on
> FMFINCODE/FMFINT: rc=5 OPTION_NOT_VALID** — identical behavior to P01.
>
> **P01→D01 gap analysis (s093, 2026-06-29):** gap ≈ 63K rows. FMFINCODE: 19,523 missing in D01
> (UNES-centric). YTFM_FUND_C5: 17,564. YTFM_FUND_CPL: 6,345. FMFCTR: 135. FMCI/TFKB: GAP=0.
> D01 already has ~71% of production funds. **Write phase not yet executed** — requires full-field
> live re-extraction (gold `funds` table has only 5 key cols, not usable as write source — claim #284).
> Full gap breakdown: claim #283. Sync method: `sap_master_data_sync` skill FM extension section.
>
> **V01 ROWSKIPS rejection confirmed empirically 2026-07-02** (extraction for the sibling `unescrp`
> actor-chain grounding probe): identical `rc=5 OPTION_NOT_VALID: "ROWSKIPS requires GET_SORTED"` (class
> SAIS) on USR02/PA0001/PA0105. **This closes the class across all 3 systems we read (P01, D01, V01):
> every secured `RFC_READ_TABLE` wrapper in this landscape rejects `ROWSKIPS` — always read
> `ROWCOUNT=0` single-call, partition the key space (not offset-paginate) on `DATA_BUFFER_EXCEEDED`.**
> Same pattern as `accumulate_logs.py::_read_window` and `p01_fm_ps_bcs_masterdata_refresh.py`. Claim #319.

## V01 actor-chain grounding tables (2026-07-02, for sibling `unescrp` project)
**Why:** `unescrp`'s `scripts/probes/check_actor_chain.py` scores whether a staff member is usable for an
E2E test (eligible + a complete actor chain whose officers exist as real users on the target system). It
was grounded on D01 only; needed V01 too. The interactive user has SSO-only access to V01 (no Basic
password) and V01's live ADT endpoint challenges Basic (realm `V01/350`) → blocked from the unescrp side.
**This project's own RFC/SNC service path (`ConnectionGuard("V01")` in
`Zagentexecution/mcp-backend-server-python/rfc_helpers.py`, `SAP_V01_*` env creds) connects independently
in ~1s and reads tables** — so the extraction was done here and handed off as a golden DB. Host
`hq-sap-v01.hq.int.unesco.org`, client 350. Script: `Zagentexecution/sap_data_extraction/scripts/extract_v01_actor_grounding.py`.

New per-system DB (mirrors `p01_gold_master_data.db` convention): **`v01_gold_master_data.db`**
(~28MB after the Funds+WBS tables below were added, gitignored, LOCAL-ONLY like the P01/D01 golds).

| SAP source | Gold DB table | What it is | Key | Rows | Notes |
|---|---|---|---|---|---|
| **USR02** | `v01_usr02` | User master authorization (lock/type) | BNAME | 5,552 | UFLAG: 64=admin-locked (5,332, majority — typical pre-prod copy), 0=unlocked (160), 192/96/128/224 = other lock reasons (60 total). Probe must read UFLAG bitmask for usability, not assume unlocked. |
| **PA0001** | `v01_pa0001` | HR Org Assignment infotype | PERNR+BEGDA | 106,995 | Cols PERNR,PERSK,GSBER,BUKRS,ANSVH,BEGDA,ENDDA. GEF-eligible pool = `GSBER='GEF' AND BUKRS='UNES' AND ANSVH='01'` → **3,093 distinct PERNR** (validity BEGDA/ENDDA applied downstream by the probe, not pre-filtered here). |
| **PA0105** | `v01_pa0105` | Communication infotype, SUBTY='0010' only | PERNR+SUBTY | 7,835 | Cols PERNR,SUBTY,USRID_LONG (staff work email). Filtered server-side to SUBTY='0010' only — not the full infotype. |

Claim #320 (connectivity) + #319 (ROWSKIPS class). Cross-link: [[reference_p01_strg_columns_unreadable]],
[[reference_d01_rowskips_and_adt_ddic_limits]] (now superseded in scope by the 3-system generalization above).

> **PA0105 SUBTY='0001' = the SAP-user link, a DIFFERENT subtype than the '0010' row above (2026-07-03,
> claim #333).** Field **USRID** (CHAR12, e.g. `A_COWLING`) carries PERNR→SY-UNAME/BNAME; `USRID_LONG` is
> empty on these rows (it belongs to '0010' = work email, above — do not conflate the two subtypes).
> The staff-time-distribution upload (`YFMOUTPUT`/`YFM_OUTPUT_MANAGEMENT` SaveFormData, see
> `Zagentexecution/tasks/2026_06_25_staff_time_distribution_bcm/ANALYSIS.md` §5) resolves each employee's
> SAP user via this link; when absent in D01/V01 the slot never fills. Measured gap P01(5,292)→D01(857
> missing)/V01(775 missing), synced 2026-07-03 via `BAPI_EMPLCOMM_CREATE` (never direct table insert) —
> `Zagentexecution/tasks/2026_07_03_pa0105_user_sync/pa0105_user_sync.py` + `README.md`. Claims
> #333-#337. Also reconfirms the SAIS wrapper's IN-clause/multi-condition WHERE limitation on PA-module
> tables (claim #337, same class as #319/#328) — read whole + filter in Python.

## V01 Funds + WBS master data (2026-07-02, for sibling `unescrp` project)
**Why:** companion to the actor-chain pull above — `unescrp`'s `specifications/test-data/crp-usable-test-data.xlsx`
"usable test data" computation needs V01 Funds + WBS master data (date validity + account-assignment +
budget), not just actors. Same rationale: requester has SSO-only V01 access, this project's own
`ConnectionGuard("V01")` RFC/SNC path pulls it independently. Script:
`Zagentexecution/sap_data_extraction/scripts/extract_v01_funds_wbs.py`. Same DB as the actor pull:
`v01_gold_master_data.db`.

| SAP source | Gold DB table | What it is | Key | Rows | Notes |
|---|---|---|---|---|---|
| **FMFINCODE** | `v01_fmfincode` | Fund master | FIKRS+FINCODE | 61,626 | Cols FIKRS,FINCODE,DATAB,DATBIS (date validity — NOT FIVOR, which does not exist on this table, claim #321),TYPE,FINUSE,PROFIL,DECKUNG,DATE_EXP,DATE_CAN. |
| **PRPS** | `v01_prps` | WBS element master | PSPNR (OBJNR=PR+PSPNR) | 49,392 | Cols incl. POSID,OBJNR,PBUKR,PRART,STUFE,PLAKZ,BELKZ (account-assignment flag; NOT PSTRT, which does not exist on this table, claim #321),KOSTL,LOEVM,PRPS_STATUS. BELKZ='X' (account-assignable) 48,451 rows (98.1%), BELKZ='' (structural) 941 rows (1.9%). |
| **JEST** (WBS only) | `v01_jest` | System status per object, filtered `OBJNR LIKE 'PR%'` | OBJNR+STAT | 284,483 | Cols OBJNR,STAT,INACT. STAT='I0002' AND INACT='' = REL (14,509 released WBS); STAT='I0001' = CRTD. |
| **PROJ** | `v01_proj` | Project definitions | PSPNR (OBJNR=PR+PSPNR) | 13,037 | Cols PSPID,PSPNR,VBUKR (company code — note the field is VBUKR on PROJ, not PBUKR as on PRPS),OBJNR,INACT,LOEVM. |
| **FMAVCT** (ledger 9H) | `v01_fmavct_2024`/`_2025`/`_2026` | AVC (Availability Control) totals | RFIKRS+RFUND+RFUNDSCTR+RCMMTITEM+RYEAR+RRCTY (row-index merged, no single PK column — see claim #322) | 14,086 / 2,577 / 44 | Field-split extraction (5 chunks, row-index merge — table exceeds 512-byte RFC_READ_TABLE line buffer, claim #322). RRCTY: 0=consumption, 1=budget. RVERS='000', RLDNR='9H'. Amounts HSLVT+HSL01..HSL16 (FM-area currency). Do NOT use for a hand-rolled availability formula — go through the standard AVC read (FMAVCR/FMAVC FM), per [[feedback_avc_real_from_standard_not_handrolled]]. |

**Reference-fund coverage (D01 cost-recovery test set S-166, claim #323):** all 8 present in
`v01_fmfincode` — 196EAR4042, 538GLO5000, 301EGY4072, 465BRZ0002, 469GLO2000, 650RER0008, 633CRP9003,
633CRP9200. **Date-EXPIRED for a 2026 test** (DATBIS in 2024): 301EGY4072, 469GLO2000, 633CRP9003 (2nd
validity row extends further, see claim #323), 633CRP9200. **Still date-valid through 2026:** 196EAR4042
(DATBIS 2026-08-31), 538GLO5000 (2026-09-30), 465BRZ0002 (2026-03-31), 650RER0008 (2026-12-31). WBS
633CRP9003 present in `v01_prps` with BELKZ='X' plus a full multi-level child hierarchy.

Claims #321 (field-name quirk), #322 (FMAVCT extraction pattern), #323 (reference-fund coverage).
Cross-link: [[feedback_p01_sais_rowskips_rejection]], [[feedback_avc_real_from_standard_not_handrolled]].

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
**Not yet catalogued: the remaining ~268 of 311 tables** (FI bsX, FM fmavc*/fmifiit*, BCM bcm_*,
config T0*, etc.). Extend incrementally; each table gets: real SAP name, what it is, how we use it, key,
provenance. Companion of capability-model dimension **D_DATA**.

### Priority extraction backlog (D_DATA gaps confirmed this session)

| SAP table | What it is | Why needed | Key | TCode | Added |
|---|---|---|---|---|---|
| **T001U** | Cross-company clearing pairs (OBYA) — for each BUKRS1/BUKRS2 direction: the two clearing G/L accounts (SAKON payer side, UKON payee side) | STEM company code has 0 pairs; MGIE has 16 (8 institutes × 2 directions). Cannot query existing config from Gold DB → live RFC required. Claim #279. | BUKRS1+BUKRS2 | OBYA / IMG: "Define Intercompany Clearing Accounts" (Real-Time CO-FI Integration) | 2026-06-26 |
