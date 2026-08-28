# -*- coding: utf-8 -*-
"""bank_account_nature_model.py — SOCIEDAD -> TIPO DE BANCO -> CUENTA, y que extracto
espera cada una.

Nace de INC-000013624 (s108). Al censar los canales de extracto aparecieron 12 cuentas
vivas que no reciben nada, y cuatro de ellas son mandatos de inversion de Northern Trust
(PIMCO, JP Morgan, RAMP, IMIP). La pregunta natural -- "¿son de inversion y por eso no
reciben?" -- obligo a buscar si el sistema clasifica las cuentas por NATURALEZA.

RESULTADO MEDIDO: no. Lo que existe es:

  * YBANK (SETLEAF) clasifica por GEOGRAFIA x DIVISA: HQ/FO x EUR/USD/OTH/XAFXOF.
    Los mandatos PIMCO, JP Morgan y RAMP estan en YBANK_ACCOUNTS_HQ_USD, el MISMO cajon
    que SOG01-USDD1 y CIT04-USD04, que son las cuentas operativas de HQ.
  * Tiene DOS nodos que si son de naturaleza, y son parciales:
      _SIGHT    6 cuentas de banco casa (a la vista / ahorro) -- util
      _DEPOSIT  4 mayores del rango 404xxxx y NINGUNO es cuenta de banco casa: es un set
                de mayores de deposito a plazo, no de cuentas bancarias
  * SKB1-FDLEV reparte B0/B1 pero NO separa mandato de operativa: las 8 cuentas de
    Northern Trust son B0, mandatos incluidos.
  * YBANK solo cubre UNES: 32 cuentas vivas quedan fuera de todo set, casi todas de los
    institutos (IBE, ICBA, ICTP, IIEP, MGIE, UBO).

Asi que la naturaleza de la cuenta NO esta modelada: vive en el TEXTO libre y en la cabeza
de la gente. Este instrumento la deriva con evidencia GRADUADA y dice de que grado es cada
fila, para que se pueda declarar lo que hoy se adivina.

Solo LECTURA. Por defecto P01, ventana 2025-2026.

Uso:
    python bank_account_nature_model.py
    python bank_account_nature_model.py --bukrs UNES --json modelo.json
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",
    "needs": "rfc_p01",
    "what": "el parque bancario en tres niveles (sociedad -> tipo de banco -> cuenta) con la "
            "NATURALEZA de cada cuenta y el extracto que deberia esperar, marcando de que "
            "grado de evidencia sale cada clasificacion",
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

MARCAS_CIERRE = ("CLOSED", "CLOSE", "FERME", "CERRAD", "OBSOLET", "INACTIV",
                 "NOT USED", "DORMANT", "CANCEL")

# Marcadores de MANDATO / CARTERA. Se eligen por lo que designan de verdad, no por sonar
# a inversion: son nombres de gestora o de programa de inversion.
#   PIMCO / JP MORGAN  gestoras externas
#   RAMP               Reserve Asset Management Programme (Banco Mundial)
#   IMIP               programa de inversion
# NO se incluye ASHI ni PFF: son FONDOS (seguro medico post-empleo, participation fund) y
# sus cuentas SI reciben extracto diario -- medido. Meterlos aqui clasificaria como
# inversion cuatro cuentas operativas. Es el error que este comentario existe para evitar.
MARCA_MANDATO = ("MANDATE", "PIMCO", "MORGAN", "RAMP", "IMIP", "PORTFOLIO", "CUSTOD")
MARCA_VISTA = ("AT SIGHT", "SAVINGS", "LIVRET", "DEPOSIT", "TERM")
MARCA_TRANSFER = ("TRANSFER", "TSF")
MARCA_OPS = ("GENERAL OPERATIONS", "GEN OPS", "GENERAL OP", "OPERATIONS")


def _y(*cond):
    return " AND ".join(c for c in cond if c)


def esta_cerrada(t):
    return any(m in (t or "").upper() for m in MARCAS_CIERRE)


def rd(conn, tab, fields, where="", n=0):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
                  OPTIONS=([{"TEXT": where}] if where else []),
                  FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, [c.strip() for c in x["WA"].split("|")])) for x in r["DATA"]]


def naturaleza(texto, ybank, canal):
    """Devuelve (naturaleza, grado_de_evidencia, de_donde).

    El grado importa mas que la etiqueta: dice si la fila se puede usar para decidir o
    solo para preguntar.
      CONFIG   sale de configuracion del sistema (un set YBANK) -- se sostiene sola
      TEXTO    sale del nombre que alguien escribio -- es una convencion, no un dato
      NINGUNA  no hay senal: hay que preguntarle a Tesoreria
    """
    t = (texto or "").upper()
    if "SIGHT" in (ybank or ""):
        return "A_LA_VISTA", "CONFIG", "set YBANK _SIGHT"
    if any(m in t for m in MARCA_MANDATO):
        return "MANDATO_INVERSION", "TEXTO", "nombre de gestora/programa en el texto"
    if any(m in t for m in MARCA_VISTA):
        return "A_LA_VISTA", "TEXTO", "texto"
    if any(m in t for m in MARCA_OPS):
        return "OPERATIVA", "TEXTO", "texto"
    if any(m in t for m in MARCA_TRANSFER):
        return "TRANSFERENCIA", "TEXTO", "texto"
    return "SIN_CLASIFICAR", "NINGUNA", "-"


def esperado(nat, canal):
    """Lo que DEBERIA pasar con el extracto, dada la naturaleza. Es una hipotesis a
    confirmar con Tesoreria, no una regla del sistema -- y se marca como tal."""
    if nat == "MANDATO_INVERSION":
        return ("plausible que NO lleve extracto diario"
                if canal == "SIN EXTRACTO" else "recibe extracto: confirmar que es correcto")
    if nat == "A_LA_VISTA":
        return "cadencia baja esperable"
    return "deberia recibir extracto" if canal == "SIN EXTRACTO" else "coherente"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="")
    ap.add_argument("--system", default="P01")
    ap.add_argument("--desde", default="20250101")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    from rfc_helpers import get_connection
    conn = get_connection(a.system)
    print("SID real: %s" % conn.sid_real)
    w = ("BUKRS = '%s'" % a.bukrs) if a.bukrs else ""

    t012k = rd(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "WAERS", "HKONT"], w)
    txt = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r["TEXT1"] for r in
           rd(conn, "T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"], _y(w, "SPRAS = 'E'"))}
    bank = {(r["BUKRS"], r["HBKID"]): r["BANKL"] for r in
            rd(conn, "T012", ["BUKRS", "HBKID", "BANKS", "BANKL"], w)}
    bnka = {r["BANKL"]: r["BANKA"] for r in rd(conn, "BNKA", ["BANKS", "BANKL", "BANKA"], "")}

    leaf = rd(conn, "SETLEAF", ["SETNAME", "VALFROM"], "SETNAME LIKE 'YBANK%'")
    gl2set = collections.defaultdict(set)
    for r in leaf:
        if r["SETNAME"] in ("YBANK_ACCOUNTS_ALL", "YBANK_ACCOUNTS_HQ", "YBANK_ACCOUNTS_FO"):
            continue
        gl2set[r["VALFROM"].lstrip("0")].add(r["SETNAME"])

    hoy = datetime.datetime.now().strftime("%Y%m%d")
    feb = rd(conn, "FEBKO", ["BUKRS", "HBKID", "HKTID", "AZDAT", "EFART"],
             _y(w, "AZDAT >= '%s'" % a.desde))
    can = collections.defaultdict(collections.Counter)
    ult = {}
    for r in feb:
        if r["AZDAT"] > hoy:
            continue
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        can[k][r["EFART"]] += 1
        if r["AZDAT"] > ult.get(k, ""):
            ult[k] = r["AZDAT"]

    filas = []
    for r in t012k:
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        t = txt.get(k, "")
        if esta_cerrada(t):
            continue
        cc = can.get(k)
        canal = ("SIN EXTRACTO" if not cc
                 else "ELECTRONICO" if cc.get("E") and not cc.get("M")
                 else "MANUAL" if cc.get("M") and not cc.get("E") else "MIXTO")
        ysets = ",".join(sorted(gl2set.get(r["HKONT"].lstrip("0"), set())))
        nat, grado, fuente = naturaleza(t, ysets, canal)
        filas.append({
            "bukrs": r["BUKRS"], "hbkid": r["HBKID"], "hktid": r["HKTID"],
            "cuenta": "%s/%s-%s" % k, "texto": t, "waers": r["WAERS"], "gl": r["HKONT"],
            "banco": bnka.get(bank.get((r["BUKRS"], r["HBKID"]), ""), ""),
            "ybank": ysets, "canal": canal, "ultimo": ult.get(k, ""),
            "naturaleza": nat, "grado": grado, "fuente": fuente,
            "esperado": esperado(nat, canal),
        })

    print("\nventana %s -> hoy · %d cuentas VIVAS" % (a.desde, len(filas)))

    # ---- NIVEL 1: SOCIEDAD ---------------------------------------------------
    print("\n" + "=" * 84)
    print("NIVEL 1 — SOCIEDAD")
    print("=" * 84)
    print("  %-6s %6s %7s %-46s" % ("soc", "bancos", "cuentas", "canales"))
    for soc in sorted({f["bukrs"] for f in filas},
                      key=lambda s: -len([f for f in filas if f["bukrs"] == s])):
        ff = [f for f in filas if f["bukrs"] == soc]
        cc = collections.Counter(f["canal"] for f in ff)
        print("  %-6s %6d %7d %s"
              % (soc, len({f["hbkid"] for f in ff}), len(ff),
                 " ".join("%s=%d" % (k[:4], v) for k, v in sorted(cc.items()))))

    # ---- NIVEL 2: BANCO ------------------------------------------------------
    print("\n" + "=" * 84)
    print("NIVEL 2 — BANCO (dentro de cada sociedad)")
    print("=" * 84)
    for soc in sorted({f["bukrs"] for f in filas}):
        ff = [f for f in filas if f["bukrs"] == soc]
        print("\n  %s — %d bancos" % (soc, len({f["hbkid"] for f in ff})))
        for hb in sorted({f["hbkid"] for f in ff}):
            g = [f for f in ff if f["hbkid"] == hb]
            nats = collections.Counter(f["naturaleza"] for f in g)
            cc = collections.Counter(f["canal"] for f in g)
            print("    %-7s %-32s %2d cta  %-34s %s"
                  % (hb, (g[0]["banco"] or "")[:32], len(g),
                     " ".join("%s=%d" % (k[:9], v) for k, v in sorted(nats.items())),
                     " ".join("%s=%d" % (k[:4], v) for k, v in sorted(cc.items()))))

    # ---- NIVEL 3: NATURALEZA x CANAL ----------------------------------------
    print("\n" + "=" * 84)
    print("NIVEL 3 — NATURALEZA x CANAL, y de que grado de evidencia sale")
    print("=" * 84)
    cr = collections.Counter((f["naturaleza"], f["grado"], f["canal"]) for f in filas)
    print("  %-18s %-8s %-13s %s" % ("naturaleza", "grado", "canal", "n"))
    for k, v in sorted(cr.items()):
        print("  %-18s %-8s %-13s %d" % (k[0], k[1], k[2], v))

    print("\n  --- las que NO reciben extracto, con su naturaleza y que esperar ---")
    for f in sorted([x for x in filas if x["canal"] == "SIN EXTRACTO"],
                    key=lambda x: (x["naturaleza"], x["cuenta"])):
        print("    %-22s %-18s %-8s %-30s %s"
              % (f["cuenta"], f["naturaleza"], f["grado"], f["texto"][:30], f["esperado"]))

    sinclas = [f for f in filas if f["naturaleza"] == "SIN_CLASIFICAR"]
    print("\n  SIN_CLASIFICAR: %d cuentas — ninguna senal, ni set ni texto reconocible."
          % len(sinclas))
    print("  Es la lista que hay que preguntarle a Tesoreria, no adivinar.")
    for f in sinclas[:15]:
        print("    %-22s %s" % (f["cuenta"], f["texto"][:52]))
    if len(sinclas) > 15:
        print("    ... +%d" % (len(sinclas) - 15))

    if a.json:
        json.dump(filas, open(a.json, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("\nescrito %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
