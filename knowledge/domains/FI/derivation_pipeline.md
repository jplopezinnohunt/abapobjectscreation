# UNESCO FI Posting Derivation Pipeline · canonical reference

> **Brain anchor**: claims 176 + 177 (TIER_1, Session #71). This document is the authoritative cheat-sheet for ANY new HKONT or GL change that affects the FI posting chain at UNESCO. Read this BEFORE proposing any GL routing change to avoid the "No funds center" / "Cost center missing" error class.

## ⚠ PREREQUISITE · activate the Cost Element FIRST (claim 178)

**Before ANYTHING else in the chain runs, the GL must exist as a Cost Element in CSKB** for the controlling area:

```
TX KA01 (or via SE16 maintain CSKB)
   KOKRS=UNES + KSTAR=<GL>
   KATYP = 11 (Revenue) for income GLs · 1 (Primary expense) for expense
   DATAB ≤ posting date ≤ DATBI
```

If CSKB does NOT have the entry, OKB9 silently skips (no error), KOSTL stays blank, and downstream chain partially fails. **This is a per-system manual activation step** — transports do NOT always auto-create CSKB entries depending on TR contents. Verify CSKB exists in **D01 + V01 + P01** before declaring the change ready.

INC-8088 V01 evidence 2026-05-07: doc 3500000008 posted with KOSTL=blank because cost element 7044013 was not yet activated in V01. After activation, FB60 test showed all derivations correct.

---

## TL;DR

Each FI line item picks up its account-assignment fields through a deterministic chain. **Every field has ONE canonical derivation point**. If you introduce a new GL into the bank/interest pipeline, you must touch:

| Field | Derivation point | Mechanism |
|---|---|---|
| **KOSTL** (Cost Center) | **OKB9** (table TKA3D) | Customizing — TX OKB9 |
| **PRCTR** (Profit Center) | CSKS (Cost Center Master) — or OKB9 sub-folder "Detail per profit center" | Master data |
| **GSBER** (Business Area) | **GGB1 callup 3** Step 002 (U910) + Step 010 (U904) | Substitution — TX GGB1 |
| **FUND_CENTER** (FISTL) | **ZXFMDTU02_RPY** (FM user exit) | ABAP user-exit |
| **FUND** (FONDS) | **ZXFMDTU02_RPY** | ABAP user-exit |
| **WBS_ELEMENT** | **ZXFMDTU02_RPY** | ABAP user-exit |
| **BUS_AREA** override | ZXFMDTU02_RPY (for ASHI/Nessim only) | ABAP user-exit |
| **CHECT / GSBER override / ZUONR** (EBS) | EXIT_RFEBBU10_001 → YTBAM001 | ABAP user-exit (EBS-only) |

## Execution order at FI document creation

```
┌─────────────────────────────────────────────────────────────────┐
│ FI line item being posted (BSEG record forming)                 │
│ Required fields: HKONT, BUKRS, optional GSBER/KOSTL/PRCTR/etc.  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│ [1] OKB9 (TKA3D) lookup                              │
│      Key: KOKRS + KSTAR + BUKRS                      │
│      Output: KOSTL (default cost center)             │
│      If BArIn=ON: add per-GSBER override grid        │
│      (e.g., GEF→113001 / MBF→143001 / OPF→133001)    │
└──────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│ [2] CSKS (Cost Center Master)                        │
│      Once KOSTL set → reads CSKS for PRCTR, FAREA,   │
│      KOSTL-default GSBER, etc.                       │
└──────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│ [3] GGB1 callup 3 (FI Document Header / Line Item)   │
│      SUBSTID='UNESCO' → 16-step ordered chain        │
│      Step 002 Form U910 (YRGGBS00) → reads YBASUBST  │
│        + YTFI_BA_SUBST keyed by HKONT/HBKID/HKTID    │
│        → derives GSBER from bank account type        │
│      Step 010 Form U904 → overrides GSBER for cash   │
│        GLs (typically forces GSBER=GEF on bank GLs)  │
│      Other steps: BVTYP, PYCUR, XREF1, XREF2, ZLSCH, │
│        FDLEV, ZUONR='Reval. Sub-Bank' (literal)      │
└──────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│ [4] EXIT_RFEBBU10_001 → YTBAM001                     │
│      EBS-ONLY path (RFEBBU10 / FEB_FILE_HANDLING)    │
│      Modifies E_FEBEP-CHECT, E_FEBEP-GSBER (override),│
│        E_FEBEP-ZUONR for specific banks              │
│      Filter: BUKRS in (UNES, UBO, IIEP) + EFART='E'  │
│      Does NOT touch HKONT or KOSTL                   │
└──────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│ [5] FMDERIVE declarative rules (TX FMDERIVE)         │
│      Strategy IDs + rules — ran BEFORE the user exit │
│      Output: FUND, FISTL, FAREA, GRANT_NBR, etc.     │
└──────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│ [6] EXIT_SAPLFMDT_002 → ZXFMDTU02_RPY                │
│      User exit for FMDERIVE (THE FM derivation point)│
│      Hardcoded IF I_COBL-HKONT='xxx' blocks:         │
│        line  85-101: FX P&L (6045011/7045011/6045014)│
│                       → UNESCO + GEF                 │
│        line 119-132: ASHI (7043011-14)               │
│                       → BFM + 645ASH9000 + OPF       │
│        line 134-145: Nessim (7043021)                │
│                       → HED + 401NHF1091 + PFF       │
│                       + WBS_ELEMENT='401NHF1091'     │
│        line 152-170: Treasury interest               │
│                       (7044011/13/14)                │
│                       → CASE GSBER:                  │
│                          GEF → UNESCO + GEF          │
│                          MBF → UNESCO + MBF          │
│        line 173+:    7044012 → per-GSBER routing     │
│      Does NOT set KOSTL or PRCTR                     │
└──────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│ [7] Validations (GB901, GB903, T80D)                 │
│      Field-value validations on the final BSEG line  │
│      For INC-8088 GLs: 0 hits across all rules       │
└──────────────────────────────────────────────────────┘
                              │
                              ▼
                    BKPF + BSEG written
```

## Field ownership matrix · which mechanism owns each field

| Field | OKB9 | CSKS | GGB1 sub | YTBAM001 | ZXFMDTU02_RPY | FMDERIVE rules |
|---|---|---|---|---|---|---|
| **KOSTL** | ✅ owner | (master) | — | — | — | — |
| **PRCTR** | (sub-folder) | ✅ owner | — | — | — | — |
| **GSBER** | (BArIn read) | (master) | ✅ owner | (override EBS) | (override) | — |
| **FUND_CENTER** | — | — | — | — | ✅ owner | (declarative) |
| **FUND** | — | — | — | — | ✅ owner | (declarative) |
| **WBS_ELEMENT** | — | — | — | — | ✅ owner | (declarative) |
| **CHECT** | — | — | — | ✅ EBS only | — | — |
| **ZUONR** | — | — | (literal step) | (override EBS) | — | — |

## Common errors and where to fix

| Error message | Most likely cause | Fix location |
|---|---|---|
| "No funds center entered/derived in item XX" | HKONT missing in ZXFMDTU02_RPY IF block | Add IF block for HKONT in `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMDTU02_RPY.abap` |
| "Cost center missing" | KOSTL not set + OKB9 has no entry for cost element | TX OKB9 → add entry for KOKRS+KSTAR+BUKRS |
| "Profit center cannot be derived" | KOSTL set but CSKS has no PRCTR on that cost center | CSKS master data — TX KS02 |
| "Business area not entered/derived" | GGB1 substitution didn't fire OR YBASUBST has no row for the HBKID/HKTID | TX GGB1 → check Step 002/010 + maintain YBASUBST |
| "The difference is too large for clearing" | Posting rule (T028D/T033F) is type 4/5/8/9 instead of type 1 (post-only) | TX OT83 → Folder 4 → set Posting Type=1 |

## INC-8088 verified end-to-end · what was done

For each newly-routed GL (7044013 + 7044014 for SOG Group A/B split), the configuration was:

| Layer | Action | Verification |
|---|---|---|
| OT83 (T028B/G/D, T033F/G) | New VGTYP SOG_FRB + posting key 111B + acc symbol INTEREST_REC_B + mask redirects | RFC re-extract 2026-05-06 verified D01 matches canonical Excel |
| OKB9 (TKA3D) | New entries for 7044013 + 7044014 with BArIn=ON + grid (GEF=113001, MBF=143001, OPF=133001) | User screenshots 2026-05-07 in V01 confirm parity with 7044011 |
| ZXFMDTU02_RPY | Patch line 155 to add `OR I_COBL-HKONT='0007044013'` to Treasury IF block | User screenshot 2026-05-06 + V01 test post 7044014 OK |
| CSKS / PRCTR | No change — derived automatically via KOSTL | Inherited from cost center master |
| GGB1 | No change — chain produces correct GSBER for SOG (GEF) | claim 168 historical 100% GEF on Group A/B |

## Anti-patterns to avoid

1. **Hardcoded HKONT lists in user exits** (claim 30 anti-pattern): ZXFMDTU02_RPY accumulates IF blocks per HKONT range. Refactor target: Z-table `ZTFI_FUND_DERIV (BUKRS, HKONT, GSBER) → (FUND_CENTER, FUND, WBS_ELEMENT)` maintained via SM30. INC-000006073 + INC-000005240 are the same defect class.
2. **OKB9 with BArIn=OFF for new bank-related GLs**: forces single cost center regardless of GSBER → loses the per-fund-type granularity that 7044011 has. INC-8088 initially fell into this and was corrected 2026-05-07.
3. **Editing the parent VGTYP TR_TRNF**: shared by 30+ banks. Per-account VGTYP clones (NT_NESS, NT_ASHIU, etc.) are safer for Phase 2.
4. **Forgetting the EBS path** when changing FI derivation: YTBAM001 has its own override logic that runs only for RFEBBU10. Test in V01 with FF.5 + a real MT940 file, not just FB01 manual posting.

## References

- Source code: `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMDTU02_RPY.abap`
- OKB9 screenshots: `companions/img/okb9/01..06_okb9_*.png`
- Brain claims: 176 (OKB9 = Cost Center derivation), 177 (full pipeline reference), 175 (ZXFMDTU02_RPY = FundCenter), 30 (hardcoded-literal anti-pattern), 27/28 (FX P&L hardcode evidence)
- KU-2026-071-13: TKA3D not yet extracted to Gold DB
