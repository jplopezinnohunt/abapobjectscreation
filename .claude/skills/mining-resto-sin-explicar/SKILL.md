---
name: mining-resto-sin-explicar
description: >
  Mineria de tipo RESTO_SIN_EXPLICAR: lo que NO sabemos nombrar todavia: el sensor de lo no clasificado.
  Reune los 4 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore resto sin explicar · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: RESTO_SIN_EXPLICAR

**Qué contesta esta clase:** lo que NO sabemos nombrar todavia: el sensor de lo no clasificado.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 4 mineros de esta clase

### `A20_comprehension_index`

**Contesta:** measure whether the EXECUTION SURFACE is closed, across the FOUR surfaces that compose it: what ran (RSAU program names), what was changed (CDHDR tcode), what runs unattended (TBTCO x TBTCP) and what ENTERS by RFC (RSAU.PARAM3 function module). Splits TECHNICAL / CROSS_CUTTING / STRANDED /…

```bash
python brain_v2/comprehension_index.py
```

**Cómo da una respuesta falsa:** a broken join produces a believable number. It happened THREE times while building this: reading A4's top-objects SUMMARY instead of running its classifier (100% ungraded); looking up a domain_axes.process field that does not exist (empty map, every object silently degraded); and feeding raw TCODEs to a PROGRAM classifier, which left XK01/SU01/PFCG Uncatalogued and invented a 35% gap in the change surface. Each…

**Aterriza en:** brain_v2/comprehension_index.json + comprehension_history.jsonl (derivada) -> brain index + docs de dominio; keep_exploring ES la lista de trabajo del agente…

### `A5_adaptive_learning_loop`

**Contesta:** auto-resolve unknown calls by function group / naming / app domain, LEARN the resolution, re-classify until convergence, expose the remainder as an explicit frontier

```bash
python process_mining/adaptive_discovery.py
```

**Cómo da una respuesta falsa:** a rule learned WRONG persists forever and invisibly — DEMONSTRATED on its first run with the new signal: mapping the broad technical bucket Basis_Security to one business process taught it that IDOCS_OUTPUT_TO_R3, IDOC_INBOUND_ASYNCHRONOUS and BAPI_EXCHANGERATE_GETDETAIL are identity management. 7 rules purged; the mapping removed so it cannot be relearned. Returning NOTHING is correct for a technical call: it goes…

**Aterriza en:** process_mining/learned_rules.json (dataset) -> brain_v2/methods/unlanded_discoveries.py - the UNRESOLVED remainder is the point. Convergence hides what it…

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
