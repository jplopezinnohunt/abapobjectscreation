# EBS — el pipeline de FICHEROS: quién los recoge, de dónde, con qué variante

**Dominio:** Treasury_EBS · **Sesión:** s108 (2026-08-28) · **Origen:** INC-000013624
**Medido en vivo en P01 por RFC.** Complementa `bank_statement_ebs_architecture.md`, que
describe qué pasa DESPUÉS de que el fichero entra (formatos, reglas de contabilización,
algoritmos de compensación). Esto es lo de ANTES, y no estaba escrito en ningún sitio.

---

## Por qué existe este documento

`bank_statement_ebs_architecture.md` (s029) daba por hecha la entrada del fichero: decía
«FF_5 / JOBBATCH, 91,2 % automático» y listaba `\\hq-sapitf\SWIFTS\output\*` como
directorio. **Ninguna de las dos cosas es lo que corre hoy**, y descubrirlo costó la mitad
del tiempo de diagnosticar INC-000013624:

- El programa **no es** `RFEBKA00`. `TBTCP` con `PROGNAME LIKE 'RFEB%'` devuelve **0 filas**
  en P01: no hay ni un solo paso de job con un programa RFEB*.
- El canal principal **ya no es SWIFT**: es **Coupa**.

## El job

| | |
|---|---|
| **Nombre del job** | `EBS INTEGRATION` |
| **Programa** | `FEB_FILE_HANDLING` (estándar SAP, 156 líneas, marco SCHEDMAN) |
| **Variante** | **`EBS JOB_COUPA`** |
| **Usuario** | `JOBBATCH` · cliente 350 |
| **Periodicidad** | periódico (`PERIODIC='X'`), ~cada hora |
| **Volumen** | 349 pasos registrados; **348 corridas del 01.08 al 28.08.2026, todas `F` (terminado)** |

⚠️ **Un job en estado `F` no significa que procesara nada.** Significa que no dumpeó. En
INC-000013624 el job llevaba 11 días terminando bien sin importar ni un extracto de la
cuenta rota. El estado del job no es un indicador de salud del flujo; el indicador es
`FEBKO` — **la fecha del último extracto por cuenta**.

## Las variantes — las dos, y qué significan

`FEB_FILE_HANDLING` tiene **un solo select-option obligatorio**:

```abap
TABLES: FEB_IMP_SOURCE, ...
SELECT-OPTIONS T_SEL_OP FOR FEB_IMP_SOURCE-PATH_SOURCE OBLIGATORY.
PARAMETERS: P_KOAUSZ LIKE RFPDO1-FEBPAUSZ.   " imprimir extracto
```

O sea: **la variante no dice cuentas ni bancos — dice qué FUENTES DE FICHERO se recogen.**
Es una variante de canal, no de alcance de negocio. Por eso no hubo que tocarla al cambiar
la cuenta, y por eso tampoco protege de nada.

| Variante | Creada | Por | Lectura |
|---|---|---|---|
| `EBS JOB` | 19.12.2016 | M_SPRONK | La original. Canal SWIFT. **No la usa ningún job hoy.** |
| **`EBS JOB_COUPA`** | **21.11.2022** | **M_SPRONK** | **La que corre.** Migración del canal a Coupa, nov-2022. |

Ninguna de las dos se ha modificado nunca (`AEDAT = 00000000` en las dos).

## Las fuentes y las rutas

`FEB_IMP_SOURCE` — 2 fuentes, las dos en formato `I`:

| PATH_SOURCE | Formato | Archivo | Error |
|---|---|---|---|
| `Y_EBS_PRO` | I | `Y_EBS_ARC` | `Y_EBS_ERR` |
| `Z_EBS_PRO` | I | `Z_EBS_ARC` | `Z_EBS_ERR` |

`FEB_FILEPATH` — ruta lógica → directorio físico (**el `<SYSID>` se sustituye en ejecución**):

| Ruta lógica | Directorio |
|---|---|
| `Y_EBS_PRO` / `_ARC` / `_ERR` / `_TRA` | `\\hq-sapitf\coupa$\<SYSID>\Out\Data\EBS\` · `\Out\Archives\EBS` · `\Out\Errors\EBS` · `\Out\Transfer\EBS` |
| `Z_EBS_PRO` / `_ARC` / `_ERR` / `_TRA` | `\\hq-sapitf\SWIFT$\<SYSID>\output\ebs\` · `\archive` · `\error` · `\transfer` |

⚠️ **El emparejamiento ruta↔directorio de esta tabla se leyó fila a fila con `WHERE PATH =`,
no emparejando dos lecturas por posición.** `FEB_FILEPATH.DIRECTORY` es `CHAR(512)` y con
cualquier otro campo revienta `RFC_READ_TABLE` con `DATA_BUFFER_EXCEEDED`; la tentación es
leer `PATH` y `DIRECTORY` por separado y casarlos por orden — eso no da error, da una
respuesta segura y falsa.

> **PENDIENTE de cerrar:** cuál de los dos juegos (Y_* o Z_*) selecciona la variante
> `EBS JOB_COUPA`. El contenido de la variante no se pudo leer por RFC
> (`RS_VARIANT_CONTENTS` y `RS_VARIANT_VALUES_TECH_DATA` no son remote-enabled; `VARIS`
> devolvió `TABLE_WITHOUT_DATA`). Se resuelve en 30 segundos abriendo la variante en SE38.
> **No se afirma cuál es.**

## El resto del customizing de importación: es GENÉRICO

Esto importa porque es lo que **no** hay que tocar al dar de alta o cambiar una cuenta:

| Tabla | Filas | Contenido |
|---|---|---|
| `FEB_IMP_POST` | 1 | Claves `BUKRS`/`HBKID`/`HKTID` **en blanco** → aplica a todo. `XPOST=1`, `FEBMREGEL=1`, `FEBVALUT=X` |
| `FEB_IMP_SELOPT` | 0 | vacía |
| `FEB_IMP_TRANS` | 1 | claves en blanco → `PATH_ERROR=Y_EBS_ERR` |
| `FEB_IMP_TRANPATH` | 1 | claves en blanco (incluida `BNKACCOUNT_EXT`) → `PATH_TRANS=Y_EBS_TRA` |
| `FEB_IMP_FORMAT` | 6 | A, B, G, I, S, X |
| `FEB_IMP_STRUCT` | 1 | `A → FEBS_PAR_BAI` |

**Ninguna está parametrizada por cuenta.** La capa de fichero es ciega a la cuenta: recoge
lo que haya en el directorio y se lo pasa al importador. Toda la resolución de cuenta
ocurre después, y ahí es donde se rompe (ver abajo).

## La resolución de cuenta — las dos tablas que sí cuelgan del número de cuenta

```
fichero MT940  :25:  →  FEBKO-ABSND = "SP0000000MX7   UNO12EUR"
                                       └ clave banco ┘ └ cuenta ┘
     │
     ├─ T012K  por BANKN o por BNKN2 (cuenta alternativa)   →  banco casa + ID de cuenta
     │
     ├─ T028B  por BANKL + BANKN   →  VGTYP (grupo de formato) + BNKKO (cuenta interna)
     │
     └─ T035D  por BUKRS + DISKB   →  cuenta de mayor
```

| Tabla | Su clave | ¿Se rompe al cambiar el nº de cuenta? |
|---|---|---|
| `T012K` | BUKRS+HBKID+HKTID | No — es lo que se cambia en FI12 |
| **`T028B`** | **BANKL + KTONR** | **SÍ. Y nadie la actualiza.** ← INC-000013624 |
| `T035D` | BUKRS + DISKB | No — su clave es la clave corta, no el número |
| `TIBAN` | BANKS+BANKL+BANKN | Se añade fila nueva; la vieja queda inocua |

**`FEBKO-ABSND` es el campo que hay que mirar** para saber con qué identidad llega un
extracto — y es lo que FF67 pinta en su cabecera como «Bank Key | Account». No es
configuración: es historia. Un usuario que mira FF67 y dice «la cuenta sigue siendo la
vieja» está leyendo el último fichero importado, no la ficha del banco.

> ⚠️ **Una cuenta nueva NO aparece en FF67 hasta que llega su primer extracto — y eso no es un
> defecto.** La lista de cuentas de FF67 es **historial de extractos recibidos**, no configuración.
> Probado el 2026-08-28: ofrece el par `(SP0000000MX7, UNO10)`, que **no existe en `T012K`** —NTB01
> usa hoy `SP0000000MXL`— pero sí en `FEBKO.ABSND`, con 10 extractos cuyo último es del
> **05.03.2015**. Una lista derivada de configuración no puede producir eso.
> **Ante «la cuenta nueva no está en FF67»: no revises la ficha del banco, comprueba si ha llegado
> algún extracto.** (claim 639 · INC-000013624)

## Cómo se comprueba que un canal está vivo

```bash
python Zagentexecution/quality_checks/house_bank_ebs_wiring_check.py
```

Y a mano, la consulta que lo dice todo en una línea: **último `FEBKO-AZDAT` por
`HBKID/HKTID`**. Una cuenta cuyo último extracto sea de hace más de una semana, mientras
sus hermanas del mismo banco entran a diario, está rota — sin importar lo que digan el
estado del job ni la ficha del banco casa.

---

**Relacionados:** [bank_statement_ebs_architecture.md](bank_statement_ebs_architecture.md) ·
[house_bank_configuration.md](house_bank_configuration.md) ·
[../../incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md](../../incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md) ·
[../../configuration_retros/NTB01_rename_2026-04-08.md](../../configuration_retros/NTB01_rename_2026-04-08.md)

## Apéndice — cómo se sabe si una cuenta está CERRADA

**No hay indicador: está en el texto.** `T012T-TEXT1` de la cuenta empieza por `CLOSED`,
con guiones arbitrarios de relleno:

```
CLOSED - UNESCO HARARE - USD
CLOSED-----UNESCO YAOUNDE - XAF
CLOSED -- UNESCO SANTIAGO - CLP
CLOSED --- UNESCO ADDIS ABABA - NON RESIDENT - ETB
```

**Medido (P01, 28.08.2026): 237 de las 411 cuentas de UNES con texto en inglés llevan esa
marca.** Es una convención humana, no configuración — pero es la única forma de saberlo, y
cualquier medida sobre el parque de cuentas que no la aplique está midiendo un denominador
falso. En la primera corrida de `house_bank_ebs_wiring_check.py`, 2 de los 4 hallazgos de
"cable roto" eran cuentas cerradas hace años.

Riesgos de la convención, para tenerlos presentes:
- Es **texto libre**: nada impide escribir `FERME` o no escribir nada.
- Es **por idioma**: la marca vive en `SPRAS='E'`; el francés y el portugués pueden ir
  desincronizados (ya pasó en el retro de NTB01 de abril con los textos del banco casa).
- **Una cuenta cerrada sigue en `T012K`.** No se borra. Así que "existe" nunca significa
  "se usa".
