"""EL SKILL COMO NODO DEL GRAFO, no como un fichero suelto que hay que acordarse de abrir.

POR QUE EXISTE
    Hay 48 skills con cientos de KB de metodo curado -- sap_payment_bcm_agent son 106 KB -- y
    medido el 2026-08-26: 57 de 75 algoritmos y 7 de 13 agentes no nombran ninguno. El caso que
    lo destapo: `config_transport_prerelease_check` se escribio y se ARREGLO DOS VECES sin abrir
    `sap_transport_intelligence`, que tiene una seccion entera sobre OBJFUNC (=M borra la tabla
    ENTERA en destino) y otra que dice que E071K vacio tambien significa ROL. Las dos cambian el
    veredicto del check.

    El primer intento de arreglo fue pedir que cada agente NOMBRARA su skill en su prosa. El
    operador lo corto: «mas que nombrarlos, tiene que haber RELACIONES». Y tiene razon, porque
    es la misma leccion que este brain ya pago -- la prosa .md NO promueve nada al grafo; hace
    falta un REGISTRO ESTRUCTURADO. Un nombre citado en un markdown no se puede consultar, no se
    puede recorrer, no avisa cuando el skill cambia y no dice quien mas deberia leerlo.

QUE PRODUCE
    brain_v2/skills/skill_registry.json — un nodo por skill, con sus ARISTAS:
      cubre_tablas      los nombres SAP que documenta (cruzados contra el brain: nada inventado)
      leido_por         agentes y algoritmos que lo nombran     <- la arista que SI existe
      deberia_leerlo    los que operan sobre sus tablas y NO lo nombran   <- LA QUE FALTA
      implementado_por  algoritmos que lo mecanizan
    Y aterriza en brain_state, asi que `graph_queries.py skill <tema>` contesta.

COMO SE DERIVA, y por que no se escribe a mano
    Las tablas de cada skill se sacan del PROPIO skill y se validan contra los nombres SAP que
    el brain ya conoce; las aristas se calculan cruzando. Escribir el mapa a mano seria una
    lista mas que envejece en silencio, que es justo lo que este fichero existe para evitar.

Uso:  python brain_v2/build_skill_registry.py
"""
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, ".agents", "skills")
AGENTS = os.path.join(ROOT, ".claude", "agents")
ALGOS = os.path.join(ROOT, "brain_v2", "methods", "algorithms.json")
SALIDA = os.path.join(ROOT, "brain_v2", "skills", "skill_registry.json")

# Mismos descartes que el gate, y por el mismo motivo: coincidir en T001 o en 'P01' no prueba
# que dos artefactos hablen del mismo tema.
DEMASIADO_COMUNES = {
    "T001", "TADIR", "USR02", "BKPF", "BSEG", "MANDT", "T000", "SPRAS",
    "P01", "D01", "V01", "TS2", "UNESCO", "UNES",
    "ALL", "OUTPUT", "DELETE", "POSTING", "CHANGE", "REPORT", "SELECT", "FILE", "TEXT",
    "HCM", "FI", "MM", "PS", "CO", "SD", "BASIS",
}
SOLAPE_MINIMO = 2

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------------------
# Se lee ANTES de construir el registro. `algorithm_memory.json` guarda, por cada memoria, su
# `implication`: que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no
# leerlas es aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo.
#
# LA RUTA SE BUSCA, NO SE CUENTA. Subiendo desde __file__ hasta el directorio que CONTIENE
# process_mining. Contarla con dirname() es como el bloque de fsv_coverage_check quedo ciego:
# dos dirname desde quality_checks/ apuntan a Zagentexecution/process_mining, que no existe, y
# un `except Exception` se tragaba el fallo en SILENCIO mientras la puerta daba verde porque
# greppeaba la CADENA, no el efecto. Aqui el fichero cuelga de brain_v2/, o sea UN nivel, pero
# la ruta se busca igual: contarla bien HOY es lo que se rompe cuando el fichero se mueve.
import os as _os, sys as _sys                                             # noqa: E401
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d):
    if _os.path.isdir(_os.path.join(_d, "process_mining")):
        _sys.path.insert(0, _os.path.join(_d, "process_mining"))
        break
    _d = _os.path.dirname(_d)
try:
    # ImportError y no Exception: cubre "metodo.py no esta" sin tragarse un fallo REAL dentro
    # de metodo.py. Y AVISA: un minero que corre sin memoria tiene que decirlo, no callarlo.
    from metodo import lo_que_ya_aprendimos as _aprendido                 # noqa: E402
except ImportError as _e:
    print("  AVISO: corriendo SIN memoria de metodo (%s)" % _e)
    _aprendido = None

# Los temas se eligieron PROBANDOLOS (`python process_mining/metodo.py <tema>`), no por sonar
# bien: los cuatro devuelven 7 memorias y las cuatro que importan describen ESTE defecto.
#   patron               A34: clasificar por PATRON sobre texto libre de SAP produce cifras
#                        plausibles, seguras y falsas -- que es LITERALMENTE el failure_mode
#                        de A51 (reconocer "lo que parece una tabla" engancho CRITICAL, NEVER,
#                        FROM, MARTIN, y dijo 43 ciegos donde habia 19)
#   sqlite_master        A18: 165 de 374 objetos del Gold son UPPERCASE y el resto minusculas;
#                        un match exacto contra sqlite_master falla en silencio. Este fichero
#                        lee sqlite_master y normaliza a mayusculas: la memoria dice POR QUE
#   tabla maestra        batch-input-explorer: que un nombre case contra una tabla maestra NO
#                        dice de que ES, solo que existe alli. Un skill que cita REGUH no es
#                        por eso el skill de REGUH -- por eso se publican CANDIDATOS
#   lista escrita a mano A50: una lista escrita a mano no avisa de lo que deja fuera. Aqui esa
#                        lista es DEMASIADO_COMUNES, y su hueco no se ve, se sufre
TEMAS_APRENDIDOS = ("patron", "sqlite_master", "tabla maestra", "lista escrita a mano")


def nombres_sap_conocidos():
    """La autoridad de que ES un nombre SAP: el brain y el Gold. No un patron."""
    out = set()
    try:
        st = json.load(open(os.path.join(ROOT, "brain_v2", "brain_state.json"),
                            encoding="utf-8"))
        out |= {str(k).upper() for k in (st.get("objects") or {})}
    except Exception:
        pass
    try:
        g = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                         "p01_gold_master_data.db")
        if os.path.exists(g):
            con = sqlite3.connect("file:%s?mode=ro" % g, uri=True, timeout=60)
            out |= {str(r[0]).upper().replace("P01_", "").replace("D01_", "")
                    for r in con.execute(
                        "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
            con.close()
    except Exception:
        pass
    return out - DEMASIADO_COMUNES


def citados(texto, conocidos):
    return {m for m in re.findall(r"\b([A-Z][A-Z0-9_/]{2,29})\b", texto or "")
            if m in conocidos}


def titulos(texto, tope=14):
    """De que habla el skill, en sus propias palabras: sus encabezados."""
    return [re.sub(r"^#+\s*", "", l).strip()
            for l in texto.split("\n") if l.startswith("##")][:tope]


def main():
    if _aprendido:
        _aprendido(*TEMAS_APRENDIDOS).avisar(minero="A51_skill_registry")
    conocidos = nombres_sap_conocidos()
    skills = {}
    for d in sorted(os.listdir(SKILLS)) if os.path.isdir(SKILLS) else []:
        p = os.path.join(SKILLS, d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        t = open(p, encoding="utf-8", errors="ignore").read()
        skills[d] = {
            "skill": d,
            "fichero": ".agents/skills/%s/SKILL.md" % d,
            "bytes": len(t),
            "de_que_habla": titulos(t),
            "cubre_tablas": sorted(citados(t, conocidos)),
            "leido_por": {"agentes": [], "algoritmos": []},
            "deberia_leerlo": [],
            "_por_que_importa": None,
        }

    # --- quien lo NOMBRA (la arista que existe) y quien DEBERIA (la que falta) ----------
    consumidores = []
    for f in sorted(os.listdir(AGENTS)) if os.path.isdir(AGENTS) else []:
        if f.endswith(".md"):
            t = open(os.path.join(AGENTS, f), encoding="utf-8", errors="ignore").read()
            consumidores.append(("agentes", f[:-3], t))
    try:
        A = json.load(open(ALGOS, encoding="utf-8")).get("algorithms") or {}
    except Exception:
        A = {}
    for k, v in A.items():
        consumidores.append(("algoritmos", k, json.dumps(v, ensure_ascii=False)))

    for tipo, quien, texto in consumidores:
        suyas = citados(texto, conocidos)
        for s, rec in skills.items():
            if s in texto:
                rec["leido_por"][tipo].append(quien)
                continue
            comun = suyas & set(rec["cubre_tablas"])
            if len(comun) >= SOLAPE_MINIMO:
                rec["deberia_leerlo"].append(
                    {"quien": quien, "tipo": tipo, "tablas_en_comun": sorted(comun)[:8],
                     "n": len(comun)})
    for rec in skills.values():
        rec["deberia_leerlo"].sort(key=lambda x: -x["n"])
        rec["_por_que_importa"] = (
            "%d artefacto(s) lo leen y %d operan sobre sus tablas SIN leerlo"
            % (len(rec["leido_por"]["agentes"]) + len(rec["leido_por"]["algoritmos"]),
               len(rec["deberia_leerlo"])))

    huerfanos = sorted(s for s, r in skills.items()
                       if not r["leido_por"]["agentes"] and not r["leido_por"]["algoritmos"])
    doc = {
        "_que_es": ("el SKILL como nodo del grafo, con sus aristas. Un skill nombrado en la "
                    "prosa de un agente no es una relacion: no se consulta, no se recorre y no "
                    "avisa de quien mas deberia leerlo"),
        "_como_se_lee": {
            "cubre_tablas": "nombres SAP que el skill documenta, validados contra el brain",
            "leido_por": "la arista que SI existe: quien lo nombra",
            "deberia_leerlo": ("LA QUE FALTA: opera sobre sus mismas tablas y no lo nombra. "
                               "El solape dice que se habla del mismo tema, no que el skill sea "
                               "el bueno -- eso lo decide quien lo lea"),
        },
        "_medido_utc": "2026-08-26",
        "skills": len(skills),
        "sin_ningun_lector": {"cuantos": len(huerfanos), "cuales": huerfanos,
                              "_ojo": ("un skill que nadie lee es metodo pagado y no cobrado. "
                                       "No siempre es un defecto -- puede ser de un tema "
                                       "dormido -- pero hay que saberlo")},
        "por_skill": skills,
    }
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)

    faltan = sum(len(r["deberia_leerlo"]) for r in skills.values())
    leen = sum(len(r["leido_por"]["agentes"]) + len(r["leido_por"]["algoritmos"])
               for r in skills.values())
    print(f"[skills] {len(skills)} skill(s) · {leen} arista(s) LEIDO_POR · "
          f"{faltan} arista(s) DEBERIA_LEERLO")
    print(f"  sin ningun lector: {len(huerfanos)}")
    print("\n  los mas ignorados (metodo pagado que nadie usa):")
    for s, r in sorted(skills.items(), key=lambda t: -len(t[1]["deberia_leerlo"]))[:8]:
        print(f"    {r['bytes']:>7,} B  {s:34s} lo leen {len(r['leido_por']['agentes']) + len(r['leido_por']['algoritmos']):>2}  "
              f"deberian {len(r['deberia_leerlo']):>2}")
    print(f"\n-> {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
