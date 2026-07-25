# HANDOFF → unesco-sap-brain : the AS-RUN operating model (re-evaluate your redesign analysis)

**From:** abapobjectscreation (SAP source of truth) · **To:** unesco-sap-brain · **Date:** 2026-06-21 · Rule ADR-007 / BROADCAST-005.
**Why you must re-evaluate:** your SAP-redesign analysis is built on an AS-IS picture of how the system is operated.
We just measured the AS-RUN from the **P01 Security Audit Log (RSAU, 15.6M rows, 4 months, host/dest/user)** and it
**changes the baseline**: UNESCO does **not operate SAP by dialog — it orchestrates it from OUTSIDE.** Re-score any
hypothesis/conclusion that assumed dialog-driven usage, SAP as the system-of-engagement, or master data maintained in-GUI.

## The discovered operating model (evidence: `knowledge/system_operating_model_rfc.md`)
- **80.6% of business RFC is driven by EXTERNAL satellites** — stable every month (Feb 86 / Mar 80 / Apr 80 / May 82 / Jun 77%).
  SAP is a **READ-DOMINANT SYSTEM-OF-RECORD**: ~80% of external traffic reads data OUT; writes flow back concentrated.
- **The satellites (named, by host):**
  - **MuleSoft** = a "synctrigger" worker fleet (174 endpoints = **17 distinct flows**), **bidirectional PPM↔SAP project+fund
    master sync** — reads WBS financials/project/customer OUT (`Y_BAPI_WBS_FINANCIAL_DATA_1`, `Y_BAPI_YPS8`), writes
    project/WBS/fund master IN (`BAPI_PROJECT_MAINTAIN`, `Y_BAPI_FUND_C5_ASSIGNMENT`, `Y_FMKU_0050_CREATE`). RFCDES
    `MULESOFT_PROD`/`MULESOFT_P01_IDOC`. **The other side is YOU/PPM** (`unescore20-PPM-brain` holds the SAP FM source).
  - **BRIDGE-RFC = ORION EAI** (host `HQ-ORION-EAI03`) = procurement+travel+master-read portal, **92% READ**.
  - **named-user portal** = THE WRITE channel (PR/vendor/FI postings under the user's ID).
  - **WF-BATCH** = HR-lifecycle workflow; **PBC engine** = payroll commitments (FMRESERV 6.4M).
- **Per-process channel map:** Procurement/Travel=BRIDGE-RFC(ORION); FM/Fund/Project master=MuleSoft; HR=WF-BATCH;
  GR/Invoice=named-user portal; Vendor master=dialog XK02(M_AYIMBA)+BAPI; GL master=dialog FS00(stable). Dialog = minority.
- **Custom satellite interfaces** (`YHRTRV_IF_*`, `ZBAPI_VENDOR_*`, `Y_FMKU_*`, `Y_BAPI_YPS8`) — the integration surface a
  redesign must preserve/replace; no commercial tool knows them.

## What to re-evaluate (concrete)
1. Any AS-IS that treats SAP as operated in-GUI → it is **integration-orchestrated (80% external)**.
2. The **S/4 / redesign blast radius** is the **satellite contract** (MuleSoft 17 flows + ORION EAI), not the dialog tcodes.
3. **Project & fund master ownership = PPM/Core Planner** (pushed into SAP via MuleSoft); SAP serves financials back.
4. Conformance/SoD risk lives in the **write channel** (portal-as-user + MuleSoft fund writes), not the (minority) dialog.

## How to consume
Read-only via your `refs_external.json` → `knowledge/system_operating_model_rfc.md` (full) +
`knowledge/process_mining_table_analysis.md` §7a–§7f + the engines in `process_mining/`. Golden DB has
`rsau_audit_history` (15.6M) if you want to recompute. Recompute your verdicts; don't trust a dialog-AS-IS.
