# -*- coding: utf-8 -*-
"""¿Separa el BALANCE lo que YBANK no separa?

YBANK clasifica por geografia x divisa y no distingue una cartera gestionada de una cuenta
corriente. Pero la version de balance (FSV, FAGL_011ZC) asigna cuentas a POSICIONES por
intervalos de numero de cuenta -- y una posicion de balance SI es una afirmacion sobre la
NATURALEZA de lo que hay ahi (efectivo vs inversion). Si el balance las separa, la
clasificacion existe y es mejor que cualquiera que inventemos.

Se compara la posicion de balance de:
  * las 4 cuentas de MANDATO   (PIMCO, JP Morgan, RAMP, IMIP)  -- no reciben extracto
  * las 4 de EFECTIVO del MISMO custodio (Nessim Habif, Cash Pool, ASHI USD, ASHI EUR)
  * las operativas de referencia (SOG01-EUR01, CIT04-USD04)

Si todas caen en la MISMA posicion, el balance tampoco separa. Si caen en posiciones
distintas, ahi esta el modelo.

Version de balance: la que la sociedad EJECUTA de verdad (FS10 para UNES), no T011.

SOLO LECTURA.
"""
import sys, os, collections

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection

c = get_connection("P01")
print("SID real:", c.sid_real)


def rd(tab, fields, where="", n=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=([{"TEXT": where}] if where else []),
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, [x.strip() for x in y["WA"].split("|")])) for y in r["DATA"]]


VERS = ["FS10", "FS11"]

# --- 1. intervalos del FSV ----------------------------------------------------
zc = []
for v in VERS:
    try:
        zc += rd("FAGL_011ZC", ["VERSN", "ERGSL", "VONKT", "BISKT"], "VERSN = '%s'" % v, 0)
    except Exception as e:
        print("FAGL_011ZC %s -> %s" % (v, str(e)[:80]))
print("intervalos leidos: %d" % len(zc))

# textos de las posiciones
txt = {}
for v in VERS:
    try:
        for r in rd("FAGL_011QT", ["VERSN", "ERGSL", "SPRAS", "TXT45"],
                    "VERSN = '%s' AND SPRAS = 'E'" % v, 0):
            txt[(r["VERSN"], r["ERGSL"])] = r["TXT45"]
    except Exception as e:
        print("FAGL_011QT %s -> %s" % (v, str(e)[:80]))
print("textos de posicion: %d" % len(txt))


def posicion(gl, versn):
    g = gl.zfill(10)
    hits = [r for r in zc if r["VERSN"] == versn
            and r["VONKT"].zfill(10) <= g <= r["BISKT"].zfill(10)]
    if not hits:
        return ("(sin posicion)", "")
    h = min(hits, key=lambda r: int(r["BISKT"].zfill(10)) - int(r["VONKT"].zfill(10)))
    return (h["ERGSL"], txt.get((versn, h["ERGSL"]), ""))


# --- 2. las cuentas a comparar ------------------------------------------------
t012k = rd("T012K", ["BUKRS", "HBKID", "HKTID", "HKONT"], "BUKRS = 'UNES'")
tx = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r["TEXT1"] for r in
      rd("T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"], "BUKRS = 'UNES' AND SPRAS = 'E'")}

GRUPOS = {
    "MANDATO (no reciben extracto)": [("NTB01", "USD04"), ("NTB01", "USD05"),
                                      ("NTB01", "USD06"), ("NTB02", "EUR02")],
    "EFECTIVO del MISMO custodio":   [("NTB01", "USD01"), ("NTB01", "USD02"),
                                      ("NTB01", "USD03"), ("NTB02", "EUR01")],
    "OPERATIVA de referencia":       [("SOG01", "EUR01"), ("SOG01", "USDD1"),
                                      ("CIT04", "USD04")],
    "A LA VISTA / AHORRO (_SIGHT)":  [("SOG03", "EURD1"), ("BNP01", "EURD1"),
                                      ("SCB14", "USDD1")],
}
gl = {(r["HBKID"], r["HKTID"]): r["HKONT"] for r in t012k}

for etiqueta, lst in GRUPOS.items():
    print("\n==== %s ====" % etiqueta)
    for hb, hk in lst:
        g = gl.get((hb, hk))
        if not g:
            print("   %-14s (no existe)" % ("%s-%s" % (hb, hk)))
            continue
        p10, t10 = posicion(g, "FS10")
        print("   %-14s GL=%-10s  FS10 pos=%-8s %-34s  %s"
              % ("%s-%s" % (hb, hk), g, p10, t10[:34],
                 (tx.get(("UNES", hb, hk), "") or "")[:34]))

# --- 3. ¿cuantas posiciones distintas cubren TODAS las cuentas de banco? ------
print("\n==== reparto: todas las cuentas de banco de UNES por posicion FS10 ====")
agg = collections.Counter()
for r in t012k:
    if not r["HKONT"]:
        continue
    p, t = posicion(r["HKONT"], "FS10")
    agg[(p, t[:44])] += 1
for k, v in sorted(agg.items(), key=lambda x: -x[1]):
    print("   %-8s %-46s %d" % (k[0], k[1], v))
print("\nOK")
