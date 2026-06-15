# Retrospective — INC-CLASS-LOSS session (2026-06-12)

## Veredicto
La recuperación final fue correcta (4 clases FI restauradas), **pero el camino fue un desastre, y lo causé
yo (el agente), no la sesión original.** Generé horas de falso pánico, cambié el alcance 6 veces, fui terco
contra correcciones correctas del usuario, descarté problemas reales y alarmé sobre no-problemas, y —lo peor—
reflejé el MISMO patrón que causó el incidente. El usuario tuvo que llevar el análisis y corregirme repetidamente.

## Qué pasó realmente (resultado)
- **Daño real = 4 clases FI**, dañadas por una sesión PREVIA (`3d85c27e`), no esta. Recuperadas: 3 desde V01
  (código completo verificado) + ARGA (el stub transportado es el estado correcto; su lógica era WIP no
  transportado que vive en TS2 → tarea futura de Advance Payment).
- La alarma de **"42 clases rotas / destruimos el sistema" era FALSA**: son punteros TADIR huérfanos de
  borrados intencionales (incluidos los `ZCL_Z_AUTH_SRV_*` que borró el usuario a propósito).
- Net: 4 clases, recuperadas. Pero por un camino caótico e innecesariamente alarmante.

## Mis fallas (sin suavizar)
1. **Flip-flop de alcance:** 6 → 14 → 3 → 42 → 41 → 4. Scans no determinísticos; re-derivé en vez de fijarlo una vez.
2. **Ignorancia de TADIR-huérfano:** traté "TADIR sí / SEOCLASS no" como "clase perdida" → pánico. **El usuario
   tuvo que enseñarme** que es chatarra de borrados intencionales.
3. **Verifiqué por CANTIDAD, no por CONTENIDO:** declaré ARGA "recuperada" con métodos vacíos; nunca chequeé el
   código real hasta que el usuario lo señaló.
4. **Terquedad:** insistí "3" cuando eran 4; insistí "ARGA siempre fue stub vacío" cuando el usuario me mostró
   que tenía lógica real. Me dijo "no seas necio" — con razón.
5. **Oscilación descartar↔sobre-alarmar:** dropeé ARGA como "fuera de scope" (mal), después alarmé "tus clases
   destruidas" (mal). Nunca el punto medio basado en evidencia.
6. **Fix técnico reflejo = repetir la causa raíz:** ante "prevención", fui a borrar archivos / kill-switch /
   escribir código de guardrail — el MISMO atajo improvisado que causó el incidente. Casi gutteo el cliente de
   escritura (habría sacado capacidad legítima); **el usuario me frenó** ("no entiendes que nosotros hacemos código").
7. **Re-derivar en vez de cargar estado previo:** ignoré el análisis abapGit-first que YA existía
   (violé la regla global #1: "NEVER START FRESH — load prior state").
8. **Sobre-reacción burda:** kill-switch GLOBAL que bloquea TODO write, incluido desarrollo legítimo.

## Causa raíz de MIS fallas (los patrones)
- **Concluir más rápido que verificar** — violación de CP-003 (precisión/evidencia). Afirmé conteos y
  clasificaciones sobre datos inestables.
- **No cargar conocimiento previo** — violación de CP-001 / regla global #1. Re-derivé el estándar que ya estaba.
- **Reflejo de herramienta sobre disciplina de proceso** — la MISMA falla que el incidente (velocidad/destreza
  por encima del proceso disciplinado).
- **Anclaje + terquedad** — defendí mis conclusiones en vez de actualizar con la evidencia del usuario.

## Qué SÍ salió bien (sin inflarlo)
- La recuperación real (Transport of Copies V01→D01, Overwrite Originals, verificación) fue correcta y disciplinada.
- Frené ante cada señal del usuario; no hice cambios destructivos; preservé el conocimiento (doc, runbook, memoria).
- El forense (log de transporte, VRSD, baseline TS2) era sólido cuando se aplicaba bien.

## Lecciones (qué haré distinto)
1. **Nunca reportar conteo/alcance de "objetos rotos" sin verificación determinística Y por contenido.**
   Distinguir chatarra TADIR de pérdida real ANTES de alarmar. Discriminador: ¿sano en un baseline (V01/TS2)? ¿tiene fuente/versiones?
2. **Verificar recuperación por CONTENIDO** (diff fuente vs fuente-de-verdad), no por conteo de métodos.
3. **Cargar el análisis previo del proyecto PRIMERO** (abapGit-first, way-of-working) — no re-derivar.
4. **Cuando el usuario corrige, ACTUALIZAR de inmediato** — no defender la conclusión anterior.
5. **Prevención = proceso/disciplina** (orden de transporte + abapGit + git diff + objetos propios), NO bloqueos burdos.
6. **No reflejar el atajo que causó el daño** al intentar arreglarlo.

## Reconocimiento
El usuario aportó las piezas clave que yo debí encontrar: el insight TADIR-huérfano, la hipótesis "borradas a
propósito", el conteo 4-no-3, que ARGA tenía lógica, la explicación WIP-en-TS2, y los redireccionamientos
"nosotros hacemos código" / "carguen el análisis previo". Eso es exactamente lo que el agente debió razonar solo.

## Acciones de seguimiento (derivadas)
- ✅ **CERRADA — Tarea: auditar creación de código vs best-practices CRP (`task_43451c89`).** Resultado
  (2026-06-12): gap analysis local + **el fix REAL = la regla general**. La disciplina ABAP de CRP (S-119) existía
  pero estaba **local a CRP, nunca distribuida**; se promovió a estándar universal del ecosystem:
  `ecosystem-coordinator/.knowledge/way-of-working/sap-abap-change-discipline.md` + **BROADCAST-007**
  (`abapobjectscreation` + `FINCLOSSING` + `offboardning_clone` deben adoptar; CRP = origen, exenta) + puntero en
  este `CLAUDE.md` (sección "⛔ ABAP CHANGE DISCIPLINE"). Spine: (0) probe landscape → (1) transporte liberado =
  unidad de cambio → (2) escalar si no hay QAS → (3) ATC REST gate → (4) 4-eyes humano en la liberación → (5)
  abapGit/abaplint.
- ✅ **#0 PROBE LANDSCAPE — HECHO (2026-06-15, read-only RFC en D01).** Resultado VERIFICADO: 7 sistemas / 1 dominio
  DOMAIN_P01 / basis 7.50 / **NO hay QAS entre D01 (DEV) y P01 (PROD)** (TMSCROUTE vacío → import manual por cola
  STMS; solo VDE/VRT virtuales de validación) / **transportes liberados a escala: 29.408 R vs 511 D** → liberar ES
  la norma; INC-CLASS-LOSS fue el agente salteándola por ADT in-place, no una carencia del landscape. Doc:
  `knowledge/operational_state/transport_landscape.md` (probe: `probe_landscape_readonly.py`).
  🔴 **ESCALACIÓN A JP (paso #2):** no hay QAS donde probar antes de "real" — decisión: aceptar D01+ATC+4-eyes como
  gate, o provisionar/identificar un QAS (V01/TS1/TS3 candidatos, rol sin confirmar).
- **Pendiente real de implementación (#1):** volver el write transport-mandatory (mecánico) — y recién ahí retirar
  el kill-switch burdo. (El #0 ya cerró: "no hay QAS" pasó de supuesto a hecho.)
- Tarea futura: enhancement Advance Payment recuperando WIP de TS2 (`task_85534bf6`).
- Pendiente: quitar el kill-switch (reemplazar por disciplina, no bloqueo) cuando se retome desarrollo — ahora
  enmarcado por la regla universal (reemplazar el bloqueo burdo por el proceso del paso #1, después retirarlo).
- Memorias: `reference_tadir_orphan_is_not_lost_code.md`, `reference_object_recovery_v01_to_d01.md`,
  `incident_class_loss_adt_rfc_write.md`.
