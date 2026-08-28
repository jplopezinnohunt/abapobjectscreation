# -*- coding: utf-8 -*-
"""¿De que TAMANO es la oportunidad? "Siete cuentas" no dice nada.

Se mide en tres capas, porque el coste de un extracto manual no es teclearlo:

  1. VOLUMEN     lineas de extracto (FEBEP), que es lo que de verdad se teclea
  2. ARRASTRE    que regla de contabilizacion reciben esas lineas y si compensan solas.
                 Un extracto manual usa reglas MXX* con algoritmo 000 = NO compensa: cada
                 linea cae en la cola de FEBAN y alguien la casa a mano DESPUES.
  3. FRAGILIDAD  cuantas personas lo sostienen y cuanto lleva callada cada cuenta

La comparacion es contra una cuenta hermana del MISMO formato que si entra electronica.

SOLO LECTURA.
"""
import sys, os, collections, datetime

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


MANUALES = [("BLN01", "USD01"), ("BLN01", "SDD01"), ("BMN01", "CUP02"), ("BMN01", "EUR01"),
            ("BTE01", "IRR02"), ("BTE01", "EUR01"), ("ECO08", "ZWG01")]
# controles: mismo formato XRT940, entran electronicos
CONTROL = [("ECO08", "USD01"), ("ECO05", "XAF01"), ("CBE01", "USD01")]

hoy = datetime.datetime.now().strftime("%Y%m%d")

# --- cabeceras: KUKEY por cuenta ---------------------------------------------
feb = rd("FEBKO", ["BUKRS", "HBKID", "HKTID", "KUKEY", "AZDAT", "EFART", "EUSER"],
         "BUKRS = 'UNES' AND AZDAT >= '20250101'")
por = collections.defaultdict(list)
for r in feb:
    if r["AZDAT"] <= hoy:
        por[(r["HBKID"], r["HKTID"])].append(r)

kukeys = {}
for grupo in (MANUALES + CONTROL):
    kukeys[grupo] = {r["KUKEY"] for r in por.get(grupo, [])}

todos = set().union(*kukeys.values()) if kukeys else set()
print("\ncabeceras de extracto a inspeccionar: %d" % len(todos))

# --- lineas: FEBEP por KUKEY -------------------------------------------------
# FEBEP es grande: se lee por rango de KUKEY de cada cuenta, nunca entera.
lineas = collections.defaultdict(list)
for grupo, ks in kukeys.items():
    if not ks:
        continue
    lo, hi = min(ks), max(ks)
    try:
        rows = rd("FEBEP", ["KUKEY", "ESNUM", "VGINT", "BELNR", "VGEXT"],
                  "KUKEY >= '%s' AND KUKEY <= '%s'" % (lo, hi))
    except Exception as e:
        print("  FEBEP %s -> %s" % (str(grupo), str(e)[:80]))
        continue
    for r in rows:
        if r["KUKEY"] in ks:
            lineas[grupo].append(r)

print("\n" + "=" * 100)
print("CAPA 1 y 2 — VOLUMEN tecleado y QUE PASA DESPUES  (2025-2026)")
print("=" * 100)
print("  %-16s %7s %8s %7s %-22s %s" %
      ("cuenta", "extr.", "lineas", "l/extr", "reglas que reciben", "sin doc FI"))


def bloque(lista, etiqueta):
    print("\n  --- %s ---" % etiqueta)
    tot_e = tot_l = 0
    for g in lista:
        e = len(kukeys.get(g, ()))
        ls = lineas.get(g, [])
        reglas = collections.Counter(x["VGINT"] for x in ls)
        sindoc = sum(1 for x in ls if x["BELNR"] in ("", "*"))
        tot_e += e
        tot_l += len(ls)
        print("  %-16s %7d %8d %7.1f %-22s %d"
              % ("%s-%s" % g, e, len(ls), (len(ls) / e if e else 0),
                 ", ".join("%s:%d" % (k, v) for k, v in reglas.most_common(3)), sindoc))
    print("  %-16s %7d %8d" % ("TOTAL", tot_e, tot_l))
    return tot_e, tot_l


me, ml = bloque(MANUALES, "MANUALES — se teclean teniendo XRT940 asignado")
ce, cl = bloque(CONTROL, "CONTROL — mismo formato XRT940, entran electronicos")

print("\n" + "=" * 100)
print("CAPA 3 — FRAGILIDAD")
print("=" * 100)
for g in MANUALES:
    rows = por.get(g, [])
    if not rows:
        print("  %-16s (sin extractos)" % ("%s-%s" % g))
        continue
    users = collections.Counter(r["EUSER"] for r in rows)
    ult = max(r["AZDAT"] for r in rows)
    dias = (datetime.datetime.strptime(hoy, "%Y%m%d")
            - datetime.datetime.strptime(ult, "%Y%m%d")).days
    print("  %-16s ultimo=%s (%3d dias) · lo hacen: %s"
          % ("%s-%s" % g, ult, dias, dict(users.most_common(3))))

personas = collections.Counter()
for g in MANUALES:
    for r in por.get(g, []):
        personas[r["EUSER"]] += 1
print("\n  personas que sostienen las 7 cuentas: %d -> %s" % (len(personas), dict(personas)))
print("\n  RESUMEN: %d extractos y %d lineas tecleadas en 2025-2026 (%d por ano aprox.)"
      % (me, ml, ml / 2))
