---
name: Capability Model — the 4th axis (domain × capability) that aligns acquired knowledge and drives expansion
description: Beyond a plan. This is the structural reflection of the process+code+conformance work into our MODEL. The domains_layer (Layer 14) had 3 axes (functional/module/process); this adds a 4th — CAPABILITY. A domain is "understood" only when we cover 10 capability dimensions for it (Standard-Ref · Process · Code · Config · Data · Authorization · Interface/File · Conformance · Improvement · S/4-Readiness). The domain × capability matrix ALIGNS all acquired knowledge to one skeleton and makes every empty cell the deterministic expansion target. Born s079.
type: project
---

# Capability Model — domain × capability (the model's 4th axis)

User (s079): "este trabajo es crucial en nuestro modelo. Cómo lo reflejamos más allá del plan. Hoy
tenemos dominios y conocimiento adquirido que debe ALINEARSE y luego AMPLIARSE." Correct: our knowledge
is organized by TOPIC (domains), not by CAPABILITY. The process-mining + code-mining + conformance work
defines the missing skeleton. Reflecting it "beyond a plan" = making it a structural axis of the brain.

## The principle: ALIGN then EXPAND
- **ALIGN** — re-express every existing domain against ONE capability skeleton. Acquired knowledge stops
  being topic-shaped prose and becomes a scored position on a common model. (CP-002: structure over prose.)
- **EXPAND** — every weak/empty cell is, by construction, the next work item — ranked, traceable, no
  guessing. The roadmap is a *consequence* of the matrix, not a separate plan document.

## A domain is TWO strata: AS-DESIGNED (standard SAP) + AS-RUN (our process)
User (s079): "en el caso de dominio, entender que tenemos el dominio ESTÁNDAR SAP como fue diseñado, y
luego NUESTRO proceso — por ejemplo cómo se planifican [los presupuestos] en public sector." A domain is
not one model. It is a **pair**, and the product lives in the gap between them:
- **AS-DESIGNED (standard)** — how SAP designed the domain: the normative reference flow/objects/config
  as delivered (e.g. PSM-FM budget formulation via FMBB → release → AVC; the SAP-delivered PaPM P2P model ✅).
- **AS-RUN (ours)** — how UNESCO ACTUALLY does it: the real process discovered from data + the Z-code,
  config, exits, .NET apps and workflows layered on top (e.g. UNESCO's biennium budget planning via SISTER /
  the .NET budget-transfer tool / the real approval workflow — NOT the textbook FMBB path).
- **THE DELTA = the value.** Capability **G (Conformance)** is literally the comparison of AS-RUN against
  AS-DESIGNED. The "custom-over-standard x-ray" is this delta made visible, down to the implementing object.

**Consequence (why G is empty everywhere):** conformance has TWO preconditions per domain — you need the
AS-DESIGNED baseline AND the AS-RUN process. Today we have neither captured as a reference for most domains.
So **capturing the standard SAP as-designed model per domain is a precondition capability**, not an
afterthought. Worked example — *public-sector budget planning*:
| Stratum | What it is | Where it comes from | Status |
|---------|-----------|---------------------|--------|
| AS-DESIGNED | SAP BCS standard: budget entry (FMBB) → release → AVC check → posting | SAP PSM-FM reference / SAP Best Practices | ○ not captured |
| AS-RUN | UNESCO planning lives in **Core Manager / Core Planner (SuccessFactors)**, integrated via MuleSoft (RFC+IDoc, PROJECT02); + .NET budget transfers + Z-config. **NOT SISTER.** | process discovery (FMBH/FMBL/FMRESERV) + interface + code/config mining | ◐ partial |
| DELTA (G) | where UNESCO extends/deviates from standard BCS, and the exact objects that implement the deviation | OPID conformance (AS-RUN vs AS-DESIGNED) | ○ unbuilt |

Every domain entry therefore carries the 8 capabilities **for each stratum** (or at minimum: the
AS-DESIGNED reference, the AS-RUN coverage, and the G delta). A capability is not fully met until BOTH
strata exist and the delta is computed.

## The 10 capability dimensions (what "understanding a domain" means)
A domain is fully modeled only when, for it, we have all ten — the precondition S, the 8 understanding
dimensions A–H (the unified graph: process + code + config + data + auth + interface + conformance +
improvement), and the composite R. Source of truth for definitions/method tiers: `capability_model.json`.
| # | Capability | The question it answers | Verified method (Phase-B) |
|---|-----------|--------------------------|---------------------------|
| **S. STANDARD-REF** | do we have the standard SAP as-designed baseline? (precondition for G) | SAP Best Practices / PaPM reference ⏳ |
| **A. PROCESS** | how does it actually run? (discovered from data, not docs) | event log → DFG/variants/performance; OCEL 2.0 ✅; pm4py ✅ |
| **B. CODE** | which programs/classes/exits/BDC implement it? | code mining: ATC/SCI ✅, dependency graph, abaplint ✅ |
| **C. CONFIG** | which customizing parameterizes it? | the standard-vs-custom config tables |
| **D. DATA** | which tables + real keys hold it? | DDIC keys; Gold DB; SAP-official P2P table set ✅ |
| **E. AUTH** | who can / does execute it? roles, users, SoD | AGR_*/SU24/SUIM/GRC ⏳ (systemic gap) |
| **F. INTERFACE/FILE** | how does it cross the boundary? RFC/IDoc/**file** | RFCDES, IDoc, file system (AL11/OPEN DATASET) 🟦 |
| **G. CONFORMANCE** | does it deviate from / extend STANDARD SAP? | OPID conformance ✅; PaPM reference baseline ✅ |
| **H. IMPROVE/SIMULATE** | where is the opportunity? what-if before building? | simulation (designed); the improvement framing |
| **R. S4-READINESS** | how ready is it for the S/4HANA migration? (COMPOSITE — its own sub-scorecard) | ATC S4HANA_READINESS + SI-Check + BP/CVI ✅ (see s4_readiness_model.json) |
✅ = verified method exists · ⏳ = gap, method not yet in our hands · 🟦 = our own design.

## The matrix — current coverage (● HAVE · ◐ PARTIAL · ○ NONE)
**SINGLE SOURCE OF TRUTH — not copied here.** The live matrix (15 domains × 10 dimensions) lives ONLY in
`brain_v2/capability_model/capability_model.json`; maturity is COMPUTED by `maturity_score.py` and rendered
in `companions/model_maturity_dashboard.html`. Do NOT hand-render a copy in prose — that is exactly what
drifted (this doc once showed 8 columns / "two empty columns" while the model had 10 / four). Query it:
`python brain_v2/graph_queries.py capability <domain>` · `... capability_gaps`.

## What the matrix reveals at a glance (this is the point of reflecting it structurally)
- **Four empty COLUMNS = systemic gaps, not per-domain gaps** (computed, s079): **S (Standard-Ref)**,
  **E (Auth/SoD)**, **G (Conformance)**, **R (S4-Readiness)** are ○ for every domain. These are not roadmap
  items inside a domain — they are *missing capabilities of the whole model*. Obvious in the matrix,
  invisible in a plan. (S is the precondition for G; closing E lifts every domain at once.)
- **Strong ROWS = leverage:** Payment/BCM and Procurement/P2P are the most complete — they are where the
  custom-over-standard x-ray (G) would land first with the least new extraction.
- **PSM/FM and Closing** are high on H (Improve) but low on A/G — we know the *opportunity* but not yet the
  *as-is process vs standard*. That ordering tells us what to mine next for those domains.

## How this lives in the brain (the structural reflection)
1. **New axis on Layer 14 (domains_layer):** each domain entry gains a `capability_coverage` block — the 8
   cells with tier + evidence path + next_step. Source of truth: `brain_v2/capability_model/capability_model.json`.
2. **It becomes queryable:** `graph_queries.py capability <domain>` and `... gaps` (list all ○ cells ranked)
   → the roadmap is generated, not written.
3. **It feeds the product framing:** A+G+H = UNDERSTAND/DESIGN/IMPROVE; the matrix IS the maturity model
   a customer would see ("here is your landscape, by domain, by capability, with the gaps").
4. **Alignment is continuous:** every new incident/claim/companion updates the cell it touches — the model
   grows the way the user wants (experiences connect, knowledge doesn't get forgotten — the s079 brain
   principle), instead of accumulating as disconnected topic prose.

## Expansion order (a CONSEQUENCE of the matrix, ranked)
1. Close column **E (Auth/SoD)** once — it lifts every domain at once (AGR_*/SU24/SUIM). Highest leverage.
2. Close column **G (Conformance)** starting on the strongest rows (Payment, P2P) where PaPM/standard
   baselines exist — the differentiator, lands fastest there.
3. Fill **A (Process)** for the high-H/low-A domains (PSM/FM, Closing) — turn known opportunity into
   discovered as-is.
4. Build **F (file/variant)** — the 🟦 additions — across Integration + the batch-heavy domains.
