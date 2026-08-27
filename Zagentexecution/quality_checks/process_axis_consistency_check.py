"""
process_axis_consistency_check.py — el eje de PROCESO vive en tres sitios, ¿coinciden?

`validate_ontology.py` comprueba bidireccionalmente los DOMINIOS, y por eso los dominios
estan limpios: 0 huerfanos. El eje de PROCESO no lo comprobaba nadie, y por eso habia
derivado en los tres sitios a la vez, cada uno por su lado:

    domains[X].primary_processes          lo que publica el BRAIN_INDEX
    process_map[P].domains                la lista escrita a mano
    ontology.domains[i].process_axis      el eje declarado en la ontologia

Medido en s106 antes de reconciliar: los SIETE procesos discrepaban, ninguno era
subconjunto de otro, y `process_map` ni siquiera tenia entrada para A2R ni para O2C.
`Payment_BCM` faltaba en H2R en DOS de las tres fuentes -- y falta justamente ahi porque
la nomina PAGA, que es el ejemplo con el que el dueno formulo la regla:

    UN SUBDOMINIO PUEDE PERTENECER A VARIOS PROCESOS. Eso no es un error: es la razon
    por la que el campo existe. Coincide con lo verificado en OCEL 2.0 (braintoolbox
    seccion 1b): forzar un solo concepto de caso produce convergencia y divergencia.

Por eso la reconciliacion correcta es UNION, y por eso esta puerta compara IGUALDAD de
los tres conjuntos: cualquier fuente que sepa algo que las otras no, es deriva.

⛔ LOS ALIAS SE RESUELVEN, SIEMPRE. Los tres stores usan vocabularios distintos --
`Treasury` / `Treasury_EBS`, `PSM` / `PSM_FM`, `HR-Workflows` / `HR_Workflows` -- y
comparar en crudo inventa discrepancias que no existen. Paso el mismo dia: una medida sin
resolver alias dio "5 referencias rotas" en P2P y eran CERO. Se resuelven las DOS tablas:
`aliases` y `subdomain_aliases` (Cost_Recovery_CRP es dominio de primer nivel en
domains.json y SUBDOMINIO de PSM_FM en el capability model -- decision declarada, no
defecto).

Solo LECTURA. No arregla: informa y falla.

Uso:
    python process_axis_consistency_check.py
"""

QUALITY_CHECK = {
    "tier": "gate",           # vocabulario real: gate | analysis | live | quarantined | library
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "needs": "nada",
    "what": "las 3 fuentes del eje de proceso declaran los mismos dominios por proceso",
    "args": "(ninguno)",
}

import json
import os
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOM = os.path.join(ROOT, "brain_v2", "domains", "domains.json")
ONT = os.path.join(ROOT, "brain_v2", "capability_model", "ontology.json")


# NO se resuelven alias a mano: brain_v2/canonical.py ES el lookup, y su docstring lleva
# desde s097 pidiendo "Import it; do not re-derive it". La primera version de esta puerta
# (s106) se lo salto y construyo su propio mapa -- el mismo defecto que el lint
# canonical_usage_lint.py marca, cometido por quien escribio el lint. Corregido aqui.
# `canonical_or_parent` es la variante opt-in que ademas colapsa subdominios declarados
# (Cost_Recovery_CRP -> PSM_FM), que es justo lo que esta comparacion necesita.
sys.path.insert(0, os.path.join(ROOT, "brain_v2"))
try:
    from canonical import canonical_or_parent as _canon   # noqa: E402
except ImportError:                                        # degradar, nunca cegar
    def _canon(x):
        return x


def main():
    try:
        d = json.load(open(DOM, encoding="utf-8"))
        o = json.load(open(ONT, encoding="utf-8"))
    except OSError as e:
        print("no puedo leer los stores: %s" % e)
        return 1

    R = lambda s: {_canon(x) for x in s}

    A, B, C = defaultdict(set), {}, defaultdict(set)
    for n, v in (d.get("domains") or {}).items():
        if isinstance(v, dict):
            for p in (v.get("primary_processes") or []):
                A[p].add(n)
    for k, v in (d.get("process_map") or {}).items():
        if isinstance(v, dict) and "domains" in v:
            B[k] = set(v["domains"])
    for e in (o.get("domains") or []):
        for p in (e.get("process_axis") or []):
            C[p].add(e["canonical_key"])

    # nombres que ninguna tabla de alias resuelve: eso es deuda de ontologia, no deriva
    from canonical import is_declared  # noqa: PLC0415
    crudos = {x for s in list(A.values()) + list(B.values()) for x in s}
    sin_resolver = sorted(x for x in crudos if _canon(x) == x and not is_declared(x))

    procesos = sorted(set(A) | set(B) | set(C))
    print("=" * 74)
    print("EJE DE PROCESO — 3 fuentes, %d procesos, alias resueltos" % len(procesos))
    print("=" * 74)
    malos = []
    for p in procesos:
        a, b, c = R(A[p]), R(B.get(p, set())), R(C[p])
        union = a | b | c
        ok = a == b == c
        print("  %-5s %2d dominios   %s" % (p, len(union), "OK" if ok else "DISCREPA"))
        if not ok:
            malos.append(p)
            for nom, s in (("primary_processes", a), ("process_map", b),
                           ("ontology.process_axis", c)):
                falta = sorted(union - s)
                if falta:
                    print("          falta en %-22s %s" % (nom, falta))

    if sin_resolver:
        print("\n  nombres sin resolver por ninguna tabla de alias: %s" % sin_resolver)
        print("  (deuda de ONTOLOGIA: no son deriva, son nombres que nadie ha declarado)")

    print("-" * 74)
    if malos or sin_resolver:
        print("FAIL — %d proceso(s) discrepan: %s" % (len(malos), malos or "-"))
        print("  El eje de proceso es UNION: si una fuente lo afirma, cuenta. Reconcilia")
        print("  ANADIENDO a las que faltan; no quites de la que lo tenia.")
        return 1
    print("OK — las 3 fuentes coinciden en los %d procesos." % len(procesos))
    print("  Recordatorio: `domains` dice QUIEN participa, NO en que orden ni donde estan")
    print("  las puertas. Que BCM este EN MEDIO de P2P no es representable hoy (H137).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
