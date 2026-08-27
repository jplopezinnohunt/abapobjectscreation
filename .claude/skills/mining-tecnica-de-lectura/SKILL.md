---
name: mining-tecnica-de-lectura
description: >
  Mineria de tipo TECNICA_DE_LECTURA: no mina: HACE POSIBLE minar. Como leer una fuente que no se deja leer.
  Reune los 10 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore tecnica de lectura · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: TECNICA_DE_LECTURA

**Qué contesta esta clase:** no mina: HACE POSIBLE minar. Como leer una fuente que no se deja leer.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 10 mineros de esta clase

### `A1_chunked_temporal_read`

**Contesta:** read a purging log in bounded time windows (<=6h) because a wide call hangs and the connection degrades every ~12 calls

```bash
python Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py
```

**Cómo da una respuesta falsa:** a silently truncated window looks like a quiet period in the data

**Aterriza en:** n/a - technique: it shapes how data is read, it does not produce findings. Classified from its own `does` text, s099.

### `A2_rolling_window_accumulation`

**Contesta:** capture a window the source purges (7-120 days) into *_history tables, turning a window into a history

```bash
python Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py
```

⚠️ **estado `FRAGILE`** — su salida NO se cita sin comprobarla.

**Cómo da una respuesta falsa:** a missed day is invisible: the history simply has a hole nobody sees

**Aterriza en:** n/a - technique: it shapes how data is read, it does not produce findings. Classified from its own `does` text, s099.

### `A41_extract_fund_center_hierarchy`

**Contesta:** Descubre BAJO QUÉ SETCLASS vive de verdad la jerarquía estándar de centros gestores (el rollup oficina→región→sector→HQ), preguntándoselo a los datos en vez de creerse la clase documentada: lee SETLEAF sin filtro de clase con una muestra de FICTR reales y se queda con la clase que más los resuelve,…

```bash
python Zagentexecution/sap_data_extraction/scripts/extract_fund_center_hierarchy.py
```

**Cómo da una respuesta falsa:** CORREGIDO -- `Zagentexecution/sap_data_extraction/scripts/extract_fund_center_hierarchy.py` no produce una respuesta falsa: NO PRODUCE NINGUNA. Es codigo muerto que nunca ha corrido, con tres paradas duras encadenadas y dos defectos de diseno latentes que solo morderian si alguien lo repara sin mirar. TRES PARADAS DURAS (medidas hoy, en el orden en que se encuentran): 1. NameError. `quoted_in()` se invoca en las…

**No puede ver:** No puede correr tal cual (NameError en `quoted_in`, líneas 93 y 186) y no podría aunque se arreglara, porque su forma de consultar (`IN (...)`) la rechaza el wrapper seguro de P01. No distingue un árbol de centros gestores de uno de centros de coste: no lee `SETHEADER.TABNAME/FIELDNAME/ROLLNAME`,…

**Aterriza en:** Gold DB: setheader (175) · setheadert (166) · setnode (150) · setleaf (878) para SETCLASS=0312 + _fund_center_hierarchy_manifest

### `A48_run_progress_from_its_own_log`

**Contesta:** contestar POR DONDE VA un proceso largo leyendo la ultima marca de paso de su log y si el log se mueve, sin abrir el proceso ni adivinar por mtimes de artefactos

```bash
python brain_v2/rebuild_progress.py
```

**Cómo da una respuesta falsa:** reconstruir 'la corrida completa' de un log que SE ACUMULA entre ejecuciones. La v1 lo intentaba cortando por la marca de Step 0, el corte fallaba y MEZCLABA corridas: reporto 'TERMINADO 7/7, 148 minutos' con el proceso vivo en el paso 4. Y el marcador de fin obvio NO sirve: 'Rebuild complete.' va a stdout y no llega al curation.log (2 ocurrencias en 80k lineas, las dos de corridas viejas). TAMPOCO se puede derivar…

**Aterriza en:** n/a - instrumento: contesta en PANTALLA, no produce artefacto

### `A48_semantic_activity_map`

**Contesta:** Convierte un log crudo de arranques de transaccion en un log de PROCESO etiquetado: cada tcode -> (actividad de negocio, proceso, clase de riesgo de control), y ademas MIDE LO QUE NO SABE NOMBRAR — la cola sin etiquetar ordenada por volumen, que es la lista de trabajo del hueco de comprension. Es…

```bash
python process_mining/semantic_activity_map.py
```

**Cómo da una respuesta falsa:** MEDIDO al correrlo contra el golden P01 (Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db), y ya contamina claims TIER_1. CAUSA RAIZ — process_mining/semantic_activity_map.py:65-66 lee la COLUMNA EQUIVOCADA. En rsau_audit_history con TXSUBCLSID='Transaction Start' (MSG='AU3' = "Transaction &A started"), el tcode ARRANCADO vive en PARAM1; SLGTC es el tcode de CONTEXTO desde el que se lanzo. Medido:…

**No puede ver:** · NO sabe si la transaccion HIZO algo: `Transaction Start` es que se abrio la pantalla, no que se contabilizo un documento. No hay documento, ni importe, ni objeto tocado. ME21N arrancada != pedido creado; para eso hace falta CDHDR/BKPF. · NO ve el canal donde ocurre el trabajo de verdad: 1,24M…

**Aterriza en:** PENDIENTE. No escribe nada: `main()` solo imprime a stdout. No hay JSON de salida, no toca el golden, no publica en `mining_bus` (no lo importa). Sus hallazgos…

### `A50_transport_content_extraction`

**Contesta:** traer al Gold QUE OBJETO viaja en QUE transporte. Sin esto se sabe que hubo un transporte y no que se movio, que es la unica pregunta interesante: 15 scripts analizan transportes y hasta hoy ninguno podia ver su contenido

```bash
python scripts/extraction/extract_fsv_structure.py
```

**Cómo da una respuesta falsa:** CUATRO, LAS CUATRO MEDIDAS EL 2026-08-25/26 Y LAS CUATRO MIAS. (1) DUPLICADO POR RE-PEDIR UN PREFIJO ENTERO: un prefijo entraba en la lista de pendientes si tenia UNA cabecera sin contenido, y entonces se pedia ENTERO. D01K tiene 10 transportes VACIOS -- cabecera sin objetos -- que no van a estar cubiertos nunca, asi que quedaba pendiente para siempre. Entre dos pases entraron 4.266.812 filas repetidas y la tabla…

**Aterriza en:** Gold DB tabla e071 -- 2.369.936 objetos en 14.939 transportes, con indice UNICO (TRKORR, AS4POS)

### `A56_audit_slot_aggregate`

**Contesta:** colapsar UNA sola vez los dos flujos de evento en un agregado EXTERNO E INDEXADO -- slots (usuario, programa, dia, hora) + conteos de cambio + los valores crudos de PARAM3/PARAMX -- para que cualquier algoritmo de comportamiento pregunte por clave en vez de pagar un escaneo completo. No responde…

```bash
python brain_v2/build_audit_slots.py
```

**Cómo da una respuesta falsa:** SUS TRAMPAS LAS HEREDA EN SILENCIO TODO EL QUE LO LEA -- y hoy las hereda sin verlas. (a) LA MARCA DE AGUA SOLO DETECTA CRECIMIENTO. `_watermark` (lineas 49-52) es `MAX(SAL_DATE)|MAX(UDATE)`, y si coincide el script imprime 'up to date -- nothing to rebuild' y sale 0 (63-71). Una RE-EXTRACCION que anada historia ANTIGUA, o una correccion de filas ya presentes, no mueve el maximo: el agregado se queda viejo mientras…

**Aterriza en:** Zagentexecution/sap_data_extraction/sqlite/derived_audit_slots.db (build_audit_slots.py:43) -- 145 MB, 987.322 slots, 507.091 grupos de cambio, 41.171 valores…

### `A57_extraction_method_resolver`

**Contesta:** responder 'como leo X y como lo analizo' sin volver a descubrirlo cada sesion. NO es una lista de tablas: es un RESOLVEDOR -- por clase DD02L cubre cualquier tabla sin enumerarla, y encima lleva las restricciones que costaron dias (P01 rechaza ROWSKIPS, RSAU se trocea a <=6h o la conexion se…

```bash
python process_mining/method_registry.py
```

⚠️ **estado `WEAK`** — su salida NO se cita sin comprobarla.

**Cómo da una respuesta falsa:** CONTESTA CON APLOMO CUANDO NO SABE, Y ADEMAS LO GUARDA. (a) `resolve()` traga el fallo del lookup DD02L (`except Exception: pass`, lineas 71-72) y cae a `TYPE_RULE.get(None, ...)` = 'RFC_READ_TABLE (assumed transparent -- verify class)' (linea 73). Sin conexion P01 -- el caso NORMAL de una sesion offline -- TODA tabla vuelve como RFC_READ_TABLE, incluidas las CLUSTER que RFC_READ_TABLE no puede leer en absoluto. El…

**Aterriza en:** brain_v2/method_registry.json (method_registry.py:79 y 96)

### `A61_capability_footprint_in_log`

**Contesta:** contestar SI UNA CAPACIDAD DEJA HUELLA ANTES DE CONCLUIR NADA DE SU SILENCIO. Se le da el conjunto de nombres por los que esa capacidad se manifestaria -- transacciones, modulos de funcion, destinos, programas -- y barre el log entero buscandolos en todas las superficies, no solo en la del nombre…

```bash
python Zagentexecution/tasks/2026_08_26_inc16471_ads_log_mining/ads_outage_window_check.py
```

**Cómo da una respuesta falsa:** LEER EL SILENCIO COMO AUSENCIA. Es el modo de fallo central y el que costo el caso ADS: cero eventos de FP_JOB_OPEN en 6,5 meses NO significa que no se renderizo ni un PDF -- significa que el render Adobe no pasa por el log de auditoria. Quien lea eso como 'no se usa' retira un canal vivo. Modos secundarios: barrer una sola superficie (el nombre puede aparecer en PARAM3 y no en SLGREPNA); tomar una ventana mas corta…

**Aterriza en:** ['brain_v2/claims/claims.json', 'brain_v2/log_reality.json', 'process_mining/mining_bus.py (publicar REALIDAD)']

### `A67_variant_write_safety`

**Contesta:** COPIAR UNA VARIANTE SIN ROMPERLA, sabiendo que las dos formas de romperla NO DAN ERROR. (1) La lectura devuelve fechas en formato EXTERNO (31.07.2026) y la escritura las quiere INTERNO (20260731): mandarlas tal cual escribe basura -- '20.7..31.0' -- y el sistema acepta. (2) Lo que no se envia se…

```bash
python Zagentexecution/tasks/2026_08_21_variant_alignment/variant_align.py
```

**Cómo da una respuesta falsa:** ESCRIBIR SIN SNAPSHOT PREVIO. Los dos modos de rotura son SILENCIOSOS, asi que sin el PRE no hay a que volver: medido en V01, tres variantes cuyas fechas eran IDENTICAS a P01 quedaron corruptas por copiarlas sin convertir, y se repararon solo porque existia el snapshot. Segundo modo: confundir el rango OBSERVADO en los datos con el CONFIGURADO en la variante -- analisis previos describian UNES_UNBA como…

**Aterriza en:** ['la variante del sistema destino', 'PRE_*.json como evidencia']

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
