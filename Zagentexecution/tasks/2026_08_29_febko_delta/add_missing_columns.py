# -*- coding: utf-8 -*-
"""Anade al Golden las columnas que los mineros piden y no estan. Sin un solo DELETE.

POR QUE ESTE FICHERO EXISTE
    Al portar los 7 mineros de banca del P01 en vivo al Golden, faltaban 7 columnas en 5
    tablas. Se diffearon TODAS de golpe contra lo que los mineros piden, en vez de irlas
    descubriendo una por error.

EL CUELLO DE BOTELLA NO ERA SAP, ERA SQLITE
    La primera version hacia un `UPDATE ... WHERE clave` POR FILA. Sobre REGUH (3,7 M filas)
    y sin indice por esa clave, cada UPDATE es un ESCANEO COMPLETO: 500.000 escaneos de 3,7 M
    filas. Se comio 580 segundos y no termino, mientras la lectura de SAP iba a 12.223 filas/s.
    Diagnosticar "va lento" como problema de RED habria sido el mismo error que ya se pago hoy
    con SAPSQL_DATA_LOSS.

    Ahora: se vuelca lo leido en una tabla TEMPORAL, se INDEXA por la clave, y se hace UN SOLO
    UPDATE correlacionado. Un escaneo del destino en vez de medio millon.

REGLAS QUE RESPETA
    - ni DELETE ni DROP sobre datos del Golden (la temporal es suya y se tira)
    - lectura de P01 mes a mes, con limite superior ABIERTO: nunca construye un 31 de febrero
    - declara el ALCANCE de lo que rellena: una columna a medias que nadie declara se lee como
      un cero, y ese es el modo de fallo mas caro de este proyecto
"""

import sqlite3
import sys
import time

sys.path.insert(0, "Zagentexecution/mcp-backend-server-python")

DB = "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"

# (tabla golden, tabla SAP, clave, columnas nuevas, campo fecha, filtro fijo)
PLAN = [
    ("FEBEP_2024_2026", "FEBEP", ["KUKEY", "ESNUM"], ["AKBLN"], "BUDAT", ""),
    ("REGUH", "REGUH", ["LAUFD", "LAUFI", "ZBUKR", "LIFNR", "VBLNR"], ["RBETR"],
     "LAUFD", "ZBUKR = 'UNES'"),
    ("REGUP_SCENARIOS", "REGUP",
     ["LAUFD", "LAUFI", "ZBUKR", "LIFNR", "BELNR", "GJAHR", "BUZEI"], ["BLART", "VBLNR"],
     "LAUFD", "ZBUKR = 'UNES'"),
]


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
    from rfc_helpers import get_connection
    conn = get_connection("P01")
    con = sqlite3.connect(DB)
    for gold, sap, clave, nuevas, fecha, fijo in PLAN:
        hay = set(r[1] for r in con.execute("PRAGMA table_info([%s])" % gold))
        if not set(clave) <= hay:
            print("  %-18s SALTADA: faltan claves %s" % (gold, sorted(set(clave) - hay)))
            continue
        for c in nuevas:
            if c not in hay:
                con.execute('ALTER TABLE [%s] ADD COLUMN "%s" TEXT' % (gold, c))
        con.commit()

        t0 = time.time()
        con.execute("DROP TABLE IF EXISTS _tmp_cols")       # temporal NUESTRA, no dato del Golden
        con.execute("CREATE TABLE _tmp_cols (%s)"
                    % ", ".join('"%s" TEXT' % c for c in clave + nuevas))
        ph = ",".join("?" * len(clave + nuevas))
        leidas = 0
        for ym in meses("202401", "202608"):
            w = " AND ".join(x for x in [fijo, "%s >= '%s01' AND %s < '%s01'"
                                         % (fecha, ym, fecha, sig(ym))] if x)
            try:
                r = conn.call("RFC_READ_TABLE", QUERY_TABLE=sap, DELIMITER="|", ROWCOUNT=0,
                              OPTIONS=[{"TEXT": w}],
                              FIELDS=[{"FIELDNAME": f} for f in clave + nuevas])
            except Exception as e:
                print("     %s ERROR %s" % (ym, str(e)[:70]))
                continue
            filas = [[x.strip() for x in d["WA"].split("|")] for d in r["DATA"]]
            if filas:
                con.executemany("INSERT INTO _tmp_cols VALUES (%s)" % ph, filas)
                leidas += len(filas)
        con.commit()
        con.execute("CREATE INDEX _ix_tmp ON _tmp_cols (%s)"
                    % ", ".join('"%s"' % k for k in clave))
        join = " AND ".join('_tmp_cols."%s" = [%s]."%s"' % (k, gold, k) for k in clave)
        sets = ", ".join('"%s" = (SELECT _tmp_cols."%s" FROM _tmp_cols WHERE %s)' % (c, c, join)
                         for c in nuevas)
        con.execute("UPDATE [%s] SET %s WHERE EXISTS (SELECT 1 FROM _tmp_cols WHERE %s)"
                    % (gold, sets, join))
        con.commit()
        n = con.execute('SELECT COUNT(*) FROM [%s] WHERE "%s" IS NOT NULL'
                        % (gold, nuevas[0])).fetchone()[0]
        tot = con.execute("SELECT COUNT(*) FROM [%s]" % gold).fetchone()[0]
        con.execute("DROP TABLE _tmp_cols")
        con.commit()
        print("  %-18s +%-14s leidas %6d · con valor %6d de %6d · %.0f s"
              % (gold, ",".join(nuevas), leidas, n, tot, time.time() - t0))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
