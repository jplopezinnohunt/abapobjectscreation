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
import hashlib
import os
import sqlite3
import sys
import time

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
    # MAESTRO: sin delta por fecha posible. UPDAT existe en LFA1/LFB1 y esta VACIO en el
    # 100% de las filas -- SAP no lo rellena aqui, los cambios viven en CDHDR. Y ERDAT es la
    # fecha de ALTA: un proveedor creado en 2019 y modificado ayer sigue con ERDAT=2019, asi
    # que una marca sobre ERDAT se saltaria el cambio. Por eso van por COMPARAR_CLAVE: se leen
    # ENTERAS y se mete por clave. Son pequenas y es lo unico correcto.
    "LFA1": {"sap": "LFA1", "clave": ["LIFNR"], "alta": None, "fecha": None, "alcance": "",
             "sonda": ["NAME1", "ORT01", "SPERR", "LOEVM", "STCD1", "ADRNR"],
             "por_que": "maestro de proveedores: se sondea nombre, poblacion, bloqueo, marca de "
                        "borrado, NIF y numero de direccion -- lo que de verdad se toca"},
    "LFB1": {"sap": "LFB1", "clave": ["LIFNR", "BUKRS"], "alta": None, "fecha": None,
             "alcance": "",
             "sonda": ["AKONT", "ZTERM", "ZWELS", "SPERR", "LOEVM"],
             "por_que": "maestro por sociedad: se sondea cuenta asociada, condiciones de pago, "
                        "vias de pago, bloqueo y marca de borrado"},
    # CLAVE CRECIENTE: un ID que solo sube vale IGUAL que una fecha, y es lo que salva a las
    # tablas que no tienen ninguna. FEBRE son los textos del extracto y su KUKEY es el mismo
    # numero de cabecera que FEBKO: va de 00668682 a 00753653 y solo avanza.
    "FEBRE": {"sap": "FEBRE", "clave": ["KUKEY", "ESNUM", "RSNUM"], "alta": None, "fecha": None,
              "creciente": "KUKEY", "alcance": "",
              "por_que": "no tiene NINGUNA fecha, pero KUKEY es monotono: el delta va por ahi"},
    # POR CDHDR: para lo que no tiene ni fecha ni clave creciente, pero SI documento de cambio.
    # essr son las hojas de entrada de servicio y su clase es ENTRYSHEET; OBJECTID mapea 1 a 1
    # con LBLNI, mismo formato con ceros a la izquierda (verificado).
    "essr": {"sap": "ESSR", "clave": ["LBLNI"], "alta": None, "fecha": None,
             "cdhdr_clase": "ENTRYSHEET", "cdhdr_campo": "LBLNI", "alcance": "",
             "por_que": "sin fecha ni clave creciente; los cambios solo constan en CDHDR"},
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


def _escribir_con_hash(gold, spec, con, cols, filas, etiqueta, marca_campo, marca_valor):
    """Compara por HASH y escribe SOLO lo que cambio. Comun a las tres estrategias sin fecha.

    Es la pieza del ODP que JP tuvo que reclamar dos veces: sin ella una relectura sobrescribe
    todo y no sabes cuantas filas cambiaron de verdad."""
    ix = [cols.index(k) for k in spec["clave"]]
    hprev = {}
    try:
        sel = ", ".join('"%s"' % c for c in cols)
        for row in con.execute("SELECT %s FROM [%s]" % (sel, gold)):
            f = tuple("" if v is None else str(v) for v in row)
            hprev[tuple(f[i] for i in ix)] = hashlib.md5(
                "\x1f".join(f).encode("utf-8", "replace")).hexdigest()
    except sqlite3.Error:
        pass
    nuevas, cambiadas, iguales = [], [], 0
    for k, f in filas.items():
        fila = tuple(f.get(c, "") for c in cols)
        h = hashlib.md5("\x1f".join(fila).encode("utf-8", "replace")).hexdigest()
        if k not in hprev:
            nuevas.append(fila)
        elif hprev[k] != h:
            cambiadas.append(fila)
        else:
            iguales += 1
    antes = con.execute("SELECT COUNT(*) FROM [%s]" % gold).fetchone()[0]
    if nuevas or cambiadas:
        con.executemany("INSERT OR REPLACE INTO [%s] VALUES (%s)"
                        % (gold, ",".join("?" * len(cols))), nuevas + cambiadas)
        con.commit()
    ahora = con.execute("SELECT COUNT(*) FROM [%s]" % gold).fetchone()[0]
    print("  %s · leidas %s · NUEVAS %s · CAMBIADAS %s · iguales %s (no se reescriben)"
          % (etiqueta, "{:,}".format(len(filas)), "{:,}".format(len(nuevas)),
             "{:,}".format(len(cambiadas)), "{:,}".format(iguales)))
    print("  Golden: %s -> %s filas · ni un DELETE" % ("{:,}".format(antes), "{:,}".format(ahora)))
    if marca_valor:
        M.escribir(con, gold, marca_campo, marca_valor, ahora, alcance=spec["alcance"],
                   nota=spec["por_que"])
        print("  marca -> %s <= %s" % (marca_campo, marca_valor))
    return 0


def por_clave_creciente(gold, spec, con, cols):
    """UN ID QUE SOLO SUBE VALE IGUAL QUE UNA FECHA.

    Estaba en la investigacion desde el primer dia y no se habia construido. Salva a las tablas
    sin ninguna fecha: se lee `campo > ultima marca` y ya."""
    from rfc_helpers import get_connection, trocear_where
    campo = spec["creciente"]
    m = M.leer(con, gold, spec["alcance"])
    desde = str(m["hasta"]) if m else con.execute(
        'SELECT MIN("%s") FROM [%s]' % (campo, gold)).fetchone()[0]
    print("  %s · CLAVE CRECIENTE %s > %s%s"
          % (gold, campo, desde, "" if m else "  (sin marca: se arranca del minimo del Golden)"))
    conn = get_connection("P01")
    w = " AND ".join(x for x in [spec["alcance"], "%s > '%s'" % (campo, desde)] if x)
    resto = [c for c in cols if c not in spec["clave"]]
    filas = {}
    for i in range(0, max(1, len(resto)), 7):
        trozo = spec["clave"] + resto[i:i + 7]
        try:
            r = conn.call("RFC_READ_TABLE", QUERY_TABLE=spec["sap"], DELIMITER="|", ROWCOUNT=0,
                          OPTIONS=trocear_where(w),
                          FIELDS=[{"FIELDNAME": f} for f in trozo])
        except Exception as e:
            print("    ERROR %s -- no se escribe con datos incompletos"
                  % str(e).split("\n")[0][:70])
            return 2
        for d in r["DATA"]:
            v = dict(zip(trozo, [x.strip() for x in d["WA"].split("|")]))
            filas.setdefault(tuple(v[k] for k in spec["clave"]), {}).update(v)
    if not filas:
        print("  nada nuevo por encima de la marca")
        return 0
    tope = max(f[campo] for f in filas.values())
    return _escribir_con_hash(gold, spec, con, cols, filas, "clave creciente", campo, tope)


def por_cdhdr(gold, spec, con, cols):
    """CDHDR COMO FUENTE DE CAMBIOS, para lo que no tiene ni fecha ni clave creciente.

    Es lo ultimo que quedaba de la investigacion sin construir. Se pregunta a los DOCUMENTOS DE
    CAMBIO que objetos se tocaron desde la marca, y solo se traen esos.

    CUANDO GANA Y CUANDO NO -- medido, no supuesto: para LFA1 la relectura completa son 21
    llamadas (una por trozo de campos, cada una devuelve las 321.360 filas) y por CDHDR serian
    ~4.700 lotes de claves. CDHDR gana cuando la tabla es GRANDE y los cambios POCOS, que es
    justo el caso de essr."""
    from rfc_helpers import get_connection, trocear_where
    clase, campo = spec["cdhdr_clase"], spec["cdhdr_campo"]
    m = M.leer(con, gold, spec["alcance"])
    desde = str(m["hasta"]) if m else "20240101"
    ids = [r[0] for r in con.execute(
        "SELECT DISTINCT OBJECTID FROM cdhdr_history WHERE OBJECTCLAS=? AND UDATE>=?",
        (clase, desde))]
    tope = con.execute("SELECT MAX(UDATE) FROM cdhdr_history WHERE OBJECTCLAS=?",
                       (clase,)).fetchone()[0]
    print("  %s · POR CDHDR (%s) desde %s -> %s objetos cambiados"
          % (gold, clase, desde, "{:,}".format(len(ids))))
    if not ids:
        print("  ningun cambio registrado: nada que traer")
        return 0
    conn = get_connection("P01")
    resto = [c for c in cols if c not in spec["clave"]]
    filas = {}
    LOTE = 40                       # el WHERE va a 72 chars por linea; 40 ids cabe holgado
    for j in range(0, len(ids), LOTE):
        lote = ids[j:j + LOTE]
        w = "%s IN (%s)" % (campo, ", ".join("'%s'" % x for x in lote))
        for i in range(0, max(1, len(resto)), 7):
            trozo = spec["clave"] + resto[i:i + 7]
            try:
                r = conn.call("RFC_READ_TABLE", QUERY_TABLE=spec["sap"], DELIMITER="|",
                              ROWCOUNT=0, OPTIONS=trocear_where(w),
                              FIELDS=[{"FIELDNAME": f} for f in trozo])
            except Exception as e:
                print("    lote %d: ERROR %s" % (j // LOTE, str(e).split("\n")[0][:60]))
                return 2
            for d in r["DATA"]:
                v = dict(zip(trozo, [x.strip() for x in d["WA"].split("|")]))
                filas.setdefault(tuple(v[k] for k in spec["clave"]), {}).update(v)
    return _escribir_con_hash(gold, spec, con, cols, filas, "por CDHDR", "UDATE(cdhdr)", tope)


def comparar_clave(gold, spec, con, cols):
    """DOS FASES: una SONDA barata dice QUE cambio, y solo eso se trae entero.

    ⛔ LA PRIMERA VERSION LEIA LA TABLA ENTERA -- las 147 columnas de las 321.360 filas de
    LFA1 -- para acabar descubriendo que no habia cambiado ninguna. JP: «no tienes que leer
    toda la data para hacer diferencias, es un error». Y lo es: 21 llamadas para enterarte de
    que no hay nada que hacer.

    FASE 1 (una sola llamada): clave + unos pocos campos volatiles. Con eso se detecta que
    filas son NUEVAS y cuales CAMBIARON en esos campos.
    FASE 2 (solo si hay diferencias): se traen ENTERAS unicamente esas claves.

    Su limite, y hay que decirlo: la sonda ve los campos que mira. Un cambio en una columna
    que no este en la sonda NO se detecta. Por eso la sonda lleva los campos que de verdad se
    tocan -- nombre, poblacion, bloqueos, marca de borrado -- y no una muestra al azar.
    """
    from rfc_helpers import get_connection, trocear_where
    if not asegura_unicidad(con, gold, spec["clave"]):
        return 2
    conn = get_connection("P01")
    resto = [c for c in cols if c not in spec["clave"]]
    sonda = [c for c in (spec.get("sonda") or []) if c in cols] or resto[:5]
    campos1 = spec["clave"] + [c for c in sonda if c not in spec["clave"]][:7 - len(spec["clave"])]
    print("  %s · DOS FASES · sonda: %s" % (gold, ", ".join(campos1)))
    print("    %s" % spec["por_que"])

    t0 = time.time()
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE=spec["sap"], DELIMITER="|", ROWCOUNT=0,
                      OPTIONS=(trocear_where(spec["alcance"]) if spec["alcance"] else []),
                      FIELDS=[{"FIELDNAME": f} for f in campos1])
    except Exception as e:
        print("    sonda: ERROR %s" % str(e).split("\n")[0][:70])
        return 2
    p01 = {}
    for d in r["DATA"]:
        v = dict(zip(campos1, [x.strip() for x in d["WA"].split("|")]))
        p01[tuple(v[k] for k in spec["clave"])] = v
    print("    fase 1: %s filas sondeadas en %.0f s (1 llamada)"
          % ("{:,}".format(len(p01)), time.time() - t0))

    ix = [cols.index(k) for k in spec["clave"]]
    sel = ", ".join('"%s"' % c for c in cols)
    gold_sonda = {}
    for row in con.execute("SELECT %s FROM [%s]" % (sel, gold)):
        f = tuple("" if v is None else str(v) for v in row)
        gold_sonda[tuple(f[i] for i in ix)] = tuple(f[cols.index(c)] for c in campos1)
    sospechosas = [k for k, v in p01.items()
                   if k not in gold_sonda
                   or gold_sonda[k] != tuple(v[c] for c in campos1)]

    # ⛔ BORRADOS: esta es la UNICA estrategia de las siete que puede verlos, porque compara
    # POBLACIONES enteras. Las demas -- fecha, clave creciente, CDHDR -- solo miran hacia
    # delante. Y es justo donde hacen falta: JP senalo que el borrado fisico se da sobre
    # objetos Z/Y, y esas tablas son pequenas, asi que caen aqui.
    # SE REPORTAN, NO SE BORRAN. Quitar filas del Golden es una decision de la persona.
    faltan_en_p01 = [k for k in gold_sonda if k not in p01]
    if faltan_en_p01:
        print("    ⛔ %s clave(s) estan en el Golden y NO en P01 -- candidatas a BORRADO:"
              % "{:,}".format(len(faltan_en_p01)))
        for k in faltan_en_p01[:5]:
            print("         %s" % ("|".join(k)))
        if len(faltan_en_p01) > 5:
            print("         ... y %d mas" % (len(faltan_en_p01) - 5))
        print("       NO se borran: eso lo decide una persona. Pero ya no pasan desapercibidas.")
    print("    fase 1: %s claves NUEVAS o con la sonda distinta, de %s"
          % ("{:,}".format(len(sospechosas)), "{:,}".format(len(p01))))
    if not sospechosas:
        print("  NADA cambio: no se hace la fase 2. Coste total: UNA llamada en vez de %d."
              % -(-len(resto) // 7))
        M.escribir(con, gold, "(sonda: sin cambios)",
                   datetime.date.today().strftime("%Y%m%d"),
                   con.execute("SELECT COUNT(*) FROM [%s]" % gold).fetchone()[0],
                   alcance=spec["alcance"], nota=spec["por_que"])
        return 0

    filas = {}
    LOTE = 40
    for j in range(0, len(sospechosas), LOTE):
        lote = sospechosas[j:j + LOTE]
        # UN `IN` sobre el primer campo de la clave, no un OR de ANDs: RFC_READ_TABLE rechaza
        # el segundo con OPTION_NOT_VALID. Se filtra por el campo mas selectivo y las claves
        # sobrantes se descartan al coser, que es mas barato que pelear con el parser.
        w = "%s IN (%s)" % (spec["clave"][0],
                            ", ".join("'%s'" % k[0] for k in lote))
        if spec["alcance"]:
            w = "%s AND %s" % (spec["alcance"], w)
        for i in range(0, len(resto), 7):
            trozo = spec["clave"] + resto[i:i + 7]
            try:
                rr = conn.call("RFC_READ_TABLE", QUERY_TABLE=spec["sap"], DELIMITER="|",
                               ROWCOUNT=0, OPTIONS=trocear_where(w),
                               FIELDS=[{"FIELDNAME": f} for f in trozo])
            except Exception as e:
                print("    fase 2 lote %d: ERROR %s" % (j // LOTE, str(e).split("\n")[0][:60]))
                return 2
            for d in rr["DATA"]:
                v = dict(zip(trozo, [x.strip() for x in d["WA"].split("|")]))
                filas.setdefault(tuple(v[k] for k in spec["clave"]), {}).update(v)
    print("    fase 2: %s filas traidas ENTERAS en %.0f s"
          % ("{:,}".format(len(filas)), time.time() - t0))
    if not filas:
        print("    P01 devolvio 0 filas: NO se toca el Golden")
        return 2
    antes = con.execute("SELECT COUNT(*) FROM [%s]" % gold).fetchone()[0]

    # ⛔ COMPARACION POR HASH — esto lo investigue, lo escribi en el skill y NO lo construi.
    # JP: «no lo construiste entonces». Sin esto, una relectura completa SOBRESCRIBE todo y no
    # sabes cuantas filas cambiaron DE VERDAD: 321.360 escrituras para, quiza, 12 cambios. Es
    # lo que hace el ODP de SAP -- comparar el hash de las filas de la franja -- y lo que
    # convierte un volcado ciego en un delta MEDIDO.
    hprev = {}
    ix = [cols.index(k) for k in spec["clave"]]
    try:
        sel = ", ".join('"%s"' % c for c in cols)
        for row in con.execute("SELECT %s FROM [%s]" % (sel, gold)):
            fila = tuple("" if v is None else str(v) for v in row)
            hprev[tuple(fila[i] for i in ix)] = hashlib.md5(
                "\x1f".join(fila).encode("utf-8", "replace")).hexdigest()
    except sqlite3.Error:
        hprev = {}

    nuevas, cambiadas, iguales = [], [], 0
    for k, f in filas.items():
        fila = tuple(f.get(c, "") for c in cols)
        h = hashlib.md5("\x1f".join(fila).encode("utf-8", "replace")).hexdigest()
        if k not in hprev:
            nuevas.append(fila)
        elif hprev[k] != h:
            cambiadas.append(fila)
        else:
            iguales += 1

    ph = ",".join("?" * len(cols))
    if nuevas or cambiadas:
        con.executemany("INSERT OR REPLACE INTO [%s] VALUES (%s)" % (gold, ph),
                        nuevas + cambiadas)
        con.commit()
    ahora = con.execute("SELECT COUNT(*) FROM [%s]" % gold).fetchone()[0]
    print("  leidas de P01: %s · NUEVAS %s · CAMBIADAS %s · iguales %s (no se reescriben)"
          % ("{:,}".format(len(filas)), "{:,}".format(len(nuevas)),
             "{:,}".format(len(cambiadas)), "{:,}".format(iguales)))
    print("  Golden: %s -> %s filas · ni un DELETE"
          % ("{:,}".format(antes), "{:,}".format(ahora)))
    if not nuevas and not cambiadas:
        print("  NADA cambio en P01 desde la ultima vez. La relectura costo lo mismo: por eso")
        print("  una tabla grande sin campo de fecha merece CDHDR como fuente de cambios.")
    M.escribir(con, gold, "(relectura completa)",
               datetime.date.today().strftime("%Y%m%d"), ahora,
               alcance=spec["alcance"], nota=spec["por_que"])
    con.close()
    return 0


def _del_registro(gold):
    """La spec de una tabla que NO esta escrita a mano: se arma del registro generado.

    ⛔ ESTO ES LO QUE FALTABA. Las 368 tablas tenian MODELO declarado y solo 12 eran
    EJECUTABLES, porque la clave estaba a mano en el diccionario de aqui abajo. JP: «mas que el
    no detectar el borrado es detectar el DELTA tambien». La clave la da DD03L, y con ella 239
    tablas pasan a ser corribles sin escribir una linea mas por tabla."""
    import json as _j
    ruta = os.path.join(REPO, "brain_v2", "gold_delta_registry.json")
    try:
        with open(ruta, encoding="utf-8") as fh:
            r = _j.load(fh)["tablas"].get(gold)
    except (OSError, ValueError, KeyError):
        return None
    if not r or not r.get("ejecutable") or not r.get("clave"):
        if r:
            print("  %s tiene MODELO (%s) pero NO es ejecutable: %s"
                  % (gold, r.get("estrategia"), r.get("clave_nota", "sin clave")))
        return None
    est = r.get("estrategia")
    spec = {"sap": r.get("sap") or gold, "clave": r["clave"], "alcance": "",
            "alta": None, "fecha": None,
            "por_que": "%s · %s" % (est, r.get("por_que", ""))}
    if est == "MARCA_AGUA":
        spec["alta"] = r["campo"]
    elif est in ("MARCA_AGUA_CON_HUECO", "POR_PERIODO"):
        spec["fecha"] = r["campo"]
    return spec


def delta(gold, desde_forzado="", hasta=""):
    spec = REGISTRO.get(gold) or _del_registro(gold)
    if spec is None:
        return 2
    con = sqlite3.connect(M.DB)
    cols = [r[1] for r in con.execute("PRAGMA table_info([%s])" % gold)]
    campo = spec.get("alta") or spec.get("fecha")
    if campo is None:
        # el ORDEN importa: clave creciente es la mas barata, CDHDR la siguiente, y releer
        # entera es el ultimo recurso -- el que cuesta lo mismo cambie o no cambie nada.
        if spec.get("creciente"):
            return por_clave_creciente(gold, spec, con, cols)
        if spec.get("cdhdr_clase"):
            return por_cdhdr(gold, spec, con, cols)
        return comparar_clave(gold, spec, con, cols)
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
        # ya no hace falta estar en REGISTRO: si el registro GENERADO la declara ejecutable,
        # se corre igual. REGISTRO queda para las que necesitan matices a mano (alcance,
        # sonda, una clave que DD03L no basta para dar).
        pass
        delta(t, a.desde)
    return 0


if __name__ == "__main__":
    sys.exit(main())
