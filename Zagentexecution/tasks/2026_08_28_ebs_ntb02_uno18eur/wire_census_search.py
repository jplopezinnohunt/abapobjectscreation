# -*- coding: utf-8 -*-
"""Cabla la BUSQUEDA en el censo de canales: que el minero se haga las preguntas el mismo.

Hoy el censo produce un censo y la oportunidad la ve quien lo lee. A partir de aqui el minero
busca sobre sus propias filas y EMITE oportunidad, riesgo y desafio -- porque nadie esta mejor
situado que el para verlo: es el unico que tiene los datos delante.
"""
import io, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

P = "Zagentexecution/quality_checks/bank_statement_channel_census.py"
s = io.open(P, encoding="utf-8").read()

BUSQUEDA = '''
    # =================================================================================
    # LA BUSQUEDA. El censo de arriba son DATOS; esto es lo que el minero ENCUENTRA.
    # =================================================================================
    # Nadie esta mejor situado que este minero para verlo: es el unico que tiene delante,
    # a la vez, el canal de cada cuenta, su cadencia real y quien la sostiene.
    from _hallazgos import Hallazgos

    h = Hallazgos(
        "bank_statement_channel_census",
        denominador=("%d cuentas de banco casa; %d excluidas por llevar CLOSED en T012T-TEXT1 "
                     "(no hay campo de estado: es una convencion humana); quedan %d vivas"
                     % (len(filas), len(filas) - len(vivas), len(vivas))),
        ventana="%s -> hoy" % a.desde)

    # --- (1) EXISTE Y NO SE USA -------------------------------------------------------
    con_modelo_sin_usar = [f for f in vivas
                           if f["canal"] in ("MANUAL", "SIN EXTRACTO") and f["tiene_t028b"]]
    if con_modelo_sin_usar:
        man = [f for f in con_modelo_sin_usar if f["canal"] == "MANUAL"]
        h.oportunidad(
            "Hay cuentas con el modelo de extracto electronico YA MONTADO que no lo usan",
            tamano=("%d cuentas (%d se teclean a mano, %d no reciben nada), frente a %d que si "
                    "lo procesan electronicamente con ese mismo modelo"
                    % (len(con_modelo_sin_usar), len(man), len(con_modelo_sin_usar) - len(man),
                       sum(1 for f in vivas if f["canal"] in ("ELECTRONICO", "MIXTO")))),
            evidencia="T028B tiene fila para su BANKN actual y FEBKO.EFART no es 'E'",
            limite=("tener el modelo asignado NO prueba que el fichero pueda llegar: la "
                    "restriccion puede estar aguas arriba, en que el banco emita MT940"),
            accion="preguntar a esos bancos si emiten MT940 -- el coste en SAP es cero")

    # --- (2) SE MUEVE SIN SU CONTRAPARTE ----------------------------------------------
    # Lo que este minero PUEDE ver: cuentas vivas sin ningun extracto. Que ademas MUEVAN
    # saldo lo sabe bank_account_behaviour_signature, no yo -- y eso se declara.
    sin_nada = [f for f in vivas if f["canal"] == "SIN EXTRACTO"]
    if sin_nada:
        h.riesgo(
            "Cuentas VIVAS sin ningun extracto bancario: nada corrobora lo que el banco dice",
            tamano="%d cuentas vivas, %d de ellas de sociedades distintas de UNES"
                   % (len(sin_nada), sum(1 for f in sin_nada if f["bukrs"] != "UNES")),
            evidencia="cero cabeceras en FEBKO en toda la ventana",
            limite=("no se si MUEVEN dinero: eso lo mide bank_account_behaviour_signature. "
                    "Sin cruzarlo, esto es una lista, no un riesgo dimensionado"),
            accion="cruzar con behaviour_signature antes de escalar")

    # --- (6) LA MISMA PERSONA EN DOS ESLABONES ----------------------------------------
    # El canal MANUAL mete una PERSONA en el eslabon de entrada. El automatico no: es
    # JOBBATCH. Esa ausencia es lo que hace mas seguro el canal automatico, y es justo lo
    # que se pierde cuando una cuenta se teclea.
    manuales = [f for f in vivas if f["canal"] == "MANUAL"]
    if manuales:
        personas = sorted({f["quien"] for f in manuales if f["quien"]})
        h.riesgo(
            "El extracto MANUAL mete una persona en el eslabon de ENTRADA, donde el canal "
            "automatico no tiene ninguna (JOBBATCH)",
            tamano="%d cuentas sostenidas por %d usuarios con nombre: %s"
                   % (len(manuales), len(personas), ", ".join(personas[:6])),
            evidencia="FEBKO.EUSER de esas cuentas",
            limite=("solo veo QUIEN teclea. Si esa misma persona ademas contabiliza o "
                    "compensa el documento resultante (BKPF.USNAM) o emite pagos (REGUH), "
                    "eso NO lo mide este minero"),
            accion="cruzar EUSER contra BKPF.USNAM y REGUH de la misma cuenta")

    # --- DESAFIOS: lo que no cuadra y no puedo cerrar yo ------------------------------
    mudas = [f for f in manuales if (f["dias_mudo"] or 0) > 60]
    if mudas:
        h.desafio(
            "Cuentas manuales que llevan meses sin extracto sin que nada lo detecte: no se si "
            "es un incumplimiento o si la cuenta dejo de usarse y nadie lo declaro",
            tamano="; ".join("%s %d dias" % (f["cuenta"], f["dias_mudo"]) for f in mudas),
            evidencia="ultimo FEBKO.AZDAT frente al ritmo propio de cada cuenta",
            limite=("NO existe en ninguna parte del sistema un responsable declarado ni una "
                    "cadencia esperada por cuenta. Se deduce del log, a posteriori"),
            quien_puede_contestar="Tesoreria (BFM/MO) y la oficina de terreno de cada cuenta")

    sin_texto = [f for f in vivas if f["canal"] == "SIN EXTRACTO" and not f["cerrada"]]
    if sin_texto:
        h.desafio(
            "No se puede distinguir 'este banco no manda extracto' de 'se dejo de hacer'",
            tamano="%d cuentas vivas sin extracto y sin declaracion de si les corresponde"
                   % len(sin_texto),
            evidencia="T012K vivas con cero FEBKO; la unica marca de estado es CLOSED en el texto",
            limite=("el formulario de alta YA pregunta '¿extracto electronico? si/no' y esa "
                    "respuesta no se guarda en ninguna parte del sistema"),
            quien_puede_contestar="Tesoreria: declarar por cuenta si se espera extracto y por que canal")

    h.emitir()

'''

anc = "    if a.json:\n        json.dump(filas, open(a.json"
if "LA BUSQUEDA. El censo de arriba" in s:
    print("censo: ya estaba")
elif anc in s:
    s = s.replace(anc, BUSQUEDA + anc, 1)
    io.open(P, "w", encoding="utf-8").write(s)
    import ast
    ast.parse(s)
    print("censo: busqueda cablada · sintaxis OK")
else:
    print("censo: ANCLA NO ENCONTRADA")
