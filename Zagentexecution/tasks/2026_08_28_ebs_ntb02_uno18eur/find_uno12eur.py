# -*- coding: utf-8 -*-
"""¿DONDE vive todavia 'UNO12EUR' en P01?

FEBKO.KTONR = 11939389, no UNO12EUR. Asi que la cadena que Ingrid ve en FF67 sale de
otro campo. Este script la BUSCA en vez de suponerla: vuelca una cabecera FEBKO entera
del extracto que ella tiene delante (AZNUM 02997, 14.08.2026) y barre los candidatos.

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


def fields_of(tab):
    return sorted(x["FIELDNAME"].strip() for x in
                  rd("DD03L", ["FIELDNAME"], "TABNAME = '%s' AND AS4LOCAL = 'A'" % tab, 500))


# ---- 1. cabecera FEBKO completa del extracto 02997 (el ultimo, 14.08.2026) ----
fn = [f for f in fields_of("FEBKO") if not f.startswith(".")]
where = "BUKRS = 'UNES' AND HBKID = 'NTB02' AND AZNUM = '02997'"
print("\n==== FEBKO — cabecera COMPLETA del extracto 02997 (14.08.2026) ====")
got = {}
for i in range(0, len(fn), 8):
    chunk = fn[i:i + 8]
    try:
        rows = rd("FEBKO", chunk, where, 5)
        if rows:
            got.update(rows[0])
    except Exception as e:
        print("  (chunk %s fallo: %s)" % (chunk, str(e)[:80]))
for k in sorted(got):
    v = got[k].strip()
    if v:
        print("  %-14s = %s" % (k, v))

print("\n  >>> campos que contienen 'UNO': %s"
      % [k for k, v in got.items() if "UNO" in v.upper()])

# ---- 2. ¿hay FEBKO con KTONR tipo UNO*? --------------------------------------
for pat in ("UNO12EUR", "UNO18EUR", "UNO12%", "UNO18%"):
    op = "=" if "%" not in pat else "LIKE"
    try:
        rows = rd("FEBKO", ["BUKRS", "HBKID", "HKTID", "KTONR", "AZDAT", "AZNUM"],
                  "KTONR %s '%s'" % (op, pat), 50)
        print("\nFEBKO KTONR %s '%s' -> %d filas" % (op, pat, len(rows)))
        for r in rows[:10]:
            print("   ", " | ".join(v.strip() for v in r.values()))
    except Exception as e:
        print("\nFEBKO KTONR %s '%s' -> ERROR %s" % (op, pat, str(e)[:90]))

# ---- 3. IBAN vigente de las cuentas NTB02 ------------------------------------
print("\n==== TIBAN — IBAN de las cuentas de NTB02 ====")
for acct in ("11939389", "18747647", "17846293"):
    try:
        rows = rd("TIBAN", ["BANKS", "BANKL", "BANKN", "IBAN", "VALID_FROM"],
                  "BANKN = '%-18s'" % acct, 20)
    except Exception:
        rows = rd("TIBAN", ["BANKS", "BANKL", "BANKN", "IBAN"], "BANKN LIKE '%s%%'" % acct, 20)
    print("  cuenta %s -> %d filas" % (acct, len(rows)))
    for r in rows:
        print("     ", " | ".join(v.strip() for v in r.values()))

print("\nOK")
