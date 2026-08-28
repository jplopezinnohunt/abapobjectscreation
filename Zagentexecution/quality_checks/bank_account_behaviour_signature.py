# -*- coding: utf-8 -*-
"""bank_account_behaviour_signature.py — clasificar una cuenta por lo que HACE, no por como
se llama.

El texto de la cuenta es una convencion humana: sirve para orientar y miente cuando alguien
no siguio la convencion. Lo que la cuenta HACE no miente. Tres ejes medidos sobre 2025-2026:

  PAGA      cuantos pagos salen por ella          (REGUH por banco casa + cuenta)
  RECIBE    cuantos extractos entran, y por que canal (FEBKO / EFART)
  SALDO     si mueve saldo y cuanto               (GLT0, movimiento por periodo)

De ahi salen tipos de comportamiento que NO dependen de que alguien escribiera bien el
nombre. Y la comparacion con la etiqueta que da el texto es en si un hallazgo: donde
comportamiento y nombre no coinciden, uno de los dos esta mal.

Solo LECTURA. P01, ventana 2025-2026 (fija: mas atras arrastra cuentas que ya no existen).
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",
    "needs": "rfc_p01",
    "what": "el tipo de comportamiento de cada cuenta bancaria medido en 2025-2026 (paga / "
            "recibe extracto / mueve saldo), independiente del texto con que alguien la nombro",
    "args": "[--bukrs <soc>] [--system P01] [--json <fichero>]",
}

import argparse
import collections
import datetime
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))

MARCAS_CIERRE = ("CLOSED", "CLOSE", "FERME", "CERRAD", "OBSOLET", "INACTIV",
                 "NOT USED", "DORMANT", "CANCEL")
ANIOS = ("2025", "2026")


def _y(*c):
    return " AND ".join(x for x in c if x)


def cerrada(t):
    return any(m in (t or "").upper() for m in MARCAS_CIERRE)


def rd(conn, tab, fields, where="", n=0):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
                  OPTIONS=([{"TEXT": where}] if where else []),
                  FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, [c.strip() for c in x["WA"].split("|")])) for x in r["DATA"]]


def num(s):
    s = (s or "0").replace(",", "").strip()
    if s.endswith("-"):
        s = "-" + s[:-1]
    try:
        return float(s)
    except ValueError:
        return 0.0


def tipo(paga, extractos, canal, periodos_con_mov, saldo_abs):
    """La decision, pura. Se prueba sin SAP delante.

    El orden importa: PAGAR es el hecho mas fuerte (esta en la configuracion del programa de
    pagos Y deja rastro), luego recibir, luego mover saldo. Una cuenta que no hace ninguna
    de las tres no es 'rara': es DURMIENTE, y eso ya es una respuesta.
    """
    if paga > 0:
        return "PAGADORA"
    if extractos > 0 and periodos_con_mov >= 6:
        return "OPERATIVA_COBRO"          # entra dinero y se mueve todos los meses
    if extractos > 0 and periodos_con_mov > 0:
        return "BAJA_ROTACION"            # recibe extracto pero se mueve poco
    if extractos > 0:
        return "EXTRACTO_SIN_MOVIMIENTO"  # llega extracto y el mayor no se mueve
    if periodos_con_mov > 0:
        return "MUEVE_SIN_EXTRACTO"       # se contabiliza a mano, sin extracto que lo respalde
    if saldo_abs > 0:
        return "INMOVIL_CON_SALDO"        # tiene dinero parado y no pasa nada
    return "DURMIENTE"


def autotest():
    casos = [
        ((5, 300, "ELECTRONICO", 18, 1e6), "PAGADORA"),
        ((0, 400, "ELECTRONICO", 20, 1e6), "OPERATIVA_COBRO"),
        ((0, 40, "MANUAL", 3, 1e5), "BAJA_ROTACION"),
        ((0, 10, "ELECTRONICO", 0, 1e5), "EXTRACTO_SIN_MOVIMIENTO"),
        ((0, 0, "SIN_EXTRACTO", 12, 1e6), "MUEVE_SIN_EXTRACTO"),
        ((0, 0, "SIN_EXTRACTO", 0, 5e5), "INMOVIL_CON_SALDO"),
        ((0, 0, "SIN_EXTRACTO", 0, 0), "DURMIENTE"),
    ]
    for args, esp in casos:
        got = tipo(*args)
        assert got == esp, "%s -> %s, esperado %s" % (args, got, esp)
    print("AUTOTEST OK — 7 casos, incluido el que NO debe clasificarse como raro (DURMIENTE)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="UNES")
    ap.add_argument("--system", default="P01")
    ap.add_argument("--json", default="")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()

    from rfc_helpers import get_connection
    conn = get_connection(a.system)
    print("SID real: %s" % conn.sid_real)
    w = ("BUKRS = '%s'" % a.bukrs) if a.bukrs else ""

    t012k = rd(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "WAERS", "HKONT"], w)
    txt = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r["TEXT1"] for r in
           rd(conn, "T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"], _y(w, "SPRAS = 'E'"))}
    leaf = rd(conn, "SETLEAF", ["SETNAME", "VALFROM"], "SETNAME LIKE 'YBANK%'")
    gl2set = collections.defaultdict(set)
    for r in leaf:
        gl2set[r["VALFROM"].lstrip("0")].add(r["SETNAME"])

    # --- PAGA: REGUH, los pagos que salieron por esa cuenta ------------------
    pagos = collections.Counter()
    for yr in ANIOS:
        try:
            for r in rd(conn, "REGUH", ["ZBUKR", "HBKID", "HKTID", "LAUFD"],
                        _y("ZBUKR = '%s'" % a.bukrs if a.bukrs else "",
                           "LAUFD LIKE '%s%%'" % yr)):
                pagos[(r["ZBUKR"], r["HBKID"], r["HKTID"])] += 1
        except Exception as e:
            print("  REGUH %s -> %s" % (yr, str(e)[:80]))

    # --- RECIBE: extractos --------------------------------------------------
    hoy = datetime.datetime.now().strftime("%Y%m%d")
    can = collections.defaultdict(collections.Counter)
    for r in rd(conn, "FEBKO", ["BUKRS", "HBKID", "HKTID", "AZDAT", "EFART"],
                _y(w, "AZDAT >= '20250101'")):
        if r["AZDAT"] <= hoy:
            can[(r["BUKRS"], r["HBKID"], r["HKTID"])][r["EFART"]] += 1

    # --- SALDO: GLT0, movimiento por periodo --------------------------------
    # 16 columnas de importe no caben en una lectura (buffer de 512): se leen por trozos y
    # se juntan por la CLAVE, nunca por posicion.
    mov = collections.defaultdict(float)
    per = collections.defaultdict(int)
    CH = [["HSL%02d" % i for i in range(1, 6)],
          ["HSL%02d" % i for i in range(6, 11)],
          ["HSL%02d" % i for i in range(11, 17)]]
    for yr in ANIOS:
        for ch in CH:
            try:
                rows = rd(conn, "GLT0", ["RACCT", "RYEAR", "DRCRK"] + ch,
                          "BUKRS = '%s' AND RYEAR = '%s' AND RACCT LIKE '00010%%'"
                          % (a.bukrs, yr))
            except Exception as e:
                print("  GLT0 %s %s -> %s" % (yr, ch[0], str(e)[:70]))
                continue
            for r in rows:
                k = r["RACCT"]
                for c in ch:
                    v = abs(num(r.get(c)))
                    if v > 0.005:
                        mov[k] += v
                        per[k] += 1

    filas = []
    for r in t012k:
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        t = txt.get(k, "")
        if cerrada(t):
            continue
        cc = can.get(k)
        ext = sum(cc.values()) if cc else 0
        canal = ("SIN_EXTRACTO" if not cc
                 else "ELECTRONICO" if cc.get("E") and not cc.get("M")
                 else "MANUAL" if cc.get("M") and not cc.get("E") else "MIXTO")
        gl = r["HKONT"]
        s = ",".join(sorted(gl2set.get(gl.lstrip("0"), set())))
        zona = ("FO" if "_FO_" in s else "SIGHT" if "_SIGHT" in s
                else "HQ" if "_HQ_" in s else "(sin set)")
        filas.append({
            "cuenta": "%s/%s-%s" % k, "texto": t, "waers": r["WAERS"], "gl": gl, "zona": zona,
            "pagos": pagos.get(k, 0), "extractos": ext, "canal": canal,
            "periodos_mov": per.get(gl, 0), "movimiento": round(mov.get(gl, 0.0), 2),
            "tipo": tipo(pagos.get(k, 0), ext, canal, per.get(gl, 0), mov.get(gl, 0.0)),
        })

    print("\ncuentas VIVAS: %d · ventana 2025-2026" % len(filas))
    print("\n" + "=" * 96)
    print("TIPO DE COMPORTAMIENTO  x  ZONA (YBANK)")
    print("=" * 96)
    zonas = ["HQ", "FO", "SIGHT", "(sin set)"]
    print("  %-26s %6s %6s %6s %10s  %s" % ("tipo", *zonas, "total"))
    for tp in sorted({f["tipo"] for f in filas}):
        g = [f for f in filas if f["tipo"] == tp]
        c = collections.Counter(f["zona"] for f in g)
        print("  %-26s %6d %6d %6d %10d  %d"
              % (tp, c.get("HQ", 0), c.get("FO", 0), c.get("SIGHT", 0), c.get("(sin set)", 0), len(g)))

    print("\n" + "=" * 96)
    print("LO QUE PIDE EXPLICACION — comportamientos que no deberian existir")
    print("=" * 96)
    for tp in ("EXTRACTO_SIN_MOVIMIENTO", "MUEVE_SIN_EXTRACTO", "INMOVIL_CON_SALDO", "DURMIENTE"):
        g = [f for f in filas if f["tipo"] == tp]
        if not g:
            continue
        print("\n  --- %s : %d ---" % (tp, len(g)))
        for f in sorted(g, key=lambda x: -abs(x["movimiento"]))[:14]:
            print("     %-22s %-4s zona=%-9s ext=%-5d pagos=%-5d per=%-3d %s"
                  % (f["cuenta"], f["waers"], f["zona"], f["extractos"], f["pagos"],
                     f["periodos_mov"], (f["texto"] or "")[:34]))

    if a.json:
        json.dump(filas, open(a.json, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("\nescrito %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
