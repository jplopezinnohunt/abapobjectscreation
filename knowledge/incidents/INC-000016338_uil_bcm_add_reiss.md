# INC-000016338 — UIL / alta de Bettina REISS en el panel de firmantes BCM

**Track**: B — ACCION OPERATIVA
**Entidad**: UIL (`BUKRS=UIL`, UNESCO Institute for Lifelong Learning, Hamburgo)
**Estado**: `EXECUTED_VERIFIED` — configuracion completa y **verificada por simulacion**.
Un unico pendiente bloqueante: el rol `BNK_APP` de `B_REISS` (Security).
**Abierto**: 2026-08-21 (Ingrid Wettie, BFM-TRS Middle Office) · **Ejecutado y verificado**: 2026-08-26
**Procedimiento**: `.agents/skills/sap_bcm_signatory_maintenance/SKILL.md` — 3.a ocurrencia, la primera con el skill escrito
**Mecanismo**: [bcm_amount_band_mechanism.md](../domains/Treasury/bcm_amount_band_mechanism.md) — nacio de este caso

---

## 0. BRIEF — 60 segundos

**Que pedian.** Anadir a Bettina REISS al panel de firmantes de UIL "y sus limites bancarios", segun dos
cartas del Tesorero de 11/08/2026 (Deutsche Bank Hamburg + Societe Generale, panel identico de 7).

**Que se hizo.** Se anadio a REISS **y** se construyo el tramo de ≤10.000 en **las dos** reglas — nodos
nuevos `50039526` (validar) y `50039525` (firmar), con REISS y BASOGLU. Los nodos de siempre se dejaron
arrancando en 0,00 con los cuatro firmantes sin tope, **a proposito**.

**Por que es correcto.** `Simulate rule resolution`: un pago de **10.000 devuelve 6 aprobadores** y uno de
**10.001 devuelve 4**. La determinacion **suma** los paneles de los nodos que encajan, asi que los cuatro
cubren todo el rango y las dos limitadas solo su tramo. Es literalmente lo que autoriza la carta.

**Lo que el ticket NO pedia y aparecio.** (1) La nota decia *"her limits"* en singular y las cartas capan a
**DOS**: BASOGLU llevaba **sin tope desde 2024-09-27**. (2) El **Tesorero que firma las cartas**
(`YLI-HIETANEN 10097358`) esta en el carton y **expirado en SAP desde 2024-01-26** — 31 meses, y **lo mismo
en UBO**. (3) Se **borraron** 3 filas de `HRP1001` en vez de delimitarlas, destruyendo la historia de
BASOGLU.

**Que bloquea el cierre.** `B_REISS` **no tiene el rol `BNK_APP`**: esta en los dos nodos y no puede firmar.
Es el mismo bloqueo que deja `INC-000011781` abierto desde junio.

**Que decide TRS.** Yli-Hietanen · la **moneda** del umbral (carta en USD, sociedad en EUR) · las
transferencias entre cuentas propias, que la carta declara **sin tope para todos** · que BASOGLU ahora
tambien firma.

**Fecha limite.** **2026-09-03** — el AO de UIL debe traer del banco la confirmacion escrita de la lista
**con los limites**.

**Visual:** [companions/bcm_amount_bands_uil.html](../../companions/bcm_amount_bands_uil.html) ·
**Mecanismo:** [bcm_amount_band_mechanism.md](../domains/Treasury/bcm_amount_band_mechanism.md) ·
**Claims:** 608–613.

---

## 1. Estado de ejecucion

| # | Accion | Quien | Estado |
|---|---|---|---|
| 1 | ADD REISS `10049633` a los nodos de UIL | DBS, P01 `OOCU_RESP` | ✅ 2026-08-26 |
| 2 | Crear nodos de tramo ≤10.000 en **las dos** reglas (`50039525`, `50039526`) | DBS, P01 | ✅ 2026-08-26 |
| 3 | Mover REISS y BASOGLU a los nodos de tramo | DBS, P01 | ✅ 2026-08-26 |
| 4 | **Verificar por `Simulate rule resolution`** | agente | ✅ 6 agentes a 10.000 · 4 a 10.001 |
| 5 | Readback `HRP1001`/`HRT1218` + refresco Gold + 3 checks | agente | ✅ ghost 0 · exit 0 |
| 6 | **Rol `YS:FI:M:BCM_MON_APP______:UIL` para `B_REISS`** | **Security** | ⛔ **PENDIENTE — bloquea el cierre** |
| 7 | Escalado a TRS: Yli-Hietanen · moneda del umbral · Basoglu ahora firma | agente → TRS | ⏳ pendiente |

**El agente no escribe en P01** (`feedback_p01_readonly_absolute`, CRITICAL). Lectura por
`RFC_READ_TABLE`/SNC. **Ninguno de estos cambios genera transporte**: se mantienen en P01 en linea
(claim 611).

---

## 2. La cadena del pedido

`Role Management Mailer Service` (2026-08-20, a Morsal Jamal, cc Bettina Reiss / Raul Valdes Cotera /
Liste.BFM-TRS-MO) → **Ingrid Wettie** (BFM-TRS Middle Office) → Pablo, 2026-08-21. Ticket SMART
**INC-000016338**.

> *"Can you please add Bettina REISS for UIL in BCM and also add her bank limits as per letter attached?"*

**La nota dice "her" — en singular. Las cartas capan a DOS personas.** Ejecutar la nota habria dejado
a BASOGLU sin tope, como llevaba desde 2024. Es la regla dura 1 en su version mas callada: la nota no
omitio una baja, omitio **a la segunda persona afectada por la misma condicion**.

---

## 3. La autoridad de registro — DOS cartas identicas, un carton

Adjunto unico `20260819 UIL.pdf`, 8 paginas = dos paquetes identicos (carta 2p + carton + pasaporte).

| REF | Banco | HBKID | Cuentas |
|---|---|---|---|
| `FIN.8/MOD/10.0000003674` | DEUTSCHE BANK HAMBURG AG | `DEU01` | USD `DE22…5580 01` · EUR `DE49…5580 00` · EUR `DE48…5580 18` |
| `FIN.8/MOD/10.0000003675` | SOCIETE GENERALE Paris | `SOG05` | USD `FR76…1903 184` · EUR `FR76…1824 905` |

Ambas de **11/08/2026**, firmadas por **Anssi Yli-Hietanen, Treasurer**. Verificado por segunda
lectura: **identicas en personas, orden y limites**. Solo cambian destinatario, REF, banco y cuentas.

- **Clausula 1**: *"Name(s) to be added: Mrs Bettina REISS"*. Ninguna baja.
- **Clausula 2**: 7 firmantes, *"authorized to sign jointly two by two"*.
- **Clausula 3**: *"This list replaces all previous signatory lists"* → panel **SUSTITUTIVO**.
- **Y una linea que casi se pasa por alto**: *"All listed signatories above are authorised to transfer
  **unlimited amount** between UNESCO UIL's bank accounts recorded in your books."* → **el tope de
  10.000 es solo para pagos que SALEN**; entre cuentas propias de UIL nadie tiene tope. SAP sabe
  expresar eso por `RULE_ID` (UNES tiene `50010079` "UNESCO bank to bank transfers"), pero **UIL tiene
  un unico `RULE_ID`**, asi que hoy esa distincion no esta representada. Queda como pregunta a TRS.

**Carton** (HEPATUS, 11/08/2026, "Code compte UIL" — de ENTIDAD, no por cuenta), 7 firmantes:

| PERNR | Nombre | Duty station | Limite |
|---|---|---|---|
| `10168474` | ABDI Dereje Bune | Hamburg | sin limite |
| `10111198` | BASOGLU Ana Suzan | Hamburg | **≤ USD 10.000** |
| `10048024` | KEMPF Isabell | Hamburg | sin limite |
| `10049633` | **REISS Bettina** | Hamburg | **≤ USD 10.000** |
| `10107337` | VALDES COTERA Raul | Hamburg | sin limite |
| `10097358` | YLI-HIETANEN Anssi | Headquarters | sin limite |
| `10137641` | ZHOLDOSHALIEVA Rakhat | Hamburg | sin limite |

**Pasaporte**: Bettina REISS, de soltera Kuster, **09.06.1970**, alemana, `C1V54HJJ8`, hasta 02.12.2028.

---

## 4. Los dos gates — PASAN

**GATE 1 · COMPLETITUD.** `T012K WHERE BUKRS='UIL'` en vivo: exactamente **2 bancos casa / 5 cuentas**
(`DEU01` USD01+EUR01+EUR02, `SOG05` USD01+EUR01). Las dos cartas los cubren **cuenta a cuenta**.

> **CORRECCION AL RUNBOOK.** El gate declara **`T042A`** como universo y **`T042A` esta VACIA en P01**
> (`TABLE_WITHOUT_DATA` sin filtro). Universo usado: `T012K` + `T042I`. **`BNK_BATCH_HEADER` tampoco
> es legible** por el usuario SNC, asi que la contradiccion C2 no se puede arbitrar leyendo: es un
> LIMITE DE LECTURA, no un "UIL no produce lotes".

**GATE 2 · ALINEACION.** Las dos cartas listan el mismo panel de 7 con los mismos limites; un solo
carton de entidad. Representable en un grupo RY.

---

## 5. Identidad en vivo (paso 6) — limpia

Los 7 con `PA0002` + `PA0105/0001` + `PA0000 STAT2=3` + `USR02 UFLAG=0/USTYP=A`, ninguno caducado.
**Ghost PERNR: 0.** **`PA0002.GBDAT = 19700609` cuadra con el pasaporte** — identidad verificada
contra el documento, no contra el nombre.

`B_REISS`: valida hasta 20271231, **nunca ha entrado al sistema** (`TRDAT = 00000000`) → necesitara
logon inicial ademas del rol.

---

## 6. La configuracion final, y por que es correcta

| Regla | Nodo | Banda | Miembros |
|---|---|---|---|
| **90000005 VALIDAR** | `50037530` UIL Validation | **0,00 → 9.999.999.999,00** | Kempf · Valdes Cotera · Zholdoshalieva · Abdi |
| **90000005 VALIDAR** | `50039526` UIL Validation up to 10000 | 0,00 → 10.000,00 | **Reiss · Basoglu** |
| **90000004 FIRMAR** | `50037531` UIL signatures for all transfers | **0,00 → 50.000.000,00** | los mismos cuatro |
| **90000004 FIRMAR** | `50039525` UIL signatures up to 10000 | 0,00 → 10.000,00 | **Reiss · Basoglu** |

**El nodo alto arranca en 0,00 a proposito.** Es lo que mantiene a los cuatro habilitados para todo el
rango; el nodo bajo anade a las dos limitadas **solo** su tramo.

### La verificacion que lo cierra — `Simulate rule resolution`

Regla 90000005, `ZBUKR=UIL`, `RULE_ID=UIL_AP_ST`, key date 26.08.2026:

| `M.PymtAmt(rcur)` | Agentes | Lectura |
|---|---|---|
| **10.000,00** | **6** — A_BASOGLU, B_REISS, DB_ABDI, I_KEMPF, R_VALDES-COT, R_ZHOLDOSHAL | los dos nodos encajan y **se SUMAN** |
| **10.001,00** | **4** — 10048024, 10107337, 10137641, 10168474 | solo el nodo alto |

**Es exactamente lo que autoriza la carta.** Y deja medidas dos cosas que el corpus no sabia:
**la determinacion devuelve la UNION** de los nodos que encajan (con `Priority` vacia,
`RH_GET_ACTORS` suma todas las responsabilidades), y **el borde es inclusivo** — 10.000,00 abajo,
10.001,00 arriba. Claim **612**.

> **Un error que la simulacion evito.** El analisis de este mismo incidente sostuvo durante unas horas
> que el solape era un defecto y que habia que subir el suelo del nodo alto a 10.000. **Habria quitado
> a los cuatro sin tope los pagos por debajo de 10.000 — autorizacion que su carta SI les da.** No lo
> corrigio un razonamiento mejor: lo corrigio una simulacion de 30 segundos que no escribe nada.
> Claims 609 y 610 quedan `PARTIALLY_SUPERSEDED`.

---

## 7. Reconciliacion carton vs SAP

| PERNR | Persona | Carton | Donde queda | Rol `BNK_APP` |
|---|---|---|---|---|
| `10168474` ABDI | sin limite | ✅ | nodo alto (cubre todo) | `:UIL` ✔ |
| `10048024` KEMPF | sin limite | ✅ | nodo alto | `:UIL` ✔ |
| `10107337` VALDES COTERA | sin limite | ✅ | nodo alto | `:UIL` ✔ |
| `10137641` ZHOLDOSHALIEVA | sin limite | ✅ | nodo alto | `:UIL` ✔ |
| `10111198` BASOGLU | ≤10K | ✅ | nodo bajo, **y ahora tambien FIRMA** | `:UIL` ✔ |
| `10049633` **REISS** | ≤10K | ✅ | nodo bajo | ⛔ **NINGUNO** |
| `10097358` YLI-HIETANEN | sin limite | ✅ | **en ningun nodo — expirado 2024-01-26** | `:ALL` ✔ |

**Sobre-autorizacion: NINGUNA.** Nadie activo en SAP esta fuera del carton.

---

## 8. Lo que el barrido encontro y nadie habia pedido

**8.1 — El tope de la carta afecta a DOS personas, y una llevaba dos anos sin tope.**
BASOGLU `10111198` estaba activa en el nodo sin tramo **desde 2024-09-27**, con cartas que ya la
capaban. La nota del correo solo hablaba de Reiss. Resuelto en este mismo cambio.

**8.2 — El Tesorero que FIRMA las cartas no puede aprobar pagos de UIL.**
`YLI-HIETANEN 10097358` esta en el carton y **expiro en SAP el 2024-01-26 en los dos nodos: 31 meses**.
Tiene el rol `:ALL`, asi que solo falta la pertenencia. **Y esta igual en UBO** (abierto en
`INC-000011781` desde junio). Dos entidades, un PERNR, un defecto → **patron, no caso**.
Retenido: nadie lo pidio y no se toca un panel sin autorizacion firmada.

**8.3 — BASOGLU ahora tambien FIRMA.** Antes solo validaba (nunca estuvo en 90000004). Al entrar en
`50039525` gana firma que no tenia. Es defendible —el carton dice *"jointly two by two"* sin
distinguir rol— pero **es una ampliacion y debe constar**, no descubrirse despues.

**8.4 — DEFECTO DE PROCESO: se BORRARON filas de `HRP1001` en vez de delimitarlas.**
`50037530` paso de 10 filas a 8 y `50037531` de 9 a 8. Faltan **3**: las dos de REISS de hoy y **la de
BASOGLU con `BEGDA=20240927`**. Cuadra con el conteo del Gold (269 esperadas → **266** reales).
Viola la regla dura: *"nunca borrar una fila de `HRP1001`; una baja se hace delimitando el `ENDDA`,
la historia hace falta para auditoria y forense de doble control"*.
**Consecuencia**: el rastro EN SAP de los ~23 meses de Basoglu sin tope **ya no existe**. El hecho SI
esta preservado — en el Gold anterior, en el backup `p01_gold_20260826_1555.db` y en este documento —
pero eso es nuestro brain, no el sistema. **Accion**: nota de proceso a DBS; no se intenta recrear la
fila (fabricar historia es peor que perderla).

---

## 9. Pendiente

**BLOQUEANTE:** rol `YS:FI:M:BCM_MON_APP______:UIL` para `B_REISS` + primer logon. El check lo
detecta solo:
```
per-node gaps:
  50039525 UIL 90000004 UIL signatures up to 10000 -> B_REISS
  50039526 UIL 90000005 UIL Validation up to 10000 -> B_REISS
```
**Y el escenario feo**: para un pago de 500, los elegibles son Reiss y Basoglu (mas los 4 por union);
si la union fallara alguna vez, quedaria **Basoglu sola** y el doble control no se satisface.

**A TRS:**
1. **Yli-Hietanen** — ¿autoriza el ADD ×2? (y ×4 en UBO, abierto desde junio).
2. **La moneda del umbral.** La carta dice **USD** 10.000; UIL es sociedad **EUR** y el campo es
   `MAXPAYAMT_RULECURR` (*rule currency*). Si la moneda de la regla no es USD, **el umbral configurado
   no es el de la carta**. UBO tiene el mismo patron (sociedad BRL, texto "USD10.000") → posible
   problema de toda la instalacion.
3. **Transferencias entre cuentas propias.** La carta las declara **sin tope para todos**; UIL no lo
   distingue (un solo `RULE_ID`). ¿Se modela como UNES (`50010079`) o se acepta?
4. **BASOGLU ahora firma** — confirmar que es lo querido.

**Plazo del AO**: **2026-09-03**. Morsal Jamal debe obtener del banco confirmacion escrita de la lista
**incluidos los limites**.

---

## 10. Lo que este caso deja para el modelo

1. **Simular es mas barato que razonar.** 30 segundos de `Simulate rule resolution` refutaron un
   analisis de horas y evitaron un cambio que habria quitado autorizacion a cuatro personas.
2. **La determinacion devuelve la UNION** y el borde de banda es **inclusivo** (claim 612).
3. **Hay dos patrones validos de tramo** conviviendo — UBO disjunto, UIL solapado — y ninguno es un
   error; lo peligroso es que convivan sin constancia.
4. **El nombre del nodo miente en el patron de UIL**: *"up to 10000"* con 2 personas cuando pueden
   seis. Se arregla renombrando a `LIMITED to 10.000`.
5. **`T042A` esta vacia en P01** — el gate 1 del runbook apunta a una tabla que no existe aqui.
6. **El check NO era ciego — le faltaba el INPUT.** Este documento afirmo que la reconciliacion
   era ASIMETRICA. **Falso**: `bcm_signatory_reconciliation_check.py:171-172` calcula las dos
   direcciones (`extras = sap - carton`, `missing = carton - sap`) y sale con codigo 1 en ambas.
   Corrido el 2026-08-26 con `--entity UIL --carton uil_deutschebank_hamburg_20260811.txt`
   devolvio **`MISSING (1): 10097358 (not active in any SAP UIL group)`, exit 1** — caza a
   Yli-Hietanen sin ayuda. La causa real de sus 31 meses invisibles es que **`--carton` es
   OPCIONAL y no habia cartones archivados**: el repo tenia UNO, el de UIS. **El control existia
   y funcionaba; faltaba su input y faltaba que fuera obligatorio.**
7. **El `BEGDA` fue a la fecha de ejecucion y no a la de la carta** — 15 dias de hueco, 2.a ocurrencia
   tras los 7 de `INC-000006313`. A la segunda toca gate.
8. **Se borro donde habia que delimitar** (8.4) — primera vez medida.
9. **El patron de tramos de UIL es una DECISION, no una desviacion** (claim 613). Los dos patrones
   son validos; se eligio el que hace directamente legible *quien esta capado*, que es la pregunta
   del cartón. Depende de que la determinacion devuelva la UNION — verificado.


## 11. Datos archivados

- `Zagentexecution/quality_checks/cartons/uil_deutschebank_hamburg_20260811.txt`
- `Zagentexecution/quality_checks/cartons/uil_societegenerale_20260811.txt`
- `.../uil_letters_cartons_20260811_INC-000016338.pdf` (**local, fuera de git**: lleva pasaporte)
- Gold DB `bcm_signatory_assignment` refrescado 2026-08-26 → **266 filas, 26 grupos**
