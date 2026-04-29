# Process Mining Tier 1 Models — V001 scope insights
**Generated**: from P01 Gold DB

## Model 8 — BCM Batch Lifecycle (BNK_BATCH_HEADER + BNK_BATCH_ITEM)

**BBH rows**: 27,443  |  **BBI rows**: 600,042

**BBH columns**: BATCH_NO, RULE_ID, ITEM_CNT, LAUFD, LAUFI, BATCH_SUM, BATCH_CURR, STATUS, CRUSR, CRDATE, CRTIME, CHUSR, CHDATE, CHTIME, CUR_PROCESSOR, ZBUKR, HBKID, CUR_STS

### Status distribution

| Status | Count |
|---|---|
| 005056BEA1661EDC | 2,669 |
| 005056BEA1661EDF | 2,365 |
| 005056BEA1661FD0 | 2,250 |
| 005056BEA1661EDD | 2,225 |
| 005056BE59091ED9 | 2,161 |
| 005056BEA1661EDE | 2,014 |
| 005056BE6DE11EDA | 1,991 |
| 005056BEA1661EDB | 1,622 |
| 005056BE836F1ED8 | 1,093 |
| 005056BE836F1ED7 | 965 |
| 005056BF458B1ED6 | 907 |
| 005056BE59091ED8 | 839 |
| 005056BF605C1ED5 | 821 |
| E4115BB756191ED7 | 805 |
| 005056BF605C1ED6 | 774 |
| 005056BE6DE11EDB | 721 |
| 005056BF458B1ED5 | 683 |
| 005056BF605C1ED4 | 465 |
| 005056BF458B1ED4 | 461 |
| 005056BE59091EDA | 448 |
| 005056BEA1661FD1 | 219 |
| 00505690518F1FE1 | 146 |
| ED69219A73C41ED8 | 126 |
| 005056BF19BB1ED4 | 102 |
| 005056BF19BD1ED4 | 100 |
| 005056BF19B91EE4 | 91 |
| 005056BF003F1ED4 | 82 |
| 005056BF605C1ED7 | 70 |
| 00505690518F1FE0 | 61 |
| 005056BF458B1ED7 | 57 |
| 005056BF00511EE4 | 54 |
| 005056BF003F1EE4 | 32 |
| 005056BF19BD1EE4 | 11 |
| 005056BEA6921ED8 | 6 |
| 005056BF19B91ED4 | 4 |
| 005056BF00511ED4 | 3 |

### Top 15 house banks by batch count

| HBKID | Batches |
|---|---|
| SOG01 | 11,334 |
| CIT04 | 4,916 |
| CIT01 | 3,054 |
| SOG03 | 2,746 |
| SOG02 | 1,465 |
| SOG04 | 860 |
| CIT21 | 783 |
| SOG05 | 767 |
| WEL01 | 504 |
| CHA01 | 499 |
| DNB01 | 185 |
| SCB14 | 75 |
| CIC01 | 70 |
| BPP01 | 70 |
| BNP01 | 42 |

## Model 9 — Per House Bank Emission Distribution

### Top 30 HBKID by F110 payment runs

| HBKID | Payments |
|---|---|
| SOG01 | 490,273 |
| CIT01 | 75,960 |
| CIT04 | 61,053 |
| UNI01 | 23,564 |
| SOG05 | 9,461 |
| SOG03 | 8,701 |
| SOG02 | 7,092 |
| CIT21 | 4,629 |
| BRA01 | 1,316 |
| AIB01 | 746 |
| BTE01 | 519 |
| SCB12 | 251 |
| BMN01 | 207 |
| ECO02 | 193 |
| CIT07 | 172 |
| CIT19 | 167 |
| SCB14 | 164 |
| ECO04 | 149 |
| CIT15 | 112 |
| SCB16 | 108 |
| BST01 | 106 |
| CIC01 | 104 |
| ECO09 | 94 |
| FTB01 | 81 |
| SCB15 | 68 |
| SCB09 | 67 |
| SCB02 | 62 |
| CBE01 | 52 |
| BOP01 | 46 |
| SCB05 | 41 |

### HBKID × Bank country (T012 join)

| HBKID | Bank country | Bank key | Payments |
|---|---|---|---|
| SOG01 | FR | SP0000006K76 | 490,273 |
| CIT01 | BR | 745-5122 | 73,520 |
| CIT04 | US | SP000000A2SU | 61,053 |
| UNI01 | IT | SP00000020MQ | 23,564 |
| SOG05 | FR | SP0000006PWR | 9,461 |
| SOG03 | FR | SP0000006K5S | 8,701 |
| SOG02 | FR | SP0000006K76 | 7,092 |
| CIT21 | CA | XX000017 | 4,629 |
| CIT01 | CA | XX000017 | 2,440 |
| BRA01 | BR | 00191607 | 1,316 |
| AIB01 | AF | SP00000000V9 | 746 |
| BTE01 | IR | IR000029 | 519 |
| SCB12 | KE | SP0000001SC2 | 251 |
| BMN01 | CU | SP0000000BDU | 207 |
| ECO02 | CI | SP0000000VHC | 193 |
| CIT07 | CD | XX000239 | 172 |
| CIT19 | EG | SP0000000M0L | 167 |
| SCB14 | GB | SP0000001SB6 | 164 |
| ECO04 | ML | SP0000000VHQ | 149 |
| CIT15 | LB | SP0000000M3H | 112 |
| SCB16 | GH | SP0000001SBC | 108 |
| BST01 | MZ | SP0000001REJ | 106 |
| CIC01 | FR | SP0000006N8S | 104 |
| ECO09 | MZ | XX001877 | 94 |
| FTB01 | KH | SP0000000Y1X | 81 |
| SCB15 | QA | SP0000001SCT | 68 |
| SCB09 | NG | SP0000001SCI | 67 |
| SCB02 | NP | SP0000001SCK | 62 |
| CBE01 | ET | SP0000000JFP | 52 |
| BOP01 | PS | SP0000001JMQ | 46 |

### Top (Co code, HBKID) combinations

| Co | HBKID | Payments |
|---|---|---|
| UNES | SOG01 | 488,402 |
| UBO | CIT01 | 73,520 |
| UNES | CIT04 | 61,053 |
| ICTP | UNI01 | 23,564 |
| UIL | SOG05 | 9,461 |
| UNES | SOG03 | 8,701 |
| IIEP | SOG02 | 7,092 |
| UNES | CIT21 | 4,629 |
| UIS | CIT01 | 2,440 |
| IIEP | SOG01 | 1,871 |
| UBO | BRA01 | 1,316 |
| UNES | AIB01 | 746 |
| UNES | BTE01 | 519 |
| UNES | SCB12 | 251 |
| UNES | BMN01 | 207 |
| UNES | ECO02 | 193 |
| UNES | CIT07 | 172 |
| UNES | CIT19 | 167 |
| UNES | SCB14 | 164 |
| UNES | ECO04 | 149 |
| UNES | CIT15 | 112 |
| UNES | SCB16 | 108 |
| UNES | BST01 | 106 |
| UNES | CIC01 | 104 |
| UNES | ECO09 | 94 |
| UNES | FTB01 | 81 |
| UNES | SCB15 | 68 |
| UNES | SCB09 | 67 |
| UNES | SCB02 | 62 |
| UNES | CBE01 | 52 |

## Model 10 — Worldlink Currencies via CITI

### Total currency distribution (top 20)

| Currency | Payments | Total amount |
|---|---|---|
| EUR | 207,749 | 1,556,700,421 |
| USD | 109,812 | 1,645,642,228 |
| BRL | 47,174 | 862,231,310 |
| XOF | 4,471 | 16,892,302 |
| MGA | 3,663 | 471,108,652 |
| CAD | 3,572 | 28,698,047 |
| XAF | 3,354 | 7,796,022 |
| GBP | 2,415 | 8,557,465 |
| INR | 2,146 | 48,964,938 |
| THB | 1,407 | 35,536,087 |
| KES | 1,307 | 35,230,391 |
| CHF | 1,274 | 14,703,091 |
| TND | 1,182 | 113,899,513 |
| IDR | 994 | 42,578,149 |
| GHS | 890 | 5,388,083 |
| NGN | 802 | 650,682,388 |
| TZS | 800 | 433,756,474 |
| CNY | 799 | 262,959 |
| MXN | 789 | 0 |
| ETB | 755 | 52,684,455 |

### Worldlink-pattern currencies (BRL/MGA/TND/...)

| Currency | Payments |
|---|---|
| BRL | 47,174 |
| MGA | 3,663 |
| INR | 2,146 |
| THB | 1,407 |
| KES | 1,307 |
| TND | 1,182 |
| IDR | 994 |
| NGN | 802 |
| CNY | 799 |
| MXN | 789 |
| ZAR | 180 |
| ARS | 160 |

### Worldlink Currency × HBKID

| Currency | HBKID | Payments |
|---|---|---|
| BRL | CIT01 | 44,344 |
| MGA | CIT04 | 3,647 |
| INR | SOG01 | 2,098 |
| BRL | SOG01 | 2,037 |
| THB | SOG01 | 1,404 |
| KES | SOG01 | 1,277 |
| TND | CIT04 | 1,162 |
| IDR | SOG01 | 990 |
| NGN | SOG01 | 801 |
| CNY | SOG01 | 796 |
| BRL | BRA01 | 792 |
| MXN | SOG01 | 789 |
| ZAR | SOG01 | 180 |
| ARS | CIT04 | 80 |
| ARS | SOG01 | 80 |
| TND | (empty) | 20 |
| INR | CIT04 | 16 |
| INR | GRN01 | 16 |
| INR | SOG03 | 16 |
| KES | CIT04 | 16 |
| MGA | (empty) | 16 |
| KES | SCB12 | 14 |
| IDR | SCB08 | 4 |
| CNY | CIT04 | 3 |
| THB | CIT04 | 3 |
| BRL | CIT04 | 1 |
| NGN | SCB09 | 1 |

## Model 6 — Reverse/Void Payment Patterns

**REGUH columns available**: LAUFD, LAUFI, ZBUKR, LIFNR, VBLNR, XVORL, HBKID, HKTID

### XVORL flag (X=test proposal, ""=real run)

| XVORL | Count |
|---|---|
| (real run) | 583,905 |
| X | 358,106 |

## Conclusions

- BCM lifecycle stats above identify chokepoints in V000 today; V001 cutover should not increase rejection rates beyond baseline
- HBKID distribution informs test matrix house-bank coverage requirements
- Worldlink currency mix validates UltmtCdtr Q3 deferral or escalation
- Void/reverse patterns identify what TYPE of failures we should test
