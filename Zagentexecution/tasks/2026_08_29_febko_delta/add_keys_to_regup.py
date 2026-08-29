# -*- coding: utf-8 -*-
"""Anade a REGUP_SCENARIOS los campos que le faltan de la clave SAP: XVORL, KUNNR, EMPFG.

CONTEXTO
    Ya se deduplicaron 2.301 copias BYTE A BYTE (borrado autorizado, verificado antes). Quedan
    2.140 filas que la clave de 7 campos no separa -- el mismo caso que REGUH: falta KUNNR.

LA FIRMA, medida antes de usarla
    clave(7)                          -> 2.140 sin separar
    clave + WRBTR                     ->    69
    clave + WRBTR + XBLNR + SGTXT     ->     0    <- esta
    Con 0 ambiguedades el UPDATE no puede tocar la fila equivocada.

LO QUE ESTE FICHERO HACE DISTINTO A MIS TRES INTENTOS ANTERIORES DE HOY
    1. Mira el PLAN antes de correr. Un join envuelto en IFNULL() anula el indice y convierte
       un UPDATE de 17 s en uno que no termina. Aqui se exige ver SEARCH ... USING INDEX.
    2. Comprueba que no hay NULL en la firma ANTES de usar igualdad directa.
    3. Estima las DOS mitades: la lectura y la escritura. Tres veces hoy estime solo la primera.
"""

import os
import sqlite3
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
GOLD, SAP = "REGUP_SCENARIOS", "REGUP"
FIRMA = ["LAUFD", "LAUFI", "ZBUKR", "LIFNR", "BELNR", "GJAHR", "BUZEI", "WRBTR", "XBLNR", "SGTXT"]
NUEVAS = ["XVORL", "KUNNR", "EMPFG"]
CLAVE_SAP = ["LAUFD", "LAUFI", "XVORL", "ZBUKR", "LIFNR", "KUNNR", "EMPFG", "VBLNR",
             "BELNR", "BUZEI", "GJAHR"]

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
    from rfc_helpers import get_connection
    con = sqlite3.connect(DB)
    cols = set(r[1] for r in con.execute("PRAGMA table_info([%s])" % GOLD))
    faltan_firma = [c for c in FIRMA if c not in cols]
    assert not faltan_firma, "el Golden no tiene %s: sin firma completa no se identifica" % faltan_firma

    q = "SELECT COUNT(*) FROM [%s] WHERE %s" % (GOLD, " OR ".join('[%s] IS NULL' % c for c in FIRMA))
    nulos = con.execute(q).fetchone()[0]
    print("filas con NULL en la firma: %d %s" % (nulos, "(igualdad directa es segura)" if not nulos
                                                 else "<<< NO usar igualdad directa"))
    assert nulos == 0

    for c in NUEVAS:
        if c not in cols:
            con.execute('ALTER TABLE [%s] ADD COLUMN "%s" TEXT' % (GOLD, c))
    con.commit()

    lo, hi = con.execute("SELECT MIN(LAUFD), MAX(LAUFD) FROM [%s]" % GOLD).fetchone()
    conn = get_connection("P01")
    con.execute("DROP TABLE IF EXISTS _tmp_regup")
    con.execute("CREATE TABLE _tmp_regup (%s)"
                % ", ".join('"%s" TEXT' % c for c in FIRMA + NUEVAS))
    ph = ",".join("?" * (len(FIRMA) + len(NUEVAS)))
    t0, leidas, fallidos = time.time(), 0, []
    for ym in meses(lo[:6], hi[:6]):
        w = "ZBUKR = 'UNES' AND LAUFD >= '%s01' AND LAUFD < '%s01'" % (ym, sig(ym))
        try:
            r = conn.call("RFC_READ_TABLE", QUERY_TABLE=SAP, DELIMITER="|", ROWCOUNT=0,
                          OPTIONS=[{"TEXT": w}],
                          FIELDS=[{"FIELDNAME": f} for f in FIRMA + NUEVAS])
        except Exception as e:
            print("  %s ERROR %s" % (ym, str(e).split("\n")[0][:70]))
            fallidos.append(ym)
            continue
        filas = [[x.strip() for x in d["WA"].split("|")] for d in r["DATA"]]
        if filas:
            con.executemany("INSERT INTO _tmp_regup VALUES (%s)" % ph, filas)
            con.commit()
            leidas += len(filas)
    print("leidas de P01: %s en %.0f s" % ("{:,}".format(leidas), time.time() - t0))
    if fallidos:
        print("MESES QUE FALLARON: %s -- no se toca el Golden con datos incompletos"
              % " ".join(fallidos))
        return 2

    con.execute("CREATE INDEX _ix_regup ON _tmp_regup (%s)"
                % ", ".join('"%s"' % c for c in FIRMA))
    join = " AND ".join('t."%s" = [%s]."%s"' % (c, GOLD, c) for c in FIRMA)
    sets = ", ".join('"%s" = (SELECT t."%s" FROM _tmp_regup t WHERE %s)' % (c, c, join)
                     for c in NUEVAS)
    sql = "UPDATE [%s] SET %s WHERE EXISTS (SELECT 1 FROM _tmp_regup t WHERE %s)" % (GOLD, sets, join)

    plan = [r[-1] for r in con.execute("EXPLAIN QUERY PLAN " + sql)]
    usa_indice = any("USING" in p and "INDEX" in p for p in plan)
    print("\nplan: %s" % (" | ".join(plan)[:150]))
    if not usa_indice:
        print("EL PLAN NO USA EL INDICE -- no se ejecuta. Asi es como un UPDATE de 17 s se "
              "convierte en uno que no termina.")
        return 2

    t1 = time.time()
    con.execute(sql)
    con.commit()
    n = con.execute('SELECT COUNT(*) FROM [%s] WHERE "KUNNR" IS NOT NULL' % GOLD).fetchone()[0]
    tot = con.execute("SELECT COUNT(*) FROM [%s]" % GOLD).fetchone()[0]
    print("UPDATE en %.0f s -> %s de %s filas con los campos de clave"
          % (time.time() - t1, "{:,}".format(n), "{:,}".format(tot)))
    con.execute("DROP TABLE _tmp_regup")
    con.commit()

    try:
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_regup_delta ON [%s] (%s)"
                    % (GOLD, ", ".join('"%s"' % c for c in CLAVE_SAP)))
        con.commit()
        print("\nINDICE UNICO creado -> el delta de %s queda DESBLOQUEADO" % GOLD)
    except sqlite3.IntegrityError:
        kk = " || '|' || ".join("IFNULL(\"%s\",'')" % c for c in CLAVE_SAP)
        a, b = con.execute("SELECT COUNT(*), COUNT(DISTINCT %s) FROM [%s]" % (kk, GOLD)).fetchone()
        print("\nel indice NO se pudo crear: %s filas / %s claves" % ("{:,}".format(a),
                                                                      "{:,}".format(b)))
        return 2
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
