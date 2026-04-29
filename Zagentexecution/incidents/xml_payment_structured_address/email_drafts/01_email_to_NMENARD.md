**To**: Menard, Nicolas <n.menard@unesco.org>
**From**: Lopez, Julio Pablo Francisco <jp.lopez@unesco.org>
**Subject**: BCM Structured Address Nov 2026 — Phase 0 closed, your specs decoded, heads-up Phase 2 review

---

Hi Nicolas,

Thanks for sending the DMEE documentation last week. After analyzing the 3 docx files (TS DMEE CGI modifications + FS+TS Payment Purpose Code) along with the live P01 configuration, I want to share the conclusions and what's ahead.

## Specs decoded (no questions for you)

Your documents resolved several open points without needing alignment:

- **Pattern A overflow logic** (`YCL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT` lines 13-31) — your TS doc 29/02/2024 confirms this is the SocGen-mandated requirement (Name1 chars 36-40 prepended to StrtNm when name > 35 chars). The V001 design preserves this in V000 mode + adds a 3-line guard for V001 structured StrtNm. **No removal — A2 guard chosen.**
- **PPC system** (`YTFI_PPC_TAG/STRUC` + `YCL_IDFI_CGI_DMEE_UTIL::get_tag_value_from_custo`) — fully decoded from your FS+TS Payment Purpose Code docs. Algorithm replicated in Python, output matches your spec byte-for-byte (e.g., IN7 → `P1019;Other services not included elsewhere;INV;<XBLNR>`). **V001 must preserve the PPC tag dispatch on `<InstrInf>` and `<RmtInf><Ustrd>` nodes — confirmed in design.**
- **FR class CM001 (D01) vs CM002 (P01) "swap"** — verified: CM002 is the PPC dispatcher entry method that was added to P01 but never retrofit to D01. Same code, just CM002 calls UTIL→get_tag_value_from_custo. **Retrofit P01→D01 included in Phase 2 Step 0.**

## Phase 0 closure — what's been done

- **51 UNESCO custom DMEE includes** byte-by-byte compared D01 vs P01: 30 IDENTICAL, 19 P01-only (DE class + IT class + FR/CM002), 2 D01-only (FR/CM001 + Z_DMEE_EXIT_TAX_NUMBER 2019 leftover)
- **17 CITIPMW V3 FMs** extracted from P01 (full source)
- **794 production scenarios** (REGUH 2025+) sampled, V000 + V001 simulated end-to-end in Python, **2,382 XSD validations 100% PASS** against pain.001.001.03 + .09
- 30 sample XMLs (V000 + V001 pairs per tree) generated for inspection
- 99 evidence claims (TIER_1) recorded in our internal knowledge base

## Phase 2 sequencing (your review request)

1. **Step 0** — `D01-RETROFIT-01` transport: 22 objects (your DE/IT classes + FR/CM002 + 3 ENHO impls) brought back to D01 to align with P01
2. **Step 1** — `D01-BADI-FIX-01` transport: 3-line Pattern A2 guard at `YCL_IDFI_CGI_DMEE_FALLBACK_CM001::GET_CREDIT` — **needs your courtesy review (5 min)**
3. **Step 2-4** — V001 tree creation per `/SEPA_CT_UNES`, `/CITI/XML/UNESCO/DC_V3_01`, `/CGI_XML_CT_UNESCO` (+ `_1`)

The Pattern A2 fix:

```abap
WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'.
  IF i_fpayh = mv_fpayh
     AND mv_cdtr_name+35 IS NOT INITIAL
     AND c_value IS INITIAL.            "← V001 guard: only prepend if StrtNm empty
    c_value = mv_cdtr_name+35.
  ELSEIF i_fpayh = mv_fpayh AND mv_cdtr_name+35 IS NOT INITIAL.
    c_value = |{ mv_cdtr_name+35 } { c_value }|.   " V000 legacy preserved
  ENDIF.
  IF c_value+70 IS NOT INITIAL.
    CLEAR c_value+70.
  ENDIF.
```

It preserves V000 production behavior (overflow into AdrLine StrtNm) and only adds a guard when V001 is active (structured StrtNm filled). Your V000 SocGen-mandated logic is untouched.

## What I need from you (low-effort)

- **Courtesy ack** that the Phase 2 sequencing makes sense (Step 0 retrofit + Step 1 Pattern A2)
- When Phase 2 Step 1 transport (`D01-BADI-FIX-01`) is ready (~May 2026), **5-min review** of the 3-line guard before release
- If you remember any UNESCO-specific edge cases for vendor names > 35 chars or any quirk we should test in Phase 3, please flag

No alignment call needed unless you'd prefer one — happy to schedule 30 min if useful.

## What's still open (not blocking)

- **Q2** (technical curiosity): why 5 objects ended up P01-only when D01 was supposed to be in sync. If you remember the D01 refresh / transport history, helpful to capture; if not, no problem — we'll retrofit forward.

Detailed analysis available in our internal knowledge base if you want to dig deeper. Happy to send any specific artifact.

Best regards,
Pablo

---

**Attachments suggested** (optional, only if you want to walk through):
- Sample V000 + V001 XML pair for `/CGI_XML_CT_UNESCO` (Worldlink Madagascar scenario) — `simulator_output/CGI/sample_3_*.xml`
- Pattern A2 ABAP guard 3 lines (above)
- Phase 2 sequencing 1-pager
