# SAP Transport Intelligence — Knowledge Base

## Document Registry

| # | Document | Modules | Key Content |
|---|----------|---------|-------------|
| 1 | `SAP_Transport_Intelligence_Reference.docx` | Base (1-10) | E07x anatomy, PGMID/OBJECT/OBJ_NAME triple, OBJFUNC semantics, artifact detection, logical objects, AI layer design, object-to-impact matrix |
| 2 | `SAP_Transport_Intelligence_Modules_Supplement.docx` | 11-15 | HR (wage types, payroll schemas/PCRs, OM/RHMOVE30), PSM-FM (FMDERIVE, AVC, BCS), PS (WBS vs config, settlement), Bank (DMEE, FBZP chain, OBPM4), FI/GL (T001B, T030, New GL, ledgers) |
| 3 | `SAP_Transport_Intelligence_REFX_Dunning.docx` | 16-17 | RE-FX (3 layers, account determination 5-step chain, RERAZA, cash flow), Dunning (T047 family, RE-FX dunning integration, form transport) |
| 4 | `SAP_Transport_Intelligence_Workflow.docx` | 18 | Classic WF (3 transport domains, SWU3 checklist, SWE2 linkages, agent assignment, BOR, versioning trap) |
| 5 | `SAP_Transport_Intelligence_FlexWF_InvUnblock_BCM.docx` | 19-21 | S/4HANA Flexible WF (scenario vs config split, SWFVISU), Invoice Unblock (T169G tolerances, MM vs FI blocks), BCM Payment (BNK_INI/BNK_COM, auto-approval rules, dual control) |

## Module Coverage Map

| Module | Doc # | Critical Tables |
|--------|-------|-----------------|
| HR/HCM | 2 | T512W, T511, T549A, T549Q, T554S, DECI (features) |
| PSM-FM | 2 | FMDERIVE, FMCI, FM01, T043, FMRP_CRIT |
| PS | 2 | OPST, T420, PROJ/PRPS (alarm), NROB |
| Bank/DMEE | 2 | T012/T012K, T042/T042Z, DMEE, OBPM4 |
| FI/GL | 1+2 | T030, T001B, SKA1/SKB1, T011, FAGL_SCENARIO |
| RE-FX | 3 | TIVCDCONDTYPE, TIVCDFLOWTYPE, TIVCDFLOWREL, RERAZA |
| Dunning | 3 | T047A-T047M, T047E+FORM, MHND (alarm), KNB5 |
| Workflow | 4 | PDWS, PDTS, SWETYPV, SWE2, SWWWIHEAD (alarm) |
| Flex WF | 5 | V_SWF_FLEX_SCACT, SWFVISU, SWF_FLEX_TASKFLT |
| Invoice Block | 5 | T169G, T169V, T161W, RBKP_BLOCKED (alarm) |
| BCM Payment | 5 | T042B BCM, BNK_INI, BNK_COM, BUSISB001 |

## ALARM Objects (reject transport immediately)

- `TABU RBKP_BLOCKED` — operational blocked invoice data
- `TABU MHND` — dunning history (operational)
- `TABU SWWWIHEAD` — workflow runtime work items
- `TABU PROJ / PRPS` — PS master data, not config
- `TABU VICNCN / VIOB01` — RE-FX contract/master data
- `TABU T001B` — posting period status (never via transport to PRD)

## Extracted Knowledge (machine-readable)

| # | File | Content |
|---|------|---------|
| 6 | `transport_object_taxonomy.md` | Complete object taxonomy extracted from all 5 docs — OBJFUNC, request types, impact by table per module, ALARM objects, cross-module patterns, pre-import checklist, post-transport actions, account determination chains |
| 7 | `process_discovery_research.md` | Research on 7 repos (pm4py, sap-extractor, RWTH oc-process-discovery, abaplint, Celonis, etc.) — what to copy, consolidated implementation plan, cross-layer impact |

## Usage

These documents serve as the semantic layer for the Transport Intelligence skill.
When analyzing a transport, the AI agent should:
1. Read `transport_object_taxonomy.md` first — it has ALL the extracted knowledge in one file
2. For deep detail, check the original .docx documents
3. Check cross-module pattern tables for combined signals
4. Apply pre-import checklists before recommending approval

For process discovery: read `process_discovery_research.md` — it has the consolidated plan and repo research.

Last updated: 2026-03-15
