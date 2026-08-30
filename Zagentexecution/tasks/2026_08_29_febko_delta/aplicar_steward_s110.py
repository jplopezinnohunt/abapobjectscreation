# -*- coding: utf-8 -*-
"""Aplica lo que el steward verifico y NO pudo escribir por haber otro escritor.

POR QUE EXISTE COMO SCRIPT Y NO SE HIZO A MANO
    El steward corrio, verifico todo contra los ficheros -- no contra mi resumen -- y se NEGO a
    escribir porque `cycle_state.json` estaba en RUNNING y `claims.json` mutando. Eso es ADR-008
    bien aplicado: un solo escritor. Dejar el contenido preparado y aplicarlo de una vez cuando
    el ciclo cierre es mas seguro que ir tocando stores a mano mientras otro proceso escribe.

    Y SE COMPRUEBA OTRA VEZ AL EMPEZAR: que el ciclo siga cerrado. El estado pudo cambiar entre
    que se escribio esto y que se ejecuta.

QUE APLICA
    1. Cuatro claims nuevos, todos TIER_1 verificados contra P01.
    2. La correccion de una cifra vieja en A83 (decia 239/35, la realidad es 251/23).
    3. Un issue de calidad: dos registros dicen cosas distintas de FEBRE y essr.
    4. Dos reglas EXTENDIDAS -- no creadas. El steward comprobo que ya habia familia.
"""

import json
import io
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
os.chdir(REPO)


def cargar(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def guardar(p, d):
    with io.open(p, "w", encoding="utf-8", newline="") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)


def main():
    est = cargar("brain_v2/methods/cycle_state.json").get("status")
    if est == "RUNNING":
        print("EL CICLO SIGUE EN RUNNING -- no se escribe. Un solo escritor (ADR-008).")
        return 3
    print("ciclo: %s -> se puede escribir\n" % est)

    # ---- 1 · CLAIMS ----------------------------------------------------------------
    P = "brain_v2/claims/claims.json"
    doc = cargar(P)
    claims = doc["claims"] if isinstance(doc, dict) and "claims" in doc else doc
    ids = [c.get("id") for c in claims if isinstance(c.get("id"), int)]
    nid = (max(ids) if ids else 0) + 1
    base = {"claim_type": "SYSTEM_FACT", "confidence": "TIER_1", "status": "VERIFIED",
            "created_session": 110, "evidence_against": []}
    nuevos = [
        dict(base, id=nid, domain="Payment_BCM",
             claim=("LAS LINEAS DE NOMINA ENTRAN EN REGUP SIN DOCUMENTO FI: BELNR vacio, "
                    "BUZEI='000' y GJAHR='0000'. La clave estandar de SAP NO las distingue EN "
                    "PRODUCCION, no solo en nuestra copia -- verificado leyendo P01, que devuelve "
                    "las mismas 3 filas colisionando (importes 1310.60/3868.81/0.00, texto "
                    "'Wage/salary 10109087/202508'). Corrige un diagnostico propio anterior que "
                    "atribuia la duplicacion a que REGUP_SCENARIOS fuera una union de escenarios "
                    "inventada por nosotros: el Golden era copia FIEL."),
             evidence_for=[{"type": "production_data",
                            "ref": "P01, RFC_READ_TABLE QUERY_TABLE=REGUP",
                            "cite": "3 filas con la misma clave y distinto importe",
                            "added_session": 110},
                           {"type": "source_code",
                            "ref": "Zagentexecution/quality_checks/gold_delta.py (REGUP_SCENARIOS)",
                            "cite": "clave ampliada con WRBTR+SGTXT: 207.779 filas / 207.779 claves",
                            "added_session": 110}],
             related_objects=["REGUP", "REGUH", "BELNR", "GJAHR"]),
        dict(base, id=nid + 1, domain="BusinessPartner",
             claim=("EL CAMPO UPDAT DE LFA1/LFB1 EXISTE Y ESTA VACIO EN EL 100% DE LAS FILAS "
                    "TAMBIEN EN P01: no es una perdida de nuestra extraccion, SAP no lo mantiene. "
                    "Y ERDAT es fecha de ALTA -- un proveedor creado en 2019 y modificado ayer "
                    "sigue con ERDAT=2019. Los cambios reales solo viven en CDHDR. Cualquier "
                    "delta futuro que asuma UPDAT como campo de cambio fallara EN SILENCIO."),
             evidence_for=[{"type": "production_data",
                            "ref": "P01, LFA1 (321.360 filas) y LFB1 (332.483) con UPDAT <> ceros",
                            "cite": "0 filas en las dos tablas",
                            "added_session": 110}],
             related_objects=["LFA1", "LFB1", "UPDAT", "ERDAT", "CDHDR"]),
        dict(base, id=nid + 2, domain="Data_Quality",
             claim=("NINGUN DELTA NUESTRO VE UN BORRADO FISICO, PERO EL RIESGO ESTA ACOTADO Y "
                    "MEDIDO: 0 tablas Z/Y entre las que tenian delta registrado; 7 llevan marca "
                    "de borrado LOGICO (FMIOI, cooi, LFA1, LFB1, ekpo, ekko, eban) que cualquier "
                    "delta ve como un cambio de valor; las grandes sin marca son append-only por "
                    "naturaleza -- logs y documentos contables, que SAP REVIERTE. Probado donde "
                    "mas se sospechaba: las PROPUESTAS de pago en 2025-01, 2025-06 y 2026-01 dan "
                    "17.236 / 12.285 / 25.142 filas IDENTICAS en Golden y P01."),
             evidence_for=[{"type": "production_data",
                            "ref": "REGUH XVORL='X' por mes, Golden frente a P01",
                            "cite": "tres ventanas, cifras identicas",
                            "added_session": 110}],
             related_objects=["REGUH", "FMIOI", "LFA1", "LFB1", "gold_delta.py"],
             resolution_notes=("corrige un aviso propio del mismo dia, tecnicamente cierto y "
                               "practicamente exagerado. Se comprueba con comparacion de "
                               "POBLACION, no con un delta")),
        dict(base, id=nid + 3, domain="Data_Quality",
             claim=("UN CAMPO DE TEXTO DE SAP PUEDE CONTENER EL CARACTER QUE USAMOS DE "
                    "DELIMITADOR, Y ESO DESPLAZA COLUMNAS EN SILENCIO. Medido: 2 filas de 670.715 "
                    "en BSAS 2024 traen 'tr|_m. Hmedat' en ZUONR. `_rfc_read_single_page` hacia "
                    "split('|') y RELLENABA los huecos que faltaran, asi que la fila seguia "
                    "adelante con todas sus columnas corridas y sin error. Se corrige cortando "
                    "por POSICION: RFC_READ_TABLE devuelve OFFSET y LENGTH en su metadato FIELDS. "
                    "Afecta a los 202 ficheros del repo que parten por delimitador."),
             evidence_for=[{"type": "production_data",
                            "ref": "P01, BSAS BUDAT 2024, BELNR=3100013108",
                            "cite": "ZUONR='tr|_m. Hmedat'; con corte por posicion BUDAT sale "
                                    "'20240508', con split salia '_m. Hmedat'",
                            "added_session": 110},
                           {"type": "source_code",
                            "ref": "Zagentexecution/mcp-backend-server-python/rfc_helpers.py",
                            "cite": "_rfc_read_single_page corta por OFFSET/LENGTH desde s110",
                            "added_session": 110}],
             related_objects=["BSAS", "ZUONR", "rfc_helpers.py", "RFC_READ_TABLE"]),
    ]
    for c in nuevos:
        claims.append(c)
    guardar(P, doc)
    print("claims: +%d (ids %d-%d)" % (len(nuevos), nid, nid + len(nuevos) - 1))

    # ---- 2 · la cifra vieja de A83 -------------------------------------------------
    P = "brain_v2/methods/algorithms.json"
    d = cargar(P)
    a = d["algorithms"].get("A83_derive_keys_from_dd03l")
    if a:
        a["validado"] = ("12 -> 239 -> 251 ejecutables · 35 -> 23 con clave incompleta · 94 sin "
                         "clave en P01. Los 12 que bajaron eran DOS BUGS DEL PROPIO DERIVADOR: "
                         "`.INCLUDE` es un pseudo-campo que hay que resolver por PRECFIELD, y el "
                         "campo de mandante tiene varios nombres (faltaba MANDANT junto a "
                         "MANDT/CLIENT/RCLNT). Probado con YTFI_PPC_STRUC, que nunca se escribio "
                         "a mano: corre en 1 llamada. Corregido en s110.")
        a["_por_que_la_cifra_vieja_seguia_ahi"] = (
            "el commit que arreglo el derivador toco el script y el registro, y NO la ficha del "
            "algoritmo. Una correccion no es un arreglo hasta que barre -- aplicado a mi propia "
            "memoria de instrumentos")
        guardar(P, d)
        print("A83: cifras corregidas (239/35 -> 251/23)")

    # ---- 3 · la incoherencia entre dos registros -----------------------------------
    P = "brain_v2/agi/data_quality_issues.json"
    try:
        d = cargar(P)
        lst = d["issues"] if isinstance(d, dict) and "issues" in d else d
        lst.append({
            "id": "DQ-s110-GOLD-DELTA-ESTRATEGIA-VS-CLAVE",
            "source": "brain_v2/gold_delta_registry.json vs Zagentexecution/quality_checks/gold_delta.py",
            "issue": ("FEBRE y essr llevan estrategia SIN_DELTA_POSIBLE (la escribe "
                      "gold_delta_census.py, que clasifica por NOMBRE de columna) junto a "
                      "ejecutable=true y una clave real (la escribe derive_keys_from_dd03l.py), "
                      "mientras gold_delta.py tiene mecanismos REALES para las dos: FEBRE por "
                      "clave creciente KUKEY, essr por CDHDR clase ENTRYSHEET. Dos escritores del "
                      "mismo fichero que no se leen entre si."),
            "severity": "LOW", "status": "open", "discovered_date": "2026-08-30",
            "impact": ("quien lea solo `estrategia` concluye que no tienen delta posible cuando "
                       "SI se refrescan. No hay perdida de dato: es el registro contradiciendose "
                       "sobre el mismo objeto"),
            "fix_path": ("gold_delta_census.py deberia leer gold_delta.REGISTRO antes de "
                         "clasificar por heuristica de nombre"),
            "affected_count": 2, "domain": "Data_Quality"})
        guardar(P, d)
        print("data_quality: +1 issue (FEBRE/essr)")
    except (OSError, ValueError, KeyError) as e:
        print("data_quality NO aplicado: %s" % str(e)[:60])

    # ---- 4 · dos reglas EXTENDIDAS, no creadas -------------------------------------
    P = "brain_v2/agent_rules/feedback_rules.json"
    d = cargar(P)
    reglas = d["rules"] if isinstance(d, dict) and "rules" in d else d
    it = reglas.values() if isinstance(reglas, dict) else reglas
    tocadas = 0
    for r in it:
        n = r.get("name", "")
        if "estimate_before_extract" in n or "estimate" in n and "extract" in n:
            r["why"] = (r.get("why", "") + " | s110, TERCERA vez el mismo dia: la LECTURA se midio "
                        "rapida (12.223 filas/s) y se confundio con el coste total; el UPDATE "
                        "contra 3.739.106 filas con el join envuelto en IFNULL() no terminaba, y "
                        "EXPLAIN QUERY PLAN mostraba SCAN en vez del indice.")
            r["how_to_apply"] = (r.get("how_to_apply", "") + " | Estima LECTURA y ESCRITURA por "
                                 "separado: una lectura RFC rapida no dice nada del coste local. "
                                 "Antes de un UPDATE/INSERT sobre mas de 100K filas, mira EXPLAIN "
                                 "QUERY PLAN; si no aparece USING ... INDEX, no lo lances.")
            tocadas += 1
        if "guard" in n and ("refuses" in n or "bypass" in n):
            r["why"] = (r.get("why", "") + " | s110, segunda instancia medida: una guarda de "
                        "fechas tomaba por fecha cualquier literal de 8 digitos y bloqueo una "
                        "lectura legitima (LIFNR = '10109087'). Arreglado exigiendo un ano "
                        "plausible (1900-2199). Una guarda con falsos positivos ensena a "
                        "desactivarla.")
            tocadas += 1
    guardar(P, d)
    print("feedback_rules: %d regla(s) EXTENDIDA(s), 0 creadas" % tocadas)
    print("\nlisto. Ahora: python brain_v2/rebuild_all.py --rapido")
    return 0


if __name__ == "__main__":
    sys.exit(main())
