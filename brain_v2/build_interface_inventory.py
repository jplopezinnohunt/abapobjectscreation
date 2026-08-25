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
    rows = [r for r in rows
            if (str(r[0]).strip().upper() in declarados)
            or (str(r[0]).strip().upper().startswith(propio) and r[1] >= 50)]
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
    for prog, n in sorted(by_prog.items(), key=lambda x: -x[1])[:12]:
        inv.append({
            "channel": "BATCH_INPUT", "artifact": prog, "direction": "inbound",
            "sessions": n, "share_of_all_sessions": round(n / total, 3),
            "generated_not_recorded": prog == "SAPMSSY1",
            "_why_that_matters": ("SAPMSSY1 is the RFC dispatcher. Sessions it creates were "
                                 "GENERATED OVER RFC, not recorded by a person at a screen — "
                                 "so this belongs to the interface channel, not the dialog "
                                 "one") if prog == "SAPMSSY1" else None,
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
    for grupo, creador, n in q(con, """SELECT GROUPID, CREATOR, COUNT(*) FROM apqi
                                       WHERE PROGID='SAPMSSY1' GROUP BY 1,2"""):
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

    for user, calls, fms, terms in q(con, """
            SELECT SLGUSER, COUNT(*), COUNT(DISTINCT PARAM3), COUNT(DISTINCT SLGLTRM2)
            FROM rsau_audit_history
            WHERE TXSUBCLSID = 'RFC Function Call' AND SLGUSER != ''
            GROUP BY SLGUSER HAVING COUNT(*) >= 1000 ORDER BY 2 DESC""") or []:
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
            "evidence_it_runs": f"{calls:,} llamadas RFC en rsau_audit_history",
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
    _con2.close()
    _riesgo = []

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
                if _a.upper() in _txt or _a.upper() in json.dumps(
                        _ch.get("modulos_custom") or {}).upper():
                    _d = _dom_canal(_ch)
                    _b = f"INFERIDO: canal declarado {_k}" if _d else None
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

        _it["domain"] = _d
        _it["domain_basis"] = _b
        _base["sin dominio" if not _d else _b.split(":")[0]] += 1
        _nat[_it.get("nature") or "sin naturaleza"] += 1

    _ok = len(inv) - _base["sin dominio"]
    print(f"  dominio asignado a {_ok} de {len(inv)} interfaces  {dict(_base)}")
    print(f"  naturaleza: {dict(_nat.most_common())}")
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
