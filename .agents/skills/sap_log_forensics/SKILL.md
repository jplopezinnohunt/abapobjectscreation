---
name: sap_log_forensics
description: Minar el log de auditoria de SAP para DESCUBRIR PROCESO y para RESOLVER INCIDENCIAS -- son el mismo metodo. Fechar un evento que el sistema no registra, medir quien hace que y cuando, y saber cuando el log NO puede contestar. Usar cuando haya que datar una caida, medir el uso real de una aplicacion, encontrar la poblacion afectada por un fallo, o probar que algo dejo de funcionar.
model: sonnet
---

# SAP Log Forensics

Minas el log de auditoría de SAP. Dos usos, **un solo método**:

- **PROCESS MINING** — quién ejecuta qué, cuándo, por qué canal, con qué intensidad, y cómo cambia.
- **RESOLUCIÓN DE INCIDENCIAS** — cuándo empezó, a cuánta gente afecta, qué dejó de funcionar.

Son la misma disciplina: **población, línea base, grupo de control, y una medida que decide.** Un
incidente es process mining con una ventana estrecha y una pregunta urgente.

---

## LA REGLA QUE TE DEFINE

> **Una ausencia es evidencia sólo en proporción a la densidad de la presencia.**

Casi todo lo que sale mal en este oficio es leer un silencio como una señal. Antes de decir *"dejó
de pasar el día X"*, **mide cuántas veces ese silencio ya había pasado con todo funcionando.**

Caso medido (INC-000016471): `ADS_AGENT` calló desde el 21 de agosto y encajaba perfectamente con
el fallo. Era falso. Ese sensor dispara **88 de ~200 días (44%)** y su silencio de 4 días **había
sido igualado o superado ocho veces**, con tres huecos de 6 días. No podía fechar nada.

---

## EL SUSTRATO — qué hay y qué miente

| Tabla | Qué es | Volumen medido |
|---|---|---|
| `rsau_audit_history` | SM20/RSAU — el log de auditoría de seguridad, **acumulado por nosotros** | ~29,4M filas |
| `rsau_audit_signal` | el mismo, filtrado a eventos con señal | ~10,5M |
| `cdhdr_history` | cabeceras de documento de cambio | ~14M |
| `tbtco_history` / `tbtcp_history` | jobs y sus pasos/variantes | ~200K / ~251K |
| `sm21_syslog_history` | syslog | 2.402 — **y parado desde 2026-06-22** |
| `snap_history` | ST22 | **0 filas: CIEGO, ver abajo** |

**P01 purga; nosotros acumulamos.** Retención real medida en P01: **≥182 días** (no los ~14 que el
acumulador asumió durante meses). Correr el acumulador cada ≤14 días es lo que hace que las
ventanas solapen y la historia sea continua.

### Campos que importan en `rsau_audit_history`

```
SAL_DATE  SAL_TIME     cuándo (AAAAMMDD / HHMMSS)
SLGUSER                quién
MSG                    clase de evento: AU1 logon OK · AU3 arranque de transacción · ...
SLGREPNA               programa
SLGTC                  código de transacción del CONTEXTO
PARAM1..PARAM3 PARAMX  la carga útil — y aquí es donde está casi todo
SLGLTRM2 / TERM_IPV6   terminal / IP de origen
```

---

## LAS SEIS TRAMPAS MEDIDAS (léelas antes de medir, no después)

**1. `PARAM1`, no `SLGTC`, para contar transacciones.** Con `TXSUBCLSID='Transaction Start'`
(`MSG='AU3'`), la transacción **arrancada** vive en `PARAM1`; `SLGTC` es la del contexto. Contar
por `SLGTC` cuenta otra cosa.

**2. El `LIKE` de tres letras no es una búsqueda.** `PARAM3 LIKE '%ADS%'` devuelve **2.831 filas y
ninguna es ADS**: el `LIKE` de SQLite es insensible a mayúsculas y **`Downloads` contiene `oads`**.
Ancla el patrón o cuenta con que publicas un canal que no existe.

**3. El último día del corpus SIEMPRE está incompleto y se lee como una caída.** Comprueba el
volumen del día y su `MAX(SAL_TIME)` antes de leer cualquier serie como un corte. Un día laborable
completo son **~157.000 filas**; si ves 23.834 hasta las 05:31, eso es tu extracción, no la
realidad.

**4. El acumulador rellena el hueco MÁS ANTIGUO, no el más nuevo.** `derive_rsau_days` elige por
antigüedad: una corrida rutinaria trajo el **3 de marzo** cuando el incidente era del **25 de
agosto**. **Si necesitas días recientes, fuerza `--rsau-days N`.** Sin eso concluirás "el log no
llega" y te equivocarás.

**5. Efecto observador.** Nuestras propias lecturas de P01 por RFC quedan en el mismo log que
medimos: **264.521 filas (0,93%)**. Un dominio parecía más vivo cuanto más lo mirábamos. Toda
métrica sobre el log necesita excluir al observador.

**6. Una consulta dentro de un bucle son N barridos de 29M filas.** Saca el dato de una vez a un
diccionario. Y **acota por `SAL_DATE` primero, siempre**.

### Y lo que este instrumento NO puede

- **`snap_history` es ciego dos veces.** 0 filas, porque P01 devuelve `TABLE_NOT_AVAILABLE` por
  `RFC_READ_TABLE` y el acumulador lo lleva desactivado; y aunque se llenara, su esquema
  (`DATUM/UZEIT/AHOST/UNAME/MODNO/SEQNO`) **no lleva programa ni texto de error**: jamás podría
  contestar *"un volcado que mencione X"*. `st22_dumps_history` sí lleva `ERROR_CLASS/MESSAGE` pero
  tiene 1 fila.
- **Lo que ocurre fuera del ABAP no está.** Un fallo de autenticación en el UME de Java no tiene
  sujeto ABAP al que atribuirse: **no puede** aparecer, ni en principio. Eso es **frontera del
  instrumento, no hueco de datos** — no se cierra acumulando más log.
- **Muchos hechos no dejan evento.** Medido: el render de un formulario Adobe deja **CERO** eventos
  `FP_*` en 6,5 meses. No es que la traza esté apagada: el evento no existe.

---

## EL MÉTODO — seis pasos

### 1. ¿Deja traza el hecho? Pregúntalo ANTES de buscarlo

Barre las cuatro superficies (`SLGREPNA`, `SLGTC`, `PARAM1`, `PARAM3`) sobre una ventana amplia. Si
sale cero en 6 meses, **el evento no existe** y todo lo que sigue cambia: pasas de medir el hecho a
medir su sombra.

Decirlo en voz alta es un resultado, no un fracaso: *"este hecho es invisible para este log"* es
información que evita que la siguiente sesión lo busque otra vez.

### 2. Si no deja traza, busca una POBLACIÓN PROXY

Normalmente: **lo que una persona hace al reaccionar.** Un botón que falla genera reintentos, y los
reintentos sí son eventos.

> **Cuando la máquina no tiene sensor, el sensor son las personas.**

La métrica útil casi nunca es el volumen: es la **intensidad** — eventos **por usuario**. El
volumen sube porque hay más gente; la intensidad sube porque la misma gente repite.

### 3. Mide la TASA BASE antes de leer cualquier desviación

Para un sensor escaso, la distribución de **huecos**:

```sql
-- días con evento, y de ahí la distribución de silencios
SELECT DISTINCT SAL_DATE FROM rsau_audit_history WHERE SLGUSER='<X>' ORDER BY SAL_DATE
```
Si el silencio actual cabe dentro de lo normal, **el sensor no puede fechar** y hay que decirlo.

Para una serie densa, la línea base de intensidad de las 2-3 semanas sanas anteriores.

### 4. Exige GRUPO DE CONTROL

Una subida sin control es *"lunes ajetreado"*. **Busca la población gemela que NO debería moverse**
— misma gente, misma plataforma, mismo tipo de objeto, distinta dependencia:

| | app afectada | familia gemela |
|---|---|---|
| línea base | 2,5 · 2,4 | 2,9 · 2,8 |
| **día del fallo** | **5,9** | 2,6 |
| siguiente | **4,5** | 2,2 |

Eso convierte un número en una prueba. Sin la columna de la derecha no tienes nada.

### 5. Acota con el sensor directo, no fecher con él

Un sensor escaso (un usuario de servicio, un job) **acota** la ventana — *"funcionaba el viernes a
las 14:35"* — pero **no la fecha**. Combina: el sensor directo da el límite superior, el proxy da
el momento.

### 6. Cierra con una SONDA DIRIGIDA

**El log da el mapa; el diagnóstico lo cierra una medida bien elegida.** Un abanico que no termina
en una sonda dirigida produce un informe, no una respuesta.

En INC-000016471 el log dio: qué aplicación, cuánta gente, qué ventana, qué máquina, dos
credenciales, y el radio HR+FI+RE. **La respuesta la dio una petición HTTP de 20 líneas.**

---

## CONSULTAS QUE YA FUNCIONAN

```sql
-- Completitud del corpus: ANTES de nada
SELECT SAL_DATE, COUNT(*), MIN(SAL_TIME), MAX(SAL_TIME)
FROM rsau_audit_history WHERE SAL_DATE >= ? GROUP BY SAL_DATE ORDER BY SAL_DATE;

-- Uso real de una aplicación / objeto, con INTENSIDAD
SELECT SAL_DATE, COUNT(*) n, COUNT(DISTINCT SLGUSER) u
FROM rsau_audit_history WHERE PARAM1 LIKE '%<OBJ>%' AND SAL_DATE >= ?
GROUP BY SAL_DATE ORDER BY SAL_DATE;          -- intensidad = n/u

-- Contraste con el grupo de control, en una sola pasada
SELECT SAL_DATE,
  SUM(CASE WHEN PARAM1 LIKE '%<OBJ>%' THEN 1 ELSE 0 END),
  COUNT(DISTINCT CASE WHEN PARAM1 LIKE '%<OBJ>%' THEN SLGUSER END),
  SUM(CASE WHEN PARAM1 LIKE '%<OBJ>%' THEN 0 ELSE 1 END),
  COUNT(DISTINCT CASE WHEN PARAM1 LIKE '%<OBJ>%' THEN NULL ELSE SLGUSER END)
FROM rsau_audit_history WHERE PARAM1 LIKE '%<FAMILIA>%' AND SAL_DATE >= ?
GROUP BY SAL_DATE ORDER BY SAL_DATE;

-- ¿Quién entra desde un host? (latido de una máquina externa)
SELECT SAL_DATE, SLGUSER, COUNT(*), MIN(SAL_TIME), MAX(SAL_TIME)
FROM rsau_audit_history WHERE SLGLTRM2 = '<IP>' AND SAL_DATE >= ?
GROUP BY SAL_DATE, SLGUSER ORDER BY SAL_DATE;
```

> **Un latido ENTRANTE no prueba una ruta SALIENTE.** Dirección, puerto e instancia son tres
> dimensiones independientes: una sonda valida exactamente la tupla que ejercitó. Una máquina puede
> latir hacia P01 por su instancia ABAP mientras su instancia Java está parada — pasó.

---

## TRAER LA VENTANA

```bash
python Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py                    # rutina
python Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py --rsau-only --rsau-days 6
python Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py --verify           # sin P01
```
Sólo lectura sobre P01 por SNC/SSO. **Un solo escritor** sobre el Gold DB (ADR-008): si lo estás
corriendo, díselo a los mineros en paralelo — si no, medirán contra una tabla que crece y
publicarán denominadores distintos del mismo hecho. Pasó.

---

## CÓMO SE ENTREGA

Toda cifra **MEDIDA** (con su consulta y su ventana) o **INFERIDA**. Nunca mezcladas. Un proxy se
declara proxy: *"cuento arranques de la aplicación, no clics en el botón — ese clic no genera
evento"*.

- Incidencia → `knowledge/incidents/INC-<id>_<slug>.md` **con BRIEF de 60 s** + registro en
  `brain_v2/incidents/incidents.json`. Gate: `incident_record_coverage_check.py`.
- Descubrimiento → claims + publicar en el bus (`process_mining/mining_bus.py`) para que otros
  mineros lo consulten.
- Trampa nueva → `brain_v2/methods/algorithm_memory.json` (INSTRUMENT / SUBSTRATE / CARRIER / TRAP).

## RELACIONADO

`A61_event_dating_without_a_trace` (este método, registrado) · `A18_reality_filter` ·
`A19_log_reality_filter` · `A7_concept_drift` · `A8_change_to_executor_attribution` ·
`A56_audit_slot_aggregate` · `A62_lazy_generated_object_as_usage_proof` ·
`A60_outbound_channel_availability` (la sonda dirigida del paso 6, para canales salientes) ·
`.agents/skills/sap_process_mining/` · `.agents/skills/sap_incident_analyst/`
