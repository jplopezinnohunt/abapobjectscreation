# -*- coding: utf-8 -*-
"""Da de alta H144 en el PMO: la naturaleza de cuenta bancaria como tema vivo.

Se inserta al PRINCIPIO del bloque de items, no al final, porque el PMO se lee de arriba
abajo y un item nuevo enterrado en la pagina 40 no existe.
"""
import io, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

P = ".agents/intelligence/PMO_BRAIN.md"
s = io.open(P, encoding="utf-8").read()

ITEM = """
---

## H144 — Naturaleza de cuenta bancaria: declararla y derivar de ella la configuración

**Abierto:** 2026-08-28 (s108) · **Origen:** INC-000013624 · **Estado:** PROPUESTA MEDIDA, pendiente de decisión de Tesorería
**Propuesta visual:** https://claude.ai/code/artifact/35649321-2ccc-4824-a029-15b28ca33309
**Conocimiento:** `knowledge/domains/Treasury/bank_account_nature_model.md` · `bank_statement_channels_by_company.md` · `ebs_format_models.md` · `ebs_file_pipeline_and_jobs.md`

### El postulado
Una vez definido el banco, lo siguiente que hay que saber es la **naturaleza** de la cuenta. De
ella se deriva qué configuración de pago lleva, qué autorización necesita, qué extracto espera y
cómo se vigila. **Hoy ese alcance sale de casillas de un formulario Excel, no de la cuenta.**

### La evidencia (medida en P01, 2025-2026)
- **La naturaleza ya predice la configuración:** de 144 cuentas vivas de UNES, las **9 OPERATIVAS
  pagan el 100 %** y mandato / a la vista / transferencia **ninguna**. Los métodos de pago igual.
- **No está modelada en ningún sitio.** Tres candidatos medidos y los tres fallan: **YBANK**
  clasifica geografía × divisa (los mandatos PIMCO/JP Morgan/RAMP están en el mismo cajón que las
  operativas de sede); **FDLEV** reparte B0/B1 y las 8 de Northern Trust son B0; **el balance FS10**
  mete las 352 cuentas en `1.1.1.1 Cash with Banks` teniendo `1.1.2.1 Short Term Deposits` y
  `1.2.1.1 Other Investments` sin usar.
- **141 de 167 cuentas vivas sin señal de naturaleza** por texto. Pero **102 de las 119 de UNES ya
  están declaradas como terreno por su set `YBANK_..._FO_*`**: el residuo real son **14**.

### Los dos ejes de mejora, que no se suman
- **A · formatos:** 9 modelos y 259 reglas para 133 cuentas; 5 existen para UNA cuenta. Potencial
  real **18 reglas seguras** (SOG_FR/SOG_FRB difieren en una) y hasta 34 más si el algoritmo 001
  de SCB19_IQ/CIT24_GA no es necesario. `CIT04_US` (algoritmo 019 DME) y `SOG_EUR4` (reglas 201I/O
  de cliente) son legítimamente distintos: absorberlos **destruiría** automatización.
- **B · adopción:** 11 cuentas tienen modelo asignado y no lo usan; **verificado el movimiento, 6
  son reales** (`CBE01-ETB02` está durmiente y se cae). Coste en SAP **cero**.
- **Tiran en sentidos opuestos sobre los huérfanos:** consolidar uno dentro de XRT940 es bajarle el
  algoritmo de 001 a 015 — cambio de comportamiento contable, no limpieza.

### Huecos de control que salieron de paso
1. **Los 3 mandatos de Northern Trust mueven saldo y no reciben NI UN extracto** (USD05 mueve 33,4 M
   en 5 periodos). Dinero moviéndose sin corroboración bancaria.
2. **Cinco cuentas, 2.321 extractos en dos años y cero movimiento** en el mayor 10xxxxx: Pekín ×2,
   Bangkok, `UIL/DEU01-USD01`, `UBO/CIT01-BRL02`.
3. **Seis cuentas manuales que pagan** (una emitió 355 pagos) cuyas 1.712 líneas **no compensan
   solas** (reglas MXX*, algoritmo 000) y van enteras a FEBAN.
4. **Proporción por sociedad:** UNES 10 % de anomalías, **UIL 40 %, UBO 33 %**.

### Lo que hay que decidir (no lo decide el agente)
1. Declarar el vocabulario de naturalezas y **extender YBANK** con nodos de naturaleza junto a
   `_SIGHT`. ⚠️ Se transporta como `TDAT GRW_SET` = tabla completa: **alinear D01 y P01 antes**.
2. Confirmar con Tesorería las 4 de mandato: ¿por qué no llega extracto y por qué figuran como
   *Cash and Cash Equivalents*? **Las dos no pueden ser ambas «no pasa nada».**
3. Preguntar a Jartúm, La Habana, Teherán y Harare **si sus bancos emiten MT940**. Coste cero.
4. Decidir si YBANK cubre a los institutos (32 cuentas vivas fuera de todo set).

### Instrumentos (registrados en `algorithms.json` como D1–D6)
`house_bank_ebs_wiring_check.py` · `bank_statement_channel_census.py` ·
`bank_account_nature_model.py` · `bank_config_profile_by_nature.py` ·
`bank_account_behaviour_signature.py` · `ebs_format_consolidation.py`

### ⚠️ Antes de retomarlo
**Correr `python brain_v2/load_domain.py <tema>`.** En s108 no se hizo y se re-derivó el job
`FEB_FILE_HANDLING` que el explorador `A44` ya publicaba como `channel_jobs STABLE` — 13 minutos,
el bloque de tiempo más caro de la sesión. Y reconciliar con `bank_model_findings.json`: su
hallazgo `receiving_accounts` es el mismo objeto que el tipo `OPERATIVA_COBRO`.

"""

MARCA = "> ## PENDIENTE AL ABRIR"
i = s.find(MARCA)
if "H144" in s:
    print("PMO: H144 ya existe")
elif i > 0:
    # justo antes del bloque PENDIENTE AL ABRIR va el separador; se mete DESPUES de ese bloque
    fin = s.find("\n## ", i)
    if fin < 0:
        fin = i
    s = s[:fin] + "\n" + ITEM.rstrip() + "\n" + s[fin:]
    io.open(P, "w", encoding="utf-8").write(s)
    print("PMO: H144 dado de alta")
else:
    io.open(P, "a", encoding="utf-8").write(ITEM)
    print("PMO: H144 anadido al final (no se encontro el ancla)")
