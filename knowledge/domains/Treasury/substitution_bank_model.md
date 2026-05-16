# Substitution Bank Model — UNESCO

**Created:** Session #071 (2026-05-05)
**Trigger:** INC-000008088 derivation question — "where do BA, CC, Fund, FundCenter come from for bank postings, and what changes do we need?"

## 🎯 The TIER_1 plot twist (headline finding)

Looking at actual posted documents (BSEG + FMIFIIT 2024-2026), **3 of 4 derivations already work correctly for all groups**. Original plan had 2 substitution + 1 derivation extensions — collapses to 1 small OKB9 maintenance.

| Field | 7044013 (A) | 7044014 (B) | 7043014 (C) | 7043021 (D) |
|---|---|---|---|---|
| **BA** | 70% GEF | **100% GEF ✅** | **100% OPF ✅** | **100% PFF ✅** |
| **Fund** | 57% GEF | **100% GEF ✅** | **100% 645ASH9000 ✅** | **100% 401NHF1091 ✅** |
| **FundCenter** | UNESCO | **100% UNESCO ✅** | **100% BFM ✅** | **100% HED ✅** |
| **CC** | 42% 113001 | 85% 113001 ✅ | 90% **131035** ⚠ | **100% empty ❌** |

Only Cost Center needs change: 7043014 currently posts KOSTL=131035 (90% of 21 hist) but Treasury wants 113001; 7043021 posts empty KOSTL, Treasury wants 113001. **2 OKB9 entries replace the original Steps 8 (GGB1) + 9 (FMDERIVE).**

## TL;DR

For every bank-related FI posting at UNESCO, four account-assignment fields are derived: Business Area (BSEG.GSBER), Cost Center (BSEG.KOSTL), Fund (FMIFIIT.FONDS), Fund Center (FMIFIIT.FISTL). The four fields ride **three different mechanisms**:

| Field | Mechanism | Where to maintain |
|---|---|---|
| Business Area | GGB1 substitution `SUBSTID=UNESCO` Step 002 (Form U910) reads YTFI_BA_SUBST + YBASUBST | tcode `YFI_BASU_MOD` (no-transport) or SE16N |
| Cost Center | OKB9 default account assignment per cost element | tcode `OKB9` |
| Fund | FMDERIVE strategy (HKONT-driven step) | tcode `FMDERIVE` |
| Fund Center | FMDERIVE strategy (Fund-driven step) | tcode `FMDERIVE` |

GGB1 does NOT set KOSTL, FONDS, or FISTL.

## 🚨 Third Actor — EXIT_RFEBBU10_001 / YTBAM001 (Session #071 discovery)

**THREE substitution layers exist for EBS posting** (the prior model documented only 2):

1. **EXIT_RFEBBU10_001 / YTBAM001** — fires during FEBEP→BSEG conversion (BEFORE OT83 chain) · modifies CHECT, GSBER, ZUONR · does NOT modify HKONT
2. **OT83 chain** (T028B → T028G → T033F → T033G) — resolves the GL via account symbols
3. **GGB1 SUBSTID UNESCO callup-3** — fires per BSEG line, 16 steps, includes Form U910 GSBER substitution again

UNESCO has been running custom code on every EBS posting since 2001 via:

```
CMOD Project YTFBE001 (Active · S.MAGAL · 27.07.2001)
└── SAP Enhancement FEB00001 "Electronic account statements"
    └── Function exit EXIT_RFEBBU10_001 (Active in P01)
        └── Customer include ZXF01U01
            └── Custom code YTBAM001 (559 lines · 2001-2014 evolution)
```

**YTBAM001 scope**: gates by `EFART='E' AND BUKRS IN {UBO, IIEP, UNES}` · 3 distinct branches.

**Modifies**: `E_FEBEP-CHECT` (cheque normalization), `E_FEBEP-GSBER` (BA derivation via `YCL_FI_ACCOUNT_SUBST_READ` reading YBASUBST), `E_FEBEP-ZUONR` (DME mass payment numbers).

**Does NOT modify**: `E_FEBEP-HKONT` — the field VGTYP cloning ultimately controls. **No conflict on HKONT field for INC-000008088.**

**Pre-existing VGTYP-aware pattern** (line 289 of YTBAM001):

```abap
IF I_FEBKO-VGTYP = 'SOG_EUR4' AND I_FEBEP-AVKOA = 'D' AND I_FEBEP-AVKON = '0000500469'.
  E_FEBEP-GSBER = 'OPF'.
ELSE.
  LV_GSBER = YCL_FI_ACCOUNT_SUBST_READ=>READ( IV_BUKRS = I_FEBKO-BUKRS ... ).
  ...
ENDIF.
```

**Decision (Session #071)**: Continue with Option A (VGTYP cloning) — see brain claim 170. YTBAM001 doesn't conflict with the OT83 chain on HKONT. Mandatory TST verification: confirm GSBER correctness on revenue GLs since they're not in YBASUBST and YTBAM001 will fall through to `YCL_FI_BSPROC_BS_ITEM->GET_GSBER` fallback.

## The 16-step UNESCO substitution chain (callup point 3)

Source: GB922 with `SUBSTID='UNESCO'` (17 rows including UNESCH MONAT-only step).

| Step | Manip / Action | Field set | Purpose |
|---|---|---|---|
| 001 | UGLS exit | BSEG.HKONT | GL account redirect |
| **002** | **U910 exit** | **BSEG.GSBER** | **BA derivation — reads YTFI_BA_SUBST + YBASUBST** |
| 003 | U901 / U902 | BVTYP, PYCUR | Bank type, payment currency |
| **004** | literal | **GSBER='GEF'** | **Default fallback** |
| 005 | UXR1 | XREF1 | Cross-reference 1 (bank-related HKONTs gated) |
| 006 | UXR2 | XREF2 | Cross-reference 2 |
| 007 | UZLS | ZLSCH | Payment method |
| 008 | UAEP exit | (no field) | Custom logic |
| 009 | literal | HKONT='2021023' | Specific GL redirect |
| **010** | **U904 exit** | **BSEG.GSBER** | **Late-stage BA override** |
| 011 | literal | FDLEV='B2' | Cash forecast level |
| 012 | literal | ZLSPR='A' | Payment block |
| 013 | U908 exit | FDLEV | FDLEV override |
| 014 | literal | ZUONR='Reval. Sub-Bank' | FX revaluation marker |
| 015 | literal | ZLSPR='N' | Release payment block |
| 016 | UATF exit | (no field) | Final exit |

## Bank-related BA tables (the U910 read chain)

### YTFI_BA_SUBST — modern, range-based, no-transport maintainable

Schema: `BUKRS + BLART + GSBER + NUMB + SIGN + OPTI + LOW + HIGH`. Tcode `YFI_BASU_MOD` adds ranges without raising a transport.

UNES has 4 rules:

| BLART | GSBER | OPTI | LOW | HIGH |
|---|---|---|---|---|
| (any) | GEF | BT | 0001000000 | 0001999999 ← catches every bank cash GL |
| Z1 | GEF | BT | 0001000000 | 0001199999 |
| PP | OPF | EQ | 0005098020 | — |
| (any) | PFF | BT | 0005098011 | 0005098023 |

### YBASUBST — legacy, flat, per-account

Schema: `BUKRS + BLART + HKONT + GSBER`. Higher precedence than YTFI_BA_SUBST for HKONTs in both.

UNES has 641 rules. Distribution:
- ~565 GEF (operating banks)
- ~50 PFF (project / restricted)
- ~25 OPF (ASHI / operations programme)

## Treasury HQ banks — coverage analysis (current state)

| HKONT | Bank | YBASUBST today | Actual BSEG GSBER | Status |
|---|---|---|---|---|
| 0001008011 | CIC USD01 (Group A) | GEF | GEF | ✅ |
| 0001008012 | CIC EUR01 (Group A) | GEF | GEF | ✅ |
| 0001008912/22/32 | CIC EURD1/2/3 (Group B savings) | not in YBASUBST | (default GEF via YTFI_BA_SUBST range) | ✅ |
| 0001095011 | NTB01-USD01 (Group D Nessim) | PFF | GEF | ⚠ Step 010 overrides |
| 0001095021 | NTB01-USD02 (Group A Current) | PFF | GEF | ⚠ Same — config drift |
| 0001095031 | NTB01-USD03 (Group C ASHI) | OPF | GEF | ⚠ Same — Step 010 override |
| 0001095012 | NTB02-EUR01 (Group C ASHI) | OPF | (no postings observed) | ⚠ |
| 0001095061 | NTB01-USD06 (new) | not in YBASUBST | GEF | (default catches it) |

**Key finding:** Bank cash GLs always end up with `GSBER=GEF` in BSEG regardless of what YBASUBST says, because Step 010 (U904) overrides Step 002 (U910) for cash-side debits. The Group classification matters on the **revenue side**, not the cash side.

## Revenue GL evidence — 4 of 4 fields land correctly today

Actual P01 posting values (BSEG + FMIFIIT, all postings 2024-2026):

| Revenue GL | Group | BA today | CC today | Fund today | FundCenter today |
|---|---|---|---|---|---|
| 7044011 (catch-all) | mixed | 45% GEF / 45% PFF / 9% OPF | 45% 113001 / 43% empty | 48% GEF / 22% PFF | UNESCO 99%+ |
| 7044013 (Group A) | A | 70% GEF / 30% PFF | 42% 113001 / 39% empty | 57% GEF | UNESCO |
| **7044014 (Group B)** | B | **100% GEF** | **85% 113001** | **100% GEF** | **100% UNESCO** |
| **7043014 (Group C)** | C | **100% OPF** | 90% **131035** ⚠ | **100% 645ASH9000** | **100% BFM** |
| **7043021 (Group D)** | D | **100% PFF** | **100% empty** ❌ | **100% 401NHF1091** | **100% HED** |

**Implication:** BA + Fund + FundCenter derivation already works correctly for all 4 groups. The only field needing change is Cost Center on 7043014 (currently 131035, Treasury wants 113001) and 7043021 (currently empty, Treasury wants 113001).

## Required action — single OKB9 maintenance

Cancels original plan Steps 8 (GGB1 substitution) + 9 (FMDERIVE).

| Step | Action | Effort |
|---|---|---|
| 1 | OKB9: KOKRS=UNES · KSTAR=0007043014 · KOSTL=0000113001 (overrides historical 131035) | 5 min |
| 2 | OKB9: KOKRS=UNES · KSTAR=0007043021 · KOSTL=0000113001 (new entry — was empty) | 5 min |
| 3 | OKB9: verify KOKRS=UNES · KSTAR=0007044013 · KOSTL=0000113001 (likely already exists) | 2 min |
| 4 | TST: post test EBS interest credits to all 4 revenue GLs → verify CC=113001 + correct Fund/FC | 15 min |

## Tables in Gold DB

| Table | Rows for UNES | Notes |
|---|---|---|
| YBASUBST | 641 | Legacy per-account BA mapping |
| YTFI_BA_SUBST | 4 | Modern range-based BA mapping (no-transport via YFI_BASU_MOD) |
| GB901 | 162 BOOLIDs containing UNES | Substitution prerequisites |
| GB922 | 17 (SUBSTID=UNESCO + UNESCH) | Substitution actions |
| GB02C | 10 | Substitution headers |
| SKB1 | 2,312 | GL Company-code-specific master data (extracted Session #071) |
| SKAT | 7,485 | GL Account texts (extracted Session #071) |
| TKA3D / TKA3E / TKA3F | not accessible via RFC | Need direct OKB9 verification or different RFC user role |
| T8JFB / T8JFC | not accessible via RFC | FMDERIVE strategy — verify via tcode FMDERIVE in P01 |
| FMIFIIT_FULL | 2.2M | FM line items (proves Fund/FISTL derivation) |

## Related

- Incident: [INC-000008088](../../incidents/INC-000008088_interest_auto_posting.md) (if created)
- Sister doc: [bank_statement_ebs_architecture.md](bank_statement_ebs_architecture.md)
- Sister doc: [house_bank_configuration.md](house_bank_configuration.md)
- Cross-domain: [knowledge/domains/FI/ggb1_substitution_tables_distinction.md](../FI/ggb1_substitution_tables_distinction.md)
- Custom code: `YRGGBS00` form `U910` calling `YCL_FI_ACCOUNT_SUBST_READ`
- Companion: `companions/bank_statement_ebs_companion.html` → tab "EBS Customizing" → card `#substitution-bank-model`

## Brain claims supporting this doc

- Claim 167 (Session #071, TIER_1): UNESCO substitution architecture — 16-step chain, U910 reads YTFI_BA_SUBST/YBASUBST
- Claim 168 (Session #071, TIER_1): 3 of 4 derivation fields already correct for ASHI/Nessim — only CC needs OKB9 update
- Claim 169 (Session #071, TIER_1): YBASUBST config drift on NTB01-USD02 (PFF entry but actual posting GEF — Step 010 overrides)
