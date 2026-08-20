"""
mmf_gl_sync.py — copia GL master de P01 (referencia) a D01 / V01.

Caso: formularios AM 3-11 para GL 4041018 (MMF EUR BNP PB) y 4041019 (MMF USD BNP PB),
creadas por MP_BOUA en UNES/P01 el 2026-07-27 y ausentes en D01 y V01.

Direccion: SIEMPRE P01 -> no productivo. P01 es FUENTE, read-only. Nunca se escribe P01.
Patron: el probado en sap_master_data_sync (2026-04-03, 880 registros, gap 0) —
        extraer LIVE -> comparar por clave -> INSERT via RFC_ABAP_INSTALL_AND_RUN -> releer y
        verificar campo a campo. BAPI_GL_ACCOUNT_CREATE no existe en este sistema y
        GL_ACCT_MASTER_MAINTAIN_RFC falla (necesita memoria de sesion FS00).

Tablas y claves:
    SKA1  KTOPL + SAKNR            (18 campos, 125 b)
    SKAT  SPRAS + KTOPL + SAKNR    ( 7 campos, 113 b)
    SKB1  BUKRS + SAKNR            (42 campos, 223 b)
Los tres caben enteros en el buffer de 512 b de RFC_READ_TABLE: no hace falta field-split.

Uso:
    python mmf_gl_sync.py                                  # dry-run, D01+V01, las 2 del ticket
    python mmf_gl_sync.py --systems D01,V01 --execute
    python mmf_gl_sync.py --systems V01 --accounts 4041015,4041016,4041018,4041019 --execute
"""
import argparse
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

KTOPL = "UNES"
SOURCE = "P01"

# Orden EXACTO de campos por tabla (DD03L, AS4LOCAL='A', sin campos '.INCLUDE').
FIELDS = {
    "SKA1": ["MANDT", "KTOPL", "SAKNR", "XBILK", "SAKAN", "BILKT", "ERDAT", "ERNAM", "GVTYP",
             "KTOKS", "MUSTR", "VBUND", "XLOEV", "XSPEA", "XSPEB", "XSPEP", "MCOD1", "FUNC_AREA"],
    "SKAT": ["MANDT", "SPRAS", "KTOPL", "SAKNR", "TXT20", "TXT50", "MCOD1"],
    "SKB1": ["MANDT", "BUKRS", "SAKNR", "BEGRU", "BUSAB", "DATLZ", "ERDAT", "ERNAM", "FDGRV",
             "FDLEV", "FIPLS", "FSTAG", "HBKID", "HKTID", "KDFSL", "MITKZ", "MWSKZ", "STEXT",
             "VZSKZ", "WAERS", "WMETH", "XGKON", "XINTB", "XKRES", "XLOEB", "XNKON", "XOPVW",
             "XSPEB", "ZINDT", "ZINRT", "ZUAWA", "ALTKT", "XMITK", "RECID", "FIPOS", "XMWNO",
             "XSALH", "BEWGP", "INFKY", "TOGRU", "XLGCLR", "MCAKEY"],
}
KEYS = {"SKA1": ["KTOPL", "SAKNR"], "SKAT": ["SPRAS", "KTOPL", "SAKNR"], "SKB1": ["BUKRS", "SAKNR"]}
# MANDT y la metadata de creacion NO se copian: se ponen en destino.
SKIP_ON_INSERT = {"MANDT", "ERDAT", "ERNAM"}


def pad(a):
    a = a.strip()
    return a if len(a) == 10 else a.zfill(10)


def parse(res):
    meta = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in meta} for r in res.get("DATA", [])]


def read(conn, table, where):
    """ROWCOUNT=0, sin ROWSKIPS (el wrapper de P01 los rechaza).
    TABLE_WITHOUT_DATA = cero filas, no un fallo."""
    try:
        res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                        FIELDS=[{"FIELDNAME": f} for f in FIELDS[table]],
                        OPTIONS=[{"TEXT": where}], ROWCOUNT=0)
        return parse(res)
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        raise


def key_of(table, row):
    return tuple(row.get(k, "") for k in KEYS[table])


def build_abap(table, rows):
    """INSERT directo. Lineas <= 72 caracteres: RFC_ABAP_INSTALL_AND_RUN trunca EN SILENCIO."""
    out = ["REPORT Z_MMF_GL_SYNC.",
           "DATA: ls TYPE %s," % table.lower(),
           "      lv_ok TYPE i,",
           "      lv_ko TYPE i.",
           ""]
    for r in rows:
        out.append("CLEAR ls.")
        out.append("ls-mandt = sy-mandt.")
        for f in FIELDS[table]:
            if f in SKIP_ON_INSERT:
                continue
            v = (r.get(f) or "").strip()
            if not v:
                continue
            line = "ls-%s = '%s'." % (f.lower(), v.replace("'", "''"))
            if len(line) > 72:
                raise ValueError("linea ABAP > 72 chars para %s-%s: %r" % (table, f, v))
            out.append(line)
        out.append("ls-erdat = sy-datum.")
        out.append("ls-ernam = sy-uname.")
        out.append("INSERT %s FROM ls." % table.lower())
        out.append("IF sy-subrc = 0. ADD 1 TO lv_ok. ELSE. ADD 1 TO lv_ko. ENDIF.")
        out.append("")
    out += ["COMMIT WORK.",
            "WRITE: / '%s OK:', lv_ok, ' KO:', lv_ko." % table]
    return out


def run_abap(conn, lines):
    res = conn.call("RFC_ABAP_INSTALL_AND_RUN",
                    PROGRAM=[{"LINE": ln[:72]} for ln in lines])
    return [w.get("ZEILE", "") for w in res.get("WRITES", [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="D01,V01")
    ap.add_argument("--accounts", default="4041018,4041019")
    ap.add_argument("--execute", action="store_true",
                    help="sin este flag es dry-run: muestra el plan y no escribe nada")
    a = ap.parse_args()
    targets = [s.strip().upper() for s in a.systems.split(",") if s.strip()]
    accounts = [pad(x) for x in a.accounts.split(",") if x.strip()]

    print("FUENTE %s (read-only)  ->  DESTINO %s" % (SOURCE, ", ".join(targets)))
    print("Cuentas: %s" % ", ".join(accounts))
    print("Modo:    %s\n" % ("EJECUTAR" if a.execute else "DRY-RUN (no escribe)"))

    src = get_connection(SOURCE)
    try:
        source_rows = {}
        for t in ("SKA1", "SKAT", "SKB1"):
            acc = []
            for x in accounts:
                w = ("KTOPL = '%s' AND SAKNR = '%s'" % (KTOPL, x)) if t != "SKB1" \
                    else ("SAKNR = '%s'" % x)
                acc.extend(read(src, t, w))
            source_rows[t] = acc
            print("  P01 %-5s %d filas" % (t, len(acc)))
        missing_src = [x for x in accounts
                       if not any(r["SAKNR"] == x for r in source_rows["SKA1"])]
        if missing_src:
            print("\nABORTA: estas cuentas no existen en P01: %s" % missing_src)
            return 2
    finally:
        src.close()

    for sysid in targets:
        print("\n" + "=" * 72)
        print("DESTINO %s" % sysid)
        print("=" * 72)
        tgt = get_connection(sysid)
        try:
            for t in ("SKA1", "SKAT", "SKB1"):
                have = set()
                for x in accounts:
                    w = ("KTOPL = '%s' AND SAKNR = '%s'" % (KTOPL, x)) if t != "SKB1" \
                        else ("SAKNR = '%s'" % x)
                    have |= {key_of(t, r) for r in read(tgt, t, w)}
                todo = [r for r in source_rows[t] if key_of(t, r) not in have]
                skip = len(source_rows[t]) - len(todo)
                print("\n  %-5s  a insertar %d   ya presentes %d" % (t, len(todo), skip))
                for r in todo:
                    print("        + %s" % " ".join("%s=%s" % (k, r.get(k)) for k in KEYS[t]))
                if not todo or not a.execute:
                    continue
                # Lote 1 primero: se verifica antes de soltar el resto (regla del skill).
                for batch in ([todo[:1]] + [todo[1:][i:i + 10]
                                            for i in range(0, len(todo) - 1, 10)]):
                    if not batch:
                        continue
                    for line in run_abap(tgt, build_abap(t, batch)):
                        print("        %s" % line)
                    time.sleep(2)

            # ------------------------------------------------ verificacion campo a campo
            print("\n  --- readback %s vs P01 ---" % sysid)
            bad = 0
            for t in ("SKA1", "SKAT", "SKB1"):
                got = {}
                for x in accounts:
                    w = ("KTOPL = '%s' AND SAKNR = '%s'" % (KTOPL, x)) if t != "SKB1" \
                        else ("SAKNR = '%s'" % x)
                    for r in read(tgt, t, w):
                        got[key_of(t, r)] = r
                for r in source_rows[t]:
                    k = key_of(t, r)
                    g = got.get(k)
                    if not g:
                        print("    %s %s  FALTA en %s" % (t, k, sysid)); bad += 1; continue
                    # ERDAT/ERNAM difieren por diseno: el destino sella su propia creacion.
                    diff = [f for f in FIELDS[t]
                            if f not in SKIP_ON_INSERT and (r.get(f) or "") != (g.get(f) or "")]
                    if diff:
                        print("    %s %s  DIFIERE: %s" % (t, k, ", ".join(
                            "%s(P01=%r %s=%r)" % (f, r.get(f), sysid, g.get(f)) for f in diff)))
                        bad += 1
                    else:
                        print("    %s %s  OK" % (t, k))
            print("\n  %s: %s" % (sysid, "TODO OK" if bad == 0 else "%d divergencias" % bad))
        finally:
            tgt.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
