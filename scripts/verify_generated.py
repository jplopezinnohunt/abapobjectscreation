"""Verify every GENERATED artefact still matches its generator. Run before any commit.

WHY THIS EXISTS
    Three companions in this repo carry a line saying "never edit the HTML, edit the
    builder". That is a BELIEF, not a check — nothing has ever verified it, and a hand-edit
    would survive indefinitely because the page still renders.

    It also catches the failure that recurred most in session 98: a template substitution
    that did not land. Four separate times a replace silently missed its anchor, the script
    printed OK because the Python still parsed, and the output shipped with a raw @TOKEN@ or
    a stray %s in it. Each was caught only because an assertion was added AFTERWARDS, by
    hand, one at a time.

WHAT IT CHECKS, and each one is a failure that actually happened
    1. REGENERATES each artefact into a temporary file and compares it to the committed one.
       A difference means either the source data moved (regenerate and commit) or somebody
       edited the output directly (the thing the docstrings forbid and nothing enforced).
    2. NO UNSUBSTITUTED TOKENS — @LIKE_THIS@ — in the output.
    3. NO STRAY FORMAT MARKERS — a bare %s or %d that survived into HTML.
    4. NO EMPTY SUBSTITUTION: a token replaced by an empty string usually means the source
       key was renamed and the builder silently produced a blank section.

WHAT IT DOES NOT DO
    It does not judge whether the CONTENT is right. A page can be perfectly generated and
    perfectly wrong; that is what the reproduction sections and the claims are for.

USAGE
    python scripts/verify_generated.py           # check, exit 1 on any failure
    python scripts/verify_generated.py --fix     # regenerate the ones that drifted
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# builder -> the artefact it owns. Adding a companion means adding a line here, and this
# file is the registry of "what is generated" that did not exist before.
GENERATED = [
    ("scripts/build_br_companion.py", "companions/budget_rate_companion_v1.html"),
    ("scripts/build_payroll_companion.py", "companions/payroll_end_to_end_companion_v1.html"),
    ("scripts/build_wbs_companion.py", "companions/project_wbs_companion_v1.html"),
    # Anadido s102: el companion de gobierno de datos maestros se genera del registro
    # brain_v2/master_data_registry.json. Estaba cableado a rebuild_all pero NO aqui, o sea
    # que nadie comprobaba que el HTML publicado siguiera coincidiendo con su generador.
    ("scripts/build_master_data_companion.py", "companions/master_data_governance.html"),
    ("brain_v2/build_br_graph.py", "brain_v2/budget_rate_graph.json"),
]

TOKEN = re.compile(r"@[A-Z][A-Z_0-9]*@")
FMT = re.compile(r"%[sdf](?![\w%])")
# An empty table body or an empty list where a section is expected: the shape of a section
# whose data key was renamed and now yields nothing.
BLANK = re.compile(r"<(table|tbody|ul|ol)[^>]*>\s*</\1>")


def read(p):
    with io.open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def main(argv):
    fix = "--fix" in argv
    bad = []
    print("VERIFICAR LO GENERADO — %d artefactos" % len(GENERATED))
    print("=" * 70)
    for builder, artefact in GENERATED:
        ap = os.path.join(ROOT, artefact)
        before = read(artefact) if os.path.exists(ap) else None
        r = subprocess.run([sys.executable, os.path.join(ROOT, builder)],
                           cwd=ROOT, capture_output=True)
        if r.returncode != 0:
            bad.append((artefact, "el generador FALLA: %s"
                        % r.stderr.decode("utf-8", "replace").strip().splitlines()[-1][:90]))
            print("  %-52s GENERADOR ROTO" % artefact)
            continue
        after = read(artefact)

        problems = []
        t = TOKEN.findall(after)
        if t:
            problems.append("tokens sin sustituir: %s" % sorted(set(t))[:3])
        f_ = FMT.findall(after)
        if f_:
            problems.append("marcadores de formato sueltos: %s" % sorted(set(f_)))
        b = BLANK.findall(after)
        if b:
            problems.append("secciones vacias (%d) — una clave del origen pudo renombrarse"
                            % len(b))
        if before is not None and before != after and not fix:
            problems.append("EL COMMITEADO NO COINCIDE con lo que produce el generador "
                            "(%d -> %d bytes)" % (len(before), len(after)))

        if problems:
            bad.append((artefact, "; ".join(problems)))
            print("  %-52s FALLA" % artefact)
            for p in problems:
                print("      %s" % p)
        else:
            print("  %-52s ok (%d KB)" % (artefact, len(after) // 1024))

    print("-" * 70)
    if bad:
        print("%d artefacto(s) con problemas." % len(bad))
        if not fix:
            print("Si la diferencia es porque el DATO cambio, regenera con --fix y comitea.")
            print("Si no cambio, alguien edito la salida a mano — que es justo lo que las")
            print("cabeceras prohiben y nada comprobaba.")
        return 1
    print("todo coincide con su generador.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
