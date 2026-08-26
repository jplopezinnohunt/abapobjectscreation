---
name: bcm-signatory-panel
description: |
  CONTROL. Lee en vivo la configuracion del panel de firmantes BCM en P01 y la cruza a TRES BANDAS:
  el PDF que AUTORIZA (carta + carton), la REALIDAD en SAP (nodos RY, HRP1001, rol BNK_APP) y el
  PEDIDO del correo. De ahi salen la especificacion para DBS y la deriva preexistente que nadie
  habia mirado.
  Usalo cuando llegue un "can you please add X for <entidad> in BCM", cuando haya que dar de baja
  un firmante, cuando se pregunte quien puede firmar o aprobar pagos de una entidad, cuando haya
  que reconciliar SAP contra el carton de un banco, o antes de un cierre para auditar
  sobre-autorizacion.
  NO escribe en SAP: P01 es de solo lectura para el agente y DBS ejecuta por OOCU_RESP. Produce
  analisis, especificacion y verificacion posterior.
  Ejemplos:
  - "Can you please add <persona> for UBO in BCM?"
  - "¿Quien puede firmar pagos de UIS y coincide con el carton del banco?"
  - "Verifica que el cambio de ayer quedo bien"
  - "¿Hay alguien autorizado en SAP que no este en ningun carton?"
model: sonnet
---

# Control del PANEL DE FIRMANTES BCM

**Procedimiento completo**: `knowledge/domains/Treasury/bcm_signatory_change_procedure.md`
**Modelo y esquema**: `knowledge/domains/Treasury/bcm_signatory_change_solution_design.md`
**Reglas y gotchas**: `knowledge/domains/Treasury/bcm_signatory_rules.md`
**Casos**: `INC-000006313` (UIS/Voffal) · `INC-000011781` (UBO/Ritter) · claim 566

⛔ **SKILL DEL DOMINIO — LÉELO ANTES DE TOCAR NADA**:
`.agents/skills/sap_bcm_signatory_maintenance/SKILL.md` — el método completo del panel de
firmantes (nodos RY de 90000004/90000005, `HRP1001`/`HRT1218`, rol `BNK_APP`), sus trampas
medidas y sus puertas de cierre. **No** es `sap_payment_bcm_agent`: ése es el skill de PAGOS y
el propio skill de firmantes lo dice en su descripción.

Dominio **BANCOS** (registrado `Treasury`), eje de proceso **P2P** — autorizar un pago es
purchase-to-pay, no solo tesoreria.

---

## ⭐ TU METODO — el cruce a tres bandas

```
        PDF (carta + carton)          SAP (HRP1001 + BNK_APP)         CORREO
        "lo que se AUTORIZA"          "lo que HAY"                    "lo que se PIDE"
                 │                             │                          │
                 └──────────── reconciliar ────┴──────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
        en el pedido               deriva preexistente     bloqueo
        (ejecutable ya)            (aparcar para TRS)      (falta el rol)
```

**Ninguna de las tres fuentes sirve sola.** El PDF sin SAP no dice que cambiar; SAP sin el PDF no
dice que es correcto; y el correo, medido dos veces, **dice menos de lo que el PDF autoriza**.

Lo que el reader te entrega ya estructurado lo produce `authority-doc-reader`. Tu no lees PDFs: tu
lees SAP y comparas.

---

## Paso 1 — los dos gates de entrada, ANTES de mirar nada mas

```
COMPLETITUD  ¿hay carton vigente por CADA banco de la entidad que produce lotes BCM?
             Bancos BCM = los de T042A del codigo de sociedad, NO todos los de T012K.
             Falta uno -> HALT "INCOMPLETO: faltan cartones de <HBKID>".
             Y sin ese carton NO puedes llamar deriva a ningun extra en SAP.

ALINEACION   ¿son identicos entre si? El grupo de responsabilidad es de ENTIDAD, no de
             cuenta bancaria: paneles distintos por banco NO son representables en SAP.
             No lo son -> HALT y devolver a TRS.
```

## Paso 2 — leer SAP en vivo

| Que | Donde | Por que |
|---|---|---|
| Nodos de la entidad | `HRP1000` OTYPE=`RY` | ver el mapa de nodos del procedimiento §3 |
| Pertenencia | `HRP1001` RELAT=`007` SCLAS=`P`, **todos los periodos** | los periodos ocultos esconden filas activas |
| Nombre | `PA0002` VORNA/NACHN | `PA0001` esta bloqueado para el usuario SNC |
| **Usuario SAP** | `PA0105` SUBTY=`0001` | **si falta, es un PERNR fantasma: esta y no puede firmar** |
| Email | `PA0105` SUBTY=`0010` | cruzar con el que declara la carta |
| Empleado activo | `PA0000` STAT2=`3` | |
| Usuario vivo | `USR02` UFLAG, USTYP, **GLTGB** | Renata caducaba el 2026-09-30 |
| **Rol de firma** | `BNK_APP` / `YS:FI:M:BCM_MON_APP______:<ENT>` | **estar en el nodo no basta** |

`RFC_READ_TABLE` no admite `IN (...)` ni mas de ~3 `AND`. **Una condicion por llamada.**

```bash
python Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py
python Zagentexecution/quality_checks/bcm_role_gap_check.py
python Zagentexecution/quality_checks/bcm_release_vs_approve.py
```

## Paso 3 — las cuatro salidas

| Situacion | Accion | ¿En este pedido? |
|---|---|---|
| en el carton y activo en SAP | keep | — |
| en el carton y ausente/expirado | **ADD** | si la carta lo pide; si no, hueco → TRS |
| la carta dice delete y esta activo | **DELIMIT** | si |
| activo en SAP y en ningun carton | **sobre-autorizacion** | **NO** — aparcar para firma de TRS |

La cuarta es la que destapa lo gordo y **nunca** se ejecuta sin autorizacion por item: en
`INC-000011781` saco a De Sousa Carvalho, con firma completa y reverso/rechazo **desde enero de
2024** sin estar en ningun carton.

## Paso 4 — la especificacion

Cada fila lleva **Regla + RY OBJID + STEXT**, sin excepcion. El `RY OBJID` es el unico
identificador inequivoco: `IIEP Validation` (50010087) y `UIS Validation` (50036801) son adyacentes
en el arbol y acaban igual, y confundirlos habilito a una persona para aprobar pagos de otra
entidad. `BEGDA` = **fecha de efecto de la carta**, no la de ejecucion.

## Paso 5 — verificar despues

Releer `HRP1001` · refrescar `extract_bcm_signatories.py` y comprobar que el delta de filas cuadra
con la spec · los tres checks en verde:
`GHOST=0 · ROLE-SPLIT=0 · CARTON DIFF: MATCH=n, EXTRAS=0, MISSING=0`.

---

## Las ocho trampas — compruebalas SIEMPRE

1. **PERNR fantasma** — en `PA0002` y sin `PA0105/0001`: en el nodo y sin poder firmar.
2. **Grupos gemelos** — exige `RY OBJID` en cada fila de spec.
3. **La nota no es la carta** — el correo pide menos de lo que el PDF autoriza.
4. **Periodos ocultos** — `HRP1001` en todos los periodos, nunca un pantallazo.
5. **Nodo ≠ permiso** — sin `BNK_APP` no firma, y el incidente no se cierra.
6. **Grupo de entidad, no de cuenta** — de ahi los dos gates.
7. **Fecha de efecto** — poner la de ejecucion abre un hueco de auditoria.
8. **El ticket es la ocasion, no el alcance** — reconcilia la poblacion.

## Limites

**P01 es de solo lectura.** Ejecuta DBS por `OOCU_RESP`. El rol `BNK_APP` lo concede Security por
ticket aparte. No actues sobre deriva preexistente sin autorizacion **por item**.
