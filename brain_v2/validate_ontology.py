"""Gate the canonical vocabulary (contract C-1) — step 0 of rebuild_all.py.

Every `domain` value in the stores must resolve, by EXACT lookup, to a key declared in
brain_v2/capability_model/ontology.json. No token matching, no fuzzy fallback.
Exit 1 (and the rebuild stops) if any value is unknown: the brain must not be
materialized on an inconsistent vocabulary.

Usage: python brain_v2/validate_ontology.py
"""
import json
import sys
from pathlib import Path

BRAIN_V2 = Path(__file__).parent
ONTOLOGY = BRAIN_V2 / "capability_model" / "ontology.json"


def load_index(path=ONTOLOGY):
    """alias/canonical/subdomain/cross-cutting key -> (canonical_key, kind)."""
    ont = json.load(open(path, encoding="utf-8"))
    idx = {}

    def put(key, canonical, kind):
        if key in idx and idx[key][0] != canonical:
            raise SystemExit("ONTOLOGY COLLISION: %r maps to both %s and %s"
                             % (key, idx[key][0], canonical))
        idx[key] = (canonical, kind)

    for d in ont["domains"]:
        put(d["canonical_key"], d["canonical_key"], "domain")
        for a in d.get("aliases", []):
            put(a, d["canonical_key"], "alias")
    for a, sub in ont.get("subdomain_aliases", {}).items():
        put(a, sub["canonical_key"], "subdomain")
    for c in ont.get("cross_cutting_keys", []):
        put(c["key"], c.get("resolves_to") or c["key"], "cross_cutting")
    return ont, idx


def sources():
    """(label, [domain values]) for every store that carries a `domain`."""
    claims = json.load(open(BRAIN_V2 / "claims" / "claims.json", encoding="utf-8"))
    claims = claims.get("claims", claims) if isinstance(claims, dict) else claims
    vals = []
    for c in claims:
        d = c.get("domain")
        vals.extend(d if isinstance(d, list) else [d] if d else [])
    yield "claims/claims.json (domain)", vals
    reg = json.load(open(BRAIN_V2 / "domains" / "domains.json", encoding="utf-8"))
    yield "domains/domains.json (keys)", list(reg.get("domains", {}))
    cm = json.load(open(BRAIN_V2 / "capability_model" / "capability_model.json", encoding="utf-8"))
    yield "capability_model/capability_model.json (domains keys)", list(cm.get("domains", {}))


def orphan_domains(ont):
    """Dominios DECLARADOS canonicos que no tienen registro en domains.json.

    El validador solo miraba una direccion -- que lo que esta en los stores resuelva contra la
    ontologia. Nunca comprobo la contraria, y por eso Closing_Activities estuvo declarado y sin
    registro desde s097 hasta s102: sus 4 documentos, 17 claims, 2 companions y su incidente
    colgaban de nada, y preguntar por "el dominio de la revaluacion" no devolvia dominio.
    Un dominio declarado sin registro no es media entrada: es conocimiento que se pierde.
    """
    reg = set(json.load(open(BRAIN_V2 / "domains" / "domains.json", encoding="utf-8"))
              .get("domains", {}))
    sub = json.load(open(BRAIN_V2 / "capability_model" / "ontology.json",
                         encoding="utf-8")).get("subdomain_aliases", {})
    orphans = []
    for d in ont["domains"]:
        keys = {d["canonical_key"]} | set(d.get("aliases") or [])
        keys |= {k for k, v in sub.items() if v.get("canonical_key") == d["canonical_key"]}
        if not (keys & reg):
            orphans.append(d["canonical_key"])
    return orphans


def main():
    ont, idx = load_index()
    print("[ontology v%s] %d canonical domains, %d aliases, %d cross-cutting keys, %d dimensions"
          % (ont["_version"], len(ont["domains"]), sum(len(d["aliases"]) for d in ont["domains"]),
             len(ont["cross_cutting_keys"]), len(ont["dimensions"])))
    unresolved, resolved, non_domain = {}, set(), set()
    for label, values in sources():
        bad = sorted({v for v in values if v not in idx})
        ok = {v for v in values if v in idx}
        resolved |= {idx[v][0] if isinstance(idx[v][0], str) else v for v in ok if idx[v][1] != "cross_cutting"}
        non_domain |= {v for v in ok if idx[v][1] == "cross_cutting"}
        print("  %-52s %3d distinct, %d unresolved" % (label, len(set(values)), len(bad)))
        if bad:
            unresolved[label] = bad
    if non_domain:
        print("  NOTE: %d registered non-domain keys in use (frozen list, see "
              "ontology.cross_cutting_keys): %s" % (len(non_domain), ", ".join(sorted(non_domain))))
    if unresolved:
        print("\nFAIL - vocabulary not canonical. Declare these in ontology.json "
              "(as an alias, a subdomain_alias or a cross_cutting_key) or fix the store:")
        for label, bad in unresolved.items():
            for v in bad:
                print("  %s :: %r" % (label, v))
        return 1
    orphans = orphan_domains(ont)
    if orphans:
        print("\nFAIL - dominios DECLARADOS sin registro en domains/domains.json. Un dominio "
              "declarado y sin registro pierde sus docs, claims, companions e incidentes:")
        for k in orphans:
            print("  ontology.domains :: %r sin entrada (ni por alias ni por subdominio)" % k)
        return 1
    print("  %-52s %3d declarados, 0 huerfanos"
          % ("bidireccional: declarado -> registro", len(ont["domains"])))
    print("\nOK - every domain value resolves. %d canonical domains referenced across %d stores."
          % (len(resolved), len(list(sources()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
