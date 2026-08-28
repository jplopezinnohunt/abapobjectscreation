# -*- coding: utf-8 -*-
"""Registra los 6 instrumentos de s108 en algorithms.json y los engancha al modelo de banca
que YA existia (house_bank_roles.json / bank_model_explorer.py), en vez de dejarlos al lado.

Se hace esto porque no hacerlo es el modo de fallo EL HUERFANO PROPIO de braintoolbox:
crear un instrumento y no declararlo. Se cometio seis veces en una sola sesion.
"""
import json, io, os, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

P = "brain_v2/methods/algorithms.json"
d = json.load(io.open(P, encoding="utf-8"))

BASE = {
    "origin": "OURS",
    "state": "WORKS",
    "generaliza": True,
    "_session": 108,
    "_nace_de": "INC-000013624 — el extracto de NTB02/EUR01 dejo de entrar al cambiar el numero de cuenta",
    "_eje": ("COMPLEMENTA a house_bank_roles.json / bank_model_explorer.py (A44). Aquel modela el "
             "papel de PAGO del BANCO (rol, corredores, metodos, DMEE, PPC); estos modelan el perfil "
             "de TENENCIA y COBRO de la CUENTA (canal de extracto, formato, naturaleza, "
             "comportamiento). Antes de usar cualquiera de los dos: correr load_domain.py sobre el "
             "tema. En s108 no se hizo y se re-derivo el job FEB_FILE_HANDLING, que el explorador "
             "ya publicaba como channel_jobs STABLE."),
}

NUEVOS = {
    "D1_house_bank_ebs_wiring": dict(BASE, **{
        "operates_on": "T012K + T028B + T035D + FEBKO + T012T. Store: salida por consola, exit 1 si hay grave.",
        "mining_kind": "CONFORMIDAD",
        "tipo_mineria": ["CONFORMIDAD"],
        "does": ("comprobar que cada cuenta de banco casa sigue CABLEADA al extracto electronico: "
                 "T028B tiene una fila con su numero de cuenta ACTUAL, no hay filas huerfanas de "
                 "numeros que ya no existen, y su canal sigue vivo frente a su propio ritmo."),
        "bound_in": ["Zagentexecution/quality_checks/house_bank_ebs_wiring_check.py"],
        "failure_mode": (
            "TRES denominadores que si no se declaran producen hallazgos falsos, y los tres se "
            "cometieron antes de encontrarlos: (1) las cuentas CERRADAS se marcan EN EL TEXTO "
            "(T012T-TEXT1 empieza por CLOSED, 237 de 411 en UNES) y sin ese corte 2 de los 4 "
            "primeros hallazgos eran cuentas cerradas hace anos; (2) solo se le exige fila de T028B "
            "a la cuenta cuyo extracto es ELECTRONICO (EFART='E'): BTE01-USD01 importo 116 extractos "
            "MANUALES sin esa fila jamas, y exigirsela publicaba un defecto inexistente; (3) FEBKO "
            "tiene fechas en los anos 2201/2203/2207/2208 -- un 2022 mal tecleado -- que envenenan "
            "cualquier max() de 'ultimo extracto' y hacian aparecer 147 cuentas como muertas."),
    }),
    "D2_bank_statement_channel_census": dict(BASE, **{
        "operates_on": "FEBKO.EFART + T012K + T012T + T028B. Salida por consola y --json.",
        "mining_kind": "CANAL_Y_ACTOR",
        "tipo_mineria": ["CANAL_Y_ACTOR", "DERIVA"],
        "does": ("censar POR QUE CANAL entra el extracto de cada cuenta -- electronico, manual "
                 "(tecleado en FF67), mixto o ninguno -- con su cadencia real y quien lo hace, "
                 "partido SIEMPRE por sociedad."),
        "bound_in": ["Zagentexecution/quality_checks/bank_statement_channel_census.py"],
        "failure_mode": (
            "AGREGAR SOCIEDADES. La MISMA cuenta se comporta al reves segun la sociedad: "
            "CBE01-ETB02 recibe 543 extractos al ano en ICBA y CERO en UNES, y en un total "
            "agregado figura como activa. Ademas el silencio solo significa algo contra el RITMO "
            "PROPIO de la cuenta: 30 dias es alarma en una diaria y rutina en una mensual."),
    }),
    "D3_bank_account_nature_model": dict(BASE, **{
        "operates_on": "T012T (texto) + SETLEAF YBANK + FEBKO + T012K. Salida --json.",
        "mining_kind": "REALIDAD",
        "tipo_mineria": ["REALIDAD", "RESTO_SIN_EXPLICAR"],
        "does": ("derivar la NATURALEZA de cada cuenta (operativa / transferencia / a la vista / "
                 "mandato de inversion) en tres niveles sociedad -> banco -> cuenta, marcando de "
                 "que GRADO de evidencia sale cada fila: CONFIG (un set del sistema), TEXTO (el "
                 "nombre que alguien escribio) o NINGUNA."),
        "bound_in": ["Zagentexecution/quality_checks/bank_account_nature_model.py"],
        "failure_mode": (
            "TOMAR EL TEXTO POR UN DATO. ASHI y PFF parecen marcadores de inversion y NO lo son: "
            "son fondos cuyas cuentas de efectivo reciben extracto diario, y meterlos en la lista "
            "clasifica como inversion cuatro cuentas operativas, incluida la del incidente. Los "
            "marcadores fiables son nombres de gestora o programa (MANDATE, PIMCO, MORGAN, RAMP, "
            "IMIP). Y segundo: mirar solo el texto ignora que 102 de las 119 'sin clasificar' YA "
            "estaban declaradas como terreno por su set YBANK_ACCOUNTS_FO_*."),
    }),
    "D4_bank_config_profile_by_nature": dict(BASE, **{
        "operates_on": "T028B + T035D + TIBAN + T042I + T030H + FAGL_011ZC + SETLEAF. Salida --json.",
        "mining_kind": "CONFORMIDAD",
        "tipo_mineria": ["CONFORMIDAD"],
        "does": ("medir que configuracion lleva DE HECHO cada naturaleza de cuenta, para poder "
                 "derivar el alcance del alta de la NATURALEZA en vez de sacarlo de casillas de un "
                 "formulario. Marca con * los grupos donde las cuentas NO coinciden: o es una regla "
                 "que nadie escribio, o es deriva."),
        "bound_in": ["Zagentexecution/quality_checks/bank_config_profile_by_nature.py"],
        "failure_mode": (
            "LEER UNA TABLA POR UN CAMPO QUE NO TIENE. T030H no tiene KONKO: su campo de cuenta es "
            "HKONT. Con el campo equivocado la lectura NO falla -- devuelve cero filas -- y el "
            "perfil publicaba 'OBA1 = 0% en TODAS las naturalezas', que es una respuesta segura y "
            "falsa. Verificar contra el diccionario antes de publicar un cero uniforme."),
    }),
    "D5_bank_account_behaviour_signature": dict(BASE, **{
        "operates_on": "REGUH + FEBKO + GLT0 (HSL01..16). Salida --json. Tiene --autotest.",
        "mining_kind": "REALIDAD",
        "tipo_mineria": ["REALIDAD", "DERIVA"],
        "does": ("clasificar cada cuenta por lo que HACE y no por como se llama: paga (REGUH), "
                 "recibe extracto (FEBKO/EFART), mueve saldo (GLT0, periodos con movimiento). El "
                 "desacuerdo entre el comportamiento y la etiqueta del texto es en si un hallazgo."),
        "bound_in": ["Zagentexecution/quality_checks/bank_account_behaviour_signature.py"],
        "failure_mode": (
            "AGREGAR GLT0 SOLO POR RACCT. El mismo numero de mayor existe en varias sociedades y se "
            "suma el movimiento de una a la otra: la clave es SOCIEDAD + mayor. Y las 16 columnas "
            "HSL no caben en una lectura de RFC_READ_TABLE (buffer de 512): se leen por trozos y se "
            "juntan por la CLAVE, nunca por posicion."),
        "_solapa_con": ("bank_model_findings.receiving_accounts del explorador A44, que ya publicaba "
                        "'16 cuentas con extracto y CERO pagos'. Reconciliar antes de publicar "
                        "cifras nuevas sobre lo mismo."),
    }),
    "D6_ebs_format_consolidation": dict(BASE, **{
        "operates_on": "T028B.VGTYP + T028G (juego de reglas por formato) + FEBKO. Salida --json.",
        "mining_kind": "CONFORMIDAD",
        "tipo_mineria": ["CONFORMIDAD", "RESTO_SIN_EXPLICAR"],
        "does": ("contar cuantos MODELOS de extracto se sostienen, cuantos bancos y cuentas cubre "
                 "cada uno, cuantas reglas cuesta, y -- la pregunta util -- para un formato dado, "
                 "que bancos lo procesan electronicamente y cuales no teniendolo asignado igual."),
        "bound_in": ["Zagentexecution/quality_checks/ebs_format_consolidation.py"],
        "failure_mode": (
            "MEDIR EL PARECIDO POR LA TUPLA EXACTA Y CONCLUIR QUE NO SE PARECEN. El Jaccard sobre "
            "(codigo externo, regla, algoritmo) da 0% entre XRT940 y SCB19_IQ, y de ahi se publico "
            "'la consolidacion facil no existe'. Mirando la FORMA, SCB19_IQ y CIT24_GA son SUBC/SUBD "
            "8+8, la MISMA estructura que XRT940: difieren en los codigos y en el algoritmo (001 vs "
            "015). La metrica medía lo que no era. Y al reves: CIT04_US (algoritmo 019, ficheros "
            "DME) y SOG_EUR4 (reglas 201I/O de cliente) son legitimamente distintos -- absorberlos "
            "destruiria automatizacion en vez de ganarla."),
    }),
}

for k, v in NUEVOS.items():
    d[k] = v
json.dump(d, io.open(P, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("algorithms.json: %d entradas (+%d de s108)" % (len(d), len(NUEVOS)))
