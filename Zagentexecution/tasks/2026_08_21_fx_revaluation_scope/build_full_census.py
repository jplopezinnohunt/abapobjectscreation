"""
build_full_census.py — CENSO COMPLETO de la revaluacion FX de una sociedad, en Excel.

Sin filtros: TODAS las cuentas de balance del plan, esten dentro o fuera de una variante, tengan
o no divisa, bloqueadas o no. La idea es control total en una sola hoja: para cada cuenta se ve
donde se presenta, quien la revalua, de que moneda es, cuanto tiene, si hay algo que revaluar y
si esta bloqueada.

Nace de la sesion 102: las tablas anteriores filtraban por "tiene divisa hoy" y eso, leido como
censo, engana — de la posicion 1.1.2.1 solo aparecia una cuenta de ocho.

Columnas, en el orden pedido: posicion FS10 -> variante -> cuenta -> el resto.

SOLO LECTURA. La exposicion se pregunta cuenta a cuenta a BSIS (una tabla de 3,3 M de filas no
se deja leer entera), asi que la corrida tarda unos minutos.

Uso:
    python build_full_census.py [--bukrs UNES] [--out <fichero.xlsx>]
"""
import argparse
import collections
import os
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "quality_checks"))
from rfc_helpers import get_connection                                   # noqa: E402
from ob09_vs_variant_check import parse, rd, variant_selection, PROGRAM  # noqa: E402
from openpyxl import Workbook                                            # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill                 # noqa: E402
from openpyxl.utils import get_column_letter                             # noqa: E402

HDR = PatternFill("solid", fgColor="08305F")
RED = PatternFill("solid", fgColor="FADDE1")
AMB = PatternFill("solid", fgColor="FFECCC")
GRN = PatternFill("solid", fgColor="E3F5EC")
GRY = PatternFill("solid", fgColor="EEF1F5")


def num(s):
    s = (s or "").strip()
    return 0.0 if not s else (-float(s[:-1]) if s.endswith("-") else float(s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="UNES")
    ap.add_argument("--ktopl", default="UNES")
    ap.add_argument("--versn", default="FS10")
    ap.add_argument("--year", default="2026")
    ap.add_argument("--out", default=os.path.join(HERE, "fx_revaluation_full_census_UNES.xlsx"))
    a = ap.parse_args()

    c = get_connection("P01")
    try:
        variants = sorted({r["VARIANT"] for r in
                           rd(c, "VARID", ["VARIANT"], "REPORT = '%s'" % PROGRAM)
                           if r["VARIANT"].startswith(a.bukrs)})
        vtext = {r["VARIANT"]: r.get("VTEXT") for r in
                 rd(c, "VARIT", ["REPORT", "VARIANT", "VTEXT"], "REPORT = '%s'" % PROGRAM)}
        sel = {v: variant_selection(c, v) for v in variants}
        ska1 = {r["SAKNR"]: r for r in rd(c, "SKA1", ["SAKNR", "XBILK"],
                                          "KTOPL = '%s'" % a.ktopl)}
        skb1 = {r["SAKNR"]: r for r in rd(c, "SKB1", ["SAKNR", "XSPEB", "MITKZ", "WAERS",
                                                      "XOPVW"], "BUKRS = '%s'" % a.bukrs)}
        txt = {r["SAKNR"]: r["TXT50"] for r in
               rd(c, "SKAT", ["SAKNR", "TXT50"], "KTOPL = '%s' AND SPRAS = 'E'" % a.ktopl)}
        qt = {r["ERGSL"]: r["TXT45"] for r in
              rd(c, "FAGL_011QT", ["VERSN", "ERGSL", "TXT45", "SPRAS"],
                 "VERSN = '%s' AND SPRAS = 'E'" % a.versn)}
        zc = rd(c, "FAGL_011ZC", ["ERGSL", "VONKT", "BISKT"],
                "KTOPL = '%s' AND VERSN = '%s'" % (a.ktopl, a.versn))
        t030h = {r["HKONT"] for r in rd(c, "T030H", ["HKONT"],
                                        "KTOPL = '%s' AND CURTP = '10'" % a.ktopl)}
        local = next((r["WAERS"] for r in rd(c, "T001", ["BUKRS", "WAERS"],
                                             "BUKRS = '%s'" % a.bukrs)), "USD")
        iv = [(r["VONKT"].rjust(10, "0"), (r["BISKT"] or r["VONKT"]).rjust(10, "0"), r["ERGSL"])
              for r in zc]
        cols = ["RACCT", "HSLVT"] + ["HSL%02d" % i for i in range(1, 13)]
        bal = {}
        for r in rd(c, "GLT0", cols, "BUKRS = '%s' AND RYEAR = '%s'" % (a.bukrs, a.year)):
            v = sum(num(r.get(k)) for k in cols[1:])
            if abs(v) > 0.005:
                bal[r["RACCT"]] = bal.get(r["RACCT"], 0.0) + v

        todas = sorted(x for x in skb1 if ska1.get(x, {}).get("XBILK") == "X")
        activas = [x for x in todas if skb1[x].get("XSPEB") != "X"]

        def pos(x):
            h = [e for lo, hi, e in iv if lo <= x <= hi]
            return sorted(set(h))[0] if h else ""

        def field(x):
            return "AKONTO" if (skb1[x].get("MITKZ") or "") else "SKONTO"

        member = collections.defaultdict(list)
        excl = collections.defaultdict(list)
        for v in variants:
            for f in ("SKONTO", "AKONTO"):
                s = sel[v][f]
                pool = [x for x in todas if field(x) == f]
                ex = {x for x in pool
                      if x in s["exc"] or any(lo <= x <= hi for lo, hi in s["rex"])}
                if not s["inc"] and not s["rin"] and (s["exc"] or s["rex"]):
                    keep = set(pool) - ex
                else:
                    keep = {x for x in pool
                            if (x in s["inc"] or any(lo <= x <= hi for lo, hi in s["rin"]))
                            and x not in ex}
                for x in keep:
                    member[x].append(v)
                for x in ex:
                    excl[x].append(v)

        print("midiendo divisa abierta cuenta a cuenta en %d cuentas activas..." % len(activas))
        fc = {}
        for i, x in enumerate(activas, 1):
            try:
                rows = parse(c.call("RFC_READ_TABLE", QUERY_TABLE="BSIS", DELIMITER="|",
                                    FIELDS=[{"FIELDNAME": y} for y in
                                            ("WAERS", "WRBTR", "DMBTR", "SHKZG")],
                                    OPTIONS=[{"TEXT": "BUKRS = '%s' AND HKONT = '%s'"
                                              % (a.bukrs, x)}], ROWCOUNT=0))
            except Exception:
                continue
            d, eq = {}, 0.0
            for r in rows:
                if r["WAERS"] and r["WAERS"] != local:
                    sg = -1 if r["SHKZG"] == "H" else 1
                    d[r["WAERS"]] = d.get(r["WAERS"], 0.0) + sg * num(r["WRBTR"])
                    eq += sg * num(r["DMBTR"])
            d = {k: v for k, v in d.items() if abs(v) > 0.005}
            if d:
                fc[x] = (d, eq)
            if i % 150 == 0:
                print("   %d/%d" % (i, len(activas)), flush=True)
    finally:
        c.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Full census"
    head = ["FS10 position", "Position text", "F.05 variant", "G/L account", "Description",
            "Account currency", "Currency is fixed?", "Managed as", "Blocked?",
            "Balance %s (%s)" % (a.year, local), "Anything to revalue?", "Open FX",
            "FX in %s" % local, "OB09 (T030H)", "Verdict"]
    ws.append(head)
    for x in sorted(todas, key=lambda z: (pos(z), ", ".join(member[z]), z)):
        r = skb1[x]
        blocked = r.get("XSPEB") == "X"
        vs = ", ".join(sorted(member[x]))
        d, eq = fc.get(x, ({}, 0.0))
        fixed = bool(r.get("WAERS")) and r["WAERS"] != local
        if blocked:
            verdict = "Blocked - out of scope"
        elif d and not vs:
            verdict = "GAP - FX open, no variant"
        elif vs:
            verdict = "Revalued"
        elif x in t030h:
            verdict = "Latent - OB09 set, no variant, no FX today"
        elif excl[x]:
            verdict = "Excluded on purpose (%s)" % ", ".join(sorted(excl[x]))
        else:
            verdict = "Out - nothing to revalue"
        ws.append([pos(x), qt.get(pos(x), ""), vs or "NONE", x, txt.get(x, ""),
                   r.get("WAERS") or "", "YES" if fixed else "no",
                   "Open items" if r.get("XOPVW") == "X" else "Balance",
                   "YES" if blocked else "", round(bal.get(x, 0.0), 2),
                   "YES" if d else "no",
                   " | ".join("%s %s" % (k, "{:,.0f}".format(v)) for k, v in sorted(d.items())),
                   round(eq, 2) if eq else None,
                   "YES" if x in t030h else "", verdict])
        i = ws.max_row
        fill = (GRY if blocked else RED if verdict.startswith("GAP") else
                AMB if verdict.startswith("Latent") else GRN if vs else None)
        for cn in range(1, len(head) + 1):
            if fill:
                ws.cell(row=i, column=cn).fill = fill
            if cn in (10, 13):
                ws.cell(row=i, column=cn).number_format = "#,##0"
    for cell in ws[1]:
        cell.fill = HDR
        cell.font = Font(color="FFFFFF", bold=True, size=10)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = "A1:%s%d" % (get_column_letter(len(head)), ws.max_row)
    for j, w in enumerate([13, 26, 17, 13, 40, 12, 12, 11, 9, 17, 12, 34, 15, 10, 34], 1):
        ws.column_dimensions[get_column_letter(j)].width = w

    ws2 = wb.create_sheet("By position")
    ws2.append(["FS10 position", "Position text", "Accounts", "Revalued", "Not revalued",
                "Blocked", "With FX open", "GAPS (FX + no variant)", "Balance (%s)" % local,
                "Variants working this position"])
    for p in sorted({pos(x) for x in todas}):
        g = [x for x in todas if pos(x) == p]
        act = [x for x in g if skb1[x].get("XSPEB") != "X"]
        inv = [x for x in act if member[x]]
        gaps = [x for x in act if x in fc and not member[x]]
        ws2.append([p, qt.get(p, ""), len(g), len(inv), len(act) - len(inv),
                    len(g) - len(act), len([x for x in act if x in fc]), len(gaps),
                    round(sum(bal.get(x, 0.0) for x in g), 2),
                    ", ".join(sorted({v for x in inv for v in member[x]})) or "NONE"])
        i = ws2.max_row
        for cn in range(1, 11):
            if gaps:
                ws2.cell(row=i, column=cn).fill = RED
            elif act and not inv:
                ws2.cell(row=i, column=cn).fill = AMB
            if cn == 9:
                ws2.cell(row=i, column=cn).number_format = "#,##0"
    for cell in ws2[1]:
        cell.fill = HDR
        cell.font = Font(color="FFFFFF", bold=True, size=10)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws2.freeze_panes = "A2"
    for j, w in enumerate([13, 30, 10, 10, 13, 9, 12, 14, 18, 34], 1):
        ws2.column_dimensions[get_column_letter(j)].width = w

    wb.save(a.out)
    gaps = [x for x in activas if x in fc and not member[x]]
    print("\nescrito: %s" % a.out)
    print("  %d cuentas de balance (%d activas, %d bloqueadas) · %d con divisa abierta · %d GAPS"
          % (len(todas), len(activas), len(todas) - len(activas), len(fc), len(gaps)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
