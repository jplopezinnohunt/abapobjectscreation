# -*- coding: utf-8 -*-
"""field_coverage_sampler.py — que campos USA de verdad una tabla, y cuales de esos no tenemos.

LA CRITICA QUE LO ORIGINA (JP, 2026-08-29)
    «Tu idea me parece estupida. Para algo construimos miners.»

    Tenia razon. Habia hecho A MANO -- en un script de usar y tirar -- un metodo que es
    GENERICO: coger una muestra pequena de filas, leer TODOS los campos de la tabla, y mirar
    cuales vienen con valor. Eso no es una respuesta a una pregunta: es un INSTRUMENTO, y sirve
    para cualquier tabla y cualquier escenario.

EL DOLOR QUE RESUELVE
    El Golden guarda 30 de los 180 campos de REGUH -- el 17%. Durante toda la sesion las
    columnas que faltaban se fueron descubriendo POR ERROR, una a una, cuando un minero las
    pedia y reventaba. Este minero da la lista entera de golpe y ANTES.

POR QUE UNA MUESTRA PEQUENA BASTA, Y POR QUE ES LO UNICO SENSATO
    Leer 180 campos de una tabla de millones de filas es imposible: RFC_READ_TABLE tiene un
    buffer de 512 bytes por fila. Pero para saber QUE CAMPOS SE USAN en un escenario no hace
    falta la poblacion: hacen falta 10 filas de ese escenario y las 180 columnas. Se lee ANCHO
    y CORTO en vez de estrecho y largo -- que es exactamente al reves de como se extrae.

    Su limite, y hay que decirlo al publicar: un campo que sale vacio en 10 filas puede estar
    relleno en otras. Esto dice QUE SE USA, nunca que algo no se use.

LO QUE ENCONTRO EN SU PRIMERA CORRIDA
    Muestreando 10 propuestas de pago sin proveedor (REGUH, XVORL='X', LIFNR=''): 44 campos con
    valor de 177, y entre ellos **KUNNR relleno** -- el numero de cliente, que es la clave que
    faltaba y que el Golden no tiene. Tres hipotesis mias habian fallado antes de esto por no
    haber mirado la fila entera.

Solo LECTURA. Muestra acotada por ROWCOUNT: no arrastra poblacion.
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "una tabla de SAP frente a su copia en el Golden",
    "needs": "rfc_p01",
    "what": "que campos usa de verdad un escenario, y cuales de esos no estan en el Golden",
    "args": "<TABLA> [--where \"...\"] [--n 10] [--system P01]",
}

import argparse
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
# Un campo con esto NO cuenta como "usado": es el vacio de SAP con otra cara.
VACIOS = {"", "0", "0.00", "0.000", "00000000", "0000000000", "0.00000",
          "0000000000000000", "000000", "00"}


def campos_de(conn, tabla):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD03L", DELIMITER="|", ROWCOUNT=0,
                  OPTIONS=[{"TEXT": "TABNAME = '%s'" % tabla}],
                  FIELDS=[{"FIELDNAME": "FIELDNAME"}])
    # los .INCLUDE no son campos: son estructuras embebidas y RFC_READ_TABLE los rechaza
    return [x["WA"].strip() for x in r["DATA"] if not x["WA"].strip().startswith(".")]


def en_el_golden(tabla):
    """Como se llama esa tabla en el Golden y que columnas tiene. Prueba variantes de nombre
    porque el Golden mezcla mayusculas, minusculas y sufijos de ventana."""
    try:
        g = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    except sqlite3.Error:
        return None, set()
    nombres = [r[0] for r in g.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for n in nombres:
        if n.upper() == tabla.upper() or n.upper().startswith(tabla.upper() + "_"):
            return n, {r[1] for r in g.execute("PRAGMA table_info([%s])" % n)}
    return None, set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabla")
    ap.add_argument("--where", default="")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--system", default="P01")
    ap.add_argument("--ancho", type=int, default=7, help="campos por lectura ademas del ancla")
    a = ap.parse_args()

    from rfc_helpers import get_connection
    conn = get_connection(a.system)
    campos = campos_de(conn, a.tabla)
    if not campos:
        print("  %s no existe o no tiene campos en DD03L" % a.tabla)
        return 2
    gold_name, gold_cols = en_el_golden(a.tabla)

    print("=" * 100)
    print("QUE CAMPOS USA DE VERDAD  ·  %s  ·  muestra de %d filas" % (a.tabla, a.n))
    print("=" * 100)
    print("  %d campos en %s · en el Golden: %s (%d columnas)"
          % (len(campos), a.system, gold_name or "NO ESTA", len(gold_cols)))
    if a.where:
        print("  escenario: %s" % a.where)

    # ANCLA: un campo que va en TODAS las lecturas para poder coser los trozos. Sin el, dos
    # lecturas pueden devolver las filas en otro orden y se mezclarian valores de filas
    # distintas -- un error que no daria ningun aviso.
    ancla = campos[0]
    filas = [{} for _ in range(a.n)]
    malos = []
    for i in range(0, len(campos), a.ancho):
        trozo = [ancla] + [c for c in campos[i:i + a.ancho] if c != ancla]
        try:
            d = conn.call("RFC_READ_TABLE", QUERY_TABLE=a.tabla, DELIMITER="|", ROWCOUNT=a.n,
                          OPTIONS=([{"TEXT": a.where}] if a.where else []),
                          FIELDS=[{"FIELDNAME": f} for f in trozo])
        except Exception as e:
            malos.append((trozo[1:], str(e).split("key=")[-1][:30]))
            continue
        for j, x in enumerate(d["DATA"][:a.n]):
            filas[j].update(dict(zip(trozo, [y.strip() for y in x["WA"].split("|")])))
    if malos:
        print("\n  NO SE PUDIERON LEER (se dice, no se callan):")
        for cs, err in malos[:6]:
            print("    %-46s %s" % (", ".join(cs)[:46], err))

    usados = sorted({k for f in filas for k, v in f.items() if v not in VACIOS})
    faltan = [k for k in usados if gold_cols and k not in gold_cols]
    print("\n  CON VALOR en al menos una fila: %d de %d campos" % (len(usados), len(campos)))
    print("  de esos, QUE EL GOLDEN NO TIENE: %d" % len(faltan))

    if faltan:
        print("\n  %-16s %s" % ("campo", "valores distintos en la muestra"))
        print("  " + "-" * 88)
        for k in faltan:
            vals = sorted({f.get(k, "") for f in filas if f.get(k, "") not in VACIOS})
            print("  %-16s %s" % (k, " · ".join(str(v)[:20] for v in vals[:4])))
        print("\n  Cada uno es un PASO DE EXTRACCION candidato. No los pidas todos: mira cual")
        print("  contesta la pregunta que tenias, que es para lo que se muestrea.")

    print("\n  LIMITE: un campo vacio en %d filas puede estar relleno en otras. Esto dice QUE SE"
          % a.n)
    print("  USA en este escenario, nunca que algo no se use.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
