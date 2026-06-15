# Identificar el/los RUN de pago detrás de un MEDIO (DME/DMEE)

**Propósito**: dado un medio de pago creado (archivo DMEE/DME que ves en **FDTA**), identificar el/los
**run de pago** (LAUFD/LAUFI/GRPNO) que lo produjeron, y elegir runs **re-ejecutables** de verdad.
Origen: sesión 2026-06-15 (test de `/CITI/XML/UNESCO/DC_V3_01` en V01 con `ZSAPFPAYM_REPLAY`).

## La verdad está en REGUT, no en DFPAYG

| Tabla | Qué es | Confiable para "¿existe el medio?" |
|---|---|---|
| **`REGUT`** | **Administración del medio (TemSe) — esto es lo que muestra FDTA.** 1 fila por archivo creado. | ✅ **AUTORITATIVA** |
| `DFPAYG` | Grupos de pago formados durante F110 (intermedio). | ⚠️ Puede tener grupos **huérfanos/stale** sin medio real |
| `REGUH` / `REGUP` | Cabeceras / posiciones de pago (los pagos en sí). | ✅ para los pagos, pero puede traer runs sin medio |
| `REGUV` | Cabecera del run (status, contadores). | ❌ **puede estar VACÍA** en sistemas de validación refrescados |

**Regla de oro**: para saber qué runs produjeron un medio CITI/SEPA/CGI real → **leer `REGUT`**
(`DTFOR` = formato = DMEE `TREE_ID`/`FORMI`). NUNCA derivar runs sólo de `DFPAYG`. Confirmar consistencia
**REGUT ⟷ DFPAYG (erz=erl) ⟷ REGUH** antes de afirmar que un run es re-ejecutable.

> **Por qué importa (caso real)**: en V01, `DFPAYG` devolvió `20240531/00001B` como grupo CITI; parecía real
> (REGUH tenía 182 pagos) pero **no había medio en FDTA/REGUT** y `REGUV` estaba vacía → F110 decía "No
> parameters entered". El run correcto se obtuvo de `REGUT`. DFPAYG mintió; REGUT no.

## Cadena de identificación

```
[REGUT]  un medio creado  ──(LAUFD, LAUFI, GRPNO, DTFOR=formato)──►  el RUN + el formato/árbol DMEE
   │
   ├─► [DFPAYG]  WHERE LAUFD+LAUFI  → grupos (GRPNO, FORMI, ANZ_ERZ=ANZ_ERL ⇒ medio completo)
   │
   └─► [REGUH]   WHERE LAUFD+LAUFI  → los pagos (LIFNR, ZBUKR, HBKID, RZAWE, WAERS, RBETR,
                                       UBNKS=país banco benef., ZLAND=país dirección, ZNME1/ZSTRA/…)
                  [REGUP]  WHERE LAUFD+LAUFI+LIFNR → posiciones (facturas) del pago
```

## Campos clave de REGUT (estructura verificada V01, 7.50)

`MANDT, ZBUKR, BANKS, LAUFD, LAUFI, XVORL, DTKEY, LFDNR, WAERS, RBETR, RENUM, DTFOR, TSNAM, TSDAT, TSTIM,
TSUSR, DWNAM, DWDAT, DWTIM, DWUSR, KADAT, KATIM, KAUSR, REPORT, FSNAM, USREX, EDINUM, GRPNO, DTTYP, GUID,
SAPRL, CODEPAGE, STATUS`

| Campo | Significado | Uso |
|---|---|---|
| `LAUFD` + `LAUFI` | Identificación del run de pago | clave del run (= columnas "Run On"/"Identification" en FDTA) |
| `GRPNO` | Nº de grupo de pago | input del medio (en UNESCO suele ser `100`) |
| `DTFOR` | **Formato** = DMEE `TREE_ID`/`FORMI` | `/CITI/XML/UNESCO/DC_V3_01`, `/SEPA_CT_UNES`, … |
| `ZBUKR` | Sociedad pagadora | UNES/UBO/UIS/… |
| `BANKS` | País del banco | — |
| `WAERS` / `RBETR` | Moneda / importe del medio | columnas "Currency"/"Amount" en FDTA |
| `XVORL` | Flag de propuesta (`X`=propuesta, `''`=real) | **filtrar `XVORL=''`** para medios reales |
| `TSNAM` | Nombre del objeto TemSe (el archivo) | el medio físico |
| `TSDAT`/`TSTIM`/`TSUSR` | Creado fecha/hora/usuario | "Date created"/"Entered by" en FDTA |
| `DWDAT`/`DWUSR` | Descargado fecha/usuario | si ya se bajó externamente |
| `DTTYP` / `STATUS` | Tipo / estado del medio | — |

## Cómo identificar runs por RFC (RFC_READ_TABLE)

```python
# Medios reales de un formato (= lo que ves en FDTA):
REGUT  WHERE DTFOR = '/CITI/XML/UNESCO/DC_V3_01' AND LAUFD LIKE '2024%'
       FIELDS LAUFD,LAUFI,XVORL,ZBUKR,GRPNO,WAERS,RBETR,TSUSR   # filtrar XVORL=='' (no propuesta)
# Pagos de un run (rama de dirección = UBNKS):
REGUH  WHERE LAUFD = '<d>' AND LAUFI = '<i>'  FIELDS LIFNR,UBNKS,ZLAND,WAERS,RBETR,HBKID,ZNME1
# Grupo del run (consistencia):
DFPAYG WHERE LAUFD = '<d>' AND LAUFI = '<i>'  FIELDS GRPNO,FORMI,ZBUKR,HBKID,ANZ_ERZ,ANZ_ERL
```

### Gotchas RFC verificados (V01)
- **OPTIONS línea máx 72 chars**: una WHERE con el string largo del formato `/CITI/...` desborda →
  `OPTION_NOT_VALID / DB_Error`. Solución: **sacar el formato del WHERE** y filtrar `DTFOR` en Python,
  o partir la WHERE en varias líneas de OPTIONS ≤72.
- **Espacios obligatorios alrededor de `=`**: `UBNKS = 'SE'` funciona; `UBNKS='SE'` falla silenciosamente (0 filas).
- `DMEE_TREE_HEAD`/`DMEE_TREE_NODE`: el **WHERE-pushdown no es fiable** (falsos `TABLE_WITHOUT_DATA`) →
  leer sin WHERE y filtrar en Python. Tabla **cliente-independiente** (sin `MANDT`); no tiene `EX_STATUS`
  en 7.50.

## Re-ejecutar el medio
- Estándar `SAPFPAYM`/F110 leen `REGUV` (vacía en V01) → **no cargan** el run.
- **`ZSAPFPAYM_REPLAY`** salta el gate de `REGUV` (lee `DFPAYG`+`REGUH`/`REGUP`) → es el camino en V01.
  Inputs: `PM_LAUFD`, `PM_LAUFI`, `PM_GRPNO` (de REGUT), `PAR_FORM` (=`DTFOR`). Ver
  `extracted_code/FI/SAPFPAYM/ZSAPFPAYM_REPLAY/README_REPLAY.md`.

## Anclas
- README del replay: `extracted_code/FI/SAPFPAYM/ZSAPFPAYM_REPLAY/README_REPLAY.md`
- Memoria: `reference_zsapfpaym_replay_and_citi_ubiso`
- Probes: `Zagentexecution/mcp-backend-server-python/probe_v01_regut*.py`, `probe_v01_verify_real.py`
