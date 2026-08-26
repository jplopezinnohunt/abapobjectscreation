"""A claim that NAMES an entity but does not LINK it is invisible to the entity index.

WHY THIS EXISTS
---------------
The entity index (s099) made knowledge reachable by thing instead of by wording, and it is
built strictly from TYPED link fields -- claims.related_objects, incidents.related_*,
companion entities. That strictness is deliberate: scraping prose is how noise gets in.

But it puts the whole index at the mercy of whoever wrote the record. Mention T015L in the
prose of a claim and forget to add it to related_objects, and that claim is invisible to
`graph_queries.py entity T015L` forever. Nothing notices. The knowledge is stored, correct,
and unreachable -- the exact failure mode of this whole session, one level down.

So this compares the two: for every claim, which KNOWN entities appear in its prose but not
in its related_objects. Known means already in the entity index -- never a guess at what
looks like an SAP name, which would flood the report with false positives from ordinary
words in capitals.

It reports; it does not edit. Adding a link changes what the index returns, and that is a
judgement about meaning: a claim can mention a table as a contrast ("unlike BSEG...") without
being about it. The check surfaces the candidates and a human decides.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": "claims naming a known entity in prose without linking it in related_objects",
}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline import verdict  # noqa: E402  (sibling module)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
CLAIMS = REPO / "brain_v2" / "claims" / "claims.json"
INDEX = REPO / "brain_v2" / "entity_index.json"

# Only entities specific enough that appearing in prose really means "this claim is about it".
# Short or dictionary-like names (FUND, SYSTEM, PAYMENT) match everywhere and mean nothing.
PERSON = re.compile(r"^[A-Z]_[A-Z]{2,}$")   # C_LOPEZ, N_MENARD
MIN_LEN = 4
GENERIC = {
    "SYSTEM", "PAYMENT", "TRANSPORT", "TREASURY", "BUDGET", "VALIDATION", "COMPANY CODE",
    "BRAIN", "AUDIT", "BASIS", "CASH", "CLOSING", "COMPLIANCE", "DERIVATION", "DONOR",
    "STEM", "FUND", "CONNECTIVITY", "BUSINESS AREA", "TAXONOMY", "UPGRADE", "MATURITY",
}


def main():
    if not CLAIMS.exists() or not INDEX.exists():
        print("SKIPPED - claims.json or entity_index.json missing. Not a pass: nothing "
              "verified. Run python brain_v2/build_entity_index.py")
        return 3

    def specific(e):
        """Specific enough that seeing it in prose really means the claim is about it."""
        if len(e) < MIN_LEN or e in GENERIC:
            return False
        # SAP usernames are not objects. They are in the index because some record listed a
        # person in related_objects, and chasing them here would push the index toward being
        # a people-tracker -- which the PMO flags as sensitive under H71 (a capability is not
        # proven fraud; route through controls, do not broadcast names).
        if PERSON.match(e):
            return False
        # Incident ids belong in related_incidents, not related_objects. Counting them as a
        # missing OBJECT link asks for the wrong fix.
        if e.startswith("INC-"):
            return False
        # an underscore (YTFI_PPC_STRUC) or an embedded digit (T015L, BSEG2) marks a real
        # object name; a bare capitalised word does not
        return "_" in e or any(c.isdigit() for c in e)

    known = {e for e in json.loads(INDEX.read_text(encoding="utf-8")).get("entities", {})
             if specific(e)}

    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    if isinstance(claims, dict):
        claims = claims.get("claims", [])

    print("=" * 76)
    print("typed-link coverage - is what a claim TALKS ABOUT also what it LINKS TO?")
    print("=" * 76)
    print("entities specific enough to test: {}".format(len(known)))
    print("claims: {}".format(len(claims)))

    gaps = []
    for c in claims:
        if not isinstance(c, dict):
            continue
        prose = " ".join(str(c.get(f) or "") for f in ("claim", "resolution_notes"))
        if not prose:
            continue
        linked = {str(o).strip().upper() for o in (c.get("related_objects") or [])}
        # UN JUICIO QUE NO SE GUARDA SE VUELVE A PEDIR.
        #
        # Este check dice "la prosa nombra una entidad que related_objects no tiene", y para
        # muchas la respuesta correcta es NO ENLAZARLA: el autor de la medida (JP_LOPEZ suele
        # ser quien la hizo, no el sujeto), un ejemplo ilustrativo (FBL1N como uno de los pares
        # dominantes de una muestra), o un contraste ("no es X sino Y"). Enlazarlas ensucia
        # `graph_queries.py entity <nombre>`, que es como se busca: si al preguntar por una
        # tabla salen 40 claims que solo la mencionan, la consulta deja de servir.
        #
        # Sin esta exclusion el check las señalaria PARA SIEMPRE, y un gate que repite un aviso
        # ya resuelto acaba ignorandose entero. Se excluye CON MOTIVO ESCRITO en el propio
        # claim (`_no_enlazado_a_proposito`), igual que las demas puertas de este repo: una
        # exclusion sin motivo es un hueco disfrazado.
        a_proposito = {str(k).strip().upper()
                       for k in (c.get("_no_enlazado_a_proposito") or {})}
        words = set(re.findall(r"[A-Z][A-Z0-9_/-]{3,39}", prose.upper()))
        missing = sorted((words & known) - linked - a_proposito)
        if missing:
            gaps.append((c.get("id"), missing))

    print("claims naming a known entity they do not link: {}".format(len(gaps)))
    if gaps:
        print()
        for cid, miss in sorted(gaps, key=lambda x: -len(x[1]))[:15]:
            print("  claim {:>4}  missing links: {}".format(cid, ", ".join(miss[:8])))
        if len(gaps) > 15:
            print("  ... and {} more".format(len(gaps) - 15))
        print()
        print("Each is invisible to `graph_queries.py entity <name>` for the entity it")
        print("discusses. Add the link where the claim is genuinely ABOUT the entity; a")
        print("passing mention or a contrast is not, and should be left alone.")

    return verdict("claims_missing_typed_links", len(gaps), "claims with an unlinked entity",
                   "Prose the index cannot see is knowledge that cannot be found.")


if __name__ == "__main__":
    sys.exit(main())
