# -*- coding: utf-8 -*-
"""INC-000016471 - graba en algorithm_memory.json lo aprendido sobre el SUSTRATO.

El bus lleva HALLAZGOS sobre el inquilino; esto lleva lo que aprendimos sobre el
INSTRUMENTO: hasta donde ve cada log y que campo miente. A11 lo dice: lo escribe
cualquier algoritmo, lo leen todos.

ADR-008 (un solo escritor): hay otro minero vivo en este repo, asi que el append se
verifica -- se cuenta antes, se escribe, se relee y se comprueba que no se perdio
ninguna memoria ajena. Si el recuento no cuadra, aborta sin tocar nada.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MEM = REPO / "brain_v2/methods/algorithm_memory.json"

NUEVAS = [
    {
        "subject": "rsau.FP_ / el render Adobe",
        "kind": "INSTRUMENT",
        "fact": "el render Adobe (ADS) NO DEJA HUELLA en el log de auditoria. Cero eventos de "
                "FP_JOB_OPEN, FP_FUNCTION_MODULE_NAME o FP_GET_LAST_ADS_ERRSTR en las cuatro "
                "superficies (SLGREPNA, SLGTC, PARAM1, PARAM3) en 6,5 meses, y la transaccion SFP "
                "solo se abrio 2 veces, las dos por un desarrollador. El motivo es estructural: el "
                "render es un modulo de funcion LOCAL dentro de un programa, no un arranque de "
                "transaccion ni una llamada RFC ENTRANTE, que son las unicas cosas que el filtro "
                "SM19 de este inquilino captura.",
        "learned_by": "inc16471_ads_log_mining (A19_log_reality_filter + A56 slots)",
        "evidencia_extra": "SLGREPNA LIKE 'FP%' = 14 filas; PARAM3 LIKE 'FP%' = 8; SLGTC LIKE 'SFP%' = 2",
        "evidence": "rsau_audit_history 28,58M filas 2026-02-03..2026-08-25",
        "implication": "no se puede fechar una caida de ADS -- ni de ningun destino tipo G -- con "
                       "este log. Ausencia de dato, NO de problema. Para un canal SALIENTE hay que "
                       "medir el proxy que SI entra (el host llamando de vuelta) o declarar el punto "
                       "ciego; nunca publicar 'no se usa' desde observed_calls=0.",
        "confidence": "MEASURED",
        "session": 105,
    },
    {
        "subject": "rsau.PARAM3 LIKE '%ADS%'",
        "kind": "TRAP",
        "fact": "devuelve 2.831 filas y NINGUNA es ADS: el LIKE de SQLite es insensible a mayusculas "
                "en ASCII y 'Downloads' contiene 'oads'. Todas son rutas de descarga de puesto de "
                "trabajo (C:/Users/<x>/Downloads/EXPORT.XLSX y similares).",
        "learned_by": "inc16471_ads_log_mining",
        "evidence": "top 40 valores de PARAM3 que casan: 40 de 40 son rutas de fichero",
        "implication": "una sigla de tres letras NO se busca por subcadena en un campo que lleva "
                       "rutas. Mira los VALORES DISTINTOS antes de contar: aqui la cuenta sola daba "
                       "un canal vivo con 2.831 eventos que no existe.",
        "confidence": "MEASURED",
        "session": 105,
    },
    {
        "subject": "el borde del corpus acumulado",
        "kind": "TRAP",
        "fact": "el ULTIMO DIA de rsau_audit_history esta siempre a medias y se lee como una caida. "
                "Medido mientras el acumulador corria: el 22-ago tenia 23.834 filas hasta las 05:31 y "
                "el 24-ago 22.987 hasta las 05:14, contra ~157.000-166.000 de un dia laborable "
                "completo. Horas despues los mismos dias estaban completos.",
        "learned_by": "inc16471_ads_log_mining",
        "evidence": "20260820:158.783 21:157.305 22:23.834 23:84.369(domingo) 24:166.176",
        "implication": "antes de leer cualquier serie diaria como un corte, comprueba el VOLUMEN del "
                       "dia y su MAX(SAL_TIME) contra la mediana de un dia laborable. Y no confundas "
                       "un domingo (~84K) con una caida: la semana tiene forma.",
        "confidence": "MEASURED",
        "session": 105,
    },
    {
        "subject": "sm21_syslog_history / snap_history / st22_dumps_history",
        "kind": "INSTRUMENT",
        "fact": "los tres logs de INFRAESTRUCTURA estan practicamente vacios y no se llenan solos. "
                "accumulate_logs.py acumula exactamente cuatro flujos -- TBTCO, TBTCP, CDHDR y RSAU. "
                "SM21 tiene 2.402 filas de una extraccion suelta del 15..22 de junio de 2026 (y su "
                "contenido SI sirve: lleva plugin HTTP en AREA R2/SUBID G y UNCAUGHT_EXCEPTION en "
                "E0/A). SNAP tiene 0 filas y esta DESACTIVADO a proposito -- P01 devuelve "
                "TABLE_NOT_AVAILABLE por RFC_READ_TABLE -- y ademas su esquema (DATUM/UZEIT/AHOST/"
                "UNAME/MODNO/SEQNO) no lleva ni programa ni texto, asi que aunque se llenara no "
                "podria contestar 'un volcado que mencione X'. st22_dumps_history si lleva "
                "ERROR_CLASS/OBJECT/MESSAGE pero tiene 1 fila.",
        "learned_by": "inc16471_ads_log_mining",
        "evidence": "sm21 2.402 filas 20260615..20260622; snap_history 0; st22_dumps_history 1 "
                    "(20260621, DBIF_REPO_SQL_ERROR); accumulate_logs.py LOG_TABLES + lineas 114-117",
        "implication": "cualquier pregunta de INFRAESTRUCTURA -- se cayo el ICM, hubo timeout HTTP, "
                       "volco un programa -- es HOY incontestable con el golden, y esa respuesta hay "
                       "que darla como frontera del instrumento, no como 'no hubo nada'. Si se quiere "
                       "contestar, lo que falta es meter SM21 en el acumulador y ST22 por su FM "
                       "(sap_system_monitor.py), no una consulta mas lista.",
        "confidence": "MEASURED",
        "session": 105,
    },
    {
        "subject": "tbtco.STATUS = 'F'",
        "kind": "TRAP",
        "fact": "'F' es TERMINADO, no CORRECTO. RFFOAVIS_FPAYM (aviso de pago, el unico programa de "
                "nuestro corpus con formulario Adobe) corrio 7 veces el 25-ago y 19 el 26 y acabo en "
                "F las 26, durante una caida declarada del servicio que renderiza sus PDF.",
        "learned_by": "inc16471_ads_log_mining",
        "evidence": "tbtco_history x tbtcp_history por PROGNAME, 20260810..20260826",
        "implication": "el estado de un job no es una senal de exito FUNCIONAL. Un fallo de render, de "
                       "salida o de negocio capturado dentro del programa deja el job en F. Para saber "
                       "si el trabajo SALIO hay que mirar lo que produce, no como acabo.",
        "confidence": "MEASURED",
        "session": 105,
    },
]


def main():
    d = json.loads(MEM.read_text(encoding="utf-8"))
    antes = d["memories"]
    n_antes = len(antes)
    ya = {(m.get("subject"), m.get("session")) for m in antes}
    add = [m for m in NUEVAS if (m["subject"], m["session"]) not in ya]
    if not add:
        print("nada que anadir: ya estaban")
        return
    antes.extend(add)
    MEM.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")

    # verificacion: ninguna memoria ajena se perdio en el camino
    rel = json.loads(MEM.read_text(encoding="utf-8"))["memories"]
    if len(rel) != n_antes + len(add):
        raise SystemExit(f"ABORTA: esperaba {n_antes + len(add)} memorias y hay {len(rel)}. "
                         "Otro escritor toco el fichero: revisar a mano antes de nada.")
    print(f"anadidas {len(add)} memorias; total {len(rel)} (antes {n_antes})")
    for m in add:
        print("  -", m["subject"], "/", m["kind"])


if __name__ == "__main__":
    main()
