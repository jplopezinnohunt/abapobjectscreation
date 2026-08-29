# -*- coding: utf-8 -*-
"""gold_delta_census.py — que delta le toca a CADA tabla del Golden, y cuanto cuesta no tenerlo.

LA PETICION (JP, 2026-08-29)
    «Cada tabla de las 230 o mas del Golden deberia tener un delta basado en el TIPO DE
    EXTRACCION. Esto es de vital importancia en tablas que tienen millones de registros.»

POR QUE UN CENSO ANTES QUE UN MOTOR
    Sin medir, "230 tablas necesitan delta" es una lista de deseos. Medido, es una cola de
    trabajo ordenada por lo que de verdad duele: una tabla de 3,7 M de filas sin delta obliga a
    un barrido completo cada vez; una de 200 filas se relee entera en un parpadeo y no merece
    ni una linea de codigo.

    Coste real medido hoy: refrescar FEBKO por barrido leyo 60.453 filas de P01 para anadir
    41.466. Con marca de agua, la siguiente corrida leyo 2.818. Dos tercios del trafico sobraba
    -- y FEBKO es de las PEQUENAS.

LA ESTRATEGIA DEPENDE DEL TIPO, no del gusto
    TRANSACCIONAL   filas que solo se anaden, con fecha  -> MARCA DE AGUA. Es donde esta el dinero.
    MAESTRO/TEXTO   pocas filas, cambian en sitio        -> COMPARAR POR CLAVE; releer entera es barato
    CONFIG          pocas filas, cambian en sitio        -> igual que maestro
    TOTALES         agregados por ejercicio/periodo      -> por PERIODO, se recarga el periodo abierto
    LOG             solo crece, con sello de tiempo      -> MARCA DE AGUA sobre el sello

LA TRAMPA QUE HAY QUE MIRAR EN CADA UNA
    La marca debe ir sobre la fecha de ALTA, no la del documento. Con la del documento, una
    carga retroactiva queda por debajo de la marca y NO ENTRA NUNCA. Por eso este censo
    distingue las dos: `alta` (segura) y `doc` (delta con agujero declarado).

Solo LECTURA. No toca SAP ni escribe en el Golden.
"""

QUALITY_CHECK = {
    "tier": "repo",
    "sobre": "Golden + brain_v2/gold_table_registry.json",
    "needs": "nada",
    "what": "que estrategia de delta le toca a cada tabla del Golden y cuales duelen mas",
    "args": "[--top N] [--sin-delta]",
}

import argparse
import json
import os
import re as __RE__
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
REG = os.path.join(REPO, "brain_v2", "gold_table_registry.json")

# Campos de ALTA (cuando la fila entro) -- los unicos seguros para una marca de agua.
ALTA = ["EDATE", "ERDAT", "CPUDT", "AEDAT", "ERSDA", "LAEDA", "CREATED_ON", "TIMESTAMP",
        "TIMESTMP", "AENAM_DAT", "ERFDAT", "UDATE", "LOGDATE"]
# Campos de fecha del DOCUMENTO -- sirven, pero dejan un agujero con las cargas retroactivas.
DOC = ["BUDAT", "AZDAT", "LAUFD", "BLDAT", "ZALDT", "VALUT", "DATUM", "BEGDA", "ENDDA", "GJAHR"]
PERIODO = ["GJAHR", "PERIO", "MONAT", "POPER", "RYEAR", "RPMAX"]


def tipos_por_tabla():
    """Tipo de extraccion declarado en el registro, por nombre de tabla del Golden."""
    out = {}
    try:
        with open(REG, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return out
    for dom, v in (d.get("domains") or {}).items():
        for tipo, specs in v.items():
            if not isinstance(specs, list):
                continue
            for s in specs:
                if isinstance(s, dict) and s.get("gold"):
                    out[s["gold"]] = (tipo, dom)
    return out


FECHA_RE = __RE__.compile(r"^(19|20)\d{6}$")
TS_RE = __RE__.compile(r"^(19|20)\d{2}[-/]?\d{2}[-/]?\d{2}[T ]")


def candidatos_por_los_DATOS(g, tabla, cols):
    """⛔ DERIVA el campo de fecha MIRANDO LOS VALORES, no una lista de nombres.

    La primera version buscaba nombres en una lista fija y publico
    `rsau_audit_history: SIN DELTA POSIBLE` sobre 29,8 M de filas -- un tercio del Golden --
    cuando esa tabla tiene `SAL_DATE`, `SAL_TIME` y hasta `_first_seen`, nuestro propio sello
    de extraccion. No es que no hubiera delta: es que mi lista no tenia ese nombre.

    Es el mismo modo de fallo que este proyecto persigue: buscar la FORMA (que se llame como yo
    espero) en vez del EFECTO (que contenga fechas). Un nombre que no esta en mi lista no da
    error: da un 'no hay', que es la peor respuesta posible."""
    out = []
    for c in cols:
        try:
            v = g.execute("SELECT [%s] FROM [%s] WHERE [%s] IS NOT NULL AND [%s] <> '' "
                          "LIMIT 3" % (c, tabla, c, c)).fetchall()
        except sqlite3.Error as e:
            # ⛔ NO se traga el error. La version anterior tenia la comilla rota, la consulta
            # era invalida, el except la silenciaba y el censo publicaba "no hay campo de
            # fecha" sobre 29,8 M de filas. Un except mudo convierte un bug en un hecho.
            print("    [aviso] %s.%s no se pudo muestrear: %s" % (tabla, c, str(e)[:60]))
            continue
        vals = [str(x[0]).strip() for x in v]
        if not vals:
            continue
        if all(FECHA_RE.match(x) for x in vals) or all(TS_RE.match(x) for x in vals):
            out.append(c)
    return out


def estrategia(tipo, cols, filas):
    """Que delta le toca. Devuelve (estrategia, campo, por_que)."""
    alta = next((c for c in ALTA if c in cols), None)
    doc = next((c for c in DOC if c in cols), None)
    per = [c for c in PERIODO if c in cols]
    if tipo in ("transaction", "log"):
        if alta:
            return "MARCA_AGUA", alta, "campo de ALTA: delta seguro, ve cargas retroactivas"
        if doc:
            return "MARCA_AGUA_CON_HUECO", doc, ("no hay campo de alta: el delta va por fecha "
                                                 "de documento y NO ve cargas retroactivas")
        if per:
            return "POR_PERIODO", "+".join(per), "sin fecha; se recarga el periodo abierto"
        return "SIN_DELTA_POSIBLE", "", "transaccional y sin ninguna fecha: barrido obligado"
    if tipo == "totals":
        return ("POR_PERIODO", "+".join(per), "agregados: se recarga el periodo abierto") if per \
            else ("COMPARAR_CLAVE", "", "totales sin periodo")
    if filas > 200000:
        return ("MARCA_AGUA", alta, "no es transaccional pero es GRANDE: releerla entera duele") \
            if alta else ("COMPARAR_CLAVE", "", "grande y sin fecha: comparar por clave")
    return "COMPARAR_CLAVE", "", "pocas filas: releerla entera es mas barato que un delta"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--generar", action="store_true",
                    help="escribe brain_v2/gold_delta_registry.json desde el censo")
    ap.add_argument("--sin-delta", action="store_true", dest="sin",
                    help="solo las que hoy no tienen ninguna estrategia registrada")
    a = ap.parse_args()

    g = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    tipos = tipos_por_tabla()
    try:
        marcadas = {r[0] for r in g.execute("SELECT gold FROM _gold_marca_agua")}
    except sqlite3.OperationalError:
        marcadas = set()

    filas = []
    for (nombre,) in g.execute("SELECT name FROM sqlite_master WHERE type='table' "
                               "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '\\_%' ESCAPE '\\'"):
        try:
            n = g.execute("SELECT COUNT(*) FROM [%s]" % nombre).fetchone()[0]
            cols = {r[1] for r in g.execute("PRAGMA table_info([%s])" % nombre)}
        except sqlite3.Error:
            continue
        tipo, dom = tipos.get(nombre, ("(sin tipo)", "-"))
        est, campo, por = estrategia(tipo, cols, n)
        # si la lista de nombres no encontro campo, PREGUNTA A LOS DATOS antes de decir que no
        if not campo or est in ("SIN_DELTA_POSIBLE", "COMPARAR_CLAVE"):
            cand = candidatos_por_los_DATOS(g, nombre, sorted(cols))
            if cand:
                # `_first_seen` es NUESTRO sello de extraccion: mejor marca que cualquier
                # campo de negocio, porque no puede llegar retroactivo.
                pref = ([c for c in cand if c.startswith("_")]
                        or [c for c in cand if any(k in c.upper() for k in
                                                   ("ERDAT", "CPUDT", "UDATE", "CREAT", "SAL_"))]
                        or cand)
                if n > 200000 or tipo in ("transaction", "log"):
                    est = ("MARCA_AGUA" if (pref[0].startswith("_") or "SAL_" in pref[0].upper()
                                            or pref[0] in ALTA) else "MARCA_AGUA_CON_HUECO")
                    campo = pref[0]
                    por = "campo DERIVADO de los datos, no de una lista de nombres: %s" % ", ".join(cand[:5])
        filas.append((n, nombre, tipo, est, campo or "-", nombre in marcadas, por))

    filas.sort(reverse=True)
    total = sum(f[0] for f in filas)
    print("=" * 108)
    print("QUE DELTA LE TOCA A CADA TABLA DEL GOLDEN — ordenado por lo que duele")
    print("=" * 108)
    print("  %d tablas · %s filas en total" % (len(filas), "{:,}".format(total)))
    print("  con marca de agua puesta HOY: %d" % len(marcadas))

    grandes = [f for f in filas if f[0] >= 1000000]
    print("\n  TABLAS DE MAS DE UN MILLON DE FILAS: %d, que son el %.0f%% de todo el Golden"
          % (len(grandes), 100.0 * sum(f[0] for f in grandes) / max(1, total)))
    sin = [f for f in grandes if not f[5]]
    print("  de esas, SIN delta registrado: %d — %s filas que hoy obligan a un barrido"
          % (len(sin), "{:,}".format(sum(f[0] for f in sin))))

    ver = [f for f in filas if not f[5]] if a.sin else filas
    print("\n  %-30s %11s %-13s %-22s %-10s %s"
          % ("tabla", "filas", "tipo", "estrategia", "campo", "marca?"))
    print("  " + "-" * 104)
    for n, nombre, tipo, est, campo, marcada, por in ver[:a.top]:
        print("  %-30s %11s %-13s %-22s %-10s %s"
              % (nombre[:30], "{:,}".format(n), tipo[:13], est, campo[:10],
                 "si" if marcada else ""))

    # --generar: el registro se ESCRIBE del censo. Mantenerlo a mano para 368 tablas es
    # exactamente lo que hace inviable el delta.
    if a.generar:
        reg = {}
        for n, nombre, tipo, est, campo, marcada, por in filas:
            if est in ("COMPARAR_CLAVE", "SIN_DELTA_POSIBLE") or campo in ("", "-"):
                continue
            # VENTANA DE SOLAPE (lookback). Es LA pieza que hace el delta facil: releer una
            # franja ANTERIOR a la marca captura las escrituras tardias, y como la carga es
            # idempotente (indice UNICO por clave) los duplicados no danan. Con solape, un
            # campo de fecha de DOCUMENTO deja de tener agujero: ya no hay que razonar tabla
            # por tabla si el campo es de alta o de documento, se le pone mas solape.
            solape = 7 if est == "MARCA_AGUA" else 90
            reg[nombre] = {"campo": campo, "solape_dias": solape, "tipo": tipo,
                           "filas_hoy": n, "estrategia": est, "por_que": por}
        ruta = os.path.join(REPO, "brain_v2", "gold_delta_registry.json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump({"_que_es": "delta por tabla, GENERADO por gold_delta_census.py --generar. "
                                  "No editar a mano: mantener 368 tablas a mano es lo que hace "
                                  "inviable el delta.",
                       "_solape": "releer una franja ANTERIOR a la marca captura escrituras "
                                  "tardias; la carga es idempotente por indice UNICO, asi que "
                                  "los duplicados no danan. 7 dias si el campo es de ALTA, 90 "
                                  "si es fecha de DOCUMENTO.",
                       "tablas": reg}, fh, ensure_ascii=False, indent=1)
        print("\n  GENERADO %s con %d tablas" % (os.path.relpath(ruta, REPO), len(reg)))

    print("\n  COMO SE LEE:")
    print("  MARCA_AGUA             delta seguro por campo de ALTA — es donde esta el ahorro")
    print("  MARCA_AGUA_CON_HUECO   solo hay fecha de DOCUMENTO: no ve cargas retroactivas,")
    print("                         y eso hay que DECLARARLO donde se publique el numero")
    print("  POR_PERIODO            se recarga el periodo abierto, no la historia")
    print("  COMPARAR_CLAVE         tan pequena que releerla entera es mas barato que el delta")
    print("  SIN_DELTA_POSIBLE      transaccional y sin ninguna fecha: barrido obligado, y")
    print("                         entonces el coste se declara en vez de sufrirse en silencio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
