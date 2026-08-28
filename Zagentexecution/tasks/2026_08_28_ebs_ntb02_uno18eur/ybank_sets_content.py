# -*- coding: utf-8 -*-
"""¿Que hay DENTRO de _SIGHT y _DEPOSIT, y que dice FDLEV?

La jerarquia YBANK resulta clasificar por GEOGRAFIA + DIVISA (HQ/FO x EUR/USD/OTH), no por
NATURALEZA de la cuenta. Pero tiene dos nodos que si suenan a naturaleza -- SIGHT (a la
vista) y DEPOSIT (capital) -- y hay que ver que meten ahi de verdad antes de decir que la
naturaleza no esta modelada en ningun sitio.

Segundo candidato: SKB1-FDLEV, el nivel de planificacion de tesoreria.

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


# mapa GL -> cuenta de banco casa + texto
t012k = rd("T012K", ["BUKRS", "HBKID", "HKTID", "HKONT", "WAERS"])
txt = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r["TEXT1"] for r in
       rd("T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"], "SPRAS = 'E'")}
gl2acc = {}
for r in t012k:
    k = (r["BUKRS"], r["HBKID"], r["HKTID"])
    gl2acc.setdefault(r["HKONT"], []).append(
        ("%s/%s-%s" % k, txt.get(k, ""), r["WAERS"]))

print("\n==== contenido de los sets de NATURALEZA ====")
for s in ("YBANK_ACCOUNTS_SIGHT_EUR", "YBANK_ACCOUNTS_SIGHT_USD", "YBANK_ACCOUNTS_DEPOSIT",
          "YBANK_ACCOUNTS_HQ_EUR", "YBANK_ACCOUNTS_HQ_USD", "YBANK_ACCOUNTS_HQ_OTH"):
    rows = rd("SETLEAF", ["SETNAME", "VALFROM", "VALTO"], "SETNAME = '%s'" % s)
    print("\n   --- %s : %d ---" % (s, len(rows)))
    for r in rows:
        gl = r["VALFROM"]
        accs = gl2acc.get(gl) or gl2acc.get(gl.zfill(10)) or []
        if accs:
            for a, t, w in accs:
                print("      %-10s %-22s %-4s %s" % (gl, a, w, t))
        else:
            print("      %-10s (ninguna cuenta de banco casa apunta a este mayor)" % gl)

# ---- FDLEV, leido de forma que P01 no rechace --------------------------------
print("\n==== SKB1 — nivel de planificacion (FDLEV) de los mayores de banco de UNES ====")
sk = {}
for pref in ("00010", "00014", "00091"):
    try:
        for r in rd("SKB1", ["BUKRS", "SAKNR", "FDLEV", "XOPVW"],
                    "BUKRS = 'UNES' AND SAKNR LIKE '%s%%'" % pref):
            sk[r["SAKNR"]] = r
    except Exception as e:
        print("   %s -> %s" % (pref, str(e)[:80]))
print("   mayores leidos: %d" % len(sk))
niv = collections.Counter(r["FDLEV"] or "(vacio)" for r in sk.values())
print("   reparto FDLEV: %s" % dict(niv))

print("\n   FDLEV de las cuentas de Northern Trust (operativas vs mandato):")
for r in sorted(t012k, key=lambda x: (x["HBKID"], x["HKTID"])):
    if r["HBKID"].startswith("NTB") and r["BUKRS"] == "UNES":
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        s = sk.get(r["HKONT"], {})
        print("      %-22s GL=%-10s FDLEV=%-4s %s"
              % ("%s/%s-%s" % k, r["HKONT"], s.get("FDLEV", "-"), txt.get(k, "")))

# ---- ¿cuantas cuentas VIVAS con extracto NO estan en ningun set YBANK? -------
print("\n==== cobertura de la jerarquia YBANK ====")
leaf = rd("SETLEAF", ["SETNAME", "VALFROM"], "SETNAME LIKE 'YBANK%'")
en_set = {r["VALFROM"] for r in leaf} | {r["VALFROM"].zfill(10) for r in leaf}
vivas = [r for r in t012k
         if not any(m in (txt.get((r["BUKRS"], r["HBKID"], r["HKTID"]), "") or "").upper()
                    for m in ("CLOSED", "FERME", "CERRAD"))]
fuera = [r for r in vivas if r["HKONT"] not in en_set and r["HKONT"].lstrip("0") not in en_set]
print("   cuentas vivas: %d · fuera de TODO set YBANK: %d" % (len(vivas), len(fuera)))
for r in fuera[:30]:
    k = (r["BUKRS"], r["HBKID"], r["HKTID"])
    print("      %-22s GL=%-10s %s" % ("%s/%s-%s" % k, r["HKONT"], txt.get(k, "")))
if len(fuera) > 30:
    print("      ... +%d" % (len(fuera) - 30))
