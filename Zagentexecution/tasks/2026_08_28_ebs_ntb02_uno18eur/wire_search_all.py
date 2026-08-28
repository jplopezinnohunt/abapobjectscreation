# -*- coding: utf-8 -*-
"""Cabla la BUSQUEDA en los cinco mineros que faltaban.

Cada uno busca sobre los datos que YA tiene en la mano al terminar -- no se anaden lecturas.
El principio es el mismo: nadie esta mejor situado que el minero para verlo, porque es el
unico que tiene esa poblacion delante en ese momento.
"""
import io, sys, ast

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

Q = "Zagentexecution/quality_checks/"

# ---------------------------------------------------------------- D1 cableado
D1 = '''
    # ---- LO QUE ESTE MINERO ENCUENTRA -------------------------------------------
    from _hallazgos import Hallazgos
    h = Hallazgos("house_bank_ebs_wiring_check",
                  denominador=("%d cuentas T012K; se excluyen las CERRADAS (marca CLOSED en "
                               "T012T-TEXT1: %d de %d con texto) y las de extracto MANUAL, que "
                               "no necesitan T028B" % (len(t012k), cerradas, len(txt))))
    rotos = [x for x in h_ if x["clase"] == "A_CABLE_ROTO"]
    if rotos:
        h.riesgo("Cuentas VIVAS con extracto electronico cuyo cableado T028B apunta a un numero "
                 "de cuenta que ya no existe: el extracto deja de entrar EN SILENCIO",
                 tamano="%d cuenta(s): %s" % (len(rotos), ", ".join(x["cuenta"] for x in rotos)),
                 evidencia="T028B no tiene fila para el BANKN actual de T012K",
                 limite="veo el cable roto, no si el banco sigue emitiendo el fichero",
                 accion="anadir la fila en V_T028B con el numero ACTUAL y transportar")
    huerf = [x for x in h_ if x["clase"] == "B_HUERFANA"]
    if huerf:
        h.oportunidad("Filas de T028B con numeros de cuenta que ya no son de ninguna cuenta "
                      "viva: el rastro acumulado de cambios que nadie barrio",
                      tamano="%d filas huerfanas de %d" % (len(huerf), len(t028b)),
                      evidencia="T028B.KTONR sin correspondencia en T012K.BANKN",
                      limite="no se si alguna se dejo a proposito como historico",
                      accion="borrar tras confirmar que su cuenta ya no recibe")
    mudos = [x for x in h_ if x["clase"] == "C_CANAL_MUERTO"]
    if mudos:
        h.desafio("Cuentas que recibian con regularidad y llevan dias mudas mientras su sociedad "
                  "sigue recibiendo: no se si el banco dejo de mandar o si nadie lo procesa",
                  tamano="%d cuenta(s): %s" % (len(mudos),
                                               "; ".join(x["cuenta"] for x in mudos[:6])),
                  evidencia="ultimo FEBKO.AZDAT frente al maximo de su sociedad",
                  limite="no puedo ver el directorio del banco desde aqui",
                  quien_puede_contestar="Tesoreria (BFM/MO) y el equipo de interfaces")
    h.emitir()

'''

# ---------------------------------------------------------------- D3
D3 = '''
    # ---- LO QUE ESTE MINERO ENCUENTRA -------------------------------------------
    from _hallazgos import Hallazgos
    h = Hallazgos("bank_account_nature_model",
                  denominador="%d cuentas VIVAS (excluidas las marcadas CLOSED en el texto)"
                              % len(filas))
    sinc = [f for f in filas if f["naturaleza"] == "SIN_CLASIFICAR"]
    if sinc:
        h.desafio("La NATURALEZA de la cuenta no esta declarada en ninguna parte del sistema: "
                  "se deduce del texto libre, y en la mayoria no hay ni texto reconocible",
                  tamano="%d de %d cuentas vivas sin ninguna senal (%.0f%%)"
                         % (len(sinc), len(filas), 100.0 * len(sinc) / max(1, len(filas))),
                  evidencia="ni pertenencia a un set YBANK ni palabra reconocible en T012T",
                  limite=("YBANK clasifica geografia x divisa, no naturaleza; SKB1-FDLEV es "
                          "binario; y el balance mete todas las cuentas en Cash with Banks"),
                  quien_puede_contestar="Tesoreria: declarar el vocabulario y extender YBANK")
    mand = [f for f in filas if f["naturaleza"] == "MANDATO_INVERSION"]
    sin_ext = [f for f in mand if f["canal"] == "SIN EXTRACTO"]
    if mand and len(sin_ext) == len(mand):
        h.riesgo("TODAS las cuentas de mandato de inversion carecen de extracto bancario, y aun "
                 "asi se presentan en el balance como Cash and Cash Equivalents",
                 tamano="%d de %d cuentas de mandato" % (len(sin_ext), len(mand)),
                 evidencia="cero FEBKO y posicion FS10 = 1.1.1.1 Cash with Banks",
                 limite=("la pata de EFECTIVO de un mandato de custodia es legitimamente "
                         "efectivo: NO se afirma error contable"),
                 accion="preguntar a Finanzas: si el saldo es efectivo, por que no llega extracto")
    h.emitir()

'''

# ---------------------------------------------------------------- D4
D4 = '''
    # ---- LO QUE ESTE MINERO ENCUENTRA -------------------------------------------
    from _hallazgos import Hallazgos
    h = Hallazgos("bank_config_profile_by_nature",
                  denominador="%d cuentas VIVAS de %s" % (len(filas), a.bukrs or "todas las sociedades"))
    # (5) DISCREPANCIA: grupos donde las cuentas de una misma naturaleza NO coinciden.
    # No es una regla rota: es que NO HAY regla, o hay deriva. Las dos hay que resolverlas.
    disc = []
    for nat in sorted({f["naturaleza"] for f in filas}):
        g = [f for f in filas if f["naturaleza"] == nat]
        for e in ELEM:
            p = pct(g, e)
            if 15 <= p <= 85 and len(g) >= 4:
                disc.append("%s/%s %d%%" % (nat, e, p))
    if disc:
        h.desafio("Cuentas de la MISMA naturaleza no coinciden en su configuracion: o es una "
                  "regla que nadie escribio, o es deriva",
                  tamano="%d combinaciones naturaleza x elemento sin consenso: %s"
                         % (len(disc), ", ".join(disc[:8])),
                  evidencia="porcentaje de cuentas del grupo que tienen el elemento",
                  limite="no se cual de las dos es sin preguntar: el dato no lo distingue",
                  quien_puede_contestar="Tesoreria / DBS: decidir si es regla o deriva")
    paga = [f for f in filas if f["PAGA_T042I"]]
    ops = [f for f in filas if f["naturaleza"] == "OPERATIVA"]
    if ops and paga:
        h.dato("La naturaleza YA PREDICE la configuracion de pago, aunque nadie la haya declarado",
               tamano="%d de %d OPERATIVAS estan en determinacion de banco; de las demas "
                      "naturalezas, %d" % (sum(1 for f in ops if f["PAGA_T042I"]), len(ops),
                                           len([f for f in paga if f["naturaleza"] != "OPERATIVA"])),
               evidencia="T042I frente a la naturaleza derivada",
               limite="correlacion medida, no regla declarada en el sistema",
               accion="es el argumento para declarar la naturaleza (PMO H144)")
    h.emitir()

'''

# ---------------------------------------------------------------- D5
D5 = '''
    # ---- LO QUE ESTE MINERO ENCUENTRA -------------------------------------------
    from _hallazgos import Hallazgos
    h = Hallazgos("bank_account_behaviour_signature",
                  denominador="%d cuentas VIVAS (excluidas las marcadas CLOSED en el texto)"
                              % len(filas))
    mse = [f for f in filas if f["tipo"] == "MUEVE_SIN_EXTRACTO"]
    if mse:
        h.riesgo("Cuentas que MUEVEN SALDO sin recibir ni un extracto bancario: nada corrobora "
                 "el movimiento",
                 tamano="%d cuenta(s), %s" % (len(mse), "; ".join(
                     "%s %d periodos" % (f["cuenta"], f["periodos_mov"]) for f in mse[:5])),
                 evidencia="GLT0 con movimiento y cero cabeceras en FEBKO",
                 limite="no se si el banco emite extracto y no llega, o no lo emite",
                 accion="reclamar el extracto al banco o declarar por que no aplica")
    ese = [f for f in filas if f["tipo"] == "EXTRACTO_SIN_MOVIMIENTO"]
    if ese:
        h.oportunidad("Cuentas que reciben extractos y no producen NINGUN movimiento contable: "
                      "trabajo que se procesa sin efecto",
                      tamano="%d cuentas, %d extractos en la ventana"
                             % (len(ese), sum(f["extractos"] for f in ese)),
                      evidencia="FEBKO con cabeceras y GLT0 sin periodos con movimiento",
                      limite=("puede que sean extractos a cero legitimos, o que la "
                              "contabilizacion vaya a otro mayor: el dato no lo distingue"),
                      accion="mirar una de ellas en FEBAN antes de generalizar")
    durm = [f for f in filas if f["tipo"] == "DURMIENTE"]
    if durm:
        h.desafio("Cuentas VIVAS que no pagan, no reciben y no mueven: no se si estan cerradas "
                  "de hecho y nadie lo declaro",
                  tamano="%d cuentas: %s" % (len(durm), ", ".join(f["cuenta"] for f in durm[:8])),
                  evidencia="cero en los tres ejes durante toda la ventana",
                  limite="'CLOSED' en el texto es la unica marca de estado y estas no la llevan",
                  quien_puede_contestar="Tesoreria: cerrarlas o declarar por que siguen abiertas")
    h.emitir()

'''

# ---------------------------------------------------------------- D6
D6 = '''
    # ---- LO QUE ESTE MINERO ENCUENTRA -------------------------------------------
    from _hallazgos import Hallazgos
    h = Hallazgos("ebs_format_consolidation",
                  denominador="%d cuentas VIVAS de %s, %d con extracto en la ventana"
                              % (len(filas), a.bukrs or "todas",
                                 sum(1 for f in filas if f["extractos"])))
    if solos:
        nr = sum(len(reglas.get(v, ())) for v, _ in solos)
        nc = sum(len(g) for _, g in solos)
        h.oportunidad("Modelos de extracto que existen para UN SOLO banco: cada uno es un modelo "
                      "entero -- con su prueba y su riesgo -- sosteniendo muy pocas cuentas",
                      tamano="%d modelos, %d reglas para %d cuentas, sobre un total de %d reglas"
                             % (len(solos), nr, nc, tot_reglas),
                      evidencia="T028B agrupado por VGTYP y T028G contado por modelo",
                      limite=("parecido alto NO significa consolidable: absorber uno dentro de "
                              "otro puede CAMBIAR su algoritmo y con el la contabilizacion"),
                      accion="mirar primero los pares con parecido alto, no los mas pequenos")
    sin_modelo = [f for f in filas if f["vgtyp"] == "(sin modelo)" and f["extractos"] > 0]
    if sin_modelo:
        h.riesgo("Cuentas que RECIBEN extracto y no tienen modelo de formato asignado",
                 tamano="%d cuenta(s), %d extractos: %s"
                        % (len(sin_modelo), sum(f["extractos"] for f in sin_modelo),
                           ", ".join(f["cuenta"] for f in sin_modelo[:5])),
                 evidencia="sin fila en T028B para su clave de banco y numero de cuenta",
                 limite="el extracto pudo entrar antes de que el numero cambiara",
                 accion="es la firma exacta del defecto de INC-000013624")
    h.emitir()

'''

PLAN = [
    (Q + "house_bank_ebs_wiring_check.py", D1,
     "    graves = [x for x in h if x[\"grave\"]]"),
    (Q + "bank_account_nature_model.py", D3, "    if a.json:"),
    (Q + "bank_config_profile_by_nature.py", D4, "    if a.json:"),
    (Q + "bank_account_behaviour_signature.py", D5, "    if a.json:"),
    (Q + "ebs_format_consolidation.py", D6, "    if a.json:"),
]

for path, bloque, anc in PLAN:
    s = io.open(path, encoding="utf-8").read()
    nombre = path.split("/")[-1]
    if "LO QUE ESTE MINERO ENCUENTRA" in s:
        print("%-42s ya estaba" % nombre)
        continue
    if anc not in s:
        print("%-42s ANCLA NO ENCONTRADA (%s)" % (nombre, anc.strip()[:30]))
        continue
    # D1 usa `h` como nombre de su lista de hallazgos: se renombra para no chocar
    if "house_bank_ebs_wiring" in path:
        s = s.replace("    h = analizar(", "    h_ = analizar(", 1)
        s = s.replace("    for x in h:\n", "    for x in h_:\n")
        s = s.replace("        por[x[\"clase\"]].append(x)", "        por[x[\"clase\"]].append(x)")
        s = s.replace("    for x in h:", "    for x in h_:")
        s = s.replace("x[\"grave\"]] for x in h]", "x[\"grave\"]] for x in h_]")
        s = s.replace("graves = [x for x in h if x[\"grave\"]]", "graves = [x for x in h_ if x[\"grave\"]]")
        s = s.replace("len(h) - len(graves)", "len(h_) - len(graves)")
        anc = "    graves = [x for x in h_ if x[\"grave\"]]"
    s = s.replace(anc, bloque + anc, 1)
    io.open(path, "w", encoding="utf-8").write(s)
    try:
        ast.parse(s)
        print("%-42s cableado · sintaxis OK" % nombre)
    except SyntaxError as e:
        print("%-42s SINTAXIS ROTA: %s" % (nombre, e))
