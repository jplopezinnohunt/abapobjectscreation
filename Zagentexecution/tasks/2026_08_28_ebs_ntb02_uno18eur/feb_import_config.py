# -*- coding: utf-8 -*-
"""La configuracion de ENTRADA de ficheros del EBS moderno (FEB_IMP_*) + el contenido
de la variante 'EBS JOB_COUPA' que el job usa.

FEB_FILE_HANDLING tiene UN solo select-option obligatorio: FEB_IMP_SOURCE-PATH_SOURCE.
O sea que la variante dice QUE FUENTES se procesan, y FEB_IMP_SOURCE dice que es cada
fuente: directorio, formato y — esto es lo que importa — a que banco/cuenta pertenece.

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
    rows = rd("DD03L", ["FIELDNAME", "POSITION"], "TABNAME = '%s' AND AS4LOCAL = 'A'" % tab, 300)
    rows.sort(key=lambda r: r["POSITION"].strip())
    return [r["FIELDNAME"].strip() for r in rows
            if not r["FIELDNAME"].strip().startswith(".") and r["FIELDNAME"].strip() != "MANDT"]


def dump(tab, where="", chunk=5):
    try:
        fl = fields_of(tab)
    except Exception as e:
        print("\n--- %s: sin campos (%s)" % (tab, str(e)[:60]))
        return
    print("\n===== %s ===== campos(%d): %s" % (tab, len(fl), fl))
    merged = None
    for i in range(0, len(fl), chunk):
        part = fl[i:i + chunk]
        try:
            rows = rd(tab, part, where, 0)
        except Exception as e:
            print("   chunk %s -> %s" % (part, str(e)[:70]))
            continue
        if merged is None:
            merged = [dict(r) for r in rows]
        else:
            for j, r in enumerate(rows):
                if j < len(merged):
                    merged[j].update(r)
    if not merged:
        print("   (sin filas)")
        return
    print("   filas: %d" % len(merged))
    for r in merged[:30]:
        print("   " + " | ".join("%s=%s" % (k, v.strip()) for k, v in r.items() if v.strip()))


for t in ("FEB_IMP_SOURCE", "FEB_FILEPATH", "FEB_IMP_FORMAT", "FEB_IMP_POST",
          "FEB_IMP_SELOPT", "FEB_IMP_TRANS", "FEB_IMP_TRANPATH", "FEB_IMP_STRUCT"):
    dump(t)

# ---- contenido de la variante -------------------------------------------------
print("\n\n===== VARIANTE 'EBS JOB_COUPA' de FEB_FILE_HANDLING =====")
for fm, kw in (
    ("RS_VARIANT_CONTENTS", {"REPORT": "FEB_FILE_HANDLING", "VARIANT": "EBS JOB_COUPA"}),
    ("RS_VARIANT_VALUES_TECH_DATA", {"REPORT": "FEB_FILE_HANDLING", "VARIANT": "EBS JOB_COUPA"}),
):
    try:
        res = c.call(fm, **kw)
        for k, v in res.items():
            if isinstance(v, list) and v:
                print("  [%s] %s (%d)" % (fm, k, len(v)))
                for row in v[:60]:
                    print("     ", {kk: str(vv).strip() for kk, vv in row.items() if str(vv).strip()}
                          if isinstance(row, dict) else str(row)[:150])
        break
    except Exception as e:
        print("  %s -> %s" % (fm, str(e)[:110]))

# VARIS = valores de select-options de la variante
print("\n--- VARIS (valores de select-options de las variantes del programa) ---")
try:
    for r in rd("VARIS", ["REPORT", "VARIANT", "SELNAME", "KIND", "SIGN", "OPTI", "LOW", "HIGH"],
                "REPORT = 'FEB_FILE_HANDLING'", 200):
        print("   " + " | ".join(v.strip() for v in r.values()))
except Exception as e:
    print("   VARIS -> %s" % str(e)[:110])

print("\nOK")
