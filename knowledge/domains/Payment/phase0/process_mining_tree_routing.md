# Process Mining: Tree × Co × Payment Method Routing Matrix
**Generated**: from P01 Gold DB REGUH 942K payments

## Tree usage totals (top of funnel)

| Tree (FORMI) | Total payments routed | Status |
|---|---|---|
| `NO_T042Z_MATCH` | 916,913 | ❓ No T042Z routing |
| `` | 19,300 | ⚪ Out of scope |
| `/SEPA_CT_UNES` | 4,363 | 🎯 IN SCOPE |
| `/CGI_XML_CT_UNESCO` | 1,163 | 🎯 IN SCOPE |
| `/CMI101` | 272 | ⚪ Out of scope |

## Tier-1 routing combinations (volume > 100 payments)

| Co | Co country | Pay method | Tree | XBKKT | XSTRA | Volume | Description |
|---|---|---|---|---|---|---|---|
| ICTP | FR | S | `/SEPA_CT_UNES` | X | X | 4,002 | SEPA Payment |
| ICTP | FR | J | `/CGI_XML_CT_UNESCO` | X | X | 1,163 | Euro Payment outside SEPA-zone |
| IIEP | FR | S | `/SEPA_CT_UNES` | X | X | 321 | SEPA Payment |

## All routing combinations within scope (full set)

**Total in-scope payments**: 5,526

| Co | Co country | Pay method | Tree | Volume |
|---|---|---|---|---|
| ICTP | FR | S | `/SEPA_CT_UNES` | 4,002 |
| ICTP | FR | J | `/CGI_XML_CT_UNESCO` | 1,163 |
| IIEP | FR | S | `/SEPA_CT_UNES` | 321 |
| UIL | FR | S | `/SEPA_CT_UNES` | 40 |

## Conclusions

- **Target trees** (4 + bonus _BK) carry approximately **0.6%** of total payments (5,526 / 942,011)
- Tier-1 test combinations cover the realistic V001 cutover scenarios
- Out-of-scope trees handle internal transfers, payroll, etc. — not affected by structured address change
