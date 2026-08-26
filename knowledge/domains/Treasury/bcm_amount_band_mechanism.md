# BCM — cómo se decide QUIÉN firma un lote: el mecanismo de TRES NIVELES

**Medido**: 2026-08-26, P01 en vivo (`HRP1218`/`HRT1218`, `HRP1001`, `HRP1000`) + Gold DB para la
cadena `TBCA_*` / `TBNK_*` (esas tablas **no son legibles por RFC** con el usuario SNC:
`TABLE_WITHOUT_DATA` / `TABLE_NOT_AVAILABLE`; el Gold las tiene extraídas el 2026-06-19).
**Origen**: `INC-000016338` (UIL / alta de Bettina REISS con tope de USD 10.000).

> **Por qué existe este documento.** El corpus tenía la selección de nodo (IT1218) y tenía la cadena
> de release (`TBCA_*`), pero **en documentos distintos y sin conectar**, y no tenía en absoluto la
> regla de agrupación (`TBNK_RULE`). Al configurar un tope de importe para UIL quedó claro que son
> **tres niveles encadenados** y que tocar sólo uno no produce el efecto buscado.

---

## ⛔ PRIMERO: qué es cada regla y PARA QUÉ SIRVE

Nunca proponer "ajustar la regla 90000004" a secas. **Toda recomendación se escribe con el
objetivo de la regla delante**, porque el número no dice nada y se confunde con el release de
factura (ver la confusión documentada abajo).

| Regla | Clase | Paso | **Su objetivo — qué decide** | Cuándo ocurre |
|---|---|---|---|---|
| **90000005** | `BNK_INI` | **1.º VALIDAR** | **quién APRUEBA el lote de pago** una vez creado: la primera revisión, antes de que exista nada firmado | después de F110/FBPM1, sobre el **fichero** |
| **90000004** | `BNK_COM` | **2.º COMPROMETER** | **quién da la FIRMA FINAL que libera el fichero al banco**: pasado esto el dinero sale | después de la validación, sobre el **mismo** fichero |

**Las dos son BCM y las dos actúan sobre el MISMO lote de pago, después de F110.** No son
"una para la factura y otra para pagar": son **los dos pasos del doble control sobre el fichero de
pago**. Por eso `rel_proc = 01` (*Principle of Dual Control*) está en las dos, y por eso una misma
persona en las dos rompe el control (chequeo de doble sombrero).

**Lo que SÍ autoriza la factura es otra cosa y no está aquí:** `WS90000003` — *FI Release for
Payment*, a nivel de **DOCUMENTO** y **ANTES** de F110; es donde vive el código custom de UNESCO.
La cadena de firmantes BCM es `WS50100024` → `WS50100021` (`BNK_COM`) y `31000004` (`BNK_INI`),
cableada en `TBCA_RTW_LINKAGE`. **La confusión entre las dos cosas está registrada como
contradicción C1 del skill** y ya causó que se buscara el workflow equivocado en `SWDD`.

**Cómo se nombra un cambio, entonces:**
> *"Ajustar la regla **90000005 (BNK_INI, nodo `50039526` — quién valida los lotes de UIL de hasta
> 10.000)** y la regla **90000004 (BNK_COM, nodo `50039525` — quién da la firma final que libera
> esos mismos lotes al banco)**."*

---

## Los tres niveles, en orden de ejecución

```
F110 / FBPM1
    │
    ▼
[1] REGLA DE AGRUPACIÓN      TBNK_RULE + TBNK_RULE_SELOP
    ¿en qué lote cae este pago?  →  produce RULE_ID en BNK_BATCH_HEADER
    │
    ▼
[2] SELECCIÓN DE NODO        HRP1218 + HRT1218 (infotipo 1218 sobre el objeto RY)
    ¿qué panel de personas aplica a este lote?
    clave = ZBUKR + MAXPAYAMT_RULECURR + RULE_ID, evaluada contra BNK_STR_BATCH_REL_APPR
    │
    ▼
[3] PROCEDIMIENTO DE RELEASE TBCA_RELPROC_CUS + TBCA_RELPROC_EXP + TBCA_REL_PROC(T)
    ¿cuántas firmas hacen falta?  →  01 = Dual Control · 02 = 3x · 03 = 4x · 00 = sin release
    │
    ▼
HRP1001 del nodo elegido  →  las personas  →  BNK_APP (y su rol)  →  DMEE  →  banco
```

---

## Nivel 1 — la regla de AGRUPACIÓN, y la asimetría entre entidades

`TBNK_RULE_SELOP` (Gold: `bcm_grouping_rule_selop`) define los criterios de cada `RULE_ID`.
**La aridad — cuántos criterios lleva — difiere por entidad, y es lo que decide si el importe
parte el lote:**

| RULE_ID | Aridad | Criterios | ¿Parte por importe? |
|---|---|---|---|
| `UBO_AP_MAX` / `UBO_AP_ST` | **4** | DORIGIN · ZBUKR · **AMT_RULECU** · RZAWE | **SÍ** |
| `UIS_AP_MAX` / `UIS_AP_ST` | **3** | DORIGIN · ZBUKR · **AMT_RULECU** | **SÍ** |
| **`UIL_AP_ST`** | **2** | DORIGIN · ZBUKR | **NO** |
| `IIEP_AP_ST` | 2 | DORIGIN · ZBUKR | NO |
| `PAYROLL` | 2 | DORIGIN · ZBUKR | NO |

**`UIL_AP_ST` es la ÚNICA regla de agrupación de UIL.** Consecuencia medida: **todo lote de UIL
sale con el mismo `RULE_ID`, sea de 100 € o de 2 M €.** UIL nunca ha partido lotes por importe.

Notación de `AMT_RULECU` (trampa de lectura): los valores se guardan como
`low = '10000.00-'` (negativo, el pago sale) con `high = '0.00'`. Por eso
`UBO_AP_MAX` lleva `GT -10000` = **pagos de hasta 10.000** (su texto dice
*"max amount USD10.000"*), y `UBO_AP_ST` lleva `LE -10000` = **por encima de 10.000**.
**Leer `GT`/`LE` sin ver el signo invierte el sentido de la regla.**

## Nivel 2 — la selección de NODO (IT1218)

`HRP1218` (cabecera → `TABNR`) → `HRT1218` (filas `ELEMENT` / `EXPR_LOW` / `EXPR_HIGH`), evaluadas
contra la estructura estándar `BNK_STR_BATCH_REL_APPR`. `HRP1222` (los criterios PFAC estándar)
está **VACÍA** para estos nodos: buscar ahí devuelve nada.

**`MAXPAYAMT_RULECURR` es el importe del PAGO MÁS ALTO del lote**, no el total.
*(Semántica del nombre del campo; pendiente de confirmar con una simulación — ver §Abierto.)*

**No hay ningún campo de banco en la clave** → la selección es *bank-agnostic*, y por eso el grupo
RY es de ENTIDAD y cubre todas las cuentas de todos sus bancos.

### El patrón CORRECTO — UBO, medido

| Nodo | Regla | Banda | RULE_ID |
|---|---|---|---|
| `50034894` UBO signatures up to 10.000 | 90000004 COM | **0,00 → 10.000,00** | — |
| `50036737` UBO signatures for transfers over 10.000 | 90000004 COM | **10.000,00 → 50.000.000,00** | — |
| `50034892` UBO Validation up to 10.000 | 90000005 INI | 0,00 → 10.000,00 | `UBO_AP_MAX` |
| `50034893` UBO Validation up to 5.000.000 | 90000005 INI | 10.000,00 → 5.000.000,00 | `UBO_AP_ST` |

**Bandas DISJUNTAS.** La baja termina donde la alta empieza.

### El patrón A MEDIO HACER — UIL, dos lecturas del mismo día

**Lectura A — 2026-08-26, justo tras crear los nodos de tramo** (el peor estado, y la razón por la
que este documento existe):

| Nodo | Regla | Banda | Miembros |
|---|---|---|---|
| `50037530` UIL Validation | 90000005 INI | 0,00 → 9.999.999.999,00 | 6 |
| `50039526` UIL Validation upon 10000 | 90000005 INI | 0,00 → 10.000,00 | **0 — vacío** |
| `50037531` UIL signatures for all transfers | 90000004 COM | 0,00 → 50.000.000,00 | 4 |
| `50039525` UIL signatures up to 10000 | 90000004 COM | 0,00 → 10.000,00 | **1, sin rol `BNK_APP`** |

Un nodo vacío no tiene a quién enrutar y uno de una persona no satisface el doble control: los pagos
de UIL ≤10.000 no podían completar **ninguno** de los dos pasos.

**Lectura B — mismo día, tras repartir a los limitados** (estado actual mientras se escribe esto):

| Nodo | Regla | Banda | Miembros |
|---|---|---|---|
| `50037530` UIL Validation | 90000005 INI | **0,00** → 9.999.999.999,00 | 4 — Kempf, Valdes Cotera, Zholdoshalieva, Abdi |
| `50039526` UIL Validation up to 10000 | 90000005 INI | 0,00 → 10.000,00 | 2 — Reiss, Basoglu |
| `50037531` UIL signatures for all transfers | 90000004 COM | **0,00** → 50.000.000,00 | 4 — los mismos cuatro |
| `50039525` UIL signatures up to 10000 | 90000004 COM | 0,00 → 10.000,00 | 2 — Reiss, Basoglu |

Simétrico y legible, **pero todavía incompleto por dos razones**:
1. **Los nodos viejos siguen arrancando en 0,00** → el tramo 0–10.000 sigue teniendo dos dueños en
   los dos pasos.
2. **Los cuatro sin tope NO están en los nodos bajos.** Subir el suelo ahora los dejaría sin poder
   aprobar por debajo de 10.000 — que es autorización que su carta SÍ les da. Es la consecuencia 2
   de más abajo, y es el orden lo que la evita: **primero poblar el nodo bajo, después subir el
   suelo del alto.**

## Nivel 3 — el PROCEDIMIENTO de release (cuántas firmas)

| Objeto | `rel_type` | `rel_proc` | Significado | Workflow |
|---|---|---|---|---|
| `BNK_INI` | 1 | `01` | **Principle of Dual Control** | `31000004` |
| `BNK_COM` | 3 | `01` | **Principle of Dual Control** | `50100021` |

Maestro: `50100024`. Catálogo (`TBCA_REL_PROCT`): `00` No Release · `01` Dual Ctrl ·
`02` 3x Control · `03` 4x Control.
La determinación (`TBCA_RELPROC_EXP`) lista **`UIL_AP_ST` explícitamente** para `BNK_COM` → el
commit de UIL corre bajo doble control. **Todos los `RULE_ID` de la instalación apuntan a `01`**:
no hay ninguna entidad con triple o cuádruple control.

---

## Las tres consecuencias que sólo se ven cruzando los tres niveles

**1. Si la regla de agrupación no lleva importe, la banda del nodo es la ÚNICA discriminación —
y entonces ser disjuntas no es una mejora, es un REQUISITO.**
En UBO el importe discrimina dos veces (nivel 1 y nivel 2), así que un solape en el nivel 2 quedaría
tapado por el `RULE_ID`. En UIL no hay red: los dos nodos INI llevan **el mismo** `RULE_ID`
(`UIL_AP_ST`), y los dos COM no llevan ninguno. Con bandas solapadas, **nada discrimina**.

**2. Quien NO tiene tope tiene que estar en LOS DOS nodos.**
Es el error de concepto más fácil de cometer, y el que invierte el resultado: si a alguien sin
límite se le deja sólo en el nodo alto, **no puede firmar un pago pequeño**. En UBO se ve el patrón
correcto: el panel de la banda alta es un **subconjunto** del de la baja, y quien sobra en la baja es
justamente el limitado (`E_AMARAL`).
Corolario para UIL: subir el suelo de `50037530` a 10.000 **sin** mover a BASOGLU al nodo bajo la
dejaría autorizada **sólo por encima de 10.000** — exactamente lo contrario de lo que dice su carta.

**3. Un nodo con 0 o 1 personas no es un panel: es una parada.**
Con `rel_proc 01` (doble control), un nodo **vacío** no tiene a quién enrutar el work item y un nodo
de **una** persona no puede satisfacer el doble control. Y estar en el nodo **no** habilita a firmar:
hace falta además el rol `YS:FI:M:BCM_MON_APP______:<ENTIDAD>`. Medido en UIL el 2026-08-26:
`50039526` vacío y `50039525` con una sola persona **sin rol** → los pagos de UIL ≤10.000 no podían
completar ninguno de los dos pasos.

---

## La receta, en el orden en que hay que hacerla

1. **Simular primero** — `OOCU_RESP` → nodo → *Simulate rule resolution*, con un importe de cada
   tramo. No escribe nada y responde qué nodo gana.
2. **Hacer las bandas disjuntas** subiendo el **suelo** del nodo antiguo al techo del nuevo.
   Crear el nodo de tramo sin tocar el viejo deja el solape.
3. **Repartir las personas**: sin tope → en los dos nodos; con tope → sólo en el bajo.
4. **El rol** `BNK_APP` de la entidad, ticket aparte a Security.
5. **Re-simular** y releer `HRP1001` + `HRT1218` en vivo.

---

## Abierto — lo que hay que medir, no rellenar

1. **¿En qué MONEDA es el umbral?** El campo es `MAXPAYAMT_RULECURR` — *rule currency*. Las cartas
   TRS expresan el tope en **USD**; UIL es sociedad **EUR** (`T001`: UIL / DE / EUR) y UBO es
   **BRL** con el texto *"max amount USD10.000"*. Si la moneda de la regla no es USD, **el umbral
   configurado no es el de la carta** — y sería un problema de toda la instalación, no de UIL.
   **Medir**: la moneda de la regla, y una simulación con un importe alrededor del umbral.
2. **El borde exacto.** En UBO las dos bandas incluyen `10.000,00`; un pago de exactamente 10.000
   encaja en las dos. **Medir** con la simulación en el punto.
3. **`MAXPAYAMT_RULECURR` = pago más alto del lote** está tomado de la semántica del nombre, no
   verificado. **Medir**: un lote con varios pagos y comprobar qué nodo resuelve.
4. **La ruta exacta en pantalla para crear el nodo y su banda** sigue sin escribirse. Lo que SÍ está
   resuelto: se hace **en `OOCU_RESP`, directamente en P01, y NO genera transporte** (ver abajo).
   **Medir**: acompañar a DBS y capturar la secuencia de pantallas.

---

## De dónde sale cada dato

| Nivel | Tabla SAP | Tabla Gold DB | Legible por RFC/SNC |
|---|---|---|---|
| 1 agrupación | `TBNK_RULE` / `TBNK_RULE_SELOP` | `bcm_grouping_rule` / `bcm_grouping_rule_selop` | **NO** |
| 2 nodo | `HRP1218` / `HRT1218` / `HRP1000` / `HRP1001` | `bcm_node_selection_criteria` | **SÍ** |
| 3 procedimiento | `TBCA_RELPROC_CUS` / `_EXP` / `TBCA_REL_PROC(T)` / `TBCA_RTW_LINKAGE` | `bcm_release_proc_assign` / `_determination` / `bcm_release_procedure(_t)` / `bcm_release_wf_linkage` | **NO** |

**Relacionados**: [bcm_signatory_rules.md](bcm_signatory_rules.md) ·
[bcm_signatory_change_solution_design.md](bcm_signatory_change_solution_design.md) ·
skill `sap_bcm_signatory_maintenance` ·
incidentes [INC-000016338](../../incidents/INC-000016338_uil_bcm_add_reiss.md) ·
[INC-000011781](../../incidents/INC-000011781_ubo_bcm_add_ritter.md)


---

## Dónde vive el cambio: P01 directo, sin transporte — y qué implica

**Confirmado 2026-08-26 por el operador que ejecutó el cambio** (INC-000016338): crear los nodos
`50039525` / `50039526` con su banda de importe, y mantener las personas, se hace **en `OOCU_RESP`
directamente en P01**. **No genera orden de transporte.** Cierra el hueco 7 del skill.

Coherente con lo que ya constaba: D01 no tiene estructura HR válida para probarlo
(`bcm_signatory_rules.md:170`) y los OBJID **colisionan** entre D01 y P01
(`..._solution_design.md:252`), así que estos nodos no se transportan por diseño.

**La consecuencia que hay que tener escrita:** un cambio en **quién puede liberar dinero** se hace
en producción **sin ninguno de los controles técnicos que este proyecto exige para el código** — sin
transporte liberado como unidad de cambio, sin ATC, sin cuatro ojos técnicos, sin un rastro que un
tercero pueda auditar dentro del sistema.

**No es una violación de la disciplina ABAP**: no es código ni customizing transportable, es dato PD
(`HRP1000` / `HRP1001` / `HRP1218` / `HRT1218`). Pero sí significa que el **único** control real es:

1. el **proceso documental** — la carta TRS y el cartón como autoridad de registro, y
2. el **readback posterior** por `RFC_READ_TABLE`.

Por eso el readback de `HRP1001` y `HRT1218` **no es una verificación opcional**: es el único rastro
reproducible que queda del cambio. Y la tabla *Change history* de
[bcm_signatory_rules.md](bcm_signatory_rules.md) es el único registro que tiene la instalación.

*(Claim 611.)*
