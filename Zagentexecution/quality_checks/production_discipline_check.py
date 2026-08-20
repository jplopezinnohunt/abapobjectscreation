# -*- coding: utf-8 -*-
"""El sesgo a producir no se apaga por diagnosticarlo. Esto lo mide.

POR QUE EXISTE
    2026-08-20. Al cerrar una sesion escribi "anoto la leccion: el sesgo a producir no se
    apaga solo porque lo hayas diagnosticado". JP contesto lo unico que cabia contestar:
    "no sirve anotar, hay que mecanizar". Tenia razon -- la sesion entera trataba de que
    anotar no funciona, y la conclusion fue una nota.

    Ese dia, ademas, estuve a punto de RETIRAR 9 reglas usando como prueba que "no estaban
    citadas" -- un proxy, no evidencia -- el mismo dia en que escribi tres checks para
    impedir exactamente esa clase de error. Entre las candidatas habia una regla CRITICAL que
    protege contra la clase de incidente que corrompio clases en D01, y otra que yo mismo
    habia violado la vispera.

    Este check mide las DOS caras de ese sesgo, y las mide sobre git, no sobre intencion.

QUE MIDE

  1. RETIRADAS SIN EVIDENCIA  (mecaniza feedback_never_retire_anything_without_evidence)
     Cualquier id que existia en un store y ya no esta. Los stores no son ficheros de
     trabajo: un claim, una regla, un incidente o un algoritmo que DESAPARECE es una
     retirada, y una retirada exige evidencia escrita. La disciplina del proyecto es
     SUPERSEDE, no borrar (CP-002). Si algo se fue, tiene que haber quedado dicho por que.

  2. PRODUCIDO FRENTE A CONECTADO  (mecaniza el sesgo en si)
     Ficheros nuevos que nadie referencia. No es lo mismo que artifact_wiring_check, que
     mira TODO el repositorio y mantiene una poblacion estable: esto mira SOLO lo que se
     creo en la ventana, que es donde el sesgo actua y donde todavia es barato arreglarlo.

     Un artefacto nace desconectado y se conecta despues -- o no se conecta nunca. La
     diferencia entre esas dos cosas es una sesion de distancia, y por eso el momento de
     preguntarlo es el cierre y no un mes despues.

USO
    python Zagentexecution/quality_checks/production_discipline_check.py
    python ... --since HEAD~3        (por defecto: los commits de hoy)

Read-only sobre git. Exit 0 = limpio. Exit 1 = hay retiradas sin evidencia o produccion
desconectada.
"""

# --- self-declaration, read by quality_checks/run_all.py -------------------
QUALITY_CHECK = {
    "tier": "gate",
    "needs": "files",
    "what": "retiradas sin evidencia + ficheros creados que nadie referencia (el sesgo a producir, medido)",
}
# --------------------------------------------------------------------------
import glob
import io
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stores donde una desaparicion es una RETIRADA, no una edicion.
STORES = {
    "brain_v2/claims/claims.json": "claim",
    "brain_v2/agent_rules/feedback_rules.json": "regla",
    "brain_v2/incidents/incidents.json": "incidente",
    "brain_v2/methods/algorithms.json": "algoritmo",
}

# Lo que no cuenta como "produccion" a conectar.
IGNORE_NEW = re.compile(
    r"(^|/)(\.|__pycache__|node_modules)|"
    r"\.(png|jpg|jpeg|gif|csv|log|zip|db|xlsx|docx|pdf)$|"
    r"^brain_v2/(brain_state|BRAIN_INDEX)|"
    r"^Zagentexecution/tasks/|^knowledge/session_retros/|^companions/"
)


def git(*a):
    try:
        return subprocess.check_output(["git"] + list(a), cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode("utf-8", "replace")
    except Exception:
        return ""


def ids_of(blob, kind):
    """Los ids de un store, sea lista o dict."""
    try:
        d = json.loads(blob)
    except Exception:
        return None
    if isinstance(d, dict):
        d = d.get("rules") or d.get("claims") or d.get("incidents") or d.get("algorithms") or d
        if isinstance(d, dict):
            return set(map(str, d.keys()))
    if isinstance(d, list):
        return {str(x.get("id")) for x in d if isinstance(x, dict) and x.get("id") is not None}
    return None


def corpus():
    txt = {}
    for pat in ("**/*.py", "**/*.md", "**/*.json"):
        for f in glob.glob(os.path.join(ROOT, pat), recursive=True):
            rel = os.path.relpath(f, ROOT).replace("\\", "/")
            if "__pycache__" in rel or rel.startswith(".git/"):
                continue
            try:
                txt[rel] = io.open(f, encoding="utf-8", errors="replace").read()
            except OSError:
                pass
    return txt


def main():
    a = sys.argv[1:]
    since = a[a.index("--since") + 1] if "--since" in a else None
    if not since:
        today = time.strftime("%Y-%m-%d")
        n = len([l for l in git("log", "--since=%s 00:00" % today,
                                "--pretty=format:%h").splitlines() if l.strip()])
        if n == 0:
            print("Sin commits hoy. Nada que medir.")
            return 0
        since = "HEAD~%d" % n

    print("=" * 78)
    print("DISCIPLINA DE PRODUCCION -- ventana: %s..HEAD" % since)
    print("=" * 78)

    fails = []

    # ---- 1. retiradas
    print("\n  1. RETIRADAS DE LOS STORES")
    gone_total = 0
    for path, kind in STORES.items():
        before, after = git("show", "%s:%s" % (since, path)), git("show", "HEAD:%s" % path)
        if not before or not after:
            print("     %-38s (no comparable en esta ventana)" % os.path.basename(path))
            continue
        b, aft = ids_of(before, kind), ids_of(after, kind)
        if b is None or aft is None:
            print("     %-38s (no parseable)" % os.path.basename(path))
            continue
        gone = sorted(b - aft)
        if not gone:
            print("     %-38s sin retiradas  (+%d nuevos)" % (os.path.basename(path), len(aft - b)))
            continue
        gone_total += len(gone)
        # evidencia = el id desaparecido nombrado en los mensajes de commit de la ventana
        msgs = git("log", "%s..HEAD" % since, "--pretty=format:%B")
        sin_ev = [g for g in gone if g not in msgs]
        print("     %-38s %d RETIRADO(S): %s" % (os.path.basename(path), len(gone),
                                                 ", ".join(gone[:6])))
        if sin_ev:
            fails.append(("retirada sin evidencia", kind,
                          "%d %s(s) desaparecieron y ningun mensaje de commit los nombra: %s"
                          % (len(sin_ev), kind, ", ".join(sin_ev[:6]))))
    if not gone_total:
        print("     -> ninguna retirada en la ventana.")

    # ---- 2. producido vs conectado
    print("\n  2. PRODUCIDO FRENTE A CONECTADO")
    new = [l.strip() for l in git("diff", "--name-only", "--diff-filter=A", "%s..HEAD" % since).splitlines()
           if l.strip() and not IGNORE_NEW.search(l.strip())]
    if not new:
        print("     Ningun fichero nuevo relevante en la ventana.")
    else:
        txt = corpus()
        loose = []
        for f in new:
            base = os.path.basename(f)
            who = [k for k, t in txt.items() if k != f and (base in t or f in t)]
            if not who:
                loose.append(f)
        print("     creados: %d   conectados: %d   SUELTOS: %d"
              % (len(new), len(new) - len(loose), len(loose)))
        for f in loose:
            print("        %s" % f)
        if loose:
            fails.append(("produccion desconectada", "ficheros",
                          "%d de %d ficheros creados en la ventana no los referencia nadie"
                          % (len(loose), len(new))))

    print("\n" + "-" * 78)
    if fails:
        for kind, what, why in fails:
            print("  [FALLA] %-26s %s" % (kind, why))
        print()
        print("  Una retirada sin evidencia es una perdida, no una limpieza: 'no se cita' o")
        print("  'no se ejecuta' es un PROXY, no evidencia. La disciplina es SUPERSEDE (CP-002).")
        print("  Y un fichero que nace suelto casi nunca se conecta despues: el momento barato")
        print("  de conectarlo es ahora, no dentro de un mes.")
        return 1

    print("  OK -- nada retirado sin evidencia, y todo lo creado tiene quien lo referencie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
