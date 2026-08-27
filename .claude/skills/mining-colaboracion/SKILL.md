---
name: mining-colaboracion
description: >
  Mineria de tipo COLABORACION: quien sabe que, quien deberia preguntarle a quien, y donde se pierde el trabajo entre instrumentos.
  Reune los 12 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore colaboracion · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: COLABORACION

**Qué contesta esta clase:** quien sabe que, quien deberia preguntarle a quien, y donde se pierde el trabajo entre instrumentos.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 12 mineros de esta clase

### `A30_mining_bus`

**Contesta:** dar a los mineros un sitio comun donde publicar lo que concluyen y consultar lo que concluyeron los demas, con jerarquia de EVIDENCIA -- un campo que SAP declara vence a una heuristica sobre comportamiento -- y sacar a la luz los CHOQUES

```bash
python process_mining/mining_bus.py
```

**Cómo da una respuesta falsa:** UN BUS ACELERA LA PROPAGACION EN LOS DOS SENTIDOS. La heuristica falsa de A23 -- 'los logons RFC dominan, luego no es una persona' -- se colo en la documentacion del agente de batch input y vivio ahi un dia. Con un bus habria llegado antes a mas sitios. Por eso lleva jerarquia de autoridad y sustitucion por aspecto, no acumulacion simple. | Y el primer defecto real: sustituia por (minero, sujeto), asi que cuando A27…

**Aterriza en:** process_mining/mining_findings.json

### `A32_mining_capability_census`

**Contesta:** encontrar scripts que leen datos de EVENTO y sacan patrones de ellos sin estar registrados como algoritmo, y emitir el borrador de alta para que pasen al grupo de mineria y los pueda usar todo el mundo (--proponer)

```bash
python Zagentexecution/quality_checks/mining_capability_census.py
```

**Cómo da una respuesta falsa:** UN CENSO CON LA VENTANA MAL PUESTA MIENTE EN LOS DOS SENTIDOS. Con la ventana estrecha -- solo process_mining/ -- no veia a la mayoria de los mineros, que viven repartidos. Con la ventana ancha y sin filtro dio 55 candidatos e incluia un lexer de pygments dentro de un venv, carpetas archivadas, scripts de incidencia de un solo uso y SU PROPIO CODIGO detectandose. Un gate que grita en falso deja de leerse y con el se…

**Aterriza en:** brain_v2/methods/mining_candidates.json

### `A35_mining_artifact_detector`

**Contesta:** avisar EN EL MOMENTO de que acabas de construir un artefacto que mina y no lo has registrado: un script que lee eventos y saca patrones, un store que asigna cosas a grupos, o un agente cuyo metodo solo vive en su prompt

```bash
python Zagentexecution/quality_checks/mining_artifact_detector.py
```

**Cómo da una respuesta falsa:** EN SU PRIMERA CORRIDA COMETIO EL DEFECTO QUE EXISTE PARA CAZAR: medir la forma en vez del efecto. Buscaba 'vari' como SUBCADENA y casaba con 'varias', 'variable' y 'varios' en castellano, asi que marco de minero a tres generadores que no leen una sola tabla de evento. Con frontera de palabra: de 5 hallazgos a 2, y los 2 correctos -- uno de ellos el propio detector, que efectivamente no estaba registrado. | Riesgo…

**Aterriza en:** n/a - gate: su salida es el aviso, y el sitio donde se actua es algorithms.json

### `A36_mining_capability_router`

**Contesta:** convertir cada minero en una CAPACIDAD INVOCABLE: se pregunta por tema, en el idioma de quien lo necesita, y contesta que minero sabe, con la llamada exacta, como importarlo desde otro script, lo que NO puede y su trampa

```bash
python process_mining/ask.py
```

**Cómo da una respuesta falsa:** EL CATALOGO ES A MANO, ASI QUE ENVEJECE EN SILENCIO. Las capacidades estan escritas en una lista dentro del script y no se derivan del registro de algoritmos: un minero nuevo no aparece aqui hasta que alguien lo anade, y uno que cambia de comportamiento sigue prometiendo lo de antes. Es el mismo modo de fallo que tiene cualquier documentacion escrita al lado del codigo. | Segundo: contesta por coincidencia de…

**Aterriza en:** n/a - servicio de enrutado; su salida es la llamada al minero que sabe

### `A37_method_memory_applied`

**Contesta:** dar a cualquier minero, ANTES de correr, lo que este proyecto ya aprendio de su instrumento -- ordenado por peso, con las TRAMPAS primero -- y dejarle preguntar si una memoria desaconseja lo que iba a hacer (`prohibe`). Y devolver al store lo aprendido, con su implicacion obligatoria

```bash
python process_mining/metodo.py
```

**Cómo da una respuesta falsa:** LEER NO ES OBEDECER, Y LA PUERTA SOLO MIDE LO PRIMERO. Que un minero importe `metodo` y imprima las memorias que le aplican NO cambia lo que hace: hoy solo A31 condiciona su comportamiento con `prohibe()`. Los otros 31 la leen y la muestran, y el gate los da por buenos. Es una medida de FORMA disfrazada de medida de efecto -- exactamente el defecto que esta sesion cazo cuatro veces. | Segundo: `prohibe()` empareja…

**Aterriza en:** brain_v2/methods/algorithm_memory.json (escribe) - y su lectura no aterriza

### `A38_claim_resolution`

**Contesta:** cerrar el circulo de vuelta: encontrar los claims abiertos para los que un minero YA produjo la evidencia que esperaban, y separar si la RESUELVEN, la REFUERZAN o la CONTRADICEN

```bash
python process_mining/claim_resolution.py
```

**Cómo da una respuesta falsa:** PROPONE POR COINCIDENCIA DE TERMINOS, Y ESO NO ES UNA RESPUESTA. Un hallazgo puede compartir cinco palabras con un claim y no contestar su pregunta. Por eso NO CIERRA nada: un cierre automatico daria por sabido lo que no lo esta, y un claim cerrado en falso no se vuelve a mirar NUNCA -- mientras que uno abierto se mira. | Y el falso positivo ya medido en su estrena: la deteccion de CONTRADICE busca palabras de…

**Aterriza en:** brain_v2/claim_resolution_proposals.json

### `A51_skill_registry`

**Contesta:** convertir cada SKILL en un NODO con sus aristas: que tablas SAP documenta, quien lo LEE, y -- lo que no existia -- quien DEBERIA leerlo porque opera sobre sus mismas tablas y no lo nombra

```bash
python brain_v2/build_skill_registry.py
```

**Cómo da una respuesta falsa:** CRUZAR POR PALABRAS EN VEZ DE POR NOMBRES SAP. La primera version reconocia 'lo que parece una tabla' por forma -- mayusculas con digito o guion bajo -- y engancho CRITICAL, NEVER, FROM, SELECT, MARTIN, RISK. Con esa lista dijo «43 ciegos», mezclando aciertos reales (bcm-signatory-panel con sap_payment_bcm_agent por HRP1000/HRP1001/BNK_APP) con basura (brain-steward con el mismo skill por 'ABAP, FILE, NEVER'). Con…

**Aterriza en:** brain_v2/skills/skill_registry.json

### `A52_toolgraph`

**Contesta:** EL BRAIN DEL BRAIN: un grafo de mis PROPIOS instrumentos con quien usa a quien (LEE, DEBERIA_LEER, ATERRIZA_EN, VIGILA, INVOCA, RECUERDA), y un COORDINADOR: ante una tarea, `graph_queries.py tool para <tarea>` contesta que SKILL leer primero, que ALGORITMO ya existe, que AGENTE la hace y que PUERTA…

```bash
python brain_v2/build_toolgraph.py
```

**Cómo da una respuesta falsa:** SER UNA SEPTIMA LISTA. El riesgo de un grafo de herramientas es duplicar los stores que ya existen y quedarse viejo aparte; por eso NO copia contenido -- cada store sigue siendo la fuente de su tipo de nodo -- y solo construye y mide las ARISTAS, que es lo que no existia en ningun sitio. | SEGUNDO: el modo coordinador cruza por PALABRAS de la tarea, asi que una tarea descrita con otro vocabulario no encuentra a…

**Aterriza en:** brain_v2/toolgraph.json

### `A54_collaboration_mechanism`

**Contesta:** hacer que los mineros COLABOREN, no que se mida si colaboran. Tres piezas: REPARTIR -- una pregunta dirigida a CUALQUIERA se asigna al minero que DECLARA esa capacidad, porque una pregunta a cualquiera es una pregunta a nadie; PONERLA DELANTE -- las preguntas abiertas que un minero puede contestar…

```bash
python process_mining/colaborar.py
```

**Cómo da una respuesta falsa:** SER OPCIONAL. `pendientes()` existia desde el primer dia y ningun minero la llamaba: 307 hallazgos publicados y UNA pregunta contestada de catorce. Un mecanismo que depende de que alguien se acuerde es una costumbre, y las costumbres se pierden entre sesiones. Por eso va dentro de una llamada que ya se hacia, y por eso hay una puerta que falla si no se hizo. | SEGUNDO, medido al engancharlo: el reparto cruza por…

**Aterriza en:** process_mining/mining_findings.json (las respuestas) + process_mining/colaboracion_state.json (quien paso por el foro)

### `A58_companion_knowledge_graph`

**Contesta:** convertir el catalogo PLANO de companions en un GRAFO: dos companions que comparten dominio, incidente o vocabulario SAP estan relacionados, y esa arista no existia en ningun sitio, asi que los companions no eran usables COMO conocimiento. Cada arista guarda QUE tokens comparte, o sea es explicable…

```bash
python scripts/build_companion_graph.py
```

**Cómo da una respuesta falsa:** EL VOCABULARIO ES CERRADO Y SE PRESENTA COMO SIMILITUD. `VOCAB` (lineas 37-49) es una lista curada a mano de ~60 tokens: un companion cuyo dominio no esta en la lista no recibe senal de vocabulario y se hunde por debajo del umbral. No es teorico -- MEDIDO por mi el 2026-08-26 leyendo companions/companion_graph.json: 48 nodos, 153 aristas, umbral 0.18, y CUATRO companions con CERO aristas --…

**Aterriza en:** companions/companion_graph.json (+ el campo `related` inyectado en companions.json con --write-related). Wired: brain_v2/rebuild_all.py:394 (Step 7a/7) lo…

### `A63_discovery_raises_questions`

**Contesta:** CONVERTIR UN HALLAZGO EN PREGUNTAS PARA QUIEN NO SABIA QUE LE AFECTABA. Un descubrimiento no crece el grafo por el nodo: crece por las ARISTAS, y cada arista nueva puede invalidar o poner en duda lo que otro instrumento daba por sabido. Ese segundo efecto se perdia entero. Extrae los SUJETOS del…

```bash
python process_mining/knowledge_propagation.py
```

**Cómo da una respuesta falsa:** TOMAR ENFASIS POR SUJETO. Los claims escriben EN MAYUSCULAS para enfatizar, asi que 'toda palabra en mayuscula es un objeto SAP' da CERO, SOLO, DATOS y PARA como si fueran tablas: la primera version publicaba 47 afectados casi todos por ruido, y un propagador ruidoso es peor que ninguno porque entrena a ignorar sus preguntas. Un sujeto tiene FORMA -- digito, guion bajo, barra o punto. Segundo modo: inventar…

**Aterriza en:** ['process_mining/mining_findings.json (via mining_bus.preguntar)']

### `A69_agent_roster_enumeration`

**Contesta:** enumerar que agentes existen y cuales se OFRECIERON esta sesion, separandolos por PROCEDENCIA (propio / del harness / propio-no-ofrecido), y diffear cada declaracion contra la anterior. El hallazgo NO es la lista: es el CAMBIO. Un agente que aparece o desaparece del harness es un cambio de…

```bash
python brain_v2/record_agent_roster.py
```

**Cómo da una respuesta falsa:** REPORTAR UN NUMERO COMPLETO SOBRE UNA POBLACION QUE NO PUEDE VER. Es el DENOMINADOR INCOMPLETO de braintoolbox aplicado a nosotros mismos, y ya se cometio: un enumerador de `.claude/agents/*.md` encuentra los PROPIOS y es ESTRUCTURALMENTE ciego al resto. Medido s106: SEIS invisibles -- Explore, Plan, general-purpose, claude, claude-code-guide, statusline-setup -- y `Explore` fue, por consumo, el agente que MAS…

**No puede ver:** ENUMERAR SOLO. La mitad del harness es UNOBSERVABLE desde disco por construccion, no por falta de esfuerzo: el harness entrega esa lista al contexto del modelo. El unico observador posible es LA SESION, y por eso esto se INVOCA desde la sesion en vez de correr solo -- mismo patron que el gate del…

**Aterriza en:** brain_v2/agent_roster.jsonl (append-only, una linea por declaracion, con nuevos_vs_anterior y desaparecidos_vs_anterior ya calculados)

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
