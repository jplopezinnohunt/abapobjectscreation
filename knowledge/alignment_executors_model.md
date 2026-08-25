# Modelo de ejecutores de alineamiento P01 → D01 / V01

**Qué es esto.** El inventario canónico de lo que sabemos medir y alinear entre sistemas, con su
canal, su peldaño y su estado. Nace de s102 (2026-08-20/21), cuando se descubrió que las
capacidades existían dispersas en scripts y que un skill llegaba a **afirmar lo contrario** de lo
que el sistema permite.

**Regla de entrada:** un ejecutor solo pertenece a este modelo si (a) su canal está **medido**
—preguntado a `TFDIR`, no recordado—, (b) **verifica releyendo** y no por código de retorno, y
(c) está cableado a un agente o skill. Un script suelto no es una capacidad.

---

## 0. La escalera de canales — decide el peldaño ANTES de escribir

| Peldaño | Canal | Cuándo | Framework | Orden |
|---|---|---|---|---|
| **1** | API estándar del objeto (BAPI / FM RFC) | existe en `TFDIR WHERE FMODE='R'` | ✅ | según el objeto |
| **2** | BC-Set (`SCPRMP_UPDATE_BCSET_REMOTE` → `SCPR_ACTIV_MN_REMOTE_SUB`) | customizing **sin** API | ✅ | ✅ `TASK_CUST_EXP` |
| **3** | `RFC_ABAP_INSTALL_AND_RUN` + `INSERT` | tablas propias `Y*`/`Z*` · **o excepción autorizada** | ❌ | ❌ |

**Si un artefacto dice "no hay canal", no le creas: pregúntale al sistema.**
`RFC_READ_TABLE` sobre `TFDIR WHERE FMODE = 'R' AND FUNCNAME LIKE '%<TEMA>%'`.
Así se recuperaron `GL_ACCT_MASTER_SAVE_RFC` y `RS_CREATE_VARIANT_RFC`, ambos dados por inexistentes.

---

## 1. Medidores — solo lectura, nunca escriben

| Ejecutor | Qué mide | Salida |
|---|---|---|
| `Zagentexecution/tasks/2026_08_20_mmf_gl_sync/gl_alignment_check.py` | GL master (`SKA1`/`SKAT`/`SKB1`) P01 vs D01/V01, **fechando cada hueco con `ERDAT`** | separa deriva nueva de "nunca llegó"; permite falsar un "esto estaba alineado a fecha X" |
| `Zagentexecution/quality_checks/fsv_alignment_check.py` | las 8 tablas de la versión de balance | diff + **especificación de cambio** (`--spec`) |
| `Zagentexecution/quality_checks/ob09_vs_variant_check.py` | `T030H` × la selección de las variantes **leída con el resolutor legado `covered()`** (mezcla `SKONTO` con `AKONTO`, sin la regla de solo-exclusiones) — **no válido para cuentas asociadas `MITKZ D/K`**; A47 `DEFECTO_VIVO` | exit 1 solo si hay **exposición abierta en divisa** sin valorar |
| `Zagentexecution/quality_checks/config_transport_prerelease_check.py` | **DEFECTO_VIVO desde 2026-08-25** — diff de la tabla entera sobre una **TAREA** de customizing; sobre la ORDEN, que es lo que se libera, devuelve exit 0 sin analizar nada | clasifica VIAJA / NO-OP / DERIVA. **INTRUSA no es fiable**: sólo dispara en tablas con campo clave discriminante y mayoría estricta. Ver `brain_v2/methods/algorithms.json` A40 antes de usarlo |
| `variant_align.py` (sin `--execute`) | las 21 variantes de `SAPF100` en los 3 sistemas | diff por entrada |

> **`config_transport_prerelease_check.py` no cumple hoy la regla de entrada (b)** de este modelo
> —«verifica releyendo y no por código de retorno»—: publica precisamente un código de retorno
> engañoso. **Se mantiene listado para no perder la trazabilidad: marcado, no retirado.**

> **La celda de SALIDA de `ob09_vs_variant_check.py` NO está contaminada — sobrevive al defecto A47.**
> Verificado en código: `rc=1` depende sólo de `active = defect` (HEAD l.251 y l.263-264), y los 34
> falsos positivos del resolutor legado no pueden entrar en `defect` porque `exposure()` les devuelve
> «NO» al no mirar `BSID`/`BSIK`. El exit 1 sigue significando exactamente lo que dice la tabla.
> El epígrafe «Medidores — solo lectura, nunca escriben» también se verificó leyendo el fichero
> entero: no escribe nada. Anotado aquí para que la próxima revisión no lo reabra por contagio.

> **Texto retirado 2026-08-26 (conservado para anti-regresión).**
> - Fila 34, celda «Qué mide»: ~~`T030H` × selección real de las variantes~~ — RETIRADO 2026-08-26:
>   «real» es falso en la palabra que decide; lee la mezcla legada de `variant_accounts`
>   (HEAD l.81-102), no la selección real. Ver claim 599.
> - Fila 35: ~~`Zagentexecution/quality_checks/config_transport_prerelease_check.py` | una orden de
>   customizing contra la tabla entera | clasifica VIAJA / INTRUSA / NO-OP / DERIVA~~ — RETIRADO
>   2026-08-26: lo que mide no es una ORDEN sino una TAREA; contra una orden (`TRFUNCTION=W/K`)
>   imprime «E071K vacío» y sale 0 sin clasificar nada (medido con `D01K9B0FXE`,
>   `algorithms.json:1313`). Y la clase INTRUSA puede ser falsa **por vacuidad**.

**Medir siempre EN VIVO.** El Gold DB va meses por detrás; usarlo para un análisis de hueco produjo
en s102 una conclusión falsa sobre 20 M EUR de exposición.

---

## 2. Actuadores — escriben, y cada uno declara su peldaño

| Objeto | Ejecutor | Canal | Peldaño | Estado |
|---|---|---|---|---|
| **Cuentas GL** | `2026_08_20_mmf_gl_sync/gl_master_sync.py` | `GL_ACCT_MASTER_GET_COA_RFC` + `_GET_CCODE_RFC` → **`GL_ACCT_MASTER_SAVE_RFC`** | 1 | ✅ ejecutado: 2 en D01, 33 en V01 |
| **Variantes de programa** | `2026_08_21_variant_alignment/variant_align.py` | `RS_VARIANT_CONTENTS_RFC` → `RS_VARIANT_DELETE_RFC` + **`RS_CREATE_VARIANT_RFC`** | 1 | ✅ ejecutado: **21/21** idénticas en D01 y V01 |
| **Fondos** | `2026_06_29_fm_model_sync/fund_sync.py` · `fund_reconcile.py` | `FM_FUND_GET_DETAIL_RFC` → `FM_FUND_CREATE_RFC` / `_CHANGE_RFC` | 1 | ✅ probado s093 |
| **Centros gestores** | `2026_06_29_fm_model_sync/fund_center_sync.py` | `FM_FUNDS_CTR_CREATE_RFC` | 1 | ✅ probado s093 |
| **Proyectos / WBS** | `2026_06_29_fm_model_sync/ps_project_sync.py` | `BAPI_PROJECT_MAINTAIN` + `BAPI_TRANSACTION_COMMIT` | 1 | ✅ probado |
| **Versión de balance (FSV)** | `2026_08_21_fsv_alignment/fsv_align_exc001.py` | sin API → `RFC_ABAP_INSTALL_AND_RUN` | **3** | 🟡 **EXC-001**, bloqueado por el harness |
| **Centros de coste** | *(sin ejecutor)* | `BAPI_COSTCENTER_CREATEMULTIPLE` | 1 | ⚪ canal medido, sin construir |
| **`T030H` / OB09** | *(no hace falta)* | **transporte** — probado con `D01K9B0FXP` | — | ✅ canal ortodoxo |
| **Elementos de coste** | — | `BAPI_COSTELEMENT_CREATEMULTIPLE` **no** remote-enabled | — | 🔴 canal sin resolver |
| **Centros de beneficio** | — | — | — | ⛔ **no se usan en UNESCO** |

> **La fila `T030H` / OB09 SOBREVIVE al defecto A40 — no la reabras (verificado 2026-08-26).**
> Lo que afirma es que `T030H` **viaja por transporte**, y eso no lo produce el clasificador
> defectuoso: se prueba con que `E071K` tenga claves de `T030H` para ese `TRKORR` — lectura directa
> de tabla, ajena a los tres defectos de A40. Además, medido 2026-08-25 (`algorithms.json:1310`),
> `D01K9B0FXP` está ya **liberado e importado**: el canal no sólo se capturó, se ejecutó extremo a
> extremo, lo que refuerza la afirmación en vez de debilitarla. Que el `TRKORR` citado sea una
> **tarea** afecta al ALCANCE de aquella corrida (ver la nota de la fila 35), no a la existencia
> del canal.

Spikes cerrados: `spike_variant_write.py` (probó el canal de variantes) ·
`spike_bcset_activate.py` (peldaño 2: el BC-Set debe crearse a mano, `SCPR20`; sin eso no hay cadena).

---

## 3. El método común — los siete pasos que TODO actuador cumple

1. **Leer la referencia de P01 EN VIVO.** Si no se lee entera, abortar: media referencia produce un
   diff mentiroso.
2. **Diferenciar por CLAVE**, no por contenido, y declarar la clave explícitamente.
3. **Clasificar la diferencia antes de copiar.** No todo lo que difiere debe igualarse:
   *selección* (qué se procesa) · *modo/config* (cómo corre) · *residuo* de la última ejecución.
   "Hazlas idénticas" no es una instrucción segura por defecto.
4. **Respetar el orden referencial** (padres antes que hijos; plan de cuentas antes que sociedad;
   centros gestores antes que fondos; jerarquía y textos antes que asignaciones).
5. **Snapshot PRE a fichero** antes de tocar nada, y **restauración automática** si la escritura
   falla a medias.
6. **Dry-run por defecto**, `--execute` explícito, y el **flag de simulación siempre explícito** —
   es inverso entre APIs: omitir `I_FLG_TESTRUN` simula, omitir `TESTMODE` escribe.
7. **Verificar releyendo, clave a clave.** Un `RETURN` limpio no prueba nada.

### Las trampas medidas — todas rompen sin dar error
- **Fechas externo vs interno.** Se leen `31.07.2026`, se escriben `20260731`. Mandarlas tal cual
  graba basura (`20.7..31.0`). Rompió 4 parámetros en 3 variantes de V01 que **eran correctos**.
- **Lo que no se envía se rellena con defectos.** Una variante creada con 2 líneas salió con 9
  parámetros a cero. Copiar de menos pierde el proceso.
- **Estructuras aplanadas.** `GL_ACCT_MASTER_*` expone `KEYY/DATA/INFO/ACTION` anidados, no campos
  planos. `RFC_GET_FUNCTION_INTERFACE` da los tipos DDIC pero **no** esa forma: usar
  `conn.get_function_description(FM)` y recorrer `type_description.fields`.
- **`ACTION` obligatorio** en las API GL: sin él, `FH502 "Import of table SKA1 not possible"`, que
  suena a fallo técnico y es solo la acción vacía.
- **72 caracteres por línea** en ABAP generado: se trunca en silencio. Cortar con excepción, no con
  `[:72]` silencioso.
- **`TABLE_WITHOUT_DATA` = cero filas**, no un fallo — y una lectura fallida **no es ausencia**.

---

## 4. Cableado al modelo

| Artefacto | Qué contiene |
|---|---|
| Agente `master-data-sync` | matriz de canales, flag inverso, estructuras aplanadas, método |
| Agente `variant-intelligence` | lectura **y escritura** de variantes, clasificación de divergencia |
| Skill `sap_master_data_sync` | escalera de 3 peldaños + **registro de excepciones autorizadas** |
| Skill `sap_variant_analysis` | lectura y alineamiento de variantes |
| `capability_model` | `Closing_Activities.C_CONFIG` — de leer a leer-y-escribir la parametrización |
| Reglas | `feedback_standard_master_data_writes_through_the_standard_api` · `feedback_master_data_sync_does_not_carry_customizing` · `feedback_read_the_variant_the_variant_is_the_process` · `feedback_name_the_source_before_you_assert` |

## 5. Lo que este modelo NO cubre todavía
- **Centros de coste**: canal medido, ejecutor sin construir.
- **Elementos de coste**: sin canal RFC. Resolverlo antes de prometerlo.
- **Peldaño 2 (BC-Sets)**: viable pero exige un bootstrap manual por sistema.
- **La deriva de extensión a sociedad**: D01 y V01 tienen filas `SKB1` ausentes en sociedades
  distintas de UNES (14 y 146). Fuera del alcance trabajado.
