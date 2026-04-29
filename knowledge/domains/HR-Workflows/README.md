# HR Workflows — UNESCO Domain

**Owner role**: HR Workflow Developer Team
**Parent domain**: HCM
**Primary modules**: PD (Personnel Development), HCM, Fiori/UI5, WebDynpro ABAP, SFSF (incoming)
**Primary processes**: H2R (Hire-to-Retire)
**Status**: long-running (activity 2017-2026), **in active migration to SuccessFactors (SFSF) with target completion 2026**
**Established as named domain**: Session #60 (2026-04-22)

## Strategic context (2026)

- **Target**: migrate HR Workflows to **SuccessFactors (SFSF)** by end of 2026
- **End state**: hybrid — SFSF handles standard HR processes; UNESCO **retains some custom apps** (likely Offboarding, Family/Dependent, Benefits, Education Grant, Rental — TBD) for flows SFSF cannot cover due to UN common-system rules
- **Integration layer**: BizTalk planned per MEMORY.md (not live yet) or MuleSoft alternative — to be confirmed
- **Project team**: **the Core HR Project 2025-2026 IS the SFSF integration project**. N_MENARD (historical lead) + 4 new editors joining 2025-10 onward (S_IGUENINNI, GD_SCHELLINC, N_VIDAL, G_SONNET). 133 HR-Fiori transports in the burst.
- **Open questions**: see [KU-042 / KU-043 / KU-044](../../../brain_v2/agi/known_unknowns.json) — which apps are retained, integration architecture, employee master data source of truth post-cutover.

## Scope

HR Workflows is the UNESCO domain covering **end-user-facing HR self-service flows**: employee lifecycle approvals, benefits enrollment, offboarding, family/dependent declarations, and related workflow state machines. These live primarily in:

- **SAPUI5 / Fiori apps** (WAPP/YHR_*)
- **WebDynpro ABAP** (WDYC/WDYV)
- **ABAP classes** (CL_HRFIORI_*, CL_HCMFAB_*, ZCL_HR_FIORI_*, ZCL_ZHRF_*)
- **Workflow handlers** (WS9000xxxx, rule resolvers, custom exits)
- **Schemas/PCRs occasionally shipped as collateral** (PSCC, PCYC — bundled with larger UI releases)

## Activity timeline (HR-Fiori-filtered transports)

| Year | TRs | Distinct editors |
|---|---|---|
| 2017 | 15 | 3 |
| 2018 | 15 | 3 |
| 2019 | 33 | 3 |
| 2020 | 49 | 3 |
| 2021 | 74 | 2 |
| 2022 | 86 | 3 |
| 2023 | 21 | 2 |
| 2024 | 34 | 1 |
| 2025 | 80 | 4 |
| 2026 YTD | 53 | 6 |

The **2025-10 burst** (80 TRs by 4 editors) is the start of the **Core HR Project 2025-2026** — see below.

## Primary maintainers

### Historical (permanent) — N_MENARD

**N_MENARD** is the long-running primary maintainer. **158 HR-Fiori TRs from 2022-05-02 to 2026-03-11**, continuous across all 4 years (2022=43, 2023=20, 2024=34, 2025=47, 2026=14 YTD). He is the only editor with unbroken yearly activity in the domain.

### Core HR Project 2025-2026 (time-bound burst)

Starting 2025-10, four new editors joined N_MENARD to work on a concentrated Core HR Project:

| Editor | HR-Fiori TRs | First | Latest | Notes |
|---|---|---|---|---|
| **N_MENARD** | continuous | 2022-05-02 | 2026-03-11 | Historical lead |
| **S_IGUENINNI (Said Iguenini)** | 40 | 2025-10-29 | 2026-02-12 | New developer joined 2025-10; has 95 total TRs of which ~40 are HR-Fiori + ~55 are larger bundles with ABAP methods, data elements, web apps |
| **GD_SCHELLINC** | 16 | 2025-11-18 | 2026-03-05 | Joined 2025-11 |
| **N_VIDAL** | 6 | 2026-01-19 | 2026-03-10 | Joined 2026-01 |
| **G_SONNET** | 6 | 2026-02-24 | 2026-03-10 | Joined 2026-02 |

Also sporadic: F_GUILLOU (11 TRs in 2022 only), A_SEFIANI (6 TRs across the period, cross-domain from PY-Finance).

### About S_IGUENINNI's transports

Said's 95 transports 2025-10 → 2026-02 are large release bundles (avg 41 objects, 3,921 total object hits). Example (D01K9B0E7W, 2025-12-04, 78 objects):

- `DTED/ZE_HRFIORI_OFFBOARDING_DOC_TX` — data element texts for Offboarding
- `METH/ZCL_HRFIORI_CHANGE_SISTER` — ABAP method for Change Sister workflow
- `METH/ZCL_ZHRF_OFFBOARD_DPC_EXT` — Fiori DPC_EXT redefinitions for Offboarding
- `WAPP/YHR_BEN_ENRL` — SAPUI5 Benefits Enrollment app (component.js, controllers, 26+ i18n files)
- `PCYC/<PY cycle>` — one PY cycle dragged along
- `PSCC/<PY schema>` — one PY schema dragged along

The 8 "WT-related" classifications in session #60 PY-Finance analysis were **false positives** — the PY objects are collateral from HR workflow releases, not intentional wage type configuration. They belong here in HR-Workflows (Core HR Project 2025-2026), not in PY-Finance. See [staff_rejected_flow.md](staff_rejected_flow.md) for the canonical workflow mechanic.

## Known apps / app families

| App / Family | Purpose | Objects |
|---|---|---|
| **Offboarding (HRFIORI_OFFBOARDING)** | Employee separation workflow | ZCL_HR_FIORI_OFFBOARDING_REQ, ZCL_ZHRF_OFFBOARD_DPC_EXT, DTED/ZE_HRFIORI_OFFBOARDING_* |
| **Benefits Enrollment (YHR_BEN_ENRL)** | Self-service benefit selection | WAPP/YHR_BEN_ENRL (full UI5 stack + i18n), ZCL_ZHR_BENEFITS_REQUE_DPC_EXT |
| **Family Management (CHANGE_SISTER / FAMILY_SISTER)** | Family/dependent updates | ZCL_HRFIORI_CHANGE_SISTER, ZCL_HRFIORI_FAMILY_SISTER |
| **Rental (ZCL_HR_FIORI_RENTAL)** | Rental reimbursement | ZCL_HR_FIORI_RENTAL |
| **Education Grant (ZCL_HR_FIORI_EDUCATION_GRANT)** | Education grant requests | ZCL_HR_FIORI_EDUCATION_GRANT |
| **Secondary Dependent (ZCL_SECONDARY_DEPENDENT)** | Dependent management | UPDATE_SECONDARY_DEP method |
| **ASR Framework** | Standard SAP Adobe Service Request HR forms, redefined | CL_HCMFAB_*, CL_HRASR00GEN_SERVICE implementations |

## Cross-references

- **Parent**: [HCM](../HCM/README.md)
- **Sibling (config-owned)**: [PY-Finance](../PY-Finance/README.md) — wage type config work; Said occasionally ships PSCC/PCYC schemas bundled with HR-Workflow Fiori releases (collateral)
- **SAP Framework doc**: [HCM/asr_framework_deep_dive.md](../HCM/asr_framework_deep_dive.md)

## Governance observations (2026-04-22)

1. **100% undocumented transports for Core HR Project cohort** — Said's 95 transports 2025-10 → 2026-02 have zero E07T description text. Governance intervention candidate for the project team's release protocol.
2. **Large bundles obscure audit** — average 41 objects per transport (S_IGUENINNI) makes change-tracking expensive. Compare to Finance Tier-1 transports (5-10 objects each).
3. **PY collateral risk** — 8 of 95 Said transports ship PSCC/PCYC objects. Needs verification whether intentional or accidental.
4. **Single-editor continuity risk (historical)** — N_MENARD is the only editor with unbroken yearly HR-Workflows activity 2022-2026. The Core HR Project 2025-2026 cohort mitigates this for now but only through the project lifetime.

## Data quality items

- DQ-026: S_IGUENINNI's 95 transports 100% undocumented in E07T (already raised as DQ-023 in PY-Finance; shared issue).
- DQ-027: PY schema/PCR collateral in HR-Workflow transports — verify per-transport whether intentional.
