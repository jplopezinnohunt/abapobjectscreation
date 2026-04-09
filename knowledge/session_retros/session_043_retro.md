# Session #043 Retro — House Bank Configuration & Treasury Domain

**Date:** 2026-04-07  
**Duration:** Extended session  
**Focus:** House bank configuration (UBA01), Treasury domain creation, companion ecosystem  

## What We Did

### 1. House Bank Configuration — UBA01 (UBA Mozambique)
- Read and analyzed 45-page handover procedure PDF
- Parsed email request (INC-000005586) + 6 Excel forms + bank confirmation PDF
- Configured UBA01 in D01 (USD01 + MZN01, 4 G/L accounts)
- Built automated compliance checker (15 checks via RFC)
- Ran cross-system comparison D01 vs P01
- Found and fixed 7 issues:
  1. Missing G/L accounts 1165421/1165424 in D01 → INSERT via RFC
  2. KTOKS=OTHR instead of BANK → UPDATE SKA1
  3. XINTB flag missing → UPDATE SKB1
  4. OBA1 incomplete (LKORR/LSBEW/LHBEW blank) → UPDATE T030H
  5. T028B entries missing (different key than T035D) → SPRO manual
  6. YBANK sets misaligned P01↔D01 → SETLEAF sync via RFC (101 ops)
  7. P01 HBKID=ECO09 on all 4 accounts → PENDING (fix after transport)

### 2. ECO09 Benchmark
- Extracted full configuration of ECO09 (Ecobank Maputo) from P01
- Documented every field, every pattern
- Used as gold standard for UBA01 validation

### 3. Treasury Domain Created
- New domain: `knowledge/domains/Treasury/`
- Full README with 6 sub-domains, 28 SAP tables, E2E flow
- Moved 3 docs from FI (house_bank_config, bank_statement_ebs, payment_landscape)

### 4. Skills Created
- `sap_house_bank_configuration` — 13 steps, patterns, compliance checker, pitfalls
- `sap_account_comparison` — Cross-system G/L field-by-field comparison

### 5. Companions
- Built `treasury_operations_companion_v2.html` (storytelling edition, 70KB, 6 tabs)
- Moved all 16 companions to `companions/` at project root
- Added navigation header to ALL 16 companions (sticky top bar with cross-links)
- Updated landing page (Treasury Operations under Support & Maintenance)

### 6. Configuration Retros
- Created `knowledge/configuration_retros/` folder
- UBA01 report as first entry

### 7. Tools Built
- `house_bank_compliance_checker.py` — 15 automated checks, reusable for any house bank
- `ybank_setleaf_sync.py` — SETLEAF P01→D01 sync
- `uba01_final_report.py` — Cross-system comparison
- `uba01_d01_fix.py` — RFC fixes
- `uba01_gl_comparison.py` — Deep G/L comparison

## UBA01 Open Tasks
- [ ] GS02: Add 1065421 to FO_USD + 1065424 to FO_OTH (D01 + P01)
- [ ] TIBAN: Generate IBAN
- [ ] P01: Fix HBKID ECO09→UBA01 on 4 accounts via FS00
- [ ] TRS confirmations: MZN receiving (T018V), USD payment (T042I), OBPM4, TRM5

## Next Session Backlog
- Treasury landing page (connects 3 treasury companions)
- Basis Monitoring companion (script ready)
- Landing page restructure (Support → Monitoring + Support)
- Treasury companion v3 (deeper per-step detail)

## Key Discoveries
1. T035D and T028B are in the SAME SPRO screen but different tables — both required for EBS
2. T028B is keyed by BANKL (bank key), not HBKID — compliance checkers must search correctly
3. OBA1 has 3 sections that ALL must be filled (Realized + Valuation + Correction)
4. Sub-bank accounts (11*) need XOPVW=X (Open Item Management) for reconciliation
5. YBANK sets use exact match, not ranges — must be added manually per system
6. MD team copies reference G/L and keeps old HBKID — always verify after creation
7. GS02 sets drift between systems — periodic sync needed

## Patterns Established
- ECO09 as benchmark for field office house banks
- 13-step process with automated compliance validation
- Cross-system comparison before transport
- Configuration retros as knowledge artifacts
- Companion versioning (v1→v2, page-level updates)
- Navigation headers across companion ecosystem
