# sap_bcm_signatory_maintenance — referencia detallada

> Extraído de `SKILL.md` para que su cuerpo no ocupe contexto en cada turno.
> Lo carga quien lo necesite; el índice está en `SKILL.md`.

## Objetos SAP que toca

### Transacciones y aplicaciones
| Objeto | Papel | Fuente |
|---|---|---|
| `OOCU_RESP` | Mantenimiento del nodo (criterios + personas). **La que se usa.** Cascara BCM/Treasury sobre PFAC | `rules:14`, `:167-168`; `design:169`, `:203` |
| `PP01` | Ve el objeto RY, **pero NO muestra los criterios de seleccion** | `design:203`; cf. `rules:75` |
| `BNK_APP` | Aplicacion de aprobacion: *Validate batch* / *Commit*. Firma = **System Signature** (usuario SAP + password, **no PKI**) | `rules:54`, `:56` |
| `BNK_MONI` | Monitor del lote | `design:203` |
| `PFCG` | Roles: donde se concede/retira `BNK_APP` | `design:195`, `:203` |
| `F110` / `FBPM1` | Corrida de pagos y creacion de los lotes BCM | `rules:50-51` |
| `DMEE` | Generacion del fichero tras el *Approved* | `rules:56` |

### Infotipos PD y datos de persona
| Tabla | Que guarda | Campos clave |
|---|---|---|
| `HRP1000` | Cabecera del objeto PD: los grupos `RY`, su `SHORT` (clase de regla) y `STEXT` | `PLVAR`, `OTYPE='RY'`, `OBJID`, `SHORT`, `STEXT`, `ISTAT`, `BEGDA`, `ENDDA` (`rules:25`) |
| `HRP1001` | Relaciones PD: RY → Persona. **La pertenencia.** | `OTYPE='RY'`, `OBJID`, `RELAT='007'`, `SCLAS='P'`, `SOBID`(=PERNR), `BEGDA`, `ENDDA` (`rules:26`) |
| `HRP1218` | Cabecera del infotipo 1218 → `TABNR` | `rules:64`, `:75` |
| `HRT1218` | Filas de expresion = **los criterios de seleccion del nodo** | `ELEMENT`, `EXPR_LOW`, `EXPR_HIGH`, `REFSTRUCT` (`rules:64`, `:75`) |
| `HRP1222` | Criterios PFAC estandar — **VACIA** para estos nodos | `rules:64`, `design:346` |
| `HRP1230` | Via PFAC generica — **VACIA** aqui | `design:346` |
| `PA0000` | Vigencia del empleado | `STAT2='3'` = activo (`procedure:129`) |
| `PA0002` | Datos personales | `PERNR`, `VORNA`, `NACHN` (`rules:27`) |
| `PA0105` | Comunicacion | `SUBTY='0001'`→`USRID` (logon) · `SUBTY='0010'`→`USRID_LONG` (email) (`rules:28`) |
| `PA0001` | **BLOQUEADA** para el usuario SNC | `rules:212` |
| `USR02` | Usuario vivo | `BNAME`, `UFLAG`, `USTYP`, `GLTGV`, `GLTGB` (`procedure:130`) |

### Estructura, reglas y cadena de release
| Objeto | Que es | Fuente |
|---|---|---|
| `BNK_STR_BATCH_REL_APPR` | Estructura estandar contra la que se evaluan las expresiones IT1218 | `rules:64`, `design:63` |
| `BNK_BATCH_HEADER` | El lote BCM: `ZBUKR` + `HBKID` + `RULE_ID` + importe. El `HBKID` se **transporta** pero nunca se **evalua** | `rules:51`, `design:42`, `:150` |
| Regla **90000004** / clase `BNK_COM` | **COMMIT** — quien da la firma final | `rules:44` |
| Regla **90000005** / clase `BNK_INI` | **INITIATE / VALIDATE** — quien aprueba primero | `rules:45` |
| `TBCA_RELPROC_CUS` | Objeto de release → tipo + procedimiento (`BNK_COM`=tipo 3/proc 01; `BNK_INI`=tipo 1/proc 01) | `design:107` |
| `TBCA_RELPROC_EXP` | **Determinacion**: que procedimiento dispara (expresion OR sobre `RULE_ID`) | `design:108` |
| `TBCA_REL_PROC` / `_T` | Catalogo de nombres: 01="Dual Ctrl", 00 sin release, 02 3x, 03 4x | `design:109` |
| `TBCA_REL_RULE` | **El cableado paso → regla**: `BNK_INI/01/01`→90000005 · `BNK_COM/01/01`→90000004 | `design:110` |
| `TBCA_REL_OBJ_CAT` | Categoria de objeto → `BNK_STR_BATCH_REL_APPR` | `design:66`, `:348` |
| `TBCA_REL_FM` | Actividad → modulo de funcion (todos estandar `BNK_API_BATCH_*`) | `design:114` |
| `TBCA_RTW_LINKAGE` | Workflow por paso: `BNK_INI`→WF **31000004** · `BNK_COM`→WF **50100021**; maestro **50100024** | `design:115` |
| `TBNK_RULE` / `_T` / `_SELOP` | Reglas de **agrupacion** del lote: `DORIGIN`+`ZBUKR`+`AMT_RULECU`+`RZAWE`. **Sin `HBKID`** | `design:38`, `:91-100` |
| `T042A` | Los bancos que realmente llegan a BCM por F110. **El universo del gate de completitud** | `procedure:68`, `design:285` |
| `T012` / `T012K` | Bancos casa de la sociedad. **NO es el universo del gate** | `procedure:68`, `design:32` |
| `F_STAT_USR` | Objeto de autorizacion: 4 ojos frente al creador de la F110 | `rules:54` |
| `F_STAT_MON` | `BNK_ACT` / `BNK_RULE` / `BNK_ITMDET` = validar / comprometer / rechazar | `design:195` |
| `F_REGU_BUK` | `BUKRS=$BUKRS` — la restriccion de entidad del rol derivado | `design:195` |
| `C_SIGN` | `SIGNAPPL=BANCO`, `SIGNOBJ=BC_LOG` — firma digital | `design:195` |
| `AGR_1251` / `AGR_TCODES` / `AGR_USERS` | De donde sale quien tiene `BNK_APP` | `design:179` |
| `BNK_API_GET_REL_ACTORS` → `BCA_API_REL_GET_ACTORS` → `BCA_OBJ_REL_GET_ACTORS` → `RH_GET_ACTORS` | La cadena de seleccion de agente, **100% estandar** | `design:66` |
| `RFC_READ_TABLE` | Canal de lectura del agente sobre P01 (con sus limites de sintaxis) | `rules:210-211` |

### Tablas del Gold DB (locales, NO en git)
`bcm_signatory_responsibility` · `bcm_signatory_assignment` (`rule_number`, `stext`, `pernr`,
`firstname`, `lastname`, `uname`, `email`, `begda`, `endda`) · `bcm_node_selection_criteria`
(67 filas / 24 nodos) · `bcm_signatory_role_gap` (40 filas) · `bcm_node_agent_role_check` (89 filas)
· `bcm_release_vs_approve` (11 filas) · `bcm_node_d01_vs_p01` · `bcm_approve_role` ·
`bcm_grouping_rule` · `bcm_grouping_rule_selop` · `bcm_release_rule` · `bcm_release_procedure(_t)` ·
`bcm_release_object` · `bcm_release_wf_linkage` · `bcm_release_proc_assign` ·
`bcm_release_proc_determination` · `bcm_release_activity_fm` · `bcm_workflow_custom_task`.
Fuente: `rules:5`, `design:79`, `:193`, `:232`, `:278`, `:350`.
Gold DB: `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`.

---

## Contradicciones entre fuentes

No las resuelvo en silencio. Las dos versiones, cual es mas reciente y por que.

### C1 — Que workflow enruta al firmante BCM: `90000003` vs `50100021`
- **`bcm_signatory_rules.md:47`** (extraccion 2026-04-09): *"Both are consumed by workflow 90000003
  (BNK_BATCH_HEADER approval)"*. Lo repite `rules:252` al explicar el ghost PERNR, y lo repite la
  regla `feedback_bcm_ghost_pernr_check`.
- **`..._solution_design.md:124`** (2026-06-19) lo **corrige explicitamente**: hay **DOS** puertas
  distintas. `WS90000003` es la puerta **FI Release for Payment**, a nivel de **documento**, **antes**
  de F110 — y es donde vive el codigo custom de UNESCO. La puerta de firmantes BCM es
  `WS50100024`→`WS50100021` (estandar `BUSISB001`), **despues** de F110, sobre el fichero de pago
  (`design:151-158`), cableada en `TBCA_RTW_LINKAGE` (`design:115`). Literal: *"The migrated-session
  note that called 90000003 'the BCM workflow' conflated the two."*

**Mas reciente y mas fundamentado: el diseno (2026-06-19)** — lee la tabla de linkage en vivo y
nombra la confusion. **Pero la correccion NO se ha propagado**: `rules:47`, `rules:252` y la regla
`feedback_bcm_ghost_pernr_check` siguen diciendo 90000003. **No afecta al metodo** (la mecanica del
ghost PERNR es la misma: la regla resuelve, devuelve el PERNR, busca el logon y lo encuentra vacio),
pero si a cualquiera que vaya a `SWDD` a mirar el workflow.

### C2 — Cual es el universo de bancos a reconciliar: `T042A` o `BNK_BATCH_HEADER`
- **`..._procedure.md:68`** y **`..._solution_design.md:285`**: bancos BCM = los de **`T042A`** del
  codigo de sociedad.
- **`INC-000011781:73`** (learning 3, 2026-06-19): *"Reconciliation universe = banks that produce BCM
  batches (`BNK_BATCH_HEADER`), not all `T042A` banks — UBO/BRA01 is Process 2 (manual), only CIT01
  reaches BCM."*

**Mas reciente: el procedimiento (2026-08-21)**, y **lo reconcilia en la practica** en `:82-83`:
*"UBO tiene dos bancos pero solo CIT01 produce lotes BCM; BRA01 es proceso manual. Aun asi se exigio
carton de los dos, porque la autorizacion si cubre ambos."*
**Como operar**: el gate de COMPLETITUD usa **`T042A`** (mas conservador: pide mas cartones);
`BNK_BATCH_HEADER` dice cuales de esos bancos **de verdad** generan lotes, que es lo que decide si un
extra en SAP tiene defensa de "otro banco".

### C3 — La clase de regla: `BNK_01_01_03` o `BNK_COM_01_01_03`
Dos cadenas distintas para lo mismo, **dentro del mismo fichero y la misma extraccion**
(2026-04-09), sin fecha que las separe:
- `bcm_signatory_rules.md:31-33`: `BNK_01_01_03` → 90000004 · `BNK_01_01_04` → 90000005.
- `bcm_signatory_rules.md:44-45`: titula la columna *"Rule class"* con `BNK_COM_01_01_03` y
  `BNK_INI_01_01_04`.

**La version anclada al campo es la de `:32`**, porque dice literalmente que es lo que
*"`HRP1000.SHORT` holds"*. **Tercera fuente independiente que la respalda**: la regla
`feedback_bcm_signatory_ry_otype` (HIGH) usa `BNK_01_01_03` / `BNK_01_01_04`. Lo de `:44-45` parece
el nombre logico de la regla, no el contenido del campo. **No esta resuelto en el fichero.**

### C4 — Cuantas filas de asignacion tiene la regla 90000004: 113 o 93
- `bcm_signatory_rules.md:108` declara **113 assignment rows**.
- Su propia tabla (`:112-118`) suma **93** (13+20+15+16+11+10+8).
- `bcm_signatory_rules.md:141` declara **253 filas totales entre las dos reglas**, y la tabla de
  90000005 (`:145-159`) suma **160**. **93 + 160 = 253**.

**El numero desviado es el 113**: el total de 253 es coherente con 93, no con 113. Corroborado
ademas por `INC-000006313:99` (*"row count: 253 → 255"*).

### C5 — Bandas activas de UNES INI: 6 u 8
- `bcm_signatory_rules.md:91`: UNES INI tiene **6** bandas activas (snapshot 2026-04-13).
- `bcm_signatory_rules.md:148-155`: la tabla lista **8** grupos UNES, **sin columna de "activos"**,
  asi que 6 contra 8 no se reconcilia dentro de ese fichero.

**Resuelto por una tercera fuente mas reciente**: `..._solution_design.md:265-270` (2026-06-19) lista
**exactamente 6 nodos UNES INI con gente**: `50032363`, `50010075`, `50010076`, `50038878`,
`50010077`, `50010078`. Los dos que faltan son `50036716` (marcado *(0)* en `..._procedure.md:99`) y
`50010079`. **6 es correcto; 8 es el conteo de grupos existentes, no de activos.**

### C6 — Svein OESTTVEIT aparece como committer ACTIVO y como firmante DESHABILITADO
- `bcm_signatory_rules.md:123` lo lista entre los *"Active committers as of 2026-04-09"* de UIS — y
  es **el unico nombre de esa lista sin UNAME entre parentesis**.
- `bcm_signatory_rules.md:252-253` (DEF-BCM-001, **el mismo dia**) dice que su PERNR es fantasma y
  que *"Svein silently cannot sign UIS payments in BNK_APP"*.

**No es un error de ninguna de las dos: es exactamente la trampa T1** — *"activo en SAP"* y *"puede
firmar"* no son lo mismo. Lo criticable es que el fichero nunca lo dice **en la lista**, solo 130
lineas mas abajo. La pista esta en el propio dato: **el UNAME vacio**.

### C7 — Donde se ven los criterios de seleccion: `PP01` si o no
- `bcm_signatory_rules.md:75`: *"View it: `PP01` (plan version 01, object type `RY`, infotype
  `1218`)"*.
- `..._solution_design.md:203` (2026-06-19): `PP01` tiene el tipo *"Responsibility"* en el desplegable
  **pero lista solo infotipos PD** (Object/Relationships/Description/Profiles) y **NO muestra los
  criterios de seleccion**; hay que ir por `OOCU_RESP` o por RFC.

**Mas reciente y mas especifico: el diseno.** Usa `OOCU_RESP` (doble clic en la responsabilidad →
*Responsibility Specs*) o lee `HRP1218`/`HRT1218` por RFC.

### C8 — Fecha de vigencia del doc de reglas
`bcm_signatory_rules.md:3` declara **una** fuente: *"direct read from P01 on 2026-04-09"*. Pero el
analisis de paneles es de un snapshot Gold DB de **2026-04-13** (`:77`) y la seccion de seleccion de
nodo es de una lectura viva de **2026-06-18** (`:62`, `:278`). **Es un compuesto de al menos tres
fechas bajo una sola cabecera; lo mas reciente es 2026-06-18.** Ademas el titulo *"Known defects
(open as of 2026-04-09)"* (`:246`) **nunca se re-fecho** pese a que el fichero incorpora contenido de
2026-06-18: el estado real de DEF-BCM-001, UQ-BCM-001 y UQ-BCM-002 a dia de hoy **no consta**.

---

## Lo que no esta resuelto

Huecos reales. No los relleno con SAP generico: cada uno dice **que hace falta medir**.

1. **El procedimiento en pantalla de `OOCU_RESP` no esta escrito.** Los ficheros nombran la
   transaccion (`rules:168`) y el resultado en `HRP1001` (`rules:171-172`), y el diseno da la ruta de
   menu a grandes rasgos (*Change* → regla → nodo → *Agent assignment*, `design:169`), pero **no hay
   ni un paso de navegacion**: como se abre el grupo, donde se teclea el PERNR, como se delimita.
   **Medir**: acompanar a DBS en la proxima ejecucion y capturar la secuencia.
2. **La especificacion de insercion sigue sin cerrar del todo.** `rules:172` da
   `OTYPE/OBJID/RELAT/SCLAS/SOBID/BEGDA/ENDDA`; `..._procedure.md:167` anade `PLVAR=01` e `ISTAT=1`.
   **Siguen sin aparecer en ninguna fuente**: `RSIGN` y la relacion inversa (`B007`). **Medir**:
   leer una fila `HRP1001` creada por DBS y ver que campos quedan poblados.
3. **Como se MODIFICA el infotipo 1218 no esta documentado.** Solo como se VE. Crear un nodo, cambiar
   una banda de importe o retirar una banda: el diseno dice que es *Approval Procedure customizing*
   que regenera la condicion IT1218 (`design:171`), pero **eso es un puntero, no un procedimiento** —
   y el propio corpus documenta que UIS retiro dos bandas y las colapso en una (`rules:94-97`), asi
   que se hizo sin dejar escrito como. **Medir**: la ruta IMG exacta y que transporta.
4. **Donde vive el NUMERO de validaciones requeridas por tramo.** `rules:45` afirma *"1 or 2
   validators depending on amount/entity"* y `rules:55` *"the required number of validations is
   reached (tier-dependent)"*, pero la clave de IT1218 (`rules:66`) solo tiene `ZBUKR` + banda +
   `RULE_ID`: **no hay campo de conteo**. El diseno da la mitad: el numero lo fija el
   **PROCEDIMIENTO** (`TBCA_REL_PROC`: 01="Dual Ctrl", 02=3x, 03=4x) y quien elige procedimiento es
   `TBCA_RELPROC_EXP` por `RULE_ID` (`design:108-109`). **Pero todos los `RULE_ID` listados apuntan a
   proc 01**, luego seria siempre dual control — lo que **no** sostiene el *"1 or 2 depending on
   amount"*. **Medir**: leer `TBCA_RELPROC_EXP` completa y comprobar si algun `RULE_ID` cae fuera de
   proc 01.
5. **La mitad Coupa del control de UNES queda fuera de este metodo.** `rules:58` dice que la 2a
   validacion vive en Coupa y `design:275` que *"For UNES 'who signs' is not a SAP node"*. **No consta**
   quien mantiene ese panel, en que sistema, ni si existe un equivalente que reconciliar contra el
   carton. **Medir**: preguntar a TRS/DBS por el panel Coupa de UNES.
6. **No hay lista nominal de VALIDADORES activos de la regla 90000005 comparable a la de committers.**
   `rules:143-159` da OBJID, STEXT, filas, entidad y tramo, pero **sin columna "Active" ni nombres**,
   al contrario que la 90000004 (`rules:110-135`). `design:258-270` da los nombres a 2026-06-19 pero
   por banda cruzada, no como lista limpia por nodo. **Medir**: correr la query de cobertura del
   paso 11 y publicar el resultado.
7. **No hay registro del cambio DENTRO de SAP.** El cambio va a P01 directo (`rules:168`) y el unico
   rastro que las fuentes definen es la tabla *Change history* de un fichero `.md`
   (`rules:272-277`). **Nada** sobre transporte, documento de modificacion ni evidencia en el
   sistema. **Medir**: comprobar si los infotipos PD dejan `AEDTM`/`UNAME` o documento de cambio para
   estas modificaciones.
8. **Solo existe UN carton archivado.** Medido en disco 2026-08-26:
   `Zagentexecution/quality_checks/cartons/` contiene **un unico fichero**,
   `uis_citibank_canada_20260402.txt`. **No hay cartones de UBO, IIEP, UIL ni UNES**, con lo cual el
   diff carton-vs-SAP del paso 10.3 **no se puede correr** para esas entidades. Y es peor que un
   hueco: **los dos cartones de UBO SE RECIBIERON y se leyeron** (`INC-000011781:17`, `:40` — 8
   firmantes, identicos), pero **nunca se archivaron**, contra la instruccion explicita de
   `rules:240`. **Accion**: recuperar los PDF de UBO del `.eml` de `INC-000011781` y archivarlos con
   la fecha del carton (08/04/2026).
9. **`full_inventory.py` no existe.** `..._solution_design.md:226` remite a *"full_inventory.py
   output"* para los conteos activos por nodo. Busqueda recursiva en el repo el 2026-08-26: **cero
   coincidencias**. **Accion**: o se escribe, o se sustituye la referencia por la query del paso 11.
10. **La correccion de C1 no esta propagada.** `rules:47`, `rules:252` y la regla
    `feedback_bcm_ghost_pernr_check` siguen nombrando el workflow `90000003` para el enrutado del
    firmante BCM. **Accion**: corregir a `WS50100024`→`WS50100021` citando `design:115` y `:124`.
11. **Abierto de los dos casos** (`..._procedure.md:257-260`, `INC-000011781:19-23`):
    - `INC-000011781`: el rol `BNK_APP` de Renata (`YS:FI:M:BCM_MON_APP______:UBO`) sigue **pendiente
      en Security** y **bloquea el cierre**; y **Yli-Hietanen `10097358`** esta en el carton y en
      ningun nodo UBO → **ADD ×4**.
    - `INC-000006313`: ¿tiene UIS cuentas en otros bancos donde Stephenson y Zhang siguieran
      autorizados? Se les dio de baja asumiendo que el carton de Citibank Canada es el unico panel de
      UIS — **parqueado para TRS** (= UQ-BCM-001).
12. **Estado actual de DEF-BCM-001 (ghost de Svein) no consta.** El fix path esta escrito
    (`rules:254`) pero ninguna fuente dice que se haya ejecutado, y la seccion que lo contiene nunca
    se re-fecho (C8). **Medir**: leer `HRP1001` de `50010054` y `50036801` y comprobar si `10567156`
    sigue activo.
13. **Hueco 5M–50M** (T12): declarado, sin confirmar si esos importes ocurren en UBO/UIS
    (`design:274`).

---

## De donde sale cada cosa

Este skill **no sustituye** a los documentos: los **indexa**. Cuando necesites el porque, ve a la
fuente.

### Documentos de dominio (`knowledge/domains/Treasury/`)
| Fichero | Que aporta | Fecha efectiva |
|---|---|---|
| `bcm_signatory_change_procedure.md` | **EL RUNBOOK**: 13 secciones, los 2 gates, las 4 salidas, la spec, las 8 trampas, la plantilla de respuesta y la puerta de cierre | 2026-08-21 (mas reciente) |
| `bcm_signatory_change_solution_design.md` | **EL MODELO**: 3 niveles, seleccion IT1218 probada leyendo el codigo, cadena de release `TBCA_REL_*`, inventario de nodos, control de acceso `BNK_APP`, cruce releaser-vs-signer | v1.2, 2026-06-19 |
| `bcm_signatory_rules.md` | **QUE GUARDA `OOCU_RESP`**: tablas y semantica de campos, las 2 reglas, el flujo, analisis de bandas, queries del Gold DB, 8 gotchas del extractor, defectos conocidos, change history | compuesto 2026-04-09 / 04-13 / 06-18 (ver C8) |
| `README.md` | Indice del dominio Treasury | — |

### Incidentes (`knowledge/incidents/`)
- `INC-000006313_uis_bcm_add_voffal.md` — UIS / Said Voffal + limpieza completa del panel. Contiene el
  near-miss de IIEP (`:191-200`), el delta 253→255 (`:99`) y el plazo de 2 semanas de la AO (`:20`).
- `INC-000011781_ubo_bcm_add_ritter.md` — UBO / Renata Ritter + baja de Martin + hallazgo De Sousa.
  Estado **EXECUTED (partial)**, con 2 items abiertos (`:19-23`).

### Herramientas
| Fichero | Que hace | Tier |
|---|---|---|
| `.claude/agents/bcm-signatory-panel.md` | **El agente que ejecuta este metodo.** Cruce a tres bandas: PDF / SAP / correo | agente |
| `.claude/agents/authority-doc-reader.md` | Convierte el PDF autorizante en hechos estructurados. **No lee SAP** | agente |
| `Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py` | **La puerta**: ghost PERNR + role-split + diff carton. Exit 0/1/2 | gate |
| `Zagentexecution/quality_checks/bcm_band_consistency_check.py` | **¿El panel POR TRAMO dice lo mismo que el carton?** Razona por TRAMO EFECTIVO (union de nodos, claim 612), no por nodo, asi que vale para los DOS patrones. Comprueba cobertura · exceso · quorum de 2 con rol · extras · `BEGDA` contra la fecha de la carta. Exit 0/1/2 | **gate** |
| `Zagentexecution/quality_checks/bcm_role_gap_check.py` | ¿Tiene rol `BNK_APP` cada asignado? Reconstruye `bcm_node_agent_role_check` y `bcm_signatory_role_gap` | live |
| `Zagentexecution/quality_checks/bcm_release_vs_approve.py` | Cruce paso 1 (validar) vs paso 2 (firmar) por entidad × banda | analysis |
| `Zagentexecution/mcp-backend-server-python/extract_bcm_signatories.py` | Refresco del Gold DB (unica copia en el repo, verificado 2026-08-26) | extractor |
| `Zagentexecution/quality_checks/cartons/` | Cartones historicos. **Nunca sobrescribir.** Hoy: 1 fichero | datos |

### Companion
`companions/bcm_signatory_companion.html` (115 KB) — la visual viva del panel.

### Reglas de comportamiento (`brain_v2/agent_rules/feedback_rules.json`)
`feedback_p01_readonly_absolute` (CRITICAL) · `feedback_authority_of_record_not_the_requester_note`
(CRITICAL) · `feedback_the_ticket_is_the_occasion_sweep_the_population` (HIGH) ·
`feedback_bcm_spec_must_include_rule_ry_stext` (HIGH) · `feedback_bcm_ghost_pernr_check` (HIGH) ·
`feedback_bcm_signatory_ry_otype` (HIGH) · `feedback_second_occurrence_earns_a_procedure` (HIGH) ·
`feedback_incident_doc_without_record_is_invisible` (HIGH) ·
`feedback_at_incident_close_check_for_related_domain_knowledge` (CRITICAL).

### Claims
**566** (VERIFIED, TIER_1) — el runbook y sus 8 trampas medidas.
**567** (VERIFIED, TIER_1) — 11 de 13 incidentes sin documento de proceso; la medicion que hizo
existir este skill.

### Skills vecinos (no confundir)
`sap_payment_bcm_agent` — pagos, F110, FBZP, bancos casa, lotes BCM. Es a donde el coordinador
mandaba **por defecto** antes de que existiera este skill.
`sap_payment_e2e` · `sap_house_bank_configuration` · `sap_bank_statement_recon`.

---

**Ultima actualizacion**: 2026-08-26 — creacion, consolidando 6 fuentes dispersas.
Nada de este skill es SAP generico: cada afirmacion lleva su fichero y su linea.
