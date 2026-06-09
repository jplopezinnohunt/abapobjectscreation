---
name: SAP Event-Source Catalog for Process Mining (deep-research verified)
description: The canonical set of SAP ECC tables/logs used as EVENT SOURCES for process mining, with per-source event-log mapping (case/activity/timestamp/resource) and extraction priority. Verified s079 via deep research (van der Aalst/RWTH sap-extractor, OCEL 2.0, Processmind, SAP KBA). Drives the L7 Process Intelligence engine.
type: project
---

# SAP Event-Source Catalog (process mining)

Deep-research verified (24/25 claims confirmed). Primary sources: van der Aalst/RWTH "sap-extractor"
(arXiv:2110.03467, Springer JIIS 2023), OCEL 2.0 (arXiv:2403.01975), Processmind AP template, SAP KBA 3527846.

## The 5-class table taxonomy (an event log MUST span all of these, not just FI docs)
| Class | Role | Examples | Event-log mapping |
|-------|------|----------|-------------------|
| **Flow** | document chains (object lifecycle) | VBFA (O2C), EKBE (P2P), AWTYP+AWKEY (FI) | activity = current doc type (VBTYP_N); links prev->current doc |
| **Transaction** | business records (the events) | BKPF, RBKP, VBRK | activity = "Executed <tcode>"; ts = posting/entry |
| **Change** | audit trail (field changes) | CDHDR + **CDPOS** | activity = "Changed <field>" / old-vs-new; ts = CDHDR.UDATE+UTIME; CHNGIND I/U/D |
| **Record** | document headers | EKKO, EBAN, VBAK | activity = "Created <obj>" |
| **Detail** | line items | EKPO, BSEG | object linkage / object-centric (OCEL) |
OCEL 2.0: each event has exactly one type (activity) + one timestamp, linked to objects via qualified
Event-to-Object relations; a qualifier distinguishes the **actor** (resource/user). SAP relationships are
mostly one-to-many -> object-centric (OCEL) is the right model.

## Per-source mapping + extraction priority (MISSING from our Gold DB)
| Prio | Source | case_id | activity | timestamp | resource | unlocks |
|------|--------|---------|----------|-----------|----------|---------|
| **1 CRITICAL** | **CDPOS** (+ CDHDR have) | OBJECTID | field change (FNAME / old->new) | CDHDR.UDATE+UTIME | CDHDR.USERNAME | control-deviation, field-level activities (payment block, price, release) |
| **2 HIGH** | **JCDS** (+ JEST have) | OBJNR | status (STAT decoded via TJ02T) | JCDS.UDATE+UTIME | JCDS.USERID | status lifecycle (created->released->completed->closed) for orders/PS/PM/QM — NOT in CDHDR/CDPOS |
| **3 HIGH** | **VBFA** | VBELN | current doc type VBTYP_N | (from VBAK/LIKP/VBRK) | — | O2C document flow / lifecycle |
| **4 MED-HIGH** | **SWWWIHEAD + SWWLOGHIST** | COALESCE(TOP_WI_ID, WI_ID) | work-item / step | WI date/time | agent | approval flows, agents, SoD/control |
| 5 LOWER | NAST | doc | message output | — | — | output/print/send events |
| 5 LOWER | BALHDR/BALDAT (SLG1) | OBJECT+SUBOBJECT | log message | timestamp | user | application-log events |
| 5 LOWER | APQI/APQD | session | BDC step | date/time | user | batch-input/BDC forensics (custom Allos/Y1) |
| 5 LOWER | STAD/SWNCMONI | user/session | tcode executed | time | user | ALL tcode usage (short-retention -> accumulator) |
| 5 LOWER | SNAP/SNAPT | dump | ABAP error | time | user | runtime-error events |

Already HAVE as sources: bkpf/bseg_union (transaction), cdhdr-headers (change — needs CDPOS), jest
(status current — needs JCDS for history), edidc (IDoc), tbtco/tbtcp (jobs).

## 🔴 CRITICAL extraction caveat — CDPOS is a CLUSTER table
CDPOS sits behind cluster **CDCLS** in classic ECC. **RFC_READ_TABLE / raw SQL CANNOT read or join it**
the normal way. Canonical extraction: read CDHDR first, then CDPOS `FOR ALL ENTRIES` in ABAP, joined on
OBJECTCLAS+OBJECTID+CHANGENR (3 fields, not just CHANGENR). On EhP8 the cluster is SOMETIMES declustered
(transparent) — **must verify empirically on the UNESCO kernel** (probe RFC_READ_TABLE CDPOS for one
OBJECTID; if it errors/empty, fall back to an ABAP read via CHANGEDOCUMENT_READ_POSITIONS or a custom
SELECT FOR ALL ENTRIES through RFC_ABAP_INSTALL_AND_RUN). This affects `extract_cdpos_by_object.py`.
Note the compliance posture: pure RFC_READ_TABLE is Note-3255746-safe; an ABAP read program is a
different (still read-only) path — confirm before running.

## Activity-mapping strategies (change tables)
1. **tcode -> activity** (TCODE of the change).
2. **field -> activity** (FNAME, e.g. "Price Changed").
3. **old-vs-new value -> activity** (compare VALUE_OLD/VALUE_NEW, e.g. "Postpone Delivery",
   "Payment Block Set/Removed" for BSEG-ZLSPR). CHNGIND='I' = creation event.

## 🟦 ADDITION (s079, user) — JOB INTENT via VARIANT (not just program choreography)
Mining `tbtco/tbtcp` today gives only "which program ran when". That is HALF the signal. **`TBTCP` already
carries the `VARIANT` column per step** — and the variant encodes WHAT the run actually targets (company
code, account range, date/period, test-vs-update, reversal flag). The job's INTENT lives in the variant,
not in the program name. Chain:
  **job (TBTCO) → step program + VARIANT (TBTCP) → variant contents → targeted scope/objects → intent.**
- Variant contents: pool tables **VARI / VARIS** (RFC reads the KEY field only — pool-table limitation
  proven s078; full selection values via FM `RS_VARIANT_CONTENTS` / `RS_VARIANT_VALUES` through
  RFC_ABAP_INSTALL_AND_RUN). We already built this: skill **`sap_variant_analysis`** (proven on SAPF100 —
  21 variants, error-generators, reversal variants, account-block cross-ref).
- Event-log effect: a `jobs_batch` event becomes "Program X with intent {BUKRS=…, HKONT-range=…,
  BUDAT=…, test/update}" — i.e. the job step is no longer an opaque program, it is a **parameterized
  business action**. This also links jobs→config (the variant references CCs/accounts that are OCEL objects).
- TODO: enrich `sap_process_discovery.py jobs_batch` to join TBTCP.VARIANT and resolve variant contents;
  add VARI/VARIS to the Gold DB; emit variant params as event attributes.

## 🟦 ADDITION (s079, user) — FILE SYSTEM as an event/object source (currently UNMODELED — real gap)
Where SAP **reads or writes files** is a whole integration surface we have NOT evaluated anywhere. Files
are an OCEL **object type** ("File"); activities = `File written` / `File read` / `File archived`;
resource = the job/program. Sources:
| Artifact | What it gives | Note |
|----------|---------------|------|
| **AL11** directories (DIR_* on app server) | physical paths SAP reads/writes | runtime listing; `EPS*` FMs / `RZL_READ_DIR_LOCAL` |
| **Logical file paths** — tables `PATH`, `FILEPATH`, `FILENAMECI`, `FILENAME`, `OPSYSTEM` (tcode **FILE**/SF01) | logical→physical filename mapping = the config of WHERE each interface lands | static config, extractable |
| **`OPEN DATASET … FOR INPUT/OUTPUT`** in ABAP | the exact programs that read/write files = code-level file I/O | discoverable via static code mining (#3) / cross-reference |
| IDoc **file ports** (`EDIPOF`/`EDIPO`, EDIDC port) | which IDoc channels are file-based vs RFC | links to interface intelligence |
| File-based interfaces (COUPA in/out, bank statement **MT940** import, **DMEE** payment file output, payroll/BDC input files) | the actual business files crossing the boundary | the variant of the file-processing job carries the path |
- Why it matters: the file is the JOIN between an external system and the SAP process. A payment run writes
  a DMEE file → bank; a bank statement file → EBS posting. Without the file object, that handover is invisible
  — the process map "ends" at SAP and silently "restarts" later, looking like two processes instead of one.
- Connects three layers: **job variant** (which file path) ↔ **code** (`OPEN DATASET`) ↔ **interface**
  (file port / external system). This is exactly the custom-over-standard x-ray at the file boundary.
- TODO: extract logical-file-path config (PATH/FILENAMECI/FILENAME) to Gold DB; add a file-I/O scan to the
  code-mining pass (#3, `OPEN DATASET` cross-reference); model File as an OCEL object type.

## Open questions (second research pass / kernel probe needed)
- Vendor connector confirmation (Celonis EMS / Signavio Process Insights) for NAST/BAL*/APQ*/STAD/SNAP
  centrality — currently expert-inferred, not source-verified.
- CDPOS cluster vs transparent on UNESCO EhP8 — empirical probe when P01 is active.
- SWW* combination (SWWWIHEAD + SWWLOGHIST + SWEL) for full agent/step/timestamp reconstruction.
