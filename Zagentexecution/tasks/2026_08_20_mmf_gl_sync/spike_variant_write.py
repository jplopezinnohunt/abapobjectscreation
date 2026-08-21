"""
spike_variant_write.py — ¿se puede ESCRIBIR una variante de programa por RFC?

Es la pieza que falta de H113. Hoy sabemos LEER variantes (RS_VARIANT_CONTENTS_RFC) y sabemos que
NO se transportan (VARID.TRANSPORT='F'), asi que UNES_DEPOSIT tiene tres contenidos distintos en
P01/D01/V01 y los no productivos no reproducen F.05. Si RS_CREATE_VARIANT_RFC o
RS_VARIANT_CHANGE_RFC escriben, H113 se resuelve sin excepcion de escritura directa.

DISCIPLINA: el spike NO toca UNES_DEPOSIT. Crea una variante DESECHABLE (ZZTEST_S102) sobre el
mismo programa, comprueba leyendola con RS_VARIANT_CONTENTS_RFC, y la borra con
RS_VARIANT_DELETE_RFC. Probar el mecanismo en un objeto de usar y tirar, nunca en el que importa.

Destino: D01. Nunca P01 -- ademas el cliente esta cerrado (CCCORACTIV='2').

Uso:
    python spike_variant_write.py              # introspeccion + prueba + limpieza en D01
    python spike_variant_write.py --keep       # no borra al final (para inspeccion manual)
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

PROGRAM = "SAPF100"
VARIANT = "ZZTEST_S102"          # desechable, prefijo Z, nunca UNES_*
TARGET = "D01"


def dump_iface(raw, fm):
    print("\n=== %s ===" % fm)
    try:
        d = raw.get_function_description(fm)
    except Exception as e:
        print("   NO EXISTE / ERR: %s" % str(e)[:120])
        return None
    for p in d.parameters:
        ts = p.get("type_description")
        print("   %-12s %-24s %s" % (p["direction"], p["name"], p["parameter_type"]))
        if ts is not None:
            print("        " + ", ".join(f["name"] for f in ts.fields))
    return d


def read_variant(c, variant):
    try:
        r = c.call("RS_VARIANT_CONTENTS_RFC", REPORT=PROGRAM, VARIANT=variant, VALUTAB=[])
        return [x for x in (r.get("VALUTAB") or []) if (x.get("LOW") or "").strip()]
    except Exception as e:
        return "ERR: " + str(e)[:110]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    c = get_connection(TARGET)
    raw = c._conn
    try:
        for fm in ("RS_CREATE_VARIANT_RFC", "RS_VARIANT_CHANGE_RFC",
                   "RS_VARIANT_DELETE_RFC", "RS_CREATE_VARIANT_255_RFC"):
            dump_iface(raw, fm)

        print("\n" + "=" * 70)
        print("PRE — %s en %s: %s" % (VARIANT, TARGET, read_variant(c, VARIANT)))

        # Contenido minimo: una sociedad y una cuenta. Si el FM acepta esto, acepta el resto.
        valutab = [
            {"SELNAME": "BUKRS", "KIND": "S", "SIGN": "I", "OPTION": "EQ",
             "LOW": "UNES", "HIGH": ""},
            {"SELNAME": "SKONTO", "KIND": "S", "SIGN": "I", "OPTION": "EQ",
             "LOW": "0004041018", "HIGH": ""},
        ]
        print("\n--- RS_CREATE_VARIANT_RFC ---")
        try:
            r = c.call("RS_CREATE_VARIANT_RFC", CURR_REPORT=PROGRAM, CURR_VARIANT=VARIANT,
                       VARI_DESC={"REPORT": PROGRAM, "VARIANT": VARIANT,
                                  "ENAME": "JP_LOPEZ", "MLANGU": "E",
                                  "PROTECTED": "", "ENVIRONMNT": "A", "TRANSPORT": "F"},
                       VARI_CONTENTS=valutab)
            print("   OK ->", {k: v for k, v in r.items() if not isinstance(v, list)})
        except Exception as e:
            print("   EXC %s" % str(e)[:200])

        print("\nPOST — %s: %s" % (VARIANT, read_variant(c, VARIANT)))

        if not a.keep:
            print("\n--- limpieza: RS_VARIANT_DELETE_RFC ---")
            try:
                c.call("RS_VARIANT_DELETE_RFC", REPORT=PROGRAM, VARIANT=VARIANT, FLAG_CONFIRMSCREEN="X")
                print("   borrada")
            except Exception as e:
                print("   EXC %s" % str(e)[:160])
            print("   comprobacion: %s" % read_variant(c, VARIANT))

        print("\n>>> UNES_DEPOSIT NO se ha tocado en ningun momento.")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
