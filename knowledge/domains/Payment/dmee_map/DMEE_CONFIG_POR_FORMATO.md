# Configuracion DMEE por formato -- D01

> GENERADO por `Zagentexecution/quality_checks/dmee_tree_map.py`. **No editar a mano.**
> Regenerar: `python Zagentexecution/quality_checks/dmee_tree_map.py --sys D01 --md <este_fichero>`

Que lee cada seccion: el arbol DMEE completo de un formato -- estructura, de donde sale el valor de cada nodo, que exit lo decide, y bajo que condicion se emite. El **orden de los hijos es el orden del XML**, y para `PstlAdr` ese orden es un `xs:sequence` de ISO 20022: violarlo es el rechazo del 21-07-2026.

Un nodo puede tener mapping **y** exit a la vez. **Gana el exit** -- el mapping solo dice que haria SAP si nadie lo hubiera sobrescrito.

## Formatos vivos

Medido en `REGUT.DTFOR` de P01 (la tabla de medios = lo que ve FDTA), no supuesto.

| Formato (= TREE_ID) | Total 2024+ | 2026 | Paises | Nodos | PstlAdr | Hallazgos |
|---|---:|---:|---|---:|---:|---|
| `/CGI_XML_CT_UNESCO` | 3323 | 697 | FR, GB | 628 | 7 | NOV-2026×2 |
| `/CITI/XML/UNESCO/DC_V3_01` | 2695 | 607 | BR, CA, US | 625 | 10 | HIBRIDO×5, NOV-2026×1 |
| `/SEPA_CT_UNES` | 1192 | 258 | FR | 111 | 2 | HIBRIDO×1, ORDEN×1 |
| `/SEPA_CT_ICTP_ISO` | 671 | 112 | IT | 113 | 2 | - |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA` | 532 | 136 | IT | 120 | 3 | NOV-2026×1 |
| `ZSETIF_FOR_ICTP` | 27 | 0 | IT | 134 | 0 | - |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA_I` | 9 | 4 | IT | 116 | 3 | NOV-2026×1 |

---

## `/CGI_XML_CT_UNESCO`

628 nodos en V001 (versiones existentes: 000, 001, 002). 3323 medios generados desde 2024, 697 en 2026, paises FR, GB.

### Exits que llama

| Funcion | Nodos | Quien la entrega |
|---|---:|---|
| `FI_CGI_DMEE_EXIT_W_BADI` | 392 | SAP estandar |

### Direcciones postales

#### `CdtTrfTxInf > Cdtr > PstlAdr` -- OK

Nodo padre `N_8311560080`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `-PstlAdr_More_Nodes_Cdtr` | `N_6304594040` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` |
| 2 | `Dept` | `N_5483073050` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 3 | `SubDept` | `N_6298847140` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 4 | `StrtNm` | `N_8711074510` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 5 | `BldgNb` | `N_4025073060` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 6 | `PstCd` | `N_1441905910` | `FPAYH-ZPSTL` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 7 | `TwnNm` | `N_1709533600` | `FPAYH-ZORT1` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 8 | `CtrySubDvsn` | `N_3320603430` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 9 | `Ctry` | `N_9930896580` | `FPAYHX-ZLISO` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |

#### `CdtTrfTxInf > CdtrAgt > FinInstnId > PstlAdr` -- OK

Nodo padre `N_0693479130`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_0597776110` | `FPAYH-ZBSTR` · `cv 'CL RP    X'` |
| 2 | `TwnNm` | `N_5046489430` | `FPAYH-ZBORT` · `cv 'CL RP    X'` |
| 3 | `CtrySubDvsn` | `N_0992690140` | `FPAYHX-ZBREGX` · `cv 'CL RP    X'` |
| 4 | `Ctry` | `N_9575266080` | `FPAYHX-ZBISO` · `cv 'CL       X'` |

#### `CdtTrfTxInf > IntrmyAgt1 > FinInstnId > PstlAdr` -- **[NOV-2026]**

Nodo padre `N_1676766900`.

- **NOV-2026** -- sin <TwnNm> estructurado

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `Ctry` | `N_8089003480` | `FPAYH-BNKS1` |

#### `CdtTrfTxInf > UltmtCdtr > PstlAdr` -- OK

Nodo padre `N_4634017880`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `-PstlAdr_More_Nodes_UltmtCdtr` | `N_4036970840` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` |
| 2 | `Dept` | `N_2174147050` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 3 | `SubDept` | `N_2270667760` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 4 | `StrtNm` | `N_8210927030` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 5 | `BldgNb` | `N_3599361390` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 6 | `PstCd` | `N_0620492590` | `FPAYH-ZPSTL` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 7 | `TwnNm` | `N_9772090110` | `FPAYP-ORT01` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 8 | `CtrySubDvsn` | `N_1436085460` | `FPAYP-REGIO` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 9 | `Ctry` | `N_9987779130` | `FPAYP-LAND1` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |

#### `CdtTrfTxInf > UltmtDbtr > PstlAdr` -- OK

Nodo padre `N_8824498030`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `-PstlAdr_More_Nodes_UltmtDbtr` | `N_7541094900` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` |
| 2 | `Dept` | `N_3227684200` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 3 | `SubDept` | `N_6373861330` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 4 | `StrtNm` | `N_7241032040` | `FPAYP-REF01` · `cv 'CL RP    X'` |
| 5 | `BldgNb` | `N_8697150300` | `FPAYP-REF01` · `cv 'CL RP    X'` |
| 6 | `PstCd` | `N_6911918850` | `FPAYP-REF01` · `cv 'CL RP    X'` |
| 7 | `TwnNm` | `N_9049844490` | `FPAYP-BORT1` · `cv 'CL RP    X'` |
| 8 | `CtrySubDvsn` | `N_3583105820` | `FPAYP-REF01` · `cv 'CL RP    X'` |
| 9 | `Ctry` | `N_6604713370` | `FPAYP-BLAND` · `cv 'CL RP    X'` |

#### `Dbtr > PstlAdr` -- OK

Nodo padre `N_1160789980`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `-PstlAdr_More_Nodes` | `N_2326418530` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` |
| 2 | `Dept` | `N_0293281340` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 3 | `SubDept` | `N_8127716780` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 4 | `StrtNm` | `N_3466207710` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 5 | `BldgNb` | `N_9244532990` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 6 | `PstCd` | `N_6313994640` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 7 | `TwnNm` | `N_8152860500` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 8 | `CtrySubDvsn` | `N_5664097610` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 9 | `Ctry` | `N_9432681780` | `FPAYHX-LDISO` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |

#### `DbtrAgt > FinInstnId > PstlAdr` -- **[NOV-2026]**

Nodo padre `N_7978288280`.

- **NOV-2026** -- sin <TwnNm> estructurado

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `Ctry` | `N_6779051850` | `FPAYHX-UBISO` |
| 2 | `AdrLine1` | `N_6968343150` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 3 | `AdrLine` | `N_6461922040` | `FPAYHX-UBSTR` · `node N_6968343150` · `cv 'CL RP    X'` |
| 4 | `AdrLine2` | `N_3814726690` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 5 | `AdrLine` | `N_4920858270` | `FPAYHX-UBORT` · `node N_3814726690` · `cv 'CL RP    X'` |

---

## `/CITI/XML/UNESCO/DC_V3_01`

625 nodos en V001 (versiones existentes: 000, 001, 002). 2695 medios generados desde 2024, 607 en 2026, paises BR, CA, US.

### Exits que llama

| Funcion | Nodos | Quien la entrega |
|---|---:|---|
| `FI_CGI_DMEE_EXIT_W_BADI` | 22 | SAP estandar |
| `/CITIPMW/V3_DMEE_EXIT_CGI_XML` | 3 | Citi (add-on del banco) |
| `/CITIPMW/V3_EXIT_CGI_CRED_NAME` | 2 | Citi (add-on del banco) |
| `/CITIPMW/V3_CGI_CRED_PO_CITY` | 2 | Citi (add-on del banco) |
| `/CITIPMW/V3_CGI_CRED_STREET` | 2 | Citi (add-on del banco) |
| `/CITIPMW/V3_EXIT_CGI_CRED_CITY` | 2 | Citi (add-on del banco) |
| `/CITIPMW/V3_CGI_CRED_REGION` | 2 | Citi (add-on del banco) |
| `/CITIPMW/V3_POSTALCODE` | 2 | Citi (add-on del banco) |
| `/CITIPMW/V3_GET_CDTR_BLDG` | 2 | Citi (add-on del banco) |
| `/CITIPMW/V3_EXIT_CGI_CRED_NM2` | 2 | Citi (add-on del banco) |
| `/CITIPMW/V3_DMEE_EXIT_INV_DESC` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_GET_CDTR_EMAIL` | 1 | Citi (add-on del banco) |
| `Z_DMEE_EXIT_TAX_NUMBER` | 1 | **nuestra** -- la podemos cambiar |
| `/CITIPMW/V3_CGI_TAX_CATEGORY` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_CGI_TAX_METHOD` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_CGI_REGULATORY_INF` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_CGI_TAX_FORMS_CODE` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_EXIT_CGI_CRED_NM4` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_CGI_BANK_NAME` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_EXIT_CGI_TP_WHT` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_WL949_BIC_OR_ID` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_EXIT_CGI_DEBT_NAME` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_EXIT_CGI_TAX_SQNB` | 1 | Citi (add-on del banco) |
| `DMEE_EXIT_SEPA_21` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_41` | 1 | SAP estandar |
| `/CITIPMW/V3_CGI_TAX_CTGRY_DTLS` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_GET_CDTR_MOBILE` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_EXIT_CGI_CRED_NM3` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_CGI_TAXAMT_TTLAMT` | 1 | Citi (add-on del banco) |
| `/CITIPMW/V3_TAXAMT_TXBASEAMT` | 1 | Citi (add-on del banco) |
| `DMEE_EXIT_SEPA_31` | 1 | SAP estandar |
| `Y_FI_DMEE_NAME` | 1 | **nuestra** -- la podemos cambiar |

### Direcciones postales

#### `CdtTrfTxInf > Cdtr > PstlAdr` -- OK

Nodo padre `N_1496761000`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_3511983780` | `cv 'CLURP    X'` |
| 2 | `BldgNb` | `N_9516561760` | `EXIT /CITIPMW/V3_GET_CDTR_BLDG [CITI]` |
| 3 | `PstCd` | `N_4122233110` | `(vacio)` |
| 4 | `TwnNm` | `N_3708282600` | `(vacio)` |
| 5 | `CtrySubDvsn` | `N_7413462330` | `(vacio)` |
| 6 | `Ctry` | `N_8876219870` | `FPAYHX-ZLISO` |

#### `CdtTrfTxInf > Cdtr > PstlAdr` -- OK

Nodo padre `N_2368849090`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_3825417170` | `cv 'CLURP    X'` |
| 2 | `BldgNb` | `N_4400978440` | `EXIT /CITIPMW/V3_GET_CDTR_BLDG [CITI]` |
| 3 | `PstCd` | `N_0249673900` | `(vacio)` |
| 4 | `TwnNm` | `N_3747128920` | `(vacio)` |
| 5 | `CtrySubDvsn` | `N_3301357040` | `(vacio)` |
| 6 | `Ctry` | `N_6501921410` | `FPAYHX-ZLISO` |

#### `CdtTrfTxInf > CdtrAgt > FinInstnId > PstlAdr` -- **[HIBRIDO]**

Nodo padre `N_5135503450`.

- **HIBRIDO** -- estructurado + AdrLine en el mismo PstlAdr

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_4517277200` | `FPAYH-ZBSTR` · `cv 'CL RP    X'` |
| 2 | `TwnNm` | `N_0693583510` | `FPAYH-ZBORT` · `cv 'CL RP    X'` |
| 3 | `CtrySubDvsn` | `N_8863924120` | `FPAYHX-ZBREGX` · `cv 'CL RP    X'` |
| 4 | `Ctry` | `N_0956892600` | `(vacio)` |
| 5 | `AdrLine` | `N_4255403060` | `(vacio)` |

#### `CdtTrfTxInf > IntrmyAgt1 > FinInstnId > PstlAdr` -- **[HIBRIDO]**

Nodo padre `N_8694918840`.

- **HIBRIDO** -- estructurado + AdrLine en el mismo PstlAdr

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `TwnNm` | `N_8051547660` | `FPAYHX-AGNT1ORT01` · `cv 'CL       X'` |
| 2 | `Ctry` | `N_2610452900` | `FPAYH-BNKS1` |
| 3 | `AdrLine` | `N_7208252640` | `FPAYHX-AGNT1STRAS` · `cv 'CL       X'` |

#### `CdtTrfTxInf > IntrmyAgt2 > FinInstnId > PstlAdr` -- **[HIBRIDO]**

Nodo padre `N_7565057960`.

- **HIBRIDO** -- estructurado + AdrLine en el mismo PstlAdr

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `TwnNm` | `N_5965287340` | `FPAYHX-AGNT2ORT01` · `cv 'CL       X'` |
| 2 | `Ctry` | `N_9803166830` | `FPAYH-BNKS2` |
| 3 | `AdrLine` | `N_2930009720` | `FPAYHX-AGNT2STRAS` · `cv 'CL       X'` |

#### `CdtTrfTxInf > UltmtCdtr > PstlAdr` -- **[HIBRIDO]**

Nodo padre `N_3468319710`.

- **HIBRIDO** -- estructurado + AdrLine en el mismo PstlAdr

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `-PstlAdr_More_Nodes_UltmtCdtr` | `N_1384700510` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` |
| 2 | `Dept` | `N_1729098660` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 3 | `SubDept` | `N_0068661910` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 4 | `StrtNm` | `N_1015394030` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 5 | `BldgNb` | `N_7033747740` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 6 | `PstCd` | `N_8256311070` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 7 | `TwnNm` | `N_7990518960` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 8 | `CtrySubDvsn` | `N_9916193710` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 9 | `Ctry` | `N_9752167650` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL RP    X'` |
| 10 | `AdrLine` | `N_0634513430` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |

#### `CdtTrfTxInf > UltmtCdtr > PstlAdr` -- **[HIBRIDO]**

Nodo padre `N_4600960730`.

- **HIBRIDO** -- estructurado + AdrLine en el mismo PstlAdr

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_1622450530` | `cv 'CLURP    X'` |
| 2 | `PstCd` | `N_8447100720` | `FPAYH-ZPSTL` |
| 3 | `TwnNm` | `N_8324954730` | `FPAYH-ZORT1` · `cv 'CLURP    X'` |
| 4 | `CtrySubDvsn` | `N_7777719150` | `FPAYH-ZREGI` · `cv 'CLURP    X'` |
| 5 | `Ctry` | `N_8276095420` | `FPAYH-ZLAND` |
| 6 | `AdrLine` | `N_9497274200` | `(vacio)` |

#### `Dbtr > PstlAdr` -- OK

Nodo padre `N_1905437260`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `Dept` | `N_7832936870` | `(vacio)` |
| 2 | `SubDept` | `N_4483531300` | `(vacio)` |
| 3 | `StrtNm` | `N_6139800480` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 4 | `BldgNb` | `N_4712017280` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 5 | `PstCd` | `N_3474870610` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 6 | `TwnNm` | `N_2266488280` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 7 | `CtrySubDvsn` | `N_6927898900` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 8 | `Ctry` | `N_4523469420` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |

#### `Dbtr > PstlAdr` -- OK

Nodo padre `N_5197213060`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `Dept` | `N_9619139080` | `(vacio)` |
| 2 | `SubDept` | `N_7678372610` | `(vacio)` |
| 3 | `StrtNm` | `N_7635476580` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 4 | `BldgNb` | `N_5208833070` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 5 | `PstCd` | `N_9674037090` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 6 | `TwnNm` | `N_2369381760` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 7 | `CtrySubDvsn` | `N_1368770440` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 8 | `Ctry` | `N_1761658350` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |

#### `DbtrAgt > FinInstnId > PstlAdr` -- **[NOV-2026]**

Nodo padre `N_4249821970`.

- **NOV-2026** -- sin <TwnNm> estructurado

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `Ctry` | `N_7268011670` | `FPAYHX-UBISO` |

---

## `/SEPA_CT_UNES`

111 nodos en V001 (versiones existentes: 000, 001, 002). 1192 medios generados desde 2024, 258 en 2026, paises FR.

### Exits que llama

| Funcion | Nodos | Quien la entrega |
|---|---:|---|
| `Y_FI_DMEE_ADR` | 17 | **nuestra** -- la podemos cambiar |
| `FI_CGI_DMEE_EXIT_W_BADI` | 2 | SAP estandar |
| `DMEE_EXIT_SE_DATE` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_31` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_41` | 1 | SAP estandar |
| `ZDMEE_EXIT_SEPA_21` | 1 | **nuestra** -- la podemos cambiar |

### Direcciones postales

#### `CdtTrfTxInf > Cdtr > PstlAdr` -- OK

Nodo padre `N_0412758380`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `-PstlAdr_More_Nodes_Cdtr` | `N_9051681470` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` |
| 2 | `Dept` | `N_7213712110` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 3 | `SubDept` | `N_0038163390` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 4 | `StrtNm` | `N_8434593170` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CLURP    X'` |
| 5 | `BldgNb` | `N_6554304020` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL RP    X'` |
| 6 | `PstCd` | `N_1214474870` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 7 | `TwnNm` | `N_5373093250` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 8 | `CtrySubDvsn` | `N_4548550170` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 9 | `Ctry` | `N_1974922770` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |

#### `Dbtr > PstlAdr` -- **[ORDEN]** **[HIBRIDO]**

Nodo padre `N_9412627890`.

- **ORDEN** -- orden ISO roto: Dept SubDept StrtNm BldgNb PstCd TwnNm Ctry CtrySubDvsn AdrLine -> debe ser Dept SubDept StrtNm BldgNb PstCd TwnNm CtrySubDvsn Ctry AdrLine
- **HIBRIDO** -- estructurado + AdrLine en el mismo PstlAdr

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `-PstlAdr_More_Nodes` | `N_9268732240` | `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` |
| 2 | `Dept` | `N_4947603910` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 3 | `SubDept` | `N_8690323650` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 4 | `StrtNm` | `N_1215903670` | `FPAYHX-AUST2` · `cv 'CL       X'` |
| 5 | `BldgNb` | `N_1396453300` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 6 | `PstCd` | `N_2703639030` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 7 | `TwnNm` | `N_7609981350` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 8 | `Ctry` | `N_2225746230` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 9 | `CtrySubDvsn` | `N_7471680250` | `EXIT Y_FI_DMEE_ADR [CUSTOM]` · `cv 'CL       X'` |
| 10 | `AdrLine` | `N_4946758140` | `FPAYHX-ORT1Z` · `cv 'CL RP    X'` |

---

## `/SEPA_CT_ICTP_ISO`

113 nodos en V001 (versiones existentes: 000, 001). 671 medios generados desde 2024, 112 en 2026, paises IT.

### Exits que llama

| Funcion | Nodos | Quien la entrega |
|---|---:|---|
| `DMEE_EXIT_SE_DATE` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_31` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_41` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_21` | 1 | SAP estandar |

### Direcciones postales

#### `CBIPaymentRequest > PmtInf > CdtTrfTxInf > Cdtr > PstlAdr` -- OK

Nodo padre `N_4754354180`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_2790093090` | `FPAYH-ZSTRA` · `cv 'CL RP    X'` |
| 2 | `PstCd` | `N_1659664320` | `FPAYH-ZPSTL` · `cv 'CL RP    X'` |
| 3 | `TwnNm` | `N_7068451440` | `FPAYH-ZORT1` · `cv 'CL RP    X'` |
| 4 | `Ctry` | `N_4138520450` | `FPAYHX-ZLISO` |

#### `CBIPaymentRequest > PmtInf > Dbtr > PstlAdr` -- OK

Nodo padre `N_9926185740`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_4946758140` | `FPAYH-ZSTRA` · `cv 'CL RP    X'` |
| 2 | `PstCd` | `N_4266300820` | `FPAYHX-REF01` · `cv 'CL RP    X'` |
| 3 | `TwnNm` | `N_6311223610` | `FPAYHX-ORT1Z` · `cv 'CL RP    X'` |
| 4 | `Ctry` | `N_3928239110` | `FPAYHX-LAND1` |

---

## `/SEPA_CT_ICTP_ISO_EXTRASEPA`

120 nodos en V001 (versiones existentes: 000, 001). 532 medios generados desde 2024, 136 en 2026, paises IT.

### Exits que llama

| Funcion | Nodos | Quien la entrega |
|---|---:|---|
| `FI_CGI_DMEE_EXIT_W_BADI` | 2 | SAP estandar |
| `Z_ICTP_DMEE_J_IBAN` | 1 | **nuestra** -- la podemos cambiar |
| `DMEE_EXIT_SE_DATE` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_31` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_41` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_21` | 1 | SAP estandar |

### Direcciones postales

#### `CBICrossBorderPaymentRequestLogMsg > PmtInf > CdtTrfTxInf > Cdtr > PstlAdr` -- OK

Nodo padre `N_4754354180`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_2790093090` | `FPAYH-ZSTRA` · `cv 'CL RP    X'` |
| 2 | `PstCd` | `N_1659664320` | `FPAYH-ZPSTL` · `cv 'CL RP    X'` |
| 3 | `TwnNm` | `N_7068451440` | `FPAYH-ZORT1` · `cv 'CL RP    X'` |
| 4 | `Ctry` | `N_4138520450` | `FPAYHX-ZLISO` |

#### `CBICrossBorderPaymentRequestLogMsg > PmtInf > CdtTrfTxInf > CdtrAgt > FinInstnId > PstlAdr` -- **[NOV-2026]**

Nodo padre `N_9054224620`.

- **NOV-2026** -- sin <TwnNm> estructurado

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `Ctry` | `N_8370781800` | `const 'TRF'` · `FPAYHX-ZBISO` |

#### `CBICrossBorderPaymentRequestLogMsg > PmtInf > Dbtr > PstlAdr` -- OK

Nodo padre `N_9926185740`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_4946758140` | `const 'Strada Costiera 11'` · `FPAYHX-REF01` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 2 | `TwnNm` | `N_6311223610` | `FPAYHX-ORT1Z` · `cv 'CL RP    X'` |
| 3 | `Ctry` | `N_3928239110` | `FPAYHX-LAND1` |

---

## `ZSETIF_FOR_ICTP`

134 nodos en V000 (versiones existentes: 000). 27 medios generados desde 2024, 0 en 2026, paises IT.

### Exits que llama

| Funcion | Nodos | Quien la entrega |
|---|---:|---|
| `Z_ICTP_DMEE_SETIF` | 1 | **nuestra** -- la podemos cambiar |
| `ZDMEE_EXIT_ZSETIF_FOR_INTCN3` | 1 | **nuestra** -- la podemos cambiar |
| `ZDMEE_ICTP_EXIT_SETIF` | 1 | **nuestra** -- la podemos cambiar |
| `ZDMEE_EXIT_ZSETIF_IBAN` | 1 | **nuestra** -- la podemos cambiar |

### Direcciones postales

---

## `/SEPA_CT_ICTP_ISO_EXTRASEPA_I`

116 nodos en V001 (versiones existentes: 000, 001). 9 medios generados desde 2024, 4 en 2026, paises IT.

### Exits que llama

| Funcion | Nodos | Quien la entrega |
|---|---:|---|
| `FI_CGI_DMEE_EXIT_W_BADI` | 2 | SAP estandar |
| `DMEE_EXIT_SE_DATE` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_31` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_41` | 1 | SAP estandar |
| `DMEE_EXIT_SEPA_21` | 1 | SAP estandar |

### Direcciones postales

#### `CBICrossBorderPaymentRequestLogMsg > PmtInf > CdtTrfTxInf > Cdtr > PstlAdr` -- OK

Nodo padre `N_4754354180`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_2790093090` | `FPAYH-ZSTRA` · `cv 'CL RP    X'` |
| 2 | `PstCd` | `N_1659664320` | `FPAYH-ZPSTL` · `cv 'CL RP    X'` |
| 3 | `TwnNm` | `N_7068451440` | `FPAYH-ZORT1` · `cv 'CL RP    X'` |
| 4 | `Ctry` | `N_4138520450` | `FPAYHX-ZLISO` |

#### `CBICrossBorderPaymentRequestLogMsg > PmtInf > CdtTrfTxInf > CdtrAgt > FinInstnId > PstlAdr` -- **[NOV-2026]**

Nodo padre `N_9054224620`.

- **NOV-2026** -- sin <TwnNm> estructurado

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `Ctry` | `N_8370781800` | `const 'TRF'` · `FPAYHX-ZBISO` |

#### `CBICrossBorderPaymentRequestLogMsg > PmtInf > Dbtr > PstlAdr` -- OK

Nodo padre `N_9926185740`.

| # | Etiqueta XML | Nodo | De donde sale el valor |
|---:|---|---|---|
| 1 | `StrtNm` | `N_4946758140` | `const 'Strada Costiera 11'` · `FPAYHX-REF01` · `EXIT FI_CGI_DMEE_EXIT_W_BADI [SAP]` · `cv 'CL       X'` |
| 2 | `TwnNm` | `N_6311223610` | `FPAYHX-ORT1Z` · `cv 'CL RP    X'` |
| 3 | `Ctry` | `N_3928239110` | `FPAYHX-LAND1` |

