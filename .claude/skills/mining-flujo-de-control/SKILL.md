---
name: mining-flujo-de-control
description: >
  Mineria de tipo FLUJO_DE_CONTROL: que sigue a que: mapa de proceso, variantes, cuellos de botella y tiempos de ciclo.
  Reune los 4 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore flujo de control · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: FLUJO_DE_CONTROL

**Qué contesta esta clase:** que sigue a que: mapa de proceso, variantes, cuellos de botella y tiempos de ciclo.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 4 mineros de esta clase

### `A68_payment_lifecycle_e2e`

**Contesta:** construir el log de eventos del ciclo de vida del PAGO -- factura contabilizada -> vencimiento -> propuesta F110 -> pago ejecutado -> lote BCM (creado/actualizado/aprobado/completado/anulado) -> proveedor compensado -- y descubrir que la compensacion de UNESCO NO es un flujo sino CUATRO: F110/BCM…

```bash
python Zagentexecution/mcp-backend-server-python/payment_process_mining.py
```

**Cómo da una respuesta falsa:** MEDIDO al correr build_event_log() en modo SOLO LECTURA el 2026-08-27 (1.975.206 eventos / 611.760 casos / 90 s). CINCO formas de dar una respuesta verosimil y falsa. (a) EL TRAMO DE PROPUESTA F110 DA CERO EN SILENCIO. El paso 3f imprime '-> 0 proposal events linked to invoices' y sigue. Es imposible por construccion: enlaza REGUH con XVORL='X' contra payment_to_invoices, que se construye desde BSAK.AUGBL, y una…

**No puede ver:** 1. EL PEDIDO: no lee ekko/ekpo/ekbe/rseg/rbkp; su primer evento es 'Invoice Posted' y el circuito del dueno empieza dos pasos antes. 2. LA APROBACION POR WORKFLOW: SWWWIHEAD/SWWLOGHIST estan declaradas rango 4 en knowledge/sap_event_sources_catalog.md:30 y NO estan en el Gold (0 de 384 tablas); su…

**Aterriza en:** PARCIAL. Escribe Zagentexecution/mcp-backend-server-python/payment_event_log.csv (211 MB en git-LFS; en el arbol local es un puntero de 134 bytes) y…

### `B1_dfg_discovery`

**Contesta:** build the process map from an event log — activities as nodes, observed transitions as edges

```bash
python Zagentexecution/sap_data_extraction/scripts/sap_process_discovery.py
```

**Cómo da una respuesta falsa:** a DFG on the wrong case notion produces a plausible map of a process that does not exist

**Aterriza en:** Gold DB process tables + Zagentexecution/sap_data_extraction/process_discovery/ (dataset) -> brain_v2/claims/claims.json - the map is the dataset; what the map…

### `B2_variant_analysis`

**Contesta:** group cases by exact path, rank by frequency and cost — the long tail is where exceptions live

```bash
python Zagentexecution/sap_data_extraction/scripts/sap_process_discovery.py
```

**Cómo da una respuesta falsa:** variants computed on a truncated log look like process simplicity

**Aterriza en:** Zagentexecution/sap_data_extraction/process_discovery/ (dataset) -> brain_v2/claims/claims.json - the long tail is where exceptions live; a costly variant…

### `B3_performance_bottleneck`

**Contesta:** cycle time per transition; waiting versus processing

```bash
python Zagentexecution/sap_data_extraction/scripts/sap_process_discovery.py
```

**Cómo da una respuesta falsa:** timestamps from different systems make a bottleneck out of a clock skew

**Aterriza en:** Zagentexecution/sap_data_extraction/process_discovery/ (dataset) -> brain_v2/claims/claims.json - a transition that waits is a claim about the process, not a…

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
