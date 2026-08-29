# -*- coding: utf-8 -*-
"""Anade KUNNR a REGUH en el Golden. Es la columna que DESBLOQUEA su delta.

POR QUE ESTA COLUMNA
    REGUH no admitia indice unico: 611.720 filas comparten clave. Medido con
    `field_coverage_sampler`, esas filas llevan KUNNR RELLENO -- son pagos contra una ficha de
    CLIENTE, no de proveedor, y por eso LIFNR viene vacio. Verificado: en el grupo que se repite
    2.075 veces hay 2.075 KUNNR DISTINTOS. Una columna cierra la clave.

EL PROBLEMA DE ESCRIBIRLA, Y COMO SE RESUELVE
    Para meter KUNNR en una fila hay que IDENTIFICARLA -- y son justo las filas que no tienen
    clave unica. Circulo cerrado.

    Se rompe con una FIRMA MAS ANCHA. Medido sobre el Golden:
        clave sola                     -> 611.720 filas sin separar
        clave + NAME1                  -> 2
        clave + NAME1 + RWBTR          -> 0     <- esta
    Las 3.707.737 filas quedan identificadas sin ambiguedad, asi que el UPDATE no puede tocar
    la fila equivocada.

COMO ESCRIBE, Y POR QUE ASI
    Volcado a una tabla TEMPORAL, indexada por la firma, y UN SOLO UPDATE correlacionado. Hacer
    un UPDATE por fila sobre 3,7 M sin indice son 3,7 M de escaneos completos: hoy eso se comio
    580 segundos sin terminar. Ni un DELETE, ni un DROP sobre dato del Golden.

Y AL FINAL, EL INDICE UNICO sobre la clave SAP completa -- con KUNNR dentro -- que es lo que
permite que `gold_delta` vuelva a escribir en REGUH sin apilar duplicados.
"""

import os
import sqlite3
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
GOLD = "REGUH"
FIRMA = ["LAUFD", "LAUFI", "XVORL", "ZBUKR", "LIFNR", "EMPFG", "VBLNR", "NAME1", "RWBTR"]
NUEVA = "KUNNR"
CLAVE_SAP = ["LAUFD", "LAUFI", "XVORL", "ZBUKR", "LIFNR", "KUNNR", "EMPFG", "VBLNR"]
LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kunnr.lock")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def meses(a, b):
    y, m = int(a[:4]), int(a[4:])
    out = []
    while "%04d%02d" % (y, m) <= b:
        out.append("%04d%02d" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def sig(ym):
    y, m = int(ym[:4]), int(ym[4:]) + 1
    return "%04d%02d" % (y + 1, 1) if m == 13 else "%04d%02d" % (y, m)


def main():
    if os.path.exists(LOCK):
        print("YA HAY UN ESCRITOR: %s" % LOCK)
        return 3
    open(LOCK, "w").write(str(os.getpid()))
    try:
        return _main()
    finally:
        os.remove(LOCK)


def _main():
    from rfc_helpers import get_connection
    con = sqlite3.connect(DB)
    cols = set(r[1] for r in con.execute("PRAGMA table_info([%s])" % GOLD))
    for c in FIRMA:
        assert c in cols, "el Golden no tiene %s: sin firma completa no se puede identificar" % c
    if NUEVA not in cols:
        con.execute('ALTER TABLE [%s] ADD COLUMN "%s" TEXT' % (GOLD, NUEVA))
        con.commit()
        print("columna %s anadida" % NUEVA)

    lo, hi = con.execute("SELECT MIN(LAUFD), MAX(LAUFD) FROM [%s]" % GOLD).fetchone()
    conn = get_connection("P01")
    con.execute("DROP TABLE IF EXISTS _tmp_kunnr")          # temporal NUESTRA, no dato del Golden
    con.execute("CREATE TABLE _tmp_kunnr (%s)"
                % ", ".join('"%s" TEXT' % c for c in FIRMA + [NUEVA]))
    ph = ",".join("?" * (len(FIRMA) + 1))
    t0 = time.time()
    leidas = 0
    fallidos = []
    for ym in meses(lo[:6], hi[:6]):
        w = "LAUFD >= '%s01' AND LAUFD < '%s01'" % (ym, sig(ym))
        try:
            r = conn.call("RFC_READ_TABLE", QUERY_TABLE=GOLD, DELIMITER="|", ROWCOUNT=0,
                          OPTIONS=[{"TEXT": w}],
                          FIELDS=[{"FIELDNAME": f} for f in FIRMA + [NUEVA]])
        except Exception as e:
            print("  %s ERROR %s" % (ym, str(e).split("\n")[0][:70]))
            fallidos.append(ym)
            continue
        filas = [[x.strip() for x in d["WA"].split("|")] for d in r["DATA"]]
        if not filas:
            continue
        con.executemany("INSERT INTO _tmp_kunnr VALUES (%s)" % ph, filas)
        con.commit()
        leidas += len(filas)
        if ym.endswith(("01", "07")):
            print("  %s  acumuladas %s filas  (%.0f s)" % (ym, "{:,}".format(leidas),
                                                           time.time() - t0))
    print("\nleidas de P01: %s en %.0f s" % ("{:,}".format(leidas), time.time() - t0))
    if fallidos:
        print("MESES QUE FALLARON: %s -- NO se toca el Golden con datos incompletos"
              % " ".join(fallidos))
        return 2

    con.execute("CREATE INDEX _ix_kunnr ON _tmp_kunnr (%s)"
                % ", ".join('"%s"' % c for c in FIRMA))
    join = " AND ".join('IFNULL(_tmp_kunnr."%s",\'\') = IFNULL([%s]."%s",\'\')' % (c, GOLD, c)
                        for c in FIRMA)
    t1 = time.time()
    con.execute('UPDATE [%s] SET "%s" = (SELECT _tmp_kunnr."%s" FROM _tmp_kunnr WHERE %s) '
                'WHERE EXISTS (SELECT 1 FROM _tmp_kunnr WHERE %s)'
                % (GOLD, NUEVA, NUEVA, join, join))
    con.commit()
    n = con.execute('SELECT COUNT(*) FROM [%s] WHERE "%s" IS NOT NULL' % (GOLD, NUEVA)).fetchone()[0]
    tot = con.execute("SELECT COUNT(*) FROM [%s]" % GOLD).fetchone()[0]
    print("UPDATE en %.0f s · %s de %s filas con KUNNR" % (time.time() - t1,
                                                           "{:,}".format(n), "{:,}".format(tot)))
    con.execute("DROP TABLE _tmp_kunnr")
    con.commit()

    # EL INDICE UNICO: es el objetivo de todo esto.
    try:
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_reguh_delta ON [%s] (%s)"
                    % (GOLD, ", ".join('"%s"' % c for c in CLAVE_SAP)))
        con.commit()
        print("\nINDICE UNICO creado sobre %s" % "+".join(CLAVE_SAP))
        print("-> el delta de REGUH queda DESBLOQUEADO")
    except sqlite3.IntegrityError:
        kk = " || '|' || ".join("IFNULL(\"%s\",'')" % c for c in CLAVE_SAP)
        a, b = con.execute("SELECT COUNT(*), COUNT(DISTINCT %s) FROM [%s]" % (kk, GOLD)).fetchone()
        print("\nel indice SIGUE sin poder crearse: %s filas / %s claves. KUNNR no basta."
              % ("{:,}".format(a), "{:,}".format(b)))
        return 2
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
