# UNESCO Vendor Address Routing by KTOKK (Account Group)

**Discovered**: Session #073 (2026-05-09) during V001 SEPA Dbtr/Cdtr fix.
**Severity**: HIGH — affects every system that prints/exports vendor addresses.

## The pattern

UNESCO maintains **multiple LIFNR records per real-world entity** with different
KTOKKs, and the meaning of `ADRC.STREET` depends on the account group.

### Example: Marlies SPRONK (one person → 4 LIFNR)

| LIFNR | KTOKK | ADRC.STREET | Real meaning |
|---|---|---|---|
| 0000407692 | INDV | `Laurierstraat`, 1016 PL Amsterdam | Personal record (real address) |
| 0010082471 | UNES | `PLACE FONTENOY`, 75352 Paris | UNESCO HQ link |
| 0010199971 | SCSA | **`ADM/DIT/MIS/FBS`**, 75007 Paris | Staff payroll record (dept code, NOT a street) |
| VS90199528 | ICVS | `1, rue Miollis`, Paris | Inter-Company / sub-building |

### Example: Simona BERTOLDINI

| LIFNR | KTOKK | ADRC.STREET | Real meaning |
|---|---|---|---|
| 0010008305 | SCSA | **`BFM/FAS/PAY`**, 75007 Paris | Staff (dept code, NOT a street) |

### Same person's PA0006 SUBTY='1' (HR Address Infotype)

| Person | PERNR | PA0006 SUBTY=1 STRAS | PSTLZ | ORT01 | LAND1 |
|---|---|---|---|---|---|
| Marlies SPRONK | 10199971 | `7, rue des Richardes` | 92260 | FONTENAY-aux-Roses | FR |
| Simona BERTOLDINI | 10008305 | `16 avenue des Murs du Parc` | 94300 | Vincennes | FR |

**Key insight**: PERNR = SCSA LIFNR auto-cast to NUMC(8) (drop leading zeros).

## Decision matrix — where to read the address

| KTOKK | Field interpretation | Source for SEPA / output |
|---|---|---|
| **SCSA** (Staff) | ADRC.STREET = department code (`BFM/FAS/PAY`, `ADM/DIT/MIS/FBS`, `KMI/FAM`, `HRM/SES/BNF`, etc.) | **PA0006 SUBTY='1'** of the PERNR (LIFNR cast to NUMC8). Real home address. |
| **INDV** (Individual) | ADRC.STREET = real personal/home street | ADRC of the LIFNR |
| **UNES** (UNESCO HQ link) | ADRC.STREET = `PLACE FONTENOY` (HQ) | ADRC of the LIFNR |
| **ICVS** (Inter-Company) | ADRC.STREET = real address (e.g. another UNESCO building) | ADRC of the LIFNR |
| Other (external suppliers) | ADRC.STREET = real supplier street | ADRC of the LIFNR |

## Why this matters across UNESCO

UNESCO uses `ADRC.STREET` of the SCSA record to encode internal routing:
`<DEPT>/<DIVISION>/<SUB>` — useful for internal work-item routing, payroll
distribution, badging, but **NOT a real address**.

**Any system that assumes "vendor ADRC = real street" will produce wrong output for staff payments.**

Areas confirmed/likely affected:
- ☑ SEPA Credit Transfer XML (this fix, V001 SEPA_CT_UNES)
- ☑ CGI XML CT formats (same Cdtr/PstlAdr nodes)
- ☑ CITI XML formats
- ⚠ Avisos de pago (RFFOAVIS_FPAYM) — likely shows dept code as street
- ⚠ F110 confirmation prints — likely same
- ⚠ BCM batch printout — likely same
- ⚠ Bank statement reconciliation reports — depend on which path they read
- ⚠ Treasury cash forecasting — probably uses ADRC, may be OK for non-SCSA only

## Implementation reference: `Y_FI_DMEE_ADR` (custom UNESCO FM)

Function module `Y_FI_DMEE_ADR` (in `SAPLYFPAYM` function group, include
`LYFPAYMU19`) implements the routing for SEPA V001:

```abap
SELECT SINGLE ktokk FROM lfa1 INTO lv_ktokk
  WHERE lifnr = <fs_item>-fpayh-gpa1r.
CASE lv_ktokk.
  WHEN 'SCSA'.
    lv_pernr = <fs_item>-fpayh-gpa1r.   " auto-cast C(10) → NUMC(8)
    SELECT SINGLE * FROM pa0006 INTO ls_pa0006
      WHERE pernr = lv_pernr AND subty = '1'
        AND endda >= sy-datlo AND begda <= sy-datlo.
    " StrtNm = ls_pa0006-stras (already includes house number)
    " PstCd  = ls_pa0006-pstlz
    " TwnNm  = ls_pa0006-ort01
    " Ctry   = ls_pa0006-land1
  WHEN 'INDV' | 'UNES' | 'ICVS' | OTHERS.
    " Read ADRC of vendor (real address fields)
    SELECT SINGLE * FROM adrc WHERE addrnumber = <fs_item>-fpayh-zadnr.
ENDCASE.
```

## Audit & remediation pattern

For any payment / reporting object that uses vendor addresses, check:

1. Does it read **ADRC of LIFNR** without checking KTOKK? → likely bug for SCSA
2. Does it read **PA0006** for staff and **ADRC** for others? → correct
3. Does it have a different convention? → document it, then map to this matrix

Recommended: build a centralized helper FM `Y_GET_VENDOR_ADDRESS(LIFNR)` that
returns the real address based on KTOKK, replacing all ad-hoc ADRC reads.

## Closure simulation — full P01 universe (Session #074, 2026-05-10)

After the BERTOLDINI live test in D01, the v6 logic was replayed in pure SQL against
**every payment** made via every SEPA format in P01 over the last 2 years. Universe built
from `DFPAYG ↔ REGUH ↔ LFA1 ↔ PA0006 SUBTY=1 active ↔ ADRC date-valid`.

### Scope clarification — `Y_FI_DMEE_ADR` only fires in `/SEPA_CT_UNES`

P01 `DMEE_TREE_NODE.MP_EXIT_FUNC` per SEPA tree:

| Tree | Address exit FM | In-scope for v6? |
|---|---|---|
| `/SEPA_CT_UNES` | `Y_FI_DMEE_ADR` (after V001 cutover) | **YES** |
| `/SEPA_CT_ICTP_ISO` | none — direct FPAYHX bindings | no |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA` | `FI_CGI_DMEE_EXIT_W_BADI` → `YCL_IDFI_CGI_DMEE_FALLBACK` (Nicolas's class hierarchy) | no |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA_I` | `FI_CGI_DMEE_EXIT_W_BADI` (same) | no |

### `/SEPA_CT_UNES` aggregate result (UNES + IIEP + UIL cocodes)

| Metric | Value |
|---|---|
| Distinct vendors paid (last 2y) | **15,305** |
| PA0006 hits (employee path) | 2,096 |
| Drift v6 ≠ V0 (employees corrected) | **1,905 (12.4%)** |
| Theory violators (drift without PA0006 hit) | **0** |
| KTOKKs that drift | UNES (96.0% of 1,497), SCSA (73.8% of 508), INT (1/1) |
| KTOKKs that don't drift | INDV, INSO, PART, HQSU, FELL, GVNT, UNAG, INGO, UBO (9 KTOKKs · 13,400 vendors · 0% drift) |
| PA0006 hit but no drift (edge case) | 178 — vendors whose ADRC.STREET equals their PA0006.STRAS |

### Theory empirically confirmed: "only employees vary"

Across the 15,305 in-scope vendors, **every single drift case has a PA0006 hit**, and
**every PA0006 hit lives in a staff KTOKK** (UNES / SCSA / INT). Non-staff KTOKKs
(institutional suppliers, individuals, partners, fellowships, governments, agencies,
NGOs) emit identical output to V0 because PA0006 SUBTY=1 never matches their NUMC8 cast.
The PA0006-first detection cleanly partitions the population: employees → home address,
everyone else → vendor ADRC.

### Sample drift rows (KTOKK=UNES — HQ-link staff)

| LIFNR | Name | V0 StrtNm (ADRC) | v6 StrtNm (PA0006) |
|---|---|---|---|
| 0010000146 | Ahmed ABDELLI | `ERI/SEC/FSO` | `20 Rue Rabelais` (Saint Ouen) |
| 0010000247 | Corinne BITOUN | `IEP/IST/LKM` | `38 rue Rieussec` (VIROFLAY) |
| 0010000861 | Irma EKUE | `BFM/USLS` | `3 rue Leroyer` (Vincennes) |
| 0010000942 | Aurore BRILLANT | `7 place de fontenoy` (HQ) | `7 rue Jobbé Duval` (Paris) |
| 0010032406 | Irene FERNANDEZ RAMOS (SCSA) | `CLT/WHC` | `10 Rue René Villermé` |
| 0010103539 | Alessandra BORCHI (SCSA) | `PAX/SRC` | `56 rue de Vouillé` |

### Out-of-scope — ICTP SEPA trees

`/SEPA_CT_ICTP_ISO` + 2 EXTRASEPA variants pay 83 UNES staff making business trips to
Trieste. These trees do **not** wire `Y_FI_DMEE_ADR`. Per rule
`feedback_only_modify_our_own_code`, the fix path is either:

- **Option A**: ask Nicolas to extend `YCL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT` with the
  same PA0006-first detection. Cleanest, but external dependency.
- **Option B**: wire `Y_FI_DMEE_ADR` into the ICTP trees as well (DMEE_TREE_NODE config
  change at the StrtNm/PstCd/TwnNm/Ctry leaves). UNESCO-controlled, no Nicolas dep.

Tracked as known-unknown follow-up; **not part of the V001 SEPA scope**.

### Reproducibility

- Script: `Zagentexecution/sepa_simulator_step1.py` → `step2.py` → `sepa_simulator_all.py`
- Result table: Gold DB → `sim_sepa_all` (21,507 rows · all SEPA tuples) and
  `sim_v6_results` (`/SEPA_CT_UNES UNES` only · 14,636 rows)
- New Gold DB tables: `DFPAYG` (9,848 rows · last 2y) · `DFPAYV` (84 rows · config matrix)

## Related artefacts
- `Y_FI_DMEE_ADR` — DMEE exit FM (this implementation)
- `LYFPAYMU19` — include containing the FM source
- `LFA1` — vendor master (KTOKK), `ADRC` — address master, `PA0006` — HR address infotype
- `extracted_code/FI/DMEE_full_inventory/Y_FI_DMEE_ADR_v5.abap` — current source
- `extracted_code/FI/DMEE_p01_canonical/YCL_IDFI_CGI_DMEE_FALLBACK====CM001.abap` — Nicolas's BAdI (Cdtr/Nm overflow handling, complementary to this FM)
