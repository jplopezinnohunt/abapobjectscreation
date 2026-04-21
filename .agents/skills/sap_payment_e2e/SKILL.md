---
name: sap_payment_e2e
description: End-to-end payment lifecycle process mining — Invoice → Due Date → F110 → BCM → Bank File → Cleared. 1.4M events, 550K cases, 9 company codes. BCM batch tracking, FBZP validation, cycle-time analysis, company-code comparison.
domains:
  functional: [Payment, Treasury, BCM]
  module: [FI]
  process: [T2R, P2P]
tier: project
maturity: production
origin_session: 20
last_updated_session: 55
triggers: [payment process mining, F110, BCM batch, invoice-to-payment cycle time, company code comparison, BKPF, BSAK, BSIK, REGUH, REGUP, PAYR]
subtopics: [process_mining_1_4M_events, company_code_comparison, fbzp_chain_validation]
---

# SAP Payment E2E — Invoice to Reconciliation

## Metadata
- **Name**: sap_payment_e2e
- **Maturity**: Production
- **Origin**: Session #020 — Payment process mining across 9 company codes
- **Dependencies**: Gold DB (BKPF, BSAK, BSIK, BNK_BATCH_HEADER, T042*, T012*, T001)

## Purpose

End-to-end payment lifecycle process mining for UNESCO SAP. Traces the full flow:
**Invoice Posted → Due Date → F110 Payment Run → BCM Batch → Bank File Sent → Vendor Cleared**

Includes BCM (Bank Communication Management) batch tracking, FBZP chain completeness validation, cycle time analysis, and company code comparison across all 9 active company codes.

## NEVER Do This

1. **Never assume F110 is the only payment path** — UNESCO has BCM manual payment requests, advance payments (FBA6/KA), and direct payments (F-53)
2. **Never skip BCM analysis** — BCM is the primary payment approval mechanism. BNK_BATCH_HEADER has 27,443 batches.
3. **Never use SGTXT for payment identification** — Use BKPF.BLART (doc type) + BSAK.AUGBL (clearing doc) for reliable linking
4. **Never confuse T042A with T042C** — T042A = payment methods per paying company code (76 rows). T042C = client-level settings only (0 rows in UNESCO)
5. **Never ignore OBPM4** — Selection variants are NEVER transported. Must recreate manually per system.

## Data Sources (Gold DB)

### Transaction Data (already extracted)
| Table | Rows | Purpose |
|-------|------|---------|
| bkpf | 1.67M | Document headers — BLART identifies: KR/RE=invoice, ZP=payment, KA=advance |
| bsak | 739K | Vendor cleared items — AUGDT/AUGBL links invoice→payment |
| bsik | 8K | Vendor open items (unpaid invoices) |
| BNK_BATCH_HEADER | 27,443 | BCM batches — CRDATE/CRUSR/CHDATE/CHUSR/CUR_STS tracks approval flow |

### Configuration Data (extracted Session #020)
| Table | Rows | Purpose |
|-------|------|---------|
| T001 | 9 | Company code master (BUKRS, BUTXT, LAND1, WAERS) |
| T042/T042A | 9/76 | Paying company codes + payment method assignments |
| T042B | 9 | Paying company code settings (min amounts, advice forms) |
| T042E | 89 | Payment methods per country |
| T042I | 76 | Bank ranking order for F110 bank selection |
| T042Z | 263 | Payment method definitions per country |
| T012 | 211 | House bank master |
| T012K | 402 | House bank accounts + GL reconciliation |

### Pending Extraction (VPN dependent)
| Table | Purpose | Status |
|-------|---------|--------|
| BNK_BATCH_ITEM | BCM batch items — VBLNR links batch→payment doc→invoice | Pending |
| REGUH | F110 payment run headers — LAUFD/LAUFI/XVORL proposal flag | Readable, pending |
| FEBEP | Electronic bank statement items — **223,710 rows (2024-2026), 99.9% posted** | ✅ Extracted #029 |
| PAYR | Payment register (checks/transfers) | Readable, pending |

## Event Log Construction

### Case ID Strategy
- **Invoice cases**: `INV_{BUKRS}_{BELNR}_{GJAHR}` — invoice is the anchor
- **Down payment cases**: `DP_{BUKRS}_{BELNR}_{GJAHR}`
- **BCM batch cases**: `BCM_{ZBUKR}_{BATCH_NO}` — batch-level tracking
- **Unlinked payments**: `PAY_{BUKRS}_{BELNR}_{GJAHR}`

### Activity Mapping (11 activities)

| Activity | Source | Timestamp | Link Logic |
|----------|--------|-----------|------------|
| Invoice Posted | BKPF BLART=KR/RE/KG | BUDAT | Direct |
| Invoice Due | BSAK/BSIK.ZFBDT | ZFBDT | Same doc keys |
| Down Payment Request | BKPF BLART=KA | BUDAT | Direct |
| Payment Executed | BKPF BLART=ZP/KZ | BUDAT | BSAK.AUGBL=payment BELNR |
| BCM Batch Created | BNK_BATCH_HEADER | CRDATE | LAUFD+LAUFI=F110 run |
| BCM Batch Approved | BNK_BATCH_HEADER (CHUSR!=CRUSR) | CHDATE | Same batch |
| BCM Batch Updated | BNK_BATCH_HEADER (CHUSR=CRUSR) | CHDATE | Same batch |
| BCM Sent to Bank | BNK_BATCH_HEADER CUR_STS=IBC05 | CHDATE | Same batch |
| BCM Batch Completed | BNK_BATCH_HEADER CUR_STS=IBC15 | CHDATE | Same batch |
| BCM Batch Reversed | BNK_BATCH_HEADER CUR_STS=IBC20 | CHDATE | Same batch |
| Vendor Cleared | BSAK.AUGDT | AUGDT | AUGBL links payment→invoice |

### BCM Status Codes (from BNK_BATCH_HEADER.CUR_STS)
| Code | Meaning | Count |
|------|---------|-------|
| (empty) | **Pre-TMS legacy 2014–2021** — CUR_STS not populated before Coupa/TMS migration (2022). All 15K batches confirmed in 2014–2021 date range. Zero empty-status batches after 2021. [VERIFIED from CRDATE analysis] | 15,003 |
| IBC15 | Completed | 7,016 |
| IBC17 | Failed | 2,056 |
| IBC05 | Sent to bank | 1,650 |
| IBC11 | Approved | 1,291 |
| IBC06 | Rejected | 161 |
| IBC20 | Reversed | 69 |

## FBZP Chain Validation

6-level dependency chain — F110 requires all 6:
```
T042 (Paying CoCode) → T042A (Pmt Methods/CoCode) → T042E (Pmt Methods/Country)
    → T042I (Bank Ranking) → T012 (House Banks) → T012K (Bank Accounts)
```

**Critical finding**: T042C is NOT the bank determination table in this SAP version. T042A holds payment method assignments per paying company code (76 rows, 14 unique RULE configurations).

## Company Code Payment Profile

| Code | Name | Invoices | BCM Batches | House Banks | Currency |
|------|------|----------|-------------|-------------|----------|
| UNES | UNESCO HQ | 146,990 | 21,855 | SOG01,CIT04,SOG03,CIT21,WEL01,CHA01,SOG04,DNB01,SCB14 | USD |
| UBO | UNESCO Brazil | 19,757 | 1,696 | CIT01 | BRL |
| IIEP | IIEP Paris | 6,728 | 2,099 | SOG02,SOG01 | EUR |
| ICTP | ICTP Trieste | 4,640 | — | — | EUR |
| IBE | UNESCO Spain | 3,105 | — | — | XOF/CHF |
| UIL | UNESCO Hamburg | 2,632 | 435 | SOG05 | EUR |
| MGIE | UNESCO Stat | 1,495 | — | — | — |
| ICBA | UNESCO Archives | 1,206 | — | — | — |
| UIS | UNESCO Stats | 876 | 1,358 | CIT01 | CAD |

## BCM Rules (Payment Grouping)

| Rule ID | Count | Purpose |
|---------|-------|---------|
| UNES_AP_ST | 8,195 | Standard AP payments |
| UNES_TR_TR | 4,305 | Treasury transfers |
| PAYROLL | 3,518 | Payroll payments |
| UNES_AP_10 | 2,488 | AP batch threshold 10 |
| IIEP_AP_ST | 2,099 | IIEP standard AP |
| UNES_AR_BP | 1,585 | AR business partner |
| UBO_AP_MAX | 1,337 | UBO max batch |
| UNES_AP_EX | 1,121 | AP exceptions |

## BCM Users (Top 10 Batch Creators)

| User | Batches | Role (inferred) |
|------|---------|-----------------|
| C_LOPEZ | 7,043 | Primary AP processor |
| I_MARQUAND | 6,938 | Primary AP processor |
| I_WETTIE | 3,634 | AP processor |
| F_DERAKHSHAN | 3,048 | AP processor |
| S_COURONNAUD | 2,035 | AP processor |
| E_AMARAL | 1,525 | UBO AP processor |

## Custom Payment Programs

| Program | Lines | Purpose |
|---------|-------|---------|
| ZFI_SWIFT_UPLOAD_BCM | 2,800 | BCM SWIFT payment file upload |
| YENH_FI_DMEE | 20 | DMEE format enhancement (credit/debit calc) |
| YCEI_FI_SUPPLIERS_PAYMENT | — | Supplier payment enhancement |
| Y_F110_AVIS_IBE | — | Payment advice form (IBE) |
| ZF140_CHEQUE_DOC | — | Cheque document form (ICTP) |

## Cycle Time Analysis (Session #020 Results)

| Metric | Mean | Median | P90 | N |
|--------|------|--------|-----|---|
| Invoice → Payment | 4.1d | 2.0d | 8.0d | 84,166 |
| Invoice → Clearing (E2E) | 5.6d | 2.0d | 10.0d | 183,399 |
| Payment → Clearing | 0.0d | 0.0d | 0.0d | 212,465 |
| Due Date → Payment | 26.8d | 14.0d | 59.0d | 42,945 |

**On-Time Payment: 1.1%** — Invoices are paid median 14 days AFTER due date.

## Process Mining Results

- **Total Events**: 1,435,376
- **Cases**: 550,993
- **Activities**: 12
- **Variants**: 207

### Top Variants
1. Invoice Posted → Vendor Cleared (direct clearing, no separate payment doc)
2. Invoice Posted → Payment Executed → Vendor Cleared (standard F110 flow)
3. Invoice Due → Invoice Posted → Payment Executed → Vendor Cleared (full lifecycle)
4. BCM Batch Created → BCM Batch Updated → BCM Batch Completed (BCM flow)
5. BCM Batch Created → BCM Batch Approved → BCM Batch Completed (BCM with approval)

## Script Location

| Script | Purpose |
|--------|---------|
| `Zagentexecution/mcp-backend-server-python/payment_process_mining.py` | Main: event log + analysis + HTML |
| `Zagentexecution/mcp-backend-server-python/extract_payment_config.py` | Config extraction (T042*/T012*/T001) |
| `Zagentexecution/mcp-backend-server-python/build_payment_companion.py` | Companion builder (config interpretation) |
| `Zagentexecution/mcp-backend-server-python/payment_event_log.csv` | Event log (1.4M rows, pm4py/Celonis ready) |
| `Zagentexecution/mcp-backend-server-python/payment_process_mining.html` | Process mining dashboard (694KB) |
| `Zagentexecution/mcp-backend-server-python/payment_bcm_companion.html` | Payment & BCM companion v6 (13 tabs, PPC verified, Discoveries tab) |
| `knowledge/domains/FI/payment_full_landscape.md` | Full payment landscape knowledge doc (100% PDF coverage) |

## Related Skills

**Session #022 note**: sap_payment_bcm_agent was deeply enriched — 13 PDFs fully extracted. Key new knowledge: payroll BCM flow (ZHRUN→FBPM1→BNK_APP), Note to Payee SWIFT :70 spec, HR payroll ZUONR formula, SWIFT directory access groups, BCM auth objects, 4 payment processes (Processes 1-4), 2023 security incident.

| Skill | Relationship |
|-------|-------------|
| `sap_payment_bcm_agent` | Domain agent — routes all payment/BCM questions. Has full config interpretation. |
| `sap_company_code_copy` | FBZP chain gaps, 41-task post-copy checklist |
| `sap_transport_intelligence` | BCM post-transport actions (SWU3, SWE2, OBPM4) |

## Integration Points

- **P2P Process Mining** (`p2p_process_mining.py`) — P2P ends at Invoice Posted; this skill picks up from there
- **Company Code Copy** (`sap_company_code_copy/SKILL.md`) — FBZP chain gaps affect payment capability
- **Transport Intelligence** (`sap_transport_intelligence/SKILL.md`) — BCM post-transport checklist
- **FI Domain Agent** (`fi_domain_agent/SKILL.md`) — FM-FI bridge for budget linkage

## Extracted Tables (Session #020)

| Table | Rows | Purpose |
|-------|------|---------|
| BNK_BATCH_HEADER | 27,443 | BCM batch headers |
| BNK_BATCH_ITEM | 600,042 | BCM batch items — VBLNR links to invoices |
| REGUH | 942,011 | F110 payment run headers (358K proposals, 584K final) |
| PAYR | 4,431 | Payment register (checks: ICTP + UNES field offices) |
| FEBEP | **223,710** | **CORRECTED #029**: 223K items (2024-2026), 99.9% posted. EBS is FULLY active. FEBKO=84,972 headers. See `bank_statement_ebs_architecture.md` |

## 4-Stream Payment Architecture (Discovery #1 — Session #027)

UNESCO HQ clearing is NOT a single stream. BSAK analysis confirmed 4 structurally distinct clearing streams:

| Stream | BLART | Count | GL Account | Bank System | In Event Log? |
|--------|-------|-------|------------|-------------|---------------|
| 1 — F110/BCM (HQ auto) | ZP | 215K | T012K standard | SWIFT via BCM | ✅ Yes |
| 2 — Field office sub-bank | OP | 274,863 | 2021xxx (NOT in T012K) | Local banking system | ✅ #028 |
| 3 — Internal netting | AB | 138,378 | Vendor reconciliation | No bank transfer | ✅ #028 |
| 4 — Tier 3 codes (IBE/MGIE/ICBA) | OP | 82 | Local sub-accounts | Local banking | ✅ #028 |

**Key evidence**: REGUH.VBLNR = BSAK.AUGBL WHERE BSAK.BLART=OP → **0 rows** (confirmed Session #027).
OP documents are completely outside F110/BCM. GL 2021xxx are field office sub-bank clearing accounts not in T012K.
AB = BSCHL=31 (109K credit netting) + BSCHL=29 (24K advance offset). No bank transfer.

**Impact**: All 4 streams now modeled (Session #028). Total: 1,848,699 events / 550,993 cases. Event log = `payment_event_log.csv`, dashboard = `payment_process_mining.html`.

## Known Gaps

1. **FCLM_BAM_* tables don't exist** — UNESCO uses BNK_BATCH_* not FCLM_BAM_* for BCM
2. **REGUH→Invoice link validated** — REGUH.VBLNR = BSAK.AUGBL: **1,380,108 matched rows** confirmed. [VERIFIED Session #027]. OP docs are outside REGUH scope (REGUH→OP = 0 rows). Scope difference only, not a data quality issue.
3. **On-Time 1.1% is a measurement artifact** — 73% of invoices have ZTERM=0001 (immediate) with ZFBDT=BUDAT. This means the "due date" = posting date. Real on-time for items with actual terms = 4.6%. The 26.8d/1.1% metrics should NOT be presented as late-payment KPIs without segmentation by ZTERM. [VERIFIED Session #026]
4. **IBE/MGIE/ICBA DO clear invoices via F-53 (BLART=OP)** — 5,364 + 3,211 + 1,227 OP docs confirmed in BSAK 2024–2026. "Outside SAP" refers to the bank instruction, not the accounting document. [VERIFIED Session #026]
5. ~~**IBC17 failures uninvestigated**~~ — Closed Session #028: ALL 2,056 IBC17 failures are 2021-2022 (BCM activation outage Jul21-Dec22). Zero failures in 2024-2026. Root cause: BCM misconfigured for 15 months after activation, fixed Oct-Dec 2022.
6. ~~**Event log covers Stream 1 only**~~ — Resolved Session #028: All 4 streams now modeled. Stream 2 (OP field office): 274,863 events. Stream 3 (AB netting): 138,378 events. Stream 4 (Tier 3): 82 events. Total: 1,848,699 events.

## You Know It Worked When

1. Dashboard opens in VSCode with vis.js DFG rendering
2. 8 tabs all populated: Activities, Variants, Cycle Times, Company Codes, FBZP Chain, Timeline, TCodes, BCM Flow
3. BCM flow shows two paths: Created→Updated→Completed and Created→Approved→Completed
4. FBZP chain matrix shows green/red per company code
5. CSV importable into pm4py: `import pm4py; log = pm4py.read_xes('payment_event_log.csv')`
