# -*- coding: utf-8 -*-
"""LA PREGUNTA ABIERTA: ¿el fichero de NTB02 llega y rebota, o no llega?

El directorio de ERRORES de Coupa lleva los ficheros que SAP recogio y no pudo procesar,
con el nombre OSOGEFRPPXXX_<SOCIEDAD>_<BANCO>_<CUENTA>_<FECHA>. Si hay uno de
UNES_NTB02_EUR01 posterior al 14.08, el fichero LLEGA y la causa es T028B, punto.
Si no hay ninguno, ademas hay que reclamar aguas arriba.

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

DIRS = {
    "PROCESO (entrada)": r"\\hq-sapitf\coupa$\P01\Out\Data\EBS",
    "ERRORES":           r"\\hq-sapitf\coupa$\P01\Out\Errors\EBS",
    "TRANSFER":          r"\\hq-sapitf\coupa$\P01\Out\Transfer\EBS",
}

for etiqueta, d in DIRS.items():
    print("\n" + "=" * 70)
    print("%s  ->  %s" % (etiqueta, d))
    try:
        res = c.call("RZL_READ_DIR_LOCAL", NAME=d)
    except Exception as e:
        print("   ERROR: %s" % str(e)[:120])
        continue
    ent = [e for e in (res.get("FILE_TBL") or []) if (e.get("NAME") or "").strip() not in (".", "..")]
    print("   %d ficheros" % len(ent))
    if ent:
        print("   claves que devuelve la FM: %s" % sorted(ent[0].keys()))

    nombres = [(e.get("NAME") or "").strip() for e in ent]

    # ¿alguno de NTB02?
    hits = [n for n in nombres if "NTB02" in n.upper()]
    print("\n   >>> ficheros que mencionan NTB02: %d" % len(hits))
    for n in hits[:40]:
        print("        %s" % n)

    # ¿de que bancos son los que estan aqui?
    bancos = collections.Counter()
    for n in nombres:
        p = n.split("_")
        if len(p) >= 4:
            bancos["%s_%s" % (p[2], p[3])] += 1
        else:
            bancos["(otro formato) %s" % n[:24]] += 1
    print("\n   reparto por banco_cuenta (top 20):")
    for k, v in bancos.most_common(20):
        print("        %-28s %d" % (k, v))
