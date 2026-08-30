# -*- coding: utf-8 -*-
"""custom_extension_census_check.py — ¿cada extensión custom que carga el sistema está registrada?

MINERO (clase REALIDAD). Lee el GOLDEN y el repo, nunca P01.

Pregunta falsable: la población de extensiones custom que el sistema DECLARA llevar
(ENHOBJ Z*/Y*, smodilog) ¿está cubierta por el registro maestro
(knowledge/sap_custom_enhancement_registry.md) y por el corpus extraído?

Tres medidas, cada una con su denominador:
  1. Enhancement Framework: ENHNAME Z*/Y* distintos en ENHOBJ vs menciones en el registro
     y presencia en extracted_code/ENHO/. Lo no registrado es código que DECIDE y que
     ningún análisis ve (patrón MV_EXTENSION_YEARS).
  2. Modificaciones al estándar: objetos distintos en smodilog, separando el ruido
     SAP-delivered (claim 211: CLS4SIC_* llega con el SP stack, no es nuestro).
  3. El hueco de inventario CMOD: MODACT/MODSAP no están en el Gold DB — el censo clásico
     de user-exits sólo se conoce por el código que extrajimos, no por el registro del
     propio sistema.

Límite declarado: "mencionado en el registro" es un grep de texto — mide presencia del
nombre, no calidad del análisis. Y ENHOBJ dice qué existe, no qué se EJECUTA.
"""

import os
import re
import sqlite3
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _HERE)
from _hallazgos import Hallazgos  # noqa: E402

GOLD = os.path.join(_REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
REGISTRY = os.path.join(_REPO, "knowledge", "sap_custom_enhancement_registry.md")
AUTOPSIES = os.path.join(_REPO, "knowledge", "domains", "PSM", "EXTENSIONS")
ENHO_DIR = os.path.join(_REPO, "extracted_code", "ENHO")


def _texto_registro():
    partes = []
    for p in [REGISTRY] + sorted(
            os.path.join(AUTOPSIES, f) for f in os.listdir(AUTOPSIES)
            if f.endswith(".md")) if os.path.isdir(AUTOPSIES) else [REGISTRY]:
        try:
            with open(p, encoding="utf-8") as fh:
                partes.append(fh.read().upper())
        except OSError:
            pass
    return "\n".join(partes)


def main():
    db = sqlite3.connect(GOLD)
    corpus = _texto_registro()
    extraidos = set(os.listdir(ENHO_DIR)) if os.path.isdir(ENHO_DIR) else set()

    # --- 1. Enhancement Framework (ENHOBJ Z*/Y*) ---
    enh = [r[0].strip() for r in db.execute(
        "SELECT DISTINCT ENHNAME FROM ENHOBJ "
        "WHERE ENHNAME LIKE 'Z%' OR ENHNAME LIKE 'Y%'")]
    sin_registro = [e for e in enh if e.upper() not in corpus]
    sin_extraer = [e for e in enh if e not in extraidos]

    h = Hallazgos(
        "custom_extension_census_check",
        denominador="%d enhancements Z*/Y* distintos en ENHOBJ (P01) · %d objetos distintos "
                    "en smodilog" % (len(enh), db.execute(
                        "SELECT COUNT(DISTINCT OBJ_NAME) FROM smodilog").fetchone()[0]),
        sistema="P01 (via Gold DB)", ventana="foto ENHOBJ/smodilog en Gold DB")

    if sin_registro:
        h.oportunidad(
            "enhancements custom del Enhancement Framework SIN mención en el registro maestro "
            "ni en las autopsias: son código que decide y que ningún análisis de customizing ve",
            tamano="%d de %d Z*/Y* sin registrar (%.0f%%); ejemplos: %s"
                   % (len(sin_registro), len(enh),
                      100.0 * len(sin_registro) / max(len(enh), 1),
                      ", ".join(sorted(sin_registro)[:8])),
            evidencia="ENHOBJ (Gold DB) vs grep de sap_custom_enhancement_registry.md + "
                      "knowledge/domains/PSM/EXTENSIONS/*.md",
            limite="mencion por grep: mide presencia del nombre, no calidad del análisis; "
                   "y ENHOBJ dice qué existe, no qué se ejecuta",
            accion="triaje por MAIN_TYPE/MAIN_NAME (qué objeto estándar tocan) y autopsia de "
                   "los que cuelguen de puntos de contabilización o pago")
    else:
        h.dato("los %d enhancements Z*/Y* de ENHOBJ están todos mencionados en el registro"
               % len(enh),
               tamano="%d de %d" % (len(enh), len(enh)),
               evidencia="ENHOBJ vs registro + autopsias",
               limite="mención no es análisis",
               accion="nada")

    if sin_extraer:
        h.dato("enhancements Z*/Y* sin fuente en extracted_code/ENHO/",
               tamano="%d de %d sin carpeta de extracción" % (len(sin_extraer), len(enh)),
               evidencia="ENHOBJ vs listado de extracted_code/ENHO/",
               limite="el fuente puede estar en otro corpus (UNESCO_CUSTOM_LOGIC) bajo otro nombre",
               accion="skill sap_enhancement_extraction para los que pesen")

    # --- 2. Modificaciones al estándar ---
    mods = db.execute(
        "SELECT COUNT(DISTINCT OBJ_NAME) FROM smodilog "
        "WHERE OBJ_NAME NOT LIKE 'Y%' AND OBJ_NAME NOT LIKE 'Z%' "
        "AND OBJ_NAME NOT LIKE '/SAPQUERY/%' AND OBJ_NAME NOT LIKE 'CLS4SIC%'").fetchone()[0]
    h.dato("objetos ESTÁNDAR con entrada en el log de modificaciones (smodilog), quitado el "
           "ruido conocido (queries generadas, CLS4SIC del SP stack — claim 211)",
           tamano="%d objetos estándar tocados" % mods,
           evidencia="Gold DB smodilog; split UNESCO-vs-SAP-delivered por patrón de nombre",
           limite="smodilog registra el AJUSTE (SPAU/SPDD), no distingue mod viva de revertida; "
                  "el split por prefijo es aproximado",
           accion="la regla hacia delante es no modificar estándar; esto es inventario, no precedente")

    # --- 3. Censo CMOD (hueco cerrado s111: MODACT/MODSAP/MODATTR extraídas) ---
    tiene_modact = db.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('modact','MODACT')"
    ).fetchone()[0]
    if not tiene_modact:
        h.desafio("el censo de proyectos CMOD no existe en el Gold DB: MODACT/MODSAP sin "
                  "extraer — el inventario clásico de user-exits se conoce sólo por el código "
                  "que extrajimos, no por el registro del propio sistema",
                  tamano="2 tablas ausentes (MODACT, MODSAP); población desconocida",
                  evidencia="sqlite_master del Gold DB",
                  limite="este minero no lee P01; la extracción es un paso previo",
                  accion="python Zagentexecution/sap_data_extraction/scripts/extract_cmod_inventory.py")
    else:
        # MODACT = el cableado real proyecto->enhancement SMOD; MODSAP es el CATÁLOGO
        # SAP de definiciones (10K+ filas, casi todo sin usar) — censar sobre MODSAP
        # inflaría la población, el clásico defecto de denominador.
        proys = {r[0].strip(): (r[1] or "").strip() for r in db.execute(
            "SELECT NAME, GROUP_CONCAT(MEMBER, ', ') FROM modact "
            "WHERE MEMBER<>'' GROUP BY NAME")}
        attrs = {r[0].strip() for r in db.execute("SELECT NAME FROM modattr")}
        sin_wiring = sorted(attrs - set(proys))
        cmod_sin_registro = sorted(p for p in proys if p.upper() not in corpus)
        if cmod_sin_registro:
            h.oportunidad(
                "proyectos CMOD activos (user-exits clásicos cableados a puntos estándar) "
                "sin mención en el registro maestro ni en las autopsias",
                tamano="%d de %d proyectos sin registrar; son: %s"
                       % (len(cmod_sin_registro), len(proys),
                          "; ".join("%s->%s" % (p, proys[p]) for p in cmod_sin_registro)),
                evidencia="MODACT (Gold DB, cableado real) vs grep del registro + autopsias",
                limite="MODACT dice qué está cableado, no cuánto se ejecuta; y la mención "
                       "por grep no mide calidad del análisis",
                accion="autopsia priorizando los que cuelgan de puntos financieros "
                       "(SAPLFMDT/FMRESERV/FEB00001/ACBAPI01)")
        else:
            h.dato("los %d proyectos CMOD con cableado están todos mencionados en el registro"
                   % len(proys),
                   tamano="%d de %d" % (len(proys), len(proys)),
                   evidencia="MODACT vs registro + autopsias",
                   limite="mención no es análisis",
                   accion="nada")
        if sin_wiring:
            h.dato("proyectos CMOD con atributos (MODATTR) pero SIN enhancement cableado en "
                   "MODACT: cáscaras vacías o proyectos a medio montar",
                   tamano="%d: %s" % (len(sin_wiring), ", ".join(sin_wiring)),
                   evidencia="MODATTR vs MODACT (Gold DB)",
                   limite="un proyecto sin members puede haberse vaciado deliberadamente",
                   accion="candidatos a limpieza; verificar antes de tocar")

    h.emitir()
    return 0


if __name__ == "__main__":
    sys.exit(main())
