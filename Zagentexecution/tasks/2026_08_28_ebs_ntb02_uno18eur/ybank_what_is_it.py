# -*- coding: utf-8 -*-
"""¿QUE es YBANK exactamente, y DONDE se mantiene?

Se ha usado como "la lista maestra de cuentas bancarias" sin que nadie dijera nunca que
clase de objeto es, quien lo toca, ni si viaja por transporte. Eso decide si se puede
extender con un nodo de naturaleza y como.

SOLO LECTURA.
"""
import sys, os, collections

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection


def rd(c, tab, fields, where="", n=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=([{"TEXT": where}] if where else []),
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, [x.strip() for x in y["WA"].split("|")])) for y in r["DATA"]]


for sistema in ("P01", "D01"):
    print("\n" + "=" * 72)
    try:
        c = get_connection(sistema)
    except Exception as e:
        print("%s: no conecta (%s)" % (sistema, str(e)[:80]))
        continue
    print("SISTEMA %s" % c.sid_real)

    # --- SETHEADER: que clase de conjunto es -------------------------------
    try:
        fl = [x["FIELDNAME"] for x in rd(c, "DD03L", ["FIELDNAME"],
                                         "TABNAME = 'SETHEADER' AND AS4LOCAL = 'A'", 100)]
        use = [f for f in ["SETCLASS", "SETNAME", "SUBCLASS", "SETTYPE", "TABNAME", "FIELDNAME"]
               if f in fl][:6]
        rows = rd(c, "SETHEADER", use, "SETNAME LIKE 'YBANK%'")
        print("\n  SETHEADER (%s): %d" % (use, len(rows)))
        for r in rows:
            print("    " + " | ".join("%s=%s" % (k, v) for k, v in r.items()))
    except Exception as e:
        print("  SETHEADER -> %s" % str(e)[:100])

    # --- SETHEADERT: descripcion -------------------------------------------
    try:
        for r in rd(c, "SETHEADERT", ["SETCLASS", "SETNAME", "LANGU", "DESCRIPT"],
                    "SETNAME LIKE 'YBANK%' AND LANGU = 'E'"):
            print("    TEXTO  %-34s %s" % (r["SETNAME"], r["DESCRIPT"]))
    except Exception as e:
        print("  SETHEADERT -> %s" % str(e)[:90])

    # --- SETNODE: la jerarquia --------------------------------------------
    try:
        rows = rd(c, "SETNODE", ["SETCLASS", "SETNAME", "SUBSETNAME", "SEQNR"],
                  "SETNAME LIKE 'YBANK%'")
        print("\n  SETNODE — aristas de la jerarquia: %d" % len(rows))
        hijos = collections.defaultdict(list)
        for r in rows:
            hijos[r["SETNAME"]].append(r["SUBSETNAME"])
        for padre in sorted(hijos):
            print("    %-34s -> %s" % (padre, ", ".join(sorted(hijos[padre]))))
    except Exception as e:
        print("  SETNODE -> %s" % str(e)[:100])

    # --- cuantas hojas y cuantos valores -----------------------------------
    try:
        leaf = rd(c, "SETLEAF", ["SETNAME", "VALFROM"], "SETNAME LIKE 'YBANK%'")
        n = collections.Counter(r["SETNAME"] for r in leaf)
        print("\n  SETLEAF — valores por hoja: total %d en %d hojas" % (len(leaf), len(n)))
        for k, v in sorted(n.items()):
            print("    %-34s %d" % (k, v))
    except Exception as e:
        print("  SETLEAF -> %s" % str(e)[:100])

# --- ¿viaja por transporte? -------------------------------------------------
print("\n" + "=" * 72)
print("¿YBANK viaja por TRANSPORTE? — se busca en objetos de transporte (E071)")
c = get_connection("P01")
for pat in ("YBANK%",):
    try:
        rows = rd(c, "E071", ["TRKORR", "PGMID", "OBJECT", "OBJ_NAME"],
                  "OBJ_NAME LIKE '%s'" % pat, 100)
        print("  E071 con OBJ_NAME LIKE '%s': %d" % (pat, len(rows)))
        for r in rows[:15]:
            print("    " + " | ".join(r.values()))
    except Exception as e:
        print("  E071 -> %s" % str(e)[:110])
print("\nOK")
