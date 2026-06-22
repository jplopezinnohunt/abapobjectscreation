---
name: Gold DB × SAP Process Mining — what info each table holds and how it's used
description: Analysis (2026-06-21) mapping every Gold DB table category to its SAP process-mining role (5-class taxonomy + case/activity/timestamp/resource), which end-to-end process it serves, and coverage vs gaps. Leverages the verified sap_event_sources_catalog.md + process_mining_capability_inventory.md. Companion to gold_db_table_catalog.md.
type: project
---

# Gold DB × SAP Process Mining

> "Qué información tenemos de todas las tablas, y para qué se usan en process mining." Built on the
> deep-research-verified base: `sap_event_sources_catalog.md` (van der Aalst/RWTH sap-extractor, OCEL 2.0)
> + `process_mining_capability_inventory.md`. Not re-derived — synthesized from what we already evaluated.

## 1. The SAP process-mining model (best practice)
An event log must span **5 table classes**, and every event maps to **case / activity / timestamp / resource**:
| Class | Role | SAP examples |
|---|---|---|
| **Flow** | document chains (object lifecycle) | EKBE (P2P), VBFA (O2C), AWTYP+AWKEY (FI) |
| **Transaction** | the business records = the events | BKPF, RBKP, VBRK |
| **Change** | audit trail (field changes) | **CDHDR + CDPOS** |
| **Record** | document headers | EKKO, EBAN, VBAK |
| **Detail** | line items | EKPO, BSEG |
SAP relations are mostly one-to-many → **object-centric (OCEL 2.0)** is the correct model (not flattened).

## 2. What we have — Gold DB inventory by category (row counts 2026-06-21)
| Category | Tables | Rows | Process-mining role |
|---|---|---|---|
| **LOGS / audit / change** | 15 | **28.8M** | the EVENT raw material — see §3 |
| FI docs / GL | 8 | 8.4M | Transaction + Detail (postings) |
| Treasury / payment | 16 | 6.0M | Payment E2E events + bank recon |
| PSM / FM budget | 39 | 4.8M | B2R budget lifecycle |
| MM / P2P | 12 | 4.7M | Flow + Record + Detail (procurement) |
| CO / PS | 10 | 3.8M | cost/project postings |
| Master data | 15 | 2.3M | OCEL objects (Vendor/Customer/Bank/Address) |
| Config (T*) | 81 | 113K | activity decode + decision rules (TJ02T, T028*, TCURR) |
| Transport / integration | 5 | 142K | IDoc/RFC interface events (EDIDC) |
| D01-provenance | 24 | — | system-invariant maps (tcode→program) |
| Custom / analysis | 44 | — | our derived event logs / sims |

## 3. Tables → process-mining role + which process they serve
| SAP source (Gold DB) | PM class | case_id | activity | timestamp | resource | Process |
|---|---|---|---|---|---|---|
| **BKPF** (+bseg_union) | Transaction | BELNR | "Posted <BLART>" | BUDAT/CPUDT | USNAM | FI / all |
| **EKKO/EKPO/EBAN** | Record | EBELN/BANFN | "Created PO/PR" | AEDAT | ERNAM | **P2P** |
| **EKBE** | Flow | EBELN | GR/IR (BEWTP) | BUDAT | — | **P2P** |
| **ESSR/ESLL** | Flow/Detail | LBLNI | service entry | — | — | **P2P** services |
| **RBKP/RSEG** | Transaction/Detail | BELNR | invoice receipt | BUDAT | USNAM | **P2P** |
| **REGUH/REGUP** + FEBEP/FEBKO/FEBRE | Transaction/Flow | LAUFD/payment | pay run / clearing / bank stmt | — | — | **Payment E2E** |
| **FMIFIIT/FMIOI/FMBH/FMBL** | Transaction/Flow | FMBELNR | budget consume/commit/CF | PERIO | — | **B2R / budget** |
| **CDHDR** (12M, have) | **Change** (header) | OBJECTCLAS+OBJECTID | "Changed <obj>" / tcode | UDATE+UTIME | USERNAME | audit / all |
| CDPOS (NOT have) | **Change** (detail) | +CHANGENR | field old→new | (CDHDR) | — | audit (field-level) |
| **rsau_audit_history** (8.5M, NEW) | **Resource / org / control** | SLGUSER+session | logon / tcode-start / report-start / RFC / master-change | SAL_DATE+SAL_TIME | SLGUSER | **SoD / security / "way of working"** |
| **tbtco/tbtcp** (have) | batch | JOBNAME | program + VARIANT (intent) | SDLSTRTDT | AUTHCKNAM | batch automation |
| EDIDC (have) | interface | DOCNUM | IDoc status | CREDAT | — | integration |
| JEST/JCDS | status | OBJNR | status change (TJ02T) | (JCDS) | — | order/PS lifecycle |

## 4. What the LOG tables we just built UNLOCK
- **`rsau_audit_history` = the Resource/Organizational/SoD source.** In `process_mining_capability_inventory.md` §G (Organizational) this was **NONE**. We now have it: handover-of-work, resource/role profiling, and **systematic Segregation-of-Duties** (the BCM dual-control we found *by hand* becomes a query: same user create+approve). Plus security events (logon, master-data changes). The triage filter (keep Dialog Logon + Transaction Start + User Master Changes + High severity) is in `gold_db_table_catalog.md`.
- **`cdhdr_history` (12M) = the Change class.** Drives `cdhdr_activity_mapping.py` (OBJECTCLAS+TCODE→activity). The field-level Detail (CDPOS) stays the #1 deferred gap.
- **`tbtco/tbtcp` = batch process + JOB INTENT via VARIANT** (skill `sap_variant_analysis`).

## 5. Coverage vs gaps (against the 5-class best practice)
- **HAVE:** Transaction (BKPF/RBKP), Record (EKKO/EBAN), Flow (EKBE; partial), Change-header (CDHDR), **Resource (RSAU — new)**, batch (TBTCO/TBTCP), interface (EDIDC).
- **MISSING (priority, per catalog §L):** **CDPOS** (Change detail — deferred by decision), **JCDS** (status history — order/PS lifecycle), **VBFA/VBAK** (O2C flow — we have almost no Sales), **SWW*** (workflow/approval steps + agents), **NAST** (output/print), AFKO/RESB/QMEL (PP/QM).
- **Analysis layer (capability inventory):** we use ~5-10% — only DFG discovery; **conformance (as-implemented vs standard), object-centric (OCPN/OCEL 2.0), event-log quality filtering, predictive/ML, decision mining, and systematic SoD are all NONE.** That backlog is the real product, not more extraction.

## 6. End-to-end processes our data enables
- **P2P** — strong (EKKO/EKPO/EKBE/ESSR/RBKP + BKPF). Built: `p2p.ocel2.sqlite`, `p2p_process_mining`.
- **Payment E2E** — strong (REGUH/REGUP/FEBEP/FEBKO/FEBRE/BNK_BATCH). Built: `payment_process_mining`.
- **B2R / budget** — strong (FM tables). 
- **Audit / SoD / "forma de trabajar"** — **newly enabled** by `rsau_audit_history` + `cdhdr_history`.
- **O2C** — weak/missing (no VBAK/VBAP/VBFA/VBRK extracted) → biggest source gap if Sales matters.

## 7b. RSAU process-engineering analysis — FIRST CUT (2026-06-21, human activity Apr–Jun)
Categorization (§3) ≠ analysis. Mining the human signal (Dialog Logon + Transaction Start, technical users excluded):
- **What humans actually do** (after stripping nav SESSION_MANAGER/S000): the work is **Finance/FM/Treasury/P2P** —
  MIRO/MIR4 (invoice verification), FMRP_*/FMX3 (budget reporting), FEB_BSPROC + F.13 (bank stmt + clearing),
  FBL1N/ME23N (vendor items / PO display), custom cockpits ZICTP_COCKPIT/YFM1. `SE16` by 13 users = direct
  table access (a control flag).
- **When** (by hour, UTC): office double-peak **10–11h & 14–16h with a 12–13h lunch dip**, plus a **persistent
  4–9K/hour overnight floor → globally distributed workforce** (field offices across timezones), not just HQ.
- **User fingerprints**: generalists (T_NDUNGU 22 tcodes, G_PEROTIN 21) vs specialists (O_KIRARA 5 — the vendor-
  address XK02 editor seen in CDHDR). Each user's tcode mix = their de-facto role.
- **NEXT analysis layers (not yet done)**: (a) **tcode SEQUENCES per session** = the actual process flows
  (pm4py DFG on user-sessions, case_id = SLGUSER+logon-window); (b) **systematic SoD** = users doing both
  entry (MIRO/FB60) and settle/clear (F.13/FBRA/F110) — the BCM dual-control finding generalized; (c)
  **handover-of-work** between users on the same object (join to CDHDR by OBJECTID); (d) off-hours actor
  drill-down (who/where the overnight floor is).

## 7c. Master data & financials run via RFC/BAPI, NOT dialog (2026-06-21, user-confirmed + audit-located)
Why dialog MDM ≈ 0 (FS00 by 1 user): GL accounts and **vendor master are maintained by EXTERNAL solutions via
RFC/BAPI**, invisible to tcode analysis but captured in the RSAU "RFC Function Call" stream (PARAM3 = FM name,
SLGUSER = RFC user). Located in `rsau_audit_history`:
- **Vendor master CHANGE = `ZBAPI_VENDOR_CHANGE`** (MP_ANCUTA 19,481 + S_STANTIC 4,683) — not XK02. Read/search via
  **BRIDGE-RFC** (`ZBAPI_VENDOR_GETDETAIL` 72K, `ZBAPI_VENDOR_SEARCH*`); bank via `ZBAPI_GET_BANK_COUNTRY_DATA`.
- **FM/Fund master = MuleSoft** (`Y_FMKU_0050_CREATE_WITH_COMMIT`, `FM_FUND_CHANGE_RFC`).
- Integration backbone (top RFC): `Y_BAPI_WBS_FINANCIAL_DATA_1` 974K (#1, WBS financials), `Z_RFC_GET_USER` 508K,
  `Y_BAPI_YPS8` 461K, `Y_BAPI_CUSTOMER_GET_ID` 148K, `BAPI_INCOMINGINVOICE_CREATE1`/`BAPI_GOODSMVT_CREATE` (E_SILVA/L_NEVES).
- **GL-account-master BAPI not yet surfaced** (low volume or differently named) — OPEN: grep RFC stream for GL/SKA1.
- Implication: the master-data + WBS-financial "way of working" is a BAPI/integration process. Model it from the
  RFC stream (resource = SLGUSER incl. BRIDGE-RFC/MULESOFT; activity = FM name). Custom Z-BAPI names = the brain/LLM moat.

## 7. Next steps (incremental)
1. Finish the RSAU **quarter** (4-month) pull → find the real audit retention boundary.
2. Apply the RSAU **type filter** as the retention policy (keep signal, drop machine noise).
3. From the capability backlog: wire **conformance** + **OCEL 2.0 / pm4py-full** (the as-implemented-vs-standard overlay) — highest-value analysis we don't yet do.
4. Extend this catalog/analysis to the remaining ~280 tables incrementally.
