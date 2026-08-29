# -*- coding: utf-8 -*-
"""gold_family_coherence_check.py — dos tablas que se UNEN no pueden estar en fechas distintas.

EL DEFECTO QUE LO ORIGINA (2026-08-29)
    No fue que una tabla estuviera vieja. Fue que **dos tablas que se unen tenian fechas
    distintas**: `FEBKO` (cabeceras de extracto) refrescada al 2026-08-28 y `FEBEP` (las
    posiciones DEL MISMO EXTRACTO) parada en 2026-03-30. Refresque el padre y deje al hijo
    atras.

    Nadie lo veia. Ni el censo de delta -- que mira tabla a tabla -- ni la cobertura declarada,
    porque **cada tabla por separado estaba "bien"**. El minero de segregacion de funciones une
    las dos, y su cifra publicada descansaba sobre ese desajuste: al alinearlas paso de 302 a
    316 pagos y de 866.722 a 888.673 USD.

    Lo encontre A MANO, mirando. Eso es exactamente lo que no puede quedarse en la memoria de
    una sesion.

POR QUE UN DESAJUSTE ASI ES PEOR QUE UNA TABLA VIEJA
    Una tabla vieja da un numero pequeno -- se nota. Dos tablas desalineadas dan un numero
    PLAUSIBLE: la union simplemente pierde filas del lado que va por detras, sin error, sin
    hueco visible, sin nada que mirar. Es el modo de fallo mas caro de este proyecto con un
    disfraz nuevo.

COMO SE DERIVAN LAS FAMILIAS (no se mantienen a mano)
    Dos tablas son de la misma familia si COMPARTEN COLUMNAS DE CLAVE. `FEBKO`/`FEBEP`
    comparten `KUKEY`; `REGUH`/`REGUP` comparten `LAUFD+LAUFI+ZBUKR+LIFNR`;
    `BNK_BATCH_HEADER`/`ITEM` comparten su clave de lote. Mantener la lista a mano garantiza
    que la familia numero 8 no entre nunca.

Solo LECTURA. No toca SAP ni escribe en el Golden.
"""

QUALITY_CHECK = {
    "tier": "repo",
    "sobre": "Golden + brain_v2/gold_delta_registry.json",
    "needs": "nada",
    "what": "tablas que se unen y estan en fechas distintas: una union asi pierde filas sin dar "
            "error",
    "args": "[--dias N] [--todas]",
}

import argparse
import datetime
import json
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
REG = os.path.join(REPO, "brain_v2", "gold_delta_registry.json")

# Columnas demasiado comunes para indicar parentesco: casi toda tabla SAP las lleva.
UBICUAS = {"MANDT", "BUKRS", "GJAHR", "WAERS", "SPRAS", "ERNAM", "USNAM", "AEDAT", "ERDAT",
           "BUDAT", "BLDAT", "CPUDT", "SRC", "_first_seen", "_rowhash", "LIFNR", "KUNNR",
           "HKONT", "SAKNR", "KOSTL", "PRCTR", "BELNR", "BUZEI", "ZUONR", "SGTXT", "XBLNR"}


def maximo(g, tabla, campo):
    """El maximo REAL: el mayor valor que no sea futuro. Devuelve (real, futuro_o_None).

    ⛔ Un MAX() a pelo devuelve la BASURA. Medido: FEBKO/FEBEP traen fechas de 2205 y 2208, y
    HRFPM_FM_POS de 2029. Con eso, la primera corrida de esta puerta publico parejas con 65.222
    dias de diferencia y TAPO las de verdad -- los 157 dias entre FEBKO y PAYR, que es lo que
    venia a buscar. Una fecha imposible no es retraso: es dato sucio, y merece su propia lista
    en vez de contaminar esta."""
    hoy = datetime.date.today().strftime("%Y%m%d")
    try:
        r = g.execute('SELECT MAX("%s") FROM [%s] WHERE "%s" <= ?' % (campo, tabla, campo),
                      (hoy,)).fetchone()
        real = str(r[0])[:8] if r and r[0] else None
        b = g.execute('SELECT MAX("%s") FROM [%s]' % (campo, tabla)).fetchone()
        bruto = str(b[0])[:8] if b and b[0] else None
        return real, (bruto if bruto and bruto > hoy else None)
    except sqlite3.Error:
        return None, None


def dias(s):
    try:
        return (datetime.date.today()
                - datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))).days
    except (ValueError, TypeError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=45,
                    help="a partir de cuantos dias de diferencia se considera incoherente")
    ap.add_argument("--todas", action="store_true", help="lista tambien las familias coherentes")
    a = ap.parse_args()

    with open(REG, encoding="utf-8") as fh:
        reg = json.load(fh)["tablas"]
    g = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)

    info, sucias = {}, []
    for t, v in reg.items():
        cols = set(r[1] for r in g.execute("PRAGMA table_info([%s])" % t))
        if not cols:
            continue
        m, futuro = maximo(g, t, v["campo"])
        if futuro:
            sucias.append((t, v["campo"], futuro))
        if not m:
            continue
        info[t] = {"cols": cols, "campo": v["campo"], "hasta": m, "filas": v["filas_hoy"],
                   "dias": dias(m)}

    # FAMILIAS DERIVADAS: comparten columnas de clave que NO sean ubicuas.
    familias = []
    nombres = sorted(info)
    for i, x in enumerate(nombres):
        for y in nombres[i + 1:]:
            comun = (info[x]["cols"] & info[y]["cols"]) - UBICUAS
            if len(comun) < 2:
                continue
            dx, dy = info[x]["dias"], info[y]["dias"]
            if dx is None or dy is None:
                continue
            familias.append((abs(dx - dy), x, y, sorted(comun)[:4],
                             info[x]["hasta"], info[y]["hasta"],
                             min(info[x]["filas"], info[y]["filas"])))
    familias.sort(reverse=True)

    print("=" * 100)
    print("TABLAS QUE SE UNEN Y ESTAN EN FECHAS DISTINTAS")
    print("=" * 100)
    print("  %d tablas con marca · %d parejas emparentadas por clave compartida"
          % (len(info), len(familias)))
    print("  umbral de incoherencia: %d dias de diferencia" % a.dias)
    if sucias:
        print("\n  FECHAS EN EL FUTURO — dato SUCIO, no retraso (se excluyen del maximo):")
        for t, c, f in sorted(sucias)[:8]:
            print("    %-26s %-10s max bruto %s" % (t, c, f))
    print()

    malas = [f for f in familias if f[0] > a.dias]
    ver = familias if a.todas else malas
    if not ver:
        print("  ninguna pareja emparentada difiere mas de %d dias" % a.dias)
    else:
        print("  %-24s %-24s %6s  %-9s %-9s  %s"
              % ("tabla A", "tabla B", "dias", "A hasta", "B hasta", "clave compartida"))
        print("  " + "-" * 96)
        for d, x, y, comun, hx, hy, _ in ver[:25]:
            print("  %-24s %-24s %6d  %-9s %-9s  %s"
                  % (x[:24], y[:24], d, hx, hy, ", ".join(comun)))

    if malas:
        print("\n" + "-" * 100)
        print("FAIL — %d pareja(s) que se unen y no estan en la misma fecha." % len(malas))
        print("  Una tabla vieja da un numero PEQUENO y se nota. Dos tablas desalineadas dan un")
        print("  numero PLAUSIBLE: la union pierde filas del lado atrasado, sin error y sin")
        print("  hueco visible. Medido: alinear FEBKO/FEBEP movio una cifra de riesgo publicada")
        print("  de 302 a 316 pagos y de 866.722 a 888.673 USD.")
        print("\n  Alinea la que va por detras:")
        for d, x, y, comun, hx, hy, _ in malas[:5]:
            atras = x if hx < hy else y
            print("    python Zagentexecution/quality_checks/gold_delta.py %s" % atras)
        return 1
    print("\nOK — las tablas emparentadas estan en fechas compatibles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
