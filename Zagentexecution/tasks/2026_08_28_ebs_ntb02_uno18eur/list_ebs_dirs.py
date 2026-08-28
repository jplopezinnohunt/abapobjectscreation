# -*- coding: utf-8 -*-
"""Directorio FISICO de las rutas logicas del EBS, y su contenido.

Discriminante final: si en el directorio de PROCESO o de ERROR hay ficheros de la cuenta
EUR posteriores al 14.08, el fichero LLEGA y SAP lo rechaza (la causa es T028B). Si no
hay nada, ademas hay que mirar aguas arriba.

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


print("\n==== FEB_FILEPATH — ruta logica -> directorio ====")
paths = {}
for pair in (["PATH", "DIRECTORY"], ["PATH", "FILENAME"], ["PATH", "UPD_MODE"]):
    try:
        for r in rd("FEB_FILEPATH", pair, "", 0):
            k = r["PATH"].strip()
            paths.setdefault(k, {}).update({kk: vv.strip() for kk, vv in r.items()})
    except Exception as e:
        print("   %s -> %s" % (pair, str(e)[:80]))
for k, v in sorted(paths.items()):
    print("   %-12s %s" % (k, {kk: vv for kk, vv in v.items() if kk != "PATH" and vv}))

dirs = sorted({v.get("DIRECTORY", "") for v in paths.values() if v.get("DIRECTORY")})
print("\n   directorios distintos:", dirs)

print("\n==== contenido de cada directorio ====")
for d in dirs:
    try:
        res = c.call("RZL_READ_DIR_LOCAL", NAME=d)
        ent = res.get("FILE_TBL") or []
        print("\n   --- %s : %d entradas ---" % (d, len(ent)))
        rows = []
        for e in ent:
            nm = (e.get("NAME") or "").strip()
            if nm in (".", ".."):
                continue
            rows.append((e.get("MODDATE", ""), e.get("MODTIME", ""), e.get("LEN", ""), nm))
        rows.sort(reverse=True)
        for r0 in rows[:40]:
            print("       %s %s %10s  %s" % (r0[0], r0[1], r0[2], r0[3][:90]))
        if not rows:
            print("       (vacio)")
    except Exception as e:
        print("\n   --- %s -> ERROR %s" % (d, str(e)[:110]))

print("\nOK")
