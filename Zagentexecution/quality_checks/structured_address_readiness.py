#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
structured_address_readiness.py -- quien NO va a poder cobrar desde el 14-11-2026.

Recorre los pagos reales y devuelve, nominalmente y ordenada por volumen, la lista
de proveedores y empleados cuya direccion no soporta la direccion estructurada
obligatoria -- con lo que le falta a cada uno y a quien hay que pedirselo.

LOS TRES CORTES, EN ESTE ORDEN. OMITIR UNO INVENTA UN PROBLEMA O ESCONDE OTRO.
------------------------------------------------------------------------------
Los tres se aprendieron fallando, el mismo dia (2026-08-19), y cada uno costo una
conclusion equivocada entregada al usuario:

1. DORIGIN -- QUIEN cobra, porque cada origen tiene su fuente de verdad.
   El 35% de las lineas de pago son NOMINA, y ahi el receptor es un PERNR que NO
   EXISTE en LFA1: su direccion viene del infotipo HR y viaja dentro del propio
   REGUH. Una auditoria que mire solo LFA1+ADRC da esos 5.128 receptores por
   inexistentes y dictamina "99% sano".

2. T042Z -- POR DONDE sale el pago. FORMI = va en un fichero ISO. XSCHK = cheque.
   Sin este corte se reporto como GRAVE que 943 empleados no podrian cobrar en
   noviembre. Cobran por CHEQUE (metodos O y U), y un cheque no lleva <PstlAdr>.
   Cero de ellos estaban en alcance. El incidente entero era inexistente.
   OJO: T042Z es POR PAIS. El mismo ZLSCH puede ser cheque en un pais y fichero
   en otro; hay que acotar al pais de la sociedad pagadora o el corte se cruza.

3. RAIL -- CONTRA QUE REGLA se mide, porque los bancos no piden lo mismo.
   Citi exige CtrySubDvsn ("both fields are mandatory" en su Linea 2); SocGen no.
   Filtrando por el rail CITI se reportaron 941 proveedores afectados. Sin
   filtrar son 8.149: el numero real era nueve veces mayor.

QUE EVALUA
----------
Lo que REALMENTE VIAJA al fichero (los campos Z* de REGUH), porque es lo que el
banco lee. Para proveedores se cruza ademas el maestro (LFA1->ADRC), que es donde
hay que ir a corregir: si el maestro esta bien y el pago mal, el problema es de
derivacion y no de dato -- y se marca distinto.

  BLOQUEANTE  sin ciudad o sin pais -> <TwnNm>/<Ctry> obligatorios: el pago cae
  REGION      sin CtrySubDvsn Y pagado por un rail que lo exige (Citi)
  SUCIO       ciudad con digitos o coma ('NEW YORK, NY 10017', 'WIEN A-1010'):
              hoy pasa como texto libre; estructurado produce un dato INCORRECTO,
              que es peor que uno ausente porque nadie lo detecta
  COMODIN     codigo postal de relleno (99999, Z9Z 9Z9, 00000). NO derivar nada
              de el: un 99999 en una direccion de New York cae en el rango de
              Alaska y cargaria un estado falso con total confianza
  VIGILAR     sin codigo postal -- "strongly recommended", no obligatorio
  SIN CALLE   informativo

MEDIR CONTRA LA NORMA, NO CONTRA EL HISTORICO
---------------------------------------------
Que hoy el banco lo acepte no es evidencia: la regla no esta en vigor. Todo lo
que sale de aqui se juzga contra el texto publicado.
(regla feedback_grace_period_acceptance_is_not_evidence)

USO
    python structured_address_readiness.py
    python structured_address_readiness.py --origin HR-PY --csv nomina.csv
    python structured_address_readiness.py --incluir-no-fichero   # ver tambien cheques
    python structured_address_readiness.py --rail /CITI/XML/UNESCO/DC_V3_01
    python structured_address_readiness.py --pais-sociedad FR --top 50

Solo lectura. Sin ROWSKIPS (P01 lo rechaza).
"""
from __future__ import annotations

# El bloque va aqui, y no pegado al docstring, por una regla del LENGUAJE y no de estilo:
# `from __future__` tiene que ser la primera sentencia del modulo o el fichero no compila
# (probado: SyntaxError "from __future__ imports must occur at the beginning of the file").
# `run_all.declaration()` lo lee por AST recorriendo todo el cuerpo del modulo, asi que la
# posicion no le afecta.
QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",  # datos_sap | conocimiento | herramientas
    "needs": "rfc_p01",    # gold_db | rfc_p01 | files
    "what": ("receptores cuyo dato no soporta la direccion estructurada obligatoria del "
             "14-11-2026, con los tres cortes aplicados (DORIGIN = quien cobra, "
             "T042Z = fichero o cheque, rail = contra que regla se mide)"),
    "args": ("[--sys P01] [--since YYYYMMDD] [--vivos-desde YYYYMMDD] "
             "[--origin FI-AP,HR-PY,FI-AR,TR-CM-BT] [--pais-sociedad FR] "
             "[--rail <FORMATO>] [--incluir-no-fichero] [--top N] [--csv <f>]"),
    # POR QUE `live` Y NO `gate`: no puede correr sin SAP. `build()` (l.238) abre una
    # sesion RFC (l.239) y lee REGUH, REGUT, T042Z y, para proveedores, LFA1 + ADRC.
    # Poblacion entera desde --since, sin ROWSKIPS.
    #
    # SI TIENE VEREDICTO, y el exit no significa "roto": main() devuelve 1 cuando hay
    # receptores VIVOS, EN ALCANCE y con defecto accionable (l.426-427). Es una cola de
    # trabajo con fecha limite, no un fallo del sistema. Leer un exit 1 de aqui como
    # "check roto" es el error contrario al que este script existe para evitar.
    #
    # LO QUE SI SE PUEDE VERIFICAR SIN SAP son sus funciones puras, y esta hecho:
    # test_structured_address_readiness.py cubre receptor_key, es_placeholder, classify
    # y worst con los errores reales del 2026-08-19 (26 OK / 0 fallos, corrido 2026-08-26).
    # Ese test es la red de seguridad de este fichero; si se toca classify() o el
    # detector de codigos postales comodin, correrlo antes de creer nada.
}

import argparse
import collections
import csv
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "mcp-backend-server-python"))

# <TwnNm> y <Ctry> son obligatorios en cuanto se emite <PstlAdr>.
# Sin ellos el pago cae, en cualquier rail.
BLOCKING = ("ciudad", "pais")

# Una ciudad "sucia" lleva el resto de la direccion pegada. Al estructurar se
# emite tal cual en <TwnNm> y el banco recibe un dato falso con pinta de bueno.
DIRTY_CITY = re.compile(r"[\d,]")

# Codigos postales de relleno. Detectarlos es OBLIGATORIO antes de derivar nada
# de ellos: '99999' en una direccion de New York cae en el rango de Alaska y
# cargaria un estado falso con total confianza.
#
# Se normaliza QUITANDO separadores antes de comparar. La primera version anclaba
# el patron al final de la cadena y por eso NO reconocia '99999-9999' ni
# 'Z9Z 9Z9', que son justo las dos formas que mas aparecen -- 64 de los 68 casos
# reales. Lo caso el test de abajo, no una lectura del codigo.
_PC_PLACEHOLDERS = (
    re.compile(r"^0+$"),          # 00000, 0000000
    re.compile(r"^9{4,}$"),       # 99999, 999999999
    re.compile(r"^Z9Z9Z9$"),      # comodin canadiense
    re.compile(r"^X+$"),
    re.compile(r"^1234\d*$"),
)


def es_placeholder(pc):
    """True si el codigo postal es relleno y no se puede derivar nada de el."""
    if not pc:
        return False
    n = re.sub(r"[\s\-./]", "", pc).upper()
    return any(p.match(n) for p in _PC_PLACEHOLDERS)

# Rails que exigen CtrySubDvsn. Citi lo documenta "both fields are mandatory"
# (reglas GOLD 2026-05-06, hoja 499_US_WIRE, Target Address Line 2 =
# TwnNm + coma + CtrySubDvsn). SocGen solo lo llama "strongly recommended".
RAILS_EXIGEN_REGION = {"/CITI/XML/UNESCO/DC_V3_01"}

# Paises donde el estado/provincia ES parte de la direccion, no un adorno.
REGION_ES_ESENCIAL = {"US", "CA"}

# De donde sale la direccion de cada tipo de pago, y quien la corrige.
ORIGINS = {
    "FI-AP":    ("proveedor", "LFA1 -> ADRC",        "Compras / Finanzas"),
    "HR-PY":    ("empleado",  "infotipo HR (REGUH)", "RR.HH. de la oficina"),
    "FI-AR":    ("cliente",   "KNA1 -> ADRC",        "Finanzas"),
    "TR-CM-BT": ("tesoreria", "REGUH",               "Tesoreria"),
}

REGUH_F = ["LAUFD", "LAUFI", "ZBUKR", "LIFNR", "PERNR", "DORIGIN", "RZAWE", "ZNME1",
           "ZSTRA", "ZORT1", "ZPSTL", "ZREGI", "ZLAND", "ZBNKS", "ZBNKL"]

# Los tres cortes de arriba no son un comentario: estan aplicados en build().
# Implementa feedback_declare_the_cuts_before_measuring.


def read_table(conn, table, fields, where="", rowcount=0):
    kw = dict(QUERY_TABLE=table, DELIMITER="|",
              FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rowcount)
    if where:
        kw["OPTIONS"] = [{"TEXT": where}]     # max 72 chars por linea
    r = conn.call("RFC_READ_TABLE", **kw)
    return [dict(zip(fields, [c.strip() for c in d["WA"].split("|")]))
            for d in r["DATA"]]


def receptor_key(p):
    """La clave del receptor NO es la misma en todos los origenes.

    En nomina es el PERNR; en proveedores el LIFNR. Usar `PERNR or LIFNR` sin
    mirar el origen colapso 8.894 proveedores en 1, porque en FI-AP el PERNR
    viene relleno de ceros y es un string no vacio.
    """
    return p["PERNR"] if p["DORIGIN"] == "HR-PY" else p["LIFNR"]


def canales(conn, pais_sociedad):
    """Clasifica cada metodo de pago: va en fichero ISO, es cheque, u otra cosa.

    ACOTADO POR PAIS: T042Z es por pais y el mismo ZLSCH puede ser cheque en uno
    y fichero en otro. Sin acotar, los conjuntos se solapan y la clasificacion
    da totales mayores que la poblacion.
    """
    rows = read_table(conn, "T042Z", ["LAND1", "ZLSCH", "XSCHK", "FORMI"],
                      "LAND1 = '%s'" % pais_sociedad)
    fichero, cheque = {}, set()
    for x in rows:
        if x["FORMI"]:
            fichero.setdefault(x["ZLSCH"], set()).add(x["FORMI"])
        if x["XSCHK"] == "X":
            cheque.add(x["ZLSCH"])
    solapan = set(fichero) & cheque
    return fichero, cheque, solapan


def classify(street, city, postcode, country, region, exige_region, pais):
    """Los defectos de UNA direccion, mas severos primero."""
    out = []
    if not city:
        out.append(("BLOQUEANTE", "sin ciudad -- <TwnNm> es obligatorio"))
    elif DIRTY_CITY.search(city):
        out.append(("SUCIO", "ciudad con digitos o coma: %r" % city))
    if not country:
        out.append(("BLOQUEANTE", "sin pais -- <Ctry> es obligatorio"))
    if not region and exige_region:
        esencial = " (y en %s el estado ES parte de la direccion)" % pais \
            if pais in REGION_ES_ESENCIAL else ""
        out.append(("REGION", "sin <CtrySubDvsn> y el rail lo exige%s" % esencial))
    if es_placeholder(postcode):
        out.append(("COMODIN", "codigo postal de relleno %r -- NO derivar la "
                               "region de el" % postcode))
    elif not postcode:
        out.append(("VIGILAR", "sin codigo postal -- no obligatorio, "
                               "'strongly recommended'"))
    if not street:
        out.append(("SIN CALLE", "sin calle -- no bloquea, pero no es completa"))
    return out


ORDEN = ["BLOQUEANTE", "REGION", "SUCIO", "COMODIN", "VIGILAR", "SIN CALLE"]


def worst(defects):
    for lvl in ORDEN:
        if any(d[0] == lvl for d in defects):
            return lvl
    return "OK"


def build(system, since, vivos_desde, origins, pais_sociedad, rail_filtro):
    from rfc_helpers import get_connection
    c = get_connection(system)
    try:
        pagos = read_table(c, "REGUH", REGUH_F, "LAUFD >= '%s'" % since)
        medios = read_table(c, "REGUT", ["LAUFD", "LAUFI", "ZBUKR", "DTFOR"],
                            "LAUFD >= '%s'" % since)
        fichero, cheque, solapan = canales(c, pais_sociedad)
        maestro = {}
        if "FI-AP" in origins:
            lfa1 = read_table(c, "LFA1", ["LIFNR", "ADRNR", "NAME1", "LAND1", "REGIO"])
            adrc = {x["ADDRNUMBER"]: x for x in read_table(
                c, "ADRC", ["ADDRNUMBER", "STREET", "CITY1", "POST_CODE1",
                            "REGION", "COUNTRY"])}
            for v in lfa1:
                a = adrc.get(v["ADRNR"]) if v["ADRNR"] not in ("", "0000000000") else None
                maestro[v["LIFNR"]] = (v, a)
    finally:
        c.close()

    if solapan:
        print("!! AVISO: en %s hay metodos que son cheque Y fichero a la vez: %s. "
              "La clasificacion por canal no es fiable." % (pais_sociedad, sorted(solapan)))

    rail_corrida = collections.defaultdict(set)
    for m in medios:
        rail_corrida[(m["LAUFD"], m["LAUFI"], m["ZBUKR"])].add(m["DTFOR"])

    who = {}
    for p in pagos:
        o = p["DORIGIN"]
        if o not in origins:
            continue
        # CORTE 2 -- el canal. Un cheque no lleva <PstlAdr>: no esta en alcance.
        rails_metodo = fichero.get(p["RZAWE"], set())
        if rails_metodo:
            canal = "fichero"
        elif p["RZAWE"] in cheque:
            canal = "cheque"
        else:
            canal = "otro"
        # CORTE 3 -- el rail. De la corrida si se pudo atribuir; si no, del metodo.
        rails = rail_corrida.get((p["LAUFD"], p["LAUFI"], p["ZBUKR"])) or rails_metodo
        if rail_filtro and rail_filtro not in rails:
            continue
        key = (o, receptor_key(p))
        w = who.get(key)
        if w is None:
            w = who[key] = {"origen": o, "id": key[1], "nombre": p["ZNME1"],
                            "pais": p["ZLAND"], "pagos": 0, "ultimo": "",
                            "rails": set(), "canales": set(), "banco": "",
                            "street": "", "city": "", "pc": "", "country": "",
                            "region": ""}
        w["pagos"] += 1
        w["canales"].add(canal)
        w["rails"] |= {x for x in rails if x}
        if p["LAUFD"] > w["ultimo"]:
            # la direccion que vale es la del pago MAS RECIENTE: es la que viajaria
            w["ultimo"] = p["LAUFD"]
            w["street"], w["city"] = p["ZSTRA"], p["ZORT1"]
            w["pc"], w["country"] = p["ZPSTL"], p["ZLAND"]
            w["region"], w["nombre"], w["pais"] = p["ZREGI"], p["ZNME1"], p["ZLAND"]
            w["banco"] = "%s/%s" % (p["ZBNKS"], p["ZBNKL"]) if p["ZBNKL"] else ""

    filas = []
    for w in who.values():
        en_fichero = "fichero" in w["canales"]
        exige_region = bool(w["rails"] & RAILS_EXIGEN_REGION)
        d = classify(w["street"], w["city"], w["pc"], w["country"], w["region"],
                     exige_region, w["pais"])
        tipo, fuente, dueno = ORIGINS.get(w["origen"], ("?", "?", "?"))
        maestro_estado = ""
        if w["origen"] == "FI-AP":
            v, a = maestro.get(w["id"], (None, None))
            if v is None:
                maestro_estado = "NO EXISTE en LFA1"
            elif a is None:
                maestro_estado = "sin ficha de direccion (ADRNR vacio)"
            else:
                md = classify(a["STREET"], a["CITY1"], a["POST_CODE1"], a["COUNTRY"],
                              a["REGION"], exige_region, a["COUNTRY"])
                maestro_estado = "maestro OK" if not md else \
                    "maestro: " + "; ".join(x[1] for x in md)
        filas.append({
            "severidad": worst(d) if en_fichero else "FUERA DE ALCANCE",
            "en_fichero_ISO": "SI" if en_fichero else "no",
            "canal": ",".join(sorted(w["canales"])),
            "tipo": tipo, "origen": w["origen"], "id": w["id"], "nombre": w["nombre"],
            "pais": w["pais"], "pagos": w["pagos"], "ultimo_pago": w["ultimo"],
            "vivo": "SI" if w["ultimo"] >= vivos_desde else "no",
            "rails": ",".join(sorted(w["rails"])),
            "rail_exige_region": "SI" if exige_region else "no",
            "calle": w["street"], "ciudad": w["city"], "cod_postal": w["pc"],
            "region": w["region"], "pais_iso": w["country"], "banco": w["banco"],
            "defectos": " | ".join(x[1] for x in d),
            "fuente_del_dato": fuente, "lo_corrige": dueno,
            "estado_maestro": maestro_estado})
    return filas


def report(filas, top, csv_path, incluir_no_fichero):
    rk = {k: i for i, k in enumerate(ORDEN)}
    rk["OK"] = 90
    rk["FUERA DE ALCANCE"] = 99
    filas.sort(key=lambda f: (rk[f["severidad"]], -f["pagos"]))

    print("=" * 100)
    print("PREPARACION PARA LA DIRECCION ESTRUCTURADA (obligatoria 14-11-2026)")
    print("=" * 100)

    print("\nCORTE 1 y 2 -- por ORIGEN del pago y por CANAL:\n")
    print("  %-9s %-11s %9s %11s %9s   %s"
          % ("ORIGEN", "TIPO", "recept.", "EN FICHERO", "fuera", "lo corrige"))
    for o in sorted({f["origen"] for f in filas}):
        g = [f for f in filas if f["origen"] == o]
        enf = [f for f in g if f["en_fichero_ISO"] == "SI"]
        tipo, _, dueno = ORIGINS.get(o, ("?", "?", "?"))
        print("  %-9s %-11s %9d %11d %9d   %s"
              % (o, tipo, len(g), len(enf), len(g) - len(enf), dueno))
    print("\n  Los de 'fuera' cobran por cheque u otro canal: un cheque no lleva")
    print("  <PstlAdr>, luego no estan en alcance de la norma.")

    alcance = [f for f in filas if f["en_fichero_ISO"] == "SI"]
    if not incluir_no_fichero:
        filas = alcance

    print("\nCORTE 3 -- por RAIL (que regla aplica a cada uno):\n")
    porrail = collections.Counter(r for f in alcance for r in f["rails"].split(",") if r)
    for r, n in porrail.most_common():
        marca = "  <- exige CtrySubDvsn" if r in RAILS_EXIGEN_REGION else ""
        print("  %-38s %6d receptores%s" % (r, n, marca))

    print("\nHALLAZGOS sobre los %d receptores EN ALCANCE:\n" % len(alcance))
    sev = collections.Counter(f["severidad"] for f in alcance)
    for k in ORDEN + ["OK"]:
        if sev.get(k):
            print("  %-14s %6d receptores  %7d pagos"
                  % (k, sev[k], sum(f["pagos"] for f in alcance if f["severidad"] == k)))

    urg = [f for f in alcance
           if f["severidad"] in ("BLOQUEANTE", "REGION", "SUCIO") and f["vivo"] == "SI"]
    print("\nTRABAJO REAL: %d receptores vivos, en alcance, con defecto accionable "
          "(%d pagos)" % (len(urg), sum(f["pagos"] for f in urg)))

    porpais = collections.Counter((f["origen"], f["pais"]) for f in urg)
    if porpais:
        print("\nDonde esta concentrado (origen / pais / receptores):")
        for (o, p), n in porpais.most_common(15):
            print("   %-9s %-4s %5d" % (o, p or "??", n))

    print("\nLos %d mas urgentes:" % min(top, len(urg)))
    print("  %-11s %-9s %-12s %-24s %-4s %6s  %s"
          % ("SEVERIDAD", "ORIGEN", "ID", "NOMBRE", "PAIS", "PAGOS", "QUE FALTA"))
    for f in urg[:top]:
        print("  %-11s %-9s %-12s %-24s %-4s %6d  %s"
              % (f["severidad"], f["origen"], f["id"], (f["nombre"] or "")[:24],
                 f["pais"] or "??", f["pagos"], f["defectos"][:58]))

    if csv_path:
        cols = list(filas[0].keys()) if filas else []
        with io.open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, delimiter=";")
            w.writeheader()
            for f in filas:
                w.writerow(f)
        print("\nCSV -> %s   (%d filas)" % (csv_path, len(filas)))
    return len(urg)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--sys", default="P01")
    ap.add_argument("--since", default="20240101", help="pagos desde (YYYYMMDD)")
    ap.add_argument("--vivos-desde", default="20260101",
                    help="a partir de que fecha se considera receptor VIVO")
    ap.add_argument("--origin", default="FI-AP,HR-PY,FI-AR,TR-CM-BT",
                    help="origenes a evaluar, separados por coma")
    ap.add_argument("--pais-sociedad", default="FR",
                    help="pais de la sociedad pagadora -- acota T042Z, que es por pais")
    ap.add_argument("--rail", help="evaluar solo un formato")
    ap.add_argument("--incluir-no-fichero", action="store_true",
                    help="incluir tambien los que cobran por cheque u otro canal, "
                         "marcados FUERA DE ALCANCE (por defecto se excluyen)")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--csv")
    a = ap.parse_args()
    origins = {x.strip() for x in a.origin.split(",") if x.strip()}
    filas = build(a.sys, a.since, a.vivos_desde, origins, a.pais_sociedad, a.rail)
    urgentes = report(filas, a.top, a.csv, a.incluir_no_fichero)
    return 1 if urgentes else 0


if __name__ == "__main__":
    sys.exit(main())
