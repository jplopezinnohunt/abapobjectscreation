# -*- coding: utf-8 -*-
"""validation_substitution_drift_check.py — ¿el perímetro de contabilización sigue siendo el documentado?

MINERO (clase CONFORMIDAD). Lee el GOLDEN, nunca P01 (regla: extracción y minería son actos
distintos — el refresco es `sap_data_extraction/scripts/extract_yfmxchk_control_tables.py`).

Pregunta falsable: las tres tablas de control del perímetro (yfmxchk / yfmxchkp / yxuser)
¿siguen diciendo lo que los claims 648-650 documentaron en s111 (2026-08-30)?

Qué vigila y por qué es un RIESGO y no un dato:
  - YXUSER: la tabla de bypass. En s111 tiene UNA fila (FM/HIPER) y NADIE tiene 'BC' ni
    'FRTL'. Una fila nueva aquí es una concesión de bypass de controles de contabilización
    — merece mirada de incidente el día que aparezca.
  - YFMXCHKP: la puerta fiscal. En s111 está APAGADA en toda variante con lector (FY/BB/BE);
    las 9 filas activas son CHTYP='CM' sin lector en el corpus. Una variante con lector que
    se ACTIVE cambia el comportamiento de TODAS las contabilizaciones de esa sociedad.
  - YFMXCHK: el multiplexor XCHECK. La distribución s111 es Y=3003 T=38 F=35 H=28 D=9 Z=2.
    Un cambio de distribución = alguien movió reglas de negocio por tabla (sin transporte de
    código), que es exactamente la clase de cambio que ningún análisis de customizing ve.

Límite declarado: compara contra la ÚLTIMA extracción en el Gold DB, no contra P01 en vivo.
Si la extracción está vieja, el drift real es invisible — por eso la edad de la extracción
es el primer hallazgo, no una nota al pie.
"""

import os
import sqlite3
import sys
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _HERE)
from _hallazgos import Hallazgos  # noqa: E402

GOLD = os.path.join(_REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")

# La foto documentada (claims 648-650, s111, extracción P01 2026-08-30).
BASELINE_XCHECK = {"Y": 3003, "T": 38, "F": 35, "H": 28, "D": 9, "Z": 2}
BASELINE_YXUSER = {("FM", "HIPER")}
BASELINE_CHKP_ACTIVE = {("CM", 9)}   # (CHTYP, filas ACTIV='X') — CM sin lector en el corpus
MAX_AGE_DAYS = 35                     # más viejo que esto = el minero está ciego


def main():
    h = Hallazgos(
        "validation_substitution_drift_check",
        denominador="3 tablas de control del perímetro (yfmxchk/yfmxchkp/yxuser) vs "
                    "su mapa documentado en claims 648-650 (s111)",
        sistema="P01 (via Gold DB)", ventana="foto s111 -> última extracción")
    db = sqlite3.connect(GOLD)

    # 0) ¿de cuándo es la foto? Un drift-check sobre datos viejos es un semáforo pintado de verde.
    row = db.execute(
        "SELECT MAX(extracted_at) FROM _config_frontier_manifest "
        "WHERE grp='posting_gate_controls'").fetchone()
    age_days = None
    if row and row[0]:
        age_days = (datetime.now() - datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")).days
    if age_days is None:
        h.desafio("las tablas de control del perímetro NO están en el Gold DB — el drift es invisible",
                  tamano="0 de 3 tablas presentes",
                  evidencia="_config_frontier_manifest sin grp='posting_gate_controls'",
                  limite="este minero no lee P01; la extracción es un paso previo",
                  accion="python Zagentexecution/sap_data_extraction/scripts/extract_yfmxchk_control_tables.py")
        h.emitir()
        return 0
    if age_days > MAX_AGE_DAYS:
        h.desafio("la foto del perímetro tiene %d días — el drift real es invisible" % age_days,
                  tamano="%d días > umbral %d" % (age_days, MAX_AGE_DAYS),
                  evidencia="_config_frontier_manifest.extracted_at",
                  limite="comparo contra la extracción, no contra P01 en vivo",
                  accion="rerun extract_yfmxchk_control_tables.py y volver a pasar este check")

    # 1) YXUSER — cada fila nueva es una concesión de bypass.
    vivas = {(r[0].strip(), r[1].strip()) for r in
             db.execute("SELECT XTYPE, UNAME FROM yxuser")}
    nuevas = vivas - BASELINE_YXUSER
    idas = BASELINE_YXUSER - vivas
    if nuevas:
        h.riesgo("YXUSER tiene titulares de bypass NUEVOS respecto a s111: %s"
                 % ", ".join("%s/%s" % t for t in sorted(nuevas)),
                 tamano="%d filas nuevas sobre baseline de 1" % len(nuevas),
                 evidencia="Gold DB yxuser vs claim 649",
                 limite="no sé QUIÉN la concedió ni cuándo — eso pide CDHDR/log",
                 accion="tratar como cambio de control: ¿qué rutina desbloquea ese XTYPE y quién lo pidió?")
    if idas:
        h.dato("YXUSER perdió titulares respecto a s111: %s"
               % ", ".join("%s/%s" % t for t in sorted(idas)),
               tamano="%d de 1" % len(idas),
               evidencia="Gold DB yxuser vs claim 649",
               limite="una baja puede ser limpieza o un borrado por error",
               accion="actualizar claim 649 si se confirma")

    # 2) YFMXCHKP — una variante con lector que se activa cambia todas las contabilizaciones.
    act = {}
    for chtyp, n in db.execute(
            "SELECT CHTYP, COUNT(*) FROM yfmxchkp WHERE ACTIV='X' GROUP BY CHTYP"):
        act[chtyp.strip()] = n
    reader_backed = {"FY", "BB", "BE"}
    encendidas = sorted(v for v in act if v in reader_backed)
    if encendidas:
        h.riesgo("la puerta fiscal YFMXCHKP se ENCENDIÓ en variante(s) con lector: %s"
                 % ", ".join(encendidas),
                 tamano="; ".join("%s=%d filas activas" % (v, act[v]) for v in encendidas),
                 evidencia="Gold DB yfmxchkp vs claim 650 (en s111 todas apagadas)",
                 limite="no distingo activación deliberada de cierre de un error",
                 accion="verificar con el dueño del cierre qué sociedad/mes queda bloqueado")
    cm_now = act.get("CM", 0)
    if cm_now != dict(BASELINE_CHKP_ACTIVE).get("CM", 0):
        h.dato("las filas activas CHTYP='CM' de YFMXCHKP cambiaron: %d (s111: 9)" % cm_now,
               tamano="%d filas ACTIV='X'" % cm_now,
               evidencia="Gold DB yfmxchkp",
               limite="CM sigue sin lector conocido en el corpus extraído",
               accion="si aparece un lector de 'CM', el claim 650 se supersede")

    # 3) YFMXCHK — distribución XCHECK.
    dist = {r[0].strip(): r[1] for r in
            db.execute("SELECT XCHECK, COUNT(*) FROM yfmxchk GROUP BY XCHECK")}
    deltas = []
    for letra in sorted(set(dist) | set(BASELINE_XCHECK)):
        antes, ahora = BASELINE_XCHECK.get(letra, 0), dist.get(letra, 0)
        if antes != ahora:
            deltas.append("%s: %d -> %d" % (letra, antes, ahora))
    if deltas:
        h.dato("la distribución XCHECK de YFMXCHK se movió respecto a s111: %s"
               % "; ".join(deltas),
               tamano="%d letras cambiaron de %d totales" % (len(deltas), len(set(dist) | set(BASELINE_XCHECK))),
               evidencia="Gold DB yfmxchk vs claim 648",
               limite="un alta en 'Y' es rutina de cierre; una letra NUEVA es una regla nueva sin código",
               accion="letra nueva o salto grande -> leer qué fondos entraron y quién los pidió")
        letras_nuevas = set(dist) - set(BASELINE_XCHECK)
        if letras_nuevas:
            h.desafio("YFMXCHK trae letra(s) XCHECK sin semántica documentada: %s"
                      % ", ".join(sorted(letras_nuevas)),
                      tamano="%d letras sin consumidor conocido" % len(letras_nuevas),
                      evidencia="ninguna rutina del corpus consulta esas letras (claim 648)",
                      limite="el corpus extraído puede no ser el total del código",
                      accion="grep del corpus por la letra; si nadie la lee, es config muerta o código nuevo sin extraer")

    if not h.items:
        h.dato("el perímetro de contabilización sigue exactamente como lo documentó s111",
               tamano="yxuser=1 · yfmxchkp activas CM=9 (sin lector) · XCHECK Y=3003 T=38 F=35 H=28 D=9 Z=2",
               evidencia="Gold DB vs claims 648-650, foto de hace %d días" % (age_days or 0),
               limite="vigencia = edad de la extracción",
               accion="nada")
    h.emitir()
    return 0


if __name__ == "__main__":
    sys.exit(main())
