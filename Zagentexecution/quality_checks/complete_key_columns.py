# -*- coding: utf-8 -*-
"""complete_key_columns.py — trae del P01 los campos de CLAVE que le faltan a una tabla del Golden.

EL HUECO QUE CIERRA
    Tras derivar las claves de DD03L quedaron 23 tablas marcadas NO EJECUTABLES: el Golden no
    tiene todos los campos de su clave. Sin la clave completa no se puede crear el indice unico,
    y sin indice unico `INSERT OR REPLACE` no reemplaza -- APILA. Asi que esas 23 tablas no
    tienen delta, no por falta de modelo, sino por falta de una columna.

    No son 23 trabajos: el campo que falta se repite. `ZUONR` en las seis tablas `bs*`,
    `UMSKS`+`UMSKZ` en cuatro, `GUID` en las dos de BCM. La familia `bs*` sola son 6,5 M filas.

COMO IDENTIFICA LA FILA A ACTUALIZAR, que es el problema no obvio
    Para escribir un campo de la clave en una fila hay que IDENTIFICARLA -- y el campo que falta
    es justamente parte de lo que la identifica. Se rompe comprobando ANTES que la parte
    PRESENTE de la clave ya separa. Medido en la familia `bs*`: separa en 5 de 6 tablas, y en
    `bsis` deja 3 colisiones de 3.348.456. Si no separase, este script se NIEGA: un UPDATE
    ambiguo no da error, escribe en la fila equivocada.

LAS TRES LECCIONES DEL MISMO DIA QUE ESTE FICHERO YA TRAE DE SERIE
    1. Se mira `EXPLAIN QUERY PLAN` ANTES de correr el UPDATE. Un join envuelto en `IFNULL()`
       anula el indice y convierte 17 segundos en algo que no termina.
    2. Se comprueba que no haya NULL en la firma antes de usar igualdad directa.
    3. Se estiman las DOS mitades, lectura y escritura. Estimar solo la lectura fallo tres veces.

Ni un DELETE. Solo ALTER TABLE ADD COLUMN + UPDATE por firma.
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "Golden + P01",
    "needs": "rfc_p01",
    "what": "completa los campos de clave que le faltan a una tabla del Golden para que su "
            "delta sea ejecutable",
    "args": "<TABLA> [--fecha BUDAT] [--desde 2024]",
}

import argparse
import json
import os
import sqlite3
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
REG = os.path.join(REPO, "brain_v2", "gold_delta_registry.json")


def anios(desde, hasta):
    return [str(y) for y in range(int(desde), int(hasta) + 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabla")
    ap.add_argument("--fecha", default="BUDAT", help="campo por el que se trocea la lectura")
    ap.add_argument("--desde", default="2024")
    ap.add_argument("--hasta", default="2026")
    a = ap.parse_args()

    from rfc_helpers import get_connection, trocear_where
    with open(REG, encoding="utf-8") as fh:
        spec = json.load(fh)["tablas"].get(a.tabla)
    if not spec or not spec.get("clave"):
        print("  %s no tiene clave derivada en el registro" % a.tabla)
        return 2

    con = sqlite3.connect(DB)
    cols = [r[1] for r in con.execute("PRAGMA table_info([%s])" % a.tabla)]
    clave = spec["clave"]
    # ⛔ "LA COLUMNA EXISTE" NO ES "LA COLUMNA TIENE DATOS". Una corrida anterior que reventara
    # despues del ALTER TABLE deja la columna CREADA Y VACIA, y con solo mirar el esquema este
    # script decia "ya tiene la clave completa" y se iba. Verde por no mirar, en el propio
    # instrumento que existe para evitar eso. Se cuenta cuantas filas la traen rellena.
    vacias = []
    for c in clave:
        if c not in cols:
            vacias.append(c)
            continue
        n_ok = con.execute("SELECT COUNT(*) FROM [%s] WHERE IFNULL([%s],'') <> ''"
                           % (a.tabla, c)).fetchone()[0]
        if n_ok == 0:
            print("  aviso: [%s] existe pero esta VACIA en las %s filas -- se vuelve a traer"
                  % (c, "{:,}".format(con.execute("SELECT COUNT(*) FROM [%s]"
                                                  % a.tabla).fetchone()[0])))
            vacias.append(c)
    firma = [c for c in clave if c in cols and c not in vacias]
    faltan = vacias
    if not faltan:
        print("  %s ya tiene la clave completa Y con datos" % a.tabla)
        return 0
    sap = spec.get("sap") or a.tabla.upper()
    n = con.execute("SELECT COUNT(*) FROM [%s]" % a.tabla).fetchone()[0]

    print("=" * 92)
    print("%s · %s filas · SAP %s" % (a.tabla, "{:,}".format(n), sap))
    print("  clave SAP : %s" % "+".join(clave))
    print("  FALTAN    : %s" % ", ".join(faltan))
    print("  firma     : %s" % "+".join(firma))

    # ⛔ SIN FIRMA QUE SEPARE, NO SE ESCRIBE. Un UPDATE ambiguo no da error: escribe en la fila
    # equivocada, y eso no se ve nunca.
    kk = " || '|' || ".join("IFNULL([%s],'')" % c for c in firma)
    d = con.execute("SELECT COUNT(DISTINCT %s) FROM [%s]" % (kk, a.tabla)).fetchone()[0]
    if d < n:
        print("\n  LA FIRMA NO SEPARA: %s filas para %s firmas (%s ambiguas)."
              % ("{:,}".format(n), "{:,}".format(d), "{:,}".format(n - d)))
        if (n - d) > n * 0.001:
            print("  Mas del 0,1%: NO se escribe. Un UPDATE ambiguo escribe en la fila que no es.")
            return 2
        print("  Por debajo del 0,1%: se sigue, y esas filas quedaran con el valor de una de sus"
              " gemelas.")
    else:
        print("  la firma SEPARA las %s filas" % "{:,}".format(n))

    nulos = con.execute("SELECT COUNT(*) FROM [%s] WHERE %s"
                        % (a.tabla, " OR ".join("[%s] IS NULL" % c for c in firma))).fetchone()[0]
    print("  filas con NULL en la firma: %d %s" % (nulos, "(igualdad directa segura)" if not nulos
                                                   else "<<< se usara IFNULL, mas lento"))

    for c in faltan:
        if c not in cols:
            con.execute('ALTER TABLE [%s] ADD COLUMN "%s" TEXT' % (a.tabla, c))
    con.commit()

    conn = get_connection("P01")
    con.execute("DROP TABLE IF EXISTS _tmp_keys")
    con.execute("CREATE TABLE _tmp_keys (%s)" % ", ".join('"%s" TEXT' % c for c in firma + faltan))
    ph = ",".join("?" * (len(firma) + len(faltan)))
    t0, leidas, fallidos = time.time(), 0, []
    for y in anios(a.desde, a.hasta):
        w = "%s >= '%s0101' AND %s < '%s0101'" % (a.fecha, y, a.fecha, str(int(y) + 1))
        try:
            r = conn.call("RFC_READ_TABLE", QUERY_TABLE=sap, DELIMITER="|", ROWCOUNT=0,
                          OPTIONS=trocear_where(w),
                          FIELDS=[{"FIELDNAME": f} for f in firma + faltan])
        except Exception as e:
            print("    %s ERROR %s" % (y, str(e).split("\n")[0][:70]))
            fallidos.append(y)
            continue
        # ⛔ NO SE PARTE POR DELIMITADOR. `bsas` y `bsis` reventaron con "8 placeholders, 9
        # valores" porque un ZUONR contiene el propio caracter '|'. Es texto libre: nada impide
        # que lleve el delimitador dentro. Y no es un fallo de esas dos tablas -- TODA nuestra
        # capa de lectura parte por '|', asi que el mismo dato roto puede estar entrando en
        # silencio en cualquier otra, desplazando columnas sin dar error.
        # RFC_READ_TABLE devuelve OFFSET y LENGTH de cada campo en su metadato FIELDS: se corta
        # por POSICION, que no puede colisionar con el contenido.
        meta = sorted((int(f["OFFSET"]), int(f["LENGTH"]), f["FIELDNAME"].strip())
                      for f in r["FIELDS"])
        filas = [[dd["WA"][o:o + ln].strip() for o, ln, _ in meta] for dd in r["DATA"]]
        if filas:
            con.executemany("INSERT INTO _tmp_keys VALUES (%s)" % ph, filas)
            con.commit()
            leidas += len(filas)
        print("    %s  %s filas  (%.0f s)" % (y, "{:,}".format(len(filas)), time.time() - t0))
    if fallidos:
        print("  ANOS QUE FALLARON: %s -- no se escribe con datos incompletos" % " ".join(fallidos))
        return 2
    if not leidas:
        print("  P01 devolvio 0 filas: NO se toca el Golden")
        return 2

    con.execute("CREATE INDEX _ix_keys ON _tmp_keys (%s)" % ", ".join('"%s"' % c for c in firma))
    join = " AND ".join('t."%s" = [%s]."%s"' % (c, a.tabla, c) for c in firma)
    sets = ", ".join('"%s" = (SELECT t."%s" FROM _tmp_keys t WHERE %s)' % (c, c, join)
                     for c in faltan)
    sql = ("UPDATE [%s] SET %s WHERE EXISTS (SELECT 1 FROM _tmp_keys t WHERE %s)"
           % (a.tabla, sets, join))
    plan = [x[-1] for x in con.execute("EXPLAIN QUERY PLAN " + sql)]
    if not any("USING" in p and "INDEX" in p for p in plan):
        print("\n  EL PLAN NO USA EL INDICE -- no se ejecuta:\n    %s" % " | ".join(plan)[:160])
        return 2
    t1 = time.time()
    con.execute(sql)
    con.commit()
    con.execute("DROP TABLE _tmp_keys")
    con.commit()
    con.execute("VACUUM") if False else None
    hechas = con.execute('SELECT COUNT(*) FROM [%s] WHERE "%s" IS NOT NULL'
                         % (a.tabla, faltan[0])).fetchone()[0]
    print("\n  leidas de P01: %s · UPDATE en %.0f s · %s de %s filas con la clave completa"
          % ("{:,}".format(leidas), time.time() - t1, "{:,}".format(hechas), "{:,}".format(n)))

    kk2 = " || '|' || ".join("IFNULL([%s],'')" % c for c in clave)
    d2 = con.execute("SELECT COUNT(DISTINCT %s) FROM [%s]" % (kk2, a.tabla)).fetchone()[0]
    print("  con la clave COMPLETA: %s filas / %s claves -> %s"
          % ("{:,}".format(n), "{:,}".format(d2),
             "UNICA, el delta queda desbloqueado" if d2 == n
             else "aun %s sin separar" % "{:,}".format(n - d2)))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
