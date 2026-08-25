"""
fsv_coverage_check.py — ¿esta cuenta CAE en alguna posicion del balance?

La tercera tarea posterior al alta de una cuenta de mayor (las otras dos son OB09 y la
variante de F.05). Crear la cuenta no la mete en el balance: la FSV asigna por INTERVALOS
de numero de cuenta (FAGL_011ZC), asi que una cuenta nueva entra sola si alguien ya habia
dejado el rango abierto — y si no, cae en el nodo "Not assigned" y NADIE se entera, porque
el balance cuadra igual: la cuenta esta, solo que colgando de la nada.

Nace de INC-000016262 (s102), donde 4041018/19 quedaron cubiertas por casualidad: el
intervalo 4041015-4041019 ya existia. La siguiente cuenta, la 4041020, ya no.

Dos modos:
  * CUENTAS CONCRETAS  — para el alta: "¿las que acabo de crear estan cubiertas?"
  * BARRIDO            — para la deriva: toda cuenta con movimiento que no cae en ninguna
                         posicion. Es la regla #172: la ocasion es el ticket, el alcance
                         es la poblacion.

Solo LECTURA. Por defecto P01 (donde vive la verdad de la config).

Uso:
    python fsv_coverage_check.py 4041018 4041019
    python fsv_coverage_check.py --sweep
    python fsv_coverage_check.py --sweep --system V01 --versions FS10,FS11
"""

QUALITY_CHECK = {
    "tier": "live",   # gate | live | analysis | quarantined
    "needs": "rfc_p01",
    "what": "una cuenta cae en alguna posicion de la version de balance que la sociedad EJECUTA de verdad",
    "args": "<cuenta...> [--ref <cuenta>] | --sweep",
}

import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "process_mining"))
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None


def parse(res):
    m = res.get("FIELDS", [])
    return [{f["FIELDNAME"]: r["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
             for f in m} for r in res.get("DATA", [])]


def read(conn, table, cols, where=""):
    """None = no pudimos VER. Distinto de [] = vimos y no hay nada."""
    try:
        return parse(conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                               FIELDS=[{"FIELDNAME": c} for c in cols],
                               OPTIONS=([{"TEXT": where}] if where else []), ROWCOUNT=0))
    except Exception as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        print("   ERR %s: %s" % (table, str(e)[:110]))
        return None


def num(s):
    s = (s or "").strip()
    if not s:
        return 0.0
    return -float(s[:-1]) if s.endswith("-") else float(s)


def pad(a):
    """Los intervalos de FAGL_011ZC estan a 10 con ceros. '4041018' no compara con
    '0004041018' como cadena, y la comparacion de intervalos ES por cadena."""
    a = (a or "").strip().upper()
    return a.rjust(10, "0") if a.isdigit() else a


def versions_in_use(conn, bukrs):
    """Que version de balance se ejecuta DE VERDAD para esta sociedad.

    No se deduce de T011: una version existe para todas y se USA para algunas. Quien lo
    sabe es la VARIANTE de RFBILA00 (parametro BILAVERS + SD_BUKRS) — el programa dice lo
    que se puede hacer, la variante lo que se hace.

    Medido 2026-08-21 en P01: FS10 -> UNES (13 variantes) · FS11 -> IIEP/ICTP (16) ·
    FS01 -> mixta y antigua (4). Barrer cuentas de UNES contra FS11 mide el denominador
    equivocado y fabrica un hueco de 144 M que no existe.

    Devuelve (usadas_por_esta_sociedad, mapa_version -> sociedades). None si no se pudo ver.
    """
    v = read(conn, "VARID", ["VARIANT"], "REPORT = 'RFBILA00'")
    if v is None:
        return None, {}
    mapa = {}
    for x in v:
        try:
            r = conn.call("RS_VARIANT_CONTENTS_RFC", REPORT="RFBILA00", VARIANT=x["VARIANT"])
        except Exception:
            continue
        d = {y["SELNAME"]: (y.get("LOW") or "").strip() for y in (r.get("VALUTAB") or [])}
        ver = d.get("BILAVERS")
        if ver:
            mapa.setdefault(ver, set()).add(d.get("SD_BUKRS") or "(sin sociedad)")
    # una variante sin sociedad fijada la puede lanzar cualquiera: cuenta como generica
    usadas = {v for v, b in mapa.items() if bukrs in b or "(sin sociedad)" in b}
    _persistir(mapa)
    return usadas, mapa


def _persistir(mapa):
    """Lo que cuesta una conexion a P01 no se imprime y se tira.

    Este mapa es la unica respuesta que existe a "¿que version de balance EJECUTA esta
    sociedad?", y hace falta leer las 33 variantes de RFBILA00 una a una para tenerlo. Hasta
    hoy se calculaba en cada corrida, se pintaba en pantalla y se perdia -- asi que cualquier
    otro analisis que necesitara el dato tenia dos opciones: repetir la extraccion, o elegir
    una version. Elegir la equivocada es el error de los 144 M EUR (barrer UNES contra FS11).

    Ahora aterriza. `process_mining/account_classes.py` (A34) lo consume para no clasificar una
    cuenta contra una estructura que su sociedad no ejecuta.
    """
    if not mapa:
        return
    import datetime
    import json
    destino = os.path.join(REPO, "brain_v2", "fsv_versions_in_use.json")
    doc = {
        "_que_es": "que version de balance EJECUTA cada sociedad, no cual tiene configurada",
        "_de_donde_sale": ("de las VARIANTES de RFBILA00 (parametro BILAVERS + SD_BUKRS), una a "
                           "una via RS_VARIANT_CONTENTS_RFC. NUNCA de T011: una version EXISTE "
                           "para todas las sociedades y se EJECUTA para algunas"),
        "_por_que_importa": ("barrer las 1.018 cuentas de UNES contra FS11 invento un hueco de 68 "
                             "cuentas y 144 M EUR; contra FS10 -- la que UNES ejecuta -- son 4 "
                             "cuentas y 0,01 EUR"),
        "_ojo": ("una variante sin SD_BUKRS fijado la puede lanzar cualquiera, asi que aparece "
                 "como '(sin sociedad)' y cuenta como generica para todas"),
        "_medido_utc": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        "_medido_por": "Zagentexecution/quality_checks/fsv_coverage_check.py :: versions_in_use",
        "version_a_sociedades": {v: sorted(b) for v, b in sorted(mapa.items())},
        "sociedad_a_versiones": {},
    }
    for v, soc in mapa.items():
        for s in soc:
            doc["sociedad_a_versiones"].setdefault(s, []).append(v)
    for s in doc["sociedad_a_versiones"]:
        doc["sociedad_a_versiones"][s].sort()
    try:
        with open(destino, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
        print("   -> medido y GUARDADO en brain_v2/fsv_versions_in_use.json "
              "(lo consume A34_account_behaviour_classes)")
    except OSError as e:
        print("   AVISO: no se pudo guardar el mapa de versiones: %s" % e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accounts", nargs="*", help="cuentas a comprobar (vacio + --sweep = barrido)")
    ap.add_argument("--system", default="P01")
    ap.add_argument("--ktopl", default="UNES")
    ap.add_argument("--bukrs", default="UNES")
    ap.add_argument("--year", default="2026")
    ap.add_argument("--versions", default="", help="por defecto: todas las que tengan intervalos")
    ap.add_argument("--sweep", action="store_true", help="toda cuenta con movimiento en el ejercicio")
    ap.add_argument("--ref", default="",
                    help="cuenta de REFERENCIA del formulario AM 3-11. Si la referencia tampoco "
                         "esta en una version, esa version no incluye esta familia: no es hueco")
    ap.add_argument("--no-variants", action="store_true",
                    help="no derivar de las variantes que version se usa (mas rapido, menos fiable)")
    a = ap.parse_args()
    if not a.accounts and not a.sweep:
        ap.error("da cuentas concretas o usa --sweep")

    print("COBERTURA FSV — %s · plan %s · sociedad %s\n" % (a.system, a.ktopl, a.bukrs))
    conn = get_connection(a.system)
    try:
        zc = read(conn, "FAGL_011ZC", ["VERSN", "ERGSL", "VONKT", "BISKT"],
                  "KTOPL = '%s'" % a.ktopl)
        if zc is None:
            print("ABORTA: no se pudo leer FAGL_011ZC — no se concluye cobertura sin verla.")
            return 2
        usadas, mapa = versions_in_use(conn, a.bukrs) if not a.no_variants else (None, {})
        if a.versions:
            versions = [v.strip().upper() for v in a.versions.split(",") if v.strip()]
        elif usadas:
            versions = sorted(usadas)
            print("  versiones EN USO para la sociedad %s (segun variantes de RFBILA00): %s"
                  % (a.bukrs, ", ".join(versions)))
        else:
            versions = sorted({r["VERSN"] for r in zc})
            print("  AVISO: no se pudo determinar que version se ejecuta; se miran todas.")
        if mapa:
            for v in sorted(mapa):
                print("     %-6s la ejecutan: %s" % (v, ", ".join(sorted(mapa[v]))))
        iv = {v: [(pad(r["VONKT"]), pad(r["BISKT"] or r["VONKT"]), r["ERGSL"])
                  for r in zc if r["VERSN"] == v] for v in versions}
        vacias = [v for v in versions if not iv.get(v)]
        for v in versions:
            print("  version %-5s %d intervalos%s"
                  % (v, len(iv.get(v, [])),
                     "   -> sin asignaciones para el plan %s: se descarta" % a.ktopl
                     if not iv.get(v) else ""))
        versions = [v for v in versions if iv.get(v)]
        if not any(iv.values()):
            print("\nABORTA: ninguna version con intervalos. Nada que comprobar.")
            return 2

        txt = {r["SAKNR"]: r["TXT50"] for r in
               (read(conn, "SKAT", ["SAKNR", "TXT50"],
                     "KTOPL = '%s' AND SPRAS = 'E'" % a.ktopl) or [])}

        if a.sweep:
            cols = ["RACCT", "HSLVT"] + ["HSL%02d" % i for i in range(1, 13)]
            glt = read(conn, "GLT0", cols,
                       "BUKRS = '%s' AND RYEAR = '%s'" % (a.bukrs, a.year))
            if glt is None:
                print("\nABORTA: GLT0 no legible — no se barre a ciegas.")
                return 2
            saldo = {}
            for r in glt:
                v = sum(num(r.get(k)) for k in cols[1:])
                if abs(v) > 0.005:
                    saldo[r["RACCT"]] = saldo.get(r["RACCT"], 0.0) + v
            targets = sorted(saldo)
            print("\n  cuentas con movimiento en %s: %d" % (a.year, len(targets)))
        else:
            targets, saldo = [pad(x) for x in a.accounts], {}

        rc = 0
        for v in versions:
            if a.ref and not [e for lo, hi, e in iv[v] if lo <= pad(a.ref) <= hi]:
                # La referencia del formulario es el patron de comparacion: si ELLA no esta,
                # esta version no cubre esta familia de cuentas y nunca la cubrio.
                print("\n" + "=" * 78)
                print("VERSION %s — la REFERENCIA %s tampoco esta: version SELECTIVA, no es hueco"
                      % (v, pad(a.ref)))
                print("=" * 78)
                continue
            huecos = [t for t in targets
                      if not [e for lo, hi, e in iv[v] if lo <= pad(t) <= hi]]
            print("\n" + "=" * 78)
            print("VERSION %s — %d de %d SIN posicion" % (v, len(huecos), len(targets)))
            print("=" * 78)
            if not a.sweep:
                for t in targets:
                    hit = [e for lo, hi, e in iv[v] if lo <= pad(t) <= hi]
                    print("  %-12s %-46s %s" % (pad(t), txt.get(pad(t), "")[:46],
                                                ("posicion " + ", ".join(sorted(set(hit))))
                                                if hit else "*** SIN POSICION ***"))
            else:
                for t in sorted(huecos, key=lambda x: -abs(saldo.get(x, 0)))[:40]:
                    print("  %-12s %18s  %s" % (t, "{:,.2f}".format(saldo.get(t, 0)),
                                                txt.get(t, "")[:46]))
                if len(huecos) > 40:
                    print("  ... y %d mas" % (len(huecos) - 40))
                neto = sum(saldo.get(t, 0) for t in huecos)
                if huecos:
                    # Un juego que NETEA a cero suele ser tecnico a proposito (constant
                    # dollar, compensacion). Decirlo, en vez de contar 4 y alarmar.
                    print("\n  neto de los descubiertos: %s%s"
                          % ("{:,.2f}".format(neto),
                             "  <- netean a cero: juego tecnico, probablemente intencional"
                             if abs(neto) < 1 else ""))
            if huecos:
                if usadas is not None and v not in usadas:
                    print("  ^^ version NO ejecutada para la sociedad %s (la usan: %s):"
                          " esto NO es un hueco, es el denominador equivocado."
                          % (a.bukrs, ", ".join(sorted(mapa.get(v, {"?"})))))
                else:
                    rc = 1

        print("\n%s" % ("COBERTURA COMPLETA" if rc == 0 else
                        "HAY CUENTAS FUERA DEL BALANCE — revisa si son tecnicas o es un hueco"))
        return rc
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
