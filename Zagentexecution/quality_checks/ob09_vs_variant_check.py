"""
ob09_vs_variant_check.py — SOLO LECTURA. Valida la configuracion de revaluacion FX cruzando
las DOS condiciones que tienen que darse a la vez, y que nadie cruzaba porque una no se sabia leer:

  (1) T030H / OB09  dice DONDE se postea la diferencia de cambio.
  (2) La VARIANTE de F.05 decide SI la cuenta entra siquiera en el calculo.

Una cuenta con (1) y sin (2) esta perfectamente configurada y NO SE VALORA NUNCA. No da error:
simplemente no ocurre. Ese es el defecto que este check caza.

Lee el contenido real de las variantes con RS_VARIANT_CONTENTS_RFC (remote-enabled, funciona en
P01 sin S_DEVELOP). VARI guarda el contenido en CLUSTD, un campo RAW que RFC_READ_TABLE no
devuelve, y VARIS no contiene rangos: por eso durante sesiones se creyo que esto no era auditable.

Uso:
    python ob09_vs_variant_check.py                       # P01
    python ob09_vs_variant_check.py --systems P01,D01,V01 # y compara los tres
    python ob09_vs_variant_check.py --accounts 40410      # limita a un prefijo
Salida: exit 0 limpio · exit 1 si hay cuentas ACTIVAS con OB09 fuera de toda variante.
"""
import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

KTOPL = "UNES"
BUKRS = "UNES"
PROGRAM = "SAPF100"


def parse(res):
    m = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in m} for r in res.get("DATA", [])]


def rd(conn, table, fields, where):
    try:
        return parse(conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                               FIELDS=[{"FIELDNAME": f} for f in fields],
                               OPTIONS=[{"TEXT": where}], ROWCOUNT=0))
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        print("    ERR %s: %s" % (table, str(e)[:100]))
        return []


def variant_accounts(conn, variant):
    """Devuelve (incluidas, excluidas, rangos) de la seleccion de cuentas de una variante.
    OJO: el mecanismo cambia entre variantes del MISMO programa — UNES_DEPOSIT usa valores
    sueltos EQ, UNES_UNBA usa rangos BT. No asumir uno de los dos."""
    inc, exc, rngs = set(), set(), []
    try:
        r = conn.call("RS_VARIANT_CONTENTS_RFC", REPORT=PROGRAM, VARIANT=variant, VALUTAB=[])
    except Exception as e:
        print("    variante %s no legible: %s" % (variant, str(e)[:90]))
        return inc, exc, rngs
    for x in (r.get("VALUTAB") or []):
        if (x.get("SELNAME") or "").strip() not in ("SKONTO", "AKONTO"):
            continue
        lo, hi = (x.get("LOW") or "").strip(), (x.get("HIGH") or "").strip()
        sign, opt = (x.get("SIGN") or "").strip(), (x.get("OPTION") or "").strip()
        if not lo:
            continue
        if opt == "BT" and hi:
            rngs.append((sign, lo.zfill(10), hi.zfill(10)))
        else:
            (exc if sign == "E" else inc).add(lo.zfill(10))
    return inc, exc, rngs


def covered(saknr, sets):
    """¿La cuenta entra en la seleccion de alguna variante? Devuelve la lista de variantes."""
    hit = []
    for var, (inc, exc, rngs) in sets.items():
        if saknr in exc:
            continue
        if saknr in inc or any(lo <= saknr <= hi for sign, lo, hi in rngs if sign == "I"):
            hit.append(var)
    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="P01")
    ap.add_argument("--accounts", default="", help="prefijo de cuenta para acotar, p.ej. 40410")
    a = ap.parse_args()
    systems = [s.strip().upper() for s in a.systems.split(",") if s.strip()]
    rc = 0

    for sysid in systems:
        print("\n" + "=" * 78)
        print("%s — OB09 (T030H) x variantes de %s" % (sysid, PROGRAM))
        print("=" * 78)
        c = get_connection(sysid)
        try:
            variants = sorted({x["VARIANT"] for x in
                               rd(c, "VARID", ["VARIANT"], "REPORT = '%s'" % PROGRAM)
                               if x["VARIANT"].startswith(BUKRS)})
            print("  variantes de %s: %s" % (BUKRS, ", ".join(variants) or "(ninguna)"))
            sets = {v: variant_accounts(c, v) for v in variants}
            for v, (inc, exc, rngs) in sets.items():
                print("    %-16s sueltas=%-3d excluidas=%-3d rangos=%s"
                      % (v, len(inc), len(exc),
                         ", ".join("%s-%s" % (lo, hi) for s, lo, hi in rngs) or "-"))

            where = "KTOPL = '%s' AND CURTP = '10'" % KTOPL
            if a.accounts:
                where += " AND HKONT LIKE '%%%s%%'" % a.accounts
            t030h = rd(c, "T030H", ["HKONT", "LKORR", "LSBEW", "LHBEW"], where)
            hk = sorted({x["HKONT"] for x in t030h})
            print("\n  cuentas con fila en T030H (CURTP 10): %d" % len(hk))

            blocked = {x["SAKNR"] for x in
                       rd(c, "SKB1", ["SAKNR", "XSPEB"], "BUKRS = '%s'" % BUKRS)
                       if x.get("XSPEB") == "X"}

            orphan = []
            for x in t030h:
                s = x["HKONT"]
                if covered(s, sets):
                    continue
                orphan.append((s, s in blocked, (x.get("LKORR") or "").strip()))
            active = [o for o in orphan if not o[1]]

            print("  configuradas y FUERA de toda variante: %d  (de ellas ACTIVAS: %d)"
                  % (len(orphan), len(active)))
            for s, blk, lk in sorted(orphan):
                print("     %s %s  LKORR=%s" % (s, "[bloqueada]" if blk else "[ACTIVA]  ", lk or "-"))

            # el reverso: en la variante pero sin OB09 -> si tiene exposicion, no sabe donde postear
            invar = set()
            for v, (inc, exc, rngs) in sets.items():
                invar |= (inc - exc)
            no_ob09 = sorted(invar - set(hk)) if not a.accounts else []
            if no_ob09:
                print("\n  en variante y SIN fila en T030H: %d" % len(no_ob09))
                for s in no_ob09:
                    print("     %s" % s)

            if active:
                rc = 1
        finally:
            c.close()

    print("\n%s" % ("LIMPIO" if rc == 0 else
                    "HAY CUENTAS ACTIVAS CON OB09 QUE NINGUNA VARIANTE SELECCIONA"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
