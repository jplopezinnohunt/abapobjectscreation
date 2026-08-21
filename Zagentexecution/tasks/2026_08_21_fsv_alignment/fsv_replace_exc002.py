"""
fsv_replace_exc002.py — REEMPLAZO ATOMICO POR VERSION de la FSV: P01 -> D01 / V01.

⚖️ OPERA BAJO **EXC-002**, autorizada por JP el 2026-08-21. Distinta de EXC-001 y mas agresiva:
   EXC-001 solo INSERTABA filas ausentes. EXC-002 **BORRA la version entera en el destino y la
   vuelve a escribir desde P01**, para que quede IDENTICA.

POR QUE ATOMICO Y NO FILA A FILA
   FAGL_011PC.ID es una CLAVE SUBROGADA y PARENT/CHILD/NEXTN APUNTAN A ELLA. Los ID se asignan por
   contador segun el orden de creacion, asi que el mismo nodo tiene ID distinto en cada sistema.
   - Insertar fila a fila produce un SUPERCONJUNTO: eso fue EXC-001, y dejo FS10 de D01 con 304
     nodos donde P01 tiene 167 (la estructura de 2017 conviviendo con la de 2026).
   - UPDATE fila a fila seria PEOR: escribir el PARENT de P01 en un nodo de D01 lo hace apuntar a
     un ID que alli significa otra cosa.
   Borrando primero, los ID de P01 aterrizan intactos y los punteros quedan autoconsistentes.
   La unidad de alineamiento es la VERSION, no la fila.

QUE JUSTIFICA BORRAR (medido con FAGL_011PC.AEDAT/USNAM)
   No hay tres ramas de trabajo: hay una sola estructura fotografiada en tres momentos, y toda la
   hizo J_LA. D01 = 2017 · V01 = 2024 · P01 = 2026. Las filas "locales" del destino son versiones
   viejas que P01 ya reorganizo, no trabajo de nadie que se pierda.

ALCANCE AUTORIZADO — y nada mas
   tablas   FAGL_011PC · FAGL_011QT · FAGL_011ZC · FAGL_011SC
   VERSIONES **FS10 y FS11 UNICAMENTE**. FS01 y FS02 ya son identicas en los tres sistemas y
            NO SE TOCAN: hay un check que aborta si su recuento cambia.
   destinos D01, V01 · P01 jamas
   autoria  USNAM = JP_LOPEZ y AEDAT = hoy en FAGL_011PC (unica tabla con esos campos).
            Se registra QUIEN alineo y CUANDO, en vez de fingir la autoria de P01.
            EXC-001 dejo esos campos VACIOS por no incluirlos: aqui se corrige.

Uso:
    python fsv_replace_exc002.py                       # dry-run
    python fsv_replace_exc002.py --targets D01 --execute
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

SOURCE = "P01"
KTOPL = "UNES"
ALLOWED_TARGETS = {"D01", "V01"}                       # G1
VERSIONS = ["FS10", "FS11"]                            # alcance EXC-002
UNTOUCHED = ["FS01", "FS02"]                           # deben quedar intactas
USNAM = "JP_LOPEZ"
BATCH = 25

# G4 — lista blanca LITERAL. Orden de INSERCION (referencial). El borrado va al reves.
TABLES = [
    ("FAGL_011PC", ["VERSN", "ID"],
     ["VERSN", "ID", "TYPE", "ERGSL", "PARENT", "CHILD", "NEXTN", "STUFE", "SUMME", "SIGN"],
     ["AEDAT", "USNAM"]),                              # metadatos que SI se rellenan
    ("FAGL_011QT", ["VERSN", "SPRAS", "ERGSL", "TXTYP", "ZEILE"],
     ["VERSN", "SPRAS", "ERGSL", "TXTYP", "ZEILE", "TXT45"], []),
    ("FAGL_011ZC", ["VERSN", "ERGSL", "KTOPL", "VONKT"],
     ["VERSN", "ERGSL", "KTOPL", "VONKT", "BISKT", "XSOLL", "XHABN", "XVERD"], []),
    ("FAGL_011SC", ["VERSN", "ERGSL"],
     ["VERSN", "ERGSL", "SETPR", "SETVS", "SETNR"], []),
]


def parse(res):
    m = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in m} for r in res.get("DATA", [])]


def read(conn, table, cols, versns):
    w = "VERSN IN ( %s )" % ", ".join("'%s'" % v for v in versns)
    if "KTOPL" in cols:
        w += " AND KTOPL = '%s'" % KTOPL
    try:
        return parse(conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                               FIELDS=[{"FIELDNAME": c} for c in cols],
                               OPTIONS=[{"TEXT": w}], ROWCOUNT=0))
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        print("      ERR %s: %s" % (table, str(e)[:110]))
        return None


def count(conn, table, versns):
    r = read(conn, table, ["VERSN"], versns)
    return None if r is None else len(r)


def abap(lines_body):
    return ["REPORT Z_FSV_EXC002."] + lines_body


def abap_delete(table):
    """Borra SOLO las versiones autorizadas. La lista va literal en el codigo, no por parametro."""
    inlist = " OR ".join("versn = '%s'" % v for v in VERSIONS)
    return abap([
        "DATA lv_n TYPE i.",
        "DELETE FROM %s WHERE ( %s )." % (table.lower(), inlist),
        "lv_n = sy-dbcnt.",
        "COMMIT WORK.",
        "WRITE: / 'DEL', lv_n.",
    ])


def abap_insert(table, cols, meta, rows, today):
    out = ["DATA: ls TYPE %s," % table.lower(), "      lv_ok TYPE i,", "      lv_ko TYPE i.", ""]
    for r in rows:
        out.append("CLEAR ls.")
        out.append("ls-mandt = sy-mandt.")
        for c in cols:
            v = (r.get(c) or "").strip()
            if not v:
                continue
            line = "ls-%s = '%s'." % (c.lower(), v.replace("'", "''"))
            if len(line) > 72:
                raise ValueError("linea >72 en %s-%s: %r" % (table, c, v))
            out.append(line)
        if "AEDAT" in meta:
            out.append("ls-aedat = '%s'." % today)
        if "USNAM" in meta:
            out.append("ls-usnam = '%s'." % USNAM)
        out.append("INSERT %s FROM ls." % table.lower())
        out.append("IF sy-subrc = 0. ADD 1 TO lv_ok. ELSE. ADD 1 TO lv_ko. ENDIF.")
        out.append("")
    out += ["COMMIT WORK.", "WRITE: / 'OK', lv_ok, 'KO', lv_ko."]
    return abap(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="D01,V01")
    ap.add_argument("--execute", action="store_true")                       # G7
    a = ap.parse_args()
    targets = [t.strip().upper() for t in a.targets.split(",") if t.strip()]
    bad = [t for t in targets if t not in ALLOWED_TARGETS]                  # G1
    if bad:
        print("ABORTA (G1): destino no autorizado por EXC-002: %s" % bad)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    print("EXC-002 — reemplazo atomico  %s -> %s  ·  versiones %s  ·  modo %s\n"
          % (SOURCE, ", ".join(targets), "+".join(VERSIONS),
             "EJECUTAR" if a.execute else "DRY-RUN"))

    src = get_connection(SOURCE)                                            # G2
    try:
        ref = {t: read(src, t, cols, VERSIONS) for t, _, cols, _ in TABLES}
    finally:
        src.close()
    for t, _, _, _ in TABLES:
        print("  %s %-12s %s" % (SOURCE, t,
                                 "NO LEIBLE" if ref[t] is None else "%d filas" % len(ref[t])))
    if any(v is None for v in ref.values()):
        print("\nABORTA (G2): la referencia no se leyo entera.")
        return 2
    total = sum(len(v) for v in ref.values())
    print("  total a escribir por destino: %d filas" % total)

    rc = 0
    for tgt in targets:
        print("\n" + "=" * 74)
        print("DESTINO %s" % tgt)
        print("=" * 74)
        conn = get_connection(tgt)
        try:
            # --- guardia de versiones intocables, ANTES
            guard_before = {t: count(conn, t, UNTOUCHED) for t, _, _, _ in TABLES}
            print("  intocables %s antes: %s" % ("+".join(UNTOUCHED), guard_before))
            cur = {t: read(conn, t, cols, VERSIONS) for t, _, cols, _ in TABLES}
            for t, _, _, _ in TABLES:
                print("  %-12s en destino %s" % (t, "NO LEIBLE" if cur[t] is None
                                                 else "%d filas" % len(cur[t])))
            if any(v is None for v in cur.values()):
                print("  ABORTA: destino no legible entero."); rc = 1; continue
            if not a.execute:
                for t, _, _, _ in TABLES:
                    print("     %-12s %4d -> %4d" % (t, len(cur[t]), len(ref[t])))
                print("  DRY-RUN: nada escrito.")
                rc = 1
                continue

            snap = os.path.join(HERE, "PRE_EXC002_%s_%s.json" % (tgt, stamp))   # G5
            with open(snap, "w", encoding="utf-8") as fh:
                json.dump({"system": tgt, "versions": VERSIONS, "rows_before": cur},
                          fh, ensure_ascii=False, indent=1)
            print("  PRE -> %s" % os.path.basename(snap))

            # --- BORRADO en orden inverso al referencial.
            # El DELETE por RFC_ABAP_INSTALL_AND_RUN NO es fiable: medido 2026-08-21, a veces no
            # borra nada y no lo dice. Si no se comprueba, los INSERT chocan por clave duplicada y
            # el "reemplazo atomico" se convierte en un no-op silencioso. Se AFIRMA que quedo a 0.
            fallo_delete = False
            for table, _, cols, _ in reversed(TABLES):
                res = conn.call("RFC_ABAP_INSTALL_AND_RUN",
                                PROGRAM=[{"LINE": l[:72]} for l in abap_delete(table)])
                salida = " ".join(w.get("ZEILE", "").strip()
                                  for w in (res.get("WRITES") or []))
                queda = read(conn, table, cols, VERSIONS)
                n = "?" if queda is None else len(queda)
                print("     DEL %-12s %-18s -> quedan %s" % (table, salida, n))
                if queda is None or len(queda) > 0:
                    print("        !!! EL BORRADO NO VACIO LA TABLA. Abortando antes de insertar:")
                    print("            insertar ahora chocaria por clave y dejaria el contenido viejo.")
                    fallo_delete = True
                    break
                time.sleep(0.5)
            if fallo_delete:
                print("  ABORTA: reemplazo no atomico. Estado intacto; PRE en %s"
                      % os.path.basename(snap))
                rc = 1
                continue

            # --- INSERCION en orden referencial
            for table, keys, cols, meta in TABLES:
                rows = ref[table]
                for i in range(0, len(rows), BATCH):
                    res = conn.call("RFC_ABAP_INSTALL_AND_RUN",
                                    PROGRAM=[{"LINE": l[:72]} for l in
                                             abap_insert(table, cols, meta,
                                                         rows[i:i + BATCH], today)])
                    msg = " ".join(w.get("ZEILE", "").strip() for w in (res.get("WRITES") or []))
                    if " KO " in " %s " % msg and not msg.rstrip().endswith("0"):
                        print("       %s lote %d: %s" % (table, i // BATCH, msg[:80]))
                    time.sleep(0.4)
                print("     INS %-12s %d filas" % (table, len(rows)))

            # --- readback: identidad con P01 + versiones intocables sin cambio
            print("\n  --- verificacion ---")
            for table, keys, cols, meta in TABLES:
                post = read(conn, table, cols, VERSIONS)
                if post is None:
                    print("     %-12s POST no legible" % table); rc = 1; continue
                a_ = sorted(tuple(r.get(c, "") for c in cols) for r in ref[table])
                b_ = sorted(tuple(r.get(c, "") for c in cols) for r in post)
                print("     %-12s %s (%d filas)"
                      % (table, "IDENTICA a P01" if a_ == b_ else "!!! DIFIERE", len(post)))
                if a_ != b_:
                    rc = 1
            guard_after = {t: count(conn, t, UNTOUCHED) for t, _, _, _ in TABLES}
            ok_guard = guard_after == guard_before
            print("     intocables %s despues: %s  %s"
                  % ("+".join(UNTOUCHED), guard_after,
                     "OK" if ok_guard else "!!! HAN CAMBIADO"))
            if not ok_guard:
                rc = 1

            led = os.path.join(HERE, "LEDGER_EXC002_%s_%s.json" % (tgt, stamp))   # G9/G10
            with open(led, "w", encoding="utf-8") as fh:
                json.dump({"exception": "EXC-002", "authorized_by": "JP", "date": stamp,
                           "operation": "DELETE version completa + INSERT desde P01",
                           "versions": VERSIONS, "target": tgt, "rows_written": total,
                           "usnam_stamped": USNAM, "aedat_stamped": today,
                           "G10_pendiente": ("registrar en una orden de customizing y validar con "
                                             "config_transport_prerelease_check.py")},
                          fh, ensure_ascii=False, indent=1)
            print("  G9/G10 -> %s" % os.path.basename(led))
        finally:
            conn.close()

    print("\n%s" % ("FSV IDENTICA A P01 en FS10 y FS11" if rc == 0
                    else "REVISA ARRIBA — no se completo"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
