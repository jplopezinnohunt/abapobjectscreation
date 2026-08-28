# -*- coding: utf-8 -*-
"""bank_statement_channel_census.py — POR QUE CANAL entra el extracto de cada cuenta.

Nace de INC-000013624 (s108). Diagnosticando ese incidente se descubrio que el parque de
cuentas no es homogeneo y que NADIE lo tenia escrito: hay cuentas cuyo extracto entra
ELECTRONICO (fichero MT940 recogido por un job) y cuentas cuyo extracto lo TECLEA UNA
PERSONA en FF67. Se distinguen por `FEBKO.EFART` ('E' vs 'M').

La distincion no es un detalle tecnico: cambia QUE CONFIGURACION hace falta, QUE PUEDE
ROMPERSE, y sobre todo QUIEN SE ENTERA cuando deja de entrar.

  * ELECTRONICA  necesita fila en T028B con el numero de cuenta ACTUAL. Si el numero
                 cambia, deja de entrar en silencio (el incidente).
  * MANUAL       no necesita T028B -- medido: BTE01-USD01 importo 116 extractos sin esa
                 fila. Lo que necesita es que ALGUIEN LO TECLEE, y no hay ningun
                 mecanismo que avise cuando esa persona deja de hacerlo.

Ese segundo caso no tiene proceso definido y este censo es lo que lo hace visible.

Solo LECTURA. Por defecto P01.

Uso:
    python bank_statement_channel_census.py
    python bank_statement_channel_census.py --bukrs UNES --json salida.json
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",
    "needs": "rfc_p01",
    "what": "por que canal entra el extracto de cada cuenta de banco casa (electronico / manual / "
            "ninguno), con que cadencia y desde cuando esta callada",
    "args": "[--bukrs <soc>] [--system P01] [--json <fichero>]",
}

import argparse
import collections
import datetime
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))

MARCAS_CIERRE = ("CLOSED", "CLOSE", "FERME", "CERRAD", "OBSOLET", "INACTIV",
                 "NOT USED", "DORMANT", "CANCEL")


def esta_cerrada(t):
    return any(m in (t or "").upper() for m in MARCAS_CIERRE)


def rd(conn, tab, fields, where="", n=0):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|", ROWCOUNT=n,
                  OPTIONS=([{"TEXT": where}] if where else []),
                  FIELDS=[{"FIELDNAME": f} for f in fields])
    return [dict(zip(fields, [c.strip() for c in x["WA"].split("|")])) for x in r["DATA"]]


def _y(*cond):
    """Compone un WHERE sin dejar un AND colgando cuando una condicion viene vacia.
    Concatenar a pelo con un filtro vacio produce " AND X", que el parser de
    RFC_READ_TABLE rechaza -- y el sintoma (OPTION_NOT_VALID) no dice cual sobra."""
    return " AND ".join(c for c in cond if c)


def cadencia(fechas):
    """Dias medios entre extractos. Distingue una cuenta DIARIA de una MENSUAL, y por tanto
    cuanto silencio es normal en cada una. Sin esto, '30 dias mudo' es alarma en una y
    rutina en la otra."""
    f = sorted(set(x for x in fechas if x and len(x) == 8))
    if len(f) < 3:
        return None
    try:
        d = [datetime.datetime.strptime(x, "%Y%m%d") for x in f[-25:]]
    except ValueError:
        return None
    if len(d) < 3:
        return None
    huecos = [(d[i + 1] - d[i]).days for i in range(len(d) - 1)]
    huecos = [h for h in huecos if h > 0]
    return round(sum(huecos) / len(huecos), 1) if huecos else None


def etiqueta_cadencia(c):
    if c is None:
        return "?"
    if c <= 1.6:
        return "DIARIA"
    if c <= 9:
        return "SEMANAL"
    if c <= 45:
        return "MENSUAL"
    return "ESPORADICA"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="", help="vacio = TODAS las sociedades")
    ap.add_argument("--system", default="P01")
    ap.add_argument("--desde", default="20250101")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    from rfc_helpers import get_connection
    conn = get_connection(a.system)
    print("SID real: %s" % conn.sid_real)

    # ALCANCE: siempre 2025-2026 y siempre PARTIDO POR SOCIEDAD. Las dos cosas son
    # decisiones de metodo, no comodidad: mezclar sociedades esconde que cada una opera su
    # parque de bancos de forma distinta, y mirar mas atras de 2025 arrastra cuentas que ya
    # no existen y fechas basura (FEBKO tiene extractos con AZDAT en el ano 2207).
    w = ("BUKRS = '%s'" % a.bukrs) if a.bukrs else ""
    t012k = rd(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BNKN2", "WAERS", "HKONT"], w)
    t012 = {(r["BUKRS"], r["HBKID"]): r["BANKL"]
            for r in rd(conn, "T012", ["BUKRS", "HBKID", "BANKS", "BANKL"], w)}
    txt = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r["TEXT1"]
           for r in rd(conn, "T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"], _y(w, "SPRAS = 'E'"))}
    t028b = {(r["BANKL"], r["KTONR"]): r for r in
             rd(conn, "T028B", ["BANKL", "KTONR", "VGTYP", "BNKKO", "BUKRS"], "")}

    feb = rd(conn, "FEBKO", ["BUKRS", "HBKID", "HKTID", "AZDAT", "EFART", "VGTYP", "EUSER"],
             _y(w, "AZDAT >= '%s'" % a.desde))
    hoy = datetime.datetime.now().strftime("%Y%m%d")

    por = collections.defaultdict(lambda: {"n": 0, "efart": collections.Counter(),
                                           "vgtyp": collections.Counter(),
                                           "user": collections.Counter(), "fechas": []})
    for r in feb:
        if r["AZDAT"] > hoy:      # fechas imposibles: 2207/2208 existen en FEBKO
            continue
        e = por[(r["BUKRS"], r["HBKID"], r["HKTID"])]
        e["n"] += 1
        e["efart"][r["EFART"]] += 1
        e["vgtyp"][r["VGTYP"]] += 1
        e["user"][r["EUSER"]] += 1
        e["fechas"].append(r["AZDAT"])

    filas = []
    for r in t012k:
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        e = por.get(k)
        t = txt.get(k, "")
        bl = t012.get((r["BUKRS"], r["HBKID"]), "")
        if not e:
            canal = "SIN EXTRACTO"
        else:
            ee = e["efart"]
            canal = ("ELECTRONICO" if ee.get("E", 0) and not ee.get("M", 0)
                     else "MANUAL" if ee.get("M", 0) and not ee.get("E", 0)
                     else "MIXTO")
        ult = max(e["fechas"]) if e and e["fechas"] else ""
        cad = cadencia(e["fechas"]) if e else None
        mudo = None
        if ult:
            try:
                mudo = (datetime.datetime.strptime(hoy, "%Y%m%d")
                        - datetime.datetime.strptime(ult, "%Y%m%d")).days
            except ValueError:
                pass
        filas.append({
            "cuenta": "%s/%s-%s" % k, "texto": t, "cerrada": esta_cerrada(t),
            "canal": canal, "n": e["n"] if e else 0, "ultimo": ult,
            "dias_mudo": mudo, "cadencia_dias": cad, "ritmo": etiqueta_cadencia(cad),
            "vgtyp": (e["vgtyp"].most_common(1)[0][0] if e and e["vgtyp"] else ""),
            "quien": (e["user"].most_common(1)[0][0] if e and e["user"] else ""),
            # todos los que la han tecleado, no solo el dominante: publicar el dominante
            # SUBESTIMA -- medido en s108, los dominantes son 4 y el reparto real son 10
            "quienes": (sorted(e["user"]) if e else []),
            "pct_manual": (round(100.0 * e["efart"].get("M", 0) / max(1, e["n"])) if e else 0),
            # el CONTEO crudo, no el porcentaje: pct_manual esta REDONDEADO, asi que una
            # cuenta con 1 extracto tecleado entre 500 da 0 y desaparece del filtro. Es el
            # mismo cero silencioso de siempre -- no falla, resta poblacion.
            "n_manual": (e["efart"].get("M", 0) if e else 0),
            "bankn": r["BANKN"], "bankl": bl,
            "tiene_t028b": (bl, r["BANKN"]) in t028b,
        })

    for f in filas:
        f["bukrs"] = f["cuenta"].split("/")[0]
    vivas = [f for f in filas if not f["cerrada"]]
    print("\nventana %s -> hoy · %d cuentas · %d cerradas por texto · %d VIVAS"
          % (a.desde, len(filas), len(filas) - len(vivas), len(vivas)))

    # ---- OVERVIEW POR SOCIEDAD -------------------------------------------------
    # Partir por sociedad no es presentacion: cada sociedad opera su parque de bancos de
    # forma distinta, y el agregado esconde justo eso -- una sociedad que lo lleva TODO a
    # mano desaparece dentro de un total dominado por UNES.
    print("\n" + "=" * 78)
    print("COMO SE MANEJAN LOS EXTRACTOS, POR SOCIEDAD (solo cuentas VIVAS)")
    print("=" * 78)
    print("  %-6s %5s %5s %5s %5s %6s   %s" %
          ("soc", "ELEC", "MANU", "MIXT", "NADA", "vivas", "perfil"))
    socs = collections.defaultdict(collections.Counter)
    for f in vivas:
        socs[f["bukrs"]][f["canal"]] += 1
    for soc in sorted(socs, key=lambda x: -sum(socs[x].values())):
        cc = socs[soc]
        tot = sum(cc.values())
        con = cc["ELECTRONICO"] + cc["MANUAL"] + cc["MIXTO"]
        if con == 0:
            perfil = "no recibe extractos en SAP"
        elif cc["MANUAL"] + cc["MIXTO"] == 0:
            perfil = "todo automatico"
        elif cc["ELECTRONICO"] == 0:
            perfil = "TODO A MANO"
        else:
            perfil = "mixto: %d%% con intervencion manual" % round(
                100.0 * (cc["MANUAL"] + cc["MIXTO"]) / con)
        print("  %-6s %5d %5d %5d %5d %6d   %s" %
              (soc, cc["ELECTRONICO"], cc["MANUAL"], cc["MIXTO"], cc["SIN EXTRACTO"], tot, perfil))

    print("\n" + "=" * 78)
    print("CANAL DE ENTRADA — solo cuentas VIVAS")
    print("=" * 78)
    cnt = collections.Counter(f["canal"] for f in vivas)
    for k in ("ELECTRONICO", "MANUAL", "MIXTO", "SIN EXTRACTO"):
        if cnt.get(k):
            print("  %-14s %3d" % (k, cnt[k]))

    for canal in ("MANUAL", "MIXTO"):
        lst = sorted([f for f in vivas if f["canal"] == canal],
                     key=lambda x: (x["dias_mudo"] is None, -(x["dias_mudo"] or 0)))
        if not lst:
            continue
        print("\n" + "-" * 78)
        if canal == "MANUAL":
            print("MANUAL — TODO el extracto lo teclea una persona en FF67. NO necesita T028B.")
            print("La columna 'quien' es un USUARIO CON NOMBRE: si esa persona deja de hacerlo,")
            print("no hay nada que lo detecte. Ese es el proceso que falta.")
        else:
            print("MIXTO — entra por fichero pero ALGUIEN mete extractos a mano tambien.")
            print("Ojo: 'quien' aqui suele ser JOBBATCH, o sea que el grueso es automatico y lo")
            print("manual es la EXCEPCION (correccion, dia suelto). No confundir con MANUAL.")
            print("La columna %%man dice cuanto de esa cuenta va realmente a mano.")
        print("-" * 78)
        print("  %-22s %-9s %5s %5s %-11s %-9s %s"
              % ("cuenta", "ultimo", "n", "%man", "ritmo", "mudo", "quien"))
        for f in sorted(lst, key=lambda x: (x["bukrs"], -(x["dias_mudo"] or 0))):
            print("  %-22s %-9s %5d %4d%% %-11s %-9s %s"
                  % (f["cuenta"], f["ultimo"], f["n"], f["pct_manual"], f["ritmo"],
                     ("%d d" % f["dias_mudo"]) if f["dias_mudo"] is not None else "-", f["quien"]))

    lst = sorted([f for f in vivas if f["canal"] == "ELECTRONICO"],
                 key=lambda x: -(x["dias_mudo"] or 0))
    print("\n" + "-" * 78)
    print("ELECTRONICO — %d cuentas. Necesitan fila en T028B con el numero ACTUAL." % len(lst))
    print("-" * 78)
    rotas = [f for f in lst if not f["tiene_t028b"]]
    print("  sin fila T028B: %d %s" % (len(rotas), [f["cuenta"] for f in rotas] or ""))
    # Umbral: 3 veces su propio ritmo, con suelo de 7 dias. Con suelo de 14 el incidente se
    # escapaba por UN dia -- una cuenta DIARIA callada 14 dias ya es una alarma clara.
    mudas = [f for f in lst if (f["dias_mudo"] or 0) > max(7, 3 * (f["cadencia_dias"] or 5))]
    print("  mudas para su propio ritmo: %d" % len(mudas))
    for f in mudas[:20]:
        print("     %-22s ritmo=%-11s ultimo=%s (%d d)"
              % (f["cuenta"], f["ritmo"], f["ultimo"], f["dias_mudo"]))

    sin = [f for f in vivas if f["canal"] == "SIN EXTRACTO"]
    print("\n" + "-" * 78)
    print("SIN EXTRACTO — %d cuentas VIVAS que no han recibido NADA desde %s" % (len(sin), a.desde))
    print("-" * 78)
    print("  No es un defecto por si mismo: puede que ese banco no mande extracto. Pero nadie")
    print("  lo ha declarado nunca, asi que no se distingue 'no aplica' de 'se dejo de hacer'.")
    for f in sin[:25]:
        print("     %-22s %s" % (f["cuenta"], f["texto"]))
    if len(sin) > 25:
        print("     ... +%d" % (len(sin) - 25))


    # =================================================================================
    # LA BUSQUEDA. El censo de arriba son DATOS; esto es lo que el minero ENCUENTRA.
    # =================================================================================
    # Nadie esta mejor situado que este minero para verlo: es el unico que tiene delante,
    # a la vez, el canal de cada cuenta, su cadencia real y quien la sostiene.
    from _hallazgos import Hallazgos

    h = Hallazgos(
        "bank_statement_channel_census",
        denominador=("%d cuentas de banco casa; %d excluidas por llevar CLOSED en T012T-TEXT1 "
                     "(no hay campo de estado: es una convencion humana); quedan %d vivas"
                     % (len(filas), len(filas) - len(vivas), len(vivas))),
        ventana="%s -> hoy" % a.desde)

    # --- (1) EXISTE Y NO SE USA -------------------------------------------------------
    con_modelo_sin_usar = [f for f in vivas
                           if f["canal"] in ("MANUAL", "SIN EXTRACTO") and f["tiene_t028b"]]
    if con_modelo_sin_usar:
        man = [f for f in con_modelo_sin_usar if f["canal"] == "MANUAL"]
        h.oportunidad(
            "Hay cuentas con el modelo de extracto electronico YA MONTADO que no lo usan",
            tamano=("%d cuentas (%d se teclean a mano, %d no reciben nada), frente a %d que si "
                    "lo procesan electronicamente con ese mismo modelo"
                    % (len(con_modelo_sin_usar), len(man), len(con_modelo_sin_usar) - len(man),
                       sum(1 for f in vivas if f["canal"] in ("ELECTRONICO", "MIXTO")))),
            evidencia="T028B tiene fila para su BANKN actual y FEBKO.EFART no es 'E'",
            limite=("tener el modelo asignado NO prueba que el fichero pueda llegar: la "
                    "restriccion puede estar aguas arriba, en que el banco emita MT940"),
            accion="preguntar a esos bancos si emiten MT940 -- el coste en SAP es cero")

    # --- (2) SE MUEVE SIN SU CONTRAPARTE ----------------------------------------------
    # Lo que este minero PUEDE ver: cuentas vivas sin ningun extracto. Que ademas MUEVAN
    # saldo lo sabe bank_account_behaviour_signature, no yo -- y eso se declara.
    sin_nada = [f for f in vivas if f["canal"] == "SIN EXTRACTO"]
    if sin_nada:
        h.riesgo(
            "Cuentas VIVAS sin ningun extracto bancario: nada corrobora lo que el banco dice",
            tamano="%d cuentas vivas, %d de ellas de sociedades distintas de UNES"
                   % (len(sin_nada), sum(1 for f in sin_nada if f["bukrs"] != "UNES")),
            evidencia="cero cabeceras en FEBKO en toda la ventana",
            limite=("no se si MUEVEN dinero: eso lo mide bank_account_behaviour_signature. "
                    "Sin cruzarlo, esto es una lista, no un riesgo dimensionado"),
            accion="cruzar con behaviour_signature antes de escalar")

    # --- (6) LA MISMA PERSONA EN DOS ESLABONES ----------------------------------------
    # El canal MANUAL mete una PERSONA en el eslabon de entrada. El automatico no: es
    # JOBBATCH. Esa ausencia es lo que hace mas seguro el canal automatico, y es justo lo
    # que se pierde cuando una cuenta se teclea.
    # LA POBLACION NO ES "canal == MANUAL". Ese es el defecto de denominador que este
    # minero cometio y que un agente cazo cruzandolo: la etiqueta `canal` se deriva de que
    # EXISTAN extractos E y M, asi que una cuenta 97% tecleada a mano sale MIXTO y desaparece
    # del relato. Medido: por etiqueta salen 8 cuentas y 4 personas; la poblacion real de
    # "alguien teclea esto" son 39 cuentas (34 vivas) y 41 usuarios. Subestimaba 5-10x.
    # Quien necesita responsable y cadencia es TODA cuenta con al menos un extracto tecleado.
    manuales = [f for f in vivas if (f.get("n_manual") or 0) > 0]
    if manuales:
        # OJO: f["quien"] es el usuario DOMINANTE de cada cuenta, no todos los que la tocan.
        # Publicar ese recuento como "personas" SUBESTIMA -- medido en s108: los dominantes son
        # 4 y el reparto real son 10. Se cuenta sobre `can`, que tiene el detalle por usuario.
        personas = sorted({u for f in manuales for u in (f.get("quienes") or [])})
        dominantes = sorted({f["quien"] for f in manuales if f["quien"]})
        h.riesgo(
            "El extracto TECLEADO mete una persona en el eslabon de ENTRADA, donde el "
            "canal automatico no tiene ninguna (JOBBATCH)",
            tamano=("%d cuentas VIVAS reciben algun extracto tecleado (%d de ellas al "
                    "100%%) · %d usuarios con nombre lo hacen · las mas tecleadas: %s"
                    % (len(manuales), sum(1 for f in manuales if f.get("pct_manual") == 100),
                       len(personas),
                       ", ".join("%s %d%%" % (f["cuenta"], f["pct_manual"])
                                 for f in sorted(manuales, key=lambda x: -(x.get("pct_manual") or 0))[:5]))),
            evidencia="FEBKO.EUSER de esas cuentas",
            limite=("solo veo QUIEN teclea. Si esa misma persona ademas contabiliza o "
                    "compensa el documento resultante (BKPF.USNAM) o emite pagos (REGUH), "
                    "eso NO lo mide este minero"),
            accion="cruzar EUSER contra BKPF.USNAM y REGUH de la misma cuenta")

    # --- DESAFIOS: lo que no cuadra y no puedo cerrar yo ------------------------------
    mudas = [f for f in manuales if (f["dias_mudo"] or 0) > 60]
    if mudas:
        h.desafio(
            "Cuentas manuales que llevan meses sin extracto sin que nada lo detecte: no se si "
            "es un incumplimiento o si la cuenta dejo de usarse y nadie lo declaro",
            tamano="; ".join("%s %d dias" % (f["cuenta"], f["dias_mudo"]) for f in mudas),
            evidencia="ultimo FEBKO.AZDAT frente al ritmo propio de cada cuenta",
            limite=("NO existe en ninguna parte del sistema un responsable declarado ni una "
                    "cadencia esperada por cuenta. Se deduce del log, a posteriori"),
            quien_puede_contestar="Tesoreria (BFM/MO) y la oficina de terreno de cada cuenta")

    sin_texto = [f for f in vivas if f["canal"] == "SIN EXTRACTO" and not f["cerrada"]]
    if sin_texto:
        h.desafio(
            "No se puede distinguir 'este banco no manda extracto' de 'se dejo de hacer'",
            tamano="%d cuentas vivas sin extracto y sin declaracion de si les corresponde"
                   % len(sin_texto),
            evidencia="T012K vivas con cero FEBKO; la unica marca de estado es CLOSED en el texto",
            limite=("el formulario de alta YA pregunta '¿extracto electronico? si/no' y esa "
                    "respuesta no se guarda en ninguna parte del sistema"),
            quien_puede_contestar="Tesoreria: declarar por cuenta si se espera extracto y por que canal")

    h.emitir()

    if a.json:
        json.dump(filas, open(a.json, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("\nescrito %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
