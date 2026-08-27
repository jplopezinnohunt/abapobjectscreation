---
name: mining-caso
description: >
  Mineria de tipo CASO: que documento es el CASO de un proceso, y si el identificador elegido aguanta como columna vertebral.
  Reune los 2 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore caso · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: CASO

**Qué contesta esta clase:** que documento es el CASO de un proceso, y si el identificador elegido aguanta como columna vertebral.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 2 mineros de esta clase

### `A21_case_spine`

**Contesta:** probar, clase a clase, si el identificador de caso del log de cambios (CDHDR.OBJECTCLAS + OBJECTID) ALCANZA su documento en la Gold DB. Sin ese salto hay un quien-y-cuando sin importe, sin moneda y sin dueno del dinero, que es auditoria pero no es process mining

```bash
python brain_v2/case_spine.py
```

**Cómo da una respuesta falsa:** declarar que una clase 'combina' porque el nombre de la columna encaja. Se declara por el PORCENTAJE que casa sobre claves reales. Y el corte del OBJECTID se verifica: BELEG lleva el MANDANTE incrustado (350) y un BUKRS de 3 caracteres rellenado a 4, cosa que ningun patron de nombre dice -- inferirlo devolvio None y esa es justo la regla que el proyecto ya tiene escrita sobre no deducir claves SAP del nombre

**Aterriza en:** brain_v2/case_spine.json -> insumo del constructor de event log por caso, y de B1-B5 (DFG, variantes, cuellos, conformance, OCEL) fuera de P2P

### `A68_payment_lifecycle_e2e`

**Contesta:** construir el log de eventos del ciclo de vida del PAGO -- factura contabilizada -> vencimiento -> propuesta F110 -> pago ejecutado -> lote BCM (creado/actualizado/aprobado/completado/anulado) -> proveedor compensado -- y descubrir que la compensacion de UNESCO NO es un flujo sino CUATRO: F110/BCM…

```bash
python Zagentexecution/mcp-backend-server-python/payment_process_mining.py
```

**Cómo da una respuesta falsa:** MEDIDO al correr build_event_log() en modo SOLO LECTURA el 2026-08-27 (1.975.206 eventos / 611.760 casos / 90 s). CINCO formas de dar una respuesta verosimil y falsa. (a) EL TRAMO DE PROPUESTA F110 DA CERO EN SILENCIO. El paso 3f imprime '-> 0 proposal events linked to invoices' y sigue. Es imposible por construccion: enlaza REGUH con XVORL='X' contra payment_to_invoices, que se construye desde BSAK.AUGBL, y una…

**No puede ver:** 1. EL PEDIDO: no lee ekko/ekpo/ekbe/rseg/rbkp; su primer evento es 'Invoice Posted' y el circuito del dueno empieza dos pasos antes. 2. LA APROBACION POR WORKFLOW: SWWWIHEAD/SWWLOGHIST estan declaradas rango 4 en knowledge/sap_event_sources_catalog.md:30 y NO estan en el Gold (0 de 384 tablas); su…

**Aterriza en:** PARCIAL. Escribe Zagentexecution/mcp-backend-server-python/payment_event_log.csv (211 MB en git-LFS; en el arbol local es un puntero de 134 bytes) y…

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
