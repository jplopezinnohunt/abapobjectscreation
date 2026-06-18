---
name: Process Mining — Known Gaps & What We're NOT Doing (self-audit)
description: Adversarial self-audit of the L7 process-mining approach. Not "validate what we do" but "what are we doing WRONG / not doing at all". Born s079 when the user caught that the deep research only validated the plan instead of finding blind spots. Drives correctness for the commercial product.
type: project
---

# Process Mining — Known Gaps (what we're getting WRONG / NOT doing)

Method note (the meta-lesson): inquiry must be framed adversarially — "what am I missing / getting
wrong" — NOT "confirm my plan". External research/input is to find BLIND SPOTS, not to validate.
"No puede ser que estemos haciendo todo [bien]." Run this audit as a standing pass.

## PROVEN WRONG (s079)
- **Reported noise as findings.** The "380-day bottlenecks" from clearing_lifecycle were all
  minimal-support transitions (not in top-60 DFG) — incomplete-case truncation artifacts, NOT real
  bottlenecks. Cause: NO event-log quality control (no support threshold, no incomplete-case handling).

## DOING THE ANTI-PATTERN
- **Flattening to a single case (AUGBL / OBJECTID) = case-centric mining.** ERP is one-to-many, so a
  single case notion causes CONVERGENCE (an event shared by N objects is duplicated) and DIVERGENCE
  (events of different objects in one case get falsely ordered). Object-centric PM (OCEL) exists to fix
  exactly this. We CLAIM object-centric but the engine flattens. FIX: real OCEL via pm4py
  (discover_ocdfg on an OCEL 2.0 log with multiple object types), not single case_id.
- **Timestamp ordering** — date-only (BUDAT) + CPUTM often 0 → intra-day DFG edges are arbitrary. FIX:
  use a secondary order key (document number / line) or flag intra-day order as uncertain.

## NOT DOING AT ALL (blind spots)
1. **Event-log quality layer** — incomplete-case filtering (trace within window), support/noise
   thresholds, long-tail variant handling, dedup. Without it, discovery surfaces artifacts.
2. **Conformance / normative model** — only as-is discovery. The product's improve/control value needs
   conformance vs a reference model (exists for standard SAP processes; the LDB/expected flow is one).
3. **Business KPIs** — rework rate, automation/touchless %, happy-path %, SoD violations, on-time/cycle,
   cost-per-case. We compute DFG/variants only — not the metrics that make it a product.
4. **PII / anonymization** — USNAM/resource is PERSONAL DATA (GDPR, works-council, public-sector). A
   COMMERCIAL blocker. Need pseudonymization + role-based access. Celonis/Signavio ship this; we ignored it.
5. **Validation of discovered processes** vs ground truth (sampling, sanity checks). The 380d artifact
   proves we don't validate outputs.
6. **Scale architecture** — full event log into pandas memory won't scale to multi-tenant / millions of
   cases. Need chunked / DB-side aggregation.
7. **Resource/actor as an OCEL object role** — we treat USNAM as a column, not as an actor object with
   an E2O qualifier (the OCEL way) — limits social-network / handover analysis.

## Priority to fix (correctness before more features)
A. Event-log quality (incomplete-case + support filtering) — stop reporting artifacts. IMMEDIATE.
B. Real OCEL (multi-object) instead of flattening — the core methodological fix.
C. Conformance + business KPIs — what makes it a product, not a graph viewer.
D. PII handling — commercial/legal blocker before any external use.
E. Validation + scale.

## The standing method
Every analysis/build gets an adversarial pass: "what would a skeptical PM expert say we're doing wrong
or missing here?" — and we act on THAT, not on the confirmation.
