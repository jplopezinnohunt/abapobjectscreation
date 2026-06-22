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

## Implication for the model & next steps
- This is the **AS-RUN** the capability model wants (A_PROCESS) and the **F_INTERFACE** reality. Feed it there.
- The **moat**: custom satellite interfaces (`YHRTRV_IF_*`, `ZBAPI_VENDOR_*`, `Y_FMKU_*`, `Y_BAPI_YPS8`) — no
  commercial PM tool understands them; our brain (d01_tstc→program, the Z-code graph) does.
- Next: resolve MuleSoft `dest` GUIDs → individual flows (SOAMANAGER logical ports); connect to PPM brain
  (unescore20-PPM-brain = the Salesforce/Core-Planner other side); drive the remaining ~9% UNKNOWN down; then
  do conformance per satellite-process (a satellite call IS a process step — model it in the OCEL with origin=resource).
