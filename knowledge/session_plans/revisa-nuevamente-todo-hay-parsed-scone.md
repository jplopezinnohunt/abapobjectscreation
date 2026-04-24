# Plan — UNESCO DMEE Structured Address Migration (CBPR+ Nov 2026)

**Date**: 2026-04-24 · **Session**: #62 · **Project**: abapobjectscreation
**Drivers**: Marlies Spronk (FIN/TRS) email 2026-04-14 + `UNESCO_BCM_StructuredAddress_AgentHandoff.docx` v1.0

---

## Context — Why this change

Banks will reject XML payment files with **only unstructured `<AdrLine>`** addresses starting **November 2026** (ISO 20022 CBPR+ mandate, enforced by SocGen / Citi / CGI member banks). UNESCO runs **3 custom DMEE trees** in P01 that currently emit Hybrid or fully Unstructured addresses. Marlies (treasury, also the historical author of 28 DMEE transports 2017-2024) has analyzed 10 real production payments, identified which tags need structuring per tree, and requested technical support to execute the change in 2026.

**The change is bank-driven** (not just regulatory) — a specific "request from the banks" per the user. Each bank's exact strictness may differ from the CBPR+ minimum (`TwnNm` + `Ctry` mandatory, rest optional under Hybrid), so per-bank spec acquisition is gate zero.

**Coexistence strategy** (user-confirmed): we run **old AdrLine-based format and new structured format in parallel** during transition — not a hard cutover. Hybrid (structured + AdrLine side-by-side) is valid CBPR+ through 2026, giving a rollback safety net and a migration buffer for vendor master data quality fixes.

**Intended outcome**: by 2026-11-01, every outgoing pain.001 from UNESCO has at minimum `<TwnNm>` + `<Ctry>` + preferably the full 5-tag structured PstlAdr in Cdtr and Dbtr blocks, with AdrLine removed or deprioritized per tree.

---

## Reference architecture — interpreted from `UNESCO_BCM_StructuredAddress_AgentHandoff.docx` v1.0

This doc is not an input among many — it is the **technical reference we execute against**. Three interpretive conclusions from reading it end-to-end shape the plan:

### Conclusion 1 — Compliance has 3 states, not 2

| State | Example | Validity after Nov 2026 | Our use |
|---|---|---|---|
| **Unstructured** | `<AdrLine>...</AdrLine><Ctry>FR</Ctry>` | REJECTED | Today's state in SEPA + CITI trees |
| **Hybrid** (min viable) | `<TwnNm>Paris</TwnNm><Ctry>FR</Ctry><AdrLine>...</AdrLine>` | OK — `TwnNm`+`Ctry` are the ONLY two mandatory, rest optional | **Minimum survival target per tree** |
| **Fully Structured** | `<StrtNm>…</StrtNm><BldgNb>…</BldgNb><PstCd>…</PstCd><TwnNm>…</TwnNm><Ctry>…</Ctry>` | OK + future-proof | Long-term target, gradual migration |

**Priority order for our work**: guarantee `TwnNm` + `Ctry` on every `<PstlAdr>` across 3 trees FIRST (= compliance survival). Then add `StrtNm`/`BldgNb`/`PstCd` (= preferred). This makes phase 2 gradual, not all-or-nothing — and matches the user directive "2 formatos que podrán coexistir".

### Conclusion 2 — Three asymmetric technical patterns by XML party

The doc's section 5 makes clear that Cdtr, Dbtr, and UltmtCdtr each require a **different mechanism**:

| Party | Data source today | Change mechanism |
|---|---|---|
| **Cdtr** (vendor) | SAP auto-populates `FPAYHX-Z*` (ZSTRA/ZHSNM/ZPSTL/ZORT1/ZLAND) from LFA1→ADRC at payment-run time | **DMEE tree configuration only** — add 5 child element nodes under `Cdtr/PstlAdr` sourced from FPAYHX Z-fields. No ABAP needed. ⚠ Depends on GAP-005 confirming the Z-field populator. |
| **Dbtr** (UNESCO) | NOT in FPAYHX or FPAYH — must be produced at runtime | **User exit ABAP** (new FM `Z_DMEE_UNESCO_DEBTOR_ADDR`) + registration in OBPM4 **Event 05** + DMEE nodes reading `FPAYH-REF01..REF05`. **Same FM registered in all 3 PMW formats** per doc recommendation. |
| **UltmtCdtr** (Worldlink only — CITI) | **UNKNOWN** per doc Q3 "confirm data source with DBS before coding" | **BLOCKED — cannot plan config until source resolved**. Candidates: vendor master, Z-table, separate user exit. |

### Conclusion 3 — 17-step checklist in doc §9 replaces inventing our own Phase 2

Handoff doc §9 is a turnkey May 2026 execution checklist: steps 1-17 covering tree confirmation, transport creation, per-tree node changes, user exit creation, OBPM4 registration, test F110 runs, XSD validation, screenshots, and release to V01. Phase 2 of this plan adopts those 17 steps directly instead of paraphrasing.

### Reference SAP Notes ranked by actionability

From doc §10 (we fetch from SAP Launchpad, not in our repo):
1. **1665873** — CGI_XML_CT full introduction guide (59 pages). **Canonical source** for the CGI tree we copy as template. First to fetch.
2. **2795667** — ISO 20022 adoption core note (SEPA harmonization).
3. **2668719** — PMW format lifecycle — relevant when modifying format versions.
4. **2819590** — CGI structured remittance gap. Doc says "check applicability" — verify via DMEE tree node inspection.
5. **2845063** — CGI IDs + org ID config.

### Open questions from doc §11 — status vs our baseline

| Doc Q# | Question | Pri | Our status |
|---|---|---|---|
| Q1 | CITI tree name DEV vs PRD | HIGH | **CLOSED** — our Session #039 P01 baseline has `/CITI/XML/UNESCO/DC_V3_01` confirmed (h18_dmee_tree_nodes.csv) |
| Q2 | CITI pain.001 variant tags (proprietary?) | HIGH | **OPEN** — depends on bank spec (Phase 1) |
| Q3 | Worldlink UltmtCdtr data source | HIGH | **OPEN + BLOCKS CITI change** — must resolve in Phase 0 or 1 before Phase 2 CITI work |
| Q4 | IIEP/UIL separate PMW assignments | MEDIUM | **OPEN** — check FBZP in Phase 1 |
| Q5 | UBO/UIS separate OBPM4 Event 05 registrations | MEDIUM | **OPEN** — check in Phase 1 |
| Q6 | Vendor master DQ count | HIGH | **OPEN** — run SQL from doc §7.2 in Phase 0 |
| Q7 | Formal bank deadline communications | MEDIUM | **OPEN** — via TRM outreach in Phase 1 |
| Q8 | SEPA into CGI consolidation | LOW | **PARKED** — post-go-live decision |

### BCM context from brain v2 — what we already know (beyond the handoff doc)

The handoff doc is DMEE-focused (left half of the F110 → DMEE → BCM → SWIFT flow). But the structured-address change flows through BCM, and the brain has material BCM context the plan must integrate:

**BCM routing — Claim #65 TIER_1** (`brain_v2/brain_state.json`):
*"BCM routing at UNESCO is triggered by tcode OBPM5 configuration (table TFIBLMPAYBLOCK, 2 rows): LAUFK=' '/P + LAUFI='*' + XBATCH='X' — wildcard routes EVERY F110 + Payroll into BCM."*
→ **Implication for the plan**: every test case in Phase 3-4 MUST run end-to-end through BCM, not just validate XML schema at DMEE output. Payment must batch, queue for approval, route to workflow 90000003, send via SWIFT. XML-schema-valid is necessary but not sufficient.

**DMEE-enabled flag — T042Z.XBKKT='X'** (brain annotation on T042Z):
Only payment methods with XBKKT='X' emit via BCM/DMEE. The structured-address change must preserve this config — any new/cloned payment method must carry the flag. Phase 1 bank_spec_matrix adds a check column for this.

**BCM signatory rules — Claim #42/43, rule `feedback_bcm_signatory_ry_otype`**:
Groups stored as PD objects OTYPE='RY' under PLVAR='01', workflow rules 90000004 (BNK_COM) / 90000005 (BNK_INI). Resolved via HRP1000 / HRP1001 / PA0002 / PA0105.
→ **Implication**: **signatory approval screens may render the payment address to the approver**. If the address format changes from hybrid to structured, approvers see new tags. Phase 3 test needs to verify the approval UI (tx BNK_APP) renders correctly for a sample BCM batch post-change.

**BCM dual-control gap — H13** (`knowledge/domains/BCM/h13_executive_summary.md` + `bcm_dual_control_audit.html`):
3,359 same-user batches ($656M), C_LOPEZ + I_MARQUAND 94.7%/92.9% self-approval. Active monitor `Zagentexecution/bcm_dual_control_monitor.py`.
→ **Implication**: extend existing H13 monitor post-cutover to track BCM reject count attributable to address changes. The plumbing is already built; reuse don't rebuild. Add this to Phase 5 monitoring.

**BCM layer BAdIs — GAP from Phase 0 inventory**:
`BCM_BATCH_ENHANCE`, `BCM_BATCH_GROUP`, `BCM_BATCH_APPROVAL`, `BCM_BATCH_STATUS`, `BCM_BATCH_SUBMISSION` — not extracted yet. These can intercept the XML post-DMEE, pre-SWIFT. If any UNESCO implementation reads/mutates address content for filtering or enhancement, our change may collide. Phase 0 GAP-006 extracts and classifies them.

**Payment E2E process mining — 1.4M events, 550K cases, 9 co codes** (`knowledge/domains/Treasury/payment_full_landscape.md`):
The event log (`Zagentexecution/process_mining/payment_event_log.csv` if present or to re-extract) gives us realistic distribution of vendors/countries/currencies/payment methods used in production. Test matrix priority stratification should be data-driven from this, not synthetic.
→ **Implication**: Phase 3 test matrix tier-1 selection driven by top-frequency cases from process mining, not arbitrary picks.

**Active BCM incidents touching signatory/workflow**:
- **INC-000006313** (UIS BCM add VOFFAL signatory, ghost PERNR 10567156 resolved session #051+)
- Rule `feedback_bcm_ghost_pernr_check` — active DQ check at session start for BCM signatory reconciliation
→ **Implication**: if any test case involves a UIS payment, run the ghost-PERNR check pre-test (`python Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py`).

**payment_bcm_companion.html v4 — 13 tabs**: contains authoritative BCM Config tab (YS/YT variants, BCM_MERGE_PAY/BCM_MON_APP/etc.), Roles & Auth tab, WF Architecture tab. We do NOT rebuild this companion; we link from `BCM_StructuredAddressChange.html` to it as the BCM-wide reference.

**21 SAP Notes for BCM catalogued in `.agents/skills/sap_payment_bcm_agent/SKILL.md`**:
Beyond the 5 from the handoff doc, 21 BCM-specific notes are documented. Phase 0 cross-reference those against the handoff list to see if any are directly relevant to structured address and we're missing them.

**4 payment processes mapped in sap_payment_bcm_agent**:
Process 3+4 = F110+BCM+DMEE file generation (in scope). Processes 1+2 may route via different config. Phase 1 confirms which trees each of 4 processes uses.

### Implications for future change decisions (beyond this one change)

Consolidating what brain tells us about the BCM stack — this plan is ONE change in a bigger picture. Future decisions shaped by the brain:

1. **Any BAdI we create (e.g. `Z_DMEE_UNESCO_DEBTOR_ADDR`) should be BCM-aware**: read `T001-ADRNR` via `BAPI_COMPANYCODE_GETDETAIL` per SAP Community pattern. Preserve compatibility with future BCM enhancements (structured vendor name, CtctDtls email, etc.).
2. **If a future change needs preventive address validation**: follow the H39 pattern (separate BAdI, not DMEE config) — brain has this documented as the correct architecture for cross-cutting validation.
3. **Vendor master cleanup is cross-cutting**: the DQ audit in Phase 0 feeds multiple tracks (structured address, BR substitution H39, carry-forward 2026, future MDM efforts). Output belongs in the shared knowledge base, not buried in this project.
4. **Coexistence strategy (Hybrid transition)** extends to future format changes too: any future migration (pain.001.001.09, new countries, new UltmtCdtr tags) should default to additive/coexistence, not replacement.
5. **Signatory workflow immutability during this change**: we change what gets rendered to approvers but not how they approve. Any touch to workflow 90000003 is out of scope and requires a separate change decision with H13 implications considered.

### Brain ↔ Plan feedback loop (bidireccional)

El proyecto tiene un brain v2 que conoce 246 objetos, 93 rules, 65 claims, 8 incidentes, 14 domains. **Usarlo es obligatorio**, no opcional. Y cualquier nuevo descubrimiento se vuelve a inyectar para que el brain crezca.

#### Brain → Plan (enrichment, ya hecho en este plan)

Todo lo que el plan extrae del brain con cita explícita:

| Del brain | Cómo enriqueció el plan |
|---|---|
| Claim #65 TIER_1 OBPM5/TFIBLMPAYBLOCK routing | Phase 3 testing ahora es E2E F110→DMEE→BCM→SWIFT, no solo XSD validation |
| Claim #42/43 BCM signatory rules OTYPE='RY' | Phase 3 valida BNK_APP approval UI para ver si approvers ven tags structured vs AdrLine |
| H13 dual-control artifacts | Phase 5 monitoring reusa `bcm_dual_control_monitor.py` — no se reinventa |
| `feedback_bcm_ghost_pernr_check` | Pre-test UIS casos corre `bcm_signatory_reconciliation_check.py` |
| `feedback_only_p01_for_config_analysis` #204 | Gate: toda config decision anclada en P01 baseline, D01 solo para draft detection |
| Session #039 baseline (H18) | Tree names verificados, cerró Q1 del handoff doc automáticamente |
| Session #038 YWFI extraction | YCL_IDFI_CGI_DMEE_FR/FALLBACK/UTIL source disponible para regression check |
| CTS 10-year snapshot | Marlies's 28 transports + Francesco's 5 transports identificados sin nueva extracción |
| Payment E2E mining (1.4M events) | Test matrix tier-1 data-driven (vendors/países reales), no sintético |
| `payment_bcm_companion.html v4` | Linkable, no rebuild — reusable BCM-wide reference |
| Domain docs `bcm_signatory_rules.md` + `xref_office_tagging_model.md` | BCM layer context para user exit design |

#### Plan → Brain (feedback, post-ejecución)

Cada Phase produce **artefactos que se inyectan al brain**. Lo declaro explícito acá para que no se pierda en el session close:

**Post Phase 0 — 100% code inventory closure**:
- **Nuevos objetos first-class**: ADRC, ADR2, ADR3, FPAYH, FPAYHX (resolvidos de blind_spots a objects). CI_FPAYHX append structure. AE/BH classes si existen en P01. BAdI populator de Z-fields (GAP-005). SAPLFPAY_EVENTS handlers (GAP-002).
- **Nuevas annotations**: por cada objeto, la annotation "role in XML payment generation" con evidence tier TIER_1/2/3.
- **Nuevas claims**:
  - Claim candidato: *"At UNESCO P01 the FPAYHX Z-fields (ZSTRA/ZHSNM/ZPSTL/ZORT1/ZLAND) are populated by [FM name from GAP-005]"* — TIER_1 after extraction
  - Claim candidato: *"YCL_IDFI_CGI_DMEE_AE / _BH [exist|do not exist] in P01 TADIR as of YYYY-MM-DD"* — TIER_1, resolves Session #038 H4 partial
- **Nuevas feedback rules candidatas**:
  - `feedback_structured_addr_hybrid_is_default_transition` — "When migrating an XML payment format to ISO 20022 structured address, default to Hybrid (TwnNm+Ctry mandatory + AdrLine fallback) unless bank spec demands fully-structured. Rationale: vendor master DQ is never 100%."
  - `feedback_structured_addr_three_asymmetric_patterns` — "Cdtr via DMEE config only (FPAYHX auto-populated), Dbtr via user exit + OBPM4 Event 05 + FPAYH-REF01..05, UltmtCdtr requires explicit data source decision."
  - `feedback_dmee_one_fm_three_pmw` — "A user exit FM for DMEE can be registered in multiple PMW formats via OBPM4 simultaneously. Write once, reuse. Avoid per-format FM duplication."
- **KUs resuelven**: Q1-Q8 del handoff doc convertidas a KU objects + closure evidence cuando resuelvan.

**Post Phase 1 — Config matrix + bank specs**:
- **Nueva claim**: *"Bank [X] at UNESCO pain.001 strictness = [Fully Structured | Hybrid minimum]"* per bank — TIER_1 con source = TRM written confirmation
- **Francesco audit**: 5 transports FP_SPEZZANO 2025 clasificados BLOCK/ASSIST/IRRELEVANT — nueva data_quality / known_unknown entry
- **Data quality claim**: *"N% of active UNESCO vendors missing CITY1 or COUNTRY in ADRC as of YYYY-MM-DD"* — baseline metric
- **M_SPRONK** promocionada como objeto first-class tipo `PERSON / DOMAIN_EXPERT` con annotation "authored 28 DMEE transports 2017-2024, historical config owner" (ya vimos en audit, formalizarlo)

**Post Phase 2 — Config D01**:
- **Nuevos transports**: TRKORRs de los 17 steps del checklist → feed `brain_v2/cts/` + claims con release dates
- **Source code extracted**: `Z_DMEE_UNESCO_DEBTOR_ADDR` → `extracted_code/FI/DMEE/`
- **Nueva annotation** en tree objects: "as of YYYY-MM-DD, structured address tier [A|B|C] implemented on [Dbtr|Cdtr|UltmtCdtr] via transport [TRKORR]"

**Post Phase 3-4 — Unit + UAT**:
- **Falsification predictions**: cada bank spec → predicción verificable post-pilot. *"Structured address file X will be accepted by bank Y"* → verified PASSED / FAILED.
- **New claims**: bank-by-bank acceptance status

**Post Phase 5 — Go-live**:
- **Incidents record** (si hay): como INC- entries en `brain_v2/incidents/incidents.json`
- **Closure annotation** en cada tree: "compliance state = [Fully Structured | Hybrid | Unstructured] as of 2026-11-01"
- **Retro feedback**: lessons learned → nuevas feedback rules

#### Mecanismo concreto de inyección

- **Rebuild script**: `python brain_v2/rebuild_all.py` al cierre de cada Phase — regenera `brain_state.json` desde los source-of-truth JSONs
- **Single-commit rule**: el mismo commit que ships un Phase deliverable DEBE incluir los updates a `brain_v2/annotations/annotations.json`, `claims/claims.json`, `incidents/incidents.json`, `agent_rules/feedback_rules.json` cuando aplica
- **CP-001 applied**: nunca compresión destructiva — agregamos, no consolidamos
- **Tab 2 del companion** ("The Plan live") se regenera cada vez que el brain recibe feedback — el companion refleja el estado actual del brain sobre este change

### What this reference architecture changes in our plan

- **Phase 0 GAP-005 closure is mandatory** — without identifying the FPAYHX Z-field populator we can't design the Cdtr change per doc §5.1
- **Phase 2 adopts handoff §9 17-step checklist verbatim** — no reinvention
- **Hybrid (TwnNm+Ctry minimum) becomes the default transition state**, fully-structured becomes the aspiration target per tree based on bank spec
- **UltmtCdtr CITI is gated on Q3 resolution** — it cannot start until Phase 1 determines data source
- **User exit FM is written ONCE** and registered 3× in OBPM4 — scope reduction vs my original per-tree approach
- **SAP Note 1665873** becomes the must-read for Phase 0/1

---

## Scope — 3 trees, 3 compliance states, asymmetric change patterns

| Tree (P01 verified Session #039) | Bank | Users | Current state (Marlies Excel) | Target |
|---|---|---|---|---|
| `/SEPA_CT_UNES` (95 nodes) | Société Générale EUR | UNES HQ, IIEP, UIL | Dbtr **Hybrid**, Cdtr **Hybrid** — postal code missing | Structured Dbtr + Cdtr (template = CGI). Hybrid acceptable transition. |
| `/CITI/XML/UNESCO/DC_V3_01` (~610 nodes) | Citibank USD + Worldlink TND/MGA/BRL | UNES HQ, UBO, UIS | Dbtr **Unstructured** (no Ctry!), Cdtr mostly Structured, **UltmtCdtr** WHO/ICC special case Hybrid | Fix Dbtr (add Ctry + restructure), handle UltmtCdtr Worldlink beneficiaries |
| `/CGI_XML_CT_UNESCO` + `/CGI_XML_CT_UNESCO_1` (631+639 P01 / 1262+1264 D01) | All other (SocGen non-SEPA, Shinhan KR, Metro GB, GT NG) | UNES + others | Dbtr **Structured** ✅ (TEMPLATE), Cdtr **Structured** ✅, CdtrAgt **Unstructured** | Fix CdtrAgt only. D01 drafts require purge/merge decision. |

**Insight**: CGI's Dbtr is already the target structure. **We lift CGI's Dbtr pattern to SEPA + CITI** rather than design from scratch.

---

## Phase 0 — 100% Code Inventory Closure (BLOCKER for any work below)

**Driver** (user directive 2026-04-24): "Tenemos que identificar el 100% para saber dónde se hace el cambio o los cambios." Until we know EVERY code point that shapes XML payment output, we cannot design where the structured-address change happens. The Phase 1 Explore pass identified 8 material gaps. Phase 0 closes each.

### The 8 gaps to close (identified in Phase 1 Explore)

| ID | What | Why it blocks "where does the change happen" | Closure method |
|---|---|---|---|
| **GAP-001** | **YRGGBS00 substitution rule logic** (H48 carryover) | If a substitution writes `BSEG-XREFn` or `BSEG-SGTXT` and a DMEE tree reads BSEG directly, changing the tree without knowing the sub rule fires wrongly | Extract substitution steps via pyrfc: GB01/GB03/GB04 tables + YRGGBS00 source via RPY_PROGRAM_READ. Trace which BSEG fields it writes. |
| **GAP-002** | **SAPLFPAY_EVENTS / FPAY_EVENT_05 handler** | Event 05 post-processes FPAYH BEFORE DMEE renders. UNESCO may have custom logic there that the handoff doc didn't map. Without it, our own Z_DMEE_UNESCO_DEBTOR_ADDR may collide. | Grep TADIR in P01 for SAPLFPAY_* + FPAY_EVENT_* + Y_FPAY_* + Z_FPAY_*. Extract any UNESCO customization. |
| **GAP-003** | **YCL_IDFI_CGI_DMEE_AE / _BH** existence in P01 | Session #038 falsified their presence in D01 but never confirmed P01 status. If they exist in P01, they handle UAE/Bahrain payment address formatting differently and must be in scope. | `RFC_READ_TABLE` on TADIR in P01, OBJECT='CLAS', OBJ_NAME='YCL_IDFI_CGI_DMEE_AE' / '_BH'. If present, `RPY_CLASS_READ`. |
| **GAP-004** | **CI_FPAYHX append structure full schema** | We know 5 Z-fields (ZSTRA/ZHSNM/ZPSTL/ZORT1/ZLAND) from handoff. There may be more (ZLAND_ISO, ZCTRY_SUB, etc.) we've never seen. Unknown fields = unknown mutation surface. | Extract DD03L for FPAYHX + resolve CI_FPAYHX include via DDIF_FIELDINFO_GET. Get ALL Z-fields with their data elements and domains. |
| **GAP-005** ⚠️ | **THE BAdI that populates FPAYHX Z-fields at F110 runtime** | **THIS IS THE CRITICAL UNKNOWN.** The structured-address change has to happen AT THE POINT where ZSTRA gets its value. If that point today reads `LFA1-STRAS` (free-text) we need to change it to parse `ADRC-STREET` + `ADRC-HOUSE_NUM1` separately. Without finding this BAdI, we might edit the DMEE tree thinking that fixes everything while the real bug is upstream. | Trace: grep extracted_code for `FPAYHX-Z` writes. Check OBPM4 Events 04/05/06 registered FMs. Check BAdI `FI_PAYMENT_MEDIUM` variants. Verify via SE19 in D01 what enhancement impls are active on payment medium creation. |
| **GAP-006** | **EXIT_FUNC column distribution across 8,309 DMEE nodes** | Each node with a non-empty `EXIT_FUNC` is its own mutation point. If an address node has an EXIT_FUNC and we change the tree but not the FM behind it, we break. | Parse `knowledge/domains/Payment/h18_dmee_tree_nodes.csv` columns. Bucket by tree + EXIT_FUNC. List all FMs referenced; extract any Y/Z FMs not already known. |
| **GAP-007** | **Post-DMEE file transmission code** (naming, directory, Alliance Lite2 integration) | The XML output goes through `\\hq-sapitf\SWIFT$\P01\input\` with a naming scheme. If there is a Z-program transforming/renaming/validating the file post-DMEE, it's another code point. | Grep P01 TADIR for `SWIFT`, `ALLIANCE`, `FPAYM` programs + SM69 external commands. Check ICF services. |
| **GAP-008** | **T042Z/E/I runtime selection logic** | Confirm that per-payment the correct tree is selected dynamically — no hardcoded overrides we're unaware of. | Read T042Z/E/I from P01 + trace via FPAYH-ZFORMI at runtime (debug F110 run if needed, or trust handoff). |

### Phase 0 deliverables

1. **`knowledge/domains/Payment/gap_closure_report.md`** — per-gap: status (CLOSED / PARTIAL / BLOCKED), findings, source citations, remaining unknowns
2. **`extracted_code/FI/DMEE_full_inventory/`** — every new extracted object per gap (AE/BH classes if found, Event 05 handlers, Z-field populator BAdI, etc.)
3. **`knowledge/domains/Payment/xml_touch_points_complete.md`** — definitive inventory of ALL code points that affect XML, with:
   - Entity · Type · Path · Invocation trigger · Tag(s) affected · Change required (Yes/No/Maybe)
   - Grouped by payment lifecycle stage: vendor-master read → F110 selection → FPAYHX population → OBPM4 events → DMEE tree traversal → node EXIT_FUNC calls → post-DMEE file handling → BCM batch → SWIFT
4. **Updated brain v2**: all newly discovered entities registered as first-class objects under Payment domain
5. **Go/No-Go decision**: after Phase 0, formal sign-off that **we know 100% where the change must happen**. If any gap remains BLOCKED (e.g., a BAdI we can't extract), that becomes a **named risk** in the plan and we decide to proceed, scope it out, or escalate.

### Phase 0 exit gate

Pablo + Marlies joint review of `xml_touch_points_complete.md`. No "UNKNOWN" in the "Change required" column. Any "Maybe" has a named test case in Phase 3 that will resolve it.

### Phase 0 duration estimate

3-4 working days. Runs in parallel with bank spec gathering (which has its own 7-day window). **Phase 0 does not delay Marlies's May config start** because Phase 1 (change matrix) depends on Phase 0 output but both finish by 2026-04-30.

### Phase 0 risks

- **GAP-005 may not close from static analysis alone**. The BAdI that populates Z-fields may only be visible via runtime trace (ST05) on F110. **Mitigation**: if 48h of static search doesn't find it, book a 30-min F110 debug session in D01 with Marlies running a real payment.
- **P01 TADIR extraction** requires SNC/SSO session active. **Mitigation**: schedule around VPN / refresh Kerberos ticket (`klist purge` + Win+L unlock per memory reference).
- **Scope creep** — the 100% inventory could surface 20 more BAdIs tangentially related. **Mitigation**: rigid filter: "does this object read or write to the XML output path from F110 to SWIFT file?" — if no, park it.

---

## Phase 1 — Config matrix + bank specs (2026-04-27 → 2026-04-30, depends on Phase 0)

### Deliverables

1. **`knowledge/domains/Payment/baselines/2026-04-30_P01/`** — frozen snapshot of 7 DMEE tables for 3 trees, via extended `Zagentexecution/mcp-backend-server-python/h18_dmee_tree_probe.py`. Tables: DMEE_TREES, DMEE_TREE_NODES, DMEE_NODE_SRC_ATTR, DMEE_NODE_COND, DMEE_NODE_TGT_ATTR, DMEE_NODE_CUST_EXIT, DMEE_NODE_ELEM. Git-committed.
2. **`knowledge/domains/Payment/francesco_audit.md`** — per-transport audit of 5 FP_SPEZZANO 2025 DMEE transports (from `Zagentexecution/mcp-backend-server-python/cts_batch_2025.json`). Each classified BLOCK / ASSIST / IRRELEVANT (user directive: "audit as context, don't assume pattern").
3. **`knowledge/domains/Payment/bank_spec_matrix.md`** — per-bank requirement matrix (SocGen / Citi / CGI). TRM calls scheduled week 1 May with Marlies.
4. **`knowledge/domains/Payment/change_matrix.csv`** — target state per node (schema below), filled from Marlies's Excel + handoff doc + P01 baseline + bank specs.
5. **Vendor master data-quality audit** — SQL per handoff §7.2, query LFA1+ADRC for active vendors missing CITY1 or COUNTRY. Count + vendor list. Critical pre-req before Phase 3.
6. **Brain v2 updates** — new first-class objects: ADRC, ADR2, ADR3, FPAYH, FPAYHX (currently blind spots). Annotations linking each tree to the incident.
7. **`Zagentexecution/incidents/xml_payment_structured_address/README.md`** — incident home with the full trail of artifacts.

### Change matrix schema (`change_matrix.csv`)

```
tree_id | parent_path | node_id | tech_name | action (ADD/MOD/DEL/KEEP) | 
current_src_type | current_src_val | current_cond | 
target_src_type | target_src_val | target_cond | 
bank_spec_ref | marlies_excel_ref | handoff_doc_ref | 
transport_id | test_case_ids | test_status | approval_by | approval_date
```

### Francesco audit procedure

For each of 5 FP_SPEZZANO 2025 transports (most recent `D01K9B0CZ0` 2025-03-20 on `/CGI_XML_CT_UNESCO`):
- Extract `obj_list` from `cts_batch_2025.json`
- Map objects to DMEE table targets (TREES/NODES/etc.)
- Classify: **BLOCK** (touches Dbtr/Cdtr/CdtrAgt/UltmtCdtr address subtree), **ASSIST** (scaffolding for address work), **IRRELEVANT** (other parts of the tree)
- For BLOCK+ASSIST: read transport objects, compare against P01 baseline, flag conflict surfaces
- Output `francesco_audit.md` with verdict + evidence per transport

### Bank spec sub-plan

| Bank | Channel | Contact path | Ask | Deadline |
|---|---|---|---|---|
| Société Générale | SEPA + Non-SEPA CGI | Marlies's SocGen TRM | pain.001.001.09 SG implementation guide + structured address strictness (fully structured required? hybrid acceptable?) | 2026-04-30 |
| Citibank | DC_V3_01 + Worldlink | Marlies's Citi TRM via CitiConnect | DC_V3 CBPR+ addendum + per-currency rules TND/MGA/BRL + UltmtCdtr Worldlink beneficiary policy | 2026-04-30 |
| CGI banks (Shinhan KR, Metro GB, GT NG) | via SocGen CGI network | TRM per bank via Marlies | CGI-MP pain.001 supplement + per-country PstCd/TwnNm strictness | 2026-05-05 |
| SAP | Platform | SAP for Me / Launchpad | Notes **2795667** (SEPA ISO), **2668719** (PMW lifecycle), **2819590** (CGI remittance), **1665873** (CGI_XML_CT 59-page guide), **2845063** (CGI IDs), **2944738** (pain.001.001.09), **3208888** (CBPR+ structured) | Pablo fetches 2026-04-28 |

### Success criteria

- Baseline replayable via `h18_dmee_tree_probe.py`
- All 5 Francesco transports classified
- Bank specs received from at least SocGen + Citi
- `change_matrix.csv` has **0 UNKNOWN** target fields per node
- Vendor DQ count < 5% missing-mandatory; remediation plan exists for those

### Exit gate

Pablo + Marlies joint sign-off on `change_matrix.csv` + `bank_spec_matrix.md` before any D01 touch.

---

## Phase 2 — May 2026 Config in D01 (SEPA → Citi → CGI)

### Approach — coexistence-first

Per user directive, **we don't delete AdrLine at day 1**. We add structured nodes IN PARALLEL to AdrLine (Hybrid), validate, then phase out AdrLine tree-by-tree once bank confirms. This gives:
- Rollback = disable the structured branch via condition, AdrLine already there
- Buffer for vendor master data cleanup
- Gradual visibility to the business

### Per-tree transport sequencing — adopts handoff doc §9 17-step checklist verbatim

We execute the 17-step checklist from `UNESCO_BCM_StructuredAddress_AgentHandoff.docx` §9 as-is. Each step becomes a row in `change_matrix.csv` with owner, transport, date, evidence:

| # | Task | T-code | Owner | Depends on |
|---|---|---|---|---|
| 1 | Confirm DMEE tree names for SEPA, CITI, CGI in DEV | DMEE | Pablo | **Already CLOSED** by Session #039 baseline |
| 2 | Create DEV transport request for all DMEE changes | SE09 | Pablo | Step 1 |
| 3 | SEPA: Add/update Cdtr PstlAdr structured nodes (FPAYHX mapping) | DMEE | Pablo | GAP-005 closed |
| 4 | SEPA: Deactivate AdrLine nodes under Cdtr PstlAdr (or leave for Hybrid transitional) | DMEE | Pablo | Step 3 + bank spec |
| 5 | SEPA: Add Dbtr PstlAdr structured nodes (REF field mapping) | DMEE | Pablo | Step 9 (user exit live first) |
| 6 | CITI: Add/update Cdtr PstlAdr structured nodes | DMEE | Pablo | Step 3 pattern, GAP-005 closed |
| 7 | CITI: Add/update UltmtCdtr PstlAdr structured nodes (Worldlink) | DMEE | Pablo + DBS | **BLOCKED by Q3** until data source resolved |
| 8 | CGI: Add/update Cdtr PstlAdr structured nodes (+ fix CdtrAgt per Marlies Excel) | DMEE | Pablo | Steps 3+6 pattern |
| 9 | Create user exit FM `Z_DMEE_UNESCO_DEBTOR_ADDR` for UNESCO debtor address | SE37 | Pablo | Phase 0 complete |
| 10 | Register debtor FM in OBPM4 Event 05 for **all 3 PMW formats** (one FM, three registrations — doc recommendation) | OBPM4 | Pablo | Step 9 |
| 11 | Verify PMW format → DMEE tree links are correct | OBPM1 | Pablo | Steps 3-10 |
| 12 | Run test F110 in DEV — SEPA format, inspect XML output | F110 | Pablo + Marlies | Steps 3-5, 9-10 |
| 13 | Run test F110 in DEV — CITI format, inspect XML output | F110 | Pablo + Marlies | Steps 6-8, 9-10 |
| 14 | Run test F110 in DEV — CGI format, inspect XML output | F110 | Pablo + Marlies | Step 8, 9-10 |
| 15 | Validate XML schema of output files against pain.001.001.03 XSD | External | Pablo | Steps 12-14 |
| 16 | Document DMEE tree changes — before/after screenshots per tree | N/A | Pablo | Steps 3-8 |
| 17 | Release transport to V01 / QA | SE10 | Basis | Step 15 |

**Sequencing note**: Steps 3 (SEPA Cdtr), 6 (CITI Cdtr), 8 (CGI Cdtr) can run in parallel once GAP-005 is closed. Step 9 (user exit) is the gate for steps 5, 7, and Dbtr work. Step 7 (CITI UltmtCdtr) is the only one blocked on an unresolved Q (Q3 data source) — scope it last or carve out to a separate transport if Q3 resolution takes time.

### Priority stratification — Hybrid-minimum first, Structured-preferred second

Per reference architecture conclusion 1 (TwnNm+Ctry is the only mandatory pair):

**Tier A (compliance survival — do first, week 1)**: ensure every `<PstlAdr>` in the 3 trees emits `<TwnNm>` + `<Ctry>` unconditionally. Even for the CGI Dbtr treasury-transfer case that currently has only `<Ctry>FR</Ctry>` (Marlies Excel row 10), we add TwnNm. No AdrLine change yet.

**Tier B (preferred structured — week 2-3)**: add StrtNm, BldgNb, PstCd. AdrLine kept with "suppress if populated" condition for Hybrid fallback on vendors with incomplete data.

**Tier C (cleanup — week 4, post bank spec confirmation)**: per-bank, decide whether to fully deprecate AdrLine or keep Hybrid indefinitely. Depends on bank spec strictness from Phase 1.

### User exit for UNESCO Dbtr address (handoff §5.2 — mandatory)

Per handoff doc, Dbtr (UNESCO company address) is **NOT in FPAYHX/FPAYH** — needs custom FM.

- **FM**: `Z_DMEE_UNESCO_DEBTOR_ADDR` (new)
- **Logic**: `SELECT SINGLE * FROM ADRC WHERE ADDRNUMBER = (SELECT ADRNR FROM T001 WHERE BUKRS = I_FPAYH-ZBUKR)` → populate E_FPAYH-REF01..05 with STREET / HOUSE_NUM1 / POST_CODE1 / CITY1 / COUNTRY
- **Registration**: OBPM4 Event 05 for all 3 PMW formats (SEPA, CITI, CGI)
- **Reuse**: same FM for all 3 formats per handoff recommendation
- **Traceability**: new class/FM under `extracted_code/FI/DMEE/` after write; transport `D01K-FMFI-001`

### Per-transport deliverables

- `change_log.md` with node-by-node before/after
- Sample XML generated from DMEE simulation mode, diffed against Marlies Tab 2 target
- Reviewer sign-off (Marlies) before progression to next tree

### Exit gate

Each tree's transport reviewed + signed by Marlies before next tree config starts.

---

## Phase 3 — June 2026 Unit Test in D01/V01

### Test matrix (`test_matrix.csv`)

**Dimensions**: 3 trees × vendor archetypes (Domestic / Foreign / PO-Box / Long-name>35 / Diacritic / Individual-STCD2) × countries (FR, US, GB, KR, NG, BR, MG, TN) × edge cases (street>35, city>35, missing PstCd, null Ctry, Arabic chars).

**Priority tier 1**: ~50 cases (all 3 trees × 6 vendors × 3 countries + handoff UT-01..08 mandatory)
**Full grid**: ~144 cases

**Schema validation layer**: automated diff against pain.001.001.09 XSD + bank-specific XSDs (SocGen, Citi).

### BAdI regression

Verify `YCL_IDFI_CGI_DMEE_FALLBACK_CM001.abap:13-31` (35-char StrtNm overflow from Cdtr.Nm) behavior in structured mode — either still triggers appropriately or is documented as dead. Don't let a 2-decade-old overflow handler silently break new structured output.

### Success criteria

- 100% XSD pass rate on tier-1 cases
- Zero regressions vs P01 baseline for payments that already work
- Hybrid coexistence verified: tree emits structured AND AdrLine when vendor master has both; emits structured only when complete; emits AdrLine fallback when vendor incomplete

### Exit gate

Pablo + Marlies + DBS sign `test_results_june.md`.

---

## Phase 4 — July 2026 UAT in V01

### Deliverables

- **Per-bank pilot file** sent to SocGen + Citi + CGI banks for acceptance validation at their gateway (not just schema-valid)
- UAT scenarios per handoff §8.2 (UAT-01 to UAT-12), validated by: Finance/Treasury, HRM (Worldlink TND/MGA), UBO/UIS/IIEP/UIL entity owners
- Bank acknowledgment emails archived

### Success criteria

All 3 banks (+ CGI-routed banks) return written confirmation that structured address is accepted at their gateway (not just schema-valid at XSD level).

### Exit gate

Treasury head + all 4 entity finance leads sign UAT close-out.

---

## Phase 5 — August–November 2026 Deploy & Monitor

### Cutover order

**CGI first** (narrowest change = CdtrAgt only, low business impact) → **SEPA** (medium) → **CITI last** (highest volume, Ctry fix touches every Worldlink currency). Staggered 2-week windows.

### Rollback strategy (per tree, 3 layers)

1. **Transport revert** — prior TR is TOC-able via DBS, revert DMEE_TREE_NODES to P-1 state
2. **Config revert** — T042Z/T042E/T042I changes captured in transports, same revert path
3. **Code revert** — git tag `baseline-pre-phase2-2026-04-30` on `extracted_code/FI/DMEE/` + ABAP transport of prior class version

**Rollback trigger**: >2 bank rejects in 24h post-cutover **OR** schema validation failure rate >1%.

### Post-go-live monitoring

Daily BCM batch reject count per tree for 30 days post-each-cutover. Dashboard: extend `companions/payment_bcm_companion.html` with a rejections tab.

### Exit criteria

Nov 2026 CBPR+ deadline met; all 3 trees emit compliant address format; zero address-attributable rejects for 14 days straight.

---

## Companion HTML — Single Source of Truth (user directive)

**File**: `companions/BCM_StructuredAddressChange.html` · versioned v1 (end Phase 0), v2 (end Phase 1), v3 (mid Phase 2), etc.
**Pattern**: reuse styling of existing `companions/payment_bcm_companion.html` (dark theme, tab-based, self-contained single HTML).
**Rule**: everything relevant to this change lives here. **The plan in this file is reproduced inside the companion**. When the plan changes, the companion's Plan tab changes in the same commit.

### Tabs (each is its own section, all cross-linked)

| # | Tab | Content | Updated at |
|---|---|---|---|
| 1 | **Overview** | Why this change (bank-driven + CBPR+ Nov 2026), deadline, 3-states compliance model, coexistence strategy | Phase 0 |
| 2 | **The Plan (live)** | **This exact plan file rendered in the companion**. Phases 0-5 with status, current blockers, next steps. Updated every session that advances the project. | Every phase gate |
| 3 | **Reference Architecture** | Interpretation of handoff doc v1.0 — 3 compliance states, 3 asymmetric patterns (Cdtr/Dbtr/UltmtCdtr), 17-step checklist §9 verbatim | Phase 0 |
| 4 | **The 3 Trees** | Current state per Marlies Excel (10 cases) + target state + node-level diff. One subtab per tree. | Phase 0 |
| 5 | **Change Matrix** | Interactive table sourced from `change_matrix.csv` (every node × action × transport × test status) | Phase 1 → all phases |
| 6 | **XML Before/After** | Side-by-side XML samples per party (Dbtr/Cdtr/UltmtCdtr) per tree, from Marlies Excel + handoff doc §2.1 | Phase 0 |
| 7 | **SAP Architecture** | F110 → FBZP → OBPM1 → DMEE → OBPM4 Event 05 → BCM → SWIFT flow. Adapted from handoff §4.1 + Session #039 findings | Phase 0 |
| 8 | **Code Inventory (100%)** | Output of Phase 0 — every code point that touches the XML, classified: DMEE tree / BAdI class / user exit / event FM / substitution rule / file transmission code. One row per asset. Gap status per GAP-001..008. | Phase 0 |
| 9 | **User Exit** | `Z_DMEE_UNESCO_DEBTOR_ADDR` source (from handoff §5.2 + extracted after Phase 2 Step 9), OBPM4 Event 05 registration, REF field mapping, test invocations | Phase 2 |
| 10 | **Test Matrix** | Test cases from handoff §8.1 (UT-01..08) + §8.2 (UAT-01..12). Pass/fail dashboard after Phase 3-4. | Phase 3+ |
| 11 | **Transport Plan** | TRKORR list per 17-step task with status, owner, date, release path D01→V01→P01 | Phase 2+ |
| 12 | **Francesco Audit** | 5 FP_SPEZZANO 2025 transports, classified BLOCK/ASSIST/IRRELEVANT (per user directive: audit as context, don't assume pattern) | Phase 0 |
| 13 | **Vendor Master DQ** | Count of non-compliant vendors per handoff §7.2 SQL. Remediation plan. Re-count at each phase. | Phase 0 + refresh |
| 14 | **Q1-Q8 Status** | Open questions from handoff §11 with status (CLOSED/OPEN/BLOCKED) + resolution owner | Phase 0 → resolved one-by-one |
| 15 | **Timeline** | Gantt of 5 phases with real dates + milestones (bank spec received, GAP-005 closed, etc.) | Every phase |
| 16 | **References** | See below — exhaustive list | Phase 0 + any new refs added |

### Tab 16 — References (exhaustive, evidence-only)

Grouped by source type. Every reference cited somewhere in the plan or analysis appears here with path/URL + what we use it for.

**A. UNESCO-internal documents (user-provided, primary inputs)**
- `Zagentexecution/incidents/xml_payment_structured_address/original_marlies/XML Address un structured.xlsx` — Marlies Spronk's tag analysis: 10 production payments in tab 1 + SEPA target proposal in tab 2
- `Zagentexecution/incidents/xml_payment_structured_address/original_marlies/body.txt` — Marlies's original email 2026-04-14 18:06 UTC+2
- `Zagentexecution/incidents/xml_payment_structured_address/body.txt` — the follow-up Re: thread body
- `C:/Users/jp_lopez/Downloads/UNESCO_BCM_StructuredAddress_AgentHandoff.docx` — **the reference architecture document**, v1.0, April 2026. All 14 tables + Sections 2, 4, 5, 6, 7, 9, 10 of it are the primary technical reference. Any deviation from this doc is flagged explicitly

**B. UNESCO-internal baselines (project-extracted, verified)**
- `knowledge/domains/Payment/h18_dmee_tree_nodes.csv` — 8,308 DMEE nodes extracted from P01 on 2026-04-06 (Session #039). Our authoritative pre-change baseline for the 3 target trees
- `knowledge/domains/Payment/h18_dmee_d01_vs_p01_comparison.csv` — D01 vs P01 drift table for the 4 UNESCO-custom DMEE trees
- `knowledge/domains/Payment/h18_dmee_tree_findings.md` — Session #039 writeup of DMEE tree discovery
- `knowledge/domains/Treasury/payment_full_landscape.md` — char-filter 3-layer rules (lines 104-111), payment chain architecture, country-specific requirements
- `Zagentexecution/mcp-backend-server-python/h18_dmee_tree_probe.py` — reusable probe (SNC/SSO) for DMEE tables
- `Zagentexecution/mcp-backend-server-python/cts_10yr_raw.json` + `cts_batch_YYYY.json` (2017-2026) — CTS 10-year snapshot; source for Francesco audit and Marlies-28-transport history
- `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db` — 68 Gold tables including LFA1, LFB1, LFBK, T001, T042Z/E/I, FPAYP — source for vendor DQ SQL
- `extracted_code/FI/DMEE/YCL_IDFI_CGI_DMEE_FALLBACK_CM001.abap` lines 13-31 — existing StrtNm overflow logic (35-char truncation), evidence that structured address hooks already partially exist
- `extracted_code/FI/DMEE/YCL_IDFI_CGI_DMEE_FR_*` + `_UTIL_*` — other extracted BAdI classes for DMEE
- `extracted_code/FI/YWFI/` — full YWFI package (Session #038)
- `brain_v2/brain_state.json` — claims, annotations, feedback rules anchoring this project in UNESCO's knowledge graph

**C. SAP-official (to fetch from SAP for Me in Phase 0 — not in repo yet)**
- SAP Note **1665873** — CGI_XML_CT format introduction guide (59 pages, canonical). Priority 1 to fetch.
- SAP Note **2795667** — ISO 20022 adoption / SEPA harmonisation
- SAP Note **2668719** — PMW format lifecycle
- SAP Note **2819590** — Structured remittance gap in CGI XML output (check applicability)
- SAP Note **2845063** — CGI Identifications and organization ID config
- SAP Note **2944738** — pain.001.001.09 (for future version-upgrade discussion, out of scope of current change)
- SAP Note **3208888** — CBPR+ structured address (if exists — confirm during fetch)

**D. SAP Community — technical reference threads**
- [SAP Community — DMEE Debtor Address (Event 05 pattern)](https://community.sap.com/t5/enterprise-resource-planning-q-a/dmee-debtor-address/qaq-p/11572706) — confirms OBPM4 Event 05 approach for UNESCO debtor address (note: direct WebFetch was blocked 403, but the Event-05-via-BAPI_COMPANYCODE_GETDETAIL pattern is documented per WebSearch summary)
- [SAP Community — XML as Global Payment File](https://community.sap.com/t5/-/-/m-p/13239330) — DMEE+PMW full walkthrough (SAP blog 2014, redirected; WebFetch returned 403 — re-fetch manually or via another route)
- [SAP Community — SEPA_CT integration into CGI_XML_CT](https://community.sap.com/t5/-/-/m-p/13389342) — SEPA-into-CGI consolidation pattern (related to handoff doc Q8, parked for post-go-live)
- [SAP Community — How to Update DMEE Format CGI_XML_CT to pain 001.001.09](https://community.sap.com/t5/financial-management-q-a/how-to-update-dmee-format-cgi-xml-ct-to-the-pain-001-001-09-version/qaq-p/13897978) — the exact UNESCO scenario documented by another customer
- [SAP Community — ISO20022 format switch 001.03 → 001.09](https://community.sap.com/t5/financial-management-q-a/iso20022-format-switch-from-pain-001-001-03-to-pain-001-001-09/qaq-p/14358927)
- [SAP Community — Source of Information for Tags of CGI Pain.001 File](https://community.sap.com/t5/enterprise-resource-planning-blog-posts-by-sap/source-of-information-for-tags-of-cgi-pain-001-file/ba-p/13536706)

**E. ISO 20022 / SWIFT / Bank-industry sources**
- [Deutsche Bank ISO 20022 FAQ — Corporates and Institutions](https://corporates.db.com/in-focus/Focus-topics/iso20022/faqs) — authoritative on Nov 2025 3-options / Nov 2026 2-options timeline
- [SAP Community — Structured address data elements in ISO 20022 messages](https://community.sap.com/t5/enterprise-resource-planning-blog-posts-by-sap/structured-address-data-elements-in-iso-20022-messages/ba-p/14174822)
- [PIKON blog — ISO 20022 why you need to switch your payment formats now](https://www.pikon.com/en/blog/iso-20022-why-you-need-to-switch-your-payment-formats-now/) — consultant-level overview (business-level, no technical depth)
- [Medium — ISO 20022 Enhanced Data — Structured Addresses by Dominic Digby](https://medium.com/@domdigby/iso-20022-enhanced-data-structured-addresses-c64c645cc161) — tag-by-tag explanation
- [The Paypers — Structured addresses and ISO 20022: What corporates need to prepare before November 2026](https://thepaypers.com/regulations/explainers/structured-addresses-and-iso-20022-what-corporates-need-to-prepare-before-november-2026)
- [State Street Client Guide to ISO 20022 (PDF)](https://www.statestreet.com/web/insights/articles/documents/state-street-client-guide-to-iso-20022-2025.pdf)
- [Banking.Vision — ISO 20022 The Final Chapter Begins](https://banking.vision/en/iso-20022-the-final-chapter-begins/)

**F. Bank-specific specs — to request in Phase 1 (not in repo)**
- Société Générale — pain.001 implementation guide (current version) — via Marlies's SG TRM
- Citibank — DC_V3_01 CBPR+ addendum + Worldlink per-currency rules (TND/MGA/BRL) — via Citi CitiConnect TRM
- CGI-routed banks (Shinhan KR, Metro GB, GT NG, etc.) — each bank's pain.001 supplement — via Marlies's TRMs

**G. Methodology / process references**
- `C:/Users/jp_lopez/projects/ecosystem-coordinator/.knowledge/way-of-working/session-start.md` — ecosystem session-start protocol
- `C:/Users/jp_lopez/projects/ecosystem-coordinator/.knowledge/way-of-working/collaboration-terms.md` — challenge assumptions, distinguish [VERIFIED] from [INFERRED]
- `CLAUDE.md` Core Principles CP-001/002/003
- `brain_v2/agent_rules/feedback_rules.json` — specifically rule #204 (only P01 trustworthy for config analysis)

### Evidence integrity rules for the companion

- Every claim in the companion must cite its source from this References list
- `[VERIFIED]` = taken from handoff doc or verified against P01 baseline
- `[INFERRED]` = deduced from other evidence, must be flagged
- `[TODO]` = placeholder awaiting Phase 0 or bank spec
- No invented content — if we don't have a source, it doesn't go in

### Companion vs plan file relationship

| Artifact | Role | Location |
|---|---|---|
| Plan file (this file) | Working draft for agent + Pablo | `C:/Users/jp_lopez/.claude/plans/revisa-nuevamente-todo-hay-parsed-scone.md` |
| Companion Tab 2 | **Rendered version of the plan** — what Marlies + DBS + auditors see | `companions/BCM_StructuredAddressChange.html` |
| Companion Tab 5 | Change matrix rendered from `change_matrix.csv` | idem |
| Companion Tab 16 | References, kept in sync with plan | idem |

When the plan changes, the companion updates in the same commit. Single source of truth.

---

## Critical files to create or modify

| Path | Action | Phase |
|---|---|---|
| `knowledge/domains/Payment/gap_closure_report.md` | Create: close 8 gaps GAP-001..008 | **Phase 0** |
| `knowledge/domains/Payment/xml_touch_points_complete.md` | Create: definitive inventory of every code point touching XML | **Phase 0** |
| `extracted_code/FI/DMEE_full_inventory/` | Create: extract AE/BH classes, Event 05 handlers, Z-field populator BAdI, YRGGBS00 source | **Phase 0** |
| `Zagentexecution/mcp-backend-server-python/f110_xfield_tracer.py` | Create: trace FPAYHX Z-field write points (likely static grep + optional ST05 playback) | **Phase 0** |
| `Zagentexecution/mcp-backend-server-python/h18_dmee_tree_probe.py` | Extend: dump all 7 DMEE tables, not just NODES | Phase 1 |
| `knowledge/domains/Payment/baselines/2026-04-30_P01/*.json` | Create: frozen baseline | Phase 1 |
| `knowledge/domains/Payment/change_matrix.csv` | Create: the master change tracker | Phase 1 → Phase 5 |
| `knowledge/domains/Payment/bank_spec_matrix.md` | Create: per-bank requirements | Phase 1 |
| `knowledge/domains/Payment/francesco_audit.md` | Create: 5 transports classified | Phase 1 |
| `knowledge/domains/Payment/vendor_master_dq.md` | Create: count + remediation | Phase 1 |
| `extracted_code/FI/DMEE/Z_DMEE_UNESCO_DEBTOR_ADDR/` | Create: user exit FM | Phase 2 |
| `Zagentexecution/incidents/xml_payment_structured_address/README.md` | Create: incident trail | Phase 1 |
| `companions/BCM_StructuredAddressChange.html` | Create + version v1-v5 across phases | All phases |
| `brain_v2/incidents/incidents.json` | Add record for this change | Phase 1 |
| `brain_v2/domains/domains.json` | Register new objects (ADRC, FPAYHX, FPAYH, user exit FM) | Phase 1 |
| `knowledge/session_retros/session_062_retro.md` | Create at session close | End of session |

---

## Existing functions / utilities to reuse (do NOT rebuild)

| Asset | Path | Reuse for |
|---|---|---|
| DMEE tree probe (SNC/SSO) | [h18_dmee_tree_probe.py](Zagentexecution/mcp-backend-server-python/h18_dmee_tree_probe.py) | Phase 1 baseline extraction, Phase 3 test output extraction |
| DMEE node baseline (8,308 nodes P01) | [h18_dmee_tree_nodes.csv](knowledge/domains/Payment/h18_dmee_tree_nodes.csv) | Phase 1 current-state column of change_matrix |
| D01 vs P01 diff | [h18_dmee_d01_vs_p01_comparison.csv](knowledge/domains/Payment/h18_dmee_d01_vs_p01_comparison.csv) | Phase 1 D01 draft purge decision |
| CTS 10-year snapshot | `Zagentexecution/mcp-backend-server-python/cts_10yr_raw.json` + yearly `cts_batch_YYYY.json` | Phase 1 Francesco audit + Marlies's 28-transport history |
| ABAP BAdI boilerplate | [YCL_IDFI_CGI_DMEE_FALLBACK_CM001.abap](extracted_code/FI/DMEE/YCL_IDFI_CGI_DMEE_FALLBACK_CM001.abap) lines 13-31 | Phase 3 regression check on 35-char overflow |
| 3-layer char filter rules | [payment_full_landscape.md:104-111](knowledge/domains/Treasury/payment_full_landscape.md) | Phase 2 per-node configuration of char suppression |
| Companion HTML pattern | [payment_bcm_companion.html](companions/payment_bcm_companion.html) | Phase 1+ `BCM_StructuredAddressChange.html` skeleton |
| Gold DB (LFA1, LFB1, LFBK, FPAYP, T001) | `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db` | Phase 1 vendor DQ audit, Phase 3 test vendor sampling |
| Feedback rule (P01 only) | `brain_v2/agent_rules/feedback_rules.json#204` | All phases — D01 config findings flagged as untrustworthy |

---

## Verification — how to test end-to-end

### Phase 1 (baseline + spec + audit)
- `python Zagentexecution/mcp-backend-server-python/h18_dmee_tree_probe.py --tree /SEPA_CT_UNES --system P01 --dump-all --out baselines/2026-04-30_P01/` — dumps 7 DMEE tables; verify file count + row counts match prior session #039 baseline (sanity check).
- `change_matrix.csv` parses cleanly; every row has target_src_type filled; no UNKNOWNs.
- `francesco_audit.md` classifies all 5 transports; any BLOCK transports have an alignment meeting minuted.

### Phase 2 (config)
- DMEE Tx → tree → Test mode: render sample payment → confirm XML contains `<StrtNm>Place de Fontenoy</StrtNm><BldgNb>7</BldgNb><PstCd>75007</PstCd><TwnNm>PARIS</TwnNm><Ctry>FR</Ctry>` for UNESCO Dbtr, matching Marlies Tab 2.
- F110 proposal mode in D01: generate XML, no posting. Diff against target.
- Transport export via SE10; verify TOC contains DMEE objects of correct scope only.

### Phase 3 (unit test)
- F110 proposals in V01 for 50 tier-1 test cases.
- XSD validation script runs against pain.001.001.09 schema — 100% pass required.
- BAdI regression: payment with Cdtr.Nm >35 chars → verify overflow behaves per legacy OR fails loud if deprecated.
- Hybrid coexistence test: vendor with full ADRC → structured-only output; vendor with partial ADRC → Hybrid fallback.

### Phase 4 (UAT)
- Each bank receives pilot file → written acceptance
- Business users run 12 UAT scenarios per handoff §8.2
- All sign-offs archived

### Phase 5 (deploy)
- Post-cutover: BCM rejects < P-1 baseline + 1%
- Daily monitor for 14 days per tree
- 2026-11-01: formal CBPR+ compliance letter to internal audit

---

## Open architectural decisions (require Pablo + Marlies alignment pre-Phase-2)

1. **Per-bank strictness**: Fully structured vs Hybrid per bank — decided in Phase 1 after bank specs. Default: Hybrid-coexistence (per user directive).
2. **BAdI overflow logic fate**: keep / deprecate / refactor — decided during Phase 3 based on test.
3. **D01 draft purge on CGI trees**: the 2× node delta may be unrelated to structured address but may still block our changes. Decide after Francesco audit.
4. **UltmtCdtr data source for Worldlink** (Citi): vendor master / Z-table / user exit — handoff Q3, depends on Citi spec + DBS input in Phase 1.
5. **Separate PMW formats per entity** (IIEP/UIL for SEPA; UBO/UIS for CITI): per handoff Q4+Q5 — check FBZP during Phase 1.

---

## Non-obvious risks

1. **Marlies is the author AND the reviewer** (28 prior transports) — she may prefer to edit directly, bypassing the audit trail. **Mitigation**: change_matrix as shared single source; both sign each row before Phase 2 execution.
2. **Francesco territory on CGI D01** — his most recent transport (2025-03-20) is on `/CGI_XML_CT_UNESCO`. Editing could overwrite uncommitted WIP. **Mitigation**: Phase 1 audit precedes any CGI D01 edit; BLOCK classifications trigger 3-way alignment.
3. **BAdI wiring ambiguity**: `YCL_IDFI_CGI_DMEE_FALLBACK_CM001` has PstlAdr/StrtNm boilerplate — unknown if live trees invoke it. Silent break risk. **Mitigation**: trace MP_FCODE / exit-function column per Cdtr node in `h18_dmee_tree_nodes.csv` during Phase 1.
4. **Worldlink exotic currencies** (TND 3-decimal, MGA no-IBAN, BRL STCD2, ARS 90-day hold — `payment_full_landscape.md:114-128`) interact with structured address non-trivially. **Mitigation**: tier-1 test matrix must include BR, MG, TN, AR scenarios.
5. **Vendor master DQ**: the handoff SQL query will surface a count of non-compliant vendors. If the count is high (>5% of active), Phase 3 UAT is at risk. **Mitigation**: Phase 1 counts first; remediation plan with Master Data team before Phase 2 ends.
6. **Push blocker from Session #061** — local git only. **Mitigation**: all artifacts committed locally with safety tags; remote push decision deferred per user.
7. **"Francesco no sabía"** — user's directive says audit his transports as context but don't assume pattern. He may know more than it appears OR less. **Mitigation**: audit is evidence-only; if his transports surface relevant work, flag to user for decision; do not assume.

---

## Not in scope

- Migration to pain.001.001.09 (from current .03 version) — that's a parallel SAP-upgrade topic handled via SAP Notes 2944738 / 2668719, tracked separately.
- Consolidation of SEPA into CGI_XML_CT (some SAP customers have done this) — handoff Q8 says LOW priority, park for post-go-live.
- Vendor master cleanup for non-active vendors (LOEVM = 'X').
- Non-payment address flows (e.g., customer master, BP master addresses in non-payment contexts).
- BCM dual-control remediation (H13 — separate track, already in PMO).

---

## Timeline (gated)

| Phase | Period | Owner | Gate |
|---|---|---|---|
| **0 — 100% Code Inventory Closure** | **2026-04-24 → 04-27** | **Pablo** | **`xml_touch_points_complete.md` signed; 0 UNKNOWN in "Change required" column** |
| 1 — Config matrix + bank specs | 2026-04-27 → 04-30 | Pablo + Marlies | Matrix + bank specs + DQ count signed |
| 2 — Config D01 | 2026-05-01 → 05-31 | Pablo (config) + Marlies (review) | Each tree transport signed before next |
| 3 — Unit Test | 2026-06-01 → 06-30 | Pablo + DBS + Marlies | 100% XSD pass + BAdI regression green |
| 4 — UAT V01 | 2026-07-01 → 07-31 | Marlies (business) + Pablo (tech) | 3 bank acceptances + all UAT scenarios signed |
| 5 — Deploy | 2026-08-01 → 11-01 | DBS (transport) + Pablo (monitoring) | Nov 2026 CBPR+ compliance |
