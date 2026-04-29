**To**: [BANK_TRM_CONTACT]
**Cc**: Spronk, Marlies <m.spronk@unesco.org>; Lopez, Julio Pablo Francisco <jp.lopez@unesco.org>
**Subject**: UNESCO — pain.001 structured address compliance Nov 2026 — your acceptance criteria

---

Dear [BANK NAME] Treasury Management Team,

UNESCO is preparing to migrate our outgoing payment file format to ISO 20022 CBPR+ structured address, ahead of the **November 2026 mandate** ([SocGen confirmed | Citi confirmed | CGI banks expected]).

To ensure our pain.001 files will be accepted at your gateway after the cutover, we'd like to request the following information:

## 1. CBPR+ acceptance criteria

What is your bank's enforcement policy for the November 2026 deadline?
- (a) **Hybrid acceptable**: structured tags (`<TwnNm>` + `<Ctry>` minimum) + `<AdrLine>` fallback OK
- (b) **Fully structured required**: `<StrtNm>` + `<BldgNb>` + `<PstCd>` + `<TwnNm>` + `<Ctry>`, no `<AdrLine>`
- (c) **Other / hybrid with restrictions**

## 2. Schema version

Which pain.001 version do you accept (today / from Nov 2026):
- pain.001.001.03 (current)
- pain.001.001.09 (CBPR+ standard)
- Both

## 3. Specific bank requirements

- Bank-specific implementation guide / addendum to ISO 20022 spec
- Mandatory tags beyond CBPR+ minimum (PPC, regulatory info, etc.)
- Test gateway endpoint + access for pilot files
- Acceptance test cycle / window

## 4. UNESCO-specific

For our 4 UNESCO co code → bank pairs that route through your bank:
- [List UNESCO co codes → your bank pairs, e.g.: UNES → SocGen, IIEP → SocGen, UIL → SocGen for SocGen]
- Any account-level configuration we should be aware of

## Pilot test

We'd like to send 5-10 pilot files to your test gateway in **July 2026** (Phase 4 UAT) for acceptance validation. Please confirm:
- Test gateway endpoint
- Required test environment configuration on your side
- Expected acceptance turnaround

## Background

UNESCO operates 3 DMEE payment trees in production:
- `/SEPA_CT_UNES` — Société Générale EUR
- `/CITI/XML/UNESCO/DC_V3_01` — Citibank USD + Worldlink (BRL/MGA/TND/etc)
- `/CGI_XML_CT_UNESCO` (+ `_1`) — multi-bank including [your bank if non-SEPA non-CITI]

Marlies Spronk (treasury) is the business lead for this project. I'm the technical lead.

We'd appreciate your response within **2 weeks** so we can finalize Phase 1 (config matrix). Happy to schedule a call if a 30-min discussion is more convenient.

Thank you for your support.

Best regards,
Pablo Lopez
[Title]
UNESCO

CC: Marlies Spronk (Treasury / FIN-TRS)

---

**Send to**:
- **SocGen TRM** — [primary contact via Marlies]
- **Citibank TRM (CitiConnect)** — [primary contact via Marlies]
- **CGI-routed banks** (Shinhan KR, Metro Bank GB, Guaranty Trust NG, Standard Chartered, etc.) — request distribution via Marlies

**Tracking**: log responses in `knowledge/domains/Payment/phase0/bank_spec_matrix.md`
