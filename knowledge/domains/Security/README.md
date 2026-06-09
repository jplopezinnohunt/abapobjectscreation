---
name: Security / Authorization & SoD — NEW domain (s079), seeded from the verified method
description: New domain. Seeds the E_AUTH capability (the biggest systemic gap, NONE across all domains). The METHOD is now VERIFIED (research wwyujjqyk, RES-AUTH-SOD): the SAP authorization table model + how to detect Segregation-of-Duties conflicts, scoreable from extracted AGR_*/USOBT_C tables. Coverage is still NONE (no auth data extracted yet) — this doc is the method + the plan, not yet applied. The only existing instance is the BCM dual-control finding (hand-built).
type: project
---

# Security — Authorization & Segregation of Duties (SoD)

NEW domain (s079). Fills **E_AUTH** — the dimension that is NONE for every domain (the biggest systemic
model gap). The METHOD is now VERIFIED; we hold ZERO auth tables, so coverage stays NONE until extraction.

## The authorization data model (verified, RES-AUTH-SOD)
| Layer | Tables |
|-------|--------|
| Roles | `AGR_DEFINE` (roles, PARENT_AGR for derived) · `AGR_USERS` (user↔role + FROM/TO_DAT validity) · `AGR_TCODES` (role↔tcode) · **`AGR_1251`** (role auth-object/field values LOW/HIGH) · `AGR_AGRS` (composite→single) · `AGR_1016` (profiles) |
| Users | `USR01/02/04/12` · `UST12` (effective auth values) |
| SU24 proposals | `USOBT_C` (field values) · `USOBX_C` (check indicator OKFLAG N/X/Y) · `TSTCA` (start-tcode auth) |
Reconstruct "who can do what": expand `AGR_USERS → AGR_1251` for a user's effective role authorizations.

## SoD conflict detection (verified)
- A **Function** = task = transactions + the auth objects/values it needs (e.g. maintain bank master; run
  payment proposal). A **Risk** = 2+ conflicting functions. Three risk types: **SoD · Critical Action ·
  Critical Permission**, at two levels: **action** (transaction) and **permission** (auth object/value).
- GRC Access Control: 3-tier function→action→permission; risk header `GRACSODRISK` (field RISKTYPE); ruleset
  is COMPILED. (REFUTED, do NOT assert: the exact "5 GRC tables" list + "GRACSODRISK = violations".)

## CRITICAL caveat (verified)
SU24/`USOBX_C` is a **PROPOSAL, not enforcement** — an auth object is only really checked where the program
code has an `AUTHORITY-CHECK`. So static role analysis must be **paired with a code scan / ST01-STAUTHTRACE**.

## D01 / P01 split (what we can do without P01)
- **Role STRUCTURE** (AGR_DEFINE/AGR_1251/USOBT_C/TSTCA) = **D01, system-invariant → ROLE-level SoD without
  P01** (which roles grant conflicting combos).
- **User ASSIGNMENTS** (AGR_USERS/USR02/UST12) = **P01 → USER-level SoD** (who actually HAS conflicting
  access) — gated on P01.

## What exists today
Only ONE instance, hand-built: the **BCM dual-control** finding (same user create+approve payment batches,
CRUSR=CHUSR — `companions/bcm_dual_control_audit.html`). That is a SoD violation detected from CHANGE data,
NOT from the authorization model. This domain generalizes it: a systematic SoD analyzer over the auth tables.

## Plan (backlog)
EXT-AUTH (D01 role-structure first → role-level SoD without P01; then P01 assignments) → build the SoD
ruleset (Function→Risk) → score role-level + user-level conflicts → link auth object → tcode → program.
