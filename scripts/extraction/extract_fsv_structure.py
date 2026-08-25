"""Trae al Gold la ESTRUCTURA DE BALANCE y lo que un transporte CONTIENE.

POR QUE LAS DOS JUNTAS
    Las dos son capacidades REGISTRADAS cuyo store no existe, y las dos dependen de una
    conexion a P01 que hoy se ha caido dos veces. Cuando la conexion esta, se extrae.

QUE FALTA Y POR QUE IMPORTA

    FAGL_011ZC — los intervalos de cuenta de cada posicion del balance. Es lo que convierte una
    cuenta de mayor en un TIPO de cuenta (banco, deposito, inversion, deudor), y de ahi en un
    comportamiento esperado. Hoy `fsv_coverage_check.py` lo lee EN VIVO en cada corrida y no lo
    guarda, asi que la revaluacion FX, el analisis de bancos y el alta de maestros re-derivan
    cada uno lo mismo -- o peor, lo adivinan por el nombre de la cuenta.

    ⛔ Y la trampa que ya costo una medida entera: una version de balance EXISTE para todas las
    sociedades y se EJECUTA para algunas. Barrer las 1.018 cuentas de UNES contra FS11 invento
    un hueco de 68 cuentas y 144 M EUR; contra FS10 -- la que UNES ejecuta de verdad -- son 4
    cuentas y 0,01 EUR. Quien sabe que version corre es la VARIANTE de RFBILA00 (BILAVERS),
    NUNCA T011. Por eso se extrae tambien T011 pero se marca que no decide nada.

    E071 — el CONTENIDO de cada transporte: que objeto viaja en cual. En el Gold solo esta E070
    (las cabeceras, 20.915) y E07T (los textos). Sin E071 se sabe que hubo un transporte y no
    QUE se movio, que es la unica pregunta interesante: 15 scripts analizan transportes y solo
    uno esta registrado como algoritmo.

P01 es de SOLO LECTURA. Esto lee y nada mas.
Uso:  python scripts/extraction/extract_fsv_structure.py [--solo fsv|transportes]
"""
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from gold_refresh import GOLD, read_p01, get_connection  # type: ignore

TABLAS = {
    "FAGL_011ZC": (["VERSN", "ERGSL", "VONKT", "BISKT", "KTOPL"], None),
    "FAGL_011QT": (["VERSN", "ERGSL", "SPRAS", "TXT45"], "SPRAS = 'E'"),
    "T011": (["VERSN", "KTOPL", "XKONT"], None),
    "T011T": (["VERSN", "SPRAS", "TXT50"], "SPRAS = 'E'"),
}


def ya_esta_en_el_gold(con, nombre, minimo=1):
    """EL GOLD PRIMERO, Y COMPROBADO POR EL SCRIPT — no por quien lo lanza.

    La regla se cumplio hoy a mano antes de escribir esto, y cumplirla a mano es exactamente
    como se pierde: la proxima corrida no se acuerda. Ademas no basta con que la tabla EXISTA:
    `sapf100_varid` existe en el Gold con 21 filas y TODAS VACIAS, asi que el minero de
    variantes creia tener cobertura y leia el 100% por RFC. Una tabla vacia parece cobertura.
    Por eso se cuenta CONTENIDO, no filas.
    """
    try:
        n = con.execute(f"SELECT COUNT(*) FROM {nombre.lower()}").fetchone()[0]
    except sqlite3.Error:
        return False
    if n < minimo:
        return False
    # y que tenga contenido de verdad en su primera columna util
    try:
        cols = [c[1] for c in con.execute(f"PRAGMA table_info({nombre.lower()})")]
        util = cols[1] if len(cols) > 1 else cols[0]
        con_dato = con.execute(f"SELECT COUNT(*) FROM {nombre.lower()} "
                               f"WHERE TRIM(COALESCE([{util}],'')) <> ''").fetchone()[0]
    except sqlite3.Error:
        con_dato = n
    if con_dato < minimo:
        print(f"  {nombre:12s} existe con {n:,} filas pero SIN CONTENIDO: se re-extrae")
        return False
    print(f"  {nombre:12s} YA ESTA en el Gold ({con_dato:,} filas con dato) -- no se toca P01")
    return True


def guardar(con, nombre, campos, filas):
    cur = con.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {nombre.lower()}")
    cur.execute(f"CREATE TABLE {nombre.lower()} (" +
                ", ".join(f'"{c}" TEXT' for c in campos) + ")")
    cur.executemany(f"INSERT INTO {nombre.lower()} VALUES "
                    f"({','.join('?' * len(campos))})",
                    [tuple(f.get(c, "") for c in campos) for f in filas])
    con.commit()
    return cur.execute(f"SELECT COUNT(*) FROM {nombre.lower()}").fetchone()[0]


def main():
    solo = None
    if "--solo" in sys.argv:
        solo = sys.argv[sys.argv.index("--solo") + 1]

    g = get_connection()
    con = sqlite3.connect(GOLD, timeout=900)

    if solo in (None, "fsv"):
        print("=== ESTRUCTURA DE BALANCE ===")
        for t, (campos, where) in TABLAS.items():
            if ya_esta_en_el_gold(con, t):
                continue
            filas = read_p01(g, t, campos, where=where or "")
            if not filas:
                print(f"  {t:12s} 0 filas -- no se toca el Gold")
                continue
            n = guardar(con, t, campos, filas)
            print(f"  {t:12s} {n:>7,} filas")
        try:
            v = con.execute("SELECT COUNT(DISTINCT VERSN) FROM fagl_011zc").fetchone()[0]
            i = con.execute("SELECT COUNT(*) FROM fagl_011zc").fetchone()[0]
            print(f"  -> {v} version(es) de balance con {i:,} intervalos de cuenta")
            print("     OJO: que una version EXISTA no significa que se EJECUTE. Quien decide")
            print("     cual corre es la VARIANTE de RFBILA00 (BILAVERS), nunca T011.")
        except sqlite3.Error:
            pass

    if solo in (None, "transportes"):
        print("\n=== CONTENIDO DE LOS TRANSPORTES (E071) ===")
        # E071 es grande: se parte por la INICIAL del TRKORR, que es lo unico que la tabla
        # ofrece sin inventarse un criterio. Y '_' no se usa como comodin (leccion de USR02).
        campos = ["TRKORR", "AS4POS", "PGMID", "OBJECT", "OBJ_NAME", "OBJFUNC", "LOCKFLAG"]
        todas, vistos, incompletos = [], set(), []
        # LO QUE YA ESTA EN LA TABLA CUENTA COMO VISTO. Sin esto el completar DUPLICA: un
        # prefijo entra en la lista de pendientes si tiene UNA cabecera sin cubrir -- D01K
        # tenia 10 transportes vacios -- y entonces se re-pide el prefijo ENTERO. Medido:
        # anadio 2.136.494 filas repetidas y el numero de transportes no se movio, que es la
        # firma exacta de un duplicado y lo unico que lo delataba.
        try:
            for k in con.execute("SELECT TRKORR || AS4POS FROM e071"):
                vistos.add(k[0])
            print(f"  {len(vistos):,} objeto(s) ya en el Gold: no se vuelven a pedir")
        except sqlite3.Error:
            pass

        def traer(pref):
            """Trae un prefijo, y si el servidor se queda sin memoria PARTE y reintenta.

            Medido 2026-08-25: 'P01K%' devolvio 1.906.549 objetos y murio con
            TSV_TNEW_PAGE_ALLOC_FAILED. Sin esto el total sale como si fuera un recuento
            cuando es un SUELO -- y un suelo presentado como total es peor que no medir,
            porque nadie vuelve a mirarlo. Si ni partiendo entra, se DECLARA incompleto.
            """
            try:
                return read_p01(g, "E071", campos, where=f"TRKORR LIKE '{pref}%'")
            except Exception as e:
                # SOLO se parte cuando el servidor se queda sin memoria. Un prefijo vacio de
                # verdad (SAPK, E01K) devuelve [] y no hay nada que partir: recursar ahi
                # dispararia 36 consultas inutiles por cada prefijo que simplemente no existe.
                if "PAGE_ALLOC" not in str(e) and "memory" not in str(e).lower():
                    raise
            if len(pref) >= 10:
                incompletos.append(pref)
                print(f"  {pref}  NO ENTRA ni partido -- se declara INCOMPLETO")
                return []
            # LAS LETRAS POR LAS QUE PARTIR SE LEEN DE E070, NO SE ESCRIBEN A MANO.
            #
            # Medido 2026-08-25, y es mi propio fallo dos veces en el mismo fichero: partiendo
            # con un alfabeto '0-9A-Z' escrito a mano, los 5.455 transportes SAPK devolvieron
            # CERO -- se llaman 'SAPK-10001INIWPGW', con GUION en la quinta posicion, que no
            # estaba en el alfabeto. Cada subconsulta devolvia 0 legitimamente y el total se
            # reporto como exito. Leidos uno a uno tienen 713, 205, 393 objetos cada uno.
            siguientes = sorted({r[0] for r in con.execute(
                "SELECT DISTINCT SUBSTR(TRKORR,?,1) FROM e070 WHERE TRKORR LIKE ?",
                (len(pref) + 1, pref + "%")) if r[0]})
            if not siguientes:
                incompletos.append(pref)
                print(f"  {pref}* no cabe y E070 no dice por donde partirlo -- INCOMPLETO")
                return []
            print(f"  {pref}* no cabe de una: se parte en {len(siguientes)} "
                  f"({''.join(siguientes)[:40]})")
            out = []
            for c in siguientes:
                out.extend(traer(pref + c))
            if not out:
                # el padre fallo por memoria y las partes suman cero: eso no es 'no hay datos'
                incompletos.append(pref)
                print(f"  ⛔ {pref}*: fallo por memoria y las partes suman 0 -- INCOMPLETO")
            return out

        # LOS PREFIJOS SE LEEN DEL GOLD, NO SE ESCRIBEN A MANO.
        #
        # La primera version llevaba la lista codificada -- D01K, V01K, P01K, SAPK, E01K, Q01K --
        # y trajo 2,1 millones de objetos que parecian todo. No lo eran: E070 tiene cabeceras de
        # CIENTOS de prefijos (ICDK, DUBK, A01K, DF5K...) y ICDK900002 solo tiene 154 objetos que
        # nadie habria leido nunca. El limite era mi lista, no el sistema, y una lista a mano no
        # avisa de lo que se deja fuera. E070 ya esta en el Gold: que diga el que prefijos hay.
        try:
            todos = [r[0] for r in con.execute(
                "SELECT DISTINCT SUBSTR(TRKORR,1,4) FROM e070 ORDER BY 1") if r[0]]
            # y de esos, SOLO los que tienen alguna cabecera sin contenido leido: re-tirar
            # 1,9 millones de filas de P01 que ya estan en el Gold es exactamente lo que la
            # regla del Gold-primero existe para evitar.
            # ⛔ Y SOLO SE PIDE UN PREFIJO ENTERO SI NO HAY NADA SUYO EN LA TABLA.
            #
            # Aqui estaba la causa raiz del duplicado. Un prefijo entraba en pendientes si
            # tenia UNA cabecera sin cubrir, y entonces se pedia ENTERO. D01K tiene 10
            # transportes VACIOS -- cabecera sin objetos -- que no van a estar cubiertos nunca,
            # porque no hay nada que cubrir. Asi que D01K quedaba pendiente para siempre y cada
            # pase re-pedia sus 223.769 filas. Igual P01K con 1.906.549.
            #
            # Un prefijo del que ya hay algo NO se vuelve a pedir en bloque: lo que falte de
            # el se pide transporte a transporte, que es lo unico que no re-lee lo que ya esta.
            con_algo = {r[0] for r in con.execute(
                "SELECT DISTINCT SUBSTR(TRKORR,1,4) FROM e071") if r[0]}
            sin_contenido = [r[0] for r in con.execute(
                """SELECT DISTINCT SUBSTR(TRKORR,1,4) FROM e070
                   WHERE TRKORR NOT IN (SELECT TRKORR FROM e071) ORDER BY 1""") if r[0]]
            prefijos = [p for p in sin_contenido if p not in con_algo]
            sueltos = [r[0] for r in con.execute(
                """SELECT DISTINCT TRKORR FROM e070
                   WHERE TRKORR NOT IN (SELECT TRKORR FROM e071)
                     AND SUBSTR(TRKORR,1,4) IN (SELECT DISTINCT SUBSTR(TRKORR,1,4) FROM e071)
                   ORDER BY 1""")]
            print(f"  {len(todos)} prefijo(s) en E070 (derivados, no una lista a mano); "
                  f"{len(prefijos)} sin nada leido -- se piden en bloque; "
                  f"{len(sueltos)} transporte(s) sueltos de prefijos ya empezados")
        except sqlite3.Error:
            todos = prefijos = ["D01K", "V01K", "P01K", "Q01K"]
            print("  AVISO: E070 no esta en el Gold; se cae a los 4 prefijos propios y SE DECLARA")
            incompletos.append("prefijos-no-derivados-de-E070")

        for sis in prefijos:
            r = traer(sis)
            nuevos = [x for x in r if x.get("TRKORR", "") + x.get("AS4POS", "") not in vistos]
            for x in nuevos:
                vistos.add(x.get("TRKORR", "") + x.get("AS4POS", ""))
            todas.extend(nuevos)
            if nuevos:
                print(f"  {sis}*  {len(nuevos):>9,} objetos")

        # y los transportes sueltos, uno a uno. Muchos saldran VACIOS: una cabecera en E070 sin
        # ninguna fila en E071 es un transporte que se creo y no llego a llevar nada. Eso es un
        # hecho del sistema, no un fallo de lectura -- y hay que poder distinguirlos, que es lo
        # que la cobertura de mas abajo no sabia hacer.
        vacios_confirmados = []
        for t in sueltos:
            try:
                r = read_p01(g, "E071", campos, where=f"TRKORR = '{t}'")
            except Exception as e:
                incompletos.append(t)
                print(f"  {t}  ERR {str(e)[:60]}")
                continue
            if not r:
                vacios_confirmados.append(t)
                continue
            nuevos = [x for x in r if x.get("TRKORR", "") + x.get("AS4POS", "") not in vistos]
            for x in nuevos:
                vistos.add(x.get("TRKORR", "") + x.get("AS4POS", ""))
            todas.extend(nuevos)
        if vacios_confirmados:
            print(f"  {len(vacios_confirmados):,} transporte(s) leidos UNO A UNO y VACIOS de "
                  f"verdad: cabecera sin objetos, no un fallo de lectura")
        if todas:
            # AÑADIR, no rehacer: lo que ya se leyo se queda. `guardar` hace DROP, y usarlo aqui
            # tiraria millones de filas correctas para volver a pedirlas a P01.
            #
            # ⛔ TRES CIERRES, PORQUE ESTO YA METIO 2.136.494 FILAS REPETIDAS (2026-08-25):
            #   1. `vistos` se precarga de la tabla (arriba), no arranca vacio cada corrida.
            #   2. INSERT OR IGNORE sobre un indice UNICO (TRKORR, AS4POS): aunque el llamador
            #      se equivoque, la clave repetida no entra. La base defiende su propia clave.
            #   3. La asercion de abajo: si suben los OBJETOS y no suben los TRANSPORTES, es un
            #      duplicado. Esa fue la unica señal que hubo y no estaba comprobada por nadie.
            cur = con.cursor()
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_e071 ON e071(TRKORR, AS4POS)")
            obj_antes = cur.execute("SELECT COUNT(*) FROM e071").fetchone()[0]
            trs_antes = cur.execute("SELECT COUNT(DISTINCT TRKORR) FROM e071").fetchone()[0]
            cur.executemany(f"INSERT OR IGNORE INTO e071 VALUES "
                            f"({','.join('?' * len(campos))})",
                            [tuple(f.get(c, "") for c in campos) for f in todas])
            con.commit()
            n = cur.execute("SELECT COUNT(*) FROM e071").fetchone()[0]
            trs = {r[0] for r in con.execute("SELECT DISTINCT TRKORR FROM e071")}
            print(f"  +{n - obj_antes:,} objetos nuevos de {len(todas):,} leidos "
                  f"({len(todas) - (n - obj_antes):,} ya estaban)")
            if n > obj_antes and len(trs) == trs_antes:
                raise SystemExit(
                    f"⛔ PARADA: entraron {n - obj_antes:,} objetos y el numero de transportes "
                    f"no se movio ({trs_antes:,}). Eso es un duplicado, no un hallazgo. "
                    f"El Gold NO se deja asi -- revisa por que se volvio a pedir un prefijo "
                    f"que ya estaba entero.")
            print(f"  -> e071: {n:,} objetos en {len(trs):,} transportes")
            top = con.execute("""SELECT OBJECT, COUNT(*) FROM e071
                                 GROUP BY 1 ORDER BY 2 DESC LIMIT 8""").fetchall()
            print("     que viaja mas:", ", ".join(f"{o}:{c:,}" for o, c in top))

            # LA COBERTURA SE DECLARA, NO SE DA POR SUPUESTA. E070 ya esta en el Gold con las
            # CABECERAS: si E071 cubre menos transportes que cabeceras hay, la diferencia son
            # transportes de los que se sabe que existieron y no que movieron -- que es justo la
            # pregunta interesante. Callarlo hace que 2,1 millones de objetos parezcan "todo".
            try:
                cab = con.execute("SELECT COUNT(DISTINCT TRKORR) FROM e070").fetchone()[0]
                falt = con.execute("""SELECT COUNT(*) FROM (SELECT DISTINCT TRKORR FROM e070
                                      WHERE TRKORR NOT IN (SELECT TRKORR FROM e071))"""
                                   ).fetchone()[0]
                print(f"     COBERTURA: {len(trs):,} de {cab:,} transportes con cabecera en E070; "
                      f"{falt:,} sin contenido leido")
                if falt:
                    print("       (una cabecera sin objetos puede ser un transporte VACIO o uno "
                          "no leido: son cosas distintas y aqui NO se distinguen todavia)")
            except Exception as e:
                print(f"     no se pudo medir la cobertura contra E070: {type(e).__name__}")
            if incompletos:
                print(f"     ⛔ INCOMPLETO en {len(incompletos)} prefijo(s): {incompletos[:6]}")
        else:
            print("  0 filas -- no se toca el Gold")

    con.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
