"""
fx_revaluation_peer_check.py — SOLO LECTURA. ¿QUE CUENTA NO ESTA EN UNA VARIANTE DE F.05
TENIENDO A SUS IGUALES DENTRO?

EL METODO, que es lo que este check aporta
    Una variante no es un filtro tecnico: se crea para AGRUPAR ELEMENTOS QUE ALGUIEN CONSIDERA
    SIMILARES. Por eso leerla es explorar comportamiento, y por eso el defecto no se define
    contra una regla externa sino contra los IGUALES:

        La incoherencia no es "no estar". Es NO ESTAR CUANDO TUS IGUALES SI ESTAN.

    Contar "cuentas de balance fuera de toda variante" no significa nada: son 497 en UNES y casi
    todas estan fuera con razon. Lo que significa algo es la cuenta que falta en un grupo que su
    variante SI trabaja.

LOS CUATRO PASOS
    1. MATERIALIZAR la pertenencia de cada variante: resolver rangos, aplicar exclusiones, y
       elegir el campo correcto por cuenta (AKONTO si SKB1-MITKZ esta lleno, SKONTO si no).
    2. DERIVAR los grupos que cada variante trabaja, DE SU PERTENENCIA REAL, en DOS EJES:
         * posicion del balance (FS10)  -- vale para las variantes por RANGO y para las de submayor
         * bloque de numeracion de cuenta -- vale para las variantes por LISTA, cuyos miembros
           estan repartidos entre posiciones (UNES_DEPOSIT toca 5 posiciones distintas)
       Hacen falta LOS DOS. Con solo la posicion, 4041011 se cae: su posicion 1.1.2.1 no la ocupa
       ningun miembro de UNES_DEPOSIT, pero su bloque 404101 tiene cuatro miembros dentro.
    3. CANDIDATA = cuenta activa, con partidas abiertas en divisa, fuera de toda variante, NO
       excluida explicitamente, y cuyo grupo (por cualquiera de los dos ejes) lo trabaja alguna
       variante. Se le asigna esa variante.
    4. RESTO = con divisa pero sin ningun grupo trabajado por nadie. Eso NO es un hueco de
       revaluacion: es una pregunta de COMPENSACION o de politica contable. No lo mezcles.

TRES TRAMPAS QUE ESTE CHECK EVITA (las tres costaron un falso positivo el 2026-08-21)
    * Una seleccion con SOLO exclusiones significa TODO MENOS ESO, no "nada".
    * SKONTO y AKONTO son universos distintos: mezclarlos deja fuera a todas las asociadas.
    * Una cuenta EXCLUIDA a proposito es una decision, no un olvido. Nunca se marca.

Solo LECTURA. Reglas: feedback_a_selection_with_only_exclusions_means_everything_else.

Uso:
    python fx_revaluation_peer_check.py                 # P01 / UNES
    python fx_revaluation_peer_check.py --json out.json
Salida: exit 1 si hay candidatas con divisa abierta.
"""

QUALITY_CHECK = {
    "tier": "live",   # gate | live | analysis | quarantined
    "needs": "rfc_p01",
    "what": "cuentas fuera de variante TENIENDO iguales dentro de su posicion de balance",
    "args": "[--bukrs UNES]",
}

import argparse
import collections
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
sys.path.insert(0, HERE)
from rfc_helpers import get_connection                                  # noqa: E402
from ob09_vs_variant_check import parse, rd, variant_selection, PROGRAM  # noqa: E402


def num(s):
    s = (s or "").strip()
    return 0.0 if not s else (-float(s[:-1]) if s.endswith("-") else float(s))


def money(v):
    return "{:,.0f}".format(v).replace(",", " ") if abs(v) > 0.5 else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default="P01")
    ap.add_argument("--bukrs", default="UNES")
    ap.add_argument("--ktopl", default="UNES")
    ap.add_argument("--versn", default="FS10")
    ap.add_argument("--block", type=int, default=6,
                    help="digitos significativos del bloque de numeracion (por defecto 6)")
    ap.add_argument("--json", default="", help="volcar el resultado a un fichero")
    a = ap.parse_args()

    c = get_connection(a.system)
    try:
        variants = sorted({r["VARIANT"] for r in
                           rd(c, "VARID", ["VARIANT"], "REPORT = '%s'" % PROGRAM)
                           if r["VARIANT"].startswith(a.bukrs)})
        if not variants:
            print("ABORTA: %s no tiene variantes de %s." % (a.bukrs, PROGRAM))
            return 2
        vtext = {r["VARIANT"]: r.get("VTEXT") for r in
                 rd(c, "VARIT", ["REPORT", "VARIANT", "VTEXT"], "REPORT = '%s'" % PROGRAM)}
        sel = {v: variant_selection(c, v) for v in variants}
        ska1 = {r["SAKNR"]: r for r in rd(c, "SKA1", ["SAKNR", "XBILK"],
                                          "KTOPL = '%s'" % a.ktopl)}
        skb1 = {r["SAKNR"]: r for r in rd(c, "SKB1", ["SAKNR", "XSPEB", "MITKZ"],
                                          "BUKRS = '%s'" % a.bukrs)}
        txt = {r["SAKNR"]: r["TXT50"] for r in
               rd(c, "SKAT", ["SAKNR", "TXT50"], "KTOPL = '%s' AND SPRAS = 'E'" % a.ktopl)}
        qt = {r["ERGSL"]: r["TXT45"] for r in
              rd(c, "FAGL_011QT", ["VERSN", "ERGSL", "TXT45", "SPRAS"],
                 "VERSN = '%s' AND SPRAS = 'E'" % a.versn)}
        zc = rd(c, "FAGL_011ZC", ["ERGSL", "VONKT", "BISKT"],
                "KTOPL = '%s' AND VERSN = '%s'" % (a.ktopl, a.versn))
        t030h = {r["HKONT"] for r in rd(c, "T030H", ["HKONT"],
                                        "KTOPL = '%s' AND CURTP = '10'" % a.ktopl)}
        iv = [(r["VONKT"].rjust(10, "0"), (r["BISKT"] or r["VONKT"]).rjust(10, "0"), r["ERGSL"])
              for r in zc]
        local = next((r["WAERS"] for r in rd(c, "T001", ["BUKRS", "WAERS"],
                                             "BUKRS = '%s'" % a.bukrs)), "USD")

        act = [x for x in skb1 if ska1.get(x, {}).get("XBILK") == "X"
               and skb1[x].get("XSPEB") != "X"]

        def pos(x):
            h = [e for lo, hi, e in iv if lo <= x <= hi]
            return sorted(set(h))[0] if h else "(sin posicion)"

        def blk(x):
            """Bloque de numeracion: los N digitos significativos, ceros de relleno aparte.
            Con block=6, la cuenta 0004041011 da el bloque 404101 -- el que comparte con
            4041013/17/18/19, que si estan en UNES_DEPOSIT."""
            sig = x.lstrip("0")
            return sig[:a.block].rjust(a.block, "0")

        def field(x):
            return "AKONTO" if (skb1[x].get("MITKZ") or "") else "SKONTO"

        # ---- 1. pertenencia materializada, con exclusiones
        members, excluded = {}, {}
        for v in variants:
            mem, exc = set(), set()
            for f in ("SKONTO", "AKONTO"):
                s = sel[v][f]
                pool = [x for x in act if field(x) == f]
                ex = {x for x in pool
                      if x in s["exc"] or any(lo <= x <= hi for lo, hi in s["rex"])}
                if not s["inc"] and not s["rin"] and (s["exc"] or s["rex"]):
                    mem |= set(pool) - ex           # solo exclusiones = TODAS menos esas
                else:
                    mem |= {x for x in pool
                            if (x in s["inc"] or any(lo <= x <= hi for lo, hi in s["rin"]))
                            and x not in ex}
                exc |= ex
            members[v], excluded[v] = mem, exc
        inside = set().union(*members.values())
        excl_all = set().union(*excluded.values())

        # ---- 2. grupos por variante, en los DOS ejes
        gpos = {v: {pos(x) for x in members[v]} for v in variants}
        gblk = {v: {blk(x) for x in members[v]} for v in variants}

        print("ALCANCE POR IGUALES — %s / %s · balance %s\n" % (a.system, a.bukrs, a.versn))
        print("  cuentas de balance activas: %d · dentro de alguna variante: %d"
              % (len(act), len(inside)))
        for v in variants:
            print("  %-16s %-38s %4d miembros · %2d exclusiones · %d posiciones · %d bloques"
                  % (v, (vtext.get(v) or "")[:38], len(members[v]), len(excluded[v]),
                     len(gpos[v]), len(gblk[v])))

        # ---- 3. exposicion abierta en divisa, solo de las que estan fuera
        fuera = [x for x in act if x not in inside and x not in excl_all]
        print("\n  fuera de toda variante y no excluidas: %d — preguntando a BSIS por divisa..."
              % len(fuera))
        fc = {}
        for x in fuera:
            try:
                rows = parse(c.call("RFC_READ_TABLE", QUERY_TABLE="BSIS", DELIMITER="|",
                                    FIELDS=[{"FIELDNAME": y} for y in
                                            ("WAERS", "WRBTR", "DMBTR", "SHKZG")],
                                    OPTIONS=[{"TEXT": "BUKRS = '%s' AND HKONT = '%s'"
                                              % (a.bukrs, x)}], ROWCOUNT=0))
            except Exception as e:
                if "TABLE_WITHOUT_DATA" not in str(e):
                    print("     [!] BSIS %s no legible" % x)
                continue
            d, eq = {}, 0.0
            for r in rows:
                if r["WAERS"] and r["WAERS"] != local:
                    sg = -1 if r["SHKZG"] == "H" else 1
                    d[r["WAERS"]] = d.get(r["WAERS"], 0.0) + sg * num(r["WRBTR"])
                    eq += sg * num(r["DMBTR"])
            d = {k: round(v, 2) for k, v in d.items() if abs(v) > 0.005}
            if d:
                fc[x] = {"fc": d, "usd": round(eq, 2)}
    finally:
        c.close()

    # ---- 4. clasificar
    cand, resto = [], []
    for x in sorted(fc):
        via = None
        for v in variants:
            if pos(x) in gpos[v]:
                via = (v, "posicion %s" % pos(x)); break
            if blk(x) in gblk[v]:
                via = (v, "bloque %s" % blk(x).lstrip("0")); break
        (cand if via else resto).append((x, via))

    print("\n" + "=" * 100)
    print("CANDIDATAS — con divisa abierta, fuera de variante, y con IGUALES dentro: %d · %s %s"
          % (len(cand), money(sum(fc[x]["usd"] for x, _ in cand)), local))
    print("=" * 100)
    byv = collections.defaultdict(list)
    for x, via in cand:
        byv[via[0]].append((x, via[1]))
    for v in variants:
        if not byv[v]:
            continue
        print("\n  -> %s   %d cuentas · %s %s"
              % (v, len(byv[v]), money(sum(fc[x]["usd"] for x, _ in byv[v])), local))
        for x, por in sorted(byv[v], key=lambda z: -abs(fc[z[0]]["usd"])):
            print("     %-11s %-40s por %-18s %-26s %s"
                  % (x, txt.get(x, "")[:40], por,
                     " ".join("%s %s" % (k, money(val))
                              for k, val in list(fc[x]["fc"].items())[:2])[:26],
                     "OB09" if x in t030h else ""))

    print("\n" + "=" * 100)
    print("RESTO — con divisa pero sin ningun grupo que alguna variante trabaje: %d · %s %s"
          % (len(resto), money(sum(fc[x]["usd"] for x, _ in resto)), local))
    print("  NO son huecos de revaluacion: son preguntas de COMPENSACION o de politica contable.")
    print("=" * 100)
    for x, _ in sorted(resto, key=lambda z: -abs(fc[z[0]]["usd"])):
        print("     %-11s %-40s %-12s %s"
              % (x, txt.get(x, "")[:40], pos(x),
                 " ".join("%s %s" % (k, money(v)) for k, v in list(fc[x]["fc"].items())[:2])[:30]))

    n_exc = len([x for x in excl_all if x in fc])
    print("\n  excluidas a proposito y con divisa (NO se marcan, excluir es una decision): %d" % n_exc)
    if a.json:
        json.dump({"candidatas": [{"acct": x, "variante": v[0], "por": v[1],
                                   "fc": fc[x]["fc"], "usd": fc[x]["usd"],
                                   "ob09": x in t030h, "texto": txt.get(x, "")}
                                  for x, v in cand],
                   "resto": [{"acct": x, "posicion": pos(x), "fc": fc[x]["fc"],
                              "usd": fc[x]["usd"], "texto": txt.get(x, "")} for x, _ in resto]},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  json -> %s" % a.json)
    return 1 if cand else 0


if __name__ == "__main__":
    sys.exit(main())
