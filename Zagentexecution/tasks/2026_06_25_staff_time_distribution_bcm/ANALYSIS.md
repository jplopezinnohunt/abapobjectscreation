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

## 4. Open / to verify (known_unknowns)
- **Upstream source = Salesforce?** The 43 C/5 / output catalog is likely owned by the **Core Planner (PPM, Salesforce-based — ecosystem project `unescore20-PPM-brain`)**. Whether the template originates there (vs. a manual Excel) is **unconfirmed** — verify and, if so, this is a sync-gap to close at the source, not row-by-row in SAP.
- **Exact storage of the % distribution:** confirm whether the percentage rides on an HRP1001 relationship subtype or a UNESCO custom PD infotype (no HRP9xxx seen in N_MENARD change docs).
- **The Excel "issues" file** (row-level rejects) is not in this .eml — needed for a line-by-line template↔SAP diff.

## Evidence sources
- Gold DB `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`: `ytfm_output(_t)`, `d01_tstc`, `cdhdr/cdhdr_history`, `rsau_audit_history`.
- N_MENARD object inventory: `Zagentexecution/tasks/2026_06_10_nmenard_inventory/nmenard_inventory.json`.
- `knowledge/domains/Integration/integration_map_complete.md` (Data Hub extracts).
- Email + `attachments/image001.png`.
