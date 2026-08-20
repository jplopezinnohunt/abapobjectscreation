"""
gl_alignment_check.py — SOLO LECTURA. Mide la alineacion real de GL master entre P01, D01 y V01.

Por que: se afirma que "al 30/06/2026 estaba todo alineado". Es comprobable. Si lo estuviera, lo
unico que deberia faltar en D01 y V01 son las cuentas creadas en P01 DESPUES de esa fecha. Este
script lo mide y fecha cada hueco con SKA1.ERDAT, para separar "deriva nueva" de "nunca llego".

No escribe en ningun sistema. No toca el Gold DB. Solo RFC_READ_TABLE.

Uso:
    python gl_alignment_check.py                    # P01 vs D01 y V01, chart UNES
    python gl_alignment_check.py --since 20260630   # cambia la fecha de corte que se contrasta
"""
import argparse
import os
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

KTOPL = "UNES"
BUKRS_ALL = ["UNES", "IIEP", "ICTP", "UIS", "UIL", "IBE", "UBO", "MGIE", "ICBA", "STEM"]
SPRAS_ALL = ["E", "F", "P", "S", "D"]


def parse(res):
    m = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in m} for r in res.get("DATA", [])]


def rd(conn, table, fields, where):
    """ROWCOUNT=0 sin ROWSKIPS (el wrapper de P01 los rechaza).
    TABLE_WITHOUT_DATA = cero filas; None = no pudimos VER (que no es lo mismo)."""
    try:
        return parse(conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                               FIELDS=[{"FIELDNAME": f} for f in fields],
                               OPTIONS=[{"TEXT": where}], ROWCOUNT=0))
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        print("      ERR %s [%s]: %s" % (table, where[:40], str(e)[:90]))
        return None


def snapshot(sysid):
    """Devuelve los 3 conjuntos de claves + ERDAT por cuenta. Particionado para no reventar
    el buffer de RFC_READ_TABLE."""
    conn = get_connection(sysid)
    try:
        ska1, erdat, unseen = set(), {}, 0
        rows = rd(conn, "SKA1", ["SAKNR", "ERDAT"], "KTOPL = '%s'" % KTOPL)
        if rows is None:
            unseen += 1
            rows = []
        for r in rows:
            ska1.add(r["SAKNR"])
            erdat[r["SAKNR"]] = r.get("ERDAT", "")

        skat = set()
        for sp in SPRAS_ALL:
            r = rd(conn, "SKAT", ["SPRAS", "SAKNR"], "KTOPL = '%s' AND SPRAS = '%s'" % (KTOPL, sp))
            if r is None:
                unseen += 1
                continue
            skat |= {(x["SPRAS"], x["SAKNR"]) for x in r}

        skb1 = set()
        for bu in BUKRS_ALL:
            r = rd(conn, "SKB1", ["BUKRS", "SAKNR"], "BUKRS = '%s'" % bu)
            if r is None:
                unseen += 1
                continue
            skb1 |= {(x["BUKRS"], x["SAKNR"]) for x in r}

        print("  %-4s  SKA1 %5d   SKAT %5d   SKB1 %5d%s"
              % (sysid, len(ska1), len(skat), len(skb1),
                 "   [%d lecturas fallidas]" % unseen if unseen else ""))
        return {"SKA1": ska1, "SKAT": skat, "SKB1": skb1, "ERDAT": erdat}
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="20260630",
                    help="fecha de corte YYYYMMDD que se dice alineada")
    ap.add_argument("--systems", default="D01,V01")
    a = ap.parse_args()
    targets = [s.strip().upper() for s in a.systems.split(",") if s.strip()]

    print("Alineacion GL master — chart %s. FUENTE P01 (read-only).\n" % KTOPL)
    src = snapshot("P01")
    snaps = {t: snapshot(t) for t in targets}

    for t in targets:
        s = snaps[t]
        print("\n" + "=" * 74)
        print("P01 -> %s" % t)
        print("=" * 74)
        for tbl in ("SKA1", "SKAT", "SKB1"):
            missing = src[tbl] - s[tbl]
            extra = s[tbl] - src[tbl]
            print("  %-5s  faltan en %s: %-5d   solo en %s: %d"
                  % (tbl, t, len(missing), t, len(extra)))

        missing = sorted(src["SKA1"] - s["SKA1"])
        if not missing:
            print("\n  SKA1 alineada al 100%.")
            continue

        # ---- el contraste con la fecha que se da por alineada
        after = [x for x in missing if (src["ERDAT"].get(x) or "") > a.since]
        before = [x for x in missing if (src["ERDAT"].get(x) or "") <= a.since]
        print("\n  De las %d cuentas que faltan en %s:" % (len(missing), t))
        print("    creadas DESPUES de %s : %3d  -> coherente con 'alineado a esa fecha'"
              % (a.since, len(after)))
        print("    creadas ANTES o el   %s : %3d  -> %s"
              % (a.since, len(before),
                 "NO coherente: la alineacion nunca fue completa" if before else "ninguna, premisa OK"))
        for x in after:
            print("      + %s  ERDAT %s  (posterior al corte)" % (x, src["ERDAT"].get(x)))
        if before:
            print("\n    Las %d anteriores al corte, por anio de creacion:" % len(before))
            for yr, n in sorted(Counter((src["ERDAT"].get(x) or "????")[:4] for x in before).items()):
                print("      %s: %d" % (yr, n))
            for x in before[:40]:
                print("      ! %s  ERDAT %s" % (x, src["ERDAT"].get(x)))
            if len(before) > 40:
                print("      ... y %d mas" % (len(before) - 40))
    print("\nNada escrito. Solo lectura.")


if __name__ == "__main__":
    sys.exit(main())
