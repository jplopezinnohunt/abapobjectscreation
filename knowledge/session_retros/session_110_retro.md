# Sesión s110 — medir el proceso propio, y equivocarme cuatro veces al medirlo

**Fecha:** 2026-08-30 · **Entrada:** continuación de s109. Sin incidente nuevo: la petición fue
*«corre el opportunity_watch cuando vuelva P01»*, y de ahí salió todo lo demás.

## Qué se pidió y qué salió

Se pidió correr los mineros. Al intentarlo, JP cortó con una corrección de arquitectura que
cambió la sesión entera: **«los mineros no deben correr contra P01, deben correr contra el
Golden»**. De ahí salieron tres días de trabajo comprimidos: el mecanismo de delta, la medición
del proceso propio, y el descubrimiento de que el catálogo no se encontraba a sí mismo.

## Lo que se construyó, y funciona

1. **Los 7 mineros de banca dejan de leer P01.** Medido el alcance antes de tocar: de 118
   instrumentos que leen datos SAP, 24 iban a P01 en vivo — y la capa de minería vieja estaba
   BIEN (`process_mining`: 24 contra Golden, 3 contra P01). El defecto estaba **concentrado en
   lo que yo construí en s108/s109: 7 de 7**.
2. **`gold_delta` con siete estrategias**, investigadas en varias fuentes (SAP ODP, Theobald,
   Qlik, BryteFlow), no inventadas: marca de agua, clave creciente, CDHDR, comparación por hash,
   y el sondeo en dos fases. **De 12 tablas ejecutables a 251**, con la clave derivada de `DD03L`.
3. **El delta sobre el log: 22 min → 7 s**, con las mismas conclusiones exactas. Recorría
   29,8 M de filas para encontrar 356.186 nuevas — el 1,2 % — y devolvía siempre lo mismo.
4. **La familia `bs*` completa**: seis tablas con clave única y delta ejecutable.
5. **El ciclo se cronometra solo** (`cycle_timings.json`) y dice por qué paso va.

## El hallazgo que más vale, y no era de banca

**Un campo de texto de SAP puede contener el carácter que usamos de delimitador.** Medido: 2
filas de 670.715 en `BSAS` 2024 traen `tr|_m. Hmedat` en `ZUONR`. El helper compartido hacía
`split("|")` y **rellenaba los huecos**, así que la fila seguía adelante con **todas sus
columnas corridas y sin error**. Solo dio la cara en un script que contaba los valores antes de
escribirlos; cualquier minero se habría comido el dato corrido.

Corregido cortando por **posición** (`OFFSET`/`LENGTH` del metadato), **en el helper compartido**
— hay 202 ficheros que parten por delimitador.

## Y el patrón de la sesión: CUATRO medidas mías malas

Todas la misma forma — **afirmar sobre un proxy antes de mirar el efecto**:

| dije | era |
|---|---|
| «68 minutos en un paso» | **145 s** — el resto era contención mía sobre el mismo SQLite |
| «un índice lo arreglará» | lo hizo **10× más lento** (37 s → 360 s) |
| «se perdieron 140 objetos» | muestras **capadas a 80**: otra rodaja, no otro pastel |
| «70 algoritmos sin código» | la distinción `script`/`bound_in` **ya existía**; 70 de 70 apuntan a ficheros que existen |

Lo incómodo: extendimos `feedback_a_gate_must_measure_the_effect_not_the_form` con los tres
primeros **y volví a hacerlo dos horas después**. La regla no protege si se aplica al mirar y no
se mira.

## Registrar no es encontrar

Tras un rebuild completo de 33 minutos, dos de cuatro preguntas seguían devolviendo `NADA` sobre
instrumentos que existían y estaban registrados. La causa: **un algoritmo se indexaba por su
nombre** — `state`, `mining_kind`, `bound_in`, `lands_in` — y nada de lo que dice **para qué
sirve**. El `preguntas_que_contesta` que yo había añadido **no lo leía ningún código**.

Arreglado: las cuatro contestan con su instrumento en primer lugar. Y `DEBERÍA_LEER` bajó de
**152 a 138** cerrando dos skills con punteros que dicen **qué** aplica, no el nombre suelto.

## SAP Learnings This Session (Fase 4b)

- **La nómina entra en `REGUP` sin documento FI** — `BELNR` vacío, `BUZEI='000'`, `GJAHR='0000'`.
  Verificado contra P01: pasa **en SAP**, no en nuestra copia. Claim 644.
- **`UPDAT` de `LFA1`/`LFB1` está vacío al 100 % también en P01.** SAP no lo mantiene; los
  cambios solo viven en `CDHDR`. Cualquier delta que lo asuma falla **en silencio**. Claim 645.
- **El agujero de los borrados, acotado con medida**: 0 tablas Z/Y con delta, 7 con marca de
  borrado lógico, y las propuestas de pago **no se borran** (tres meses idénticos Golden vs P01).
  Claim 646.
- **`AZDAT <= '<mes>31'` es el 31 de febrero** y SAP responde `SAPSQL_DATA_LOSS`, que suena a
  anchura de campo. Costó horas de diagnóstico equivocado. Guarda puesta en `rfc_helpers`.
- **`KUNNR` cierra la clave de `REGUH`**: 2.075 filas, 2.075 valores distintos.

## Aterrizaje

31 commits. Reglas 261 (2 extendidas, 0 creadas). Claims 644-647. Ciclo medido: **60,4 min,
29 pasos, 0 fallos** — y declara que es PARCIAL porque uno necesita RFC.

**Pendiente y es lo que toca:** `YFMXCHK` en `YFI_YRGGBS00_EXIT::U913` — una tabla que el brain
no explica, consultada desde el exit de sustituciones de FI, que **puede bloquear una
contabilización**. Es el patrón de `MV_EXTENSION_YEARS`: las reglas que deciden viven en el
código, y ningún análisis de configuración las ve.
