---
name: Product Direction — Understand HOW it works (code/objects), not KPIs
description: The real differentiation. Not Celonis's game (KPIs/conformance/BI). Our product is Process Intelligence that explains HOW a process is IMPLEMENTED and WHY it behaves that way — at the code / object / exit / config level — by connecting the mined as-is process to the as-coded reality in the unified brain. This is the MOAT and the lead, not a "later" item. Persisted s079 (user redirect).
type: project
---

# Product Direction: understand HOW the process works (code + objects), not KPIs

User redirect (s079): "No me interesan mucho KPIs — esto más en buscar cómo las cosas funcionan, el
código, los objetos." And: the unified brain (process + code + config + exits + transports + users in one
graph — competitors keep them separate), deterministic/auditable, simulate-before-build, Claude agentic
— THIS is the product, not a thing that "only matters after table-stakes."

We do NOT chase Celonis/Signavio on KPI libraries, conformance dashboards, benchmarking, BI. They win
that. We win a different game they STRUCTURALLY cannot play: they see the DATA the process leaves; we
see the **CODE and OBJECTS that produce it** — and we connect the two.

## Proof it already works (in miniature)
FX revaluation: from the mined process (F.05) we descended to SAPF100 → T030H → OB09 → the user exits →
the root-cause config gap → the incident → the transports. That descent — process to its implementation —
is the product. Generalize it.

## What we can DO there (the capabilities, grounded in our assets)
1. **Process → Implementation map.** For any discovered process/step, show the exact PROGRAMS, FMs,
   TABLES, USER EXITS/BAdIs, VALIDATION/SUBSTITUTION rules, CONFIG tables, and TRANSPORTS that implement
   it. (We have the connective layer: STEP→tcode→program→tables→users; + the brain's code edges.)
2. **"Why does it behave this way?" — code-level root cause.** Trace a mined behavior (a variant, a
   deviation, a delay) to the CODE/CONFIG that causes it: the exit that overwrites a field
   (YRGGBS00 XREF1), the hardcode (ZXFMDTU02 UNESCO), the config that routes it (OB09/T030H, OBPM5).
   Celonis surfaces the SYMPTOM in the data; we surface the CAUSE in the code. This is our root-cause.
3. **Custom-vs-standard X-ray.** Process mining reveals WHERE custom code (Z exits, BDC, the 7 .NET apps)
   intervenes vs standard SAP — the "as-implemented vs as-delivered" gap. Unique: nobody else sees the
   code layer under the process.
4. **Implementation conformance (not data conformance).** Not "does the data match a reference flow"
   (Celonis) but "does the IMPLEMENTATION match the intended design": a validation commented out, an exit
   that breaks SoD, a hardcoded account, a substitution with a gap. The mined process flags the symptom;
   the brain proves the code defect.
5. **Impact analysis at code/object level.** Change THIS config/exit/program → which process steps,
   documents, users are affected? (Brain impact analysis over 55K nodes — we have it.)
6. **Design + simulate at the object level.** To improve a process you change CODE/CONFIG. We can design
   the change against the real objects and simulate-before-build + feasibility-probe it (the code/objects
   make the simulation concrete, not abstract).
7. **Exit/extension discovery per process.** SAP processes are heavily customized via user exits, BAdIs,
   substitutions/validations, BDC. Best-in-class PM is BLIND to this. We show: "this step fires exit X,
   which does Y" — the actual logic, extracted and connected.

## Why competitors structurally can't do this
Celonis/Signavio connect to DATA (event logs). They don't extract and parse the ABAP code, the exits, the
config logic, or unify them with the process in one graph. Our brain does (code_ingestor, the extracted
exits/classes, the config, the connective layer). The process↔code unification is the moat.

## Reframe of the 4 capabilities (product_architecture)
- UNDERSTAND now means: understand the IMPLEMENTATION (code/objects/exits/config behind the mined process),
  not just the data flow. The "why".
- DESIGN / SIMULATE / IMPROVE operate at the code/object level (change the exit/config, simulate, build).
- KPIs/conformance-dashboards are NOT our focus. Data breadth (more event sources) matters only as INPUT
  to connect more process to more code — not as a feature race.

## Next build (the differentiated capability)
Wire the DISCOVERED process to its IMPLEMENTATION: for each mined step's tcode, traverse the brain
(tcode → program → tables/FMs → exits/BAdIs → config → incidents/transports) and present the
"how-it-works" view per process. Start from a process we've mined (PO lifecycle, FX) and the FX template
we already proved.
