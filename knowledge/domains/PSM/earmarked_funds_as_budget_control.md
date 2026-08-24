# Cómo UNESCO gestiona las reservas de fondos

> **Esto es un PROCESO, no un dato.** Es el mecanismo por el que se compromete presupuesto, y
> mueve el 52% de todos los cambios del sistema.
>
> Medido 2026-08-24 sobre `KBLK` (2.844.883), `KBLP` (3.216.206) y `FMIOI` (2.254.039).
> Fuente de la semántica: `ytfm_wrttp_gr`, configuración propia de UNESCO. Todo MEDIDO.

## Por qué importa

`FMRESERV` es la clase de documento de cambio **más grande del sistema**: 7.252.630 cambios, el
52% del log. Nada más se le acerca.

Y no es una comunidad de gestores apartando su presupuesto cuando lo necesitan. Es **un proceso
mensual, automatizado, que ejecutan dos usuarios**, con una periferia de unas 300 personas
haciendo reservas manuales encima.

## Dónde vive el dato

`TCDOB` lo dice: `FMRESERV` → **`KBLE`, `KBLK`, `KBLKKRED`, `KBLP`**. No `FMBH`/`FMBL`, que son
documentos de presupuesto BCS y son otra cosa — esa fue la hipótesis razonable y era falsa.

En `FMIOI` las reservas son **`REFBT='110'`**: 1.415.828 filas que casan al **100%** con
`KBLK.BELNR` (cruzado, no supuesto).

## Los tipos de valor, según la configuración de UNESCO

`ytfm_wrttp_gr` es una tabla **propia de UNESCO** que agrupa los tipos de valor. No hace falta
adivinar la semántica:

| WRTTP | Grupo | Qué es |
|---|---|---|
| **65** | `COMMITM` | **compromiso — la reserva de verdad** |
| **80** | `BLOCKED` | bloqueado |
| **81** | `EXPENDU` · `IC_OBL` | gasto |
| **82** | `PRECOMM` | pre-compromiso |

**Separar por WRTTP es obligatorio antes de cualquier medida.** Mezclarlos produce cifras que
parecen razonables y son falsas — ver la sección de trampas al final.

## LO AUTOMÁTICO: el 83,5% son dos usuarios y la nómina

| Transacción | Líneas | | Importe | Usuarios |
|---|---:|---:|---:|---:|
| `SE38` | 477.846 | 33,8% | 1.124.806.450 | **HIPER 100%** |
| `ZPBC_PERIOD_CLS_EXEC` | 434.859 | 30,7% | 1.045.188.361 | **HIPER 100%** |
| *(sin tcode — batch)* | 268.379 | 19,0% | 822.877.299 | **F_DERAKHSHAN 99%** |

**1.181.084 líneas, el 83,5%, y efectivamente DOS usuarios.**

`ZPBC_PERIOD_CLS_EXEC` es el **cierre periódico de PBC** (Position Budgeting and Control). Junto
con `PA30`, `PCP0`, `HRPBC_ENGINE_PNP` y `HRFPM_VACANCY_DISP`, esto es el mecanismo por el que
**cada puesto reserva su coste mes a mes**. El presupuesto de personal no se gestiona: se
compromete automáticamente por puesto.

Los tipos de documento lo confirman: de las reservas reales (WRTTP 65), **794.157 son `BLART=91`**
y 8.954 son `92`. Un solo tipo de documento carga con el 99% de la nómina.

## LO MANUAL: unas 300 personas, el 16,5%

| Transacción | Líneas | Usuarios | Qué es |
|---|---:|---:|---|
| `FMX2` | 98.293 | **296** | modificar reserva de fondos |
| `FB60` | 36.204 | **298** | factura de acreedor (consume) |
| `PA30` | 21.152 | 72 | datos maestros de personal |
| `FB01` | 18.836 | 37 | contabilizar documento |
| `FMW2` | 12.124 | 11 | pre-compromiso |
| `FMJ2` | 9.297 | 11 | **arrastre de compromisos** |
| `FMX1` | 3.240 | **198** | crear reserva de fondos |

Nota la asimetría: **`FMX2` (modificar) tiene 98.293 líneas y `FMX1` (crear) solo 3.240.** La
gente **retoca** reservas mucho más de lo que las crea — porque las crea la máquina.

`W_NORTON` es un caso aparte: 1.148 líneas a **16.599 €/línea**, frente a los 2.164 de HIPER.
Reservas grandes y puntuales, otro proceso.

## El calendario: dos eventos mensuales distintos

**Creación — días 3, 4 y 5:** 172.412 + 327.497 + 106.250 = **606.159 de 803.111 (75%)**, con el
día 4 dominante.

**Modificación — días 14 y 15:** 1.552.752 + 1.355.890 = **2.908.642 de 7.252.630 cambios (40%)**.

O sea: se crea a principio de mes y se retoca a mitad. Dos ventanas fijas.

Y el volumen es **plano hasta lo inhumano**: 24.000–27.000 líneas y 50–59 M cada mes, sin
variación, durante dos años y medio. Ningún proceso humano tiene esa forma.

**34.420 líneas (94,7 M) tienen fecha futura**, hasta diciembre de 2026: se reserva por
adelantado todo el ejercicio.

## Solo dos entidades reservan

| Entidad (FIKRS) | Líneas | Importe |
|---|---:|---:|
| UNES | 800.645 | 1.768.734.459 |
| UBO | 2.466 | 64.400.531 |

**IBE, ICTP, IIEP, UIL, MGIE, UIS e ICBA tienen CERO reservas reales.** Tienen líneas en `FMIOI`,
pero de otros tipos de valor. El mecanismo de reserva de puestos es de **UNES y UBO**, no de los
institutos.

## DOS MODELOS OPERATIVOS BAJO EL MISMO SISTEMA

Cortando por área de gestión financiera aparece la diferencia estructural: **la sede tiene el
proceso automatizado y los institutos lo hacen entero a mano.**

| Área | Total | SE38 | ZPBC | batch | **diálogo** | usuarios diálogo |
|---|---:|---:|---:|---:|---:|---:|
| UNES | 1.386.850 | 476.288 | 442.557 | 267.176 | 200.829 | 350 |
| UBO | 10.959 | 1.558 | 1.479 | 1.203 | 6.719 | 15 |
| IBE | 5.550 | 0 | 0 | 0 | **5.550** | 15 |
| ICTP | 4.457 | 0 | 0 | 0 | **4.457** | 13 |
| IIEP | 3.898 | 0 | 0 | 0 | **3.898** | 27 |
| UIL | 1.341 | 0 | 0 | 0 | **1.341** | 4 |
| MGIE | 1.038 | 0 | 0 | 0 | **1.038** | 9 |
| UIS | 892 | 0 | 0 | 0 | **892** | 15 |
| ICBA | 843 | 0 | 0 | 0 | **843** | 13 |

**Los siete institutos tienen CERO ejecución automática.** Ni un `SE38`, ni un `ZPBC`, ni una
línea de fondo. El 100% pasa por una persona en una pantalla.

UNES tiene el **85,5% automatizado**; UBO el 38,7%.

### Y el perfil de lo manual también difiere

| | institutos | UNES en diálogo |
|---|---:|---:|
| `FMX2` modificar reserva | **63,8%** | 43,1% |
| `FB01` contabilizar | 15,8% | 5,1% |
| `FB60` factura acreedor | 8,3% | 17,2% |
| `PA30` datos de personal | — | 10,5% |

El instituto vive en `FMX2`: dos de cada tres cosas que hace son **retocar una reserva a mano**.

### Qué significa

La automatización de UNES es **el cierre periódico de PBC**, que compromete el coste de cada
puesto. Los institutos no tienen eso — **no comprometen presupuesto de personal
automáticamente**. Su presupuesto de puestos, si lo gestionan, no pasa por este mecanismo.

Carga por persona, que lo confirma: UNES 3.951 líneas/persona frente a UIS 59 o ICBA 65. No es
que los institutos trabajen menos: es que el volumen de UNES lo genera una máquina.

## Ciclo de vida

| Estado (`ERLKZ`) | Líneas | | Importe |
|---|---:|---:|---:|
| `X` cerrada | 605.921 | 75,4% | 1.311.133.463 |
| `F` | 154.045 | 19,2% | 386.915.001 |
| *(vacío)* abierta | 43.145 | 5,4% | 135.086.527 |

Consumo global sobre `KBLP`: **85,3%** (37,2 de 43,6 mil millones). El arrastre existe y se hace
— `FMJ2` tocó 4.116 líneas en 2024 y 4.222 en 2025.

Lo que queda abierto del bienio anterior son **7 líneas por 8.109 €**. Nada.

## Las trampas de medir esto (cada una produjo una cifra creíble y falsa)

1. **`WTABG = 0` no es "sigue bloqueando".** Significa "no se consumió", y un documento puede
   estar cerrado sin consumo. Medido así daban **~2.400 M** fuera del bienio actual. Con `ERLKZ`
   de `FMIOI`: **271,9 M**. Nueve veces menos.

2. **No separar WRTTP mezcla gasto con reserva.** Las 4.907 líneas "abiertas del bienio
   anterior" son **4.414 de WRTTP 81 = gasto**. Reservas de verdad: 7.

3. **Un porcentaje por entidad sin separar WRTTP inventa diferencias.** Se reportó que "IIEP
   tiene el 28,4% abierto frente al 7,2% de UNES". Falso: IIEP **no tiene reservas**.

4. **El tipo `FB` no bloquea 153 M.** Parecía reservar 153.152.809 sin consumir nada, y el cruce
   contra `FMIOI` devuelve **cero filas**: esos documentos no generan líneas de compromiso en FM.
   No impactan presupuesto en absoluto.

## Lo que NO se sabe

- **`ERLKZ='F'`** (154.045 líneas, 386,9 M) frente a `'X'`. Si `F` es un cierre parcial, la cifra
  de abierto se mueve. **Necesita P01.**
- **Textos de los tipos de documento** (`91`, `92`, `12`, `13`, `FB`): medidos por comportamiento,
  no por su descripción. **Necesita P01.**
- **Qué es `HIPER`** exactamente — usuario de proceso, pero no se ha verificado su definición.

## Cómo se reproduce

```sql
-- las reservas REALES: REFBT='110' (casan 100% con KBLK) y WRTTP='65' (COMMITM)
SELECT FIKRS, TCODE, USNAM, COUNT(*), SUM(CAST(FKBTR AS REAL))
FROM FMIOI WHERE REFBT='110' AND WRTTP='65' GROUP BY 1,2,3;
```

Quién y cuándo: `cdhdr_history WHERE OBJECTCLAS='FMRESERV'` (USERNAME, UDATE, TCODE).
Semántica de los tipos de valor: `ytfm_wrttp_gr`.

## Enlaces

- Dominio hermano que lo dispara: `knowledge/domains/PBC/`
- Claims 568–571 · columna vertebral de casos: `brain_v2/case_spine.json`
- Trampas de método: `brain_v2/methods/algorithm_memory.json`
