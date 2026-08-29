# -*- coding: utf-8 -*-
"""golden_write_discipline_check.py — quien BORRA en el Golden, y con que justificacion.

LA REGLA (JP, 2026-08-29)
    **Las actualizaciones son DELTA. Borrar debe ser una EXCEPCION**, declarada y con motivo.

POR QUE ES URGENTE
    El Golden son 22,9 GB de procedencia P01, LOCAL-ONLY: no esta en git y hoy no tiene copia
    (`D:` sin conectar). Un `DROP TABLE` o un `DELETE FROM` mal acotado no da error -- deja una
    tabla mas pequena, y el siguiente que la lea publica un numero sobre una poblacion mutilada
    creyendo que es entera. Es el DENOMINADOR INCOMPLETO, pero causado por nosotros y sin vuelta
    atras.

    El caso concreto que lo destapo: `gold_refresh.refresh_pk_upsert` BORRA las claves que estan
    en el Golden y no vienen de la lectura de P01. Curar la spec de FEBKO con un `where` acotado
    al hueco se habria llevado por delante las 13.604 filas de 2024, en silencio.

QUE HACE
    Censa TODA sentencia destructiva contra el Golden en la capa de extraccion y la clasifica:

      DELTA        el fichero no borra: solo INSERT/INSERT OR REPLACE           -> bien
      DECLARADA    borra y lo declara en EXCEPCIONES con su motivo              -> aceptable
      SIN DECLARAR borra y nadie ha dicho por que                               -> FALLA

    No prohibe borrar: hay recargas legitimas (una tabla de configuracion pequena que se
    reconstruye entera). Exige que este DICHO. Lo que no se puede es que un borrado viva
    escondido dentro de un refresco que se llama "refresh".

COMO SE SALDA UNA SIN DECLARAR
    O se convierte en delta (INSERT OR REPLACE por clave, sin DELETE), o se anade a EXCEPCIONES
    con el motivo y el alcance exacto. Anadirla sin motivo es hacer trampa al propio check.

Solo LECTURA. No toca el Golden ni SAP.
"""

QUALITY_CHECK = {
    "tier": "repo",
    "sobre": "scripts/extraction + Zagentexecution/sap_data_extraction",
    "needs": "nada",
    "what": "quien borra en el Golden y con que justificacion: delta / excepcion declarada / "
            "sin declarar",
    "args": "[--todo]",
}

import argparse
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DIRS = ["scripts/extraction", "Zagentexecution/sap_data_extraction/scripts"]
DESTRUCTIVO = re.compile(r"\b(DROP\s+TABLE|DELETE\s+FROM|TRUNCATE)\b", re.I)

# Cada excepcion lleva MOTIVO y ALCANCE. Una entrada sin motivo es hacer trampa al check.
EXCEPCIONES = {
    "gold_refresh.py": (
        "pk-upsert y value-compare borran POR DISENO para reflejar bajas reales en SAP. "
        "PELIGRO MEDIDO: con un `where` acotado, todo lo que quede fuera se ve como baja. "
        "Solo es seguro si el `where` cubre TODO el alcance de la tabla destino."),
    "purge_simulation_runs.py": (
        "su trabajo ES purgar: limpia corridas de simulacion, que son desechables por "
        "definicion y no son procedencia P01."),
    "split_golden_by_system.py": (
        "reparte el Golden por sistema; el DROP es sobre la BD DESTINO recien creada, no "
        "sobre el Golden de origen."),
}


OBJ = re.compile(r"\b(?:DROP\s+TABLE(?:\s+IF\s+EXISTS)?|DELETE\s+FROM|TRUNCATE(?:\s+TABLE)?)\s+"
                 r"[\"'\[]?\{?([A-Za-z_][A-Za-z0-9_]*)", re.I)


def objeto(linea):
    """El nombre de la tabla que se borra. Si va en una f-string (`{gold}`), sale el NOMBRE DE
    LA VARIABLE -- y eso ya distingue un temporal literal de una tabla parametrizada."""
    m = OBJ.search(linea)
    return m.group(1) if m else None


def es_temporal(obj, fuente):
    """Una tabla que el propio fichero CREA es suya: tirarla no borra dato de procedencia P01.

    Sin esto el censo mete `DROP TABLE _dorigin_dedup` en el mismo saco que `DELETE FROM proj`,
    y publica un numero que invita a arreglar ficheros que no tienen nada roto."""
    if obj.startswith("_") or "tmp" in obj.lower() or "temp" in obj.lower():
        return True
    return bool(re.search(r"CREATE\s+(TEMP\w*\s+)?TABLE\s+(IF\s+NOT\s+EXISTS\s+)?"
                          r"[\"'\[]?%s\b" % re.escape(obj), fuente, re.I))


def acotado(linea):
    """Un DELETE con WHERE parametrizado es el IDIOMA DEL DELTA -- recargar un periodo o una
    particion -- no un borrado total. `DELETE FROM x` a secas y `DROP TABLE` si lo son."""
    if re.search(r"\bDROP\s+TABLE\b|\bTRUNCATE\b", linea, re.I):
        return False
    return bool(re.search(r"\bWHERE\b", linea, re.I))


def ficheros():
    for d in DIRS:
        base = os.path.join(REPO, d)
        if not os.path.isdir(base):
            continue
        for f in sorted(os.listdir(base)):
            if f.endswith(".py"):
                yield d, f, os.path.join(base, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--todo", action="store_true", help="lista tambien los ficheros limpios")
    a = ap.parse_args()

    delta, declaradas, sin_declarar = [], [], []
    for d, f, p in ficheros():
        try:
            with open(p, encoding="utf-8") as fh:
                lineas = fh.readlines()
        except (OSError, UnicodeDecodeError):
            continue
        fuente = "".join(lineas)
        hits = []
        for i, l in enumerate(lineas, 1):
            s = l.strip()
            # una mencion en un comentario o docstring no borra nada
            if s.startswith("#") or DESTRUCTIVO.search(l) is None:
                continue
            if "execute" not in l and "db_queue" not in l:
                continue
            # ⛔ DISCRIMINAR, no contar. La primera version metia en el mismo saco un DROP de
            # tabla temporal y un borrado de dato de procedencia P01, y publicaba "29 sin
            # declarar". Ese numero invita a lo peor: arreglar 29 ficheros de golpe, o meterlos
            # en la lista blanca para ver verde. Contar la FORMA en vez del EFECTO.
            obj = objeto(l)
            if obj and es_temporal(obj, fuente):
                continue                       # tabla que el propio fichero crea y tira
            hits.append((i, s[:96], "ACOTADO" if acotado(l) else "TOTAL", obj or "?"))
        hits = [h for h in hits if h[2] == "TOTAL"]   # un borrado ACOTADO es el idioma del delta
        if not hits:
            delta.append((d, f))
        elif f in EXCEPCIONES:
            declaradas.append((d, f, hits))
        else:
            sin_declarar.append((d, f, hits))

    print("=" * 98)
    print("QUIEN BORRA EN EL GOLDEN — las actualizaciones son DELTA, borrar es la EXCEPCION")
    print("=" * 98)
    n = len(delta) + len(declaradas) + len(sin_declarar)
    print("  %d ficheros de extraccion · %d no borran · %d borran declarandolo · %d SIN DECLARAR"
          % (n, len(delta), len(declaradas), len(sin_declarar)))

    print("\n  EXCEPCIONES DECLARADAS (%d)" % len(declaradas))
    for d, f, hits in declaradas:
        print("    %-42s %d sentencia(s)" % (f, len(hits)))
        print("        motivo: %s" % EXCEPCIONES[f])

    print("\n  SIN DECLARAR (%d) — borran y nadie ha dicho por que" % len(sin_declarar))
    for d, f, hits in sorted(sin_declarar, key=lambda x: -len(x[2])):
        print("    %-42s %d sentencia(s)  %s" % (f, len(hits), d))
        for h in hits[:3]:
            print("        :%-5d [%s] %s" % (h[0], h[2], h[1]))
        if len(hits) > 3:
            print("        ... y %d mas" % (len(hits) - 3))

    if a.todo:
        print("\n  SOLO DELTA (%d)" % len(delta))
        for d, f in delta:
            print("    %s" % f)

    if sin_declarar:
        print("\n" + "-" * 98)
        print("FAIL — %d fichero(s) borran en el Golden sin declarar por que." % len(sin_declarar))
        print("  Se salda de UNA de estas dos formas, nunca de una tercera:")
        print("   (a) convertirlo en DELTA: INSERT OR REPLACE por clave, sin DELETE; o")
        print("   (b) anadirlo a EXCEPCIONES con su motivo y su ALCANCE exacto.")
        print("  Anadirlo sin motivo es hacer trampa al propio check.")
        print("\n  Y pesa mas de lo normal: el Golden son 22,9 GB local-only, fuera de git, y")
        print("  hoy sin copia. Un borrado mal acotado no da error: da una tabla mas pequena.")
        return 1
    print("\nOK — nadie borra en el Golden sin declararlo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
