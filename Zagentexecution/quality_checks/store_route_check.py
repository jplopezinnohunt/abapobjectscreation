"""GATE: toda ruta declarada hacia un store EXISTE en el store. Determinista, sin juicio.

POR QUE EXISTE
    `STORES_AL_GRAFO` declara, por cada store de descubrimiento, DONDE vive su contenido:
    `at: "delta_vs_model.worklist_custom"`. Esas rutas se escribieron de memoria y CINCO de
    ellas no existian en su fichero. El extractor, al no encontrarlas, caia en un fallback al
    documento entero, contaba las claves de PRIMER NIVEL, las daba por conocidas y publicaba
    "0 NUEVOS". El fichero llevaba 1.318 objetos sin explicar.

    Nadie lo noto durante semanas porque el cero era PLAUSIBLE. Un error de clave se habia
    convertido en un hallazgo ("no hay nada nuevo"), que ademas es la conclusion que impide
    seguir buscando.

    Esta es la mitad DETERMINISTA de ese problema: comprobar que la ruta existe no requiere
    juicio, solo abrir el fichero. Y por eso puede ser una puerta.

QUE COMPRUEBA
    1. El fichero del store EXISTE
    2. La ruta `at` RESUELVE dentro de el
    3. Lo que hay al final de la ruta es RECORRIBLE (dict o lista no vacia)
    4. Si es una lista de diccionarios, el `name_field` declarado EXISTE en sus registros

LO QUE NO HACE
    No dice si el contenido es CORRECTO -- eso es juicio y no cabe en una puerta. Dice si la
    ruta apunta a algo, que es la mitad que se puede automatizar.

Uso:  python Zagentexecution/quality_checks/store_route_check.py [--json]
Salida: exit 0 limpio · exit 1 si alguna ruta no resuelve
"""
QUALITY_CHECK = {
    "tier": "gate",
    "needs": "files",
    "what": ("rutas declaradas hacia un store que no existen en el store: el extractor cae en "
             "su fallback y publica ceros creibles"),
}
# ----------------------------------------------------------------------------
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDER = os.path.join(ROOT, "brain_v2", "build_brain_state.py")


def cargar_declaracion():
    """Lee STORES_AL_GRAFO del constructor sin ejecutar su main()."""
    sp = importlib.util.spec_from_file_location("_bbs", BUILDER)
    m = importlib.util.module_from_spec(sp)
    try:
        sp.loader.exec_module(m)
    except Exception as e:
        print(f"no se pudo leer {BUILDER}: {type(e).__name__}: {e}")
        return []
    return getattr(m, "STORES_AL_GRAFO", [])


def resolver(data, at):
    if not at:
        return data, True
    nodo = data
    for parte in str(at).split("."):
        if isinstance(nodo, dict) and parte in nodo:
            nodo = nodo[parte]
        else:
            return None, False
    return nodo, True


def main():
    stores = cargar_declaracion()
    h = []
    for st in stores:
        rel = st["file"]
        p = os.path.join(ROOT, "brain_v2", rel)
        if not os.path.exists(p):
            p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(p):
            h.append({"store": rel, "que_pasa": "el fichero no existe", "clave": st.get("at")})
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            h.append({"store": rel, "que_pasa": f"ilegible ({type(e).__name__})"})
            continue

        nodo, ok = resolver(d, st.get("at"))
        if not ok:
            disponibles = list(d)[:8] if isinstance(d, dict) else []
            h.append({
                "store": rel, "clave": st.get("at"),
                "que_pasa": ("la ruta declarada NO EXISTE en el fichero. El extractor caeria en "
                             "su fallback y publicaria un cero creible"),
                "claves_de_primer_nivel": disponibles})
            continue
        if not nodo or (isinstance(nodo, (list, dict)) and len(nodo) == 0):
            h.append({"store": rel, "clave": st.get("at"),
                      "que_pasa": "la ruta resuelve pero esta VACIA: nada que colgar del grafo"})
            continue
        nf = st.get("name_field")
        if nf and isinstance(nodo, list) and nodo and isinstance(nodo[0], dict):
            if nf not in nodo[0]:
                h.append({"store": rel, "clave": st.get("at"), "name_field": nf,
                          "que_pasa": (f"el campo que nombra ('{nf}') no esta en los registros"),
                          "campos_reales": list(nodo[0])[:8]})

    rep = {"_que_comprueba": "que toda ruta declarada hacia un store exista y apunte a algo",
           "_por_que": ("cinco rutas escritas de memoria no existian, el extractor cayo en su "
                        "fallback y publico '0 NUEVOS' sobre un fichero con 1.318 objetos sin "
                        "explicar. El cero era plausible y nadie lo miro"),
           "rutas_declaradas": len(stores), "hallazgos": h}
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if h else 0

    print(f"[rutas de store] {len(stores)} declaradas")
    if not h:
        print("  OK - todas resuelven y apuntan a algo")
        return 0
    for x in h:
        print(f"  [{x['store']}] at={x.get('clave')!r}")
        print(f"      {x['que_pasa']}")
        if x.get("claves_de_primer_nivel"):
            print(f"      el fichero tiene: {', '.join(x['claves_de_primer_nivel'])}")
        if x.get("campos_reales"):
            print(f"      los registros tienen: {', '.join(x['campos_reales'])}")
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
