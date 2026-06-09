---
name: Payment/Clearing — AS-RUN conformance (inductive miner + token replay, s079)
description: Applied result for Payment_BCM. The invoice-to-payment clearing lifecycle discovered with pm4py inductive miner + token-replay conformance over 161,172 clearing cases / 609,345 events. fitness 0.98 = the discovered model explains 98% of real behavior. Applied model: INDUCTIVE_CONFORMANCE (see applied_models.json). No extraction. The SoD angle (BCM dual-control) is now a verified method → see domains/Security.
type: project
---

# Payment / Clearing — AS-RUN conformance

From the Gold DB (no extraction): `sap_process_discovery.py clearing_lifecycle` (case = clearing doc AUGBL,
activity = doc type, BUDAT≥2025).

- **161,172 clearing cases · 609,345 events.**
- Inductive miner Petri net: 116 places / 178 transitions (4,000-case sample — inductive untractable on the
  full 600K events, the scalability ceiling).
- **Conformance (token replay): fitness 0.98 · precision 0.634.** fitness 0.98 = the model explains 98% of
  real behavior; precision 0.634 = the model is over-general (allows ~37% unseen behavior) → tighten with a
  reference net. This is the basis of as-is-vs-reference conformance for the payment domain.

## Capability impact (Payment_BCM)
- **A_PROCESS = HAVE** (deepened with inductive + conformance, beyond the existing 1.4M-event DFG mining).
- **E_AUTH**: the BCM dual-control (same user create+approve, CRUSR=CHUSR) is a SoD finding — the METHOD to
  generalize it systematically is now VERIFIED (see `domains/Security`). Payment is the first place to apply
  role-level SoD once EXT-AUTH lands.

## Caveats
4,000-case sample for the inductive step; same-day order arbitrary without intra-day timestamps (EXT-CDPOS).
