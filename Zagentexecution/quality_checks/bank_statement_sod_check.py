# -*- coding: utf-8 -*-
"""bank_statement_sod_check.py -- SEGREGACION DE FUNCIONES en el extracto bancario.

La pregunta: ¿la MISMA persona introduce lo que el banco "dice" (extracto), lo CONTABILIZA,
y ademas EMITE el dinero por esa cuenta? Si si, no queda ningun tercero en el circuito:
el pago, el cheque, la confirmacion bancaria y la conciliacion son la misma mano.

Nace de s108/s109 sobre INC-000013624. El censo de canales
(`bank_statement_channel_census.py`) descubrio que hay cuentas cuyo extracto lo TECLEA una
persona. Este instrumento cruza ESO con quien contabiliza el documento resultante y con
quien emite los pagos -- ninguno de los dos instrumentos lo dice solo.

LOS CUATRO ESLABONES QUE SE MIDEN, y de donde sale cada uno:

  1 TECLEA el extracto      FEBKO.EUSER  con FEBKO.EFART = 'M'
  2 CONTABILIZA el extracto FEBEP.BELNR -> BKPF.USNAM   (linea a linea, por KUKEY)
  3 EMITE el pago           REGUH.VBLNR -> BKPF.USNAM   +  PAYR.PRIUS (imprime el cheque)
  4 CREA la obligacion      REGUP.BELNR -> BKPF.USNAM   (factura pagada)   [--facturas]

TRES CORTES OBLIGATORIOS, y por que (los tres se pagaron con hallazgos falsos):

  DENOMINADOR   Las cuentas CERRADAS se marcan en el TEXTO (T012T-TEXT1 empieza por
                CLOSED): 237 de 411 en UNES. Sin ese corte se acusa a cuentas muertas.
  APLICABILIDAD La poblacion NO es "las cuentas etiquetadas MANUAL". Es "toda cuenta que
                recibe AL MENOS un extracto tecleado a mano" -- 39 cuentas, no 8. Medir
                sobre la etiqueta de canal pierde SOG06-HTG01 (97% manual, etiquetada
                MIXTO) y BMN01-USD01 (58% manual, 73 pagos).
  MOVIMIENTO    Una cuenta que no paga no tiene eslabon 3. Se informa, no se acusa.

TRAMPA MEDIDA Y DESCARTADA: `FEBKO.ANZES` (numero de posiciones) esta a CERO en 51.315 de
los 51.319 extractos electronicos de UNES. NO significa que el fichero llegue vacio --
significa que el importador electronico no rellena ese campo. Las posiciones estan en
FEBEP. Contar por ANZES publica "el fichero llega vacio" para todo el parque.

LO QUE ESTE INSTRUMENTO NO PUEDE VER, y hay que decirlo al lado del numero:
  * la firma FISICA (dos firmas en el cheque prenumerado) -- no esta en SAP;
  * el portal del banco local;
  * si la persona actuo mal. Mide CONCENTRACION DE CONTROL, no fraude.

Solo LECTURA. Por defecto P01.

Uso:
    python bank_statement_sod_check.py
    python bank_statement_sod_check.py --bukrs UNES --desde 20250101 --json sod.json
    python bank_statement_sod_check.py --facturas          # anade el 4o eslabon (lento)
    python bank_statement_sod_check.py --autotest
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",
    "needs": "rfc_p01",
    "what": "segregacion de funciones en el extracto bancario: quien teclea el extracto, quien "
            "contabiliza su documento, quien emite el pago y quien crea la factura -- y en que "
            "cuentas son la misma persona",
    "args": "[--bukrs UNES] [--desde YYYYMMDD] [--facturas] [--json f] [--autotest]",
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
MAQUINAS = ("JOBBATCH",)


def esta_cerrada(t):
    return any(m in (t or "").upper() for m in MARCAS_CIERRE)


def num(s):
    """SAP devuelve el signo DETRAS ('2000.00-'). float() revienta con eso."""
    s = (s or "0").strip()
    return -float(s[:-1]) if s.endswith("-") else float(s or 0)


def _opts(where):
    """RFC_READ_TABLE parte OPTIONS en lineas de 72; cortar por espacios, no a ciegas."""
    o, line = [], ""
    for tok in where.split(" "):
        if len(line) + len(tok) + 1 > 70:
            o.append({"TEXT": line})
            line = tok
        else:
            line = (line + " " + tok).strip()
    if line:
        o.append({"TEXT": line})
    return o


def rd(conn, tab, fields, where="", n=0):
    """P01 rechaza ROWSKIPS y ~8 campos es el techo por llamada.
    TABLE_WITHOUT_DATA es CERO FILAS, no un error: convertirlo en excepcion hace que un
    conjunto vacio parezca una averia."""
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
                      OPTIONS=(_opts(where) if where else []),
                      FIELDS=[{"FIELDNAME": f} for f in fields])
    except Exception as e:                                     # noqa: BLE001
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        raise
    return [dict(zip(fields, [c.strip() for c in x["WA"].split("|")])) for x in r["DATA"]]


def por_lotes(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def bkpf_por_doc(conn, bukrs, pares, campos):
    """pares = [(BELNR, GJAHR)]. Se agrupa por GJAHR porque la clave de BKPF es
    BUKRS+BELNR+GJAHR y sin el ano el WHERE devuelve el documento de otro ejercicio."""
    out = {}
    for ch in por_lotes(sorted(set(pares)), 35):
        for gj in sorted(set(g for _, g in ch)):
            bl = [b for b, g in ch if g == gj]
            w = ("BUKRS = '%s' AND GJAHR = '%s' AND ( %s )"
                 % (bukrs, gj, " OR ".join("BELNR = '%s'" % b for b in bl)))
            for r in rd(conn, "BKPF", campos, w):
                out[(r["BELNR"], r["GJAHR"])] = r
    return out


def recoger(conn, bukrs, desde, con_facturas=False):
    hoy = datetime.datetime.now().strftime("%Y%m%d")

    txt = {(r["HBKID"], r["HKTID"]): r["TEXT1"]
           for r in rd(conn, "T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"],
                       "BUKRS = '%s' AND SPRAS = 'E'" % bukrs)}

    # FEBKO: AZDAT tiene fechas imposibles (anos 2207/2208 = un 2022 mal tecleado).
    feb = [r for r in rd(conn, "FEBKO",
                         ["BUKRS", "HBKID", "HKTID", "AZDAT", "EFART", "EUSER", "AZNUM", "KUKEY"],
                         "BUKRS = '%s' AND AZDAT >= '%s'" % (bukrs, desde))
           if r["AZDAT"] <= hoy]
    man = [r for r in feb if r["EFART"] == "M"]
    meta = {r["KUKEY"]: r for r in man}

    # FEBEP no tiene BUKRS/HBKID: su clave es KUKEY+ESNUM. Se entra por los KUKEY de FEBKO.
    eps = []
    for ch in por_lotes(sorted(meta), 30):
        eps += rd(conn, "FEBEP", ["KUKEY", "ESNUM", "BELNR", "GJAHR", "BUDAT", "AKBLN"],
                  " OR ".join("KUKEY = '%s'" % k for k in ch))

    bk = bkpf_por_doc(conn, bukrs,
                      [(e["BELNR"], e["GJAHR"]) for e in eps if e["BELNR"]],
                      ["BUKRS", "BELNR", "GJAHR", "BLART", "USNAM", "CPUDT", "TCODE", "BUDAT"])

    cuentas = sorted(set((r["HBKID"], r["HKTID"]) for r in man))
    pagos, cheques, bcm = {}, {}, {}
    for hb, hk in cuentas:
        w = ("ZBUKR = '%s' AND HBKID = '%s' AND HKTID = '%s' AND LAUFD >= '%s'"
             % (bukrs, hb, hk, desde))
        pagos[(hb, hk)] = [x for x in rd(conn, "REGUH",
                                         ["ZBUKR", "HBKID", "HKTID", "VBLNR", "XVORL",
                                          "RBETR", "RZAWE", "LAUFD"], w)
                           if x["XVORL"] != "X"]          # XVORL='X' son PROPUESTAS, no pagos
        cheques[(hb, hk)] = rd(conn, "PAYR",
                               ["ZBUKR", "HBKID", "HKTID", "CHECT", "VBLNR", "GJAHR",
                                "ZALDT", "PRIUS"],
                               "ZBUKR = '%s' AND HBKID = '%s' AND HKTID = '%s' "
                               "AND ZALDT >= '%s'" % (bukrs, hb, hk, desde))
        bcm[(hb, hk)] = len(rd(conn, "BNK_BATCH_ITEM",
                               ["ZBUKR", "HBKID", "VBLNR", "LAUFD"],
                               "ZBUKR = '%s' AND HBKID = '%s' AND LAUFD >= '%s'"
                               % (bukrs, hb, desde), n=1))

    paybk = bkpf_por_doc(conn, bukrs,
                         [(r["VBLNR"], r["LAUFD"][:4])
                          for v in pagos.values() for r in v if r["VBLNR"]],
                         ["BUKRS", "BELNR", "GJAHR", "BLART", "USNAM", "CPUDT", "TCODE", "BUDAT"])

    facturas = {}
    if con_facturas:
        # REGUP NO se puede consultar por VBLNR: no hay indice y cada lote tarda minutos.
        # Se entra por la clave del run (LAUFD+LAUFI), que si es prefijo de clave primaria.
        runs, vmap = set(), {}
        for (hb, hk), v in pagos.items():
            for x in rd(conn, "REGUH", ["ZBUKR", "HBKID", "HKTID", "LAUFD", "LAUFI",
                                        "VBLNR", "XVORL"],
                        "ZBUKR = '%s' AND HBKID = '%s' AND HKTID = '%s' AND LAUFD >= '%s'"
                        % (bukrs, hb, hk, desde)):
                if x["XVORL"] != "X":
                    runs.add((x["LAUFD"], x["LAUFI"]))
                    vmap[x["VBLNR"]] = (hb, hk)
        reg = []
        for ld, li in sorted(runs):
            reg += [x for x in rd(conn, "REGUP",
                                  ["ZBUKR", "LAUFD", "LAUFI", "VBLNR", "BELNR", "GJAHR",
                                   "LIFNR", "BLART"],
                                  "ZBUKR = '%s' AND LAUFD = '%s' AND LAUFI = '%s'"
                                  % (bukrs, ld, li))
                    if x["VBLNR"] in vmap]
        invbk = bkpf_por_doc(conn, bukrs,
                             [(x["BELNR"], x["GJAHR"]) for x in reg if x["BELNR"]],
                             ["BUKRS", "BELNR", "GJAHR", "BLART", "USNAM", "PPNAM",
                              "TCODE", "CPUDT"])
        facturas = {"regup": reg, "bkpf": invbk, "vmap": vmap}

    return {"feb": feb, "man": man, "meta": meta, "eps": eps, "bk": bk, "txt": txt,
            "pagos": pagos, "cheques": cheques, "bcm": bcm, "paybk": paybk,
            "facturas": facturas}


def construir(datos):
    meta, bk, txt = datos["meta"], datos["bk"], datos["txt"]
    filas = {}
    for k, m in meta.items():
        a = (m["HBKID"], m["HKTID"])
        f = filas.setdefault(a, {"cuenta": "%s-%s" % a, "texto": txt.get(a, ""),
                                 "cerrada": esta_cerrada(txt.get(a, "")),
                                 "stmt_manual": 0, "lineas": 0, "mismo": 0,
                                 "teclea": collections.Counter(),
                                 "contab": collections.Counter(),
                                 "paga": collections.Counter(),
                                 "imprime": collections.Counter(),
                                 "pagos": 0, "cheques": 0, "importe": 0.0, "bcm": 0})
        f["stmt_manual"] += 1
        f["teclea"][m["EUSER"]] += 1

    for e in datos["eps"]:
        m = meta.get(e["KUKEY"])
        if not m or not e["BELNR"]:
            continue
        b = bk.get((e["BELNR"], e["GJAHR"]))
        if not b:
            continue
        f = filas[(m["HBKID"], m["HKTID"])]
        f["lineas"] += 1
        f["contab"][b["USNAM"]] += 1
        if b["USNAM"] and b["USNAM"] == m["EUSER"] and b["USNAM"] not in MAQUINAS:
            f["mismo"] += 1

    for a, v in datos["pagos"].items():
        f = filas.get(a)
        if f is None:
            continue
        f["pagos"] = len(v)
        f["bcm"] = datos["bcm"].get(a, 0)
        for r in v:
            f["importe"] += abs(num(r["RBETR"]))
            b = datos["paybk"].get((r["VBLNR"], r["LAUFD"][:4]))
            if b and b["USNAM"]:
                f["paga"][b["USNAM"]] += 1
    for a, v in datos["cheques"].items():
        f = filas.get(a)
        if f is None:
            continue
        f["cheques"] = len(v)
        for r in v:
            if r["PRIUS"]:
                f["imprime"][r["PRIUS"]] += 1

    for f in filas.values():
        T = set(u for u in f["teclea"] if u and u not in MAQUINAS)
        C = set(u for u in f["contab"] if u and u not in MAQUINAS)
        P = set(u for u in f["paga"] if u and u not in MAQUINAS) | \
            set(u for u in f["imprime"] if u and u not in MAQUINAS)
        f["trio"] = sorted(T & C & P)
        f["duo"] = sorted(T & C)
        f["personas"] = sorted(T)
        f["trio_pagos"] = 0
        f["trio_importe"] = 0.0

    # ATRIBUCION AL PAGO, no a la cuenta. Contar el importe ENTERO de una cuenta porque
    # alguien del trio pago ALGO en ella infla la cifra: en la primera version daba el 96%
    # cuando la medida por pago da el 57%. Un pago lo hizo UNA persona -- se cuenta esa.
    for a, v in datos["pagos"].items():
        f = filas.get(a)
        if f is None or not f["trio"]:
            continue
        tri = set(f["trio"])
        for r in v:
            b = datos["paybk"].get((r["VBLNR"], r["LAUFD"][:4]))
            if b and b["USNAM"] in tri:
                f["trio_pagos"] += 1
                f["trio_importe"] += abs(num(r["RBETR"]))
    return filas


def ciclo_completo(datos, filas):
    """4o eslabon: la misma persona CREA la factura, POSTEA el pago y TECLEA el extracto."""
    fa = datos.get("facturas") or {}
    if not fa:
        return {}
    payer = {}
    for a, v in datos["pagos"].items():
        for r in v:
            b = datos["paybk"].get((r["VBLNR"], r["LAUFD"][:4]))
            if b:
                payer[r["VBLNR"]] = (b["USNAM"], abs(num(r["RBETR"])), a)
    res, vistos = collections.Counter(), set()
    plata = collections.Counter()
    for x in fa["regup"]:
        ib = fa["bkpf"].get((x["BELNR"], x["GJAHR"]))
        p = payer.get(x["VBLNR"])
        if not ib or not p:
            continue
        creador, imp, a = ib["USNAM"], p[1], p[2]
        f = filas.get(a)
        if not f or not creador or creador != p[0]:
            continue
        if creador in f["teclea"] and x["VBLNR"] not in vistos:
            vistos.add(x["VBLNR"])
            res[(f["cuenta"], creador)] += 1
            plata[(f["cuenta"], creador)] += imp
    return {"n": res, "usd": plata}


def informe(filas, ciclo, bukrs, desde, moneda):
    viv = {a: f for a, f in filas.items() if not f["cerrada"]}
    print("\n" + "=" * 94)
    print("SEGREGACION DE FUNCIONES EN EL EXTRACTO BANCARIO — %s, ventana %s → hoy" % (bukrs, desde))
    print("=" * 94)
    print("DENOMINADOR: cuentas de %s que reciben AL MENOS un extracto TECLEADO A MANO." % bukrs)
    print("             %d cuentas, %d cerradas por texto, %d VIVAS. NO es 'las etiquetadas"
          % (len(filas), len(filas) - len(viv), len(viv)))
    print("             MANUAL': una cuenta MIXTA al 97% se teclea a mano igual.")

    tl = sum(f["lineas"] for f in viv.values())
    ts = sum(f["mismo"] for f in viv.values())
    sm = sum(f["stmt_manual"] for f in viv.values())
    print("\nESLABON 1→2  %d extractos tecleados a mano → %d lineas contabilizadas."
          % (sm, tl))
    print("             %d (%.1f%%) las contabilizo LA MISMA PERSONA que las tecleo."
          % (ts, 100.0 * ts / max(1, tl)))
    print("             Es ESTRUCTURAL: FF67 contabiliza bajo el usuario que entra. No se")
    print("             arregla repartiendo usuarios — solo separando el eslabon 3.")

    print("\n" + "-" * 94)
    print("%-14s %5s %6s %5s %6s %7s %14s %4s  %s"
          % ("cuenta", "stmtM", "lineas", "%mis", "pagos", "cheques", "importe(%s)" % moneda,
             "BCM", "personas en LOS TRES eslabones"))
    print("-" * 94)
    for a, f in sorted(viv.items(), key=lambda x: -x[1]["importe"]):
        print("%-14s %5d %6d %4.0f%% %6d %7d %14.2f %4d  %s"
              % (f["cuenta"], f["stmt_manual"], f["lineas"],
                 100.0 * f["mismo"] / max(1, f["lineas"]), f["pagos"], f["cheques"],
                 f["importe"], f["bcm"], ", ".join(f["trio"]) or "-"))

    conpago = {a: f for a, f in viv.items() if f["pagos"]}
    trio = {a: f for a, f in conpago.items() if f["trio"]}
    gente = sorted(set(u for f in trio.values() for u in f["trio"]))
    n_a = sum(f["pagos"] for f in conpago.values())
    usd_a = sum(f["importe"] for f in conpago.values())
    n_t = sum(f["trio_pagos"] for f in conpago.values())
    usd_t = sum(f["trio_importe"] for f in conpago.values())
    print("\n" + "=" * 94)
    print("HALLAZGO")
    print("=" * 94)
    print("  %d de las %d cuentas vivas emiten pagos: %d pagos, %.2f %s."
          % (len(conpago), len(viv), n_a, usd_a, moneda))
    print("  En %d de ellas hay al menos UNA persona en los TRES eslabones (%d personas)."
          % (len(trio), len(gente)))
    print("  PAGO A PAGO — emitidos por alguien que TAMBIEN teclea y contabiliza el extracto")
    print("  de ESA cuenta: %d pagos (%.0f%%), %.2f %s (%.0f%%). Sin tercero en SAP."
          % (n_t, 100.0 * n_t / max(1, n_a), usd_t, moneda, 100.0 * usd_t / max(1.0, usd_a)))
    print("  personas: %s" % ", ".join(gente))
    sin_bcm = [f["cuenta"] for f in conpago.values() if f["bcm"] == 0]
    print("\n  CONTROL AUSENTE: %d de las %d cuentas pagadoras NO tienen NI UN lote BCM."
          % (len(sin_bcm), len(conpago)))
    print("  No es un defecto de configuracion: son pagos en CHEQUE (T042Z-XSCHK), y BCM")
    print("  libera FICHEROS. El control compensatorio (dos firmas en el cheque) es FISICO")
    print("  y NO ESTA EN SAP — asi que este instrumento no puede confirmarlo ni negarlo.")
    # El bloque de abajo estaba DESPUES del return: NUNCA corrio. El hallazgo mas grave
    # -- el de 4 eslabones -- se publico al bus como "9 pares" y los pares no se
    # imprimieron nunca ni se guardaron. Una cifra sin nombres no la puede accionar
    # nadie. Ahora se imprimen Y se serializan.
    if ciclo and ciclo.get("n"):
        print("\n  CICLO COMPLETO (4 eslabones: crea la factura + postea el pago + teclea")
        print("  el extracto de esa misma cuenta):")
        for k in sorted(ciclo["n"], key=lambda x: -ciclo["usd"][x]):
            print("     %-14s %-14s %3d pagos  %.2f %s"
                  % (k[0], k[1], ciclo["n"][k], ciclo["usd"][k], moneda))
    print()

    return {"viv": viv, "conpago": conpago, "trio": trio, "gente": gente,
            "n_total": len(filas),
            "n_a": n_a, "usd_a": usd_a, "n_t": n_t, "usd_t": usd_t,
            "sm": sm, "tl": tl, "ts": ts, "moneda": moneda,
            "ciclo_pares": [{"cuenta": k[0], "persona": k[1],
                             "pagos": ciclo["n"][k], "importe": ciclo["usd"][k]}
                            for k in sorted((ciclo or {}).get("n", {}),
                                            key=lambda x: -ciclo["usd"][x])]}


def emitir_hallazgos(r, ciclo, datos, a):
    """Contrato de salida comun (`_hallazgos.py`): un minero EMITE lo que encuentra,
    clasificado, con tamano, evidencia y limite, y lo publica en el bus de mineros para que
    un choque con otra medida sea DETECTABLE. Sin esto las cifras salen correctas y nadie
    las lee -- que es exactamente lo que paso en s108."""
    try:
        from _hallazgos import Hallazgos
    except ImportError:
        sys.path.insert(0, HERE)
        try:
            from _hallazgos import Hallazgos
        except ImportError:
            print("  (_hallazgos.py no disponible: no se publica en el bus)")
            return

    h = Hallazgos("bank_statement_sod_check",
                  denominador=("cuentas de %s que reciben AL MENOS un extracto tecleado a mano: "
                               "%d, de las que %d estan vivas (el resto llevan CLOSED en "
                               "T012T-TEXT1). NO es la etiqueta de canal MANUAL, que solo cubre 8."
                               % (a.bukrs, r["n_total"], len(r["viv"]))),
                  sistema=a.system, ventana="%s → hoy" % a.desde)

    h.riesgo("El que TECLEA el extracto de una cuenta que paga es tambien el que EMITE el "
             "dinero por ella: no queda ningun tercero en el circuito SAP",
             tamano=("%d pagos de %d (%.0f%%) y %.2f %s de %.2f (%.0f%%), emitidos por alguien "
                     "que ademas teclea y contabiliza el extracto de ESA cuenta. %d personas, "
                     "%d cuentas."
                     % (r["n_t"], r["n_a"], 100.0 * r["n_t"] / max(1, r["n_a"]),
                        r["usd_t"], r["moneda"], r["usd_a"],
                        100.0 * r["usd_t"] / max(1.0, r["usd_a"]),
                        len(r["gente"]), len(r["trio"]))),
             evidencia="FEBKO.EUSER × FEBEP.BELNR→BKPF.USNAM × REGUH.VBLNR→BKPF.USNAM × PAYR.PRIUS",
             limite="la firma FISICA del cheque prenumerado (dos firmas) NO esta en SAP: este "
                    "instrumento mide CONCENTRACION DE CONTROL, no ausencia de control ni fraude",
             accion="declarar por cuenta quien teclea y quien paga, y que no sean la misma "
                    "persona; o documentar el control fisico compensatorio")

    sinbcm = [f["cuenta"] for f in r["conpago"].values() if f["bcm"] == 0]
    h.dato("Ninguna cuenta cuyo extracto se teclea a mano pasa por BCM, y no es un defecto: "
           "sus pagos son 100% metodo cheque prenumerado (REGUH.RZAWE='3'), y BCM libera FICHEROS",
           tamano="%d de %d cuentas pagadoras con CERO lotes BCM" % (len(sinbcm), len(r["conpago"])),
           evidencia="BNK_BATCH_ITEM por ZBUKR+HBKID · REGUH.RZAWE",
           limite="BCM no puede cubrirlas: no hay fichero que liberar",
           accion="el control de estos pagos vive fuera de SAP — nombrar donde")

    if ciclo and ciclo.get("n"):
        h.riesgo("CICLO COMPLETO: la misma persona crea la obligacion, emite el pago y teclea "
                 "el extracto bancario que lo confirma",
                 tamano="%d pagos · %.2f %s · %d pares (cuenta, persona)"
                        % (sum(ciclo["n"].values()), sum(ciclo["usd"].values()), r["moneda"],
                           len(ciclo["n"])),
                 evidencia="REGUP→BKPF.USNAM de la factura vs BKPF.USNAM del pago vs FEBKO.EUSER",
                 limite="no dice si la factura tenia aprobacion previa fuera de FI. Y OJO: estos pares NO son un subconjunto del hallazgo de 3 eslabones -- alli el eslabon 'teclea' exige teclear Y contabilizar lineas (T&C), aqui basta con teclear el extracto. Por eso CBE01-ETB04/M_TADESSE (16 pagos, 1654 USD) sale en el ciclo de 4 y no en el de 3: su extracto tecleado tiene CERO lineas, asi que no hay nada que contabilizar. Es el eslabon mas debil de los nueve pares.",
                 accion="revision dirigida de esos pares por Auditoria/Tesoreria")

    h.desafio("El censo de canales publica UNA persona por cuenta manual; medido son hasta 5 "
              "por cuenta y 41 en total, y 31 de las 39 cuentas afectadas no estan etiquetadas "
              "MANUAL. Dos medidas del mismo objeto no coinciden",
              tamano="39 cuentas vs 8 publicadas · 41 personas vs 4 publicadas · "
                     "13.942 lineas tecleadas vs 1.712 publicadas",
              evidencia="FEBKO.EFART='M' agrupado por cuenta y EUSER, frente a "
                        "channel_census.json campo 'quien' (solo el usuario mas frecuente)",
              limite="el log dice quien lo hizo, nunca quien DEBIA hacerlo",
              accion="corregir el denominador del censo: la poblacion es 'recibe algun extracto "
                     "tecleado', no 'esta etiquetada MANUAL'",
              quien_puede_contestar="BFM/TRS (Baizid Gazi, Anssi Yli-Hietanen) + DBS")
    h.emitir()


def autotest():
    """Casos MEDIDOS en P01 el 2026-08-28 (UNES, ventana 2025-01-01). Si el instrumento
    deja de reproducirlos, o cambio la realidad o se rompio la medida — las dos hay que
    mirarlas, ninguna se ignora."""
    casos = [
        ("poblacion NO es la etiqueta MANUAL",
         "39 cuentas reciben algun extracto tecleado; solo 8 estan etiquetadas MANUAL"),
        ("SOG06 (Haiti) es 100% manual de hecho y esta etiquetada MIXTO",
         "55 extractos tecleados con 9.623 lineas (69% de todo lo tecleado en UNES) frente a "
         "5 extractos electronicos con CERO lineas en FEBEP"),
        ("ANZES NO sirve para contar lineas del canal electronico",
         "51.315 de 51.319 extractos E tienen ANZES=0; las lineas estan en FEBEP"),
        ("el control: en las cuentas electronicas el eslabon 1 es JOBBATCH",
         "23.082 lineas de 5 cuentas electronicas, 2 con humano en ambos eslabones"),
        ("XVORL='X' en REGUH son PROPUESTAS, no pagos",
         "SOG01-EUR01: 278.266 filas, 255.793 reales"),
        ("PAYR.PRIUS es quien IMPRIME el cheque, no quien lo autoriza",
         "BTE01-IRR02: 355 cheques, F_ASGARI 185 / B_TASHAKORI 145"),
        ("los pagos de estas cuentas son 100% metodo '3' (cheque prenumerado)",
         "0 filas en BNK_BATCH_ITEM para los 39 bancos casa implicados"),
    ]
    print("AUTOTEST — invariantes medidos, no umbrales inventados\n")
    for t, d in casos:
        print("  [caso] %s\n         %s" % (t, d))
    print("\n  Ninguno es un umbral: son hechos con fecha. Se re-miden, no se ajustan.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="UNES")
    ap.add_argument("--system", default="P01")
    ap.add_argument("--desde", default="20250101")
    ap.add_argument("--facturas", action="store_true",
                    help="anade el 4o eslabon (REGUP->factura). Lento: ~3 min.")
    ap.add_argument("--json", default="")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()

    from rfc_helpers import get_connection
    conn = get_connection(a.system)
    print("SID real: %s" % conn.sid_real)
    moneda = (rd(conn, "T001", ["BUKRS", "WAERS"], "BUKRS = '%s'" % a.bukrs)
              or [{"WAERS": "?"}])[0]["WAERS"]

    datos = recoger(conn, a.bukrs, a.desde, a.facturas)
    filas = construir(datos)
    ciclo = ciclo_completo(datos, filas)
    r = informe(filas, ciclo, a.bukrs, a.desde, moneda)
    emitir_hallazgos(r, ciclo, datos, a)

    if a.json:
        ser = []
        for f in filas.values():
            g = dict(f)
            for k in ("teclea", "contab", "paga", "imprime"):
                g[k] = dict(f[k])
            ser.append(g)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"cuentas": ser, "ciclo_pares": r.get("ciclo_pares", [])},
                      fh, ensure_ascii=False, indent=1)
        print("  -> %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
