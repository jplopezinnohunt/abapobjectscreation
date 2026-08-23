# La arquitectura de exploración

> Construida el 2026-08-22/23. Todo lo que sigue está MEDIDO y cada pieza tiene su algoritmo
> registrado en `brain_v2/methods/algorithms.json`.

## Qué problema resuelve

Teníamos 28,5M de filas de log de auditoría y no sabíamos qué parte del sistema entendíamos.
El bucle de descubrimiento llevaba **75 días parado** y nadie lo notó, porque nada medía si la
comprensión se movía.

La arquitectura contesta una sola pregunta, que es la pregunta de madurez:

> **De todo lo que este sistema ejecuta, cambia y corre solo: ¿está identificado, y lo que no
> es técnico, lo entendemos y sabemos a qué dominio pertenece?**

## La cadena, y el orden es el contenido

```
ACUMULAR    accumulate_logs.py      A1 chunks ≤6h · A2 ventana derivada de la cobertura real
   └── FILTRAR      log_reality_filter.py   A19  objeto / instancia generada / actor
         └── SITUAR       executed_objects_domain_map.py  A4 escalera ordenada · A3 dos ejes
               └── MEDIR        comprehension_index.py    A20  4 superficies × 5 vías × 4 grados
                     └── ABRIR        domain_composition.py     A22  de qué está hecho cada dominio
                           └── ENCADENAR     case_spine.py       A21  el caso: del cambio al documento
                                 └── ATERRIZAR   claims · incidentes · docs de dominio · capability_model
```

## Las cuatro superficies de ejecución

Medir programas solo contesta un cuarto de la pregunta y se lee como el todo.

| Superficie | Qué es | Fuente |
|---|---|---|
| **objects** | lo que corre | `RSAU.SLGREPNA` |
| **changes** | lo que se altera | `CDHDR.TCODE` |
| **jobs** | lo que corre solo | `TBTCO × TBTCP` (el **programa del paso**, no el nombre del job) |
| **rfc** | **lo que ENTRA** | `RSAU.PARAM3` de las filas `RFC Function Call` |

La cuarta es la mayor y fue la última en cablearse: **12.589.665 ejecuciones, ~40% del total**.
Una llamada RFC no está en `SLGREPNA` — ahí solo aparece `SAPMSSY1`, el despachador. Las otras
tres veían el tubo y no lo que pasa por dentro. La prueba de que faltaba es exacta:
`CROSS_CUTTING` pasó de **0 a 922.428** al añadirla.

## Las cinco vías, y por qué no son grados de lo mismo

| Vía | Significa |
|---|---|
| **TECHNICAL** | fontanería. Nadie la "hace", ocurre. El despachador, el planificador, el sustrato de sesión |
| **CROSS_CUTTING** | trabajo de un equipo que sirve a **todas** las cadenas: seguridad, integraciones, transportes. Exigirle una cadena de negocio es un error de categoría |
| **BUSINESS** | tiene dominio y cadena B2R/P2P/H2R/T2R/P2D. Aquí sí hay grados |
| **STRANDED** | sin cadena **y** sin ser técnico. Hueco real, y va **nombrado** |
| **OBSERVER** | nosotros mirando. Separado, nunca restado |

Clasificar algo como técnico **es una respuesta**, no un hueco. 17,5M de ejecuciones son
`SAPMSSY1`. Contarlas como incomprensión hacía que el índice dijera que el sistema es un
misterio cuando su fontanería está donde debe.

Y la lista de técnicos va **corta y nombrada** a propósito: en cuanto crezca para absorber algo
incómodo, el índice empieza a mentir a nuestro favor.

## Los cuatro grados de lo que sí es negocio

| Grado | Prueba que exige |
|---|---|
| 0 EJECUTA | está en el log |
| 1 SITUADO | dominio + cadena de proceso, asignados por A4 |
| 2 DESCRITO | quién, cuándo, por qué canal — probado por una **forma** (actores concentrados o perfil temporal real), nunca porque el campo de usuario esté lleno, que lo está siempre |
| 3 EXPLICADO | un store lo nombra con prosa, claim o anotación. **Nunca** por plausibilidad |

Se publica el **reparto**, jamás una media: 90% situado con 5% explicado dice lo cierto —
sabemos etiquetar y no sabemos explicar — y una media lo esconde. Y se pondera **por
ejecuciones, no por objetos**.

## El observador en su propia medida

Nuestra herramienta lee P01 por RFC y cada lectura cae en el mismo log que medimos:
**264.521 filas (0,93%)**, 135.377 de la superficie RFC.

El grueso es inofensivo (`RFC_READ_TABLE`, `RFCPING`) porque cae en sustrato. Pero
`FM_FUND_GET_DETAIL_RFC`, `GL_ACCT_MASTER_GET_*` y `BAPI_PROJECTDEF_GETDETAIL` son módulos de
**negocio**: un dominio parecía más vivo cuanto más lo mirábamos.

Va **separado, no restado**. Restado desaparece y nadie lo audita.

**Control permanente:** `cdhdr_history` con nuestro usuario = **0 filas** sobre 13,97M de
cambios. La disciplina de solo-lectura deja rastro medible, o su ausencia.

## Agregar sin abrir invierte la importancia

`PS` salió con 3.501.373 ejecuciones — el **39,1% de toda la actividad de negocio**, más que FI
y HCM juntos. Leído así, PS sería el corazón del sistema.

Abierto: el **99,7%** de su tráfico RFC son **dos objetos con un actor cada uno** —
`Y_BAPI_WBS_FINANCIAL_DATA_1` (1.861.107) y `Y_BAPI_YPS8` (878.833). No es gente gestionando
proyectos: es un satélite leyendo datos financieros de WBS en bucle.

Por eso existe A22. Un porcentaje por dominio es un número sin proceso dentro.

## Dos conocimientos, dos stores

| | Dónde vive |
|---|---|
| **Del DATO** — qué hace el sistema | claims · incidentes · docs de dominio · capability_model |
| **Del MÉTODO** — cómo explorar | `brain_v2/methods/algorithm_memory.json` |

El segundo tiene cuatro clases: `INSTRUMENT` (hasta dónde ve un canal) · `SUBSTRATE` ·
`CARRIER` (una columna que lleva o no lleva lo que dice) · `TRAP` (una lectura que produce una
respuesta segura y equivocada).

**Su regla:** toda memoria lleva quién la aprendió, con qué evidencia, y **qué deben hacer
distinto los demás algoritmos**. *Una memoria sin implicación es una nota, y las notas no las
ejecuta una máquina.*

El conocimiento del dato lo consume un humano una vez; el del método, cada corrida futura.

## Las trampas que costaron llegar aquí

Todas produjeron una **cifra creíble desde un cruce roto**, que es el defecto más caro que hay:

1. **Un resumen no es un mapa.** Leer los top-317 de A4 en vez de correr su clasificador → "100% no entendemos nada".
2. **Un campo inexistente falla en silencio.** Buscar `domain_axes.process` (no existe) → mapa vacío, todo degradado. Ahora hay un `assert`.
3. **Un tcode no es un programa.** Pasar TCODEs pelados a un clasificador de programas → `XK01`, `SU01`, `PFCG` sin catalogar y un hueco inventado del **35%**.
4. **Tres stores desiguales no se eligen, se unen.** Las cadenas de proceso viven en tres sitios; leer el más fino dejaba CO, TRM, PBC, PM y SD sin cadena.
5. **`TABLE_WITHOUT_DATA` no significa vacía.** Significa que *tu selección* no devolvió filas. `KBLK` "vacía" con lista de campos, y con solo `BELNR` devolvía los documentos.
6. **Un techo tuyo no es un límite del sistema.** Se fijó una retención de 70 días llamándola medida cuando era el día más profundo que la sonda había probado. P01 servía **182**.
7. **Un patrón ingenioso captura de más.** `^AB[AZ]` para activos fijos se traga `ABAP4_CALL_TRANSACTION`.
8. **El resto sin clasificar es el sensor.** Los 44 `UNKNOWN` de A19 delataron una gramática entera que el autor no conocía.
9. **Comparar alcances distintos no es una derivada.** Al cablear la cuarta superficie el sin-clasificar subió de 2,66% a 5,09% sin que nadie entendiera menos.
10. **El instrumento aparece en su propia medida.**

## Cómo se dispara

Nada de esto depende de que alguien se acuerde:

- **`rebuild_all.py`** pasos 2j/2k: A19 filtra, A20 mide.
- **`run_analysis_cycle.py`**: A19 y A20 en su orden de dependencia.
- **`check_triggers.py`**: dispara si el sin-clasificar **sube** medio punto con el mismo
  alcance, si **no se mueve** (el bucle paró), o si cambia el alcance. Un tercer disparo es
  **AUTHORING** y no CYCLE a propósito: el grado 3 exige prosa y correr el ciclo otra vez no lo
  sube ni un punto.
- **`BRAIN_INDEX.md`** lleva el bloque, así que se llega desde el punto de entrada. *Guardar no
  es recuperar.*
- El agente **`log-process-discovery`** trabaja `keep_exploring`, ordenado por ejecuciones.

## Comandos

```bash
python process_mining/log_reality_filter.py      # A19 filtrar
python brain_v2/comprehension_index.py           # A20 medir
python brain_v2/domain_composition.py            # A22 abrir todos
python brain_v2/domain_composition.py PS         # A22 abrir uno
python brain_v2/case_spine.py                    # A21 caso -> documento
python brain_v2/methods/check_triggers.py        # qué toca re-correr y por qué
```
