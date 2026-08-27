"""
fsv_align_exc001.py — alinea la VERSION DE BALANCE (FSV) de P01 hacia D01 / V01.

⚖️ OPERA BAJO **EXC-001**, la unica excepcion de escritura directa autorizada.
   Registro: .claude/skills/sap_master_data_sync/SKILL.md -> "REGISTRO DE EXCEPCIONES AUTORIZADAS".
   Alcance autorizado por JP el 2026-08-20: FAGL_011PC / FAGL_011QT / FAGL_011ZC / FAGL_011SC,
   chart UNES, destinos D01 y V01, **SOLO INSERT de filas ausentes**.

   Por que hace falta excepcion: se pregunto a TFDIR y NO EXISTE ningun FM remote-enabled para
   mantener la FSV. El peldano 2 (BC-Sets) exige crear el BC-Set a mano, que no es RFC. Queda el
   peldano 3, prohibido por defecto y aqui autorizado nominalmente.

LAS DIEZ PUERTAS — en el codigo, no en la intencion
   G1  destino en {D01, V01}; P01 rechazado por nombre
   G2  origen = P01 leido EN VIVO (nunca el Gold DB: su cache va meses por detras)
   G3  SOLO INSERT de filas ausentes; jamas UPDATE ni DELETE de filas existentes
   G4  lista blanca de tablas LITERAL; no hay parametro de tabla libre
   G5  snapshot PRE a fichero + readback POST clave a clave
   G6  orden referencial forzado: PC -> QT -> ZC -> SC
   G7  dry-run por defecto; --execute para escribir
   G8  tope de filas y aborto si la clave ya existe en destino
   G9  registro auditable de la invocacion
   G10 declarar las claves escritas para registrarlas despues en una orden de customizing
       y validarla con config_transport_prerelease_check.py

Uso:
    python fsv_align_exc001.py                      # dry-run D01 y V01
    python fsv_align_exc001.py --targets D01 --execute
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
ALLOWED_TARGETS = {"D01", "V01"}                                    # G1
MAX_ROWS_PER_TABLE = 600                                            # G8
BATCH = 12

# G4 — lista blanca LITERAL. Orden = G6 (referencial: posiciones y textos antes que asignaciones).
TABLES = [
    ("FAGL_011PC", ["VERSN", "ID"],
     ["VERSN", "ID", "TYPE", "ERGSL", "PARENT", "CHILD", "NEXTN", "STUFE", "SUMME", "SIGN"]),
    ("FAGL_011QT", ["VERSN", "SPRAS", "ERGSL", "TXTYP", "ZEILE"],
     ["VERSN", "SPRAS", "ERGSL", "TXTYP", "ZEILE", "TXT45"]),
    ("FAGL_011ZC", ["VERSN", "ERGSL", "KTOPL", "VONKT"],
     ["VERSN", "ERGSL", "KTOPL", "VONKT", "BISKT", "XSOLL", "XHABN", "XVERD"]),
    ("FAGL_011SC", ["VERSN", "ERGSL"],
     ["VERSN", "ERGSL", "SETPR", "SETVS", "SETNR"]),
]


def parse(res):
    m = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in m} for r in res.get("DATA", [])]


def read(conn, table, cols):
    where = "KTOPL = '%s'" % KTOPL if "KTOPL" in cols else ""
    try:
        return parse(conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                               FIELDS=[{"FIELDNAME": c} for c in cols],
                               OPTIONS=([{"TEXT": where}] if where else []), ROWCOUNT=0))
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        print("      ERR %s: %s" % (table, str(e)[:100]))
        return None                       # None = no pudimos VER, distinto de vacio


def abap_insert(table, cols, rows):
    """INSERT directo. <=72 chars por linea: RFC_ABAP_INSTALL_AND_RUN trunca EN SILENCIO."""
    out = ["REPORT Z_FSV_EXC001.",
           "DATA: ls TYPE %s," % table.lower(),
           "      lv_ok TYPE i,",
           "      lv_ko TYPE i.",
           ""]
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
        out.append("INSERT %s FROM ls." % table.lower())
        out.append("IF sy-subrc = 0. ADD 1 TO lv_ok. ELSE. ADD 1 TO lv_ko. ENDIF.")
        out.append("")
    out += ["COMMIT WORK.", "WRITE: / 'OK', lv_ok, 'KO', lv_ko."]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="D01,V01")
    ap.add_argument("--execute", action="store_true")                # G7
    a = ap.parse_args()
    targets = [t.strip().upper() for t in a.targets.split(",") if t.strip()]
    bad = [t for t in targets if t not in ALLOWED_TARGETS]           # G1
    if bad:
        print("ABORTA (G1): destino no autorizado por EXC-001: %s. Solo %s."
              % (bad, sorted(ALLOWED_TARGETS)))
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print("EXC-001 — FSV  %s -> %s   modo %s\n"
          % (SOURCE, ", ".join(targets), "EJECUTAR" if a.execute else "DRY-RUN"))

    src = get_connection(SOURCE)                                     # G2
    try:
        ref = {t: read(src, t, cols) for t, _, cols in TABLES}
    finally:
        src.close()
    for t, _, _ in TABLES:
        print("  %s %-12s %s" % (SOURCE, t,
                                 "NO LEIBLE" if ref[t] is None else "%d filas" % len(ref[t])))
    if any(v is None for v in ref.values()):
        print("\nABORTA (G2): la referencia no se pudo leer entera.")
        return 2

    rc, ledger, pendientes = 0, {}, 0
    for tgt in targets:
        print("\n" + "=" * 74)
        print("DESTINO %s" % tgt)
        print("=" * 74)
        conn = get_connection(tgt)
        written = []
        try:
            for table, keys, cols in TABLES:                          # G6 orden referencial
                cur = read(conn, table, cols)
                if cur is None:
                    print("  %-12s NO LEIBLE en destino — se salta" % table)
                    rc = 1
                    continue
                have = {tuple(r.get(k, "") for k in keys) for r in cur}
                todo = [r for r in ref[table]
                        if tuple(r.get(k, "") for k in keys) not in have]   # G3 solo ausentes
                print("  %-12s en destino %-5d · faltan %-4d" % (table, len(cur), len(todo)))
                if not todo:
                    continue
                if len(todo) > MAX_ROWS_PER_TABLE:                    # G8
                    print("     ABORTA (G8): %d filas supera el tope de %d"
                          % (len(todo), MAX_ROWS_PER_TABLE))
                    rc = 1
                    continue
                if not a.execute:
                    pendientes += len(todo)
                    for r in todo[:4]:
                        print("       + %s" % {k: r.get(k) for k in keys})
                    continue

                snap = os.path.join(HERE, "PRE_%s_%s_%s.json" % (tgt, table, stamp))  # G5
                with open(snap, "w", encoding="utf-8") as fh:
                    json.dump({"system": tgt, "table": table, "keys": keys,
                               "rows_before": cur}, fh, ensure_ascii=False, indent=1)
                print("     PRE -> %s (%d filas)" % (os.path.basename(snap), len(cur)))

                ok = True
                for i in range(0, len(todo), BATCH):
                    chunk = todo[i:i + BATCH]
                    try:
                        res = conn.call("RFC_ABAP_INSTALL_AND_RUN",
                                        PROGRAM=[{"LINE": l[:72]}
                                                 for l in abap_insert(table, cols, chunk)])
                        msg = " ".join(w.get("ZEILE", "").strip()
                                       for w in (res.get("WRITES") or []))
                        if "KO" in msg and not msg.rstrip().endswith("0"):
                            print("       lote %d: %s" % (i // BATCH, msg[:90]))
                    except Exception as e:
                        print("       lote %d ERROR: %s" % (i // BATCH, str(e)[:120]))
                        ok = False
                        break
                    time.sleep(1.0)

                post = read(conn, table, cols)                        # G5 readback
                if post is None:
                    print("     POST no legible"); rc = 1; continue
                still = [r for r in ref[table]
                         if tuple(r.get(k, "") for k in keys)
                         not in {tuple(x.get(k, "") for k in keys) for x in post}]
                if still:
                    print("     !!! POST: siguen faltando %d filas" % len(still))
                    rc = 1
                else:
                    print("     VERIFICADA: 0 filas de %s sin replicar (%d -> %d)"
                          % (SOURCE, len(cur), len(post)))
                    written += [(table, tuple(r.get(k, "") for k in keys)) for r in todo]
                if not ok:
                    rc = 1
        finally:
            conn.close()

        if written:                                                   # G9 + G10
            led = os.path.join(HERE, "LEDGER_%s_%s.json" % (tgt, stamp))
            with open(led, "w", encoding="utf-8") as fh:
                json.dump({"exception": "EXC-001", "authorized_by": "JP", "date": stamp,
                           "source": SOURCE, "target": tgt, "operation": "INSERT filas ausentes",
                           "keys_written": [{"table": t, "key": list(k)} for t, k in written],
                           "G10_pendiente": ("registrar estas claves en una orden de customizing "
                                             "(SE01 -> R3TR TABU <tabla> + claves) y validar con "
                                             "config_transport_prerelease_check.py")},
                          fh, ensure_ascii=False, indent=1)
            ledger[tgt] = led
            print("\n  G9/G10 -> %s (%d claves escritas)" % (os.path.basename(led), len(written)))

    # Un dry-run con filas pendientes NO esta alineado: decirlo, o el instrumento miente.
    if rc == 0 and pendientes:
        print("\nDRY-RUN: %d filas PENDIENTES de insertar. Nada escrito." % pendientes)
        rc = 1
    else:
        print("\n%s" % ("FSV ALINEADA" if rc == 0 else "HUBO PROBLEMAS — revisa arriba"))
    if ledger:
        print("PENDIENTE G10: registrar las claves de %s en una orden de customizing."
              % ", ".join(ledger))
    return rc


if __name__ == "__main__":
    sys.exit(main())
