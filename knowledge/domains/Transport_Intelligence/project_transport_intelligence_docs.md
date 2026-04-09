---
name: Transport Intelligence Document Library
description: 5 reference documents covering SAP transport semantic analysis across 21 modules (HR, PSM-FM, PS, Bank, FI/GL, RE-FX, Dunning, Workflow, Flex WF, Invoice Unblock, BCM Payment)
type: project
---

## Transport Intelligence Knowledge Base

**Location**: `knowledge/domains/Transport_Intelligence/`

### Documents (added 2026-03-15)
1. **Reference** (base, modules 1-10) — E07x anatomy, OBJFUNC, artifacts, logical objects, AI prompt patterns
2. **Modules_Supplement** (11-15) — HR payroll/PCRs, PSM-FM FMDERIVE/AVC, PS, Bank/DMEE, FI/GL
3. **REFX_Dunning** (16-17) — RE-FX 5-step account determination chain, T047 dunning family
4. **Workflow** (18) — Classic WF 3 transport domains, SWU3, SWE2, agent assignment
5. **FlexWF_InvUnblock_BCM** (19-21) — S/4HANA Flex WF, invoice tolerance T169G, BCM dual control

### Key Capability Added
- Object-to-Impact classification (CRITICAL/HIGH/MEDIUM/LOW) per object type
- Cross-module pattern triggers for rapid transport assessment
- Pre-import checklists per module
- ALARM object detection (RBKP_BLOCKED, MHND, SWWWIHEAD, PROJ/PRPS, VICNCN)
- AI prompt pattern for LLM-based transport analysis

### Integration
These docs provide the semantic layer for the `sap_transport_intelligence` skill and the CTS dashboard (7,745 transports).
