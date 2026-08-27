---
name: mining-codigo-como-fuente
description: >
  Mineria de tipo CODIGO_COMO_FUENTE: que HACE el sistema leido de su propio fuente ABAP -- las reglas que DECIDEN viven muchas veces en el codigo y no en la configuracion, y ningun analisis de customizing las ve.
  Reune los 13 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore codigo como fuente · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: CODIGO_COMO_FUENTE

**Qué contesta esta clase:** que HACE el sistema leido de su propio fuente ABAP -- las reglas que DECIDEN viven muchas veces en el codigo y no en la configuracion, y ningun analisis de customizing las ve.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 13 mineros de esta clase

### `A16_payroll_end_to_end`

**Contesta:** discover payroll end to end in six parts: the ENGINE (schemas), the LOGIC (rules), the OUTPUT (wage types, grouped by stem), the GATES (features), the MASTER DATA including whether it is maintained by hand or fed, and the POSTING path with the enhancements sitting on it

```bash
python process_mining/payroll_discovery.py
```

**Cómo da una respuesta falsa:** chasing the account determination through the FI configuration for three extractions before measuring the field widths. The fix is now part 7: read the documents

**Aterriza en:** brain_v2/payroll_discovery.json (dataset) -> brain_v2/claims/claims.json + knowledge/domains/PY/*.md - the engine, its rules and its gates

### `A39_fx_revaluation_scope_by_nature`

**Contesta:** Descubre QUE CUENTAS DEBERIAN REVALUARSE Y NO SE REVALUAN, entrando por la NATURALEZA de la cuenta (lo que el balance que la sociedad EJECUTA presenta como banco, caja, deposito, letras del tesoro o inversion) y no por su configuracion. Es la unica puerta que ve una cuenta sin OB09 y sin variante:…

```bash
python Zagentexecution/quality_checks/fx_revaluation_scope_check.py
```

**Cómo da una respuesta falsa:** DOS MECANISMOS, LOS DOS MEDIDOS EN P01 EL 2026-08-25 CORRIENDO EL PROPIO CHECK. (1) LA ILUSION DE ALCANCE — la respuesta verosimil y falsa. Con las 5 posiciones por defecto (1.1.1.1 / 1.1.1.2 / 1.1.2.1 / 1.1.2.3 / 1.2.1.1) la corrida de hoy da exit 1 con FALTA VARIANTE=1 (0004041011 Term Deposits Principal), FALTA DETERMINACION=2 (0001101601 Tashkent, 0001194311 Harare) y FUERA DE TODO=0, sobre una poblacion de 1084…

**No puede ver:** NO decide si una cuenta DEBE revaluarse -- el alcance correcto es un juicio de negocio (Tesoreria); el check lo acorrala con datos. NO ve fuera de las posiciones que se le pasen: con el defecto, ~2% de la clase de defecto medida sobre el balance entero. NO clasifica el MODO de seleccion…

**Aterriza en:** PENDIENTE — hoy solo IMPRIME y devuelve exit 0/1. No escribe store, no publica en mining_bus, no toca claims. El conocimiento de sus corridas llego al brain A…

### `A41_extract_fund_center_hierarchy`

**Contesta:** Descubre BAJO QUÉ SETCLASS vive de verdad la jerarquía estándar de centros gestores (el rollup oficina→región→sector→HQ), preguntándoselo a los datos en vez de creerse la clase documentada: lee SETLEAF sin filtro de clase con una muestra de FICTR reales y se queda con la clase que más los resuelve,…

```bash
python Zagentexecution/sap_data_extraction/scripts/extract_fund_center_hierarchy.py
```

**Cómo da una respuesta falsa:** CORREGIDO -- `Zagentexecution/sap_data_extraction/scripts/extract_fund_center_hierarchy.py` no produce una respuesta falsa: NO PRODUCE NINGUNA. Es codigo muerto que nunca ha corrido, con tres paradas duras encadenadas y dos defectos de diseno latentes que solo morderian si alguien lo repara sin mirar. TRES PARADAS DURAS (medidas hoy, en el orden en que se encuentran): 1. NameError. `quoted_in()` se invoca en las…

**No puede ver:** No puede correr tal cual (NameError en `quoted_in`, líneas 93 y 186) y no podría aunque se arreglara, porque su forma de consultar (`IN (...)`) la rechaza el wrapper seguro de P01. No distingue un árbol de centros gestores de uno de centros de coste: no lee `SETHEADER.TABNAME/FIELDNAME/ROLLNAME`,…

**Aterriza en:** Gold DB: setheader (175) · setheadert (166) · setnode (150) · setleaf (878) para SETCLASS=0312 + _fund_center_hierarchy_manifest

### `A42_fm_executed_census`

**Contesta:** Contrasta el catalogo estatico de PSM-FM contra la evidencia de EJECUCION real y responde, por objeto: quien lo corre, por que canal (dialogo / report / RFC-BAPI / job batch) y cuanto. De ahi salio que solo el 15,7% de las 1.331 transacciones FM del catalogo esta viva (473 ejecutadas), que el canal…

```bash
python process_mining/fm_executed_census.py
```

**Cómo da una respuesta falsa:** MEDIDO CORRIENDOLO (2026-08-26, Gold DB 28.580.216 filas). `TXSUBCLSID='Transaction Start'` NO significa "arranco una transaccion". El filtro de la linea 78 devuelve 1.235.225 filas de CINCO clases distintas: AU3 1.123.933 (arranque real) · DU9 79.110 (acceso generico a tabla: PARAM1 es un NOMBRE DE TABLA tecleado en SE16/SE11/SE16N/SQVI) · CUI 24.619 y CUJ 586 (arranque y FALLO de aplicaciones WebDynpro, PARAM1…

**No puede ver:** No puede decir CUANDO ni con que cadencia (no agrupa por SAL_DATE aunque el campo esta: sin eje temporal no separa vivo de muerto, que es justo lo que R_S4_READINESS necesita). No puede decir a que PROCESO sirvio cada ejecucion -- el propio doc de metodo avisa de que objeto<->proceso es…

**Aterriza en:** brain_v2/fm_executed_census.json -- EXISTE, esta commiteado y el script lo escribe; lo consume brain_v2/interpret_code.py, que promueve cada clave a una…

### `A46_mine_domain`

**Contesta:** Descubre, por DOMINIO, quien mueve de verdad cada objeto ejecutado y por que canal: separa el trabajo humano del que entra por satelite/RFC y del batch, con serie mensual, marca de objeto sin uso reciente y deteccion de extracciones ad-hoc por SAP Query. No dice que existe (eso ya lo dice el…

```bash
python process_mining/mine_domain.py
```

**Cómo da una respuesta falsa:** mine_domain.py — cuatro defectos MEDIDOS (2026-08-26, Gold DB p01_gold_master_data.db) que producen cifras verosimiles y falsas ya publicadas en .claude/skills/sap_process_mining/SKILL.md:129 y en brain_v2/domain_footprints/_index.json. (1) `dead` NO significa muerto, significa "no se ejecuto en el mes EN CURSO". mine_domain.py:155 fija `last_global = max(mes global)` = 202608, un mes cortado el dia 22 (SAL_DATE max…

**No puede ver:** No hace FLUJO: no hay caso, ni orden entre eventos, ni grafo de seguimiento — cuenta ejecuciones por objeto, no secuencias, asi que no puede decir que sigue a que ni donde se espera. No dice que HIZO una ejecucion: rsau registra el ARRANQUE, no los datos, ni el resultado, ni si termino bien; un…

**Aterriza en:** `brain_v2/domain_footprints/<DOMAIN>.json` + `_index.json` — el store EXISTE y se escribe (17 ficheros en el repo). Pero hacia el brain esta PENDIENTE:…

### `A47_ob09_vs_variant_check`

**Contesta:** Encuentra la cuenta que esta PERFECTAMENTE configurada para revaluacion FX y NO SE VALORA NUNCA — y no da ningun error al no hacerlo. Cruza las tres condiciones que tienen que darse a la vez y que nadie cruzaba porque una no se sabia leer: T030H/OB09 dice DONDE se postea la diferencia, la SELECCION…

```bash
python Zagentexecution/quality_checks/ob09_vs_variant_check.py
```

**Cómo da una respuesta falsa:** MODO 1 (principal, medido en vivo P01 2026-08-25). `main()` de Zagentexecution/quality_checks/ob09_vs_variant_check.py resuelve la cobertura en la linea 221 con `covered()` — la funcion LEGADO que mezcla SKONTO con AKONTO y que NO aplica la regla de solo-exclusiones — teniendo en el mismo fichero `variant_selection()`/`covered_in()`, escritas para arreglar justo eso (commit 8da7910) y usadas correctamente por el…

**No puede ver:** NO VE LA CUENTA QUE NO TIENE FILA EN T030H: entra por T030H, asi que una cuenta de banco o deposito sin OB09 y sin variante le es invisible — y esa es la PEOR de las tres situaciones (por eso existe `fx_revaluation_scope_check.py`, que entra por la naturaleza de la cuenta). No lee SKB1-XOPVW, que…

**Aterriza en:** PENDIENTE — no escribe nada. Solo stdout y exit code (0 limpio / 1 hay defecto). Los hallazgos llegaron a `brain_v2/claims/claims.json` (549, 562, 563) y a…

### `A51_skill_registry`

**Contesta:** convertir cada SKILL en un NODO con sus aristas: que tablas SAP documenta, quien lo LEE, y -- lo que no existia -- quien DEBERIA leerlo porque opera sobre sus mismas tablas y no lo nombra

```bash
python brain_v2/build_skill_registry.py
```

**Cómo da una respuesta falsa:** CRUZAR POR PALABRAS EN VEZ DE POR NOMBRES SAP. La primera version reconocia 'lo que parece una tabla' por forma -- mayusculas con digito o guion bajo -- y engancho CRITICAL, NEVER, FROM, SELECT, MARTIN, RISK. Con esa lista dijo «43 ciegos», mezclando aciertos reales (bcm-signatory-panel con sap_payment_bcm_agent por HRP1000/HRP1001/BNK_APP) con basura (brain-steward con el mismo skill por 'ABAP, FILE, NEVER'). Con…

**Aterriza en:** brain_v2/skills/skill_registry.json

### `A57_extraction_method_resolver`

**Contesta:** responder 'como leo X y como lo analizo' sin volver a descubrirlo cada sesion. NO es una lista de tablas: es un RESOLVEDOR -- por clase DD02L cubre cualquier tabla sin enumerarla, y encima lleva las restricciones que costaron dias (P01 rechaza ROWSKIPS, RSAU se trocea a <=6h o la conexion se…

```bash
python process_mining/method_registry.py
```

⚠️ **estado `WEAK`** — su salida NO se cita sin comprobarla.

**Cómo da una respuesta falsa:** CONTESTA CON APLOMO CUANDO NO SABE, Y ADEMAS LO GUARDA. (a) `resolve()` traga el fallo del lookup DD02L (`except Exception: pass`, lineas 71-72) y cae a `TYPE_RULE.get(None, ...)` = 'RFC_READ_TABLE (assumed transparent -- verify class)' (linea 73). Sin conexion P01 -- el caso NORMAL de una sesion offline -- TODA tabla vuelve como RFC_READ_TABLE, incluidas las CLUSTER que RFC_READ_TABLE no puede leer en absoluto. El…

**Aterriza en:** brain_v2/method_registry.json (method_registry.py:79 y 96)

### `A60_outbound_channel_availability`

**Contesta:** contestar la pregunta que ningun inventario nuestro contestaba: DE LOS 239 DESTINOS SALIENTES, ¿CUALES RESPONDEN AHORA MISMO? Parsea RFCOPTIONS (H host, I puerto, N path, s SSL, D usuario, Q auth), hace UNA peticion SIN CREDENCIALES por destino y clasifica la FORMA del fallo, que es el dato:…

```bash
python Zagentexecution/quality_checks/outbound_channel_availability_check.py
```

**Cómo da una respuesta falsa:** CONFUNDIR DISPONIBILIDAD CON USO, en los dos sentidos. 'Arriba' NO significa 'se usa': un destino vivo y sin trafico es indistinguible aqui de uno vivo y muy usado -- el trafico de un saliente se mide en el OTRO extremo. Y 'caido' NO significa 'incidente': muchos destinos estan configurados y nunca se usaron. Ademas: (a) un 200 en el endpoint de configuracion NO garantiza que la aplicacion funcione -- ADS puede…

**Aterriza en:** n/a - instrumento: contesta en PANTALLA (o --json), no produce artefacto persistente todavia

### `A9_business_rules_from_source`

**Contesta:** extract the DECISIONS that live in code rather than in configuration — quasi-config literals, hard constants with their reasoning, intent comments, modification blocks with the transport that made them, which standard interfaces are overridden, and debug leftovers still in production

```bash
python process_mining/extract_business_rules.py
```

**Cómo da una respuesta falsa:** IT READS TEXT. A construct it does not recognise is simply not reported, so ABSENCE IN ITS OUTPUT IS NEVER EVIDENCE — which is the single most dangerous way to misuse it, because the output looks like an inventory. Every finding carries a line number so it can be confirmed against the source, and it must be, before anyone acts. It also cannot tell a live rule from dead code: `GET_SCENARIO` returning a constant and a…

**Aterriza en:** brain_v2/business_rules.json (dataset) -> brain_v2/claims/claims.json + knowledge/domains/<domain>/*.md - the decisions that live in code rather than in config…

### `C1_component_resolution_chain`

**Contesta:** object -> TADIR (package) -> TDEVC (component id) -> DF14L (application component)

```bash
python brain_v2/system_profile/probes/extract_component_hierarchy.py
```

**Cómo da una respuesta falsa:** a name-range chunk that returns exactly the cap truncates silently

**Aterriza en:** n/a - technique: the lookup object -> TADIR -> TDEVC -> DF14L. A resolution chain, not a discovery

### `C3_static_edge_extraction`

**Contesta:** parse ABAP source for reads_tables / writes_tables / calls_fms and merge the edges into the graph

```bash
python brain_v2/parse_abap_edges.py
```

**Cómo da una respuesta falsa:** a WRONG edge is worse than a missing one — it sends someone to change the wrong thing. The parser is deliberately conservative: unambiguous SELECT/INSERT/CALL FUNCTION forms only, full-line comments stripped so a commented-out SELECT never becomes a dependency, dynamic forms skipped.

**Aterriza en:** n/a - technique: it shapes how data is read, it does not produce findings. Classified from its own `does` text, s099.

### `C5_source_identity_and_integrity`

**Contesta:** resolve a SAP object name to the file that actually holds its BODY, across every extraction root and any encoding, and flag when the canonical path holds a stub while the real source lives elsewhere. Groups candidate files by RARE name tokens only — a token shared by a dozen objects identifies none…

```bash
python brain_v2/build_code_inventory.py
```

**Cómo da una respuesta falsa:** over-grouping. Grouping on a common token (PAYMEDIUM) merged twelve distinct function modules onto one 535-line neighbour and reported ten 0-byte extractions as healthy — the tool hid the very defect it exists to find. Under-grouping is the mirror risk: a genuinely split object reads as two.

**Aterriza en:** brain_v2/code_inventory.json + DQ records for EMPTY/STUB findings

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
