#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
load_domain.py — DOMAIN LOAD, the missing tier between BRAIN_INDEX and the full brain.

WHY THIS EXISTS
---------------
Session bootstrap is TIERED (s079): read `brain_v2/BRAIN_INDEX.md` (~4KB) and drill with
`graph_queries.py`. That is correct for orientation and wrong for WORKING. The index gives
headlines; the drills give fragments. Between the 4KB index and the ~400K-token brain there
was NOTHING — so every session that actually worked a topic had to re-discover its own
corpus by grepping, and the user had to ask for it. Measured on the DMEE topic: 5,946 lines
of domain docs + 1,006,032 chars of companions were sitting on disk, reachable only by
knowing they existed.

This is the missing step: name the topic, get EVERYTHING that topic knows, in one ordered
payload, chunked so it can actually be read.

USAGE
-----
    python brain_v2/load_domain.py dmee
    python brain_v2/load_domain.py Payment_BCM
    python brain_v2/load_domain.py "purpose of payment"
    python brain_v2/load_domain.py --list          # what topics/domains exist

Then READ the parts it prints, in order. That is the load.

CP-002: it does not compress. It orders, de-duplicates by path, and chunks.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chars per part. The Read tool caps at 25K TOKENS, and the ratio is not constant:
# MEASURED on this repo's own payload, dense JSON (claims/incidents, quoted keys, indentation)
# runs ~1.95 chars/token, while prose runs ~4. Sizing at 60K chars assumed prose and produced
# a 59,975-char part that Read refused at 30,766 tokens. Size for the WORST case:
# 40,000 / 1.95 ≈ 20.5K tokens, inside the cap with margin.
PART_CHARS = 40_000

OUT_ROOT = os.environ.get(
    "BRAIN_LOAD_DIR",
    os.path.join(
        os.environ.get("TEMP", os.path.join(ROOT, ".brain_loads")), "brain_domain_loads"
    ),
)

# ---------------------------------------------------------------------------
# Topic aliases. A topic is what the USER says; a domain is what the stores key on.
# Only aliases that are NOT discoverable by token search belong here.
# ---------------------------------------------------------------------------
ALIASES = {
    # List only the domains that OWN the topic. Adding adjacent ones (Treasury, EBS) to
    # 'dmee' inflated the load from 335K to 650K tokens with pages that only touch it —
    # the peripheral tier already names those, so nothing is lost by keeping this tight.
    "dmee": ["Payment", "Payment_BCM", "DMEE", "PPC"],
    "pmw": ["Payment", "Payment_BCM", "DMEE"],
    "bank file": ["Payment", "Payment_BCM", "DMEE"],
    "fichero de bancos": ["Payment", "Payment_BCM", "DMEE"],
    "payment": ["Payment", "Payment_BCM", "DMEE", "PPC", "Treasury", "BCM"],
    "pago": ["Payment", "Payment_BCM", "DMEE", "PPC", "Treasury", "BCM"],
    "ppc": ["PPC", "Payment", "Payment_BCM", "Procurement", "Procurement_P2P"],
    "purpose of payment": ["PPC", "Payment", "Payment_BCM", "Procurement", "Procurement_P2P"],
    "f110": ["Payment", "Payment_BCM", "DMEE", "Treasury"],
    "bcm": ["Payment_BCM", "BCM", "Payment", "Treasury"],
    "sepa": ["Payment", "Payment_BCM", "DMEE"],
    "citi": ["Payment", "Payment_BCM", "DMEE", "Treasury"],
    "cgi": ["Payment", "Payment_BCM", "DMEE"],
    "ebs": ["Treasury_EBS", "Treasury", "Payment"],
    "avc": ["PSM_FM", "PSM"],
    "budget": ["PSM_FM", "PSM", "CO"],
    "travel": ["Travel", "HCM"],
    "payroll": ["PY_Finance", "PY-Finance", "HCM", "PBC"],
    "transport": ["Transport_Intelligence", "CTS"],
}

# Adjacent domains: used ONLY for the cheap structured stores (claims, incidents, rules,
# code, gold, capability). Those are small, and missing one is a correctness bug — tightening
# 'dmee' to its owner domains silently dropped 8 of 9 incidents, INC-EGYPT-PPC among them,
# because that one is filed under Procurement. Prose (docs, companions) stays on the tight
# owner set; records widen.
ADJACENT = {
    "dmee": ["Treasury", "Treasury_EBS", "BCM", "Procurement", "Procurement_P2P", "FI"],
    "pmw": ["Treasury", "BCM", "FI"],
    "bank file": ["Treasury", "Treasury_EBS", "BCM", "FI"],
    "fichero de bancos": ["Treasury", "Treasury_EBS", "BCM", "FI"],
    "ppc": ["Treasury", "FI", "DMEE"],
    "purpose of payment": ["Treasury", "FI", "DMEE"],
    "sepa": ["Treasury", "BCM", "FI", "PPC"],
    "citi": ["Treasury", "BCM", "FI", "PPC"],
    "cgi": ["Treasury", "BCM", "FI", "PPC"],
    "f110": ["Treasury", "BCM", "FI", "PPC", "Procurement"],
}

STOP = {
    "the", "and", "for", "with", "que", "los", "las", "del", "por", "una", "como",
    "de", "el", "la", "en", "un", "of", "to", "is", "a",
}


def norm(s: str) -> str:
    """Lowercase, strip accents — so 'configuración' matches 'configuracion'."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def load_json(rel, default=None):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return default
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            return json.load(fh)
    except Exception as exc:  # a broken store must not block the load
        sys.stderr.write("WARN cannot parse %s: %s\n" % (rel, exc))
        return default


def read_text(path) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def html_to_text(path) -> str:
    """Companions are the living artefacts; their PROSE is the knowledge. Strip markup only."""
    s = read_text(path)
    s = re.sub(r"(?is)<script.*?</script>", "", s)
    s = re.sub(r"(?is)<style.*?</style>", "", s)
    s = re.sub(r"(?is)<!--.*?-->", "", s)
    s = re.sub(r"(?i)</(p|div|tr|li|h[1-6]|section|table)>", "\n", s)
    s = re.sub(r"(?i)</t[dh]>", " | ", s)
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'"), ("&mdash;", "--"), ("&middot;", "·"),
                 ("&rarr;", "->"), ("&rsquo;", "'"), ("&ldquo;", '"'), ("&rdquo;", '"'),
                 ("&ndash;", "-")):
        s = s.replace(a, b)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n[ |]*\n+", "\n", s)
    return s.strip()


# ---------------------------------------------------------------------------
# Vocabulary + resolution
# ---------------------------------------------------------------------------
def known_domains():
    doms = set()
    cm = load_json("brain_v2/capability_model/capability_model.json", {}) or {}
    doms |= set((cm.get("domains") or {}).keys())
    ci = load_json("brain_v2/code_inventory.json", {}) or {}
    doms |= set((ci.get("by_domain") or {}).keys())
    reg = load_json("brain_v2/gold_table_registry.json", {}) or {}
    doms |= set((reg.get("domains") or {}).keys())
    kd = os.path.join(ROOT, "knowledge", "domains")
    if os.path.isdir(kd):
        doms |= {d for d in os.listdir(kd) if os.path.isdir(os.path.join(kd, d))}
    for c in load_json("brain_v2/claims/claims.json", []) or []:
        if c.get("domain"):
            doms.add(c["domain"])
    return {d for d in doms if d and not d.startswith("_")}


def resolve(topic):
    """topic -> (domains, tokens). Alias first, then exact/fuzzy domain, then token-only."""
    t = norm(topic).strip()
    doms = set()
    if t in ALIASES:
        doms |= set(ALIASES[t])
    all_doms = known_domains()
    by_norm = {norm(d): d for d in all_doms}
    if t in by_norm:
        doms.add(by_norm[t])
    for nd, d in by_norm.items():
        # Payment matches Payment_BCM; do NOT let 'fi' swallow 'FI_AA' by accident —
        # require a separator boundary.
        if nd == t or nd.startswith(t + "_") or nd.startswith(t + "-"):
            doms.add(d)
    tokens = {w for w in re.split(r"[^a-z0-9_/]+", t) if len(w) > 2 and w not in STOP}
    tokens.add(t.replace(" ", "_")) if " " in t else None
    tokens = {w for w in tokens if w}
    wide = set(doms) | set(ADJACENT.get(t, []))
    return doms, tokens | {t}, wide


def hits(text, tokens):
    n = norm(text)
    return any(tok in n for tok in tokens)


# ---------------------------------------------------------------------------
# Collectors — each returns a list of (section_title, body)
# ---------------------------------------------------------------------------
def collect_docs(doms, tokens):
    """Returns (core, peripheral). CORE = the topic OWNS it (its domain folder, or its
    name is in the filename). PERIPHERAL = filed elsewhere, merely mentions the topic."""
    core, periph, seen = [], [], set()
    kd = os.path.join(ROOT, "knowledge", "domains")
    dnorm = {norm(d) for d in doms}
    for dirpath, _dirs, files in os.walk(kd):
        rel_dir = os.path.relpath(dirpath, kd).replace("\\", "/")
        head = norm(rel_dir.split("/")[0])
        in_domain = head in dnorm or any(head.startswith(d) or d.startswith(head) for d in dnorm if d)
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            if rel in seen:
                continue
            if in_domain or hits(f, tokens):
                seen.add(rel)
                core.append((rel, read_text(p)))
                continue
            try:
                body = read_text(p)
            except Exception:
                continue
            if hits(body[:4000], tokens):
                seen.add(rel)
                periph.append((rel, body))
    return core, periph


def collect_claims(doms, tokens):
    rows = []
    for c in load_json("brain_v2/claims/claims.json", []) or []:
        blob = " ".join([
            str(c.get("claim", "")), str(c.get("domain", "")),
            " ".join(map(str, c.get("related_objects") or [])),
        ])
        if (c.get("domain") in doms) or hits(blob, tokens):
            rows.append(c)
    return rows


def collect_incidents(doms, tokens):
    rows = []
    for i in load_json("brain_v2/incidents/incidents.json", []) or []:
        ds = {i.get("domain")} | set(i.get("secondary_domains") or [])
        blob = json.dumps(i, ensure_ascii=False)
        if (ds & doms) or hits(blob, tokens):
            rows.append(i)
    return rows


def collect_annotations(tokens, objects):
    ann = load_json("brain_v2/annotations/annotations.json", {}) or {}
    out = {}
    onorm = {norm(o) for o in objects}
    for obj, payload in ann.items():
        if norm(obj) in onorm or hits(obj, tokens) or hits(json.dumps(payload, ensure_ascii=False), tokens):
            out[obj] = payload
    return out


def collect_rules(doms, tokens):
    rows = []
    for r in load_json("brain_v2/agent_rules/feedback_rules.json", []) or []:
        blob = json.dumps(r, ensure_ascii=False)
        if hits(blob, tokens) or any(norm(d) in norm(blob) for d in doms):
            rows.append(r)
    return rows


def collect_companions(doms, tokens, incident_ids):
    """Companions are a GRAPH (s083). SCORE them — a companion whose TITLE is the topic is
    not the same as one that merely lists it among 40 entities. Returns (core, peripheral).

    NOTE the graph's `domain` field is a coarse bucket (finance/process/transport/support),
    NOT a SAP domain name — never score against it, it matches nothing.

    Score: title/filename match = 10 (the page is ABOUT it) · linked incident = 6 ·
    topic-token in curated entities = 4 · resolved-domain-name in entities = 2 (cap 4).
    Core is >=8, which the domain bonus ALONE cannot reach — deliberately. A broad topic
    resolves to many domains (dmee -> 7), so scoring on domain alone made every finance page
    'core' and the load unusable at 721K tokens. The topic itself must be present."""
    graph = load_json("companions/companion_graph.json", {}) or {}
    scored = []
    for n in graph.get("nodes") or []:
        f = n.get("file")
        if not f:
            continue
        score = 0
        if hits("%s %s" % (n.get("title", ""), f), tokens):
            score += 10
        if set(map(str, n.get("incidents") or [])) & incident_ids:
            score += 6
        ents = {norm(e) for e in (n.get("entities") or [])}
        score += 4 * sum(1 for t in tokens if t in ents)
        score += min(4, 2 * sum(1 for d in doms if norm(d) in ents))
        if score:
            scored.append((score, f))
    core, periph = [], []
    for score, f in sorted(scored, key=lambda x: (-x[0], x[1])):
        p = os.path.join(ROOT, "companions", f)
        if not os.path.exists(p):
            continue
        entry = ("companions/%s  [relevance %d]" % (f, score), html_to_text(p))
        (core if score >= 8 else periph).append(entry)
    return core, periph


def collect_code(doms, tokens):
    ci = load_json("brain_v2/code_inventory.json", {}) or {}
    by_dom = ci.get("by_domain") or {}
    objects = set()
    for d, lst in by_dom.items():
        if d in doms or hits(d, tokens):
            for o in lst:
                objects.add(o if isinstance(o, str) else o.get("object", str(o)))
    for name, meta in (ci.get("objects") or {}).items():
        if hits(name, tokens):
            objects.add(name)
    return sorted(x for x in objects if x)


def collect_gold(doms, tokens):
    reg = load_json("brain_v2/gold_table_registry.json", {}) or {}
    out = {}
    for d, payload in (reg.get("domains") or {}).items():
        if d in doms or hits(d, tokens):
            out[d] = payload
    return out


def collect_capability(doms):
    cm = load_json("brain_v2/capability_model/capability_model.json", {}) or {}
    return {d: v for d, v in (cm.get("domains") or {}).items() if d in doms}


# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------
def emit(topic, doms, tokens, wide):
    # Prose on the tight owner set; records on the wide adjacent set (see ADJACENT).
    docs, docs_p = collect_docs(doms, tokens)
    claims = collect_claims(wide, tokens)
    incidents = collect_incidents(wide, tokens)
    rules = collect_rules(wide, tokens)
    comps, comps_p = collect_companions(
        doms, tokens, {str(i.get("id")) for i in incidents})
    code = collect_code(wide, tokens)
    gold = collect_gold(wide, tokens)
    cap = collect_capability(wide)

    objs = set()
    for c in claims:
        objs |= set(map(str, c.get("related_objects") or []))
    for i in incidents:
        objs |= set(map(str, i.get("related_objects") or []))
    anns = collect_annotations(tokens, objs)

    sections = []
    sections.append(("STRUCTURED — capability model rows", json.dumps(cap, ensure_ascii=False, indent=1)))
    sections.append(("STRUCTURED — incidents (%d)" % len(incidents),
                     json.dumps(incidents, ensure_ascii=False, indent=1)))
    sections.append(("STRUCTURED — claims (%d)" % len(claims),
                     json.dumps(claims, ensure_ascii=False, indent=1)))
    sections.append(("STRUCTURED — annotations (%d objects)" % len(anns),
                     json.dumps(anns, ensure_ascii=False, indent=1)))
    sections.append(("STRUCTURED — feedback rules (%d)" % len(rules),
                     json.dumps(rules, ensure_ascii=False, indent=1)))
    sections.append(("STRUCTURED — Gold DB tables by domain",
                     json.dumps(gold, ensure_ascii=False, indent=1)))
    sections.append(("STRUCTURED — extracted code objects (%d)" % len(code),
                     "\n".join(code)))
    for rel, body in docs:
        sections.append(("DOC — " + rel, body))
    for rel, body in comps:
        sections.append(("COMPANION — " + rel, body))

    outdir = os.path.join(OUT_ROOT, re.sub(r"[^a-z0-9]+", "_", norm(topic)).strip("_") or "topic")
    os.makedirs(outdir, exist_ok=True)
    for old in os.listdir(outdir):
        if old.endswith(".md"):
            os.remove(os.path.join(outdir, old))

    # `where` maps part-number -> the section titles inside it. Without it the manifest only
    # says "77 parts, read them all", so finding one section means reading in order until you
    # hit it — which defeats the point of having the load on disk at all. s100.
    parts, buf, buflen, where = [], [], 0, {}

    def _mark(part_no, title):
        titles = where.setdefault(part_no, [])
        if title not in titles:
            titles.append(title)

    for title, body in sections:
        block = "\n\n@@@@@ %s\n\n%s\n" % (title, body)
        # A single oversized section is split rather than dropped (CP-002: never lose).
        while len(block) > PART_CHARS:
            cut = block.rfind("\n", 0, PART_CHARS) or PART_CHARS
            head, block = block[:cut], "\n@@@@@ (cont.) %s\n%s" % (title, block[cut:])
            if buf:
                parts.append("".join(buf)); buf, buflen = [], 0
            parts.append(head); _mark(len(parts), title)
        if buflen + len(block) > PART_CHARS and buf:
            parts.append("".join(buf)); buf, buflen = [], 0
        buf.append(block); buflen += len(block); _mark(len(parts) + 1, title)
    if buf:
        parts.append("".join(buf))

    written = []
    for i, p in enumerate(parts, 1):
        name = "part_%02d.md" % i
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as fh:
            fh.write(p)
        written.append((name, len(p)))

    total = sum(n for _, n in written)
    man = [
        "# DOMAIN LOAD — %s" % topic,
        "",
        "Domains (owner, prose): %s" % (", ".join(sorted(doms)) or "(token-only match)"),
        "Domains (adjacent, records): %s" % (", ".join(sorted(wide - doms)) or "(none)"),
        "Tokens: %s" % ", ".join(sorted(tokens)),
        "",
        "| what | CORE (loaded) | peripheral (listed, not loaded) |",
        "|---|---|---|",
        "| domain docs | %d | %d |" % (len(docs), len(docs_p)),
        "| companions | %d | %d |" % (len(comps), len(comps_p)),
        "| claims | %d | — |" % len(claims),
        "| incidents | %d | — |" % len(incidents),
        "| annotated objects | %d | — |" % len(anns),
        "| feedback rules | %d | — |" % len(rules),
        "| extracted code objects | %d | — |" % len(code),
        "| Gold DB domains | %d | — |" % len(gold),
        "",
        "**%d parts · %s chars · ~%dK tokens.** READ THEM ALL, IN ORDER:" % (
            len(written), "{:,}".format(total), total // 4000),
        "",
    ]
    man += ["", "### Part index — go straight to the part you need", "",
            "| part | chars | contains |", "|---|---|---|"]
    for i, (name, n) in enumerate(written, 1):
        titles = " · ".join(where.get(i, ["(continuation)"]))
        man.append("| `%s` | %s | %s |" % (
            os.path.join(outdir, name), "{:,}".format(n), titles[:170]))
    man += ["", "## CORE — what was loaded", ""]
    for rel, _b in docs:
        man.append("- doc: %s" % rel)
    for rel, _b in comps:
        man.append("- companion: %s" % rel)
    # No silent caps: what was left out is NAMED, so the next reader can pull it deliberately.
    man += ["", "## PERIPHERAL — mentions the topic, NOT loaded (pull by path if needed)", ""]
    for rel, _b in docs_p:
        man.append("- doc: %s" % rel)
    for rel, _b in comps_p:
        man.append("- companion: %s" % rel)
    if not docs_p and not comps_p:
        man.append("- (none)")
    manifest = "\n".join(man)
    with open(os.path.join(outdir, "00_MANIFEST.md"), "w", encoding="utf-8") as fh:
        fh.write(manifest)
    print(manifest)


def main():
    args = [a for a in sys.argv[1:] if a]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--list":
        print("\n".join(sorted(known_domains())))
        print("\nALIASES: " + ", ".join(sorted(ALIASES)))
        return 0
    topic = " ".join(args)
    doms, tokens, wide = resolve(topic)
    if not doms and not tokens:
        print("No domain or token resolved for %r. Try --list." % topic)
        return 1
    emit(topic, doms, tokens, wide)
    return 0


if __name__ == "__main__":
    sys.exit(main())
