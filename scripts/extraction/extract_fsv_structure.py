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
        if ya_esta_en_el_gold(con, "E071", minimo=100):
            con.close()
            return 0
        todas, vistos = [], set()
        for sis in ("D01K", "V01K", "P01K", "SAPK", "E01K", "Q01K"):
            r = read_p01(g, "E071", campos, where=f"TRKORR LIKE '{sis}%'")
            nuevos = [x for x in r if x.get("TRKORR", "") + x.get("AS4POS", "") not in vistos]
            for x in nuevos:
                vistos.add(x.get("TRKORR", "") + x.get("AS4POS", ""))
            todas.extend(nuevos)
            print(f"  {sis}*  {len(nuevos):>7,} objetos")
        if todas:
            n = guardar(con, "E071", campos, todas)
            print(f"  -> e071: {n:,} objetos en "
                  f"{len({x['TRKORR'] for x in todas}):,} transportes")
            top = con.execute("""SELECT OBJECT, COUNT(*) FROM e071
                                 GROUP BY 1 ORDER BY 2 DESC LIMIT 8""").fetchall()
            print("     que viaja mas:", ", ".join(f"{o}:{c:,}" for o, c in top))
        else:
            print("  0 filas -- no se toca el Gold")

    con.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
