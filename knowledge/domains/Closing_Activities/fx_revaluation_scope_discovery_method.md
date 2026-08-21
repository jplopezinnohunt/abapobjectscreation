# Método de descubrimiento del ALCANCE de una revaluación FX

**Dominio**: `Closing_Activities` · **Proceso**: `B2R` · **Nivel de evidencia**: TIER_1 — medido en
vivo contra P01, sesión 102 (2026-08-21)
**Autor del método**: JP. **Blindajes y segunda pasada**: derivados de los falsos positivos que
produjo cada paso al implementarlo el mismo día.
**Instrumentos**: `Zagentexecution/quality_checks/fx_revaluation_peer_check.py` ·
`Zagentexecution/tasks/2026_08_21_fx_revaluation_scope/build_full_census.py` ·
agente `fx-revaluation-scope` · claims 558–564.

---

## Por qué hace falta un método y no una consulta

La pregunta *"¿qué cuentas deberían revaluarse y no se revalúan?"* no tiene respuesta en ninguna
tabla. `T030H` dice dónde postear, la variante dice qué se calcula, y **ninguna de las dos dice
qué *debería* entrar**. El alcance correcto es un juicio de negocio, y el método sirve para
acorralarlo con datos en vez de opinarlo.

El error de partida —el que cometí— es medir contra el balance entero: *"cuentas de balance fuera
de toda variante"* da **497** en UNES y no significa nada, porque la mayoría están fuera con toda
la razón. **El universo lo definen las variantes, no el plan de cuentas.**

---

## Los seis pasos

```
1. LEER LAS VARIANTES          -> qué cuentas usa cada una
2. MAPEARLAS A SU POSICIÓN     -> ese conjunto de posiciones ES EL UNIVERSO
3. LISTAR todas las cuentas de esas posiciones -> cuáles NO están en variante
4. ¿USD o moneda extranjera?
5. ¿Tiene saldo que revaluar?
6. ¿Está bloqueada?            -> se MARCA, no es error
```

Medido en UNES: el universo son **28 posiciones de 79**. Las otras 51 quedan fuera del análisis
**por diseño**, no por olvido — y decirlo explícitamente es la mitad del valor del método.

---

## Lo que blinda cada paso

Cada uno de estos cuatro puntos costó un falso positivo el mismo día en que se implementó el
método. Están aquí para que no se vuelvan a pagar.

### Paso 1 — resolver la selección de verdad

**Una selección con SOLO exclusiones significa TODO MENOS ESO, jamás «nada».** En un
`select-option` de ABAP un rango vacío es *sin restricción*; añadirle solo líneas `SIGN='E'` sigue
siendo *sin restricción, salvo estas*. `UNES_OI_AR/AP` trae **27 líneas `AKONTO` y las 27 son de
exclusión**: significa *todas las cuentas asociadas menos esas 27*. Leerlo como conjunto vacío
daba 549 cuentas fuera en vez de 497, y **68 asociadas huérfanas en vez de 16**.

**`SKONTO` y `AKONTO` son universos distintos.** `SKONTO` selecciona cuentas de **mayor**; `AKONTO`,
cuentas **asociadas** de submayor. El campo que aplica a una cuenta lo decide `SKB1-MITKZ`.
Mezclarlos en un único conjunto hace que toda cuenta asociada salga «fuera».

**Una cuenta excluida a propósito es una DECISIÓN, no un olvido.** Se marca como tal y no se
cuenta como hueco — exactamente igual que las bloqueadas del paso 6.

### Paso 5 — saldo no es exposición

`4041011` tiene **571,6 M USD de saldo** y solo **10 M EUR** que revaluar: el resto son dólares
limpios. Lo que se mide son las **partidas abiertas** (`BSIS`) en moneda distinta de la de la
sociedad, netas por `SHKZG`, y se reporta **en su propia moneda**, no solo en contravalor.

Y una lectura fallida es **DESCONOCIDA**, nunca «no»: `RFC_READ_TABLE` devuelve
`TABLE_WITHOUT_DATA` tanto cuando no hay filas como cuando preguntaste mal.

### Paso 4 — qué significa la moneda de la cuenta

`SKB1-WAERS = <moneda de la sociedad>` **no** quiere decir «cuenta en dólares»: quiere decir
**admite cualquier moneda**. Una cuenta con `EUR` en el maestro solo admite euros. De ahí salen
dos poblaciones con comportamiento opuesto, y **medido en la familia de depósitos**:

| Grupo | Cobertura | Por qué |
|---|---|---|
| Moneda extranjera **fija** | **4 de 4 — 100 %** | su moneda la delata en el maestro, se cubre sola |
| Moneda de sociedad **con divisa dentro** | 4 de 5 | **el maestro no lo dice**: hay que mirar los apuntes |

La clase de defecto vive entera en el segundo grupo.

---

## La segunda pasada: por BLOQUE DE NUMERACIÓN

El paso 2 define el universo **por posición**, y eso deja fuera a una variante por **lista** cuyos
miembros están repartidos entre posiciones. Medido: `1.1.2.1 Short Term Deposits` **no la ocupa
ningún miembro de `UNES_DEPOSIT`**, así que con el proceso puro **`4041011` no aparece**.

Aparece al repetir el paso 2 usando el **bloque de numeración** de los miembros: el bloque
`404101` tiene a `4041013 / 17 / 18 / 19` dentro. **Ejecuta las dos pasadas y marca por cuál entró
cada candidata** — no las mezcles, porque la evidencia es de distinta fuerza.

---

## ⭐ La columna que explica el comportamiento: `Selected by`

No basta con saber **si** una cuenta entra: hay que saber **cómo**.

| Modo | Qué es | Comportamiento |
|---|---|---|
| `RANGE` | la coge un intervalo | **se mantiene solo** — una cuenta nueva dentro del rango queda cubierta el día que se crea |
| `ALL-BUT` | el campo solo tiene exclusiones | **se mantiene solo, al revés** — cubierta por defecto salvo decisión expresa |
| `INDIVIDUAL` | puesta a mano, una a una | **se degrada** — cada alta exige que alguien se acuerde |

**Medido sobre las 556 cuentas activas que sí se revalúan:**

| Modo | Cuentas | % cobertura | Huecos que genera |
|---|---|---|---|
| `RANGE` | 483 | **87 %** | **0** por sí solo |
| `ALL-BUT` | 53 | 10 % | 4 |
| `INDIVIDUAL` | 20 | **4 %** | **47** |

**`INDIVIDUAL` cubre el 4 % y concentra el 68 % de los huecos** — una desproporción de casi 20 a 1.
La razón es mecánica, no de disciplina: **un rango es una regla y una lista es un inventario**. La
regla no envejece; el inventario sí.

Por variante:

| Variante | Selecciona por | Cubre de sus posiciones |
|---|---|---|
| `UNES_UNBA` | RANGE | 225 de 391 — 58 % |
| `UNES_OI_G/L` | RANGE | 143 de 312 — 46 % |
| `UNES_OI_AR/AP` | ALL-BUT + INDIVIDUAL + RANGE | 172 de 341 — 50 % |
| **`UNES_DEPOSIT`** | **INDIVIDUAL** | **16 de 344 — 5 %** |

**Uso operativo directo:** filtra `Selected by = INDIVIDUAL` y tienes el **inventario de fragilidad**
del proceso — todo lo que depende de que una persona se acuerde. Hoy son 20 cuentas y cabe en una
pantalla.

**Y cambia la recomendación de sitio**: no es *«añadid `4041011` y las nueve de institutos»* —eso
repara el síntoma y el año que viene habrá otras— sino **convertir `UNES_DEPOSIT` de lista a rango**,
con las exclusiones que Tesorería quiera. Es la diferencia entre corregir un dato y arreglar el
generador.

---

## Qué produce el método

| Salida | Qué es |
|---|---|
| **CANDIDATA** | activa, con divisa abierta, fuera de variante, no excluida, y **con iguales dentro** de su grupo. Se le asigna la variante que ya cubre a sus iguales |
| **LATENTE** | configuración incompleta y sin exposición hoy. No es alarma; lo será el día que se postee en divisa |
| **BLOQUEADA** | se marca, sale de la población, **no es error** |
| **EXCLUIDA** | decisión expresa en la variante, **no es error** |
| **FUERA DEL UNIVERSO** | su posición no la trabaja nadie. **No es un hueco de revaluación**: es una pregunta de compensación o de política contable, y va por otro camino |

Esa última fila es de JP y es la que evita el error más caro: de los ~744 M USD que aparecían «sin
revaluar», la mayor parte está en posiciones que ninguna variante trabaja — préstamos, condiciones
con donantes, patrimonio. Mezclarlas con los huecos de revaluación convierte un hallazgo accionable
en una alarma que nadie puede atender.

---

## Reproducirlo

```bash
python Zagentexecution/quality_checks/fx_revaluation_peer_check.py
python Zagentexecution/tasks/2026_08_21_fx_revaluation_scope/build_full_census.py
```

Agente: `fx-revaluation-scope`. Reglas:
`feedback_a_selection_with_only_exclusions_means_everything_else` ·
`feedback_a_config_object_applies_to_a_population_prove_it_before_measuring` ·
`feedback_read_the_variant_the_variant_is_the_process`.
