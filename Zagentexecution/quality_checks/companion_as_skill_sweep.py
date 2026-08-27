"""
companion_as_skill_sweep.py — la tesis del dueno, MEDIDA: "los companions contienen skills
de dominio que nadie declaro". H137 punto 4, s107.

LA TESIS
    Tenemos 50 companions en disco y 50 skills. Si una parte del conocimiento de dominio vive
    atrapada en HTML que nadie declara como skill, entonces: no lo lee ningun instrumento, no
    es nodo del toolgraph, y no puede tener lectores porque no es nodo. Seria el mismo agujero
    de H116 (39 skills sin lector) pero un piso mas abajo: conocimiento que ni siquiera llego
    a ser skill.

POR QUE HAY QUE MEDIRLO Y NO OPINARLO
    "Este companion parece un skill" es exactamente el juicio que en s106 metio
    `sap_transport_companion` como prioridad numero uno por una cifra de solape, y al ABRIRLO
    no procedia: no es conocimiento de transportes, es el metodo para CONSTRUIR el companion.
    De 6 candidatos revisados a mano, 5 procedian y 1 no. Asi que esto RANQUEA DONDE MIRAR;
    NO da veredicto. Se abre el fichero antes de declarar nada.

QUE MIDE, POR COMPANION
    CLASE      — que ES el artefacto, por su forma:
                 CASO  = registro de un hecho concreto (INC-*, retro, sesion, un transporte).
                         Su valor es el caso, no el metodo: no es un skill y no lo sera.
                 PANEL = tablero. Mucha tabla y poca prosa: es una MEDIDA, no un metodo.
                 MODELO= narrativa de como funciona algo. Aqui, y solo aqui, cabe un skill.
    PROSA      — marcas de conocimiento INSTRUCTIVO (NEVER / no hagas / how to / why it
                 matters / trampa / ojo / si...entonces / que configurar / re-derive). Es lo
                 que separa "te explico como se opera esto" de "aqui tienes los numeros".
    COBERTURA  — que skill YA cubre su vocabulario, por solape contra `cubre_nombres` +
                 `cubre_tablas` de brain_v2/skills/skill_registry.json. Si un skill ya lo
                 cubre, lo que falta NO es un skill nuevo: es DECLARAR EL PAR (el companion es
                 la cara visual de ese skill). Crear uno al lado seria duplicar.
    LECTORES   — quien nombra el fichero en el repo, fuera de companions/ y fuera de los
                 stores generados. Un companion con 0 lectores es conocimiento sin consumidor.

LO QUE ESTE INSTRUMENTO NO PUEDE VER (declarado, no descubierto por el siguiente)
    - Si la prosa es BUENA. Cuenta marcas, no calidad. Un fichero que repite "NEVER" en un
      pie de pagina puntua como uno que explica una trampa real.
    - El solape con un skill es por VOCABULARIO. Compartir tablas no es tratar el mismo tema
      (lo demostro RFC_READ_TABLE inflando 109 de 302 solapes, claim 622). Por eso el solape
      alto se lee como "abre este skill antes", no como "ya esta cubierto".
    - Los HTML fuera de companions/. El canonico es ese directorio.

Uso:
    python companion_as_skill_sweep.py                 # el barrido entero
    python companion_as_skill_sweep.py --clase MODELO  # solo los candidatos reales
    python companion_as_skill_sweep.py --json          # salida para otro instrumento
"""

QUALITY_CHECK = {
    "tier": "analysis",
    "sobre": "conocimiento",
    "needs": "files",
    "what": "que companions son de facto un skill de dominio sin declarar, y cuales ya tienen skill",
    "args": "[--clase MODELO|PANEL|CASO] [--json]",
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
COMP = os.path.join(REPO, "companions")
GRAPH = os.path.join(COMP, "companion_graph.json")
SKILLS = os.path.join(REPO, "brain_v2", "skills", "skill_registry.json")

SKIP = {"unesco_sap_landing.html", "companion_graph_v1.html"}

# CASO: el nombre ya lo dice. Un registro de un hecho concreto no se convierte en metodo.
CASO_RE = re.compile(r"^(inc[_-]|inc\d|session_|.*_retro|transport_companion_|upgrade_\d)", re.I)

# marcas de conocimiento INSTRUCTIVO — lo que distingue metodo de medida
PROSA_RE = re.compile(
    r"\bNEVER\b|\bDO NOT\b|\bmust\b|\bgotcha\b|\bpitfall\b|\bcaveat\b|\bwarning\b|"
    r"\bhow to\b|\bwhy it matters\b|\bwhat you need\b|\bre-derive\b|\bbeware\b|"
    r"\btrampa\b|\bojo\b|\bnunca\b|\bcuidado\b|\bcomo se\b|\bpor que importa\b|\bque hacer\b",
    re.I)
TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<script.*?</script>", re.S | re.I)
STYLE_RE = re.compile(r"<style.*?</style>", re.S | re.I)
TR_RE = re.compile(r"<tr[\s>]", re.I)


def cargar(p, d=None):
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return d if d is not None else {}


def lectores_del_repo(nombres):
    """Quien NOMBRA cada companion, fuera de companions/ y de los stores generados.

    SE RECORRE EL REPO UNA VEZ Y NO SE GUARDA NADA. La primera version acumulaba el texto
    de cada fichero en una lista para cruzarlo despues: medido, 930 MB de RSS y el proceso
    a swap con 6 s de CPU en 15 minutos. Guardar el corpus para preguntarle 50 veces cuesta
    mas que preguntarle 50 veces mientras pasa. Aqui cada fichero se lee, se le buscan los 50
    nombres, y se suelta.
    """
    ruido = ("node_modules", ".git", ".venv", "__pycache__", "extracted_code", "extracted_sap",
             "extracted_sap_p01", "playwright_data", "dist", "build", ".external")
    generados = {"brain_state.json", "companion_graph.json", "companions.json",
                 "toolgraph.json", "capability_artifacts.json", "BRAIN_INDEX.md"}
    lect = {n: [] for n in nombres}
    for raiz, dirs, ficheros in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in ruido and not d.startswith(".")]
        rel = os.path.relpath(raiz, REPO).replace("\\", "/")
        if rel.startswith("companions"):
            continue
        for f in ficheros:
            if f in generados or not f.endswith((".py", ".md", ".json", ".yaml", ".yml")):
                continue
            fp = os.path.join(raiz, f)
            try:
                if os.path.getsize(fp) > 4_000_000:
                    continue
                t = io.open(fp, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            r = os.path.relpath(fp, REPO).replace("\\", "/")
            for n in nombres:
                if n in t:
                    lect[n].append(r)
            del t
    return lect


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clase", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    graph = cargar(GRAPH)
    nodos = {n["file"]: n for n in (graph.get("nodes") or [])}
    circuitos = graph.get("circuits") or {}
    en_circuito = {}
    for clave, cc in circuitos.items():
        for s in cc["stages"]:
            for c in s["companions"]:
                en_circuito.setdefault(c, []).append(f"{clave}:{s['id']}")

    reg = cargar(SKILLS)
    por_skill = reg.get("por_skill") or {}
    vocab_skill = {k: {t.lower() for t in (v.get("cubre_nombres") or []) + (v.get("cubre_tablas") or [])}
                   for k, v in por_skill.items()}

    # --- IDF SOBRE EL VOCABULARIO DE LOS SKILLS -------------------------------------
    # LA PRIMERA CORRIDA DE ESTE BARRIDO SALIO MAL Y ASI ES COMO: `sap_company_code_copy`
    # aparecio como "skill mas cercano" 17 veces de 50. No porque cubra 17 dominios: porque
    # su vocabulario lleva muchos nombres UBICUOS. Medido aqui mismo -- `rfc_read_table` esta
    # en 20 skills de 50, `f110` en 16, las sociedades (`iiep` 10, `ubo` 10) en diez. Es
    # EXACTAMENTE el claim 622, el inflado que ya invirtio el ranking del toolgraph, repetido
    # un piso mas abajo. Contarlo crudo publica "28 companions YA TIENEN SKILL" sobre una
    # senal que no distingue tema de fontaneria.
    # Se pesa igual que en scripts/build_companion_graph.py: un nombre en muchos skills vale
    # ~0, uno raro lleva el solape. Y se exige AL MENOS UN nombre raro, para que la suma de
    # ubicuos no pueda por si sola declarar cobertura.
    import math
    NSK = max(len(vocab_skill), 1)
    df_sk = {}
    for voc in vocab_skill.values():
        for t in voc:
            df_sk[t] = df_sk.get(t, 0) + 1

    def idf_sk(t):
        d = df_sk.get(t, 0)
        if d < 1 or d > 0.25 * NSK:        # en mas de 1 de cada 4 skills = fontaneria
            return 0.0
        return math.log(NSK / d)

    RARO = math.log(NSK / max(1, 0.10 * NSK))    # umbral de "nombre raro" (<=10% de skills)

    # --- Y ANTES QUE NADA, EL NOMBRE ------------------------------------------------
    # LA SEGUNDA CORRIDA TAMBIEN SALIO MAL, Y DE FORMA MAS TONTA: marco
    # `house_bank_configuration_companion.html` como CANDIDATO_A_SKILL -- "ningun skill cubre
    # su vocabulario" -- cuando `sap_house_bank_configuration` existe y se llama igual. Estaba
    # comparando solo VOCABULARIO SAP e ignorando la senal mas fuerte y mas barata que hay.
    # Un companion y un skill que comparten el nombre tratan el mismo tema por construccion;
    # ninguna medida de solape de tablas hace falta para saberlo.
    PALABRA_VACIA = {"sap", "companion", "v1", "v2", "html", "unesco", "agent", "model",
                     "map", "analysis", "dashboard", "the", "de", "y"}

    def tokens_nombre(x):
        return {t for t in re.split(r"[_\-.]", x.lower()) if len(t) > 2 and t not in PALABRA_VACIA}

    tok_skill = {k: tokens_nombre(k) for k in vocab_skill}

    def skill_por_nombre(companion):
        tc = tokens_nombre(companion.replace(".html", ""))
        if not tc:
            return None, 0
        mejor, best = None, 0
        for sk, ts in tok_skill.items():
            ov = len(tc & ts)
            if ov > best:
                mejor, best = sk, ov
        return mejor, best

    if not os.path.isdir(COMP):
        print("companions/ no existe — la puerta NO PUEDE VER")
        return 1

    nombres_comp = [n for n in sorted(os.listdir(COMP))
                    if n.endswith('.html') and n not in SKIP]
    lectores = lectores_del_repo(nombres_comp)
    filas = []
    for n in sorted(os.listdir(COMP)):
        if not n.endswith(".html") or n in SKIP:
            continue
        fp = os.path.join(COMP, n)
        raw = io.open(fp, encoding="utf-8", errors="replace").read()
        kb = os.path.getsize(fp) // 1024
        cuerpo = STYLE_RE.sub("", SCRIPT_RE.sub("", raw))
        texto = TAG_RE.sub(" ", cuerpo)
        palabras = len(texto.split())
        filas_tabla = len(TR_RE.findall(cuerpo))
        prosa = len(PROSA_RE.findall(texto))

        # CLASE ------------------------------------------------------------------
        if CASO_RE.match(n):
            clase = "CASO"
        elif palabras and filas_tabla * 12 > palabras:      # mas celda que frase
            clase = "PANEL"
        else:
            clase = "MODELO"

        # que skill YA lo cubre ---------------------------------------------------
        ents = {e.lower() for e in (nodos.get(n, {}).get("entities") or [])}
        mejor, puntos, raros, crudo = None, 0.0, [], 0
        for sk, voc in vocab_skill.items():
            comun = ents & voc
            if not comun:
                continue
            p = sum(idf_sk(t) for t in comun)
            rr = sorted((t for t in comun if idf_sk(t) >= RARO), key=lambda t: -idf_sk(t))
            if not rr:                      # sin un solo nombre raro no hay tema compartido
                continue
            if p > puntos:
                mejor, puntos, raros, crudo = sk, p, rr, len(comun)

        # lectores ----------------------------------------------------------------
        lect = sorted(lectores.get(n, []))

        # VEREDICTO ---------------------------------------------------------------
        sk_nombre, ov_nombre = skill_por_nombre(n)
        if ov_nombre >= 2:                 # el nombre manda: mismo tema por construccion
            mejor, raros = sk_nombre, raros or [f"NOMBRE:{ov_nombre} tokens"]

        if clase != "MODELO":
            veredicto = "NO_ES_SKILL"
        elif ov_nombre >= 2 or len(raros) >= 2:
            veredicto = "YA_TIENE_SKILL"
        elif prosa >= 5:
            veredicto = "CANDIDATO_A_SKILL"
        else:
            veredicto = "MODELO_SIN_METODO"

        filas.append({
            "companion": n, "kb": kb, "clase": clase, "prosa": prosa,
            "palabras": palabras, "filas_tabla": filas_tabla,
            "skill_mas_cercano": mejor, "solape_crudo": crudo,
            "puntos_idf": round(puntos, 2), "nombres_raros": raros[:5],
            "skill_por_nombre": sk_nombre, "tokens_nombre": ov_nombre,
            "lectores": len(lect), "lectores_ficheros": lect[:4],
            "en_circuito": en_circuito.get(n, []),
            "veredicto": veredicto,
        })

    if a.clase:
        filas = [f for f in filas if f["clase"] == a.clase]
    if a.json:
        print(json.dumps(filas, ensure_ascii=False, indent=2))
        return 0

    orden = {"CANDIDATO_A_SKILL": 0, "YA_TIENE_SKILL": 1, "MODELO_SIN_METODO": 2, "NO_ES_SKILL": 3}
    filas.sort(key=lambda f: (orden[f["veredicto"]], -f["prosa"]))

    print("=" * 108)
    print("BARRIDO DE COMPANIONS — ¿cual es de facto un skill de dominio sin declarar?  (H137, s107)")
    print("=" * 108)
    print(f"{'veredicto':<18} {'clase':<7} {'prosa':>5} {'kb':>6} {'lect':>4} {'idf':>6} {'raros':>5}  "
          f"{'skill mas cercano':<30} companion")
    print("-" * 118)
    for f in filas:
        print(f"{f['veredicto']:<18} {f['clase']:<7} {f['prosa']:>5} {f['kb']:>6} {f['lectores']:>4} "
              f"{f['puntos_idf']:>6} {len(f['nombres_raros']):>5}  {(f['skill_mas_cercano'] or '-'):<30} {f['companion']}"
              + ("   [CIRCUITO]" if f["en_circuito"] else ""))
        if f["nombres_raros"]:
            print(f"{'':>52}por: {', '.join(f['nombres_raros'][:5])}")

    print("-" * 108)
    tot = {}
    for f in filas:
        tot[f["veredicto"]] = tot.get(f["veredicto"], 0) + 1
    print("RESUMEN: " + " · ".join(f"{k} {v}" for k, v in sorted(tot.items(), key=lambda kv: orden[kv[0]])))
    sin_lector = [f["companion"] for f in filas if f["lectores"] == 0]
    print(f"SIN NINGUN LECTOR en el repo: {len(sin_lector)}")
    for c in sin_lector:
        print(f"   - {c}")
    print("\nCOMO SE LEE ESTO — y como NO:")
    print("  CANDIDATO_A_SKILL = narrativa + prosa instructiva y NINGUN skill cubre su vocabulario.")
    print("     Es DONDE MIRAR, no un veredicto: se ABRE el fichero antes de declarar nada")
    print("     (en s106, el candidato numero uno por cifra no procedia al abrirlo).")
    print("  YA_TIENE_SKILL    = el conocimiento ya tiene casa. Lo que falta es DECLARAR EL PAR")
    print("     companion<->skill, no escribir un skill nuevo al lado.")
    print("  MODELO_SIN_METODO = narra pero no ensena. Suele ser una foto de un modelo, no un metodo.")
    print("  NO_ES_SKILL       = caso o tablero. Su valor es el hecho o la cifra, y esta bien asi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
