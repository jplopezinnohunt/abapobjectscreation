# PPC Validation Report
**Generated**: from Gold DB algorithm replay + lxml XSD validation

## Summary

- PPC config: 11 tag rows + 133 struc rows + 73 SCB indicators
- Scenario samples (PPC countries): 24
- Predictions executed: 24
- XSD pass rate: 6/24

## Per-sample predictions

| # | Co | Vendor bank | Cur | PM | PayType | LZBKZ | InstrInf | Ustrd | XSD |
|---|---|---|---|---|---|---|---|---|---|
| 21 | IIEP | IN | USD | N | O |  | `` | `` | ❌ |
| 33 | UIL | IN | EUR | N | O | IN7 | `` | `P1019;Other services not ` | ❌ |
| 33 | UIL | IN | EUR | N | O | IN7 | `` | `P1019;Other services not ` | ❌ |
| 33 | UIL | IN | EUR | N | O | IN7 | `` | `P1019;Other services not ` | ❌ |
| 33 | UIL | IN | EUR | N | O | IN7 | `` | `P1019;Other services not ` | ❌ |
| 33 | UIL | IN | EUR | N | O | IN7 | `` | `P1019;Other services not ` | ❌ |
| 33 | UIL | IN | EUR | N | O | IN7 | `` | `P1019;Other services not ` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 59 | UNES | JO | USD | J | O | JO8 | `` | `/PURP/809/<XBLNR>` | ❌ |
| 63 | UIL | IN | USD | N | O |  | `` | `` | ✅ |
| 63 | UIL | IN | USD | N | O |  | `` | `` | ✅ |
| 63 | UIL | IN | USD | N | O |  | `` | `` | ✅ |
| 63 | UIL | IN | USD | N | O |  | `` | `` | ✅ |
| 63 | UIL | IN | USD | N | O |  | `` | `` | ✅ |
| 63 | UIL | IN | USD | N | O |  | `` | `` | ✅ |
| 63 | UIL | IN | USD | N | O |  | `` | `` | ❌ |

## Sample breakdown (first 5)


### Scenario 21 — IIEP → IN (LZBKZ=)

**Ustrd**: predicted = ``

  no LZBKZ → no PPC tag


### Scenario 33 — UIL → IN (LZBKZ=IN7)

**Ustrd**: predicted = `P1019;Other services not included elsewhere                           ;INV;<XBLNR>`

    ORD=01 PPC_VAR → T015L[IN7].ZWCK1.first='P1019'
    ORD=02 SEPARATOR → ';'
    ORD=03 PPC_DESCR → T015L[IN7].ZWCK1.rest='Other services not included elsewhere                           '
    ORD=04 SEPARATOR → ';'
    ORD=05 FIXED_VAL → 'INV'
    ORD=06 SEPARATOR → ';'
    ORD=07 PAY_FIELD FPAYP-XBLNR → (requires runtime data)


### Scenario 33 — UIL → IN (LZBKZ=IN7)

**Ustrd**: predicted = `P1019;Other services not included elsewhere                           ;INV;<XBLNR>`

    ORD=01 PPC_VAR → T015L[IN7].ZWCK1.first='P1019'
    ORD=02 SEPARATOR → ';'
    ORD=03 PPC_DESCR → T015L[IN7].ZWCK1.rest='Other services not included elsewhere                           '
    ORD=04 SEPARATOR → ';'
    ORD=05 FIXED_VAL → 'INV'
    ORD=06 SEPARATOR → ';'
    ORD=07 PAY_FIELD FPAYP-XBLNR → (requires runtime data)


### Scenario 33 — UIL → IN (LZBKZ=IN7)

**Ustrd**: predicted = `P1019;Other services not included elsewhere                           ;INV;<XBLNR>`

    ORD=01 PPC_VAR → T015L[IN7].ZWCK1.first='P1019'
    ORD=02 SEPARATOR → ';'
    ORD=03 PPC_DESCR → T015L[IN7].ZWCK1.rest='Other services not included elsewhere                           '
    ORD=04 SEPARATOR → ';'
    ORD=05 FIXED_VAL → 'INV'
    ORD=06 SEPARATOR → ';'
    ORD=07 PAY_FIELD FPAYP-XBLNR → (requires runtime data)


### Scenario 33 — UIL → IN (LZBKZ=IN7)

**Ustrd**: predicted = `P1019;Other services not included elsewhere                           ;INV;<XBLNR>`

    ORD=01 PPC_VAR → T015L[IN7].ZWCK1.first='P1019'
    ORD=02 SEPARATOR → ';'
    ORD=03 PPC_DESCR → T015L[IN7].ZWCK1.rest='Other services not included elsewhere                           '
    ORD=04 SEPARATOR → ';'
    ORD=05 FIXED_VAL → 'INV'
    ORD=06 SEPARATOR → ';'
    ORD=07 PAY_FIELD FPAYP-XBLNR → (requires runtime data)


## XSD validation errors

- Scenario 21: <string>:8:0:ERROR:SCHEMASV:SCHEMAV_CVC_DATATYPE_VALID_1_2_1: Element '{urn:iso:std:iso:20022:tech:xsd:pain.001.001.03}CtrlSum': '6453.00-' is not a v
- Scenario 33: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 110 (<string>, line 63)
- Scenario 33: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 110 (<string>, line 63)
- Scenario 33: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 110 (<string>, line 63)
- Scenario 33: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 110 (<string>, line 63)
- Scenario 33: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 110 (<string>, line 63)
- Scenario 33: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 110 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 59: XML syntax: Opening and ending tag mismatch: XBLNR line 63 and Ustrd, line 63, column 45 (<string>, line 63)
- Scenario 63: <string>:8:0:ERROR:SCHEMASV:SCHEMAV_CVC_DATATYPE_VALID_1_2_1: Element '{urn:iso:std:iso:20022:tech:xsd:pain.001.001.03}CtrlSum': '88.92-' is not a val
