#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
structured_address_readiness.py -- quien NO va a poder cobrar a partir del 14-11-2026.

QUE CONTESTA
------------
Desde el 14-11-2026 la direccion postal sin estructurar queda prohibida en los
ficheros ISO 20022, y <TwnNm> + <Ctry> son obligatorios en cuanto se emite un
<PstlAdr>. Este script recorre los pagos reales y devuelve, nominalmente y
ordenada por volumen, la lista de PROVEEDORES y EMPLEADOS cuya direccion no
soporta ese cambio -- con lo que le falta a cada uno y a quien hay que pedirselo.

LA REGLA QUE HACE QUE ESTO FUNCIONE: PARTIR POR DORIGIN
-------------------------------------------------------
Medido 2026-08-19 en REGUH P01: de 1.096.949 lineas de pago, el 35% son NOMINA
(DORIGIN='HR-PY'), y ahi el receptor es un **PERNR que NO EXISTE en LFA1**. Su
direccion no sale de LFA1/ADRC sino del infotipo HR, viajando dentro del propio
REGUH (ZSTRA/ZORT1/ZPSTL/ZLAND).

Una auditoria que mire solo LFA1+ADRC da esos 5.128 receptores por inexistentes y
concluye "99% sano". Es exactamente el error que se cometio antes de escribir
esto: los proveedores estaban al 100% con ciudad y la averia entera estaba en la
nomina -- 1.016 empleados sin ciudad, 804 de ellos cobrando todavia en 2026,
concentrados en oficinas de terreno (CM, BR, SN, IN, AF, ZW, TH, KE, ML, IQ).

Asi que el primer corte NO es el pais ni el proveedor: es el ORIGEN DEL PAGO, y
cada origen tiene su propia fuente de verdad y su propio dueno del arreglo.

  FI-AP     proveedores  -> LFA1.ADRNR -> ADRC   ... lo corrige Compras/Finanzas
  HR-PY     nomina       -> infotipo HR (via REGUH) ... lo corrige RR.HH. de terreno
  FI-AR     clientes     -> KNA1.ADRNR -> ADRC
  TR-CM-BT  tesoreria    -> lo que viaje en REGUH

QUE EVALUA
----------
Lo que se comprueba es lo que REALMENTE VIAJA al fichero (los campos Z* de REGUH),
porque es lo que el banco va a leer. Para los proveedores se cruza ademas con el
maestro (LFA1->ADRC), que es donde hay que ir a corregir: si el maestro esta bien
y REGUH mal, el problema es de derivacion, no de dato -- y se marca distinto.

  BLOQUEANTE  sin ciudad, o sin pais -> <TwnNm>/<Ctry> obligatorios: el pago cae
  SUCIO       ciudad con digitos o coma ('NEW YORK, NY 10017', 'WIEN A-1010'):
              hoy pasa como texto libre; estructurado produce un dato INCORRECTO,
              que es peor que uno ausente porque nadie lo detecta
  VIGILAR     sin codigo postal -> depende del rail; Citi exige las cinco etiquetas,
              SocGen se conforma con TwnNm+Ctry
  SIN CALLE   informativo: no bloquea, pero no es direccion estructurada completa

Y separa VIVOS (con pagos en el ejercicio en curso) de historicos: solo los vivos
son trabajo real.

USO
    python structured_address_readiness.py
    python structured_address_readiness.py --origin HR-PY --csv nomina.csv
    python structured_address_readiness.py --since 20260101 --top 50
    python structured_address_readiness.py --sys P01 --vivos-desde 20260101

Solo lectura. Ningun argumento esta cableado -- se parametriza todo por CLI.
"""

from __future__ import annotations

import argparse
import collections
import csv
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "mcp-backend-server-python"))

# <TwnNm> y <Ctry> son obligatorios en cuanto se emite <PstlAdr> (SocGen brochure
# 3.3.5.1 + guia citada por el validador). Sin ellos el pago no sale.
BLOCKING = ("ciudad", "pais")

# Una ciudad "sucia" lleva el resto de la direccion pegada. Al estructurar se
# emite tal cual en <TwnNm> y el banco recibe un dato falso con pinta de bueno.
DIRTY_CITY = re.compile(r"[\d,]")

# De donde sale la direccion de cada tipo de pago, y quien la corrige.
ORIGINS = {
    "FI-AP":    ("proveedor", "LFA1 -> ADRC",        "Compras / Finanzas"),
    "HR-PY":    ("empleado",  "infotipo HR (REGUH)", "RR.HH. de la oficina"),
    "FI-AR":    ("cliente",   "KNA1 -> ADRC",        "Finanzas"),
    "TR-CM-BT": ("tesoreria", "REGUH",               "Tesoreria"),
}

REGUH_F = ["LAUFD", "LAUFI", "ZBUKR", "LIFNR", "PERNR", "DORIGIN", "ZNME1",
           "ZSTRA", "ZORT1", "ZPSTL", "ZLAND", "ZBNKS", "ZBNKL"]


def read_table(conn, table, fields, where="", rowcount=0):
    kw = dict(QUERY_TABLE=table, DELIMITER="|",
              FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rowcount)
    if where:
        kw["OPTIONS"] = [{"TEXT": where}]     # ojo: max 72 chars por linea
    r = conn.call("RFC_READ_TABLE", **kw)
    return [dict(zip(fields, [c.strip() for c in d["WA"].split("|")]))
            for d in r["DATA"]]


def classify(street, city, postcode, country):
    """Los defectos de UNA direccion, mas severos primero."""
    out = []
    if not city:
        out.append(("BLOQUEANTE", "sin ciudad -- <TwnNm> es obligatorio"))
    elif DIRTY_CITY.search(city):
        out.append(("SUCIO", "ciudad con digitos o coma: %r" % city))
    if not country:
        out.append(("BLOQUEANTE", "sin pais -- <Ctry> es obligatorio"))
    if not postcode:
        out.append(("VIGILAR", "sin codigo postal -- depende del rail"))
    if not street:
        out.append(("SIN CALLE", "sin calle -- no bloquea, pero no es completa"))
    return out


def worst(defects):
    for lvl in ("BLOQUEANTE", "SUCIO", "VIGILAR", "SIN CALLE"):
        if any(d[0] == lvl for d in defects):
            return lvl
    return "OK"


def build(system, since, vivos_desde, origins):
    from rfc_helpers import get_connection
    c = get_connection(system)
    try:
        pagos = read_table(c, "REGUH", REGUH_F, "LAUFD >= '%s'" % since)
        # rail por corrida: REGUT es la tabla de medios (= lo que ve FDTA)
        medios = read_table(c, "REGUT", ["LAUFD", "LAUFI", "ZBUKR", "DTFOR"],
                            "LAUFD >= '%s'" % since)
        # maestro de proveedores, solo si se piden proveedores
        maestro = {}
        if "FI-AP" in origins:
            lfa1 = read_table(c, "LFA1", ["LIFNR", "ADRNR", "NAME1", "LAND1"])
            adrc = {x["ADDRNUMBER"]: x for x in read_table(
                c, "ADRC", ["ADDRNUMBER", "STREET", "CITY1", "POST_CODE1",
                            "REGION", "COUNTRY"])}
            for v in lfa1:
                a = adrc.get(v["ADRNR"]) if v["ADRNR"] not in ("", "0000000000") else None
                maestro[v["LIFNR"]] = (v, a)
    finally:
        c.close()

    rail = collections.defaultdict(set)
    for m in medios:
        rail[(m["LAUFD"], m["LAUFI"], m["ZBUKR"])].add(m["DTFOR"])

    who = {}
    for p in pagos:
        o = p["DORIGIN"]
        if o not in origins:
            continue
        key = (o, p["LIFNR"] or p["PERNR"])
        w = who.get(key)
        if w is None:
            w = who[key] = {"origen": o, "id": key[1], "nombre": p["ZNME1"],
                            "pais": p["ZLAND"], "pagos": 0, "ultimo": "",
                            "rails": set(), "banco": "",
                            "street": "", "city": "", "pc": "", "country": ""}
        w["pagos"] += 1
        if p["LAUFD"] > w["ultimo"]:
            # la direccion que vale es la del pago MAS RECIENTE, no la primera
            w["ultimo"] = p["LAUFD"]
            w["street"], w["city"] = p["ZSTRA"], p["ZORT1"]
            w["pc"], w["country"] = p["ZPSTL"], p["ZLAND"]
            w["nombre"], w["pais"] = p["ZNME1"], p["ZLAND"]
            w["banco"] = "%s/%s" % (p["ZBNKS"], p["ZBNKL"]) if p["ZBNKL"] else ""
        w["rails"] |= rail.get((p["LAUFD"], p["LAUFI"], p["ZBUKR"]), set())

    filas = []
    for w in who.values():
        d = classify(w["street"], w["city"], w["pc"], w["country"])
        tipo, fuente, dueno = ORIGINS.get(w["origen"], ("?", "?", "?"))
        # para proveedores: el arreglo va al MAESTRO, no al pago
        maestro_estado = ""
        if w["origen"] == "FI-AP":
            v, a = maestro.get(w["id"], (None, None))
            if v is None:
                maestro_estado = "NO EXISTE en LFA1"
            elif a is None:
                maestro_estado = "sin ficha de direccion (ADRNR vacio)"
            else:
                md = classify(a["STREET"], a["CITY1"], a["POST_CODE1"], a["COUNTRY"])
                maestro_estado = "maestro OK" if not md else \
                    "maestro: " + "; ".join(x[1] for x in md)
        filas.append({
            "severidad": worst(d), "tipo": tipo, "origen": w["origen"],
            "id": w["id"], "nombre": w["nombre"], "pais": w["pais"],
            "pagos": w["pagos"], "ultimo_pago": w["ultimo"],
            "vivo": "SI" if w["ultimo"] >= vivos_desde else "no",
            "rails": ",".join(sorted(x for x in w["rails"] if x)),
            "calle": w["street"], "ciudad": w["city"],
            "cod_postal": w["pc"], "pais_iso": w["country"],
            "banco": w["banco"], "defectos": " | ".join(x[1] for x in d),
            "fuente_del_dato": fuente, "lo_corrige": dueno,
            "estado_maestro": maestro_estado})
    return filas


def report(filas, top, csv_path, solo_vivos):
    orden = {"BLOQUEANTE": 0, "SUCIO": 1, "VIGILAR": 2, "SIN CALLE": 3, "OK": 4}
    if solo_vivos:
        filas = [f for f in filas if f["vivo"] == "SI"]
    filas.sort(key=lambda f: (orden[f["severidad"]], -f["pagos"]))

    print("=" * 100)
    print("PREPARACION PARA LA DIRECCION ESTRUCTURADA (obligatoria 14-11-2026)")
    print("=" * 100)
    print("\nPor origen de pago -- cada uno tiene su fuente y su dueno:\n")
    print("  %-9s %-11s %8s %11s %9s %8s %9s   %s"
          % ("ORIGEN", "TIPO", "recept.", "BLOQUEANTE", "SUCIO", "VIGILAR", "vivos", "lo corrige"))
    for o in sorted({f["origen"] for f in filas}):
        g = [f for f in filas if f["origen"] == o]
        b = sum(1 for f in g if f["severidad"] == "BLOQUEANTE")
        s = sum(1 for f in g if f["severidad"] == "SUCIO")
        v = sum(1 for f in g if f["severidad"] == "VIGILAR")
        vi = sum(1 for f in g if f["vivo"] == "SI" and f["severidad"] in ("BLOQUEANTE", "SUCIO"))
        tipo, _, dueno = ORIGINS.get(o, ("?", "?", "?"))
        print("  %-9s %-11s %8d %11d %9d %8d %9d   %s"
              % (o, tipo, len(g), b, s, v, vi, dueno))

    urg = [f for f in filas if f["severidad"] in ("BLOQUEANTE", "SUCIO")
           and f["vivo"] == "SI"]
    print("\nTRABAJO REAL: %d receptores vivos con defecto bloqueante o sucio "
          "(%d pagos en juego)" % (len(urg), sum(f["pagos"] for f in urg)))

    porpais = collections.Counter((f["origen"], f["pais"]) for f in urg)
    if porpais:
        print("\nDonde esta concentrado (origen / pais / receptores):")
        for (o, p), n in porpais.most_common(15):
            print("   %-9s %-4s %5d" % (o, p or "??", n))

    print("\nLos %d mas urgentes (por numero de pagos):" % min(top, len(urg)))
    print("  %-11s %-9s %-12s %-26s %-4s %6s  %s"
          % ("SEVERIDAD", "ORIGEN", "ID", "NOMBRE", "PAIS", "PAGOS", "QUE FALTA"))
    for f in urg[:top]:
        print("  %-11s %-9s %-12s %-26s %-4s %6d  %s"
              % (f["severidad"], f["origen"], f["id"], (f["nombre"] or "")[:26],
                 f["pais"] or "??", f["pagos"], f["defectos"][:60]))

    if csv_path:
        cols = ["severidad", "tipo", "origen", "id", "nombre", "pais", "pagos",
                "ultimo_pago", "vivo", "rails", "calle", "ciudad", "cod_postal",
                "pais_iso", "banco", "defectos", "fuente_del_dato", "lo_corrige",
                "estado_maestro"]
        with io.open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, delimiter=";")
            w.writeheader()
            for f in filas:
                w.writerow(f)
        print("\nCSV -> %s   (%d filas, ordenadas por severidad y volumen)"
              % (csv_path, len(filas)))
    return len(urg)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--sys", default="P01")
    ap.add_argument("--since", default="20240101", help="pagos desde (YYYYMMDD)")
    ap.add_argument("--vivos-desde", default="20260101",
                    help="a partir de que fecha se considera receptor VIVO")
    ap.add_argument("--origin", default="FI-AP,HR-PY,FI-AR,TR-CM-BT",
                    help="origenes a evaluar, separados por coma")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--csv")
    ap.add_argument("--solo-vivos", action="store_true",
                    help="excluir del informe y del CSV los receptores sin pagos "
                         "recientes (por defecto salen todos, marcados vivo=SI/no)")
    a = ap.parse_args()
    origins = {x.strip() for x in a.origin.split(",") if x.strip()}
    filas = build(a.sys, a.since, a.vivos_desde, origins)
    urgentes = report(filas, a.top, a.csv, solo_vivos=a.solo_vivos)
    # exit 1 = hay trabajo pendiente, para poder encadenarlo en un check recurrente
    return 1 if urgentes else 0


if __name__ == "__main__":
    sys.exit(main())
