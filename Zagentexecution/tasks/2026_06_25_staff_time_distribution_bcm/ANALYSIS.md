---
name: Staff Worktime Distribution by Output — BCM / Personnel Cost by Output
description: Email-thread analysis (RE_ Template of update staff work time distribution). Upload process, program/transaction identification, SAP-vs-template inconsistencies, data-flow claim.
type: project
created: 2026-06-25
source_email: "C:/Users/jp_lopez/Downloads/RE_ Template of update staff work time distribution .eml"
---

# Staff Worktime Distribution by Output (BCM — "personnel cost by output")

## 0. Email thread (who/when)
Thread `RE: Template of update staff work time distribution`, 2025-12-19 → 2026-06-24.
Participants: **N. Menard** (DBS/SDI/TPI — system dev analyst, SAP side), **L. Chabeau** + **Y. Guo** + **L. Caballé** (budget office — prepare the Expenditure Plan), JT Bruce, JP Lopez (cc), I. Konakov, S. Dartigolle, D. Michenet.
Business object: worktime distribution **by output, per position (post)** for the **43 C/5 Expenditure Plan** (biennium 2026-2027), needed to update **financial reporting by output**.

Attachments in THIS (final) reply .eml: only inline `image001.png` (the duplicate-output screenshot). The Excel template + the "issues" Excel referenced in earlier messages were **dropped from the reply chain** — not present in this file.

## 1. The upload process + program/transaction (Point 1)
- **Maintenance / upload tool:** tcode **`YFMOUTPUT`** → program **`YFM_OUTPUT_MANAGEMENT`** ("FM Output Management"), BL classes `YCL_FM_OUTPUT_MANAGEMENT` / `YCL_FM_OUTPUT_BL`. Companions: `YFM_OUTPUT_UPDATE` ("FM: Update Output data"), `Y_FM_OUTPUT_MAINTAIN` ("FM: Maintain outputs").
- **Upload validation:** `YFM_OUTPUT_CHECK_POSITION` ("Check position") — generates the reject list Menard reported (output not in referential, post acronym not identifiable, distribution ≠ 100%).
- **Where it is stored:** Organizational Management on positions — **HRP1000** (object) + **HRP1001** (relationships), with **biennium start/end dates ⇒ retroactive** (Menard: "even if done later"). Evidence: N_MENARD's **2025-01-28 SE38** change docs created `HR_IT1000/1001/1005/1013/1050` (prior-biennium load).
- **Production-write evidence near the emails:** RSAU/SM20 audit (covers 2026-02-21→06-21) shows N_MENARD on **2026-06-18 = only 24 events, NO report/transaction-start, NO change documents** ⇒ the "upload test in the production system" ran in **validation/test mode** (produced rejects, did not commit). The real load is scheduled for after the file is clean (post-2026-06-24, outside the data window). His heavy P01 work was Jun 9–16 (HRP1000 ×19, PPOSE, PA20 — OM/position maintenance) iterating on this.

## 2. Consuming reports / where the data is used (Point 3 — the "claim")
Transaction → program (verified in P01 `d01_tstc`):

| Transaction | Program | Purpose |
|---|---|---|
| `YFM_STAFF_COST_2` | `YFM_STAFF_COST_DISTRIBUT` | Staff cost distribution per sector & output |
| `YFM_STAFF_COST`   | `YFM_STAFF_COST_PER_OUTPUT` | Staff costs distribution per output |
| `YFM_POS_OUTPUT`   | `YFM_OUTPUT_REPORT_1` | List of outputs per position |
| `YHR_POS2`         | `YHR_POSITION_WITH_NODE_1` | Positions in the C/5 structure |
| `YHR_POS1`         | `YHR_ORG_UNIT_COUNT` | Org-unit headcount (established/vacant) |

Outbound to **Data Hub / BW** (file integrations, P01):
- `YFM_STAFF_COST_DISTRIBUT_DH` (4 CC variants: UBO, UNES_MCA, UNES_RGF, UNES_RP) → table `YTDH_STFCO`/`YTDH_STFCO_2`
- `YFM_OUTPUT_INDIRECT_COSTS_DH` (11 CC variants) → `YTDH_INDCO`
⇒ feeds **financial reporting by output** downstream. Brain claim **#263** (TIER_1).

## 3. SAP-vs-template inconsistencies (Point 2) — brain claim #264 (TIER_1)
Referential table = **`YTFM_OUTPUT`** (+ `_T` text). Cols: `FM_OUTPUT, ZZSECT, ORANK, OTYPE` / `SPRSL, FM_OUTPUT, ONAME, OTEXT` (+ `ODESC` long text seen in screenshot, client 350/V01). 193 OUTPUT + 66 OFFICE4 = 259 rows in P01 gold.

**SAP-internal defects (verified in gold):**
- **Duplicate:** `FM_OUTPUT 3075` & `3083`, both `ONAME=8.13.PPF` (only real dup besides 31 blank-ONAME rows). 3075 retained (used in tables), **3083 to be deleted** ensuring no budgets are linked.
- 31 rows with blank `ONAME`.

**Template-vs-SAP mismatch (from the upload test):**
- File `8.10.CPE` / `8.11.FLD` / `8.12.PFF` → **do not exist** in SAP. SAP has `8.10.BSP`, `8.11.CPE`, `8.12.FLD`, `8.13.PPF`. ⇒ a **number↔acronym shift** + a **PFF↔PPF transposition**.
- 64 posts with no acronym (temporary assistance not created in SAP).
- Post `SHS 143` closed (SC/SHS sector merge); post `SHS 041` invalid (handled manually).
- 4 posts with output distribution ≠ 100% (shared posts across sectors).

**Root cause:** the upstream output catalog (Expenditure Plan / 43 C/5, maintained by the budget office) and SAP `YTFM_OUTPUT` are maintained **separately and not synchronized**. Chabeau: *"I do not know how the outputs were created in SAP."*

### 3a. REFINED (Nicolas follow-up after 2026-06-24) — validation fails on TWO dimensions
The test-mode upload reconciliation (*"After checks between SAP upload log (in test mode) and the Excel file, I found a bug"*) confirms the upload runs in **test/simulation mode producing a log** (⇒ no commit, explains zero CDHDR on Jun-18) and that the load is a **manual iterative reconcile loop** (test upload → reject list emailed → budget office fixes Excel → repeat → operator decides load-as-is vs fix).

Two INDEPENDENT referential failures:
- **DIM-A — OUTPUT referential (`YTFM_OUTPUT`):** outputs in file not in SAP (8.10.CPE/8.11.FLD/8.12.PFF) + duplicate 8.13.PPF (above).
- **DIM-B — POST/POSITION master (OM / HRP1000):** 13 posts *"not available for the biennium"*: SHS 041, SC 122, PAX 311, PAX 009, OPS 944, BSP 129, `4KZCI 1000RP`, SC 337, SC 169, SC 142, SC 399, SC 351, SHS 001. By sector: **SC=6, SHS=2**, PAX=2, OPS=1, BSP=1, 4KZCI=1 ⇒ **8/13 (62%) are SC/SHS** = the **SC↔SHS sector-merge fallout** Lionel flagged (*"merge of the SC and SHS sectors… update manually in OM few other posts"*). *"Not available for the biennium"* = the OM position validity (HRP1000 BEGDA/ENDDA) doesn't cover the 43 C/5 biennium (closed/delimited/merged). Handled by reject + manual OM correction (same as SHS 041 *"deal with it manually"*).

**Validation note:** post-by-post verification needs live HRP1000 (OM not in Gold DB) → **blocked on SSO** (same blocker as the cadence question). The SC/SHS-merge explanation is strong from the thread itself.

**Improvement opportunity (H_IMPROVE):** the whole biennium load is a manual back-and-forth driven by drift between the planning master (posts+outputs) and SAP OM/`YTFM_OUTPUT` after org restructuring. Candidate: a pre-validation that diffs the Excel against live OM validity + `YTFM_OUTPUT` BEFORE the email loop, and a source-side sync so closed/merged posts and renumbered outputs don't reach the file.

## 3b. Execution frequency (measured in P01 — TBTCO/TBTCP/EVENTID/RSAU, window 2026-03-04..06-20)
The process runs at DIFFERENT cadences per layer — they are not the same:

| Layer | Object | Frequency | Evidence |
|---|---|---|---|
| Master distribution load (the email) | YFMOUTPUT→YFM_OUTPUT_MANAGEMENT → HRP1000/1001 | **Once per biennium** (every 2y) at biennium start + ad-hoc manual corrections | biennium start/end dating; 43 C/5 = 2026-2027; thread = the load exercise |
| Staff + indirect cost per output → Data Hub | YFM_STAFF_COST_DATA_HUB_* (5) + YFM_IND_COST_DATA_HUB_* (11 entities) | **Event-triggered on FI period-close `Y_FI_CLOSE_PERIOD`** — fired once (Mar 5-12 2026 cluster, staggered per entity) in a 3.5-month window ⇒ per reporting close (≈quarterly/ad-hoc, NOT monthly) | tbtco_history EVENTID=Y_FI_CLOSE_PERIOD; 4 firings all Mar 5-12; none Apr-Jun |
| Position/headcount → Data Hub | YFM_ESTABLISH_POST / YFM_VACANT_POST_FOR_DATA_HUB | **Weekly** (Fri/Sat: 7,14 Mar … 6,13,20 Jun) | tbtco 7-day cadence |
| HR staging (SuccessFactors/PA/OM) | STAFFING* (PA0001, OMPOSITIONSALL…) | **Daily** | 43-86 runs, daily dates |
| Consuming dialog reports | YFM_STAFF_COST_2 / YFM_POS_OUTPUT / YHR_POS2 | **On-demand** (~9/5/3 runs in 4mo, 1-2 analysts, concentrated Apr-May) | RSAU report/tx starts |

**Business read:** the email process (master distribution load) is once-per-biennium; the cost-per-output figures only refresh to the Data Hub **when Finance runs the reporting period-close** — hence the urgency: if the distribution isn't loaded *before* the close, that close yields no by-output data for the biennium.

### Cadence precision — quarterly vs monthly (BLOCKED on live, 2026-06-25)
Corrected interpretation: local TBTCO history is **two discontinuous snapshots** (2026-03-04..18 and 2026-06-06..20; no Apr/May) — so April/May "absence" is a CAPTURE GAP, not a real gap. What IS a real within-window signal: the cost-per-output extract (`YFM_*_DATA_HUB_*`, event `Y_FI_CLOSE_PERIOD`) ran in the **March window (5-12 Mar, staggered per entity)** and did **NOT** run in the **June 6-20 window**. Note `YFI_POST_CLOSING_STATEMENT_*` runs **daily** (PRD=1d) in both windows — that's the daily statement posting, NOT the event.
- Consistent with **quarterly / reporting-milestone** (Q1 close early Mar; Q2 close ~early Jul, outside the Jun-20 window). Monthly is **not excluded** (a monthly close could fall outside 6-20 Jun).
- **Definitive answer needs the job's SCHEDULING DEFINITION** (PERIODIC flag + event binding), not run-history. Attempted live P01 read (`read_job_cadence_p01.py`, RFC_READ_TABLE on TBTCO incl. PERIODIC/PRDMONTHS/EVENTID) → **BLOCKED: SNC GSS-API "No credentials were supplied"** (SSO/Kerberos not authenticated in this context). Not a code problem; re-run once SAP GUI/VPN SSO is active.
- **Unblock paths:** (1) authenticate SSO → I re-run `read_job_cadence_p01.py` (answer in seconds); (2) user opens **SM37** in P01, job `YFM_STAFF_COST_DATA_HUB_UNES` (or any `YFM_*_DATA_HUB_*`) → Job → "Start condition" → reads *"After event Y_FI_CLOSE_PERIOD"* + Periodic Y/N + period unit. Parked as execution-backlog item.

## 4. Open / to verify (known_unknowns)
- **Upstream source = Salesforce?** The 43 C/5 / output catalog is likely owned by the **Core Planner (PPM, Salesforce-based — ecosystem project `unescore20-PPM-brain`)**. Whether the template originates there (vs. a manual Excel) is **unconfirmed** — verify and, if so, this is a sync-gap to close at the source, not row-by-row in SAP.
- **Exact storage of the % distribution:** confirm whether the percentage rides on an HRP1001 relationship subtype or a UNESCO custom PD infotype (no HRP9xxx seen in N_MENARD change docs).
- **The Excel "issues" file** (row-level rejects) is not in this .eml — needed for a line-by-line template↔SAP diff.

## 5. Dependency closed 2026-07-03 — PA0105-0001 (SAP-user link) gap in D01/V01

The `YFMOUTPUT` SaveFormData lookup depends on **PA0105 subtype 0001** (PERNR → SAP-user
`SY-UNAME`/BNAME, field **USRID**, not `USRID_LONG` which belongs to subtype 0010 = work email). If this
infotype link is missing for an employee in D01/V01, the upload's user-resolution step never fills that
slot — a distinct, prior blocker from the output-catalog/OM issues in sections 1-3 above.

**Measured (RFC, 2026-07-03):** P01 has 5,292 employees with the link (source of truth). Gap = D01 857,
V01 775 — in every case the SAP user already existed in the target `USR02`, only the infotype link was
missing. **Synced** via standard BAPI path (`BAPI_EMPLOYEE_ENQUEUE` → `BAPI_EMPLCOMM_CREATE` SUBTYPE=0001
→ `BAPI_TRANSACTION_COMMIT` → `BAPI_EMPLOYEE_DEQUEUE`, never direct infotype-table insert): D01 +855
(2,314→3,173), V01 +773 (4,267→5,040). Golden-12 12/12 D01, 11/12 V01. 4 real edge cases could not be
copied (SAP user already linked to a different PERNR in target — needs a human which-PERNR decision, not
a copy): D01 10005045, D01 10100301, V01 10152769 (`X_LI`), V01 10158641 (`Z_LIU`).

Reusable script: `Zagentexecution/tasks/2026_07_03_pa0105_user_sync/pa0105_user_sync.py`. Full detail:
`Zagentexecution/tasks/2026_07_03_pa0105_user_sync/README.md`. Brain claims **#333-#337** (TIER_1).

## Evidence sources
- Gold DB `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`: `ytfm_output(_t)`, `d01_tstc`, `cdhdr/cdhdr_history`, `rsau_audit_history`.
- N_MENARD object inventory: `Zagentexecution/tasks/2026_06_10_nmenard_inventory/nmenard_inventory.json`.
- `knowledge/domains/Integration/integration_map_complete.md` (Data Hub extracts).
- Email + `attachments/image001.png`.
