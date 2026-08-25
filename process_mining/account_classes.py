"""A34 — DE QUE TIPO ES CADA CUENTA, segun la estructura de balance que se EJECUTA.

POR QUE EXISTE
    Saber que una cuenta es de BANCO, de DEPOSITO o de INVERSION decide cosas caras: si tiene
    que revaluar, si entra en el analisis de bancos, que control le toca al darla de alta. Ese
    conocimiento se derivaba EN VIVO dentro de `fsv_coverage_check.py` en cada corrida y no se
    guardaba, asi que tres analisis distintos lo re-derivaban cada uno por su cuenta -- o peor,
    lo adivinaban por el nombre de la cuenta.

⛔ LA TRAMPA QUE YA COSTO UNA MEDIDA ENTERA
    Una version de balance EXISTE para todas las sociedades y se EJECUTA para algunas. Barrer
    las 1.018 cuentas de UNES contra FS11 invento un hueco de 68 cuentas y 144 M EUR; contra
    FS10 -- la que UNES ejecuta de verdad -- son 4 cuentas y 0,01 EUR.

    **Quien sabe que version corre es la VARIANTE de RFBILA00 (parametro BILAVERS + SD_BUKRS),
    NUNCA T011.** Este minero no clasifica una cuenta contra una version que su sociedad no
    ejecuta, y cuando no puede saber cual ejecuta, lo DICE en vez de elegir una.

COMO CLASIFICA
    El nodo del balance (ERGSL) tiene un TEXTO, y ese texto es la unica declaracion de que es
    esa cuenta que existe en el sistema. No se adivina por el numero: se lee el nodo en el que
    cae, y si cae en varios se dicen todos.

Uso:  python process_mining/account_classes.py [--sociedad UNES]
Aterriza en: brain_v2/account_classes.json + publica en el bus
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SALIDA = REPO / "brain_v2" / "account_classes.json"
sys.path.insert(0, str(REPO / "process_mining"))
try:
    from metodo import lo_que_ya_aprendimos as _aprendido
except Exception:
    _aprendido = None

# TRES EJES, Y EN ESTE ORDEN DE AUTORIDAD.
#
#  1. DECLARADO_POR_SAP — un campo, no una interpretacion:
#       SKA1-XBILK  X = patrimonio · vacio = resultado   (el eje que yo intentaba deducir)
#       SKA1-KTOKS  grupo de cuentas: BANK · OTHR · P&L · COLL · UNDP
#       T012K.HKONT si la cuenta esta ahi, ES la contrapartida de una cuenta de banco casa.
#                   No es un indicio: es la configuracion que la hace serlo.
#  2. MEDIDO — el CONCEPTO: donde la pone el balance que su sociedad EJECUTA de verdad.
#  3. HEURISTICA — el patron sobre el texto libre. Se conserva, se etiqueta, y NUNCA es la
#     respuesta principal.
#
# ⛔ POR QUE ESTE ORDEN, MEDIDO EN ESTE MISMO FICHERO
#     La primera version clasificaba SOLO con el eje 3 y publicaba "1.418 cuentas de CAJA".
#     Falso: 1.278 de ellas son cuentas de BANCO. El patron de BANCO pedia el literal
#     "CASH AT BANK" y el texto real de UNESCO es "Cash with Banks" / "Cash on current & call
#     accounts", asi que caian en el patron de CAJA por la palabra "Cash". Del mismo modo
#     'Investment income' y 'Finance Revenue' -- que son RESULTADO -- salian como INVERSION.
#     Numeros plausibles, seguros y equivocados, que es la peor combinacion posible. El campo
#     KTOKS dice BANK para 918 cuentas sin que nadie tenga que interpretar nada.
CLASES = [
    ("BANCO", r"\bBANK|BANCO|CASH AT BANK|CUENTA CORRIENTE"),
    ("DEPOSITO", r"DEPOSIT|PLAZO|TERM DEP"),
    ("INVERSION", r"INVESTMENT|INVERSION|SECURIT|PORTFOLIO|FUND[S]? HELD"),
    ("CAJA", r"\bCASH\b|PETTY|CAJA"),
    ("DEUDOR", r"RECEIVABLE|DEUDOR|DEBTOR|A COBRAR"),
    ("ACREEDOR", r"PAYABLE|ACREEDOR|CREDITOR|A PAGAR"),
    ("ANTICIPO", r"ADVANCE|ANTICIPO|PREPAY"),
    ("PROVISION", r"PROVISION|RESERVE|ACCRUAL"),
]


def gold():
    from gold_ref import GOLD  # type: ignore
    return sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True, timeout=900)


def clase_del_nodo(texto):
    t = (texto or "").upper()
    for nombre, patron in CLASES:
        if re.search(patron, t):
            return nombre
    return None


def concepto_del_nodo(texto):
    """El texto del nodo, normalizado — y la normalizacion NO es cosmetica.

    Medido: la misma posicion se escribe distinto en versiones distintas ('Financial
    Contributions' vs 'Financial contributions', 'Other Contracts' vs 'Other contracts').
    Cualquier recuento que agrupe por la cadena cruda parte un concepto en dos y luego los
    presenta como dos cosas del negocio. Aqui se agrupa por el concepto normalizado y se
    conserva aparte la grafia literal de cada version.
    """
    return re.sub(r"\s+", " ", (texto or "").strip()).upper() or None


def versiones_que_se_ejecutan(con):
    """QUE VERSION CORRE CADA SOCIEDAD — de la VARIANTE, no de la configuracion.

    Sin esto no se puede clasificar: una cuenta que no cae en ninguna posicion de la version
    que su sociedad EJECUTA no esta fuera de la estructura, esta fuera de OTRA estructura.

    Aqui se lee lo que ya midio `fsv_coverage_check` si esta a mano; si no, se declara que no
    se sabe y NO se elige una version por defecto. Elegir la equivocada es el error de los
    144 M EUR.
    """
    p = REPO / "brain_v2" / "fsv_versions_in_use.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")), "medido de la variante de RFBILA00"
        except Exception:
            pass
    return {}, ("NO SE SABE que version ejecuta cada sociedad: hace falta leer la VARIANTE de "
                "RFBILA00 (BILAVERS + SD_BUKRS) en vivo. NO se elige una por defecto -- barrer "
                "contra la version equivocada invento un hueco de 144 M EUR")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sociedad", default=None)
    a = ap.parse_args()

    if _aprendido:
        _aprendido("balance", "cuenta", "variante", "bilavers").avisar()

    con = gold()

    # --- EJE 1: LO QUE SAP DECLARA -----------------------------------------------------
    # SKB1 es por sociedad y no lleva plan de cuentas; SKA1 es por plan. Se indexa por numero
    # de cuenta y se CONSERVA el plan, para que un mismo numero declarado distinto en dos
    # planes se vea en vez de que uno pise al otro en silencio.
    declarado = {}
    for ktopl, saknr, xbilk, ktoks in con.execute(
            "SELECT KTOPL, SAKNR, XBILK, KTOKS FROM p01_ska1"):
        k = (saknr or "").strip()
        d = {"plan": (ktopl or "").strip(),
             "patrimonio_o_resultado": "PATRIMONIO" if (xbilk or "").strip() == "X" else "RESULTADO",
             "grupo_de_cuentas": (ktoks or "").strip() or None}
        if k in declarado and declarado[k] != d:
            declarado[k]["_declarada_distinto_en_otro_plan"] = d
        else:
            declarado.setdefault(k, d)
    # T012K: estar aqui no es un indicio de ser cuenta de banco, es lo que la hace serlo
    banco_casa = {}
    for bukrs, hbkid, hktid, hkont in con.execute(
            "SELECT BUKRS, HBKID, HKTID, HKONT FROM t012k"):
        banco_casa.setdefault((hkont or "").strip().lstrip("0"), []).append(
            f"{(bukrs or '').strip()}/{(hbkid or '').strip()}/{(hktid or '').strip()}")

    try:
        intervalos = con.execute("""SELECT VERSN, ERGSL, VONKT, BISKT FROM fagl_011zc
                                    WHERE TRIM(COALESCE(VONKT,'')) <> ''""").fetchall()
    except sqlite3.Error:
        raise SystemExit("fagl_011zc no esta en el Gold: corre primero "
                         "scripts/extraction/extract_fsv_structure.py")
    textos = {}
    try:
        for v, e, t in con.execute("SELECT VERSN, ERGSL, TXT45 FROM fagl_011qt"):
            textos[(v, e)] = (t or "").strip()
    except sqlite3.Error:
        pass

    ejecuta, como = versiones_que_se_ejecutan(con)

    # Las cuentas reales, y de que sociedad
    try:
        cuentas = con.execute("""SELECT DISTINCT BUKRS, SAKNR FROM P01_SKB1
                                 WHERE TRIM(COALESCE(SAKNR,'')) <> ''""").fetchall()
    except sqlite3.Error:
        cuentas = con.execute("""SELECT DISTINCT BUKRS, SAKNR FROM SKB1
                                 WHERE TRIM(COALESCE(SAKNR,'')) <> ''""").fetchall()
    con.close()

    def pad(x):
        x = (x or "").strip()
        return x.zfill(10) if x.isdigit() else x

    porversion = defaultdict(list)
    for v, e, lo, hi in intervalos:
        porversion[v].append((pad(lo), pad(hi or lo), e))

    def versiones_de(bukrs):
        """Solo las que esta sociedad EJECUTA. Si no se sabe, TODAS y marcado."""
        v = ejecuta.get("sociedad_a_versiones", {}).get(bukrs) if ejecuta else None
        gen = ejecuta.get("sociedad_a_versiones", {}).get("(sin sociedad)", []) if ejecuta else []
        return sorted(set((v or []) + gen)) or None

    clasificadas, sin_nodo, grafias = {}, [], defaultdict(dict)
    for bukrs, saknr in cuentas:
        if a.sociedad and bukrs != a.sociedad:
            continue
        k = pad(saknr)
        suyas = versiones_de(bukrs)
        nodos = []
        for v, ivs in porversion.items():
            if suyas and v not in suyas:
                continue                      # esa estructura no la ejecuta: no la juzga
            for lo, hi, e in ivs:
                if lo <= k <= hi:
                    t = textos.get((v, e)) or ""
                    c = concepto_del_nodo(t)
                    if c:
                        grafias[c][v] = t          # grafia POR VERSION, no un conjunto plano
                    nodos.append({"version": v, "nodo": e, "texto": t, "concepto": c,
                                  "clase": clase_del_nodo(t)})
        if not nodos:
            sin_nodo.append({"cuenta": f"{bukrs}/{saknr}",
                             "versiones_que_ejecuta": suyas,
                             "_que_significa": ("no cae en ninguna posicion de la estructura que "
                                                "su sociedad ejecuta" if suyas else
                                                "no cae en ninguna posicion de NINGUNA version")})
            continue
        cls = [n["clase"] for n in nodos if n["clase"]]
        cps = [n["concepto"] for n in nodos if n["concepto"]]
        dec = declarado.get((saknr or "").strip(), {})
        hb = banco_casa.get((saknr or "").strip().lstrip("0"), [])
        heur = Counter(cls).most_common(1)[0][0] if cls else None

        # LA CLASE SE APOYA EN LO QUE SAP DECLARA. La heuristica solo habla cuando la
        # declaracion no distingue -- y entonces se dice que es una heuristica.
        if hb:
            clase, apoyo = "BANCO", "T012K"
        elif dec.get("grupo_de_cuentas") == "BANK":
            clase, apoyo = "BANCO", "KTOKS_BANK"
        elif dec.get("patrimonio_o_resultado") == "RESULTADO":
            clase, apoyo = None, "XBILK_RESULTADO"
        elif heur:
            clase, apoyo = heur, "HEURISTICA"
        elif dec.get("grupo_de_cuentas"):
            # NO es un hueco: SAP la declara patrimonial y de un grupo que simplemente no es
            # uno de los que deciden comportamiento. Son INTER-FUND BALANCES, NET ASSETS,
            # INVENTORIES, DEFERRED EXPENDITURES... perfectamente identificadas. Decir aqui
            # "sin declaracion" seria fabricar un hueco de 1.278 cuentas que no existe.
            clase, apoyo = None, "PATRIMONIO_OTRO_GRUPO"
        else:
            clase, apoyo = None, "SIN_APOYO"

        clasificadas[f"{bukrs}/{saknr}"] = {
            "sociedad": bukrs, "cuenta": saknr,
            "patrimonio_o_resultado": dec.get("patrimonio_o_resultado"),
            "grupo_de_cuentas": dec.get("grupo_de_cuentas"),
            "cuentas_de_banco_casa": hb or None,
            "concepto": Counter(cps).most_common(1)[0][0] if cps else None,
            "clase": clase,
            "_en_que_se_apoya_la_clase": apoyo,
            "_heuristica_decia": heur if heur != clase else None,
            "versiones_que_ejecuta": suyas,
            # SOLO version + nodo + concepto. El TEXTO y la CLASE se repetian aqui 8.781 veces
            # para 152 conceptos distintos y el store pesaba 9,9 MB -- tanto como el brain
            # entero. No se pierde nada: `por_concepto[c]` guarda la grafia POR VERSION y las
            # clases. Comprimir duplicacion no es comprimir conocimiento (CP-002).
            "nodos": [{"version": n["version"], "nodo": n["nodo"], "concepto": n["concepto"]}
                      for n in nodos[:6]],
            "_ojo_si_difiere": ("cae en clases distintas segun la version: solo vale la que su "
                               "sociedad EJECUTA") if len(set(cls)) > 1 else None,
        }

    # el mismo concepto escrito de dos maneras en versiones distintas
    drift = {c: sorted(set(g.values())) for c, g in grafias.items() if len(set(g.values())) > 1}

    # DONDE CAE CADA GRUPO DECLARADO, SIN VEREDICTO.
    #
    # La version anterior de esto llamaba "desacuerdo" a toda cuenta KTOKS=BANK cuyo concepto
    # no contuviera la subcadena "BANK", y publico 935. Eran FALSOS: todos colgaban de 'Cash on
    # current & call accounts', que es una posicion de banco escrita de otra manera. Decidir
    # "el balance no la pone en banco" comparando cadenas es el MISMO error que este fichero
    # acaba de corregir un nivel mas arriba, cometido en la comprobacion que iba a delatarlo.
    #
    # Asi que aqui no hay veredicto: se publica el cruce grupo-declarado x concepto y se deja
    # a la vista. Un humano ve en dos segundos si 'Cash in Hand' con KTOKS=BANK es un error;
    # una regex no.
    cruce = defaultdict(Counter)
    for v in clasificadas.values():
        if v["grupo_de_cuentas"] and v["concepto"]:
            cruce[v["grupo_de_cuentas"]][v["concepto"]] += 1

    # EL INDICE POR CONCEPTO — lo que hace este store RECORRIBLE.
    #
    # Colgar del grafo 8.781 claves 'sociedad/cuenta' no crea conocimiento navegable: crea
    # 8.781 nodos que nadie va a recorrer. Lo que SI es un concepto del negocio, y lo que
    # alguien preguntara, son las 152 POSICIONES del balance: "¿que es 'Field Office Imprest
    # Accounts', que cuentas cuelgan de ahi y como las declara SAP?". El detalle por cuenta se
    # queda en `cuentas` para el drill-down.
    por_concepto = {}
    for v in clasificadas.values():
        c = v["concepto"]
        if not c:
            continue
        d = por_concepto.setdefault(c, {
            "concepto": c, "cuentas": set(), "sociedades": set(), "versiones": set(),
            "grupos_declarados": Counter(), "clases": Counter(),
            "patrimonio_o_resultado": Counter(), "en_t012k": 0, "grafias": {}})
        d["cuentas"].add(v["cuenta"])
        d["sociedades"].add(v["sociedad"])
        d["grupos_declarados"][v["grupo_de_cuentas"]] += 1
        d["patrimonio_o_resultado"][v["patrimonio_o_resultado"]] += 1
        if v["clase"]:
            d["clases"][v["clase"]] += 1
        if v["cuentas_de_banco_casa"]:
            d["en_t012k"] += 1
        for n in v["nodos"]:
            d["versiones"].add(n["version"])
        # la grafia POR VERSION: es lo que hace recuperable que 'Financial Contributions' es
        # de FS10 y 'Financial contributions' de FS01. Sale de `grafias`, no de los nodos por
        # cuenta, que ya no llevan el texto repetido 8.781 veces.
        d["grafias"] = dict(grafias.get(c, {}))
    for c, d in por_concepto.items():
        for k in ("cuentas", "sociedades", "versiones"):
            d[k] = sorted(d[k]) if k != "cuentas" else len(d[k])
        d["cuentas_distintas"] = d.pop("cuentas")
        for k in ("grupos_declarados", "clases", "patrimonio_o_resultado"):
            d[k] = dict(d[k].most_common())
        d["_ojo"] = ("SAP no declara estas cuentas del grupo BANK aunque el balance las cuelgue "
                     "de una posicion de banco: un alcance por KTOKS=BANK las deja fuera"
                     ) if ("CASH" in c or "DEPOSIT" in c or "IMPREST" in c) and \
                          "BANK" not in d["grupos_declarados"] else None

    doc = {
        "_algoritmo": "A34_account_behaviour_classes",
        "_que_es": ("de que TIPO es cada cuenta segun el nodo del balance en el que cae, y por "
                    "tanto que comportamiento le toca"),
        "_LA_TRAMPA": (
            "una version de balance EXISTE para todas las sociedades y se EJECUTA para algunas. "
            "Barrer contra la equivocada invento un hueco de 68 cuentas y 144 M EUR; contra la "
            "que se ejecuta de verdad eran 4 cuentas y 0,01 EUR. Quien lo decide es la VARIANTE "
            "de RFBILA00 (BILAVERS + SD_BUKRS), NUNCA T011"),
        "_que_version_ejecuta_cada_sociedad": ejecuta or None,
        "_como_se_supo": como,
        "_la_clase_sale_del_TEXTO_del_nodo": (
            "no del numero de cuenta. El texto del nodo es la unica declaracion que existe en el "
            "sistema de que es esa cuenta; el numero solo dice donde la pusieron"),
        "_leyenda_de_en_que_se_apoya": {
            "_como_se_lee": ("cada cuenta lleva un CODIGO en `_en_que_se_apoya_la_clase`. Los que "
                             "empiezan por declaracion valen para decidir; HEURISTICA no"),
            "T012K": ("DECLARADO_POR_SAP -- la cuenta es contrapartida de una cuenta de banco "
                      "casa en T012K. No es un indicio: es lo que la hace serlo"),
            "KTOKS_BANK": "DECLARADO_POR_SAP -- SKA1-KTOKS = BANK",
            "XBILK_RESULTADO": ("DECLARADO_POR_SAP -- SKA1-XBILK vacio = cuenta de RESULTADO; la "
                                "clase de comportamiento solo aplica a patrimonio. Sin clase NO "
                                "es sin identificar: su identidad esta en el concepto"),
            "PATRIMONIO_OTRO_GRUPO": ("DECLARADO_POR_SAP -- patrimonio de un grupo que no decide "
                                      "comportamiento (OTHR, COLL). Tampoco es un hueco"),
            "HEURISTICA": ("patron sobre el texto libre del nodo. NO lo declara SAP: verificar "
                           "antes de decidir nada con esto"),
            "SIN_APOYO": "ni declaracion en SKA1 ni patron en el texto",
        },
        "_tres_ejes_por_orden_de_autoridad": {
            "1_DECLARADO_POR_SAP": ("SKA1-XBILK (patrimonio/resultado) · SKA1-KTOKS (grupo: BANK, "
                                    "OTHR, P&L, COLL, UNDP) · T012K.HKONT (la cuenta ES de banco "
                                    "casa, no lo parece)"),
            "2_MEDIDO": "el concepto: donde la pone el balance que su sociedad EJECUTA de verdad",
            "3_HEURISTICA": ("patron sobre el texto libre. Se conserva etiquetada y NUNCA es la "
                             "respuesta principal: clasificando solo con esto salieron 1.418 "
                             "cuentas de CAJA de las que 1.278 son de BANCO"),
        },
        "_donde_cae_cada_grupo_declarado": {
            "_que_es": ("cruce entre lo que SAP declara (SKA1-KTOKS) y donde lo pone el balance "
                        "ejecutado. SIN VEREDICTO a proposito"),
            "_por_que_sin_veredicto": (
                "la version anterior llamaba 'desacuerdo' a toda cuenta KTOKS=BANK cuyo concepto "
                "no contuviera la subcadena 'BANK', y publico 935. Eran falsos: colgaban de "
                "'Cash on current & call accounts', que es banco escrito de otra forma. Comparar "
                "cadenas para dictar un desacuerdo es el mismo error que este minero corrige"),
            "cruce": {g: dict(c.most_common(12)) for g, c in sorted(cruce.items())},
        },
        "versiones_en_la_estructura": sorted(porversion),
        "intervalos": len(intervalos),
        "cuentas_clasificadas": len(clasificadas),
        "cuentas_sin_nodo": len(sin_nodo),
        "_sin_nodo_no_es_un_error": (
            "no caer en ninguna posicion de la estructura que la sociedad EJECUTA es un hallazgo "
            "real (la cuenta cuelga de 'Not assigned' y el balance cuadra igual). No caer en una "
            "version que la sociedad no ejecuta no significa nada: por eso aqui solo se juzga "
            "contra las versiones que ejecuta, cuando se sabe cuales son"),
        "muestra_sin_nodo": sin_nodo[:20],
        "reparto_por_clase": dict(Counter(c["clase"] for c in clasificadas.values())),
        "reparto_por_concepto": dict(Counter(c["concepto"] for c in clasificadas.values())
                                     .most_common(40)),
        "conceptos_distintos": len({c["concepto"] for c in clasificadas.values() if c["concepto"]}),
        "_grafias_del_mismo_concepto": {
            "_que_es": ("la misma posicion escrita distinto en versiones distintas. Agrupar por "
                        "la cadena cruda parte un concepto en dos y los presenta como dos cosas "
                        "del negocio"),
            "cuantos": len(drift),
            "ejemplos": dict(list(drift.items())[:15]),
        },
        "por_concepto": por_concepto,
        "cuentas": clasificadas,
    }
    SALIDA.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        from mining_bus import publicar, preguntar
        for cl, n in doc["reparto_por_clase"].items():
            if cl:
                publicar("A34_account_behaviour_classes", "REALIDAD", f"CLASE:{cl}",
                         f"{n} cuenta(s) caen en un nodo de balance cuyo texto las declara {cl}",
                         evidencia="fagl_011zc x fagl_011qt x SKB1, Gold DB",
                         aspecto="clase_de_cuenta")
        if drift:
            publicar("A34_account_behaviour_classes", "DERIVA", "GRAFIA_DEL_MISMO_CONCEPTO",
                     f"{len(drift)} concepto(s) del balance se escriben de mas de una manera "
                     f"segun la version (p.ej. {list(drift)[0]}): agrupar por el texto crudo "
                     f"parte un concepto en dos",
                     evidencia="fagl_011qt, textos de nodo por version, Gold DB",
                     aspecto="clase_de_cuenta")
        if not ejecuta:
            preguntar("A34_account_behaviour_classes", "VERSION_QUE_SE_EJECUTA",
                      "¿que version de balance ejecuta cada sociedad? Sin eso no se puede decir "
                      "si una cuenta esta fuera de la estructura o fuera de OTRA estructura",
                      para="REALIDAD",
                      porque=("se lee de la VARIANTE de RFBILA00 (BILAVERS + SD_BUKRS) y este "
                              "minero solo tiene la configuracion, que no decide"))
    except Exception as e:
        print(f"  AVISO: no se pudo usar el bus ({type(e).__name__})")

    apoyos = Counter(v["_en_que_se_apoya_la_clase"] for v in clasificadas.values())
    print(f"\nCLASES DE CUENTA — {len(clasificadas):,} con concepto, de "
          f"{len(clasificadas) + len(sin_nodo):,}")
    print(f"  versiones en la estructura: {', '.join(sorted(porversion))}")
    print(f"  que version EJECUTA cada sociedad: {como[:88]}")
    print(f"  conceptos distintos declarados: {doc['conceptos_distintos']:,}")
    print("\n  EN QUE SE APOYA CADA CLASIFICACION:")
    for k, n in apoyos.most_common():
        print(f"    {k:22s} {n:>6,}")
    print("\n  reparto por clase:")
    for cl, n in sorted(doc["reparto_por_clase"].items(), key=lambda t: -t[1]):
        if cl:
            print(f"    {cl:14s} {n:>6,}")
    print(f"  sin clase (RESULTADO declarado por SAP): "
          f"{doc['reparto_por_clase'].get(None, 0):,}")
    print("\n  DONDE CAE CADA GRUPO DECLARADO (sin veredicto):")
    for g, c in sorted(cruce.items()):
        print(f"    {g:6s} -> " + " · ".join(f"{t.title()} {n:,}" for t, n in c.most_common(4)))
    print(f"\n  el mismo concepto con 2 grafias distintas: {len(drift):,}")
    print(f"  sin caer en ninguna posicion que su sociedad ejecute: {len(sin_nodo):,}")
    print(f"\n-> {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
