# INC-MMF-BNPPB-2026 — traspaso de ejecución en P01

**Para quien teclee en P01.** El agente no escribe P01: todo lo de abajo está leído en vivo de P01
el 2026-08-20 y verificado. Dos acciones, y solo sobre **4041018**.

---

## Contexto en una línea

Se crearon `4041018 MMF EUR BNP PB` y `4041019 MMF USD BNP PB` en UNES el 27-07-2026 (MP_BOUA).
Las dos son **cuentas de inversión** (fondo monetario BP2S LUX / BNP Paribas Insticash, *earmarked
for cash pool*), grupo `OTHR`, bloque 404xxxx. **Solo la EUR se revalúa.**

## Lo que YA está bien — no tocar

| | |
|---|---|
| `SKB1.WAERS` de 4041018 | **EUR** — correcto, idéntica a su referencia 4041017 en todos los campos funcionales |
| `SKB1.WAERS` de 4041019 | USD — correcto, idéntica a su referencia 4041016 |
| Mapeo "cash and cash equivalent" (lo que pidió Thavry) | ✅ **ya cumplido**: FSV `FS10`, posición `1.1.1.1 "Cash with Banks"`, cubiertas por el intervalo `0004041015–0004041019` que ya existía |
| D01 y V01 | alineados el 2026-08-20 (2 y 33 cuentas, readback campo a campo OK) |

---

## ACCIÓN 1 — `OB09` (tabla `T030H`), solo `4041018`

Copia exacta de `4041017`, leída en vivo de P01:

| `CURTP` | `LKORR` | `LSREA` | `LHREA` | `LSBEW` | `LHBEW` |
|---|---|---|---|---|---|
| **10** | `0004041018` | `0006045011` | `0007045011` | `0006045011` | `0007045011` |
| **30** | `0004041018` | `0005022012` | `0005022012` | `0005022012` | `0005022012` |

`LKORR` = la propia cuenta: es **auto-revaluación**, el patrón de las cuentas de inversión. **No**
lleva sub-cuenta de ajuste — eso es el patrón de la conciliación AP/AR, no el de éstas.

## ACCIÓN 2 — variante de F.05 `UNES_DEPOSIT`  ⚠️ la que se olvida

Añadir `4041018` como **valor individual `EQ`** en la selección de cuentas (`SKONTO`).

**No la absorbe ningún rango.** En P01 esa variante **no usa intervalos**: es una lista de **16
valores sueltos** — `2021053`, `4041013`, `4041017`, `4043011/12/13/14/25/26`,
`5091010/14/15/16/19/20/23`. Con 4041018 pasa a 17.

> `T030H` dice **dónde** se postea la diferencia. La **variante** decide **si** la cuenta entra en
> el cálculo. Hacer solo la Acción 1 deja una revaluación que **nunca corre y no da ningún error**.

---

## LO QUE NO SE HACE — `4041019`

**Nada.** Tres evidencias independientes:
1. Su formulario AM 3-11 firmado marca **`GL to be revaluated = NO`**.
2. Su referencia declarada es **`4041016`** (no 4041017, como decía el correo de traslado), y
   `4041016` **no tiene ninguna fila en `T030H`**.
3. Es **USD en una sociedad USD** (`T001.WAERS(UNES)='USD'`): no hay exposición que revaluar.

Confirmarlo con Jeannette por escrito antes de que alguien lo configure "por simetría" con la EUR.

---

## VERIFICACIÓN — después de las dos acciones

```bash
python Zagentexecution/quality_checks/ob09_vs_variant_check.py --systems P01 --accounts 40410
```
`4041018` debe dejar de aparecer como cuenta sin cobertura. Exit 0 no se espera todavía: quedan
3 cuentas activas con OB09 fuera de toda variante, que son la pregunta abierta de abajo.

---

## PREGUNTA ABIERTA PARA TESORERÍA (no bloquea el ticket)

Salió del barrido de la población, no del ticket:

| Cuenta | `T030H` | ¿en alguna variante? | Exposición medida (`GLT0`) |
|---|---|---|---|
| `4041011` Term Deposits Principal | sí | **no** | **EUR en 2023, 2024 y 2025** |
| `4041012` Term Accounts Principal Current | sí | **no** | EUR en 2023 y 2024 |
| `4041014` MMF USD JPMorgan | sí | **no** | solo USD → inocuo |

Llevan años configuradas y sin valorarse. **¿Es intencionado?** Si no lo es, son diferencias de
cambio no reconocidas. (`glt0_p01` llega hasta 2025; el estado 2026 no está medido.)

---

## BORRADOR DE RESPUESTA A JEANNETTE

> Bonjour Jeannette,
>
> He revisado las dos cuentas. **4041018 (MMF EUR BNP PB)** sí necesita revaluación y la estoy
> configurando como 4041017: OB09 con la cuenta como su propio ajuste, y la cuenta añadida a la
> variante `UNES_DEPOSIT` de F.05 — este segundo paso es imprescindible, sin él la configuración de
> OB09 no llega a ejecutarse nunca.
>
> **4041019 (MMF USD BNP PB) no necesita revaluación**, y aquí difiero de la nota. Su formulario
> AM 3-11 indica *GL to be revaluated = NO* y da como referencia **4041016**, no 4041017. He
> comprobado que 4041016 tampoco está revaluada. Es coherente: al ser una cuenta en USD dentro de
> una sociedad cuya moneda es USD, no hay diferencia de cambio que reconocer. Configurarla añadiría
> una entrada sin efecto.
>
> Sobre la petición de Thavry de mapearlas bajo *cash and cash equivalent*: **ya está hecho**, las
> dos caen en la posición `1.1.1.1 Cash with Banks` de la versión de balance.
>
> Aparte, y sin relación con vuestra petición: al revisar la familia he visto que **4041011 y
> 4041012** tienen configuración de revaluación pero no están incluidas en ninguna variante de F.05,
> así que no se valoran. 4041011 ha movido euros en 2023, 2024 y 2025. ¿Sabéis si se dejaron fuera a
> propósito?
