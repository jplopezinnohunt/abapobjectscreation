"""A31 — EL CANAL BATCH INPUT, MINADO ENTERO. Quién genera, qué ejecuta, quién lo corre.

POR QUÉ EXISTE
    Este método encontró ALLOS: una herramienta Excel que genera sesiones por RFC y que se
    llevaba más de un año sin identificar. Encontrada, el método se quedó viviendo SOLO como
    prompt de agente. Un método que solo vive en un prompt no se repite, no se programa, no se
    gatea y no se compara con la corrida del mes pasado.

    La primera mecanización (2026-08-25) fue PEOR que no mecanizarlo: conservó "agrupa APQI por
    PROGID" y tiró once piezas del método — la derivación a transacción, los tres ejes que
    separan una herramienta de otra, la vuelta por el log, el aviso del 92,6%. Una auditoría de
    fidelidad las contó: 18 pérdidas, 11 graves. Esta versión las lleva todas.

LAS CUATRO CAPAS
    LEER         apqi entera (2005→hoy), NO solo la ventana reciente
    INTERPRETAR  PROGID→transacción · CREATOR≠identidad · QSTATE≠tasa · forma del GROUPID
    AGRUPAR      por herramienta, con TRES ejes que solo juntos identifican
    CONTEXTO     qué se ejecutó de verdad (rsau), quién lo corre (SM35 vs SM37), desde cuándo

⛔ LOS CUATRO LÍMITES DEL INSTRUMENTO — cada cifra sale marcada con el suyo

  1. APQI ES UNA COLA, NO UN ARCHIVO. Las sesiones que se procesan BIEN se BORRAN. Todo lo que
     se cuenta aquí es "lo que QUEDA visible", no "lo que pasa". Leer el reparto de QSTATE como
     tasa de fallo da un 92,6% que no existe.
  2. LA TRANSACCIÓN NO SE LEE DE DENTRO. `APQD.VARDATA` es LCHR(7902) y `RFC_READ_TABLE` lo
     rechaza con OPTION_NOT_VALID. No insistas: no es un fallo de la llamada, es el canal. Por
     eso hay que rodear por TSTC y por el log.
  3. `TCODE` VACÍO NO DISTINGUE batch input de job de fondo — el 61% de los cambios de los
     creadores de sesiones lo tiene vacío, y el log NO tiene clase de evento para batch input.
     Lo que sí separa es quién corre **SM35/SM35P** (ejecutar sesiones) frente a **SM37**
     (monitor de jobs).
  4. `APQI.CREATOR` ES UN TEXTO que la herramienta escribe en `BDC_OPEN_GROUP`, y SAP NO lo
     valida: de 14 grafías `*-RFC` medidas, nueve existen en USR02 y cinco no. Contar creadores
     es contar PARÁMETROS, no actores. Y `USERID` —el usuario bajo el que la sesión se
     EJECUTA— es otro campo distinto.

⛔ MIRA DEBAJO DEL TOP
    Se concluyó una vez "el batch input es de viajes" porque `TRIP_*` es el 86,4% de lo que
    queda. Debajo había 1.806 grupos sin mirar, y ahí estaba ALLOS. Este minero NO corta en
    top-N: agrega la cola y la nombra.

⛔ QUE UNA CLAVE CASE NO DICE DE QUÉ ES
    Los GROUPID de ALLOS casaron 200/200 contra `LFA1.LIFNR` y la conclusión "es de acreedores"
    era FALSA: son números de 8 dígitos y los PERNR también lo son. **La prueba de a qué dominio
    pertenece es lo que el usuario CAMBIA (`cdhdr`), no cómo se llama el grupo.**

Uso:  python process_mining/bdc_channel_mining.py [--desde AAAAMMDD] [--sin-log]
Aterriza en: brain_v2/bdc_channel.json · el bus de mineros · algorithm_memory.json
Método: .claude/agents/batch-input-explorer.md
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SALIDA = REPO / "brain_v2" / "bdc_channel.json"
MEMORIA = REPO / "brain_v2" / "methods" / "algorithm_memory.json"
sys.path.insert(0, str(REPO / "process_mining"))

# Qué hace cada generador. Sin esto, la salida dice "143 sesiones de SAPF100" y no dice nada.
QUE_HACE = {
    "SAPMSSY1": "el DESPACHADOR RFC: la sesion vino de FUERA. No identifica la herramienta",
    "RFBIKR00": "carga del maestro de acreedores",
    "RFBIBL01": "carga de documentos contables (report, se lanza por SE38 o job)",
    "SAPF100": "revaluacion en moneda extranjera",
    "RFEBBU00": "extractos bancarios (report)",
    "SAPF180": "ajuste de intereses (report)",
    "HUNUPSR0": "nomina",
    "ZHR_UPDATE_IT0021": "infotipo 0021 = FAMILIA. DATO PERSONAL SENSIBLE",
    "ZHR_UPDATE_IT0167": "infotipo 0167 = PLANES DE SALUD. DATO PERSONAL SENSIBLE",
    "ZHR_RETIRE_COPY_SPI": "cartas de jubilacion",
    "YEBUET01": "extractos UBO",
    "ZMM_BI_MM01_PLANT": "maestro de materiales por centro",
    "/SAPDMC/SAP_LSMW_BI_RECORDING": "LSMW: grabacion de carga (report)",
    "SAPMSBDT": "SHDB, el grabador BDC",
}
# Código PROPIO cuyo fuente no está extraído: escribe en produccion por BDC y no se audita.
SIN_FUENTE = {"ZHR_RETIRE_COPY_SPI", "YEBUET01", "ZHR_UPDATE_IT0167", "ZHR_UPDATE_IT0021",
              "ZMM_BI_MM01_PLANT"}
SENSIBLE = {"ZHR_UPDATE_IT0021", "ZHR_UPDATE_IT0167"}
# Los UNICOS que la fuente verifico como reports (se lanzan por SE38 o por job, sin tcode).
# De los demas sin tcode no se afirma nada: "no se encontro" es correcto, inventar no.
REPORTS = {"RFBIBL01", "RFEBBU00", "SAPF180", "/SAPDMC/SAP_LSMW_BI_RECORDING"}

USTYP_ES = {"A": "Dialogo = PERSONA", "B": "Sistema (tecnico)", "C": "Comunicacion CPIC/RFC",
            "S": "Servicio", "L": "Referencia"}


def gold():
    from gold_ref import GOLD  # type: ignore
    return sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True, timeout=900)


def memorias_de_metodo():
    """PASO 0: leer lo que este instrumento YA enseño, y dejar que cambie lo que hago.

    Se delega en el modulo compartido para que todos los mineros lean el mismo store de la
    misma forma, y para que la implicacion de cada memoria -- que es lo que dice QUE HACER
    DISTINTO -- llegue igual a todos. Antes cada minero tenia su propia lectura, o ninguna: la
    memoria "APQI.CREATOR no es una identidad" estaba escrita el 24-ago y al dia siguiente se
    mecanizo un minero de ese canal que contaba creadores como actores.
    """
    from metodo import lo_que_ya_aprendimos  # type: ignore
    return lo_que_ya_aprendimos("apqi", "creator", "batch input", "bdc", "groupid",
                                "tcode vacio", "claves numericas")


def forma(groupid):
    """EJE 1 — la FORMA del nombre es el dato. Digitos->9, letras->A. Una herramienta emite con
    una PLANTILLA: si mil grupos comparten forma, eso es una plantilla, no una convencion."""
    g = (groupid or "").strip()
    return re.sub(r"[0-9]", "9", re.sub(r"[A-Za-z]", "A", g))


def transacciones_de(con):
    """PROGID -> TRANSACCION via TSTC. Es el paso que convierte un PROGID en algo ACCIONABLE, y
    la version anterior no lo daba: publicaba 'no se puede auditar que hacen' sobre generadores
    que TSTC nombra en una consulta.

    DOS AVISOS, los dos medidos:
      (a) un PROGID SIN transaccion NO es un fallo: RFBIBL01, RFEBBU00, SAPF180 y LSMW son
          REPORTS, se lanzan por SE38 o por job. Decir 'no se encontro' es correcto;
          inventarle una, no.
      (b) el campo TCODE de cdhdr puede contener un PROGRAMA y no una transaccion
          (RE_RHAKTI00 aparece 79.342 veces). Comprobar en TSTC antes de tratarlo como tcode.
    """
    m = defaultdict(list)
    for t in ("tstc", "d01_tstc"):
        try:
            for tcode, prog in con.execute(
                    f"SELECT TCODE, PGMNA FROM [{t}] WHERE TRIM(COALESCE(PGMNA,'')) <> ''"):
                p = (prog or "").strip().upper()
                c = (tcode or "").strip()
                if c and c not in m[p]:
                    m[p].append(c)
        except sqlite3.Error:
            continue
        if m:
            break
    textos = {}
    try:
        for tc, tx in con.execute(
                "SELECT TCODE, TTEXT FROM d01_tstct WHERE SPRSL='E'"):
            textos[(tc or "").strip()] = (tx or "").strip()
    except sqlite3.Error:
        pass
    return m, textos


def tipos_de_usuario(con):
    try:
        return {(b or "").strip().upper(): (t or "").strip()
                for b, t in con.execute("SELECT BNAME, USTYP FROM usr02")}
    except sqlite3.Error:
        return {}


def _en_lotes(con, sql, claves, campo):
    """Cuenta sobre la POBLACION ENTERA, por lotes. SQLite limita los parametros de un IN, y
    esa limitacion se resolvio antes cortando la poblacion a 400 -- que es como se publico un
    '243 de 243, el 100%' que sobre las 1.728 claves reales es el 32%."""
    tot, lote = 0, sorted(claves)
    for i in range(0, len(lote), 900):
        trozo = lote[i:i + 900]
        q = ",".join("?" * len(trozo))
        try:
            tot += con.execute(sql.format(q=q), tuple(trozo)).fetchone()[0]
        except sqlite3.Error:
            return None
    return tot


def prueba_objeto_de_negocio(con, muestra):
    """La clave del GROUPID, contrastada contra los MAESTROS -- con el numero RELLENADO A 10 CON
    CEROS, que es como SAP guarda LIFNR; sin eso casaba 0 de 400.

    Y LA REGLA QUE LO CORRIGE: que una clave CASE no dice de que ES. Los mismos 8 digitos casan
    contra LFA1 y contra PA0001 porque acreedor y PERNR tienen el mismo ancho. La prueba de
    dominio es lo que el usuario CAMBIA, no contra que tabla casa el numero.
    """
    nums = set()
    for g in muestra:
        mm = re.match(r"^(\d{1,8})", (g or "").strip())
        if mm:
            nums.add(mm.group(1))
    if not nums:
        return {}
    # SIN CORTES. La version anterior cortaba a 4.000 grupos y luego a 400 claves, y publicaba
    # "243 de 243 contra las TRES tablas -- el 100%". Sobre las 1.728 claves reales son 560,
    # 565 y 565: el 32%. Ese 100% ademas se escribio como HECHO en algorithm_memory.
    pad = {n.zfill(10) for n in nums}
    corto = {n.zfill(8) for n in nums}
    out = {"claves_probadas": len(nums), "_sin_muestreo": True}
    for tabla, campo, conj in (("lfa1", "LIFNR", pad), ("pa0001", "PERNR", corto),
                               ("hrp1001", "OBJID", corto)):
        n = _en_lotes(con, f"SELECT COUNT(DISTINCT {campo}) FROM [{tabla}] "
                           f"WHERE {campo} IN ({{q}})", conj, campo)
        out[f"casan_contra_{tabla}"] = n
        if n is not None:
            out[f"pct_{tabla}"] = round(100.0 * n / len(conj), 1)
    out["_la_regla"] = (
        "QUE UNA CLAVE CASE NO DICE DE QUE ES. Acreedor y PERNR tienen el mismo ancho, asi que "
        "los mismos numeros casan contra las dos tablas. La prueba de dominio es lo que el "
        "usuario CAMBIA en cdhdr, no contra que maestro casa el numero. Esta comprobacion sirve "
        "para saber que la clave ES un objeto de negocio, no para decidir CUAL")
    return out


def dominio_por_lo_que_cambian(con, creadores_por_herramienta):
    """LA PRUEBA DE DOMINIO, la buena: que OBJETOS cambian de verdad los que crean sesiones.

    ⛔ SEGMENTADO POR HERRAMIENTA, NUNCA MEZCLADO. La version anterior juntaba los 446 creadores
    externos -- 407 de Travel y 40 de ALLOS -- y publicaba el resultado agregado bajo el rotulo
    "la prueba de a que dominio pertenece un canal". Con Travel dentro, el top sale FMRESERV
    966.671 y BELEG 299.899, asi que el cubo llamado HCM_ALLOS quedaba "probado" como FM.

    Es el MISMO error que este bloque existe para no repetir, cometido en espejo: mezclar
    poblaciones en vez de mezclar tablas. Segmentado, ALLOS da HR_IT1018 6.855, HR_IT1001 4.476
    y Y_HR_IT1081 1.214 -- que es HCM, la conclusion ya medida el 24-ago.

    Y sin ventana: `cdhdr_history` cubre mucho mas que el log de auditoria, y recortarla por un
    parametro pensado para rsau tiraba datos sin decirlo.
    """
    out = {}
    for herramienta, creadores in (creadores_por_herramienta or {}).items():
        cs = {c for c in creadores if c}
        if not cs:
            continue
        agg = Counter()
        lote = sorted(cs)
        roto = False
        for i in range(0, len(lote), 900):
            trozo = lote[i:i + 900]
            q = ",".join("?" * len(trozo))
            try:
                for clase, n in con.execute(
                        f"""SELECT OBJECTCLAS, COUNT(*) FROM cdhdr_history
                            WHERE UPPER(TRIM(USERNAME)) IN ({q}) GROUP BY 1""", tuple(trozo)):
                    agg[clase] += n
            except sqlite3.Error:
                roto = True
                break
        if roto:
            continue
        out[herramienta] = {
            "creadores": len(cs),
            "objetos_que_cambian": [{"clase": c, "cambios": n} for c, n in agg.most_common(8)],
        }
    out["_por_que"] = ("la prueba de a que DOMINIO pertenece un canal es lo que su gente CAMBIA "
                       "-- no como se llama el grupo, ni contra que maestro casa la clave. Y "
                       "SEGMENTADO por herramienta: mezclar Travel con ALLOS hace que el cubo "
                       "de ALLOS salga 'probado' como FM")
    return out


def quien_ejecuta_sesiones(con, desde):
    """LIMITE 3 hecho medida: SM35/SM35P (ejecutar sesiones) frente a SM37 (monitor de jobs).
    Es la unica senal barata que separa al operador de sesiones del operador de jobs, porque
    TCODE vacio no distingue nada."""
    out = {}
    for tcode, etiqueta in (("SM35", "ejecuta sesiones"), ("SM35P", "ejecuta sesiones"),
                            ("SM37", "monitor de JOBS, no de sesiones")):
        try:
            filas = con.execute(
                """SELECT SLGUSER, COUNT(*) FROM rsau_audit_history
                   WHERE SLGTC = ? AND SAL_DATE >= ? GROUP BY 1 ORDER BY 2 DESC LIMIT 6""",
                (tcode, desde)).fetchall()
        except sqlite3.Error:
            continue
        if filas:
            out[tcode] = {"significa": etiqueta,
                          "top": [{"usuario": u, "veces": n} for u, n in filas]}
    out["_por_que"] = ("TCODE vacio NO distingue batch input de job de fondo -- el 61% de los "
                       "cambios de los creadores de sesiones lo tiene vacio, y el log no tiene "
                       "clase de evento para batch input. Quien corre SM35 ejecuta SESIONES; "
                       "quien corre SM37 mira JOBS")
    return out


def lo_que_de_verdad_se_ejecuto(con, creadores, desde):
    """LA VUELTA POR EL LOG. VARDATA esta cerrado, pero cuando alguien CORRE la sesion las
    transacciones se ejecutan bajo su usuario y SI quedan en rsau.

    Es CORRELACION TEMPORAL, no causalidad: se reporta como 'que arrancaron el mismo dia esos
    mismos usuarios', nunca como 'que hizo la sesion'.
    """
    if not creadores:
        return {}
    q = ",".join("?" * len(creadores))
    try:
        filas = con.execute(
            f"""SELECT SLGTC, COUNT(*) FROM rsau_audit_history
                WHERE TXSUBCLSID = 'Transaction Start' AND SAL_DATE >= ?
                  AND UPPER(TRIM(SLGUSER)) IN ({q}) AND TRIM(COALESCE(SLGTC,'')) <> ''
                GROUP BY 1 ORDER BY 2 DESC LIMIT 15""",
            (desde,) + tuple(creadores)).fetchall()
    except sqlite3.Error:
        return {}
    return {"transacciones_que_arrancan": [{"tcode": t, "veces": n} for t, n in filas],
            "_como_se_lee": ("CORRELACION TEMPORAL, no causalidad: son las transacciones que "
                             "esos mismos usuarios arrancaron en la ventana, no lo que la sesion "
                             "ejecuto. Es el unico rodeo posible porque APQD.VARDATA es LCHR y "
                             "RFC_READ_TABLE lo rechaza con OPTION_NOT_VALID")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="20250101",
                    help="ventana para el cruce con el log. La COLA se lee entera siempre")
    ap.add_argument("--sin-log", action="store_true", help="salta los cruces con rsau/cdhdr")
    a = ap.parse_args()

    mem = memorias_de_metodo()
    mem.avisar()
    # Y que CAMBIE lo que hago, no solo que se imprima: si hay una memoria que desaconseja
    # tratar CREATOR como una identidad, este minero no puede publicar "N creadores" a secas.
    if mem.prohibe("creator no es una identidad usuario"):
        globals()["_CREATOR_NO_ES_ACTOR"] = True

    con = gold()
    tcodes, textos_tc = transacciones_de(con)
    ustyp = tipos_de_usuario(con)

    # ---- LA COLA ENTERA, no una ventana. El argumento mas fuerte de este canal es que lleva
    #      casi VEINTE anos activo, y la ventana de 2025 miraba el 17,7% de las sesiones.
    filas = con.execute("""SELECT PROGID, GROUPID, CREATOR, USERID, CREDATE, QSTATE
                           FROM apqi""").fetchall()
    total = len(filas)

    gen = defaultdict(lambda: {"sesiones": 0, "creator_strings": set(), "userids": set(),
                               "estados": Counter(), "primera": None, "ultima": None,
                               "por_ano": Counter()})
    ext_grupos, ext_creadores, ext_userids = [], set(), set()
    ext_creadores_por_grupo = []      # paralelo a ext_grupos: quien creo CADA sesion externa
    for prog, grupo, creador, userid, fecha, estado in filas:
        p = (prog or "").strip()
        g = gen[p]
        g["sesiones"] += 1
        g["creator_strings"].add((creador or "").strip())
        g["userids"].add((userid or "").strip())
        g["estados"][(estado or "").strip() or "(vacio)"] += 1
        f = (fecha or "").strip()
        if f:
            g["primera"] = min(g["primera"] or f, f)
            g["ultima"] = max(g["ultima"] or f, f)
            g["por_ano"][f[:4]] += 1
        if p == "SAPMSSY1":
            ext_grupos.append((grupo or "").strip())
            ext_creadores_por_grupo.append((creador or "").strip().upper())
            ext_creadores.add((creador or "").strip())
            ext_userids.add((userid or "").strip())

    # ---- GENERADORES, TODOS. Sin corte: la cola larga es donde estuvo ALLOS un ano.
    generadores = []
    for p, g in sorted(gen.items(), key=lambda kv: -kv[1]["sesiones"]):
        tcs = tcodes.get(p.upper(), [])
        propio = p[:1] in ("Z", "Y")
        generadores.append({
            "progid": p,
            "que_hace": QUE_HACE.get(p),
            "transacciones_derivadas": tcs[:6] or None,
            # SIN TCODE NO SIGNIFICA "ES UN REPORT". SAPMSSY1 es el DESPACHADOR RFC y salia con
            # las dos cosas a la vez en el mismo registro. Y de los que no tienen tcode, la
            # fuente solo verifico cuatro como reports: afirmarlo de los demas es inventar.
            "_sin_transaccion": (
                "es el DESPACHADOR RFC: no tiene ni debe tener transaccion" if p == "SAPMSSY1"
                else "es un REPORT verificado: se lanza por SE38 o por job" if p in REPORTS
                else "no tiene tcode en TSTC. NO se ha verificado que sea un report: decir 'no "
                     "se encontro' es correcto, inventarle una categoria no") if not tcs else None,
            "texto_de_la_transaccion": [textos_tc.get(t) for t in tcs[:3] if textos_tc.get(t)],
            "sesiones": g["sesiones"],
            "creator_strings": len(g["creator_strings"]),
            "usuarios_de_ejecucion": len([u for u in g["userids"] if u]),
            "estados": dict(g["estados"]),
            # El aviso viaja CON la cifra, no en una nota general al principio del fichero: quien
            # lee un generador concreto lee esta linea, no el preambulo. La puerta de obediencia
            # (A37) lo comprueba sobre la salida, no sobre el codigo.
            "_estados_no_es_una_tasa": ("NO dividir entre el total: 'F' significa FINALIZADA CON "
                                        "EXITO y la cola BORRA los exitos, asi que el "
                                        "denominador esta sesgado por construccion"),
            "activo_desde": g["primera"], "ultima": g["ultima"],
            "por_ano": dict(sorted(g["por_ano"].items())),
            "autoria": ("PROPIO" if propio else
                        "EXTERNO por RFC" if p == "SAPMSSY1" else "de SAP"),
            "codigo_extraido": (False if p in SIN_FUENTE else None) if propio else None,
            "dato_personal_sensible": True if p in SENSIBLE else None,
        })

    # ---- LOS TRES EJES sobre lo EXTERNO. Ninguno basta solo.
    # EL EJE 1 MIDE CUANTOS GRUPOS COMPARTEN PLANTILLA, no cuantas sesiones. Contando sesiones
    # decia "50.166 grupos" con forma AAAA_AAAAAA cuando hay DOS (TRIP_CREATE/TRIP_MODIFY), y
    # 3.535 para 99999999A999 cuando los distintos son 1.346 -- que es justo la cifra que el
    # metodo cita como la prueba de que hay una plantilla detras.
    formas, formas_ses = Counter(), Counter()
    for g in set(ext_grupos):
        formas[forma(g)] += 1
    for g in ext_grupos:
        formas_ses[forma(g)] += 1
    suf = Counter()
    for g in set(ext_grupos):
        m = re.match(r"^\d{1,8}([A-Z0-9]{2,4})$", g, re.I)
        if m:
            suf[m.group(1).upper()] += 1
    creador_patron = Counter()
    for c in ext_creadores:
        creador_patron["sufijo *-RFC o *_RFC" if re.search(r"[-_]RFC$", c, re.I)
                        else "sin sufijo tecnico"] += 1
    no_en_usr02 = sorted(c for c in ext_creadores if c and c.upper() not in ustyp)

    ejes = {
        "_regla": ("los tres ejes solo identifican JUNTOS. Ninguno basta: una forma repetida "
                   "puede ser una convencion humana, un sufijo -RFC puede ser una cuenta real, "
                   "y una cadencia larga puede ser un job de SAP"),
        "eje_1_forma_del_groupid": {
            "_que_mide": ("una herramienta emite con PLANTILLA. Digitos->9, letras->A: si "
                          "muchos grupos comparten forma, eso es una plantilla"),
            "top": [{"forma": f, "grupos_distintos": n, "sesiones": formas_ses[f]}
                    for f, n in formas.most_common(8)],
            "formas_distintas": len(formas),
            "_grupos_no_es_sesiones": ("una plantilla se prueba con GRUPOS distintos, no con "
                                       "sesiones: TRIP_* son 50.166 sesiones y solo DOS grupos")},
        "eje_2_patron_del_creator": {
            "_que_mide": "un sufijo repetido -RFC / _RFC senala una herramienta, no una persona",
            "reparto": dict(creador_patron),
            "grafias_que_NO_existen_en_usr02": no_en_usr02[:14],
            "_limite_4": ("CREATOR es un TEXTO de BDC_OPEN_GROUP que SAP no valida. "
                          f"{len(no_en_usr02)} de {len(ext_creadores)} grafias no existen como "
                          "usuario: contar creadores es contar PARAMETROS, no actores")},
        "eje_3_cadencia": {
            "_que_mide": "una herramienta sostenida en anos no es una carga puntual",
            "por_ano": dict(sorted(gen["SAPMSSY1"]["por_ano"].items())),
            "activo_desde": gen["SAPMSSY1"]["primera"]},
        "sufijos_del_groupid": {
            "top": [{"sufijo": s, "grupos": n} for s, n in suf.most_common(8)],
            "_cuidado": ("el sufijo es A VECES la TRANSACCION (PA30) y a veces un codigo de "
                         "oficina. Afirmar 'codigo de oficina' como hecho fijo enmascara los "
                         "casos en que es la transaccion, que es la unica pista directa de que "
                         "se ejecuta")},
        "prueba_contra_maestros": prueba_objeto_de_negocio(con, ext_grupos[:4000]),
    }

    # ---- LA COLA LARGA, nombrada. Nunca un top-N a secas.
    conocidas = {"TRAVEL": [], "HCM_ALLOS": [], "SIN_GRAMATICA": []}
    cre_por_herramienta = {"TRAVEL": set(), "HCM_ALLOS": set(), "SIN_GRAMATICA": set()}
    for g, c in zip(ext_grupos, ext_creadores_por_grupo):
        if g.upper().startswith("TRIP_"):
            k = "TRAVEL"
        elif re.match(r"^\d{1,8}[A-Z0-9]{2,4}$", g, re.I):
            k = "HCM_ALLOS"
        else:
            k = "SIN_GRAMATICA"
        conocidas[k].append(g)
        cre_por_herramienta[k].add(c)
    cola = {
        k: {"sesiones": len(v), "grupos_distintos": len(set(v)),
            "muestra": sorted(set(v))[:12]} for k, v in conocidas.items()}
    cola["_mira_debajo_del_top"] = (
        "se concluyo una vez 'el batch input es de viajes' porque TRIP_* es el 86,4% de lo que "
        "queda. Debajo habia 1.806 grupos sin mirar, y ahi estaba ALLOS. Por eso este bloque no "
        "corta: la cola se agrega y se nombra")
    cola["SIN_GRAMATICA"]["_que_falta_para_cerrarlo"] = (
        "para nombrar la herramienta que hay detras hace falta: su usuario tecnico (cruzar "
        "CREATOR y USERID contra USR02), su destino RFC si lo tiene, y su programa. Un cubo "
        "desconocido que no dice que le falta no genera trabajo: se queda ahi corrida tras "
        "corrida")

    # ---- CONTEXTO: quien lo corre, que se ejecuta, que cambian
    # LA VENTANA REAL DEL LOG, leida del dato. Declarar "20250101" cuando rsau empieza en
    # 20260203 es peor que no declarar nada: el parametro no recortaba nada y la cifra decia
    # salir de una ventana que no existe.
    try:
        _lo, _hi = con.execute("SELECT MIN(SAL_DATE), MAX(SAL_DATE) "
                               "FROM rsau_audit_history").fetchone()
    except sqlite3.Error:
        _lo = _hi = None
    ventana_real = {"desde": _lo, "hasta": _hi,
                    "_ojo": ("es la ventana del LOG, no la de la cola: apqi cubre desde 2005. "
                             "Poner cifras de las dos juntas sin decirlo compara denominadores "
                             "distintos")}

    ctx = {"ventana_real_del_log": ventana_real}
    if not a.sin_log:
        # SIN CORTE ALFABETICO. Antes se cogian 60 de 446 creadores ordenados alfabeticamente
        # -- solo 9 de los 40 de ALLOS caian dentro -- y nada en la salida decia que habia
        # muestra. Con los 446 los mismos recuentos salen 30 veces mayores.
        todos = {c.upper() for c in ext_creadores if c}
        ctx["quien_ejecuta_sesiones"] = quien_ejecuta_sesiones(con, _lo or "00000000")
        ctx["lo_que_de_verdad_se_ejecuto"] = lo_que_de_verdad_se_ejecuto(
            con, tuple(sorted(todos)), _lo or "00000000")
        ctx["dominio_por_lo_que_cambian"] = dominio_por_lo_que_cambian(
            con, {k: {c.upper() for c in v if c} for k, v in cre_por_herramienta.items()})

    # QUIEN ENTRA: todos, y los que NO existen en USR02 primero -- que es lo que este bloque
    # existe para ensenar. El corte alfabetico de 20 los dejaba fuera precisamente a ellos.
    entra = {c: USTYP_ES.get(ustyp.get(c.upper()), "NO EXISTE en USR02")
             for c in sorted(ext_creadores) if c}
    ctx["quien_entra"] = {
        "total": len(entra),
        "NO_EXISTEN_en_usr02": sorted(k for k, v in entra.items() if v.startswith("NO EXISTE")),
        "por_tipo": dict(Counter(entra.values())),
        "_creator_no_es_identidad": ("es un texto de BDC_OPEN_GROUP que SAP no valida: contar "
                                     "creadores es contar PARAMETROS, no actores"),
    }
    con.close()

    doc = {
        "_algoritmo": "A31_bdc_channel_mining",
        "_metodo": ".claude/agents/batch-input-explorer.md",
        "_LIMITES_DEL_INSTRUMENTO": {
            "1_es_una_cola": ("APQI BORRA las sesiones que se procesan bien. Todo recuento de "
                              "aqui es LO QUE QUEDA, no lo que pasa"),
            "2_la_transaccion_no_se_lee_de_dentro": (
                "APQD.VARDATA es LCHR(7902) y RFC_READ_TABLE lo rechaza con OPTION_NOT_VALID. "
                "No es un fallo de la llamada, es el canal. Por eso se rodea por TSTC y por rsau"),
            "3_tcode_vacio_no_distingue": (
                "el 61% de los cambios de los creadores de sesiones tiene TCODE vacio y el log "
                "no tiene clase de evento para batch input. Lo que separa es SM35 vs SM37"),
            "4_creator_no_es_identidad": (
                "es un texto de BDC_OPEN_GROUP que SAP no valida, y USERID -- el usuario bajo "
                "el que se EJECUTA -- es otro campo"),
        },
        "_qstate_no_es_una_tasa": (
            "NO dividir los estados entre el total. 'F' significa FINALIZADA CON EXITO, y el "
            "denominador esta sesgado por construccion porque la cola borra los exitos: leerlo "
            "como tasa de fallo da un 92,6% que no existe"),
        "_cuidado_con_la_tendencia": (
            "la serie es mas fiable hacia el PRESENTE que hacia atras, porque el pasado esta "
            "mas borrado. NO leer la pendiente como actividad: todo canal antiguo parece crecer"),
        "sesiones_en_la_cola": total,
        "ventana_del_cruce_con_el_log": a.desde,
        "generadores": generadores,
        "lo_externo_por_rfc": {"sesiones": len(ext_grupos),
                               "grupos_distintos": len(set(ext_grupos)),
                               "creator_strings": len(ext_creadores),
                               "usuarios_de_ejecucion": len([u for u in ext_userids if u]),
                               "tres_ejes": ejes, "por_gramatica": cola},
        "contexto": ctx,
        "el_hueco": {
            "generadores_propios_sin_fuente_extraida": sorted(SIN_FUENTE),
            "con_dato_personal_sensible": sorted(SENSIBLE),
            "_que_pasa": ("codigo PROPIO que ESCRIBE en produccion por BDC y cuyo fuente no "
                          "esta extraido, asi que no se puede auditar que hace. Dos tocan datos "
                          "personales sensibles: el infotipo 0021 es FAMILIA y el 0167 PLANES "
                          "DE SALUD")},
        "_memorias_de_metodo_leidas": [m.get("fact") for m in mem[:8]],
    }
    SALIDA.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- publicar, y consultar ANTES lo que saben los demas
    try:
        from mining_bus import publicar, consultar, preguntar
        for g in generadores:
            # CONSULTAR DE VERDAD. `if otros: pass` estaba aqui, listado como corregido en un
            # commit y sin corregir: se llamaba a consultar() y se tiraba el resultado. Leer lo
            # que otro minero ya dijo del mismo sujeto es la mitad del mecanismo de choque.
            otros = [o for o in consultar(g["progid"])
                     if not str(o.get("minero", "")).startswith("A31")]
            tc = (", ".join(g["transacciones_derivadas"] or [])
                  or ("el DESPACHADOR RFC, sin transaccion" if g["progid"] == "SAPMSSY1"
                      else "report verificado, sin tcode" if g["progid"] in REPORTS
                      else "sin tcode en TSTC; NO verificado como report"))
            hallazgo = (f"genera {g['sesiones']} sesiones de batch input desde "
                        f"{g['activo_desde']}; transaccion: {tc}. "
                        f"{g['que_hace'] or ''}").strip()
            if otros:
                # Lo que ya dijeron los demas viaja CON el hallazgo, para que el desacuerdo sea
                # visible en el sitio donde alguien lo va a leer.
                hallazgo += (" | YA DICHO POR OTROS: " +
                             "; ".join(f"{o['minero'].split('/')[0]}: "
                                       f"{str(o['hallazgo'])[:70]}" for o in otros[:2]))
            publicar("A31_bdc_channel_mining", "CANAL_Y_ACTOR", g["progid"], hallazgo,
                     evidencia="apqi entera x TSTC, brain_v2/bdc_channel.json",
                     aspecto="genera_batch_input")

        # PREGUNTAR: donde este minero llega a su limite, lo dice en vez de callarse.
        sin_nombre = cola.get("SIN_GRAMATICA", {})
        if isinstance(sin_nombre, dict) and sin_nombre.get("sesiones"):
            preguntar("A31_bdc_channel_mining", "EXTERNO:SIN_GRAMATICA",
                      f"{sin_nombre['sesiones']} sesiones externas por RFC con "
                      f"{sin_nombre['grupos_distintos']} grupo(s) que no encajan en ninguna "
                      "gramatica conocida. ¿Que herramienta las genera?",
                      para="CANAL_Y_ACTOR",
                      porque=("mi instrumento solo ve la cabecera de la sesion: APQD.VARDATA es "
                              "LCHR y RFC_READ_TABLE lo rechaza. Quien mire el destino RFC o el "
                              "programa que llama puede cerrarlo"))
        no_usr = ctx.get("quien_entra", {}).get("NO_EXISTEN_en_usr02") or []
        if no_usr:
            preguntar("A31_bdc_channel_mining", "CREATOR_SIN_USUARIO",
                      f"{len(no_usr)} grafias aparecen como CREATOR de sesiones y NO existen en "
                      f"USR02: {', '.join(no_usr[:6])}. ¿Son cuentas borradas, o texto que la "
                      "herramienta escribe sin validar?",
                      para="CANAL_Y_ACTOR",
                      porque=("APQI.CREATOR es un parametro de BDC_OPEN_GROUP y SAP no lo "
                              "valida; desde aqui no se distingue una cuenta borrada de un "
                              "texto inventado"))
        for k, v in cola.items():
            if isinstance(v, dict) and v.get("sesiones"):
                publicar("A31_bdc_channel_mining", "CANAL_Y_ACTOR", f"EXTERNO:{k}",
                         f"{v['sesiones']} sesiones externas por RFC en "
                         f"{v['grupos_distintos']} grupos",
                         evidencia="apqi PROGID=SAPMSSY1 por forma del GROUPID",
                         aspecto="genera_batch_input")
    except Exception as e:
        print(f"  AVISO: no se pudo usar el bus ({type(e).__name__})")

    # ---- devolver al store de METODO lo aprendido del instrumento
    try:
        M = json.loads(MEMORIA.read_text(encoding="utf-8"))
        hechos = {m.get("fact", "")[:60] for m in M["memories"]}
        nuevo = (f"APQI tiene {total:,} sesiones desde {min((g['primera'] for g in gen.values() if g['primera']), default='?')}: la ventana "
                 "de 2025 mira menos del 18%. El argumento mas fuerte de este canal es su "
                 "ANTIGUEDAD, y una ventana corta lo borra.")
        if nuevo[:60] not in hechos:
            base = {k: None for k in M["memories"][0]}
            base.update({"fact": nuevo, "kind": "INSTRUMENT",
                         "learned_by": "A31_bdc_channel_mining",
                         "implication": ("no acotar apqi por fecha al medir el canal; la ventana "
                                         "solo vale para el cruce con el log"),
                         "session": 103, "source": "medido 2026-08-25"})
            M["memories"].append(base)
            MEMORIA.write_text(json.dumps(M, indent=2, ensure_ascii=False), encoding="utf-8")
            print("  memoria de metodo escrita")
    except Exception:
        pass

    print(f"\nCANAL BATCH INPUT — LA COLA ENTERA: {total:,} sesiones "
          f"(desde {min((g['primera'] for g in gen.values() if g['primera']), default='?')})")
    print("  OJO: la cola BORRA lo que se proceso bien. Esto es lo que QUEDA, no lo que pasa.\n")
    print(f"  {'generador':30s} {'sesiones':>9s} {'desde':>9s}  transaccion / que hace")
    for g in generadores[:16]:
        tc = (", ".join(g["transacciones_derivadas"] or [])[:26]
              or ("(despachador RFC)" if g["progid"] == "SAPMSSY1"
                  else "(report verificado)" if g["progid"] in REPORTS
                  else "(sin tcode; no verificado)"))
        print(f"  {g['progid'][:30]:30s} {g['sesiones']:>9,} {str(g['activo_desde'])[:8]:>9s}  "
              f"{tc}")
    if len(generadores) > 16:
        resto = sum(g["sesiones"] for g in generadores[16:])
        print(f"  {'... y ' + str(len(generadores) - 16) + ' generadores mas':30s} "
              f"{resto:>9,}   <- LA COLA, nombrada y no tirada")
    print("\n  lo externo por RFC, por gramatica del GROUPID:")
    for k, v in cola.items():
        if isinstance(v, dict) and v.get("sesiones"):
            print(f"    {k:16s} {v['sesiones']:>7,} sesiones · {v['grupos_distintos']:>5} grupos")
    print(f"\n  tres ejes: {len(formas)} formas distintas · "
          f"{len(no_en_usr02)} grafias de CREATOR que NO existen en USR02")
    print(f"\n-> {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
