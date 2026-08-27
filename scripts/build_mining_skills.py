"""build_mining_skills.py — los MINEROS dejan de perderse: una skill por CLASE. s107.

EL PROBLEMA, MEDIDO
    72 mineros registrados. Los 72 con script que EXISTE (0 rutas rotas). Y aun asi
    **49 de 72 (68%) no los invoca nadie**. El agujero no es el codigo: es que un minero solo
    corre si alguien recuerda que existe y abre `algorithms.json`, un JSON de 96 fichas que
    ninguna sesion carga. Por clase, la peor es CODIGO_COMO_FUENTE: 13 mineros, 10 huerfanos.

POR QUE UNA SKILL POR CLASE Y NO POR MINERO
    La documentacion de Claude Code da la primitiva exacta: una skill puede llevar
    `scripts/` que se EJECUTAN sin cargarse en contexto, y su cuerpo solo se carga al
    invocarla. Asi que el coste real es la DESCRIPCION. Medido: 12 clases ~= 1.200 tokens por
    sesion; 72 mineros ~= 7.200. Y la mayoria de los mineros no son pertinentes a una sesion
    dada, asi que 72 entradas son ruido permanente para que una sea util.
    La unidad de 12 no es inventada: es el eje `tipo_de_exploracion` que braintoolbox ya
    define, y que es ORTOGONAL al dominio -- por eso un minero sirve a cualquier dominio.

POR QUE ESTO ARREGLA EL 68%
    Como skill, el MODELO la elige cuando la descripcion encaja con la tarea. Deja de
    depender de que alguien se acuerde, que es la misma cura que se aplico a las 50 skills de
    dominio el mismo dia.

GENERADO, NO ESCRITO A MANO
    La fuente es `brain_v2/methods/algorithms.json`. Editar el SKILL.md a mano lo pierde en
    la siguiente corrida: lo que se edita es la FICHA del minero. Es la misma regla que la
    landing page.

Uso:  python scripts/build_mining_skills.py [--dry-run]
"""
import argparse
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALGOS = os.path.join(ROOT, "brain_v2", "methods", "algorithms.json")
DEST = os.path.join(ROOT, ".claude", "skills")

# Que contesta cada clase de exploracion. Es lo unico escrito a mano aqui, y va en la
# `description` -- que es lo que el modelo lee para decidir si esta skill le sirve.
QUE_CONTESTA = {
    "REALIDAD": "que ES cada nombre antes de contarlo: si un identificador del log es un objeto real, un generado o una ruta de fichero",
    "CANAL_Y_ACTOR": "por donde ENTRA el trabajo al sistema y QUIEN lo mueve: interfaces, satelites, sesiones de batch input, personas frente a herramientas",
    "CASO": "que documento es el CASO de un proceso, y si el identificador elegido aguanta como columna vertebral",
    "FLUJO_DE_CONTROL": "que sigue a que: mapa de proceso, variantes, cuellos de botella y tiempos de ciclo",
    "CONFORMIDAD": "lo REAL contra lo que DEBERIA ser: reglas normativas, desviaciones y su coste",
    "OBJETO_CENTRICO": "varios objetos a la vez, sin forzar una nocion unica de caso -- convergencia y divergencia",
    "DERIVA": "como cambia algo EN EL TIEMPO: perfiles mensuales, tasas por dia, señales de deriva",
    "RESTO_SIN_EXPLICAR": "lo que NO sabemos nombrar todavia: el sensor de lo no clasificado",
    "TECNICA_DE_LECTURA": "no mina: HACE POSIBLE minar. Como leer una fuente que no se deja leer",
    "CODIGO_COMO_FUENTE": "que HACE el sistema leido de su propio fuente ABAP -- las reglas que DECIDEN viven muchas veces en el codigo y no en la configuracion, y ningun analisis de customizing las ve",
    "COLABORACION": "quien sabe que, quien deberia preguntarle a quien, y donde se pierde el trabajo entre instrumentos",
    "ORQUESTACION": "que instrumento usar para una tarea, y en que orden",
}


def slug(c):
    return "mining-" + c.lower().replace("_", "-")


def corta(t, n):
    t = " ".join(str(t or "").split())
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    A = json.load(io.open(ALGOS, encoding="utf-8"))["algorithms"]
    porclase = {}
    for k, v in A.items():
        tm = v.get("tipo_mineria") or v.get("mining_kind")
        for t in ([tm] if isinstance(tm, str) else (tm or [])):
            porclase.setdefault(t, []).append((k, v))

    escritas = []
    for clase, mineros in sorted(porclase.items(), key=lambda kv: -len(kv[1])):
        mineros.sort(key=lambda kv: kv[0])
        qc = QUE_CONTESTA.get(clase)
        if not qc:
            print("  !! clase sin descripcion escrita: %s — se salta (dilo, no la inventes)" % clase)
            continue

        L = []
        L.append("---")
        L.append("name: " + slug(clase))
        L.append("description: >")
        L.append("  Mineria de tipo %s: %s." % (clase, qc))
        L.append("  Reune los %d mineros de esta clase con su comando exacto y su modo de fallo."
                 % len(mineros))
        L.append("  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos")
        L.append("  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.")
        L.append("when_to_use: >")
        L.append("  antes de escribir un script que explore %s · cuando quieras saber si"
                 % clase.lower().replace("_", " "))
        L.append("  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde")
        L.append("---")
        L.append("")
        L.append("# Mineria: %s" % clase)
        L.append("")
        L.append("**Qué contesta esta clase:** %s." % qc)
        L.append("")
        L.append("> Generado por `scripts/build_mining_skills.py` desde")
        L.append("> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se")
        L.append("> regenera. Lo que se edita es la ficha del minero.")
        L.append("")
        L.append("## Antes de correr ninguno")
        L.append("")
        L.append("**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los")
        L.append("de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice")
        L.append("cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede")
        L.append("verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.")
        L.append("")
        L.append("## Los %d mineros de esta clase" % len(mineros))
        L.append("")

        huerfanos = []
        for k, v in mineros:
            b = v.get("bound_in") or []
            cmd = str(b[0]).split(" ")[0] if b else None
            L.append("### `%s`" % k)
            L.append("")
            L.append("**Contesta:** %s" % corta(v.get("does"), 300))
            if cmd:
                L.append("")
                L.append("```bash")
                L.append("python %s" % cmd)
                L.append("```")
            est = v.get("state")
            if est and est not in ("WORKS", "STRONG"):
                L.append("")
                L.append("⚠️ **estado `%s`** — su salida NO se cita sin comprobarla." % est)
            fm = corta(v.get("failure_mode"), 420)
            if fm:
                L.append("")
                L.append("**Cómo da una respuesta falsa:** %s" % fm)
            nop = corta(v.get("lo_que_NO_puede"), 300)
            if nop:
                L.append("")
                L.append("**No puede ver:** %s" % nop)
            li = corta(v.get("lands_in"), 160)
            if li:
                L.append("")
                L.append("**Aterriza en:** %s" % li)
            L.append("")

        L.append("## Cómo se lee esta lista")
        L.append("")
        L.append("Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno")
        L.append("y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar")
        L.append("es pérdida por construcción.")

        txt = "\n".join(L) + "\n"
        d = os.path.join(DEST, slug(clase))
        p = os.path.join(d, "SKILL.md")
        if a.dry_run:
            print("  [dry] %-28s %2d mineros · %4d lineas" % (slug(clase), len(mineros), len(L)))
        else:
            os.makedirs(d, exist_ok=True)
            io.open(p, "w", encoding="utf-8").write(txt)
            escritas.append((slug(clase), len(mineros), len(L)))

    print("\nSKILLS DE MINERIA %s: %d" % ("que se escribirian" if a.dry_run else "escritas",
                                          len(escritas) or len(porclase)))
    for s, n, l in escritas:
        aviso = "  ⚠ pasa de 500 lineas" if l > 500 else ""
        print("  %-28s %2d mineros · %4d lineas%s" % (s, n, l, aviso))
    if escritas:
        print("\ncoste ~= %d tokens/sesion en descripciones (una por clase, no por minero)"
              % (len(escritas) * 100))


if __name__ == "__main__":
    main()
