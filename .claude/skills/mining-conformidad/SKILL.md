---
name: mining-conformidad
description: >
  Mineria de tipo CONFORMIDAD: lo REAL contra lo que DEBERIA ser: reglas normativas, desviaciones y su coste.
  Reune los 10 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore conformidad · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: CONFORMIDAD

**Qué contesta esta clase:** lo REAL contra lo que DEBERIA ser: reglas normativas, desviaciones y su coste.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 10 mineros de esta clase

### `A17_change_governance`

**Contesta:** detect three governance conditions: a CHANNEL DIFFERENCE where an object is reached by a route its other maintainers do not use, CONFIGURATION changed in production that has never travelled by transport, and a transport channel carrying DATA rather than development

```bash
python process_mining/change_governance.py
```

**Cómo da una respuesta falsa:** two, both found by running it. Listing business DOCUMENTS as 'never transported' — true and useless, since transactional data does not travel; fixed by splitting configuration from documents on volume and maintainer count. And missing the case where the generic route is the modal one, which is worse than an outlier, not better

**Aterriza en:** brain_v2/change_governance.json (dataset) -> brain_v2/claims/claims.json + brain_v2/incidents/incidents.json - a channel difference or an unconsented config…

### `A39_fx_revaluation_scope_by_nature`

**Contesta:** Descubre QUE CUENTAS DEBERIAN REVALUARSE Y NO SE REVALUAN, entrando por la NATURALEZA de la cuenta (lo que el balance que la sociedad EJECUTA presenta como banco, caja, deposito, letras del tesoro o inversion) y no por su configuracion. Es la unica puerta que ve una cuenta sin OB09 y sin variante:…

```bash
python Zagentexecution/quality_checks/fx_revaluation_scope_check.py
```

**Cómo da una respuesta falsa:** DOS MECANISMOS, LOS DOS MEDIDOS EN P01 EL 2026-08-25 CORRIENDO EL PROPIO CHECK. (1) LA ILUSION DE ALCANCE — la respuesta verosimil y falsa. Con las 5 posiciones por defecto (1.1.1.1 / 1.1.1.2 / 1.1.2.1 / 1.1.2.3 / 1.2.1.1) la corrida de hoy da exit 1 con FALTA VARIANTE=1 (0004041011 Term Deposits Principal), FALTA DETERMINACION=2 (0001101601 Tashkent, 0001194311 Harare) y FUERA DE TODO=0, sobre una poblacion de 1084…

**No puede ver:** NO decide si una cuenta DEBE revaluarse -- el alcance correcto es un juicio de negocio (Tesoreria); el check lo acorrala con datos. NO ve fuera de las posiciones que se le pasen: con el defecto, ~2% de la clase de defecto medida sobre el balance entero. NO clasifica el MODO de seleccion…

**Aterriza en:** PENDIENTE — hoy solo IMPRIME y devuelve exit 0/1. No escribe store, no publica en mining_bus, no toca claims. El conocimiento de sus corridas llego al brain A…

### `A40_config_transport_prerelease_check`

**Contesta:** Antes de liberar una orden de customizing, dice QUE VA A CAMBIAR DE VERDAD al importar: cruza las claves que la orden lleva (E071K) contra el diff de la TABLA ENTERA origen vs destino, y separa el cambio que querias del que te llevas puesto. Descubre dos cosas que ninguna revision centrada en "esta…

```bash
python Zagentexecution/quality_checks/config_transport_prerelease_check.py
```

**Cómo da una respuesta falsa:** `Zagentexecution/quality_checks/config_transport_prerelease_check.py` devuelve exit 0 con salida verosimil sobre transportes defectuosos por tres vias, dos de ellas medidas hoy contra D01/P01: (A) FALSO NEGATIVO TOTAL EN LA ORDEN QUE SE LIBERA. Las claves de customizing viven en E071K de la TAREA, no de la orden padre. Con D01K9B0FXE (TRFUNCTION=W, la orden de Egipto) el check imprime "El transporte no lleva claves…

**No puede ver:** No lee E071 (lista de objetos), solo E071K (claves): un R3TR TABU con clave generica "*" no deja filas en E071K y cae en la rama "no lleva claves" con exit 0, aunque arrastre la tabla entera. No baja de la orden padre a sus tareas hijas (E070.STRKORR). No mira nada que no sea TABU: programas, DDIC,…

**Aterriza en:** PENDIENTE — no escribe ningun store. Solo stdout + exit code (0 OK / 1 INTRUSA / 2 error o troceo roto). Sus dos hallazgos reales aterrizaron A MANO: el de…

### `A47_ob09_vs_variant_check`

**Contesta:** Encuentra la cuenta que esta PERFECTAMENTE configurada para revaluacion FX y NO SE VALORA NUNCA — y no da ningun error al no hacerlo. Cruza las tres condiciones que tienen que darse a la vez y que nadie cruzaba porque una no se sabia leer: T030H/OB09 dice DONDE se postea la diferencia, la SELECCION…

```bash
python Zagentexecution/quality_checks/ob09_vs_variant_check.py
```

**Cómo da una respuesta falsa:** MODO 1 (principal, medido en vivo P01 2026-08-25). `main()` de Zagentexecution/quality_checks/ob09_vs_variant_check.py resuelve la cobertura en la linea 221 con `covered()` — la funcion LEGADO que mezcla SKONTO con AKONTO y que NO aplica la regla de solo-exclusiones — teniendo en el mismo fichero `variant_selection()`/`covered_in()`, escritas para arreglar justo eso (commit 8da7910) y usadas correctamente por el…

**No puede ver:** NO VE LA CUENTA QUE NO TIENE FILA EN T030H: entra por T030H, asi que una cuenta de banco o deposito sin OB09 y sin variante le es invisible — y esa es la PEOR de las tres situaciones (por eso existe `fx_revaluation_scope_check.py`, que entra por la naturaleza de la cuenta). No lee SKB1-XOPVW, que…

**Aterriza en:** PENDIENTE — no escribe nada. Solo stdout y exit code (0 limpio / 1 hay defecto). Los hallazgos llegaron a `brain_v2/claims/claims.json` (549, 562, 563) y a…

### `A53_skill_binding_gate`

**Contesta:** parar cuando alguien opera sobre un tema que YA tiene skill y no lo nombra. Es el control que convierte «hay que mirar lo que hay» de promesa en comprobacion

```bash
python Zagentexecution/quality_checks/skill_binding_check.py
```

**Cómo da una respuesta falsa:** GRITAR EN FALSO. Un gate que señala 43 casos de los que la mitad son ruido deja de leerse, y entonces protege menos que no existir. Por eso exige DOS nombres SAP en comun, valida los nombres contra el brain y el Gold, y descarta con motivo escrito los que no distinguen nada: tablas que toca todo el SAP financiero (T001, BKPF), nombres de SISTEMA (P01, D01) y codigos de MODULO (FI, HCM) -- dos artefactos de FI no…

**Aterriza en:** n/a - gate: su salida es el aviso; se actua en el agente o en algorithms.json

### `A55_query_discipline_lint`

**Contesta:** comprobar lo real (nuestro codigo) contra la norma (tres reglas de consulta que eran solo prosa): subconsulta correlacionada sobre la Gold DB, lectura de E071/E071K sin filtrar transportes liberados, y recuentos de filas cableados como si fueran el tamano de una tabla. Cada hallazgo cita la regla…

```bash
python Zagentexecution/quality_checks/query_discipline_check.py
```

⚠️ **estado `WEAK`** — su salida NO se cita sin comprobarla.

**Cómo da una respuesta falsa:** GRITA POR PROSA. `RE_E071` (linea 79) es `\bE071K?\b` contra el TEXTO ENTERO del fichero, comentarios y docstrings incluidos, de modo que un fichero que solo NOMBRA E071 al explicar por que existe queda denunciado como si la leyera sin filtrar. MEDIDO por mi el 2026-08-26 corriendolo: 10 hallazgos, y VERIFIQUE tres de ellos linea a linea -- skill_binding_check.py:11, build_skill_registry.py:8 y build_toolgraph.py:19…

**Aterriza en:** n/a - analysis: solo imprime y devuelve 0 SIEMPRE (linea 163). Se declara `tier: analysis` y NO gate a proposito (36-52), porque como gate con 30% de ruido y…

### `A64_authority_vs_request_delta`

**Contesta:** SEPARAR LO QUE UN DOCUMENTO AUTORIZA DE LO QUE UN CORREO PIDE, y aplicar los cinco gates: (1) DELTA -- lo que se pide y nadie autoriza, no ejecutable; (2) OMISION -- lo autorizado que el correo no menciona, que es donde muerde; (3) SUSTITUCION -- si alguna clausula dice 'replaces all previous', el…

```bash
python process_mining/authority_delta.py
```

**Cómo da una respuesta falsa:** RESUMIR EL DOCUMENTO A PARTIR DEL CORREO. Es el fallo que este algoritmo existe para impedir y se ha medido DOS VECES: INC-000011781 (la nota decia 'add Renata', las cartas decian ADD y DELETE Martin) e INC-000016262 (el correo pedia revaluar dos cuentas, el formulario AM 3-11 firmado decia NO para una). Segundo modo: dar OK cuando el gate de completitud NO SE PUDO EVALUAR -- si nadie declaro objetos_esperados el…

**Aterriza en:** ['el veredicto va al doc del incidente y a la spec de ejecucion']

### `A65_authorised_panel_reconciliation`

**Contesta:** RECONCILIAR QUIEN PUEDE FIRMAR CONTRA QUIEN ESTA AUTORIZADO A FIRMAR, y separar las cuatro salidas que no son lo mismo: en el carton y activo (keep) · en el carton y ausente (ADD, si la carta lo pide; si no, hueco para el negocio) · la carta pide baja y sigue activo (DELIMIT) · activo y en NINGUN…

```bash
python Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py
```

**Cómo da una respuesta falsa:** LLAMAR DERIVA A UN EXTRA SIN TENER TODOS LOS CARTONES. El grupo de responsabilidad es de ENTIDAD y un carton es de UN banco: si falta el carton de algun banco de la entidad, alguien que sobra aqui puede estar perfectamente autorizado alli. Sin el gate de completitud la conclusion 'sobra' es una acusacion sin prueba. Segundo modo: concluir desde una pantalla de OOCU_RESP -- 'Other period' esconde filas activas,…

**Aterriza en:** ['knowledge/incidents/INC-*.md', 'el spec de ejecucion para DBS']

### `A66_master_data_replication_by_standard_api`

**Contesta:** MEDIR EL HUECO REAL LEYENDO LOS DOS SISTEMAS EN VIVO Y REPLICAR POR LA API DEL OBJETO, con readback campo a campo. Tres reglas que no se negocian: P01 es FUENTE y jamas destino; la API estandar y nunca un INSERT plano sobre tabla estandar -- eso salta derivacion, rangos de numeracion, validez,…

```bash
python Zagentexecution/tasks/2026_08_20_mmf_gl_sync/gl_master_sync.py
```

**Cómo da una respuesta falsa:** CREER AL CODIGO DE RETORNO. Un BAPIRET2 limpio no es evidencia de escritura: la evidencia es el readback. Segundo modo: mandar campos planos a una API que espera ESTRUCTURAS ANIDADAS -- GL_ACCT_MASTER_SAVE_RFC necesita ACCOUNT_COA con KEYY dentro y ACTION='I', y sin ACTION falla con FH502 'Import of table SKA1 not possible'. Tercero: fechar el hueco. Una cuenta ausente en V01 desde hace dos anos y otra de ayer son…

**Aterriza en:** ['el maestro de D01/V01', 'knowledge/domains/Master_Data_Governance/']

### `B4_declarative_conformance`

**Contesta:** state the normative rules, classify every case against them, quantify the deviation in money

```bash
python process_mining/p2p_conformance.py
```

**Cómo da una respuesta falsa:** applying a market normative model without checking the tenant's real shape. A standard O2C model here would report 100% non-conformance because there are ZERO deliveries — a false finding.

**Aterriza en:** Zagentexecution/sap_data_extraction/process_discovery/p2p_conformance.json (dataset) -> brain_v2/claims/claims.json + brain_v2/incidents/incidents.json when a…

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
