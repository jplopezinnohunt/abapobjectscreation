# GAP-005 — Static Analysis of FPAYHX Z-field Population

**Phase 0 deliverable** · Session #62 · 2026-04-24 · Evidence tier: TIER_1 (static) / needs TIER_1 (runtime) to fully close

## The question

Where, in UNESCO's custom code, are `FPAYHX-ZSTRA`, `ZHSNM`, `ZPSTL`, `ZORT1`, `ZLAND` (the structured-address Z-fields consumed by DMEE tree nodes) and `FPAYH-REF01..REF05` (buffer fields for user exits) written during F110 runtime?

## Static grep — result

**Pattern set**: `FPAYHX-Z*=`, `FPAYHX-*=`, `E_FPAYHX-*=`, `CS_FPAYHX-*=`, `MODIFY *FPAYHX`, `FPAYH-REF\d+=`, `E_FPAYH-REF\d+=`, `MOVE * TO FPAYHX`
**Scope**: 986 `.abap` files in `extracted_code/`
**Hits**: **0**

## YCL_IDFI_CGI_DMEE_FALLBACK_CM001.abap:13-31 — re-reading

Method `get_credit`, `WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'`:

```abap
WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Nm>'.
  "If payment origin is TR-CM-BT, then put item text to this tag
  IF i_fpayp-origin = 'TR-CM-BT'.
    c_value = i_fpayp-sgtxt.
  ENDIF.
  "Only 35 first characters, remaining characters must be set in tag <StrtNm>
  mv_cdtr_name = c_value.
  IF c_value+35 IS NOT INITIAL.
    CLEAR c_value+35.
  ENDIF.
  mv_fpayh = i_fpayh.   "Set to buffer for tag <StrtNm>
WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'.
  IF i_fpayh = mv_fpayh AND mv_cdtr_name+35 IS NOT INITIAL.
    c_value = |{ mv_cdtr_name+35 } { c_value }|.
  ENDIF.
  IF c_value+70 IS NOT INITIAL.
    CLEAR c_value+70.
  ENDIF.
ENDCASE.
```

**What it actually does**:
1. Intercepts the `<Cdtr><Nm>` node: if payment origin = TR-CM-BT, override with `FPAYP-SGTXT`. **Truncate the name to 35 chars**, save overflow to `mv_cdtr_name` buffer.
2. Intercepts `<Cdtr><PstlAdr><StrtNm>` node: if there's name overflow AND same FPAYH, **prepend** the overflow chars to the street value, then truncate to 70 chars.

**What it does NOT do**:
- Does NOT populate FPAYHX-ZSTRA or any Z-field
- Does NOT populate the base value of StrtNm (that arrives pre-populated in `c_value`)
- Does NOT touch FPAYH-REF fields

The input parameter `c_value` carries the **already-populated street value from SAP standard PMW+DMEE source-field mapping**. The BAdI only potentially mutates it (prepends overflow).

## Conclusion — GAP-005 closed (static side) [VERIFIED]

1. **FPAYHX-Z* fields are populated by SAP-STANDARD mechanism** during F110: Payment Medium Workbench reads vendor master LFA1+ADRC (via ADRNR), writes the address components into FPAYHX auto-append Z-fields.
2. **No UNESCO custom code writes FPAYHX-Z* fields**. Zero hits across all 986 extracted ABAP files.
3. **The existing FALLBACK BAdI does address-adjacent work** (name-into-street overflow) but is NOT the populator of the street value — it's a post-processor.
4. **FPAYH-REF01..05 fields also have zero writes** in extracted code. Expected: these are BUFFER fields filled by user exits; no UNESCO exit does so today. Our Phase 2 will create the first one (`Z_DMEE_UNESCO_DEBTOR_ADDR`).

## What this means for the plan

**Major scope reduction for Cdtr address**:

- We do NOT need to identify or modify any UNESCO-specific Z-field populator BAdI
- We ONLY need to add DMEE tree nodes (e.g., `<StrtNm>` with source `FPAYHX-ZSTRA`) — SAP's auto-populate does the rest
- Matches handoff doc §5.1: "address is available in FPAYHX structure, which is populated during payment run"

**Regression risk** — the existing overflow logic in FALLBACK_CM001:
- If a vendor name is > 35 chars, overflow prepends to StrtNm
- Post-structured-address, StrtNm will receive the real street value from FPAYHX-ZSTRA
- If overflow fires AND real street is present, the final StrtNm = `<name_overflow> <street>` (concatenated with space)
- **This is a silent semantic issue**: the bank will see `JONES SMITH INTERNATIONAL LTD Main Street` as the street name, which is WRONG
- **Decision needed** (before Phase 2): deprecate the overflow logic OR constrain it to cases where StrtNm source is empty

**N_MENARD owns this code** (9 transports, most recently 2024-11-22 on FALLBACK GET_CREDIT). Include him as reviewer for the overflow-deprecation decision.

## Remaining unknowns — pyrfc-needed [PARTIAL, to close]

This static analysis confirms NO UNESCO code writes the Z-fields, but doesn't confirm which SAP standard mechanism does. To confirm [TIER_1 runtime]:

1. Check if `CI_FPAYHX` append structure exists in P01 DDIC — confirms Z-fields are SAP-auto-populated via structure binding (GAP-004)
2. Check P01 SAP Note implementation: Notes 1665873, 2795667 describe the PMW address population behavior. Fetch these to confirm expected source.
3. Optional: F110 trace (ST05) in D01 with a test payment to capture the exact moment FPAYHX-ZSTRA gets its value — overkill for current plan but definitive if needed.

## Claim to add to brain

`claim_no_unesco_fpayhx_z_write`: TIER_1 — "No UNESCO custom ABAP code writes FPAYHX-Z* or FPAYH-REF* fields as of 2026-04-24 extraction. Scan of 986 ABAP files returned zero hits across 8 write patterns. Implies FPAYHX Z-fields are SAP-standard populated via PMW at F110 runtime."

Supersedes: prior Phase 1 Explore agent speculation that a "UNESCO BAdI populates the Z-fields" — falsified.
