# -*- coding: utf-8 -*-
"""Pasada de steward de s108: promueve al store central lo que quedaba solo en la conversacion.

Dos cosas, y solo dos, porque el resto ya estaba promovido (incidente, docs de dominio,
skills, companions, algorithms D1-D6, PMO H144, memoria):

  1. CLAIMS  -- los hechos medidos hoy no estaban en claims.json
  2. UNA REGLA se EXTIENDE, no se duplica. feedback_name_the_source_before_you_assert ya
     cubre "lectura FALLIDA no es ausencia". Lo de hoy es distinto: lecturas que salieron
     BIEN, sin error y con cero filas, porque preguntaban en el sitio equivocado. Se anade
     como quinta forma (e) a la regla que ya existe.
"""
import json, io, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- 1. CLAIMS ---------------------------------------------------------
P = "brain_v2/claims/claims.json"
claims = json.load(io.open(P, encoding="utf-8"))
maxid = max(c.get("id", 0) for c in claims)

BASE = dict(claim_type="SYSTEM_FACT", confidence="TIER_1", status="VERIFIED",
            domain="Treasury_EBS", created_session=108)

NUEVOS = [
    dict(BASE, claim=(
        "EL NUMERO DE CUENTA DE UN BANCO CASA VIVE EN DOS TABLAS DE CUSTOMIZING Y FI12 SOLO "
        "ESCRIBE EN UNA. Medido en P01 el 2026-08-28: de las 41 tablas de customizing con un "
        "campo cuyo elemento de datos es un numero de cuenta bancaria, solo DOS contienen las "
        "cuentas de UNESCO -- T012K (ficha del banco casa, la que toca FI12) y T028B "
        "(Transaction Type of Sender Bank, SM30 V_T028B), cuya clave es BANKL+KTONR. Al cambiar "
        "el numero, la fila de T028B queda huerfana y el extracto electronico DEJA DE ENTRAR EN "
        "SILENCIO: no hay error, la ficha se ve perfecta y el job EBS INTEGRATION sigue "
        "terminando en verde. Control: las 6 cuentas de NTB01 que siguen entrando a diario "
        "tienen T028B.KTONR identico a T012K.BANKN; NTB02/EUR01 dejo de tenerlo el 17.08.2026 y "
        "el extracto se paro ese dia. T035D NO es esa tabla (es Cash Management Account Names, "
        "clave BUKRS+DISKB, no se ve afectada)."),
        domain_axes=dict(functional=["Treasury"], module=["FI"], process=["T2R"]),
        evidence_for=["knowledge/incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md",
                      "Zagentexecution/quality_checks/house_bank_ebs_wiring_check.py"],
        evidence_against=[],
        related_objects=["T028B", "T012K", "T035D", "V_T028B", "FI12", "NTB02", "NTB01"],
        resolution_notes="INC-000013624. Procedimiento: house_bank_configuration.md seccion 2b."),

    dict(BASE, claim=(
        "LA NATURALEZA DE UNA CUENTA BANCARIA NO ESTA MODELADA EN NINGUNA PARTE DEL SISTEMA: "
        "vive en el texto libre. Tres candidatos medidos en P01 el 2026-08-28 y los tres fallan. "
        "(1) YBANK (sets de Report Painter, SETCLASS 0000 sobre GLT0-RACCT, se mantienen en "
        "GS01/GS02) clasifica GEOGRAFIA x DIVISA: los mandatos MANDATE PIMCO, MANDATE JP MORGAN y "
        "RAMP estan en YBANK_ACCOUNTS_HQ_USD, el MISMO cajon que SOG01-USDD1 y CIT04-USD04, que "
        "son las operativas generales de sede. (2) SKB1-FDLEV reparte los 549 mayores de banco de "
        "UNES en B0=392 y B1=157, pero las 8 cuentas de Northern Trust son B0, mandatos incluidos. "
        "(3) La version de balance FS10 -- la que UNES ejecuta de verdad -- mete las 352 cuentas de "
        "banco en UNA sola posicion, 1.1.1.1 Cash with Banks, teniendo 1.1.2.1 Short Term Deposits "
        "y 1.2.1.1 Other Investments construidas y sin usar por ninguna cuenta. Resultado: 141 de "
        "167 cuentas vivas sin señal de naturaleza."),
        domain_axes=dict(functional=["Treasury"], module=["FI"], process=["T2R"]),
        evidence_for=["knowledge/domains/Treasury/bank_account_nature_model.md",
                      "Zagentexecution/quality_checks/bank_account_nature_model.py"],
        evidence_against=[],
        related_objects=["YBANK_ACCOUNTS_HQ_USD", "SETLEAF", "SKB1", "FAGL_011ZC", "T012T",
                         "NTB01", "NTB02", "GS02"],
        resolution_notes="PMO H144. YBANK es aun asi el mejor de los tres y el sitio para extender."),

    dict(BASE, claim=(
        "LOS SETS YBANK LOS CONSUME UN SOLO INFORME Y SE TRANSPORTAN COMO TABLA COMPLETA. Medido "
        "en P01 el 2026-08-28: SETUSE_REP tiene 7.693 referencias de set en 894 informes de Report "
        "Painter, y EXACTAMENTE UNA nombra un set YBANK -- 0B1 / ZAVERAGE / 0000YBANK_ACCOUNTS_ALL, "
        "el informe de saldos medios que se corre desde GS02. Y SOLO el nodo RAIZ: las 10 hojas y "
        "los subnodos (_HQ_CA, _SIGHT, _DEPOSIT, _HQ_EUR...) no los nombra ningun informe, existen "
        "unicamente como estructura de desglose. En ABAP el uso es CERO en todo el corpus extraido. "
        "Se transportan como objeto TDAT GRW_SET -- contenido de tabla, no sets con nombre: el "
        "transporte D01K9B0F5F (liberado, JP_LOPEZ, 2026-04-07) contiene UNA sola entrada, y por "
        "eso E071 da cero filas para YBANK% y 0000YBANK%. Lleva el SET COMPLETO, no un delta: hay "
        "que alinear D01 y P01 ANTES de transportar. SUPERSEDE la afirmacion previa de "
        "house_bank_configuration.md de que 'no son transportables'."),
        domain_axes=dict(functional=["Treasury"], module=["FI"], process=["T2R"]),
        evidence_for=["knowledge/domains/Treasury/bank_account_nature_model.md",
                      "Zagentexecution/tasks/2026_08_28_ebs_ntb02_uno18eur/ybank_what_is_it.py",
                      "Zagentexecution/tasks/2026_08_28_ebs_ntb02_uno18eur/ybank_where_used.py"],
        evidence_against=[],
        related_objects=["SETUSE_REP", "ZAVERAGE", "SETHEADER", "SETNODE", "SETLEAF", "GRW_SET",
                         "D01K9B0F5F", "GS02"],
        resolution_notes="Corrige un claim implicito que llevaba meses escrito en el doc de dominio."),

    dict(BASE, claim=(
        "EL PARQUE DE CUENTAS BANCARIAS NO ES HOMOGENEO Y LAS CUENTAS CERRADAS SE MARCAN EN EL "
        "TEXTO. Medido en P01, ventana 2025-2026: de 404 cuentas de banco casa, 237 llevan CLOSED "
        "en T012T-TEXT1 (con guiones arbitrarios de relleno: 'CLOSED-----UNESCO YAOUNDE') -- NO hay "
        "campo de estado, es una convencion humana, y toda medida sobre el parque que no aplique "
        "ese corte mide un denominador falso. De las 167 vivas: 120 reciben extracto ELECTRONICO, "
        "8 MANUAL tecleado en FF67, 27 MIXTO y 12 ninguno. El extracto MANUAL (FEBKO.EFART='M') NO "
        "necesita fila en T028B -- BTE01-USD01 importo 116 extractos y BTE01-IRR01 otros 156 sin "
        "esa fila jamas. Solo 131 de las 143 cuentas con extractos son electronicas. Y hay que "
        "partir SIEMPRE por sociedad: CBE01-ETB02 recibe 543 extractos al año en ICBA y CERO en "
        "UNES. Proporcion de anomalias: UNES 10%, UIL 40%, UBO 33%."),
        domain_axes=dict(functional=["Treasury"], module=["FI"], process=["T2R"]),
        evidence_for=["knowledge/domains/Treasury/bank_statement_channels_by_company.md",
                      "Zagentexecution/quality_checks/bank_statement_channel_census.py"],
        evidence_against=[],
        related_objects=["T012T", "FEBKO", "T028B", "FF67", "BTE01", "CBE01", "BLN01", "BMN01"],
        resolution_notes="Los tres cortes (cerrada / electronica / ventana) estan clavados como autotest."),

    dict(BASE, claim=(
        "UNESCO SOSTIENE 9 MODELOS DE EXTRACTO Y 259 REGLAS PARA 133 CUENTAS, Y CINCO EXISTEN PARA "
        "UNA SOLA CUENTA. Medido en P01 sobre UNES, 2025-2026: XRT940 cubre 60 bancos, 104 cuentas "
        "y 38.822 extractos con 130 reglas (todas SUBC/SUBD, algoritmo 015). TR_TRNF 7 bancos, 20 "
        "reglas, algoritmo 000. SOG_FR y SOG_FRB son 89% identicos -- difieren en UNA regla (111I "
        "vs 111B) -- y son la unica consolidacion que la evidencia sostiene sola: 36 reglas donde "
        "bastan 18. SCB19_IQ y CIT24_GA son SUBC/SUBD 8+8, la MISMA forma que XRT940, con "
        "algoritmo 001 en vez de 015: hasta 34 reglas mas si se decide que el 001 no hace falta. "
        "CIT04_US (algoritmo 019, ficheros DME de Worldlink) y SOG_EUR4 (reglas 201I/201O de "
        "cliente) son legitimamente distintos -- absorberlos DESTRUIRIA automatizacion. Y once "
        "cuentas tienen modelo asignado y no lo usan; verificado el movimiento, SEIS son reales "
        "(CBE01-ETB02 esta durmiente)."),
        domain_axes=dict(functional=["Treasury"], module=["FI"], process=["T2R"]),
        evidence_for=["knowledge/domains/Treasury/ebs_format_models.md",
                      "Zagentexecution/quality_checks/ebs_format_consolidation.py"],
        evidence_against=[],
        related_objects=["T028B", "T028G", "XRT940", "TR_TRNF", "SOG_FR", "SOG_FRB", "CIT04_US",
                         "SCB19_IQ", "CIT24_GA", "SOG_EUR4"],
        resolution_notes="PMO H144 eje A. Medir el parecido por tupla exacta daba 0% y era la metrica equivocada."),

    dict(BASE, claim=(
        "TRES CUENTAS DE MANDATO DE INVERSION MUEVEN SALDO SIN RECIBIR NI UN EXTRACTO BANCARIO. "
        "Medido en P01, 2025-2026: UNES/NTB01-USD04 (MANDATE PIMCO), USD05 (MANDATE JP MORGAN) y "
        "USD06 (RAMP) tienen movimiento en 3, 5 y 3 periodos respectivamente -- USD05 mueve 33,4 M "
        "en moneda local -- y CERO extractos. La cuarta de mandato, NTB02-EUR02 (IMIP), esta "
        "realmente durmiente: sin extractos, sin pagos y sin movimiento. El control que da valor al "
        "hallazgo: el MISMO custodio tiene otras cuatro cuentas -- USD01 PFF Nessim Habif, USD02 "
        "Cash Pool, USD03 ASHI USD y NTB02-EUR01 ASHI EUR -- que reciben extracto a diario con el "
        "MISMO formato TR_TRNF. No es el banco ni el formato: es la cuenta. Ademas, las cuatro se "
        "presentan en el balance como Cash and Cash Equivalents. PREGUNTA ABIERTA para Finanzas: "
        "si su saldo es efectivo, por que no llega extracto; y si no lo es, la posicion de balance "
        "no es la suya. NO se afirma error contable: la pata de efectivo de un mandato de custodia "
        "es legitimamente efectivo."),
        confidence="TIER_1", status="OPEN_QUESTION",
        domain_axes=dict(functional=["Treasury"], module=["FI"], process=["T2R"]),
        evidence_for=["knowledge/domains/Treasury/bank_account_nature_model.md",
                      "Zagentexecution/quality_checks/bank_account_behaviour_signature.py"],
        evidence_against=[],
        related_objects=["NTB01", "NTB02", "TR_TRNF", "GLT0", "FEBKO", "FAGL_011ZC"],
        resolution_notes="PMO H144 punto 2. Requiere confirmacion de Tesoreria/Finanzas."),
]

for i, c in enumerate(NUEVOS, 1):
    c["id"] = maxid + i
    claims.append(c)
json.dump(claims, io.open(P, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("claims.json: %d (+%d de s108, ids %d-%d)"
      % (len(claims), len(NUEVOS), maxid + 1, maxid + len(NUEVOS)))

# ---------- 2. EXTENDER la regla, no duplicarla -------------------------------
R = "brain_v2/agent_rules/feedback_rules.json"
d = json.load(io.open(R, encoding="utf-8"))
rules = d if isinstance(d, list) else d.get("rules")
EXT = (" (e) UNA LECTURA QUE SALE BIEN EN EL SITIO EQUIVOCADO TAMPOCO ES AUSENCIA, y es peor "
       "que (a) porque no avisa: no hay error, no hay TABLE_WITHOUT_DATA, hay CERO FILAS limpias. "
       "Tres veces el mismo dia en s108: busque el set YBANK en E071 por OBJ_NAME LIKE 'YBANK%' y "
       "di cero -- se transporta como TDAT GRW_SET, un nombre que no contiene 'YBANK'; ademas "
       "busque un transporte D01K* en el E071 de P01, donde no vive. Busque el informe ZCASH en "
       "TSTC y VARID, donde un informe de Report Painter no esta por definicion. Y lei T030H por "
       "KONKO, campo que esa tabla no tiene, publicando 'OBA1 = 0% en TODAS las naturalezas'. "
       "ANTES de leer un cero como inexistencia: comprobar que el LOCUS y la CLAVE son los que el "
       "objeto usa de verdad -- diccionario para el campo, y para el nombre, como se llama el "
       "objeto en ESE registro. Un cero uniforme sobre una poblacion entera es la señal de alarma.")
n = 0
for x in rules:
    if (x.get("id") or x.get("name")) == "feedback_name_the_source_before_you_assert":
        if "(e) UNA LECTURA QUE SALE BIEN" not in x.get("rule", ""):
            x["rule"] = x["rule"].rstrip() + EXT
            x["extended_session"] = 108
            n += 1
json.dump(d, io.open(R, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("feedback_rules.json: regla extendida (%d)" % n)
print("\nNO se anade regla nueva: las 258 ya cubren esta familia "
      "(name_the_source, declare_the_denominator, gate_measures_the_effect). "
      "Hoy se violaron reglas EXISTENTES, no se descubrio una nueva.")
