"""
fx_revaluation_scope_check.py — SOLO LECTURA. ¿QUE CUENTAS DE BANCO O INVERSION SE QUEDARON
FUERA DE LA REVALUACION?

La diferencia con `ob09_vs_variant_check.py` no es de matiz, es de PUERTA DE ENTRADA:

    ob09_vs_variant_check  entra por T030H  -> solo ve cuentas que YA tienen OB09.
    este check             entra por la NATURALEZA de la cuenta (que se presenta como banco,
                           deposito o inversion en el balance que la sociedad ejecuta).

Una cuenta de banco **sin OB09 y sin variante** es invisible para el primero: no tiene fila en
T030H, asi que nunca aparece en su poblacion. Y es justo la peor de las tres situaciones, porque
no hay ni medio indicio de que alguien pensara en valorarla.

Nace de `4041011` (s102): 10 M EUR netos abiertos, `T030H` configurado y en NINGUNA variante de
F.05. Se encontro barriendo, no porque nadie lo pidiera. La pregunta de JP fue la correcta:
¿y que OTRAS quedaron fuera? Esto la contesta sobre la poblacion entera.

COMO SE DECIDE QUE UNA CUENTA "ES DE BANCO O INVERSION" — medido, no por el nombre
    Por su POSICION en la version de balance que la sociedad EJECUTA de verdad (derivada de las
    variantes de RFBILA00, no de T011 — regla
    feedback_a_config_object_applies_to_a_population_prove_it_before_measuring).
    Posiciones por defecto, medidas en FS10/UNES el 2026-08-21:
        1.1.1.1 Cash with Banks · 1.1.1.2 Cash in Hand · 1.1.2.1 Short Term Deposits
        1.1.2.3 Treasury Bills  · 1.2.1.1 Other Investments
    Se pueden cambiar con --positions; el criterio queda EXPLICITO, no escondido en el codigo.

EL ARBOL DE DETERMINACION ES POR CUENTA (SKB1-XOPVW), NO POR VARIANTE
    XOPVW = 'X'  -> partidas abiertas -> KDF -> T030H, una fila POR CUENTA (OB09)
    XOPVW = ''   -> saldo             -> KDB -> T030S, una fila por CLAVE de diferencias de
                    cambio (SKB1-KDFSL); la fila con clave vacia es el DEFECTO del plan.
    Medido en UNES 2026-08-21: KDFSL vacio en las 2.315 cuentas, asi que TODA cuenta valorada por
    saldo cae en el defecto del plan -> gasto 6045011 / ingreso 7045011. La fila 'GRP' (5022012)
    esta definida y no la usa nadie. Pedir T030H a una cuenta de saldo daba 160 falsos defectos.

LAS CUATRO SALIDAS
    OK                    en variante Y con su determinacion (T030H o T030S segun XOPVW)
    FALTA VARIANTE        tiene determinacion y no entra en ninguna variante: NO SE VALORA NUNCA,
                          y sin error. Es el defecto que nadie ve.
    FALTA DETERMINACION   entra en variante y no tiene la fila que le toca: F.05 fallara al postear
    FUERA DE TODO         ni determinacion ni variante, pero CON exposicion abierta en divisa

SEGUNDO MODO DE FALLO CONOCIDO, anadido 2026-08-26 (A47) - CONTAMINADO-LATENTE: LO DECIDE UN
ARGUMENTO CLI
    Este check resuelve la pertenencia a variante con `covered()` (l.239), el resolutor LEGADO de
    `ob09_vs_variant_check` (importado en l.68), que MEZCLA SKONTO con AKONTO y por tanto no
    respeta "un campo con solo exclusiones = todo lo demas". El correcto es
    `variant_selection()` + `covered_in()` eligiendo el campo por SKB1-MITKZ.

    VALIDO HOY SOLO PARA LAS 5 POSICIONES POR DEFECTO: sobre ellas la poblacion son exactamente
    1.084 cuentas y las marcadas ALL-BUT (AKONTO) son 0, luego `covered()` y `covered_in()` son
    INDISTINGUIBLES ahi y ninguna cifra ya publicada por este script necesita sustituto (medido
    2026-08-26 sobre el censo del 2026-08-21).

    PERO --positions (l.94) cambia la poblacion, y las 58 cuentas ALL-BUT viven en 1.1.4.1 /
    1.1.4.2 / 1.1.5.1 / 1.1.6.1 / 1.2.3.1-5 / 1.2.4.6 / 1.2.5.1-3 / 2.1.1.1 / 2.1.1.2 / 2.1.2.1 /
    2.1.5.5: apuntar el check a cualquiera de esas y el defecto DISPARA. La trampa ya registrada
    arriba era la ILUSION DE ALCANCE; esta es la SEGUNDA, y no estaba registrada.

    PENDIENTE (cambio de LOGICA, NO hecho en la corrida del 2026-08-26): migrar l.68 / l.169 /
    l.239 a variant_selection()+covered_in() con el campo derivado de SKB1-MITKZ (el fichero ya
    lee SKB1), y mientras tanto un guard que aborte -- o marque la salida como NO VALIDA -- si
    alguna cuenta de la poblacion tiene MITKZ lleno. Ver claim 599 (TIER_1, OPEN) y A47
    state=DEFECTO_VIVO.

Uso:
    python fx_revaluation_scope_check.py
    python fx_revaluation_scope_check.py --system P01 --positions 1.1.1.1,1.1.2.1
Salida: exit 0 si toda cuenta con exposicion esta completa · exit 1 si hay alguna incompleta.
"""

QUALITY_CHECK = {
    "tier": "live",   # gate | live | analysis | quarantined
    "needs": "rfc_p01",
    "what": "alcance de la revaluacion FX: que cuentas entran, cuales se quedan fuera y con que exposicion",
    "args": "[--bukrs UNES]",
}

import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
sys.path.insert(0, HERE)
from rfc_helpers import get_connection                                    # noqa: E402
from ob09_vs_variant_check import parse, rd, variant_accounts, covered, PROGRAM  # noqa: E402
# ENMENDADO 2026-08-26 (A47): `covered` es el resolutor LEGADO (mezcla SKONTO/AKONTO). Se
# sigue importando A PROPOSITO en esta corrida -- migrarlo es cambio de LOGICA -- pero el
# limite de validez esta escrito arriba, en el docstring: solo las 5 posiciones por defecto,
# donde hay 0 cuentas AKONTO. Con otras --positions esta lectura NO es valida.
from fsv_coverage_check import versions_in_use, pad                       # noqa: E402

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `brain_v2/methods/algorithm_memory.json` guarda, por cada memoria, su
# `implication`: que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no
# leerlas es aprender y no aprender a la vez -- y peor, el error queda MECANIZADO: este check
# corre solo, asi que un criterio equivocado se repite cada semana sin que nadie lo relea.
# El try/except es a proposito: si `metodo` no esta, el check sigue corriendo.
sys.path.insert(0, os.path.join(REPO, "process_mining"))
try:
    from metodo import lo_que_ya_aprendimos as _aprendido                 # noqa: E402
except ImportError:
    _aprendido = None

# Medidas en FS10/UNES el 2026-08-21. Explicitas para que se puedan discutir.
DEFAULT_POSITIONS = ["1.1.1.1", "1.1.1.2", "1.1.2.1", "1.1.2.3", "1.2.1.1"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default="P01")
    ap.add_argument("--bukrs", default="UNES")
    ap.add_argument("--ktopl", default="UNES")
    ap.add_argument("--version", default="", help="version de balance; por defecto, la que la "
                                                  "sociedad ejecuta segun las variantes")
    ap.add_argument("--positions", default=",".join(DEFAULT_POSITIONS))
    a = ap.parse_args()

    # ANTES de leer nada: que sabe ya este proyecto de balance / variante / alcance. La trampa
    # registrada de este check es la ILUSION DE ALCANCE — con las 5 posiciones por defecto ve
    # una fraccion de la poblacion — y hay memoria escrita justo sobre eso.
    if _aprendido:
        _aprendido("revaluacion", "balance", "variante", "bilavers", "alcance").avisar()

    pos = [p.strip() for p in a.positions.split(",") if p.strip()]

    print("ALCANCE DE LA REVALUACION FX — %s · sociedad %s\n" % (a.system, a.bukrs))
    c = get_connection(a.system)
    try:
        # --- 1. la version de balance que se EJECUTA (no la que existe)
        if a.version:
            versn = a.version.upper()
            print("  version de balance: %s (forzada)" % versn)
        else:
            usadas, mapa = versions_in_use(c, a.bukrs)
            zc_all = rd(c, "FAGL_011ZC", ["VERSN"], "KTOPL = '%s'" % a.ktopl)
            con_datos = {r["VERSN"] for r in zc_all}
            cand = sorted((usadas or set()) & con_datos,
                          key=lambda v: -len([r for r in zc_all if r["VERSN"] == v]))
            if not cand:
                print("  ABORTA: no se pudo determinar que version ejecuta %s." % a.bukrs)
                return 2
            versn = cand[0]
            print("  version de balance en uso por %s: %s   (la ejecutan: %s)"
                  % (a.bukrs, versn, ", ".join(sorted(mapa.get(versn, {"?"})))))

        # --- 2. las cuentas que el balance presenta como banco / deposito / inversion
        qt = {r["ERGSL"]: r["TXT45"] for r in
              rd(c, "FAGL_011QT", ["VERSN", "ERGSL", "TXT45", "SPRAS"],
                 "VERSN = '%s' AND SPRAS = 'E'" % versn)}
        zc = rd(c, "FAGL_011ZC", ["ERGSL", "VONKT", "BISKT"],
                "KTOPL = '%s' AND VERSN = '%s'" % (a.ktopl, versn))
        iv = [(pad(r["VONKT"]), pad(r["BISKT"] or r["VONKT"]), r["ERGSL"])
              for r in zc if r["ERGSL"] in pos]
        print("\n  posiciones consideradas de banco / inversion:")
        for p in pos:
            n = len([1 for lo, hi, e in iv if e == p])
            print("     %-10s %-42s %d intervalo(s)" % (p, qt.get(p, "(sin texto)")[:42], n))
        if not iv:
            print("\n  ABORTA: ninguna de esas posiciones tiene intervalos en %s." % versn)
            return 2

        skb1 = rd(c, "SKB1", ["SAKNR", "WAERS", "XSPEB", "XOPVW", "KDFSL"],
                  "BUKRS = '%s'" % a.bukrs)
        txt = {r["SAKNR"]: r["TXT50"] for r in
               rd(c, "SKAT", ["SAKNR", "TXT50"],
                  "KTOPL = '%s' AND SPRAS = 'E'" % a.ktopl)}
        pobl = []
        for r in skb1:
            s = pad(r["SAKNR"])
            hit = [e for lo, hi, e in iv if lo <= s <= hi]
            if hit:
                pobl.append((s, r, sorted(set(hit))[0]))
        print("\n  cuentas de la sociedad en esas posiciones: %d" % len(pobl))

        # --- 3. las dos mitades del gate
        t030h = {x["HKONT"]: (x.get("LKORR") or "").strip() for x in
                 rd(c, "T030H", ["HKONT", "LKORR"],
                    "KTOPL = '%s' AND CURTP = '10'" % a.ktopl)}
        # KDB: determinacion por CLAVE de diferencias de cambio, no por cuenta. La fila con
        # KDFSL vacio es el DEFECTO del plan y cubre a toda cuenta sin clave propia.
        t030s = {(x.get("KDFSL") or ""): (x.get("KSOLL"), x.get("KHABN")) for x in
                 rd(c, "T030S", ["KTOPL", "KDFSL", "KSOLL", "KHABN"],
                    "KTOPL = '%s'" % a.ktopl)}
        print("  T030S (KDB, por clave de dif. de cambio): %d fila(s) -> %s"
              % (len(t030s), ", ".join("%s=%s/%s" % (k or "(defecto)", v[0], v[1])
                                       for k, v in sorted(t030s.items()))))
        variants = sorted({x["VARIANT"] for x in
                           rd(c, "VARID", ["VARIANT"], "REPORT = '%s'" % PROGRAM)
                           if x["VARIANT"].startswith(a.bukrs)})
        sets = {v: variant_accounts(c, v) for v in variants}
        # Que MECANISMO usa cada variante: saldo (X_SALBEW) o partidas abiertas (X_GL/X_AP/X_AR).
        # De ello depende si T030H aplica, asi que se lee, no se supone.
        saldo_only = {}
        for v in variants:
            try:
                d = {x["SELNAME"]: (x.get("LOW") or "").strip() for x in
                     (c.call("RS_VARIANT_CONTENTS_RFC", REPORT=PROGRAM, VARIANT=v,
                             VALUTAB=[]).get("VALUTAB") or [])}
            except Exception:
                saldo_only[v] = None
                continue
            saldo_only[v] = (d.get("X_SALBEW") == "X"
                             and not any(d.get(k) == "X" for k in ("X_GL", "X_AP", "X_AR")))
        print("  variantes de %s de %s: %s" % (PROGRAM, a.bukrs, ", ".join(variants) or "(ninguna)"))
        for v in variants:
            print("     %-16s mecanismo: %s" % (v, "SALDO (X_SALBEW)" if saldo_only.get(v)
                                                else "partidas abiertas" if saldo_only.get(v) is False
                                                else "no legible"))
        print("  cuentas con fila en T030H (CURTP 10): %d" % len(t030h))

        local = next((x["WAERS"] for x in rd(c, "T001", ["BUKRS", "WAERS"],
                                             "BUKRS = '%s'" % a.bukrs)), "")
        print("  moneda de la sociedad: %s" % local)

        def exposure(acct):
            """SI / NO / DESCONOCIDA. Nunca 'NO' por una lectura fallida (claim 496)."""
            try:
                rows = parse(c.call("RFC_READ_TABLE", QUERY_TABLE="BSIS", DELIMITER="|",
                                    FIELDS=[{"FIELDNAME": "WAERS"}],
                                    OPTIONS=[{"TEXT": "BUKRS = '%s' AND HKONT = '%s'"
                                              % (a.bukrs, acct)}], ROWCOUNT=0))
            except Exception as e:
                if "TABLE_WITHOUT_DATA" in str(e):
                    return "NO"
                return "DESCONOCIDA"
            return "SI" if any(r["WAERS"] and r["WAERS"] != local for r in rows) else "NO"

        # --- 4. clasificar la poblacion entera
        #
        # DOS FILTROS QUE NO SON OPCIONALES, y que en la primera version de este check faltaban:
        #   * BLOQUEADA (SKB1-XSPEB): una cuenta bloqueada no se postea, asi que no hay nada que
        #     valorar. Sale de la poblacion, no es un defecto.
        #   * SIN EXPOSICION: una cuenta activa cuyas partidas en divisa estan TODAS compensadas
        #     tampoco tiene nada que valorar, y F.05 no le pedira cuenta de contrapartida. Marcarla
        #     como "falta OB09" es un falso positivo — es el mismo error que refuto el claim 540
        #     el 2026-08-20 con 4041012 y 4041014, y la primera corrida de este check lo repitio
        #     sobre 241 cuentas. La configuracion incompleta SIN exposicion se reporta como
        #     LATENTE: se sabra, pero no es una alarma y no rompe el gate.
        # Otra sociedad no hace falta filtrarla: SKB1 se lee ya por BUKRS.
        #
        # Y la exposicion solo se pregunta a las cuentas con configuracion INCOMPLETA: una cuenta
        # completa esta bien la tenga o no, asi que preguntar por las 1.084 era gastar 800 lecturas
        # de BSIS para no cambiar ninguna conclusion.
        buckets = {"OK": [], "FALTA VARIANTE": [], "FALTA DETERMINACION": [], "FUERA DE TODO": [],
                   "DESCONOCIDA": [], "LATENTE": [], "BLOQUEADA": []}
        for s, r, p in sorted(pobl):
            if r.get("XSPEB") == "X":
                buckets["BLOQUEADA"].append((s, p, "bloqueada para contabilizar"))
                continue
            # EL ARBOL DE DECISION ES POR CUENTA, NO POR VARIANTE (companion fx_revaluation_f05_v1,
            # verificado en vivo 2026-08-21):
            #     SKB1-XOPVW = 'X'  -> partidas abiertas -> KDF  -> T030H, fila POR CUENTA
            #     SKB1-XOPVW = ''   -> saldo             -> KDB  -> T030S, fila por CLAVE de
            #                          diferencias de cambio (SKB1-KDFSL); vacia = fila por
            #                          defecto del plan. En UNES: KDFSL vacio en las 2.315
            #                          cuentas -> todas caen en la fila por defecto,
            #                          gasto 6045011 / ingreso 7045011.
            # Sin esto el check pedia T030H a 160 cuentas de banco que se determinan por T030S y
            # estan perfectamente configuradas.
            # ENMENDADO 2026-08-26 (A47): resolutor LEGADO. Valido solo mientras la
            # poblacion no traiga cuentas ALL-BUT (AKONTO); ver docstring del modulo.
            vs = covered(s, sets)
            if r.get("XOPVW") == "X":
                has, via = s in t030h, "T030H"
            else:
                has, via = (r.get("KDFSL") or "") in t030s, "T030S/%s" % (r.get("KDFSL") or "default")
            if vs and has:
                buckets["OK"].append((s, p, "%s · %s" % (", ".join(vs), via)))
                continue
            # OJO — el mecanismo de la variante decide si T030H aplica siquiera:
            #   X_SALBEW = X  -> valoracion de SALDO. T030H/OB09 es la determinacion de las
            #                    PARTIDAS ABIERTAS, asi que su ausencia NO es un defecto aqui.
            #   X_GL/X_AP/X_AR -> valoracion de partidas abiertas: ahi T030H SI hace falta.
            # Medido 2026-08-21: UNES_UNBA corre con X_SALBEW=X y X_GL/X_AP/X_AR en blanco, y
            # T030 no tiene NINGUNA fila KDB. Juzgar esas cuentas con la regla de las partidas
            # abiertas producia 160 falsos defectos. Hasta que el mecanismo de contrapartida de
            # la valoracion por saldo este EXPLICADO, esas cuentas se marcan REVISAR, no DEFECTO.
            hueco = ("FALTA VARIANTE" if has else
                     "FALTA DETERMINACION" if vs else "FUERA DE TODO")
            nota = ("determinacion %s, fuera de toda variante" % via if has else
                    "en %s pero SIN fila en %s" % (", ".join(vs), via) if vs else
                    "ni determinacion (%s) ni variante" % via)
            e = exposure(s)
            if e == "DESCONOCIDA":
                buckets["DESCONOCIDA"].append((s, p, "no se pudo leer BSIS — %s" % nota))
            elif e == "SI":
                buckets[hueco].append((s, p, nota))
            else:
                buckets["LATENTE"].append((s, p, "%s · sin exposicion hoy" % hueco))

        print("\n" + "=" * 78)
        print("  poblacion de banco / inversion de %s: %d cuentas" % (a.bukrs, len(pobl)))
        for k in ("OK", "FALTA VARIANTE", "FALTA DETERMINACION", "FUERA DE TODO",
                  "DESCONOCIDA", "LATENTE", "BLOQUEADA"):
            marca = "  <<< DEFECTO VIVO" if (k in ("FALTA VARIANTE", "FALTA DETERMINACION",
                                                   "FUERA DE TODO") and buckets[k]) else ""
            print("  %-16s %4d%s" % (k, len(buckets[k]), marca))
        print("=" * 78)
        rc = 0
        for k in ("FALTA VARIANTE", "FALTA DETERMINACION", "FUERA DE TODO",
                  "DESCONOCIDA"):
            if not buckets[k]:
                continue
            if k != "DESCONOCIDA":
                rc = 1
            if k == "REVISAR SALDO":
                print("\nREVISAR (%d) — valoradas por SALDO (X_SALBEW) y sin fila en T030H. "
                      "T030H/OB09 gobierna las PARTIDAS ABIERTAS, asi que su ausencia aqui no "
                      "prueba un defecto; y T030 no tiene ninguna fila KDB. El mecanismo de "
                      "contrapartida NO esta explicado: no se cuenta como defecto hasta que lo "
                      "este." % len(buckets[k]))
            else:
                print("\n%s (%d) — cuentas ACTIVAS y CON exposicion abierta en divisa:"
                      % (k, len(buckets[k])))
            for s, p, nota in buckets[k][:20]:
                print("   %-12s %-8s %-44s %s" % (s, p, txt.get(s, "")[:44], nota))
            if len(buckets[k]) > 20:
                print("   ... y %d mas" % (len(buckets[k]) - 20))
        if buckets["LATENTE"]:
            print("\nLATENTE (%d) — configuracion incompleta pero sin exposicion hoy. No es"
                  " alarma; lo sera el dia que se postee en divisa:" % len(buckets["LATENTE"]))
            for s, p, nota in buckets["LATENTE"][:15]:
                print("   %-12s %-8s %-44s %s" % (s, p, txt.get(s, "")[:44], nota))
            if len(buckets["LATENTE"]) > 15:
                print("   ... y %d mas" % (len(buckets["LATENTE"]) - 15))
        if rc == 0:
            print("\nToda cuenta de banco o inversion ACTIVA y CON exposicion esta completa.")
        else:
            print("\nHay defectos vivos — arriba, por tipo de hueco.")
        return rc
    finally:
        c.close()


if __name__ == "__main__":
    sys.exit(main())
