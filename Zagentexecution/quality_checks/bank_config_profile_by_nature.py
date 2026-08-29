# -*- coding: utf-8 -*-
"""bank_config_profile_by_nature.py — QUE CONFIGURACION lleva de hecho cada NATURALEZA.

La lista de 12 pasos del alta de un banco casa es UNICA para todas las cuentas y se ramifica
por casillas de un formulario ("¿extracto electronico? si/no", "¿es banco pagador?"). O sea
que el alcance de la configuracion depende de lo que alguien marque en un Excel, no de lo
que la cuenta ES.

Este instrumento invierte la pregunta: en vez de decir que configuracion DEBERIA llevar cada
naturaleza, MIDE la que llevan las cuentas que ya existen y saca el perfil. Si las cuentas de
una naturaleza coinciden, eso es una regla que nadie habia escrito; si estan repartidas, es
DERIVA. No inventa el deber ser: ensena la distribucion y marca donde no hay consenso.

Solo LECTURA. Por defecto P01 / UNES, ventana 2025-2026.
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",
    "needs": "rfc_p01",
    "what": "que elementos de configuracion (extracto, pago, IBAN, revaluacion, balance, sets) "
            "lleva de hecho cada naturaleza de cuenta bancaria, para derivar el alcance del alta "
            "de la NATURALEZA en vez de un formulario",
    "args": "[--bukrs <soc>] [--system P01] [--json <fichero>]",
}

import argparse
import collections
import datetime
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
sys.path.insert(0, HERE)
import _golden as _G  # noqa: E402

MARCAS_CIERRE = ("CLOSED", "CLOSE", "FERME", "CERRAD", "OBSOLET", "INACTIV",
                 "NOT USED", "DORMANT", "CANCEL")
MARCA_MANDATO = ("MANDATE", "PIMCO", "MORGAN", "RAMP", "IMIP", "PORTFOLIO", "CUSTOD")
MARCA_VISTA = ("AT SIGHT", "SAVINGS", "LIVRET", "DEPOSIT", "TERM")
MARCA_TRANSFER = ("TRANSFER", "TSF")
MARCA_OPS = ("GENERAL OPERATIONS", "GEN OPS", "GENERAL OP", "OPERATIONS")


def _y(*c):
    return " AND ".join(x for x in c if x)


def cerrada(t):
    return any(m in (t or "").upper() for m in MARCAS_CIERRE)


def rd(conn, tab, fields, where="", n=0):
    """Delega en el lector del Golden. La firma NO cambia a proposito: asi el port
    es cambiar DE DONDE se lee, no COMO se interpreta, y ni una llamada se toca."""
    return _G.rd(conn, tab, fields, where, n)


def naturaleza(texto, ysets):
    t = (texto or "").upper()
    if "SIGHT" in (ysets or ""):
        return "A_LA_VISTA"
    if any(m in t for m in MARCA_MANDATO):
        return "MANDATO_INVERSION"
    if any(m in t for m in MARCA_VISTA):
        return "A_LA_VISTA"
    if any(m in t for m in MARCA_OPS):
        return "OPERATIVA"
    if any(m in t for m in MARCA_TRANSFER):
        return "TRANSFERENCIA"
    return "SIN_CLASIFICAR"


ELEM = ["T028B", "T035D", "BNKN2", "IBAN", "PAGA_T042I", "OBA1", "FSV", "YBANK"]


def pct(g, e):
    v = [f[e] for f in g if f.get(e) is not None]
    return round(100.0 * sum(1 for x in v if x) / len(v)) if v else 0


def linea(nombre, g):
    cel = []
    for e in ELEM:
        p = pct(g, e)
        cel.append("%-10s" % ("%3d%%%s" % (p, "*" if 15 <= p <= 85 else " ")))
    return "  %-20s %5d  %s" % (nombre, len(g), " ".join(cel))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="", help="vacio = TODAS las sociedades")
    ap.add_argument("--system", default="P01")
    ap.add_argument("--desde", default="20250101")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    # MINERIA -> GOLDEN, nunca P01. Un minero lee mucho y correlaciona; RFC solo deja
    # leer estrecho. Si falta dato, exige() se NIEGA y manda al paso de EXTRACCION.
    conn = _G.abrir()
    _SELLO = _G.exige(conn, ['FAGL_011ZC', 'FEBKO', 'SETLEAF', 'T012', 'T012K', 'T012T', 'T028B', 'T030H', 'T035D', 'T042I', 'TIBAN'])
    # el SELLO dice DE QUE FOTO sale todo lo que este minero publique. Se imprime
    # y se mete en el limite de sus hallazgos: una conclusion sobre una foto vale,
    # lo que no vale es no decir de cuando es la foto.
    print(_SELLO)
    w = ("BUKRS = '%s'" % a.bukrs) if a.bukrs else ""

    t012k = rd(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BNKN2", "WAERS", "HKONT"], w)
    t012 = {(r["BUKRS"], r["HBKID"]): r["BANKL"] for r in
            rd(conn, "T012", ["BUKRS", "HBKID", "BANKS", "BANKL"], w)}
    txt = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r["TEXT1"] for r in
           rd(conn, "T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"], _y(w, "SPRAS = 'E'"))}

    t028b = {(r["BANKL"], r["KTONR"]) for r in rd(conn, "T028B", ["BANKL", "KTONR"], "")}
    t035d = {(r["BUKRS"], r["DISKB"]) for r in rd(conn, "T035D", ["BUKRS", "DISKB"], "")}
    iban = {r["BANKN"] for r in rd(conn, "TIBAN", ["BANKS", "BANKL", "BANKN"], "")}

    # T042I — determinacion de banco para el programa de pagos: si la cuenta esta ahi, PAGA
    paga = set()
    zlsch = collections.defaultdict(set)
    try:
        for r in rd(conn, "T042I", ["ZBUKR", "HBKID", "HKTID", "ZLSCH", "WAERS"], ""):
            paga.add((r["ZBUKR"], r["HBKID"], r["HKTID"]))
            zlsch[(r["ZBUKR"], r["HBKID"], r["HKTID"])].add(r["ZLSCH"])
    except Exception as e:
        print("  T042I -> %s" % str(e)[:90])

    # OBA1 / revaluacion: T030H. El campo de cuenta es HKONT, NO 'KONKO' -- esa tabla no
    # tiene KONKO. Con el campo equivocado la lectura no falla: devuelve 0 filas y el perfil
    # publica "OBA1 = 0% en TODAS las naturalezas", que es una respuesta segura y falsa.
    t030h = {r["HKONT"] for r in rd(conn, "T030H", ["KTOPL", "HKONT"], "", 0)}

    zc = rd(conn, "FAGL_011ZC", ["VERSN", "ERGSL", "VONKT", "BISKT"], "VERSN = 'FS10'", 0)
    leaf = rd(conn, "SETLEAF", ["SETNAME", "VALFROM"], "SETNAME LIKE 'YBANK%'")
    gl2set = collections.defaultdict(set)
    for r in leaf:
        if r["SETNAME"] in ("YBANK_ACCOUNTS_ALL", "YBANK_ACCOUNTS_HQ", "YBANK_ACCOUNTS_FO"):
            continue
        gl2set[r["VALFROM"].lstrip("0")].add(r["SETNAME"])

    hoy = datetime.datetime.now().strftime("%Y%m%d")
    can = collections.defaultdict(collections.Counter)
    for r in rd(conn, "FEBKO", ["BUKRS", "HBKID", "HKTID", "AZDAT", "EFART"],
                _y(w, "AZDAT >= '%s'" % a.desde)):
        if r["AZDAT"] <= hoy:
            can[(r["BUKRS"], r["HBKID"], r["HKTID"])][r["EFART"]] += 1

    def en_fsv(gl):
        g = gl.zfill(10)
        return any(x["VONKT"].zfill(10) <= g <= x["BISKT"].zfill(10) for x in zc)

    filas = []
    for r in t012k:
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        t = txt.get(k, "")
        if cerrada(t):
            continue
        bl = t012.get((r["BUKRS"], r["HBKID"]), "")
        gl = r["HKONT"]
        sub = ("00011" + gl[5:]) if len(gl) == 10 and gl.startswith("00010") else ""
        cc = can.get(k)
        canal = ("SIN_EXTRACTO" if not cc
                 else "ELECTRONICO" if cc.get("E") and not cc.get("M")
                 else "MANUAL" if cc.get("M") and not cc.get("E") else "MIXTO")
        ysets = ",".join(sorted(gl2set.get(gl.lstrip("0"), set())))
        filas.append({
            "cuenta": "%s/%s-%s" % k, "texto": t, "waers": r["WAERS"], "gl": gl,
            "naturaleza": naturaleza(t, ysets), "canal": canal, "ybank_set": ysets,
            "T028B": (bl, r["BANKN"]) in t028b,
            "T035D": any(d[0] == r["BUKRS"] and d[1].startswith(r["HBKID"]) for d in t035d),
            "BNKN2": bool(r["BNKN2"]),
            "IBAN": r["BANKN"] in iban,
            "PAGA_T042I": k in paga,
            "metodos": sorted(zlsch.get(k, set())),
            "OBA1": (gl in t030h) or (bool(sub) and sub in t030h),
            "FSV": en_fsv(gl),
            "YBANK": bool(ysets),
        })

    print("\ncuentas VIVAS analizadas: %d" % len(filas))
    cab = "  %-20s %5s  %s" % ("", "n", " ".join("%-10s" % e for e in ELEM))

    print("\n" + "=" * 100)
    print("PERFIL DE CONFIGURACION POR NATURALEZA  (% de cuentas que lo tienen)")
    print("=" * 100)
    print(cab)
    for nat in sorted({f["naturaleza"] for f in filas}):
        print(linea(nat, [f for f in filas if f["naturaleza"] == nat]))

    print("\n" + "=" * 100)
    print("PERFIL POR CANAL DE EXTRACTO")
    print("=" * 100)
    print(cab)
    for canal in ("ELECTRONICO", "MIXTO", "MANUAL", "SIN_EXTRACTO"):
        g = [f for f in filas if f["canal"] == canal]
        if g:
            print(linea(canal, g))
    print("\n  (* = entre 15% y 85%: las cuentas de ese grupo NO coinciden. O es una regla que")
    print("   nadie escribio, o es deriva. Las dos hay que resolverlas.)")

    print("\n" + "=" * 100)
    print("LOS METODOS DE PAGO QUE SE USAN, POR NATURALEZA")
    print("=" * 100)
    for nat in sorted({f["naturaleza"] for f in filas}):
        g = [f for f in filas if f["naturaleza"] == nat and f["metodos"]]
        m = collections.Counter(x for f in g for x in f["metodos"])
        print("  %-20s cuentas que pagan: %-4d metodos: %s"
              % (nat, len(g), dict(m.most_common(12)) or "-"))

    print("\n" + "=" * 100)
    print("LAS 4 DE MANDATO, ELEMENTO A ELEMENTO")
    print("=" * 100)
    for f in filas:
        if f["naturaleza"] == "MANDATO_INVERSION":
            print("  %-22s %s" % (f["cuenta"],
                                  " ".join("%s=%s" % (e, "SI" if f[e] else "no") for e in ELEM)))


    # ---- LO QUE ESTE MINERO ENCUENTRA -------------------------------------------
    from _hallazgos import Hallazgos
    h = Hallazgos("bank_config_profile_by_nature",
                  denominador="%d cuentas VIVAS de %s" % (len(filas), a.bukrs or "todas las sociedades"))
    # (5) DISCREPANCIA: grupos donde las cuentas de una misma naturaleza NO coinciden.
    # No es una regla rota: es que NO HAY regla, o hay deriva. Las dos hay que resolverlas.
    disc = []
    for nat in sorted({f["naturaleza"] for f in filas}):
        g = [f for f in filas if f["naturaleza"] == nat]
        for e in ELEM:
            p = pct(g, e)
            if 15 <= p <= 85 and len(g) >= 4:
                disc.append("%s/%s %d%%" % (nat, e, p))
    if disc:
        h.desafio("Cuentas de la MISMA naturaleza no coinciden en su configuracion: o es una "
                  "regla que nadie escribio, o es deriva",
                  tamano="%d combinaciones naturaleza x elemento sin consenso: %s"
                         % (len(disc), ", ".join(disc[:8])),
                  evidencia="porcentaje de cuentas del grupo que tienen el elemento",
                  limite="no se cual de las dos es sin preguntar: el dato no lo distingue",
                  quien_puede_contestar="Tesoreria / DBS: decidir si es regla o deriva")
    paga = [f for f in filas if f["PAGA_T042I"]]
    ops = [f for f in filas if f["naturaleza"] == "OPERATIVA"]
    if ops and paga:
        h.dato("La naturaleza YA PREDICE la configuracion de pago, aunque nadie la haya declarado",
               tamano="%d de %d OPERATIVAS estan en determinacion de banco; de las demas "
                      "naturalezas, %d" % (sum(1 for f in ops if f["PAGA_T042I"]), len(ops),
                                           len([f for f in paga if f["naturaleza"] != "OPERATIVA"])),
               evidencia="T042I frente a la naturaleza derivada",
               limite="correlacion medida, no regla declarada en el sistema",
               accion="es el argumento para declarar la naturaleza (PMO H144)")
    h.emitir()

    if a.json:
        json.dump(filas, open(a.json, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("\nescrito %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
