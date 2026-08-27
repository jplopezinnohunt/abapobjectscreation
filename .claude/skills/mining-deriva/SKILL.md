---
name: mining-deriva
description: >
  Mineria de tipo DERIVA: como cambia algo EN EL TIEMPO: perfiles mensuales, tasas por dia, señales de deriva.
  Reune los 2 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore deriva · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: DERIVA

**Qué contesta esta clase:** como cambia algo EN EL TIEMPO: perfiles mensuales, tasas por dia, señales de deriva.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 2 mineros de esta clase

### `A43_fsv_alignment_check`

**Contesta:** Mide, clave a clave, cuanto se ha ido la VERSION DE BALANCE (FSV) de produccion respecto de D01/V01, y emite la especificacion de cambio OB58 fila a fila. Descubre lo que el sync de master data NO lleva — el customizing — que es invisible mirando la cuenta.

```bash
python Zagentexecution/quality_checks/fsv_alignment_check.py
```

**Cómo da una respuesta falsa:** MEDIDO HOY (2026-08-25) en Zagentexecution/quality_checks/fsv_alignment_check.py — tres modos; el (1) reproducido extremo a extremo, el (2) y el (3) ciertos por codigo y corroborados por .claude/skills/sap_master_data_sync/SKILL.md:127,153,155-158. (1) UN SISTEMA QUE NADIE LEYO SE CERTIFICA ALINEADO. `main()` (lineas 120,130-133) acepta `--systems` sin validarlo y rotula la salida con la cadena del usuario.…

**No puede ver:** NO escribe, y es deliberado: se pregunto a TFDIR WHERE FMODE='R' por FSV/BILANZ/ERGSL/FIN_STATEMENT y no existe NINGUN FM remote-enabled; FAGL_011* son tablas ESTANDAR, asi que el INSERT plano esta prohibido — el canal es OB58 en el destino o una orden de customizing, y lo que produce es la…

**Aterriza en:** PENDIENTE. Hoy solo stdout + exit code, y con `--spec` un fichero Zagentexecution/quality_checks/fsv_change_spec_<SYS>.md (D01 134 KB, V01 110 KB, ambos del…

### `A7_concept_drift`

**Contesta:** monthly activity profile per domain as RATES PER DAY (executions, distinct objects, distinct users); a month is flagged when at least TWO signals depart from the trailing baseline by more than 50%. One signal moving is noise; two is a change of shape.

```bash
python process_mining/detect_drift.py
```

**Cómo da una respuesta falsa:** TWO defects found on its own first runs, both worth recording because both produce confident nonsense: (1) comparing monthly VOLUMES across unequal months produced 11 signals, almost all in the first FULL month — the window is 2026-02-21..2026-06-21, so February has 3 days and April 30. Fixed by normalising per day. (2) z-scores over a two-month baseline exploded to z=1016 because the standard deviation collapses.…

**Aterriza en:** brain_v2/drift_signals.json + brain_v2/drift_profile.json (dataset) -> brain_v2/claims/claims.json - a flagged month is not knowledge until it carries its…

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
