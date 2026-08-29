# -*- coding: utf-8 -*-
"""gold_delta.py — EL mecanismo de delta del Golden: lee solo lo que falta, para CUALQUIER tabla.

LA PETICION (JP, 2026-08-29)
    «No tienes un mecanismo para hacer el delta. Eso es lo que mas ayudaria.»

    Tenia razon. Habia un delta metido A MANO dentro del script de FEBKO, atado a esa tabla.
    Esto lo saca de ahi: una tabla mas es una FILA en el registro, no un script nuevo.

QUE HACE, EN UNA FRASE
    Mira hasta donde se extrajo (`_gold_marca_agua`), lee de P01 SOLO desde ahi, mete por clave
    con INSERT OR REPLACE, y mueve la marca. Ni un DELETE, nunca.

LAS CUATRO TRAMPAS QUE YA SE PAGARON HOY, Y QUE ESTE MODULO EVITA POR CONSTRUCCION
    1. LA MARCA VA SOBRE LA FECHA DE ALTA, no la del documento. Con `AZDAT`, un extracto de
       fecha vieja cargado ayer queda por debajo de la marca y NO ENTRA NUNCA. Cuando una tabla
       no tiene campo de alta se DECLARA: su refresco es un barrido y cuesta lo que cuesta.
    2. NUNCA SE CONSTRUYE UN DIA 31. `AZDAT <= '<mes>31'` es el 31 de febrero: SAP responde
       SAPSQL_DATA_LOSS, que suena a "el dato no cabe" y no lo es. Limite superior ABIERTO.
    3. INSERT OR REPLACE NO REEMPLAZA SIN INDICE UNICO: apila. Si la tabla destino no tiene
       unicidad por la clave, este modulo la CREA antes de escribir. Sin eso se acumulan
       duplicados y el total sube, que parece progreso.
    4. NO SE ESCRIBE FILA A FILA. Se vuelca a una temporal indexada y se hace un solo UPDATE /
       upsert. 500.000 UPDATE con clave sin indice sobre 3,7 M filas = 500.000 escaneos
       completos: 580 s sin terminar, frente a 190 s las tres tablas por el camino bueno.

Y LA MARCA SE MUEVE AL FINAL, SOLO SI NO FALLO NINGUN TROZO
    Moverla antes, o con huecos, congela un agujero que ningun delta posterior vuelve a mirar.
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "Golden + P01",
    "needs": "rfc_p01",
    "what": "delta por marca de agua para cualquier tabla del Golden: lee solo lo que falta",
    "args": "<tabla> | --estado | --todas",
}

import argparse
import datetime
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
import _marca_agua as M                                                # noqa: E402

# EL REGISTRO. Una tabla mas = una fila mas aqui. `alta` es el campo por el que avanza la
# marca; si es None, esa tabla NO tiene delta posible y su refresco es un barrido declarado.
REGISTRO = {
    "FEBKO_2024_2026": {
        "sap": "FEBKO", "clave": ["KUKEY"], "alta": "EDATE", "alcance": "",
        "por_que": "EDATE es la fecha de ALTA del extracto; AZDAT es la del extracto y dejaria "
                   "fuera para siempre cualquier carga retroactiva"},
    "FEBEP_2024_2026": {
        "sap": "FEBEP", "clave": ["KUKEY", "ESNUM"], "alta": None, "fecha": "BUDAT",
        "alcance": "",
        "por_que": "FEBEP no trae fecha de alta: su delta va por BUDAT y por tanto NO ve una "
                   "posicion retroactiva. Declarado, no escondido"},
    "REGUH": {
        # KUNNR entra en la clave el 2026-08-29: es lo que separa los pagos contra ficha de
        # CLIENTE (LIFNR vacio). OJO -- solo esta relleno en 2.591.955 de 3.707.737 filas; en
        # 2025-2026 cubre el 97%, en el historico no. SQLite deja pasar los NULL en un indice
        # unico, asi que el indice NO prueba unicidad en esas: el delta es seguro porque solo
        # escribe desde la marca hacia delante.
        "sap": "REGUH",
        "clave": ["LAUFD", "LAUFI", "XVORL", "ZBUKR", "LIFNR", "KUNNR", "EMPFG", "VBLNR"],
        "alta": None, "fecha": "LAUFD", "alcance": "ZBUKR = 'UNES'",
        "por_que": "LAUFD es la fecha de la CORRIDA de pago, que en la practica solo avanza; "
                   "y RBETR solo esta rellena para UNES desde 2024 -- fuera de ahi es NULL"},
    # LA CADENA DEL PAGO. Iban 157/156/113 dias por detras de FEBKO, y las cuatro alimentan
    # el hallazgo de segregacion de funciones: PAYR dice quien IMPRIME el cheque, BNK_BATCH si
    # paso por BCM, DFPAYG que fichero se genero. La CLAVE es lo unico que no se puede derivar
    # sin riesgo: una clave mal puesta no da error, apila duplicados.
    "PAYR": {
        "sap": "PAYR", "clave": ["ZBUKR", "HBKID", "HKTID", "RZAWE", "CHECT"],
        "alta": None, "fecha": "LAUFD", "alcance": "",
        "por_que": "cheques emitidos; LAUFD es la corrida de pago"},
    "BNK_BATCH_HEADER": {
        "sap": "BNK_BATCH_HEADER", "clave": ["BATCH_NO"],
        "alta": "CRDATE", "alcance": "",
        "por_que": "CRDATE es la fecha de ALTA del lote BCM: delta seguro"},
    "BNK_BATCH_ITEM": {
        "sap": "BNK_BATCH_ITEM", "clave": ["BATCH_NO", "ITEM_NO"],
        "alta": None, "fecha": "LAUFD", "alcance": "",
        "por_que": "posiciones del lote BCM; sin fecha de alta propia"},
    "DFPAYG": {
        "sap": "DFPAYG", "clave": ["LAUFD", "LAUFI", "XVORL", "GRPNO"],
        "alta": None, "fecha": "LAUFD", "alcance": "",
        "por_que": "grupos de fichero de pago"},
    "REGUP_SCENARIOS": {
        # ⛔ LA CLAVE SAP NO BASTA, y no es culpa de la extraccion: MEDIDO contra P01, las
        # lineas de NOMINA entran en REGUP con BELNR vacio, BUZEI='000' y GJAHR='0000' -- sin
        # referencia a documento FI. Tres importes del mismo empleado comparten clave EN SAP,
        # no en nuestra copia. Se anaden WRBTR y SGTXT para identificarlas.
        # CONSECUENCIA A DECLARAR: si el importe de una fila cambiara, entraria como fila NUEVA
        # en vez de reemplazar. Para partidas de pago ya ejecutadas, que no cambian, es aceptable.
        "sap": "REGUP",
        "clave": ["LAUFD", "LAUFI", "XVORL", "ZBUKR", "LIFNR", "KUNNR", "EMPFG", "VBLNR",
                  "BELNR", "BUZEI", "GJAHR", "WRBTR", "SGTXT"],
        "alta": None, "fecha": "LAUFD", "alcance": "ZBUKR = 'UNES'",
        "por_que": "OJO: es un SUBCONJUNTO por escenarios, no REGUP entera"},
}


def meses(a, b):
    y, m = int(a[:4]), int(a[4:])
    out = []
    while "%04d%02d" % (y, m) <= b:
        out.append("%04d%02d" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def sig(ym):
    y, m = int(ym[:4]), int(ym[4:]) + 1
    return "%04d%02d" % (y + 1, 1) if m == 13 else "%04d%02d" % (y, m)


def asegura_unicidad(con, gold, clave):
    """Sin unicidad, INSERT OR REPLACE APILA. Hoy dejo 38.764 duplicados byte a byte."""
    ix = "ux_%s_delta" % gold.lower()
    try:
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS %s ON [%s] (%s)"
                    % (ix, gold, ", ".join('"%s"' % k for k in clave)))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        n, d = con.execute("SELECT COUNT(*), COUNT(DISTINCT %s) FROM [%s]"
                           % (" || '|' || ".join('"%s"' % k for k in clave), gold)).fetchone()
        print("  NO se puede crear el indice UNICO: ya hay %d filas para %d claves. "
              "Deduplica antes; escribir asi apilaria mas." % (n, d))
        return False


def delta(gold, desde_forzado="", hasta=""):
    spec = REGISTRO[gold]
    con = sqlite3.connect(M.DB)
    cols = [r[1] for r in con.execute("PRAGMA table_info([%s])" % gold)]
    campo = spec.get("alta") or spec.get("fecha")
    if campo not in cols:
        print("  %s no tiene %s: sin delta posible." % (gold, campo))
        return 2
    if not asegura_unicidad(con, gold, spec["clave"]):
        return 2

    m = M.leer(con, gold, spec["alcance"])
    hasta = hasta or datetime.date.today().strftime("%Y%m")
    if desde_forzado:
        desde, modo = desde_forzado, "FORZADO"
    elif m:
        desde, modo = str(m["hasta"])[:6], "DELTA desde la marca (%s <= %s)" % (m["campo_marca"],
                                                                               m["hasta"])
    else:
        desde, modo = "202401", "BARRIDO (no hay marca, y se dice)"
    print("  %s · %s · %s..%s" % (gold, modo, desde, hasta))
    if not spec.get("alta"):
        print("    AVISO: %s no tiene campo de ALTA -> el delta va por %s y NO ve cargas "
              "retroactivas. %s" % (gold, campo, spec["por_que"]))

    from rfc_helpers import get_connection
    conn = get_connection("P01")
    ph = ",".join("?" * len(cols))
    leidas = nuevas = 0
    fallidos = []
    ya = set()
    if spec["clave"] == ["KUKEY"]:
        ya = set(str(r[0]) for r in con.execute("SELECT KUKEY FROM [%s]" % gold))
    for ym in meses(desde, hasta):
        w = " AND ".join(x for x in [spec["alcance"],
                                     "%s >= '%s01' AND %s < '%s01'" % (campo, ym, campo, sig(ym))]
                         if x)
        filas = {}
        resto = [c for c in cols if c not in spec["clave"]]
        try:
            for i in range(0, len(resto), 7):
                trozo = spec["clave"] + resto[i:i + 7]
                r = conn.call("RFC_READ_TABLE", QUERY_TABLE=spec["sap"], DELIMITER="|",
                              ROWCOUNT=0, OPTIONS=[{"TEXT": w}],
                              FIELDS=[{"FIELDNAME": f} for f in trozo])
                for d in r["DATA"]:
                    v = dict(zip(trozo, [x.strip() for x in d["WA"].split("|")]))
                    filas.setdefault(tuple(v[k] for k in spec["clave"]), {}).update(v)
        except Exception as e:
            print("    %s ERROR %s" % (ym, str(e).split("\n")[0][:70]))
            fallidos.append(ym)
            continue
        if not filas:
            continue
        n_new = len([k for k in filas if k[0] not in ya]) if ya else 0
        con.executemany("INSERT OR REPLACE INTO [%s] VALUES (%s)" % (gold, ph),
                        [tuple(f.get(c, "") for c in cols) for f in filas.values()])
        con.commit()
        leidas += len(filas)
        nuevas += n_new
        print("    %s  %5d filas%s" % (ym, len(filas),
                                       "  (%d nuevas)" % n_new if ya else ""))
    tot = con.execute("SELECT COUNT(*) FROM [%s]" % gold).fetchone()[0]
    print("  leidas de P01: %d · Golden: %d filas · ni un DELETE" % (leidas, tot))
    if fallidos:
        print("  NO se mueve la marca: fallaron %s. Marcar con huecos congela un agujero que "
              "ningun delta posterior vuelve a mirar." % " ".join(fallidos))
        con.close()
        return 2
    tope = M.desde_el_dato(con, gold, campo, spec["alcance"].replace(" = ", "="))
    if tope:
        M.escribir(con, gold, campo, tope, tot, alcance=spec["alcance"], nota=spec["por_que"])
        print("  marca -> %s <= %s" % (campo, tope))
    con.close()
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabla", nargs="?", default="")
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--estado", action="store_true")
    ap.add_argument("--desde", default="", help="AAAAMM: ignora la marca y lee desde ahi")
    a = ap.parse_args()
    if a.estado or (not a.tabla and not a.todas):
        print("tablas con delta registrado: %s\n" % ", ".join(sorted(REGISTRO)))
        return M.resumen()
    objetivos = sorted(REGISTRO) if a.todas else [a.tabla]
    for t in objetivos:
        if t not in REGISTRO:
            print("  %s no esta en el registro de gold_delta. Anadir una FILA en REGISTRO, "
                  "no un script." % t)
            continue
        delta(t, a.desde)
    return 0


if __name__ == "__main__":
    sys.exit(main())
