# -*- coding: utf-8 -*-
"""Registra INC-000013624 como REGISTRO DE PRIMERA CLASE en incidents.json.

Un doc sin registro es invisible para BRAIN LOOKUP: la siguiente sesion que busque
'extracto bancario' o 'NTB02' no lo encuentra. Por eso existe la puerta
incident_record_coverage_check.py.
"""
import json, io, os, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
P = os.path.join(REPO, "brain_v2", "incidents", "incidents.json")
inc = json.load(io.open(P, encoding="utf-8"))

REC = {
    "id": "INC-000013624",
    "status": "ROOT_CAUSE_CONFIRMED_ACTION_PENDING",
    "title": "El extracto bancario electronico de NTB02/EUR01 (Northern Trust ASHI EUR) dejo "
             "de entrar al cambiar el numero de cuenta: T028B se quedo apuntando a la cuenta vieja",
    "reporter": "Ingrid Wettie (BFM/MO) -> Baizid Gazi (BFM/TRS) -> Anssi Yli-Hietanen -> JP Lopez (DBS)",
    "received_date": "2026-08-28",
    "analyzed_session": 108,
    "domain": "Treasury_EBS",
    "secondary_domains": ["Payment_BCM", "Integration", "Master_Data_Governance", "Support"],
    "transactions": ["FI12", "FF67", "FF_5", "OT43", "SE38"],
    "primary_object_id": "T028B",
    "primary_subject": "Banco casa UNES/NTB02-EUR01, cuenta 11939389 -> 18747647, "
                       "cuenta alternativa UNO12EUR -> UNO18EUR, IBAN GB54... -> GB42...",
    "company_codes_involved": ["UNES"],
    "scenario": "house_bank_account_number_change_orphans_ebs_wiring",
    "incident_type": "CONFIGURATION",
    "error_messages": ["(sin mensaje: el extracto simplemente deja de entrar, en silencio)"],
    "root_cause_summary":
        "El cambio pedido (numero de cuenta, IBAN y cuenta alternativa) se hizo COMPLETO y esta "
        "verificado en vivo en P01: T012K UNES/NTB02/EUR01 lleva BANKN=18747647 y BNKN2=UNO18EUR, "
        "y TIBAN lleva GB42CNOR23286318747647 con VALID_FROM=20260817. Lo que NO se actualizo es "
        "T028B (SPRO: asignar cuentas bancarias a tipos de operacion), cuya CLAVE es BANKL+KTONR: "
        "sigue con la fila SP0000000MX7 / 11939389 -> TR_TRNF / NTB02-EUR1, y no existe ninguna "
        "fila para 18747647. Al llegar el fichero, SAP resuelve la cuenta del :25: (FEBKO-ABSND = "
        "'SP0000000MX7   UNO12EUR') contra T012K por BANKN o BNKN2, y con el BANKN resultante "
        "busca T028B para obtener grupo de formato y cuenta interna. Ese segundo salto ya no "
        "encuentra fila y el extracto no se procesa. MEDIDO: ultimo extracto de NTB02/EUR01 el "
        "14.08.2026 (estadillo 2997, importado el 15.08); el cambio se hizo el 17.08; desde "
        "entonces han entrado 1.046 extractos de otros bancos en UNES y CERO de NTB02, mientras "
        "las seis cuentas de NTB01 (mismo Northern Trust) siguen entrando a diario hasta el "
        "27.08. CONTROL: en las 6 cuentas de NTB01 que funcionan, T028B.KTONR coincide "
        "exactamente con T012K.BANKN; en NTB02 ya no. La captura de FF67 que mandan los usuarios "
        "muestra 'Account UNO12EUR' pero eso es FEBKO-ABSND, o sea lo que trajo el ULTIMO fichero "
        "importado -- es historia, no configuracion, y por eso despista.",
    "fix_path":
        "Anadir en D01 y transportar: T028B BANKL=SP0000000MX7, KTONR=18747647, VGTYP=TR_TRNF, "
        "BNKKO=NTB02-EUR1, BUKRS=UNES (resto de campos vacios, como en las 6 filas de NTB01). "
        "Borrar despues la fila 11939389 tras verificar la entrada del primer extracto. Antes de "
        "liberar: python Zagentexecution/quality_checks/config_transport_prerelease_check.py "
        "<TRKORR> -- T028B es tabla de customizing y un transporte de tabla exporta el VALOR al "
        "liberar, con lo que puede arrastrar claves ajenas. NO hay que tocar T035D (su clave es "
        "DISKB, no el numero de cuenta; UNES/NTB02-EUR1 -> 0001095012 existe), ni FEB_IMP_* "
        "(todo generico, claves en blanco), ni TIBAN.",
    "open_question":
        "Falta saber si el fichero LLEGA y SAP lo rechaza, o si Northern Trust / Coupa todavia no "
        "emiten el extracto de UNO18. No hay ningun log de aplicacion FEB* desde el 01.08 y el "
        "listado del share por RFC se colgo. Se cierra en 2 minutos: AL11 sobre "
        "\\\\hq-sapitf\\coupa$\\P01\\Out\\Data\\EBS\\ y \\Out\\Errors\\EBS, buscando ficheros "
        "posteriores al 14.08 para esta cuenta.",
    "related_objects": ["T028B", "T012K", "T035D", "T035U", "TIBAN", "FEBKO", "FEBEP",
                        "FEB_FILE_HANDLING", "FEB_IMP_SOURCE", "FEB_FILEPATH", "NTB02", "NTB01",
                        "EBS INTEGRATION", "EBS JOB_COUPA", "FF67", "FI12"],
    "population_sweep":
        "El barrido de la poblacion entera (368 cuentas T012K de UNES) encontro 3 cuentas MAS con "
        "el mismo cable roto que nadie ha reportado: BTE01-USD01 (T012K 0050070646 vs T028B "
        "342518788/4190205431), SCB01-USD01 (8700220052800 vs 8740320052800/0100220052800) y "
        "BPO01-USD01 (06-1822-H, sin ninguna fila T028B). Ademas 25 filas huerfanas en T028B y 15 "
        "canales mudos entre 13 y 497 dias.",
    "class_generalization":
        "Cambiar el numero de cuenta de un banco casa deja HUERFANA toda configuracion cuya clave "
        "sea ese numero. FI12 actualiza T012K y no arrastra a T028B. El sistema no avisa: la ficha "
        "queda perfecta, el job sigue en verde y el extracto deja de entrar en silencio. El "
        "precedente ya existia y no se cerro: el retro NTB01_rename_2026-04-08.md dejo escrito "
        "'comprobar las entradas de T028B para la clave de banco de NTB01' cuatro meses antes.",
    "analysis_doc": "knowledge/incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md",
    "recurring_check": "Zagentexecution/quality_checks/house_bank_ebs_wiring_check.py",
}

inc = [x for x in inc if x.get("id") != REC["id"]] + [REC]
json.dump(inc, io.open(P, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("incidents.json: %d registros, INC-000013624 escrito" % len(inc))
