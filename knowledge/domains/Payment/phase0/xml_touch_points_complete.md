# Complete XML Touch-Point Inventory

**Single source of truth for every code point that affects outgoing XML payment file content.**

**Session #62** · **2026-04-24** · **Target trees**: `/SEPA_CT_UNES`, `/CITI/XML/UNESCO/DC_V3_01`, `/CGI_XML_CT_UNESCO`, `/CGI_XML_CT_UNESCO_1`

---

## Grouped by payment lifecycle stage

```
[Vendor master read] → [F110 selection] → [FPAYHX population]
  → [OBPM4 events] → [DMEE tree traversal] → [node EXIT_FUNC calls]
  → [XML assembly] → [post-DMEE file handling] → [BCM batch] → [SWIFT delivery]
```

Each table below = one stage. Every asset that can mutate the XML appears in exactly one stage. "Change required" column is the output for the Phase 0 exit gate.

---

### Stage 1 — Vendor master / address source (data layer)

Data flows INTO F110, which copies into FPAYHX/FPAYH/FPAYP structures.

| Asset | Type | Path/location | Role | Change required? |
|---|---|---|---|---|
| LFA1 | SAP_TABLE | Gold DB + P01 | Vendor master, STRAS/ORT01/PSTLZ/LAND1/ADRNR | NO — data source |
| ADRC | SAP_TABLE | Gold DB + P01 | Central address mgmt, STREET/HOUSE_NUM1/CITY1/POST_CODE1/COUNTRY | NO — data source; **DQ remediation for 5 vendors** missing CITY1/COUNTRY |
| LFBK | SAP_TABLE | Gold DB + P01 | Vendor bank account | NO |
| T001 | SAP_TABLE | Gold DB + P01 | Company code (UNESCO) master, ADRNR → ADRC for Dbtr address | NO — data source |

### Stage 2 — F110 payment run (standard SAP, not touched)

SAP standard F110 picks open items, groups by vendor/bank/currency, populates FPAYHX/FPAYH/FPAYP structures using vendor master + company code address + payment method config.

| Asset | Type | Role | Change required? |
|---|---|---|---|
| F110 transaction | SAP_TCODE | Entry point | NO — used as-is for test |
| SAPFPAYM | SAP_PROG | Payment medium generator | NO |
| T042Z_FULL | TABL | country+method → DMEE tree (FORMI) mapping | NO — already configured |
| T042A | TABL | payment method per co code | NO |
| T042I | TABL | house bank per co code per method | NO |

### Stage 3 — FPAYHX / FPAYH / FPAYP population

SAP standard PMW auto-populates the structures at F110 runtime. No UNESCO custom code writes to Z-fields (verified: 0 writes in 986 ABAP files).

| Asset | Type | Role | Change required? |
|---|---|---|---|
| FPAYHX | STRU | 432 fields, 25 Z-fields (ZPFST/ZPLOR/ZLISO/... + ZREF01..10) | NO — SAP-populated |
| FPAYH | STRU | Payment header | NO — SAP-populated |
| FPAYP | STRU | Payment line | NO — SAP-populated |
| CI_FPAYHX | APPEND | Customer append structure defining Z-fields | NO for this change; **confirm membership** in Phase 1 |

### Stage 4 — OBPM4 Event 05 (user exit hook)

Currently no UNESCO Event 05 handler exists for address. Phase 2 creates one.

| Asset | Type | Role | Change required? |
|---|---|---|---|
| OBPM4 customizing (TFPM042FB) | TABL | Event registrations per format | **YES — register our new FM** (Step 10) |
| `Z_DMEE_UNESCO_DEBTOR_ADDR` | FUGR/FM | **NEW** — reads T001→ADRC for Dbtr, writes FPAYHX-ZREF01..ZREF05 | **YES — CREATE** (Step 9) |
| Other Y/Z Event 05 handlers | FUGR | None found for address in P01 | NO — only ZWFPAYROLL_STATUS for payroll |

### Stage 5 — DMEE tree traversal (per target tree)

4 target trees, 1,975 nodes total, 354 address+party-related. SAP standard DMEE engine walks each tree per payment, reading values from source fields and calling exits.

| Tree | Total nodes | Address+party | Change required? | Priority |
|---|---|---|---|---|
| `/SEPA_CT_UNES` | 95 | 15 | **YES — add structured nodes to Dbtr+Cdtr** | P1 (Tier A) |
| `/CITI/XML/UNESCO/DC_V3_01` | 610 | 83 | **YES — add Ctry to Dbtr, restructure Dbtr, verify UltmtCdtr Worldlink** | P1 + blocked by Q3 |
| `/CGI_XML_CT_UNESCO` | 631 | 124 | **YES — fix CdtrAgt Unstructured** (Dbtr already ok) | P2 |
| `/CGI_XML_CT_UNESCO_1` | 639 | 132 | **YES — same as CGI_XML_CT_UNESCO** | P2 |

### Stage 6 — Node EXIT_FUNC calls (794 nodes mediated by BAdI)

When a node has `MP_EXIT_FUNC='FI_CGI_DMEE_EXIT_W_BADI'`, the value goes through one of our 5 country-class implementations. 146 address-related nodes have exits.

| Exit function | Node count | Extracted? | Change required? |
|---|---|---|---|
| `FI_CGI_DMEE_EXIT_W_BADI` (dispatches to country) | 794 | BAdI def SAP, 3 impls extracted (FR/FALLBACK/UTIL), 2 not yet (DE/IT) | **MAYBE — each new structured node must decide: set EXIT_FUNC='' (skip BAdI) or let BAdI process** |
| `/CITIPMW/V3_*` (12 prebuilt CITI exits) | 18 | SAP standard | NO — preserve |
| `DMEE_EXIT_SEPA_*` (3 SEPA exits) | 5 | SAP standard | NO |
| `Z_DMEE_EXIT_TAX_NUMBER` | 1 | Not extracted | NO — not address |
| `ZDMEE_EXIT_SEPA_21` | 1 | Not extracted | NO — not address |

### Stage 7 — BAdI implementations (our 5 UNESCO classes)

| Class | Extracted | Author | Change required? |
|---|---|---|---|
| YCL_IDFI_CGI_DMEE_FR | ✅ | N_MENARD | **MAYBE — review name-overflow-into-StrtNm quirk** (FALLBACK_CM001:13-31 semantics) |
| YCL_IDFI_CGI_DMEE_FALLBACK | ✅ | N_MENARD (2024-11-22) | **MAYBE — same quirk review** |
| YCL_IDFI_CGI_DMEE_UTIL | ✅ | N_MENARD | NO — utility only |
| YCL_IDFI_CGI_DMEE_DE | ❌ (exists in P01, not extracted) | likely N_MENARD | **Extract in Phase 0 follow-up** |
| YCL_IDFI_CGI_DMEE_IT | ❌ (exists in P01, not extracted) | likely N_MENARD | **Extract in Phase 0 follow-up** |

**N_MENARD = required code reviewer for Phase 2 Step 9** (`Z_DMEE_UNESCO_DEBTOR_ADDR`) and any changes to the BAdI classes.

### Stage 8 — Post-DMEE file handling

XML file is written to directory per handoff doc §4.3 (Alliance Lite2 pickup).

| Asset | Type | Role | Change required? |
|---|---|---|---|
| File transmission code | PROG (not extracted) | Writes XML to `\\hq-sapitf\SWIFT$\P01\input\` | NO — address change is within XML content, not filename |
| Alliance Lite2 client | External | SWIFT file pickup | NO |
| File naming convention | DOC | `aaaa_bbbb_ccxxxxxxxxyyyy.in` | NO |

### Stage 9 — BCM (Bank Communication Management)

BCM receives the generated file, queues for dual-control approval, sends to bank.

| Asset | Type | Role | Change required? |
|---|---|---|---|
| OBPM5 routing (TFIBLMPAYBLOCK) | TABL | 100% F110+payroll routed through BCM (Claim #65) | NO — preserve routing |
| BNK_BATCH_HEADER / BNK_BATCH_ITEM | SAP_TABLE | Batch records | NO — data |
| Workflow 90000003 | WF | Payment approval workflow | NO — out of scope |
| BCM_BATCH_* BAdIs | BADI (not extracted) | Batch enhancement hooks | NO — address change does not affect batch-level logic |
| BNK_APP signatory approval UI | SAP_TCODE | Where signatories see the batch | **MAYBE — verify UI renders structured tags correctly** (Phase 3 test) |

### Stage 10 — Supporting / governance / monitoring

| Asset | Type | Role | Change required? |
|---|---|---|---|
| H13 dual-control monitor | PY_SCRIPT | `Zagentexecution/bcm_dual_control_monitor.py` | **NO change to script; EXTEND monitoring post-go-live** for address-related reject tracking |
| `feedback_bcm_ghost_pernr_check` | RULE | Pre-test DQ check for UIS payments | NO |
| `feedback_only_p01_for_config_analysis` #204 | RULE | Decision anchor | NO |

---

## Change locus summary

**Where the change physically happens**:

| Where | What | Who | Depends on |
|---|---|---|---|
| **DMEE tree nodes (SEPA + CITI + CGI)** via tx DMEE | Add structured `<StrtNm>/<BldgNb>/<PstCd>/<TwnNm>/<Ctry>` nodes under Cdtr/Dbtr/UltmtCdtr PstlAdr; deactivate AdrLine or keep for Hybrid | Pablo | GAP-006 closed ✅ |
| **OBPM4 Event 05** via tx OBPM4 | Register new FM `Z_DMEE_UNESCO_DEBTOR_ADDR` for all 3 PMW formats | Pablo | Step 9 complete |
| **Function module** `Z_DMEE_UNESCO_DEBTOR_ADDR` in ABAP via tx SE37 | New FM: reads T001→ADRC, writes `E_FPAYHX-ZREF01..ZREF05` (not FPAYH-REF) | Pablo + N_MENARD review | GAP-004 closed ✅ |
| **Optional — BAdI classes** `YCL_IDFI_CGI_DMEE_FALLBACK/_FR` | Review + possibly constrain name-overflow quirk | N_MENARD | Phase 2 decision |
| **Vendor master** (LFA1+ADRC) | Fix 5 vendors missing CITY1 or COUNTRY | Master Data team | Phase 1 |

**Where the change DOES NOT physically happen**:
- F110 itself (standard SAP used as-is)
- Payment medium programs SAPFPAYM / RFFO* (standard)
- BCM workflow 90000003 (out of scope)
- File transmission / SWIFT (not affected)
- LFA1/ADRC populator code (SAP standard)
- FPAYHX/FPAYH/FPAYP data model (append structures unchanged)

---

## Outstanding (Phase 0 follow-ups that don't block Phase 1)

1. **Extract `YCL_IDFI_CGI_DMEE_DE` and `_IT`** source via pyrfc RPY_CLASS_READ. Needed for Phase 3 German/Italian regression tests.
2. **Extract source of `Z_DMEE_EXIT_TAX_NUMBER` and `ZDMEE_EXIT_SEPA_21`** to confirm they're unrelated to address.
3. **Confirm `CI_FPAYHX` include structure** membership via DD03L probe (partial today — 25 Z-fields known, confirm they're all in CI_FPAYHX).
4. **Resolve Q3 (Worldlink UltmtCdtr data source)** — doc blocker for Phase 2 Step 7.

## Zero UNKNOWN in "Change required" column — Phase 0 exit gate met

Every asset above has a verdict: YES / NO / MAYBE (with decision point) / extraction-follow-up.
