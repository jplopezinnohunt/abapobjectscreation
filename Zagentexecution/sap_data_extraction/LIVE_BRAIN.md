# UNESCO P01 — LIVE EXTRACTION BRAIN
> **Authoritative inventory** of everything extracted from SAP P01.
> Updated: 2026-03-15.  Read this FIRST before any extraction or analysis work.

---

## 1. WHAT WE HAVE — Complete Inventory

### A. SQLite Databases

| DB File | Size | Purpose |
|---------|------|---------|
| `sap_data_extraction/sqlite/p01_gold_master_data.db` | **503 MB** | **PRIMARY** — PSM master data + FM/FI integration |
| `sap_data_extraction/sqlite/p01_master_data_v2.db` | 5.7 MB | Older draft — superseded by gold |
| `mcp-backend-server-python/tadir_cache.sqlite` | 0.37 MB | CTS dashboard TADIR cache |

### B. p01_gold_master_data.db — Table Inventory

| SQLite Table | SAP Source | Rows | Status | Domain |
|---|---|---:|---|---|
| **`fmifiit_full`** | **FMIFIIT** | **2,070,523** | **✅ COMPLETE** | **FM/FI Integration** |
| `funds` | FMFCT | **64,799** | ✅ populated | FM |
| `prps` | PRPS | **58,516** | ✅ populated | PS/WBS |
| `cts_objects` | E071 | **108,290** | ✅ populated | CTS |
| `fmavct_summary` | FMAVCT | **19,111** | ✅ populated | FM Availability |
| `fmbdt_summary` | FMBDT | **19,008** | ✅ populated | FM Budget |
| `movements_summary` | FMIFIIT | **18,975** | ✅ populated | FM (aggregated) |
| `proj` | PROJ | **13,878** | ✅ populated | PS |
| `cts_transports` | E070 | **7,745** | ✅ populated | CTS |
| `ytfm_fund_cpl` | YTFM_FUND_CPL | **6,368** | ✅ populated | UNESCO Custom |
| `tadir_enrichment` | TADIR | **4,168** | ✅ populated (54% with devclass) | Cross |
| `fund_centers` | FMFCTR | **764** | ✅ populated | FM |
| `volume_anchors` | RFC counts | **66** | ✅ populated | Reference |
| `ytfm_wrttp_gr` | YTFM_WRTTP_GR | **66** | ✅ populated | UNESCO Custom |
| `cooi` | COOI | 0 | ❌ EMPTY | CO |
| `coep` | COEP | 0 | ❌ EMPTY | CO |
| `rpsco` | RPSCO | 0 | ❌ EMPTY | PS |
| `jest` | JEST | 0 | ❌ EMPTY | Status |
| `fmifiit_raw_data` | FMIFIIT | 0 | 🗑️ RETIRED (replaced by fmifiit_full) | FM |
| `projects` | PROJ | 0 | 🗑️ OLD v1 (use `proj`) | PS |
| `wbs_elements` | PRPS | 0 | 🗑️ OLD v1 (use `prps`) | PS |

**Total populated rows: ~2,392,277**

### C. CTS JSON Extractions (D01 Transport System)

Stored in `sap_data_extraction/reports/cts_data/`:

| File | Size | Content |
|------|------|---------|
| `cts_10yr_analyzed.json` | 32 MB | Full 10yr transport history (analyzed) |
| `cts_10yr_raw.json` | 32 MB | Full 10yr transport raw |
| `cts_8yr_raw.json` | 27 MB | 8yr transport raw (earlier pull) |
| `cts_batch_2017-2026.json` | 2-5 MB each | Per-year batches |
| `cts_config_detail.json` | 2.2 MB | Config object details |
| `cts_eventlog.json` | 0.19 MB | Process mining event log |
| `cts_dashboard.html` | 2.2 MB | **Live CTS Dashboard** |

### D. FI/MM Tables — NOT YET EXTRACTED

Scripts are ready but overnight extraction has NOT been run yet:

| Table | SAP Source | Filter | Checkpoints Planned |
|-------|-----------|--------|---------------------|
| BKPF | FI Doc Headers | BUDAT 2024-2026 | 36 monthly files |
| BSEG | FI Line Items | BUDAT 2024-2026 | 36 monthly files |
| EKKO | PO Headers | BEDAT 2024-2026 | 36 monthly files |
| EKPO | PO Lines | AEDAT 2024-2026 | 36 monthly files |
| EKBE | PO History/GR/SES | BUDAT 2024-2026 | 36 monthly files |
| ESSR | Entry Sheet Headers | ERDAT 2024-2026 | 36 monthly files |
| ESLL | Entry Sheet Lines | via ESSR keys | 1 file |

### E. ABAP Code Extractions (extracted_sap/)

| Domain | Objects Extracted |
|--------|-----------|
| HCM/Offboarding | BSP_ZHROFFBOARDING, BSP_YHR_OFFBOARDEMP (full source) |
| HCM/Offboarding/classes | ZCL_ZHRF_OFFBOARD_DPC_EXT + MPC + MPC_EXT + DPC variants |
| HCM/Benefits/classes | ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT, Benefits MPC/DPC |
| HCM/_shared/classes | ZCL_HR_FIORI_OFFBOARDING_REQ, BENEFITS, BADCOMMON, RENTAL, REQUEST |

### F. BDC / Monitoring (in-memory, P01 — NOT persisted to disk)

| Data | Source | Key Facts |
|------|--------|-----------|
| BDC Sessions (90 days) | APQI/APQD | 500 sessions; 135 Allos (PRAA*); 1,180 Travel |
| System Object Counts | TADIR | 826 PROG / 142 CLAS / 0 WAPA in P01 |
| TADIR cache | tadir_cache.sqlite | 4,168 object→package mappings |

---

## 2. TABLE RELATIONSHIP MAP (The Brain)

```
PSM / FUND MANAGEMENT DOMAIN
────────────────────────────────────────────────────────────────
FMFCT (funds 64K) ─────────────────────────────────────────────┐
  .FINCODE (fund key)                                           │
                                                                ├──> FMIFIIT (2.07M rows!) ◀── NEW
FMFCTR (fund_centers 764) ─────────────────────────────────────┤     .FONDS → funds.FINCODE (99.9% match)
  .FICTR (fund center key)                                      │     .FISTL → fund_centers.FICTR (100% match)
                                                                │     .GJAHR (2024-2026)
FMBDT (fmbdt_summary 19K) ─ budget by fund/fund center         │     .FMBELNR (FM doc number)
FMAVCT (fmavct_summary 19K) availability by fund/center        │     .KNBELNR ──> BKPF (FI doc headers) [NOT YET]
YTFM_FUND_CPL (6K) ───────── UNESCO ceiling mapping            │                    .BELNR, .GJAHR, .BUDAT
YTFM_WRTTP_GR (66) ───────── UNESCO value type groups          │                    .BELNR ──> BSEG (FI line items)

FMIFIIT KEY FIELDS (verified from DD03L):
  Keys: MANDT, FIKRS, GJAHR, FMBELNR, FMBUZEI, BTART, RLDNR, STUNR
  Financial: FONDS, FISTL, FIPEX, FAREA, WRTTP, TWAER, FKBTR, TRBTR
  Period: PERIO (001-016, SAP special periods included)
  FI Link: KNBELNR/KNGJAHR/KNBUZEI → BKPF.BELNR/GJAHR
  Refs: BUKRS, HKONT, PRCTR, GRANT_NBR, MEASURE, SGTXT

PS / PROJECT SYSTEM
────────────────────────────────────────────────────────────────
PROJ (proj 13K) ─── project definitions                        │
  .PSPID ──> PRPS (prps 58K) WBS elements                      ├──> RPSCO (cost plan, EMPTY)
              .PS_POSID ──> links to BSEG postings             │    COEP (CO postings, EMPTY)
                         ──> links to FMIFIIT sponsored pgms   │
                                                                │
PROCUREMENT DOMAIN (not yet extracted)                          │
────────────────────────────────────────────────────────────────┤
EKKO (PO headers)                                              │
  .EBELN ──> EKPO (PO lines)                                   │
  .EBELN ──> EKBE (GR history) ──> BKPF.BELNR (GR posting)   │
  .EBELN ──> ESSR (entry sheets) ──> ESLL (entry sheet lines) │
```

---

## 3. KNOWLEDGE VALUE - WHAT QUERIES BECOME POSSIBLE

### ✅ Already possible (PSM + FMIFIIT extracted):
- Fund master: all 64,799 UNESCO funds with type/date/creator
- Fund center hierarchy (764 centers)
- Project portfolio: 13,878 projects + 58,516 WBS elements
- Budget vs availability overview by fund/fund center (summary level only)
- UNESCO-specific fund ceiling rules (YTFM custom tables)
- **NEW: FM document-level spending by fund/center/period (2.07M line items!)**
- **NEW: Fund spending by period (PERIO 001-016) across 3 years**
- **NEW: FM transaction types (VRGNG) and value types (WRTTP) analysis**
- **NEW: FI document references ready for BKPF/BSEG join (KNBELNR field)**

### ✅ NEW — Example FM Queries (now possible):

```sql
-- Actual spending by fund, year, period
SELECT FONDS, GJAHR, PERIO, SUM(CAST(FKBTR AS REAL)) as total_amount
FROM fmifiit_full
WHERE FIKRS='UNES' AND GJAHR='2024'
GROUP BY FONDS, GJAHR, PERIO
ORDER BY FONDS, PERIO;

-- Top funds by transaction volume
SELECT FONDS, COUNT(*) as docs, COUNT(DISTINCT FMBELNR) as unique_docs
FROM fmifiit_full WHERE FIKRS='UNES' AND GJAHR='2025'
GROUP BY FONDS ORDER BY docs DESC LIMIT 20;

-- FM to FI linkage readiness (KNBELNR populated?)
SELECT GJAHR, COUNT(*) as total,
       SUM(CASE WHEN KNBELNR!='' THEN 1 ELSE 0 END) as has_fi_link
FROM fmifiit_full GROUP BY GJAHR;
```

### 🔜 Unlocked after overnight FI/MM extraction:
- **Actual spending by fund with FI detail** -- join FMIFIIT.KNBELNR→BKPF→BSEG
- **PO-to-payment lifecycle** -- EKKO→EKPO→EKBE→ESSR→BKPF→BSEG
- **Entry sheet verification** -- ESSR/ESLL vs BKPF payments
- **Vendor spending patterns** -- EKKO.LIFNR aggregated 3yr
- **Budget vs actual** -- FMBDT (budget) vs FMIFIIT (actuals) per fund

---

## 4. GAPS — What We Are Missing

| Gap | Business Impact | Fix |
|-----|----------------|-----|
| ~~FMIFIIT full not loaded~~ | ~~Cannot link FM docs to FI docs~~ | ✅ **DONE — 2,070,523 rows loaded** |
| COOI/COEP/RPSCO empty | No CO order/WBS actual cost data | Needs new extraction script |
| BKPF/BSEG not extracted | No actual FI posting data | Run overnight extraction |
| EKKO/EKPO/EKBE not extracted | No PO/GR/entry sheet data | Run overnight extraction |
| BDC intelligence not persisted | Allos analysis lost between sessions | Save APQI results to JSON |
| fmifiit_raw_data / projects / wbs_elements | Deprecated empty shells | Can be dropped |

---

## 5. DATA INTEGRITY (verified 2026-03-15)

| Verification | Result |
|-------------|--------|
| FMIFIIT row counts vs volume_anchors | **21/21 passed** ✅ |
| Key fields (FIKRS,GJAHR,FMBELNR,FMBUZEI) nulls | **0 nulls** ✅ |
| FONDS → funds.FINCODE join | **99.9%** (7,905/7,909) ✅ |
| FISTL → fund_centers.FICTR join | **100%** (358/358) ✅ |
| CTS transport headers (owner/date) | **100%** filled ✅ |

---

## 6. SCRIPT MAP

| Script | Extracts/Does | State |
|--------|--------------|-------|
| `extract_fmifiit_full.py` | FMIFIIT 2024-2026 all 7 areas | ✅ DONE + auto-loads to SQLite |
| `extract_bkpf_bseg_parallel.py` | BKPF + BSEG 2024-2026 | Ready - NOT RUN |
| `extract_ekko_ekpo_parallel.py` | EKKO/EKPO/EKBE/ESSR/ESLL | Ready - NOT RUN |
| `run_overnight_extraction.py` | Orchestrates both (max 2 concurrent SAP) | Ready - NOT RUN |
| `extraction_status.py` | Status dashboard + SQLite loader | Working |
| `cts_extract_batch.py` | CTS transport orders | Done (10yr data) |
| `sap_system_monitor.py` | BDC, dumps, users, jobs from P01 | Working |
| `read_psm_logic.py` + related | PSM tables → SQLite (gold_master) | Done |

---

## 7. NEXT ACTIONS

```
[PRIORITY 1 - RUN TONIGHT]
cd sap_data_extraction
python scripts/run_overnight_extraction.py
  -> Extracts BKPF, BSEG, EKKO, EKPO, EKBE, ESSR, ESLL
  -> Uses max 2 concurrent SAP connections
  -> JSON checkpoints saved to extracted_data/

[PRIORITY 2 - MORNING CHECK]
python scripts/extraction_status.py
  -> Shows all tables: PSM (what we have), FI/MM (what just landed)

[PRIORITY 3 - AFTER EXTRACTION]
Load FI/MM checkpoints into SQLite (auto-load should be added to scripts)

[PRIORITY 4 - FUTURE]
- Extract COOI, COEP, RPSCO for CO cost data
- Persist BDC session data (APQI results) to bdc_sessions.db
- Delete JSON checkpoints once SQLite is verified (save ~2GB disk)
- Drop deprecated tables: fmifiit_raw_data, projects, wbs_elements
```
