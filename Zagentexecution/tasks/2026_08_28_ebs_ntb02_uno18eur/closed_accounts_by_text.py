# -*- coding: utf-8 -*-
"""Las cuentas cerradas se marcan EN EL TEXTO. Vamos a verlo.

Si es cierto, el texto de la cuenta es el discriminador que separa "canal roto" (hay que
arreglarlo) de "cuenta cerrada" (no hay nada que arreglar) — y sin el, la puerta llena de
rojo permanente y esconde el caso vivo.

SOLO LECTURA.
"""
import sys, os

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


print("\n==== campos de T012T ====")
fl = [x["FIELDNAME"] for x in rd("DD03L", ["FIELDNAME"], "TABNAME = 'T012T' AND AS4LOCAL = 'A'", 100)]
print("  ", fl)

use = [f for f in ["BUKRS", "HBKID", "HKTID", "SPRAS", "TEXT1"] if f in fl]
rows = rd("T012T", use, "SPRAS = 'E'", 0)
print("\n  textos en ingles: %d" % len(rows))

# las cuentas que el barrido dio por mudas / rotas
SOSPECHOSAS = [
    ("UNES", "NTB02", "EUR01"), ("UNES", "BPO01", "USD01"), ("UNES", "BTE01", "USD01"),
    ("UNES", "SCB01", "USD01"), ("UNES", "BMN01", "EUR01"), ("UNES", "BMN01", "CUP02"),
    ("UNES", "CAB02", "JOD01"), ("UNES", "CIT03", "USD02"), ("UNES", "CIT03", "RUB02"),
    ("UNES", "SOG06", "HTG01"), ("UNES", "SOG06", "USD01"), ("UNES", "ECO08", "ZWG01"),
    ("UNES", "BAE01", "CLP01"), ("UNES", "BAE01", "USD01"), ("UNES", "CBE01", "ETB03"),
    ("UNES", "BST01", "USD01"), ("UNES", "BST01", "MZM01"), ("UNES", "SCB03", "XAF01"),
]
idx = {}
for r in rows:
    idx[(r.get("BUKRS", ""), r.get("HBKID", ""), r.get("HKTID", ""))] = r.get("TEXT1", "")

print("\n==== texto de las cuentas que el barrido marco ====")
for k in SOSPECHOSAS:
    t = idx.get(k, "(sin texto / clave distinta)")
    print("   %-6s %-6s %-6s : %s" % (k[0], k[1], k[2], t))

MARCAS = ["CLOSED", "CLOSE", "FERME", "FERMÉ", "CERRAD", "OLD", "OBSOLET", "INACTIV",
          "NOT USED", "NO USE", "DO NOT", "CANCEL", "DORMANT", "BLOCK"]
print("\n==== TODAS las cuentas de UNES cuyo texto lleva marca de cierre ====")
n = 0
for r in rows:
    t = r.get("TEXT1", "").upper()
    if r.get("BUKRS") == "UNES" and any(m in t for m in MARCAS):
        n += 1
        print("   %-6s %-6s : %s" % (r.get("HBKID"), r.get("HKTID"), r.get("TEXT1")))
print("   total: %d" % n)
