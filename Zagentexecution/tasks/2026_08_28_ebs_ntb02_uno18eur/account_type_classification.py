# -*- coding: utf-8 -*-
"""¿Son de INVERSION las cuentas que no reciben extracto? ¿Y existe ya una clasificacion?

Antes de inventar un subgrupo se mira si el sistema ya lo tiene. Candidatos, en orden:

  1. JERARQUIA YBANK (SETLEAF/SETNODE) -- el doc del dominio ya la describe con nodos
     _CA (cuentas corrientes), _SIGHT (a la vista), _DEPOSIT (capital). Si eso cubre el
     parque, la clasificacion EXISTE y no hay que crear nada.
  2. SKB1.FDLEV -- nivel de planificacion de tesoreria (B0/B1...), que en teoria separa
     disponible de colocado.
  3. El TEXTO de la cuenta -- MANDATE / RAMP / DEPOSIT / CASH POOL.

Se cruza con el canal de entrada del extracto para ver si "sin extracto" y "de inversion"
son la misma poblacion.

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


def rd(tab, fields, where="", n=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=([{"TEXT": where}] if where else []),
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, [x.strip() for x in y["WA"].split("|")])) for y in r["DATA"]]


# ---- 1. ¿existe la jerarquia YBANK y que cubre? ------------------------------
print("\n==== 1. jerarquia YBANK (SETLEAF) ====")
leaf = rd("SETLEAF", ["SETCLASS", "SETNAME", "LINEID", "VALFROM", "VALTO"], "SETNAME LIKE 'YBANK%'")
sets = collections.defaultdict(list)
for r in leaf:
    sets[r["SETNAME"]].append((r["VALFROM"], r["VALTO"]))
for s in sorted(sets):
    print("   %-32s %d valores" % (s, len(sets[s])))
if not sets:
    print("   (SETLEAF no devuelve nada para YBANK* — o no existe, o no es legible)")

# mapa cuenta de mayor -> set hoja
gl2set = {}
for s, vals in sets.items():
    if s in ("YBANK_ACCOUNTS_ALL", "YBANK_ACCOUNTS_HQ", "YBANK_ACCOUNTS_FO"):
        continue
    for lo, hi in vals:
        gl2set.setdefault(lo.lstrip("0") or lo, set()).add(s)

# ---- 2. cuentas vivas + su canal (del censo ya calculado) --------------------
censo_p = os.path.join(HERE, "channel_census.json")
censo = json.load(open(censo_p, encoding="utf-8")) if os.path.exists(censo_p) else []
print("\n   censo cargado: %d cuentas" % len(censo))

t012k = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r for r in
         rd("T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "WAERS", "HKONT"])}

# ---- 3. SKB1: nivel de planificacion y gestion de partidas ------------------
gls = sorted({r["HKONT"] for r in t012k.values() if r["HKONT"]})
print("\n==== 2. SKB1 — nivel de planificacion (FDLEV) de las cuentas de mayor de banco ====")
skb1 = {}
for i in range(0, len(gls), 60):
    trozo = gls[i:i + 60]
    cond = " OR ".join("SAKNR = '%s'" % g for g in trozo)
    try:
        for r in rd("SKB1", ["BUKRS", "SAKNR", "FDLEV", "XOPVW", "ZUAWA"], "(%s)" % cond):
            skb1[(r["BUKRS"], r["SAKNR"])] = r
    except Exception as e:
        print("   trozo fallo: %s" % str(e)[:80])
niv = collections.Counter(r["FDLEV"] for r in skb1.values())
print("   reparto de FDLEV: %s" % dict(niv))

# ---- 4. cruce: canal x tipo -------------------------------------------------
PAL_INV = ("MANDATE", "RAMP", "PIMCO", "MORGAN", "IMIP", "ASHI", "DEPOSIT", "CASH POOL",
           "INVEST", "CUSTOD", "PORTFOLIO", "FUND", "HABIF")
print("\n==== 3. cruce CANAL x pistas de INVERSION ====")
print("   %-22s %-13s %-9s %-6s %-28s %s" % ("cuenta", "canal", "GL", "FDLEV", "texto", "pista"))
filas = []
for f in censo:
    if f.get("cerrada"):
        continue
    bu, resto = f["cuenta"].split("/")
    hb, hk = resto.split("-", 1)
    k = (bu, hb, hk)
    m = t012k.get(k, {})
    gl = m.get("HKONT", "")
    sk = skb1.get((bu, gl), {})
    t = (f.get("texto") or "").upper()
    pista = ",".join(p for p in PAL_INV if p in t)
    sset = ",".join(sorted(gl2set.get(gl.lstrip("0"), set()) | gl2set.get(gl, set())))
    fila = dict(f, gl=gl, fdlev=sk.get("FDLEV", ""), ybank=sset, pista=pista)
    filas.append(fila)
    if f["canal"] == "SIN EXTRACTO" or pista:
        print("   %-22s %-13s %-9s %-6s %-28s %s"
              % (f["cuenta"], f["canal"], gl, sk.get("FDLEV", "-"),
                 (f.get("texto") or "")[:28], pista or "-"))

print("\n==== 4. ¿la jerarquia YBANK separa esas cuentas? ====")
for f in filas:
    if f["canal"] == "SIN EXTRACTO":
        print("   %-22s GL=%-10s YBANK=%s" % (f["cuenta"], f["gl"], f["ybank"] or "(en NINGUN set)"))

print("\n==== 5. reparto CANAL x set YBANK (cuentas vivas) ====")
cr = collections.Counter((f["canal"], f["ybank"] or "(sin set)") for f in filas)
for k, v in sorted(cr.items()):
    print("   %-13s %-34s %d" % (k[0], k[1], v))

json.dump(filas, open(os.path.join(HERE, "account_types.json"), "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
print("\nOK")
