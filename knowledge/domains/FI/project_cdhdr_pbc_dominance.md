---
name: CDHDR PBC Volume Dominance
description: PBC (Planning/Budgeting) generates ~90% of CDHDR volume via FMRESERV - critical for filtering and analysis
type: project
---

PBC (Planning and Budgeting for Public Sector) generates ~90% of ALL CDHDR change document volume in P01.

**Why:** FMRESERV is 82% of CDHDR (6.4M of 7.8M rows, 2024-2026). Of that, ~95% is PBC-driven:
- **F_DERAKHSHAN**: 5.14M rows — 4.9M without TCODE (RFC/BAPI from PBC engine), 147K via HRPBC_ENGINE_PNP, rest PA30/FMZ6
- **HIPER** (system account): 622K rows — 287K via ZPBC_PERIOD_CLS_EXEC (period close), 223K via SE38 (batch programs)
- HIPER spikes only in January each year (carryforward at fiscal year start)
- F_DERAKHSHAN is consistent 200-400K/month year-round

**How to apply:**
- When analyzing CDHDR for non-FM processes, ALWAYS filter out OBJECTCLAS='FMRESERV' to avoid PBC noise drowning real signals
- When analyzing FM specifically, be aware that "change activity" is dominated by automated PBC, not manual user actions
- For process mining on CDHDR, separate PBC-generated events from manual events (TCODE blank or HRPBC_* = PBC)
- The remaining 1.4M rows (18%) contain the actual cross-module audit trail: BELEG(442K), EINKBELEG(189K), KRED(143K), ENTRYSHEET(128K), BANF(107K), HR_IT*(140K), FMFUNDBPD(34K)
