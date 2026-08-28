# INC-000013624 — El extracto electrónico de NTB02/EUR01 dejó de entrar al cambiar el número de cuenta

**Estado:** SAP COMPLETO (T012K + TIBAN + T028B verificados en P01) — ESCALADO AGUAS ARRIBA: el fichero no llega
**Sociedad:** UNES · **Banco casa:** NTB02-EUR01 (NORTHERN TRUST — UNESCO ASHI — EUR)
**Ticket:** INC-000013624 · **Sesión:** s108 (2026-08-28)
**Solicitante:** Ingrid Wettie (BFM/MO) vía Baizid Gazi (BFM/TRS) → Anssi Yli-Hietanen → DBS
**Dominio:** Treasury_EBS · secundarios: Payment_BCM, Integration, Master_Data_Governance

---

## 1. Qué se pidió y qué se hizo

Petición del 08.07.2026, ejecutada el 17.08.2026:

| Campo | Antes | Después |
|---|---|---|
| Número de cuenta | 11939389 | **18747647** |
| IBAN | GB54CNOR23286311939389 | **GB42CNOR23286318747647** |
| Cuenta alternativa | UNO12EUR | **UNO18EUR** |

**Los tres cambios están hechos y verificados en vivo en P01** (lectura RFC, 2026-08-28):

```
T012K  UNES | NTB02 | EUR01 | BANKN=18747647 | BNKN2=UNO18EUR | EUR | HKONT=0001095012
TIBAN  GB | SP0000000MX7 | 18747647 | GB42CNOR23286318747647 | VALID_FROM=20260817
```

No queda ni una fila de T012K en todo el paisaje con la cuenta vieja. El cambio pedido
se hizo bien y completo. **Eso no es lo que estaba roto.**

## 2. El síntoma, y por qué la captura de FF67 despista

Ingrid manda una captura de **FF67** donde el encabezado dice `Account UNO12EUR` y los
últimos extractos son el 2997 del 14.08.2026 y el 2981 del 23.07.2026, y concluye que
«la cuenta sigue siendo UNO12EUR».

Lo que se ve en FF67 **no es la configuración**: es el campo `FEBKO-ABSND`, la
identificación del REMITENTE tal como venía en el fichero que se importó. Medido:

```
FEBKO KUKEY=00767493  AZNUM=02997  AZDAT=20260814  ASTAT=8  EUSER=JOBBATCH
      ABSND = "SP0000000MX7   UNO12EUR"      <-- lo que trajo el FICHERO
      KTONR = 11939389                        <-- la cuenta con la que se resolvió
      VGTYP = TR_TRNF   HKONT = 0001095012
```

O sea: FF67 muestra el pasado, no el presente. La captura confirma el síntoma —
**no entra nada nuevo** — pero no señala la causa.

## 3. El hecho duro: la fecha en que se paró

| Cuenta | Clave de banco | ABSND | Extractos | Último |
|---|---|---|---|---|
| NTB01/USD01 | SP0000000MXL | `UNO10USD` | 2.995 | **27.08.2026** |
| NTB01/USD02 | SP0000000MXL | `UNO11USD` | 2.995 | **27.08.2026** |
| NTB01/USD03 | SP0000000MXL | `UNO12USD` | 2.240 | **27.08.2026** |
| **NTB02/EUR01** | **SP0000000MX7** | **`UNO12EUR`** | **2.233** | **14.08.2026** ⛔ |

- Último extracto importado: **estadillo 2997, fecha 14.08, importado el 15.08**.
- El cambio se hizo el **17.08**.
- Desde el 17.08 han entrado **1.046 extractos** en UNES de todos los demás bancos, y
  **cero** de NTB02.
- **Jamás ha entrado un extracto con `UNO18EUR`.**

El resto de Northern Trust sigue entrando a diario. Se paró esta cuenta, y se paró
exactamente con el cambio.

## 4. CAUSA RAÍZ — `T028B` se quedó apuntando a la cuenta vieja

La tabla **`T028B`** (*Asignar cuentas bancarias a tipos de operación*, SPRO → Extracto
bancario electrónico) tiene por **clave el número de cuenta**: `BANKL + KTONR`. Es la que
dice, para un extracto que llega, qué grupo de formato (`VGTYP`) y qué cuenta bancaria
interna (`BNKKO`) le corresponden.

Medido en P01 el 28.08.2026:

```
==== T028B — TODAS las filas de la clave de banco de NTB02 ====
   SP0000000MX7 | 11939389 | TR_TRNF | NTB02-EUR1 | UNES      <-- cuenta VIEJA

==== ¿existe la cuenta NUEVA 18747647 en T028B? ====
   filas: 0
```

**Control — las seis cuentas de NTB01, que sí siguen entrando:**

```
   SP0000000MXL | 17-18205 | TR_TRNF | NTB01-USD1 | UNES
   SP0000000MXL | 17-18206 | TR_TRNF | NTB01-USD2 | UNES
   SP0000000MXL | 17-54968 | TR_TRNF | NTB01-USD3 | UNES
   SP0000000MXL | 17-91492 | TR_TRNF | NTB01-USD4 | UNES
   SP0000000MXL | 17-91738 | TR_TRNF | NTB01-USD5 | UNES
   SP0000000MXL | 70-22442 | TR_TRNF | NTB01-USD6 | UNES
```

En las seis, `T028B.KTONR` **coincide exactamente** con `T012K.BANKN`. En NTB02 ya no.
Esa es la única diferencia entre las cuentas que entran y la que no.

### Cómo resuelve SAP la cuenta (deducido de la evidencia, no del manual)

El fichero **nunca** trae el número 11939389: trae `UNO12EUR`. Y sin embargo la
importación funcionó durante años con `T028B.KTONR = 11939389`. Por eliminación, la
cadena es:

```
fichero MT940  :25:  →  "SP0000000MX7 UNO12EUR"
     │
     ├─ T012K: se busca por BANKN o por BNKN2 (cuenta alternativa)  →  NTB02 / EUR01
     │
     └─ T028B: se busca por BANKL + el BANKN de la cuenta encontrada  →  VGTYP + BNKKO
                                                                          ⛔ ya no existe
```

Al cambiar `BANKN` de 11939389 a 18747647, el segundo salto se quedó sin fila. El
extracto no puede recibir tipo de operación ni cuenta interna, y no se procesa.

**Nivel de evidencia:** la asociación `T028B.KTONR = T012K.BANKN` está medida en 7 de 7
cuentas de Northern Trust. La lectura del código de la resolución no se ha hecho — la
inferencia es por eliminación y por control, no por lectura del estándar.

## 5. LO QUE HAY QUE HACER

Una entrada de configuración, en D01, por transporte, con alcance controlado:

| Tabla | Acción | Valor |
|---|---|---|
| `T028B` | **AÑADIR** | `BANKL=SP0000000MX7` · `KTONR=18747647` · `VGTYP=TR_TRNF` · `BNKKO=NTB02-EUR1` · `BUKRS=UNES` |
| `T028B` | **BORRAR** (después de verificar) | la fila `SP0000000MX7 / 11939389` |

Los demás campos (`CURRKEY`, `DSART`, `XVERD`, `WORKLIST`, `NOCLEAR`, `MANSP`, `ANZTG`)
van vacíos, igual que en las seis filas de NTB01 y que en la fila vieja.

**No hace falta tocar nada más.** Verificado:

- `T035D` — `UNES / NTB02-EUR1 → 0001095012` existe y está bien (su clave es `DISKB`, no
  el número de cuenta; no se ve afectada por el cambio).
- `T035U` — texto `BK NORTHERN TRUST- ASHI - EUR` presente en E/F/P.
- `FEB_IMP_SOURCE`, `FEB_IMP_POST`, `FEB_IMP_TRANS`, `FEB_IMP_TRANPATH` — todos
  **genéricos** (claves en blanco); no hay nada por cuenta que actualizar.
- `TIBAN` — conserva la fila vieja (11939389 → GB54…). Es inocua: ya no la referencia
  ninguna cuenta. No se toca.

### Antes de liberar el transporte

`T028B` es una tabla de customizing y un transporte de tabla **guarda la CLAVE y exporta
el VALOR al liberar** — con lo que puede arrastrar claves ajenas. Puerta obligatoria:

```bash
python Zagentexecution/quality_checks/config_transport_prerelease_check.py <TRKORR>
```

### Lo que NO se puede afirmar todavía

Si el fichero **llega y SAP lo rechaza**, o si **no llega**. No es lo mismo: lo primero se
arregla solo con T028B; lo segundo necesita además que Northern Trust / Coupa empiecen a
emitir el extracto de UNO18. Lo que se sabe:

- El job de recogida corre y termina bien (348 corridas desde el 01.08, la última hoy a
  las 11:45).
- No hay **ningún** log de aplicación de objeto `FEB*` desde el 01.08 — no hay rastro de
  rechazo registrado.
- El directorio físico está identificado (§6) pero listarlo por RFC se colgó (share de
  red). **Es el siguiente paso, y es de 2 minutos por AL11.**

Mirar en **AL11** → `\\hq-sapitf\coupa$\P01\Out\Data\EBS\` y
`\\hq-sapitf\coupa$\P01\Out\Errors\EBS` si hay ficheros posteriores al 14.08 para esta
cuenta. Y en paralelo preguntar a Ingrid/Baizid si Northern Trust ya emite el extracto de
UNO18 — el SSI del 25.06 (`Consolidation UNO18`, IBAN GB42…647) dice que la cuenta existe,
pero no que el extracto se esté enviando.

## 6. El pipeline de ficheros (documentado por primera vez)

Ver `knowledge/domains/Treasury/ebs_file_pipeline_and_jobs.md`. Resumen:

```
Northern Trust  →  Coupa Treasury  →  share \\hq-sapitf\coupa$\P01\Out\Data\EBS\
                                            │
                     job "EBS INTEGRATION" (JOBBATCH, cada hora)
                     programa FEB_FILE_HANDLING · variante "EBS JOB_COUPA"
                                            │
                     FEB_IMP_SOURCE: Y_EBS_PRO / Z_EBS_PRO, formato I
                                            │
                     resolución de cuenta  →  T012K (BANKN | BNKN2)  →  T028B  ⛔
                                            │
                     FEBKO / FEBEP  →  documento Z1
```

## 7. GENERALIZACIÓN — la clase de defecto

> **Cambiar el número de cuenta de un banco casa deja huérfana toda configuración cuya
> CLAVE sea ese número.** FI12 cambia `T012K`; no arrastra a `T028B`. El sistema no avisa:
> la cuenta queda perfecta en su ficha maestra y el extracto simplemente deja de entrar,
> en silencio, y se nota semanas después cuando alguien mira un saldo.

Es la misma forma que ya conocíamos en otros sitios: **una corrección no es un arreglo —
barre la población** (regla #172). Aquí la población son las demás cuentas cuyo número
haya cambiado alguna vez.

Y hay un precedente que lo anunció y no se cerró: el retro `NTB01_rename_2026-04-08.md`
(abril) encontró que **`T035D` estaba vacía para NTB01** y dejó escrito «verificar si las
demás cuentas necesitan entrada» y «**comprobar las entradas de T028B para la clave de
banco de NTB01**». Ese pendiente, cuatro meses después, es este incidente en otra tabla.

### El barrido: NO es un caso aislado — hay 3 cuentas más rotas igual

`house_bank_ebs_wiring_check.py --bukrs UNES` sobre la población entera (368 cuentas de
`T012K`, 188 bancos casa, 171 filas de `T028B`, 143 cuentas con extractos):

`house_bank_ebs_wiring_check.py --bukrs UNES` sobre la población entera (368 cuentas de
`T012K`, 188 bancos casa, 171 filas de `T028B`, 143 cuentas con extractos).

**El corte que hace válida la medida: las cuentas cerradas se marcan EN EL TEXTO.** UNESCO
no usa un indicador — escribe `CLOSED` en `T012T-TEXT1`, con todas las variantes de guiones
(`CLOSED-----UNESCO YAOUNDE - XAF`). Medido: **237 de las 411 cuentas de UNES** están así.
Sin ese corte el barrido acusaba a 4 cuentas y **2 eran cerradas desde hace años**
(`CLOSED - UNESCO HARARE - USD`, `CLOSED----UNESCO IESALC - USD`). Con él:

| Cuenta | Texto | `T012K.BANKN` | Lo que tiene `T028B` |
|---|---|---|---|
| **UNES/NTB02-EUR01** | NORTHERN TRUST - UNESCO ASHI - EUR | `18747647` | `11939389` ← **el ticket** |

**Es la unica.** El barrido acusó primero a cuatro cuentas y las tres restantes se cayeron al
aplicar dos cortes que la primera version del instrumento no tenia — y cada corte salio de
mirar la evidencia, no de afinar un umbral:

1. **Cuentas CERRADAS** (marcadas en el texto): `SCB01-USD01` y `BPO01-USD01` llevaban años
   cerradas.
2. **Extracto MANUAL**: `BTE01-USD01` (UNESCO Teherán) tiene `EFART='M'` — se teclea por FF67.
   **Importó 116 extractos sin haber tenido nunca fila en `T028B`**, igual que `BTE01-IRR01`
   con otros 156. Para el extracto manual esa fila no hace falta, asi que exigírsela publicaba
   un defecto inexistente. Medido: de 143 cuentas con extractos en UNES, solo **131 son
   electrónicas**; a las otras 12 no se les puede aplicar esta regla.

Ese fue el primer falso positivo de la puerta, y esta clavado como caso de autotest para que
no vuelva.

Además, informativo: **25 filas huérfanas** en `T028B` (números que ya no son de ninguna
cuenta viva — el rastro acumulado de cambios sin barrer) y **9 canales mudos** de cuentas
vivas entre 13 y 180 días (BMN01 La Habana, CAB02 Ammán, CIT03 IITE, SOG06 Puerto Príncipe,
ECO08 Harare). Ninguna está marcada como cerrada. No se ha mirado nunca porque no había
con qué.

### Puerta mecanizada

`Zagentexecution/quality_checks/house_bank_ebs_wiring_check.py` — para cada cuenta de
`T012K`, comprueba que exista la fila de `T028B` con su `BANKN` actual y la de `T035D` con
su `DISKB`, y marca las filas de `T028B` cuyo `KTONR` **no** corresponde ya a ninguna
cuenta viva (huérfanas = una cuenta que cambió de número y nadie barrió).

---

## 8. ACTUALIZACIÓN 2026-08-28 tarde — el lado SAP está COMPLETO; la causa restante está aguas arriba

**La fila de `T028B` ya está grabada y transportada.** Verificado leyendo el destino en los dos
sistemas, no la pantalla:

```
D01  SP0000000MX7 | 18747647 | TR_TRNF | NTB02-EUR1 | UNES     ✅
P01  SP0000000MX7 | 18747647 | TR_TRNF | NTB02-EUR1 | UNES     ✅
```

Con eso, **las tres piezas de configuración que dependían del número de cuenta están correctas**:
`T012K` (BANKN + BNKN2), `TIBAN` (IBAN nuevo desde 17.08) y `T028B`. **No queda nada que hacer en
SAP.**

### Y sin embargo no entra nada. Lo medido:

| Comprobación | Resultado |
|---|---|
| ¿Algún extracto con `UNO18EUR`, alguna vez? | **NINGUNO** — cero filas en `FEBKO` en toda la historia |
| Último de NTB02/EUR01 | estadillo **2997, 14.08.2026**, importado el 15.08 |
| ¿Entra algo de otros bancos? | sí — **102 · 109 · 108** extractos los días 25, 26 y 27.08 |
| ¿NTB02 en ese rango? | **0** |
| Ficheros que mencionen NTB02 en el directorio de ERRORES de Coupa | **0** |

**Conclusión: el fichero no llega.** No es que SAP lo rechace — no hay nada que rechazar. Northern
Trust / Coupa no están emitiendo el extracto de la cuenta UNO18.

### Por qué FF67 no ofrece la cuenta nueva — y no es un defecto

El usuario reporta que al crear un extracto manual la cuenta nueva no aparece en la lista.
**La lista de FF67 no se deriva de la configuración: contiene el historial de extractos recibidos.**

La prueba está en la propia captura del usuario: muestra el par `SP0000000MX7` + `UNO10`, y **esa
combinación no existe en `T012K`** — NTB01 tiene hoy clave de banco `SP0000000MXL`. Lo que sí
existe es en `FEBKO`:

```
SP0000000MX7   UNO10USD    n=10     último 05.03.2015
SP0000000MX7   UNO11USD    n=10     último 05.03.2015
SP0000000MX7   UNO12EUR    n=2233   último 14.08.2026
```

Coincide par por par. Una lista derivada de configuración **no puede** producir una fila de 2015 de
una cuenta que desde entonces cambió de clave de banco.

> ⚠️ **Lo que está probado y lo que no.** Probado: la lista **no** sale (solo) de `T012K`, porque
> contiene un par ausente de `T012K`. Fuertemente respaldado: coincide exactamente con
> `FEBKO.ABSND`. **No leído:** el fuente de `SAPMF40K` — el module pool devuelve 25 líneas sin
> includes por `RPY_PROGRAM_READ`, así que no se afirma de qué tabla lee exactamente.

**Consecuencia práctica:** `UNO18EUR` aparecerá en FF67 **cuando llegue su primer extracto**, no
antes. Que hoy no esté es el síntoma, no la causa.

### Lo que hay que hacer ahora — y ya no es de DBS

1. **Reclamar a Northern Trust / Coupa** que emitan el extracto de la cuenta UNO18. El SSI del
   25.06 (`Consolidation UNO18`, IBAN GB42…647) prueba que la cuenta existe; no que el extracto se
   esté enviando.
2. **Confirmar con qué identidad lo van a emitir.** SAP espera `UNO18EUR` en el `:25:` — es lo que
   tiene `T012K.BNKN2`. Si el banco emite otra cosa (por ejemplo el número `18747647`), hay que
   saberlo: la resolución se hace por `BANKN` **o** `BNKN2`, y ambas están puestas, pero conviene
   confirmarlo antes de que llegue el primero.
3. **Cuando entre el primero, borrar la fila vieja** `11939389` de `T028B`. Nunca antes.
4. Mientras tanto, si Tesorería necesita el saldo, se puede **teclear el extracto en FF67** — la
   configuración lo soporta desde ahora.

**Estado: SAP COMPLETO — ESCALADO AGUAS ARRIBA.**

---

## Registro

- `brain_v2/incidents/incidents.json` → `INC-000013624`
- Artefactos de medida: `Zagentexecution/tasks/2026_08_28_ebs_ntb02_uno18eur/`
- Capturas del correo extraídas: `image001..006.png` (FI12 antes, FF67, End-of-Day
  statement de Coupa, SSI de UNO18)
