# -*- coding: utf-8 -*-
"""conclusion_saturation_check.py — ¿a partir de cuanta historia deja de cambiar la conclusion?

LA PREGUNTA (JP, 2026-08-29)
    «Hay un punto donde la conclusion de un minero no cambia. Si ya tienes mas de 4 a 6 meses
    de info, la conclusion no cambiara practicamente. Los datos de refresco son mas criticos
    cuando medimos LOGS.»

    Es una hipotesis, y tiene numero. Este instrumento la MIDE en vez de darla por buena.

POR QUE IMPORTA, Y MUCHO
    De la respuesta depende cuanto hay que refrescar el Golden. Si una conclusion satura a los
    6 meses, tener el 28,8% de una ventana de 2 anos NO invalida nada -- y toda la alarma sobre
    la cobertura estaba mal calibrada. Si NO satura, cada mes que falta mueve el resultado y el
    refresco es obligatorio antes de publicar.

    Y no hay una sola respuesta: **depende de la CLASE de dato**.
      - estructural (que cuentas existen, que formato usan): cambia poco, satura pronto
      - distribucion (que proporcion de extractos entra por cada canal): satura pronto
      - EXISTENCIA de un caso concreto (¿llego YA el extracto de la cuenta nueva?): NO satura
        nunca -- es justo lo que preguntaba INC-000013624, y ahi el ultimo mes lo es todo
      - LOGS: retencion corta y volumen enorme; lo viejo se purga. Refrescar es todo.

COMO LO MIDE
    Toma la conclusion completa (toda la historia disponible) como referencia, y la recalcula
    con ventanas de 1, 2, 3, 4, 6, 9, 12, 18 y 24 meses hacia atras. Para cada ventana dice
    que porcentaje de la conclusion COINCIDE con la de referencia. La saturacion es donde esa
    curva se aplana.

    Dos conclusiones distintas, a proposito:
      A · POBLACION  — que cuentas aparecen (¿descubro cuentas nuevas con mas historia?)
      B · ETIQUETA   — que canal se le asigna a cada cuenta (¿cambia el veredicto?)

    B es la que de verdad importa: descubrir una cuenta mas no cambia lo que dices de las otras.

Solo LECTURA sobre el Golden. No toca SAP.
"""

QUALITY_CHECK = {
    "tier": "repo",
    "sobre": "Golden FEBKO_2024_2026",
    "needs": "nada",
    "what": "a partir de cuantos meses de historia deja de cambiar la conclusion de un minero",
    "args": "[--bukrs UNES] [--hasta AAAAMM]",
}

import argparse
import collections
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
VENTANAS = (1, 2, 3, 4, 6, 9, 12, 18, 24)


def restar(ym, n):
    y, m = int(ym[:4]), int(ym[4:])
    m -= n - 1
    while m < 1:
        m += 12
        y -= 1
    return "%04d%02d" % (y, m)


def conclusion(filas):
    """La conclusion del censo de canales: por cuenta, que canal usa.

    Es la MISMA regla que publica bank_statement_channel_census -- si aqui se usara otra, la
    saturacion medida no diria nada sobre ese minero."""
    por = collections.defaultdict(collections.Counter)
    for cuenta, efart in filas:
        por[cuenta][efart or "?"] += 1
    out = {}
    for c, k in por.items():
        e, m = k.get("E", 0), k.get("M", 0)
        out[c] = "ELECTRONICO" if m == 0 else "MANUAL" if e == 0 else "MIXTO"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="UNES")
    ap.add_argument("--hasta", default="")
    a = ap.parse_args()

    g = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    w = "WHERE BUKRS = '%s'" % a.bukrs if a.bukrs else ""
    filas = g.execute("SELECT SUBSTR(AZDAT,1,6), BUKRS||'/'||HBKID||'-'||HKTID, EFART "
                      "FROM FEBKO_2024_2026 %s" % w).fetchall()
    meses = sorted(set(f[0] for f in filas))
    hasta = a.hasta or meses[-1]
    filas = [f for f in filas if f[0] <= hasta]
    print("=" * 96)
    print("¿CUANTA HISTORIA HACE FALTA PARA QUE LA CONCLUSION NO CAMBIE?")
    print("=" * 96)
    print("  sociedad %s · %d cabeceras · historia %s..%s (%d meses)"
          % (a.bukrs or "todas", len(filas), meses[0], hasta, len(meses)))

    ref = conclusion([(f[1], f[2]) for f in filas])
    print("  referencia = TODA la historia: %d cuentas\n" % len(ref))
    print("  %-9s %-9s %-11s %-13s %s" %
          ("ventana", "desde", "cuentas", "POBLACION", "ETIQUETA (la que importa)"))
    print("  " + "-" * 88)
    prev = None
    for n in VENTANAS:
        if n > len(meses):
            break
        desde = restar(hasta, n)
        sub = [(f[1], f[2]) for f in filas if f[0] >= desde]
        c = conclusion(sub)
        pob = 100.0 * len(c) / max(1, len(ref))
        iguales = sum(1 for k, v in c.items() if ref.get(k) == v)
        etiq = 100.0 * iguales / max(1, len(c))
        # lo que de verdad se le pregunta a un minero: de TODA la conclusion final, cuanta
        # habrias acertado con solo esta ventana
        cobertura_total = 100.0 * iguales / max(1, len(ref))
        marca = ""
        if prev is not None and abs(cobertura_total - prev) < 1.0:
            marca = "  <- ya no se mueve (<1 punto)"
        print("  %-9s %-9s %4d (%3.0f%%) %8.1f%%      %5.1f%% de las suyas · %5.1f%% del total%s"
              % ("%d mes%s" % (n, "" if n == 1 else "es"), desde, len(c), pob, pob,
                 etiq, cobertura_total, marca))
        prev = cobertura_total

    print("\n  COMO SE LEE, y el limite:")
    print("  Esto mide una conclusion de DISTRIBUCION (que canal usa cada cuenta). NO se puede")
    print("  extrapolar a una de EXISTENCIA — '¿ya llego el extracto de la cuenta nueva?' —,")
    print("  que es lo que preguntaba INC-000013624 y donde el ULTIMO mes lo es todo.")
    print("  Y no dice nada de los LOGS: ahi la retencion es corta y lo viejo se purga, asi que")
    print("  refrescar no es una mejora, es la unica forma de tener el dato.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
