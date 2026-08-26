# INC-000016338 — UIL / alta de Bettina REISS en el panel de firmantes BCM

**Track**: B — ACCION OPERATIVA (que hay que hacer se sabe; hacerlo bien es el trabajo)
**Entidad**: UIL (`BUKRS=UIL`, UNESCO Institute for Lifelong Learning, Hamburgo)
**Estado**: `SPEC_READY` — pendiente de ejecucion por DBS en P01 + rol de Security
**Abierto**: 2026-08-21 (Ingrid Wettie, BFM-TRS Middle Office) · **Analizado**: 2026-08-26
**Procedimiento**: `.agents/skills/sap_bcm_signatory_maintenance/SKILL.md` (3.a ocurrencia — la primera que se ejecuta con el skill ya escrito)

---

## 1. Estado de ejecucion (lo primero, porque es Track B)

| # | Accion | Quien | Sistema | Estado |
|---|---|---|---|---|
| 1 | ADD REISS `10049633` a `50037530` + `50037531` | **DBS** | P01 `OOCU_RESP` | PENDIENTE |
| 2 | Rol `YS:FI:M:BCM_MON_APP______:UIL` a `B_REISS` | **Security** | P01 `PFCG` | PENDIENTE — **BLOQUEA EL CIERRE** |
| 3 | Readback `HRP1001` + refresco Gold DB + 3 checks | agente | P01 (lectura) | tras 1 |
| 4 | Escalado a TRS: limite ≤10K no representable | agente → TRS | — | PENDIENTE |
| 5 | Escalado a TRS: Yli-Hietanen expirado / Basoglu role-split | agente → TRS | — | PENDIENTE |

**El agente no escribe en P01.** Lectura por `RFC_READ_TABLE` sobre SNC/SSO unicamente
(`feedback_p01_readonly_absolute`, CRITICAL). D01 no es alternativa: sin estructura HR valida y
con OBJID que significan otra cosa.

---

## 2. La cadena del pedido

`Role Management Mailer Service` (2026-08-20 16:37, a Morsal Jamal, cc Bettina Reiss / Raul Valdes
Cotera / Liste.BFM-TRS-MO) -> **Ingrid Wettie** (BFM-TRS Middle Office) -> Pablo, 2026-08-21 08:02,
cc Liste.BFM-TRS-MO + Patrick Ikouna Bouangolh. Ticket SMART **INC-000016338**.

**Nota del solicitante** (= la OCASION, no la especificacion):
> *"Can you please add Bettina REISS for UIL in BCM and also add her bank limits as per letter attached?"*

---

## 3. La autoridad de registro — DOS cartas, un carton

Adjunto unico: `20260819 UIL.pdf`, 8 paginas = **dos paquetes identicos** (carta 2p + carton 1p +
pasaporte 1p).

| REF | Banco | HBKID | Cuentas nombradas en la carta |
|---|---|---|---|
| `FIN.8/MOD/10.0000003674` | DEUTSCHE BANK HAMBURG AG (Mrs Bettina Koepke, Adolphsplatz 7, 20457 Hamburg) | `DEU01` | USD `DE22 2007 0000 0023 5580 01` · EUR `DE49 ... 5580 00` · EUR `DE48 ... 5580 18` |
| `FIN.8/MOD/10.0000003675` | SOCIETE GENERALE (Mrs Aude Ginestet, Ile de France Institutionnels, 50 rue d Anjou, 75008 Paris) | `SOG05` | USD `FR76 3000 3016 7800 0501 1903 184` · EUR `FR76 3000 3016 7800 0501 1824 905` |

Ambas de **11/08/2026**, firmadas por **Anssi Yli-Hietanen, Treasurer**.

- **Clausula 1 — la instruccion operativa**: *"Name(s) to be added: Mrs Bettina REISS"*. Ninguna baja.
- **Clausula 2 — el estado resultante**: 7 firmantes, *"authorized to sign jointly two by two"*.
- **Clausula 3 — `This list replaces all previous signatory lists`** -> el panel es **SUSTITUTIVO**.
  Es lo que habilita a calificar de sobre-autorizacion cualquier extra en SAP.
- **Clausula 6/7**: solo el Tesorero negocia descubiertos y designa firmantes.

**Carton des signatures** (HEPATUS V10.6.2.0, 11/08/2026, "Code compte UIL" — **de ENTIDAD, no por
cuenta**), 7 firmantes con PERNR, con firma manuscrita de cada uno:

| PERNR | Nombre | Duty station | Limite segun la carta |
|---|---|---|---|
| `10168474` | ABDI Dereje Bune | Hamburg | sin limite |
| `10111198` | BASOGLU Ana Suzan | Hamburg | **hasta USD 10.000,00** |
| `10048024` | KEMPF Isabell | Hamburg | sin limite |
| `10049633` | **REISS Bettina** | Hamburg | **hasta USD 10.000,00** |
| `10107337` | VALDES COTERA Raul | Hamburg | sin limite |
| `10097358` | YLI-HIETANEN Anssi | Headquarters | sin limite |
| `10137641` | ZHOLDOSHALIEVA Rakhat | Hamburg | sin limite |

**Pasaporte** (paginas 4 y 8): Bettina REISS, de soltera Kuster, nacida **09.06.1970**, alemana,
pasaporte `C1V54HJJ8`, valido hasta 02.12.2028, Hamburgo.

---

## 4. GATE 1 · COMPLETITUD — **PASA**

Hay carton vigente para cada banco de UIL. `T012K WHERE BUKRS='UIL'`, leido en vivo
2026-08-26, da exactamente **2 bancos casa / 5 cuentas**, y las dos cartas los cubren cuenta a cuenta:

| HBKID | HKTID | BANKN | WAERS | Cubierto por |
|---|---|---|---|---|
| `DEU01` | `USD01` | 0023558001 | USD | carta 3674 (`DE22 ... 5580 01`) |
| `DEU01` | `EUR01` | 0023558000 | EUR | carta 3674 (`DE49 ... 5580 00`) |
| `DEU01` | `EUR02` | 0023558018 | EUR | carta 3674 (`DE48 ... 5580 18`) |
| `SOG05` | `USD01` | 00050119031 | USD | carta 3675 (`FR76 ... 1903 184`) |
| `SOG05` | `EUR01` | 00050118249 | EUR | carta 3675 (`FR76 ... 1824 905`) |

> **CORRECCION AL RUNBOOK.** El skill y `bcm_signatory_change_procedure.md:68` declaran **`T042A`**
> como universo del gate. **`T042A` esta VACIA en P01**: `RFC_READ_TABLE` sin filtro devuelve
> `TABLE_WITHOUT_DATA`. Universo usado: **`T012K`** (bancos casa) corroborado con **`T042I`**
> (determinacion de banco por metodo de pago; para UIL: `ZLSCH` N/S -> `SOG05` EUR01/USD01).
> **`BNK_BATCH_HEADER` tampoco es legible** por el usuario SNC (`TABLE_WITHOUT_DATA` sin filtro),
> asi que la contradiccion C2 no se puede arbitrar por lectura: **no se puede afirmar cuales de los
> 2 bancos generan de verdad lotes BCM**. Es un limite de lectura, NO un "UIL no produce lotes".

## 5. GATE 2 · ALINEACION — **PASA**

Las dos cartas listan **el mismo panel de 7 con los mismos limites**, y el carton es uno solo, de
entidad. El grupo RY es de nivel entidad y cubre todos los bancos: la regla **es representable**
en cuanto a QUIEN. (En cuanto a CUANTO, no — ver seccion 8.)

---

## 6. Lectura previa en vivo (paso 6) — 2026-08-26, P01

Los 7 del carton, `PA0002` + `PA0105` + `PA0000` + `USR02`:

| PERNR | PA0002 | UNAME (`PA0105/0001`) | Email (`/0010`) | `PA0000 STAT2` | `USR02` |
|---|---|---|---|---|---|
| `10049633` | Bettina REISS | `B_REISS` | B.REISS@UNESCO.ORG | 3 activo (desde 20260701) | UFLAG=0 · USTYP=A · hasta 20271231 · **nunca ha entrado (TRDAT=00000000)** |
| `10097358` | Anssi YLI-HIETANEN | `A_YLI-HIETAN` | A.YLI-HIETANEN@... | 3 activo | UFLAG=0 · hasta 20271011 · ult. logon 20260723 |
| `10111198` | Ana Suzan BASOGLU | `A_BASOGLU` | A.BASOGLU@... | 3 activo | UFLAG=0 · hasta 20270323 · ult. logon 20260806 |
| `10168474` | Dereje Bune ABDI | `DB_ABDI` | DB.ABDI@... | 3 activo | UFLAG=0 · hasta 20280630 · ult. logon 20260826 |
| `10048024` | Isabell KEMPF | `I_KEMPF` | I.KEMPF@... | 3 activo | UFLAG=0 · hasta 20271231 · ult. logon 20260826 |
| `10107337` | Raul VALDES COTERA | `R_VALDES-COT` | R.VALDES-COTERA@... | 3 activo | UFLAG=0 · hasta 20270915 · ult. logon 20260825 |
| `10137641` | Rakhat ZHOLDOSHALIEVA | `R_ZHOLDOSHAL` | R.ZHOLDOSHALIEVA@... | 3 activo | UFLAG=0 · hasta 20270114 · ult. logon 20260826 |

- **PERNR fantasma (T1): 0.** Los 7 tienen `PA0105/0001` poblado.
- **Cruce con el pasaporte**: `PA0002.GBDAT = 19700609` vs pasaporte `09.06.1970` -> **coincide**.
  Identidad de la persona a dar de alta verificada contra el documento, no contra el nombre.

---

## 7. Reconciliacion — carton (7) vs `HRP1001` en vivo, 2026-08-26

Nodos de UIL (patron "nodo unico", sin tramo de importe):

| Regla | RY OBJID | STEXT |
|---|---|---|
| 90000005 (BNK_INI / validar) | `50037530` | UIL Validation |
| 90000004 (BNK_COM / firmar) | `50037531` | UIL signatures for all transfers |

| PERNR | Persona | Carton | `50037530` INI | `50037531` COM | Rol `BNK_APP` | Accion |
|---|---|---|---|---|---|---|
| `10168474` | ABDI | si | ACTIVO 20240807 | ACTIVO 20240807 | `...:UIL` OK | keep |
| `10048024` | KEMPF | si | ACTIVO 20240125 | ACTIVO 20240125 | `...:UIL` OK | keep |
| `10107337` | VALDES COTERA | si | ACTIVO 20230615 | ACTIVO 20230615 | `...:UIL` OK | keep |
| `10137641` | ZHOLDOSHALIEVA | si | ACTIVO 20230615 | ACTIVO 20230615 | `...:UIL` OK | keep |
| `10111198` | BASOGLU | si (<=10K) | ACTIVO 20240927 | **NUNCA** | `...:UIL` OK | **role-split -> TRS** |
| `10097358` | YLI-HIETANEN | si | **EXPIRADO 20240126** | **EXPIRADO 20240126** | `...:ALL` OK | **hueco -> TRS** |
| `10049633` | **REISS** | si (<=10K) | **AUSENTE** | **AUSENTE** | **NINGUNO** | **ADD x2 + rol** |

**Sobre-autorizacion: NINGUNA.** Todo activo en SAP esta en el carton — primera entidad limpia por
ese lado, pese a que la clausula sustitutiva habilitaba a buscarla.

---

## 8. HALLAZGO ESTRUCTURAL — el limite de USD 10.000 NO es representable en UIL

La nota pide *"add her bank limits as per letter attached"*. **No se puede hacer hoy.**

`HRP1218` -> `HRT1218`, leido en vivo (la seleccion de nodo vive en IT1218, no en `HRP1222`, que
esta vacia):

| Nodo | `ZBUKR` | `MAXPAYAMT_RULECURR` | `RULE_ID` |
|---|---|---|---|
| `50037530` UIL Validation | UIL | **0,00 -> 9.999.999.999,00** | `UIL_AP_ST` |
| `50037531` UIL signatures | UIL | **0,00 -> 50.000.000,00** | — |
| *(referencia)* `50034892` UBO Validation up to 10.000 | UBO | 0,00 -> **10.000,00** | `UBO_AP_MAX` |

**UIL no tiene banda de importe.** Meter a Reiss en esos nodos le concede firma **efectivamente
ilimitada** dentro de SAP, cuando la carta la limita a **USD 10.000**.

**Y no es nuevo: ya esta vivo.** `BASOGLU 10111198` esta activa en `50037530` **sin limite desde
2024-09-27** y la carta vigente la capa en 10.000. Ejecutar el ADD de Reiss **duplica** una desviacion
que ya existe; no la crea.

**Lo que haria falta**: crear nodos con banda <=10K para UIL (como los de UBO) y repartir el panel.
Eso es *Approval Procedure customizing* que regenera la condicion IT1218 — y **como se MODIFICA el
infotipo 1218 no esta documentado en ninguna fuente del corpus** (hueco 3 del skill). Requiere
decision de TRS + procedimiento de DBS. **Se escala; no se improvisa.**

---

## 9. Los otros dos hallazgos del barrido (regla dura 2: el ticket es la ocasion, no el alcance)

**9.1 — El Tesorero que FIRMA la carta no puede aprobar pagos de UIL.**
`YLI-HIETANEN 10097358` esta en el carton y **expiro en SAP el 2024-01-26 en los dos nodos**:
**31 meses**. Tiene el rol `YS:FI:M:BCM_MON_APP______:ALL`, asi que el permiso esta — falta la
pertenencia al nodo.
**Es el MISMO hallazgo abierto en UBO** (`INC-000011781`: *"Yli-Hietanen 10097358 esta en el carton
y en ningun nodo UBO -> ADD x4"*). Dos entidades, el mismo PERNR, el mismo defecto -> **patron, no
caso**. Candidato inmediato a check recurrente: *"esta cada firmante del carton activo en el nodo?"*

**9.2 — BASOGLU solo valida, no firma.** Activa en `50037530`, nunca en `50037531`. El carton dice
*"jointly two by two"* **sin distinguir rol**, asi que el diff por nombres no lo resuelve (trampa T9,
misma familia que `uq_uis_bcm_role_split_consistency`). Puede ser intencionado (junior que valida y
no compromete) o accidente de mantenimiento. **Pregunta para TRS.**

---

## 10. LA ESPECIFICACION PARA DBS

```
Sistema : P01          Transaccion : OOCU_RESP
Constantes de toda fila HRP1001:
   PLVAR=01   OTYPE=RY   RELAT=007   ISTAT=1   SCLAS=P
   BEGDA=20260811   ENDDA=99991231
BEGDA = 11/08/2026 = FECHA DE LA CARTA ("as of immediate effect"), NO la fecha de ejecucion.
```

### Pedido actual — AUTORIZADO por las cartas 3674 y 3675

| Op | Regla | RY OBJID | STEXT | PERNR | Persona | UNAME |
|---|---|---|---|---|---|---|
| **ADD** | 90000005 | `50037530` | UIL Validation | `10049633` | REISS Bettina | `B_REISS` |
| **ADD** | 90000004 | `50037531` | UIL signatures for all transfers | `10049633` | REISS Bettina | `B_REISS` |

**Bajas: NINGUNA.** Las cartas no instruyen ninguna, y el barrido no encontro sobre-autorizacion.

**A declarar por escrito al ejecutar**: estos nodos **no llevan banda de importe**, de modo que
la alta concede firma sin limite dentro de SAP mientras la carta limita a Reiss a USD 10.000. Es
una desviacion **conocida, declarada y ya existente** (Basoglu), abierta con TRS en la seccion 8.

### Ticket separado a Security — BLOQUEA EL CIERRE

| Usuario | Rol | Nivel org |
|---|---|---|
| `B_REISS` | `YS:FI:M:BCM_MON_APP______:UIL` | `$BUKRS = UIL` |

**Todo cambio de firmante son DOS acciones**: el nodo (`OOCU_RESP`/DBS) **y** el rol (`PFCG`/Security).
Estar en el nodo NO habilita a firmar (trampa T5). Es lo que dejo `INC-000011781` sin cerrar.

### Retenido para firma de TRS — NO ejecutar sin autorizacion por item

| Op propuesta | Regla | RY OBJID | PERNR | Persona | Motivo |
|---|---|---|---|---|---|
| ADD | 90000005 | `50037530` | `10097358` | YLI-HIETANEN | en el carton, expirado desde 20240126 |
| ADD | 90000004 | `50037531` | `10097358` | YLI-HIETANEN | idem |
| ADD | 90000004 | `50037531` | `10111198` | BASOGLU | en el carton, solo valida; split intencionado? |
| — | — | — | — | limites <=10K | crear nodos de banda para UIL (seccion 8) |

---

## 11. Verificacion posterior (obligatoria, en este orden)

1. Releer `HRP1001` de `50037530` y `50037531`, **todos los periodos** — la fila de Reiss existe con
   `BEGDA=20260811 ENDDA=99991231`. (`OOCU_RESP` consolida periodos en pantalla: nunca concluir de
   un pantallazo — trampa T4.)
2. `python Zagentexecution/mcp-backend-server-python/extract_bcm_signatories.py`
   -> el conteo debe pasar de **263 a 265** (+2, exactamente las 2 operaciones de la spec).
3. Los tres checks:
   - `python Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py`
   - `python Zagentexecution/quality_checks/bcm_role_gap_check.py`
   - `python Zagentexecution/quality_checks/bcm_release_vs_approve.py`
   **Esperado**: `GHOST=0` · UIL sin hueco de rol · `CARTON DIFF UIL: MATCH=7, EXTRAS=0, MISSING=0`
   (MISSING solo llega a 0 cuando TRS autorice ademas los ADD de Yli-Hietanen).
4. `python Zagentexecution/quality_checks/incident_record_coverage_check.py` -> exit 0.

## 12. Plazo del solicitante

El correo del Role Management recuerda que, **en dos semanas desde 2026-08-20**, el AO de la entidad
(Morsal Jamal, UIL) debe obtener del banco confirmacion escrita de la lista de firmantes **incluidos
los limites** y notificar a ADM/FIN/TRS cualquier discrepancia. -> **vence 2026-09-03.**
Ahi es donde el hueco de la seccion 8 se hara visible desde el lado del banco.

## 13. Datos archivados

- `Zagentexecution/quality_checks/cartons/uil_deutschebank_hamburg_20260811.txt`
- `Zagentexecution/quality_checks/cartons/uil_societegenerale_20260811.txt`
- `Zagentexecution/quality_checks/cartons/uil_letters_cartons_20260811_INC-000016338.pdf`

(Antes de este caso el archivo tenia **un solo carton**, el de UIS. Los dos de UBO se leyeron en
`INC-000011781` y nunca se archivaron — hueco 8 del skill, sigue abierto.)
