# -*- coding: utf-8 -*-
"""derive_keys_from_dd03l.py — la CLAVE de cada tabla, sacada del diccionario de SAP.

EL HUECO QUE CIERRA (JP, 2026-08-29)
    «Mas que el no detectar el borrado es detectar el DELTA tambien.»

    Tenia razon y era el problema mayor. Las 368 tablas del Golden tenian MODELO declarado
    -- marca de agua, clave creciente, comparar por clave... -- pero `gold_delta.py` solo podia
    EJECUTAR 12, porque la clave estaba escrita A MANO en un diccionario. 356 tablas con plan y
    sin forma de correrlo. Un modelo sin clave no es un modelo: es una intencion.

POR QUE NO HABIA QUE INVENTARLA
    La clave la DECLARA SAP en `DD03L` con `KEYFLAG = 'X'`. Es autoritativa, esta en produccion
    y se lee en una llamada. Escribirla a mano para 368 tablas garantiza dos cosas: que nunca
    se termina, y que alguna quede mal -- y una clave mal puesta NO da error, APILA duplicados.

LO QUE SI HAY QUE VIGILAR, Y POR ESO ESTO NO ES UN VOLCADO CIEGO
    1. `MANDT`/`CLIENT` es parte de la clave en SAP y NO esta en nuestras copias: se quita.
    2. Nuestra copia puede tener MENOS columnas que la tabla real. Si falta un campo de la
       clave, la tabla NO queda ejecutable -- y se dice cual falta, en vez de dejar una clave
       incompleta que apilaria.
    3. Una tabla del Golden puede no existir en P01 (derivadas, simulaciones, historicos
       nuestros). Tambien se declara.

Solo LECTURA. Escribe unicamente en brain_v2/gold_delta_registry.json.
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "brain_v2/gold_delta_registry.json",
    "needs": "rfc_p01",
    "what": "deriva de DD03L la clave de cada tabla del Golden para que su delta sea EJECUTABLE",
    "args": "[--solo <TABLA>]",
}

import argparse
import json
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
REG = os.path.join(REPO, "brain_v2", "gold_delta_registry.json")
CLIENTE = {"MANDT", "CLIENT", "RCLNT"}


def sap_name(gold):
    """El nombre en SAP de una tabla del Golden. Nuestras copias llevan sufijos de ventana
    (_2024_2026), minusculas, o nombres propios de derivadas."""
    n = gold.upper()
    for suf in ("_2024_2026", "_HISTORY", "_FULL", "_P01", "_SCENARIOS", "_USD"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", default="")
    a = ap.parse_args()

    from rfc_helpers import get_connection, trocear_where
    with open(REG, encoding="utf-8") as fh:
        doc = json.load(fh)
    reg = doc["tablas"]
    g = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    conn = get_connection("P01")

    objetivos = [a.solo] if a.solo else sorted(reg)
    ok = falta_col = no_existe = 0
    for gold in objetivos:
        cols = {r[1] for r in g.execute("PRAGMA table_info([%s])" % gold)}
        if not cols:
            continue
        sap = sap_name(gold)
        try:
            r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD03L", DELIMITER="|", ROWCOUNT=0,
                          OPTIONS=trocear_where("TABNAME = '%s' AND KEYFLAG = 'X'" % sap),
                          FIELDS=[{"FIELDNAME": "FIELDNAME"}, {"FIELDNAME": "POSITION"}])
        except Exception as e:
            reg[gold]["clave"] = None
            reg[gold]["clave_nota"] = "DD03L fallo: %s" % str(e).split("key=")[-1][:40]
            no_existe += 1
            continue
        pares = sorted((x["WA"].split("|")[1].strip(), x["WA"].split("|")[0].strip())
                       for x in r["DATA"])
        clave = [f for _, f in pares if f not in CLIENTE]
        if not clave:
            reg[gold]["clave"] = None
            reg[gold]["clave_nota"] = ("%s no existe en P01 o no tiene clave: es una tabla "
                                       "nuestra (derivada, simulacion o historico)" % sap)
            no_existe += 1
            continue
        faltan = [c for c in clave if c not in cols]
        reg[gold]["sap"] = sap
        reg[gold]["clave"] = clave
        if faltan:
            reg[gold]["ejecutable"] = False
            reg[gold]["clave_nota"] = ("NO ejecutable: al Golden le faltan campos de la clave "
                                       "(%s). Una clave incompleta no da error, APILA"
                                       % ", ".join(faltan))
            falta_col += 1
        else:
            reg[gold]["ejecutable"] = True
            reg[gold]["clave_nota"] = "clave de DD03L (KEYFLAG=X), sin el campo de mandante"
            ok += 1

    doc["_clave"] = ("derivada de DD03L KEYFLAG='X' el 2026-08-29. NO se escribe a mano: 368 "
                     "tablas a mano no se terminan nunca, y una clave mal puesta no da error, "
                     "apila duplicados.")
    with open(REG, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)

    print("=" * 88)
    print("CLAVES DERIVADAS DEL DICCIONARIO DE SAP")
    print("=" * 88)
    print("  EJECUTABLES ahora            : %d" % ok)
    print("  con la clave INCOMPLETA      : %d  (al Golden le faltan campos)" % falta_col)
    print("  sin clave en P01             : %d  (derivadas, simulaciones, historicos nuestros)"
          % no_existe)
    print("\n  Antes eran 12 ejecutables de 368, con la clave escrita a mano.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
