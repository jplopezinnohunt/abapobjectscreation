---
name: UNESCO SAP — real operating model (integration-orchestrated, from the audit log)
description: The discovered operating model of UNESCO's P01 — SAP is NOT operated by dialog, it is ORCHESTRATED FROM OUTSIDE (80.6% of business RFC = external satellites). Built from rsau_audit_history (15.6M, 4 months) via the 2-axis system-explanation engine (process × origin). 91.1% of business RFC explained. 2026-06-21.
type: project
---

# UNESCO SAP — Real Operating Model (from the logs)

**Headline:** UNESCO does not "use" SAP via dialog — it **orchestrates SAP from satellite applications**.
Measured from the RSAU audit log (15.6M rows, 4 months Feb–Jun 2026, RFC Function Call stream with
host/dest/user): **80.6% of business RFC traffic is driven by EXTERNAL satellites**, and the 2-axis
system-explanation engine now maps **91.1% of business calls** to a known process. Method + engine:
`process_mining/rfc_process_classifier.py` (replicable; coverage climbed 67.0%→76.2%→91.1% in one session).

## The 2-axis method (the model)
Every RFC/BAPI/IDoc call is explained on two axes — neither alone is enough:
- **PROCESS** (from the FM name → business process). Coverage **91.1%**.
- **ORIGIN** (from host/dest/user → which system/satellite). **80.6% external.** Without origin, a MuleSoft
  call and an internal report look identical. (e.g. `Y_BAPI_YPS8` 461K looked "unknown, 1 caller" → with
  host/dest/user it is **MuleSoft, external, 8 logical-port GUIDs, RFC-inbound** = the project-financials sync.)
A call is explained as a **(process, origin-system)** pair; the worklist = the intersection of gaps.

## The satellites (who orchestrates what)
| Satellite (origin) | Volume | What it does | Key FMs / interfaces |
|---|---|---|---|
| **MuleSoft** (external bus) | **1.62M** | **SAP ↔ PPM/Salesforce project-financials sync** (reads WBS/project financials, creates funds, project IDocs) | `Y_BAPI_WBS_FINANCIAL_DATA_1` (974K), `Y_BAPI_YPS8` (461K), `Y_BAPI_CUSTOMER_GET_ID` (148K), `Y_FMKU_0050_CREATE_WITH_COMMIT`, IDOCS_OUTPUT_TO_R3. RFCDES: `MULESOFT_PROD` (HTTP/G) + `MULESOFT_P01_IDOC` (TCP/T) |
| **BRIDGE-RFC** (external portal) | **875K** | **Procurement + Travel + master-data-read self-service portal** | `ZBAPI_VENDOR_GETDETAIL/SEARCH*`, `BAPI_PR_GETDETAIL`, `BAPI_PO_GETDETAIL1`, `BAPI_ENTRYSHEET_GET*`, `BAPI_TRIP_CHECK_STATUS`+`YHRTRV_IF_*`, `ZBAPI_READ_BNKA`, `Z_RFC_GET_USER` |
| **Named-user BAPI** (portal-as-user) | 501K | Receiving/AP posting under the user's ID | `BAPI_GOODSMVT_CREATE` (GR), `BAPI_INCOMINGINVOICE_CREATE1`, `BAPI_PR_CHANGE`, `BAPI_PO_CREATE1` (E_SILVA/L_NEVES/MP_ANCUTA) |
| **WF-BATCH** (workflow auto) | — | HR lifecycle (infotype org/relationships HR_IT1000/1001 via RE_RHAKTI00) | — |
| **PBC engine** (ZPBC/HIPER) | — | Payroll-commitment generation (FMRESERV 6.4M, blank tcode) | ZPBC_PERIOD_CLS_EXEC |
| **us (JP_LOPEZ)** | ~80–124K | OUR extraction (filter out) | RFC_READ_TABLE, DDIF_*, RSAU_API_* |

## What is still DIALOG (the minority)
Vendor master change (XK02/M_AYIMBA 72K — dual-channel with BAPI), GL master (FS00, stable/rare), bank (FI01),
some FI postings. Dialog is a MINORITY for P2P, Travel, FM/Project master, HR-org.

## By-month (the REAL %, normalized) + multi-channel (2026-06-21)
**The 80% external is STRUCTURAL, not an artifact** — business RFC external share by month: 2026-02=86%,
03=80%, 04=80%, 05=82%, 06=77% (MuleSoft ~50% / BRIDGE-RFC ~25% / named ~15% every month). Our own footprint
(JP_LOPEZ) was an April burst (11,263) — separable; the external rate holds without it. By-month is the right
normalization (raw totals are skewed by partial months + our extraction bursts).
**Multi-channel operation model** (combine these, not just RFC):
1. **RFC/BAPI satellites** — ~80% external, the dominant channel (this doc).
2. **IDoc** — PROJECT + BW (RSINFO/RSRQST) + exchange rates (edidc).
3. **Jobs / batch** — ~50–58K jobs/month (TBTCO) = heavy internal automation (the PBC engine, RE_RHAKTI00, etc.).
4. **Direct-table-access** — ~99% US (RFC_READ_TABLE by JP_LOPEZ 76K); the only external is **`RFC-SSIS`** (123) =
   a Microsoft SSIS BI/data-warehouse extractor reading SAP tables raw. Minor but a real (BI) channel.
Dialog is the minority across all of these. TODO: a unified channel mix % (RFC vs IDoc vs Jobs vs direct-table vs dialog).

## External→internal: WHAT the system does (read vs write per satellite, 2026-06-21)
Each external call does something internal — read or write. The direction split tells what each satellite IS:
- **MuleSoft** (1.62M): READ-dominant (`Y_BAPI_YPS8`/`Y_BAPI_WBS_FINANCIAL_DATA_1` = reads project financials OUT
  to PPM/Salesforce) + targeted WRITES of fund master (`FM_FUND_CREATE_RFC`/`FM_FUND_CHANGE_RFC`) + project IDoc out.
- **BRIDGE-RFC** (875K): **92% READ** — a display/read portal (vendor/PR/PO/service/travel/bank/user details OUT
  to the procurement+travel self-service UI). Barely writes.
- **named-user portal** (501K): **balanced 37% read / 32% write — THE write channel.** Real transactions + master
  changes enter under the user's ID: `BAPI_PR_CHANGE` (37K), `Y_RFC_FMRP_RFFMEP1FX_FI_POST` (31K, FI posting),
  `ZBAPI_VENDOR_CHANGE` (24K, vendor master).
**Characterization: SAP is the authoritative SYSTEM-OF-RECORD.** ~80% of external traffic READS it (satellites pull
data out: project financials→PPM, procurement/travel→portals); the WRITES (transactions + master changes) flow back
in concentrated through the portal-as-user channel (+ MuleSoft funds). Dialog is the minority everywhere. The system
FEEDS satellites (read) and RECEIVES targeted transactions (write) — operated almost entirely by integration.
(Caveat: verb-based READ/WRITE undercounts non-standard read names like YPS8/WBS_FINANCIAL_DATA — MuleSoft is more
read-heavy than its 9% literal READ suggests.)

## Finer breakdown via host/dest/path — the satellites have NAMES (2026-06-21)
Parsing PARAMX `caller: host= dest= user=` gives the real external systems, not just the RFC user:
- **MuleSoft = a FLEET of 174 endpoints** (dest GUIDs = SOAMANAGER logical ports), hosts `synctrigger-sap-app-6d/76/79/6f…`
  — a **"synctrigger" sync-worker fleet** all calling `Y_BAPI_WBS_FINANCIAL_DATA_1` + `Y_BAPI_YPS8` = triggered
  **project-financials sync** (→ PPM/Salesforce; connect to `unescore20-PPM-brain`).
- **BRIDGE-RFC = ORION EAI** — a single server `HQ-ORION-EAI03` (2 endpoints). The procurement/travel/master-read
  portal middleware is **ORION** (Enterprise Application Integration). 
The host field NAMES the system: `synctrigger` (MuleSoft sync fleet) + `HQ-ORION-EAI03` (ORION EAI). Granularity
ladder: origin-user → dest-GUID (the flow/connection) → host (the physical worker/server). TODO: resolve the 174
MuleSoft dest GUIDs to named SOAMANAGER logical ports; cross host inventory with RFCDES + the .NET/integration map.

## MuleSoft = 17 flows (bidirectional PPM↔SAP project+fund sync) + ecosystem link confirmed (2026-06-21)
**The 174 MuleSoft dest-GUIDs collapse to 17 distinct FLOWS** (by dominant call) — 174 was connection instances,
17 is the real flow count:
- READ (out): `Y_BAPI_WBS_FINANCIAL_DATA_1` (975K, 26 ep), `Y_BAPI_YPS8` (463K, 23 ep), `Y_BAPI_CUSTOMER_GET_ID` (148K, 34 ep).
- WRITE (in): `Y_FMKU_0050_CREATE_WITH_COMMIT` (fund create), `Y_BAPI_FUND_C5_ASSIGNMENT` (fund assign — C5 biennium),
  `FM_FUND_CHANGE_RFC`, `BAPI_PROJECT_MAINTAIN` (project), `Y_BAPI_WBS_TEXT_MAINTAIN` + `Y_BAPI_WBS_CUS_FIELD_UPDATE` (WBS).
So MuleSoft is **bidirectional**: reads SAP project financials OUT + writes project/WBS/fund master IN (PPM is the
master for projects/funds; SAP receives them + serves financials back). This is the **PPM↔SAP project+fund master sync**.
**GUID resolution:** SOAMANAGER `SRT_*`/logical-port tables are NOT in the Gold DB → naming the 174 GUIDs needs a
live SRT_* probe on P01 (deferred). ORION (BRIDGE-RFC) is inbound → not in RFCDES; outbound dests = `MULESOFT_PROD`
(HTTP/G) + `MULESOFT_P01_IDOC` (TCP/T).
**Ecosystem link CONFIRMED:** `unescore20-PPM-brain` already holds SAP artifacts (`artifacts/sap_source/
YCL_FM_STAFF_COST_DISTRIBUT_BL_source.json` + integration-layer docs) — the other side of the synctrigger sync
(Core Planner/Salesforce ↔ SAP project/fund/cost). The ADR-007 ecosystem edge is real and bidirectional here.

## Items 5-9 — write-channel SoD, channel-mix, PPM side, P2P-by-channel (2026-06-21)
- **#6 WRITE-CHANNEL SoD (the real conformance focus):** named-user portal writes carry SoD conflicts —
  **E_SILVA + L_NEVES do BOTH `BAPI_GOODSMVT_CREATE` (GR) AND `BAPI_INCOMINGINVOICE_CREATE1` (invoice)** =
  can self-approve the 3-way match. **MP_ANCUTA + S_STANTIC do `BAPI_PR_CHANGE` AND `ZBAPI_VENDOR_CHANGE`** =
  can direct spend to a vendor they control. `UBO-RFC` posts FI (`Y_RFC_FMRP_RFFMEP1FX_FI_POST` 30K). Extends
  the dialog SoD (claim #213) to the integration write channel — this is where conformance/SoD must focus.
- **#7 Permission-level SoD: ✅ DONE 2026-06-22 (PMO H71/H76).** AGR_USERS/AGR_1251/AGR_AGRS pulled from P01 →
  Gold DB `agr_users` + `agr_1251_sod`. **Declared SoD CONFIRMS behavioral** with precision: Conflict 1 (Brasília
  `Y_UBO_*` bundle) = GR+invoice+PO at change-level (vendor-bank role display-only); Conflict 2 (HQ `Y_ICTP_SIS`) =
  vendor+PR+PO change. **Root weakness exposed: `S_RFC=*` + custom `ZBAPI_VENDOR_CHANGE` skips `F_LFA1`** (S_STANTIC
  changed 6,972 vendors with no F_LFA1 grant). Full analysis + control design: `knowledge/domains/Security/h71_write_channel_sod_remediation.md`, claims #237–240. $ exposure: Conflict 1 R$ 264.7M; Conflict 2 ~EUR 11.8M.
- **#8 CHANNEL-MIX by month:** RFC business is **~5-6x dialog tcode-starts** every month (Mar 738K vs 156K,
  Apr 956K vs 202K, May 912K vs 172K) → the integration channel dominates operation, stable. (IDoc/Jobs sparse
  in the snapshots, not representative.) Dialog is a minority.
- **#9 PPM side (the other bridge end):** `unescore20-PPM-brain` = Salesforce/Core Planner; holds a SAP
  integration catalog **INT-01..06**, models MuleSoft, has SAP P01 as a graph node (31 edges) + SAP FM source
  (`YCL_FM_STAFF_COST_DISTRIBUT`). Our **17 MuleSoft flows = their INT-01..06 from the SAP side** — align them.
- **#5 Integration-first reframe:** the P2P conformance (EKKO/EKBE) is already CHANNEL-AGNOSTIC (EKBE records
  GR/IR regardless of dialog vs BAPI) → the 38%-clean / 70-IR-before-GR findings HOLD. The missing piece was
  channel attribution per step: Create PO→BRIDGE/dialog, **GR/Invoice→BAPI (E_SILVA/L_NEVES AP portal)**,
  PR→BAPI_PR_CHANGE (MP_ANCUTA/ORION). TODO: full OCEL with origin=resource per event.

## PROBLEMS analysis — the failure side mirrors the operating model (2026-06-21)
Analysis of `st22_dumps_history` (1) + `sm21_syslog_history` (2,402, ~7d):
- **Application-healthy:** only **1 ABAP dump in 7+ days**, and it is infrastructure not code — `DBIF_REPO_SQL_ERROR`
  (2026-06-21 02:53, SAP↔SQL Server `MDS_CTRL_STRATEGY`, "TCP connection forcibly closed by remote host", net 10054 =
  a DB maintenance/blip window). No recurring app crashes.
- **⚠️ CORRECTED 2026-06-22 (H74 deepening — `knowledge/h74_syslog_10054_connectivity_analysis.md`, claim #236):**
  the "272 `10054` = satellite connection drops" reading below was WRONG. Decoding CENTDATA + temporal correlation
  (`process_mining/parse_syslog.py`): **269/272 `10054` are end-user SAP GUI frontend resets** (`frontend_DIAG_reset`
  — WP=`DP` dispatcher = frontend, NOT the RFC gateway; companion `dpTermin` names only end-user workstations; 86%
  business-hours, weekday, weekend-collapse Sat=1/Sun=8 = a human diurnal curve). **Only 3/272 are the SAP↔SQL Server
  link**, all at **Sun 02:53 = one maintenance window** (= the lone dump). **ZERO gateway/RFC-server TCP resets** in
  the syslog ⇒ the MuleSoft/ORION RFC links are **not** TCP-dropping. The genuine integration tail is small (3 SQL
  resets + 3 `DBSQL` errors in batch `RFFMAVC_OVERALL_VIEW` + 3 ORION app errors + 13 RFC/CPIC); 28 HTTP "plugin auto
  logout" are **expected** idle timeouts. Keepalive tuning to the satellites is NOT indicated.
- **~~The #1 failure mode is NETWORK CONNECTIVITY~~ (SUPERSEDED by the above):** ~12% of syslog = `10054` (272) +
  `recv` errors (268) + HTTP timeouts (30). *Original (incorrect) reading: failures are in the CONNECTIONS to the
  satellites.* Corrected: the bulk is benign **frontend GUI session churn**, not satellite integration.
- **72% of syslog is operational noise** (E0A 1,181 = one user heavy on FMX3; R47 547 = session rollout resource
  cleanup), not errors. Note: the `10054`/`recv` "network" class is *also* mostly benign frontend churn — true error
  signal is the small integration tail above. Custom touch-points with minor issues: SAPMHTTP (HTTP), HRPADUNEDGR.
- **Monitoring conclusion (CORRECTED):** the satellites are NOT the problem — watch the **SAP↔SQL Server link**
  (make alerting maintenance-window-aware: suppress Sun 02:00–06:00) and the **`RFFMAVC_OVERALL_VIEW` batch SQL
  error**; reclassify frontend GUI resets as *churn, not failures*. SM21 retains only ~7 days → keep the accumulator
  (`process_mining/accumulate_problems.py`, weekly) running to build a >7-day baseline that separates episodic from
  chronic. Decode/classify with `process_mining/parse_syslog.py`.

## Implication for the model & next steps
- This is the **AS-RUN** the capability model wants (A_PROCESS) and the **F_INTERFACE** reality. Feed it there.
- The **moat**: custom satellite interfaces (`YHRTRV_IF_*`, `ZBAPI_VENDOR_*`, `Y_FMKU_*`, `Y_BAPI_YPS8`) — no
  commercial PM tool understands them; our brain (d01_tstc→program, the Z-code graph) does.
- Next: resolve MuleSoft `dest` GUIDs → individual flows (SOAMANAGER logical ports); connect to PPM brain
  (unescore20-PPM-brain = the Salesforce/Core-Planner other side); drive the remaining ~9% UNKNOWN down; then
  do conformance per satellite-process (a satellite call IS a process step — model it in the OCEL with origin=resource).
