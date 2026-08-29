# Sesión s109 — los mineros dejan de censar y empiezan a buscar

**Fecha:** 2026-08-28 → 29 · **Entrada:** continuación de s108. No hubo incidente nuevo: la
petición fue *«corre el toolgraph con las preguntas de esta sesión»* y, de ahí, *«los mineros
deben encontrar oportunidades, riesgos y desafíos y registrarlos»*.

## Qué se pidió y qué salió

Se pidió **validar la puerta de entrada** con las preguntas reales de la sesión anterior y hacer
que **los agentes intervinieran de verdad**. Salió que la puerta estaba rota, que los agentes
encuentran cosas que yo no, y que mis propios instrumentos tenían dos defectos de construcción
que ninguna puerta veía.

## Lo que se aprendió del MÉTODO

1. **La puerta de entrada estaba ciega a nuestro idioma.** El toolgraph indexaba el 28 % de las
   descripciones de skill; se preguntaba en español contra un corpus en inglés. Cuatro defectos
   medidos, glosario ES→EN + peso IDF, cobertura al 100 %, y una batería de 12 preguntas reales
   como regresión (`toolgraph_retrieval_check.py`). **Sigue sin ser perfecta:** dos de las doce
   fallan hoy y están declaradas, no escondidas.

2. **Un minero no censa: BUSCA.** Ese fue el giro de la sesión y lo marcó el usuario tres veces
   («no, no es eso — debe buscar oportunidades», «y desafíos y registrarlos», «no hay nadie mejor
   que el minero para verlo»). El contrato `_hallazgos.py` fija cuatro clases —OPORTUNIDAD ·
   RIESGO · **DESAFÍO** · DATO— seis formas genéricas de búsqueda y tres reglas duras: sin tamaño
   no se publica (`ValueError`), se declara el límite, se declara el denominador. Cableado en los
   siete mineros del dominio.

3. **Los agentes encuentran lo que yo no, y me corrigen.** El árbitro de minería no desempató
   16-vs-80: descubrió que la Gold DB solo tiene el **41,7 %** de las filas de `FEBKO` y el 45 %
   de los bancos, y que yo contaba `REGUH` sin filtrar `XVORL='X'`. El agente de SoD encontró un
   riesgo de **2,4 M USD** en una cuenta (Kabul) que no estaba en ninguna lista mía.

4. **Un verde puede ser «no miré».** Registré D1–D6 en la **raíz** de `algorithms.json`, fuera
   del contenedor que la puerta recorre: `algorithm_landing_check` daba PASS sin haberlos mirado
   nunca. Y los prefijos colisionaban con entradas que ya significaban otra cosa. Migrados a
   A72–A78; el registro pasó de 98 a 105.

5. **Código tras un `return` dejó el hallazgo más grave sin nombres.** Los nueve pares del ciclo
   completo se publicaron como agregado —«9 pares»— y no se imprimieron ni se guardaron jamás.
   Auditoría no puede revisar «9 pares».

Los dos últimos son la misma falta y ahora son **regla**: `feedback_gate_coverage_is_bounded_by_what_it_walks`
y `feedback_an_aggregate_finding_without_named_subjects_is_not_actionable` (ambas CRITICAL).

## SAP Learnings This Session (Fase 4b)

- **Segregación de funciones en el extracto tecleado a mano** (P01/UNES, 2025→hoy). De 34 cuentas
  vivas que reciben algún extracto tecleado, 17 pagan; en **14** hay alguien en los tres eslabones
  (teclea + contabiliza + paga). Atribuido **pago a pago**: 420 de 1.249 pagos y **2.401.283 USD
  de 4.222.714 (57 %)**, 16 personas. Mayores: AIB01-USD01 Kabul 1.412.699 y BTE01-IRR02 Teherán
  536.669. En **7 de las 14 el solape es una sola persona**. → claim 642, PMO H145,
  `Zagentexecution/quality_checks/bank_statement_sod_check.py`.
- **La atribución correcta es al pago, no a la cuenta.** Contar el importe entero de la cuenta
  daba 96 %; por pago da 57 %. Escrito en el código, no solo en el retro.
- **Ciclo de cuatro eslabones** (crea la factura además): 60 pagos, 65.409 USD, **9 pares con
  nombre**. Y una asimetría que nadie habría adivinado: **no son subconjunto** del hallazgo de
  tres — allí «teclea» exige teclear *y* contabilizar líneas, aquí basta con teclear. Por eso
  `CBE01-ETB04/M_TADESSE` (16 pagos) sale en el de 4 y no en el de 3: su extracto tiene **cero
  líneas**. → claim 642 extendido.
- **BCM no puede cubrir estas cuentas y no es un defecto:** las 17 pagadoras tienen cero lotes
  BCM porque sus pagos son **100 % cheque prenumerado** (`REGUH.RZAWE='3'`) y BCM libera
  *ficheros*. → hallazgo DATO en el bus.
- **La Gold DB no es completa para `FEBKO`:** 41,7 % de las filas, 45 % de los bancos. Toda medida
  de extractos contra el Gold está sesgada; hay que ir a P01. → hallazgo del árbitro.
- **Corrección de una cifra publicada por mí:** «8 cuentas manuales / 4 personas / 1.712 líneas»
  era falso. Real: **39 cuentas (34 vivas) / 41 personas / 13.942 líneas**. Dos causas: la
  etiqueta de canal deriva de la *presencia* de E/M (una cuenta 97 % manual figura MIXTA), y el
  filtro usaba un porcentaje **redondeado**. Barrido a los 10 ficheros donde vivía la cifra vieja.

## ⚠️ MEJORAS Y RIESGOS — dónde se recuerdan, no aquí

Esto es lo que la sesión pide recordar, y **el sitio para recordarlo no es este fichero**: un
retro se lee una vez. Viven en un registro **generado del bus**, que es el único que dice **desde
cuándo** está abierto cada cosa:

| dónde | qué es |
|---|---|
| `.agents/intelligence/PMO_OPORTUNIDADES.md` | **19 hallazgos vivos** de 7 mineros: 🔴 6 riesgos · 🟠 7 desafíos · 🟢 4 oportunidades · ⚪ 2 datos. Generado — no editar. |
| `companions/oportunidades_y_desafios.html` | el mismo registro, visual |
| `process_mining/mining_findings.json` | el bus: la fuente. Cada corrida **reemplaza lo suyo**, así que *lo que desaparece es lo que dejó de encontrarse* |
| `.agents/intelligence/PMO_BRAIN.md` H144 · H145 | los dos temas que necesitan decisión humana |

Regenerar: `python scripts/build_oportunidades.py`.

**Los tres que no deben perderse de vista:**

- 🔴 **H145 — SoD en el extracto tecleado.** 2,4 M USD sin tercero en SAP. **El límite es la mitad
  de la lectura:** mide *concentración de control*, **no** ausencia de control ni fraude — las dos
  firmas físicas del cheque no están en SAP. La acción no es acusar: es **declarar por cuenta
  quién teclea y quién paga**, o nombrar dónde vive el control físico. Hoy no está nombrado.
- 🟠 **7 desafíos esperan que alguien conteste.** Un desafío no es fallo ni mejora: es una pregunta
  que el minero no puede resolver solo. Varios apuntan a BFM/TRS y a DBS.
- 🟢 **H144 — la naturaleza de cuenta bancaria no está modelada** (viene de s108, sigue vivo).

## El cierre encontró más de lo que venía a cerrar

La puerta de la tríada (*objeto · proceso · método*) dio **NO en proceso y NO en método** para
`INC-000013624`, teniendo los tres. La causa: el incidente declaraba `domain: "Treasury_EBS"`, que
**no existe** — el dominio real es `Treasury`, subtopic `bank_statement_ebs`. Un incidente cuyo
dominio no resuelve queda desconectado de sus docs, companions e instrumentos.

Corregido, y de paso wireado lo que s108/s109 escribieron y nadie había enganchado: **Treasury
pasa de 9 a 14 docs y de 2 a 9 instrumentos**. Los dos parámetros de variante que deciden de
dónde sale el fichero (`FEB_IMP_SOURCE`, `FEB_FILEPATH`) no estaban en ningún registro — el job
se conocía y sus parámetros no. Aterrizados en el claim 536. **La tríada de este incidente ahora
es OK · OK · OK.**

Y **es la regla de hoy aplicándose a sí misma el día que se escribió**: la puerta de ontología
que impide materializar un dominio inventado **solo recorre los claims, no los incidentes**.

**Luego cometí el mismo modo de fallo al medirlo.** Publiqué «11 de 19 incidentes declaran un
dominio inexistente» contando como inventadas `BASIS`, `Security`, `Infrastructure` y
`Brain_Architecture` — que **sí están registradas** como claves transversales. Me corrigió el
propio validador en su salida. Medido bien: **9 de 16**, y no son invenciones sino **alias sin
resolver** (`BCM`→Payment_BCM, `HR`→HCM, `CTS`→Transport_Intelligence, `MasterDataConfig`→
Master_Data_Governance). Es un **DESAFÍO**, no un riesgo. Está en el registro con la corrección
escrita dentro del propio límite, no borrada.

## Lo que corregí de mí mismo

- Dije que el steward «afirmó tres registros y solo entró uno». **Mis dos sondas leían el nivel
  equivocado del JSON.** El steward tenía razón; el defecto (registro en la raíz) era mío.
- Al encargar el segundo pase afirmé que los hechos nucleares de SoD eran nuevos. **Ya estaban
  centrales desde `e6b977e`.** El steward lo comprobó contra el store en vez de fiarse de mi
  inventario y no los duplicó.

Las dos veces el fallo fue el mismo: **verificar contra mi memoria en vez de contra el fichero.**

## Aterrizaje

11 commits (`bd32832` → `85c8199`), todos en `origin/master`. Reglas 258 → 260 · registro de
algoritmos 98 → 105 · mineros 72 → 74 · gates 62 → 70 · cobertura del brain 100,0 % (2180/2180),
0 blind spots · claims 642.

**Sigue pendiente y es lo más frágil:** `D:` no está conectado, así que la Golden DB (21,25 GB) y
`~/.claude` **no tienen copia fuera de este disco**. Git no los protege.
`python scripts/backup_golden.py --dest D:\claude_backups` en cuanto conecte.

**P01 estaba caído al cerrar** (`WSAETIMEDOUT` contra `172.16.4.100:4800`) — red, no código. El
segundo pase del minero de SoD no llegó a completar; el límite corregido se editó en el bus a
mano y los datos vienen del pase que sí terminó.
