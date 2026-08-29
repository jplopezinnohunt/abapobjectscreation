# -*- coding: utf-8 -*-
"""Refresca FEBKO_2024_2026 en el Golden con el DELTA, sin borrar NADA.

POR QUE NO USA gold_refresh
    `refresh_pk_upsert` BORRA las claves que estan en el Golden y no vienen de la lectura de
    P01 (`gold_refresh.py:136-138`). Con un `where` acotado al hueco eso se llevaria por delante
    las 13.604 filas de 2024, y NO daria error: dejaria un Golden mas pequeno y nadie lo notaria.
    Aqui no hay ni un DELETE. Solo `INSERT OR REPLACE` por KUKEY.

EL TROCEADO DE CAMPOS
    FEBKO_2024_2026 tiene 62 columnas y 62 campos dan DATA_BUFFER_EXCEEDED, asi que se lee en
    trozos de 8 con KUKEY en cada uno y se cosen por KUKEY. ANCHO FIJO, medido una vez.

LOS DOS ERRORES DE ESTE FICHERO, ESCRITOS PARA QUE NADIE LOS REPITA
    1. `AZDAT <= '<ym>31'` construye el 31 de FEBRERO. SAP no puede convertir esa fecha y
       devuelve **SAPSQL_DATA_LOSS**, que suena a "dato demasiado ancho" y no lo es. Fallaron
       exactamente febrero, abril, junio, septiembre y noviembre -- los meses sin 31 dias. Yo
       lo diagnostique como un problema de ANCHO y monte un reintento adaptativo carisimo
       (releer el mes entero a anchos 19/9/4/2/1) para un defecto que estaba en mi literal.
       Un limite superior ABIERTO por el mes siguiente no puede construir una fecha invalida.
    2. `INSERT OR REPLACE` NO REEMPLAZA si la tabla no tiene restriccion de unicidad: APILA.
       Dejo 38.764 filas duplicadas byte a byte antes de que nadie lo notara, porque el total
       subia y eso parecia progreso. Ahora hay `ux_febko_kukey` UNIQUE sobre KUKEY.
    La leccion comun: los dos se veian como PROGRESO -- filas que suben, reintentos que
    "aguantan" -- y ninguno daba error.

POR QUE MES A MES
    El wrapper de P01 RECHAZA ROWSKIPS, asi que no hay paginacion: se acota por AZDAT. Un mes
    es un trozo comodo y ademas hace el progreso visible y reanudable.

LO QUE NO SE HACE, Y ES DELIBERADO
    No se cuenta primero contra P01 para "saber el hueco". Contar con RFC_READ_TABLE arrastra
    las filas -- el 2026-08-29 costo 61.769 filas por el cable saber UN numero. La propia
    lectura mide: cada mes reporta cuantas trajo, cuantas eran nuevas y cuantas ya estaban.
"""

import datetime
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "mcp-backend-server-python"))
DB = os.path.join(REPO, "Zagentexecution", "sap_data_extraction", "sqlite",
                  "p01_gold_master_data.db")
GOLD = "FEBKO_2024_2026"
SAP = "FEBKO"
DESDE = "202401"


def meses(desde, hasta):
    y, m = int(desde[:4]), int(desde[4:])
    out = []
    while "%04d%02d" % (y, m) <= hasta:
        out.append("%04d%02d" % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def siguiente(ym):
    y, m = int(ym[:4]), int(ym[4:]) + 1
    return "%04d%02d" % (y + 1, 1) if m == 13 else "%04d%02d" % (y, m)


def leer(conn, campos, where):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=SAP, DELIMITER="|", ROWCOUNT=0,
                  OPTIONS=[{"TEXT": where}],
                  FIELDS=[{"FIELDNAME": f} for f in campos])
    return [dict(zip(campos, [c.strip() for c in x["WA"].split("|")])) for x in r["DATA"]]


MALOS = set()


def leer_troceado(conn, cols, where, ancho=8):
    """ANCHO FIJO 8, MEDIDO -- no adaptativo.

    ⛔ La version adaptativa (empezar en 20 y partir al fallar) releia el MES ENTERO a anchos
    19, 9, 4, 2 y 1 y se comio decenas de minutos sin escribir una fila -- persiguiendo un
    error que ni siquiera era de anchura. Con ancho 8 fijo, un mes son 5 SEGUNDOS y 8 lecturas.

    La leccion: mide el limite UNA VEZ y usa un parametro fijo. Un reintento adaptativo
    esconde su propio coste Y disfraza la causa real de bucle de rendimiento."""
    resto = [c for c in cols if c != "KUKEY"]
    filas = {}
    i = 0
    while i < len(resto):
        n = ancho - 1
        while n >= 1:
            trozo = ["KUKEY"] + resto[i:i + n]
            try:
                for r in leer(conn, trozo, where):
                    filas.setdefault(r["KUKEY"], {}).update(r)
                break
            except Exception as e:
                # Red de seguridad, no la via normal. OJO: SAPSQL_DATA_LOSS casi NUNCA es
                # anchura -- aqui era una FECHA INVALIDA en el where. Si aparece, sospecha
                # primero del filtro, no de los campos.
                if not any(k in str(e) for k in ("DATA_BUFFER_EXCEEDED", "SAPSQL_DATA_LOSS")):
                    raise
                if n == 1:
                    # el campo solo tampoco entra: se deja VACIO y se DICE cual es.
                    MALOS.add(trozo[-1])
                    break
                n = max(1, n // 2)
        i += n
    return filas


LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".escritor.lock")


def main():
    # UN SOLO ESCRITOR. Hoy corrieron DOS a la vez sobre esta tabla porque pregunte a la lista
    # de procesos si el primero seguia vivo y me dijo que no. Preguntar por el proxy en vez de
    # por el efecto. El fichero de bloqueo no opina: existe o no existe.
    if os.path.exists(LOCK):
        print("YA HAY UN ESCRITOR: %s\nSi sabes que murio, borra ese fichero." % LOCK)
        return 3
    open(LOCK, "w").write(str(os.getpid()))
    try:
        return _main()
    finally:
        os.remove(LOCK)


def _main():
    # --meses AAAAMM,AAAAMM  -> solo esos. Existe porque tras una corrida quedan REZAGADOS y
    # volver a leer los 32 meses para arreglar 11 es tirar lecturas contra P01 sin motivo.
    solo = set()
    if "--meses" in sys.argv:
        solo = set(sys.argv[sys.argv.index("--meses") + 1].split(","))
    from rfc_helpers import get_connection
    con = sqlite3.connect(DB)
    cols = [r[1] for r in con.execute("PRAGMA table_info([%s])" % GOLD)]
    assert "KUKEY" in cols, "sin KUKEY no hay clave para el upsert"
    ya = set(str(r[0]) for r in con.execute("SELECT KUKEY FROM [%s]" % GOLD))
    print("Golden ANTES: %d filas · %d columnas" % (len(ya), len(cols)))

    conn = get_connection("P01")
    print("P01 conectado (solo lectura). Delta mes a mes desde %s.\n" % DESDE)
    hasta = datetime.date.today().strftime("%Y%m")

    # ⛔ DELTA POR MARCA DE AGUA, no barrido. Antes se leian los 32 meses del rango para anadir
    # 41.466 filas de 60.453 leidas: dos tercios del trafico contra P01 sobraba. La marca va
    # sobre EDATE (fecha de ALTA), no sobre AZDAT: con AZDAT, un extracto de fecha vieja cargado
    # ayer quedaria por debajo de la marca y NO ENTRARIA NUNCA.
    if not solo:
        sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "quality_checks"))
        import _marca_agua as M                                        # noqa: E402
        m = M.leer(con, GOLD)
        if m:
            desde_marca = str(m["hasta"])[:6]
            print("marca de agua: %s <= %s (%s). Solo desde ahi." % (m["campo_marca"],
                                                                     m["hasta"], m["cuando"]))
            solo = set(meses(desde_marca, hasta))
        else:
            print("SIN marca de agua: esta corrida es un BARRIDO completo, y se dice.")
    tot_new = tot_upd = tot_leidas = 0
    fallidos = []
    ph = ",".join("?" * len(cols))
    for ym in meses(DESDE, hasta):
        if solo and ym not in solo:
            continue
        # ⛔ EL '31' ERA EL BUG, y costo horas. `AZDAT <= '20240231'` es el 31 de FEBRERO:
        # SAP no puede convertir esa fecha y devuelve SAPSQL_DATA_LOSS. Los 13 meses que
        # "fallaron" fueron febrero, abril, junio, septiembre y noviembre -- los que no tienen
        # 31 dias. Yo lo lei como un problema de ANCHO DE FILA y monte un reintento adaptativo
        # carisimo para un defecto que estaba en mi propio literal. Limite ABIERTO por el mes
        # siguiente: nunca se construye una fecha que pueda no existir.
        w = "AZDAT >= '%s01' AND AZDAT < '%s01'" % (ym, siguiente(ym))
        try:
            filas = leer_troceado(conn, cols, w)
        except Exception as e:
            print("  %s  ERROR: %s" % (ym, str(e).split("\n")[0][:90]))
            fallidos.append(ym)
            continue
        if not filas:
            print("  %s  —" % ym)
            continue
        nuevas = [k for k in filas if k not in ya]
        con.executemany("INSERT OR REPLACE INTO [%s] VALUES (%s)" % (GOLD, ph),
                        [tuple(f.get(c, "") for c in cols) for f in filas.values()])
        con.commit()
        ya |= set(filas)
        tot_leidas += len(filas)
        tot_new += len(nuevas)
        tot_upd += len(filas) - len(nuevas)
        print("  %s  leidas %5d · NUEVAS %5d · ya estaban %5d" % (ym, len(filas), len(nuevas),
                                                                  len(filas) - len(nuevas)))
    fin = con.execute("SELECT COUNT(*) FROM [%s]" % GOLD).fetchone()[0]
    print("\n%s" % ("=" * 70))
    print("leidas de P01: %d · NUEVAS: %d · refrescadas: %d" % (tot_leidas, tot_new, tot_upd))
    print("Golden: %d -> %d filas   (ni un DELETE)" % (len(ya) - tot_new, fin))
    print(con.execute("SELECT MIN(AZDAT),MAX(AZDAT) FROM [%s]" % GOLD).fetchone())
    # La marca se escribe DESPUES del commit del dato y SOLO si no fallo ningun mes: marcarla
    # antes, o con huecos, congela un agujero que ningun delta posterior vuelve a mirar.
    if not fallidos:
        sys.path.insert(0, os.path.join(REPO, "Zagentexecution", "quality_checks"))
        import _marca_agua as M                                        # noqa: E402
        tope = M.desde_el_dato(con, GOLD, "EDATE")
        if tope:
            M.escribir(con, GOLD, "EDATE", tope,
                       con.execute("SELECT COUNT(*) FROM [%s]" % GOLD).fetchone()[0],
                       nota="delta por EDATE (fecha de alta), no por AZDAT")
            print("marca de agua actualizada: EDATE <= %s" % tope)
    con.close()
    if MALOS:
        print("\nCOLUMNAS QUE NO SE PUDIERON LEER (quedan VACIAS, y se dice cuales): %s"
              % ", ".join(sorted(MALOS)))
    if fallidos:
        # EXIT != 0. La primera version salio con 0 sin haber entrado 13 MESES, y esos meses
        # conservan sus filas viejas: PARECEN llenos. Un mes que no entra se ve igual que un
        # mes al dia si nadie lo dice. No es dato PERDIDO -- es dato PENDIENTE DE REFRESCAR.
        print("\nMESES QUE NO ENTRARON — %d: %s" % (len(fallidos), " ".join(fallidos)))
        print("  Conservan sus filas VIEJAS: no es dato perdido, es dato pendiente de refrescar,")
        print("  pero PARECEN al dia y no lo estan.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
