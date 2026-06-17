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

## 7. CITI vs CGI — source of each address tag + ACTION (deep, all parties, D01 V000)

### 7.0 Estructura de NODOS — CITI NO es 1 nodo por partido (MEDIDO D01 V000, `probe_pstladr_nodes_full.py`)

Cada partido tiene **N nodos `PstlAdr` condicionados por `UBISO`** — la dirección que sale depende de QUÉ nodo
dispara. CITI = 12 nodos PstlAdr (Dbtr **4** · UltmtDbtr **0** · Cdtr 2 · UltmtCdtr 2); CGI = 7 (1 por partido, uniforme).

**CITI Dbtr — 4 nodos (clave):**
| Nodo | Cond `UBISO` | Dispara | Emite | Estado / Acción |
|---|---|---|---|---|
| #1 `N_1531351640` | cond `<>US/CA/PR AND <>''` PERO **nodo DESACTIVADO** | nunca (off) | (no renderiza) | legacy — **ya apagado** (probado: XML BR real = 1 PstlAdr). Sin acción |
| #2 `N_1905437260` | `<>US AND <>CA AND <>PR` | **BR / resto** | `StrtNm·BldgNb·CtrySubDvsn·Ctry` (BAdI); PstCd/TwnNm con `=SE`→**suprimidos** | estructurado, **D-2**. 🔴 quitar `=SE` |
| #3 `N_4078824850` | `=USA OR CAN OR PRO` (3-letras) | **nunca** | `AdrLine×3` | **muerto**. higiene opcional |
| #4 `N_5197213060` | `=US OR CA OR PR` | **US/CA/PR** | `StrtNm·BldgNb·PstCd·TwnNm·CtrySubDvsn·Ctry` (BAdI) | ✅ **completo** |

→ **US/CA/PR** → #4 → completo ✅. **BR** → solo **#2** (#1 desactivado) → **1 `PstlAdr` sin PstCd/TwnNm** = **D-2**
(PROBADO en XML BR real, §10.1). **NO hay duplicado** (D-1 retractado: el #1 no renderiza). El "D-1 resuelto" previo
era correcto; el flag de desactivación del nodo no vive en `DMEE_TREE_COND`, por eso leer solo la condición engañó.
Versión activa = **V000** (confirmado usuario).

**CITI Cdtr — 2 nodos** (`PmtInf/CdtTrfTxInf/Cdtr/PstlAdr`): #1 `N_1496761000` (`=US OR CA OR PR`, estruct puro) · #2
`N_2368849090` (`<>RU AND <>JP AND <>US AND <>CA AND <>PR`, estruct + `AdrLine×3`←ZNME2/3/4 name-overflow). Ambos ✅.
**CITI UltmtDbtr — Nm-only POR DISEÑO** (`PmtInf/UltmtDbtr` solo `Nm`, sin `PstlAdr` a ningún nivel; **NO es gap** —
CGI tiene uno estructurado a nivel transacción `N_8824498030` que **no se replica en CITI**). **CITI UltmtCdtr — 2 nodos**
(`PmtInf/CdtTrfTxInf/UltmtCdtr/PstlAdr`): #1 `N_3468319710` (BAdI, gated `=SPACE`) + #2 `N_4600960730` (`UBISO<>''`,
directos `FPAYH-Z*`: PstCd←ZPSTL, TwnNm←ZORT1, CtrySubDvsn←ZREGI, Ctry←ZLAND).
**Otras partes con PstlAdr (bancos, aparte):** DbtrAgt · CdtrAgt · IntrmyAgt1 (CITI+CGI) · IntrmyAgt2 (CITI) — todas
`FinInstnId/PstlAdr` = dirección del **banco** (T012K/BNKA), no de las partes cliente analizadas aquí.

**CGI — 1 nodo estructurado por partido (uniforme), gated por flag overflow:** Dbtr `N_1160789980`(`-PstlAdrMore=SPACE`)
· UltmtDbtr `N_8824498030`(`=SPACE`, directos FPAYP) · Cdtr `N_8311560080`(`<>X`) · UltmtCdtr `N_4634017880`(`=SPACE`).
→ CGI es limpio (1 nodo/partido); CITI es el desordenado (4 Dbtr con solape, UltmtDbtr Nm-only por diseño, Cdtr 2, UltmtCdtr 2).

### 7.1 Fuente de cada tag (dentro del nodo que dispara)

Sources fully resolved: `BADI`→ qué lee de verdad el exit estándar `FI_CGI_DMEE_EXIT_W_BADI`; `CITIPMW V3_*`→
campo ADRC; campo directo→ struct field. **Byte-offsets del buffer `FPAYHX-REF01` = Event 05 (MEDIDO):**
street@0(60) · building@60(20) · postcode@80(10) · region@90(10) · house@100(10) · city@`REF06`+0(40).

| Party | Tag | CITI — source (resuelto) | CGI — source (resuelto) | **Acción** |
|---|---|---|---|---|
| **Dbtr** *(ente pagador, `T001[ZBUKR]→ADRC`; nodos #3 US/CA, #4 resto=BR)* | StrtNm | BAdI std → buffer `FPAYHX-REF01+0(60)` (street) | BAdI std → idem buffer street | ✅ ninguna (emite en #3 y #4) |
| | BldgNb | BAdI std → `FPAYHX-REF01+60(20)` (building) + house `+100(10)` | BAdI std → idem | ✅ ninguna |
| | **PstCd** | `FPAYHX-REF01+80(10)` (postcode) — **en #4 gated `UBISO='SE'`** ⇒ suprimido BR/UBO | BAdI std → buffer postcode (sin gate) | 🔴 **FIX D-2**: quitar `=SE` del `PstCd` en nodo #4 (`N_1905437260`) → BR/UBO emite |
| | **TwnNm** | `FPAYHX-ORT1Z` — **en #4 gated `UBISO='SE'`** ⇒ suprimido BR/UBO | BAdI std → buffer city (`REF06`) | 🔴 **FIX D-2**: quitar `=SE` del `TwnNm` en nodo #4 |
| | CtrySubDvsn | BAdI std → `FPAYHX-REF01+90(10)` (region) | BAdI std → idem | ✅ ninguna |
| | Ctry | `FPAYHX-LAND1` (directo) | BAdI std → LAND1 | ✅ ninguna |
| | AdrLine | `FPAYHX-AUST2` (directo) | — (CGI no lo tiene) | ✅ opcional |
| | *(nodo #1 legacy N_1531351640)* | dispara para BR junto a #2 ⇒ 2º `PstlAdr` (Ctry+AdrLine) = **duplicado D-1** | — | 🧹 **D-1**: desactivar #1 (BR→solo #2); borrar #1 + #3 muerto |
| **UltmtDbtr** *(parte última, on-behalf-of)* | **`PmtInf/UltmtDbtr` = solo `Nm`** | `Nm` ← `FPAYP-BNAME` (sin PstlAdr) | `Nm`+`Id` (sin PstlAdr en PmtInf) | ✅ **Nm-only POR DISEÑO** (ISO 20022 permite parte última solo por nombre) — **NO es gap, NO add** |
| | *(nivel transacción)* | CITI: sin `CdtTrfTxInf/UltmtDbtr/PstlAdr` | CGI: `N_8824498030` estruct (directos `FPAYP-REF01/BORT1/BLAND/BSTRAS`, gated `=SPACE`) | ✅ **NO copiar a CITI** (parte opcional, decisión de diseño confirmada por usuario) |
| **Cdtr** *(beneficiario, maestro vendor `ADRC` v.`nation`)* | StrtNm | exit `V3_CGI_CRED_STREET` → **`ADRC-STREET`** (one-time→`BSEC-STRAS`; fallback HR/F111/PR→`ZSTRA`; PO box→"PO BOX"+`ZPFAC`) | BAdI std → ADRC + **FALLBACK** (name-overflow: antepone nombre chars 35+) | ✅ ninguna (CITI más rico) |
| | BldgNb | `V3_GET_CDTR_BLDG` → **`ADRC-BUILDING`** | BAdI std | ✅ ninguna |
| | PstCd | `V3_POSTALCODE` (`ZPST2` PO box / `ZPSTL`) | BAdI std | ✅ ninguna |
| | TwnNm | `V3_*_CRED_CITY`/`_PO_CITY` → **`ADRC-CITY1`/`PO_BOX_CTY`** (one-time→`BSEC-ORT01`; fb→`ZORT1`) | BAdI std | ✅ ninguna |
| | CtrySubDvsn | `V3_CGI_CRED_REGION` → **`ADRC-REGION`** (payroll→`ZREGI`) | BAdI std | ✅ ninguna |
| | Ctry | `FPAYHX-ZLISO` (directo, país del beneficiario) | BAdI std | ✅ ninguna |
| | Nm | `V3_EXIT_CGI_CRED_NAME` → **`ADRC-NAME1`** | **FALLBACK**: `TR-CM-BT`→`FPAYP-SGTXT`; trunca 35, overflow→StrtNm | ✅ ninguna |
| | AdrLine ×3 | `FPAYH-ZNME2/3/4` (**overflow de NOMBRE**, no dirección; 4.7% BR) | — (CGI manda el overflow a StrtNm vía FALLBACK) | 🟢 **mejora opcional**: consolidar con la función combina-nombres (otro modelo) — *pendiente detalle* |
| **UltmtCdtr** *(opcional; cubierto ambos)* | StrtNm…Ctry | BAdI std (exit `FI_CGI`) | BAdI std (exit `FI_CGI`) | ✅ ninguna (presente en CITI y CGI) |
| | AdrLine | `FPAYH-ZSTRA`/`ZORT2` (directo) | BAdI std | ✅ ninguna |
| *(transversal)* | InstrForCdtrAgt / RmtInf (PPC) | clases país `FR/DE/IT`→`get_tag_value_from_custo` (`mt_ppc_cus` por país·D/C·pay_type·tag) | idem | ✅ no es dirección (purpose code) |

**Resumen de acciones (CORREGIDO 2026-06-17 — D-2 probado en XML real; D-1 retractado):**
1. 🔴 **FIX D-2 (ALTA — ÚNICA ACCIÓN REAL)** — Dbtr CITI `PstCd`+`TwnNm`: quitar `=SE` del nodo #2 estructurado
   `N_1905437260` (dejarlos incondicionales como el #4). Afecta **83,224 pagos (8.5%·53% del flujo CITI)**, campo
   **obligatorio** CBPR+. **PROBADO end-to-end** en el XML BR real (§10.1: Dbtr BR sale sin `PstCd`/`TwnNm`).
   **ZERO-RIESGO (usuario 2026-06-17): NO existe flujo `SE` (Suecia)** → el `=SE` es código muerto que nunca emite;
   quitarlo no regresa ningún caso real. Y como el Dbtr BR **ya emite** `StrtNm`/`BldgNb`/`CtrySubDvsn` de la misma
   fuente (`ADRC` de UBO Brasil), el código postal y la ciudad están casi seguro poblados → al quitar el `=SE` saldrían
   (Brasília + CEP), no tags vacíos. **Cambio limpio, sin pre-condición pendiente.**
2. ❌ **D-1 (duplicado) — RETRACTADO, no hay acción.** El XML BR real trae **1 solo `PstlAdr`**; el nodo legacy #1
   `N_1531351640` **está desactivado** (no renderiza). La nota previa "D-1 resuelto" era correcta. (`#3 N_4078824850`
   muerto = higiene opcional, sin impacto.)
3. 🟢 **Cdtr name-overflow (MEJORA)** — opcional: consolidar `ZNME2/3/4`→`AdrLine` con la función combina-nombres. 4.7% BR.
4. ❌ **UltmtDbtr — SIN acción.** `PmtInf/UltmtDbtr` es **Nm-only por diseño** en CITI **y** CGI (confirmado: 0 UltmtDbtr
   en los 3 XML reales, incl. el ALPAY). No es un gap.

**Versión activa: V000** (confirmado usuario 2026-06-17). V001/V002 son copias de trabajo.

*(SEPA aparte: sus UltmtDbtr/UltmtCdtr son Nm-only igual — mismo diseño. Lo relevante de SEPA es Dbtr/Cdtr vía custom
`Y_FI_DMEE`. Impacto de las "ausencias" de parte última = mínimo, ver §9.)*

## 8. BAdI internals — qué hace `FI_CGI_DMEE_EXIT_W_BADI` por partido (CGI/CITI)

**Verificado leyendo TODAS las clases de la implementación UNESCO** (`YCL_IDFI_CGI_DMEE_FALLBACK / _FR / _UTIL`,
métodos `*_CM00x`, `extracted_code/FI/DMEE/`). El "BADI" de la matriz §4/§7 **NO es un único bloque de código que
arma cada dirección**: es un wrapper SAP-estándar + 2 capas UNESCO muy acotadas. Detalle:

### 8.1 La capa SAP-estándar (la mayoría de los tags "BADI")
El exit estándar `FI_CGI_DMEE_EXIT_W_BADI` arma la dirección de **Dbtr, Cdtr y UltmtCdtr** leyendo el buffer
`FPAYHX_FREF` (poblado por **Event 05**, byte-layout street@0·building@60·postcode@80·region@90·house@100·city@REF06)
y/o `ADRC`. **UNESCO no override esto** — es SAP nativo. Por eso "BADI" en la matriz = *SAP-standard*, no custom.

### 8.2 Capa UNESCO #1 — `FALLBACK->get_credit` (CM001): override **SÓLO del Cdtr**
Único método con redefinición *hard-coded* de nodos. `CASE i_node_path` activo = **2 WHEN, ambos Cdtr** (Dbtr=0,
UltmtDbtr=0, UltmtCdtr=0 — grep verificado):
- `<…><Cdtr><Nm>` → si `FPAYP-ORIGIN='TR-CM-BT'` usa `FPAYP-SGTXT` (texto del ítem); **trunca a 35**; guarda el
  sobrante (`mv_cdtr_name+35`) en buffer de instancia.
- `<…><Cdtr><PstlAdr><StrtNm>` → **Pattern A (name-overflow)**: antepone los chars 35+ del nombre a la calle
  (`c_value = |{ mv_cdtr_name+35 } { c_value }|`); trunca a 70.

→ El **único** retoque UNESCO de dirección es el desbordamiento de nombre largo del beneficiario hacia la calle. El
resto del Cdtr (y todo Dbtr/UltmtCdtr) es SAP-estándar; en **CITI** el Cdtr lo reemplazan los exits `CITIPMW V3_*`
(leen `ADRC` directo, §7) — más ricos que el genérico.

### 8.3 Capa UNESCO #2 — country dispatch `FR/DE/IT/FALLBACK->get_value` → **PPC (no es dirección)**
`if_idfi_cgi_dmee_countries~get_value` (clase por país) es un **dispatcher genérico data-driven**, no código por nodo.
Llama `YCL_IDFI_CGI_DMEE_UTIL->get_tag_value_from_custo`, que busca en customizing `mt_ppc_cus` por clave
**(land1=`FPAYH-ZBNKS` país banco · deb_cre D/C · pay_type · tag_full=node_path)** y arma el valor con componentes
`SEPARATOR / FIXED_VAL` (literal), `PPC_VAR / PPC_DESCR` (parten `T015L-ZWCK1` por `LZBKZ` = Verwendungszweck),
`PAY_FIELD` (lectura dinámica `IS_<struc>-<field>`). `pay_type` ← `FPAYH-DORIGIN(2)`: **HR→P** (payroll) · **TR→R**
(treasury) · **else→O**. → Es el mecanismo de **purpose/remittance code por país**, aplicable a cualquier tag que
esté en la tabla, normalmente NO los de dirección. Por país sólo cambia `flt_val_country`; la lógica es la misma UTIL.

### 8.4 Resumen por partido (CGI/CITI) — quién arma la dirección
| Partido | UNESCO override hard-coded? | Mecanismo real |
|---|---|---|
| **Dbtr** | ❌ 0 nodos | SAP-std CGI exit (buffer `FPAYHX_FREF` ← Event 05 / ADRC) |
| **UltmtDbtr** | ❌ 0 (ni exit) | Campos directos `FPAYP-REF01/BORT1/BLAND/BSTRAS` (`MP_IF_TP=1`) — CGI sí, CITI NO los tiene |
| **Cdtr** | ✅ sólo `Nm`+`StrtNm` (name-overflow) | CGI: SAP-std + FALLBACK · CITI: exits `CITIPMW V3_*`→ADRC |
| **UltmtCdtr** | ❌ 0 nodos | SAP-std CGI exit |
| *(transversal)* | PPC por país (FR/DE/IT) | data-driven `mt_ppc_cus` — purpose code, no dirección |

**Implicación para "structured address to all":** el lever NO es "tocar el BAdI por partido" (apenas existe). Es
**config DMEE**: (1) CITI UltmtDbtr → copiar los nodos de campo-directo del CGI (`FPAYP-*`, ya poblados por Event 05);
(2) Dbtr/UltmtCdtr ya salen del estándar — si fallan, el problema está en el buffer (Event 05) o en agregar nodos al
árbol, no en código BAdI. El único código UNESCO de dirección a preservar es el name-overflow del Cdtr (Pattern A).

## 9. Impacto de las diferencias — NO son iguales (medido P01, REGUH, 2024-2026)

Las "diferencias" de §5 no pesan igual. Dos ejes deciden el impacto: **(a) tier regulatorio** — ¿el partido es
OBLIGATORIO (Dbtr/Cdtr, dirección mandatoria CBPR+) u OPCIONAL (UltmtDbtr/UltmtCdtr, solo on-behalf-of)? — y
**(b) volumen real**. Base: 983,561 pagos 2024-2026 (REGUH P01).

| # | Diferencia | Tipo | Partido | Volumen (MEDIDO) | Mandato | Impacto |
|---|---|---|---|---|---|---|
| **D-2** | CITI Dbtr: `=SE` suprime `PstCd`/`TwnNm` p/ clearing≠US/CA/PR | **DEFECTO en partido obligatorio** | Dbtr | **83,224 pagos (8.5% del total · 52.9% del flujo CITI)**; BR=79,674, creciendo | **MANDATORIO** (CBPR+ structured addr) → riesgo rechazo/retorno | **🔴 ALTO — PROBADO en XML BR real (§10.1)** |
| ~~D-1~~ | ~~Dbtr BR: 2º `PstlAdr`~~ → **RETRACTADO** | nodo #1 desactivado | Dbtr | — | XML BR real trae **1 solo `PstlAdr`** | ⚪ **N/A (no ocurre)** |
| ~~G-1~~ | ~~UltmtDbtr sin dirección~~ → **NO es diferencia** | **Nm-only POR DISEÑO** (ISO 20022) | UltmtDbtr | — | parte última identificable solo por nombre | ⚪ **N/A (no es gap)** |

**Veredicto:** la **única** diferencia con impacto — y ya **probada en output real** (§10.1) — es **D-2** (Dbtr CITI
BR/UBO): borra campos **obligatorios** (`PstCd`/`TwnNm`) en un partido **siempre presente**, en el **8.5% de TODOS los
pagos** (mitad del flujo CITI, creciendo). **D-1 (duplicado) NO ocurre** (XML BR real = 1 `PstlAdr`; nodo #1 desactivado).
**`UltmtDbtr` = Nm-only por diseño** (no es gap). → **Acción ÚNICA: fijar D-2.**

## 10. Validación EMPÍRICA — 2 XML reales generados (CITI, replay, 2026-06-17)

Usuario aportó 2 salidas reales del formato CITI (`pain.001.001.03`, vía ZSAPFPAYM_REPLAY; `CreDtTm` hoy, `ReqdExctnDt`
2022/2023). Ambas **US-cleared** (`DbtrAgt/BIC=CITIUS33`, ABA 021000089) → `UBISO=US`. Confirman el modelo corregido:

| Observación en el XML real | Confirma |
|---|---|
| **Dbtr UNESCO COMPLETO** (`StrtNm·BldgNb·PstCd=75007·TwnNm=PARIS·Ctry=FR`) en ambos | US-clearing → nodo **#4 `N_5197213060`** (`=US/CA/PR`) emite completo; **D-2 NO se dispara para US** |
| Dbtr `Ctry=FR` (Paris) pese a clearing US | Dbtr = dirección propia `ZBUKR→T001→ADRC`, **no** país de clearing |
| **`UltmtCdtr` Serbia estructurado FULL** (`Strt·BldgNb=24·PstCd=11000·TwnNm=BELGRADE·Ctry=RS`) (file ALPAY txn2) | CITI UltmtCdtr estructurado (2 nodos) funciona |
| **`UltmtDbtr` AUSENTE en ambos** (incl. el "ALPAY") | **UltmtDbtr Nm-only/no-emitido POR DISEÑO** (valida corrección 2026-06-17) |
| Cdtr (STEG/BG/Serbie) con dirección pero **sin `BldgNb`** | CITIPMW→`ADRC`; `BldgNb` vacío = `ADRC-BUILDING` vacío en esos vendors |
| `InstrForCdtrAgt=ROUT ID 10` (file2) | capa PPC (FR/DE/IT `get_tag_value_from_custo`) = routing, **no** dirección |

**"Alternative payer" — precisión:** el file `ALPAY` muestra un **alternative PAYEE** (txn2: `Cdtr`=Delegation Serbie
Paris recibe en SocGen; `UltmtCdtr`=Commission Serbia Belgrade = beneficiario último). **No hay `UltmtDbtr`** (alt payer)
en ninguno → el Dbtr es UNESCO siempre. El escenario alt-payee se renderiza vía `UltmtCdtr`, no via `UltmtDbtr`.

### 10.1 XML BR real — D-2 CONFIRMADO end-to-end + D-1 RETRACTADO (2026-06-17)

Usuario replayó la corrida BR **D01 20210924/UBO/100** (`ReqdExctnDt=2021-09-24`, `DbtrAgt/BIC=CITIBRBR`, `UBISO=BR`,
BRL). El `<Dbtr><PstlAdr>` real (UNESCO Brazilian Office):

| Tag Dbtr | US file (CITIUS33) | **BR file (CITIBRBR)** |
|---|---|---|
| StrtNm | ✓ Place de Fontenoy | ✓ SAS Quadra 05 Bloco H |
| BldgNb | ✓ 7 | ✓ Lote 6 |
| **PstCd** | ✓ 75007 | **❌ AUSENTE** |
| **TwnNm** | ✓ PARIS | **❌ AUSENTE** |
| CtrySubDvsn | — | ✓ DF |
| Ctry | ✓ FR | ✓ BR |

✅ **D-2 PROBADO tree→output:** el Dbtr BR emite `StrtNm·BldgNb·CtrySubDvsn·Ctry` **sin `PstCd` ni `TwnNm`** (nodo #2
`N_1905437260`, gate `=SE`). `TwnNm` es obligatorio CBPR+ → riesgo de rechazo. **Este es el único defecto real.**

❌ **D-1 (duplicado) RETRACTADO:** el Dbtr real trae **UN solo `<PstlAdr>`** (el del #2), NO dos. El nodo legacy #1
`N_1531351640` **no renderiza** (de dos nodos que solapan condición para BR, solo salió el #2 ⇒ **#1 está desactivado**).
La nota previa "D-1 resuelto" era **correcta**; mi re-análisis por-condición (s-actual) estaba **mal** — el flag de
desactivación no vive en `DMEE_TREE_COND`. **No hay duplicado en producción.**

✅ **Cdtr COMPLETO** (Iron Mountain do Brasil): `StrtNm·PstCd=70632-200·TwnNm=BRASILIA DF·CtrySubDvsn=DF·Ctry=BR` →
confirma que **solo el Dbtr** tiene el hueco; el Cdtr (CITIPMW→ADRC) está sano. → **Acción única: FIX D-2.**

(Archivos crudos no versionados: IBANs/tax-IDs reales; solo se persiste la estructura.)

## Probes
`probe_models.py` (PARAM_STRUC + familias de exit) · `probe_models_matrix.py` (matriz) ·
`probe_ultmdbtr_compare.py` (UltmtDbtr CITI vs CGI) — en `Zagentexecution/mcp-backend-server-python/`.
BAdI internals: clases `YCL_IDFI_CGI_DMEE_{FALLBACK,FR,UTIL}_CM00x.abap` en `extracted_code/FI/DMEE/`.
