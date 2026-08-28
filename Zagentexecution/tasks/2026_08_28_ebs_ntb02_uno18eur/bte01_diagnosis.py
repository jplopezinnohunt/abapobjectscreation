# -*- coding: utf-8 -*-
"""BTE01 (UNESCO TEHERAN) — el segundo cable roto. La configuracion EXACTA que falta.

Ojo: aqui NO se puede copiar el razonamiento de NTB02 sin mirar. NTB02 tenia UNA fila en
T028B y una cuenta; BTE01 tiene DOS filas de T028B con numeros que no casan, asi que hay
que averiguar a que cuenta pertenece cada una antes de proponer nada. Una de ellas puede
ser de otra cuenta del mismo banco, no un huerfano.

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
               OPTIONS=([{"TEXT": w} for w in ([where] if isinstance(where, str) and where else [])]),
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, [x.strip() for x in y["WA"].split("|")])) for y in r["DATA"]]


def show(t, rows, cols=None):
    print("\n==== %s ==== (%d)" % (t, len(rows)))
    if not rows:
        print("   (vacio)")
        return
    for r in rows:
        print("   " + " | ".join("%s=%s" % (k, v) for k, v in r.items()))


# 1. el banco casa y su clave
show("T012 — banco casa BTE01",
     rd("T012", ["BUKRS", "HBKID", "BANKS", "BANKL"], "BUKRS = 'UNES' AND HBKID = 'BTE01'"))

# 2. TODAS sus cuentas
t012k = rd("T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BNKN2", "WAERS", "HKONT"],
           "BUKRS = 'UNES' AND HBKID = 'BTE01'")
show("T012K — cuentas de BTE01", t012k)

# 3. textos (¿viva o cerrada?)
show("T012T — textos (ingles)",
     rd("T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"],
        "BUKRS = 'UNES' AND HBKID = 'BTE01' AND SPRAS = 'E'"))

# 4. T028B de esa clave de banco — ¿a que cuenta apunta cada fila?
t028b = rd("T028B", ["BANKL", "KTONR", "VGTYP", "BNKKO", "BUKRS", "WORKLIST", "NOCLEAR"],
           "BANKL = 'IR000029'")
show("T028B — filas de la clave de banco IR000029", t028b)

vivos = {r["BANKN"]: r["HKTID"] for r in t012k}
print("\n   --- cruce fila a fila ---")
for r in t028b:
    dueno = vivos.get(r["KTONR"])
    print("   KTONR=%-14s BNKKO=%-12s -> %s" %
          (r["KTONR"], r["BNKKO"],
           ("cuenta VIVA %s" % dueno) if dueno else "NINGUNA cuenta viva tiene este numero"))
for r in t012k:
    tiene = any(x["KTONR"] == r["BANKN"] for x in t028b)
    print("   cuenta %-6s BANKN=%-14s -> %s" %
          (r["HKTID"], r["BANKN"], "tiene fila T028B" if tiene else ">>> SIN FILA T028B <<<"))

# 5. T035D / T035U
show("T035D — clave corta -> cuenta de mayor",
     rd("T035D", ["BUKRS", "DISKB", "BNKKO"], "DISKB LIKE 'BTE01%'"))
show("T035U — texto de la clave corta",
     rd("T035U", ["SPRAS", "BUKRS", "DISKB", "TEXTL"], "DISKB LIKE 'BTE01%' AND SPRAS = 'E'"))

# 6. historial de extractos
feb = rd("FEBKO", ["BUKRS", "HBKID", "HKTID", "KTONR", "ABSND", "AZDAT", "AZNUM", "EFART"],
         "BUKRS = 'UNES' AND HBKID = 'BTE01'")
print("\n==== FEBKO — extractos de BTE01: %d ====" % len(feb))
agg = collections.Counter()
last = {}
for r in feb:
    k = (r["HKTID"], r["KTONR"], r["ABSND"], r["EFART"])
    agg[k] += 1
    if r["AZDAT"] > last.get(k, ""):
        last[k] = r["AZDAT"]
for k, n in agg.most_common():
    print("   HKTID=%-6s KTONR=%-14s ABSND=[%s] EFART=%s  n=%-5d ultimo=%s"
          % (k[0], k[1], k[2], k[3], n, last[k]))

recientes = sorted([r for r in feb if r["AZDAT"] >= "20260101"], key=lambda x: x["AZDAT"])
print("\n   ultimos 10 extractos de 2026:")
for r in recientes[-10:]:
    print("      %s AZNUM=%s HKTID=%s KTONR=%s" % (r["AZDAT"], r["AZNUM"], r["HKTID"], r["KTONR"]))

# 7. ¿cuando cambio el numero? pista: TIBAN
show("TIBAN — IBANs de la clave de banco IR000029",
     rd("TIBAN", ["BANKS", "BANKL", "BANKN", "IBAN", "VALID_FROM"], "BANKL = 'IR000029'"))

print("\nOK")
