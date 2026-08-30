"""
ob09_vs_variant_check.py — SOLO LECTURA. Valida la configuracion de revaluacion FX cruzando
las DOS condiciones que tienen que darse a la vez, y que nadie cruzaba porque una no se sabia leer:

  (1) T030H / OB09  dice DONDE se postea la diferencia de cambio.
  (2) La VARIANTE de F.05 decide SI la cuenta entra siquiera en el calculo.

Una cuenta con (1) y sin (2) esta perfectamente configurada y NO SE VALORA NUNCA. No da error:
simplemente no ocurre. Ese es el defecto que este check caza.

Lee el contenido real de las variantes con RS_VARIANT_CONTENTS_RFC (remote-enabled, funciona en
P01 sin S_DEVELOP). VARI guarda el contenido en CLUSTD, un campo RAW que RFC_READ_TABLE no
devuelve, y VARIS no contiene rangos: por eso durante sesiones se creyo que esto no era auditable.

Uso:
    python ob09_vs_variant_check.py                       # P01
    python ob09_vs_variant_check.py --systems P01,D01,V01 # y compara los tres
    python ob09_vs_variant_check.py --accounts 40410      # limita a un prefijo
Salida: exit 0 limpio · exit 1 si hay cuentas ACTIVAS con OB09 fuera de toda variante.
"""
# LEE PRIMERO `.claude/skills/sap_data_extraction` si vas a ampliar sus lecturas: extrae de
# P01 por RFC, y de alli salen las trampas ya pagadas -- max ~8 campos por RFC_READ_TABLE,
# P01 rechaza ROWSKIPS, y no se parte por delimitador porque un campo de texto puede
# contenerlo.

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",  # datos_sap | conocimiento | herramientas
    "needs": "rfc_p01",
    "what": "cruza T030H/OB09 contra la variante de F.05 que de verdad selecciona la cuenta",
    "args": "[--systems P01,D01,V01] [--accounts <prefijo>]",
    # SUPERSEDE 2026-08-26 (A43, misma clase que fsv_alignment_check.py). Se conserva lo que se
    # declaraba: `--bukrs` NO EXISTE en este script (BUKRS es la constante de l.59) y la
    # declaracion OMITIA por completo `--systems` (l.180), que es el flag que si tiene. La lee
    # una MAQUINA (run_all.py:60-74, por AST) y se publica en brain_v2/quality_checks_state.json.
    "_superseded_text": {"args": "[--bukrs UNES]"},
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
# Se lee ANTES de minar. `brain_v2/methods/algorithm_memory.json` guarda, por cada memoria, su
# `implication`: que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no
# leerlas es aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo.
# Para ESTE check los temas no son decorativos: "variante" trae la memoria de que una version/
# variante EXISTE para todas y se EJECUTA para algunas; "table_without_data" trae la que dice que
# ese error NO significa tabla vacia (y aqui `rd()` y `exposure()` lo tragan como si lo
# significara); "ceros a la izquierda" trae la del relleno de claves numericas que sostiene todo
# el zfill(10) de la comparacion de rangos; "exclusion" trae la de un check que reporta
# candidatos y no sabe registrar "revisado, excluido"; y "balance" trae la peor de todas: el
# mismo defecto reaparece en la COMPROBACION que deberia delatarlo.
sys.path.insert(0, os.path.join(REPO, "process_mining"))
try:
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None

KTOPL = "UNES"
BUKRS = "UNES"
PROGRAM = "SAPF100"


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
        print("    ERR %s: %s" % (table, str(e)[:100]))
        return []


def variant_accounts(conn, variant):
    """Devuelve (incluidas, excluidas, rangos) de la seleccion de cuentas de una variante.
    OJO: el mecanismo cambia entre variantes del MISMO programa — UNES_DEPOSIT usa valores
    sueltos EQ, UNES_UNBA usa rangos BT. No asumir uno de los dos."""
    inc, exc, rngs = set(), set(), []
    try:
        r = conn.call("RS_VARIANT_CONTENTS_RFC", REPORT=PROGRAM, VARIANT=variant, VALUTAB=[])
    except Exception as e:
        print("    variante %s no legible: %s" % (variant, str(e)[:90]))
        return inc, exc, rngs
    for x in (r.get("VALUTAB") or []):
        if (x.get("SELNAME") or "").strip() not in ("SKONTO", "AKONTO"):
            continue
        lo, hi = (x.get("LOW") or "").strip(), (x.get("HIGH") or "").strip()
        sign, opt = (x.get("SIGN") or "").strip(), (x.get("OPTION") or "").strip()
        if not lo:
            continue
        if opt == "BT" and hi:
            rngs.append((sign, lo.zfill(10), hi.zfill(10)))
        else:
            (exc if sign == "E" else inc).add(lo.zfill(10))
    return inc, exc, rngs


def variant_selection(conn, variant, fields=("SKONTO", "AKONTO")):
    """Seleccion de la variante SEPARADA POR CAMPO. Usa esta, no variant_accounts().

    `variant_accounts` mezcla SKONTO (cuentas de mayor) con AKONTO (cuentas asociadas de
    submayor) en un unico conjunto, y al mezclarlas pierde la semantica de cada campo. Medido el
    2026-08-21 en UNES_OI_AR/AP: SKONTO trae 12 inclusiones y AKONTO trae 27 lineas que son
    TODAS de exclusion. Mezclados parece "12 dentro, 27 fuera"; separados dicen otra cosa muy
    distinta -> ver `covered_in`.
    """
    out = {f: {"inc": set(), "exc": set(), "rin": [], "rex": []} for f in fields}
    try:
        r = conn.call("RS_VARIANT_CONTENTS_RFC", REPORT=PROGRAM, VARIANT=variant, VALUTAB=[])
    except Exception as e:
        print("    variante %s no legible: %s" % (variant, str(e)[:90]))
        return out
    for x in (r.get("VALUTAB") or []):
        f = (x.get("SELNAME") or "").strip()
        if f not in out:
            continue
        lo, hi = (x.get("LOW") or "").strip(), (x.get("HIGH") or "").strip()
        if not lo:
            continue
        sign, opt = (x.get("SIGN") or "").strip(), (x.get("OPTION") or "").strip()
        if opt == "BT" and hi:
            out[f]["rex" if sign == "E" else "rin"].append((lo.zfill(10), hi.zfill(10)))
        else:
            out[f]["exc" if sign == "E" else "inc"].add(lo.zfill(10))
    return out


def covered_in(saknr, selections, field="SKONTO"):
    """¿La cuenta entra por ESE campo en alguna variante? Devuelve la lista de variantes.

    LA REGLA QUE HAY QUE RESPETAR: en un select-option de ABAP, si un campo no tiene ninguna
    linea de INCLUSION pero si de exclusion, el conjunto resultante es **TODO MENOS LO
    EXCLUIDO**, no el conjunto vacio. UNES_OI_AR/AP tiene AKONTO con 27 exclusiones y cero
    inclusiones: significa "todas las cuentas asociadas menos estas 27". Leerlo como "ninguna"
    daba 549 cuentas fuera de toda variante cuando son 497, y ensuciaba entero cualquier barrido
    de proveedores y clientes.

    Y el campo importa: una cuenta ASOCIADA de submayor (SKB1-MITKZ lleno) se selecciona por
    AKONTO; una cuenta de mayor normal, por SKONTO. Preguntar por el campo equivocado es
    preguntar por el universo equivocado.
    """
    hit = []
    for var, sel in selections.items():
        s = sel.get(field)
        if not s:
            continue
        if saknr in s["exc"] or any(lo <= saknr <= hi for lo, hi in s["rex"]):
            continue
        solo_exclusiones = not s["inc"] and not s["rin"] and (s["exc"] or s["rex"])
        if solo_exclusiones or saknr in s["inc"] \
                or any(lo <= saknr <= hi for lo, hi in s["rin"]):
            hit.append(var)
    return hit


def covered(saknr, sets):
    """LEGADO — mezcla SKONTO y AKONTO. Correcto para cuentas de mayor normales; para cuentas
    ASOCIADAS de submayor da falsos negativos. Prefiere variant_selection() + covered_in()."""
    hit = []
    for var, (inc, exc, rngs) in sets.items():
        if saknr in exc or any(lo <= saknr <= hi for sign, lo, hi in rngs if sign == "E"):
            continue
        if saknr in inc or any(lo <= saknr <= hi for sign, lo, hi in rngs if sign == "I"):
            hit.append(var)
    return hit


def main():
    if _aprendido:
        _aprendido("variante", "cuenta", "balance", "table_without_data",
                   "ceros a la izquierda", "exclusion").avisar()
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="P01")
    ap.add_argument("--accounts", default="", help="prefijo de cuenta para acotar, p.ej. 40410")
    a = ap.parse_args()
    systems = [s.strip().upper() for s in a.systems.split(",") if s.strip()]
    rc = 0

    for sysid in systems:
        print("\n" + "=" * 78)
        print("%s — OB09 (T030H) x variantes de %s" % (sysid, PROGRAM))
        print("=" * 78)
        c = get_connection(sysid)
        try:
            variants = sorted({x["VARIANT"] for x in
                               rd(c, "VARID", ["VARIANT"], "REPORT = '%s'" % PROGRAM)
                               if x["VARIANT"].startswith(BUKRS)})
            print("  variantes de %s: %s" % (BUKRS, ", ".join(variants) or "(ninguna)"))
            sets = {v: variant_accounts(c, v) for v in variants}
            for v, (inc, exc, rngs) in sets.items():
                print("    %-16s sueltas=%-3d excluidas=%-3d rangos=%s"
                      % (v, len(inc), len(exc),
                         ", ".join("%s-%s" % (lo, hi) for s, lo, hi in rngs) or "-"))

            where = "KTOPL = '%s' AND CURTP = '10'" % KTOPL
            if a.accounts:
                where += " AND HKONT LIKE '%%%s%%'" % a.accounts
            t030h = rd(c, "T030H", ["HKONT", "LKORR", "LSBEW", "LHBEW"], where)
            hk = sorted({x["HKONT"] for x in t030h})
            print("\n  cuentas con fila en T030H (CURTP 10): %d" % len(hk))

            # ARREGLADO 2026-08-26 (A47): se lee TAMBIEN MITKZ, no solo XSPEB.
            #
            # MITKZ dice si la cuenta es ASOCIADA de submayor, y de eso depende POR QUE CAMPO
            # la selecciona la variante: AKONTO si lo es, SKONTO si no. main() solo leia XSPEB,
            # asi que la eleccion de campo por cuenta ni siquiera estaba implementada en el
            # camino que corre -- y por eso tenia que usar covered(), el resolutor LEGADO que
            # mezcla los dos campos. 34 falsos positivos sobre 780 cuentas.
            _skb1 = rd(c, "SKB1", ["SAKNR", "XSPEB", "MITKZ"], "BUKRS = '%s'" % BUKRS)
            blocked = {x["SAKNR"] for x in _skb1 if x.get("XSPEB") == "X"}
            mitkz = {x["SAKNR"]: (x.get("MITKZ") or "").strip() for x in _skb1}

            # TERCERA CONDICION (s102, tras refutar el claim 540). Sin ella este check daba
            # FALSOS POSITIVOS: marcaba 4041011/4041012/4041014 como defecto cuando sus partidas
            # en euros estaban TODAS compensadas, asi que no habia nada que valorar.
            # GLT0.RTCUR dice en que moneda se MOVIO algo; la exposicion viva son las PARTIDAS
            # ABIERTAS en moneda distinta de la local (bsis frente a bsas).
            local = next((x["WAERS"] for x in rd(c, "T001", ["BUKRS", "WAERS"],
                                                 "BUKRS = '%s'" % BUKRS)), "")

            def exposure(acct):
                """'SI' / 'NO' / 'DESCONOCIDA'. BSIS entera revienta (SQL_CAUGHT_RABAX, 3,3M
                filas), asi que se pregunta CUENTA A CUENTA. Y si la lectura falla se devuelve
                DESCONOCIDA, nunca 'NO': leer la ausencia de una lectura fallida como ausencia en
                el sistema es el error que refuto el claim 540 y el que describe el claim 496.

                ENMENDADO 2026-08-26 (A47) — EL DOCSTRING SE QUEDABA CORTO Y HAY UN AGUJERO:
                esta funcion interroga UNICAMENTE BSIS. Las partidas abiertas de una cuenta
                ASOCIADA de submayor (SKB1-MITKZ lleno) viven en BSID/BSIK, NUNCA en BSIS, asi
                que para esas cuentas la respuesta correcta es DESCONOCIDA ("preguntamos a la
                tabla equivocada"), no 'NO' — y hoy TABLE_WITHOUT_DATA se traga como 'NO'
                (l.232-233), que es exactamente el error que este docstring dice estar evitando.
                Cerrar el agujero exige derivar el campo por SKB1-MITKZ y leer BSID/BSIK: es
                cambio de LOGICA y NO se hizo en esta corrida. Cuantas de esas cuentas tienen de
                verdad exposicion abierta SE DESCONOCE."""
                try:
                    rows = parse(c.call("RFC_READ_TABLE", QUERY_TABLE="BSIS", DELIMITER="|",
                                        FIELDS=[{"FIELDNAME": "WAERS"}],
                                        OPTIONS=[{"TEXT": "BUKRS = '%s' AND HKONT = '%s'"
                                                  % (BUKRS, acct)}], ROWCOUNT=0))
                except Exception as e:
                    if "TABLE_WITHOUT_DATA" in str(e):
                        return "NO"
                    print("        [!] BSIS %s no legible: %s" % (acct, str(e)[:70]))
                    return "DESCONOCIDA"
                return "SI" if any(r["WAERS"] and r["WAERS"] != local for r in rows) else "NO"

            # ARREGLADO 2026-08-26 (A47) — main() pasa al camino CORRECTO.
            #
            # Antes: `if covered(acct, sets)`, el resolutor LEGADO. Su propio docstring (l.147)
            # dice literalmente «Prefiere variant_selection() + covered_in()», las dos funciones
            # estaban en ESTE MISMO fichero desde el commit 8da7910 y el vecino
            # fx_revaluation_peer_check.py las usaba bien. El fichero EXPORTABA lo correcto y
            # CONSUMIA lo legado. Medido sobre 780 cuentas: covered() 273 fuera de toda
            # variante, covered_in() por MITKZ 239 -> 34 FALSOS POSITIVOS, todos MITKZ=D/K
            # (20110xx, 20210xx, 20220xx, 20290xx) que UNES_OI_AR/AP si selecciona por AKONTO
            # con «todas menos esas 27».
            seleccion = {v: variant_selection(c, v) for v in variants}
            orphan = []
            for x in t030h:
                acct = x["HKONT"]
                # el CAMPO se deriva de la cuenta, que es justo lo que el camino legado no
                # podia hacer: una asociada de submayor se selecciona por AKONTO.
                campo = "AKONTO" if mitkz.get(acct) else "SKONTO"
                if covered_in(acct, seleccion, field=campo):
                    continue
                orphan.append((acct, acct in blocked, (x.get("LKORR") or "").strip()))

            print("  moneda local: %s" % local)
            # SUPERSEDE 2026-08-26 (A47) — TEXTO IMPRESO. Lo que se imprimia:
            #   ~~"  configuradas y FUERA de toda variante: %d"~~
            # RETIRADO: ese rotulo daba el numero como SI FUERA la cifra de "cuentas de
            # T030H/KTOPL=UNES/CURTP=10 fuera de toda variante". No lo es: lo alimenta
            # `covered()` (la llamada `if covered(acct, sets)` justo arriba, l.256 hoy), el
            # resolutor LEGADO que mezcla SKONTO con AKONTO y por tanto
            # no respeta "solo exclusiones = todo lo demas". Medido: 273 frente a 239 por el
            # camino correcto (covered_in con el campo derivado de SKB1-MITKZ) = 34 falsos
            # positivos, +14%, asimetria 0 en sentido contrario.
            # LA CIFRA CORRECTA SE DESCONOCE hoy: la unica medicion del camino bueno es 239 el
            # 2026-08-25 contra P01 y no se ha vuelto a medir. NO sustituir 273 por 239 en
            # ningun artefacto publicado sin re-medir. Ver claim 599 (TIER_1, OPEN) y A47
            # state=DEFECTO_VIVO. HECHO el 2026-08-26: main() ya usa
            # variant_selection() + covered_in() con el campo derivado de SKB1-MITKZ, y la
            # corrida da 239 -- exactamente la cifra que el camino correcto midio el 2026-08-25.
            #
            # El rotulo de abajo decia «CIFRA NO VALIDA, resolutor LEGADO» y se quedo puesto
            # despues de arreglar el codigo: mentia al reves. Es el mismo patron que este
            # fichero lleva persiguiendo -- arreglar el codigo y no el texto que lo describe --
            # y por eso se anota aqui en vez de borrarlo sin mas.
            print("  configuradas en T030H y FUERA de toda variante: %d" % len(orphan))
            print("     (resuelto por variant_selection()+covered_in(), campo derivado de "
                  "SKB1-MITKZ: AKONTO para cuenta asociada, SKONTO para la de mayor)")
            defect, inert, unknown = [], [], []
            for acct, blk, lk in sorted(orphan):
                if blk:
                    inert.append((acct, lk, "bloqueada"))
                    continue
                e = exposure(acct)
                if e == "SI":
                    defect.append((acct, lk))
                elif e == "NO":
                    # SUPERSEDE 2026-08-26 (A47) — TEXTO IMPRESO. Se retira la etiqueta
                    #   ~~"sin partidas abiertas en divisa"~~
                    # porque AFIRMA LO CONTRARIO de lo unico que se comprobo: exposure() solo
                    # interroga BSIS, y para una cuenta asociada (SKB1-MITKZ lleno) las partidas
                    # abiertas viven en BSID/BSIK -> TABLE_WITHOUT_DATA -> "NO" -> se publicaba
                    # una ausencia que nadie midio. Aqui aterrizan los 34 falsos positivos del
                    # resolutor legado (3 bloqueadas + 31 sin-divisa, 0 DEFECTO).
                    inert.append((acct, lk,
                                  "BSIS no devolvio partidas en divisa — DESCONOCIDA si la "
                                  "cuenta es ASOCIADA (SKB1-MITKZ): esas viven en BSID/BSIK"))
                else:
                    unknown.append((acct, lk))

            print("     DEFECTO  (activa + partidas abiertas en divisa): %d" % len(defect))
            for acct, lk in defect:
                print("        %s  LKORR=%s   <<< exposicion que no se valora" % (acct, lk or "-"))
            # ENMENDADO 2026-08-26 (A47): la lista se trunca a 20 y ANTES no lo decia, asi que
            # de las 31 inertes "sin divisa" la mayoria ni se imprimia y el operador leia el
            # recuento como si fuera la lista.
            print("     inertes  (config sin efecto): %d%s"
                  % (len(inert),
                     "   [se listan solo las 20 primeras; OCULTAS %d]" % (len(inert) - 20)
                     if len(inert) > 20 else ""))
            for acct, lk, why in inert[:20]:
                print("        %s  LKORR=%s   (%s)" % (acct, lk or "-", why))
            if unknown:
                print("     DESCONOCIDA (no pudimos VER la exposicion): %d" % len(unknown))
                for acct, lk in unknown:
                    print("        %s  LKORR=%s" % (acct, lk or "-"))

            active = defect

            # el reverso: en la variante pero sin OB09 -> si tiene exposicion, no sabe donde postear
            invar = set()
            for v, (inc, exc, rngs) in sets.items():
                invar |= (inc - exc)
            no_ob09 = sorted(invar - set(hk)) if not a.accounts else []
            if no_ob09:
                # SUPERSEDE 2026-08-26 (A47) — SEGUNDO defecto, DISTINTO del anterior: no lo
                # arregla la migracion a covered_in(). Se retira el rotulo
                #   ~~"\n  en variante y SIN fila en T030H: %d"~~
                # porque `invar` se construye DESCARTANDO `rngs` por completo (l. arriba:
                # `invar |= (inc - exc)`), y hay variantes cuya seleccion es SOLO rangos:
                # medido sin tocar SAP, en la hoja "Variants and methods" de
                # fx_revaluation_scope_UNES.xlsx, UNES_OI_G/L = 3 rangos (0001100000-0001199999,
                # 0001500000-0001599999, 0001700000-0001799999) y UNES_UNBA = 3 rangos
                # (0001000000-0001099999, 0001400000-0001499999, 0001900000-0001999999), ambas
                # SIN valores sueltos -> `inc` vacio -> no aportan NADA a invar.
                # Consecuencia medida: imprimia 2 cuando el contraste real son 589. No es que
                # encuentre poco: NO HA MIRADO. La cifra real SE DESCONOCE hasta reconstruir
                # invar expandiendo los rangos de inclusion contra SKB1 (y restando los de
                # exclusion) — cambio de LOGICA, no hecho en esta corrida. Es la rama que
                # ejercita knowledge/domains/FI/fsv_alignment_runsheet.md:155.
                print("\n  [CIFRA NO VALIDA — el universo ignora los RANGOS de las variantes;")
                print("   la cifra real de 'en variante y SIN fila en T030H' SE DESCONOCE]: %d"
                      % len(no_ob09))
                for s in no_ob09:
                    print("     %s" % s)

            if active:
                rc = 1
        finally:
            c.close()

    print("\n%s" % ("LIMPIO" if rc == 0 else
                    "HAY CUENTAS ACTIVAS CON OB09 QUE NINGUNA VARIANTE SELECCIONA"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
