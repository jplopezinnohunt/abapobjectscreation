"""Promote a fact into the brain WITHOUT the two dedup failures that happened in one session.

WHY THIS EXISTS
    Session 98 failed to deduplicate twice, in mirror-image forms, and both were mechanical:

      · checking for an existing rule by EXACT ID missed
        feedback_a_dead_agent_leaves_a_valid_different_file and a near-duplicate was written;
      · over-correcting, a CONCEPT search reported the three-axis method and the authorship
        lesson as already present. 'cardinality' had matched a rule about ROWSKIPS rejection
        and 'authorship' a rule about not modifying other people's code. Both false, and both
        would have left real knowledge in the chat.

    The second is the worse one: a duplicate is visible and somebody eventually removes it,
    while a false "already covered" ENDS THE SEARCH and nobody ever learns to look.

WHAT THIS DOES DIFFERENTLY
    It never answers yes or no. It PRINTS the candidate records it found — id, store and the
    first line of each — and makes a human (or the model) look at them before writing. Two
    lines of output turn a boolean into evidence.

    It searches all three stores at once, because a fact can already live as a claim, as a
    rule, or as an algorithm memory, and checking only one is how the first duplicate got in.

USAGE
    python brain_v2/promote.py "concept words to search for"
    python brain_v2/promote.py --id feedback_some_rule_id
"""
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

STORES = [
    ("claims", "brain_v2/claims/claims.json", "claims", "id", ("claim", "resolution_notes")),
    ("rules", "brain_v2/agent_rules/feedback_rules.json", "rules", "id",
     ("rule", "why", "how_to_apply")),
    ("memory", "brain_v2/methods/algorithm_memory.json", "memories", "subject",
     ("fact", "implication")),
]
STOP = set("the a an of to in on is are and or for with that this it its from by as at be "
           "was were not no una que los las del con por para una the".split())


def load(path, key):
    d = json.load(io.open(os.path.join(ROOT, path), encoding="utf-8"))
    return d[key] if isinstance(d, dict) and key in d else d


def terms(q):
    return [w for w in re.findall(r"[a-z0-9_]{4,}", q.lower()) if w not in STOP]


def main(argv):
    if "--id" in argv:
        wanted = argv[argv.index("--id") + 1]
        for label, path, key, idf, _ in STORES:
            for r in load(path, key):
                if str(r.get(idf, "")).lower() == wanted.lower():
                    print("EXISTE en %s: %s" % (label, r.get(idf)))
                    return 1
        print("no existe ese id — pero eso NO significa que el hecho no este.")
        print("Busca tambien por concepto: python brain_v2/promote.py \"<palabras>\"")
        return 0

    q = " ".join(a for a in argv if not a.startswith("--"))
    if not q:
        print(__doc__.strip().splitlines()[-3])
        return 2
    tw = terms(q)
    if not tw:
        print("nada que buscar tras quitar palabras vacias")
        return 2
    print("BUSCANDO: %s" % ", ".join(tw))
    print("=" * 74)

    total = 0
    for label, path, key, idf, textf in STORES:
        # A 1-of-4 term match is noise, and noise is what makes a reader stop reading —
        # which recreates the very failure this tool exists to prevent. Require most of
        # the terms, so a hit means something.
        floor = max(2, (len(tw) + 1) // 2)
        scored = []
        for r in load(path, key):
            blob = " ".join(str(r.get(f) or "") for f in textf).lower()
            hits = [w for w in tw if w in blob]
            if len(hits) >= floor:
                scored.append((len(hits), hits, r))
        scored.sort(key=lambda x: -x[0])
        if not scored:
            print("\n%s: SIN COINCIDENCIAS (umbral %d de %d terminos)"
                  % (label.upper(), floor, len(tw)))
            continue
        print("\n%s: %d registro(s) tocan el concepto" % (label.upper(), len(scored)))
        for n, hits, r in scored[:5]:
            first = ""
            for f in textf:
                if r.get(f):
                    first = re.sub(r"\s+", " ", str(r[f]))[:150]
                    break
            print("  [%d/%d] %s" % (n, len(tw), r.get(idf)))
            print("        coincide en: %s" % ", ".join(hits))
            print("        %s..." % first)
        if len(scored) > 5:
            print("  ... y %d mas" % (len(scored) - 5))
        total += len(scored)

    print("\n" + "=" * 74)
    if total > 40:
        print("DEMASIADAS coincidencias (%d): los terminos son genericos y el resultado no" % total)
        print("distingue nada. Vuelve a buscar con las palabras ESPECIFICAS del hecho —")
        print("nombres de objeto, de campo, de mecanismo — no con vocabulario de metodo.")
    elif total:
        print("LEE los de arriba antes de escribir nada. Un acierto de subcadena NO es")
        print("cobertura: en s098 'cardinality' casaba con una regla sobre ROWSKIPS y")
        print("'authorship' con una sobre no tocar codigo ajeno. Ninguna de las dos era.")
    else:
        print("nada toca el concepto en los tres almacenes — hueco real, escribelo.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
