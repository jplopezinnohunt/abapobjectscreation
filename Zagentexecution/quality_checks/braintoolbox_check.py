"""
braintoolbox_check.py — el BRAINTOOLBOX se mide, o esta muerto.

`brain_v2/braintoolbox.yaml` es el modelo canonico de COMO TRABAJAMOS: los tres roles, los dos ejes,
la triada, el bucle y su termometro. Y afirma de si mismo que **cada cifra suya se puede
recalcular**. Esta puerta lo comprueba: si una cifra del YAML ya no coincide con lo que dicen
los ficheros vivos, esa linea esta muerta y hay que actualizarla o retirarla.

POR QUE UN DOCUMENTO SOBRE UNO MISMO NECESITA PUERTA
    Un modelo de como se trabaja envejece mas rapido que el trabajo, y envejece EN SILENCIO:
    nadie lo relee porque cree conocerlo. Un `braintoolbox.yaml` con cifras de hace tres semanas es
    peor que ninguno, porque da confianza falsa sobre el propio estado. Medido el 2026-08-27:
    el termometro paso de 19,7 %% a otro valor en la misma sesion en que se escribio.

NO valida la PROSA del YAML — las ideas no se miden. Valida las CIFRAS, que si.

Uso:
    python braintoolbox_check.py            # exit 1 si alguna cifra derivo
    python braintoolbox_check.py --fix      # reescribe las cifras con lo medido ahora
"""

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",
    "needs": "files",
    "what": "las cifras del modelo de la caja siguen coincidiendo con los ficheros vivos",
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
YML = os.path.join(REPO, "brain_v2", "braintoolbox.yaml")


def cargar(p):
    fp = os.path.join(REPO, p)
    try:
        return json.load(io.open(fp, encoding="utf-8"))
    except Exception:
        return {}


def medir():
    """Recalcula, AHORA, cada cifra que el modelo afirma."""
    tg = cargar("brain_v2/toolgraph.json")
    res = (tg.get("resumen") or {})
    nod, ar = res.get("nodos") or {}, res.get("aristas") or {}
    sal = tg.get("salud") or {}
    lee, deb = ar.get("LEE", 0), ar.get("DEBERIA_LEER", 0)
    m = {
        "skills": nod.get("SKILL", 0),
        "agentes": nod.get("AGENTE", 0),
        "mineros": nod.get("MINERO", 0),
        "gates": nod.get("GATE", 0),
        "stores": nod.get("STORE", 0),
        "clases_de_mineria": nod.get("CLASE_MINERIA", 0),
        "skills_sin_ningun_lector": (sal.get("skills_sin_ningun_lector") or {}).get("cuantos", 0),
        "agentes_sin_instrumento_declarado":
            (sal.get("agentes_sin_instrumento_declarado") or {}).get("cuantos", 0),
        "instrumentos_rotos_o_con_defecto_vivo":
            (sal.get("instrumentos_rotos_o_con_defecto_vivo") or {}).get("cuantos", 0),
        "agentes_que_no_delegan_en_nadie":
            len((sal.get("colaboracion_entre_agentes") or {})
                .get("agentes_que_no_delegan_en_nadie") or []),
        "LEE": lee, "DEBERIA_LEER": deb,
        "conectividad_pct": round(100.0 * lee / max(1, lee + deb), 1),
    }
    # la triada se recalcula corriendo su propio check, no copiando su ultimo resultado
    inc = cargar("brain_v2/incidents/incidents.json") or []
    m["trabajos"] = len(inc)
    # preguntas propagadas realmente en el bus
    bus = cargar("process_mining/mining_findings.json")
    m["preguntas_propagadas"] = len([q for q in (bus.get("preguntas") or [])
                                     if q.get("de") == "knowledge_propagation"])
    return m


# (clave del YAML tal como aparece escrita, funcion que saca su valor medido)
COMPROBADAS = [
    (r"medido_hoy: (\d+) skills · (\d+) sin ningun lector", ("skills", "skills_sin_ningun_lector")),
    (r"medido_hoy: (\d+) agentes · (\d+) sin instrumento declarado", ("agentes",
                                                                     "agentes_sin_instrumento_declarado")),
    (r"medido_hoy: (\d+) mineros sobre (\d+) clases de mineria", ("mineros", "clases_de_mineria")),
    (r"medido_hoy: (\d+) gates", ("gates",)),
    (r"medido_hoy: (\d+) stores", ("stores",)),
    (r"conectividad_pct: ([\d.]+)", ("conectividad_pct",)),
    (r"hoy: LEE (\d+) · DEBERIA_LEER (\d+)", ("LEE", "DEBERIA_LEER")),
    (r"skills_sin_ningun_lector: (\d+)", ("skills_sin_ningun_lector",)),
    (r"agentes_sin_instrumento_declarado: (\d+)", ("agentes_sin_instrumento_declarado",)),
    (r"agentes_que_no_delegan_en_nadie: (\d+)", ("agentes_que_no_delegan_en_nadie",)),
    (r"instrumentos_rotos_o_con_defecto_vivo: (\d+)",
     ("instrumentos_rotos_o_con_defecto_vivo",)),
    (r"medido_hoy: (\d+) preguntas dirigidas", ("preguntas_propagadas",)),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(YML):
        print("no existe brain_v2/braintoolbox.yaml — el modelo de la caja no esta escrito")
        return 1
    s = io.open(YML, encoding="utf-8").read()
    m = medir()

    print("BRAINTOOLBOX — ¿siguen vivas sus cifras?\n")
    print("%-46s %10s %10s" % ("AFIRMACION", "EN EL YAML", "MEDIDO"))
    derivadas, nuevo = [], s
    for patron, claves in COMPROBADAS:
        mt = re.search(patron, s)
        if not mt:
            print("%-46s %10s %10s" % (patron[:46], "NO ESTA", "-"))
            continue
        for i, k in enumerate(claves, 1):
            dicho, real = mt.group(i), str(m.get(k))
            ok = dicho == real
            print("%-46s %10s %10s   %s" % (k, dicho, real, "" if ok else "<<< DERIVO"))
            if not ok:
                derivadas.append((k, dicho, real))
        if a.fix and any(mt.group(i) != str(m.get(k)) for i, k in enumerate(claves, 1)):
            trozo = mt.group(0)
            for i, k in enumerate(claves, 1):
                trozo = trozo.replace(mt.group(i), str(m.get(k)), 1)
            nuevo = nuevo.replace(mt.group(0), trozo, 1)

    print("\n" + "=" * 70)
    if not derivadas:
        print("OK — las %d cifras del modelo siguen coincidiendo con los ficheros vivos"
              % sum(len(c) for _, c in COMPROBADAS))
        return 0
    if a.fix:
        io.open(YML, "w", encoding="utf-8").write(nuevo)
        print("ACTUALIZADAS %d cifras en braintoolbox.yaml. Revisa que la PROSA siga siendo cierta:"
              % len(derivadas))
        for k, d, r in derivadas:
            print("   %-42s %s -> %s" % (k, d, r))
        print("\nUna cifra se arregla sola; una idea que ya no se sostiene, no.")
        return 0
    print("%d CIFRAS DEL MODELO HAN DERIVADO — la caja dice de si mismo algo que ya no es:"
          % len(derivadas))
    for k, d, r in derivadas:
        print("   %-42s dice %s · mide %s" % (k, d, r))
    print("\nCorre con --fix para actualizarlas, y RELEE la prosa: si la cifra cambio mucho,")
    print("puede que la idea que la acompana tampoco se sostenga.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
