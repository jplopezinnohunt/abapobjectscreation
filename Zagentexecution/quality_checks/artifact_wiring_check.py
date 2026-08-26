# -*- coding: utf-8 -*-
"""Lo que construimos, ¿lo invoca alguien? O es algo que hicimos y no usamos más.

POR QUE EXISTE
    2026-08-20. JP pregunto exactamente eso sobre los artefactos de la sesion. Auditando a
    mano aparecieron TRES huerfanos: un quality check sin declaracion (el runner lo veia como
    UNCLASSIFIED), un JSON de hallazgos que el explorador escribia en cada rebuild y que no
    leia nadie, y dos pasos de rebuild con nombre duplicado. Los tres se habrian detectado
    solos con este check.

    NO comprueba los quality checks sin declarar: eso ya lo reporta run_all.py como
    [UNCLASSIFIED] en cada corrida, y duplicar un aviso es como se consigue que se ignoren
    los dos.

    Ya habia cuatro checks de conexion y ninguno cubria esto:
        typed_link_coverage_check    un claim nombra una entidad y no la enlaza
        finding_promotion_check      un algoritmo produjo hallazgos y nadie los promovio
        knowledge_reachability_check el trabajo abierto se alcanza desde el arranque
        algorithm_landing_check      un algoritmo declara donde aterriza
    Los cuatro miran la SALIDA. Este mira la ENTRADA: quien dispara el artefacto.

    Un artefacto que nadie invoca no es capacidad: es deuda con aspecto de capacidad.

QUE COMPRUEBA
    script          lo referencia rebuild_all.py, un hook, otro script, o companions.json
    agente          se le nombra en algun sitio (CLAUDE.md, un doc, otro agente, un skill)
    artefacto JSON  algo lo LEE, no solo lo escribe

QUE NO PUEDE DECIR
    Que el artefacto sirva para algo. Solo que hay un camino que lo dispara. Un script
    referenciado desde un paso que nunca se ejecuta sigue estando muerto, y eso no se ve
    desde aqui.

Read-only. Exit 0 = todo tiene quien lo dispare. Exit 1 = hay huerfanos.
"""

# --- self-declaration, read by quality_checks/run_all.py -------------------
QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "herramientas",  # datos_sap | conocimiento | herramientas
    "needs": "files",
    "what": "artefactos que nadie invoca: scripts sin llamador, agentes sin mencion, JSON que nadie lee ni su autor",
}
# --------------------------------------------------------------------------
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Donde puede vivir la llamada a algo.
CALLERS = [
    "brain_v2/rebuild_all.py", "brain_v2/*_hook.py", "brain_v2/**/*.py",
    "scripts/**/*.py", "Zagentexecution/quality_checks/*.py",
    "companions/companions.json", "CLAUDE.md", ".claude/agents/*.md",
    "knowledge/**/*.md", ".agents/**/*.md", "brain_v2/methods/*.json",
    "brain_v2/agent_rules/feedback_rules.json",
]

# Scripts que son punto de entrada por definicion: nadie tiene que llamarlos.
ENTRYPOINTS = {
    "rebuild_all.py", "load_domain.py", "graph_queries.py", "meta_capability.py",
    "claims_health.py", "run_all.py", "run_all_tests.py", "session_preflight.py",
    "build_brain_index.py", "curate.py", "verify_generated.py", "backup_golden.py",
}


def corpus():
    txt = {}
    for pat in CALLERS:
        for f in glob.glob(os.path.join(ROOT, pat), recursive=True):
            if not os.path.isfile(f):
                continue
            try:
                txt[os.path.relpath(f, ROOT).replace("\\", "/")] = io.open(
                    f, encoding="utf-8", errors="replace").read()
            except OSError:
                pass
    return txt


def cited(txt, needle, exclude):
    """Quien menciona `needle`, sin contarse a si mismo."""
    return [f for f, t in txt.items()
            if f.replace("\\", "/") not in exclude and needle in t]


def main():
    txt = corpus()
    orphans, ok = [], 0

    # --- 1. los quality checks SIN declarar los reporta ya run_all.py en cada corrida
    #     como [UNCLASSIFIED]. Duplicarlo aqui seria anadir un segundo aviso para el mismo
    #     hecho, y la preferencia del proyecto es eliminar antes que anadir. Se deja fuera
    #     a proposito -- comprobado el 2026-08-20: run_all.py saca los 10 que hay.

    # --- 2. scripts sin llamador
    for pat in ("brain_v2/*.py", "scripts/*.py"):
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            base = os.path.basename(f)
            rel = os.path.relpath(f, ROOT).replace("\\", "/")
            if base.startswith("_") or base in ENTRYPOINTS:
                continue
            who = cited(txt, base, {rel})
            if who:
                ok += 1
            else:
                orphans.append(("script sin llamador", rel,
                                "nadie lo nombra: ni el rebuild, ni un hook, ni otro script"))

    # --- 3. agentes sin mencion
    for f in sorted(glob.glob(os.path.join(ROOT, ".claude", "agents", "*.md"))):
        base = os.path.basename(f)
        name = base[:-3]
        rel = ".claude/agents/" + base
        who = cited(txt, name, {rel})
        if who:
            ok += 1
        else:
            orphans.append(("agente sin mencion", name,
                            "no se le nombra en CLAUDE.md, ni en un doc, ni en otro agente: "
                            "nadie sabra que existe"))

    # --- 4. JSON que se escribe y nadie lee
    written = {}
    for f, s in txt.items():
        if not f.endswith(".py"):
            continue
        for m in re.finditer(r'["\']([\w/\\.-]+\.json)["\']', s):
            j = os.path.basename(m.group(1))
            if j in ("package.json", "package-lock.json", "companions.json"):
                continue
            written.setdefault(j, set()).add(f)
    for j, writers in sorted(written.items()):
        readers = [f for f, s in txt.items() if j in s and f not in writers]
        # Un fichero que su PROPIO escritor relee en la vuelta siguiente es ESTADO, no un
        # huerfano: asi funcionan las lineas base y las instantaneas de deriva. Contarlo como
        # muerto hace que el check llore lobo 18 veces y deje de leerse -- que es el modo de
        # fallo que este check existe para evitar.
        self_read = any(re.search(r'json\.load|\.exists\(\)|os\.path\.exists', txt[w])
                        for w in writers)
        if readers or len(writers) > 1 or self_read:
            ok += 1
        else:
            w = sorted(writers)[0]
            orphans.append(("JSON que nadie lee", j,
                            "solo %s lo escribe y ni siquiera el lo relee" % w))

    print("=" * 78)
    print("CABLEADO DE ARTEFACTOS -- lo que construimos, lo invoca alguien?")
    print("=" * 78)
    print("\n  con quien los dispare : %d" % ok)
    print("  HUERFANOS             : %d\n" % len(orphans))

    if orphans:
        by = {}
        for kind, what, why in orphans:
            by.setdefault(kind, []).append((what, why))
        for kind in sorted(by):
            print("  %s (%d):" % (kind.upper(), len(by[kind])))
            for what, why in sorted(by[kind])[:12]:
                print("     %-46s %s" % (what, why))
            if len(by[kind]) > 12:
                print("     ... y %d mas" % (len(by[kind]) - 12))
            print()
        print("  Un artefacto que nadie invoca no es capacidad: es deuda con aspecto de")
        print("  capacidad. O se encadena, o se retira -- pero no se deja ahi.")
        return 1

    print("  OK -- todo artefacto tiene un camino que lo dispara.")
    print("  (Ojo: esto NO dice que sirva. Un script llamado desde un paso que nunca")
    print("   se ejecuta sigue muerto, y eso no se ve desde aqui.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
