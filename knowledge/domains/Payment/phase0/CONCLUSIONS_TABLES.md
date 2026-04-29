# Phase 0 Conclusions — All findings in tables

**Generated**: 2026-04-29 · **Session**: #62 · **Anchored on P01 production data**

> Principle: every classification, decision, and recommendation below is anchored on **P01 runtime evidence**. D01 used only for retrofit planning, never as truth.

---

## Section 1 — Active inventory P01 (verified by runtime evidence)

### 1.1 — DMEE trees (4 in scope + 1 bonus)

| Tree | Active version | Last user | Last date | XSLT | Status |
|---|---|---|---|---|---|
| `/SEPA_CT_UNES` | V000 | M_SPRONK | 2021-11-23 | (none) | 🎯 IN SCOPE |
| `/CITI/XML/UNESCO/DC_V3_01` | V000 | M_SPRONK | 2023-01-31 | CGI_XML_CT_XSLT | 🎯 IN SCOPE |
| `/CGI_XML_CT_UNESCO` | V000 | FP_SPEZZANO | 2025-03-20 | (none) | 🎯 IN SCOPE |
| `/CGI_XML_CT_UNESCO_1` | V000 | FP_SPEZZANO | 2025-02-14 | (none) | 🎯 IN SCOPE |
| `/CGI_XML_CT_UNESCO_BK` | V000 | (extracted) | TBD | (none) | 🎯 IN SCOPE (bonus) |

**Conclusion 1.1**: 5 trees in scope. CITI uses XSLT post-processing; SEPA + CGI variants do not.

### 1.2 — Function modules registered in TFPM042FB Event 05

| FM | Trees using | Source | Status |
|---|---|---|---|
| `FI_PAYMEDIUM_DMEE_CGI_05` | CGI_XML_CT_UNESCO + _1 + _BK | SAP-std | ACTIVE |
| `/CITIPMW/V3_PAYMEDIUM_DMEE_05` | CITI/XML/UNESCO/DC_V3_01 | CITIPMW Industry Solution | ACTIVE |
| (none) | /SEPA_CT_UNES | n/a | SEPA does NOT use Event 05 |

**Conclusion 1.2**: SEPA tree generates structured address purely via DMEE node config — no FM hook. CGI + CITI use Event 05 to populate FPAYHX_FREF buffer pre-traversal.

### 1.3 — UNESCO custom Y* classes (BAdI FI_CGI_DMEE_EXIT_W_BADI)

| Class | Role | Method count | Active in P01 |
|---|---|---|---|
| `YCL_IDFI_CGI_DMEE_FALLBACK` | Default impl (always dispatched) | 9 includes (CCDEF/CCIMP/CCMAC/CI/CM001/CM002/CO/CP/CT/CU) | ✅ YES |
| `YCL_IDFI_CGI_DMEE_FR` | Country-specific FR | 8 includes + CM002 (CM001 only in D01) | ✅ YES |
| `YCL_IDFI_CGI_DMEE_DE` | Country-specific DE — overrides `<MmbId>` (uses ZBNKL) | 9 includes | ✅ YES (P01-only) |
| `YCL_IDFI_CGI_DMEE_IT` | Country-specific IT — overrides `<MmbId>` | 9 includes | ✅ YES (P01-only) |
| `YCL_IDFI_CGI_DMEE_UTIL` | Helper class (called by FR CM002 for PPC dispatcher) | 11 includes | ✅ YES |

**Conclusion 1.3**: 5 active UNESCO custom classes. DE/IT classes are critical for German/Italian vendor bank `<MmbId>` formatting — FALLBACK has it commented out.

### 1.4 — Function modules at node-level (MP_EXIT_FUNC) — 33 total

| Category | Count | Examples |
|---|---|---|
| CITIPMW V3 (CITI tree only) | 26 | V3_CGI_CRED_STREET, V3_CGI_BANK_NAME, V3_POSTALCODE, V3_TAX_*, etc. |
| SAP-std SEPA exits | 4 | DMEE_EXIT_SEPA_21/31/41, DMEE_EXIT_SE_DATE |
| BAdI dispatcher | 1 | FI_CGI_DMEE_EXIT_W_BADI (registered for CGI + CGI_1) |
| UNESCO Z customs | 2 | ZDMEE_EXIT_SEPA_21, Z_DMEE_EXIT_TAX_NUMBER |

**Extraction status**: 17/17 CITIPMW V3 FMs extracted to `extracted_code/FI/DMEE_full_inventory/`

### 1.5 — SAP-std country dispatcher classes (cl_idfi_cgi_call05_factory pattern)

| Verdict | Count | Classes |
|---|---|---|
| 🔥 HIGH usage (>1000 P01 payments) | 12 | FR (148K), US (38K), IT (22K), DE (20K), GB (9K), BE (7K), ES (7K), CA (5K), CH (2.5K), CN (2.3K), AU (1.7K), MX (1.6K) |
| ✅ Active (100-1000 payments) | 6 | PL (931), DK (871), PT (857), AT (545), SE (416), LT (377) |
| 💀 DEAD (zero P01 traffic) | 10 | BG, CZ, EE, HK, HR, IE, LU, RO, SK, TW |

**Conclusion 1.5**: 18 active country dispatchers (vendor bank country drives dispatch). 10 extracted but DEAD — UNESCO has no vendor banks in those countries.

---

## Section 2 — D01 vs P01 drift (retrofit planning)

### 2.1 — Code drift verdicts (51 includes analyzed byte-by-byte)

| Verdict | Count | Action |
|---|---|---|
| **IDENTICAL** (byte-by-byte) | 30 | Skip — no retrofit needed |
| **P01_ONLY** (must retrofit P01→D01) | 19 | Include in `D01-RETROFIT-01` |
| **D01_ONLY** (need N_MENARD review) | 2 | Decision required |

### 2.2 — P01_ONLY includes detail (must retrofit)

| Class / object | Includes | Author | Why retrofit needed |
|---|---|---|---|
| `YCL_IDFI_CGI_DMEE_DE` | 9 (CCDEF/CCIMP/CCMAC/CI/CM001/CO/CP/CT/CU) | N_MENARD | Override `<MmbId>` for DE-bank vendors. ~9K-20K payments/yr need this. |
| `YCL_IDFI_CGI_DMEE_IT` | 9 (same) | N_MENARD | Override `<MmbId>` for IT-bank vendors. ~10K-22K payments/yr need this. |
| `YCL_IDFI_CGI_DMEE_FR====CM002` | 1 method | N_MENARD | PPC customizing dispatcher — calls UTIL->get_tag_value_from_custo |
| `Y_IDFI_CGI_DMEE_COUNTRIES_DE` (ENHO) | 1 enh impl | N_MENARD | BAdI wire-up for DE class |
| `Y_IDFI_CGI_DMEE_COUNTRIES_FR` (ENHO) | 1 enh impl | N_MENARD | BAdI wire-up for FR class — Francia core |
| `Y_IDFI_CGI_DMEE_COUNTRIES_IT` (ENHO) | 1 enh impl | N_MENARD | BAdI wire-up for IT class |

**Total retrofit scope**: 22 objects (19 includes + 3 ENHO).

### 2.3 — D01_ONLY anomalies (need N_MENARD decision)

| Object | Discovered | Decision |
|---|---|---|
| `YCL_IDFI_CGI_DMEE_FR====CM001` | D01 has it (2024-03-22), P01 has CM002 instead. Method-level swap. | Q1bis — align D01 to P01 (delete CM001, add CM002)? |
| `Z_DMEE_EXIT_TAX_NUMBER====FT` (function group include) | D01 since 2019-07-26 by SAP*, never in P01 | Likely safe to leave (7-yr leftover) |

### 2.4 — Customizing drift (D01 has WIP not in our scope)

| Table | Extra rows in D01 | Content | Affects our scope? |
|---|---|---|---|
| TFPM042FB | +5 rows | All `FORMI=/CHECK_SG` (SocGen check printing) | NO |
| T042Z | +3 rows | 1 SocGen check + 2 China manual transfers | NO |

**Conclusion 2**: Phase 2 sequencing requires `D01-RETROFIT-01` transport BEFORE any V001/Pattern A work. 22 objects mandatory + 2 anomalies for N_MENARD decision.

---

## Section 3 — Per-year HBKID volume (2024-2026 Q1)

### 3.1 — Total payments per year (REGUH.LAUFD-based)

| Year | Payments | Notes |
|---|---|---|
| 2024 | 406,458 | Full year baseline |
| 2025 | 435,080 | +7% YoY growth |
| 2026 Q1 | 100,473 | On track for ~400K full year |

### 3.2 — Top 11 HBKIDs × Year matrix

| HBKID | Banco | Co | 2024 | 2025 | 2026 Q1 | Total | Tree (in scope?) |
|---|---|---|---|---|---|---|---|
| **SOG01** | SocGen FR | UNES | 213,448 | 228,648 | 48,177 | **490K** | 🎯 SEPA + CGI |
| **CIT01** | Citi BR | UBO+UIS | 33,803 | 34,683 | 7,474 | **76K** | 🎯 CITI |
| **CIT04** | Citi US | UNES | 26,727 | 28,329 | 5,997 | **61K** | 🎯 CITI |
| **UNI01** | UniCredit IT | ICTP | 11,034 | 10,261 | 2,269 | **24K** | ⚪ Out of scope (ICTP) |
| **SOG05** | SocGen FR | UIL | 4,604 | 4,137 | 720 | 9K | 🎯 SEPA |
| **SOG02** | SocGen FR | IIEP | 3,403 | 3,039 | 650 | 7K | 🎯 SEPA |
| **SOG03** | SocGen FR | UNES | 3,870 | 3,995 | 836 | 9K | 🎯 SEPA + CGI |
| **CIT21** | Citi CA | UNES (CA) | 2,189 | 1,977 | 463 | 5K | 🎯 CITI |
| BRA01 | Banco BR | UBO | 578 | 564 | 174 | 1,316 | 🎯 CITI |
| AIB01 | Bank AF | UNES | TBD | TBD | TBD | 746 | TBD |
| BTE01 | Bank IR | UNES | TBD | TBD | TBD | 519 | TBD |

**Conclusion 3**: 70% of all UNESCO REGUH payments (~654K of 942K) flow through 4 in-scope trees. Volumes are stable YoY (~7% growth, no seasonality). UNI01 (ICTP) explicitly out of scope.

---

## Section 4 — HBKID drill-down (vendor bank country emission)

### 4.1 — SOG01 (UNES SocGen FR) — 512K payments

| Vendor bank country | Vendor address country | Payments | Comment |
|---|---|---|---|
| (empty) | (empty) | 267,630 | 52% — domestic SEPA / one-time CPD vendors |
| FR | FR | 81,683 | 16% — French vendors with French banks (FR class fires) |
| IT | IT | 9,901 | 2% — Italian vendors via SEPA tree (IT class fires) |
| UA | UA | 8,336 | Ukraine refugees / NGO via SEPA |
| DE | DE | 6,408 | German vendors via SEPA tree (DE class fires) |
| LB | LB | 5,826 | Lebanon |
| ES | ES | 5,688 | Spain |
| GB | GB | 3,673 | United Kingdom |
| BE | BE | 3,526 | Belgium |
| EG | EG | 3,244 | Egypt |
| ZW | ZW | 3,156 | Zimbabwe |
| US | FR | 2,618 | US-bank vendor with FR address |
| KE | KE | 2,579 | Kenya |
| ZA | ZA | 2,367 | South Africa |
| BA | BA | 2,196 | Bosnia |

### 4.2 — CIT01 (UBO Citi BR) — 79K payments

| Vendor bank country | Vendor address country | Payments | Comment |
|---|---|---|---|
| BR | BR | 70,081 | 89% — core Worldlink BRL traffic |
| (empty) | BR | 4,736 | One-time BR vendors |
| CA | CA | 1,647 | Canadian bridge from UBO |
| US | BR | 346 | US-bank Brazilian vendor |
| FR | FR | 242 | French vendors paid by UBO |

### 4.3 — CIT04 (UNES Citi US) — 67K payments

| Vendor bank country | Vendor address country | Payments | Comment |
|---|---|---|---|
| (empty) | (empty) | 27,414 | 41% — Worldlink generic / CPD |
| US | US | 9,615 | Domestic US |
| US | FR | 4,122 | US Citi paying French vendors |
| **MG** | **MG** | **4,094** | **Madagascar Worldlink — exotic currency** |
| US | MM | 1,820 | Myanmar |
| FR | FR | 1,773 | FR vendors via Citi |
| **TN** | **TN** | **1,628** | **Tunisia Worldlink** |
| MM | MM | 1,356 | Myanmar bridge |
| US | AR | 908 | Argentina |
| US | LB | 516 | Lebanon |
| US | TH | 464 | Thailand |
| US | CR | 420 | Costa Rica |
| US | ZW | 407 | Zimbabwe |
| GB | IT | 384 | UK-bank Italian vendor |
| US | ET | 384 | Ethiopia |

**Conclusion 4.3**: CIT04 confirms Worldlink exotic currencies (MG/TN/AR/MM/etc.). Resolves Q3 — UltmtCdtr Worldlink scope.

### 4.4 — SOG05 (UIL Hamburg DE) — 12K payments

| Vendor bank country | Vendor address country | Payments | Comment |
|---|---|---|---|
| **DE** | **DE** | **9,143** | **77% — primary trigger of DE class** |
| GB | GB | 308 | UK vendors via UIL |
| DE | LU | 244 | Luxembourg |
| FR | FR | 224 | French |
| ES | ES | 216 | Spanish |
| IE | IE | 183 | Ireland |

**Conclusion 4.4**: UIL co code (Hamburg) is the PRIMARY trigger of `YCL_IDFI_CGI_DMEE_DE` class (9K+ payments/yr). Without retrofit, F110 in D01 cannot replicate this for German vendor `<MmbId>`.

---

## Section 5 — BCM batches (Model 8)

### 5.1 — BCM Batch totals

| Metric | Value |
|---|---|
| BNK_BATCH_HEADER rows | 27,443 |
| BNK_BATCH_ITEM rows | 600,042 |
| Distinct status codes | 36 (workflow technical IDs) |

### 5.2 — Top BCM-routing house banks

| HBKID | Batches | Co | Tree |
|---|---|---|---|
| SOG01 | 11,334 | UNES | SEPA + CGI |
| CIT04 | 4,916 | UNES | CITI |
| CIT01 | 3,054 | UBO+UIS | CITI |
| SOG03 | 2,746 | UNES | SEPA + CGI |
| SOG02 | 1,465 | IIEP | SEPA |
| SOG04 | 860 | UNES | TBD |
| CIT21 | 783 | UNES | CITI |
| SOG05 | 767 | UIL | SEPA |
| WEL01 | 504 | UNES | TBD (Wells Fargo) |
| CHA01 | 499 | UNES | TBD |

**Conclusion 5**: BCM workflow handles 27K batches across all UNESCO co codes. SOG01 alone = 41% of BCM batches (~11K). Test matrix V001 must cover top 10 HBKIDs for representative coverage.

---

## Section 6 — F110 testing pattern (Model 6)

| XVORL flag | Count | % | Meaning |
|---|---|---|---|
| (empty) | 583,905 | 62% | Real F110 runs |
| X | 358,106 | 38% | Test proposals (no posting) |

**Conclusion 6**: UNESCO uses extensive proposal-before-run pattern. **Phase 3 unit testing can leverage this** — F110 proposal mode lets us validate V001 XML output without payment posting risk.

---

## Section 7 — Retrofit transport `D01-RETROFIT-01` summary

| Section | Count | Status |
|---|---|---|
| Mandatory P01→D01 retrofit (UNESCO Y* classes + ENHO) | 22 objects | Specified |
| D01-only anomalies for N_MENARD decision | 2 (FR/CM001 swap, Z_TAX_FT 2019 leftover) | Q1bis pending |
| Customizing drift (out of scope WIP) | 8 rows (TFPM042FB +5, T042Z +3) | Documented, NOT in retrofit |
| Verified IDENTICAL (skip) | 30 includes | No action |

**Sequencing Phase 2**:

| Step | Transport | Output |
|---|---|---|
| **0** | `D01-RETROFIT-01` | D01 ↔ P01 parity for UNESCO custom code |
| **1** | `D01-BADI-FIX-01` | Pattern A 3-line guard at FALLBACK CM001 |
| 2-4 | `D01-DMEE-V001-{SEPA,CITI,CGI}` | V001 trees with structured address |
| 5 | `D01-OBPM4-SEPA-EVENT05` | Add 1 row to TFPM042FB for SEPA Event 05 |

---

## Section 8 — Test matrix Tier 1 (CONFIG-DERIVED from production)

**Final** test scenarios anchored on REGUH_FAST × T001 × T042Z (567K payments 2025+):

| # | HBKID | Tree (CONFIG) | 2025 vol | 2026 Q1 | Total | % of in-scope |
|---|---|---|---|---|---|---|
| **T01** | SOG01 | `/SEPA_CT_UNES` | 129,722 | 37,685 | **167,407** | 50% |
| **T02** | SOG01 | `/CGI_XML_CT_UNESCO` | 54,998 | 15,541 | **70,539** | 21% |
| **T03** | CIT01 | `/CITI/XML/UNESCO/DC_V3_01` | 34,677 | 11,122 | **45,799** | 14% |
| **T04** | CIT04 | `/CITI/XML/UNESCO/DC_V3_01` | 28,139 | 8,275 | **36,414** | 11% |
| T05 | SOG03 | `/CGI_XML_CT_UNESCO` | 3,893 | 1,114 | **5,007** | 1.5% |
| T06 | SOG05 | `/SEPA_CT_UNES` | 3,783 | 945 | **4,728** | 1.4% |
| T07 | SOG02 | `/SEPA_CT_UNES` | 2,976 | 793 | **3,769** | 1.1% |
| T08 | CIT21 | `/CITI/XML/UNESCO/DC_V3_01` | 1,954 | 605 | **2,559** | 0.8% |

**Conclusion 8**: 8 Tier-1 (HBKID, Tree) combinations cover **~336K of 567K REGUH** (60% of total payments). The TOP 4 alone cover **96% of in-scope traffic**.

### Worldlink coverage (Model 10 — CONFIG-derived)

| Currency | Primary HBKID | Volume | Tree route |
|---|---|---|---|
| BRL | CIT01 | 44,344 | /CITI/XML/UNESCO/DC_V3_01 |
| MGA | CIT04 | 3,647 | /CITI/XML/UNESCO/DC_V3_01 |
| TND | CIT04 | 1,162 | /CITI/XML/UNESCO/DC_V3_01 |
| INR | SOG01 | 2,098 | /CGI_XML_CT_UNESCO (treasury route) |
| THB | SOG01 | 1,404 | /CGI_XML_CT_UNESCO (treasury route) |
| KES | SOG01 | 1,277 | /CGI_XML_CT_UNESCO (treasury route) |
| NGN | SOG01 | 801 | /CGI_XML_CT_UNESCO (treasury route) |
| CNY | SOG01 | 796 | /CGI_XML_CT_UNESCO (treasury route) |

**Conclusion Worldlink**: Two routing paths confirmed.
- Path 1: Citi → /CITI tree (BRL/MGA/TND, true Worldlink Citi)
- Path 2: SocGen → /CGI tree (INR/THB/KES/NGN/CNY, treasury non-Citi route)

V001 cutover MUST cover both paths for exotic currencies. Test matrix Worldlink subset adds T09–T13.

---

## Section 9 — Vendor master DQ (corrected from initial PM #3)

| Metric | Value | Verdict |
|---|---|---|
| Active vendors with valid ADRC join | 111,238 / 99.997% | ✅ |
| Missing CITY1 OR COUNTRY (CBPR+ blockers) | **5 / 0.005%** | ✅ Acceptable |
| Active payment vendors (in REGUH) missing LAND1 | **19 of 31,334 (one-time CPD only, none paid)** | ✅ |
| Missing STREET (optional CBPR+) | 5,570 / 5.0% | OK |
| Missing POST_CODE1 (optional) | 1,153 / 1.0% | OK |
| Missing HOUSE_NUM1 (optional) | 76,574 / 68.8% | Expected — many addresses don't have house number |

**Conclusion 9**: DQ is healthy. Phase 0 Finding A's "5/111K vendors missing" reaffirmed. Earlier 5,022 alarm was a LEFT JOIN artifact (REGUH.LIFNR with no LFA1 record = legacy/deleted IDs). **Not a Phase 2/3 blocker**.

---

## Section 10 — Open questions for N_MENARD alignment

| Q# | Question | Decision needed |
|---|---|---|
| Q1 | Pattern A: remove (A1) or guard (A2) the name-overflow logic? | Code owner preference |
| **Q1bis** | FR class has `CM001` in D01, `CM002` in P01 — method swap. Align D01 to P01? | Code owner explanation + decision |
| Q2 | Why are 5 objects P01-only (DE/IT classes + 3 ENHO)? | Production state explanation |
| Q3 | Retrofit method preference (reverse transport / SAPLink / paste)? | Operational preference |
| Q4 | Phase 2 review scope (a/b/c)? | Time-boxing |
| Q5 | Vendor edge cases for V001 testing? | Institutional memory |
| Q6 | Any UNESCO-specific gotchas? | Open exploratory |

---

## Section 11 — Pending work — UPDATED

| Task | Status | Output |
|---|---|---|
| REGUH_FAST extraction (11 cols, 2025+) | ✅ DONE | 567,059 rows in Gold DB REGUH_FAST |
| Real tree mapping JOIN | ✅ DONE | 8 Tier-1 (HBKID,Tree) combinations CONFIG-derived |
| Model 10 — Worldlink currencies | ✅ DONE | Dual-route confirmed (Citi + SocGen) |
| REGUH_FULL (27 cols full history) | ❌ Cancelled (RFC stalled 30+min) | REGUH_FAST gives 60% coverage in 4 min |
| REGUP extraction | ❌ Cancelled | Not blocking Phase 2 design |

---

## Section 12 — PPC system (Payment Purpose Code) — discovered 2026-04-29 from N_MENARD email

### 12.1 — DDIC inventory (11 objects all by N_MENARD)

| Object | Type | Rows | DDIC drift |
|---|---|---|---|
| `YTFI_PPC_TAG` | TABL | 11 | Identical structure + data D01↔P01 |
| `YTFI_PPC_STRUC` | TABL | 133 | Identical structure + data D01↔P01 |
| `YD_FI_PPC_CODE` | DOMA | values: PPC_VAR, PPC_DESCR, SEPARATOR, FIXED_VAL, PAY_FIELD | identical |
| `YD_FI_PAY_TYPE` | DOMA | values: '', P, R, O | identical |
| `YD_FI_PAY_STRUC` | DOMA | values: FPAYH, FPAYHX, FPAYP | identical |
| `YD_FI_TAG_ID` | DOMA | (free text) | identical |
| `YE_FI_PPC_CODE` / `YE_FI_TAG_ID` / `YE_FI_PAY_TYPE` / `YE_FI_PAY_STRUC` / `YE_FI_TAG_FULL` | DTEL × 5 | (data elements) | identical |

DDIC drift: 6 months timestamp (P01 2024-09-06, D01 2024-03-18) — **non-functional**.

### 12.2 — 9 PPC countries impact

| LAND1 | Tag location | XML format example | Required for |
|---|---|---|---|
| AE | `<InstrForCdtrAgt><InstrInf>` | `/REC/FIS` | UAE bank acceptance |
| BH | `<RmtInf><Ustrd>` | `/STR/Travel` | Bahrein |
| CN | `<InstrForCdtrAgt><InstrInf>` | `/REC/CSTRDR` | China |
| ID | `<RmtInf><Ustrd>` | `/PURP/2490/Consulting` | Indonesia |
| IN | `<RmtInf><Ustrd>` | `P0301;Purchases;INV;6523486` | India |
| JO | `<RmtInf><Ustrd>` | `/PURP/801/Consulting` | Jordan |
| MA | `<RmtInf><Ustrd>` | `/PURP/510/Consulting` | Morocco |
| MY | `<RmtInf><Ustrd>` | `/PURP/16510/Consulting` | Malaysia |
| PH | `<RmtInf><Ustrd>` | `/PURP/SUPP/Consulting` | Philippines |

### 12.3 — T015L SCB indicator master

| | P01 | D01 |
|---|---|---|
| Total rows | 73 | 74 |
| D01-only row | n/a | LZBKZ='DK1' "NOT VALID JUST TO AVOID ERROR" — dev placeholder, ignore |

### 12.4 — Code chain CONFIRMED

| Layer | Object | Status | Action |
|---|---|---|---|
| BAdI dispatcher | `FI_CGI_DMEE_EXIT_W_BADI` | Active in both | NO change |
| FR country class | `YCL_IDFI_CGI_DMEE_FR` (CCDEF/CCIMP/CI/CO/CP/CT/CU + CM001 in D01 / CM002 in P01) | Drift: D01 has CM001, P01 has CM002 | **Retrofit P01's CM002 to D01** |
| PPC entry method | `CM002.if_idfi_cgi_dmee_countries~get_value` | P01 only | Mandatory retrofit |
| PPC dispatcher | `YCL_IDFI_CGI_DMEE_UTIL_CM003.get_tag_value_from_custo` | Identical D01↔P01 | NO change |
| Source data | T015L (SCB) + YTFI_PPC_STRUC + YTFI_PPC_TAG | Identical content | NO change |

### 12.5 — Connection to Worldlink dual-route (claim 95)

Recall: PM Model 10 found that exotic currencies route via **two paths**:
- Path A: Citi (CIT01/CIT04) → /CITI tree (BRL/MGA/TND)
- Path B: SocGen (SOG01) → /CGI tree (INR/THB/KES/NGN/CNY)

**PPC fires on Path B for IN/CN/MY/PH/JO/MA** payments. So the CGI tree carries:
1. UNESCO HQ treasury via SocGen (INR, THB, KES, NGN, CNY) → PPC dispatched
2. UNESCO HQ treasury (Euro outside SEPA) → no PPC
3. Country-specific tax-receipt vendors in PPC countries → PPC mandatory

→ **V001 cutover on /CGI_XML_CT_UNESCO directly affects PPC**. Test matrix MUST cover PPC country payments.

### 12.6 — V001 design impact

**MUST PRESERVE**: in V001 of /CGI_XML_CT_UNESCO, the nodes `<InstrForCdtrAgt><InstrInf>` and `<RmtInf><Ustrd>` MUST continue to fire the BAdI/PPC dispatcher AND emit the same content as V000.

**Verification (Phase 2 Step 0+1)**: extract the YCL_IDFI_CGI_DMEE_FR_CM002 source, retrofit to D01, then run F110 proposal mode for each PPC country in D01 + V000 and compare PPC tag output to P01 baseline. After V001 changes, repeat — output must match.

---

## Final Phase 0 conclusions (consolidated)

| # | Finding | Verdict |
|---|---|---|
| 1 | P01 = canonical source of truth | Adopted as principle (rule 98) |
| 2 | 4 trees + 1 bonus _BK in scope | Verified V000 active |
| 3 | 5 UNESCO Y* classes ACTIVE | DE/IT need retrofit (P01-only) |
| 4 | 17 CITIPMW V3 FMs ACTIVE | All extracted |
| 5 | 18 SAP-std country dispatchers active, 10 DEAD | Test matrix can skip dead ones |
| 6 | DQ healthy (5/111K) | Not a blocker |
| 7 | 22 objects retrofit P01→D01 | `D01-RETROFIT-01` Phase 2 Step 0 |
| 8 | Pattern A target (FALLBACK CM001) byte-identical D01 vs P01 | Fix safe to apply |
| 9 | Test matrix Tier 1 = 8 (HBKID,Tree) combinations CONFIG-derived | TOP 4 cover 96% of in-scope |
| 10 | F110 proposal mode (XVORL=X) used 38% — leverage for safe testing | Phase 3 strategy |
| 11 | YoY growth ~7%, stable seasonality | V001 cutover safe any window |
| 12 | Worldlink dual-route: Citi (BRL/MGA/TND) + SocGen (INR/THB/KES/NGN/CNY) | Both must be tested |
| 13 | T042I = canonical house bank derivation (77 rules) | Used in real config JOIN |
| 14 | LIVE_CONFIG_MAP.md = end-to-end connected (vendor → file → bank) | Pre-Phase 2 reference |
| 15 | Country dispatcher (FR/DE/IT) fires ONLY on CGI tree | NOT SEPA, NOT CITI |
| 16 | Two dispatcher mechanisms (Event 05 factory + per-node BAdI) | Distinguished in plan |
| **17** | **Pattern A is BANK-MANDATED** (SocGen requirement) — Q1 RESOLVED | **A2 (guard) only valid path** |
| **18** | **PPC system = 11 DDIC objects + 2 tables (133+11 rows)** for 9 countries | **V001 must preserve** |
| **19** | **FR/CM002 swap RESOLVED**: not a swap — it's PPC dispatcher entry never retrofitted to D01 | **Mandatory retrofit** |
| **20** | **PPC + Worldlink overlap**: SOG01 → /CGI tree carries PPC payments to IN/CN/MY/PH | **27 test scenarios** (9 countries × 3 pay types) |
| **21** | **PPC infrastructure data IDENTICAL** D01↔P01 (YTFI tables + T015L) | **Only code dispatcher missing in D01** |

---

## Cross-reference

- Brain claims: 65, 80-93 (TIER_1)
- Feedback rule: 98 (P01 canonical)
- Drift artifacts: `knowledge/domains/Payment/phase0/d01_vs_p01_drift_*.md`
- PM artifacts: `knowledge/domains/Payment/phase0/process_mining_*.md`
- N_MENARD questions: `knowledge/domains/Payment/phase0/nmenard_alignment_questions.md`
- Plan: `knowledge/session_plans/session_062_plan.md`
- Companion: `companions/BCM_StructuredAddressChange.html`
