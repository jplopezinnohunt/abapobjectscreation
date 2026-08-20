"""
gl_master_sync.py — sincroniza cuentas GL de P01 (fuente, read-only) a D01 / V01.

CANAL: **API ESTANDAR**. Lectura GL_ACCT_MASTER_GET_COA_RFC + GL_ACCT_MASTER_GET_CCODE_RFC,
escritura GL_ACCT_MASTER_SAVE_RFC. NUNCA INSERT plano sobre SKA1/SKAT/SKB1: eso salta derivacion,
rangos de numeracion y checks de consistencia, y esta PROHIBIDO para master data estandar
(RFC_ABAP_INSTALL_AND_RUN solo vale para tablas propias Y*/Z*).

Sustituye a mmf_gl_sync.py, que usaba el canal prohibido.

☠️ TESTMODE de GL_ACCT_MASTER_SAVE_RFC viene VACIO por defecto -> omitirlo ESCRIBE DE VERDAD.
   Es la trampa INVERSA de FM_FUND_CREATE_RFC, donde omitir I_FLG_TESTRUN simula en silencio.
   Aqui se pasa SIEMPRE explicito, en los dos sentidos.

Uso:
    python gl_master_sync.py --systems D01 --accounts 4041018,4041019           # dry-run
    python gl_master_sync.py --systems D01 --accounts 4041018,4041019 --execute
    python gl_master_sync.py --systems V01 --missing --execute   # todo lo que falte en V01
"""
import argparse
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

KTOPL = "UNES"
BUKRS = "UNES"          # JP s102: "estamos alineando UNES"
SOURCE = "P01"


def pad(a):
    a = str(a).strip()
    return a if len(a) == 10 else a.zfill(10)


def parse(res):
    m = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in m} for r in res.get("DATA", [])]


def rd(conn, table, fields, where):
    try:
        return parse(conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                               FIELDS=[{"FIELDNAME": f} for f in fields],
                               OPTIONS=[{"TEXT": where}], ROWCOUNT=0))
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        raise


def read_gl(conn, saknr):
    """Lee una cuenta completa por la API estandar. Devuelve (coa, names, ccode) o None."""
    try:
        r1 = conn.call("GL_ACCT_MASTER_GET_COA_RFC",
                       ACCOUNT_COA={"KEYY": {"KTOPL": KTOPL, "SAKNR": saknr}})
    except Exception as e:
        print("      GET_COA %s: %s" % (saknr, str(e)[:110]))
        return None
    coa, names = r1.get("ACCOUNT_COA"), r1.get("ACCOUNT_NAMES") or []
    try:
        r2 = conn.call("GL_ACCT_MASTER_GET_CCODE_RFC",
                       ACCOUNT_CCODE={"KEYY": {"BUKRS": BUKRS, "SAKNR": saknr}})
        ccode = r2.get("ACCOUNT_CCODE")
    except Exception as e:
        # NOT_EXISTING a nivel sociedad es un dato, no un fallo: la cuenta existe en el plan
        # pero no esta extendida a esta sociedad.
        print("      GET_CCODE %s: %s" % (saknr, str(e)[:80]))
        ccode = None
    return coa, names, ccode


def msgs(res):
    out = []
    for m in (res.get("RETURN") or []):
        if m.get("TYPE") in ("E", "A", "W"):
            out.append("%s %s%s %s" % (m.get("TYPE"), m.get("ID"), m.get("NUMBER"),
                                       m.get("MESSAGE")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="D01")
    ap.add_argument("--accounts", default="")
    ap.add_argument("--missing", action="store_true",
                    help="calcula las cuentas que faltan en el destino en vez de darlas a mano")
    ap.add_argument("--execute", action="store_true",
                    help="sin este flag va en TESTMODE='X' y no escribe")
    a = ap.parse_args()
    targets = [s.strip().upper() for s in a.systems.split(",") if s.strip()]
    if "P01" in targets:
        print("ABORTA: P01 es FUENTE, nunca destino.")
        return 2

    print("FUENTE %s (read-only, API estandar)  ->  DESTINO %s" % (SOURCE, ", ".join(targets)))
    print("Modo: %s\n" % ("EJECUTAR (TESTMODE='')" if a.execute else "DRY-RUN (TESTMODE='X')"))

    src = get_connection(SOURCE)
    try:
        src_all = {r["SAKNR"] for r in rd(src, "SKA1", ["SAKNR"], "KTOPL = '%s'" % KTOPL)}
        print("  P01 SKA1 (chart %s): %d cuentas" % (KTOPL, len(src_all)))

        for sysid in targets:
            print("\n" + "=" * 74)
            print("DESTINO %s" % sysid)
            print("=" * 74)
            tgt = get_connection(sysid)
            try:
                if a.missing:
                    have = {r["SAKNR"] for r in rd(tgt, "SKA1", ["SAKNR"], "KTOPL = '%s'" % KTOPL)}
                    todo = sorted(src_all - have)
                    print("  faltan en %s: %d cuentas" % (sysid, len(todo)))
                else:
                    todo = [pad(x) for x in a.accounts.split(",") if x.strip()]
                if not todo:
                    print("  nada que hacer.")
                    continue

                ok = fail = 0
                for saknr in todo:
                    got = read_gl(src, saknr)
                    if not got:
                        print("  %s  NO LEIBLE en P01 — se salta" % saknr)
                        fail += 1
                        continue
                    coa, names, ccode = got
                    txt = next((n["DATA"].get("TXT50") or n["DATA"].get("TXT20") or ""
                                for n in names if n["KEYY"].get("SPRAS") == "E"), "")
                    # ACTION='I' = alta. Probado: 'U' sobre una cuenta inexistente devuelve
                    # FH058, y sin ACTION la API responde FH502 "Import of table SKA1 not
                    # possible" -- que suena a fallo tecnico y es solo la accion vacia.
                    coa = dict(coa); coa["ACTION"] = "I"
                    names = [dict(n, ACTION="I") for n in names]
                    kw = {"ACCOUNT_COA": coa, "ACCOUNT_NAMES": names,
                          "TESTMODE": "" if a.execute else "X"}
                    if ccode:
                        kw["ACCOUNT_CCODES"] = [dict(ccode, ACTION="I")]
                    try:
                        res = tgt.call("GL_ACCT_MASTER_SAVE_RFC", **kw)
                    except Exception as e:
                        print("  %s  %-28s SAVE ERR %s" % (saknr, txt[:28], str(e)[:80]))
                        fail += 1
                        continue
                    errs = msgs(res)
                    tag = "OK " if not [m for m in errs if m[0] in "EA"] else "ERR"
                    print("  %s %s  %-28s %s" % (tag, saknr, txt[:28],
                                                 (" | ".join(errs))[:110] if errs else ""))
                    ok += 1 if tag == "OK " else 0
                    fail += 1 if tag == "ERR" else 0
                    time.sleep(0.4)

                print("\n  %s: %d ok, %d con problema" % (sysid, ok, fail))

                # -------- readback: la unica prueba que vale. Nunca fiarse de RETURN.
                if a.execute:
                    print("\n  --- readback %s vs P01 (campo a campo) ---" % sysid)
                    bad = 0
                    for saknr in todo:
                        p, t = read_gl(src, saknr), read_gl(tgt, saknr)
                        if not t or not t[0]:
                            print("    %s  NO EXISTE en %s" % (saknr, sysid))
                            bad += 1
                            continue
                        pd_, td_ = (p[0] or {}).get("DATA", {}), (t[0] or {}).get("DATA", {})
                        diff = [k for k in pd_ if (pd_.get(k) or "") != (td_.get(k) or "")]
                        if diff:
                            print("    %s  DIFIERE en %s" % (saknr, ", ".join(diff[:8])))
                            bad += 1
                        else:
                            print("    %s  OK" % saknr)
                    print("\n  readback: %s" % ("TODO OK" if bad == 0 else "%d divergencias" % bad))
            finally:
                tgt.close()
    finally:
        src.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
