"""Index the knowledge by THING, not by wording.

WHY THIS EXISTS
---------------
JP, s099: "el conocimiento usas algoritmos especificos por tema para que no sea texto???"

Measured answer at that moment: no. The brain had exactly four indexes -- by_incident,
by_domain, uncertain_claims, superseded_claims -- and not one by entity. There was no way to
ask "what do we know about DMEE" or "who touches T015L" except a substring scan, and substring
scans fail on wording: 'purpose of payment' missed 91 claims that all say 'Payment Purpose
Code', and a filename grep for 'dmee' missed a companion with 965 mentions of it.

The galling part is that the structure was already there and pointing the wrong way. Claims
carry `related_objects`. Incidents carry `related_objects`, `related_tcodes`,
`related_programs`, `related_structures`. Companions carry extracted `entities`. Every one of
those is a typed link from an artifact TO a thing -- and nothing indexed it back from the
thing to the artifacts. So the answer to "what do we know about X" had to be reconstructed by
reading everything, every time.

This builds the reverse index. One generic pass over the structured fields that already
exist -- NOT one algorithm per topic, which would be fifty things to maintain and would rot
the moment a new topic appeared.

  entity -> { claims, incidents, companions, code, domains, rules }

Drill it with `python brain_v2/graph_queries.py entity <name>`.
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "entity_index.json"

# An entity is a NAME OF A THING: an SAP table, transaction, program, class, field, or one of
# our own Z*/Y* objects. Free prose is not an entity -- that is what the text search is for.
RE_ENTITY = re.compile(r"^[A-Z_][A-Z0-9_/-]{2,39}$")
STOPWORDS = {
    "THE", "AND", "FOR", "NOT", "ALL", "ANY", "NONE", "YES", "TRUE", "FALSE", "NULL",
    "TIER_1", "TIER_2", "TIER_3", "HIGH", "LOW", "MEDIUM", "CRITICAL", "OPEN", "CLOSED",
    "ACTIVE", "P01", "D01", "V01",  # systems are context, not subjects
}

OBJECT_FIELDS = ("related_objects", "related_tcodes", "related_programs",
                 "related_structures", "related_forms", "objects", "entities")


def norm(x):
    return str(x or "").strip().upper()


def entities_of(record):
    """Only the typed link fields. Never scraped from prose -- that is how noise gets in."""
    found = set()
    for f in OBJECT_FIELDS:
        v = record.get(f)
        if isinstance(v, str):
            v = [v]
        if not isinstance(v, list):
            continue
        for item in v:
            name = norm(item.get("name") if isinstance(item, dict) else item)
            if name and name not in STOPWORDS and RE_ENTITY.match(name):
                found.add(name)
    return found


def load(path, key=None):
    p = REPO / path if not str(path).startswith(str(REPO)) else Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    if key and isinstance(data, dict):
        data = data.get(key, [])
    if isinstance(data, dict):
        data = list(data.values())
    return data if isinstance(data, list) else []


def run():
    idx = defaultdict(lambda: defaultdict(list))

    for c in load("brain_v2/claims/claims.json"):
        if not isinstance(c, dict):
            continue
        for e in entities_of(c):
            idx[e]["claims"].append({"id": c.get("id"), "domain": c.get("domain"),
                                     "confidence": c.get("confidence"),
                                     "status": c.get("status")})

    for i in load("brain_v2/incidents/incidents.json", "incidents"):
        if not isinstance(i, dict):
            continue
        for e in entities_of(i):
            idx[e]["incidents"].append({"id": i.get("id"), "status": i.get("status"),
                                        "title": (i.get("title") or "")[:80]})

    for a in load("brain_v2/annotations/annotations.json", "annotations"):
        if not isinstance(a, dict):
            continue
        name = norm(a.get("object") or a.get("object_name"))
        if name and RE_ENTITY.match(name):
            idx[name]["annotations"].append({"kind": a.get("kind") or a.get("type"),
                                             "session": a.get("session")})

    # companions carry entities extracted from their own HTML -- lowercase vocabulary, not
    # object names, so they are indexed under the upper-cased term when it looks like one
    cg = REPO / "companions" / "companion_graph.json"
    if cg.exists():
        for n in json.loads(cg.read_text(encoding="utf-8")).get("nodes", []):
            for e in n.get("entities") or []:
                name = norm(e)
                if name and name not in STOPWORDS and RE_ENTITY.match(name):
                    idx[name]["companions"].append({"file": "companions/" + str(n.get("file")),
                                                    "title": n.get("title")})
            for iid in n.get("incidents") or []:
                idx[norm(iid)]["companions"].append({"file": "companions/" + str(n.get("file")),
                                                     "title": n.get("title")})

    inv = HERE / "code_inventory.json"
    if inv.exists():
        data = json.loads(inv.read_text(encoding="utf-8"))
        objs = data.get("objects", data) if isinstance(data, dict) else data
        objs = list(objs.values()) if isinstance(objs, dict) else objs
        for o in objs if isinstance(objs, list) else []:
            if not isinstance(o, dict):
                continue
            name = norm(o.get("name"))
            if name and RE_ENTITY.match(name):
                idx[name]["code"].append({"integrity": o.get("integrity"),
                                          "domains": o.get("domains")})

    out = {
        "_design": ("Reverse index: entity -> the artifacts that mention it. Built from the "
                    "TYPED link fields that already existed (claims.related_objects, "
                    "incidents.related_*, companion entities, code inventory) -- never "
                    "scraped from prose. One generic pass, not one algorithm per topic."),
        "entities": {k: dict(v) for k, v in sorted(idx.items())},
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    per = {k: sum(len(x) for x in v.values()) for k, v in idx.items()}
    top = sorted(per.items(), key=lambda x: -x[1])[:12]
    print("entity index: {} entities -> {}".format(len(idx), OUT.relative_to(REPO)))
    print("richest:")
    for k, n in top:
        kinds = ",".join(sorted(idx[k]))
        print("   {:22} {:>4} refs   [{}]".format(k[:22], n, kinds))
    return 0


if __name__ == "__main__":
    sys.exit(run())
