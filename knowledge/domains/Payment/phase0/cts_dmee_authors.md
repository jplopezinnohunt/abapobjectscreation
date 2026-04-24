# CTS DMEE Author Map — 10-year history

**Phase 0 deliverable** · Session #62 · 2026-04-24 · Evidence tier: TIER_1 (parsed from `Zagentexecution/mcp-backend-server-python/cts_batch_2017.json` through `cts_batch_2026.json`)

## Summary

**53 DMEE-touching transports** across 10 years, **8 distinct authors**. The target trees (`/SEPA_CT_UNES`, `/CITI/XML/UNESCO/DC_V3_01`, `/CGI_XML_CT_UNESCO`, `/CGI_XML_CT_UNESCO_1`) are primarily owned by two people: Marlies Spronk (M_SPRONK, configuration) and Nicolas Ménard (N_MENARD, ABAP code).

## Author ranking (DMEE-touching only)

| Author | DMEE transports | Role | Primary focus |
|---|---|---|---|
| **M_SPRONK** (Marlies Spronk) | **31** | DMEE tree configuration (FI/TRS Treasury) | CITI DC_V3_01 (27), SEPA_CT_UNES (7), CGI (4), some overlap |
| **N_MENARD** (Nicolas Ménard) | **9** | ABAP BAdI code owner | `YCL_IDFI_CGI_DMEE_FALLBACK`/`_FR`/`_UTIL`/`_DE`/`_IT` class implementations |
| **FP_SPEZZANO** (Francesco Spezzano) | **5** | Unknown — 2025 Q1 cluster | `/CGI_XML_CT_UNESCO` + `_1` only, empty descriptions |
| **E_FRATNIK** | **4** | ICTP Trieste trees | `SEPA_CT_ICTP_ISO*` (out of our scope — ICTP separate) |
| **I_KONAKOV** | 1 | Config | (One-off) |
| **V.VAURETTE** | 1 | Unknown | (One-off) |
| **USER_SPDD** | 1 | SPDD / SPAU upgrade | (One-off) |
| **SM36623** | 1 | 2019 legacy | `CITIPMW/CITI_XML_V*` (legacy pre-cutover) |

## Correction to earlier Explore agent claim

Prior Explore agent reported "M_SPRONK authored **28** DMEE transports 2017-2024". Actual parsing: **31** (+3 diff). Sources: E_FRATNIK's transports were erroneously attributed to M_SPRONK OR the agent used a narrower keyword filter. This doc supersedes. Confirmed count: 31.

## M_SPRONK full DMEE transport list (31)

| Date | TRKORR | Tree(s) touched | obj_count |
|---|---|---|---|
| 2024-05-31 | D01K9B0BQG | CITI DC_V3_01 | 2 |
| 2024-03-26 | D01K9B0BL1 | /CGI_XML_CT_UNESCO | 15 |
| 2023-07-18 | D01K9B0AT1 | /CGI_XML_CT_UNESCO | 3 |
| 2023-06-19 | D01K9B0AO3 | /CGI_XML_CT_UNESCO | 3 |
| 2023-01-31 | D01K9B0A9D | CITI DC_V3_01 | 2 |
| 2022-12-20 | D01K9B0A1O | CITI DC_V3_01 | 2 |
| 2022-10-04 | D01K9B09P4 | CITI DC_V3_01 | 2 |
| 2022-08-03 | D01K9B09KD | CITI DC_V3_01 | 2 |
| 2022-06-24 | D01K9B09GL | CITI DC_V3_01 | 2 |
| 2022-06-21 | D01K9B09F3 | CITI DC_V3_01 | 2 |
| 2022-06-13 | D01K9B09E1 | CITI DC_V3_01 | 2 |
| 2022-05-11 | D01K9B097T | CITI DC_V3_01 | 2 |
| 2021-12-02 | D01K9B08GM | CITI DC_V3_01 | 1 |
| 2021-11-23 | D01K9B08DT | **SEPA_CT_UNES + DC_V3_01 (+ DIRECT_CREDIT)** | 7 |
| 2021-09-07 | D01K9B0810 | SEPA_CT_UNES + DC_V3_01 | 3 |
| 2021-09-03 | D01K9B080Q | CITI DC_V3_01 | 2 |
| 2021-08-31 | D01K9B080K | SEPA_CT_UNES + DC_V3_01 | 4 |
| 2021-07-06 | D01K9B07VI | (other) | 2 |
| 2021-06-21 | D01K9B07T6 | CITI DC_V3_01 | 2 |
| 2021-04-14 | D01K9B07HB | CITI DC_V3_01 | 2 |
| 2021-04-02 | D01K9B0601 | SEPA_CT_UNES + DC_V3_01 | 4 |
| 2021-04-02 | D01K9B0603 | CITI DC_V3_01 | 2 |
| 2020-04-30 | D01K9B0605 | CITI DC_V3_01 | 2 |
| 2020-02-07 | D01K9B04YK | CITI DC_V3_01 | 2 |
| 2020-02-07 | D01K9B05CI | SEPA_CT_UNES + DC_V3_01 | 4 |
| 2019-05-24 | D01K9B04Y6 | CITI DC_V3_01 | 5 |
| 2019-05-13 | D01K9B04LK | (other) | 2 |
| 2019-01-31 | D01K9B04F8 | (other) | 2 |
| 2018-09-19 | D01K9B03ZF | CITI DC_V3_01 | 2 |
| 2018-09-04 | D01K9B0393 | CITI DC_V3_01 | 6 |
| 2017-12-06 | D01K9B033V | CITI DC_V3_01 | 8 |

## N_MENARD DMEE transport list (9) — **critical: owns the BAdI code**

| Date | TRKORR | What | obj_count |
|---|---|---|---|
| 2024-11-22 | D01K9B0CEW | `YCL_IDFI_CGI_DMEE_FALLBACK` method `GET_CREDIT` | 2 |
| 2024-07-08 | D01K9B0BZ3 | CLAS `YCL_IDFI_CGI_DMEE_FALLBACK + _FR + _UTIL` | 46 |
| 2024-07-03 | D01K9B0BYP | METH `YCL_IDFI_CGI_DMEE_UTIL` `GET_TAG_VALUE_FROM_CUSTO` | 2 |
| 2024-07-02 | D01K9B0BXH | CLAS `YCL_IDFI_CGI_DMEE_FALLBACK + _FR + _UTIL` | 48 |
| 2024-06-21 | D01K9B0B5K | `/SEPA_CT_ICTP_ISO` tree (ICTP — out of scope) | 2 |
| 2024-03-26 | D01K9B0BN9 | CLAS `YCL_IDFI_CGI_DMEE_DE + _FR + _IT` | 54 |
| 2024-03-18 | D01K9B0BL9 | CLAS `YCL_IDFI_CGI_DMEE_FALLBACK` | 6 |
| 2024-01-10 | D01K9B0BDM | CLAS `YCL_IDFI_CGI_DMEE_DE + _IT + _FR` | 16 |
| (+ one ICTP transport from 2024-06-21) | | | |

**N_MENARD has implemented country-specific classes `_DE`, `_IT`, `_FR`** — the handoff doc mentioned `_AE` and `_BH` as "possibly not in P01". Correction: the brain has confirmed `_DE`, `_FR`, `_IT` exist; `_AE`/`_BH` presence is still GAP-003.

## Implications for the plan

1. **Marlies is the DMEE config SME** — she will execute the 17-step checklist of handoff §9. Her 31 prior transports confirm capability.
2. **N_MENARD is the BAdI code owner**. If the plan requires any ABAP change to `YCL_IDFI_CGI_DMEE_FALLBACK/_FR/_UTIL/_DE/_IT`, N_MENARD is the code reviewer. Plan addition: **N_MENARD as required reviewer for the new `Z_DMEE_UNESCO_DEBTOR_ADDR` FM** (Phase 2 step 9).
3. **The 2024-11 FALLBACK method update by N_MENARD** might have touched the StrtNm/Nm overflow logic we see in `YCL_IDFI_CGI_DMEE_FALLBACK_CM001.abap:13-31`. Worth confirming via git blame / D01 version compare in Phase 0.
4. **Francesco's 5 CGI transports** are not anomalies — they fit his small share of DMEE work but are the most recent activity on the target trees. Pre-Phase-2 alignment call recommended.
5. **E_FRATNIK's ICTP work is out of scope** — confirmed isolation.

## Claims to add to brain (Phase 0 output)

- `claim_marlies_31_dmee_transports`: TIER_1 — "M_SPRONK authored 31 DMEE transports 2017-2024 for /SEPA_CT_UNES + /CITI/XML/UNESCO/DC_V3_01 + /CGI_XML_CT_UNESCO trees, all Released"
- `claim_nmenard_badi_owner`: TIER_1 — "N_MENARD authored the UNESCO BAdI classes YCL_IDFI_CGI_DMEE_FALLBACK/_FR/_UTIL/_DE/_IT via 9 transports 2024"
- `claim_fp_spezzano_cgi_only`: TIER_1 — "FP_SPEZZANO touched /CGI_XML_CT_UNESCO + _1 in 5 transports 2025 Q1, never SEPA_CT_UNES or CITI/XML/UNESCO/DC_V3_01, all Released, all Workbench, descriptions empty"

## Data source

- `Zagentexecution/mcp-backend-server-python/cts_batch_YYYY.json` (10 files, 2017-2026, `meta.source_system = D01`)
- `meta.e070l_note`: "E070L not readable via RFC. Deploy level inferred from TRSTATUS."
