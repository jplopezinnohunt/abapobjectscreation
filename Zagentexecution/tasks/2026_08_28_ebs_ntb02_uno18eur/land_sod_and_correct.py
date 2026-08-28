# -*- coding: utf-8 -*-
"""Aterriza el hallazgo de segregacion de funciones y CORRIGE las cifras que publique mal.

El agente cruzo los mineros y encontro dos cosas: un riesgo de SoD dimensionado, y que mi
censo publicado subestimaba la poblacion manual entre 5 y 10 veces. Lo segundo hay que
corregirlo donde se publico, no solo reconocerlo.
"""
import json, io, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- 1. CLAIMS ---------------------------------------------------------
P = "brain_v2/claims/claims.json"
cl = json.load(io.open(P, encoding="utf-8"))
mx = max(c.get("id", 0) for c in cl)
BASE = dict(claim_type="SYSTEM_FACT", confidence="TIER_1", status="VERIFIED",
            domain="Treasury_EBS", created_session=108,
            domain_axes=dict(functional=["Treasury"], module=["FI"], process=["T2R"]))

NUEVOS = [
    dict(BASE, claim=(
        "SEGREGACION DE FUNCIONES EN EL EXTRACTO BANCARIO: 420 PAGOS Y 2.401.283 USD LOS EMITE "
        "QUIEN ADEMAS TECLEA Y CONTABILIZA EL EXTRACTO DE ESA MISMA CUENTA. Medido en P01, UNES, "
        "2025-2026. La cadena tiene cuatro eslabones y hay que separarlos porque solo uno es "
        "remediable. (1->2) De 802 extractos tecleados a mano salen 13.942 lineas FEBEP, 10.285 "
        "con documento FI, y 10.217 (99,3%) las contabiliza EXACTAMENTE la misma persona que las "
        "teclea: eso es MECANICO, no un fallo de asignacion -- FF67 contabiliza bajo el usuario "
        "que entra, y no se arregla repartiendo usuarios. Control: 5 cuentas electronicas suman "
        "23.082 lineas con 2 casos de humano en los dos extremos (0,009%), porque ahi el eslabon "
        "de entrada es JOBBATCH. (3) EL ESLABON REMEDIABLE: de 1.249 pagos, 420 (34%) y 2.401.283 "
        "USD (57%) los emite alguien que tambien teclea y contabiliza esa cuenta -- 16 personas, "
        "14 cuentas. La mayor es AIB01-USD01 (Kabul) con 262 pagos y 2.118.599 USD, seguida de "
        "BTE01-IRR02 (Teheran, 355 pagos) y BMN01-USD01 (La Habana, 73). (4) CICLO COMPLETO: 60 "
        "pagos y 65.409 USD donde la misma persona crea la factura, emite el pago y teclea el "
        "extracto que lo confirma -- pequeno en dinero, y se dice aunque quite el titular. "
        "POR QUE NINGUN CONTROL AUTOMATICO LO VE: los 1.253 pagos son 100% metodo '3', cheque "
        "prenumerado (T042Z-XSCHK), y hay CERO filas en BNK_BATCH_ITEM para los 39 bancos casa "
        "frente a 82.678 de SOG01 y 12.827 de CIT04 en la misma ventana. NO es un defecto de "
        "configuracion: BCM libera FICHEROS y un cheque no tiene fichero."),
        status="OPEN_QUESTION",
        evidence_for=["Zagentexecution/quality_checks/bank_statement_sod_check.py",
                      "Zagentexecution/tasks/2026_08_28_ebs_ntb02_uno18eur/sod_bank_statement.json"],
        evidence_against=[],
        related_objects=["FEBKO", "FEBEP", "BKPF", "REGUH", "T042Z", "BNK_BATCH_ITEM",
                         "AIB01", "BTE01", "BMN01", "FF67"],
        resolution_notes=(
            "LIMITE DECLARADO, y es lo que convierte esto en accionable en vez de en una "
            "acusacion: el control compensatorio son DOS FIRMAS FISICAS del cheque, que estan "
            "FUERA de SAP. Este instrumento no puede confirmarlo ni negarlo. Tampoco ve el "
            "portal del banco local, ni si la factura tuvo aprobacion fuera de FI, ni QUIEN "
            "DEBIA teclear -- el log dice quien lo hizo. Es SoD CONDUCTUAL, no de roles: no se "
            "leyeron AGR_*.")),

    dict(BASE, claim=(
        "LA POBLACION DE EXTRACTO TECLEADO A MANO ES 5-10 VECES MAYOR DE LO QUE PUBLIQUE: NO SON "
        "8 CUENTAS Y 4 PERSONAS, SON 34 CUENTAS VIVAS Y 40 USUARIOS. Medido en P01, UNES, "
        "2025-2026: 39 cuentas tienen al menos un extracto con FEBKO.EFART='M' (34 vivas, 5 "
        "cerradas por texto), 41 usuarios distintos los han tecleado, y suman 802 extractos y "
        "13.942 lineas FEBEP. CAUSA DEL ERROR: la etiqueta `canal` se deriva de que EXISTAN "
        "extractos E y M, asi que una cuenta 97% tecleada a mano sale MIXTO y desaparece del "
        "relato. Caso puro: SOG06 (Haiti) tiene 55 extractos tecleados con 9.623 lineas -- el "
        "69% de todo lo tecleado a mano en UNESCO -- frente a 5 electronicos con CERO lineas en "
        "FEBEP; es 100% manual de hecho y estaba etiquetada MIXTO. Segundo defecto del mismo "
        "instrumento: filtraba por un porcentaje REDONDEADO, asi que una cuenta con 1 extracto "
        "tecleado entre 500 daba 0 y salia de la poblacion. CONSECUENCIA: el argumento publicado "
        "de que '1.712 lineas frente a 11.669 de una sola cuenta electronica desmonta la "
        "oportunidad' SE CAE en su propio denominador -- son 13.942 frente a 11.669, comparables. "
        "El tamano ya no la desmonta; tampoco la confirma, porque la restriccion sigue aguas "
        "arriba: que el banco emita MT940."),
        evidence_for=["Zagentexecution/quality_checks/bank_statement_channel_census.py",
                      "knowledge/domains/Treasury/bank_statement_channels_by_company.md"],
        evidence_against=[],
        related_objects=["FEBKO", "FEBEP", "SOG06", "BMN01", "BLN01", "BTE01"],
        resolution_notes=(
            "SUPERSEDE las cifras 8 cuentas / 4 personas / 1.712 lineas publicadas antes en "
            "bank_statement_channels_by_company.md, el companion de EBS y el skill. Los dos "
            "defectos del instrumento estan corregidos: filtra por conteo crudo y la poblacion "
            "es toda cuenta con al menos un extracto tecleado, no la etiqueta `canal`.")),
]
for i, c in enumerate(NUEVOS, 1):
    c["id"] = mx + i
    cl.append(c)
json.dump(cl, io.open(P, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("claims: +%d (ids %d-%d)" % (len(NUEVOS), mx + 1, mx + len(NUEVOS)))

# ---------- 2. CORREGIR el doc de dominio ------------------------------------
p = "knowledge/domains/Treasury/bank_statement_channels_by_company.md"
s = io.open(p, encoding="utf-8").read()
CORR = """
> ## ⚠️ CORRECCIÓN 2026-08-28 (mismo día) — las cifras de abajo SUBESTIMAN entre 5 y 10 veces
>
> Un cruce de instrumentos midió la población de verdad: **no son 8 cuentas manuales y 4
> personas, son 39 cuentas (34 vivas), 41 usuarios, 802 extractos y 13.942 líneas.**
>
> **Causa:** la etiqueta `canal` se deriva de que *existan* extractos E y M, así que una cuenta
> **97 % tecleada a mano sale MIXTO** y desaparece. Caso puro: **SOG06 (Haití)** tiene 55
> extractos tecleados con **9.623 líneas — el 69 % de todo lo tecleado a mano en UNESCO** —
> frente a 5 electrónicos con **cero** líneas en FEBEP. Es 100 % manual de hecho y figuraba como
> MIXTO. Segundo defecto: el filtro usaba un porcentaje **redondeado**, así que 1 extracto
> tecleado entre 500 daba `0` y salía de la población.
>
> **Y se cae un argumento que publiqué:** «1.712 líneas frente a 11.669 de una sola cuenta
> electrónica» ya no desmonta la oportunidad — son **13.942 frente a 11.669, comparables**.
> Tampoco la confirma: la restricción sigue aguas arriba, en que el banco emita MT940.
>
> Las dos causas están corregidas en el instrumento. Claims 642 y 643.

"""
anc = "### 2 · MANUAL — 8 cuentas · **el hueco de proceso**"
if "CORRECCIÓN 2026-08-28 (mismo día)" in s:
    print("doc: ya estaba")
elif anc in s:
    io.open(p, "w", encoding="utf-8").write(s.replace(anc, CORR.strip() + "\n\n" + anc, 1))
    print("doc: correccion insertada")
else:
    print("doc: ANCLA NO ENCONTRADA -> %s" % anc[:40])
