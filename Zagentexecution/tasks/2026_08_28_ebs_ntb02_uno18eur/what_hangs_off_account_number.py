# -*- coding: utf-8 -*-
"""¿QUE se rompe, ademas de T012K, cuando cambia el numero de cuenta de un banco casa?

No se contesta de memoria. Se contesta preguntandole al diccionario: que tablas tienen un
campo cuyo ELEMENTO DE DATOS es un numero de cuenta bancaria, y de esas, cuales contienen
todavia el numero VIEJO de la cuenta del ticket.

Dos poblaciones distintas y hay que separarlas:
  * CONFIGURACION (delivery class C/G/E) -> hay que mantenerla a mano. Es la que rompe.
  * TRANSACCIONAL (A) -> es historia. No se toca, y encontrar el numero viejo ahi es
    NORMAL: son los extractos y documentos de antes del cambio.

SOLO LECTURA.
"""
import sys, os, collections

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection

VIEJA = "11939389"
NUEVA = "18747647"

c = get_connection("P01")
print("SID real: %s" % c.sid_real)


def rd(tab, fields, where="", n=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=([{"TEXT": where}] if where else []),
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, [x.strip() for x in y["WA"].split("|")])) for y in r["DATA"]]


# --- 1. elementos de datos que SON un numero de cuenta bancaria ---------------
# BANKN es el estandar; KTONR lo usan las tablas del extracto; BNKN2 la cuenta alternativa.
DTEL = ["BANKN", "BANKN_LONG", "KTONR", "BNKN2", "BANKN_EBS", "UKONT", "BNKACCOUNT_EXT"]
print("\n==== 1. tablas con un campo cuyo elemento de datos es un numero de cuenta ====")
tablas = collections.defaultdict(list)
for dt in DTEL:
    try:
        for r in rd("DD03L", ["TABNAME", "FIELDNAME", "ROLLNAME"],
                    "ROLLNAME = '%s' AND AS4LOCAL = 'A'" % dt, 0):
            t = r["TABNAME"]
            if t.startswith(("/", "CI_", "DD", "*")) or len(t) > 16:
                continue
            tablas[t].append((r["FIELDNAME"], dt))
    except Exception as e:
        print("   %s -> %s" % (dt, str(e)[:70]))
print("   tablas candidatas: %d" % len(tablas))

# --- 2. separarlas por clase de entrega: config vs transaccional --------------
print("\n==== 2. clase de entrega (C/G/E = configuracion · A = transaccional) ====")
clase = {}
for t in sorted(tablas):
    try:
        r = rd("DD02L", ["TABNAME", "TABCLASS", "CONTFLAG"], "TABNAME = '%s' AND AS4LOCAL = 'A'" % t, 5)
        if r:
            clase[t] = (r[0]["TABCLASS"], r[0]["CONTFLAG"])
    except Exception:
        pass

conf = {t: v for t, v in clase.items() if v[0] == "TRANSP" and v[1] in ("C", "G", "E", "S")}
tran = {t: v for t, v in clase.items() if v[0] == "TRANSP" and v[1] not in ("C", "G", "E", "S")}
print("   CONFIGURACION: %d  ->  %s" % (len(conf), sorted(conf)))
print("   TRANSACCIONAL: %d  ->  %s" % (len(tran), sorted(tran)))

# --- 3. ¿cual contiene todavia el numero VIEJO? -------------------------------
print("\n==== 3. ¿donde vive todavia el numero VIEJO %s? ====" % VIEJA)
for grupo, nombre in ((conf, "CONFIGURACION"), (tran, "TRANSACCIONAL")):
    print("\n   --- %s ---" % nombre)
    for t in sorted(grupo):
        for fld, dt in tablas[t]:
            for val, et in ((VIEJA, "VIEJA"), (NUEVA, "NUEVA")):
                try:
                    rows = rd(t, [fld], "%s LIKE '%%%s%%'" % (fld, val), 20)
                except Exception:
                    continue
                if rows:
                    print("      %-18s %-16s %-6s -> %d filas" % (t, fld, et, len(rows)))

print("\nOK")
