---
name: mining-objeto-centrico
description: >
  Mineria de tipo OBJETO_CENTRICO: varios objetos a la vez, sin forzar una nocion unica de caso -- convergencia y divergencia.
  Reune los 3 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore objeto centrico · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: OBJETO_CENTRICO

**Qué contesta esta clase:** varios objetos a la vez, sin forzar una nocion unica de caso -- convergencia y divergencia.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 3 mineros de esta clase

### `A10_address_chain_reconstruction`

**Contesta:** reconstruct the chain from funding source to piece of work in an installation where no foreign key carries it: infer the GRAMMAR of the identifiers, walk each declared HOP, and report per hop whether it resolves, through WHICH carrier, how much finer resolution survives, and whether any instrument…

```bash
python process_mining/chain_lineage.py
```

**Cómo da una respuesta falsa:** scoring a carrier against a population it was never meant to serve, which reads as a broken chain and is a mis-stated denominator; and a discovered change-document class claiming a table on a shared prefix. Both were real defects in the first run, fixed with breakdown-by-grammar and one-to-one assignment

**Aterriza en:** brain_v2/chain_lineage.json (dataset) -> brain_v2/claims/claims.json - an inferred grammar is a claim and must carry its confidence

### `A24_document_lifecycle`

**Contesta:** seguir un documento como CASO -- cuantas veces se toca, quien, cuanto vive, si cruza el ejercicio y si su importe sube o baja -- en vez de contar ejecuciones

```bash
python process_mining/document_lifecycle.py
```

**Cómo da una respuesta falsa:** DOS, y las dos dan un resultado creible. (1) No traducir el codigo de transaccion al ACTO DE NEGOCIO: FMX2, FMW2 y FMZ6 son el mismo programa y la misma pantalla (SAPLFMFR dynpro 0511) y hacen cosas distintas -- tratarlas como una pierde el bloqueo, tratarlas como tres crea variantes falsas. (2) Mezclar tipos de valor: sin separar por WRTTP el gasto se cuenta como reserva, y eso costo TRES correcciones seguidas el…

**Aterriza en:** brain_v2/document_lifecycle.json (dataset) -> claims. Un documento con 352 modificaciones no es una estadistica: es un hallazgo con nombre

### `B5_ocel2_object_centric`

**Contesta:** one event references MULTIPLE object types, with no forced single-case notion

```bash
python Zagentexecution/sap_data_extraction/scripts/ocel_build_p2p.py
```

**Cómo da una respuesta falsa:** choosing object types badly reproduces the single-case distortion in a more expensive format

**Aterriza en:** Zagentexecution/sap_data_extraction/process_discovery/p2p_ocel2_summary.json (dataset) -> brain_v2/claims/claims.json - multi-object behaviour a single-case…

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
