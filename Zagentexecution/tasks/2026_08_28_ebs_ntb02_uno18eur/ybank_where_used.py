# -*- coding: utf-8 -*-
"""¿DONDE se usa el set YBANK? No donde se dice que se usa: donde se puede MEDIR.

El doc del dominio afirma que lo usan GS02 (saldos medios), los informes Report Painter
ZCASH/ZCASHFO/ZCASHFODET y "los informes de tesoreria". Eso esta DECLARADO, no medido.
Y ya se ha visto hoy que una afirmacion sobre YBANK puede llevar meses escrita y ser falsa.

Tres sitios donde puede aparecer el uso, y los tres se comprueban:
  1. CODIGO ABAP  -- corpus extraido: 0 (solo un falso positivo, MYBANKDETAILS)
  2. DEFINICIONES de Report Painter / Report Writer -- las tablas T80* y GRW*
  3. VARIANTES de programas -- un set puede entrar como valor de un select-option

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


# ---- 1. ¿que TABLAS pueden guardar el nombre de un set? ---------------------
print("\n==== 1. tablas cuyo campo es un NOMBRE DE SET (por elemento de datos) ====")
tabs = collections.defaultdict(list)
for dt in ("SETNR", "SETID", "SETNAME", "RSETNR", "SETNAMENEW", "GSETNR", "SETNAME_NEW"):
    try:
        for r in rd("DD03L", ["TABNAME", "FIELDNAME", "ROLLNAME"],
                    "ROLLNAME = '%s' AND AS4LOCAL = 'A'" % dt, 0):
            t = r["TABNAME"]
            if t.startswith(("/", "CI_", "DD", "*")) or len(t) > 16:
                continue
            tabs[t].append((r["FIELDNAME"], dt))
    except Exception as e:
        print("   %s -> %s" % (dt, str(e)[:70]))
print("   candidatas: %d" % len(tabs))

# quedarse con las que existen como transparentes y tienen datos
reales = []
for t in sorted(tabs):
    try:
        cl = rd("DD02L", ["TABNAME", "TABCLASS"], "TABNAME = '%s' AND AS4LOCAL = 'A'" % t, 3)
        if cl and cl[0]["TABCLASS"] == "TRANSP":
            reales.append(t)
    except Exception:
        pass
print("   transparentes: %d -> %s" % (len(reales), reales[:40]))

# ---- 2. ¿cual contiene realmente un YBANK? ---------------------------------
print("\n==== 2. ¿cual de ellas contiene un set YBANK_* ? ====")
encontrado = []
for t in reales:
    for fld, dt in tabs[t]:
        try:
            rows = rd(t, [fld], "%s LIKE '%%YBANK_ACCOUNTS%%'" % fld, 50)
        except Exception:
            continue
        if rows:
            print("   >>> %-16s campo %-14s -> %d filas" % (t, fld, len(rows)))
            encontrado.append((t, fld))

if not encontrado:
    print("   NINGUNA. Ninguna tabla con un campo de tipo 'nombre de set' referencia YBANK.")

# ---- 3. Report Painter / Writer: las tablas T80* --------------------------
print("\n==== 3. definiciones de Report Painter / Writer (T80*) ====")
for t in ("T803J", "T803K", "T801A", "T800A", "T804F", "T803T", "T802G", "T803G"):
    try:
        fl = [x["FIELDNAME"] for x in rd("DD03L", ["FIELDNAME"],
                                         "TABNAME = '%s' AND AS4LOCAL = 'A'" % t, 100)]
        fl = [f for f in fl if not f.startswith(".") and f != "MANDT"][:5]
        n = len(rd(t, fl[:1], "", 0)) if fl else 0
        print("   %-8s campos=%-42s filas=%d" % (t, str(fl)[:42], n))
    except Exception as e:
        print("   %-8s -> %s" % (t, str(e)[:60]))

# ---- 4. informes ZCASH: ¿existen? -----------------------------------------
print("\n==== 4. los informes que el doc dice que lo usan ====")
for w in ("REPORT LIKE 'ZCASH%'", "REPORT LIKE 'YCASH%'"):
    try:
        rows = rd("VARID", ["REPORT", "VARIANT"], w, 50)
        print("   VARID %-26s -> %d" % (w, len(rows)))
        for r in rows[:10]:
            print("      ", r)
    except Exception as e:
        print("   VARID %-26s -> %s" % (w, str(e)[:60]))
for w in ("TCODE LIKE 'ZCASH%'", "TCODE = 'TRM5'", "TCODE = 'GS02'"):
    try:
        rows = rd("TSTC", ["TCODE", "PGMNA"], w, 20)
        print("   TSTC  %-26s -> %s" % (w, rows or "0"))
    except Exception as e:
        print("   TSTC  %-26s -> %s" % (w, str(e)[:60]))

print("\nOK")
