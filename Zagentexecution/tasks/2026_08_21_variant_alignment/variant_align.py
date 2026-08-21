"""
variant_align.py — alinea variantes de programa de P01 (referencia) hacia D01 / V01.

H113. Las variantes NO se transportan (VARID.TRANSPORT='F'), asi que cada sistema tiene la suya
editada a mano y divergen. Canal: API estandar RFC, PELDANO 1 -- no hace falta excepcion de
escritura directa.

    lectura   RS_VARIANT_CONTENTS_RFC   (tambien en P01: CCCOPYLOCK no le afecta)
    borrado   RS_VARIANT_DELETE_RFC     (VARIANT es CHANGING, USE_EXCEPTIONS='X')
    creacion  RS_CREATE_VARIANT_RFC

⚠️ POR QUE BORRA Y RECREA, Y NO MODIFICA
   RS_VARIANT_CHANGE_RFC no sirve: su interfaz es REPORT + VARIANT + VALUE_OR_ATTR, sin tabla de
   contenido. Es de dialogo. La unica via por RFC es borrar y volver a crear.

☠️ LO QUE NO SE ENVIA, SAP LO RELLENA CON DEFECTOS EN SILENCIO
   Medido en el spike: una variante creada con 2 lineas salio con 9 parametros de pantalla puestos
   a cero. Por eso este script copia VALUTAB **ENTERO** de P01 -- fechas, metodo de valoracion y
   flags de modo incluidos -- y no solo la seleccion de cuentas. Copiar de menos pierde el proceso.

SEGURIDAD
   - P01 jamas es destino: rechazo cableado.
   - Snapshot PRE del destino a fichero ANTES de borrar. Si la creacion falla, restaura sola.
   - Verificacion POST releyendo y comparando contra P01, entrada a entrada.
   - Dry-run por defecto; --execute para escribir.

Uso:
    python variant_align.py                                   # dry-run, D01 y V01
    python variant_align.py --targets D01 --execute
    python variant_align.py --variants UNES_DEPOSIT --execute
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

PROGRAM = "SAPF100"
SOURCE = "P01"
DEFAULT_VARIANTS = ["UNES_DEPOSIT", "UNES_UNBA", "UNES_OI_G/L", "UNES_OI_AR/AP"]
FIELDS = ("SELNAME", "KIND", "SIGN", "OPTION", "LOW", "HIGH")


def contents(conn, variant):
    """VALUTAB entero. None = no existe / no legible (distinto de vacia)."""
    try:
        r = conn.call("RS_VARIANT_CONTENTS_RFC", REPORT=PROGRAM, VARIANT=variant, VALUTAB=[])
    except Exception as e:
        print("      [%s] no legible: %s" % (variant, str(e)[:90]))
        return None
    return [{k: (x.get(k) or "").strip() for k in FIELDS} for x in (r.get("VALUTAB") or [])]


def key(rows):
    return sorted(tuple(r[k] for k in FIELDS) for r in rows)


def texts(conn, variant):
    try:
        res = conn.call("RFC_READ_TABLE", QUERY_TABLE="VARIT", DELIMITER="|",
                        FIELDS=[{"FIELDNAME": "LANGU"}, {"FIELDNAME": "VTEXT"}],
                        OPTIONS=[{"TEXT": "REPORT = '%s' AND VARIANT = '%s'" % (PROGRAM, variant)}],
                        ROWCOUNT=0)
        meta = res.get("FIELDS", [])
        out = []
        for row in res.get("DATA", []):
            wa = row["WA"]
            d = {f["FIELDNAME"]: wa[int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
                 for f in meta}
            out.append({"MANDT": "", "LANGU": d["LANGU"], "REPORT": PROGRAM,
                        "VARIANT": variant, "VTEXT": d["VTEXT"]})
        return out
    except Exception:
        return []


_EXT_DATE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")


def to_internal(rows):
    """RS_VARIANT_CONTENTS_RFC devuelve las fechas en formato EXTERNO (31.07.2026) y
    RS_CREATE_VARIANT_RFC las quiere en INTERNO (20260731). Mandarlas como vienen NO da error:
    las escribe CORRUPTAS ('20.7..31.0'). Medido en V01 el 2026-08-21 sobre P_BBUDAT, P_BLDAT,
    STICHTAG y ST_BUDAT, que eran IDENTICAS a P01 y quedaron rotas por copiarlas tal cual."""
    out = []
    for r in rows:
        r = dict(r)
        for f in ("LOW", "HIGH"):
            m = _EXT_DATE.match(r.get(f, "") or "")
            if m:
                r[f] = m.group(3) + m.group(2) + m.group(1)
        out.append(r)
    return out


def create(conn, variant, rows, txts):
    rows = to_internal(rows)
    desc = {"REPORT": PROGRAM, "VARIANT": variant, "TRANSPORT": "F", "ENVIRONMNT": "A",
            "PROTECTED": "", "MLANGU": "E", "ENAME": "JP_LOPEZ"}
    return conn.call("RS_CREATE_VARIANT_RFC", CURR_REPORT=PROGRAM, CURR_VARIANT=variant,
                     VARI_DESC=desc, VARI_CONTENTS=rows, VARI_TEXT=txts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="D01,V01")
    ap.add_argument("--variants", default="ALL",
                    help="ALL = todas las operativas de %s en P01 (sin SAP&*)" % PROGRAM)
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    targets = [t.strip().upper() for t in a.targets.split(",") if t.strip()]
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]
    if SOURCE in targets:
        print("ABORTA: %s es la referencia, nunca destino." % SOURCE)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print("REFERENCIA %s (solo lectura)  ->  %s" % (SOURCE, ", ".join(targets)))
    print("Modo: %s\n" % ("EJECUTAR" if a.execute else "DRY-RUN (no escribe)"))

    src = get_connection(SOURCE)
    try:
        if variants == ["ALL"]:
            res = src.call("RFC_READ_TABLE", QUERY_TABLE="VARID", DELIMITER="|",
                           FIELDS=[{"FIELDNAME": "VARIANT"}],
                           OPTIONS=[{"TEXT": "REPORT = '%s'" % PROGRAM}], ROWCOUNT=0)
            variants = sorted({r["WA"].strip() for r in res.get("DATA", [])
                               if r["WA"].strip() and not r["WA"].strip().startswith("SAP&")})
            print("  %d variantes operativas en %s (excluidas las SAP&*)" % (len(variants), SOURCE))
        ref = {v: contents(src, v) for v in variants}
        reftxt = {v: texts(src, v) for v in variants}
    finally:
        src.close()
    for v in variants:
        print("  %s %-16s %s" % (SOURCE, v,
                                 "NO LEIBLE" if ref[v] is None else "%d entradas" % len(ref[v])))

    rc = 0
    for tgt in targets:
        print("\n" + "=" * 74)
        print("DESTINO %s" % tgt)
        print("=" * 74)
        conn = get_connection(tgt)
        try:
            for v in variants:
                if ref[v] is None:
                    print("  %-16s referencia no legible — se salta" % v)
                    rc = 1
                    continue
                cur = contents(conn, v)
                if cur is not None and key(cur) == key(ref[v]):
                    print("  %-16s YA IDENTICA (%d entradas)" % (v, len(cur)))
                    continue
                falt = [x for x in key(ref[v]) if x not in key(cur or [])]
                sobr = [x for x in key(cur or []) if x not in key(ref[v])]
                print("  %-16s DIFIERE: faltan %d, sobran %d" % (v, len(falt), len(sobr)))
                for x in falt[:8]:
                    print("       + %s" % (x,))
                for x in sobr[:8]:
                    print("       - %s" % (x,))
                if not a.execute:
                    continue

                # ---- snapshot PRE a disco ANTES de tocar nada
                snap = os.path.join(HERE, "PRE_%s_%s_%s.json"
                                    % (tgt, v.replace("/", "_"), stamp))
                with open(snap, "w", encoding="utf-8") as fh:
                    json.dump({"system": tgt, "report": PROGRAM, "variant": v,
                               "contents": cur, "texts": texts(conn, v)},
                              fh, ensure_ascii=False, indent=1)
                print("       PRE -> %s" % os.path.basename(snap))

                try:
                    if cur is not None:
                        conn.call("RS_VARIANT_DELETE_RFC", REPORT=PROGRAM, VARIANT=v,
                                  USE_EXCEPTIONS="X")
                        print("       borrada")
                    create(conn, v, ref[v], reftxt[v] or texts(conn, v))
                    print("       recreada desde %s" % SOURCE)
                except Exception as e:
                    print("       ERROR: %s" % str(e)[:150])
                    # ---- restauracion automatica desde el snapshot
                    try:
                        with open(snap, encoding="utf-8") as fh:
                            back = json.load(fh)
                        if back["contents"]:
                            create(conn, v, back["contents"], back["texts"])
                            print("       RESTAURADA desde el snapshot PRE")
                    except Exception as e2:
                        print("       !!! NO SE PUDO RESTAURAR: %s — usa %s"
                              % (str(e2)[:80], snap))
                    rc = 1
                    continue

                post = contents(conn, v)
                if post is not None and key(post) == key(ref[v]):
                    print("       VERIFICADA: identica a %s (%d entradas)" % (SOURCE, len(post)))
                else:
                    d1 = [x for x in key(ref[v]) if x not in key(post or [])]
                    print("       !!! POST NO COINCIDE: %d entradas sin replicar %s"
                          % (len(d1), d1[:5]))
                    rc = 1
            # variantes que existen en el destino y NO en la referencia: se REPORTAN, no se tocan
            try:
                res = conn.call("RFC_READ_TABLE", QUERY_TABLE="VARID", DELIMITER="|",
                                FIELDS=[{"FIELDNAME": "VARIANT"}],
                                OPTIONS=[{"TEXT": "REPORT = '%s'" % PROGRAM}], ROWCOUNT=0)
                here = {r["WA"].strip() for r in res.get("DATA", [])
                        if r["WA"].strip() and not r["WA"].strip().startswith("SAP&")}
                extra = sorted(here - set(variants))
                if extra:
                    print("\nsolo en %s, NO en %s (no se tocan): %s"
                          % (tgt, SOURCE, ", ".join(extra)))
            except Exception:
                pass
        finally:
            conn.close()

    print("\n%s" % ("ALINEADAS" if rc == 0 else "HUBO PROBLEMAS — revisa arriba"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
