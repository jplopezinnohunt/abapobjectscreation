# -*- coding: utf-8 -*-
"""Arregla el defecto de RECUPERACION del toolgraph: preguntamos en español, los instrumentos
se describen en inglés, y el emparejamiento es por token literal. Resultado medido: la
pregunta "el extracto bancario electronico de una cuenta dejo de procesarse" devuelve
braintoolbox y sap_log_forensics, y NO devuelve sap_bank_statement_recon. La misma pregunta en
inglés lo devuelve PRIMERO.

Ese es el fallo mas caro de s108: el experto existia y nada apuntaba a el. No es falta de
conocimiento en el skill -- es que la puerta de entrada esta ciega a nuestro idioma.

La correccion es un GLOSARIO: cada termino se expande a sus equivalentes, y una palabra cuenta
como presente si aparece ELLA o cualquiera de sus equivalentes. Aditivo: no puede empeorar una
busqueda que ya funcionaba, porque solo AÑADE formas de acertar.
"""
import io, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

P = "brain_v2/graph_queries.py"
s = io.open(P, encoding="utf-8").read()

GLOSARIO = '''
# --- PUENTE BILINGUE -------------------------------------------------------------------
# Preguntamos en español; los skills, algoritmos y agentes se describen en ingles. El
# emparejamiento es por token literal, asi que "extracto bancario electronico" puntuaba CERO
# contra un skill cuya descripcion dice "electronic bank statement". Medido en s108: la
# pregunta en ingles devolvia sap_bank_statement_recon el PRIMERO; en español, NADA -- y por
# eso se re-derivo a mano un pipeline que el skill ya documentaba.
#
# Es ADITIVO: una palabra cuenta si aparece ella O cualquiera de sus equivalentes. No puede
# empeorar una busqueda que ya acertaba, solo añade formas de acertar.
GLOSARIO_ES_EN = {
    "extracto": ["statement"], "extractos": ["statement", "statements"],
    "banco": ["bank"], "bancos": ["bank", "banks"], "bancario": ["bank", "banking"],
    "bancaria": ["bank", "banking"], "electronico": ["electronic"], "electronica": ["electronic"],
    "cuenta": ["account"], "cuentas": ["account", "accounts"],
    "pago": ["payment"], "pagos": ["payment", "payments"], "pagar": ["payment", "pay"],
    "cobro": ["collection", "incoming"], "conciliacion": ["reconciliation"],
    "fichero": ["file"], "ficheros": ["file", "files"], "formato": ["format"],
    "sociedad": ["company", "bukrs"], "sociedades": ["company", "companies"],
    "mayor": ["ledger", "gl", "account"], "saldo": ["balance"], "saldos": ["balance", "balances"],
    "divisa": ["currency"], "moneda": ["currency"], "revaluacion": ["revaluation", "valuation"],
    "transporte": ["transport"], "transportes": ["transport", "transports"],
    "proveedor": ["vendor"], "proveedores": ["vendor", "vendors"],
    "cliente": ["customer"], "clientes": ["customer", "customers"],
    "factura": ["invoice"], "facturas": ["invoice", "invoices"],
    "asiento": ["document", "posting"], "contabilizacion": ["posting"],
    "cierre": ["closing"], "presupuesto": ["budget"], "fondo": ["fund"], "fondos": ["fund", "funds"],
    "empleado": ["employee"], "nomina": ["payroll"], "viaje": ["travel"],
    "firmante": ["signatory"], "firmantes": ["signatory", "signatories"],
    "autorizacion": ["authorization", "authorisation"], "aprobacion": ["approval"],
    "interfaz": ["interface"], "interfaces": ["interface", "interfaces"],
    "trabajo": ["job"], "variante": ["variant"], "variantes": ["variant", "variants"],
    "regla": ["rule"], "reglas": ["rule", "rules"], "puerta": ["gate", "check"],
    "deriva": ["drift"], "hueco": ["gap"], "huecos": ["gap", "gaps"],
    "incidencia": ["incident"], "incidente": ["incident"],
    "configuracion": ["configuration", "customizing", "config"],
    "maestro": ["master"], "codigo": ["code"], "programa": ["program"],
    "usuario": ["user"], "usuarios": ["user", "users"], "rol": ["role"], "roles": ["role", "roles"],
    "informe": ["report"], "informes": ["report", "reports"],
    "proceso": ["process"], "procesos": ["process", "processes"],
    "naturaleza": ["nature"], "canal": ["channel"], "canales": ["channel", "channels"],
    "manual": ["manual"], "automatico": ["automatic", "automated"],
    "tesoreria": ["treasury"], "inversion": ["investment"], "deposito": ["deposit"],
    "cheque": ["check", "cheque"], "iban": ["iban"], "mandato": ["mandate"],
}


def _expandir(palabras):
    """Cada palabra mas sus equivalentes. Se conserva SIEMPRE la original."""
    fuera = []
    for w in palabras:
        fuera.append([w] + GLOSARIO_ES_EN.get(w, []))
    return fuera
'''

# 1. insertar el glosario antes de la primera funcion que lo use
anc = "def tool(brain, q):"
if "GLOSARIO_ES_EN" in s:
    print("glosario: ya estaba")
else:
    s = s.replace(anc, GLOSARIO.strip() + "\n\n\n" + anc, 1)
    print("glosario: insertado")

# 2. tool para -> puntuar contra las variantes
old = '''        def puntua(n, v):
            blob = json.dumps(v, ensure_ascii=False).lower() + " " + n.lower()
            return sum(1 for w in pal if w in blob)'''
new = '''        variantes = _expandir(sorted(pal))

        def puntua(n, v):
            blob = json.dumps(v, ensure_ascii=False).lower() + " " + n.lower()
            # una palabra cuenta si aparece ELLA o cualquiera de sus equivalentes
            return sum(1 for formas in variantes if any(f in blob for f in formas))'''
if new.split("\n")[0] in s:
    print("tool para: ya estaba")
elif old in s:
    s = s.replace(old, new, 1)
    print("tool para: puntuacion bilingue")
else:
    print("tool para: ANCLA NO ENCONTRADA")

# 3. search -> mismo puente
old2 = '''    def hit(blob):
        low = blob.lower()
        if q in low:
            return True
        return bool(words) and all(w in low for w in words)'''
new2 = '''    _var = _expandir(words)

    def hit(blob):
        low = blob.lower()
        if q in low:
            return True
        # ALL-WORDS-PRESENT, pero cada palabra vale por si misma O por su equivalente
        return bool(_var) and all(any(f in low for f in formas) for formas in _var)'''
if new2.split("\n")[0].strip() in s:
    print("search: ya estaba")
elif old2 in s:
    s = s.replace(old2, new2, 1)
    print("search: emparejamiento bilingue")
else:
    print("search: ANCLA NO ENCONTRADA")

io.open(P, "w", encoding="utf-8").write(s)
