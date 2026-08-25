---
name: Gold DB × SAP Process Mining — what info each table holds and how it's used
description: Analysis (2026-06-21) mapping every Gold DB table category to its SAP process-mining role (5-class taxonomy + case/activity/timestamp/resource), which end-to-end process it serves, and coverage vs gaps. Leverages the verified sap_event_sources_catalog.md + process_mining_capability_inventory.md. Companion to gold_db_table_catalog.md.
type: project
---

# Gold DB × SAP Process Mining

> "Qué información tenemos de todas las tablas, y para qué se usan en process mining." Built on the
> deep-research-verified base: `sap_event_sources_catalog.md` (van der Aalst/RWTH sap-extractor, OCEL 2.0)
> + `process_mining_capability_inventory.md`. Not re-derived — synthesized from what we already evaluated.

## 1. The SAP process-mining model (best practice)
An event log must span **5 table classes**, and every event maps to **case / activity / timestamp / resource**:
| Class | Role | SAP examples |
|---|---|---|
| **Flow** | document chains (object lifecycle) | EKBE (P2P), VBFA (O2C), AWTYP+AWKEY (FI) |
| **Transaction** | the business records = the events | BKPF, RBKP, VBRK |
| **Change** | audit trail (field changes) | **CDHDR + CDPOS** |
| **Record** | document headers | EKKO, EBAN, VBAK |
| **Detail** | line items | EKPO, BSEG |
SAP relations are mostly one-to-many → **object-centric (OCEL 2.0)** is the correct model (not flattened).

## 2. What we have — Gold DB inventory by category (row counts 2026-06-21)
| Category | Tables | Rows | Process-mining role |
|---|---|---|---|
| **LOGS / audit / change** | 15 | **28.8M** | the EVENT raw material — see §3 |
| FI docs / GL | 8 | 8.4M | Transaction + Detail (postings) |
| Treasury / payment | 16 | 6.0M | Payment E2E events + bank recon |
| PSM / FM budget | 39 | 4.8M | B2R budget lifecycle |
| MM / P2P | 12 | 4.7M | Flow + Record + Detail (procurement) |
| CO / PS | 10 | 3.8M | cost/project postings |
| Master data | 15 | 2.3M | OCEL objects (Vendor/Customer/Bank/Address) |
| Config (T*) | 81 | 113K | activity decode + decision rules (TJ02T, T028*, TCURR) |
| Transport / integration | 5 | 142K | IDoc/RFC interface events (EDIDC) |
| D01-provenance | 24 | — | system-invariant maps (tcode→program) |
| Custom / analysis | 44 | — | our derived event logs / sims |

## 3. Tables → process-mining role + which process they serve
| SAP source (Gold DB) | PM class | case_id | activity | timestamp | resource | Process |
|---|---|---|---|---|---|---|
| **BKPF** (+bseg_union) | Transaction | BELNR | "Posted <BLART>" | BUDAT/CPUDT | USNAM | FI / all |
| **EKKO/EKPO/EBAN** | Record | EBELN/BANFN | "Created PO/PR" | AEDAT | ERNAM | **P2P** |
| **EKBE** | Flow | EBELN | GR/IR (BEWTP) | BUDAT | — | **P2P** |
| **ESSR/ESLL** | Flow/Detail | LBLNI | service entry | — | — | **P2P** services |
| **RBKP/RSEG** | Transaction/Detail | BELNR | invoice receipt | BUDAT | USNAM | **P2P** |
| **REGUH/REGUP** + FEBEP/FEBKO/FEBRE | Transaction/Flow | LAUFD/payment | pay run / clearing / bank stmt | — | — | **Payment E2E** |
| **FMIFIIT/FMIOI/FMBH/FMBL** | Transaction/Flow | FMBELNR | budget consume/commit/CF | PERIO | — | **B2R / budget** |
| **CDHDR** (12M, have) | **Change** (header) | OBJECTCLAS+OBJECTID | "Changed <obj>" / tcode | UDATE+UTIME | USERNAME | audit / all |
| CDPOS (NOT have) | **Change** (detail) | +CHANGENR | field old→new | (CDHDR) | — | audit (field-level) |
| **rsau_audit_history** (8.5M, NEW) | **Resource / org / control** | SLGUSER+session | logon / tcode-start / report-start / RFC / master-change | SAL_DATE+SAL_TIME | SLGUSER | **SoD / security / "way of working"** |
| **tbtco/tbtcp** (have) | batch | JOBNAME | program + VARIANT (intent) | SDLSTRTDT | AUTHCKNAM | batch automation |
| EDIDC (have) | interface | DOCNUM | IDoc status | CREDAT | — | integration |
| JEST/JCDS | status | OBJNR | status change (TJ02T) | (JCDS) | — | order/PS lifecycle |

## 4. What the LOG tables we just built UNLOCK
- **`rsau_audit_history` = the Resource/Organizational/SoD source.** In `process_mining_capability_inventory.md` §G (Organizational) this was **NONE**. We now have it: handover-of-work, resource/role profiling, and **systematic Segregation-of-Duties** (the BCM dual-control we found *by hand* becomes a query: same user create+approve). Plus security events (logon, master-data changes). The triage filter (keep Dialog Logon + Transaction Start + User Master Changes + High severity) is in `gold_db_table_catalog.md`.
- **`cdhdr_history` (12M) = the Change class.** Drives `cdhdr_activity_mapping.py` (OBJECTCLAS+TCODE→activity). The field-level Detail (CDPOS) stays the #1 deferred gap.
- **`tbtco/tbtcp` = batch process + JOB INTENT via VARIANT** (skill `sap_variant_analysis`).

## 5. Coverage vs gaps (against the 5-class best practice)
- **HAVE:** Transaction (BKPF/RBKP), Record (EKKO/EBAN), Flow (EKBE; partial), Change-header (CDHDR), **Resource (RSAU — new)**, batch (TBTCO/TBTCP), interface (EDIDC).
- **MISSING (priority, per catalog §L):** **CDPOS** (Change detail — deferred by decision), **JCDS** (status history — order/PS lifecycle), **VBFA/VBAK** (O2C flow — we have almost no Sales), **SWW*** (workflow/approval steps + agents), **NAST** (output/print), AFKO/RESB/QMEL (PP/QM).
- **Analysis layer (capability inventory):** we use ~5-10% — only DFG discovery; **conformance (as-implemented vs standard), object-centric (OCPN/OCEL 2.0), event-log quality filtering, predictive/ML, decision mining, and systematic SoD are all NONE.** That backlog is the real product, not more extraction.

## 6. End-to-end processes our data enables
- **P2P** — strong (EKKO/EKPO/EKBE/ESSR/RBKP + BKPF). Built: `p2p.ocel2.sqlite`, `p2p_process_mining`.
- **Payment E2E** — strong (REGUH/REGUP/FEBEP/FEBKO/FEBRE/BNK_BATCH). Built: `payment_process_mining`.
- **B2R / budget** — strong (FM tables). 
- **Audit / SoD / "forma de trabajar"** — **newly enabled** by `rsau_audit_history` + `cdhdr_history`.
- **O2C** — weak/missing (no VBAK/VBAP/VBFA/VBRK extracted) → biggest source gap if Sales matters.

## 7b. RSAU process-engineering analysis — FIRST CUT (2026-06-21, human activity Apr–Jun)
Categorization (§3) ≠ analysis. Mining the human signal (Dialog Logon + Transaction Start, technical users excluded):
- **What humans actually do** (after stripping nav SESSION_MANAGER/S000): the work is **Finance/FM/Treasury/P2P** —
  MIRO/MIR4 (invoice verification), FMRP_*/FMX3 (budget reporting), FEB_BSPROC + F.13 (bank stmt + clearing),
  FBL1N/ME23N (vendor items / PO display), custom cockpits ZICTP_COCKPIT/YFM1. `SE16` by 13 users = direct
  table access (a control flag) — **usuarios que operaron DENTRO de SE16; el recuento de ARRANQUES de SE16
  se desconoce** (ver claim 219).
  ⚠ **La lista es INCOMPLETA** — medida con `SLGTC` (tcode LANZADOR), así que **faltan los tcodes TERMINALES**
  desde los que no se lanza nada: `XK02`, `FB01`, `PR01`, `PA30` entre ellos. **Re-derivar con `PARAM1`.**
  (Sobrevive por coincidencia: MIRO, FMX3 y FBL1N son a la vez lanzadores frecuentes y lanzados frecuentes.)
- **When** (by hour, UTC): office double-peak **10–11h & 14–16h with a 12–13h lunch dip**, plus a **persistent
  4–9K/hour overnight floor → globally distributed workforce** (field offices across timezones), not just HQ.
  > **Este perfil horario SOBREVIVE al defecto A48 — no tires la §7b entera por contagio
  > (verificado 2026-08-26).** Un perfil por hora se calcula sobre `SAL_TIME` de las filas de la
  > subclase, y **la columna por la que agrupas el tcode es irrelevante para cuándo ocurrieron esas
  > filas**. Lo único que podría moverlo es el filtro `SLGTC<>''` si los 108.375 descartados tuvieran
  > otra distribución horaria — INFERIDO, no comprobable sin el Gold: un 8,8% no borra un doble pico
  > ni un suelo nocturno de 4-9K/hora.
- **User fingerprints — RETIRADAS.** ~~generalistas (T_NDUNGU 22 tcodes, G_PEROTIN 21) vs especialistas
  (O_KIRARA 5 — the vendor-address XK02 editor seen in CDHDR). Each user's tcode mix = their de-facto role.~~
  **RETIRADO 2026-08-26:** los recuentos de tcodes distintos por usuario miden **desde dónde NAVEGA** cada
  usuario, no **qué EJECUTA** — que es exactamente lo contrario de lo que la frase promete. La contradicción
  es visible en el propio texto: O_KIRARA aparece con 5 tcodes y **sin `XK02`**, aunque CDHDR lo identifica
  como el editor de direcciones de proveedor; bajo `SLGTC` no podía estar. La inferencia
  *mezcla-de-tcodes = rol-de-facto* **es válida como MÉTODO, pero exige `PARAM1`.**
- **NEXT analysis layers (not yet done)**: (a) **tcode SEQUENCES per session** = the actual process flows
  (pm4py DFG on user-sessions, case_id = SLGUSER+logon-window); (b) **systematic SoD** = users doing both
  entry (MIRO/FB60) and settle/clear (F.13/FBRA/F110) — the BCM dual-control finding generalized; (c)
  **handover-of-work** between users on the same object (join to CDHDR by OBJECTID); (d) off-hours actor
  drill-down (who/where the overnight floor is).

## 7e. SATELLITE-APP operation map — SAP is operated heavily via RFC/BAPI, not dialog (2026-06-21, user-directed)
Triangulating CDHDR (result, channel via TCODE) × RSAU RFC stream (method, the BAPI) reveals UNESCO operates
SAP substantially through SATELLITE apps. Five drivers:
1. **BRIDGE-RFC** (procurement+travel+master-read portal gateway) — PR (BAPI_PR_GETDETAIL/CHANGE), PO
   (BAPI_PO_GETDETAIL1/CREATE1), Service (BAPI_ENTRYSHEET_GET*), Vendor/GL/Bank read (ZBAPI_VENDOR_*/GLACCOUNT_GETLIST),
   **Travel via custom `YHRTRV_IF_GET/MODIFY_TRIP`** (46K) — the #1 satellite driver.
2. **MULESOFT** (integration bus) — FM/Fund master (FMFUNDBPD via FM5U/FM5I, `Y_FMKU_0050_CREATE_WITH_COMMIT`,
   `FM_FUND_CHANGE_RFC`) + **Project creation (PROJ, blank-tcode/MULESOFT)**.
3. **WF-BATCH** (HR lifecycle workflow automation) — HR infotype changes HR_IT1000/1001 (org/relationships) via RE_RHAKTI00.
4. **PBC engine** (F_DERAKHSHAN/HIPER, ZPBC_PERIOD_CLS_EXEC/SE38) — payroll-commitment generation, **FMRESERV 6.4M** (blank tcode).
5. **Named-user BAPI** (E_SILVA/L_NEVES/MP_ANCUTA/C_SOUZA) — GR (BAPI_GOODSMVT_CREATE), invoice
   (BAPI_INCOMINGINVOICE_CREATE1), PR/PO create — an external receiving/AP portal posting under the user's ID.
DIALOG is a MINORITY for P2P, Travel, FM-master, HR-org, Projects. Custom satellite interfaces
(`YHRTRV_IF_*`, `ZBAPI_VENDOR_*`, `Y_FMKU_*`) = the brain/LLM moat (no commercial PM tool understands them).
Method: model each satellite as an OCEL resource/system; the BAPI = activity; connect to interface-intelligence
(RFCDES destinations, .NET apps, Coupa). This is the real "way of working" — operation-by-satellite.

## 7f. RFC-stream caveats: OUR footprint, more satellites, by-year (2026-06-21, user-directed)
- **DATA QUALITY — exclude OUR OWN calls:** `RFC_READ_TABLE` by `JP_LOPEZ` = 76,137 (our extraction) + DDIF_FIELDINFO_GET
  ~3K + RFC_GET_FUNCTION_INTERFACE ~1.5K = ~80K self-inflicted RFC calls in the 4-month window. ALWAYS filter
  `SLGUSER='JP_LOPEZ'` (and watch P_LUVHIMBI, who also runs DDIF/interface probes) before reporting RFC volumes.
- **More satellite RFCs (single-caller custom = dedicated external systems):** `Y_BAPI_WBS_FINANCIAL_DATA_1` **974,874**
  (#1, WBS financials, 1 caller), `Z_RFC_GET_USER` 508K (970 users, portal SSO), `Y_BAPI_YPS8` 461K (1), `Y_BAPI_CUSTOMER_GET_ID`
  148K (1), `Y_RFC_UBO_YEBUR003_BCS` 40K (1, BCS budget), `ARFC_DEST_SHIP/CONFIRM` 82K (tRFC/IDoc async). Each single-caller
  custom Y/Z RFC = a dedicated satellite reading one domain.
- **BY-YEAR (do this next):** the RSAU audit is **2026-only (4 months)** → RFC trend = by-MONTH; **CDHDR spans 2024-2026**
  → master-change trend = by-YEAR. Demo: vendor (KRED) changes 2024=29,337 → **2025=110,238 (3.7x peak)** → 2026=3,831
  (4mo, ~93% collapse). The 2025 spike (mass vendor cleanup/migration?) + 2026 collapse is exactly what the by-year cut surfaces.
  TODO: run by-year on all master OBJECTCLAS + by-month on the satellite RFCs (excluding JP_LOPEZ).

## 7d. METHOD lesson — find a blind spot from RESULT × METHOD (CDHDR is the channel-agnostic detector) (2026-06-21)
> **LECCIÓN DE MÉTODO, CORREGIDA 2026-08-26.** El stream de arranques de transacción **NO es ciego**
> al mantenimiento de maestros en diálogo — **nuestro LECTOR lo era**. Agrupábamos por `SLGTC` (el
> tcode de CONTEXTO desde el que se lanzó) en vez de por `PARAM1` (el tcode ARRANCADO), así que todo
> tcode **TERMINAL** —aquel desde el que no se lanza nada más— daba cero por construcción, y `XK02`
> entre ellos. La lección válida es OTRA y es más útil: **cuando un stream da CERO en algo que el
> negocio hace todos los días, la primera hipótesis es un defecto del LECTOR, no una propiedad del
> sistema**; y la segunda es **cruzar con una fuente independiente ANTES de publicar** — aquí CDHDR
> estaba tres líneas más abajo diciendo lo contrario. Sigue siendo cierto, y **por su propio mérito**,
> que CDHDR es el detector agnóstico de canal y el punto de partida correcto para minar procesos de
> cambio.
>
> *Texto retirado (conservado para anti-regresión):* ~~The audit-log activity stream (Transaction
> Starts) counts SESSIONS not CHANGES and misses the RFC/BAPI write channel → it made MDM look like
> \~0 (a blind spot).~~ **RETIRADO 2026-08-26:** atribuía a una PROPIEDAD DE SAP lo que era un bug de
> nuestro lector (A48 `semantic_activity_map`, agrupación por `SLGTC`; las dos columnas coinciden en
> 8 de 1.235.225 filas). Segunda mano, no re-medido: leyendo `PARAM1`, `XK01`+`XK02` = 54.126
> arranques de diálogo y MDM completo 55.024, frente a los 35 que imprime el script.

The fix: read the RESULT side — **CDHDR change documents
(channel-agnostic: every change, with USERNAME + the TCODE that delates the channel)** — and cross it with the
METHOD side (RFC/BAPI call stream). CORRECTED finding: vendor master is NOT ~0 — **KRED = 143,406 change docs**,
DOMINANTLY dialog **XK02 by M_AYIMBA (72,718 = the #1 vendor maintainer)** + a SECONDARY external BAPI channel
(`ZBAPI_VENDOR_CHANGE`/MP_ANCUTA 19K). GL master **SACH = only 25** (FS00, stable, dialog); GL is READ via BAPI
(`ZBAPI_GLACCOUNT_GETLIST`) but rarely changed. CDHDR OBJECTCLAS map = the real "what changes in P01" inventory:
FMRESERV 6.4M, BELEG 442K, EINKBELEG 188K, KRED 143K, ENTRYSHEET 128K, BANF 106K, HR_IT* . Start change-process
mining from CDHDR (result), not the activity stream. The §7c RFC/BAPI view below is the METHOD half — both are needed.

> **La CORRECCIÓN con CDHDR de este párrafo SOBREVIVE ENTERA al defecto A48 — no la reabras
> (verificado 2026-08-26).** «KRED = 143.406 change docs, dominantly dialog XK02 by M_AYIMBA
> (72.718)» y el inventario `OBJECTCLAS` salen de **CDHDR**, una fuente completamente independiente
> del audit-log y de la columna `SLGTC`. Y conviene subrayar lo que esto significa, porque vale más
> que el dato: **la evidencia que REFUTABA el artefacto estaba publicada tres líneas más arriba, en
> el mismo fichero y el mismo día, y no se leyó como refutación sino como complemento.** El fallo no
> fue falta de datos.

## 7c. Master data & financials run via RFC/BAPI **IN ADDITION TO** dialog (2026-06-21, user-confirmed + audit-located; título corregido 2026-08-26)
**El MDM en diálogo NO es ≈0** — esa lectura venía de agrupar el audit-log por `SLGTC`. Medido en CDHDR
(§7d): **`KRED` = 143.406 documentos de cambio, dominados por `XK02` en DIÁLOGO** (M_AYIMBA 72.718), con
`ZBAPI_VENDOR_CHANGE` (MP_ANCUTA 19.481 + S_STANTIC 4.683) como canal **SECUNDARIO** — el diálogo cuadruplica
al BAPI que esta sección declaraba sustituto. Lo que sí es cierto y se conserva: GL accounts y vendor master
**también** se mantienen por soluciones EXTERNAS vía RFC/BAPI, invisibles al análisis de tcode y capturadas en
el stream RSAU "RFC Function Call" (PARAM3 = FM name, SLGUSER = RFC user). Localizado en `rsau_audit_history`:

> *Texto retirado (conservado para anti-regresión):* ~~«Master data & financials run via RFC/BAPI, NOT
> dialog» · «Why dialog MDM ≈ 0 (FS00 by 1 user): GL accounts and vendor master are maintained by EXTERNAL
> solutions via RFC/BAPI»~~ — **RETIRADO 2026-08-26.** Daba el cero por hecho y se ponía a explicarlo; estaba
> refutado **dentro del mismo fichero, nueve líneas más arriba** (§7d, `KRED` dominantemente `XK02`). La
> etiqueta *user-confirmed* es lo que lo hacía peligroso: parecía validado por humano. Causa: A48
> `semantic_activity_map` agrupa por `SLGTC` (lanzador) en vez de `PARAM1` (arrancado).

- **Vendor master CHANGE también por `ZBAPI_VENDOR_CHANGE`** (MP_ANCUTA 19,481 + S_STANTIC 4,683) — **canal
  secundario, junto al `XK02` en diálogo que lo cuadruplica** (~~"not XK02"~~ RETIRADO 2026-08-26). Read/search via
  **BRIDGE-RFC** (`ZBAPI_VENDOR_GETDETAIL` 72K, `ZBAPI_VENDOR_SEARCH*`); bank via `ZBAPI_GET_BANK_COUNTRY_DATA`.
- **FM/Fund master = MuleSoft** (`Y_FMKU_0050_CREATE_WITH_COMMIT`, `FM_FUND_CHANGE_RFC`).
- Integration backbone (top RFC): `Y_BAPI_WBS_FINANCIAL_DATA_1` 974K (#1, WBS financials), `Z_RFC_GET_USER` 508K,
  `Y_BAPI_YPS8` 461K, `Y_BAPI_CUSTOMER_GET_ID` 148K, `BAPI_INCOMINGINVOICE_CREATE1`/`BAPI_GOODSMVT_CREATE` (E_SILVA/L_NEVES).
  > **Este inventario de RFCs de integración SOBREVIVE INTACTO al defecto A48 (verificado 2026-08-26):**
  > sale del stream *RFC Function Call* por `PARAM3` — **otra subclase y otra columna**, que el defecto
  > de `SLGTC` no toca. No lo tires por contagio al corregir el resto de la §7c.
- **GL-account-master BAPI not yet surfaced** (low volume or differently named) — OPEN: grep RFC stream for GL/SKA1.
- Implication: the master-data + WBS-financial "way of working" is a BAPI/integration process. Model it from the
  RFC stream (resource = SLGUSER incl. BRIDGE-RFC/MULESOFT; activity = FM name). Custom Z-BAPI names = the brain/LLM moat.

## 7. Next steps (incremental)
1. Finish the RSAU **quarter** (4-month) pull → find the real audit retention boundary.
2. Apply the RSAU **type filter** as the retention policy (keep signal, drop machine noise).
3. From the capability backlog: wire **conformance** + **OCEL 2.0 / pm4py-full** (the as-implemented-vs-standard overlay) — highest-value analysis we don't yet do.
4. Extend this catalog/analysis to the remaining ~280 tables incrementally.
