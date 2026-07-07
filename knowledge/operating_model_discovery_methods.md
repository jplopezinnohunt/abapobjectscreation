---
name: Operating-Model Discovery Methods — how to map "how UNESCO works" (the discovery patterns)
description: The discovery PATTERNS for building the AS-RUN operating model (U_USAGE): map every executed object (tcode/report/RFC-BAPI/job) to domain + actor + behavior + time, by triangulating 4 complementary methods, detect hidden/parallel extractions, and factor by time. Discovered 2026-06-23 while mapping executed objects. These are reusable methods, not one-off findings.
type: project
---

# Operating-Model Discovery Methods

> The goal: explain **100% of transactions/reports/RFC-BAPIs/jobs that run** — what they are, who/what
> calls them, where from, and whether they're an integration. = **how UNESCO actually works** (U_USAGE).
> These are the DISCOVERY PATTERNS we converged on. Reusable; not a one-off.

## The object axes (each executed object gets all four)
1. **DOMAIN** — which area (PSM_FM, FI, Payment, HCM, …).
2. **ACTOR** — who/what runs it: **human** (named user) · **integration** (MULESOFT, BRIDGE-RFC=ORION, UBO-RFC, SISTER) · **batch** (JOBBATCH) · system.
3. **BEHAVIOR / integration?** — read · DB-write · **file** (OPEN DATASET/AL11/logical file) · RFC-out. Integration = called by a technical actor OR uses file system OR writes/calls out.
4. **TIME** — when used (monthly profile) → recency/activity; detects active-vs-dead and seasonality.

## The 4 complementary mapping methods (TRIANGULATE — no single one is complete)
1. **By PACKAGE (TADIR.DEVCLASS)** — authoritative grouping; each object's dev package is module-coded
   (FMRP→PSM_FM, FBAS→FI, ME→Procurement, PC10→HCM). Cache `tadir_prog`(388K)+`tdevc`(28K) in the Gold DB.
   Reaches ~60% by execution volume; the FLOOR, always do this first.
2. **By LOGS (execution context)** — `rsau_audit_history` Transaction Start/Report Start/RFC Function Call +
   `tbtcp` jobs. Gives the AS-RUN set + volume. (channel-field map in [[reference_fm_ps_bcs_masterdata_refresher]]-adjacent census).
3. **By OBJECTS-READ** — what tables/infotypes the object touches → domain (e.g. `/1BCDWB/DBPA0001`→PA0001→HCM,
   `/1BCDWB/DBFMFINCODE`→PSM_FM). Resolves generated programs the package method misses. *(partially built; TODO)*
4. **By CALLER→DOMAIN (actor mapping)** — map the calling user/service-account to a domain + actor-type. The
   RFC caller (MULESOFT/BRIDGE/UBO-RFC) and the dialog user reveal domain AND whether it's an integration.

**Why triangulate:** the package method floors at ~60% volume; generated programs (SAP Query `AQ*`/`!Q*`,
`/1BCDWB/DB*`) and custom Z/Y need objects-read + name resolution; technical/basis substrate (SAPMSSY1, RS*) is a
legitimate non-business tier — NOT "lost knowledge".

## Discovery PATTERN — hidden / parallel extractions (high value, governance)
**Ad-hoc SAP Queries (`AQ*`/`!Q*`/SAPQUERY) = ungoverned parallel data extraction.** Detected by the
caller-method: VERIFIED 2026-06-23 — **6,060 query execs · 1,798 distinct queries · 153 users; 60% are HR
(3,658 execs, 39 users) = sensitive personnel data extracted outside governed reports.** Top runner **JOBBATCH
(1,890) = queries SCHEDULED AS JOBS → automated hidden extraction → almost certainly file output = a parallel
integration nobody catalogued.** Active & growing (2026-03→06, ~1,500/mo). Pattern: *ad-hoc query + caller +
time → shadow extraction; query→job→file → shadow integration.* This is the bridge from "report" to "integration".

## Discovery PATTERN — time factoring
Always factor usage by TIME (`rsau SAL_DATE` monthly): separates **active vs dead** objects (feeds R_S4_READINESS
dead-code), reveals seasonality (period-end, biennium), and dates the extractions. "When were they used / are they
used" is a first-class question, not a footnote.

## Status & coverage
- Built: object→domain map (`brain_v2/executed_objects_domain_map.json`, `process_mining/executed_objects_domain_map.py`),
  `tadir_prog`/`tdevc` cached (Gold DB). Coverage **60% by volume / 39% by object**; tail = ad-hoc queries +
  generated + technical (characterized, not lost).
- This is the METHOD for the **U_USAGE** capability dimension at scale (PMO H84/H85 = apply per domain).
- Cross-links: [[feedback_avc_real_from_standard_not_handrolled]] (the deep-dive pattern), H71 (write-channel SoD), H73 (arbitrary extraction auth).
