---
name: mining-realidad
description: >
  Mineria de tipo REALIDAD: que ES cada nombre antes de contarlo: si un identificador del log es un objeto real, un generado o una ruta de fichero.
  Reune los 11 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore realidad · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: REALIDAD

**Qué contesta esta clase:** que ES cada nombre antes de contarlo: si un identificador del log es un objeto real, un generado o una ruta de fichero.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 11 mineros de esta clase

### `A13_custom_field_harvest`

**Contesta:** harvest every customer-namespace field this installation added to the standard model, attribute it to its table where the code says so, record HOW it is used, and pair that with whether anything is IN it

```bash
python process_mining/harvest_custom_fields.py
```

**Cómo da una respuesta falsa:** the first version matched only TABLE-FIELD and missed every field used in a WHERE clause without a prefix. ZZFIX_RATE, which gates the entire budget-rate mechanism, was absent from the first run — that absence is now the algorithm's self-test

**Aterriza en:** brain_v2/custom_fields.json (dataset) -> brain_v2/claims/claims.json - every customer field added to the standard model is part of AS-RUN and feeds…

### `A19_log_reality_filter`

**Contesta:** classify every identifier the audit log carries into OBJECT / GENERATED INSTANCE / ACTOR, so the index eats only what is an object and the rest is RE-ROUTED to the shelf it belongs on instead of being counted or discarded

```bash
python process_mining/log_reality_filter.py
```

**Cómo da una respuesta falsa:** a generated grammar nobody taught it is classified OBJECT and silently re-inflates the corpus. That is why UNKNOWN is a first-class number and is never folded into OBJECT. Measured on its own first run: UNKNOWN held 44 names, and reading them revealed a whole grammar the author had missed (AQ<area><QUERYNAME>, named saved queries) - the remainder is the sensor

**Aterriza en:** brain_v2/log_reality.json (dataset) -> claims + capability_model U_USAGE / F_INTERFACE_FILE. Judged by the log-process-discovery agent

### `A19_wbs_model`

**Contesta:** reads every custom field of a master table on THREE axes — type-aware fill, trend by creation year, and cardinality — and emits the verdict the three produce together: EN ABANDONO, EN ADOPCION, SIN INFORMACION, EN USO, RESIDUAL or VACIO. Also establishes WHO writes the master over time, and whether…

```bash
python process_mining/wbs_model.py
```

⚠️ **estado `NEW s098`** — su salida NO se cita sin comprobarla.

**Cómo da una respuesta falsa:** reporting a verdict from one axis. The algorithm refuses to: the verdict field is only set when fill, trend and cardinality agree, and a field with no trend data is reported as SIN DATOS rather than guessed

**Aterriza en:** brain_v2/project_wbs_model.json (dataset) -> brain_v2/data_quality (via curate) + brain_v2/claims/claims.json - the verdict the three axes agree on

### `A33_variant_content_mining`

**Contesta:** leer los VALORES de las variantes para saber lo que un programa HACE de verdad, no lo que puede hacer. En los jobs es donde estan los parametros y las RUTAS DE FICHERO, o sea el mapa de integraciones por job que de otra forma no se ve; y por similitud entre variantes salen grupos de funcionalidad

```bash
python process_mining/variant_content_mining.py
```

**Cómo da una respuesta falsa:** HAY QUE SEPARAR LA VARIANTE DISENADA DE LA INSTANCIA GENERADA, igual que A19 separa el objeto del nombre generado: 29.190 pares en tbtcp y la mayoria de un solo uso -- RBDAPP01 tiene 14.585, una por ejecucion de IDoc. Las disenadas son 127 en 35 programas. | UN PATRON DE RUTA DEMASIADO ANCHO PUBLICA INTERFACES QUE NO EXISTEN: la primera version casaba con '/STANDARD', que es un nombre de LAYOUT, y publico dos. | UNA…

**Aterriza en:** brain_v2/variant_content.json

### `A34_account_behaviour_classes`

**Contesta:** decir de que TIPO es cada cuenta de mayor por TRES EJES en orden de autoridad: (1) lo que SAP DECLARA -- SKA1-XBILK patrimonio/resultado, SKA1-KTOKS grupo de cuentas, y estar en T012K.HKONT, que no es un indicio de ser cuenta de banco sino lo que la hace serlo; (2) MEDIDO, el CONCEPTO: de que nodo…

```bash
python process_mining/account_classes.py
```

**Cómo da una respuesta falsa:** UNA VERSION DE BALANCE EXISTE PARA TODAS Y SE EJECUTA PARA ALGUNAS. Barrer las 1.018 cuentas de UNES contra FS11 invento un hueco de 68 cuentas y 144 M EUR; contra FS10, que es la que UNES ejecuta de verdad, el hueco son 4 cuentas y 0,01 EUR. Quien sabe que version corre es la VARIANTE de RFBILA00 (BILAVERS + SD_BUKRS), nunca T011. | Segundo: los intervalos de FAGL_011ZC estan RELLENADOS A 10 CON CEROS, asi que…

**Aterriza en:** brain_v2/account_classes.json (cuenta -> declaracion + concepto + clase, con en_que_se_apoya) + brain_v2/fsv_versions_in_use.json (que version EJECUTA cada…

### `A3_two_axis_classification`

**Contesta:** explain every call on two independent axes — PROCESS (from the object name) and ORIGIN (from host/destination/user)

```bash
python process_mining/rfc_process_classifier.py
```

**Cómo da una respuesta falsa:** an unresolved origin collapses a fleet into one label — 174 middleware endpoints currently read as one caller

**Aterriza en:** Zagentexecution/sap_data_extraction/sqlite/job_classification.json (dataset) -> brain_v2/claims/claims.json - a call stream nobody explains is noise; the…

### `A4_ordered_classifier_ladder`

**Contesta:** ordered rule chain (package -> software component -> overlay -> name -> text -> substrate); first match wins, specificity expressed by ORDER

```bash
python process_mining/executed_objects_domain_map.py
```

**Cómo da una respuesta falsa:** ORDER-DEPENDENCE IS SILENT. A greedy early rule steals from a later one and nothing errors. Proven twice in s097: 'FTB' swallowed FTBB (bank statements) into deal management; an inline comment swallowed two dict entries and moved 70,766 executions between domains.

**Aterriza en:** Zagentexecution/sap_data_extraction/sqlite/job_classification.json (dataset) -> brain_v2/claims/claims.json + brain_v2/code_inventory.json domain links

### `A60_outbound_channel_availability`

**Contesta:** contestar la pregunta que ningun inventario nuestro contestaba: DE LOS 239 DESTINOS SALIENTES, ¿CUALES RESPONDEN AHORA MISMO? Parsea RFCOPTIONS (H host, I puerto, N path, s SSL, D usuario, Q auth), hace UNA peticion SIN CREDENCIALES por destino y clasifica la FORMA del fallo, que es el dato:…

```bash
python Zagentexecution/quality_checks/outbound_channel_availability_check.py
```

**Cómo da una respuesta falsa:** CONFUNDIR DISPONIBILIDAD CON USO, en los dos sentidos. 'Arriba' NO significa 'se usa': un destino vivo y sin trafico es indistinguible aqui de uno vivo y muy usado -- el trafico de un saliente se mide en el OTRO extremo. Y 'caido' NO significa 'incidente': muchos destinos estan configurados y nunca se usaron. Ademas: (a) un 200 en el endpoint de configuracion NO garantiza que la aplicacion funcione -- ADS puede…

**Aterriza en:** n/a - instrumento: contesta en PANTALLA (o --json), no produce artefacto persistente todavia

### `A61_capability_footprint_in_log`

**Contesta:** contestar SI UNA CAPACIDAD DEJA HUELLA ANTES DE CONCLUIR NADA DE SU SILENCIO. Se le da el conjunto de nombres por los que esa capacidad se manifestaria -- transacciones, modulos de funcion, destinos, programas -- y barre el log entero buscandolos en todas las superficies, no solo en la del nombre…

```bash
python Zagentexecution/tasks/2026_08_26_inc16471_ads_log_mining/ads_outage_window_check.py
```

**Cómo da una respuesta falsa:** LEER EL SILENCIO COMO AUSENCIA. Es el modo de fallo central y el que costo el caso ADS: cero eventos de FP_JOB_OPEN en 6,5 meses NO significa que no se renderizo ni un PDF -- significa que el render Adobe no pasa por el log de auditoria. Quien lea eso como 'no se usa' retira un canal vivo. Modos secundarios: barrer una sola superficie (el nombre puede aparecer en PARAM3 y no en SLGREPNA); tomar una ventana mas corta…

**Aterriza en:** ['brain_v2/claims/claims.json', 'brain_v2/log_reality.json', 'process_mining/mining_bus.py (publicar REALIDAD)']

### `A61_event_dating_without_a_trace`

**Contesta:** FECHAR UN EVENTO QUE EL SISTEMA NO REGISTRA. Seis pasos: (1) comprobar si el hecho deja traza -- aqui el render Adobe deja CERO eventos FP_* en 6,5 meses, asi que no es que la traza este apagada, es que el evento NO EXISTE; (2) buscar una POBLACION PROXY, tipicamente lo que una persona hace al…

```bash
python .claude/skills/sap_log_forensics/SKILL.md
```

**Cómo da una respuesta falsa:** LEER UN SILENCIO COMO SENAL SIN MEDIR LA TASA BASE DE SILENCIO. Medido y casi publicado como falso positivo: ADS_AGENT callo desde el 2026-08-21 y encajaba perfectamente con el fallo -- pero ese sensor dispara solo 88 de ~200 dias (44%) y su silencio actual de 4 dias HA SIDO IGUALADO O SUPERADO OCHO VECES con todo funcionando (tres huecos de 6 dias). Una ausencia es evidencia solo en proporcion a la densidad de la…

**Aterriza en:** knowledge/incidents/<INC>.md + claims

### `A6_frontier_with_substrate_tier`

**Contesta:** coverage % + explicit worklist, with a third tier for technical substrate (connectivity, session, monitoring): real execution, legitimately non-business

```bash
python process_mining/executed_objects_domain_map.py
```

**Cómo da una respuesta falsa:** substrate becomes a dumping ground if it is ever matched before business rules — it is matched LAST on purpose

**Aterriza en:** n/a - technique: it shapes how data is read, it does not produce findings. Classified from its own `does` text, s099.

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
