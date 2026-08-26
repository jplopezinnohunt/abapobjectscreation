---
name: sap_bcm_signatory_maintenance
description: Mantenimiento del PANEL DE FIRMANTES BCM en UNESCO — alta, baja y reconciliacion de firmantes en los nodos RY de las reglas 90000004 (BNK_COM / commit) y 90000005 (BNK_INI / validate), contra la carta TRS y el carton des signatures del banco. Metodo, trampas medidas y puertas de cierre. NO es el skill de pagos.
domains:
  functional: [BCM, Treasury, Payment_BCM]
  module: [FI, PD, HR]
  process: [P2P, T2R]
tier: project
maturity: production
origin: 2026-08-26 — auditoria "incidentes que no dejaron proceso" (claim 567)
sources_consolidated: 6
triggers: [panel de firmantes, bank signatory panel, signatory panel, change in bank signatory, add signatory, alta de firmante, baja de firmante, dar de baja un firmante, quien puede firmar pagos, quien aprueba pagos, carton, carton des signatures, OOCU_RESP, RY node, nodo RY, HRP1001, HRP1218, HRT1218, IT1218, BNK_APP, 90000004, 90000005, BNK_COM, BNK_INI, PERNR fantasma, ghost PERNR, sobre-autorizacion, over-authorization, DBS, carta TRS, FIN.8/MOD, reconciliacion de firmantes]
---

# Panel de firmantes BCM — mantenimiento y reconciliacion

> **P01 ES DE SOLO LECTURA PARA EL AGENTE.** Quien ejecuta el cambio es **DBS**, un humano
> autorizado, por la transaccion **`OOCU_RESP`** en P01. El alcance del agente es analisis +
> especificacion + verificacion posterior por `RFC_READ_TABLE`.
> Fuente: `bcm_signatory_change_procedure.md:195-196` · `bcm_signatory_change_solution_design.md:5`
> · `bcm_signatory_change_solution_design.md:329` · regla `feedback_p01_readonly_absolute`
> (CRITICAL: *"Confirmed by user during INC-000006313 with an emphatic 'you can not do any insert'"*).
> D01 **no** es alternativa: no tiene estructura organizativa HR valida y no se puede probar alli
> (`bcm_signatory_rules.md:170`), y ademas su configuracion de nodos **difiere** de P01 — el OBJID
> `50034894` significa cosas distintas en cada sistema (`..._solution_design.md:252`).

**Ejecutor del metodo**: agente `.claude/agents/bcm-signatory-panel.md` (lectura viva + cruce a tres
bandas). El PDF lo estructura `.claude/agents/authority-doc-reader.md`, que **no lee SAP**.
**Puerta de cierre**: `Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py`.

---

## Cuando usar este skill — panel de firmantes BCM (OOCU_RESP, nodos RY)

- Llega un *"Can you please add \<persona\> for \<entidad\> in BCM?"* (`..._procedure.md:21-33`).
- Hay que **dar de baja** un firmante (`bcm_signatory_rules.md:171`).
- Se pregunta **quien puede firmar o aprobar pagos** de una entidad, o hay que reconciliar SAP
  contra el **carton** de un banco (`.claude/agents/bcm-signatory-panel.md:8-11`).
- Auditoria de **sobre-autorizacion** antes de un cierre (mismo sitio).
- Health check recurrente, **al menos trimestral** (`bcm_signatory_rules.md:222`).

**No uses este skill para**: configuracion de pagos, F110, FBZP, bancos casa, metodos de pago o
lotes BCM — eso es `sap_payment_bcm_agent`. Extracto de bancos: `sap_house_bank_configuration`.

---

## Lo que NUNCA se hace con un panel de firmantes

1. **Nunca escribir en P01.** Ni por RFC, ni por BAPI, ni automatizando la WebGUI de `OOCU_RESP`
   (`feedback_p01_readonly_absolute`, CRITICAL).
2. **Nunca borrar una fila de `HRP1001`.** Una baja se hace **delimitando el `ENDDA`**; la historia
   hace falta para auditoria y para forense de doble control (`bcm_signatory_rules.md:171`,
   `..._procedure.md:186`).
3. **Nunca ejecutar la nota del solicitante.** Ver regla dura 1 abajo.
4. **Nunca actuar sobre deriva preexistente sin autorizacion por item** — se aparca para firma de
   TRS (`..._procedure.md:153-155`, `.claude/agents/bcm-signatory-panel.md:131`).
5. **Nunca describir el grupo destino solo por el nombre de la entidad.** Toda fila de spec lleva
   Regla + **RY OBJID** + STEXT (`feedback_bcm_spec_must_include_rule_ry_stext`, HIGH).
6. **Nunca concluir de un pantallazo.** `OOCU_RESP` consolida periodos en pantalla y su vista
   "Other period" **escondio la fila activa de Martin** (`bcm_signatory_rules.md:36`,
   `..._procedure.md:219`, `INC-000011781:48`).
7. **Nunca validar el comportamiento de produccion en D01, ni transportar estos nodos RY D01→P01**
   — colision de OBJID (`..._solution_design.md:252`).

---

## Por que faltaba el skill del panel de firmantes: el metodo estaba disperso en seis sitios

Para el panel de firmantes BCM existian **las reglas** (`bcm_signatory_rules.md`), **el
procedimiento** (`bcm_signatory_change_procedure.md`), **el diseno de solucion**
(`bcm_signatory_change_solution_design.md`), **un quality check**
(`bcm_signatory_reconciliation_check.py`), **un agente** (`bcm-signatory-panel`) y **un companion**
(`companions/bcm_signatory_companion.html`) — **todo menos el skill**. El metodo estaba, pero
DISPERSO en seis sitios.

Consecuencia **medida hoy, 2026-08-26**, corriendo
`python brain_v2/graph_queries.py tool "para panel de firmantes BCM"`: el bloque
`1_LEE_ESTO_PRIMERO` devolvia **`sap_payment_bcm_agent`** y **`sap_payment_e2e`** — los dos de
PAGOS, ninguno de firmantes. El agente y los tres checks si aparecian (bloques 3 y 4), pero lo que
el coordinador manda leer **antes de tocar nada** apuntaba al sitio equivocado.

La auditoria del 2026-08-26 lo clasifico como **"HAY INCIDENTES QUE NO DEJARON PROCESO"**:
`INC-000006313` (UIS, alta de VOFFAL) e `INC-000011781` (UBO, alta de RITTER) se ejecutaron los dos
y ninguno dejo herramienta. Es exactamente lo que prohibe
`feedback_second_occurrence_earns_a_procedure` (HIGH): *"2nd occurrence MUST leave a procedure doc +
a recurring check + a companion, so the 3rd is mechanical"*. Y la medicion de fondo esta en el
**claim 567**: *"11 de 13 incidentes no tenian documento de proceso en su dominio"*.

**Este skill no sustituye a los seis documentos: los INDEXA.** Cuando se quede corto, se AMPLIA —
no se construye al lado.

---

## Las dos reglas duras del cambio de firmantes (carta TRS y carton mandan)

Las dos estan verificadas en **dos sitios independientes** cada una (documento + regla de
comportamiento en `brain_v2/agent_rules/feedback_rules.json`).

### Regla dura 1 — el documento que AUTORIZA es la especificacion, nunca la nota del que pide

> *"On any operational change, the authorizing DOCUMENT is the specification — never the
> requester's summary. [...] No authority document = no change spec; stop and ask."*
> — `feedback_authority_of_record_not_the_requester_note`, **CRITICAL**

Medido **dos veces** (`..._procedure.md:35-41`):

| Caso | Nota del correo | Lo que decian las cartas |
|---|---|---|
| `INC-000011781` | *"add Renata RITTER for UBO"* | ADD Renata **+ DELETE Von Michael MARTIN** en los dos bancos |
| `INC-000006313` | *"add Ould Ahmedou Voffal, Said"* | ADD Said, y el carton revelo **3 derivas preexistentes** |
| `INC-000016338` | *"add Bettina REISS **and also add her bank limits**"* — en **singular** | las cartas capan a **DOS**: REISS **y BASOGLU**, sin tope desde 2024-09-27 |

La tercera es una **VARIANTE NUEVA**: la nota no omitio una BAJA, omitio a la **SEGUNDA PERSONA bajo la misma condicion**. Ejecutarla habria dejado a BASOGLU sin tope, como llevaba dos anos.

Ejecutar la nota de `INC-000011781` habria anadido al firmante nuevo y **dejado activo a uno no
autorizado en dos cuentas bancarias** (`feedback_authority_of_record_not_the_requester_note`, WHY;
`INC-000011781:40`).

### Regla dura 2 — el ticket es la OCASION de barrer la poblacion, no el ALCANCE

> *"After executing an operational change, reconcile the ENTIRE population against the authority —
> not just the row you touched. Whatever the sweep finds becomes a recurring check."*
> — `feedback_the_ticket_is_the_occasion_sweep_the_population`, **HIGH**

Nadie pidio auditar el panel de UBO; el pedido era anadir a una persona. El barrido contra el carton
destapo a **De Sousa Carvalho `10016038`**, activa en los 4 nodos con firma completa **y** el rol de
reverso/rechazo `BCM_REV_REJ_PAY` **desde enero de 2024**, sin estar en ningun carton: **18 meses de
sobre-autorizacion** que ninguna vigilancia miraba (`..._procedure.md:153-158`, `..._procedure.md:223`,
`INC-000011781:18`, `INC-000011781:63`).

---

## El metodo — 13 pasos, de la carta TRS al readback de HRP1001

Orden tomado del runbook (`bcm_signatory_change_procedure.md`, el documento mas reciente:
2026-08-21); los pasos de Gold DB y de barrido vienen del protocolo de reconciliacion
(`bcm_signatory_rules.md:220-242`) y las fases del diseno (`..._solution_design.md:318-330`).

### Paso 0 — Triage: la nota es la ocasion, abre los PDF primero

**Que**: reconocer la forma del pedido y tratar el correo como ocasion.
El flujo es siempre el mismo: `Role Management Mailer Service` → AO de la entidad
(*"IMPORTANT: Change in Bank Signatory panel of \<ENTIDAD\>"* + carta TRS + carton en PDF) →
**Ingrid Wettie** (BFM-TRS, Middle Office) → Pablo (`..._procedure.md:25-33`).
**Como**: abrir los adjuntos **antes** de leer la peticion. Lo estructura `authority-doc-reader`.
**Si se salta**: se ejecuta solo el ADD. Medido dos veces (regla dura 1).

### Paso 1 — Ordenar los tres artefactos por autoridad y extraer cada carta estructurada

**Que**: de mas a menos autoridad (`..._procedure.md:49-53`):
1. **Carton des signatures** (HEPATUS) — **la lista autoritativa de PERNR** y el tramo de importe.
2. **Carta TRS al banco** (REF `FIN.8/MOD/…`) — la autorizacion juridica.
3. **Nota del solicitante** — **solo la ocasion**.

**Como**: extraer `{ref, banco, cuenta(s), fecha_efecto, deletes[], adds[], panel[persona → tramo]}`
(`..._procedure.md:59-60`). Buscar **siempre** la clausula *"This list replaces all previous
signatory lists"*: cuando aparece, el panel del carton es **SUSTITUTIVO**, no incremental
(`..._procedure.md:55-57`).
**Si se salta**: sin esa clausula **no se puede calificar de sobre-autorizacion** ningun extra en SAP
(`..._procedure.md:55-57`).
**Formato del carton archivado**: cabecera con banco, cuentas, fecha, REF de la carta, modo de firma;
luego un PERNR de 8 digitos por linea con el nombre en comentario `#`
(ejemplo real: `Zagentexecution/quality_checks/cartons/uis_citibank_canada_20260402.txt`).

### Paso 2 — GATE 1 · COMPLETITUD

**Que**: ¿hay carton **vigente** para **cada** banco de la entidad que produce lotes BCM?
**Como**: los bancos BCM son los de **`T042A`** del codigo de sociedad, **NO** todos los de `T012K`

> ⚠️ **CORREGIDO 2026-08-26 (INC-000016338, claim 611).** **`T042A` está VACÍA en P01** —
> `RFC_READ_TABLE` sin filtro devuelve `TABLE_WITHOUT_DATA`. El universo del gate de completitud es
> **`T012K`** (bancos casa de la sociedad) corroborado con **`T042I`** (`ZLSCH`→`HBKID`). Y
> **`BNK_BATCH_HEADER` tampoco es legible** para el usuario SNC, así que la contradicción C2 **no se
> puede arbitrar leyendo**: es un LÍMITE DE LECTURA, nunca evidencia de que no haya lotes.
> *(Contradicción pendiente: `data_quality_issues` `DQ-2026-063-04` afirma que `T042A` sí se consultó
> con éxito en la sesión 63. O estaba poblada entonces y ahora no, o aquello nunca se re-verificó.)*
(`..._procedure.md:68`, `..._solution_design.md:285`).
Si falta uno → **HALT**: *"INCOMPLETO: faltan cartones de \<HBKID…\>"*.
**Si se salta**: con un carton faltante **NO se puede llamar deriva a ningun extra en SAP**
(`..._procedure.md:69-70`, `..._solution_design.md:295-296`).

### Paso 3 — GATE 2 · ALINEACION

**Que**: ¿son **IDENTICOS** todos esos cartones entre si?
**Por que**: el grupo de responsabilidad es de **ENTIDAD**, no de cuenta bancaria — un solo grupo
cubre todos los bancos, asi que paneles distintos por banco **no son representables en SAP** sobre
ECC (`..._procedure.md:72-75`, `..._solution_design.md:83`).
Si no lo son → **HALT** y devolver a TRS: la regla no es representable.
**Medido**: en `INC-000011781` los dos cartones (Citibank Brazil y Banco do Brasil) eran identicos —
**8 firmantes** — y por eso el cambio pudo ejecutarse (`..._procedure.md:78-80`, `INC-000011781:40`).

### Paso 4 — Refrescar el snapshot del Gold DB (bcm_signatory_assignment)

**Que**: prerequisito declarado del protocolo de reconciliacion.
**Como**: `python Zagentexecution/mcp-backend-server-python/extract_bcm_signatories.py`
→ alimenta `bcm_signatory_responsibility` y `bcm_signatory_assignment`
(`bcm_signatory_rules.md:4-5`, `:224-227`; ruta verificada en disco 2026-08-26 — es la unica copia).
**Si se salta**: el propio protocolo lo marca como *"Prereqs: Gold DB has a recent snapshot"* — sin
snapshot reciente el check compara contra datos viejos (`bcm_signatory_rules.md:224`).

### Paso 5 — Mapear el tramo del carton a NODOS (la seleccion vive en IT1218, no en PFAC)

**Que**: identificar QUE nodos RY toca el cambio.
**Como** (`bcm_signatory_rules.md:62-75`, `..._solution_design.md:61-79`):
`HRP1218` (cabecera → `TABNR`) → `HRT1218` (filas de expresion: `ELEMENT` / `EXPR_LOW` /
`EXPR_HIGH` / `REFSTRUCT`), evaluadas contra la estructura estandar **`BNK_STR_BATCH_REL_APPR`**.
**Clave de seleccion = `ZBUKR` (entidad) + `MAXPAYAMT_RULECURR` (banda de importe)** (+ `RULE_ID` en
los nodos INI). **No hay ningun campo de banco en la clave** → la seleccion es bank-agnostic
(`bcm_signatory_rules.md:66`, `..._solution_design.md:77`).
Traduccion del tramo (`..._procedure.md:104-113`):

| Lo que dice el carton | A que nodos entra |
|---|---|
| *unlimited* / sin tramo | **todos** los nodos de tramo de **ambas** reglas |
| *≤10K only* | solo los nodos ≤10K |

**Convencion medida**: *"for all transfers"* en el `STEXT` significa **sin tramo de importe** — es el
grupo vivo (`..._procedure.md:111-113`).
**Ver los criterios**: `OOCU_RESP` → doble clic en la responsabilidad → *Responsibility Specs*, o
`OOCU_RESP` → nodo → *"Simulate rule resolution"*. **`PP01` NO los muestra**: lista solo los
infotipos PD (Object/Relationships/Description/Profiles) — ver contradiccion C7.
**Si se salta**: `HRP1222` (los criterios PFAC estandar) esta **VACIO** para estos nodos — buscar ahi
devuelve nada y se concluye erroneamente que no hay criterio (`bcm_signatory_rules.md:64`,
`..._solution_design.md:346`). Y un alta "de una persona" toca **4 nodos**: `INC-000011781` anadio a
Renata Ritter a `50034892`/`50034893`/`50034894`/`50036737` (`bcm_signatory_rules.md:277`).

**Mapa de nodos** (`..._procedure.md:93-100`, `bcm_signatory_rules.md:112-118`, `:145-159`,
`..._solution_design.md:217-224`):

| Entidad | COMMIT — regla 90000004 | INICIAR/VALIDAR — regla 90000005 | Patron |
|---|---|---|---|
| **UBO** | `50034894` ≤10K · `50036737` >10K | `50034892` ≤10K · `50034893` ≤5M | 2×2 limpio, por tramo |
| **UIS** | `50010054` todos · `50036326` ≤10K *(0)* | `50010051` *(0)* · `50010053` *(0)* · `50036801` | tramos viejos retirados |
| **IIEP** | `50010088` todos | `50010087` | nodo unico |
| **UIL** | `50037531` **0→50M** · `50039525` **≤10K** | `50037530` **0→max** · `50039526` **≤10K** | **2×2 SOLAPADO** — el nodo alto arranca en 0,00 A PROPOSITO y el bajo lleva SOLO a los limitados (decision s104, claim 613). **NO 'armonizar' con UBO subiendo el suelo del alto**: quitaria a los cuatro sin tope los pagos <10.000 |
| **UNES** | `50010052` *(0 — va por Coupa)* | `50010075/76/77/78/79` · `50032363` · `50036716` *(0)* · `50038878` | muchos tramos INI |
| *stubs* | — | `50038588` / `50038589` ("Generated Rule", vacios) | **ignorar** |

*(0)* = cero miembros activos.

> **⚠️ DOS PATRONES DE TRAMO CONVIVEN, y los dos son VALIDOS** (claim **613**, s104):
> **UBO** — nodo bajo con TODOS (7) y nodo alto DISJUNTO (6, subconjunto sin la limitada).
> **UIL** — nodo bajo con SOLO los limitados (2) y nodo alto SOLAPADO 0→max (4).
> Cada uno hace directa una pregunta distinta: UBO *¿quien PUEDE aprobar ≤10K?*, UIL *¿quien esta
> LIMITADO?*. Se eligio el de UIL a proposito porque esa es la pregunta que hace el **carton**.
> **El de UIL depende de que la determinacion devuelva la UNION** — verificado (claim 612:
> 10.000,00→6 agentes, 10.001,00→4) y condicionado a que `Priority` de `OOCU_RESP` siga VACIA.
> **Antes de tocar bandas en cualquier entidad: SIMULA** (`feedback_simulate_before_deciding_the_shape`).


### Paso 6 — Lecturas previas obligatorias en vivo: PA0002, PA0105, PA0000, USR02, HRP1001

**Que**: validar identidad, usuario, vigencia, pertenencia y permiso **antes** de escribir la spec.
`PA0001` esta **bloqueado** para el usuario SNC, asi que la identidad se arma por partes
(`..._procedure.md:120-132`, `..._solution_design.md:325`, `bcm_signatory_rules.md:212-213`):

| Que | Donde | Por que importa |
|---|---|---|
| Nombre | `PA0002` `VORNA`/`NACHN` | cruzar con el carton **y con el pasaporte** del PDF |
| Usuario SAP | `PA0105` `SUBTY='0001'` → `USRID` | **si falta, es un PERNR fantasma** (trampa 1) |
| Email | `PA0105` `SUBTY='0010'` → `USRID_LONG` | cruzar con el que declara la carta |
| Empleado activo | `PA0000` `STAT2='3'` | una baja no puede firmar |
| Usuario vivo | `USR02` `UFLAG=0`, `USTYP=A`, **`GLTGB`** | Renata tenia `GLTGB=2026-09-30`: caduca |
| Pertenencia actual | `HRP1001`, **todos los periodos** | los periodos ocultos esconden filas activas |
| Rol de firma | `BNK_APP` / `YS:FI:M:BCM_MON_APP______:<ENT>` | **sin el rol no firma aunque este en el nodo** |

```bash
python Zagentexecution/quality_checks/bcm_role_gap_check.py          # rol BNK_APP por asignado
python Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py   # fantasmas + role-split + diff carton
```

**Limites de `RFC_READ_TABLE`** (`bcm_signatory_rules.md:210-211`, `..._procedure.md:139-140`):
`IN (...)` falla con `OPTION_NOT_VALID / SAIS 000 / suspicious WHERE condition`; mas de ~3 `AND`
falla con `The parser produced the error: "AN" is not valid h`. **Una o dos condiciones por llamada,
en bucle, y el resto se filtra en Python.**
**Si se salta el chequeo de `PA0105/0001`**: se crea un **GHOST PERNR** — el firmante queda
silenciosamente deshabilitado en `BNK_APP` (`bcm_signatory_rules.md:216`, `:248-253`).

**Panel activo antes del cambio** (`bcm_signatory_rules.md:179-185`; criterio de activo = `endda >= hoy`):

```sql
SELECT stext, pernr, firstname || ' ' || lastname AS name, uname, email, begda, endda
FROM bcm_signatory_assignment
WHERE rule_number = '90000004'
  AND endda >= strftime('%Y%m%d','now')
ORDER BY stext, lastname;
```

### Paso 7 — Reconciliar: las cuatro salidas

Por cada par (nodo × persona) (`..._procedure.md:148-153`, `..._solution_design.md:290-294`):

| Situacion | Accion | ¿Va en este pedido? |
|---|---|---|
| en el carton **y** activo en SAP | *keep* | — |
| en el carton **y** ausente/expirado en SAP | **ADD** | si, **si la carta lo pide**; si no, hueco → TRS |
| la carta dice *delete* **y** activo en SAP | **DELIMIT** | si |
| activo en SAP **y** en ningun carton | **sobre-autorizacion** → DELIMIT | **NO** — se aparca para firma de TRS |

La cuarta fila es la que produce los hallazgos grandes y la que **nunca** se ejecuta sin autorizacion
especifica (regla dura 2).

### Paso 8 — La especificacion para DBS

**Formato obligatorio** — cada fila lleva las **tres** identidades (`..._procedure.md:164-174`):

```
PLVAR=01  OTYPE=RY  RELAT=007  ISTAT=1  SCLAS=P
BEGDA=<fecha de efecto>  ENDDA=99991231

| Op      | Regla    | RY OBJID | STEXT               | PERNR    | Persona |
|---------|----------|----------|---------------------|----------|---------|
| ADD     | 90000005 | 50034892 | UBO Validation ≤10K | 10021811 | Ritter  |
| DELIMIT | 90000005 | 50034893 | UBO Validation ≤5M  | 10108464 | Martin  |
```

- **ALTA**: fila nueva en `HRP1001` con `OTYPE='RY' OBJID=<grupo> RELAT='007' SCLAS='P'
  SOBID=<PERNR>`, `BEGDA=fecha de efecto`, `ENDDA=99991231` (`bcm_signatory_rules.md:172`).
  `RELAT='007'` es la relacion PD generica "assigned to"; `SCLAS='P'` la estrecha a Persona
  (`bcm_signatory_rules.md:35`).
- **BAJA**: **delimitar el `ENDDA`**, nunca borrar (`bcm_signatory_rules.md:171`,
  `..._procedure.md:186`).
- **`BEGDA` = fecha de efecto de la CARTA, no la de ejecucion.** En `INC-000006313` la carta decia
  *"as of immediate effect"* con fecha 02/04 y DBS puso 09/04: **siete dias de hueco de auditoria**
  en los que Said estaba en el panel del banco y no en el enrutado de SAP (`..._procedure.md:182-184`).
- **Nunca omitir el `RY OBJID`** (`..._procedure.md:176-180`): ver trampa 2.
- **Salida completa** — una sola tabla que espeja `OOCU_RESP` **1:1**, con las filas activas **y** las
  expiradas, mas las altas. Columnas:
  `Rule | Node (OBJID) | Node name (STEXT) | PERNR | Person | Live status (HRP1001) | Carton |
  Access (BNK_APP role) | Action`, seguida del resumen de operaciones netas partido en **"pedido
  actual"** vs **"issues viejos, retenidos para TRS"** (`..._solution_design.md:302-314`).
- **Todo cambio de firmante son DOS acciones**: el nodo (`OOCU_RESP`/DBS) **y** el rol de
  autorizacion (`PFCG`/Security) (`..._solution_design.md:308`).

### Paso 9 — Ejecucion: quien y donde

| | |
|---|---|
| **Quien** | **DBS**, en P01, por `OOCU_RESP` (`..._procedure.md:195`) |
| **El agente** | **nunca escribe P01** (`..._procedure.md:196`, `..._solution_design.md:5`) |
| **Rol `BNK_APP`** | ticket **aparte** a Security. El cambio de nodo **no basta**: Renata quedo en los 4 nodos y seguia sin poder firmar (`..._procedure.md:197`, `INC-000011781:20`) |

`OOCU_RESP` es la cascara de mantenimiento BCM/Treasury sobre **PFAC**; no hay tabla BCM dedicada —
todo cae en infotipos PD de HR (`bcm_signatory_rules.md:14`).

### Paso 10 — Verificacion posterior, obligatoria y en este orden

(`..._procedure.md:203-208`)
1. **Releer `HRP1001`** de cada nodo tocado: la fila existe, con `BEGDA`/`ENDDA` esperados.
2. **Refrescar el Gold DB**: `extract_bcm_signatories.py`. En `INC-000006313` el conteo paso de
   **253 → 255**, +2 por Said — **el delta debe cuadrar con las operaciones de la spec**
   (`INC-000006313:99`).
3. **Correr los tres checks**: reconciliacion, `bcm_role_gap_check.py`, `bcm_release_vs_approve.py`.
4. **Salida esperada**: `GHOST=0 · ROLE-SPLIT=0 · CARTON DIFF: MATCH=n, EXTRAS=0, MISSING=0`.

Codigos de salida del check de reconciliacion (`bcm_signatory_reconciliation_check.py:44-47`):
**0** = limpio · **1** = ghost PERNR o mismatch de carton · **2** = error de DB/esquema.
`bcm_role_gap_check.py` solo devuelve 1 **con `--strict`** (`bcm_role_gap_check.py:52-55`).

### Paso 11 — Barrer la POBLACION y archivar el carton

**Barrido** (regla dura 2). Cobertura por grupo y doble sombrero
(`bcm_signatory_rules.md:187-202`):

```sql
-- Cobertura por grupo, ahora
SELECT stext, COUNT(*) AS active_signatories
FROM bcm_signatory_assignment
WHERE rule_number IN ('90000004','90000005') AND endda >= strftime('%Y%m%d','now')
GROUP BY rule_number, stext ORDER BY rule_number, stext;

-- Doble sombrero: ¿alguien en INI y COM de la misma entidad?
SELECT a.uname, a.stext AS ini_group, b.stext AS com_group
FROM bcm_signatory_assignment a
JOIN bcm_signatory_assignment b ON a.uname = b.uname
WHERE a.rule_number = '90000005' AND b.rule_number = '90000004'
  AND a.endda >= strftime('%Y%m%d','now') AND b.endda >= strftime('%Y%m%d','now');
```

**Archivar el carton, sin sobrescribir nunca**: un fichero por carton de cuenta bancaria en
`Zagentexecution/quality_checks/cartons/<entity>_<bank>_<yyyymmdd>.txt`. *"Keep every historical
carton — never overwrite — so we can reproduce the reconciliation as of any date"*
(`bcm_signatory_rules.md:240`).

### Paso 12 — Cierre: registrar, responder, gatear

**Registrar el cambio** en la tabla *Change history* del propio doc de reglas: fecha, incidente, que
cambio exactamente (PERNR + nodos + `BEGDA`/`ENDDA`) y la **carta origen**
(`bcm_signatory_rules.md:272-278`). Formato medido de la fila:

```
2026-04-09 | INC-000006313 | Added PERNR 10092400 (Said OULD AHMEDOU VOFFAL) to RY 50010054 and
RY 50036801, BEGDA=2026-04-09, ENDDA=99991231 | TRS letter FIN.8/MOD/10.0000003625
```

**Responder al solicitante** con la plantilla de `..._procedure.md:229-237`: persona + entidad + n
nodos + reglas + fecha de efecto + *"verificado por lectura directa de `HRP1001`"*; mas, si aplica,
la baja que instruian las cartas, el rol `BNK_APP` pendiente, la deriva preexistente sin tocar, y el
**recordatorio del plazo de dos semanas** que tiene la AO para confirmar que el banco registro el
cambio (`INC-000006313:20` — 2026-04-08 → 2026-04-22).

**Puerta de cierre** (`..._procedure.md:243-251`) — 9 casillas, y dos son bloqueantes:
- [ ] Cartas y cartones leidos; gates de completitud y alineacion pasados
- [ ] Verificacion previa en vivo (identidad, usuario, validez, periodos, IT1218)
- [ ] Spec con Regla + RY OBJID + STEXT en **cada** fila, y `BEGDA` = fecha de la carta
- [ ] DBS ejecuta en `OOCU_RESP`
- [ ] Readback de `HRP1001` + refresco del Gold DB + los tres checks en verde
- [ ] **Rol `BNK_APP` concedido — sin esto la persona no puede firmar y el incidente NO se cierra**
- [ ] Deriva preexistente registrada y comunicada a TRS, **sin actuar** sin autorizacion por item
- [ ] Respuesta enviada, con el recordatorio del plazo de dos semanas
- [ ] Incidente con registro en `brain_v2/incidents/incidents.json` y enlace al procedimiento

Gatear la ultima con
`python Zagentexecution/quality_checks/incident_record_coverage_check.py` (exit 0 = limpio):
un doc de incidente sin registro de primera clase es invisible para BRAIN LOOKUP
(`feedback_incident_doc_without_record_is_invisible`, HIGH).

### Recurrente (no disparado por ticket)

- **Health check trimestral como minimo** — mismo comando del paso 10.3
  (`bcm_signatory_rules.md:222`).
- **Re-medir la diferenciacion de paneles** despues de cada refresco del extractor: por
  (entidad, regla) comparar los paneles ACTIVOS entre bandas. El propio analisis cierra con
  *"Re-measure after refreshing `extract_bcm_signatories.py`"* (`bcm_signatory_rules.md:77-102`).

---

## Las trampas medidas

Las ocho canonicas estan en `..._procedure.md:212-223` y en el **claim 566** (VERIFIED, TIER_1).
Aqui van con su evidencia, mas las que solo aparecen en el doc de reglas y en el diseno.

### T1 — PERNR fantasma
Una fila BCM puede apuntar a un PERNR que **existe en `PA0002` pero no tiene usuario SAP en
`PA0105/0001`**. El workflow no puede enrutar el work item y el firmante queda **silenciosamente
deshabilitado**.
**Medido (DEF-BCM-001)**: PERNR fantasma `10567156` (Svein OESTTVEIT) anadido **2025-10-04** con
`ENDDA=99991231` en UIS RY `50010054` (regla 90000004) y RY `50036801` (regla 90000005). El PERNR
real es `10067156`, usuario `S_OESTTVEIT`. Descubierto en sesion #051 / `INC-000006313`. Registrado
en `brain_v2/agi/data_quality_issues.json` como `dq_ghost_pernr_bcm_oesttveit`.
Fuente: `bcm_signatory_rules.md:216`, `:248-255`; regla `feedback_bcm_ghost_pernr_check` (HIGH).
**Defensa**: exigir `PA0105/0001` a todo PERNR del nodo; detector automatico en el check de
reconciliacion.
**Fix path declarado** (para DBS, cuando TRS lo autorice): delimitar las filas con `SOBID=10567156`
en los dos grupos (`ENDDA=hoy`) e insertar filas nuevas con `SOBID=10067156`. *"Do NOT touch Svein's
historical 10567156 row — preserve as audit trail"* (`bcm_signatory_rules.md:254`).

### T2 — Grupos gemelos
`IIEP Validation` (`50010087`) y `UIS Validation` (`50036801`) son **adyacentes en el arbol de
`OOCU_RESP`**, cuelgan de la **misma regla 90000005** y **ambos acaban en "Validation"**.
**Medido**: en `INC-000006313` Parte 2 (sesion #052, 2026-04-13) el operador abrio IIEP creyendo que
era UIS y la fila `10067156` de Svein quedo en `IIEP Validation` con `BEGDA=20260413`. Svein quedo
habilitado para aprobar pagos de **otra entidad**, sin carta que lo autorizara. Lo cazo el check de
reconciliacion **el mismo dia**; DBS revirtio (delimito) y re-anadio correctamente.
Fuente: `INC-000006313:191-200`, `..._procedure.md:176-180`,
regla `feedback_bcm_spec_must_include_rule_ry_stext` (HIGH).
**Defensa**: Regla + **RY OBJID** + STEXT en cada fila de spec.

### T3 — La nota no es la carta
Ver **regla dura 1**.

### T4 — Periodos ocultos
`OOCU_RESP` **consolida el periodo en pantalla**. La validez autoritativa es la de **cada fila
`HRP1001`** (`BEGDA`/`ENDDA` por periodo), no el span que muestra la transaccion cuando hay periodos
adyacentes (`bcm_signatory_rules.md:36`).
**Medido**: la vista *"Other period"* escondia la fila activa de Martin `10108464`
(`2024-11-19 → 99991231` en `50034893`); se confirmo leyendo `HRP1001` en todos los periodos
(`INC-000011781:48`, `..._procedure.md:219`).
**Defensa**: `HRP1001` **todos los periodos**, nunca un pantallazo.

### T5 — Nodo ≠ permiso
Estar en el nodo **no** habilita a firmar: hace falta ademas el rol que concede la transaccion
`BNK_APP`.
**Medido (P01, 2026-06-19)**: de **40 firmantes activos**, **33 OK y 7 NO pueden abrir `BNK_APP`**
(`VM_MARTIN`, `I_BA`, `R_RITTER`, `B_PONT`, `I_ADJANOHOUN`, `I_BIDAULT`, `S_EL-HOLOUI`). Aplicado a
nodo × agente: **89 asignaciones activas, 76 OK, 13 no pueden firmar** (las mismas 7 personas
repetidas). Persistido en Gold DB `bcm_signatory_role_gap` (40 filas) y `bcm_node_agent_role_check`
(89 filas). Fuente: `..._solution_design.md:181-193`, `:230-244`.
**Familia de roles**: master `YS:FI:M:BCM_MON_APP______:` con un derivado por entidad que difiere
**solo en el nivel de organizacion `$BUKRS`** — `:UBO`, `:IIEP`, `:UIS`, `:UIL`, `:UKDS`, `:ALL`.
**UNES usa `:ALL`; no existe `:UNES`** (`..._solution_design.md:195`).
**Defensa**: `bcm_role_gap_check.py` + ticket a Security, y la columna *Access* en la tabla de salida.
**Corolario medido**: la simulacion de resolucion de regla devolvio a BA (`10005016`), que **no tiene
el rol** → **determinacion de agente ≠ autorizacion** (`..._solution_design.md:81`).

### T6 — Grupo de ENTIDAD, no de cuenta
No hay ningun campo de banco en la clave de seleccion. Un grupo RY es de nivel entidad y cubre
**todas** las cuentas bancarias de esa entidad, en todos los bancos
(`bcm_signatory_rules.md:66`, `..._solution_design.md:83`).
**Consecuencia medida (UQ-BCM-001)**: STEPHENSON-ODLE (`10136066`) y ZHANG (`10098989`) estan activos
en SAP y **no** en el carton UIS Citibank Canada de 2026-04-02 — y **eso puede ser legitimo** si UIS
tiene cuentas en otros bancos donde sigan autorizados. Pregunta aparcada para TRS; registrado como
`uq_uis_non_citibank_signatories` en `brain_v2/agi/known_unknowns.json`
(`bcm_signatory_rules.md:257-262`).
**Defensa**: los dos gates (pasos 2 y 3).

### T7 — Fecha de efecto
Ver paso 8. Siete dias de hueco de auditoria en `INC-000006313` (`..._procedure.md:182-184`).

### T8 — El ticket es la ocasion, no el alcance
Ver **regla dura 2**.

### T9 — Role-split: un firmante puede estar solo en Commit o solo en Validation
El carton del banco dice *"sign jointly two by two"* **sin distinguir rol**, asi que el diff
carton-vs-SAP **no se resuelve solo con la lista de nombres**.
**Medido (UQ-BCM-002)**: Anssi YLI-HIETANEN (`10097358`) activo **solo en Commit**; Lamin SANNEH
(`10150918`) **solo en Validation**, ambos en UIS RY `50010054` / `50036801`. Registrado como
`uq_uis_bcm_role_split_consistency` (`bcm_signatory_rules.md:264-268`).

### T10 — Las bandas de importe pueden ser VESTIGIALES
Asumir que la banda alta implica un panel mas restringido es **falso**.
**Medido (snapshot Gold DB 2026-04-13)**: IIEP / UIL / UIS con **1 sola banda activa**; UBO marginal;
UNES INI la unica realmente segmentada. **Evidencia dura en UIS**: nodo `50010051` (≤10K, 19 miembros
historicos) vs `50010053` (≤5M, 12) — el panel ≤5M era **subconjunto perfecto** del ≤10K
(`only-≤5M = 0`): la banda alta nunca tuvo a nadie que la baja no tuviera → el tramo **no daba
control extra** → ambos retirados y colapsados en `50036801`. Tendencia = **de-tiering**
(`bcm_signatory_rules.md:77-102`).
**Pero la banda SI enruta**: el importe es un criterio de seleccion real en IT1218
(`bcm_signatory_rules.md:81-82`).

### T11 — El COMMIT de UNES ya no existe en SAP
Todas las asignaciones UNES de la regla 90000004 estan **delimitadas** (RY `50010052`, 13 filas, 0
activas, todas cerradas el **2023-01-20**). Buscar al committer de UNES en SAP **no devuelve a
nadie, y eso es lo correcto**: UNES corre **"Process 4"** — BCM da 1 validacion (regla 90000005), el
fichero va a **Coupa** y Coupa da la 2a validacion antes del banco
(`bcm_signatory_rules.md:58`, `:112`; `..._solution_design.md:265-275`).

### T12 — Hueco de cobertura 5M–50M
En UBO y UIS existe firmante hasta 50M pero el **validador topa en 5M** → un pago en esa banda **no
se puede liberar en el paso 1**. Declarado como pendiente de confirmar si esos importes ocurren
(`..._solution_design.md:274`).

### T13 — Gotchas de lectura (los que cuestan tiempo)
(`bcm_signatory_rules.md:209-215`)
- `HRP1000` con `OTYPE='AC'` devuelve **0 filas** para el usuario SNC: las reglas BCM no estan como
  objetos PFAC `AC` genericos bajo esta autorizacion, sino como objetos **`RY`** con `SHORT` = clase
  de regla. Se encontro por fuerza bruta con `SHORT LIKE 'BNK%'`.
- `PA0001` **completamente bloqueada** (`TABLE_WITHOUT_DATA` por cada PERNR) y `HRP1000` con
  `OTYPE='P'` **tambien bloqueada**: no se puede leer la cabecera del objeto PD de la persona. Unico
  camino: `PA0002` + `PA0105` por PERNR.
- `PA0105`: `USRID` y `USRID_LONG` **no son intercambiables**. `SUBTY='0001'` usa el campo viejo
  `USRID` de 12 caracteres para el logon; `SUBTY='0010'` usa `USRID_LONG` para el email.
  Mutuamente excluyentes por subtipo.
- `OTYPE='RY'` **no esta documentado** en el mantenimiento PFAC estandar: es un subtipo especifico de
  BCM y solo aparece donde los workflows de Bank Communication Management estan activos.
- El `SHORT` de `HRP1000` guarda la **CLASE** de regla, no el **numero**: buscar `90000004` /
  `90000005` en `HRP1000` no encuentra nada (`bcm_signatory_rules.md:31-33`).

---

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
