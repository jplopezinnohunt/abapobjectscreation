# UNESCO BCM Structured Address — End-to-End Flow Map

**Session #62 · 2026-04-25 · Status: ALL components connected, no unknowns remaining for V001 design**

This document connects every extracted component into a single logical flow,
per user directive "tenemos que conectar todos los elementos en un flow logico".

---

## Master Flow Diagram (per tree)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          F110 PAYMENT RUN                                │
│  Inputs: open invoices, vendors, payment methods                         │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  T042Z LOOKUP — country+payment-method → tree FORMI                      │
│  263 rows in P01 (verified Phase 0)                                      │
│  XBKKT='X' = DMEE-enabled                                                │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
        ┌────────┴────────┬────────────────────┬──────────────────────────┐
        │                 │                    │                          │
        ▼                 ▼                    ▼                          ▼
   ┌─────────┐      ┌───────────┐       ┌──────────────────┐    ┌──────────────────┐
   │  SEPA   │      │   CGI     │       │  CGI variant 1   │    │   CITI           │
   │ payment │      │ payment   │       │   payment        │    │   payment        │
   └────┬────┘      └─────┬─────┘       └────────┬─────────┘    └────────┬─────────┘
        │                 │                      │                       │
        ▼                 ▼                      ▼                       ▼
                 ─────── EVENT 05 (OBPM4 TFPM042FB lookup) ───────
        │                 │                      │                       │
   ╔════════╗      ╔═══════════════════╗  ╔═══════════════════╗   ╔══════════════════════╗
   ║ V001:  ║      ║FI_PAYMEDIUM_      ║  ║FI_PAYMEDIUM_      ║   ║/CITIPMW/V3_         ║
   ║ ADD    ║      ║DMEE_CGI_05        ║  ║DMEE_CGI_05        ║   ║PAYMEDIUM_DMEE_05    ║
   ║ row    ║      ║(SAP std, already ║   ║(same FM)          ║   ║(CITI PMW Industry  ║
   ║ here   ║      ║registered)       ║   ║                  ║    ║Solution)            ║
   ║        ║      ╚═════════╤═════════╝  ╚═════════╤═════════╝   ╚══════════╤═══════════╝
   ╚════════╝                │                      │                        │
        │                    ▼                      ▼                        ▼
        │         ┌────────────────────────────────────────┐  ┌────────────────────────┐
        │         │ cl_idfi_cgi_call05_factory             │  │ Direct ADDR_GET via    │
        │         │ ::get_instance                         │  │ T001-ADRNR + ZADNR     │
        │         │   resolves country: format→ubiso→ubnks │  │ for one-time vendor    │
        │         │   → CL_IDFI_CGI_CALL05_FR/DE/IT/GB     │  │ uses BSEC table        │
        │         │   → fallback CL_IDFI_CGI_CALL05_GENERIC│  │                        │
        │         └─────┬──────────────────────────────────┘  └──────────┬─────────────┘
        │               │                                                 │
        ├───────────────┴─────── BUFFER POPULATION ──────────────────────┤
        │                                                                 │
        ▼                                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│       FPAYHX_FREF buffer (16 fields: REF01..REF15 + CURNO)                  │
│                                                                             │
│   Byte layout (UNIVERSAL — same in GENERIC and CITIPMW V3):                │
│       REF01[0..60]   = ADRC.STREET                                          │
│       REF01[60..80]  = ADRC.BUILDING                                        │
│       REF01[80..90]  = ADRC.POST_CODE1                                      │
│       REF01[90..100] = ADRC.REGION                                          │
│       REF01[100..110]= ADRC.HOUSE_NUM1                                      │
│       REF06[0..40]   = ADRC.CITY1                                           │
│       REF02 = Cdtr post_code2 + house_num1 (one-time vendor BSEC path)      │
│                                                                             │
│   FPAYP_FREF (5 fields: REF01..REF05) — same Dbtr address per line         │
│                                                                             │
│   Country class extras (REF14):                                             │
│     FR: SIRET 16 chars from SAPFR1 PPC param                                │
│     DE: SUN+SeqTp from T042M/T042N                                          │
│     IT: CUP+CIG+MGO from BSEG                                               │
│     GB: bnkid+SeqTp from T042M/T042N                                        │
│     SAP-std GENERIC writes nothing here                                     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DMEE TREE TRAVERSAL                                    │
│                                                                             │
│  V000 (current production):                                                 │
│    SEPA_CT_UNES   → 95 nodes  · 18 conditions · NO StrtNm/BldgNb/PstCd/TwnNm│
│    CITI DC_V3_01  → 610 nodes · 350 conditions · Dbtr unstructured          │
│    CGI_XML_CT_UNESCO   → 631 · 123 cond · Dbtr STRUCTURED ✓                 │
│    CGI_XML_CT_UNESCO_1 → 639 · 123 cond · same as parent (FIRSTNODE shared) │
│                                                                             │
│  V001 (NEW, to create):                                                     │
│    SEPA: ADD 5 Dbtr structured nodes sourcing FPAYHX-REF01/06 + MP_OFFSET   │
│    CITI: ADD 5 Dbtr structured nodes (Cdtr exits already produce structured)│
│          + 1 UltmtCdtr <StrtNm> = FPAYH-ZSTRA (Q3 RESOLVED #62, claim 99)   │
│    CGI:  FIX CdtrAgt (PstlAdr AdrLine -> structured StrtNm/PstCd/TwnNm/Ctry)│
│          Dbtr + Cdtr already structured V000, no change there               │
│    CGI_1: SYNC from parent (FIRSTNODE shared, CdtrAgt fix propagates)       │
│                                                                             │
│  Per-node node-level processing during traversal:                           │
│   • MP_SC_TAB + MP_SC_FLD + MP_OFFSET → read source                         │
│   • CV_RULE → conversion (CL=lowercase, AL.2=amount align, RP=replace)      │
│   • MP_EXIT_FUNC → call BAdI/FM if registered                               │
│   • DMEE_TREE_COND → check parent TECH switch nodes (PSTLADRMOR1/2/3 etc.)  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BAdI FI_CGI_DMEE_EXIT_W_BADI                             │
│                    (fires on 794 of 1,975 nodes = 40%)                      │
│                                                                             │
│  Dispatched by country to UNESCO impls:                                     │
│    YCL_IDFI_CGI_DMEE_FR     get_value()  → PPC dispatcher (0 rows for FR)  │
│    YCL_IDFI_CGI_DMEE_DE     get_credit() → SHELL: only ClrSysMmbId override │
│    YCL_IDFI_CGI_DMEE_IT     get_credit() → SHELL: same as DE                │
│    YCL_IDFI_CGI_DMEE_FALLBACK get_credit() → ⚠ NAME-OVERFLOW BUG (Pattern A)│
│    YCL_IDFI_CGI_DMEE_UTIL   utility class (PPC reader, helpers)             │
│                                                                             │
│  CITI tree extra layer (per-node EXIT_FUNC FMs, called only on CITI nodes): │
│    /CITIPMW/V3_CGI_CRED_STREET   → Cdtr StrtNm via BSEC or ADDR_GET          │
│    /CITIPMW/V3_CGI_CRED_PO_CITY  → Cdtr postal+city                         │
│    /CITIPMW/V3_CGI_CRED_REGION   → Cdtr CtrySubDvsn                         │
│    /CITIPMW/V3_GET_CDTR_BLDG     → Cdtr BldgNb                              │
│    /CITIPMW/V3_EXIT_CGI_CRED_NAME → Cdtr Nm                                 │
│    /CITIPMW/V3_EXIT_CGI_CRED_CITY → Cdtr TwnNm                              │
│    /CITIPMW/V3_EXIT_CGI_CRED_NM2  → Cdtr name continuation                  │
│    /CITIPMW/V3_GET_BANKCODE       → ECSIC clearing system code              │
│    /CITIPMW/V3_CGI_REGULATORY_INF → Regulatory info                         │
│                                                                             │
│  ⚠ Pattern A 3-line fix needed in YCL_IDFI_CGI_DMEE_FALLBACK_CM001:         │
│    name-overflow-into-StrtNm logic corrupts V001 structured StrtNm.         │
│    Add 'AND c_value IS INITIAL' guard. N_MENARD review required.            │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                XML ASSEMBLED IN MEMORY                                       │
│   pain.001.001.03 envelope with:                                             │
│     <Dbtr><PstlAdr>...</PstlAdr></Dbtr>                                      │
│     <Cdtr><PstlAdr>...</PstlAdr></Cdtr>                                      │
│     <CdtrAgt><FinInstnId>...</FinInstnId></CdtrAgt>                          │
│     <UltmtCdtr><PstlAdr>...</PstlAdr></UltmtCdtr>  (if Worldlink)           │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                ┌────────────────────┴────────────────────┐
                │                                         │
                ▼                                         ▼
   ┌──────────────────────────────┐        ┌────────────────────────────────┐
   │  CITI tree → XSLT post-proc   │        │  SEPA + CGI trees → no XSLT    │
   │                               │        │                                │
   │  CGI_XML_CT_XSLT (12 lines)   │        │  Empty structured nodes        │
   │  - Removes empty leaf nodes   │        │  emitted as-is unless          │
   │  - Identity copy otherwise    │        │  DMEE_TREE_COND explicitly     │
   │                               │        │  suppresses them               │
   │  Effect: empty structured     │        │                                │
   │  nodes auto-disappear → CITI  │        │  → V001 design must add        │
   │  V001 emits all 5 nodes       │        │  COND rules per node           │
   │  unconditionally              │        │  ('source field NE space')     │
   └──────────────────────────────┘        └────────────────────────────────┘
                │                                         │
                └────────────────────┬────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│   FILE WRITE                                                                │
│     \\hq-sapitf\SWIFT$\P01\input\aaaa_bbbb_ccxxxxxxxxyyyy.in                │
│     aaaa = company code (UNES/IIEP/UIL/...)                                 │
│     bbbb = payment method (S/N/J/L/X/...)                                   │
│     cc   = format (001=pain.001.001.02 / 002=mt101 / 003=pain.001.001.03)   │
│     xxxxxxxx = date · yyyy = sequence                                       │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│   BCM BATCH (Bank Communication Management)                                 │
│   - Routing: 100% F110+payroll via OBPM5/TFIBLMPAYBLOCK (Claim #65)         │
│   - Workflow 90000003: dual control approval                                │
│   - Signatories: PD objects OTYPE='RY' (Claim #42/43)                       │
│   - Status: IBC05 (Sent to Bank)                                            │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
                        ┌───────────────────────────┐
                        │   ALLIANCE LITE2 → SWIFT  │
                        │   → Bank (SocGen / Citi / │
                        │   CGI-routed banks)       │
                        └───────────────────────────┘
```

## Where each component sits in the flow

| # | Component | Type | Layer | Touched by V001? |
|---|---|---|---|---|
| 1 | T042Z mapping | DATA | Pre-tree config | NO |
| 2 | TFPM042FB Event 05 reg | CONFIG | Pre-tree config | YES (add SEPA row) |
| 3 | FI_PAYMEDIUM_DMEE_CGI_05 | CODE (SAP std) | Event 05 wrapper | NO (reused) |
| 4 | /CITIPMW/V3_PAYMEDIUM_DMEE_05 | CODE (SAP std) | Event 05 (CITI) | NO (reused) |
| 5 | CL_IDFI_CGI_CALL05_FACTORY | CODE (SAP std) | Country dispatcher | NO |
| 6 | CL_IDFI_CGI_CALL05_GENERIC | CODE (SAP std) | Address mapper | NO |
| 7 | CL_IDFI_CGI_CALL05_FR/DE/IT/GB | CODE (SAP std) | Country REF14 adders | NO |
| 8 | FPAYHX_FREF + FPAYP_FREF | DDIC | Buffers | NO (read by V001) |
| 9 | DMEE trees (4) | CONFIG | Tree traversal | YES (add V001 nodes) |
| 10 | DMEE_TREE_NODE | DATA | Tree structure | YES (V001 rows) |
| 11 | DMEE_TREE_COND | DATA | Emission gates | MAYBE (SEPA/CGI need empty-suppress conds) |
| 12 | YCL_IDFI_CGI_DMEE_FALLBACK | CODE (UNESCO) | BAdI in-tree | YES (Pattern A 3 lines) |
| 13 | YCL_IDFI_CGI_DMEE_FR/DE/IT | CODE (UNESCO) | BAdI in-tree | NO |
| 14 | YCL_IDFI_CGI_DMEE_UTIL | CODE (UNESCO) | BAdI helper | NO |
| 15 | YTFI_PPC_TAG / STRUC | DATA (Z) | PPC tables | NO (no rows for our countries) |
| 16 | /CITIPMW/V3_CGI_CRED_* | CODE (SAP std) | CITI per-node exits | NO |
| 17 | CGI_XML_CT_XSLT | CODE (SAP std) | XSLT post-proc | NO (only CITI uses it) |
| 18 | LFA1+ADRC vendor master | DATA | Address source | YES (5 vendor cleanup) |
| 19 | Z_DMEE_EXIT_TAX_NUMBER | CODE (UNESCO) | 1-node tax exit | NO |
| 20 | ZDMEE_EXIT_SEPA_21 | CODE (UNESCO) | 1-node batch_id exit | NO |
| 21 | T012/T012K house bank | DATA | CdtrAgt source | NO |
| 22 | BNKA bank master | DATA | CdtrAgt structured | NO |
| 23 | Workflow 90000003 | CONFIG | BCM approval | NO (out of scope) |
| 24 | OBPM5/TFIBLMPAYBLOCK | CONFIG | BCM routing | NO (out of scope) |
| 25 | TFPM042F variants (Francesco) | CONFIG | PMF variants | NO (parallel work) |
| 26 | BCM_BATCH_* BAdIs | CODE | BCM hooks | NO |
| 27 | File transmission (Alliance) | EXTERNAL | SWIFT delivery | NO |

## Total surgical change scope

**ABAP**: 1 method (YCL_IDFI_CGI_DMEE_FALLBACK_CM001::GET_CREDIT), 3 lines (Pattern A guard) — transport `D01K-BADI-FIX-01`, reviewer N_MENARD.

**CONFIG (CUSTOMIZING)**:
- TFPM042FB: +1 row for SEPA Event 05 registration (Sub-option A)
- DMEE V001 trees (~24 nodes total):
  - SEPA: +5 Dbtr structured nodes + 5 COND rules to suppress empty
  - CITI: +5 Dbtr structured nodes (XSLT auto-removes empty) + 1 UltmtCdtr StrtNm node (Q3 RESOLVED #62, claim 99)
  - CGI: **fix CdtrAgt** (PstlAdr from AdrLine to structured StrtNm/PstCd/TwnNm/Ctry, ~7 nodes)
  - CGI_1: SYNC from parent (FIRSTNODE shared, 0 manual nodes)

**DATA**: 5 vendor master cleanup (LFA1/ADRC).

**Risk: LOW**. All changes either additive (V001 new, V000 untouched), backward-compatible (Pattern A guarded), or data-only (vendor cleanup).

## Critical decisions baked into this flow

| Decision | Status |
|---|---|
| 2-file + DMEE versioning (not Hybrid single-file) | ✅ Adopted (user-directed 2026-04-24) |
| SEPA Sub-option A revised (FI_PAYMEDIUM_DMEE_CGI_05, not FVD_SEPA_OL) | ✅ Confirmed (D01 probe) |
| Pattern A BAdI fix for FALLBACK | ✅ Locked (3 lines, N_MENARD review, transport D01K-BADI-FIX-01) |
| CITI Cdtr untouched (EXIT_FUNCs already structured) | ✅ Locked |
| CGI CdtrAgt fix (Dbtr/Cdtr already structured ✓) | ✅ Locked (Plan §Per-tree design line 550) |
| UltmtCdtr Worldlink (Q3) — unified into V001 (NOT V002) | ✅ RESOLVED Session #62 (system-driven, brain claim 99) |
| XSLT empty-element auto-removal (CITI only) | ✅ Verified |
| SEPA needs explicit empty-suppress conds; CGI CdtrAgt uses TECH switch | ⚠ Action item Phase 2 |

## What is NOT in this flow (intentionally)

- Out of scope: pain.001.001.09 schema upgrade (separate project)
- Out of scope: BCM workflow modifications
- Out of scope: file naming convention changes
- Out of scope: Alliance Lite2 integration
- Out of scope: ICTP Trieste's separate trees (/SEPA_CT_ICTP_*)

## Cross-references

- Components map JSON: `knowledge/domains/Payment/phase0/components_map.json` (32 components)
- Brain claims: `brain_v2/claims/claims.json` ids 65-84 (BCM + structured-address related)
- Source code extracted: `extracted_code/FI/DMEE/` (UNESCO BAdIs) + `extracted_code/FI/DMEE_full_inventory/` (SAP std + CITIPMW + DE/IT shells + XSLT)
- Plan: `knowledge/session_plans/session_062_plan.md` + `~/.claude/plans/revisa-nuevamente-todo-hay-parsed-scone.md`
- Companion: `companions/BCM_StructuredAddressChange.html`
- Excel tracker: `Zagentexecution/incidents/xml_payment_structured_address/BCM_StructuredAddress_Analysis.xlsx`
