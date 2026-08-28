# -*- coding: utf-8 -*-
"""La configuracion del EBS que cuelga del NUMERO DE CUENTA, comparando la cuenta ROTA
(NTB02/EUR01) contra las que SIGUEN entrando (NTB01/USD*).

El retro de NTB01 del 2026-04-08 ya nombro T035D como el hueco. Aqui se comprueba si
NTB02 lo tiene, y con que valor.

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


def rd(tab, fields, where, n=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
               OPTIONS=[{"TEXT": w} for w in ([where] if isinstance(where, str) else where)],
               FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, x["WA"].split("|"))) for x in r["DATA"]]


def fields_of(tab):
    return [x["FIELDNAME"].strip() for x in
            sorted(rd("DD03L", ["FIELDNAME", "POSITION"],
                      "TABNAME = '%s' AND AS4LOCAL = 'A'" % tab, 500),
                   key=lambda r: r["POSITION"])
            if not x["FIELDNAME"].strip().startswith(".")]


def dump(tab, where, label, maxf=8):
    try:
        fl = [f for f in fields_of(tab) if f != "MANDT"][:maxf]
    except Exception as e:
        print("  %s: no se pueden leer campos (%s)" % (tab, str(e)[:70]))
        return []
    try:
        rows = rd(tab, fl, where, 0)
    except Exception as e:
        print("  %s [%s]: ERROR %s" % (tab, where, str(e)[:90]))
        return []
    print("\n  --- %s (%s) : %d filas --- campos=%s" % (tab, label, len(rows), fl))
    for r in rows[:40]:
        print("      " + " | ".join(v.strip() for v in r.values()))
    return rows


# ---- 1. TBTCP: pasos del job -------------------------------------------------
print("\n==== 1. TBTCP — campos reales y pasos del job EBS INTEGRATION ====")
try:
    print("  campos TBTCP:", fields_of("TBTCP")[:25])
except Exception as e:
    print("  ERROR campos TBTCP:", str(e)[:90])
for flds in (["JOBNAME", "PROGNAME", "VARIANT"], ["JOBNAME", "STEPCOUNT", "PROGNAME"]):
    try:
        st = rd("TBTCP", flds, "JOBNAME = 'EBS INTEGRATION'", 0)
        agg = collections.Counter(tuple(v.strip() for v in r.values()) for r in st)
        print("  con %s -> %d filas" % (flds, len(st)))
        for k, n in agg.most_common(10):
            print("     ", k, "n=%d" % n)
        break
    except Exception as e:
        print("  con %s -> ERROR %s" % (flds, str(e)[:80]))

# ---- 2. T035D / T035U : clave corta de cuenta bancaria -> cuenta de mayor -----
print("\n==== 2. T035D / T035U — clave corta de cuenta (DISKB) -> cuenta de mayor ====")
for tab in ("T035D", "T035U"):
    dump(tab, "DISKB LIKE 'NTB%'", "NTB*")
    dump(tab, "DISKB LIKE '%EUR%'", "*EUR*")

# ---- 3. T028B — formatos de extracto ------------------------------------------
print("\n==== 3. T028B — asignacion de formato de extracto ====")
try:
    print("  campos T028B:", fields_of("T028B"))
except Exception as e:
    print("  ERROR:", str(e)[:80])
dump("T028B", "VGTYP = 'TR_TRNF'", "VGTYP=TR_TRNF (el de NTB02/EUR01)")

# ---- 4. T012K de TODO el paisaje con las cuentas viejas/nuevas ---------------
print("\n==== 4. T012K — ¿queda la cuenta VIEJA en algun sitio del paisaje? ====")
for w, lab in (("BANKN LIKE '11939389%'", "cuenta VIEJA 11939389"),
               ("BANKN LIKE '18747647%'", "cuenta NUEVA 18747647"),
               ("BNKN2 LIKE 'UNO12%'", "BNKN2 UNO12*"),
               ("BNKN2 LIKE 'UNO1%'", "BNKN2 UNO1*")):
    try:
        rows = rd("T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BNKN2", "WAERS", "HKONT"], w, 0)
        print("\n  --- %s : %d ---" % (lab, len(rows)))
        for r in rows:
            print("      " + " | ".join(v.strip() for v in r.values()))
    except Exception as e:
        print("  %s -> ERROR %s" % (lab, str(e)[:80]))

print("\nOK")
