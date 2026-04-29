# Drift Follow-up Report
**Generated**: 2026-04-29T14:52:16.477839
## 1. Function modules — TFDIR-based verification
Replaces the false-positive "FM_MISSING" findings from initial drift run.

| FM | P01 exists? | P01 last change | D01 exists? | D01 last change | Verdict |
|---|---|---|---|---|---|
| `FI_PAYMEDIUM_DMEE_CGI_05` | ✅ | 20210410 094347 SAP | ✅ | 20210403 060256 SAP | 🟡 DRIFT |
| `/CITIPMW/V3_PAYMEDIUM_DMEE_05` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153307 SM36623 | 🟡 DRIFT |
| `/CITIPMW/V3_CGI_CRED_STREET` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153307 SM36623 | 🟡 DRIFT |
| `/CITIPMW/V3_CGI_CRED_PO_CITY` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153307 SM36623 | 🟡 DRIFT |
| `/CITIPMW/V3_CGI_CRED_REGION` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153307 SM36623 | 🟡 DRIFT |
| `/CITIPMW/V3_EXIT_CGI_CRED_NAME` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153307 SM36623 | 🟡 DRIFT |
| `/CITIPMW/V3_EXIT_CGI_CRED_NM2` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153307 SM36623 | 🟡 DRIFT |
| `/CITIPMW/V3_EXIT_CGI_CRED_CITY` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153307 SM36623 | 🟡 DRIFT |
| `/CITIPMW/V3_GET_BANKCODE` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153307 SM36623 | 🟡 DRIFT |
| `/CITIPMW/V3_GET_CDTR_BLDG` | ✅ | 20190523 173537 SM36623 | ✅ | 20190523 153306 SM36623 | 🟡 DRIFT |

## 2. DMEE tree versions (the 2x node count mystery)

### /SEPA_CT_UNES
| System | Version | Status | Last user | Last date | Node count |
|---|---|---|---|---|---|

### /CITI/XML/UNESCO/DC_V3_01
| System | Version | Status | Last user | Last date | Node count |
|---|---|---|---|---|---|

### /CGI_XML_CT_UNESCO
| System | Version | Status | Last user | Last date | Node count |
|---|---|---|---|---|---|

### /CGI_XML_CT_UNESCO_1
| System | Version | Status | Last user | Last date | Node count |
|---|---|---|---|---|---|

## 3. TFPM042FB rows — identify D01-only rows
**P01**: 311 rows · **D01**: 316 rows
**Only in D01**: 5 rows · **Only in P01**: 0 rows

### Rows only in D01 (possible WIP)
```json
[
  {
    "EVENT": "00",
    "FNAME": "FI_PAYMEDIUM_PDF_00",
    "FORMI": "/CHECK_SG"
  },
  {
    "EVENT": "30",
    "FNAME": "FI_PAYMEDIUM_CHECK_30",
    "FORMI": "/CHECK_SG"
  },
  {
    "EVENT": "05",
    "FNAME": "FI_PAYMEDIUM_CHECK_05",
    "FORMI": "/CHECK_SG"
  },
  {
    "EVENT": "20",
    "FNAME": "FI_PAYMEDIUM_PDF_20",
    "FORMI": "/CHECK_SG"
  },
  {
    "EVENT": "40",
    "FNAME": "FI_PAYMEDIUM_PDF_40",
    "FORMI": "/CHECK_SG"
  }
]
```

## 4. T042Z rows — identify D01-only rows
**P01**: 263 rows · **D01**: 266 rows
**Only in D01**: 3 rows · **Only in P01**: 0 rows

### Rows only in D01 (possible WIP)
```json
[
  {
    "BLART": "CP",
    "BLARV": "CP",
    "FORMI": "/CHECK_SG",
    "FORMZ": "",
    "LAND1": "FR",
    "MANDT": "350",
    "PROGN": "",
    "TEXT1": "M&C SOCGEN check PMW",
    "TXTSL": "",
    "UMSKZ": "",
    "WEART": "11",
    "WLSTN": "",
    "XAKTZ": "",
    "XBKKT": "",
    "XEINZ": "",
    "XESRD": "",
    "XEURO": "",
    "XEZER": "",
    "XIBAN": "",
    "XNOPO": "",
    "XNO_ACCNO": "",
    "XORB": "",
    "XPGIR": "",
    "XPSKT": "",
    "XSCHK": "X",
    "XSEPA": "",
    "XSTRA": "",
    "XSWEC": "",
    "XWANF": "",
    "XWECH": "",
    "XWECS": "",
    "XZANF": "",
    "XZWHR": "",
    "ZLSCH": "6",
    "ZLSTN": ""
  },
  {
    "BLART": "OP",
    "BLARV": "OP",
    "FORMI": "",
    "FORMZ": "",
    "LAND1": "CN",
    "MANDT": "350",
    "PROGN": "",
    "TEXT1": "Manual transfers",
    "TXTSL": "",
    "UMSKZ": "",
    "WEART": "",
    "WLSTN": "",
    "XAKTZ": "",
    "XBKKT": "X",
    "XEINZ": "",
    "XESRD": "",
    "XEURO": "",
    "XEZER": "",
    "XIBAN": "",
    "XNOPO": "",
    "XNO_ACCNO": "",
    "XORB": "",
    "XPGIR": "",
    "XPSKT": "",
    "XSCHK": "",
    "XSEPA": "",
    "XSTRA": "X",
    "XSWEC": "",
    "XWANF": "",
    "XWECH": "",
    "XWECS": "",
    "XZANF": "",
    "XZWHR": "",
    "ZLSCH": "M",
    "ZLSTN": ""
  },
  {
    "BLART": "OP",
    "BLARV": "OP",
    "FORMI": "",
    "FORMZ": "",
    "LAND1": "CN",
    "MANDT": "350",
    "PROGN": "",
    "TEXT1": "Payment requests to Field Off.",
    "TXTSL": "",
    "UMSKZ": "",
    "WEART": "",
    "WLSTN": "",
    "XAKTZ": "",
    "XBKKT": "",
    "XEINZ": "",
    "XESRD": "",
    "XEURO": "",
    "XEZER": "",
    "XIBAN": "",
    "XNOPO": "",
    "XNO_ACCNO": "",
    "XORB": "",
    "XPGIR": "",
    "XPSKT": "",
    "XSCHK": "X",
    "XSEPA": "",
    "XSTRA": "",
    "XSWEC": "",
    "XWANF": "",
    "XWECH": "",
    "XWECS": "",
    "XZANF": "",
    "XZWHR": "",
    "ZLSCH": "O",
    "ZLSTN": ""
  }
]
```
