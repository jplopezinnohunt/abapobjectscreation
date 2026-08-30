# Sesión s111 — puertas de contabilización: del pendiente a dos skills, dos mineros y una regla

**Fecha:** 2026-08-30 · **Entrada:** el bloque PENDIENTE de s110 (YFMXCHK, los tres pasos
escritos en orden) más una corrección de JP a mitad de arranque: *«hubo un trabajo enorme que
analizó todas las validaciones y sustituciones — búscalo antes de hacer nada nuevo»*.

## Qué se pidió y qué salió

Se pidió ejecutar tres pasos sobre UNA tabla. Salieron cinco claims, dos skills unificados, dos
mineros cableados al bus, una regla nueva de comportamiento y el cierre del censo CMOD — porque
la corrección de JP era cierta y estructural: el análisis existía (autopsia + matriz + mapa vivo
GB931 de INC-000005240 + registro de filtros) pero **ningún punto de entrada lo unificaba**, y
eso es exactamente cómo una sesión fresca lo re-deriva.

## Lo que se construyó, y funciona

1. **Claims 648–652.** El multiplexor XCHECK (6 reglas en una letra; la viva es `Y`=3.003
   fondos bloqueados a ejercicios futuros, 11/2025 DBM); la ruta U913 muerta (paso GB931 002:
   `BUDAT≤2011` + check FALSE; bypass 'BC' sin titulares — YXUSER tiene UNA fila, FM/HIPER);
   la puerta fiscal YFMXCHKP apagada en toda variante con lector (las 9 filas activas son
   CHTYP='CM' que nadie lee); ZTHRFIORI_ATT_TY completa (12/12 tipos ArchiveLink); y el censo
   CMOD (21 proyectos → 27 enhancements SMOD).
2. **Dos skills-punto-de-entrada:** `sap_validation_substitution` y `sap_custom_extensions`.
   Consolidan el método y REFERENCIAN los artefactos grandes en vez de duplicarlos (lección de
   la deriva de companions). `fi_domain_agent`, `unesco_filter_registry` y el agente
   `incident-analyst` (paso CODE TRACE) apuntan a ellos.
3. **Dos mineros en el bus**, cableados solos en `opportunity_watch --correr` por importar
   `_hallazgos`: `validation_substitution_drift_check` (CONFORMIDAD — primera corrida limpia,
   que era el resultado correcto) y `custom_extension_census_check` (REALIDAD — primera corrida
   ya produjo: **209 de 234 enhancements Z*/Y* sin registrar** y **19 de 21 proyectos CMOD sin
   registrar**).
4. **Regla #262** `feedback_pair_every_documented_map_with_a_watcher`, validada explícitamente
   por JP, con su porqué de process mining: estos exits son el actor OCULTO EN MEDIO del
   proceso — el event log registra el resultado, nunca la sustitución que cambió un campo ni la
   validación que bloqueó por el camino. Sin el mapa, el minero de proceso atribuye al usuario
   lo que hizo un exit.
5. **Extracciones nuevas al Gold DB** (8 tablas): yfmxchk 3.115 · yfmxchkp 11 · yxuser 1 ·
   zthrfiori_att_ty 24 · zthrfiori_att_cf 19 · modact 50 · modsap 10.273 · modattr 22.
   Refreshers: `extract_yfmxchk_control_tables.py`, `extract_cmod_inventory.py`.

## La corrección que dirigió la sesión

**«¿Por qué no es un conocimiento y lo ibas a generar nuevamente?»** — JP, en el momento justo.
La respuesta honesta: el trabajo estaba y se REUTILIZÓ (no se re-derivó), pero el reproche
señalaba el defecto real: sin punto de entrada unificado, la PRÓXIMA sesión sí lo habría
re-derivado. La sesión entera fue arreglar eso, y la regla #262 es su generalización.

## Aprendizajes SAP (Phase 4b — lo que el próximo agente necesita saber)

- **Una tabla Z puede multiplexar N reglas de negocio en un solo campo-letra** (YFMXCHK.XCHECK:
  6 semánticas distintas, una por consumidor). Nunca asumir que una tabla de control tiene UNA
  regla: leer TODOS los consumidores antes del claim.
- **MODSAP es el catálogo SAP de definiciones SMOD (10.273), NO el inventario propio** — el
  cableado real es MODACT (50 filas). Censar sobre MODSAP infla la población (defecto clásico
  de denominador).
- **P01 rechaza ROWSKIPS en MOD\* («requires GET_SORTED»)**: para tablas pequeñas, una sola
  llamada RFC_READ_TABLE sin ROWSKIPS cortando por OFFSET/LENGTH del metadato FIELDS.
- **Config activa ≠ config que gobierna**: las únicas 9 filas ACTIVAS de YFMXCHKP son de una
  variante (CM) que ningún código del corpus lee, y con MONAT=00 no bloquearían nada ni leídas.
  La frase de la autopsia «all major institutes have 2025 active in the gate» era falsa por
  esto — corregida.
- **El bypass de las puertas FM no es YXUSER sino el objeto de autorización Y_FMUECLO/YFLAG**;
  YXUSER gobierna otras rutinas y hoy tiene un solo titular (FM/HIPER). Una fila nueva ahí es
  una concesión de bypass — el minero la vigila.
- **SAPLFMDT (FMDERIVE) es el punto de entrada del proyecto CMOD ZFMACCHK** — confirmado ahora
  también por el registro del sistema, no solo por lectura de código.

## Cierre

Cola de continuación en `PMO_BRAIN.md` (bloque S111): una tarea por sesión, primera =
YTFBE001→FEB00001 (el exit del extracto bancario sin registrar). Backup diferido toda la
sesión: `D:\claude_backups` sin montar. Push a origin hecho (hasta `b12305b` + este cierre).
