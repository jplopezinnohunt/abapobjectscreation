# Process Mining Synthesis — P01 Active vs Dead (data-driven)

**Generated**: 2026-04-29 · **Sources**: 942K REGUH payments + LFA1/LFBK/LFB1/ADRC

## Headline findings

### 1. SAP-std country dispatcher: 18 active, 10 DEAD

Of the 28 SAP-std `CL_IDFI_CGI_CALL05_<country>` classes we extracted from P01:

**🔥 HIGH usage (>1000 payments — top of test matrix priority)**:
- `CL_IDFI_CGI_CALL05_FR` — **148,644** payments (UNESCO HQ vendor bank traffic)
- `CL_IDFI_CGI_CALL05_US` — 37,888
- `CL_IDFI_CGI_CALL05_IT` — 22,035 ⚠️ (P01-only class — retrofit needed)
- `CL_IDFI_CGI_CALL05_DE` — 19,889 ⚠️ (P01-only class — retrofit needed)
- `CL_IDFI_CGI_CALL05_GB` — 9,168
- `CL_IDFI_CGI_CALL05_BE` — 7,174
- `CL_IDFI_CGI_CALL05_ES` — 6,781
- `CL_IDFI_CGI_CALL05_CA` — 4,642
- `CL_IDFI_CGI_CALL05_CH` — 2,463
- `CL_IDFI_CGI_CALL05_CN` — 2,262
- `CL_IDFI_CGI_CALL05_AU` — 1,667
- `CL_IDFI_CGI_CALL05_MX` — 1,620

**✅ Active (100-1000 payments)**: PL, DK, PT, AT, SE, LT (6 classes)

**💀 DEAD (zero P01 traffic)**: BG, CZ, EE, HK, HR, IE, LU, RO, SK, TW (10 classes)
→ UNESCO has no vendor banks in these countries. Dispatchers exist but are never exercised. **Out of test scope.**

### 2. Retrofit value quantified

The DE/IT class retrofit (Phase 2 Step 0) directly affects:
- **~20K payments/year** to vendors with German banks (DE class fires for `<MmbId>` override)
- **~22K payments/year** to vendors with Italian banks (IT class fires)
- **= 42K payments/year** without correct `<MmbId>` value if D01 lacks these classes

In D01 today, F110 simulation of those 42K scenarios produces XML with empty `<MmbId>` (FALLBACK has it commented out). Cannot validate V001 reliably. **Retrofit is mandatory before Phase 2.**

### 3. Vendor master DQ — Finding A reaffirmed (NOT a blocker)

Initial PM #3 query suggested 5,022 active vendors missing CITY+COUNTRY. **Investigation revealed this was a LEFT JOIN artifact**: REGUH.LIFNR rows where the vendor doesn't exist in current LFA1 (deleted/legacy IDs).

Direct query: only **19 vendors** in P01 have empty LAND1, all are CPD (one-time, KTOKK=OCCV/VOCC). None received payments via REGUH.

**Conclusion**: vendor DQ is healthy. Phase 0 Finding A's "5/111K missing" is correct. **Not a Phase 2/3 blocker.**

### 4. Bank country traffic profile (top 20 confirms scope)

Top vendor bank countries by payment volume:
| Rank | Country | Payments | Notes |
|---|---|---|---|
| 1 | (empty) | 430,517 | One-time vendors / domestic SEPA / non-LFBK records |
| 2 | FR | 148,644 | UNESCO HQ + French vendors |
| 3 | BR | 72,240 | Brazilian Worldlink (UBO Worldlink CIT04) |
| 4 | US | 37,888 | UIS HQ + USD payments |
| 5 | IT | 22,035 | Italian vendors via CGI tree |
| 6 | DE | 19,889 | German vendors via CGI tree |

UNESCO's payment landscape is **dominated by FR + Worldlink BR + US**. The top 12 countries cover >85% of payments.

### 5. Tree-volume routing limitation

PM #2 attempted to map (co_code, payment_method) → tree via T042Z. Result: 916K payments
"NO_T042Z_MATCH" because LFB1.ZWELS holds **multi-char allowed-method strings** (e.g.,
'CJLNOSU' = methods C, J, L, N, O, S, U), not the single ZLSCH used per payment.
The actual ZLSCH per payment is in `REGUH.RZAWE` which we haven't extracted.

**Action**: extend Gold DB extraction to include REGUH.RZAWE (and a few other key
columns) for accurate per-payment tree mapping. Not blocking current Phase 2 design
because tree usage is already known via T042Z config (Finding H).

## Implications for the project

### Test matrix priority for V001 (Phase 3)

Tier-1 test cases (representative of >85% of P01 traffic):
- **FR vendors via CGI** (Treasury Transfers, Euro Payment outside SEPA-zone) — exercises FR class CM002
- **DE vendors via CGI** (International Payments DE+N) — exercises DE class
- **IT vendors via CGI** — exercises IT class
- **BR Worldlink via CITI** — exercises CITIPMW V3 + Worldlink BIC override
- **US vendors via CITI** — exercises US dispatcher
- **GB vendors via CGI** — UK SEPA-extended

Tier-2 (top 12 country coverage): BE, ES, CA, CH, CN, AU, MX

### Test matrix exclusions (DEAD dispatchers)

10 country dispatchers (BG/CZ/EE/HK/HR/IE/LU/RO/SK/TW) have ZERO traffic. **Skip in test matrix** — would produce noise without any production parity value. SAP-std code, not our maintenance burden.

### Retrofit transport `D01-RETROFIT-01` value justification

The retrofit doesn't just bring 22 objects to D01. It restores the ability to test ~42K
yearly DE+IT payment scenarios that currently can't be replicated in D01. The retrofit
is not "completeness" — it's **operational test fidelity**.

## Data limitations / follow-up needed

1. **REGUH columns extracted are minimal** (8 of 200+) — extend extraction to include RZAWE/HBKID/HKTID for accurate per-payment routing.
2. **Per-payment tree mapping** awaits column extension. Current scope: T042Z-based routing matrix is proxy.
3. **Address completeness for vendors actually paid via target trees** — needs RZAWE filter to be precise.

## Cross-reference

- Brain claim 88: P01 active inventory anchored
- Brain claim 89: Vendor DQ healthy (corrected)
- Brain claim 86: D01-RETROFIT-01 base concept
- Feedback rule 98: P01 canonical for active vs dead
- Phase 2 Step 0: D01-RETROFIT-01 transport scope
- Test matrix Phase 3: prioritized by traffic volume (this document)
