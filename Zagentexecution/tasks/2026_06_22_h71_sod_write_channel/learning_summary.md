# Task learning summary — PMO H71 write-channel SoD (2026-06-22)

## What was done
Confirmed + quantified + designed remediation for the portal-as-user write-channel SoD finding.
Deliverable: `knowledge/domains/Security/h71_write_channel_sod_remediation.md` + claims #237–240.

## Artifacts
- `pull_agr_sod.py` — live P01 pull of AGR_USERS/AGR_1251/AGR_AGRS for the 7 SoD users → Gold DB
  `agr_users` + `agr_1251_sod`, plus `agr_sod_map.json` (per-user duties + granting roles + ACTVT).

## SAP / method learnings
1. **P01 secured `RFC_READ_TABLE` (SAIS wrapper) rejects `IN (...)` WHERE clauses** — error
   `OPTION_NOT_VALID … RFC_READ_TABLE with suspicious WHERE condition`. The long IN-list also splits across the
   72-char OPTIONS boundary, compounding it. **Fix: per-value equality loop** (`FIELD = 'x'`), one ROWSKIPS-free
   call each — same pattern the log accumulators use. (Extends `reference_p01_strg_columns_unreadable`.)
2. **`AGR_1251.ACTVT` is essential to avoid overclaiming** — a role can hold an auth object for DISPLAY (03) not
   change (01/02). The `YS:CA:D:MD_VNDR_BNK_DATA_:UBO` role looked like vendor-bank-change but is display-only.
   Always resolve ACTVT (and expand LOW..HIGH ranges) before calling a grant a "duty".
3. **Declared-vs-behavioral triangulation exposes custom-code holes.** S_STANTIC changed 6,972 vendors (CDHDR KRED)
   with **no `F_LFA1` grant** but `S_RFC=*` ⇒ the custom `ZBAPI_VENDOR_CHANGE` performs no vendor AUTHORITY-CHECK.
   Behavioral alone or declared alone would have missed it; the gap between them is the finding.
4. **Two vendor numbering schemes in P01:** portal-managed vendors are the `VS9…` account group (alphanumeric),
   classic vendors are numeric `0000…`. Both appear in RBKP/EKKO/BSAK. Join carefully (don't int-normalize VS9).
5. **Gold DB gap:** MSEG/MKPF absent → cannot attribute the GR poster, so same-PO same-user GR+IR self-match can't
   be proven (capability + dual activity ARE proven). Follow-up: pull MSEG.USNAM.

## Numbers (for reuse)
- Conflict 1 (Brasília): 20,573 BRL invoices = R$ 264.7M (~US$49M); 9,411 POs, 100% with GR.
- Conflict 2 (HQ ICTP): 5,084 controlled vendors, ~EUR 11.8M cleared AP (BSAK), 77,158 PR changes.
