# Modelos de extracto — cuántos sostenemos y cuántos harían falta

**Dominio:** Treasury_EBS · **Sesión:** s108 (2026-08-28) · **Sociedad:** UNES
**Medido en vivo en P01.** Ventana 2025-2026 · Instrumento:
`Zagentexecution/quality_checks/ebs_format_consolidation.py`

---

## Qué es un «modelo de extracto»

Un extracto no se procesa en general: se procesa según un **grupo de formato**
(`T028B.VGTYP`), y cada grupo arrastra su propio juego de reglas de contabilización
(`T028G`: código externo del banco → regla + algoritmo). **Ese juego es el modelo** — lo que
cuesta mantener, lo que hay que probar cuando se toca, y lo que hay que replicar cuando entra
un banco nuevo.

**El tipo de extracto es, por tanto, un atributo de primera clase de la cuenta**, al mismo
nivel que su naturaleza: no es un detalle de configuración, es lo que determina qué se hace
con cada línea que llega.

## El reparto — 144 cuentas vivas, 133 con extracto

| Formato | Bancos | Cuentas | Extractos | Reglas | |
|---|---:|---:|---:|---:|---|
| **XRT940** | **60** | **104** | **38.822** | **130** | genérico de terreno |
| TR_TRNF | 7 | 16 | 5.495 | 20 | transferencias de tesorería |
| SOG_FR | 2 | 7 | 2.975 | 18 | Société Générale |
| SOG_FRB | 2 | 2 | 850 | 18 | Société Générale (bis) |
| SCB19_IQ | **1** | 2 | 864 | 16 | Bagdad |
| CIT21_CA | **1** | 1 | 429 | 14 | Citibank Canadá |
| CIT24_GA | **1** | 1 | 410 | 18 | Libreville |
| SOG_EUR4 | **1** | 1 | 425 | 14 | SOG BPI |
| CIT04_US | **1** | 1 | 416 | 11 | Citibank NY |
| *(sin T028B)* | 7 | 9 | 429 | — | ver abajo |

**259 reglas de contabilización mantenidas en total.**

## La oportunidad, en tres hallazgos

### ① `SOG_FR` y `SOG_FRB` son **89 % idénticos**

Dos modelos, 18 reglas cada uno, 9 cuentas entre los dos, mantenidos por separado. Es el
único candidato de consolidación que la medida sostiene por sí sola. **36 reglas donde
probablemente bastan 18.**

### ② Cinco modelos existen para **una sola cuenta** cada uno

`CIT04_US` · `CIT21_CA` · `CIT24_GA` · `SOG_EUR4` · `SCB19_IQ` (ésta con 2).
**73 reglas para 6 cuentas**: el **28 % del esfuerzo de mantenimiento para el 4,5 % de las
cuentas.** Cada uno es un modelo entero — con su prueba, su documentación y su riesgo —
sosteniendo una cuenta.

### ③ Pero **no se parecen a nada**, y eso hay que decirlo

El parecido más alto de cualquier huérfano con otro modelo es **21 %** (SCB19_IQ ↔ CIT24_GA) y
**16 %** (CIT04_US ↔ SOG_FR). Y **XRT940 tiene 0 % de parecido con todos los demás** — porque
es de otra clase: mapea los 65 códigos externos a dos reglas genéricas (`SUBC`/`SUBD`),
mientras los demás usan reglas 101/102 diferenciadas.

> **La consolidación fácil no existe.** Salvo el par SOG_FR/SOG_FRB, absorber un huérfano
> significaría *cambiar cómo se contabiliza* esa cuenta, no solo borrar una fila. Lo que la
> medida sí justifica es **preguntar por qué existen**: la hipótesis razonable es que se
> crearon por copia de un banco parecido y nunca se revisaron — que es exactamente lo que el
> procedimiento de alta prescribe hoy («copiar de una cuenta parecida»).

### La pregunta de fondo

**¿Por qué `CIT04_US` — Citibank Nueva York, la cuenta operativa principal en USD, 416
extractos al año — tiene un modelo propio de 11 reglas, mientras 60 bancos comparten uno?**
Si la respuesta es «porque su fichero es distinto», es legítimo y hay que escribirlo. Si es
«porque se hizo así», es deuda.

## La pregunta que hay que responder: mismo modelo, uso distinto

Para un modelo dado, **¿qué bancos lo usan y cuáles no, teniéndolo asignado igual?**

| Formato | Ctas | Electrónico | Mixto | Manual | Sin extracto | Bancos que NO lo procesan |
|---|---:|---:|---:|---:|---:|---|
| **XRT940** | 104 | 70 | 26 | **7** | 1 | BLN01 · BMN01 · BTE01 · CBE01 · ECO08 |
| TR_TRNF | 17 | 14 | 0 | 0 | **3** | NTB01 |
| los otros 7 formatos | 15 | 15 | 0 | 0 | 0 | — ninguno |
| *(sin modelo)* | 8 | 0 | 0 | 1 | 7 | BRA01 · BTE01 · DEU01 · DEU02 · **NTB02** · UBS02 · UNDP |

### El hueco: 11 cuentas tienen el modelo montado y no lo usan

**Siete se teclean a mano** teniendo `XRT940` asignado — el mismo modelo que **96 cuentas
procesan electrónicamente**:

| Cuenta | Canal | Extractos | Banco |
|---|---|---:|---|
| BLN01-USD01 · SDD01 | manual | 168 · 126 | Blue Nile Mashreg — Jartum |
| BMN01-CUP02 · EUR01 | manual | 63 · 49 | Banco Metropolitano — La Habana |
| BTE01-IRR02 · EUR01 | manual | 40 · 8 | Bank Tejarat — Teherán |
| ECO08-ZWG01 | manual | 10 | Ecobank — Harare |
| CBE01-ETB02 | sin extracto | 0 | Commercial Bank of Ethiopia |
| NTB01-USD04 · USD05 · USD06 | sin extracto | 0 | Northern Trust — mandatos |

**El coste en SAP es cero.** El modelo está construido, probado y corriendo para 96 cuentas: no
hay que diseñar reglas ni transportar customizing.

> ⚠️ **Lo que la medida NO dice:** tener el modelo asignado no prueba que el fichero *pueda*
> llegar. La restricción está **aguas arriba** — que el banco emita MT940 y que el fichero
> alcance el share de Coupa. Los cinco son bancos locales de contextos difíciles (Jartum, La
> Habana, Teherán, Harare, Addis Abeba) y es plausible que ahí esté el límite real. **Eso
> convierte el trabajo en una conversación de canal con el banco, no en un proyecto de
> configuración** — y esa distinción es la que hace la lista accionable en vez de una idea.

### El caso puro: mismo banco, mismo formato, comportamiento opuesto

**Northern Trust `NTB01`, formato `TR_TRNF`, seis cuentas:** `USD01/02/03` reciben extracto a
diario; `USD04/05/06` no reciben nada. Mismo banco, mismo custodio, mismo formato, misma
configuración.

**No es el banco y no es el formato: es la cuenta.** Las tres que no reciben son los mandatos
de inversión, y **mueven saldo sin ningún extracto que lo corrobore**. Ése es el hueco de
control — y la razón por la que la naturaleza de la cuenta tiene que estar declarada: es lo
único que explica por qué tres hermanas sí y tres no.

## Las 9 sin modelo asignado

| Cuenta | Extractos | |
|---|---:|---|
| **UNES/NTB02-EUR01** | **423** | **el incidente** — entra extracto y perdió su fila `T028B` |
| UNES/BTE01-USD01 | 6 | manual (FF67): no necesita `T028B` |
| BRA01-BRL01 · BRL02 · DEU01-EUR01 · DEU02-EUR01 · NTB02-EUR02 · UBS02-CHF01 · UNDP-UNDP | 0 | durmientes o sin extracto declarado |

El incidente aparece aquí desde un ángulo distinto y sin buscarlo: **una cuenta con 423
extractos al año y ningún modelo asignado.** Ésa es la firma exacta del defecto, y este
instrumento la habría detectado sin conocer el ticket.

---

**Relacionados:** [bank_account_nature_model.md](bank_account_nature_model.md) ·
[bank_statement_channels_by_company.md](bank_statement_channels_by_company.md) ·
[ebs_file_pipeline_and_jobs.md](ebs_file_pipeline_and_jobs.md) ·
[../../incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md](../../incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md)
