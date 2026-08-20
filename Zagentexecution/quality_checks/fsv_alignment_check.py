"""
fsv_alignment_check.py — SOLO LECTURA. Mide la deriva de la VERSION DE BALANCE (FSV) entre
P01 (referencia) y D01 / V01, y emite la ESPECIFICACION DE CAMBIO para cerrarla.

Por que existe: alinear master data NO alinea el sistema. Las cuentas se copian con la API
estandar (GL_ACCT_MASTER_SAVE_RFC), pero la FSV es CUSTOMIZING y viaja por otro canal — o no
viaja. Medido 2026-08-20: tras alinear las 9 cuentas 40410xx en D01 y V01, la fila
'1.1.1.1 -> 0004041015-0004041019' seguia existiendo SOLO en P01, asi que ninguna de las cuentas
nuevas quedaba mapeada a "Cash with Banks" fuera de produccion.
Y ojo con el modo de fallo: un rango no cubre nada si la FILA del rango no existe. La ausencia no
se ve mirando la cuenta; se ve mirando el intervalo.

⛔ POR QUE ESTE SCRIPT NO ESCRIBE
   Se pregunto al sistema (TFDIR WHERE FMODE='R') por un API de mantenimiento de FSV:
   NO EXISTE NINGUNO. No hay BAPI ni FM remote-enabled para T011 / FAGL_011ZC / FAGL_011QT /
   FAGL_011PC. Y FAGL_011* son tablas ESTANDAR, asi que el INSERT plano esta prohibido
   (regla feedback_standard_master_data_writes_through_the_standard_api).
   => El canal correcto es OB58 en el destino, o una orden de customizing.
   Este script produce la especificacion exacta para que un humano la aplique; no la aplica.

Tablas de la FSV:
  T011        versiones (VERSN, KTOPL, ...)          T011T       textos de version
  FAGL_011PC  jerarquia de posiciones (PARENT/CHILD) FAGL_011QT  textos de posicion
  FAGL_011ZC  ASIGNACION cuenta -> posicion  <-- el intervalo VONKT-BISKT vive aqui
  FAGL_011SC/TC/VC/FC  sets, timestamps, contrapartidas, areas funcionales

Uso:
    python fsv_alignment_check.py                          # P01 -> D01,V01, todas las versiones
    python fsv_alignment_check.py --versn FS10 --spec      # solo FS10 + especificacion de cambio
    python fsv_alignment_check.py --systems V01 --accounts 40410
Salida: exit 0 alineado · exit 1 si hay deriva.
"""
import argparse
import os
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

KTOPL = "UNES"
SOURCE = "P01"

# tabla -> (campos clave que comparamos, campos de valor)
SPEC = {
    "T011":       (["VERSN"], ["KTOPL", "XERGS", "AKTVA", "PSSVA", "ERGAK", "ERGPA", "ERGGV",
                               "ZUORD", "XAUTO", "XFBER"]),
    "T011T":      (["SPRAS", "VERSN"], ["VSTXT"]),
    "FAGL_011QT": (["VERSN", "SPRAS", "ERGSL", "TXTYP", "ZEILE"], ["TXT45"]),
    "FAGL_011PC": (["VERSN", "ID"], ["TYPE", "ERGSL", "PARENT", "CHILD", "NEXTN", "STUFE",
                                     "SUMME", "SIGN"]),
    "FAGL_011ZC": (["VERSN", "ERGSL", "KTOPL", "VONKT"], ["BISKT", "XSOLL", "XHABN", "XVERD"]),
    "FAGL_011SC": (["VERSN", "ERGSL"], ["SETPR", "SETVS", "SETNR"]),
    "FAGL_011VC": (["VERSN", "ERGS1"], ["ERGS2"]),
    "FAGL_011FC": (["VERSN", "ERGSL", "VONFB"], ["BISFB"]),
}


def parse(res):
    m = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in m} for r in res.get("DATA", [])]


def rd(conn, table, fields, where):
    """ROWCOUNT=0 sin ROWSKIPS (P01 los rechaza). TABLE_WITHOUT_DATA = cero filas,
    que NO es lo mismo que 'no pudimos ver'."""
    try:
        return parse(conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                               FIELDS=[{"FIELDNAME": f} for f in fields],
                               OPTIONS=([{"TEXT": where}] if where else []), ROWCOUNT=0))
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        print("      ERR %s: %s" % (table, str(e)[:100]))
        return None


def snapshot(sysid, versn):
    """{tabla: {clave: fila}}. None en una tabla = no se pudo leer, distinto de vacia."""
    conn = get_connection(sysid)
    out = {}
    try:
        for t, (keys, vals) in SPEC.items():
            w = []
            if versn and "VERSN" in keys:
                w.append("VERSN = '%s'" % versn)
            if "KTOPL" in keys + vals:
                w.append("KTOPL = '%s'" % KTOPL)
            rows = rd(conn, t, keys + vals, " AND ".join(w))
            if rows is None:
                out[t] = None
                continue
            out[t] = {tuple(r.get(k, "") for k in keys): r for r in rows}
    finally:
        conn.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="D01,V01")
    ap.add_argument("--versn", default="", help="limita a una version, p.ej. FS10")
    ap.add_argument("--accounts", default="", help="prefijo de cuenta para el detalle de 011ZC")
    ap.add_argument("--spec", action="store_true", help="emite la especificacion de cambio OB58")
    a = ap.parse_args()
    targets = [s.strip().upper() for s in a.systems.split(",") if s.strip()]
    rc = 0

    print("FSV — referencia %s (read-only). chart %s%s\n"
          % (SOURCE, KTOPL, ", version " + a.versn if a.versn else ""))
    src = snapshot(SOURCE, a.versn)
    for t in SPEC:
        n = src[t]
        print("  %s %-12s %s" % (SOURCE, t, "NO LEIBLE" if n is None else "%d filas" % len(n)))

    for sysid in targets:
        tgt = snapshot(sysid, a.versn)
        print("\n" + "=" * 78)
        print("%s -> %s" % (SOURCE, sysid))
        print("=" * 78)
        spec_rows = []
        for t, (keys, vals) in SPEC.items():
            s, g = src[t], tgt[t]
            if s is None or g is None:
                print("  %-12s NO COMPARABLE (lectura fallida en %s)"
                      % (t, SOURCE if s is None else sysid))
                continue
            missing = [k for k in s if k not in g]
            extra = [k for k in g if k not in s]
            drift = [k for k in s if k in g
                     and any((s[k].get(v) or "") != (g[k].get(v) or "") for v in vals)]
            flag = "" if not (missing or drift) else "  <<<"
            print("  %-12s faltan %-4d  difieren %-4d  solo en %s: %d%s"
                  % (t, len(missing), len(drift), sysid, len(extra), flag))
            if missing or drift:
                rc = 1
            for k in missing:
                spec_rows.append(("CREAR", t, s[k]))
            for k in drift:
                spec_rows.append(("MODIFICAR", t, s[k]))

        # detalle de lo que mas duele: asignacion cuenta -> posicion
        s, g = src["FAGL_011ZC"], tgt["FAGL_011ZC"]
        if s and g is not None:
            miss = sorted(k for k in s if k not in g)
            if a.accounts:
                miss = [k for k in miss if a.accounts in k[3]]
            if miss:
                print("\n  --- FAGL_011ZC: intervalos que faltan en %s (%d) ---" % (sysid, len(miss)))
                print("     por version: %s" % dict(Counter(k[0] for k in miss)))
                for k in miss[:60]:
                    r = s[k]
                    print("     %-6s %-12s %s -> %s"
                          % (r["VERSN"], r["ERGSL"], r["VONKT"], r.get("BISKT") or "(unico)"))
                if len(miss) > 60:
                    print("     ... y %d mas" % (len(miss) - 60))

        if a.spec and spec_rows:
            out = os.path.join(HERE, "fsv_change_spec_%s.md" % sysid)
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("# Especificacion de cambio FSV — %s -> %s\n\n" % (SOURCE, sysid))
                fh.write("Aplicar en **%s** por **OB58** (o por orden de customizing).\n" % sysid)
                fh.write("NO hay API RFC para esto: se comprobo en TFDIR y no existe.\n\n")
                fh.write("| Accion | Tabla | Clave | Valores |\n|---|---|---|---|\n")
                for act, t, r in spec_rows:
                    keys, vals = SPEC[t]
                    fh.write("| %s | %s | %s | %s |\n"
                             % (act, t,
                                " / ".join("%s=%s" % (k, r.get(k, "")) for k in keys),
                                " / ".join("%s=%s" % (v, r.get(v, "")) for v in vals if r.get(v))))
            print("\n  especificacion -> %s (%d filas)" % (out, len(spec_rows)))

    print("\n%s" % ("FSV ALINEADA" if rc == 0 else "HAY DERIVA DE FSV — ver detalle arriba"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
