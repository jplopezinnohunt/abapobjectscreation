# -*- coding: utf-8 -*-
"""Refresca FEBKO_2024_2026 en el Golden con el DELTA, sin borrar NADA.

POR QUE NO USA gold_refresh
    `refresh_pk_upsert` BORRA las claves que estan en el Golden y no vienen de la lectura de
    P01 (`gold_refresh.py:136-138`). Con un `where` acotado al hueco eso se llevaria por delante
    las 13.604 filas de 2024, y NO daria error: dejaria un Golden mas pequeno y nadie lo notaria.
    Aqui no hay ni un DELETE. Solo `INSERT OR REPLACE` por KUKEY.

EL TROCEADO DE CAMPOS NO ES UNA SUPOSICION, ESTA MEDIDO
    FEBKO_2024_2026 tiene 62 columnas. Probado contra P01 el 2026-08-29: 62 campos dan
    DATA_BUFFER_EXCEEDED; 20 campos entran (fila de 193 bytes). Se leen en trozos con KUKEY
    SIEMPRE en cada trozo, y se cosen por KUKEY. Si un trozo revienta el buffer, se parte solo.

POR QUE MES A MES
    El wrapper de P01 RECHAZA ROWSKIPS, asi que no hay paginacion: se acota por AZDAT. Un mes
    es un trozo comodo y ademas hace el progreso visible y reanudable.

LO QUE NO SE HACE, Y ES DELIBERADO
    No se cuenta primero contra P01 para "saber el hueco". Contar con RFC_READ_TABLE arrastra
    las filas -- el 2026-08-29 costo 61.769 filas por el cable saber UN numero. La propia
    lectura mide: cada mes reporta cuantas trajo, cuantas eran nuevas y cuantas ya estaban.
"""

import datetime
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
GOLD = "FEBKO_2024_2026"
SAP = "FEBKO"
DESDE = "202401"


def meses(desde, hasta):
    y, m = int(desde[:4]), int(desde[4:])
    out = []
    while "%04d%02d" % (y, m) <= hasta:
        out.append("%04d%02d" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def leer(conn, campos, where):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=SAP, DELIMITER="|", ROWCOUNT=0,
                  OPTIONS=[{"TEXT": where}],
                  FIELDS=[{"FIELDNAME": f} for f in campos])
    return [dict(zip(campos, [c.strip() for c in x["WA"].split("|")])) for x in r["DATA"]]


MALOS = set()


def leer_troceado(conn, cols, where, ancho=20):
    """KUKEY en CADA trozo; se cosen por KUKEY. Si un trozo revienta, se parte solo -- no se
    asume un ancho: se mide contra el error que devuelve SAP."""
    resto = [c for c in cols if c != "KUKEY"]
    filas = {}
    i = 0
    while i < len(resto):
        n = ancho - 1
        while n >= 1:
            trozo = ["KUKEY"] + resto[i:i + n]
            try:
                for r in leer(conn, trozo, where):
                    filas.setdefault(r["KUKEY"], {}).update(r)
                break
            except Exception as e:
                # DOS errores distintos piden lo mismo -- leer MENOS -- y la primera version
                # solo trataba uno. SAPSQL_DATA_LOSS es un campo mas ancho de lo que cabe;
                # partir el trozo lo AISLA. Por no contemplarlo se perdieron 13 MESES enteros
                # y el script REPORTO EXITO.
                if not any(k in str(e) for k in ("DATA_BUFFER_EXCEEDED", "SAPSQL_DATA_LOSS")):
                    raise
                if n == 1:
                    # el campo solo tampoco entra: se deja VACIO y se DICE cual es.
                    MALOS.add(trozo[-1])
                    break
                n = max(1, n // 2)
        i += n
    return filas


def main():
    from rfc_helpers import get_connection
    con = sqlite3.connect(DB)
    cols = [r[1] for r in con.execute("PRAGMA table_info([%s])" % GOLD)]
    assert "KUKEY" in cols, "sin KUKEY no hay clave para el upsert"
    ya = set(str(r[0]) for r in con.execute("SELECT KUKEY FROM [%s]" % GOLD))
    print("Golden ANTES: %d filas · %d columnas" % (len(ya), len(cols)))

    conn = get_connection("P01")
    print("P01 conectado (solo lectura). Delta mes a mes desde %s.\n" % DESDE)
    hasta = datetime.date.today().strftime("%Y%m")
    tot_new = tot_upd = tot_leidas = 0
    fallidos = []
    ph = ",".join("?" * len(cols))
    for ym in meses(DESDE, hasta):
        w = "AZDAT >= '%s01' AND AZDAT <= '%s31'" % (ym, ym)
        try:
            filas = leer_troceado(conn, cols, w)
        except Exception as e:
            print("  %s  ERROR: %s" % (ym, str(e).split("\n")[0][:90]))
            fallidos.append(ym)
            continue
        if not filas:
            print("  %s  —" % ym)
            continue
        nuevas = [k for k in filas if k not in ya]
        con.executemany("INSERT OR REPLACE INTO [%s] VALUES (%s)" % (GOLD, ph),
                        [tuple(f.get(c, "") for c in cols) for f in filas.values()])
        con.commit()
        ya |= set(filas)
        tot_leidas += len(filas)
        tot_new += len(nuevas)
        tot_upd += len(filas) - len(nuevas)
        print("  %s  leidas %5d · NUEVAS %5d · ya estaban %5d" % (ym, len(filas), len(nuevas),
                                                                  len(filas) - len(nuevas)))
    fin = con.execute("SELECT COUNT(*) FROM [%s]" % GOLD).fetchone()[0]
    print("\n%s" % ("=" * 70))
    print("leidas de P01: %d · NUEVAS: %d · refrescadas: %d" % (tot_leidas, tot_new, tot_upd))
    print("Golden: %d -> %d filas   (ni un DELETE)" % (len(ya) - tot_new, fin))
    print(con.execute("SELECT MIN(AZDAT),MAX(AZDAT) FROM [%s]" % GOLD).fetchone())
    con.close()
    if MALOS:
        print("\nCOLUMNAS QUE NO SE PUDIERON LEER (quedan VACIAS, y se dice cuales): %s"
              % ", ".join(sorted(MALOS)))
    if fallidos:
        # EXIT != 0. La primera version salio con 0 sin haber entrado 13 MESES, y esos meses
        # conservan sus filas viejas: PARECEN llenos. Un mes que no entra se ve igual que un
        # mes al dia si nadie lo dice. No es dato PERDIDO -- es dato PENDIENTE DE REFRESCAR.
        print("\nMESES QUE NO ENTRARON — %d: %s" % (len(fallidos), " ".join(fallidos)))
        print("  Conservan sus filas VIEJAS: no es dato perdido, es dato pendiente de refrescar,")
        print("  pero PARECEN al dia y no lo estan.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
