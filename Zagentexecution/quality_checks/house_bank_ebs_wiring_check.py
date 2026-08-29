# -*- coding: utf-8 -*-
"""house_bank_ebs_wiring_check.py — ¿sigue CABLEADA al EBS cada cuenta de banco casa?

Cambiar el numero de cuenta de un banco casa (FI12) actualiza T012K y deja HUERFANA toda
configuracion cuya CLAVE sea ese numero. La que mata el extracto electronico es T028B
(asignar cuentas bancarias a tipos de operacion), cuya clave es BANKL + KTONR: si el
numero cambia, la fila deja de encontrarse y el fichero del banco NO se procesa.

Y no avisa nadie. La ficha del banco queda perfecta, el job sigue terminando en verde, y
el extracto simplemente deja de entrar. Se nota semanas despues, mirando un saldo.

Nace de INC-000013624 (s108): NTB02/EUR01 cambio de 11939389 a 18747647 el 17.08.2026;
T028B se quedo en 11939389 y el extracto se paro el 14.08 mientras las otras seis cuentas
de Northern Trust seguian entrando a diario.

Cuatro comprobaciones, y la tercera es la que nadie hace:

  A  CABLE ROTO     cuenta de T012K con clave de banco cuyo T028B no tiene su BANKN
  B  HUERFANA       fila de T028B cuyo KTONR no es el BANKN de NINGUNA cuenta viva
                    (= el rastro del cambio que no se barrio)
  C  CANAL MUERTO   cuenta que recibia extractos y lleva > N dias sin recibir, mientras
                    su SOCIEDAD si sigue recibiendo. Ese corte es el que distingue
                    "roto" de "esta cuenta no recibe extractos nunca"
  D  SIN MAYOR      cuenta cableada en T028B cuyo BNKKO no existe en T035D

Solo LECTURA. Por defecto P01.

Uso:
    python house_bank_ebs_wiring_check.py
    python house_bank_ebs_wiring_check.py --bukrs UNES --dias 10
    python house_bank_ebs_wiring_check.py --autotest
"""

QUALITY_CHECK = {
    "tier": "live",
    "sobre": "datos_sap",
    "needs": "rfc_p01",
    "what": "cada cuenta de banco casa sigue cableada al EBS: T028B por su numero ACTUAL, "
            "T035D por su clave corta, y su canal de extractos sigue vivo frente a sus hermanas",
    "args": "[--bukrs <soc>] [--dias N] [--system P01] [--autotest]",
}

import argparse
import collections
import datetime
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
sys.path.insert(0, HERE)
import _golden as _G  # noqa: E402


# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO --------------------------------
# 1. P01 RECHAZA ROWSKIPS ("ROWSKIPS requires GET_SORTED"). Se lee con ROWCOUNT=0 o nada.
# 2. RFC_READ_TABLE parte a los 512 bytes de linea: nunca mas de ~8 campos, y jamas un
#    CHAR(512) acompanado. Si hace falta un campo largo, se lee SOLO y con WHERE por su
#    clave -- emparejar dos lecturas por POSICION no da error, da un cero o un cruce falso.
# 3. Un blanco final no se puede distinguir del relleno en un CHAR: comparar SIEMPRE con
#    .strip() en los dos lados, o T012K.BANKN ('18747647          ') nunca casara con
#    T028B.KTONR ('18747647').


def rd(conn, tab, fields, where="", n=0):
    """Delega en el lector del Golden. La firma NO cambia a proposito: asi el port
    es cambiar DE DONDE se lee, no COMO se interpreta, y ni una llamada se toca."""
    return _G.rd(conn, tab, fields, where, n)


MARCAS_CIERRE = ("CLOSED", "CLOSE", "FERME", "CERRAD", "OBSOLET", "INACTIV",
                 "NOT USED", "DORMANT", "CANCEL")


def esta_cerrada(texto):
    """UNESCO marca las cuentas cerradas EN EL TEXTO de la cuenta (T012T-TEXT1), no con un
    indicador. Medido: 224 de las 411 cuentas de UNES llevan 'CLOSED' en el texto, con
    todas las variantes de guiones ('CLOSED-----UNESCO YAOUNDE'). Sin este corte, la
    puerta acusa de cable roto a cuentas que llevan anos cerradas -- 2 de sus 4 primeros
    hallazgos lo eran."""
    t = (texto or "").upper()
    return any(m in t for m in MARCAS_CIERRE)


def analizar(t012k, t012, t028b, t035d, ultimo_extracto, dias_umbral, hoy, n_extractos=None,
             textos=None, electronicas=None):
    """La DECISION, pura y sin SAP delante: se puede probar sin red.

    t012k  [{BUKRS,HBKID,HKTID,BANKN,BNKN2,HKONT}]
    t012   {(BUKRS,HBKID): BANKL}
    n_extractos {(BUKRS,HBKID,HKTID): cuantos extractos de historial}
    t028b  [{BANKL,KTONR,BNKKO,BUKRS}]
    t035d  {(BUKRS,DISKB)}
    ultimo_extracto {(BUKRS,HBKID,HKTID): 'AAAAMMDD'}
    """
    hallazgos = []
    n_extractos = n_extractos or {}
    textos = textos or {}
    electronicas = electronicas if electronicas is not None else None

    cable = {(r["BANKL"], r["KTONR"]) for r in t028b}
    bnkko = {(r["BANKL"], r["KTONR"]): r.get("BNKKO", "") for r in t028b}

    # numeros de cuenta VIVOS por clave de banco
    vivos = collections.defaultdict(set)
    for r in t012k:
        bl = t012.get((r["BUKRS"], r["HBKID"]), "")
        if bl:
            vivos[bl].add(r["BANKN"])

    # --- A. cable roto ---------------------------------------------------------
    for r in t012k:
        bl = t012.get((r["BUKRS"], r["HBKID"]), "")
        if not bl:
            continue
        # solo se exige cable a las cuentas que TIENEN o TUVIERON extracto: exigirselo a
        # todas inventaria un hueco en cuentas que nunca recibieron fichero (denominador)
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        if k not in ultimo_extracto:
            continue
        if esta_cerrada(textos.get(k, "")):
            continue   # cuenta cerrada: no se le exige cable
        # SOLO se le exige fila de T028B a las cuentas cuyo extracto es ELECTRONICO
        # (FEBKO.EFART='E'). Medido en BTE01 (Teheran): USD01 importo 116 extractos y IRR01
        # otros 156, los dos con EFART='M' (entrada manual por FF67) y SIN NINGUNA fila en
        # T028B. O sea que para el extracto manual esa fila no hace falta, y exigirsela
        # publica un defecto que no existe. Fue el primer falso positivo de esta puerta.
        if electronicas is not None and k not in electronicas:
            continue
        if (bl, r["BANKN"]) not in cable:
            otras = [k for k in cable if k[0] == bl]
            hallazgos.append({
                "clase": "A_CABLE_ROTO", "grave": True,
                "efart": "E",
                "cuenta": "%s/%s-%s" % (r["BUKRS"], r["HBKID"], r["HKTID"]),
                "detalle": "T012K.BANKN=%s pero no hay fila T028B para (%s, %s). "
                           "T028B de esa clave de banco tiene: %s"
                           % (r["BANKN"], bl, r["BANKN"], [x[1] for x in otras] or "NADA"),
                "texto": textos.get(k, ""),
            })

    # --- B. huerfanas ----------------------------------------------------------
    for r in t028b:
        if r["KTONR"] and r["KTONR"] not in vivos.get(r["BANKL"], set()):
            hallazgos.append({
                "clase": "B_HUERFANA", "grave": False,
                "cuenta": "%s / %s" % (r["BANKL"], r["KTONR"]),
                "detalle": "fila T028B -> %s cuyo numero de cuenta no es el de ninguna "
                           "cuenta viva de esa clave de banco (rastro de un cambio sin barrer)"
                           % r.get("BNKKO", ""),
            })

    # --- C. canal muerto -------------------------------------------------------
    # El corte por HERMANAS del mismo banco casa no vale: NTB02 solo tiene UNA cuenta con
    # extractos, asi que el caso real de INC-000013624 se escapaba entero. El corte que si
    # discrimina es contra la SOCIEDAD: si el flujo de la sociedad sigue vivo y esta cuenta
    # -- que venia recibiendo con regularidad -- lleva N dias muda, esta rota.
    #
    # Denominador declarado: solo se juzgan cuentas VIVAS en T012K con historial
    # (>= min_hist extractos). A una cuenta sin historial no se le puede exigir cadencia,
    # y a una cerrada no se le exige nada: por eso se pide que siga en T012K.
    # FECHAS BASURA: FEBKO trae extractos con AZDAT en el ano 2201/2203/2207/2208 -- un
    # 2022 mal tecleado. Sin este filtro, el maximo de la sociedad es el ano 2208 y las
    # 147 cuentas de UNES salen "66.265 dias mudas". El instrumento no daba error: daba
    # una respuesta segura y falsa, que es peor.
    min_hist = 10
    vivas = {(r["BUKRS"], r["HBKID"], r["HKTID"]) for r in t012k}
    limpio, basura = {}, []
    for k, d in ultimo_extracto.items():
        if d and d > hoy:
            basura.append((k, d))
        else:
            limpio[k] = d
    for k, d in basura:
        hallazgos.append({
            "clase": "E_FECHA_IMPOSIBLE", "grave": False,
            "cuenta": "%s/%s-%s" % k,
            "detalle": "FEBKO trae AZDAT=%s, posterior a hoy (%s): fecha mal tecleada en "
                       "el extracto. Envenena cualquier medida de 'ultimo extracto'." % (d, hoy),
        })
    ultimo_extracto = limpio
    max_soc = {}
    for (bu, hb, hk), d in ultimo_extracto.items():
        if d > max_soc.get(bu, ""):
            max_soc[bu] = d
    for k, d in ultimo_extracto.items():
        bu = k[0]
        if k not in vivas or not d or n_extractos.get(k, 0) < min_hist:
            continue
        if esta_cerrada(textos.get(k, "")):
            continue
        mejor = max_soc.get(bu, "")
        if not mejor:
            continue
        try:
            dd = (datetime.datetime.strptime(mejor, "%Y%m%d")
                  - datetime.datetime.strptime(d, "%Y%m%d")).days
        except ValueError:
            continue
        if dd > dias_umbral:
            # ALCANCE (regla del proyecto, s108): se persigue lo de 2025-2026. Un canal que
            # lleva mudo mas de 180 dias no es "se rompio": es una cuenta que se cerro y
            # nadie la dio de baja. Se reporta, pero no como fallo -- perseguirlo llena la
            # puerta de rojo permanente y esconde el caso vivo, que es lo unico accionable.
            reciente = dd <= 180
            hallazgos.append({
                "clase": "C_CANAL_MUERTO" if reciente else "C_MUDO_ANTIGUO_probable_cierre",
                "grave": reciente,
                "cuenta": "%s/%s-%s" % k,
                "detalle": "ultimo extracto %s (%d extractos de historial); la sociedad %s "
                           "siguio recibiendo hasta el %s — %d dias de silencio"
                           % (d, n_extractos.get(k, 0), bu, mejor, dd),
            })

    # --- D. sin cuenta de mayor ------------------------------------------------
    for r in t028b:
        bk = bnkko.get((r["BANKL"], r["KTONR"]), "")
        if bk and (r.get("BUKRS", ""), bk) not in t035d:
            # NO es un defecto probado: los BNKKO que fallan llevan GUION BAJO
            # (SOG01_EUR1) y T035D usa GUION (SOG01-EUR1). Y SOG01/EUR01 recibe extractos
            # a diario, luego o el guion bajo es otra clave legitima o T035D no es
            # obligatoria por esa via. Se reporta como SOSPECHA hasta confirmarlo leyendo
            # el estandar. Publicarlo como defecto seria medir la FORMA, no el EFECTO.
            hallazgos.append({
                "clase": "D_SOSPECHA_SIN_MAYOR", "grave": False,
                "cuenta": "%s / %s" % (r["BANKL"], r["KTONR"]),
                "detalle": "T028B apunta a BNKKO=%s y no hay fila T035D para (%s, %s). "
                           "SIN CONFIRMAR: puede ser el alias guion-bajo vs guion."
                           % (bk, r.get("BUKRS", ""), bk),
            })

    return hallazgos


# ---------------------------------------------------------------------------
def autotest():
    """El instrumento no esta terminado hasta que falla A PROPOSITO."""
    t012 = {("UNES", "NTB02"): "SP0000000MX7", ("UNES", "NTB01"): "SP0000000MXL"}
    t012k = [
        {"BUKRS": "UNES", "HBKID": "NTB02", "HKTID": "EUR01", "BANKN": "18747647", "BNKN2": "UNO18EUR"},
        {"BUKRS": "UNES", "HBKID": "NTB01", "HKTID": "USD01", "BANKN": "17-18205", "BNKN2": "UNO10USD"},
        {"BUKRS": "UNES", "HBKID": "NTB01", "HKTID": "USD02", "BANKN": "17-18206", "BNKN2": "UNO11USD"},
    ]
    t028b = [
        {"BANKL": "SP0000000MX7", "KTONR": "11939389", "BNKKO": "NTB02-EUR1", "BUKRS": "UNES"},
        {"BANKL": "SP0000000MXL", "KTONR": "17-18205", "BNKKO": "NTB01-USD1", "BUKRS": "UNES"},
        {"BANKL": "SP0000000MXL", "KTONR": "17-18206", "BNKKO": "NTB01-USD2", "BUKRS": "UNES"},
    ]
    t035d = {("UNES", "NTB02-EUR1"), ("UNES", "NTB01-USD1"), ("UNES", "NTB01-USD2")}
    ult = {("UNES", "NTB02", "EUR01"): "20260814",
           ("UNES", "NTB01", "USD01"): "20260827",
           ("UNES", "NTB01", "USD02"): "20260827"}

    nh = {("UNES", "NTB02", "EUR01"): 2233, ("UNES", "NTB01", "USD01"): 2995,
          ("UNES", "NTB01", "USD02"): 2995}
    h = analizar(t012k, t012, t028b, t035d, ult, 7, "20260828", nh)
    clases = collections.Counter(x["clase"] for x in h)
    print("CASO QUE DEBE FALLAR (el real de INC-000013624):", dict(clases))
    assert clases["A_CABLE_ROTO"] == 1, "no detecto el cable roto de NTB02/EUR01"
    assert clases["C_CANAL_MUERTO"] == 1, "no detecto que el canal lleva 13 dias mudo"
    assert clases["B_HUERFANA"] == 1, "no detecto la fila huerfana 11939389"
    assert any("NTB02" in x["cuenta"] for x in h if x["clase"] == "A_CABLE_ROTO")

    # ahora se ARREGLA y tiene que volver a verde
    t028b_fix = [{"BANKL": "SP0000000MX7", "KTONR": "18747647", "BNKKO": "NTB02-EUR1", "BUKRS": "UNES"}] \
        + [r for r in t028b if r["BANKL"] != "SP0000000MX7"]
    ult_fix = dict(ult)
    ult_fix[("UNES", "NTB02", "EUR01")] = "20260827"
    h2 = analizar(t012k, t012, t028b_fix, t035d, ult_fix, 7, "20260828", nh)
    print("CASO ARREGLADO:", dict(collections.Counter(x["clase"] for x in h2)) or "limpio")
    assert not h2, "arreglado y sigue dando hallazgos: %s" % h2

    # y un caso que NO debe disparar: una cuenta que nunca recibio extracto
    t012k_extra = t012k + [{"BUKRS": "UNES", "HBKID": "NTB02", "HKTID": "EUR02",
                            "BANKN": "17846293", "BNKN2": "UNO17"}]
    h3 = analizar(t012k_extra, t012, t028b_fix, t035d, ult_fix, 7, "20260828", nh)
    assert not any(x["clase"] == "A_CABLE_ROTO" for x in h3), \
        "inventa un cable roto en una cuenta que nunca recibio fichero (denominador)"
    print("CASO QUE NO DEBE DISPARAR (cuenta sin extractos): ok")

    # y el falso positivo REAL que cometio esta puerta: cuenta de extracto MANUAL sin
    # fila en T028B. Importa extractos igual; exigirsela publica un defecto inexistente.
    t012k_man = t012k + [{"BUKRS": "UNES", "HBKID": "BTE01", "HKTID": "USD01",
                          "BANKN": "0050070646", "BNKN2": ""}]
    t012_man = dict(t012)
    t012_man[("UNES", "BTE01")] = "IR000029"
    ult_man = dict(ult_fix); ult_man[("UNES", "BTE01", "USD01")] = "20251212"
    nh_man = dict(nh); nh_man[("UNES", "BTE01", "USD01")] = 116
    txt_man = {("UNES", "BTE01", "USD01"): "UNESCO TEHRAN - USD"}
    elec = {("UNES", "NTB02", "EUR01"), ("UNES", "NTB01", "USD01"), ("UNES", "NTB01", "USD02")}
    h4 = analizar(t012k_man, t012_man, t028b_fix, t035d, ult_man, 7, "20260828",
                  nh_man, txt_man, elec)
    assert not any(x["clase"] == "A_CABLE_ROTO" for x in h4),         "exige fila T028B a una cuenta de extracto MANUAL: %s" % h4
    print("CASO QUE NO DEBE DISPARAR (extracto MANUAL, EFART=M): ok")
    print("\nAUTOTEST OK")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bukrs", default="")
    ap.add_argument("--dias", type=int, default=7)
    ap.add_argument("--system", default="P01")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()

    if a.autotest:
        return autotest()

    # MINERIA -> GOLDEN, nunca P01. Un minero lee mucho y correlaciona; RFC solo deja
    # leer estrecho. Si falta dato, exige() se NIEGA y manda al paso de EXTRACCION.
    conn = _G.abrir()
    _SELLO = _G.exige(conn, ['FEBKO', 'T012', 'T012K', 'T012T', 'T028B', 'T035D'])
    # el SELLO dice DE QUE FOTO sale todo lo que este minero publique. Se imprime
    # y se mete en el limite de sus hallazgos: una conclusion sobre una foto vale,
    # lo que no vale es no decir de cuando es la foto.
    print(_SELLO)

    w = "BUKRS = '%s'" % a.bukrs if a.bukrs else ""
    t012k = rd(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BNKN2", "HKONT"], w)
    t012r = rd(conn, "T012", ["BUKRS", "HBKID", "BANKS", "BANKL"], w)
    t012 = {(r["BUKRS"], r["HBKID"]): r["BANKL"] for r in t012r}
    t028b = rd(conn, "T028B", ["BANKL", "KTONR", "VGTYP", "BNKKO", "BUKRS"], "")
    t035d = {(r["BUKRS"], r["DISKB"]) for r in rd(conn, "T035D", ["BUKRS", "DISKB", "BNKKO"], "")}

    feb = rd(conn, "FEBKO", ["BUKRS", "HBKID", "HKTID", "AZDAT", "EFART"],
             (w + " AND " if w else "") + "AZDAT >= '20250101'")
    efart = collections.defaultdict(set)
    ult, n_ext = {}, collections.Counter()
    for r in feb:
        k = (r["BUKRS"], r["HBKID"], r["HKTID"])
        n_ext[k] += 1
        efart[k].add(r.get("EFART", ""))
        if r["AZDAT"] and (k not in ult or r["AZDAT"] > ult[k]):
            ult[k] = r["AZDAT"]

    print("poblacion: %d cuentas T012K · %d bancos casa · %d filas T028B · "
          "%d claves T035D · %d cuentas con extractos" %
          (len(t012k), len(t012), len(t028b), len(t035d), len(ult)))

    hoy = datetime.datetime.now().strftime("%Y%m%d")
    txt = {(r["BUKRS"], r["HBKID"], r["HKTID"]): r["TEXT1"]
           for r in rd(conn, "T012T", ["BUKRS", "HBKID", "HKTID", "TEXT1"], "SPRAS = 'E'")}
    cerradas = sum(1 for v in txt.values() if esta_cerrada(v))
    print("textos de cuenta: %d · marcadas CERRADAS en el texto: %d (se excluyen)"
          % (len(txt), cerradas))
    elec = {k for k, v in efart.items() if "E" in v}
    print("cuentas con extracto ELECTRONICO (EFART=E): %d de %d con extractos "
          "(al resto no se le exige fila en T028B)" % (len(elec), len(ult)))
    h_ = analizar(t012k, t012, t028b, t035d, ult, a.dias, hoy, n_ext, txt, elec)

    por = collections.defaultdict(list)
    for x in h_:
        por[x["clase"]].append(x)
    for cl in ("A_CABLE_ROTO", "C_CANAL_MUERTO", "B_HUERFANA",
               "C_MUDO_ANTIGUO_probable_cierre", "D_SOSPECHA_SIN_MAYOR", "E_FECHA_IMPOSIBLE"):
        lst = por.get(cl, [])
        print("\n=== %s : %d ===" % (cl, len(lst)))
        for x in lst[:60]:
            print("   %-22s %s" % (x["cuenta"], x["detalle"]))
            if x.get("texto"):
                print("   %-22s   texto: %s" % ("", x["texto"]))
        if len(lst) > 60:
            print("   ... +%d" % (len(lst) - 60))


    # ---- LO QUE ESTE MINERO ENCUENTRA -------------------------------------------
    from _hallazgos import Hallazgos
    h = Hallazgos("house_bank_ebs_wiring_check",
                  denominador=("%d cuentas T012K; se excluyen las CERRADAS (marca CLOSED en "
                               "T012T-TEXT1: %d de %d con texto) y las de extracto MANUAL, que "
                               "no necesitan T028B" % (len(t012k), cerradas, len(txt))))
    rotos = [x for x in h_ if x["clase"] == "A_CABLE_ROTO"]
    if rotos:
        h.riesgo("Cuentas VIVAS con extracto electronico cuyo cableado T028B apunta a un numero "
                 "de cuenta que ya no existe: el extracto deja de entrar EN SILENCIO",
                 tamano="%d cuenta(s): %s" % (len(rotos), ", ".join(x["cuenta"] for x in rotos)),
                 evidencia="T028B no tiene fila para el BANKN actual de T012K",
                 limite="veo el cable roto, no si el banco sigue emitiendo el fichero",
                 accion="anadir la fila en V_T028B con el numero ACTUAL y transportar")
    huerf = [x for x in h_ if x["clase"] == "B_HUERFANA"]
    if huerf:
        h.oportunidad("Filas de T028B con numeros de cuenta que ya no son de ninguna cuenta "
                      "viva: el rastro acumulado de cambios que nadie barrio",
                      tamano="%d filas huerfanas de %d" % (len(huerf), len(t028b)),
                      evidencia="T028B.KTONR sin correspondencia en T012K.BANKN",
                      limite="no se si alguna se dejo a proposito como historico",
                      accion="borrar tras confirmar que su cuenta ya no recibe")
    mudos = [x for x in h_ if x["clase"] == "C_CANAL_MUERTO"]
    if mudos:
        h.desafio("Cuentas que recibian con regularidad y llevan dias mudas mientras su sociedad "
                  "sigue recibiendo: no se si el banco dejo de mandar o si nadie lo procesa",
                  tamano="%d cuenta(s): %s" % (len(mudos),
                                               "; ".join(x["cuenta"] for x in mudos[:6])),
                  evidencia="ultimo FEBKO.AZDAT frente al maximo de su sociedad",
                  limite="no puedo ver el directorio del banco desde aqui",
                  quien_puede_contestar="Tesoreria (BFM/MO) y el equipo de interfaces")
    h.emitir()

    graves = [x for x in h_ if x["grave"]]
    print("\n%s — %d hallazgos graves, %d informativos"
          % ("FALLO" if graves else "LIMPIO", len(graves), len(h_) - len(graves)))
    return 1 if graves else 0


if __name__ == "__main__":
    sys.exit(main())
