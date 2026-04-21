# MGIE -> STEM Gap Analysis

**Generated:** 2026-04-15 - live RFC on E071/E071K
**MGIE source:** 16 transports from 2013 creation cluster
**STEM source:** 5 transports currently in progress

## Executive summary

- MGIE creation cluster (2013): **16 transports, 268 objects, 8696 keys** over 5 months (Jul->Dec 2013)
- STEM creation cluster (2026 in-progress): **5 transports, 48 objects, 1232 keys**

## Gap by category

| Category | MGIE (obj/keys) | STEM (obj/keys) | Gap | Criticality |
|---|---|---|---|---|
| Company Code core | 2/20 | 2/9 | 0 obj, 11 keys |  |
| House Banks + Bank Master | 4/26 | 4/14 | 0 obj, 12 keys |  |
| Payment Program (FBZP/F110) | 8/75 | 4/6 | 4 obj, 69 keys | CRITICAL |
| Tolerances | 8/22 | 8/36 | 0 obj, -14 keys |  |
| Asset Accounting | 6/27 | 7/18 | -1 obj, 9 keys |  |
| GL Accounts (co code) | 0/0 | 1/639 | -1 obj, -639 keys |  |
| MM Period | 1/1 | 1/1 | 0 obj, 0 keys |  |
| Cash Planning / Doc Types | 3/16 | 2/12 | 1 obj, 4 keys | MEDIUM |
| Dunning | 1/1 | 1/1 | 0 obj, 0 keys |  |
| Consolidation | 1/3 | 1/4 | 0 obj, -1 keys |  |
| Validations/Substitutions (GGB1) | 1/4288 | 0/0 | 1 obj, 4288 keys | CRITICAL |
| Controlling Area | 1/27 | 0/7 | 1 obj, 20 keys | CRITICAL |
| CO Master Data | 0/0 | 1/359 | -1 obj, -359 keys |  |
| Funds Management | 1/108 | 0/0 | 1 obj, 108 keys | CRITICAL |
| View metadata | 10/0 | 7/0 | 3 obj, 0 keys |  |
| HR / Travel | 2/103 | 0/0 | 2 obj, 103 keys | HIGH |
| Cash Journal | 5/37 | 0/0 | 5 obj, 37 keys | HIGH |
| Custom Auth Roles (Y_*) | 45/0 | 0/0 | 45 obj, 0 keys | HIGH |
| Cross-Company Pairs (F01U) | 16/0 | 0/0 | 16 obj, 0 keys | HIGH |
| CO-PA / Sets | 1/0 | 0/0 | 1 obj, 0 keys |  |
| CO Derivation (OKB9) | 1/0 | 0/0 | 1 obj, 0 keys | MEDIUM |
| System/Tech | 8/3181 | 0/0 | 8 obj, 3181 keys |  |
| Tax codes | 6/10 | 0/0 | 6 obj, 10 keys | HIGH |
| MM Org structures | 2/36 | 0/0 | 2 obj, 36 keys | MEDIUM |
| Other | 59/707 | 5/124 | 54 obj, 583 keys |  |

## Critical gaps (STEM missing):

### Payment Program (FBZP/F110)
**Rec:** MANDATORY: Configure FBZP payment methods/bank ranking for STEM
**Missing objects:** `T042A, T042D, T042I, T042V`

### Validations/Substitutions (GGB1)
**Rec:** MANDATORY: Create STEM substitution rule in GGB1 + OBBH assignment
**Missing objects:** `GGB1`

### Controlling Area
**Rec:** MANDATORY: Complete CO area config (V_TKA3 - CO versions) for STEM
**Missing objects:** `V_TKA3`

### Funds Management
**Rec:** MANDATORY: Complete FM area config (FM01, V_FMFUNDTYPE) for STEM
**Missing objects:** `V_FMFUNDTYPE`


## All MGIE 2013 creation transports:

| Date | TRKORR | User | Text | Objects | Keys |
|---|---|---|---|---|---|
| 20130718 | `D01K9A00FB` | M_SPRONK | CF-Delivery package MGIE Institute | 103 | 4801 |
| 20130718 | `D01K9A011G` | M_SPRONK | CF-MGIE aut cost assignment OKB9 | 4 | 19 |
| 20130718 | `D01K9A0150` | I_KONAKOV | WF - AM doc.derivations for MGIE | 2 | 0 |
| 20130801 | `D01K9A01AG` | P_IKOUNA | wf-"MGIE ROLES" PI.01.08.2013 | 49 | 2543 |
| 20130807 | `D01K9A01AS` | P_IKOUNA | WF-"Y_MGIE_CO_REPORTING" pi.07.08.2013 | 17 | 150 |
| 20130812 | `D01K9A01B4` | P_IKOUNA | wf-"maj Y_MGIE_FI_FM_MD_STRUCTURE" pi.12.08.2013 | 17 | 78 |
| 20130813 | `D01K9A01BE` | S_ROCHA | Fund Types as requested by BFM for MGIE Institute | 2 | 10 |
| 20131106 | `D01K9A01JA` | M_SPRONK | CF-MGIE tax codes india | 7 | 1 |
| 20131113 | `D01K9A01J2` | AN_LEVEQUE | MGIE-Rollout HR customizing | 6 | 36 |
| 20131118 | `D01K9A01IQ` | P_IKOUNA | wf-"MM & TV MGIEP ROLES" PI 21.10.2013 | 27 | 912 |
| 20131120 | `D01K9A01IE` | R_RIOS | MM: Account assignment MGIE - plant 7850 | 4 | 1 |
| 20131120 | `D01K9A01KK` | R_RIOS | MM: MGIEP Plant name adjust | 4 | 37 |
| 20131120 | `D01K9A01HS` | R_RIOS | MM: Purchasing Org. MGIEP | 5 | 6 |
| 20131120 | `D01K9A01IG` | R_RIOS | MM: Release strategy MGIE institute | 11 | 30 |
| 20131121 | `D01K9A01LE` | D_TAL | CLOSING OPERATIONS SETTINGS FOR UIL & MGIE | 7 | 70 |
| 20131212 | `D01K9A020G` | I_KONAKOV | CLOSING OPERATIONS SETTINGS FOR UIL & MGIE | 3 | 2 |