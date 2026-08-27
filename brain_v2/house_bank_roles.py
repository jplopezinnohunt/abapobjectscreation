# -*- coding: utf-8 -*-
"""EL ROL DE CADA BANCO CASA: quien es domestico, quien cruza fronteras, quien no emite fichero.

POR QUE EXISTE
    2026-08-20. Citibank aviso de que exigiria Purpose of Payment para Egipto. Se analizo,
    se construyo y se probo extremo a extremo. Diez dias despues Societe Generale confirmo
    que no habia nada que hacer: el canal de Citi no lleva ese flujo.

    El dato estaba medido desde el 2026-08-17 (claims 492/493: 93,9% SocGen, 2,0% Citi) y
    aun asi la pregunta no se hizo, porque estaba disperso en dos claims de prosa en vez de
    ser una propiedad consultable del modelo. La leccion de JP, que es la correcta: no falta
    una regla que recordar, falta MODELO. Que rol juega cada banco casa. Cual es domestico y
    cual cross-border. Cual emite fichero y cual cheque. Que corredor sirve cada uno.

    Con esta tabla, la pregunta "¿nos vincula el aviso de Citi?" se contesta en un vistazo:
    se mira quien sirve a los beneficiarios con banco en EG y se ve que Citi no esta ahi.

COMO SE DERIVA CADA COSA -- todo medido, nada declarado
    pais del banco casa   REGUH.UBNKS  (es NUESTRO banco, no el del beneficiario -- claim 489)
    domestico             % de sus pagos donde el pais del banco del BENEFICIARIO (LFBK-BANKS)
                          coincide con el pais del banco casa. Esa es la definicion operativa
                          de domestico: mismo sistema bancario a los dos lados.
    cheque                % por metodos con T042Z-XSCHK='X' -> no hay fichero SAP que corregir
    formato / cheque      T042Z se clava por el pais de la SOCIEDAD QUE PAGA (T001-LAND1),
                          NO por el del banco casa. UNES es francesa, asi que sus metodos
                          resuelven contra LAND1='FR' aunque el banco casa este en Egipto.
                          Usar el pais del banco aqui daba CIT19 con 0% de cheque cuando en
                          realidad es el 100% -- un error silencioso de los que cuestan caro.
    despacha PPC          por el pais del banco casa: FR -> YCL_IDFI_CGI_DMEE_FR es la unica
                          implementacion que llama al constructor PPC (claim 494). DE e IT
                          implementan GET_CREDIT y nada mas; el resto no tiene implementacion.

LA REGLA DE NEGOCIO QUE ESTO HACE VISIBLE
    Un pago DOMESTICO -- mismo pais a los dos lados -- no necesita purpose code: el banco
    local no lo pide. Solo lo piden los CROSS-BORDER. Nuestro control no distingue: u917
    bloquea por el pais del banco del BENEFICIARIO, sin mirar por donde sale el dinero, y el
    renderizado solo ocurre si NUESTRO banco esta en FR. Resultado medido: entre el 15% y el
    30% de los pagos a los nueve paises configurados capturan un codigo que nunca llega a
    ningun fichero, y 171 lineas domesticas (JO 150, MA 21) lo capturan estando pagadas por
    un banco casa LOCAL que jamas lo habria pedido. Vista: --ppc-exposure.

LA SOCIEDAD ES EL PRIMER DRIVER -- el banco solo ejecuta dentro de su marco
    Correccion estructural de JP, 2026-08-20, y encaja con lo ya medido: BCM se clava en
    ZBUKR, T042E es por sociedad, OB28 asigna la validacion por sociedad, y T001-LAND1 -- el
    pais de la sociedad -- es lo que decide QUE T042Z aplica y por tanto los metodos y los
    formatos. La sociedad decide el MARCO; el banco solo ejecuta dentro de el.

    Y explica lo que un modelo banco-primero no puede: ICTP es ITALIANA, luego su banco UNI01
    selecciona la clase BAdI _IT, que no despacha purpose codes. No es una peculiaridad de
    UNI01: es consecuencia de la sociedad. Igual UIL (alemana, _DE), UIS (canadiense), UBO
    (brasilena). Solo UNES e IIEP son francesas, y por eso solo ellas alcanzan la clase _FR.

USO
    python brain_v2/house_bank_roles.py --by-company     # la sociedad primero, el banco despues
    python brain_v2/house_bank_roles.py                 # el censo completo
    python brain_v2/house_bank_roles.py --ppc-exposure  # capturado vs renderizado por pais
    python brain_v2/house_bank_roles.py --country EG    # quien sirve a un corredor
    python brain_v2/house_bank_roles.py --bank CIT19    # que hace un banco concreto

Emite brain_v2/house_bank_roles.json. Claim 530.
"""

# REGLAS QUE APLICAN AQUI (citadas para que existan en su punto de uso, no solo en el JSON):
#   feedback_p01_canonical_for_active_classification
#     -> el momento es clasificar algo como vivo o muerto: aqui se marcan cuentas sin actividad
import collections
import io
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
OUT = os.path.join(HERE, "house_bank_roles.json")

# Que clase del BAdI despacha PPC, por pais del banco casa. Leido del fuente en s099/s101.
PPC_DISPATCH = {
    "FR": ("YCL_IDFI_CGI_DMEE_FR", True,  "unica clase que llama al constructor PPC"),
    "DE": ("YCL_IDFI_CGI_DMEE_DE", False, "implementa GET_CREDIT, nunca llama al PPC"),
    "IT": ("YCL_IDFI_CGI_DMEE_IT", False, "implementa GET_CREDIT, nunca llama al PPC"),
}
FALLBACK = ("(sin implementacion)", False, "el pais no tiene implementacion del BAdI")

# Metodos que mueven dinero entre NUESTRAS propias cuentas. T042Z pais FR: A = "Treasury
# Transfers". Sus lineas no llevan LIFNR ni PERNR porque el beneficiario somos nosotros.
TREASURY_METHODS = {"A"}

HUB_GLOBAL_DEST = 150   # destinos distintos -> concentrador global
HUB_REGIONAL_DEST = 15  # destinos distintos -> hub regional
LOCAL_TOPSHARE = 0.70   # un solo destino se lleva esto -> banco de oficina

DOMESTIC_HI = 0.80      # por encima -> domestico
DOMESTIC_LO = 0.20      # por debajo  -> cross-border
CHEQUE_HI = 0.50        # por encima -> el banco no emite fichero, emite papel


def _t042z():
    """FORMI/XSCHK por (pais, metodo) y el pais de cada sociedad (T001-LAND1).

    Se lee de P01; si no hay RFC, se sigue sin ello."""
    try:
        sys.path.insert(0, os.path.join(ROOT, "Zagentexecution", "mcp-backend-server-python"))
        from rfc_helpers import get_connection
        c = get_connection("P01")
        try:
            F = ["LAND1", "ZLSCH", "TEXT1", "FORMI", "XSCHK"]
            r = c.call("RFC_READ_TABLE", QUERY_TABLE="T042Z", DELIMITER="|",
                       FIELDS=[{"FIELDNAME": f} for f in F], ROWCOUNT=0)
            out = {}
            for d in r["DATA"]:
                v = [x.strip() for x in d["WA"].split("|")]
                out[(v[0], v[1])] = {"text": v[2], "formi": v[3], "cheque": v[4] == "X"}
            r2 = c.call("RFC_READ_TABLE", QUERY_TABLE="T001", DELIMITER="|",
                        FIELDS=[{"FIELDNAME": "BUKRS"}, {"FIELDNAME": "LAND1"},
                                {"FIELDNAME": "BUTXT"}], ROWCOUNT=0)
            cc, nm = {}, {}
            for d in r2["DATA"]:
                v = [x.strip() for x in d["WA"].split("|")]
                cc[v[0]] = v[1]
                nm[v[0]] = v[2]
            return out, cc, nm
        finally:
            c.close()
    except Exception as exc:                       # sin RFC el censo sigue siendo util
        print("  (T042Z no leido: %s -- el censo sale sin formato ni marca de cheque)"
              % str(exc)[:60], file=sys.stderr)
        return {}, {}, {}


def _q_febko():
    """HBKID -> (n extractos, ultima fecha, sociedades) desde FEBKO_2024_2026.

    Conexion propia porque build() ya cerro la suya para cuando esto se necesita. Si la
    tabla no existe (Gold DB sin extracto todavia) devuelve None, no [] -- son cosas
    distintas: "sin tabla" no es "tabla vacia", y confundirlas fue el error de la sesion
    del 2026-08-20 (claim 535).
    """
    try:
        con = sqlite3.connect("file:%s?mode=ro" % GOLD, uri=True)
        cur = con.cursor()
        cur.execute("SELECT TRIM(HBKID), COUNT(*), MAX(AZDAT), TRIM(BUKRS) "
                    "FROM FEBKO_2024_2026 GROUP BY 1, 4")
        rows = cur.fetchall()
        con.close()
        return rows
    except sqlite3.OperationalError:
        return None


def build():
    if not os.path.exists(GOLD):
        print("Gold DB no encontrado: %s" % GOLD)
        return None
    t042z, cc_country, cc_name = _t042z()
    con = sqlite3.connect("file:%s?mode=ro" % GOLD, uri=True)
    cur = con.cursor()

    rows = cur.execute("""
        SELECT TRIM(COALESCE(h.HBKID,''))  AS hbkid,
               TRIM(COALESCE(h.UBNKS,''))  AS ourctry,
               TRIM(COALESCE(h.ZBUKR,''))  AS bukrs,
               TRIM(COALESCE(h.RZAWE,''))  AS method,
               TRIM(COALESCE(b.BANKS,''))  AS payeectry,
               COUNT(*)                    AS n,
               MAX(h.LAUFD)                AS last_run
        FROM REGUH h
        LEFT JOIN (SELECT DISTINCT LIFNR, BANKS FROM LFBK) b ON b.LIFNR = h.LIFNR
        WHERE COALESCE(h.XVORL,'') <> 'X'
        GROUP BY 1,2,3,4,5
    """).fetchall()
    con.close()

    banks = {}
    corridor = collections.defaultdict(collections.Counter)   # pais destino -> banco casa
    for hbkid, ourctry, bukrs, method, payeectry, n, last_run in rows:
        if not hbkid:
            # Sin banco casa registrado. NO se ignoran: son las lineas que con mas
            # seguridad no renderizan nada, y esconderlas inflaba la cobertura -- el
            # corte por denominador es la primera cosa que hay que declarar.
            if payeectry:
                corridor[payeectry]["(sin banco casa)"] += n
            continue
        b = banks.setdefault(hbkid, {
            "house_bank": hbkid, "country": ourctry, "company_codes": collections.Counter(),
            "methods": collections.Counter(), "payee_countries": collections.Counter(),
            "lines": 0, "domestic": 0, "known_payee_bank": 0, "cheque": 0, "treasury": 0, "last_run": ""})
        if ourctry and not b["country"]:
            b["country"] = ourctry
        b["lines"] += n
        if last_run and last_run > b["last_run"]:
            b["last_run"] = last_run
        b["company_codes"][bukrs] += n
        # Transferencia de TESORERIA: sin proveedor y sin empleado no hay tercero, luego no
        # hay "destino" que resolver. Antes esto caia en SIN DESTINO CONOCIDO, que dice "no lo
        # vemos" cuando la verdad es "no aplica" -- son cosas opuestas y la etiqueta mentia.
        if method in TREASURY_METHODS:
            b["treasury"] += n
        b["methods"][method] += n
        if payeectry:
            b["payee_countries"][payeectry] += n
            b["known_payee_bank"] += n
            if payeectry == b["country"]:
                b["domestic"] += n
            corridor[payeectry][hbkid] += n
        payctry = cc_country.get(bukrs, "")
        info = t042z.get((payctry, method))
        if info and info["cheque"]:
            b["cheque"] += n
        if info and info["formi"]:
            b.setdefault("formats", set()).add(info["formi"])

    out = []
    for hbkid, b in sorted(banks.items(), key=lambda kv: -kv[1]["lines"]):
        known = b["known_payee_bank"] or 1
        dom = b["domestic"] / float(known)
        chq = b["cheque"] / float(b["lines"] or 1)
        cls, renders, why = PPC_DISPATCH.get(b["country"], FALLBACK)

        # TOPOLOGIA: un concentrador se distingue de un banco de oficina por la DIVERSIDAD
        # de destinos, no por el volumen. SOG01 alcanza 209 paises; ECO02 alcanza 3.
        ndest = len(b["payee_countries"])
        topshare = (b["payee_countries"].most_common(1)[0][1] / float(known)) if b["payee_countries"] else 0.0
        tre = b["treasury"] / float(b["lines"] or 1)
        if tre >= 0.60 and b["known_payee_bank"] == 0:
            topo = "TESORERIA (entre cuentas propias)"
        elif ndest >= HUB_GLOBAL_DEST:
            topo = "HUB GLOBAL"
        elif ndest >= HUB_REGIONAL_DEST:
            topo = "HUB REGIONAL"
        elif topshare >= LOCAL_TOPSHARE and dom >= 0.60:
            topo = "LOCAL (oficina de campo)"
        elif ndest == 0:
            topo = "SIN DESTINO RESOLUBLE"
        else:
            topo = "CORREDOR ESTRECHO"

        # Un rol domestico/cross-border sale de comparar el pais del beneficiario con el
        # nuestro. Si no HAY beneficiario, ese cociente divide por un denominador vacio y
        # devuelve CROSS-BORDER por defecto: un valor inventado. Decirlo es lo correcto.
        if topo.startswith("TESORERIA"):
            role = "n/a - no hay tercero"
        elif b["known_payee_bank"] == 0:
            role = "n/a - beneficiarios sin banco en LFBK"
        elif chq > CHEQUE_HI:
            role = "PAPEL - cheque, sin fichero SAP"
        elif dom >= DOMESTIC_HI:
            role = "DOMESTICO (%s)" % (b["country"] or "?")
        elif dom <= DOMESTIC_LO:
            role = "CROSS-BORDER"
        else:
            role = "MIXTO"

        fmts = sorted(b.get("formats", set()))
        out.append({
            "house_bank": hbkid,
            "country": b["country"],
            "role": role,
            "topology": topo,
            "treasury_share": round(tre, 3),
            "last_run": b["last_run"],
            "destination_countries": ndest,
            "top_destination_share": round(topshare, 3),
            "lines": b["lines"],
            "domestic_share": round(dom, 3),
            "cheque_share": round(chq, 3),
            "payee_bank_known_share": round(b["known_payee_bank"] / float(b["lines"] or 1), 3),
            "company_codes": [c for c, _ in b["company_codes"].most_common(6)],
            "methods": [m for m, _ in b["methods"].most_common(8)],
            "dmee_formats": fmts,
            "ppc": {"badi_class": cls, "dispatches_ppc": renders, "why": why},
            "top_payee_countries": [{"country": c, "lines": n}
                                    for c, n in b["payee_countries"].most_common(6)],
        })

    corridors = {}
    for ctry, cnt in corridor.items():
        tot = sum(cnt.values())
        # SIN truncar. Truncar aqui hacia que --ppc-exposure calculase sobre una lista
        # recortada y publicase 92% de renderizado donde el real es otro: un total correcto
        # con un desglose incompleto es peor que no tener el desglose.
        corridors[ctry] = {
            "lines": tot,
            "served_by": [{"house_bank": h, "lines": n, "share": round(n / float(tot), 3)}
                          for h, n in cnt.most_common()]}

    companies = {}
    for hbkid, ourctry, bukrs, method, payeectry, n, last_run in rows:
        if not bukrs:
            continue
        cc_ = companies.setdefault(bukrs, {"country": cc_country.get(bukrs, ""),
                                           "name": cc_name.get(bukrs, ""),
                                           "lines": 0, "cheque": 0,
                                           "banks": collections.Counter()})
        cc_["lines"] += n
        cc_["banks"][hbkid or "(sin banco casa)"] += n
        info = t042z.get((cc_["country"], method))
        if info and info["cheque"]:
            cc_["cheque"] += n
    for cid, c_ in companies.items():
        c_["cheque_share"] = round(c_["cheque"] / float(c_["lines"] or 1), 3)
        c_["banks"] = dict(c_["banks"])

    # CUENTA RECEPTORA: extracto con cero pagos. Antes esto salia como NEW en el explorador,
    # sesion tras sesion, porque el tipo estaba descrito en prosa (claim 535) pero nunca
    # programado en ESTE clasificador -- que solo lee REGUH, ciego por construccion a quien
    # solo cobra. Se deriva sin inventar: un banco con filas en FEBKO y CERO lineas en REGUH
    # (banks{}) recibe extracto y no paga. La ausencia de un banco aqui NO prueba que no
    # reciba extracto -- FEBKO_2024_2026 es un extracto PARCIAL (3 de 8 sociedades, claim 535)
    # -- asi que esto solo produce POSITIVOS, nunca ausencias declaradas como certeza.
    receiving = {}
    feb_rows = _q_febko()
    if feb_rows is not None:
        for hbkid, n, last_run, bukrs in feb_rows:
            if not hbkid or hbkid in banks:
                continue
            r = receiving.setdefault(hbkid, {"house_bank": hbkid, "statements": 0,
                                              "last_statement": "", "company_codes": set()})
            r["statements"] += n
            if last_run and last_run > r["last_statement"]:
                r["last_statement"] = last_run
            if bukrs:
                r["company_codes"].add(bukrs)
        for r in receiving.values():
            r["role"] = "CUENTA RECEPTORA (extracto, cero pagos en REGUH)"
            r["company_codes"] = sorted(r["company_codes"])

    doc = {"_what_this_is": ("Rol operativo de cada banco casa, derivado de REGUH+LFBK+T042Z. "
                            "Responde 'quien sirve este corredor' y 'este banco emite fichero "
                            "o papel' sin volver a derivarlo. Claim 530."),
           "_generated_by": "brain_v2/house_bank_roles.py",
           "companies": companies, "banks": out, "corridors": corridors,
           "receiving_accounts": receiving,
           "_receiving_accounts_caveat": (
               "Poblacion limitada a FEBKO_2024_2026, que cubre solo 3 de 8 sociedades "
               "(claim 535). Un banco AUSENTE de aqui no esta probado que no reciba "
               "extracto -- puede ser que su sociedad no este extraida todavia.")}
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, indent=2, ensure_ascii=False))
    return doc


PPC_COUNTRIES = ["AE", "BH", "CN", "ID", "IN", "JO", "MA", "MY", "PH"]


def by_company(doc):
    """La sociedad primero. Su PAIS decide el marco; sus bancos ejecutan dentro de el."""
    comps = doc.get("companies", {})
    if not comps:
        print("Sin capa de sociedad en el JSON -- regenera con la version actual.")
        return
    banks = {b["house_bank"]: b for b in doc["banks"]}
    print("=" * 92)
    print("LA SOCIEDAD ES EL PRIMER DRIVER -- su pais decide el marco, el banco ejecuta")
    print("=" * 92)
    for cid, c in sorted(comps.items(), key=lambda kv: -kv[1]["lines"]):
        if c["lines"] < 20:
            continue
        ppc = "SI" if c["country"] in PPC_DISPATCH and PPC_DISPATCH[c["country"]][1] else "no"
        print("")
        print("%-6s pais=%-3s  %-34s %10d lineas  %2d bancos  %3.0f%% cheque"
              % (cid, c["country"], c["name"][:34], c["lines"], len(c["banks"]), 100 * c["cheque_share"]))
        print("       marco: T042Z del pais %s -> sus metodos y formatos  |  clase BAdI del pais: %s -> despacha PPC: %s"
              % (c["country"], PPC_DISPATCH.get(c["country"], FALLBACK)[0], ppc))
        for hb, n in sorted(c["banks"].items(), key=lambda kv: -kv[1])[:6]:
            b = banks.get(hb)
            if not b:
                print("          %-8s %8d  (sin banco casa registrado)" % (hb, n))
                continue
            print("          %-8s %8d  %-34s %s" % (hb, n, b["topology"], b["role"]))
    print()
    print("  Leer de arriba abajo: la sociedad fija el pais, el pais fija T042Z y la clase BAdI,")
    print("  y solo entonces el banco importa. Un banco italiano no despacha purpose codes porque")
    print("  su sociedad es italiana -- no por nada del banco.")


def ppc_exposure(doc):
    """Capturado frente a renderizado, por pais con PPC configurado.

    u917 bloquea por el pais del banco del BENEFICIARIO. El renderizado depende de por
    donde sale el dinero: solo una clase BAdI, la de FR, despacha purpose codes. Las dos
    mitades no coinciden, y la diferencia es un campo que se obliga a rellenar y se tira.
    """
    by = {b["house_bank"]: b for b in doc["banks"]}
    print("=" * 88)
    print("EXPOSICION PPC -- se captura por el banco del BENEFICIARIO, se renderiza por el NUESTRO")
    print("=" * 88)
    print("%-4s %8s %10s %10s %8s %9s   bancos casa LOCALES (domestico)"
          % ("pais", "lineas", "renderiza", "domestico", "otros", "sin banco"))
    tot_c = tot_r = 0
    for ctry in PPC_COUNTRIES:
        c = doc["corridors"].get(ctry)
        if not c:
            continue
        rend = dom = otro = nohb = 0
        domhb = []
        assert sum(x["lines"] for x in c["served_by"]) == c["lines"], (
            "el desglose de %s no suma su total -- lista truncada?" % ctry)
        for s_ in c["served_by"]:
            b = by.get(s_["house_bank"], {})
            hbc = b.get("country", "")
            if s_["house_bank"] == "(sin banco casa)":
                nohb += s_["lines"]
            elif hbc == "FR":
                rend += s_["lines"]
            elif hbc == ctry:
                dom += s_["lines"]; domhb.append("%s %d" % (s_["house_bank"], s_["lines"]))
            else:
                otro += s_["lines"]
        t = c["lines"] or 1
        tot_c += t; tot_r += rend
        print("%-4s %8d %9.0f%% %9.0f%% %7.0f%% %8.0f%%   %s%s"
              % (ctry, t, 100.0 * rend / t, 100.0 * dom / t, 100.0 * otro / t,
                 100.0 * nohb / t, ", ".join(domhb) or "-",
                 "   <== capturado y NUNCA renderiza" if dom else ""))
    print()
    print("  Total: %d lineas capturadas, %.0f%% renderizan. El resto obliga a rellenar un"
          % (tot_c, 100.0 * tot_r / (tot_c or 1)))
    print("  campo que se descarta -- y las columnas 'domestico' son pagos que el banco local")
    print("  no habria pedido nunca, porque el purpose code es un requisito CROSS-BORDER.")
    print()
    print("  'sin banco' = REGUH sin HBKID: no hay canal, luego no renderiza con certeza.")
    print("  Se cuentan aqui a proposito; excluirlas inflaba la cobertura publicada.")
    print()
    print("  Nota de alcance: 'renderiza' asume que el pago llega al arbol CGI. Un banco casa")
    print("  FR pagando por un metodo de cheque tampoco produce fichero -- ver la columna")
    print("  cheque del censo. Esta vista acota por arriba, no por abajo.")


def show(doc, country=None, bank=None):
    if country:
        c = doc["corridors"].get(country.upper())
        if not c:
            print("Sin pagos a beneficiarios con banco en %s." % country.upper())
            return
        print("=" * 78)
        print("CORREDOR -> beneficiarios con banco en %s   %d lineas" % (country.upper(), c["lines"]))
        print("=" * 78)
        by = {b["house_bank"]: b for b in doc["banks"]}
        for s in c["served_by"][:8]:
            b = by.get(s["house_bank"], {})
            ppc = b.get("ppc", {})
            print("  %-7s %-5s %6d  %5.1f%%   %-28s %s"
                  % (s["house_bank"], b.get("country", "?"), s["lines"], 100 * s["share"],
                     b.get("role", "?"),
                     "PPC SI" if ppc.get("dispatches_ppc") else "PPC no"))
        print()
        print("  Lectura: el banco que domina esta fila es el que hay que consultar ante un")
        print("  requisito regulatorio sobre este corredor. Un banco con 'PAPEL' no tiene")
        print("  fichero que corregir, y uno con 'PPC no' no renderiza purpose codes.")
        return
    banks = doc["banks"]
    if bank:
        banks = [b for b in banks if b["house_bank"] == bank.upper()]
        if not banks:
            print("Banco casa %s no encontrado." % bank)
            return
    print("=" * 96)
    print("BANCOS CASA -- rol operativo derivado, no declarado")
    print("=" * 96)
    print("%-7s %-4s %8s %6s %6s %5s %-9s %-34s %-30s %s"
          % ("banco", "pais", "lineas", "domest", "cheque", "dest", "ult.pago", "topologia", "rol", "PPC"))
    for b in banks:
        if b["lines"] < 20 and not bank:
            continue
        domtxt = ("  n/a" if b["role"].startswith("n/a")
                  else "%4.0f%%" % (100 * b["domestic_share"]))
        print("%-7s %-4s %8d %6s %5.0f%% %5d %-9s %-34s %-30s %s"
              % (b["house_bank"], b["country"], b["lines"], domtxt,
                 100 * b["cheque_share"], b["destination_countries"],
                 (b["last_run"][:4] + "-" + b["last_run"][4:6]) if b["last_run"] else "-",
                 b["topology"], b["role"],
                 "si" if b["ppc"]["dispatches_ppc"] else "no"))
        if bank:
            print("   sociedades : %s" % ", ".join(b["company_codes"]))
            print("   metodos    : %s" % ", ".join(b["methods"]))
            print("   formatos   : %s" % (", ".join(b["dmee_formats"]) or "(ninguno / cheque)"))
            print("   clase BAdI : %s -- %s" % (b["ppc"]["badi_class"], b["ppc"]["why"]))
            print("   destinos   : %s" % ", ".join("%s %d" % (t["country"], t["lines"])
                                                   for t in b["top_payee_countries"]))
            print("   banco del beneficiario conocido en el %.0f%% de sus lineas"
                  % (100 * b["payee_bank_known_share"]))
    print()
    print("  domest = %% de sus pagos donde el banco del beneficiario esta en SU MISMO pais.")
    print("  cheque = %% por metodos con T042Z-XSCHK='X': no producen fichero SAP.")
    print("  dest   = paises de destino distintos: es lo que separa un HUB de una oficina.")
    print("  n/a    = no hay tercero (tesoreria) o sus beneficiarios no tienen banco en LFBK:")
    print("           el % domestico dividiria por un denominador vacio, asi que no se calcula.")
    print("  ult.pago = ultima ejecucion vista. Una cuenta muerta no es una cuenta viva.")
    print("  PPC    = si su pais selecciona una clase BAdI que despacha purpose codes.")
    print()
    print("  OJO -- la aprobacion BCM NO se clava en el banco casa: sus reglas deciden por")
    print("  ZBUKR + importe (y el destino, ZLAND/ZBNKS, para agrupar el lote). HBKID no")
    print("  aparece en bcm_grouping_rule_selop ni en bcm_node_selection_criteria. Tres capas")
    print("  sobre el mismo pago y tres ejes distintos. Claim 532.")


if __name__ == "__main__":
    a = sys.argv[1:]
    d = build()
    if not d:
        sys.exit(2)
    if "--by-company" in a:
        by_company(d)
    elif "--ppc-exposure" in a:
        ppc_exposure(d)
    else:
        show(d,
             country=a[a.index("--country") + 1] if "--country" in a else None,
             bank=a[a.index("--bank") + 1] if "--bank" in a else None)
    print("\n  emitido: brain_v2/house_bank_roles.json")
