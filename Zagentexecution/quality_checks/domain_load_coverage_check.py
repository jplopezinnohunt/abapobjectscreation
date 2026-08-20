# -*- coding: utf-8 -*-
"""Escribiste en un dominio que nunca cargaste?

POR QUE EXISTE
    2026-08-20. La sesion cargo bien el dominio 'purpose of payment' al arrancar. Despues la
    conversacion se movio a BANCOS -- rol, topologia, extractos -- y nunca se recargo nada.
    Resultado: se midio contra el Gold DB que "SOG01 no tiene extractos bancarios" y estuvo a
    un paso de publicarse, cuando knowledge/domains/Treasury/bank_statement_ebs_architecture.md
    lo tenia medido y REFUTADO desde la sesion #029, en una seccion titulada literalmente
    "Critical Correction".

    La regla #208 (feedback_load_the_domain_before_you_reason) cubre el ARRANQUE: en cuanto se
    nombra un tema, carga el dominio. Su punto ciego es el MEDIO de la conversacion, que es
    justo donde el tema deriva sin que nadie lo anuncie -- y donde el coste es mayor, porque
    para entonces ya hay artefactos publicados.

    Mecaniza feedback_reload_the_domain_when_the_topic_moves (CRITICAL).

COMO LO SABE, sin instrumentar nada
    TOCADO   los dominios con ficheros modificados o nuevos segun git, en esta rama y sin
             commitear, mas los de los commits de hoy.
    CARGADO  los temas que load_domain.py dejo en su directorio de trabajo, filtrados por
             fecha de hoy: cada carga crea <tmp>/brain_domain_loads/<topic>/part_01.md.

    Un dominio TOCADO y no CARGADO no es necesariamente un error -- corregir una errata no
    exige cargar 600K tokens. Por eso el check informa y no bloquea salvo que el dominio se
    haya tocado a lo grande.

Read-only. Exit 0 = nada que senalar. Exit 1 = se escribio EN SERIO en un dominio sin cargar.
"""

# --- self-declaration, read by quality_checks/run_all.py -------------------
QUALITY_CHECK = {
    "tier": "gate",       # gate | live | analysis | quarantined
    "needs": "files",     # gold_db | rfc_p01 | files
    "what": "dominios escritos sin haber sido cargados (feedback_reload_the_domain_when_the_topic_moves)",
}
# --------------------------------------------------------------------------
import collections
import glob
import os
import re
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOADS = os.path.join(tempfile.gettempdir(), "brain_domain_loads")

# Por debajo de esto es una errata o un enlace, no "trabajar en el dominio".
SERIOUS_LINES = 40
# Como se llama la carga frente a como se llama la carpeta del dominio.
ALIAS = {
    "treasury": {"treasury", "payment", "payment_bcm", "bank", "ebs"},
    "payment": {"payment", "treasury", "payment_bcm"},
    "psm": {"psm", "psm_fm"},
    "procurement": {"procurement", "procurement_p2p", "p2p"},
    "hcm": {"hcm", "hr-workflows", "py-finance"},
}


def _git(*a):
    try:
        return subprocess.check_output(["git"] + list(a), cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode("utf-8", "replace")
    except Exception:
        return ""


def domains_touched():
    """Dominio -> lineas cambiadas. Sin commitear + lo commiteado hoy."""
    out = collections.Counter()
    today = time.strftime("%Y-%m-%d")
    diffs = [_git("diff", "--numstat"), _git("diff", "--numstat", "--cached")]
    since = _git("log", "--since=%s 00:00" % today, "--numstat", "--pretty=format:")
    if since:
        diffs.append(since)
    for d in diffs:
        for line in d.splitlines():
            p = line.split("\t")
            if len(p) != 3:
                continue
            add, dele, path = p
            m = re.match(r"knowledge/domains/([^/]+)/", path.replace("\\", "/"))
            if not m:
                continue
            n = sum(int(x) for x in (add, dele) if x.isdigit())
            out[m.group(1)] += n
    return out


def domains_loaded():
    """Temas que load_domain.py dejo hoy en su directorio de trabajo."""
    got = set()
    if not os.path.isdir(LOADS):
        return got, False
    cutoff = time.time() - 20 * 3600
    for d in glob.glob(os.path.join(LOADS, "*")):
        if not os.path.isdir(d):
            continue
        parts = glob.glob(os.path.join(d, "part_*.md"))
        if parts and max(os.path.getmtime(x) for x in parts) >= cutoff:
            got.add(os.path.basename(d).lower())
    return got, True


def covers(loaded, domain):
    dl = domain.lower()
    for t in loaded:
        tn = t.replace(" ", "_")
        if dl in tn or tn in dl:
            return t
        for k, fam in ALIAS.items():
            if k in tn and dl in fam:
                return t
    return None


def main():
    touched = domains_touched()
    loaded, have_dir = domains_loaded()

    print("=" * 78)
    print("COBERTURA DE CARGA DE DOMINIO -- escribiste donde no leiste?")
    print("=" * 78)
    if not touched:
        print("\nNingun fichero de knowledge/domains/ tocado hoy. Nada que comprobar.")
        return 0
    if not have_dir:
        print("\nNo hay directorio de cargas (%s)." % LOADS)
        print("No se puede distinguir 'no cargo' de 'cargo en otra maquina'. SKIPPED, no PASS.")
        return 0

    print("\n  cargados hoy : %s" % (", ".join(sorted(loaded)) or "NINGUNO"))
    print("  tocados      : %d dominio(s)\n" % len(touched))

    bad = []
    for dom, n in touched.most_common():
        hit = covers(loaded, dom)
        mark = "OK  cargado como '%s'" % hit if hit else (
            "SIN CARGAR" + ("  <== y se escribio en serio" if n >= SERIOUS_LINES else "  (cambio menor)"))
        print("    %-26s %5d lineas   %s" % (dom, n, mark))
        if not hit and n >= SERIOUS_LINES:
            bad.append((dom, n))

    print()
    if bad:
        print("  FALLA. Se escribio en serio en %d dominio(s) que nunca se cargaron:" % len(bad))
        for dom, n in bad:
            print("     %s (%d lineas)  ->  python brain_v2/load_domain.py %s" % (dom, n, dom.lower()))
        print()
        print("  No es burocracia: el 2026-08-20 esto habria evitado publicar que un banco con")
        print("  1,9M de pagos no recibe extractos, teniendo la refutacion escrita en el propio")
        print("  dominio bajo el titulo 'Critical Correction'. Cargar es mas barato que corregir.")
        return 1
    print("  OK -- todo dominio escrito en serio estaba cargado.")
    print("  (Un cambio menor sin carga no falla: corregir una errata no exige 600K tokens.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
