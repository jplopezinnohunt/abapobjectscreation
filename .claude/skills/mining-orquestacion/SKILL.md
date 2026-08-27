---
name: mining-orquestacion
description: >
  Mineria de tipo ORQUESTACION: que instrumento usar para una tarea, y en que orden.
  Reune los 1 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore orquestacion · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: ORQUESTACION

**Qué contesta esta clase:** que instrumento usar para una tarea, y en que orden.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 1 mineros de esta clase

### `A29_discovery_chain`

**Contesta:** correr la cadena de descubrimiento entera -- realidad, columna vertebral de casos, familia B, ciclo de vida, aprendizaje -- y terminar CRUZANDO lo hallado contra lo que el brain ya sabe. La ingesta de log queda fuera por defecto: es un grifo caro y periodico, y cruzar conocimiento no deberia pagar…

```bash
python process_mining/run_discovery_pipeline.py
```

**Cómo da una respuesta falsa:** EL ORDEN NO ES DECORATIVO Y LA FASE DE CRUCE ES CIRCULAR. A21 es la puerta de B1-B5 -- lo declara su propio lands_in -- y correr la familia B sin columna vertebral no da cero: da un mapa plausible de un proceso que no existe. | Y el cruce, tal como esta, compara contra un brain_state que YA ingirio esos mismos stores, asi que es circular y solo puede encontrar lo que el ultimo rebuild no vio: en su estrena dio 0…

**Aterriza en:** process_mining/discovery_delta.json

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
