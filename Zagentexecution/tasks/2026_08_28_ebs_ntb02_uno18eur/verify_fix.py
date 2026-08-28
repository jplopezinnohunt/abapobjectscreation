# -*- coding: utf-8 -*-
"""Verificacion POSTERIOR al cambio: ¿que hay ahora en T028B, en D01 y en P01?

Se lee el DESTINO, no lo que dice la pantalla. Una captura prueba que se tecleo; solo la
lectura prueba que quedo grabado (y en que sistema).

SOLO LECTURA.
"""
import sys, os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection

for sistema in ("D01", "P01"):
    print("\n" + "=" * 64)
    try:
        c = get_connection(sistema)
    except Exception as e:
        print("%s -> no se pudo conectar: %s" % (sistema, str(e)[:110]))
        continue
    print("SISTEMA %s (SID real: %s)" % (sistema, c.sid_real))

    def rd(tab, fields, where="", n=0):
        r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
                   OPTIONS=([{"TEXT": where}] if where else []),
                   FIELDS=[{"FIELDNAME": f} for f in fields])
        return [dict(zip(fields, [x.strip() for x in y["WA"].split("|")])) for y in r["DATA"]]

    try:
        rows = rd("T028B", ["BANKL", "KTONR", "VGTYP", "BNKKO", "BUKRS", "WORKLIST", "NOCLEAR"],
                  "BANKL = 'SP0000000MX7'", 0)
        print("  T028B para SP0000000MX7: %d filas" % len(rows))
        for r in rows:
            marca = ""
            if r["KTONR"] == "18747647":
                marca = "  <-- NUEVA, correcta"
            elif r["KTONR"] == "11939389":
                marca = "  <-- vieja, todavia presente"
            print("     " + " | ".join("%s=%s" % (k, v) for k, v in r.items()) + marca)
        if not any(r["KTONR"] == "18747647" for r in rows):
            print("     >>> la cuenta NUEVA todavia NO esta en %s" % c.sid_real)
    except Exception as e:
        print("  T028B -> ERROR %s" % str(e)[:110])

    try:
        rows = rd("T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BNKN2"],
                  "BUKRS = 'UNES' AND HBKID = 'NTB02'", 0)
        print("  T012K NTB02:")
        for r in rows:
            print("     " + " | ".join("%s=%s" % (k, v) for k, v in r.items()))
    except Exception as e:
        print("  T012K -> ERROR %s" % str(e)[:110])

print("\nOK")
