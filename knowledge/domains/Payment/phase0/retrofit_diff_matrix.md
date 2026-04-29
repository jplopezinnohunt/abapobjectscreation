# Retrofit Diff Matrix — D01 alignment to P01 base
**Generated**: 2026-04-29T14:59:46.384097
**Total includes analyzed**: 51

## Goal

Establish P01 as the **canonical base** for UNESCO custom DMEE code, and produce the exact retrofit list to align D01.

Once D01 = P01 across all UNESCO custom code, we can safely apply the Pattern A fix and create V001 trees without risk of clobbering.

## CRITICAL (21)

| Include | Verdict | P01 (date) | D01 (date) | Detail |
|---|---|---|---|---|
| `YCL_IDFI_CGI_DMEE_DE==========CCDEF` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_DE==========CCIMP` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_DE==========CCMAC` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_DE==========CI` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_DE==========CM001` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_DE==========CO` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_DE==========CP` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_DE==========CT` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_DE==========CU` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_FR==========CM001` | D01_ONLY | - | 20240322 | Possible WIP — review with N_MENARD before deciding |
| `YCL_IDFI_CGI_DMEE_FR==========CM002` | P01_ONLY | 20240906 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CCDEF` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CCIMP` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CCMAC` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CI` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CM001` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CO` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CP` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CT` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `YCL_IDFI_CGI_DMEE_IT==========CU` | P01_ONLY | 20240305 | - | Must retrofit to D01 from P01 |
| `Z_DMEE_EXIT_TAX_NUMBER========FT` | D01_ONLY | - | 20190726 | Possible WIP — review with N_MENARD before deciding |

## HIGH (0)

_None._

## LOW (0)

_None._

## NONE (30)

| Include | Verdict | P01 (date) | D01 (date) | Detail |
|---|---|---|---|---|
| `YCL_IDFI_CGI_DMEE_FALLBACK====CCDEF` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CCIMP` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CCMAC` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CI` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CM001` | IDENTICAL | 20241128 | 20241122 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CM002` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CO` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CP` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CT` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FALLBACK====CU` | IDENTICAL | 20240906 | 20240301 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FR==========CCDEF` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FR==========CCIMP` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FR==========CCMAC` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FR==========CI` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FR==========CO` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FR==========CP` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FR==========CT` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_FR==========CU` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CCDEF` | IDENTICAL | 20240906 | 20240320 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CCIMP` | IDENTICAL | 20240906 | 20240320 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CCMAC` | IDENTICAL | 20240906 | 20240320 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CI` | IDENTICAL | 20240906 | 20240320 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CM001` | IDENTICAL | 20240906 | 20240320 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CM002` | IDENTICAL | 20240906 | 20240320 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CM003` | IDENTICAL | 20240906 | 20240703 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CM004` | IDENTICAL | 20240906 | 20240320 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CO` | IDENTICAL | 20240906 | 20240320 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CP` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CT` | IDENTICAL | 20240906 | 20240319 | Byte-by-byte equal |
| `YCL_IDFI_CGI_DMEE_UTIL========CU` | IDENTICAL | 20240906 | 20240321 | Byte-by-byte equal |

## Retrofit transport scope (D01-RETROFIT-01)

**19 includes need retrofit**:

- `YCL_IDFI_CGI_DMEE_DE==========CCDEF` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_DE==========CCIMP` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_DE==========CCMAC` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_DE==========CI` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_DE==========CM001` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_DE==========CO` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_DE==========CP` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_DE==========CT` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_DE==========CU` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_FR==========CM002` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CCDEF` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CCIMP` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CCMAC` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CI` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CM001` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CO` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CP` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CT` — P01_ONLY
- `YCL_IDFI_CGI_DMEE_IT==========CU` — P01_ONLY

**2 D01-only includes — need N_MENARD review**:

- `YCL_IDFI_CGI_DMEE_FR==========CM001` — D01 has it, P01 doesn't. WIP?
- `Z_DMEE_EXIT_TAX_NUMBER========FT` — D01 has it, P01 doesn't. WIP?

**30 includes safe to skip retrofit** (byte-equal or cosmetic blanks-only)
