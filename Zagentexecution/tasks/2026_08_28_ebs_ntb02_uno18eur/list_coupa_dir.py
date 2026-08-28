# -*- coding: utf-8 -*-
"""Mapeo EXACTO ruta logica -> directorio (una lectura por ruta, sin emparejar por
posicion) y listado del directorio donde Coupa deja los ficheros del EBS.

Emparejar dos lecturas por posicion es justo el modo de fallo 'EL ALIAS QUE DA CERO':
no da error, da una respuesta segura y falsa. Aqui se pregunta ruta por ruta.

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

PATHS = ["Y_EBS_PRO", "Y_EBS_ARC", "Y_EBS_ERR", "Y_EBS_TRA",
         "Z_EBS_PRO", "Z_EBS_ARC", "Z_EBS_ERR", "Z_EBS_TRA"]

print("\n==== mapeo EXACTO ruta logica -> directorio ====")
mapping = {}
for p in PATHS:
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="FEB_FILEPATH", DELIMITER="|", ROWCOUNT=0,
                   OPTIONS=[{"TEXT": "PATH = '%s'" % p}],
                   FIELDS=[{"FIELDNAME": "DIRECTORY"}])
        d = r["DATA"][0]["WA"].strip() if r["DATA"] else ""
        mapping[p] = d
        print("   %-12s -> %s" % (p, d))
    except Exception as e:
        print("   %-12s -> ERROR %s" % (p, str(e)[:80]))

print("\n==== listado de los directorios (sustituyendo <SYSID> por P01) ====")
for p in PATHS:
    d = mapping.get(p, "")
    if not d:
        continue
    real = d.replace("<SYSID>", "P01").rstrip("\\")
    try:
        res = c.call("RZL_READ_DIR_LOCAL", NAME=real)
        ent = [e for e in (res.get("FILE_TBL") or [])
               if (e.get("NAME") or "").strip() not in (".", "..")]
        print("\n   --- %s  ->  %s : %d ficheros ---" % (p, real, len(ent)))
        rows = sorted(((e.get("MODDATE", ""), e.get("MODTIME", ""), e.get("LEN", ""),
                        (e.get("NAME") or "").strip()) for e in ent), reverse=True)
        for r0 in rows[:30]:
            print("       %s %s %10s  %s" % (r0[0], r0[1], r0[2], r0[3][:95]))
        if not rows:
            print("       (vacio)")
    except Exception as e:
        print("\n   --- %s  ->  %s : ERROR %s" % (p, real, str(e)[:100]))

print("\nOK")
