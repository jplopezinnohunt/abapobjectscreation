"""build_interface_inventory.py — every interface, as a RECORD (s097).

**Prose is not reliable knowledge.** Everything this session discovered about how the system
is written to — the SuccessFactors service set, the custom HTTP surface, who generates the
batch-input sessions, which destinations are live — was landing inside claim TEXT. A claim
is durable, but its body is a paragraph: nothing can query it, nothing can diff it next
month, and nothing notices when it goes stale. That is the same failure as the write-channel
taxonomy sitting in markdown tables, committed one layer up.

So this derives ONE STRUCTURED INVENTORY of every inbound and outbound path, from the golden
tables, keyed on the artifact that carries it:

    RFC_DESTINATION   rfcdes x observed traffic          configured, and whether it is used
    IDOC              edidc                              message type, partners, direction
    WEB_SERVICE       wsheader                           definition, author, and SAP vs ours
    HTTP_SERVICE      icfservice / icfservloc            the ICF surface, and what is ACTIVE
    BATCH_INPUT       apqi                                who GENERATES the sessions, and state
    FILE / DBCON      the declared registry               parsed from the integration map

**Author is not a prefix.** A service carrying no Z/Y prefix can still be ours in every sense
that matters: the SuccessFactors replication set is SAP-DELIVERED and ACTIVATED here, and a
prefix filter erased the live SF-to-ECC channel from the map earlier today. So "ours" is
decided by AUTHOR, never by name shape.

**What each record carries:** what it is, how it arrives, whether there is EVIDENCE it runs,
and — when there is not — WHY not, because "we cannot see it" and "it does not happen" are
different facts and only one of them is a finding.

Emits: brain_v2/interface_inventory.json
"""
import json
import sqlite3
import sys
import re
from collections import Counter, defaultdict
from pathlib import Path

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "process_mining"))
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None

REPO = Path(__file__).resolve().parent.parent
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
DECLARED = REPO / "brain_v2" / "integration_channels.json"
ATTRIB = REPO / "brain_v2" / "change_attribution.json"
OUT = REPO / "brain_v2" / "interface_inventory.json"
CALLERS = REPO / "brain_v2" / "rfc_caller_apps.json"

# El nombre lo pone A4, no este script. Escribir 'Substrate_Technical' aqui cuando el
# clasificador dice 'Technical_Substrate' partia el mismo dominio en dos etiquetas y ninguna
# busqueda encontraba las dos mitades.
SUSTRATO = {"Technical_Substrate", "Basis_Security", "CTS_Transport"}

# TODO CORTE SE PUBLICA. "El resto sin clasificar es el sensor": un umbral que no dice cuanto
# tiro convierte una poblacion truncada en una cobertura, y nadie lo nota. Medido: el corte de
# 1.000 llamadas descartaba 1.843 de 2.098 cuentas RFC sin dejar rastro.
DESCARTES = {}

# Que hace cada generador de batch input. Sin esto, "143 sesiones de SAPF100" no dice nada.
QUE_HACE_BDC = {
    "SAPMSSY1": "el DESPACHADOR RFC: vino de FUERA. No identifica la herramienta",
    "RFBIKR00": "carga del maestro de acreedores",
    "RFBIBL01": "carga de documentos contables (report)",
    "SAPF100": "revaluacion en moneda extranjera",
    "RFEBBU00": "extractos bancarios (report)",
    "HUNUPSR0": "nomina",
    "ZHR_UPDATE_IT0021": "infotipo 0021 = FAMILIA. DATO PERSONAL SENSIBLE",
    "ZHR_UPDATE_IT0167": "infotipo 0167 = PLANES DE SALUD. DATO PERSONAL SENSIBLE",
    "ZHR_RETIRE_COPY_SPI": "cartas de jubilacion",
    "YEBUET01": "extractos UBO",
    "ZMM_BI_MM01_PLANT": "maestro de materiales por centro",
    "SAPMSBDT": "SHDB, el grabador BDC",
}
# Codigo PROPIO que escribe en produccion por BDC y cuyo fuente NO esta extraido.
BDC_SIN_FUENTE = {"ZHR_RETIRE_COPY_SPI", "YEBUET01", "ZHR_UPDATE_IT0167", "ZHR_UPDATE_IT0021",
                  "ZMM_BI_MM01_PLANT"}
BDC_SENSIBLE = {"ZHR_UPDATE_IT0021", "ZHR_UPDATE_IT0167"}

# ---------------------------------------------------------------------------------------------
# NATURALEZA: que le hace al sistema. Es un eje DISTINTO del dominio, y sin el el inventario
# dice donde pasa algo pero no que pasa. Las tres no valen lo mismo cuando fallan:
#   LECTURA       -- si se rompe, cuesta un informe. Nada queda inconsistente.
#   TRANSACCIONAL -- si se rompe o se duplica, cuesta DINERO: documentos, pagos, compromisos.
#   MASTER_DATA   -- si escribe mal, corrompe todo lo que venga detras, y en silencio.
VERBO_LEE = ("_GET", "GET_", "GETLIST", "GETDETAIL", "_READ", "READ_", "_LIST", "_DISPLAY",
             "_SELECT", "_EXPORT", "_EXTRACT", "_CHECK", "_EXISTENCE", "_FIND", "_INFO",
             "_GETSTATUS", "_QUERY", "_SEARCH")
VERBO_ESCRIBE = ("_CREATE", "CREATE_", "_CHANGE", "CHANGE_", "_POST", "POST_", "_MODIFY",
                 "_UPDATE", "UPDATE_", "_DELETE", "_INSERT", "_SAVE", "_CANCEL", "_REVERSE",
                 "_RELEASE", "_BLOCK", "_MAINTAIN", "_REPLICATE", "_UPLOAD", "_LOAD")
# Objetos que son MAESTRO. Coincide con el registro de Master_Data_Governance (10 tipos).
OBJ_MAESTRO = ("VENDOR", "CREDITOR", "LFA1", "CUSTOMER", "DEBITOR", "KNA1", "BUPA", "BP_",
               "BUSINESSPARTNER", "GLACC", "GL_ACCOUNT", "SKB1", "SKA1", "COSTCENTER", "KOSTL",
               "CSKS", "FUNDSCENTER", "FICTR", "FUND_", "FMCI", "COMMITMENTITEM", "PROJECT",
               "WBS", "PRPS", "PSPNR", "EMPLOYEE", "PERNR", "INFOTYPE", "IT00", "HRP1",
               "MATERIAL", "MATNR", "MM01", "ASSET", "ANLA", "HOUSEBANK", "BNKA", "PROFITCENTER",
               "ORGUNIT", "POSITION", "ORGSTRUCTURE", "COSTELEMENT", "CSKB")
# Objetos que son DOCUMENTO: nacen, se contabilizan y mueven saldo.
OBJ_DOCUMENTO = ("_PO_", "PURCHASEORDER", "REQUISITION", "INVOICE", "GOODSMVT", "ACC_DOCUMENT",
                 "ACCDOC", "FI_POST", "PAYMENT", "REGUH", "RESERVATION", "FMR", "KBL", "TRIP",
                 "TRAVEL", "BILLING", "DELIVERY", "SETTLEMENT", "JOURNAL", "BELEG", "EARMARKED",
                 "BUDGET", "FMBB", "TRANSFERPRICE", "PAYROLL", "TIMESHEET", "CATS")


def _naturaleza_fm(fm):
    """LECTURA / TRANSACCIONAL / MASTER_DATA / None a partir del nombre del modulo.

    El nombre de un modulo de funcion SAP no es decorativo: el verbo dice si lee o escribe y el
    objeto dice sobre que. Es la misma senal que usa cualquiera que lea SAP, hecha explicita.
    """
    u = (fm or "").upper()
    if not u:
        return None
    escribe = any(v in u for v in VERBO_ESCRIBE)
    lee = any(v in u for v in VERBO_LEE)
    if not escribe and lee:
        return "LECTURA"
    if escribe:
        if any(o in u for o in OBJ_MAESTRO):
            return "MASTER_DATA"
        if any(o in u for o in OBJ_DOCUMENTO):
            return "TRANSACCIONAL"
        return "TRANSACCIONAL"      # escribe algo que no sabemos clasificar: sigue escribiendo
    return None


# Modulos que llama TODO el mundo: existen para que el canal funcione, no para lo que hace.
FONTANERIA = {"RFCPING", "RFC_PING", "RFC_SYSTEM_INFO", "RFC_READ_TABLE", "BAPI_TRANSACTION_COMMIT",
              "BAPI_TRANSACTION_ROLLBACK", "/SAPDS/RFC_READ_TABLE2", "RFC_GET_FUNCTION_INTERFACE",
              "SYSTEM_RESET_RFC_SERVER", "RFC_METADATA_GET", "Z_RFC_READ_TABLE"}

try:
    CANALES = json.loads(CALLERS.read_text(encoding="utf-8")).get("channels") or {}
except Exception:
    CANALES = {}


try:
    _CALLERS_RAW = json.loads(CALLERS.read_text(encoding="utf-8"))
except Exception:
    _CALLERS_RAW = {}
APPS = _CALLERS_RAW.get("technical_user_apps") or {}

# La ventana del INSTRUMENTO. Un techo tuyo no es un limite del sistema: un `last_seen` puede
# ser el suelo del log, no la muerte del canal. Y APQI abarca desde 2005 mientras rsau cubre
# unos meses: poner las dos cifras juntas sin decirlo compara denominadores distintos.
VENTANA_LOG = {"_que_es": "el rango que cubre rsau_audit_history, no la vida del canal",
               "_se_rellena_al_medir": True}


def _app_detras(usuario):
    """Que APLICACION hay detras de un usuario tecnico, y si eso esta MEDIDO o AFIRMADO.

    Una afirmacion de una persona y una medida no valen lo mismo y no se mezclan: ALLOS tiene
    dominio probado contra el log de cambios; MULESOFT tiene 'Core Manager' dicho por JP y nunca
    medido. Bajo una etiqueta unica se heredan igual.
    """
    v = APPS.get((usuario or "").strip()) or APPS.get((usuario or "").strip().upper())
    if not isinstance(v, dict):
        return {}
    return {"application": v.get("primary_application"),
            "application_kind": v.get("kind") or v.get("tool"),
            "application_source": ("MEDIDO" if str(v.get("source", "")).lower().startswith(
                ("measur", "medid")) else "AFIRMADO por una persona, no medido"),
            "application_measured": v.get("measured")}


def _dom_canal(ch):
    """El dominio de un canal declarado -- SOLO si el canal lo declara.

    Deliberadamente NO deduce de 'dominios_que_toca': esa es una lista sin orden, y coger su
    primer elemento no es medir, es adivinar con cara de dato. Hacerlo daba 'BusinessPartner'
    para el canal de batch input cuando el reparto real por sesiones es Travel 50.166 y ALLOS
    4.918 -- y BusinessPartner es justo la clasificacion que este canal ya tuvo mal una vez.
    Si un canal multi-dominio no declara cual manda, la respuesta correcta es que no lo se.
    """
    d = ch.get("dominio") or ch.get("domain")
    return d.split("(")[0].strip() if isinstance(d, str) and d else None


def q(con, sql, default=None):
    try:
        return con.execute(sql).fetchall()
    except sqlite3.Error:
        return default if default is not None else []


def _clasificador():
    """A4, para poner DOMINIO a cada interfaz. Sin dominio, una interfaz no aparece en el mapa
    de su area y solo se encuentra si ya sabes que existe -- que es como se pierde."""
    import importlib.util as _u
    pm = str(REPO / "process_mining")
    if pm not in sys.path:
        sys.path.insert(0, pm)          # A4 importa gold_ref, que vive a su lado
    sp = _u.spec_from_file_location(
        "_a4", str(REPO / "process_mining" / "executed_objects_domain_map.py"))
    m = _u.module_from_spec(sp)
    # SIN try/except: un clasificador que no carga tiene que PARAR el generador. Con captura
    # silenciosa devolvia None para los 655 registros y el generador reportaba exito -- que es
    # exactamente el fallo que ya nos costo cuatro no-ops en la sesion 97.
    sp.loader.exec_module(m)
    con = sqlite3.connect(m.GOLD, timeout=300)
    return m.make_classifier(con)


# Nosotros. Todo lo que hacemos leyendo el sistema es RUIDO en cualquier medida sobre como
# trabaja UNESCO, y hay que sacarlo antes de contar, no despues de publicar.
OBSERVADORES = {"JP_LOPEZ"}

USTYP_ES = {"A": "Dialogo - una PERSONA", "B": "Sistema - tecnico, no entra por dialogo",
            "C": "Comunicacion - CPIC/RFC entre sistemas", "S": "Servicio - dialogo compartido",
            "L": "Referencia - solo hereda permisos"}


def _lo_que_cambia_de_verdad(con):
    """LA PRUEBA DE ESCRITURA ES EL LOG DE CAMBIOS, NO EL NOMBRE DEL MODULO.

    Decidir MASTER_DATA/TRANSACCIONAL por subcadenas del nombre es el metodo que este proyecto
    abandono DESPUES de equivocarse: los GROUPID de ALLOS casaron 200/200 contra LFA1 y la
    conclusion 'es de acreedores' era falsa. La regla que quedo: la prueba de a que dominio
    pertenece un canal -- y de si escribe -- es lo que su gente CAMBIA.

    Se ve en la salida: MULESOFT sale MASTER_DATA+TRANSACCIONAL por 20.197 llamadas cuyo NOMBRE
    lleva CREATE/CHANGE, cuando el canal de cambios registra ordenes de magnitud menos. Sin este
    cruce se declara escritura de datos maestros donde el sistema no registra un solo cambio.
    """
    out = {}
    try:
        for u, n, clases in con.execute("""
                SELECT UPPER(TRIM(USERNAME)), COUNT(*), COUNT(DISTINCT OBJECTCLAS)
                FROM cdhdr_history WHERE TRIM(COALESCE(USERNAME,'')) <> ''
                GROUP BY 1"""):
            out[u] = {"documentos_de_cambio": n, "clases_distintas": clases}
    except sqlite3.Error:
        return {}
    try:
        for u, clase, n in con.execute("""
                SELECT UPPER(TRIM(USERNAME)), OBJECTCLAS, COUNT(*)
                FROM cdhdr_history WHERE TRIM(COALESCE(USERNAME,'')) <> ''
                GROUP BY 1,2"""):
            d = out.get(u)
            if d is not None:
                d.setdefault("top_clases", []).append((clase, n))
    except sqlite3.Error:
        pass
    for d in out.values():
        d["top_clases"] = [{"clase": c, "cambios": k} for c, k in
                           sorted(d.get("top_clases", []), key=lambda t: -t[1])[:5]]
    return out


def _ventana_del_log(con):
    """Que rango cubre el log, y CUANTOS DIAS FALTAN dentro de el.

    Un techo del instrumento no es un limite del sistema: un `last_seen` se lee como 'el canal
    murio' cuando es el suelo de la ventana. Y APQI abarca desde 2005 mientras rsau cubre unos
    meses -- publicar las dos cifras juntas sin decirlo compara denominadores distintos.
    """
    try:
        lo, hi, dias = con.execute("""SELECT MIN(SAL_DATE), MAX(SAL_DATE),
                                             COUNT(DISTINCT SAL_DATE)
                                      FROM rsau_audit_history""").fetchone()
    except sqlite3.Error:
        return {}
    posibles = None
    try:
        from datetime import date
        a, b = (date(int(lo[:4]), int(lo[4:6]), int(lo[6:8])),
                date(int(hi[:4]), int(hi[4:6]), int(hi[6:8])))
        posibles = (b - a).days + 1
    except Exception:
        pass
    return {"_que_es": "el rango que cubre rsau_audit_history, NO la vida del canal",
            "desde": lo, "hasta": hi, "dias_con_datos": dias,
            "dias_posibles": posibles,
            "dias_ausentes": (posibles - dias) if posibles else None,
            "_como_leerlo": ("todo `calls`, `first_seen` y `last_seen` esta recortado por esta "
                             "ventana. Un last_seen igual al suelo NO significa que el canal "
                             "murio. Y las cifras de APQI (desde 2005) no son comparables con "
                             "estas sin decirlo")}


def _perfil_temporal(con):
    """CUANDO corre cada canal. Un pico entre el 1 y el 5 es CIERRE; uno a las 03:00 es BATCH;
    actividad fuera de horario es un riesgo, no una curiosidad.

    Sin esto ningun registro puede pasar de grado 1 (SITUADO) a grado 2 (DESCRITO): el perfil
    horario es literalmente la prueba que exige ese grado.
    """
    out = {}
    try:
        for u, hora, dia, n in con.execute("""
                SELECT SLGUSER, SUBSTR(SAL_TIME,1,2), SUBSTR(SAL_DATE,7,2), COUNT(*)
                FROM rsau_audit_history
                WHERE TXSUBCLSID='RFC Function Call' AND SLGUSER <> ''
                GROUP BY 1,2,3"""):
            d = out.setdefault((u or "").strip().upper(),
                               {"por_hora": Counter(), "por_dia_del_mes": Counter()})
            d["por_hora"][hora] += n
            d["por_dia_del_mes"][dia] += n
    except sqlite3.Error:
        return {}
    for u, d in out.items():
        h = d["por_hora"]
        tot = sum(h.values()) or 1
        noche = sum(v for k, v in h.items() if k and (k < "07" or k >= "20"))
        dm = d["por_dia_del_mes"]
        cierre = sum(v for k, v in dm.items() if k and k <= "05")
        d["pico_horario"] = h.most_common(1)[0][0] if h else None
        d["pct_fuera_de_horario"] = round(100.0 * noche / tot, 1)
        d["pct_primeros_5_dias"] = round(100.0 * cierre / (sum(dm.values()) or 1), 1)
        d["forma"] = ("CIERRE (se concentra al principio de mes)" if d["pct_primeros_5_dias"] > 45
                      else "BATCH NOCTURNO" if d["pct_fuera_de_horario"] > 60
                      else "CONTINUO")
        d["por_hora"] = dict(sorted(h.items()))
        d["por_dia_del_mes"] = None      # el detalle no aporta; la forma si
    return out


def _variantes_por_programa():
    """El programa dice lo que se PUEDE hacer; la VARIANTE, lo que SE HACE.

    Registrar SAPF100 o RFEBBU00 sin su variante permite afirmar el alcance de un canal -- que
    sociedades, que rangos, que rutas -- que el programa por si solo no determina. Es la misma
    clase de error que costo una medida entera: FS10 contra FS11 por BILAVERS.
    """
    p = REPO / "brain_v2" / "variant_content.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for v in d.get("variantes", []):
        out.setdefault(str(v.get("programa", "")).upper(), []).append({
            "variante": v.get("variante"),
            "mecanismo": v.get("mecanismo_de_seleccion"),
            "rutas": v.get("rutas_de_fichero") or None})
    return out


def _actores_normalizados():
    """A19 primero: normalizar antes de contar. La misma persona con dos grafias cuenta como dos
    canales -- medido en ALLOS: BILLAULT-RFC y BILLAULT_RFC."""
    p = REPO / "brain_v2" / "log_reality.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    acts = d.get("actors")
    if isinstance(acts, dict):
        return {str(k).upper(): v for k, v in acts.items() if isinstance(v, str)}
    return {}


def _tipos_de_usuario(con):
    """Lo que SAP DECLARA de cada cuenta (USR02-USTYP), no lo que parece por su nombre.

    Dos heuristicas fallaron antes que esto: 'tiene logons de dialogo -> persona' colocaba
    BRIDGE-RFC, JOBBATCH y MULESOFT entre las personas, y la version por proporcion de logons
    seguia fallando con JOBBATCH y WF-BATCH. SAP ya lo dice en un campo.
    """
    try:
        return {(b or "").strip().upper(): (t or "").strip()
                for b, t in con.execute("SELECT BNAME, USTYP FROM usr02")}
    except sqlite3.Error:
        return {}


def _desde_donde_llama(con):
    """Confirma por TERMINAL si el trafico RFC de una cuenta viene de un servidor o de su PC.

    Es lo que separa 'una persona trabajando en SAP GUI' de 'una aplicacion entrando con la
    cuenta de una persona'. Un usuario de dialogo genera eventos 'RFC Function Call' de las dos
    maneras, asi que sin este paso el tipo de usuario solo da una sospecha.

    La senal es que el terminal este COMPARTIDO: el portatil de alguien no lo usan otras diez
    cuentas; un servidor de integracion si. Es la misma senal que identifico HQ-ORION-EAI01.
    """
    porterm = defaultdict(set)
    poruser = defaultdict(Counter)
    try:
        cur = con.execute("""SELECT SLGUSER, SLGLTRM2, COUNT(*) FROM rsau_audit_history
                             WHERE TXSUBCLSID='RFC Function Call' AND SLGLTRM2 <> ''
                             GROUP BY 1, 2""")
    except sqlite3.Error:
        return {}
    for u, t, n in cur:
        u, t = (u or "").strip().upper(), (t or "").strip()
        porterm[t].add(u)
        poruser[u][t] += n

    out = {}
    for u, terms in poruser.items():
        comp = [(t, n, len(porterm[t])) for t, n in terms.items() if len(porterm[t]) >= 5]
        tot = sum(terms.values()) or 1
        desde_srv = sum(n for _, n, _ in comp)
        out[u] = {
            "terminales": len(terms),
            "pct_desde_terminal_compartido": round(100.0 * desde_srv / tot, 1),
            "ejemplos": [{"terminal": t, "llamadas": n, "cuentas_que_lo_usan": k}
                         for t, n, k in sorted(comp, key=lambda x: -x[1])[:3]],
        }
    return out


def _lo_que_mueve_cada_usuario_rfc(con, dom, ctx):
    """El dominio de un canal lo decide LO QUE MUEVE, no como se llama.

    Un usuario RFC entrante -- MULESOFT, BRIDGE-RFC, UBO-RFC -- no es un objeto ABAP, asi que
    ningun clasificador de codigo lo resuelve por el nombre. Pero SI se puede medir: se mira
    que modulos de funcion llama y con que peso, y el dominio es el de la mayoria de sus
    llamadas. Eso es evidencia, no convencion de nombres.

    Devuelve {usuario: (dominio, cobertura, top_modulos)}.
    """
    peso = {}
    try:
        cur = con.execute("""SELECT SLGUSER, PARAM3, COUNT(*) FROM rsau_audit_history
                             WHERE TXSUBCLSID = 'RFC Function Call' AND PARAM3 <> ''
                             GROUP BY 1, 2""")
    except sqlite3.Error:
        return {}
    for u, fm, n in cur:
        peso.setdefault((u or "").strip(), []).append(((fm or "").strip(), n))

    fm_dom = ctx.get("fm_dom") or {}
    out = {}
    for u, pares in peso.items():
        neg, sus, tot_neg, total = Counter(), Counter(), 0, 0
        contrib = []
        for fm, n in pares:
            total += n
            d = dom(fm, overlay=fm_dom.get(fm))
            if not d or d == "Uncatalogued":
                continue
            # Lo que TODOS los canales mueven no dice para que sirve ESTE canal. El voto por
            # numero de llamadas lo ganaban RFCPING y RFC_READ_TABLE: UBO-RFC salia 63%
            # 'sustrato tecnico' y EPAM-RFC 72%, que es cierto y no informa de nada. El sustrato
            # solo decide cuando NO hay ninguna llamada de negocio, y entonces es la respuesta.
            if d in SUSTRATO or fm in FONTANERIA:
                sus[d] += n
                continue
            neg[d] += n
            tot_neg += n
            contrib.append((fm, n))
        # NATURALEZA del canal: se pondera por llamadas, PERO una sola llamada que escribe ya
        # hace del canal un canal de escritura. Un canal que lee un millon de veces y crea diez
        # documentos no es "de lectura": es de escritura con mucho ruido de lectura delante.
        nat = Counter()
        for fm, n in pares:
            if fm in FONTANERIA:
                continue
            t = _naturaleza_fm(fm)
            if t:
                nat[t] += n
        natur, detalle = None, None
        if nat:
            escrituras = {k: v for k, v in nat.items() if k != "LECTURA"}
            tot = sum(nat.values()) or 1
            if escrituras:
                # etiqueta CANONICA: ordenada alfabeticamente, no por quien gano el recuento.
                # Sin esto salian 'TRANSACCIONAL+MASTER_DATA' y 'MASTER_DATA+TRANSACCIONAL' como
                # si fueran dos naturalezas distintas, y ninguna busqueda encontraba las dos.
                natur = "+".join(sorted(escrituras))
                detalle = (f"escribe: {sum(escrituras.values()):,} llamadas de "
                           f"{'/'.join(sorted(escrituras))}; lee: {nat['LECTURA']:,} "
                           f"({round(100.0 * sum(escrituras.values()) / tot, 1)}% escritura)")
            else:
                natur = "LECTURA"
                detalle = f"solo lectura: {nat['LECTURA']:,} llamadas, ninguna escribe"

        if neg:
            d, k = neg.most_common(1)[0]
            ej = [fm for fm, _ in sorted(contrib, key=lambda t: -t[1])[:4]]
            out[u] = (d, round(100.0 * k / max(tot_neg, 1), 1), ej, natur, detalle)
        elif sus:
            d, k = sus.most_common(1)[0]
            ej = [fm for fm, _ in sorted(pares, key=lambda t: -t[1])[:4]]
            out[u] = (d, round(100.0 * k / max(total, 1), 1), ej, natur, detalle)
    return out


def _canales_custom_de_escritura(con):
    """Modulos de funcion Z*/Y* llamados por RFC: son canales de ESCRITURA propios y casi
    nunca estan declarados. Se descubren por el log, igual que A23 descubre usuarios.

    Nace de ZRFC_FMR_CREATE -- 'crear reserva de fondos' -- que hacia 817 llamadas desde los
    servidores de ORION y no figuraba en ninguno de los 300 registros del inventario.
    """
    out = []
    # Los modulos DECLARADOS en un canal entran siempre, sea cual sea su prefijo y su volumen.
    # Dos motivos medidos: /SAPPSPRO/PD_GM_FMR2_READ_KBLE no empieza por Z ni por Y -- es del
    # espacio de nombres de SAP para Sector Publico -- y ademas tiene 32 llamadas, por debajo
    # del umbral. Se caia por los dos sitios a la vez y vivia solo en un JSON que nada enlazaba.
    declarados = set()
    for _c in (CANALES or {}).values():
        declarados |= {str(x).strip().upper() for x in (_c.get("modulos_custom") or {})}
        declarados |= {str(x).strip().upper() for x in (_c.get("modulos_estandar") or {})}
        # Y LAS BAPIs ESTANDAR QUE EL CANAL USA. Se caian por los dos filtros a la vez -- no
        # empiezan por Z/Y y no estaban en las claves que se leian -- asi que crear pedidos,
        # movimientos de mercancia y facturas de entrada desde un servidor de integracion era
        # escritura transaccional en produccion, estructuralmente invisible en el inventario.
        declarados |= {str(x).strip().upper()
                       for x in (_c.get("bapis_estandar_que_usan") or [])}
    try:
        rows = con.execute("""
            SELECT PARAM3, COUNT(*), COUNT(DISTINCT SLGUSER),
                   COUNT(DISTINCT SLGLTRM2), MIN(SAL_DATE), MAX(SAL_DATE)
            FROM rsau_audit_history
            WHERE TXSUBCLSID = 'RFC Function Call' AND PARAM3 <> ''
            GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    except sqlite3.Error:
        return out

    propio = ("Z", "Y")
    todas = len(rows)
    rows = [r for r in rows
            if (str(r[0]).strip().upper() in declarados)
            or (str(r[0]).strip().upper().startswith(propio) and r[1] >= 50)]
    # EL RESTO SIN CLASIFICAR ES EL SENSOR. Un corte que no publica lo que tiro presenta una
    # poblacion ya truncada como si fuera la cobertura. Aqui se nombra.
    DESCARTES["RFC_CUSTOM_FM"] = {
        "criterio": "modulo Z/Y con >=50 llamadas, o declarado en un canal",
        "vistos": todas, "conservados": len(rows), "descartados": todas - len(rows)}
    # los llamantes de TODOS los modulos en UNA pasada. Una consulta por modulo era un barrido
    # completo de 20M filas por cada uno: la version ingenua no termino en 15 minutos.
    porfm = {}
    try:
        for fm, u, k in con.execute("""
                SELECT PARAM3, SLGUSER, COUNT(*) FROM rsau_audit_history
                WHERE TXSUBCLSID = 'RFC Function Call'
                  AND (PARAM3 LIKE 'Z%' OR PARAM3 LIKE 'Y%')
                GROUP BY 1, 2"""):
            porfm.setdefault(fm, []).append((u, k))
    except sqlite3.Error:
        pass

    for fm, n, users, terms, lo, hi in rows:
        top = sorted(porfm.get(fm, []), key=lambda t: -t[1])[:3]
        _u = (fm or "").strip().upper()
        out.append({
            "channel": "RFC_CUSTOM_FM", "artifact": (fm or "").strip(), "direction": "inbound",
            "ours": _u.startswith(propio),
            "_autoria": ("PROPIO (Z/Y)" if _u.startswith(propio) else
                         "DE SAP, en su espacio de nombres: el canal es nuestro, el modulo no"),
            "calls": n, "distinct_users": users, "distinct_terminals": terms,
            "first_seen": lo, "last_seen": hi,
            "top_callers": [{"user": u, "calls": k} for u, k in top],
            "evidence_it_runs": f"{n:,} llamadas RFC en rsau_audit_history",
            "_why_here": ("modulo de funcion PROPIO llamado por RFC: es un canal de ESCRITURA "
                          "o lectura de la casa, y casi nunca esta declarado en rfcdes"),
        })
    return out


def main():
    if not GOLD.exists():
        print(f"golden not found: {GOLD}", file=sys.stderr)
        return 1
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
    inv = []

    # ---- WEB SERVICES ----------------------------------------------------
    # OURS is decided by AUTHOR, never by prefix: the SuccessFactors set is SAP-delivered
    # and activated here, and a Z/Y filter erased it from the map earlier today.
    for name, author, created in q(con, "SELECT WSNAME, AUTHOR, CREATEDON FROM wsheader"):
        if (author or "").strip().upper() == "SAP":
            continue
        inv.append({
            "channel": "WEB_SERVICE", "artifact": name, "direction": "inbound",
            "ours_because": f"authored by {author}, not by SAP",
            "activated_on": created,
            "evidence_it_runs": None,
            "why_no_evidence": ("SRT_MONILOG_DATA is EMPTY — the SOAP monitor is off. "
                                "Existence and activation are verified; execution cannot be. "
                                "This is UNVERIFIED, never 'unused'"),
        })

    # ---- HTTP / ICF SURFACE ----------------------------------------------
    icf = q(con, "SELECT ICF_NAME, ICFACTIVE FROM icfservice")
    custom = [(n, a) for n, a in icf if (n or "").upper().startswith(("Z", "Y"))]
    inv.append({
        "channel": "HTTP_SERVICE", "artifact": "(ICF surface)", "direction": "inbound",
        "total_services": len(icf),
        "active": sum(1 for _n, a in icf if (a or "").strip() in ("X", "A", "1")),
        "custom_services": len(custom),
        "custom_sample": [n for n, _a in custom[:10]],
        "evidence_it_runs": "activation flag only",
        "why_no_evidence": "ICF call logging is not extracted; activation is not execution",
    })

    # ---- BATCH INPUT -----------------------------------------------------
    # The finding that inverts the usual reading: the sessions are GENERATED, not recorded.
    by_prog = dict(q(con, "SELECT PROGID, COUNT(*) FROM apqi GROUP BY 1"))
    by_creator = dict(q(con, "SELECT CREATOR, COUNT(*) FROM apqi GROUP BY 1"))
    states = dict(q(con, "SELECT QSTATE, COUNT(*) FROM apqi GROUP BY 1"))
    total = sum(by_prog.values()) or 1
    # SIN CORTE. El top-12 tiraba ZMM_BI_MM01_PLANT, que es uno de los cinco generadores
    # PROPIOS cuyo codigo no esta extraido. Y cortar por arriba es como se concluyo una vez
    # "el batch input es de viajes": debajo del 86,4% de TRIP_* habia 1.806 grupos sin mirar.
    for prog, n in sorted(by_prog.items(), key=lambda x: -x[1]):
        p = (prog or "").strip()
        inv.append({
            "channel": "BATCH_INPUT", "artifact": p, "direction": "inbound",
            "sessions": n, "share_of_all_sessions": round(n / total, 3),
            "que_hace": QUE_HACE_BDC.get(p),
            "generated_not_recorded": p == "SAPMSSY1",
            "_why_that_matters": ("SAPMSSY1 is the RFC dispatcher. Sessions it creates were "
                                 "GENERATED OVER RFC, not recorded by a person at a screen — "
                                 "so this belongs to the interface channel, not the dialog "
                                 "one") if p == "SAPMSSY1" else None,
            # HUECO DE AUDITORIA: codigo PROPIO que escribe en produccion por BDC y cuyo fuente
            # no esta extraido. Dos tocan datos personales sensibles.
            "codigo_extraido": False if p in BDC_SIN_FUENTE else None,
            "dato_personal_sensible": True if p in BDC_SENSIBLE else None,
            "_el_hueco": ("codigo PROPIO que ESCRIBE en produccion por BDC y no se puede "
                          "auditar porque su fuente no esta extraido") if p in BDC_SIN_FUENTE
                         else None,
            "why_no_evidence": ("que transaccion ejecuta no se puede saber: APQD.VARDATA es "
                                "LCHR(7902) y RFC_READ_TABLE lo rechaza con OPTION_NOT_VALID"),
            "evidence_it_runs": f"{n} sessions in APQI",
        })

    # ---- ABRIR EL EXTERNO: SAPMSSY1 SOLO DICE "VINO DE FUERA" -------------
    # Sin este paso, el canal de escritura externo MAS GRANDE del sistema -- 55.087 de 57.998
    # sesiones, el 95% -- quedaba como UN registro llamado SAPMSSY1, y el clasificador de
    # dominio lo etiquetaba `Basis_Security` porque miraba el paquete del DESPACHADOR RFC. Es
    # decir: el canal por el que entran ALLOS y Travel figuraba como fontaneria de Basis.
    #
    # Lo unico que la sesion externa trae consigo es el GROUPID, y de su forma sale el dominio.
    for grupo, n in q(con, """SELECT GROUPID, COUNT(*) FROM apqi WHERE PROGID='SAPMSSY1'
                              GROUP BY 1"""):
        pass
    ext = Counter()
    ext_grupos = defaultdict(set)
    ext_creadores = defaultdict(set)
    ext_mes = defaultdict(Counter)
    for grupo, creador, fecha, n in q(con, """SELECT GROUPID, CREATOR, CREDATE, COUNT(*)
                                              FROM apqi WHERE PROGID='SAPMSSY1'
                                              GROUP BY 1,2,3"""):
        g = (grupo or "").strip()
        if g.upper().startswith("TRIP_"):
            d = "Travel"
        elif re.match(r"^\d{1,8}[A-Z0-9]{2,4}$", g, re.I):
            d = "HCM"          # la firma de ALLOS: <numero de objeto><sufijo de oficina>
        else:
            d = None
        clave = d or "EXTERNO_SIN_GRAMATICA"
        ext[clave] += n
        ext_grupos[clave].add(g)
        ext_creadores[clave].add((creador or "").strip())
        if (fecha or "").strip():
            ext_mes[clave][str(fecha)[:6]] += n
    for clave, n in ext.most_common():
        inv.append({
            "channel": "BATCH_INPUT", "artifact": f"SAPMSSY1/{clave}", "direction": "inbound",
            "sessions": n, "groups": len(ext_grupos[clave]),
            "creator_strings": len(ext_creadores[clave]),
            "domain": None if clave == "EXTERNO_SIN_GRAMATICA" else clave,
            "domain_basis": ("MEDIDO: la forma del GROUPID, que es lo unico que una sesion "
                             "externa por RFC trae consigo"),
            "_por_que_esta_abierto": (
                "SAPMSSY1 es el despachador RFC: dice que vino de fuera, no DE QUE. Sin abrirlo, "
                "el 95% del batch input quedaba en un registro etiquetado Basis_Security -- el "
                "paquete del despachador -- y ALLOS y Travel eran invisibles"),
            "_lo_que_no_encaja_es_el_hallazgo": (
                "EXTERNO_SIN_GRAMATICA son generadores que todavia no sabemos nombrar. Ahi "
                "estuvo ALLOS un ano: debajo del 86,4% de TRIP_*, en la cola larga"),
            "_que_falta_para_cerrarlo": (
                "su usuario tecnico (CREATOR y USERID contra USR02), su destino RFC si lo tiene, "
                "y su programa") if clave == "EXTERNO_SIN_GRAMATICA" else None,
            "por_mes": dict(sorted(ext_mes[clave].items())),
            "_la_serie_es_el_hallazgo": (
                "un reparto sin serie temporal dice como se ha trabajado EN TOTAL, que a veces "
                "es lo contrario de como se trabaja HOY: ALLOS paso de 6-30 sesiones al mes a "
                "115 en junio y 271 en julio de 2026, x9, mientras Travel caia un 64%. Con solo "
                "el total, ALLOS parece marginal"),
            "_cuidado_con_la_pendiente": (
                "la cola BORRA lo que se procesa bien, y borra mas cuanto mas atras: la serie es "
                "mas fiable hacia el presente. NO leer la pendiente como actividad"),
            "why_no_evidence": (
                "que TRANSACCION ejecuta cada sesion NO se puede saber: esta en APQD.VARDATA, "
                "que es LCHR(7902), y RFC_READ_TABLE lo rechaza con OPTION_NOT_VALID. No es que "
                "nadie haya mirado: es que el canal no lo permite"),
            "evidence_it_runs": f"{n} sesiones en APQI",
        })
    inv.append({
        "channel": "BATCH_INPUT", "artifact": "(session health)", "direction": "inbound",
        # CREATOR NO ES UNA IDENTIDAD: es un texto que la herramienta escribe en
        # BDC_OPEN_GROUP y que SAP no valida contra USR02. Medido: de 16 grafias *RFC que
        # aparecen como CREATOR, 10 no existen como usuario. Llamarlos "creadores" y contarlos
        # como actores es contar PARAMETROS y presentarlos como personas.
        "top_creator_strings": sorted(by_creator.items(), key=lambda x: -x[1])[:6],
        "_creator_no_es_usuario": ("APQI.CREATOR es un parametro de BDC_OPEN_GROUP, no una "
                                   "identidad validada. Cruzar contra USR02 antes de tratarlo "
                                   "como actor"),
        "states": states,
        # 'F' = FINALIZADA CON EXITO. Sumarla a los errores publicaba una tasa de fallo que
        # incluia los exitos. Y la tasa no se puede publicar de todos modos: APQI es una COLA
        # que BORRA lo que se proceso bien, asi que el denominador esta sesgado por construccion
        # -- lo que queda es, casi por definicion, lo que fallo.
        "error_sessions": states.get("E", 0),
        "_por_que_no_es_una_tasa": (
            "no dividir esto entre el total. APQI borra las sesiones que se procesan BIEN, asi "
            "que el reparto de QSTATE mide QUE QUEDA, no que pasa: leerlo como tasa de fallo da "
            "un 92,6% que no existe. Y 'F' significa FINALIZADA CON EXITO, no fallo"),
        "_finding": ("un canal de escritura que falla es un hueco de datos silencioso, y nadie "
                     "vigila esto. Pero la MAGNITUD no es medible con este instrumento"),
    })

    # ---- RFC DESTINATIONS + IDOC ------------------------------------------
    for dest, rtype in q(con, "SELECT RFCDEST, RFCTYPE FROM rfcdes"):
        inv.append({"channel": "RFC_DESTINATION", "artifact": (dest or "").strip(),
                    "direction": "outbound", "type": (rtype or "").strip(),
                    "evidence_it_runs": "see brain_v2/interface_boundary.json (F1) for "
                                        "LIVE/DEAD against observed traffic"})
    for mestyp, n in Counter(m for (m,) in q(con, "SELECT MESTYP FROM edidc") if m).items():
        inv.append({"channel": "IDOC", "artifact": mestyp, "direction": "both",
                    "documents": n, "evidence_it_runs": f"{n} documents in EDIDC"})
    # ---- RFC OBSERVADO: usuarios que ENTRAN sin destino configurado ---------
    # El inventario derivaba solo de rfcdes, que son destinos CONFIGURADOS y SALIENTES. Un
    # satelite que entra autenticandose como usuario RFC no tiene destino, luego era
    # estructuralmente invisible aqui -- por eso EPAM-RFC, con 127.832 eventos desde dos IPs
    # fijas, no figuraba en ninguno de los 300 registros. Un canal se descubre por su TRAFICO,
    # no solo por su configuracion.
    # UNA consulta agrupada, no una por usuario. La primera version hacia un COUNT por cada
    # uno de los 255 usuarios: 255 barridos completos de 28,5M de filas sin indice, y el paso
    # se volvia el mas lento del rebuild entero. El propio registro lo avisa en A7 -- "un
    # algoritmo lento se salta, y un algoritmo saltado es documentacion".
    _dialog_logons = {}
    try:
        for u, k in con.execute("SELECT SLGUSER, COUNT(*) FROM rsau_audit_history "
                                "WHERE TXSUBCLSID = 'Dialog Logon' GROUP BY SLGUSER"):
            _dialog_logons[u] = k
    except sqlite3.Error:
        _dialog_logons = {}

    # EL RESTO ES EL SENSOR. El corte de 1.000 llamadas descarta 1.843 de 2.098 cuentas RFC
    # -- 295.011 llamadas -- y sin publicarlo el "X de N con dominio" se calcula sobre una
    # poblacion ya truncada y se presenta como cobertura.
    _todos = q(con, """SELECT SLGUSER, COUNT(*), COUNT(DISTINCT PARAM3),
                              COUNT(DISTINCT SLGLTRM2)
                       FROM rsau_audit_history
                       WHERE TXSUBCLSID = 'RFC Function Call' AND SLGUSER != ''
                       GROUP BY SLGUSER ORDER BY 2 DESC""") or []
    _conserva = [r for r in _todos if r[1] >= 1000]
    DESCARTES["RFC_INBOUND_OBSERVED"] = {
        "criterio": "cuenta con >=1000 llamadas RFC",
        "vistos": len(_todos), "conservados": len(_conserva),
        "descartados": len(_todos) - len(_conserva),
        "llamadas_descartadas": sum(r[1] for r in _todos if r[1] < 1000),
        "_por_que_importa": ("un umbral que no publica lo que tira convierte una poblacion "
                             "truncada en una cobertura")}

    for user, calls, fms, terms in _conserva:
        # PERSONA o MAQUINA, decidido por una senal MEDIBLE y no por el nombre: una interfaz
        # no hace LOGON DE DIALOGO. Un humano que usa SAP GUI genera muchisimas llamadas RFC
        # -- V.VAURETTE tiene 211.702 -- y sin este corte el inventario se llena de personas.
        dlg = _dialog_logons.get(user)
        inv.append({
            "channel": "RFC_INBOUND_OBSERVED", "artifact": (user or "").strip(),
            "direction": "inbound", "calls": calls,
            "distinct_function_modules": fms, "distinct_terminals": terms,
            # ausente del dict = CERO logons de dialogo, que es la senal de maquina.
            "dialog_logons": dlg or 0,
            # QUIEN ENTRA lo dice USR02-USTYP, y se rellena mas abajo en `user_type`.
            #
            # Aqui vivia `likely: MAQUINA/PERSONA` derivado de "cero logons de dialogo", con un
            # comentario que lo defendia como "una senal medible". Es una HEURISTICA REFUTADA el
            # 2026-08-25: clasifica mal a BRIDGE-RFC, JOBBATCH, MULESOFT y WF-BATCH, que son
            # tipo B (Sistema) y tienen logons de dialogo -- MULESOFT tiene 14.224. Se publicaba
            # como campo de primera clase AL LADO de la respuesta correcta, que es peor que
            # equivocarse solo: obliga al lector a elegir entre dos respuestas del mismo fichero.
            "_likely_RETIRADO": ("2026-08-25: la senal 'cero logons de dialogo = maquina' es "
                                 "FALSA por los dos lados. Lo declara USR02-USTYP, campo "
                                 "`user_type`. No reintroducir"),
            # QUE APLICACION hay detras del usuario tecnico. El log solo da la cuenta; el
            # nombre de la aplicacion esta en rfc_caller_apps.json, en el mismo fichero que este
            # script ya abre y del que solo leia `channels`.
            **_app_detras(user),
            "evidence_it_runs": f"{calls:,} llamadas RFC en rsau_audit_history",
            "_ventana_del_instrumento": VENTANA_LOG,
            "_why_here": ("descubierto por TRAFICO, no por configuracion: no tiene entrada en "
                          "rfcdes. Un satelite que entra como usuario RFC no deja destino"),
        })

    inv.extend(_canales_custom_de_escritura(con))
    con.close()

    # ---- DECLARED (parsed from the map) + DERIVED (from the change log) ----
    declared = {}
    if DECLARED.exists():
        declared = json.load(open(DECLARED, encoding="utf-8")).get("by_artifact") or {}
    for art, entries in declared.items():
        for d in entries:
            inv.append({"channel": d["channel"], "artifact": art,
                        "direction": "inbound", "source_system": d.get("source"),
                        "declared_status": d.get("status"),
                        "from": "the integration map — a CLAIM, verified separately",
                        "evidence_it_runs": None})

    derived = {}
    if ATTRIB.exists():
        derived = json.load(open(ATTRIB, encoding="utf-8")).get("classes") or {}

    counts = Counter(r["channel"] for r in inv)

    # ---- DOMINIO a cada interfaz -------------------------------------------
    # 555 interfaces y NINGUNA llevaba dominio: no aparecian en el mapa de su area y solo se
    # encontraban si ya sabias que existian. Eso es exactamente como se pierde conocimiento.
    #
    # La escalera va de EVIDENCIA a INFERENCIA, y cada registro declara por cual entro
    # (domain_basis). Un dominio medido y uno adivinado no valen lo mismo y no se mezclan.
    _dom, _ctx = _clasificador()
    _con2 = sqlite3.connect(GOLD, timeout=300)
    _mueve = _lo_que_mueve_cada_usuario_rfc(_con2, _dom, _ctx)
    _tipos = _tipos_de_usuario(_con2)
    _desde = _desde_donde_llama(_con2)
    _cambia = _lo_que_cambia_de_verdad(_con2)
    _ventana = _ventana_del_log(_con2)
    _perfil = _perfil_temporal(_con2)
    _con2.close()
    _variantes = _variantes_por_programa()
    _norm = _actores_normalizados()
    _riesgo = []
    _contradicciones = []

    _base, _nat = Counter(), Counter()
    for _it in inv:
        _a = str(_it.get("artifact") or "").strip()
        _d, _b = None, None

        # 1. MEDIDO: lo que el canal mueve de verdad (modulos que llama, ponderado)
        _m = _mueve.get(_a.upper()) or _mueve.get(_a)
        if _m:
            _d, _b = _m[0], f"MEDIDO: {_m[1]}% de sus llamadas son {_m[0]} ({', '.join(_m[2])})"
            if _m[3]:
                _it["nature"] = _m[3]
                _it["nature_basis"] = "MEDIDO: " + _m[4]

        # 2. MEDIDO: el artefacto ES un objeto ABAP y SAP dice a que paquete pertenece
        if not _d and _a:
            _c = _dom(_a, overlay=(_ctx.get("fm_dom") or {}).get(_a))
            if _c and _c != "Uncatalogued":
                _d, _b = _c, "MEDIDO: paquete/componente del objeto (TADIR->TDEVC->DF14L)"

        # 3. INFERIDO: el sistema del otro lado ya esta caracterizado en rfc_caller_apps
        if not _d:
            for _k, _ch in (CANALES or {}).items():
                if not _a:
                    break
                _txt = (_k + " " + str(_ch.get("nombre", ""))).upper()
                # Se miran las TRES claves. La version anterior solo leia `modulos_custom`,
                # asi que /SAPPSPRO/PD_GM_FMR2_READ_KBLE entraba al inventario por la fuerza-
                # inclusion (que si lee las dos) y salia con dominio null, cuando su canal
                # declara PSM_FM y que "lee las tablas de reserva". Un dominio conocido
                # publicado como deuda.
                _decl = json.dumps({k: _ch.get(k) for k in
                                    ("modulos_custom", "modulos_estandar",
                                     "bapis_estandar_que_usan")}).upper()
                if _a.upper() in _txt or _a.upper() in _decl:
                    _d = _dom_canal(_ch)
                    _b = f"INFERIDO: canal declarado {_k}" if _d else None
                    # Un canal multi-dominio dice sus dominios secundarios en vez de perderlos.
                    _sec = _ch.get("dominios_secundarios") or _ch.get("dominios_que_toca")
                    if _sec:
                        _it["domains_secondary"] = _sec if isinstance(_sec, list) else None
                    if _d:
                        break

        # 3b. En SOAP el nombre de la operacion ES el contrato: EmployeeMasterDataBundle
        #     Replication no es una convencion de nombres interna, es lo que el servicio declara
        #     mover. Estos 8 son la replicacion de SuccessFactors, activada entre 2013 y 2015.
        if not _d and _it.get("channel") in ("WEB_SERVICE", "WEBSERVICE"):
            _U = _a.upper()
            if _U.startswith(("EMPLOYEE", "ORGANISATIONAL", "ORGOBJ", "ORGSTRUCTURE",
                              "POSITION", "JOBREPLICATION")):
                _d, _b = "HCM", "INFERIDO: la operacion SOAP declara que replica objetos de RRHH"

        # 4. SUSTRATO: un destino tecnico no tiene dominio de negocio, y decirlo es un hecho,
        #    no un hueco. Los GUID y los A01LOGON son fontaneria del propio landscape.
        if not _d and _it.get("channel") == "RFC_DESTINATION":
            _U = _a.upper()
            if (len(_a) == 32 and all(ch in "0123456789ABCDEFabcdef" for ch in _a)) or \
               _it.get("type") in ("I", "3") or _U.endswith("LOGON"):
                _d, _b = "Technical_Substrate", "SUSTRATO: destino interno del landscape"
            elif _U.startswith(("CALLTP_", "CSI_", "SAPFTP", "SAPHTTP", "TMS", "EU_SCRP",
                                "F1_HELP", "EPS_", "GFW_ITS", "DOCUMENTATION_")) or \
                    _U in ("ADS", "SAPOSCOL", "SAPCPIC"):
                # destinos que SAP ENTREGA con el sistema: ayuda F1, GUI scripting, transferencia
                # de ficheros EPS, ITS, PDF, transportes. No mueven negocio, son la maquinaria.
                _d, _b = "Technical_Substrate", "SUSTRATO: destino estandar entregado por SAP"

        # ---- NATURALEZA para los canales cuyo artefacto ES el objeto ----------
        if not _it.get("nature"):
            _n = _naturaleza_fm(_a)
            if _n:
                _it["nature"] = _n
                _it["nature_basis"] = "INFERIDO: verbo y objeto en el nombre del modulo"
            elif _it.get("channel") == "BATCH_INPUT":
                # el batch input NO PUEDE leer: graba pantallas de una transaccion. Todo canal
                # de batch input es de escritura por construccion, y eso no es una suposicion.
                _it["nature"] = ("MASTER_DATA" if any(o in _a.upper() for o in OBJ_MAESTRO)
                                 else "TRANSACCIONAL")
                _it["nature_basis"] = ("MEDIDO: el batch input reproduce una transaccion de "
                                       "dialogo, asi que escribe siempre; el objeto lo decide "
                                       "el programa generador")
            elif _it.get("channel") in ("WEB_SERVICE", "WEBSERVICE") and \
                    "REPLIC" in _a.upper():
                _it["nature"] = "MASTER_DATA"
                _it["nature_basis"] = ("INFERIDO: un servicio de REPLICACION escribe el maestro "
                                       "que replica")
            elif _it.get("channel") == "RFC_DESTINATION":
                # 'no lo se' es un estado NOMBRADO, no un hueco: un destino saliente no deja en
                # NUESTRO log que hace del otro lado. Contarlo como 'sin naturaleza' lo mezclaba
                # con lo que si podriamos medir y no medimos, que es otra cosa.
                _it["nature"] = "NO_MEDIBLE"
                _it["nature_basis"] = ("NO MEDIBLE AQUI: un destino SALIENTE no registra en "
                                       "nuestro log que hace en el sistema destino. Se mediria "
                                       "en el otro extremo. Ausencia de dato, no de riesgo")

        # ---- QUIEN ENTRA: cuenta tecnica declarada, o una persona ------------
        if _it.get("channel") == "RFC_INBOUND_OBSERVED" and _a:
            _t = _tipos.get(_a.upper())
            _it["user_type"] = _t or None
            _it["user_type_meaning"] = USTYP_ES.get(_t, "no consta en USR02") if _t else \
                "no consta en USR02 (cuenta borrada, o el nombre no es un usuario)"
            # LA CLASE QUE IMPORTA: una PERSONA por cuya cuenta entra trafico de ESCRITURA.
            # La autorizacion se comprueba contra la persona, no contra la aplicacion que la
            # usa, asi que la aplicacion hereda todo lo que esa persona pueda hacer. Es el
            # patron portal-as-user del hallazgo H71, aqui con nombre y volumen.
            if _a.upper() in OBSERVADORES:
                # nuestro propio trafico de extraccion. Medirnos a nosotros y presentarlo como
                # hallazgo sobre UNESCO es contaminar la medida con el medidor.
                _it["sod_flag"] = None
                _it["_observador"] = "trafico de NUESTRAS extracciones, fuera de toda medida"
            elif _t == "A" and _it.get("nature") not in (None, "LECTURA", "NO_MEDIBLE"):
                # UNA PERSONA POR CUYA CUENTA ENTRA ESCRITURA POR RFC. Falta un paso para
                # llamarlo canal con todas las letras: un usuario de dialogo tambien genera
                # eventos 'RFC Function Call' desde el propio SAP GUI. Lo que separa las dos
                # cosas es el TERMINAL -- un servidor de aplicacion ajeno (HQ-ORION-EAI01) no es
                # el portatil de nadie. Por eso esto es SOSPECHA_ALTA y no un veredicto.
                _dd = _desde.get(_a.upper()) or {}
                _pct = _dd.get("pct_desde_terminal_compartido", 0)
                _it["desde"] = _dd or None
                if _pct >= 50:
                    _it["sod_flag"] = "PERSONA_USADA_COMO_CANAL_DE_ESCRITURA"
                    _it["sod_flag_confianza"] = (
                        f"CONFIRMADO POR TERMINAL: {_pct}% de sus llamadas RFC salen de un "
                        f"terminal que usan 5 cuentas o mas, o sea de un servidor, no de un PC")
                    _riesgo.append((_a, _it.get("nature"), _it.get("calls") or 0, True))
                else:
                    _it["sod_flag"] = "PERSONA_CON_ESCRITURA_POR_RFC"
                    _it["sod_flag_confianza"] = (
                        f"SIN CONFIRMAR: solo el {_pct}% de sus llamadas sale de un terminal "
                        f"compartido, asi que lo mas probable es que sea la propia persona "
                        f"trabajando y no una aplicacion entrando con su cuenta")
                    _riesgo.append((_a, _it.get("nature"), _it.get("calls") or 0, False))

        # 5. NOMBRAR EL DESCONOCIDO. 'Sin dominio' mezclaba dos cosas distintas: lo que se nos
        #    paso y lo que de verdad no se puede saber desde aqui. La segunda es un estado, no
        #    una deuda, y confundirlas hace que la deuda nunca baje.
        if not _d:
            _b = ("SIN RESOLVER: ni el nombre dice a que sirve ni tenemos trafico suyo. "
                  "Se resolveria leyendo la configuracion del destino en SM59, o el codigo "
                  "que lo invoca")

        # ---- ¿ESCRIBE DE VERDAD? La prueba es el LOG DE CAMBIOS, no el nombre del modulo ----
        _c = _cambia.get(_a.upper())
        if _it.get("channel") == "RFC_INBOUND_OBSERVED":
            _it["cambios_registrados"] = (_c or {}).get("documentos_de_cambio", 0)
            _it["que_cambia_de_verdad"] = (_c or {}).get("top_clases")
            _nat_nombre = str(_it.get("nature") or "")
            if _nat_nombre and _nat_nombre not in ("LECTURA", "NO_MEDIBLE"):
                _docs = (_c or {}).get("documentos_de_cambio", 0)
                if _docs == 0:
                    # SIN VEREDICTO, Y A PROPOSITO. `cdhdr` registra CAMBIOS a objetos que
                    # tienen documento de modificacion configurado -- NO registra CREACIONES.
                    # Un canal que contabiliza en FI crea BKPF/BSEG y no deja rastro aqui: no
                    # se esta contradiciendo, esta creando. Decir "gana el log" convertiria
                    # esta comprobacion en la misma clase de conclusion apresurada que vino a
                    # corregir. Es una PREGUNTA ABIERTA, no un defecto.
                    _it["_sin_rastro_en_cdhdr"] = (
                        "el nombre de sus modulos dice que escribe y el log de CAMBIOS no "
                        "registra ni un documento suyo. Las dos lecturas son posibles y hay "
                        "que decidir mirando: (a) CREA documentos nuevos, que no generan "
                        "documento de modificacion, o (b) el nombre promete una escritura que "
                        "no ocurre. Se resuelve buscandolo en la tabla de su objeto (BKPF, "
                        "FMIOI, EKKO...), no en cdhdr")
                    _contradicciones.append((_a, _nat_nombre, 0))
                elif _docs < (_it.get("calls") or 0) / 1000:
                    _it["_desproporcion"] = (
                        f"{_docs:,} documentos de cambio frente a {(_it.get('calls') or 0):,} "
                        "llamadas: la mayor parte de su trafico NO escribe, aunque el nombre de "
                        "algunos modulos lo sugiera")

        # ---- ACTOR UNICO: es un hallazgo, no una estadistica ----
        if _it.get("distinct_users") == 1 and _it.get("nature") not in (None, "LECTURA",
                                                                       "NO_MEDIBLE"):
            _it["riesgo_actor_unico"] = (
                f"UNA sola cuenta mueve este canal de escritura ({(_it.get('calls') or 0):,} "
                "llamadas). Riesgo de persona clave: si esa cuenta cae o se va, el canal para")

        if _it.get("channel") in ("RFC_INBOUND_OBSERVED", "RFC_CUSTOM_FM"):
            _it["_ventana_del_instrumento"] = _ventana.get("desde") and \
                f"{_ventana['desde']}..{_ventana['hasta']}"
            # CUANDO corre: sin perfil temporal nada pasa de SITUADO a DESCRITO
            _p = _perfil.get(_a.upper())
            if _p:
                _it["cuando_corre"] = {
                    "forma": _p["forma"], "pico_horario": _p["pico_horario"],
                    "pct_fuera_de_horario": _p["pct_fuera_de_horario"],
                    "pct_primeros_5_dias": _p["pct_primeros_5_dias"]}
                if _p["pct_fuera_de_horario"] > 80 and _it.get("user_type") == "A":
                    _it["_actividad_fuera_de_horario"] = (
                        "una cuenta de PERSONA con mas del 80% de su trafico fuera de horario: "
                        "o la conduce una aplicacion, o es actividad que nadie mira")
            # La NORMALIZACION de A19: la misma persona con dos grafias son dos canales
            _n = _norm.get(_a.upper())
            if _n and _n.upper() != _a.upper():
                _it["actor_normalizado"] = _n
                _it["_ojo"] = ("dos grafias del mismo actor se cuentan como dos canales si no "
                               "se normaliza antes: medido en ALLOS con BILLAULT-RFC / "
                               "BILLAULT_RFC")

        # LA VARIANTE: el programa dice lo que se puede hacer; la variante, lo que se hace
        if _it.get("channel") in ("BATCH_INPUT", "FILE") and _a:
            _v = _variantes.get(_a.upper())
            if _v:
                _it["variantes"] = _v[:6]
                _it["_la_variante_es_el_alcance"] = (
                    "el programa no determina que sociedades, rangos o rutas cubre: eso lo dice "
                    "la variante con la que corre")

        _it["domain"] = _d
        _it["domain_basis"] = _b
        _base["sin dominio" if not _d else _b.split(":")[0]] += 1
        _nat[_it.get("nature") or "sin naturaleza"] += 1

    # ---- EL INDICE DE COMPRENSION, PONDERADO POR TRAFICO Y CON DERIVADA ----
    # Contar REGISTROS hace que un destino RFC muerto pese igual que
    # Y_BAPI_WBS_FINANCIAL_DATA_1 con 1.861.107 llamadas: el "X de N con dominio" puede subir
    # mientras baja la fraccion de trafico real entendida. Y sin derivada, nadie nota que la
    # frontera dejo de moverse -- eso ya duro 75 dias sin que nadie lo viera.
    _peso_tot = sum((i.get("calls") or i.get("sessions") or 0) for i in inv) or 1
    def _grado(i):
        if not i.get("domain"):
            return 0                                  # 0 EJECUTA: existe y no sabemos donde
        if not i.get("nature") or i.get("nature") == "NO_MEDIBLE":
            return 1                                  # 1 SITUADO: sabemos el area
        if not (i.get("que_cambia_de_verdad") or i.get("application") or i.get("top_callers")):
            return 2                                  # 2 DESCRITO: sabemos que hace
        return 3                                      # 3 EXPLICADO: con evidencia de quien y que
    _por_grado_reg, _por_grado_peso = Counter(), Counter()
    for i in inv:
        g = _grado(i)
        _por_grado_reg[g] += 1
        _por_grado_peso[g] += (i.get("calls") or i.get("sessions") or 0)
    _comprension = {
        "_los_cuatro_grados": {"0": "EJECUTA (sin dominio)", "1": "SITUADO (area)",
                               "2": "DESCRITO (que hace)", "3": "EXPLICADO (con evidencia)"},
        "_se_pondera_por_trafico_no_por_registros": True,
        "por_registros": {str(k): v for k, v in sorted(_por_grado_reg.items())},
        "pct_del_trafico": {str(k): round(100.0 * v / _peso_tot, 1)
                            for k, v in sorted(_por_grado_peso.items())},
    }
    try:
        _prev = json.loads(OUT.read_text(encoding="utf-8")).get("_comprension", {})
        _pa = _prev.get("pct_del_trafico") or {}
        _comprension["derivada_vs_corrida_anterior"] = {
            k: round(_comprension["pct_del_trafico"].get(k, 0) - _pa.get(k, 0), 1)
            for k in set(list(_pa) + list(_comprension["pct_del_trafico"]))}
        _comprension["_un_indice_sin_derivada"] = ("no dice si avanzamos. Un hallazgo es una "
                                                   "DIFERENCIA")
    except Exception:
        _comprension["derivada_vs_corrida_anterior"] = "primera corrida: no hay con que comparar"

    _ok = len(inv) - _base["sin dominio"]
    print(f"  dominio asignado a {_ok} de {len(inv)} interfaces  {dict(_base)}")
    print(f"  comprension por TRAFICO: {_comprension['pct_del_trafico']}  "
          f"(por registros: {_comprension['por_registros']})")
    if _contradicciones:
        print(f"  prometen escritura y no dejan rastro en cdhdr: {len(_contradicciones)} "
              f"-- {', '.join(a for a, _n, _d in _contradicciones[:5])}")
        print("     (cdhdr registra CAMBIOS, no CREACIONES: no es un veredicto, es una lista "
              "de preguntas)")
    for _k, _v in DESCARTES.items():
        print(f"  descartados en {_k}: {_v['descartados']} de {_v['vistos']} ({_v['criterio']})")
    print(f"  naturaleza: {dict(_nat.most_common())}")
    # ---- CONTESTAR A LOS DEMAS MINEROS -------------------------------------
    # Un foro donde todos publican y nadie contesta es un tablon. Este minero tiene USR02 y el
    # log de auditoria cargados; otro minero llego a su limite preguntando justo por eso. La
    # colaboracion es esto: contestar lo que tu instrumento SI puede ver y el suyo no.
    try:
        import importlib.util as _iu
        _sp = _iu.spec_from_file_location("_mb", str(REPO / "process_mining" / "mining_bus.py"))
        _mb = _iu.module_from_spec(_sp)
        _sp.loader.exec_module(_mb)
        _con3 = sqlite3.connect(GOLD, timeout=300)
        _vistos = set()
        try:
            _vistos = {(u or "").strip().upper() for (u,) in _con3.execute(
                "SELECT DISTINCT SLGUSER FROM rsau_audit_history WHERE SLGUSER <> ''")}
        except sqlite3.Error:
            pass
        _con3.close()
        _contestadas = 0
        for _q in _mb.pendientes():
            _s = str(_q.get("sujeto", "")).upper()
            if _s == "CREATOR_SIN_USUARIO":
                # La pregunta era: ¿cuentas BORRADAS o texto inventado? Se distingue mirando si
                # ese nombre llego a APARECER alguna vez en el log: una cuenta borrada dejo
                # rastro; un texto que la herramienta escribe sin validar, no.
                _nombres = re.findall(r"\b[A-Z][A-Z0-9_.-]{3,}\b", str(_q.get("pregunta", "")))
                _dejaron = sorted(n for n in _nombres if n in _vistos)
                _nunca = sorted(n for n in _nombres
                                if n not in _vistos and n not in ("USR02", "CREATOR", "BDC"))
                _mb.responder(
                    "A27_interface_nature", _s,
                    (f"de las grafias preguntadas, {len(_dejaron)} aparecen alguna vez como "
                     f"usuario en el log de auditoria ({', '.join(_dejaron[:5])}) -- esas "
                     f"EXISTIERON y estan borradas. Las otras {len(_nunca)} no aparecen NUNCA "
                     f"({', '.join(_nunca[:5])}): son texto que la herramienta escribe sin "
                     "validar, no cuentas"),
                    evidencia="usr02 + SLGUSER distinto de rsau_audit_history",
                    autoridad="MEDIDO_EN_DATOS")
                _contestadas += 1
        if _contestadas:
            print(f"  contestadas {_contestadas} pregunta(s) de otros mineros en el foro")
    except Exception as _e:
        print(f"  AVISO: no se pudo contestar en el foro ({type(_e).__name__})")

    _riesgo.sort(key=lambda t: -t[2])
    _conf = [r for r in _riesgo if r[3]]
    print(f"  personas con escritura por RFC: {len(_riesgo)}  "
          f"de las cuales CONFIRMADAS como canal por terminal: {len(_conf)}")
    if _conf:
        print("    " + ", ".join(f"{u}({n:,})" for u, _, n, _c in _conf[:6]))
    if _ok == 0:
        raise SystemExit("[interface inventory] el clasificador no resolvio NADA: "
                         "no se publica un inventario sin dominio")

    json.dump({
        "_generated_by": "brain_v2/build_interface_inventory.py",
        "_what_this_is": ("every inbound and outbound path as a RECORD, derived from the "
                          "golden tables — not a paragraph inside a claim"),
        "_why": ("prose is not reliable knowledge. Nothing can query a paragraph, diff it "
                 "next month, or notice when it goes stale."),
        "_ours_is_decided_by_author": ("never by prefix. The SuccessFactors replication set is "
                                       "SAP-delivered and ACTIVATED here; a Z/Y filter erased "
                                       "the live SF-to-ECC channel from the map earlier today"),
        "_evidence_discipline": ("every record says whether there is evidence it RUNS, and "
                                 "when there is not, WHY not. 'We cannot see it' and 'it does "
                                 "not happen' are different facts"),
        "counts": dict(counts),
        "object_classes_with_a_derived_channel": len(derived),
        # LO QUE SE TIRO, con nombre. Un umbral que no se publica convierte una poblacion
        # truncada en una cobertura y nadie lo nota.
        "_lo_descartado_por_los_cortes": DESCARTES,
        # LA VENTANA DEL INSTRUMENTO. Un techo tuyo no es un limite del sistema.
        "_ventana_del_log": _ventana,
        # DONDE EL NOMBRE PROMETE ESCRITURA Y EL LOG DE CAMBIOS NO LA VE.
        # NO es un veredicto: cdhdr registra CAMBIOS, no CREACIONES, asi que un canal que crea
        # documentos nuevos aparece aqui sin estar equivocado. Es una lista de PREGUNTAS.
        "_prometen_escritura_y_no_dejan_rastro_en_cdhdr": {
            "_como_se_lee": ("dos lecturas posibles y hay que decidir mirando la tabla del "
                             "objeto (BKPF, FMIOI, EKKO), no cdhdr: o CREA documentos nuevos "
                             "-- que no generan documento de modificacion -- o el nombre "
                             "promete una escritura que no ocurre"),
            "casos": [{"artefacto": a, "naturaleza_por_el_nombre": n,
                       "documentos_de_cambio": d} for a, n, d in _contradicciones[:20]]},
        # EL INDICE DE COMPRENSION, con su DERIVADA. Un indice sin derivada no dice si
        # avanzamos, y ponderar por REGISTROS hace que un destino muerto pese igual que un
        # canal con 1,8M de llamadas.
        "_comprension": _comprension,
        "interfaces": inv,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[interface inventory] {len(inv)} records")
    for k, v in counts.most_common():
        print(f"    {k:18s} {v}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
