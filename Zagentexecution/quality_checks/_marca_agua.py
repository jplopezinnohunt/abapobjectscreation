# -*- coding: utf-8 -*-
"""_marca_agua.py — hasta donde ya se extrajo, para no volver a leer lo que ya esta.

LA PREGUNTA QUE LO ORIGINA (JP, 2026-08-29)
    «No entiendo por que lees toda la tabla. Deberias tener un puntero de la ultima data para
    hacer el delta. Si el agente necesita un mes, ¿la lees entera?»

    No deberia, y la estaba leyendo. El refresco de FEBKO barrio los 32 meses del rango para
    anadir 41.466 filas de 60.453 leidas: dos tercios del trafico contra P01 sobraba. Lo unico
    que si justificaba leer todo el rango fue anadir una COLUMNA nueva -- un campo que no
    existe no esta en ninguna fila, asi que ahi no hay delta posible.

LA MARCA VA SOBRE LA FECHA DE ALTA, NO SOBRE LA FECHA DEL DOCUMENTO
    Es la trampa de este patron. Si la marca fuera `AZDAT` (fecha del extracto), un extracto
    con fecha VIEJA cargado ayer no volveria a entrar NUNCA: quedaria por debajo de la marca.
    Va sobre `EDATE` / la fecha en que la fila se dio de alta, que es monotona respecto a la
    extraccion. Cuando una tabla no tiene un campo asi, se DICE -- y entonces su refresco es un
    barrido, no un delta, y cuesta lo que cuesta.

QUE GUARDA
    Una fila por (tabla del Golden, ALCANCE). El alcance importa tanto como la tabla: 'REGUH
    para UNES desde 2024' no es lo mismo que 'REGUH entera', y confundirlos hace creer que hay
    dato donde solo hay NULL.
"""

import os
import sqlite3

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
TABLA = "_gold_marca_agua"


def _asegura(con):
    con.execute("""CREATE TABLE IF NOT EXISTS %s (
                     gold TEXT NOT NULL,
                     alcance TEXT NOT NULL,
                     campo_marca TEXT NOT NULL,
                     hasta TEXT NOT NULL,
                     filas INTEGER,
                     cuando TEXT NOT NULL,
                     nota TEXT,
                     PRIMARY KEY (gold, alcance))""" % TABLA)


def leer(con, gold, alcance=""):
    """Hasta donde se extrajo ya. None = nunca -> el llamador debe barrer, y decirlo."""
    _asegura(con)
    r = con.execute("SELECT campo_marca, hasta, filas, cuando FROM %s "
                    "WHERE gold=? AND alcance=?" % TABLA, (gold, alcance)).fetchone()
    return dict(zip(("campo_marca", "hasta", "filas", "cuando"), r)) if r else None


def escribir(con, gold, campo_marca, hasta, filas, alcance="", nota=""):
    """Se llama DESPUES de que el commit del dato haya ido bien.

    Al reves -- marcar antes de escribir -- la marca dice que hay dato que no llego, y el
    siguiente delta salta ese hueco para siempre. Un agujero que nadie vuelve a mirar es peor
    que no tener marca."""
    import datetime
    _asegura(con)
    con.execute("INSERT OR REPLACE INTO %s VALUES (?,?,?,?,?,?,?)" % TABLA,
                (gold, alcance, campo_marca, str(hasta), filas,
                 datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), nota))
    con.commit()


def desde_el_dato(con, gold, campo_marca, alcance_sql=""):
    """El maximo que YA hay en el Golden. Sirve para arrancar la marca sin volver a P01.

    Es preferible a fiarse de un registro que puede no existir: el dato no opina."""
    w = (" WHERE " + alcance_sql) if alcance_sql else ""
    r = con.execute('SELECT MAX("%s") FROM [%s]%s' % (campo_marca, gold, w)).fetchone()
    return r[0] if r and r[0] else None


def resumen():
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    _ = con  # solo lectura: si la tabla no existe todavia, no se crea desde aqui
    try:
        filas = con.execute("SELECT gold, alcance, campo_marca, hasta, filas, cuando "
                            "FROM %s ORDER BY gold" % TABLA).fetchall()
    except sqlite3.OperationalError:
        print("no hay marcas de agua todavia: todo refresco sera un BARRIDO completo")
        return 0
    print("%-20s %-28s %-8s %-10s %9s  %s"
          % ("tabla", "alcance", "marca", "hasta", "filas", "cuando"))
    print("-" * 100)
    for r in filas:
        print("%-20s %-28s %-8s %-10s %9s  %s"
              % (r[0], (r[1] or "(toda)")[:28], r[2], r[3], r[4], r[5]))
    return 0


if __name__ == "__main__":
    raise SystemExit(resumen())
