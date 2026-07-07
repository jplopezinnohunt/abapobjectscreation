---
name: Cost Recovery E2E — Case study staff 10025831 (G5, home office OPC)
description: Full end-to-end of one staff member's cost recovery — 12 recoveries across 9 projects, all crediting OPC, proving funds center = staff home office. FI Dr/Cr → pool 633CRP9003 → BOR supplement.
type: project
created: 2026-06-26
source: P01 Gold DB (fmifiit_full + bkpf) + live FMBL/BSEG reads
---

# Cost Recovery — End-to-End case: staff `10025831`

## 0. The actor
- **Staff `10025831`** — a **G5** position, **home office = OPC** (Operating Programme Cost), sector area SHS/Culture.
- A **shared/central resource**: their time is consumed by many projects across **BIO** and **ITH** sectors → that is *why* cost recovery exists (each project must pay OPC back for the staff time it used).
- **Invariant proven:** across 9 different projects, the recovery credit **always** goes to **OPC** (0 exceptions). The funds center follows the *person*, not the project.

## 1. The 12 recoveries (FI side, type R1, all entered by L_HANGI)
| FY | R1 doc | Date | Source project.WBS | Period | Amount USD |
|---|---|---|---|---|---:|
| 2024 | 9000007312 | 2024-03-31 | 570GLO3017.2 | JAN-DEC23 | 3,420.00 |
| 2024 | 9000028752 | 2024-11-30 | 549BEL3000 | AUG-NOV24 | 3,087.00 |
| 2024 | 9000028754 | 2024-11-30 | 549RER3003.1 | JAN-NOV24 | 1,715.00 |
| 2024 | 9000028756 | 2024-11-30 | 570GLO3023.6 | JAN-NOV24 | 5,145.00 |
| 2024 | 9000029022 | 2024-12-01 | 469GLO4000 | JAN-NOV24 | 2,401.00 |
| 2025 | 9000002218 | 2025-01-31 | 537GLO3000 | JAN-DEC24 | 11,319.00 |
| 2025 | 9000031680 | 2025-11-30 | 469GLO3007 | JAN-NOV25 | 857.50 |
| 2025 | 9000031683 | 2025-11-30 | 537GLO3001 | JAN-NOV25 | 343.00 |
| 2025 | 9000031686 | 2025-11-30 | 549BEL3000 | JAN-NOV25 | 1,715.00 |
| 2025 | 9000031692 | 2025-11-30 | 549GLO3003.5.1 | JAN-NOV25 | 5,145.00 |
| 2025 | 9000031695 | 2025-11-30 | 549RER3003.1 | JAN-NOV25 | 600.25 |
| 2025 | 9000036464 | 2025-12-30 | 469GLO4000 | JAN-NOV25 | 2,401.00 |
| | | | | **TOTAL** | **38,148.75** |

By year: **2024 = 15,768.00 · 2025 = 22,380.75**. Projects span sectors **BIO + ITH**.

## 2. The accounting per recovery (Dr/Cr) — e.g. doc 9000002218
```
Débito  (40/S)  GL 6046014 consultant cost   fund 537GLO3000  FISTL BIO   11,319   ← project pays
   Crédito (50/H)  GL 7046013 revenue         fund 633CRP9003  FISTL OPC   11,319   ← OPC earns
```
- **Debit funds center = the PROJECT's office** (BIO/ITH) — from the WBS.
- **Credit funds center = OPC = the STAFF's home office** — manual input, identifies whose staff was recovered.
- Balances to zero. KOSTL/PRCTR/WBS are blank on both lines → not FMDERIVE-derived.

## 3. End-to-end flow
```
STAFF 10025831 (G5, home=OPC)
      │  works on 9 projects (BIO/ITH) over 2023-2025
      ▼
12× R1 recoveries (FB01, L_HANGI):  Dr project(GL 6046014) / Cr OPC(GL 7046013)
      │  every credit → fund 633CRP9003, FISTL=OPC   (= 38,148.75 total)
      ▼
POOL 633CRP9003 accumulates OPC's recovered revenue (+ all other staff/offices)
      ▼
Monthly BOR (Y_FMKU_0050, PROCESS=SUPL, by G_KAPEKOVA via FMBB):
      budget supplement to OPC's fund 633CRP3190, CMMT_ITEM=TC, period 01..12
      │  text "CR <project> SHS G5 10025831 <period>" = same key as the R1
      ▼
OPC can re-spend what its staff earned (its 633CRP3190 allotment)
```

## 4. The derivation rule (proven this case)
| BOR field | Derived from | This case |
|---|---|---|
| `FUNDS_CTR` | **home office of the recovered STAFF** (manual input, NOT FMDERIVE) | OPC |
| `FUND` | `633CRP` + category + office | `633CRP3190` (cat 31 + OPC 90) |
| `CMMT_ITEM` | fixed | `TC` |
| amount | recovered staff cost | per line |

- Validated at scale: **380/395 staff (96%) → exactly one home office**; the 4% multi-office = staff who changed duty station (mobility — the credit follows the move).
- FMDERIVE has **0 rules** for the cost-recovery GLs (7046013/6046014) or `633CRP` → confirms the funds center is human input keyed on the staff's home office.

## 5. Evidence
- Gold DB `p01_gold_master_data.db`: `fmifiit_full` (SGTXT mentions 10025831), `bkpf`, `bsis`, `fmbh/fmbl`, FMDERIVE tables (`fmderive*`, `fmfmoa*`, `tabadr*`).
- Live P01 reads: BSEG (Dr/Cr), FMBL `TVAL01`/`TEXT50` (amounts + key).
- Sibling: [ANALYSIS.md](ANALYSIS.md), [TECH_SPEC_Y_FMKU_0050.md](TECH_SPEC_Y_FMKU_0050.md).
