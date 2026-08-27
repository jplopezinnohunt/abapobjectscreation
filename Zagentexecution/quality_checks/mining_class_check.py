"""
mining_class_check.py — un minero que no declara lo que mina no se puede encontrar.

QUE COMPRUEBA
    Que cada algoritmo declare las CLASES DE EXPLORACION que de verdad cubre. Deriva la clase de
    las SENALES de su propia definicion -- los FM que llama, las tablas que lee, lo que dice que
    hace -- y la compara con lo que declara en `tipo_mineria`.

POR QUE
    Medido el 2026-08-27: TRECE algoritmos leian programas, clases y tablas ABAP, repartidos en
    SEIS cajones distintos y CINCO sin clase ninguna. El hueco no era de ellos: faltaba la clase
    `CODIGO_COMO_FUENTE`. Se anadio, se reclasificaron los trece... y el problema volveria con el
    siguiente que se escriba. Esta puerta existe para que el proximo aterrice bien SIN que nadie
    se acuerde -- que es la diferencia entre una regla y un inventario.

COMO EVITA SER RUIDO (y esto importa mas que lo que detecta)
    Una clasificacion automatica que se equivoca entrena a ignorarla. Asi que:
      * cada clase se deriva de senales EXPLICITAS y estrechas, no de palabras sueltas;
      * hace falta que la senal aparezca en la DEFINICION del algoritmo, no en su prosa suelta;
      * PROPONE, no sentencia: sin `--fix` no escribe nada;
      * y un minero puede minar VARIAS cosas, asi que la clase se ANADE, nunca sustituye.

    El denominador se declara siempre: cuantos algoritmos se miran y cuantos dan senal.

Uso:
    python mining_class_check.py            # exit 1 si alguno mina algo que no declara
    python mining_class_check.py --fix      # anade las clases derivadas
"""

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",
    "needs": "files",
    "what": "cada minero declara las clases de exploracion que de verdad cubre",
    "args": "[--fix]",
}

import argparse
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ALGOS = os.path.join(REPO, "brain_v2", "methods", "algorithms.json")

# Senales por clase. DELIBERADAMENTE ESTRECHAS: se prefiere no detectar a detectar de mas,
# porque un falso positivo aqui reclasifica mal un metodo y eso es peor que dejarlo sin clase.
# Cada patron es un nombre propio de SAP o un instrumento nuestro, nunca una palabra comun.
SENALES = {
    "CODIGO_COMO_FUENTE": [
        # FUERA a proposito: DD02L y DD03L. Consultar el DICCIONARIO no es leer codigo -- lo
        # hace casi cualquier lector de tablas para saber los campos, y marcaba a A40 (que
        # compara transportes) como si minara comportamiento. La senal buena es el FUENTE.
        r"RPY_PROGRAM_READ", r"CLIF_GET_SOURCE", r"\bSEOCLASS\b", r"\bTADIR\b",
        r"\bREPOSRC\b", r"\bTRDIR\b", r"read_source", r"extracted_code", r"extracted_sap",
    ],
    "CANAL_Y_ACTOR": [
        r"\bRFCDES\b", r"\bBDCLD\b", r"\bAPQI\b", r"\bSM59\b",
        # FUERA: rsau_audit_history y USR02 solos. Leer el log de auditoria no es, por si mismo,
        # minar canal: A48 mapea actividad y A56 agrega franjas -- son tecnicas SOBRE el log, no
        # descubrimiento de canal. La senal buena es el registro de DESTINOS y colas.
    ],
    # DERIVA se queda SIN SENAL a proposito, y eso es una decision, no un olvido. Se probaron
    # dos y las dos fallaban: "serie temporal" marcaba a A61 por lo que DEVUELVE en vez de por
    # lo que estudia; y "deriva ... entre" marcaba a A40, que compara entre SISTEMAS y no en el
    # TIEMPO -- en castellano "deriva" es a la vez el sustantivo y el verbo. Una senal que no
    # discrimina es peor que ninguna: entrena a ignorar el check. DERIVA se declara a mano
    # hasta que alguien encuentre una senal que separe cambio-en-el-tiempo de diferencia-entre.
    "DERIVA": [],
    "CONFORMIDAD": [r"contra (el|la) (carton|estandar|norma|documento)", r"lo real contra"],
}
# La clase que se propone tiene que EXISTIR en la taxonomia: si no, el fallo es de la taxonomia.
TAX = "_taxonomia_mineria"


def clases_declaradas(v):
    tm = v.get("tipo_mineria") or v.get("mining_kind")
    if isinstance(tm, str):
        return [tm]
    return list(tm or [])


def senales_de(v):
    """Texto donde se busca: la DEFINICION del algoritmo, no cualquier campo suelto."""
    # El campo "evidence" describe EL CASO, no el metodo, y por eso se excluye: A63 salia
    # marcado como minero de canal porque su evidencia CITA rsau_audit_history al contar el
    # ejemplo del claim 616. Un ejemplo no es una capacidad. Tampoco se mira "failure_mode":
    # ahi se nombra lo que NO hay que hacer, y confundir la advertencia con la capacidad es la
    # misma trampa por el otro lado.
    campos = ("operates_on", "does", "bound_in", "checks_first", "lands_in")
    return json.dumps({k: v.get(k) for k in campos}, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()

    doc = json.load(io.open(ALGOS, encoding="utf-8"))
    A = doc.get("algorithms") or {}
    tax = set((doc.get(TAX) or {}).get("tipos") or {})

    # DENOMINADOR DECLARADO — regla feedback_declare_the_denominator_before_publishing_a_number
    print("MINEROS QUE NO DECLARAN LO QUE MINAN\n")
    print("denominador: %d algoritmos en el registro · %d clases en la taxonomia"
          % (len(A), len(tax)))
    desconocidas = [c for c in SENALES if c not in tax]
    if desconocidas:
        print("AVISO: hay senales para clases que NO existen en la taxonomia: %s."
              % ", ".join(desconocidas))
        print("       Ese hueco es de la taxonomia, no de los algoritmos. Se ignoran.")
    print()

    faltan = []
    for k in sorted(A):
        v = A[k]
        txt = senales_de(v)
        dec = clases_declaradas(v)
        for clase, pats in SENALES.items():
            if clase not in tax or clase in dec:
                continue
            hit = [p for p in pats if re.search(p, txt, re.I)]
            if hit:
                faltan.append((k, clase, hit[:3], dec))

    if not faltan:
        print("OK — ningun algoritmo mina algo que no declare.")
        return 0

    print("%-42s %-20s %s" % ("ALGORITMO", "CLASE QUE FALTA", "SENAL QUE LO DELATA"))
    for k, clase, hit, dec in faltan:
        print("%-42s %-20s %s" % (k[:42], clase, ", ".join(h.replace("\\b", "") for h in hit)))
        print("%-42s %-20s declara: %s" % ("", "", ", ".join(dec) or "(nada)"))

    print("\n" + "=" * 76)
    print("%d algoritmo(s) minan algo que no declaran." % len(faltan))
    if a.fix:
        for k, clase, _, dec in faltan:
            A[k]["tipo_mineria"] = dec + [clase] if dec else [clase]
        json.dump(doc, io.open(ALGOS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("ANADIDAS %d clases. Un minero puede minar varias cosas: se anade, no se sustituye."
              % len(faltan))
        print("REVISA cada una: la senal es estrecha pero no infalible, y clasificar mal un")
        print("metodo es peor que dejarlo sin clase.")
        return 0
    print("Corre con --fix para anadirlas, y revisa una por una antes de commitear.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
