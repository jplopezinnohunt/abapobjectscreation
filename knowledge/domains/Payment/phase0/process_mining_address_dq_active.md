# Process Mining: Address DQ for Active Payment Vendors
**Generated**: from P01 Gold DB REGUH+LFA1+ADRC

## Scope refinement

Phase 0 Finding A reported 5/111K vendors missing CITY1+COUNTRY. But that included all active vendors. Real V001 risk is among vendors that **actually received payments via our 4 target trees** in production.

**Active payment vendor count**: 31,334

## Address DQ per CBPR+ tag (CBPR+ Hybrid minimum = TwnNm + Ctry)

| Tag | Missing | % missing | Severity |
|---|---|---|---|
| `<Ctry>` | 5,022 | 16.03% | **CRITICAL** if >0 |
| `<TwnNm>` | 5,022 | 16.03% | **CRITICAL** if >0 |
| `<PstCd>` | 5,190 | 16.56% | OPTIONAL but preferred |
| `<StrtNm>` | 5,240 | 16.72% | OPTIONAL |
| `<BldgNb>` | 19,092 | 60.93% | OPTIONAL |

**CBPR+ blockers** (missing TwnNm OR Ctry): **5,022 vendors (16.027% of active payment base)**

## Country distribution of active payment vendors (top 30)

| Vendor LAND1 | Active vendors | % of total |
|---|---|---|
| (empty) | 5,022 | 16.03% |
| BR | 4,451 | 14.21% |
| FR | 3,963 | 12.65% |
| IT | 1,528 | 4.88% |
| US | 918 | 2.93% |
| GB | 735 | 2.35% |
| DE | 530 | 1.69% |
| UA | 527 | 1.68% |
| IN | 436 | 1.39% |
| ES | 407 | 1.30% |
| KE | 387 | 1.24% |
| AR | 341 | 1.09% |
| CA | 335 | 1.07% |
| EG | 305 | 0.97% |
| MG | 301 | 0.96% |
| ZA | 298 | 0.95% |
| LB | 274 | 0.87% |
| CN | 265 | 0.85% |
| ZW | 242 | 0.77% |
| CO | 238 | 0.76% |
| BE | 236 | 0.75% |
| BA | 227 | 0.72% |
| MA | 219 | 0.70% |
| NG | 217 | 0.69% |
| TN | 190 | 0.61% |
| SN | 189 | 0.60% |
| CH | 183 | 0.58% |
| NL | 183 | 0.58% |
| MX | 178 | 0.57% |
| GH | 173 | 0.55% |

## Blocker vendor list (5022 vendors)

| LIFNR | LAND1 | Missing | Recent payments |
|---|---|---|---|
|  |  | CITY1, COUNTRY | 115636 |
| 10154618 |  | CITY1, COUNTRY | 168 |
| 10150386 |  | CITY1, COUNTRY | 165 |
| 10000627 |  | CITY1, COUNTRY | 162 |
| 10001293 |  | CITY1, COUNTRY | 162 |
| 10002803 |  | CITY1, COUNTRY | 162 |
| 10005779 |  | CITY1, COUNTRY | 162 |
| 10011280 |  | CITY1, COUNTRY | 162 |
| 10016188 |  | CITY1, COUNTRY | 162 |
| 10023862 |  | CITY1, COUNTRY | 162 |
| 10028982 |  | CITY1, COUNTRY | 162 |
| 10030442 |  | CITY1, COUNTRY | 162 |
| 10034702 |  | CITY1, COUNTRY | 162 |
| 10035808 |  | CITY1, COUNTRY | 162 |
| 10038050 |  | CITY1, COUNTRY | 162 |
| 10051271 |  | CITY1, COUNTRY | 162 |
| 10055471 |  | CITY1, COUNTRY | 162 |
| 10056280 |  | CITY1, COUNTRY | 162 |
| 10057543 |  | CITY1, COUNTRY | 162 |
| 10059196 |  | CITY1, COUNTRY | 162 |

## Conclusions

⚠️ **5022 active-payment vendors are CBPR+ blockers**. Master Data team must fix these BEFORE V001 cutover or those payments will fail bank validation.
