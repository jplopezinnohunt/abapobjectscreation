# -*- coding: utf-8 -*-
"""Lectura EN VIVO de P01 de toda la configuracion que cuelga del NUMERO DE CUENTA
del banco casa NTB02 (UNES) — INC-000013624 / cuenta ASHI-EUR de Northern Trust.

SOLO LECTURA. Ninguna escritura, ningun transporte.
"""
import sys, os, json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection

SYS = sys.argv[1] if len(sys.argv) > 1 else "P01"
c = get_connection(SYS)
print("SID real:", c.sid_real)


def rd(tab, fields, where, n=500):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=[{"TEXT": w} for w in ([where] if isinstance(where, str) else where)],
               FIELDS=[{"FIELDNAME": f} for f in fields])
    out = []
    for x in r["DATA"]:
        parts = x["WA"].split("|")
        out.append(dict(zip(fields, parts)))
    return out


def show(title, rows, cols=None):
    print("\n==== %s ==== (%d filas)" % (title, len(rows)))
    if not rows:
        print("   (vacio)")
        return
    cols = cols or list(rows[0].keys())
    print(" | ".join(cols))
    for r in rows:
        print(" | ".join("[%s]" % r.get(cc, "") for cc in cols))


# ---------- 0. que campos tiene T012K de verdad ----------
f = rd("DD03L", ["FIELDNAME", "POSITION"], "TABNAME = 'T012K' AND AS4LOCAL = 'A'", 300)
names = sorted(x["FIELDNAME"].strip() for x in f)
print("\n==== T012K FIELDS ====")
print(" ".join(names))

# ---------- 1. cuentas del banco casa NTB02 ----------
t012k_f = ["BUKRS", "HBKID", "HKTID", "BANKN", "BNKN2", "WAERS", "HKONT",
           "REFZL", "VKONT", "BKONT"]
t012k_f = [x for x in t012k_f if x in names]
rows = rd("T012K", t012k_f, "BUKRS = 'UNES' AND HBKID = 'NTB02'")
show("T012K — cuentas de NTB02 en UNES", rows)

# la cuenta del caso
show("T012K — EUR01 (la del ticket)", [r for r in rows if r.get("HKTID", "").strip() == "EUR01"])

# ---------- 2. quien mas lleva UNO12EUR / UNO18EUR en BNKN2 ----------
if "BNKN2" in names:
    for val in ("UNO12EUR", "UNO18EUR"):
        show("T012K — cualquier cuenta con BNKN2 = %s" % val,
             rd("T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BNKN2"],
                "BNKN2 = '%s'" % val))

# ---------- 3. banco casa: clave de banco ----------
show("T012 — banco casa NTB02", rd("T012", ["BUKRS", "HBKID", "BANKS", "BANKL", "BNKN2" if "BNKN2" in names else "BUKRS"],
                                   "BUKRS = 'UNES' AND HBKID = 'NTB02'"))

# ---------- 4. IBAN ----------
try:
    show("TIBAN — IBANs de las cuentas NTB02", rd("TIBAN", ["BANKS", "BANKL", "BANKN", "IBAN"],
                                                  "BANKS = 'GB'", 500))
except Exception as e:
    print("TIBAN:", e)

json.dump({"t012k_ntb02": rows}, open(os.path.join(HERE, "ntb02_live_%s.json" % c.sid_real), "w"),
          indent=2, ensure_ascii=False)
print("\nOK")
