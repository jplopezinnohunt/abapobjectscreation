# -*- coding: utf-8 -*-
"""CONFIRMACION: ¿que tablas de configuracion siguen apuntando a la cuenta VIEJA?

T028B (OT43 — asignar cuentas bancarias a tipos de operacion) tiene por CLAVE el
numero de cuenta tal como llega en el fichero: BANKL + KTONR. Al cambiar el numero
en FI12, esa fila se queda huerfana y el extracto ya no se puede asignar.

Se comprueba contra la cuenta que SI funciona (NTB01) — el control.

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


def rd(tab, fields, where, n=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=[{"TEXT": w} for w in ([where] if isinstance(where, str) else where)],
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, x["WA"].split("|"))) for x in r["DATA"]]


print("\n==== T028B — TODAS las filas del banco de NTB02 (BANKL = SP0000000MX7) ====")
for r in rd("T028B", ["BANKL", "KTONR", "VGTYP", "BNKKO", "BUKRS", "WORKLIST", "NOCLEAR"],
            "BANKL = 'SP0000000MX7'", 0):
    print("   " + " | ".join(v.strip() for v in r.values()))

print("\n==== T028B — ¿existe ya la cuenta NUEVA 18747647? ====")
n = rd("T028B", ["BANKL", "KTONR", "VGTYP", "BNKKO", "BUKRS"], "KTONR LIKE '%18747647%'", 0)
print("   filas: %d" % len(n))
for r in n:
    print("   " + " | ".join(v.strip() for v in r.values()))

print("\n==== T028B — CONTROL: el banco de NTB01, que SI sigue entrando ====")
for r in rd("T028B", ["BANKL", "KTONR", "VGTYP", "BNKKO", "BUKRS"], "BANKL = 'SP0000000MXL'", 0):
    print("   " + " | ".join(v.strip() for v in r.values()))

print("\n==== T035D — clave corta (DISKB) -> cuenta de mayor, para NTB0* ====")
try:
    fl = ["BUKRS", "DISKB", "BNKKO", "HBKID", "HKTID"]
    rows = rd("T035D", fl, "DISKB LIKE 'NTB%'", 0)
except Exception:
    fl = ["BUKRS", "DISKB", "BNKKO"]
    rows = rd("T035D", fl, "DISKB LIKE 'NTB%'", 0)
print("   campos: %s — filas: %d" % (fl, len(rows)))
for r in rows:
    print("   " + " | ".join(v.strip() for v in r.values()))

print("\n==== ¿queda la cadena 11939389 en otras tablas de config? ====")
for tab, fld, flds in (("T028B", "KTONR", ["BANKL", "KTONR", "BNKKO", "BUKRS"]),
                       ("T012K", "BANKN", ["BUKRS", "HBKID", "HKTID", "BANKN"]),
                       ("TIBAN", "BANKN", ["BANKS", "BANKL", "BANKN", "IBAN"]),
                       ("T042I", "BANKN", ["ZBUKR", "HBKID", "HKTID"]),
                       ("BNKA", "BNKLZ", ["BANKS", "BANKL", "BANKA"])):
    try:
        rows = rd(tab, flds, "%s LIKE '%%11939389%%'" % fld, 0)
        print("   %-8s %-6s -> %d filas" % (tab, fld, len(rows)))
        for r in rows:
            print("        " + " | ".join(v.strip() for v in r.values()))
    except Exception as e:
        print("   %-8s %-6s -> ERROR %s" % (tab, fld, str(e)[:70]))

print("\nOK")
