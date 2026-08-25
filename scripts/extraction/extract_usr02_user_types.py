"""Trae USR02 de P01: EL TIPO DE USUARIO LO DECLARA SAP, no una heuristica nuestra.

POR QUE EXISTE
    Para saber que canales de escritura son tecnicos y cuales son personas se estaba usando una
    heuristica sobre el log: 'tiene logons de dialogo -> es persona'. Con eso BRIDGE-RFC,
    JOBBATCH y MULESOFT salian PERSONA. La segunda version usaba la PROPORCION de logons RFC
    contra dialogo, y seguia colocando JOBBATCH y WF-BATCH entre las personas.

    Las dos estaban adivinando algo que SAP ya dice: USR02-USTYP.
        A = Dialogo (una persona se sienta delante)
        B = Sistema (fondo/RFC; NO puede hacer logon de dialogo)
        C = Comunicacion (CPIC/RFC entre sistemas)
        S = Servicio (dialogo compartido, sin dueno)
        L = Referencia (solo para heredar permisos; no se puede usar para entrar)

    Con eso, la clase que de verdad importa deja de ser una impresion y pasa a ser medible:
    un usuario de tipo A -- una PERSONA -- por el que entra trafico RFC de escritura es el
    patron portal-as-user del hallazgo H71, y es un agujero de segregacion de funciones porque
    la comprobacion de autorizacion se hace contra la persona, no contra la aplicacion.

LO QUE NO TRAE, A PROPOSITO
    Ni nombres ni direcciones (USR21/ADRP). Para clasificar un canal hace falta el TIPO, no la
    identidad de nadie.

P01 es de SOLO LECTURA. Esto lee y nada mas.
Uso:  python scripts/extraction/extract_usr02_user_types.py
"""
import sys
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from gold_refresh import GOLD, read_p01, get_connection  # type: ignore

CAMPOS = ["BNAME", "USTYP", "CLASS", "ERDAT", "TRDAT", "UFLAG", "GLTGV", "GLTGB"]
SIGNIFICADO = {
    "A": "Dialogo - una PERSONA",
    "B": "Sistema - fondo/RFC, no puede entrar por dialogo",
    "C": "Comunicacion - CPIC/RFC entre sistemas",
    "S": "Servicio - dialogo compartido, sin dueno",
    "L": "Referencia - solo hereda permisos, no entra",
}


def main():
    g = get_connection()
    # De una sola lectura: 6.755 usuarios caben de sobra bajo el techo del wrapper.
    #
    # La primera version particionaba por la inicial del nombre y decia haber leido 13.511 --
    # el doble de los que hay. La causa: en SQL '_' es COMODIN DE UN CARACTER, asi que la
    # particion "BNAME LIKE '_%'" no leia los usuarios que empiezan por guion bajo, leia la
    # tabla ENTERA otra vez. El PRIMARY KEY lo absorbio y el numero impreso quedo mintiendo:
    # un recuento inflado que nadie habria vuelto a comprobar antes de citarlo.
    filas = read_p01(g, "USR02", CAMPOS)
    print(f"USR02: {len(filas):,} usuarios leidos de P01")
    if not filas:
        raise SystemExit("no se leyo nada de USR02 -- no se toca el Gold DB")

    con = sqlite3.connect(GOLD, timeout=600)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS usr02")
    cur.execute("CREATE TABLE usr02 (" + ", ".join(f'"{c}" TEXT' for c in CAMPOS) +
                ", PRIMARY KEY (BNAME))")
    cur.executemany(f"INSERT OR REPLACE INTO usr02 VALUES ({','.join('?' * len(CAMPOS))})",
                    [tuple(f.get(c, "") for c in CAMPOS) for f in filas])
    con.commit()

    print("\nreparto por tipo (lo que SAP declara):")
    for t, n in cur.execute("SELECT USTYP, COUNT(*) FROM usr02 GROUP BY 1 ORDER BY 2 DESC"):
        print(f"  {t or '(vacio)':2s}  {n:>6,}  {SIGNIFICADO.get(t, '?')}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
