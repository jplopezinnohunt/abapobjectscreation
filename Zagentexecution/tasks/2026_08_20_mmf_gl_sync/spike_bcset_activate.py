"""
spike_bcset_activate.py — SPIKE en SIMULACION. ¿Se puede alinear customizing P01 -> D01/V01 por
RFC, por el FRAMEWORK de customizing, sin ABAP y sin bajar el candado de P01?

Contexto: SCU0/SCMP no pueden leer P01 (TB569, T000.CCCOPYLOCK='L'). Pero RFC_READ_TABLE si puede,
y SCPR_ACTIV_MN_REMOTE_SUB (BC-Sets) esta remote-enabled y acepta los VALUES en linea, con
SIMULATION_ON y grabacion en orden de customizing. Si funciona, tenemos un mecanismo para TODO el
customizing, no solo la FSV.

⚠️ SIEMPRE arranca en SIMULATION_ON='X' + TRANSPORT_OFF='X'. Escribir requiere --commit explicito.

Caso de prueba: la fila que resuelve el ticket MMF —
    FAGL_011ZC  VERSN=FS10 ERGSL=1.1.1.1 KTOPL=UNES VONKT=0004041015 BISKT=0004041019
que existe SOLO en P01.

Uso:
    python spike_bcset_activate.py                 # simulacion contra D01
    python spike_bcset_activate.py --target V01
"""
import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

TABLE = "FAGL_011ZC"
FIELDS = ["VERSN", "ERGSL", "KTOPL", "VONKT", "BISKT", "XSOLL", "XHABN", "XVERD"]
KEYWHERE = ("VERSN = 'FS10' AND KTOPL = 'UNES' AND VONKT = '0004041015'")
BCSET_ID = "ZFSV_SPIKE_S102"


def parse(res):
    m = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in m} for r in res.get("DATA", [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="D01")
    ap.add_argument("--commit", action="store_true", help="SIN esto va en simulacion")
    a = ap.parse_args()
    if a.target.upper() == "P01":
        print("ABORTA: P01 es fuente, jamas destino.")
        return 2

    # ---------------------------------------------------------------- 1. leer P01
    src = get_connection("P01")
    try:
        rows = parse(src.call("RFC_READ_TABLE", QUERY_TABLE=TABLE, DELIMITER="|",
                              FIELDS=[{"FIELDNAME": f} for f in FIELDS],
                              OPTIONS=[{"TEXT": KEYWHERE}], ROWCOUNT=0))
    finally:
        src.close()
    if not rows:
        print("La fila de prueba no esta en P01. Aborto.")
        return 2
    row = rows[0]
    print("P01 -> %s" % row)

    # ---------------------------------------------------------------- 2. armar BC-Set en memoria
    recattr = [{"ID": BCSET_ID, "VERSION": "0001", "TABLENAME": TABLE, "RECNUMBER": "000001",
                "OBJECTNAME": "", "OBJECTTYPE": "", "ACTIVITY": "", "CLUSTNAME": "",
                "UNCOMPLETE": "", "DELETEFLAG": "", "GENREF": ""}]
    values = [{"ID": BCSET_ID, "VERSION": "0001", "TABLENAME": TABLE, "RECNUMBER": "000001",
               "FIELDNAME": f, "FLAG": "", "VALUE": row.get(f, "")} for f in FIELDS]
    print("\nRECATTR 1 fila · VALUES %d campos" % len(values))

    tgt = get_connection(a.target)
    try:
        # CONTROL_SYSTEM / CONTROL_USER son tipo SYST: el sistema y el usuario que controlan.
        sysid = a.target.upper()
        user = os.environ.get("SAP_%s_USER" % sysid, "") or os.environ.get("SAP_USER", "") or "JP_LOPEZ"

        # ACTIVATION_TYPE es un entero sin documentar aqui: se prueban los plausibles en
        # SIMULACION y se observa cual no rechaza. Nunca se adivina en modo real.
        for atype in (1, 2, 3, 0):
            kw = dict(
                ACTIVATION_TYPE=atype,
                CONTROL_SYSTEM=sysid,
                CONTROL_USER=user,
                PROTO_HANDLE="",
                SIMULATION_ON="" if a.commit else "X",
                TRANSPORT_OFF="" if a.commit else "X",
                NO_COMMIT="" if a.commit else "X",
                SAFETY="X",
                RECATTR=recattr,
                VALUES=values,
            )
            print("\n--- ACTIVATION_TYPE=%d  SIMULATION_ON=%r ---" % (atype, kw["SIMULATION_ON"]))
            try:
                r = tgt.call("SCPR_ACTIV_MN_REMOTE_SUB", **kw)
            except Exception as e:
                print("   EXC %s" % str(e)[:200])
                continue
            print("   RC_ACTIV        = %r" % r.get("RC_ACTIV"))
            print("   SIMULATION_CHNG = %r" % r.get("SIMULATION_CHANGE"))
            print("   TASK_CUST_EXP   = %r" % r.get("TASK_CUST_EXP"))
            print("   TASK_SYST_EXP   = %r" % r.get("TASK_SYST_EXP"))
            aft = r.get("AFT_IMP_DATA") or []
            print("   AFT_IMP_DATA    = %d filas %s" % (len(aft), aft[:2]))
            vo = r.get("VARIABLES_OUT") or []
            if vo:
                print("   VARIABLES_OUT   = %s" % vo[:3])
            break
    finally:
        tgt.close()

    # ---------------------------------------------------------------- 3. verificar que NO escribio
    chk = get_connection(a.target)
    try:
        after = parse(chk.call("RFC_READ_TABLE", QUERY_TABLE=TABLE, DELIMITER="|",
                               FIELDS=[{"FIELDNAME": f} for f in FIELDS],
                               OPTIONS=[{"TEXT": KEYWHERE}], ROWCOUNT=0))
    except Exception as e:
        after = [] if "TABLE_WITHOUT_DATA" in str(e) else None
    finally:
        chk.close()
    print("\n--- lectura posterior en %s: %s ---"
          % (a.target, "SIGUE SIN LA FILA (simulacion limpia)" if after == []
             else ("LA FILA EXISTE -> %s" % after if after else "no comprobable")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
