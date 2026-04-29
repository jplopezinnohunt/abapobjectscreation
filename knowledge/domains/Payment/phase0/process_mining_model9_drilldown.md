# PM Model 9 Drill-down — HBKID × Vendor matrix
**Generated**: P01 Gold DB REGUH × LFBK × LFA1

## Test matrix coverage (data-driven from production traffic)

Goal: every test case in V001 maps to a real (HBKID, vendor country) combination that exists in production. Volume gives priority.

## Per HBKID — top vendor bank countries


### SOG01 — 512,303 payments — 🎯 IN SCOPE

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | (empty) | 267,630 |
| FR | FR | 81,683 |
| IT | IT | 9,901 |
| UA | UA | 8,336 |
| DE | DE | 6,408 |
| LB | LB | 5,826 |
| ES | ES | 5,688 |
| GB | GB | 3,673 |
| BE | BE | 3,526 |
| EG | EG | 3,244 |
| ZW | ZW | 3,156 |
| US | FR | 2,618 |
| KE | KE | 2,579 |
| ZA | ZA | 2,367 |
| BA | BA | 2,196 |

### CIT01 — 78,728 payments — 🎯 IN SCOPE

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| BR | BR | 70,081 |
| (empty) | BR | 4,736 |
| CA | CA | 1,647 |
| US | BR | 346 |
| FR | FR | 242 |
| BR | FR | 238 |
| US | CA | 191 |
| US | US | 124 |
| BR | CA | 109 |
| US | AR | 92 |
| CA | US | 64 |
| BR | XX | 60 |
| FR | CA | 60 |
| CH | CH | 52 |
| BR | MZ | 40 |

### CIT04 — 67,304 payments — 🎯 IN SCOPE

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | (empty) | 27,414 |
| US | US | 9,615 |
| US | FR | 4,122 |
| MG | MG | 4,094 |
| US | MM | 1,820 |
| FR | FR | 1,773 |
| TN | TN | 1,628 |
| MM | MM | 1,356 |
| US | AR | 908 |
| US | LB | 516 |
| US | TH | 464 |
| US | CR | 420 |
| US | ZW | 407 |
| GB | IT | 384 |
| US | ET | 384 |

### UNI01 — 27,289 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| IT | IT | 9,542 |
| US | US | 655 |
| IN | IN | 646 |
| FR | FR | 592 |
| BE | IN | 521 |
| DE | DE | 472 |
| BE | IT | 442 |
| LT | IT | 394 |
| GB | GB | 384 |
| IT | IN | 375 |
| IT | AR | 369 |
| BE | BR | 279 |
| IT | US | 210 |
| BE | PK | 202 |
| IT | UZ | 191 |

### SOG05 — 11,792 payments — 🎯 IN SCOPE

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| DE | DE | 9,143 |
| GB | GB | 308 |
| DE | LU | 244 |
| FR | FR | 224 |
| ES | ES | 216 |
| IE | IE | 183 |
| CA | CA | 178 |
| US | US | 152 |
| MA | MA | 120 |
| SG | IN | 109 |
| IT | IT | 108 |
| AF | AF | 76 |
| FR | DE | 71 |
| IN | IN | 68 |
| AU | AU | 60 |

### SOG03 — 9,262 payments — 🎯 IN SCOPE

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | (empty) | 3,303 |
| GB | GB | 3,256 |
| AU | AU | 652 |
| CH | CH | 528 |
| JP | JP | 290 |
| FR | FR | 105 |
| FR | CH | 96 |
| GB | CH | 96 |
| SG | GB | 68 |
| GB | FR | 64 |
| RU | GB | 60 |
| (empty) | TH | 52 |
| AU | FR | 52 |
| TH | JP | 50 |
| CO | CO | 48 |

### SOG02 — 7,778 payments — 🎯 IN SCOPE

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| FR | FR | 5,538 |
| DE | DE | 224 |
| ES | ES | 220 |
| FR | SN | 208 |
| GB | GB | 124 |
| AT | AT | 109 |
| NL | FR | 100 |
| US | FR | 84 |
| US | ES | 80 |
| NL | NL | 56 |
| BE | BR | 52 |
| BE | ES | 52 |
| IT | FR | 45 |
| AR | AR | 44 |
| FR | CN | 44 |

### CIT21 — 4,689 payments — 🎯 IN SCOPE

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | (empty) | 3,401 |
| CA | CA | 1,048 |
| US | CA | 60 |
| CA | CO | 52 |
| FR | SN | 44 |
| CA | FR | 40 |
| FR | FR | 16 |
| FR | CA | 12 |
| IT | FR | 8 |
| US | JO | 8 |

### BRA01 — 1,320 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | BR | 732 |
| BR | BR | 508 |
| (empty) | (empty) | 80 |

### AIB01 — 739 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| AF | AF | 265 |
| (empty) | AF | 226 |
| US | FR | 114 |
| (empty) | FR | 33 |
| FR | FR | 33 |
| US | BD | 17 |
| US | CN | 11 |
| US | PK | 10 |
| CA | CA | 8 |
| HK | FR | 8 |
| US | DE | 8 |
| GB | GB | 6 |

### BTE01 — 526 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| IR | IR | 300 |
| (empty) | FR | 121 |
| (empty) | IR | 48 |
| US | FR | 31 |
| FR | FR | 26 |

### SCB12 — 231 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | KE | 202 |
| KE | KE | 11 |
| MG | MG | 9 |
| US | KE | 9 |

### BMN01 — 195 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | FR | 81 |
| CU | CU | 39 |
| (empty) | CU | 34 |
| FR | CI | 33 |
| US | FR | 8 |

### ECO02 — 193 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | CI | 128 |
| CI | CI | 65 |

### CIT07 — 167 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | CD | 113 |
| CD | CD | 54 |

### SCB14 — 164 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | (empty) | 164 |

### ECO04 — 159 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | ML | 98 |
| ML | ML | 61 |

### CIT19 — 151 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | SD | 86 |
| EG | EG | 21 |
| (empty) | EG | 20 |
| SD | SD | 17 |
| FR | EG | 7 |

### BST01 — 119 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | MZ | 74 |
| MZ | MZ | 45 |

### ECO09 — 110 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | MZ | 78 |
| MZ | MZ | 32 |

### SCB16 — 107 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | GH | 87 |
| FR | GH | 20 |

### CIT15 — 105 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| US | FR | 42 |
| (empty) | LB | 18 |
| (empty) | FR | 13 |
| LB | LB | 11 |
| AT | FR | 7 |
| FR | FR | 7 |
| FR | SN | 7 |

### CIC01 — 104 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | (empty) | 104 |

### FTB01 — 79 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | KH | 63 |
| KH | KH | 16 |

### SCB15 — 61 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | QA | 61 |

### SCB02 — 60 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | NP | 54 |
| (empty) | FR | 6 |

### SCB09 — 53 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | NG | 39 |
| US | DE | 7 |
| US | ET | 7 |

### CBE01 — 51 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| US | ET | 22 |
| (empty) | ET | 19 |
| ET | ET | 10 |

### BOP01 — 41 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | PS | 22 |
| (empty) | FR | 11 |
| (empty) | EG | 8 |

### SCB05 — 32 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | PK | 22 |
| HK | FR | 10 |

### CIT24 — 30 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | GA | 30 |

### CIT10 — 28 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | GT | 22 |
| GT | GT | 6 |

### CIT26 — 28 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | JO | 22 |
| JO | JO | 6 |

### GRN01 — 25 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | IN | 25 |

### CIT22 — 19 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | UY | 19 |

### CRA01 — 18 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | (empty) | 18 |

### BLN01 — 15 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| FR | SD | 8 |
| US | SD | 7 |

### SCB17 — 14 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | VN | 14 |

### CIT05 — 11 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | HT | 11 |

### CIT06 — 11 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| MA | MA | 11 |

### BAE01 — 7 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| CL | CL | 7 |

### CIT03 — 7 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| (empty) | RU | 7 |

### SCB08 — 6 payments — ⚪ Out of scope

| Vendor bank country | Vendor address country | Payments |
|---|---|---|
| US | ID | 6 |

## Top 10 vendors per in-scope HBKID (drill-down by recipient)


### SOG01 top recipients

| LIFNR | Name | Address country | Bank country | Payments |
|---|---|---|---|---|
|  |  |  |  | 1,541 |
| 0000347452 | BECHTLE ISD GMBH | DE | DE | 1,086 |
| 0000710195 | Orange SA | FR | FR | 1,032 |
| 0000711524 | SERENEST ENTREPRISE GROUPE VERMAAT | FR | FR | 963 |
| 0000306704 | TELECOM ITALIA SPA | IT | IT | 784 |
| 0000710609 | MSH International | FR | FR | 765 |
| 0000306470 | STARS ORBIT CONSULTANCY AND | JO | JO | 661 |
| 0000702608 | LA POSTE | FR | FR | 648 |
| 0000702321 | MARLINK SAS | FR | FR | 592 |
| 0000304452 | MAKERERE UNIVERSITY | UG | UG | 576 |

### SOG02 top recipients

| LIFNR | Name | Address country | Bank country | Payments |
|---|---|---|---|---|
| 0000702724 | ATS CULLIGAN ILE DE FRANCE | FR | FR | 168 |
| 0004023288 | THAILINGER Agustina | ES | ES | 160 |
| 0010110103 | Jean Claude NDABANANIYE | FR | FR | 152 |
| 0000700416 | DHL INTERNATIONAL EXPRESS FRANCE SA | FR | FR | 150 |
| 0000702349 | STEM PROPRETE | FR | FR | 144 |
| 0000700521 | TRESOR PUBLIC RECETTE GENERALE DES | FR | FR | 112 |
| 0010163203 | Carlos Martin BENAVIDES ABANTO | FR | FR | 109 |
| 0004017460 | GUILBERT Nathalie | FR | FR | 108 |
| 0000709186 | ORANGE BUSINESS liaison Internet | FR | FR | 104 |
| 0000702672 | AMERICAN EXPRESS CARTE FRANCE | FR | FR | 102 |

### SOG03 top recipients

| LIFNR | Name | Address country | Bank country | Payments |
|---|---|---|---|---|
| 0004027052 | HINCKS Joseph Peter | GB | GB | 136 |
| 0004016010 | KOSTIANAIA Evgeniia | GB | GB | 120 |
| 0000600014 | INTERNATIONAL UNION FOR | CH | CH | 108 |
| 0004008977 | LARA LOPEZ Ana Ligia | AU | AU | 108 |
| 0004017799 | MENDES Tania Abreu | GB | GB | 104 |
| 0004012633 | NOGUCHI Masaya | JP | JP | 100 |
| 0000100440 | UNESCO IBE | CH | CH | 96 |
| 0004024418 | SRICHAISUPHAKIT Palita | GB | GB | 96 |
| 0004023722 | MCLAREN Helen Christine | GB | GB | 84 |
| 10000627 |  |  |  | 81 |

### SOG05 top recipients

| LIFNR | Name | Address country | Bank country | Payments |
|---|---|---|---|---|
| 0000319223 | Telekom Deutschland GmbH | DE | DE | 2,490 |
| 0000319216 | AIR PLUS INTERNATIONAL GMBH | DE | DE | 518 |
| 0000334364 | Amazon Payments Europe S.C.A. | LU | DE | 244 |
| 0010048024 | Isabell KEMPF | DE | DE | 188 |
| 0010151861 | Katja ROEMER | DE | DE | 175 |
| 0010105997 | Madina Bolly | DE | DE | 163 |
| 0010134794 | Edith HAMMER | DE | DE | 155 |
| 0010106002 | Elisabeth KROLAK | DE | DE | 151 |
| 0010151742 | Annapurna AYYAPPAN | DE | DE | 144 |
| 0010131331 | Mo Wang | DE | DE | 143 |

### CIT01 top recipients

| LIFNR | Name | Address country | Bank country | Payments |
|---|---|---|---|---|
| 0000904874 | Flytour Business Travel Viagens e T | BR | BR | 691 |
| 0010062474 | Marlova JOVCHELOVITCH NOLETO | BR | BR | 586 |
| 0010081583 | Fabio SOARES EON | BR | BR | 353 |
| 0010016038 | Lorena DE SOUSA CARVALHO | BR | BR | 341 |
| 0000909405 | VIP PUBLICIDADE LEGAL E SERVICOS LT | BR | BR | 320 |
| 0010022871 | Isabel DE FREITAS PAULA | BR | BR | 286 |
| 0010015225 | Cleber C. DE SOUZA | BR | BR | 273 |
| 0010067273 | Maria OTERO GOMES | BR | BR | 265 |
| 0010006301 | Beatriz M. GODINHO BARROS COELHO | BR | BR | 261 |
| 0010106083 | Adauto CANDIDO SOARES | BR | BR | 257 |

### CIT04 top recipients

| LIFNR | Name | Address country | Bank country | Payments |
|---|---|---|---|---|
| 0000100019 | FAO - UN FOOD AND AGRICULTURAL ORG | IT | GB | 592 |
| 0000710609 | MSH International | FR | FR | 552 |
| 0000100034 | UNESCWA UNITED NATIONS ECONOMIC AND | LB | LB | 416 |
| 0000100071 | UNITED NATIONS SYSTEM STAFF COLLEGE | IT | DE | 352 |
| 0010151803 | Tamer EID | FR | FR | 352 |
| 0000200009 | COMMISSION NATIONALE MALGACHE POUR | MG | MG | 300 |
| 0010057680 | Ichiro MIYAZAWA | FR | US | 284 |
| 0000100030 | UNITED NATIONS | US | US | 272 |
| 0004012089 | LIU Bosen | US | CA | 264 |
| 0010110418 | Francesc PEDRÓ | VE | FR | 256 |

### CIT21 top recipients

| LIFNR | Name | Address country | Bank country | Payments |
|---|---|---|---|---|
| 0004014437 | BENEDETTI Lisa | CA | CA | 92 |
| 10015688 |  |  |  | 81 |
| 10016143 |  |  |  | 81 |
| 10023862 |  |  |  | 81 |
| 10040277 |  |  |  | 81 |
| 10050037 |  |  |  | 81 |
| 10053317 |  |  |  | 81 |
| 10067798 |  |  |  | 81 |
| 10068182 |  |  |  | 81 |
| 10068687 |  |  |  | 81 |

## Test matrix proposal — V001 unit tests

Tier 1 (mandatory, >1000 payments):

| Test # | HBKID | Vendor bank country | Volume |
|---|---|---|---|
| T01 | SOG01 | None | 267,630 |
| T02 | SOG01 | FR | 81,683 |
| T03 | CIT01 | BR | 70,081 |
| T04 | CIT04 | None | 27,414 |
| T05 | SOG01 | IT | 9,901 |
| T06 | CIT04 | US | 9,615 |
| T07 | SOG05 | DE | 9,143 |
| T08 | SOG01 | UA | 8,336 |
| T09 | SOG01 | DE | 6,408 |
| T10 | SOG01 | LB | 5,826 |
| T11 | SOG01 | ES | 5,688 |
| T12 | SOG02 | FR | 5,538 |
| T13 | CIT01 | None | 4,736 |
| T14 | CIT04 | US | 4,122 |
| T15 | CIT04 | MG | 4,094 |
| T16 | SOG01 | GB | 3,673 |
| T17 | SOG01 | BE | 3,526 |
| T18 | CIT21 | None | 3,401 |
| T19 | SOG03 | None | 3,303 |
| T20 | SOG03 | GB | 3,256 |
| T21 | SOG01 | EG | 3,244 |
| T22 | SOG01 | ZW | 3,156 |
| T23 | SOG01 | US | 2,618 |
| T24 | SOG01 | KE | 2,579 |
| T25 | SOG01 | ZA | 2,367 |
| T26 | SOG01 | BA | 2,196 |
| T27 | SOG01 | CA | 2,170 |
| T28 | SOG01 | CO | 2,074 |
| T29 | SOG01 | UG | 1,922 |
| T30 | CIT04 | US | 1,820 |
