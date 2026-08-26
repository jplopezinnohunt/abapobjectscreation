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
    exento          si se declaro TERMINAL, que la promocion que lo justifica siga en pie

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

# Este mismo fichero, excluido a proposito del barrido de JSON (ver seccion 4).
SELF = "Zagentexecution/quality_checks/artifact_wiring_check.py"

# --- artefactos TERMINALES: nadie los lee, y esa es la forma CORRECTA ---------------
#
# Un exento NO es un silencio. Cada entrada dice por que nadie debe leerlo y DONDE se
# promovio su contenido, y el check COMPRUEBA esa promocion: si el destino desaparece o
# deja de nombrar la fuente, la exencion CADUCA y el fichero vuelve a salir como huerfano.
# Por eso esta lista no sirve para callar un hallazgo -- solo para declarar un final, y
# anadir una entrada anade una condicion que puede fallar, no una que deja de mirarse.
#
# El criterio para entrar: es la SALIDA CRUDA de una medicion de una sola vez cuyo
# resultado ya vive donde se consulta. Encadenarlo a un ciclo seria volver a derivar lo
# que ya esta promovido -- o, peor, hacer que un rebuild offline dependa de una lectura
# en vivo de P01.
TERMINAL_JSON = {
    # INC-000005638 esta en ROOT_CAUSE_CONFIRMED. Las cifras de este JSON (profundidad del
    # bucket TC, veredicto por PO) estan transcritas en la seccion 14 del doc del incidente,
    # que ademas nombra el script que las produjo. Releerlo en un ciclo seria re-derivar una
    # investigacion cerrada en vez de usar el conocimiento ya promovido.
    "inc5638_per_po_engine_analysis.json": (
        "investigacion CERRADA: sus cifras estan en la seccion 14 del doc del incidente",
        [("knowledge/incidents/INC-000005638_ses_block_donor_fund_avc_fipex_deficit.md",
          "inc5638_per_po_engine_analysis.py"),
         ("brain_v2/incidents/incidents.json", "INC-000005638")],
    ),
    # probe_footprint.py hace una lectura ACOTADA y EN VIVO de P01 (RFC). Su salida es un
    # recibo: los volumenes se promovieron a unesco_system_profile.json, que declara la
    # procedencia y la fecha de la sonda, y compose_profile.py nombra la sonda como la
    # derivacion de los componentes footprint y org_structure. El JSON crudo ni siquiera se
    # conserva. No puede encadenarse: el rebuild es offline y no debe depender de RFC a P01.
    "p01_volume_probe.json": (
        "recibo de una sonda EN VIVO de P01: los volumenes estan en unesco_system_profile",
        [("brain_v2/system_profile/unesco_system_profile.json", "bounded probes"),
         ("brain_v2/system_profile/compose_profile.py", "probes/probe_footprint.py")],
    ),
}


def promoted(rel, needle):
    """El destino de la promocion existe y sigue nombrando la fuente?"""
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        return False, "no existe"
    try:
        if needle in io.open(p, encoding="utf-8", errors="replace").read():
            return True, ""
        return False, "ya no nombra '%s'" % needle
    except OSError:
        return False, "no se puede leer"


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



# ==============================================================================
# SEGUNDA PARTE (s104) — LOS INSTRUMENTOS QUE NO DEJAN ARTEFACTO
#
# La primera parte sigue ARTEFACTOS: ficheros producidos. Eso deja un punto
# ciego exacto: **un instrumento cuya salida es la PANTALLA no produce ningun
# artefacto, asi que es invisible aqui.**
#
# Medido el 2026-08-26: se escribio `brain_v2/rebuild_progress.py` (contesta por
# donde va el rebuild) y este check dio HUERFANOS: 0, OK, con la herramienta
# completamente descolgada. No es un fallo del check: es que medía la FORMA
# (¿tiene el artefacto quien lo dispare?) y no el EFECTO (¿se llega a la
# herramienta?).
#
# Y el descuelgue era estructural, no de timing: `graph_queries.py tool` se
# alimenta del toolgraph, que solo escanea CINCO raices --
#   brain_v2/skills/skill_registry.json · brain_v2/methods/algorithms.json ·
#   brain_v2/methods/algorithm_memory.json · .claude/agents/ ·
#   Zagentexecution/quality_checks/
# Un .py util que viva fuera de esas cinco y no lo nombre ninguna es INVISIBLE
# PARA SIEMPRE para el coordinador.
# ==============================================================================

TOOL_DIRS = ["brain_v2", "scripts"]
TOOL_SKIP = ("__init__", "setup", "conftest", "_test", "test_")


def instrumentos_descolgados():
    """.py ejecutables fuera de las raices del toolgraph que nadie nombra."""
    import glob as _glob
    txt = corpus()  # {fichero: texto} de todo lo que puede citar algo
    sueltos = []
    for d in TOOL_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for f in _glob.glob(os.path.join(base, "*.py")):
            name = os.path.splitext(os.path.basename(f))[0]
            if name.startswith(TOOL_SKIP) or name.endswith(("_test",)):
                continue
            try:
                src = io.open(f, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if "__main__" not in src:          # no es un instrumento invocable
                continue
            citas = [c for c in cited(txt, name, exclude=f)]
            if not citas:
                sueltos.append((os.path.relpath(f, ROOT), name))
    return sueltos


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
    #
    # Este fichero se EXCLUYE del barrido, escribiendo y leyendo. Sin la exclusion, nombrar
    # un JSON en TERMINAL_JSON lo convertiria en "otro escritor" (len(writers)>1) o en un
    # "lector", y el check se aprobaria a si mismo por el mero hecho de mencionarlo. Un check
    # que se cierra citandose no comprueba nada.
    exempt = []
    written = {}
    for f, s in txt.items():
        if not f.endswith(".py") or f == SELF:
            continue
        for m in re.finditer(r'["\']([\w/\\.-]+\.json)["\']', s):
            j = os.path.basename(m.group(1))
            if j in ("package.json", "package-lock.json", "companions.json"):
                continue
            written.setdefault(j, set()).add(f)
    for j, writers in sorted(written.items()):
        readers = [f for f, s in txt.items()
                   if j in s and f not in writers and f != SELF]
        # Un fichero que su PROPIO escritor relee en la vuelta siguiente es ESTADO, no un
        # huerfano: asi funcionan las lineas base y las instantaneas de deriva. Contarlo como
        # muerto hace que el check llore lobo 18 veces y deje de leerse -- que es el modo de
        # fallo que este check existe para evitar.
        self_read = any(re.search(r'json\.load|\.exists\(\)|os\.path\.exists', txt[w])
                        for w in writers)
        if readers or len(writers) > 1 or self_read:
            ok += 1
            continue
        if j in TERMINAL_JSON:
            reason, proofs = TERMINAL_JSON[j]
            roto = [(p, why) for p, n in proofs
                    for vale, why in [promoted(p, n)] if not vale]
            if roto:
                orphans.append(("exento CADUCADO", j,
                                "se declaro terminal porque su contenido estaba promovido, "
                                "y la promocion ya no esta: "
                                + "; ".join("%s %s" % (p, why) for p, why in roto)))
            else:
                exempt.append((j, reason))
                ok += 1
            continue
        w = sorted(writers)[0]
        orphans.append(("JSON que nadie lee", j,
                        "solo %s lo escribe y ni siquiera el lo relee" % w))

    # --- 5. exenciones que ya no cubren nada: si nadie produce el fichero, la entrada de
    #        TERMINAL_JSON sobra. Una lista de exentos que no se poda acaba tapando cosas
    #        que nadie decidio tapar.
    for j in sorted(TERMINAL_JSON):
        if j not in written:
            orphans.append(("exento SIN PRODUCTOR", j,
                            "declarado terminal y ya no lo escribe ningun script: "
                            "retira la entrada de TERMINAL_JSON"))

    print("=" * 78)
    print("CABLEADO DE ARTEFACTOS -- lo que construimos, lo invoca alguien?")
    print("=" * 78)
    print("\n  con quien los dispare : %d" % ok)
    print("  terminales declarados : %d" % len(exempt))
    print("  HUERFANOS             : %d\n" % len(orphans))

    # Los exentos se IMPRIMEN siempre. Un exento que no se ve es un huerfano con permiso.
    if exempt:
        print("  TERMINALES (%d) -- nadie los lee y asi debe ser; promocion verificada:"
              % len(exempt))
        for j, reason in exempt:
            print("     %-46s %s" % (j, reason))
        print()

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

    sueltos = instrumentos_descolgados()
    print()
    print("-" * 78)
    print("INSTRUMENTOS SIN ARTEFACTO -- los que contestan en pantalla")
    print("-" * 78)
    if sueltos:
        print("  DESCOLGADOS (%d) -- existen y NADIE los nombra, asi que el coordinador" % len(sueltos))
        print("  (`graph_queries.py tool`) no los encuentra NUNCA:")
        for rel, name in sueltos:
            print("     %-52s" % rel)
        print()
        print("  ARREGLO: registrarlo donde el toolgraph SI mira -- una ficha en")
        print("  brain_v2/methods/algorithms.json (dentro de la clave `algorithms`, no")
        print("  al lado), o nombrarlo desde un agente / skill / quality check.")
        print("  Un instrumento que solo imprime no deja rastro que otro check pueda seguir:")
        print("  si no lo nombra nadie, es como si no existiera.")
        return 1
    print("  OK -- todo instrumento invocable esta nombrado desde alguna raiz del toolgraph.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
