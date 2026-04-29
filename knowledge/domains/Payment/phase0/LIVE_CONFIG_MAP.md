# LIVE Configuration Map — Vendor → File → Bank (P01 anchored, all connected)

**Generated**: 2026-04-29 · **Anchored on P01 production data**

> User directive: "Saber cuál es la configuración VIVA, qué direcciona a los files que tenemos que modificar y los programas y objetos. Todo debe estar conectado."

---

## The complete chain (1 figure)

```
[VENDOR LFA1]               LFA1.LIFNR + LAND1 + ADRC.STREET/CITY/COUNTRY
  + [LFB1 per co]           LFB1.BUKRS + ZWELS (allowed methods) + HBKID (preferred)
  + [LFBK vendor bank]      LFBK.BANKS (vendor's bank country) + BANKL/BANKN
        ↓
[F110 PROPOSAL] picks open items from BSEG/BSIK matching LFB1.ZWELS
        ↓
[HOUSE BANK DERIVATION]     T042I (ZBUKR + ZLSCH + WAERS) → HBKID + HKTID
        ↓                   T012K (BUKRS + HBKID + HKTID + WAERS) → bank account
[TREE DETERMINATION]        T042Z (LAND1=co.country, ZLSCH=method) → FORMI = DMEE tree
        ↓
[REGUH row created]         per (LAUFD, LAUFI, ZBUKR, LIFNR) with RZAWE+HBKID+HKTID+UBNKS+WAERS
        ↓
[DMEE TREE TRAVERSAL]       DMEE_TREE_NODE rows in active V000
        ↓
[EVENT 05 hook] (CGI+CITI)  TFPM042FB.FNAME → fires PRE-traversal:
                              · FI_PAYMEDIUM_DMEE_CGI_05  (CGI x2 + BK)
                              · /CITIPMW/V3_PAYMEDIUM_DMEE_05  (CITI tree)
                              · NONE for /SEPA_CT_UNES
                            ↓ populates FPAYHX_FREF buffer (REF01..REF15)
        ↓
[PER-NODE EXIT_FUNC]        DMEE_TREE_NODE.MP_EXIT_FUNC fires per node
                              · 26 CITIPMW V3 FMs on CITI tree
                              · 4 SAP-std DMEE_EXIT_SEPA_* on SEPA tree
                              · 1 BAdI dispatcher FI_CGI_DMEE_EXIT_W_BADI on CGI x2
                              · ZDMEE_EXIT_SEPA_21, Z_DMEE_EXIT_TAX_NUMBER (custom)
        ↓
[BAdI DISPATCHER] (CGI only) FI_CGI_DMEE_EXIT_W_BADI per node
                              ↓ filter on flt_val_country = vendor bank country
                              · YCL_IDFI_CGI_DMEE_FALLBACK  (default)
                              · YCL_IDFI_CGI_DMEE_FR    (if vendor bank=FR)
                              · YCL_IDFI_CGI_DMEE_DE    (if vendor bank=DE) ← P01-only
                              · YCL_IDFI_CGI_DMEE_IT    (if vendor bank=IT) ← P01-only
        ↓
[XSLT POST-PROCESS] (CITI only)  CGI_XML_CT_XSLT removes empty elements
        ↓
[FILE WRITE]                \\hq-sapitf\SWIFT$\P01\input\<formi>_<batchno>.xml
        ↓
[BCM BATCH]                 OBPM5 + TFIBLMPAYBLOCK (wildcard route → workflow 90000003)
        ↓
[APPROVAL] PD signatory rules → BNK_BATCH_HEADER status flow
        ↓
[SWIFT] Alliance Lite2 → bank
```

---

## Section A — Vendor → House bank derivation chain

### A.1 — Per-co-code house bank derivation rules (T042I, 77 rows)

Rule key: `(ZBUKR, HBKID, ZLSCH, WAERS) → HKTID` (house bank account)

| Co code | LAND1 | Default HBKID | Methods → bank+account |
|---|---|---|---|
| **ICTP** | IT | UNI01 | All methods (1/2/4/5/6/E/F/G/H/I/J/K/M/O/R/S/U) → UNI01 EUR01 (or EUR02 for K) |
| **IIEP** | FR | SOG01 (USD), SOG02 (EUR) | F/M/N/USD → SOG01; E/G/J/M/S/EUR → SOG02 EUR06 |
| **UBO** | BR | BRA01 (default), CIT01 (Q/R Worldlink) | B/C/D/G/H/I/J/P/T → BRA01 BRL01; **Q/R → CIT01 BRL01** |
| **UIL** | DE | SOG05 | N (EUR or USD) → SOG05 EUR01/USD01; S/EUR → SOG05 EUR01 |
| **UIS** | CA | CIT01 | 3/C/K/M/N (CAD or USD) → **CIT01 CAD01 or USD01** |
| **UNES** | FR | SOG01 (default), CIT04 (USD), CIT21 (CAD), SOG03 (other currencies) | 5/L/N/X+USD → CIT04 USD04; C+CAD → CIT21; 4/J/S+EUR → SOG01; N+other currency → SOG03 (AUD/CHF/DKK/GBP/JPY); 3+MZN → ECO09 |

**Insight A.1**: T042I is the **canonical house bank derivation table**. Per (paying co code, payment method, currency) it produces the exact HBKID that emits the file. Derivation is **multi-currency aware**.

### A.2 — Cross-reference to actual REGUH traffic (validation)

| HBKID | Co code in T042I | Top REGUH counterpart | Match |
|---|---|---|---|
| SOG01 | UNES (4/J/S+EUR), IIEP (F/M/N+USD) | UNES SOG01 = 488K, IIEP SOG01 = 1,871 | ✅ Confirmed |
| CIT04 | UNES (5/L/N/X+USD) | UNES CIT04 = 61,053 | ✅ |
| CIT01 | UIS (multi+CAD/USD), UBO (Q/R+BRL) | UBO CIT01 = 73,520, UIS CIT01 = 2,440 | ✅ |
| SOG03 | UNES (N+AUD/CHF/DKK/GBP/JPY) | UNES SOG03 = 8,701 | ✅ |
| SOG02 | IIEP (E/G/J/M/S+EUR) | IIEP SOG02 = 7,092 | ✅ |
| BRA01 | UBO (B/C/D/G/H/I/J/P/T+BRL) | UBO BRA01 = 1,316 | ✅ but low — most UBO uses CIT01 |
| UNI01 | ICTP (all methods) | ICTP UNI01 = 23,564 | ✅ but ICTP is OUT of our 4-tree scope |
| SOG05 | UIL (N/S) | UIL SOG05 = 9,461 | ✅ |
| CIT21 | UNES (C+CAD) | UNES CIT21 = 4,629 | ✅ |
| ECO09 / UBA01 | UNES (3+MZN) | tail traffic | ✅ |

**Insight A.2**: T042I rules match actual REGUH traffic. The configuration is consistent with production behavior.

---

## Section B — House bank → DMEE tree determination

### B.1 — T042Z routing (4 in-scope trees + bonus)

| Co code's LAND1 | ZLSCH | FORMI (tree) | XBKKT | XSTRA | TEXT1 |
|---|---|---|---|---|---|
| FR | S | `/SEPA_CT_UNES` | X | X | SEPA Payment |
| DE | S | `/SEPA_CT_UNES` | X | X | SEPA Payment (UIL) |
| FR | C | `/CITI/XML/UNESCO/DC_V3_01` | X | X | CITI USD core |
| FR | L | `/CITI/XML/UNESCO/DC_V3_01` | X | X | CITI variant L |
| FR | X | `/CITI/XML/UNESCO/DC_V3_01` | X | (vacío) | CITI UNES treasury |
| CA | C | `/CITI/XML/UNESCO/DC_V3_01` | X | X | CITI Canada |
| CA | N | `/CITI/XML/UNESCO/DC_V3_01` | X | X | CITI Canada N |
| BR | Q | `/CITI/XML/UNESCO/DC_V3_01` | X | X | Worldlink BRL Q |
| BR | R | `/CITI/XML/UNESCO/DC_V3_01` | X | X | Worldlink BRL R |
| FR | A | `/CGI_XML_CT_UNESCO` | X | (vacío) | Treasury Transfers |
| FR | J | `/CGI_XML_CT_UNESCO` | X | X | Euro Payment outside SEPA-zone |
| FR | N | `/CGI_XML_CT_UNESCO` | X | X | Payments outside US non-EUR |
| DE | N | `/CGI_XML_CT_UNESCO` | X | X | UIL International Payments |

**Insight B.1**:
- `XBKKT='X'` = DMEE-enabled (emits via BCM/DMEE) — applies to all in-scope rows
- `XSTRA='X'` = structured address indicator on (most rows)
- **One row WITHOUT XSTRA**: FR+A "Treasury Transfers" → routes to CGI but currently emits Dbtr only `<Ctry>` (Marlies row 10 case)

### B.2 — Active version per tree

| Tree | Active V | Last user | Last date | Total nodes | XSLT |
|---|---|---|---|---|---|
| `/SEPA_CT_UNES` | 000 | M_SPRONK | 2021-11-23 | 95 | (none) |
| `/CITI/XML/UNESCO/DC_V3_01` | 000 | M_SPRONK | 2023-01-31 | 610 | CGI_XML_CT_XSLT |
| `/CGI_XML_CT_UNESCO` | 000 | FP_SPEZZANO | 2025-03-20 | 631 | (none) |
| `/CGI_XML_CT_UNESCO_1` | 000 | FP_SPEZZANO | 2025-02-14 | 639 | (none) |
| `/CGI_XML_CT_UNESCO_BK` | 000 | (TBD) | TBD | TBD | TBD |

---

## Section C — Per-tree complete program/object inventory

### C.1 — `/SEPA_CT_UNES` (SocGen EUR/USD, no Event 05)

| Layer | Object | Role | What V001 changes |
|---|---|---|---|
| **Tree config** | DMEE_TREE_NODE (95 rows) | Native SEPA tree structure | **Add** TECH PstlAdr switch + 5 structured nodes (StrtNm/BldgNb/PstCd/TwnNm/Ctry) |
| **Event 05** | NONE | n/a | **Add** registration if needed (Sub-option A) |
| **MP_EXIT_FUNC** | `DMEE_EXIT_SEPA_31`, `DMEE_EXIT_SEPA_41`, `DMEE_EXIT_SE_DATE`, `ZDMEE_EXIT_SEPA_21` | Date + amount + currency exits | NO change |
| **BAdI dispatcher** | NOT used (no FI_CGI_DMEE_EXIT_W_BADI on SEPA) | n/a | NO change |
| **Country class** | NOT triggered on SEPA | n/a | NO change |
| **XSLT** | NONE | n/a | NO change |
| **Source data** | FPAYHX-ZPFST (street), FPAYHX-ZLISO (country), FPAYHX-ORT1Z (city) | Currently `<Ctry>` + 3×`<AdrLine>` | **Restructure** to emit StrtNm/TwnNm/Ctry (with optional PstCd) |

**Conclusion C.1**: SEPA = simple add-5-nodes (V001). ZERO ABAP changes. Sub-option A (register Event 05 FM) optional.

### C.2 — `/CITI/XML/UNESCO/DC_V3_01` (Citi USD + Worldlink, XSLT post-process)

| Layer | Object | Role | What V001 changes |
|---|---|---|---|
| **Tree config** | DMEE_TREE_NODE (610 rows) | CITI XML CGI v3.01 | **Add** structured Dbtr nodes (5 tags) |
| **Event 05** | `/CITIPMW/V3_PAYMEDIUM_DMEE_05` | Pre-populates FPAYHX_FREF for Dbtr (byte layout matches SAP-std GENERIC) | NO change to FM (we add tree nodes only) |
| **MP_EXIT_FUNC** | 26 CITIPMW V3 FMs | See list below | NO change to FMs |
| **BAdI dispatcher** | NOT used | n/a | NO change |
| **Country class** | NOT triggered on CITI | n/a | NO change |
| **XSLT** | `CGI_XML_CT_XSLT` (SAP-std, ID-DMEE devclass) | Removes empty elements (lets V001 add nodes unconditionally — XSLT auto-suppresses empties) | NO change |
| **UltmtCdtr Worldlink** | Dispatcher Cdtr exits handle most | Q3 unresolved for UltmtCdtr (deferred to V002) | DEFER |

**26 CITIPMW V3 FMs at MP_EXIT_FUNC**:
| FM | Role |
|---|---|
| /CITIPMW/V3_CGI_BANK_NAME | Bank name override |
| /CITIPMW/V3_CGI_CRED_PO_CITY | Cdtr PO Box city |
| /CITIPMW/V3_CGI_CRED_REGION | Cdtr region |
| /CITIPMW/V3_CGI_CRED_STREET | Cdtr street |
| /CITIPMW/V3_CGI_REGULATORY_INF | Regulatory Info |
| /CITIPMW/V3_CGI_TAXAMT_TTLAMT | Tax total amount |
| /CITIPMW/V3_CGI_TAX_CATEGORY | Tax category |
| /CITIPMW/V3_CGI_TAX_CTGRY_DTLS | Tax category details |
| /CITIPMW/V3_CGI_TAX_FORMS_CODE | Tax forms code |
| /CITIPMW/V3_CGI_TAX_METHOD | Tax method |
| /CITIPMW/V3_DMEE_EXIT_CGI_XML | Generic CGI XML exit |
| /CITIPMW/V3_DMEE_EXIT_INV_DESC | Invoice description |
| /CITIPMW/V3_EXIT_CGI_CRED_CITY | Cdtr city |
| /CITIPMW/V3_EXIT_CGI_CRED_NAME | Cdtr name |
| /CITIPMW/V3_EXIT_CGI_CRED_NM2 | Cdtr name 2 |
| /CITIPMW/V3_EXIT_CGI_CRED_NM3 | Cdtr name 3 |
| /CITIPMW/V3_EXIT_CGI_CRED_NM4 | Cdtr name 4 |
| /CITIPMW/V3_EXIT_CGI_DEBT_NAME | Dbtr name |
| /CITIPMW/V3_EXIT_CGI_TAX_SQNB | Tax sequence |
| /CITIPMW/V3_EXIT_CGI_TP_WHT | Withholding tax |
| /CITIPMW/V3_GET_CDTR_BLDG | Cdtr building number |
| /CITIPMW/V3_GET_CDTR_EMAIL | Cdtr email |
| /CITIPMW/V3_GET_CDTR_MOBILE | Cdtr mobile |
| /CITIPMW/V3_POSTALCODE | Postal code |
| /CITIPMW/V3_TAXAMT_TXBASEAMT | Tax base amount |
| /CITIPMW/V3_WL949_BIC_OR_ID | Worldlink BIC/ID lookup |

**Conclusion C.2**: CITI tree = add Dbtr structured nodes only. XSLT post-process protects against empty `<BldgNb/>` etc. No FM changes.

### C.3 — `/CGI_XML_CT_UNESCO` + `_1` + `_BK` (CGI multi-bank, BAdI dispatcher fires)

| Layer | Object | Role | What V001 changes |
|---|---|---|---|
| **Tree config** | DMEE_TREE_NODE (631 + 639 + ?) | CGI XML CT format | **Fix** CdtrAgt structured nodes (Marlies row issue) |
| **Event 05** | `FI_PAYMEDIUM_DMEE_CGI_05` | SAP-std FM thin wrapper → cl_idfi_cgi_call05_factory | NO change |
| **Factory dispatcher** | `cl_idfi_cgi_call05_factory` | Routes to country class by `flt_val_country` | NO change |
| **SAP-std country classes** | 18 active (FR/US/IT/DE/GB/BE/ES/CA/CH/CN/AU/MX/PL/DK/PT/AT/SE/LT) + GENERIC | Fill FPAYHX_FREF + FPAYP_FREF | NO change |
| **MP_EXIT_FUNC** | `FI_CGI_DMEE_EXIT_W_BADI` | The BAdI dispatcher itself called per node | NO change |
| **BAdI implementations** | `YCL_IDFI_CGI_DMEE_FALLBACK` + FR + DE + IT (UNESCO custom) | Override XML node values | **Pattern A fix** (3 lines in FALLBACK CM001) |
| **BAdI ENHO wire-up** | `Y_IDFI_CGI_DMEE_COUNTRY_FR`, `Y_IDFI_CGI_DMEE_COUNTRIES_DE/FR/IT` | Register Y classes for BAdI dispatch | NO change after retrofit |
| **XSLT** | NONE | n/a | NO change |

**Conclusion C.3**: CGI = small node fixes (CdtrAgt) + Pattern A 3-line BAdI fix.

---

## Section D — Country dispatcher concept — WHERE it applies

### D.1 — When does YCL_IDFI_CGI_DMEE_<country> fire?

```
[FI_CGI_DMEE_EXIT_W_BADI is registered as MP_EXIT_FUNC ONLY on /CGI_XML_CT_UNESCO + _1]
  ↓ per DMEE node, BAdI fires
  ↓ filter flt_val_country = vendor bank country (LFBK.BANKS)
  ↓
  if filter='FR' → YCL_IDFI_CGI_DMEE_FR
  if filter='DE' → YCL_IDFI_CGI_DMEE_DE  ← P01-only retrofit needed
  if filter='IT' → YCL_IDFI_CGI_DMEE_IT  ← P01-only retrofit needed
  else → YCL_IDFI_CGI_DMEE_FALLBACK
```

**The FR/DE/IT classes ONLY fire on CGI tree** (not SEPA, not CITI).

### D.2 — Volume per country dispatcher (CGI tree only)

Adjusted from full P01 traffic to CGI-tree subset (~27K T042Z routings × pay_method):

| Vendor bank country | Estimated CGI tree volume (proxy) | Dispatcher fires | Class status |
|---|---|---|---|
| FR | 6-10K (UNES treasury via FR+A/J/N) | FR class | ✅ in D01+P01 |
| DE | 5-8K (UIL Hamburg + UNES) | **DE class** | ⚠️ **P01 only — needs retrofit** |
| IT | 2-4K (UNES via FR+J Euro outside SEPA) | **IT class** | ⚠️ **P01 only — needs retrofit** |
| Other | various | FALLBACK | ✅ in both |

**Note**: Exact CGI-tree volume requires REGUH_FULL JOIN with T042Z (in progress). Current numbers are estimates from drill-down patterns.

### D.3 — 18 SAP-std dispatchers (cl_idfi_cgi_call05_factory) — VOLUME-based ranking

These fire on Event 05 PRE-tree (FI_PAYMEDIUM_DMEE_CGI_05) populating FPAYHX_FREF — DIFFERENT from the BAdI dispatcher:

| Active dispatchers (P01 traffic) | Vendor bank country count | Test scope |
|---|---|---|
| FR (148K), US (38K), IT (22K), DE (20K), GB (9K) | 5 countries — **must test** | Tier 1 |
| BE (7K), ES (7K), CA (5K), CH (2.5K), CN (2.3K), AU (1.7K), MX (1.6K) | 7 countries — high usage | Tier 2 |
| PL, DK, PT, AT, SE, LT (100-1000) | 6 countries — moderate | Tier 3 |
| BG, CZ, EE, HK, HR, IE, LU, RO, SK, TW (zero traffic) | 10 — DEAD | **Skip in test matrix** |

**Insight D**: Two dispatcher mechanisms exist:
1. **Event 05 FM dispatcher** (cl_idfi_cgi_call05_factory) — fires once per F110 run for CGI/CITI trees, populates buffer
2. **Per-node BAdI dispatcher** (FI_CGI_DMEE_EXIT_W_BADI) — fires per DMEE node on CGI tree only, mutates output

The DEAD/ACTIVE classification (Section 1.5) is for #1. The retrofit-needed DE/IT/FR custom classes are for #2.

---

## Section E — V001 change locus per tree (where to modify)

### E.1 — `/SEPA_CT_UNES` V001

| Change point | Where | What |
|---|---|---|
| Add 5 structured PstlAdr nodes (Dbtr) | DMEE_TREE_NODE V001 | StrtNm, BldgNb, PstCd, TwnNm, Ctry |
| Add 5 structured PstlAdr nodes (Cdtr) | DMEE_TREE_NODE V001 | Same as Dbtr |
| Source field mapping | FPAYHX-ZPFST/ZLISO/ORT1Z + REF01..05 | Read from buffer |
| Empty-element suppression | DMEE_TREE_COND | Per-node IF source IS NOT INITIAL |
| Optional Sub-option A | TFPM042FB | Add Event 05 FM if found compatible |
| **NO ABAP CHANGES** | n/a | Pure config |

### E.2 — `/CITI/XML/UNESCO/DC_V3_01` V001

| Change point | Where | What |
|---|---|---|
| Add structured Dbtr nodes | DMEE_TREE_NODE V001 | 5 tags read from FPAYHX_FREF |
| Cdtr already structured | NO change | CITIPMW V3 FMs already populate |
| UltmtCdtr Worldlink | DEFERRED to V002 | Q3 unresolved |
| **NO ABAP CHANGES** | n/a | Pure config |

### E.3 — `/CGI_XML_CT_UNESCO` + `_1` V001

| Change point | Where | What |
|---|---|---|
| Fix CdtrAgt structured nodes | DMEE_TREE_NODE V001 | Marlies row issue |
| Pattern A guard | YCL_IDFI_CGI_DMEE_FALLBACK CM001 lines 13-31 | Add `c_value IS INITIAL` guard |
| **REQUIRES**: D01-RETROFIT-01 transport first | YA package | DE/IT classes + 3 ENHO + FR/CM002 |

---

## Section F — File output path

| Tree | Output path | Filename pattern |
|---|---|---|
| All in-scope trees | `\\hq-sapitf\SWIFT$\P01\input\` | `<formi>_<batch>.xml` |

Job: `ZWFPAYM_RUN` (custom) submits via SUBMIT statement with FORMI and batch ID. Then BCM picks up via OBPM5/TFIBLMPAYBLOCK wildcard.

---

## Section G — What stays IN PRODUCTION untouched

| Component | Reason |
|---|---|
| V000 of all 4 trees | Stays active until Phase 5 cutover |
| All 17 CITIPMW V3 FMs | Used as MP_EXIT_FUNC in CITI V000 + V001 (no FM change) |
| `FI_PAYMEDIUM_DMEE_CGI_05` + factory + SAP-std country classes | SAP-std, no change |
| `FI_CGI_DMEE_EXIT_W_BADI` registration | Dispatcher mechanism unchanged |
| 4 SAP-std DMEE_EXIT_SEPA_* | No change |
| ZDMEE_EXIT_SEPA_21, Z_DMEE_EXIT_TAX_NUMBER | Custom Z FMs untouched |
| TFPM042FB Event 05 registrations | No change (Sub-option C only if SEPA needs new) |
| OBPM5 / TFIBLMPAYBLOCK / Workflow 90000003 | BCM unchanged |
| XSLT CGI_XML_CT_XSLT | No change (SAP-std, devclass=ID-DMEE) |
| File output path \\hq-sapitf\SWIFT$\P01\input\ | No change |

---

## Section H — Summary of "what to modify" by phase

| Transport | What changes | Risk |
|---|---|---|
| `D01-RETROFIT-01` | 22 UNESCO custom objects (P01→D01 alignment) | LOW (already in P01 prod) |
| `D01-BADI-FIX-01` | FALLBACK CM001 3-line guard (Pattern A) | LOW (additive guard, V000 backward-compatible) |
| `D01-DMEE-V001-SEPA` | Tree V001 node additions + conditions | LOW (V000 stays active) |
| `D01-DMEE-V001-CITI` | Tree V001 node additions for Dbtr | LOW |
| `D01-DMEE-V001-CGI` | Tree V001 + CdtrAgt node fix | LOW |
| `D01-OBPM4-SEPA-EVENT05` | Optional 1-row TFPM042FB if Sub-option A | LOW |

---

## Cross-reference

- Brain claims: 65, 80-93
- Feedback rule: 98 (P01 canonical)
- Source code: `extracted_code/FI/DMEE_full_inventory/` + `extracted_code/FI/DMEE_p01_canonical/`
- Drift artifacts: `phase0/d01_vs_p01_drift_*.md`
- PM artifacts: `phase0/process_mining_*.md`
- N_MENARD questions: `phase0/nmenard_alignment_questions.md`
- Plan: `knowledge/session_plans/session_062_plan.md`
- Companion: `companions/BCM_StructuredAddressChange.html`
