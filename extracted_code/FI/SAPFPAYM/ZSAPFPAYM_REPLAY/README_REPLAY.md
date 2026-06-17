# ZSAPFPAYM_REPLAY — Payment Medium Replay para Debug DMEE

**Origen:** copia controlada de `SAPFPAYM` extraído de P01 sesión #072.
**Sistema target:** D01 (no P01 — feedback_p01_readonly_absolute).
**Run de prueba:** D01 / LAUFD=20260507 / LAUFI=10003B / GRPNO=100 / FORMI=/SEPA_CT_UNES.

## Qué hace

Re-procesa un run F110 ya consolidado en `DFPAYG` para regenerar el output DMEE
(XML SEPA, CGI, CITI, etc.) **sin** alterar `REGUV.STATUS` / `DFPAYG.ANZ_ERL`.
Permite escribir el XML a disco local o pantalla y entrar al debugger
exactamente en el momento donde el motor DMEE mapea los campos.

## Diferencias vs SAPFPAYM original

8 bloques comentados en `ZFPAYM_STA`:

| Líneas orig. | Bloque removido | Por qué |
|---|---|---|
| 17-28 | `SELECT REGUV.X_DD_PRENOTIF` + STOP | Gate prenotif DD irrelevante |
| 31-56 | `FIBL_PAYMENT_RUN_MERGE_CHECK` + STOP | Gate cross-payment merge |
| 92-100 | `check_reguv_status(sapfpaym_schedule)` + STOP | Gate REGUV.STATUS |
| 103-132 | `FI_CHECK_PAYMENT_DATA` + `FI_UPDATE_PAYMENT_DATA` | Pre-service refresh (genera UPDATE) |
| 136-155 | `FI_PAYGROUP_F4` popup | Reemplazado por `PM_GRPNO` obligatorio |
| 161-184 | `ENQUEUE_EFDFPAYG` + STOP | Lock |
| **205-232** | **`anz_erz LE anz_erl` + STOP** | **★ EL CHECK CRÍTICO QUE BLOQUEA RE-EJECUCIÓN** |
| 378 | `COMMIT WORK` | Diferido — ROLLBACK al final |

1 bloque comentado en `ZFPAYM_GET`:
- 11-40: `FI_REF_DOCUMENT_CHECK` + `REJECT`

1 inserción en `ZFPAYM_GET`:
- antes de línea 71: `BREAK-POINT ID 'YDMEE_REPLAY'.`

1 línea añadida en `ZFPAYM_END`:
- `ROLLBACK WORK.` al final → descarta UPDATE de DFPAYG.ANZ_ERL, REGUV.STATUS, REGUH.XEB1, etc.

## Archivos del paquete

| Archivo | Origen | Modificado |
|---|---|---|
| `ZSAPFPAYM_REPLAY.abap` | nuevo (driver) | nuevo |
| `ZFPAYM_TOP.abap` | = `FPAYM_TOP` | no |
| `ZFPAYM_INI.abap` | = `FPAYM_INI` | no |
| `ZFPAYM_SEL.abap` | = `FPAYM_SEL` | no |
| `ZFPAYM_STA.abap` | = `FPAYM_STA` | **sí** (8 bloques) |
| `ZFPAYM_GET.abap` | = `FPAYM_GET` | **sí** (1 bloque + 1 inserción) |
| `ZFPAYM_END.abap` | = `FPAYM_END` | **sí** (ROLLBACK WORK) |
| `ZFPAYM_LNS.abap` | = `FPAYM_LNS` | no |
| `ZFPAYM_SUB.abap` | = `FPAYM_SUB` | no |

## Deploy en D01 (SE38 / SE80)

### Opción A — manual paste

1. SE38 → crear `ZSAPFPAYM_REPLAY` (REPORT, paquete YPMW_DMEE_REPLAY)
2. SE38 → crear los 8 includes `ZFPAYM_*` (Type I)
3. Pegar contenido de cada `.abap`
4. Activar todos (Ctrl-F3 cada uno)

### Opción B — RFC `RFC_ABAP_INSTALL_AND_RUN` con `INSERT REPORT`

(El script `deploy_zsapfpaym_replay.py` se entrega aparte si la opción A es lenta.)

## Ejecución

### Selection screen (variant `ZREPLAY_10003B`)

```
PM_LAUFD  = 20260507
PM_LAUFI  = 10003B
PM_XVORL  = ' '
PM_GRPNO  = 100
PAR_FORM  = /SEPA_CT_UNES
PAR_XPY3  = 'X'                  (DMEE output)
PAR_XFIL  = 'X'                  (filesystem mode)
PAR_FILE  = C:\tmp\dmee_10003B_sepa.xml
PAR_BOTH  = ' '                  (no TemSe parallel)
PAR_XLST  = 'X'                  (accompanying list visible)
PAR_XERR  = 'X'                  (error log to spool)
```

### Debug ladder

| Nivel | Cómo | Cuándo |
|---|---|---|
| L1 — sin debug | F8 directo | Primer test "smoke": ¿genera XML? ¿coincide con archivo F110 original? |
| L2 — BREAK-POINT estructuras | SAAB → activar `YDMEE_REPLAY` → F8 | Inspeccionar `fpayh` / `gt_fpayp` / `par_form` ANTES del motor DMEE |
| L3 — BP en exit BAdI | SE24 USER-BP en `YCL_IDFI_CGI_DMEE_FALLBACK_CM001->GET_CREDIT` | Ver mapeo `i_node_path → c_value` por nodo del árbol |
| L4 — BP en motor SAP std | SE24 USER-BP en `CL_DMEE_CONVERSION->INTERPRET_NODE` | Solo si necesitas entender la traversal interna |

## Verificación post-ejecución

Después de F8:

```sql
-- Esto NO debe haber cambiado (ROLLBACK efectivo):
SELECT ANZ_ERL FROM DFPAYG WHERE LAUFD='20260507' AND LAUFI='10003B';
-- Antes y después del replay → debe ser el mismo número.

-- Esto SÍ debe existir (file I/O no transaccional):
DIR C:\tmp\dmee_10003B_sepa.xml
-- Tamaño ~1-3 KB para un solo pago SEPA EUR.
```

## V01 — CITI tree country-branch tests (added 2026-06-15)

**Target extended to V01** (system `V01`, client **350 "Validation"**, host `hq-sap-v01`,
sysnr 00). V01 holds all 4 UNESCO PAYM trees at **V000 only** (no V001). Replay here is safe
(validation system + `ROLLBACK WORK`). The replay needs `PM_GRPNO` — get it from `DFPAYG`.

**Branch driver — VERIFIED 2026-06-15:** the CITI tree `/CITI/XML/UNESCO/DC_V3_01` selects its
structured-address branch on `FPAYHX-UBISO` = **`REGUH-UBNKS`** (ultimate-beneficiary BANK
country), **NOT** the address country `ZLAND`. Conditions in the tree:
- `UBISO = US | CA | PR` → emit structured **`PstlAdr`** (StrtNm/BldgNb/PstCd/TwnNm/CtrySubDvsn/Ctry)
- `UBISO = SE` → emit **`PstCd`**
- `UBISO <> US AND <> CA AND <> PR` → **fallback** (unstructured `AdrLine`)

**2024 reality (V01):** Citi payments used only 3 bank countries — **US 8,759 · BR 8,472 · CA 1,303**.
`UBISO='SE'`→`PstCd` branch is **dead** (0 SE-bank Citi payments 2023-2026).

### 3 verified test runs (all FORMI `/CITI/XML/UNESCO/DC_V3_01`, GRPNO 100)

> **CORRECTION 2026-06-15:** an earlier pick (20240531/00001B/102, 20240124/00002B/103,
> 20240326/00008B/100) was **WRONG** — derived from `DFPAYG` (which in V01 carries stale/orphan
> groups not backed by a real medium). In V01 the run-management table **`REGUV` is empty** (refreshed
> validation system) so F110 shows "No parameters entered", and the **authoritative real-medium inventory
> is `REGUT`** (= what FDTA shows). Always pick re-run scenarios from `REGUT` (non-proposal `XVORL=''`) and
> confirm consistency across REGUT + DFPAYG + REGUH before asserting a run is re-playable.

| # | Branch | PM_LAUFD | PM_LAUFI | PM_GRPNO | Pay/HBank | n (REGUH) | UBNKS | Verified in |
|---|---|---|---|---|---|---|---|---|
| 1 | **PstlAdr (US)** | 20240424 | 00012B | 100 | UNES/CIT04 USD | 37 | 100% US | FDTA + REGUT + DFPAYG + REGUH |
| 1b | **PstlAdr (CA)** | 20240124 | 00020B | 100 | UNES/CIT21 CAD | 38 | 100% CA | REGUT + DFPAYG + REGUH |
| 2 | **Fallback (BR)** | 20240131 | 00010B | 100 | UBO/CIT01 BRL | 37 | 100% BR | REGUT + DFPAYG + REGUH |
| 3 | **PstCd (SE)** | — no historical data — synthesize SE-bank test vendor, or treat as dead config | | | | | | |

NB: standard `SAPFPAYM`/F110 read `REGUV` (empty here) → won't load these runs. The **replay** bypasses the
`REGUV` gate (reads `DFPAYG`+`REGUH`/`REGUP`) → this is precisely why the replay is needed in V01, not standard SAPFPAYM.

### D01 — CITI runs verified LIVE for replay (added 2026-06-17)

Para testear la **creación en D01** (no V01). Verificado vía RFC: `DFPAYG` (LAUFD/LAUFI/GRPNO/FORMI/ZBUKR/HBKID) +
`REGUH` (UBNKS). D01 tiene 48 grupos `DC_V3_01`; los relevantes por clearing (`HBKID`: CIT04=US, CIT21=CA, **CIT01=BR Worldlink**):

| # | Branch | PM_LAUFD | PM_LAUFI | PM_GRPNO | Pay/HBank | n (REGUH) | UBNKS | Demuestra |
|---|---|---|---|---|---|---|---|---|
| **BR-1** | **Fallback (BR/UBO)** | **20210924** | **UBO** | **100** | UBO/CIT01 BRL | 4 | 100% BR | **D-2** (Dbtr sin `PstCd`/`TwnNm`) + **D-1** (2º `PstlAdr`) |
| BR-2 | Fallback (BR) | 20210416 | 00001B | 100 | UBO/CIT01 BRL | 1 | 100% BR | idem (1 pago) |
| US-1 | PstlAdr (US) | 20240221 | 00001B | 100 | UNES/CIT04 USD | 2 | US | Dbtr completo (control, nodo #4) |
| **ALPAY-2023** | PstlAdr (US) + **alt-payee** | **20231215** | **USDI** | **100** | UNES/CIT04 USD | 8 (4 CIT04 US + SOG01/blank) | US (CITI lines) | **Fuente del XML `ALPAY` provisto.** Vendor 200027 (BG $25k) + 200319 (Delegation Serbie $20k, **`EMPFG=>0000200960>Z`** alt-payee, ultimate=Commission RS). Dbtr completo (US) → NO muestra D-2; las líneas FR clearean por `SOG01` (otra HB, no entran al CITI). El `EMPFG` produce el `<UltmtCdtr>` Serbia |

> **Solo 1 run CITI de 2023 en D01** (`20231215/USDI`) — y es US-cleared (no D-2). No hay run BR de 2023; para D-2 usar BR-1 (2021).

> El BR run **20210924/UBO/100** es el escenario clave: `ZBUKR=UBO` → `Dbtr = T001[UBO]→ADRC` = dirección de Brasil,
> `UBISO=BR` → dispara nodos #2 (`N_1905437260`, estruct con `=SE`→sin PstCd/TwnNm) **y** #1 (`N_1531351640`, legacy →
> 2º PstlAdr). El XML generado debe mostrar el `<Dbtr><PstlAdr>` **sin `<PstCd>` ni `<TwnNm>`**, y posiblemente **dos**
> bloques `<PstlAdr>`. Esto cierra la cadena tree→output real del D-2/D-1 (los XML US-cleared previos no lo muestran).
> Variante: `PM_LAUFD=20210924 · PM_LAUFI=UBO · PM_GRPNO=100 · FORMI=/CITI/XML/UNESCO/DC_V3_01 · PAR_FILE=C:\tmp\dmee_UBO_br_citi.xml · PAR_XLST='X' · PAR_XERR='X'`.

**PR + SE branches are DEAD config (verified 2026-06-15):** `REGUH.UBNKS = 'PR'` and `= 'SE'` = **0 across all
history (2006-2025)**. PR uses US banking (PR banks coded `UBNKS=US`); Swedish-ADDRESS beneficiaries exist
(`ZLAND=SE` = 8,263; 146 via Citi) but are paid through FR/US banks → `UBNKS` is never SE. So the conditions
`UBISO='PR'` and `UBISO='SE'` **never fire in production**. They can only be tested with a synthetic vendor
(`LFBK-BANKS='SE'`/`'PR'`). Net: only **2 of the 3** address branches are reachable from real data (PstlAdr via
US/CA, fallback via everything else); PstCd(SE) and the PR arm are theoretical.

### Scenario ↔ DMEE_TREE_COND filter mapping (all on `FPAYHX-UBISO` = `REGUH-UBNKS`)

**CANONICAL mapping (user-confirmed 2026-06-15):**

| Escenario | Filtro DMEE (condición sobre `UBISO` = `UBNKS`) | Resultado |
|---|---|---|
| **1 / 1b (US / CA)** | `PstlAdr` → `= US OR CA OR PR` | `<PstlAdr>` estructurado, **solo** |
| **2 (BR)** | sin-nombre `AdrLine` → `<> US AND <> CA AND <> PR` | `<AdrLine>` fallback |
| **3 (SE)** | `AdrLine` (`<> US AND <> CA AND <> PR`) **AND** `PstCd` (`= SE`) | `<PstCd>` + `<AdrLine>` (híbrido) |

Logic notes: US/CA/PR are **excluded** from the fallback → `PstlAdr` only, never `AdrLine`. **SE is a
hybrid** — it satisfies BOTH the fallback (`SE <> US/CA/PR` = TRUE, emits `AdrLine`) AND `PstCd` (`=SE`),
so an SE payment emits `AdrLine` + `PstCd` together. `PstCd` is an add-on over fallback for Sweden, not a
clean third branch.

### Explicación simple — el *compound* que genera la dirección Dbtr

Cada nodo de dirección del árbol CITI tiene una **condición compuesta** (*compound*): varias comparaciones
simples sobre `FPAYHX-UBISO` (el país del **banco del beneficiario**) unidas con **AND** u **OR**. Esa
condición decide **si el nodo se escribe** en el XML → así se elige **cómo sale la dirección del Dbtr** (UNESCO,
el pagador): estructurada, texto libre, o con código postal.

| Compound | Operador | Se cumple cuando… | Dirección Dbtr resultante |
|---|---|---|---|
| `UBISO = 'US' OR = 'CA' OR = 'PR'` | **OR** (basta UNO) | el banco del benef. está en US/CA/PR | **`<PstlAdr>` estructurado** (StrtNm · PstCd · TwnNm · CtrySubDvsn/estado · Ctry) |
| `UBISO <> 'US' AND <> 'CA' AND <> 'PR'` | **AND** (TODAS) | el banco no está en ninguno de los tres | **`<AdrLine>` texto libre** (fallback) |
| `UBISO = 'SE'` | simple | el banco está en Suecia | **`<PstCd>`** (+ también `AdrLine`) |

**En una frase**: el **OR** agrupa los países que van **estructurados**; el **AND** (que es la negación del OR)
agrupa "**todos los demás**" que van en **texto libre**; entre los dos parten el universo de países en dos
mitades que no se solapan. `SE` es un caso extra montado encima del fallback (cumple el AND **y** `=SE`).

> ⚠️ **El AND del fallback parece ilógico — "¿cómo va a ser un banco 3 países a la vez?".** No lo es: el AND
> **no** le pide a `UBISO` tener 3 valores. Un banco está en **un solo** país, así que `UBISO` tiene **un**
> valor, y el AND simplemente corre **tres chequeos contra ese único valor**. Para un beneficiario con banco en
> Brasil, `UBISO='BR'`: ¿BR distinto de US? sí; ¿de CA? sí; ¿de PR? sí → las tres ciertas a la vez (un solo
> valor sí puede diferir de tres países distintos) → se cumple → sale `<AdrLine>`. Tiene que ser **AND** porque
> la regla es "**ninguno de los tres**": para ser ninguno hay que diferir del primero **y** del segundo **y** del
> tercero; si una sola falla (el banco **sí** es US), toda la condición cae — que es lo que queremos, porque
> US/CA/PR van por la rama estructurada, no por el fallback. La lectura "imposible" sólo aplica si el operador
> fuera `=` (`=US AND =CA AND =PR`: un valor no puede ser 3 países) — pero el árbol usa `<>`, no `=`. Cambiar ese
> operador convierte la condición de "imposible" en **la rama que MÁS se dispara** (todo pago a banco fuera de
> US/CA/PR — p.ej. los ~8,500 pagos brasileños de 2024). Formalmente es De Morgan:
> `NOT(US OR CA OR PR) ≡ (NOT US) AND (NOT CA) AND (NOT PR)`.

Por qué el disparador es el país del **banco** (no el de la dirección): la forma de la dirección la exige el
**sistema de clearing** del destino — US/Canadá obligan dirección estructurada con estado+ZIP; el resto acepta
texto libre. Por eso un beneficiario en Etiopía pagado por banco US toma la rama **estructurada** (US), aunque
su dirección no tenga estado.

Replay params per scenario (same as SEPA example, only LAUFD/LAUFI/GRPNO/FORM change):
`PM_XVORL=' '` · `PAR_FORM=/CITI/XML/UNESCO/DC_V3_01` · `PAR_XPY3='X'` · `PAR_XFIL='X'` ·
`PAR_FILE=C:\tmp\dmee_<LAUFI>_citi.xml` · `PAR_XLST='X'` · `PAR_XERR='X'`.

Probe scripts: `Zagentexecution/mcp-backend-server-python/probe_v01_citi_groups.py`,
`probe_v01_ubnks.py`, `probe_confirm.py`.

> **Dónde vive este bloque en el companion**: la explicación de arriba (tabla de la condición compuesta sobre
> `UBISO` + nota De Morgan + ramas muertas-por-datos PR/SE) está también renderizada en
> `companions/BCM_StructuredAddressChange.html`, dentro de la sección **XML Before/After** de la pestaña
> **Phase 0** (fragmento `companions/bcm_structured_address_src/tabs/25_phase0.html`). El companion ya **NO**
> se regenera con el builder viejo de 16 pestañas (regresaba a ~278 KB). Se ensambla, byte-a-byte, desde los
> fragmentos verbatim en `companions/bcm_structured_address_src/` vía
> `build_bcm_structured_address_companion.py` (v2). Para editar ese bloque, edita el fragmento `25_phase0.html`
> y reconstruye. Detalle: `companions/bcm_structured_address_src/README.md`.

## Referencias

- Origen extracción: `Zagentexecution/mcp-backend-server-python/extract_sapfpaym_full_p01.py`
- Builder de los 3 modificados: `Zagentexecution/mcp-backend-server-python/build_zsapfpaym_replay.py`
- Companion (pipeline reconciliado): `Zagentexecution/mcp-backend-server-python/build_bcm_structured_address_companion.py` (v2, ensambla desde `companions/bcm_structured_address_src/`)
- Estructuras DDIC consumidas: `extracted_code/FI/SAPFPAYM/structures/{FPAYH,FPAYHX,FPAYP,REGUH,REGUP}.json`
- BAdI exit canónico: `extracted_code/FI/DMEE_p01_canonical/YCL_IDFI_CGI_DMEE_FALLBACK====CM001.abap`
- Brain rule: `feedback_search_dfpayg_for_sapfpaym_runs` (sesión #072)
- Brain rule: `feedback_p01_readonly_absolute` (sesión #052) — replay solo en D01
