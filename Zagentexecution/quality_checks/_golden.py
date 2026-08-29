# -*- coding: utf-8 -*-
"""_golden.py — de donde LEE un minero: del Golden, nunca de P01.

LA SEPARACION QUE HACE POSIBLE LA MINERIA (JP, 2026-08-29)

    EXTRACCION = un paso que ACTUALIZA datos, P01 -> Golden. Estrecho y planificado.
    MINERIA    = leer MUCHO y CORRELACIONAR: todas las tablas, todos los periodos.
    AD-HOC     = una pregunta puntual o un incidente. AHI SI se lee P01 directo, estrecho, y
                 luego se DECIDE si merece guardarse en el Golden.

    LA SECUENCIA para mineria: primero GOLDEN -> si el analisis necesita mas dato, se ACTUALIZA
    el Golden -> y ENTONCES se corren los mineros. La actualizacion es un paso con nombre propio
    en medio, no un atajo que el minero toma por su cuenta.

    Y la pregunta que separa ad-hoc de mineria: ¿es UNA pregunta estrecha, o una correlacion
    sobre una POBLACION? Si vas a publicar un numero sobre una poblacion, es mineria.

    Un minero contra P01 es un ERROR DE CATEGORIA. RFC solo deja leer estrecho -- 8 campos por
    `RFC_READ_TABLE`, sin `ROWSKIPS`, buffer de 512 bytes -- asi que un minero que lee P01 sale
    lento, atado a la VPN y **estructuralmente incapaz de correlacionar**. Para eso se saco la
    data.

    Medido el 2026-08-29: de 118 instrumentos que leen datos SAP, 24 van a P01 en vivo. La capa
    de mineria vieja estaba BIEN (`process_mining/`: 24 contra Golden, 3 contra P01). El defecto
    estaba concentrado en los 7 mineros de banca de s108/s109: 7 de 7 contra P01.

LA REGLA DURA: SI FALTA DATO, ES UN PASO DE EXTRACCION

    Este modulo NO se cae a P01 "solo por esta vez". Un fallback reintroduce el problema Y lo
    esconde. Cuando una tabla falta o esta CORTA, `exige()` se niega en voz alta y nombra el
    comando de extraccion. Un minero que lee una tabla truncada publica un numero pequeno como
    si fuera la poblacion entera: es el DENOMINADOR INCOMPLETO, el modo de fallo mas caro y mas
    repetido de este proyecto.

Y NUNCA SE CUENTA ARRASTRANDO FILAS
    El mismo dia, para saber cuantas filas tenia FEBKO en P01, se corrio `RFC_READ_TABLE` con
    `ROWCOUNT=0`: **61.769 filas por el cable para aprender UN numero**. RFC_READ_TABLE no sabe
    contar. Sobre REGUH (3,7 M) habria sido mucho peor. La cobertura se DECLARA en
    `brain_v2/gold_coverage.json` con su fecha, no se recalcula contra produccion.
"""

import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
COBERTURA = os.path.join(REPO, "brain_v2", "gold_coverage.json")

# El nombre logico NO es el nombre fisico, y adivinarlo da un cero silencioso. Cada eleccion
# lleva su porque: elegir mal aqui no da error, da una poblacion mas pequena.
TABLA = {
    "FEBKO": ("FEBKO_2024_2026", "la tabla `FEBKO` a secas del Golden son 50.000 filas -- un tope "
                                 "de ROWCOUNT, no una poblacion -- y ni siquiera tiene AZDAT"),
    "FEBEP": ("FEBEP_2024_2026", "igual: `FEBEP` a secas son 50.000 exactas = truncada"),
    "GLT0": ("glt0_p01", "en el Golden va en minusculas y con sufijo de sistema"),
    "FAGL_011ZC": ("fagl_011zc", "en minusculas"),
    "BKPF": ("bkpf", "en minusculas"),
    "REGUP": ("REGUP_SCENARIOS", "AVISO: es un SUBCONJUNTO por escenarios, no REGUP entero. "
                                 "Quien lo use para atribuir facturas debe decirlo en su limite"),
}


def abrir():
    """Solo lectura. Si alguien escribe en el Golden desde un minero, es otro defecto."""
    if not os.path.exists(DB):
        raise SystemExit("no existe el Golden: %s" % DB)
    return sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)


def fisica(tab):
    return TABLA.get(tab, (tab, ""))[0]


def _cols(g, t):
    return [r[1] for r in g.execute("PRAGMA table_info([%s])" % t)]


def rd(g, tab, fields, where="", n=0):
    """MISMA FORMA que el `rd()` de RFC que traian los mineros: lista de dicts, valores str.

    Asi el port de un minero es cambiar de donde lee, no como interpreta. El `where` que
    escribian para OpenSQL (`BUKRS = 'UNES'`, `AZDAT >= '20250101'`) vale tal cual en SQLite.
    """
    t = fisica(tab)
    hay = set(_cols(g, t))
    if not hay:
        raise KeyError("el Golden no tiene la tabla %s (fisica: %s). Eso es un PASO DE "
                       "EXTRACCION, no una lectura a P01." % (tab, t))
    faltan = [f for f in fields if f not in hay]
    if faltan:
        raise KeyError("%s en el Golden no tiene %s. Eso es un PASO DE EXTRACCION (ampliar los "
                       "campos extraidos), no una lectura a P01." % (t, ", ".join(faltan)))
    sql = "SELECT %s FROM [%s]" % (", ".join("[%s]" % f for f in fields), t)
    if where:
        sql += " WHERE " + where
    if n:
        sql += " LIMIT %d" % n
    return [dict(zip(fields, ["" if v is None else str(v).strip() for v in row]))
            for row in g.execute(sql)]


def cobertura():
    try:
        with open(COBERTURA, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def exige(g, tablas, umbral=0.95):
    """Devuelve el SELLO de la foto. Se niega solo cuando la foto es DESCONOCIDA.

    ⛔ ESTE ERA MAS DURO Y ESTABA MAL (JP, 2026-08-29). Se negaba en cuanto una tabla bajaba
    del 95%, como si una foto parcial invalidara la conclusion. No la invalida: **el Golden es
    una FOTO DE UN MOMENTO**, se toma para llegar a una conclusion, y salvo que necesitemos
    mas, la conclusion vale -- basta con decir de cuando es la foto y que abarca.

    Lo peligroso no es la foto PARCIAL: es la foto DESCONOCIDA, publicada como si fuera la
    poblacion entera. Por eso aqui solo se niega cuando la tabla falta o cuando nadie ha
    declarado su cobertura, y en los demas casos devuelve un sello que el minero DEBE meter en
    el `denominador` o el `limite` de lo que publique.
    """
    cob = cobertura().get("tablas", {})
    fallos, sello = [], []
    for tab in tablas:
        t = fisica(tab)
        if not _cols(g, t):
            fallos.append("%s (fisica %s) NO ESTA en el Golden" % (tab, t))
            continue
        c = cob.get(tab)
        if not c:
            # NO se niega: se SELLA como desconocida y se arrastra hasta lo publicado. Negarse
            # aqui bloquearia todo el trabajo por un hueco de contabilidad -- `_gold_sync_log`
            # solo fecha 34 de 384 objetos. La disciplina es el SELLO, no la negativa: lo que
            # no se puede es publicar sin decir de que foto sale.
            sello.append("%s FECHA DESCONOCIDA" % tab)
        elif c.get("pct", 0) < umbral * 100:
            sello.append("%s al %.1f%% (%s de %s, foto de %s)"
                         % (tab, c["pct"], c.get("golden"), c.get("p01"), c.get("medido")))
        else:
            sello.append("%s %.0f%% (foto de %s)" % (tab, c["pct"], c.get("medido")))
    if fallos:
        raise SystemExit(
            "\nNO SE SABE QUE FOTO ES ESTA — y sin eso no se publica. No es que el dato sea\n"
            "insuficiente: es que es DESCONOCIDO, y un numero sobre una poblacion desconocida\n"
            "se lee como si fuera la poblacion entera.\n\n  - "
            + "\n  - ".join(fallos)
            + "\n\n  LA SECUENCIA ES: primero GOLDEN -> si el analisis necesita mas dato, se\n"
              "  ACTUALIZA el Golden -> y ENTONCES se corren los mineros. Nunca minero -> P01.\n"
              "  La actualizacion es un paso con nombre propio en medio, no un atajo que el\n"
              "  minero toma por su cuenta.\n\n"
              "  Actualiza y vuelve:  python scripts/extraction/gold_refresh.py <dominio>\n")
    return "GOLDEN " + " · ".join(sello)
