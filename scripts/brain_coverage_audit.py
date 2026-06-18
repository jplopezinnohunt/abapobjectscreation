#!/usr/bin/env python
"""Brain coverage audit — per domain, which SAP objects the PROSE (.md) mentions
that have NO structured record (claim/incident) and therefore are NOT queryable
by object name in brain_state.json.

This is the backfill worklist. Deterministic: only counts tokens that are REAL
SAP objects (match a known graph node of a high-signal type), so no acronym noise.

Usage:
  python scripts/brain_coverage_audit.py              # full report to stdout + file
  python scripts/brain_coverage_audit.py <Domain>     # drill one domain (e.g. Transport_Intelligence)
"""
import json, io, re, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
GRAPH = ROOT / "brain_v2" / "output" / "brain_v2_graph.json"
CLAIMS = ROOT / "brain_v2" / "claims" / "claims.json"
INCIDENTS = ROOT / "brain_v2" / "incidents" / "incidents.json"
ANNOTATIONS = ROOT / "brain_v2" / "annotations" / "annotations.json"
DOMAINS_DIR = ROOT / "knowledge" / "domains"
OUT = ROOT / "knowledge" / "brain_coverage_audit.md"

# High-signal SAP object node types worth promoting (skip fields/data elements/forms).
SIGNAL_TYPES = {"SAP_TABLE", "ABAP_REPORT", "FUNCTION_MODULE", "ABAP_CLASS",
                "TRANSACTION", "ENHANCEMENT", "JOB_DEFINITION"}
# Names too generic to be meaningful even if they are nodes.
STOPNAMES = {"STATUS", "TEXT", "NAME", "TYPE", "DATA", "TABLE", "VALUE", "USER",
             "DATE", "TIME", "FORM", "LINE", "ITEM", "CODE", "FIELD", "INPUT",
             "OUTPUT", "BATCH", "ERROR", "CLASS", "GROUP", "RANGE", "CHECK"}


def load_signal_names():
    g = json.load(io.open(GRAPH, encoding="utf-8"))
    names = set()
    for n in g["nodes"]:
        if n.get("type") in SIGNAL_TYPES:
            nm = n.get("name", "")
            if nm and "." not in nm and nm not in STOPNAMES and len(nm) >= 3:
                names.add(nm)
    return names


def load_structured_names():
    """Every object name that already has a claim or incident (queryable today)."""
    structured = set()
    for c in json.load(io.open(CLAIMS, encoding="utf-8")):
        structured.update(c.get("related_objects", []))
    for rec in json.load(io.open(INCIDENTS, encoding="utf-8")):
        structured.update(rec.get("related_objects", []))
    ann = json.load(io.open(ANNOTATIONS, encoding="utf-8"))
    structured.update(ann.keys())
    return structured


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    signal = load_signal_names()
    structured = load_structured_names()
    # Fast path: tokenize each doc once, intersect with the signal name SET.
    # Candidate tokens: uppercase object names (T030H, BSEG, SAPF100, ZCL_*) and
    # dotted tcodes (F.05). O(tokens) instead of O(names x files).
    TOKEN = re.compile(r"\b[A-Z][A-Z0-9_/]{2,}\b|\b[A-Z]{1,4}\.\d+\b")

    mentioned = defaultdict(set)
    docs_per_domain = defaultdict(int)
    for md in DOMAINS_DIR.rglob("*.md"):
        rel = md.relative_to(DOMAINS_DIR)
        domain = rel.parts[0] if len(rel.parts) > 1 else rel.stem
        if only and domain != only:
            continue
        docs_per_domain[domain] += 1
        text = md.read_text(encoding="utf-8", errors="ignore")
        toks = set(TOKEN.findall(text))
        mentioned[domain] |= (toks & signal)

    rows = []
    for domain in sorted(mentioned, key=lambda d: -len(mentioned[d] - structured)):
        objs = mentioned[domain]
        covered = objs & structured
        gap = objs - structured
        rows.append((domain, docs_per_domain[domain], len(objs), len(covered), len(gap), sorted(gap)))

    lines = ["# Brain Coverage Audit — prose mentions vs structured records", ""]
    lines.append("Per domain: distinct REAL SAP objects mentioned in `.md` prose, how many are")
    lines.append("already queryable (have a claim/incident/annotation), and the GAP to backfill.")
    lines.append("")
    lines.append("| Domain | Docs | Objects in prose | Queryable | **GAP (backfill)** | Coverage |")
    lines.append("|--------|-----:|-----------------:|----------:|-------------------:|---------:|")
    tot_obj = tot_cov = tot_gap = 0
    for domain, ndocs, nobj, ncov, ngap, gaplist in rows:
        tot_obj += nobj; tot_cov += ncov; tot_gap += ngap
        pct = round(100 * ncov / nobj) if nobj else 0
        lines.append(f"| {domain} | {ndocs} | {nobj} | {ncov} | **{ngap}** | {pct}% |")
    pct_all = round(100 * tot_cov / tot_obj) if tot_obj else 0
    lines.append(f"| **TOTAL** | | **{tot_obj}** | **{tot_cov}** | **{tot_gap}** | **{pct_all}%** |")
    lines.append("")
    lines.append("## Gap detail per domain (objects to backfill with structured records)")
    for domain, ndocs, nobj, ncov, ngap, gaplist in rows:
        if not gaplist:
            continue
        lines.append(f"\n### {domain} — {ngap} objects")
        lines.append(", ".join("`%s`" % x for x in gaplist[:60]))
        if len(gaplist) > 60:
            lines.append(f"\n_... +{len(gaplist)-60} more_")

    report = "\n".join(lines)
    OUT.write_text(report, encoding="utf-8")
    # console summary
    print(f"Signal SAP objects in graph: {len(signal)} | already structured: {len(structured)}")
    print(f"Domains audited: {len(rows)}")
    print(f"TOTAL objects in prose: {tot_obj} | queryable: {tot_cov} | GAP: {tot_gap} ({pct_all}% covered)")
    print(f"\nTop gaps by domain:")
    for domain, ndocs, nobj, ncov, ngap, gaplist in rows[:12]:
        print(f"  {ngap:4} gap  ({ncov}/{nobj} covered)  {domain}")
    print(f"\nFull report: {OUT}")


if __name__ == "__main__":
    main()
