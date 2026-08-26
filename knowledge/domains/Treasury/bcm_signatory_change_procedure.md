# Procedimiento operativo — CAMBIO DE PANEL DE FIRMANTES BCM

**Dominio**: BANCOS (registrado como `Treasury`, canónico `Treasury_EBS`) · **Eje de proceso**: **P2P**
— autorizar un pago es *purchase-to-pay*, no solo tesorería
**Nivel de evidencia**: TIER_1 — dos casos ejecutados y verificados en vivo contra P01
**Casos que lo fundan**: [`INC-000006313`](../../incidents/INC-000006313_uis_bcm_add_voffal.md) (UIS /
Said Voffal, + limpieza completa del panel) · [`INC-000011781`](../../incidents/INC-000011781_ubo_bcm_add_ritter.md)
(UBO / Renata Ritter, + baja de Martin)
**Modelo y esquema**: [`bcm_signatory_change_solution_design.md`](bcm_signatory_change_solution_design.md)
(3 niveles, IT1218, inventario de nodos) · [`bcm_signatory_rules.md`](bcm_signatory_rules.md)
(qué guarda OOCU_RESP, las dos reglas, gotchas del extractor)
**Companion**: `companions/bcm_signatory_companion.html`

> **Qué añade este documento y qué no.** El *solution design* explica **cómo funciona** el sistema y
> tiene la rutina en 7 fases. Esto es el **runbook**: qué hacer, en qué orden, con qué lectura exacta,
> y **las ocho trampas** que ya nos costaron un incidente cada una. Si vas a resolver un pedido nuevo,
> empieza aquí y salta al design cuando necesites el porqué.

---

## 0. Cómo se reconoce el pedido

Siempre llega igual, y esa es la primera trampa:

```
Role Management Mailer Service  →  AO de la entidad
        "IMPORTANT: Change in Bank Signatory panel of <ENTIDAD>"
        + carta TRS + carton des signatures en PDF
                        │
                        ▼
Ingrid Wettie (BFM-TRS, Middle Office)  →  Pablo
        "Can you please add <PERSONA> for <ENTIDAD> in BCM?"
```

**El correo de Ingrid es la OCASIÓN, no la especificación.** En los dos casos el correo decía
*«añade a X»* y las cartas adjuntas decían **añade a X y da de baja a Y**:

| Caso | Nota del correo | Lo que decían las cartas |
|---|---|---|
| `INC-000011781` | *"add Renata RITTER for UBO"* | ADD Renata **+ DELETE Von Michael MARTIN** en los dos bancos |
| `INC-000006313` | *"add Ould Ahmedou Voffal, Said"* | ADD Said, y el carton reveló **3 derivas preexistentes** |

---

## 1. Los tres artefactos, y cuál manda

Un pedido trae hasta tres piezas con autoridad distinta. **Ordenadas de más a menos autoridad:**

| # | Artefacto | Qué es | Autoridad |
|---|---|---|---|
| **1** | **Carton des signatures** (HEPATUS) | tarjeta de especímenes con **los PERNR** y el tramo de importe | **LA LISTA AUTORITATIVA DE PERNR** |
| 2 | **Carta TRS al banco** | REF `FIN.8/MOD/…`, cuentas afectadas, ADD/DELETE, fecha de efecto, firma del Tesorero | la autorización jurídica del cambio |
| 3 | Nota del solicitante | *"add X"* | **solo la ocasión** — nunca la especificación |

**Cláusula que hay que leer siempre** en la carta: *«This list replaces all previous signatory
lists»*. Cuando aparece, el panel del carton es **sustitutivo**, no incremental — y eso convierte
cualquier extra en SAP en sobre-autorización.

**Qué extraer de cada carta**, estructurado:
`{ref, banco, cuenta(s), fecha_efecto, deletes[], adds[], panel[persona → tramo]}`

---

## 2. Los dos gates de entrada — antes de tocar nada

```
GATE 1 · COMPLETITUD   ¿hay carton VIGENTE para CADA banco de la entidad que produce lotes BCM?
                       Bancos BCM = los de T042A del código de sociedad, NO todos los de T012K.

> ⚠️ **CORREGIDO 2026-08-26 (INC-000016338, claim 611).** **`T042A` está VACÍA en P01** —
> `RFC_READ_TABLE` sin filtro devuelve `TABLE_WITHOUT_DATA`. El universo del gate de completitud es
> **`T012K`** (bancos casa de la sociedad) corroborado con **`T042I`** (`ZLSCH`→`HBKID`). Y
> **`BNK_BATCH_HEADER` tampoco es legible** para el usuario SNC, así que la contradicción C2 **no se
> puede arbitrar leyendo**: es un LÍMITE DE LECTURA, nunca evidencia de que no haya lotes.
> *(Contradicción pendiente: `data_quality_issues` `DQ-2026-063-04` afirma que `T042A` sí se consultó
> con éxito en la sesión 63. O estaba poblada entonces y ahora no, o aquello nunca se re-verificó.)*
                       Si falta uno  ->  HALT: "INCOMPLETO: faltan cartones de <HBKID…>"
                       y NO se puede llamar deriva a ningún extra en SAP.

GATE 2 · ALINEACIÓN    ¿son IDÉNTICOS todos esos cartones entre sí?
                       Si no  ->  HALT y devolver a TRS. El grupo de responsabilidad es
                       de ENTIDAD, no de cuenta bancaria: un solo grupo cubre todos los
                       bancos, así que paneles distintos por banco no son representables.
```

En `INC-000011781` los dos cartones (Citibank Brazil y Banco do Brasil) eran idénticos — 8 firmantes
— y por eso el cambio pudo ejecutarse. **Si no lo hubieran sido, el pedido no tenía solución en SAP
y había que devolverlo.**

Matiz medido: UBO tiene dos bancos pero **solo CIT01 produce lotes BCM**; BRA01 es proceso manual.
Aun así se exigió carton de los dos, porque la autorización sí cubre ambos.

---

## 3. Mapa de nodos — a qué se añade la persona

Los grupos son objetos `RY` en `HRP1000`; la pertenencia es `HRP1001` con `RELAT=007`, `SCLAS=P`,
`SOBID=<PERNR>`. **La estructura NO es uniforme «2 por sociedad»** — hay de 1 a N nodos por
(entidad × regla), escalonados por importe solo donde hizo falta:

| Entidad | COMMIT — regla 90000004 | INICIAR/VALIDAR — regla 90000005 | Patrón |
|---|---|---|---|
| **UBO** | `50034894` ≤10K · `50036737` >10K | `50034892` ≤10K · `50034893` ≤5M | **2×2 limpio, por tramo** |
| **UIS** | `50010054` todos · `50036326` ≤10K *(0)* | `50010051` *(0)* · `50010053` *(0)* · `50036801` | tramos viejos retirados |
| **IIEP** | `50010088` todos | `50010087` | nodo único |
| **UIL** | `50037531` todos | `50037530` | nodo único |
| **UNES** | `50010052` *(0 — va por Coupa)* | `50010075/76/77/78/79` · `50032363` · `50036716` *(0)* · `50038878` | muchos tramos INI |
| *stubs* | — | `50038588` / `50038589` («Generated Rule», vacíos) | **ignorar** |

*(0)* = cero miembros activos hoy.

**Cómo se traduce el tramo del carton a nodos:**

| Lo que dice el carton | A qué nodos entra |
|---|---|
| *unlimited* / sin tramo | **todos** los nodos de tramo de **ambas** reglas |
| *≤10K only* | solo los nodos ≤10K |

**Convención de nombre medida**: *«for all transfers»* en el `STEXT` significa **sin tramo de
importe** — es el grupo vivo. Si una carta dice «añadir a X en BCM» sin especificar tramo, el destino
es el grupo *for all transfers*.

La selección de nodo por importe la resuelve **IT1218** (`HRP1218`/`HRT1218` sobre
`BNK_STR_BATCH_REL_APPR`), **no** PFAC `HRP1222`, que está vacío.

---

## 4. Lecturas previas obligatorias — todas en vivo, ninguna de pantallazo

`PA0001` está bloqueado para el usuario SNC. La identidad se arma así:

| Qué | Dónde | Por qué importa |
|---|---|---|
| Nombre | `PA0002` VORNA / NACHN | cruzar con el carton **y con el pasaporte** del PDF |
| Usuario SAP | `PA0105` SUBTY=`0001` → `USRID` | **si falta, es un PERNR fantasma** (ver trampa 1) |
| Email | `PA0105` SUBTY=`0010` → `USRID_LONG` | cruzar con el que declara la carta |
| Empleado activo | `PA0000` STAT2=`3` | una baja no puede firmar |
| Usuario vivo | `USR02` UFLAG=0, USTYP=A, **GLTGB** | Renata tenía `GLTGB=2026-09-30`: caduca |
| Pertenencia actual | `HRP1001` **todos los periodos** | los periodos ocultos esconden filas activas |
| Rol de firma | `BNK_APP` (`YS:FI:M:BCM_MON_APP______:<ENT>`) | **sin el rol no puede firmar aunque esté en el nodo** |

```bash
python Zagentexecution/quality_checks/bcm_role_gap_check.py          # rol BNK_APP por asignado
python Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py   # fantasmas + role-split + diff carton
```

**`RFC_READ_TABLE` no admite WHERE compuestos**: `IN (...)` falla con `OPTION_NOT_VALID`, y más de
~3 `AND` con `parser produced the error "AN" is not valid`. **Una condición por llamada, en bucle.**

---

## 5. Reconciliación — las cuatro salidas

Por cada par (nodo × persona):

| Situación | Acción | ¿Va en este pedido? |
|---|---|---|
| en el carton **y** activo en SAP | *keep* | — |
| en el carton **y** ausente/expirado en SAP | **ADD** | sí, **si la carta lo pide**; si no, es hueco → TRS |
| la carta dice *delete* **y** activo en SAP | **DELIMIT** | sí |
| activo en SAP **y** en ningún carton | **sobre-autorización** → DELIMIT | **NO** — se aparca para firma de TRS |

La cuarta fila es la que produce hallazgos grandes y la que **nunca** se ejecuta sin autorización
específica. En `INC-000011781` destapó a **De Sousa Carvalho**, activa con firma completa y permiso
de reverso/rechazo **desde enero de 2024 sin estar en ningún carton** — 18 meses de
sobre-autorización que nadie había pedido revisar.

---

## 6. La especificación para DBS

**Formato obligatorio — cada fila lleva las TRES identidades:**

```
PLVAR=01  OTYPE=RY  RELAT=007  ISTAT=1  SCLAS=P
BEGDA=<fecha de efecto>  ENDDA=99991231

| Op      | Regla    | RY OBJID | STEXT                             | PERNR    | Persona |
|---------|----------|----------|-----------------------------------|----------|---------|
| ADD     | 90000005 | 50034892 | UBO Validation ≤10K               | 10021811 | Ritter  |
| DELIMIT | 90000005 | 50034893 | UBO Validation ≤5M                | 10108464 | Martin  |
```

**Nunca omitir el `RY OBJID`.** Es el único identificador inequívoco: en `INC-000006313` el operador
abrió **`IIEP Validation` (50010087)** creyendo que era **`UIS Validation` (50036801)** — adyacentes
en el árbol de `OOCU_RESP` y ambos acabados en «Validation». Svein quedó habilitado para aprobar
pagos de **otra entidad**, sin carta que lo autorizara. Lo cazó el check de reconciliación el mismo
día. Regla: `feedback_bcm_spec_must_include_rule_ry_stext`.

**`BEGDA` = fecha de efecto de la carta, no la de ejecución.** En `INC-000006313` la carta decía
*«as of immediate effect»* con fecha 02/04 y DBS puso 09/04: **siete días de hueco de auditoría** en
los que Said estaba en el panel del banco y no en el enrutado de SAP.

**Un DELIMIT no borra**: pone `ENDDA` al día anterior y la fila histórica se conserva. Es correcto y
es lo que hace auditable el panel.

---

## 7. Ejecución — quién y dónde

| | |
|---|---|
| **Quién** | **DBS**, en P01, por `OOCU_RESP` |
| **El agente** | **nunca escribe P01.** Su alcance es análisis + especificación + verificación posterior por `RFC_READ_TABLE` |
| **Rol `BNK_APP`** | ticket aparte a Security. **El cambio de nodo no basta**: Renata quedó en los 4 nodos y seguía sin poder firmar |

---

## 8. Verificación posterior — obligatoria, y en este orden

1. **Releer `HRP1001`** de cada nodo tocado: la fila existe, con `BEGDA`/`ENDDA` esperados.
2. **Refrescar el Gold DB**: `extract_bcm_signatories.py`. En `INC-000006313` el conteo pasó de
   253 → **255**, +2 por Said — el delta debe cuadrar con las operaciones de la spec.
3. **Correr los tres checks**: reconciliación (fantasmas + role-split + diff carton),
   `bcm_role_gap_check.py`, `bcm_release_vs_approve.py`.
4. **Salida esperada**: `GHOST=0 · ROLE-SPLIT=0 · CARTON DIFF: MATCH=n, EXTRAS=0, MISSING=0`.

---

## 9. Las ocho trampas — cada una costó un incidente

| # | Trampa | Cómo se manifestó | Defensa |
|---|---|---|---|
| **1** | **PERNR fantasma** | `10567156` (Svein) en vez de `10067156`: existe en `PA0002`, **sin `PA0105/0001`** → sin usuario SAP → no se le puede enrutar. Silencioso desde 2025-10-04 | exigir `PA0105/0001` a todo PERNR del nodo |
| **2** | **Grupos gemelos** | `IIEP Validation` vs `UIS Validation`, adyacentes en el árbol | la spec lleva Regla + **RY OBJID** + STEXT |
| **3** | **La nota no es la carta** | *«add Renata»* mientras las cartas decían añadir **y borrar** | la carta y el carton mandan, siempre |
| **4** | **Periodos ocultos** | `OOCU_RESP` «Other period» escondía la fila activa de Martin | `HRP1001` **todos los periodos**, nunca un pantallazo |
| **5** | **Nodo ≠ permiso** | Renata en los 4 nodos y sin `BNK_APP`: no puede firmar | `bcm_role_gap_check.py` + ticket a Security |
| **6** | **Grupo de entidad, no de cuenta** | un grupo cubre **todos** los bancos de la entidad; un carton es de **un** banco | gate de completitud + gate de alineación |
| **7** | **Fecha de efecto** | carta 02/04, ejecución 09/04 → 7 días de hueco | `BEGDA` = fecha de la carta |
| **8** | **El ticket es la ocasión, no el alcance** | el barrido destapó 18 meses de sobre-autorización | reconciliar **la población**, no solo lo pedido |

---

## 10. Plantilla de respuesta al solicitante

> Confirmado en SAP BCM: **\<persona\>** añadida a **\<entidad\>** en \<n\> nodos
> (\<reglas\>), con efecto \<fecha de la carta\>, verificado por lectura directa de `HRP1001`.
> **\<Si aplica\>** Las cartas REF \<refs\> también instruyen dar de baja a **\<persona\>**; ejecutado
> / pendiente de tu confirmación.
> **\<Si aplica\>** Pendiente: el rol `BNK_APP` para \<usuario\>, solicitado a Security — **hasta que
> se conceda no puede firmar**.
> **\<Si hay deriva\>** Al reconciliar contra el carton aparecen \<n\> diferencias preexistentes no
> incluidas en esta petición: \<lista\>. No se han tocado; ¿confirmáis cómo proceder?
> Recordatorio: la AO tiene hasta **\<fecha+2 semanas\>** para confirmar que el banco registró el cambio.

---

## 11. Puerta de cierre

- [ ] Cartas y cartones leídos; gates de completitud y alineación pasados
- [ ] Verificación previa en vivo (identidad, usuario, validez, periodos, IT1218)
- [ ] Spec con Regla + RY OBJID + STEXT en **cada** fila, y `BEGDA` = fecha de la carta
- [ ] DBS ejecuta en `OOCU_RESP`
- [ ] Readback de `HRP1001` + refresco del Gold DB + los tres checks en verde
- [ ] Rol `BNK_APP` concedido — **sin esto la persona no puede firmar y el incidente no se cierra**
- [ ] Deriva preexistente registrada y comunicada a TRS, **sin actuar** sin autorización por ítem
- [ ] Respuesta enviada, con el recordatorio del plazo de dos semanas
- [ ] Incidente con registro en `incidents.json` y enlace a este procedimiento

---

## 12. Lo que sigue abierto de los dos casos

| Caso | Abierto |
|---|---|
| `INC-000011781` | rol `BNK_APP` de Renata (**bloquea el cierre**) · **Yli-Hietanen `10097358`** en el carton y en ningún nodo UBO → ADD ×4 |
| `INC-000006313` | ¿tiene UIS cuentas en otros bancos donde Stephenson y Zhang siguieran autorizados? Se les dio de baja asumiendo que el carton de Citibank Canada es el único panel de UIS — **parqueado para TRS** |

---

## 13. Por qué este documento existe

Dos incidentes del mismo proceso, y el proceso operativo no estaba escrito en ninguna parte: el
modelo sí (`bcm_signatory_change_solution_design.md`), las reglas también
(`bcm_signatory_rules.md`), pero el **runbook** no. La regla
`feedback_at_incident_close_check_for_related_domain_knowledge` nació de esto: **al resolver un
incidente hay que preguntarse qué proceso enseña y dónde vive.** Medido el 2026-08-21: 11 de 13
incidentes no tenían proceso escrito en su dominio.
