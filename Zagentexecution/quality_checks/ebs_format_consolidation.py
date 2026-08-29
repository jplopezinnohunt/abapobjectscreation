# -*- coding: utf-8 -*-
"""ebs_format_consolidation.py — ¿cuantos MODELOS de extracto sostenemos, y cuantos harian falta?

Un extracto no se procesa "en general": se procesa segun un GRUPO DE FORMATO (T028B.VGTYP),
y cada grupo arrastra su propio juego de reglas de contabilizacion (T028G: codigo externo del
banco -> regla + algoritmo). Ese juego es el MODELO: lo que cuesta mantener, lo que hay que
probar cuando se toca, y lo que hay que replicar cuando entra un banco nuevo.

La pregunta de oportunidad es simple y nadie la habia hecho: **cuantos bancos comparten
modelo y cuantos tienen uno para ellos solos.** Un formato usado por un unico banco es un
modelo entero mantenido para una cuenta; si su juego de reglas se parece al de un formato
grande, es candidato a consolidar. Si no se parece, es una excepcion legitima y conviene
saber por que.

Lo que este instrumento NO hace: decidir la consolidacion. Mide el reparto, el coste en
reglas y el PARECIDO entre juegos de reglas, y deja la decision con evidencia delante.

Solo LECTURA. P01, ventana 2025-2026.
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",
    "needs": "rfc_p01",
    "what": "cuantos modelos de extracto (VGTYP) se sostienen, cuantos bancos y cuentas cubre "
            "cada uno, cuantas reglas cuesta, y cuales son huerfanos o casi iguales a otro",
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


def _y(*c):
    return " AND ".join(x for x in c if x)


def cerrada(t):
    return any(m in (t or "").upper() for m in MARCAS_CIERRE)


def rd(conn, tab, fields, where="", n=0):
    """Delega en el lector del Golden. La firma NO cambia a proposito: asi el port
    es cambiar DE DONDE se lee, no COMO se interpreta, y ni una llamada se toca."""
    return _G.rd(conn, tab, fields, where, n)


def jaccard(a, b):
    """Parecido entre dos juegos de reglas. Se compara el CONJUNTO de (codigo externo ->
    regla + algoritmo), que es lo que de verdad define el modelo. Comparar solo los codigos
    externos daria parecidos altisimos y falsos: casi todos los bancos mandan NTRF."""
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="UNES")
    ap.add_argument("--system", default="P01")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    # MINERIA -> GOLDEN, nunca P01. Un minero lee mucho y correlaciona; RFC solo deja
    # leer estrecho. Si falta dato, exige() se NIEGA y manda al paso de EXTRACCION.
    conn = _G.abrir()
    _SELLO = _G.exige(conn, ['BNKA', 'FEBKO', 'T012', 'T012K', 'T012T', 'T028B', 'T028G'])
    # el SELLO dice DE QUE FOTO sale todo lo que este minero publique. Se imprime
    # y se mete en el limite de sus hallazgos: una conclusion sobre una foto vale,
    # lo que no vale es no decir de cuando es la foto.
    print(_SELLO)
    w = ("BUKRS = '%s'" % a.bukrs) if a.bukrs else ""

    t012k = rd(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "WAERS", "HKONT"], w)
    t012 = {(r["BUKRS"], r["HBKID"]): r["BANKL"] for r in
            rd(conn, "T012", ["BUKRS", "HBKID", "BANKS", "BANKL"], w)}
    txt = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r["TEXT1"] for r in
           rd(conn, "T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"], _y(w, "SPRAS = 'E'"))}
    bnka = {r["BANKL"]: r["BANKA"] for r in rd(conn, "BNKA", ["BANKS", "BANKL", "BANKA"], "")}

    t028b = {}
    for r in rd(conn, "T028B", ["BANKL", "KTONR", "VGTYP", "BNKKO", "BUKRS"], ""):
        t028b[(r["BANKL"], r["KTONR"])] = r

    # el MODELO: juego de reglas por grupo de formato
    reglas = collections.defaultdict(set)
    for r in rd(conn, "T028G", ["VGTYP", "VGEXT", "VOZPM", "VGINT", "INTAG"], ""):
        reglas[r["VGTYP"]].add((r["VGEXT"], r["VOZPM"], r["VGINT"], r["INTAG"]))

    hoy = datetime.datetime.now().strftime("%Y%m%d")
    ext = collections.Counter()
    for r in rd(conn, "FEBKO", ["BUKRS", "HBKID", "HKTID", "AZDAT"], _y(w, "AZDAT >= '20250101'")):
        if r["AZDAT"] <= hoy:
            ext[(r["BUKRS"], r["HBKID"], r["HKTID"])] += 1

    filas = []
    for r in t012k:
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        t = txt.get(k, "")
        if cerrada(t):
            continue
        bl = t012.get((r["BUKRS"], r["HBKID"]), "")
        row = t028b.get((bl, r["BANKN"]))
        filas.append({
            "cuenta": "%s/%s-%s" % k, "hbkid": r["HBKID"], "bankl": bl,
            "banco": bnka.get(bl, ""), "waers": r["WAERS"], "texto": t,
            "vgtyp": (row or {}).get("VGTYP", "(sin T028B)"),
            "extractos": ext.get(k, 0),
        })

    print("\ncuentas VIVAS de %s: %d · con extracto en 2025-2026: %d"
          % (a.bukrs or "TODAS", len(filas), sum(1 for f in filas if f["extractos"])))

    # ---- reparto por modelo -------------------------------------------------
    print("\n" + "=" * 104)
    print("MODELOS DE EXTRACTO EN USO — cuantos bancos comparten cada uno")
    print("=" * 104)
    print("  %-12s %7s %7s %9s %7s  %s" %
          ("formato", "bancos", "cuentas", "extractos", "reglas", "lectura"))
    porv = collections.defaultdict(list)
    for f in filas:
        porv[f["vgtyp"]].append(f)
    tot_reglas = 0
    for v, g in sorted(porv.items(), key=lambda x: -len(x[1])):
        bancos = {f["hbkid"] for f in g}
        nr = len(reglas.get(v, ()))
        if v != "(sin T028B)":
            tot_reglas += nr
        lectura = ("COMPARTIDO" if len(bancos) > 3
                   else "de UN SOLO banco" if len(bancos) == 1 else "de pocos bancos")
        print("  %-12s %7d %7d %9d %7d  %s"
              % (v, len(bancos), len(g), sum(f["extractos"] for f in g), nr, lectura))
    print("\n  reglas de contabilizacion mantenidas en total: %d" % tot_reglas)

    # ---- los huerfanos ------------------------------------------------------
    print("\n" + "=" * 104)
    print("MODELOS DE UN SOLO BANCO — cada uno es un modelo entero para una sola entidad")
    print("=" * 104)
    solos = [(v, g) for v, g in porv.items()
             if v != "(sin T028B)" and len({f["hbkid"] for f in g}) == 1]
    if not solos:
        print("  ninguno")
    for v, g in sorted(solos, key=lambda x: -sum(f["extractos"] for f in x[1])):
        b = g[0]
        print("\n  --- %s : %s (%s) · %d cuentas · %d extractos · %d reglas ---"
              % (v, b["hbkid"], (b["banco"] or "")[:30], len(g),
                 sum(f["extractos"] for f in g), len(reglas.get(v, ()))))
        for f in g:
            print("       %-22s %-4s ext=%-6d %s" % (f["cuenta"], f["waers"], f["extractos"],
                                                     (f["texto"] or "")[:36]))
        # ¿a que otro modelo se parece?
        cerc = sorted(((jaccard(reglas.get(v, set()), reglas.get(o, set())), o)
                       for o in porv if o not in ("(sin T028B)", v)), reverse=True)[:3]
        print("       parecido de su juego de reglas: %s"
              % ", ".join("%s %.0f%%" % (o, s * 100) for s, o in cerc))

    # ---- matriz de parecido entre los modelos en uso -----------------------
    print("\n" + "=" * 104)
    print("PARECIDO ENTRE MODELOS (Jaccard sobre el juego codigo->regla+algoritmo)")
    print("=" * 104)
    vs = [v for v in porv if v != "(sin T028B)" and reglas.get(v)]
    vs.sort(key=lambda v: -len(porv[v]))
    print("  %-12s %s" % ("", " ".join("%-9s" % v[:9] for v in vs)))
    for x in vs:
        cel = []
        for y in vs:
            s = 100 * jaccard(reglas.get(x, set()), reglas.get(y, set()))
            cel.append("%-9s" % ("-" if x == y else "%.0f%%" % s))
        print("  %-12s %s" % (x, " ".join(cel)))
    print("\n  Un parecido alto entre un modelo grande y uno huerfano es la oportunidad:")
    print("  el huerfano se podria absorber. Un parecido bajo es una excepcion legitima —")
    print("  y entonces lo que hace falta es saber POR QUE, no consolidarla.")


    # ---- LO QUE ESTE MINERO ENCUENTRA -------------------------------------------
    from _hallazgos import Hallazgos
    h = Hallazgos("ebs_format_consolidation",
                  denominador="%d cuentas VIVAS de %s, %d con extracto en la ventana"
                              % (len(filas), a.bukrs or "todas",
                                 sum(1 for f in filas if f["extractos"])))
    if solos:
        nr = sum(len(reglas.get(v, ())) for v, _ in solos)
        nc = sum(len(g) for _, g in solos)
        h.oportunidad("Modelos de extracto que existen para UN SOLO banco: cada uno es un modelo "
                      "entero -- con su prueba y su riesgo -- sosteniendo muy pocas cuentas",
                      tamano="%d modelos, %d reglas para %d cuentas, sobre un total de %d reglas"
                             % (len(solos), nr, nc, tot_reglas),
                      evidencia="T028B agrupado por VGTYP y T028G contado por modelo",
                      limite=("parecido alto NO significa consolidable: absorber uno dentro de "
                              "otro puede CAMBIAR su algoritmo y con el la contabilizacion"),
                      accion="mirar primero los pares con parecido alto, no los mas pequenos")
    sin_modelo = [f for f in filas if f["vgtyp"] == "(sin modelo)" and f["extractos"] > 0]
    if sin_modelo:
        h.riesgo("Cuentas que RECIBEN extracto y no tienen modelo de formato asignado",
                 tamano="%d cuenta(s), %d extractos: %s"
                        % (len(sin_modelo), sum(f["extractos"] for f in sin_modelo),
                           ", ".join(f["cuenta"] for f in sin_modelo[:5])),
                 evidencia="sin fila en T028B para su clave de banco y numero de cuenta",
                 limite="el extracto pudo entrar antes de que el numero cambiara",
                 accion="es la firma exacta del defecto de INC-000013624")
    h.emitir()

    if a.json:
        json.dump({"cuentas": filas,
                   "reglas_por_modelo": {k: len(v) for k, v in reglas.items()}},
                  open(a.json, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("\nescrito %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
