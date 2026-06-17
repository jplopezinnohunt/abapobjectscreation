# DMEE payment formats — modelo de fondo compartido, exits, y matriz 4-partidos × 3-modelos

**Verificado 2026-06-16 (D01 V000 + código `extracted_code/FI/DMEE_full_inventory/`).** Anclas:
[[citi_dbtr_pstladr_format_analysis]] · [[reference_zsapfpaym_replay_and_citi_ubiso]].

## 1. Principio arquitectónico — los formatos son PROYECCIONES de un modelo de fondo

Los árboles DMEE (CITI/CGI/SEPA) **no tienen datos propios**: son **proyecciones XML** de un único **modelo de datos
runtime** del payment medium, poblado por la lógica interna (Event 05 + exits) ANTES de la traversal del árbol:

| Estructura | Qué tiene |
|---|---|
| `FPAYH` | cabecera por lote: ZBUKR, HBKID, LAUFI, ZADNR (nº dirección), DORIGIN, GPA1T… |
| `FPAYHX` | extendida: **buffers `REF01..REF15`** (dirección byte-layout), NATION, UBISO… |
| `FPAYP` | por línea: `BNAME`/`BLAND`/`BORT1`/`BSTRAS` (partido), `REF01`, XREF3… |
| `ADRC`/`LFA1` / `BSEC` | maestro de dirección del vendor / one-time vendor |

→ La diferencia entre formatos es **PRESENTACIÓN** (qué campo del modelo → qué tag XML), **NO datos**. Cualquier
formato podría emitir cualquier campo del modelo si su árbol tiene el nodo. Por eso el **V001 es config-only**.

## 2. NO es 1 modelo — son **2 modelos de fondo** (`PARAM_STRUC`)

| Árbol | `PARAM_STRUC` | Modelo |
|---|---|---|
| `/CGI_XML_CT_UNESCO` (+`_1`) | `FPM_CGI` | **modelo CGI** |
| `/CITI/XML/UNESCO/DC_V3_01` | (blank, pero usa infra CGI) | **modelo CGI** |
| `/SEPA_CT_UNES` | `FPM_SEPA` | **modelo SEPA (distinto)** |

**CITI + CGI comparten el modelo CGI; SEPA es otro modelo.**

## 3. Event 05 — la clave (SEPA NO lo llama)

| Formato | Event 05 | Efecto |
|---|---|---|
| CGI | `FI_PAYMEDIUM_DMEE_CGI_05` | llena buffer `FPAYHX_FREF` (REF01: street@0·building@60·postcode@80·region@90·house@100; city@REF06) |
| CITI | `/CITIPMW/V3_PAYMEDIUM_DMEE_05` | llena el mismo buffer `FPAYHX_FREF` |
| **SEPA** | **NINGUNO** | sin buffer → por eso UNESCO creó **17 exits custom `Y_FI_DMEE`** que leen `ADRC` directo |

(Event 05 verificado en código CITI; SEPA=NONE por conocimiento previo `LIVE_CONFIG_MAP` + consistente con que SEPA
usa `Y_FI_DMEE` y no el buffer.)

## 4. Matriz: 4 partidos × 3 modelos — qué función llaman para la dirección

| Partido | **SEPA** (`FPM_SEPA`) | **CITI** (modelo CGI) | **CGI** (`FPM_CGI`) |
|---|---|---|---|
| **Dbtr** | ✅ estruct — **`Y_FI_DMEE`** custom | ✅ estruct — `FI_CGI` BAdI (buffer REF) | ✅ estruct — `FI_CGI` BAdI |
| **UltmtDbtr** | ❌ sin dirección | ❌ sin dirección (solo `Nm`) | ✅ estruct — `FI_CGI` BAdI |
| **Cdtr** | ✅ estruct — **`Y_FI_DMEE`** custom | ✅ estruct — **`CITIPMW`** → ADRC | ✅ estruct — `FI_CGI` BAdI |
| **UltmtCdtr** | ❌ sin dirección | ✅ estruct — `FI_CGI` BAdI | ✅ estruct — `FI_CGI` BAdI |

**Familias de exit (verificado, count de `MP_EXIT_FUNC`):** CGI/CGI_1 = 100% `FI_CGI` BAdI (395/396) · CITI =
`CITIPMW`(36)+`FI_CGI`(22) · SEPA = `Y_FI_DMEE` custom(17)+SEPA-std.

## 5. Gaps de cobertura (dirección estructurada por partido)

| Modelo | Cobertura | Falta |
|---|---|---|
| **CGI** | **4/4** ✅ gold standard (todos por `FI_CGI` BAdI, uniforme) | — |
| **CITI** | 3/4 | **UltmtDbtr** sin dirección |
| **SEPA** | 2/4 | **UltmtDbtr + UltmtCdtr** sin dirección |

## 6. Implicaciones

1. **Llevar CITI/SEPA a paridad con CGI = config + (SEPA) custom**: en CITI el buffer ya está lleno (Event 05) →
   agregar nodos. En SEPA no hay buffer → ya se hizo el custom `Y_FI_DMEE`.
2. **El V001** es la materialización de esto: CITI/CGI config-only; SEPA con `Y_FI_DMEE`.
3. **La "función que llaman" = el modelo**: `FI_CGI` BAdI (CGI/CITI nativo) vs `Y_FI_DMEE` custom (SEPA bridge).
   Y el **Event 05** es el habilitador del buffer — sin él (SEPA) hace falta el custom.
4. Inconsistencias entre formatos (UltmtDbtr ausente en CITI/SEPA) = **decisiones de proyección**, no límites técnicos.

## Probes
`probe_models.py` (PARAM_STRUC + familias de exit) · `probe_models_matrix.py` (matriz) ·
`probe_ultmdbtr_compare.py` (UltmtDbtr CITI vs CGI) — en `Zagentexecution/mcp-backend-server-python/`.
