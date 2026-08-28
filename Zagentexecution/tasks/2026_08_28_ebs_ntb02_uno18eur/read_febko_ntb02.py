# -*- coding: utf-8 -*-
"""¿Que identificador de cuenta traen los extractos que ENTRAN, y desde cuando?

FF67 muestra 'Account UNO12EUR' porque el OVERVIEW se pinta de FEBKO — lo que el
FICHERO trajo — no de T012K. Asi que la pregunta no es que dice la config: es que
dice el fichero, y si desde el cambio (17.08.2026) ha entrado alguno.

SOLO LECTURA.
"""
import sys, os, json, collections

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection

c = get_connection("P01")
print("SID real:", c.sid_real)


def rd(tab, fields, where, n=0, skip=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=[{"TEXT": w} for w in ([where] if isinstance(where, str) else where)],
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, x["WA"].split("|"))) for x in r["DATA"]]


def show(title, rows, cols=None, limit=40):
    print("\n==== %s ==== (%d filas)" % (title, len(rows)))
    if not rows:
        print("   (vacio)")
        return
    cols = cols or list(rows[0].keys())
    print(" | ".join(cols))
    for r in rows[:limit]:
        print(" | ".join(r.get(cc, "").strip() for cc in cols))
    if len(rows) > limit:
        print("   ... +%d" % (len(rows) - limit))


# --- 0. campos reales de FEBKO -------------------------------------------------
f = rd("DD03L", ["FIELDNAME"], "TABNAME = 'FEBKO' AND AS4LOCAL = 'A'", 400)
names = sorted(x["FIELDNAME"].strip() for x in f)
print("\n==== FEBKO FIELDS ====")
print(" ".join(names))

want = ["BUKRS", "HBKID", "HKTID", "KTONR", "AZDAT", "ASTAT", "EFART", "AZNUM"]
use = [w for w in want if w in names][:8]
print("USO:", use)

# --- 1. extractos de NTB02 en 2026 --------------------------------------------
rows = rd("FEBKO", use, "BUKRS = 'UNES' AND HBKID = 'NTB02'", 0)
print("\nFEBKO NTB02 total filas: %d" % len(rows))

# distinto por (HKTID, BANKN/UKONT)
key_acc = "KTONR"
combos = collections.Counter()
last = {}
for r in rows:
    k = (r.get("HKTID", "").strip(), r.get(key_acc, "").strip())
    combos[k] += 1
    d = r.get("AZDAT", "").strip()
    if d and (k not in last or d > last[k]):
        last[k] = d
print("\n==== NTB02 — combinaciones (HKTID, %s) con ULTIMA fecha de extracto ====" % key_acc)
for k, n in combos.most_common():
    print("HKTID=%-6s %s=%-14s  extractos=%-6d  ultimo=%s" % (k[0], key_acc, k[1], n, last.get(k, "")))

# --- 2. lo que ha entrado DESPUES del cambio (17.08.2026) ---------------------
post = [r for r in rows if r.get("AZDAT", "").strip() >= "20260817"]
show("NTB02 — extractos con fecha >= 17.08.2026 (el cambio)", post, use)

recent = sorted([r for r in rows if r.get("AZDAT", "").strip() >= "20260701"],
                key=lambda r: r.get("AZDAT", ""))
show("NTB02 — extractos desde 01.07.2026", recent, use, limit=60)

# --- 3. ¿entra ALGO en P01 desde el 17.08 por cualquier banco? (control) ------
allpost = rd("FEBKO", ["BUKRS", "HBKID", "HKTID", "AZDAT", "ASTAT", "EFART"],
             "BUKRS = 'UNES' AND AZDAT >= '20260817'", 0)
by_bank = collections.Counter((r["HBKID"].strip(), r["HKTID"].strip()) for r in allpost)
print("\n==== CONTROL — UNES: extractos de CUALQUIER banco desde 17.08.2026: %d ====" % len(allpost))
for k, n in by_bank.most_common(25):
    print("  %s-%s : %d" % (k[0], k[1], n))

json.dump({"combos": {"%s|%s" % k: v for k, v in combos.items()},
           "last": {"%s|%s" % k: v for k, v in last.items()},
           "post_change": post},
          open(os.path.join(HERE, "febko_ntb02.json"), "w"), indent=2, ensure_ascii=False)
print("\nOK")
