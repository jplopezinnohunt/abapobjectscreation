"""Code inventory — the physical + semantic layer for extracted SAP source.

WHY THIS EXISTS (s099)
----------------------
Code is not a supporting artifact here; it is where the application's real behaviour
lives. A single object routinely serves several domains and processes at once, so a
one-domain-per-file guess destroys the very thing that makes code valuable.

Two failures forced this module:

1. INTEGRITY. `YRGGBS00` — the FI validation/substitution form pool that governs the
   whole posting perimeter — exists twice:
       extracted_sap_p01/YA/YFI_YRGGBS00_EXIT.abap          29 lines   (canonical path)
       Zagentexecution/mcp-backend-server-python/
                                    YRGGBS00_SOURCE.txt   1593 lines, UTF-16 (real body)
   A prior audit grepped the corpus for 'LZBKZ', found nothing, and published a TIER_1
   claim that a production control did not exist. The control (FORM u917, line 1547) was
   in the file that is not in the corpus, written in lowercase, in UTF-16. Three separate
   silent failures stacked: wrong root, wrong case, wrong encoding.

2. SINGLE-VALUED DOMAIN. ingestors/code_ingestor.py `_guess_domain()` returns ONE domain
   inferred from the directory name, defaulting to 'CUSTOM'. YRGGBS00 is cited from FI,
   PSM, Treasury, Payment and Support work — none of which that guess can express.

WHAT THIS BUILDS
----------------
`brain_v2/code_inventory.json`:
  files[]        every source file found under EVERY root, with lines/bytes/encoding
  objects{}      grouped by normalised SAP object name
  token_index{}  token -> files, so asking for YRGGBS00 finds BOTH files above
  domains        MULTI-VALUED per object, each link carrying its provenance (`via`)
  integrity      per object: OK / STUB_AT_CANONICAL / ONLY_OUTSIDE_CORPUS / EMPTY

Domain links are evidence-ranked, never a single guess:
  claim/incident/annotation `related_objects`  -> high     (a human asserted it)
  brain_state objects domain_axes              -> high
  executed-objects usage map + domain footprint-> medium   (measured execution)
  directory / name heuristic                   -> low      (last resort, never alone)

Run standalone or via rebuild_all.py:
    python brain_v2/build_code_inventory.py
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
BRAIN = REPO / "brain_v2"
OUT = BRAIN / "code_inventory.json"

# Every place extracted SAP source has ever landed. The corpus roots are the ones the
# artifact-hierarchy rule says are canonical; the rest are recorded precisely BECAUSE
# source keeps landing there and nothing was looking.
CORPUS_ROOTS = ["extracted_code", "extracted_sap", "extracted_sap_p01"]
SCAN_SKIP = {".git", "node_modules", "__pycache__", "sqlite", ".claude", "venv",
             ".venv", "site-packages", ".pytest_cache", "dist", "build"}
SRC_EXT = {".abap", ".txt", ".src", ".prog", ".clas", ".fugr", ".incl"}

# Tokens too generic to identify an object.
STOP_TOKENS = {
    "SOURCE", "METHODS", "ALL", "FULL", "EXIT", "CODE", "TEST", "TEMP", "OLD", "NEW",
    "BACKUP", "COPY", "DATA", "MAIN", "CLASS", "PROG", "FUGR", "INCL", "REPORT",
    "STANDARD", "CUSTOM", "UNESCO", "CANONICAL", "STATE", "INVENTORY", "RAW",
    "OUTPUT", "RESULT", "FINAL", "DRAFT", "SAMPLE", "README", "NOTES", "LOG",
}

# ABAP class-pool include names (CM001, CM00D, CCIMP, CCDEF, CCMAC, CI, CU, CO, CP, CT,
# CS, CCAU). They name a SECTION of a class, never the class — every class in the system
# has a CM001. Grouping on them merged ZCL_IM_TRIP_POST_FI's CM00C with
# YCL_FM_BR_EXCHANGE_RATE_BL's CM00C, which are unrelated code.
GENERIC_INCLUDE = re.compile(r"^(CM[0-9A-F]{3}|CC(IMP|DEF|MAC|AU)|C[IUOPTS])$", re.I)

ABAP_MARKERS = ("form ", "endform", "select single", "data:", "method ", "endmethod",
                "report ", "class ", "function ", "loop at", "call function",
                "endmethod", "endclass", "perform ")

# Lowest-confidence path hints. Deliberately kept as a hint, never a sole assignment.
PATH_DOMAIN_HINTS = {
    "DMEE": "Payment_BCM", "YWFI": "FI", "FM_BUDGETING": "PSM_FM",
    "FM_COCKPIT": "PSM_FM", "FM_MASTER_DATA": "PSM_FM", "BI_REPORTING": "Integration",
    "MM_PROCUREMENT": "Procurement", "PS_PROJECTS": "PS", "TECH_INTEGRATION": "Integration",
    "TV_TRAVEL": "Travel", "HCM": "HCM", "PSM": "PSM", "Benefits": "HCM",
    "Offboarding": "HCM", "SAPFPAYM_full": "Payment_BCM", "YFPAYM_full": "Payment_BCM",
    "BCM": "Payment_BCM", "Treasury": "Treasury", "FI": "FI",
}


# ---------------------------------------------------------------- file scanning

def detect_encoding(raw: bytes) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "utf-16"
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    return "utf-8"


def read_text(path: Path):
    """Return (text, encoding). Encoding-normalised — this is the whole point."""
    try:
        raw = path.read_bytes()
    except Exception:
        return None, "?"
    enc = detect_encoding(raw)
    try:
        return raw.decode(enc, errors="replace"), enc
    except Exception:
        return None, enc


def is_abap_source(text: str) -> bool:
    if not text or len(text) < 60:
        return False
    low = text[:8000].lower()
    return sum(m in low for m in ABAP_MARKERS) >= 2


def normalise_object_name(stem: str) -> str:
    """Strip SAP class-pool `=` padding and file-naming noise."""
    n = stem.strip()
    n = re.sub(r"\.clas$|\.prog$|\.fugr$", "", n, flags=re.I)
    n = n.replace("=", " ").strip()          # YCL_X==========CI -> "YCL_X CI"
    n = re.split(r"\s+", n)[0] if n else n
    return n.upper()


def name_tokens(stem: str) -> set:
    """Identifying tokens for a file name, used to group split/duplicated sources."""
    parts = re.split(r"[^A-Za-z0-9]+", stem.upper())
    toks = set()
    for p in parts:
        if (len(p) >= 5 and p not in STOP_TOKENS and not p.isdigit()
                and not GENERIC_INCLUDE.match(p)):
            toks.add(p)
    # also the whole normalised name
    n = normalise_object_name(stem)
    if len(n) >= 5:
        toks.add(n)
    return toks


def scan_files():
    files = []
    for root, dirs, names in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SCAN_SKIP]
        rp = Path(root)
        try:
            rel = rp.relative_to(REPO)
        except ValueError:
            continue
        top = rel.parts[0] if rel.parts else ""
        for fn in names:
            ext = Path(fn).suffix.lower()
            if ext not in SRC_EXT:
                continue
            p = rp / fn
            try:
                size = p.stat().st_size
            except Exception:
                continue
            if size > 8_000_000:          # abapGit standalone and friends
                continue
            text, enc = read_text(p)
            if text is None:
                continue
            if ext != ".abap" and not is_abap_source(text):
                continue                  # a .txt is only source if it reads like ABAP
            if ext == ".abap" and size == 0:
                lines = 0
            else:
                lines = text.count("\n") + 1
            stem = Path(fn).name
            for suf in (".clas.abap", ".prog.abap", ".fugr.abap", ".abap", ".txt",
                        ".src", ".prog", ".clas", ".fugr", ".incl"):
                if stem.lower().endswith(suf):
                    stem = stem[: -len(suf)]
                    break

            # A file named CM003.abap / CCIMP.abap / CI.abap is a SECTION of a class, not
            # an object. Its identity is the directory it sits in. Left alone these became
            # ~30 free-floating objects called CM001..CM00D that could never carry a domain,
            # and — worse — the real method bodies never attached to their class.
            member = None
            if GENERIC_INCLUDE.match(stem):
                parent = rp.name
                if len(parent) >= 5 and not GENERIC_INCLUDE.match(parent):
                    member, stem = stem.upper(), parent
            files.append({
                "path": str(rel / fn).replace("\\", "/"),
                "name": normalise_object_name(stem),
                "tokens": sorted(name_tokens(stem)),
                "lines": lines,
                "bytes": size,
                "encoding": enc,
                "in_corpus": top in CORPUS_ROOTS,
                "root": top,
                "member": member,
            })
    return files


# ---------------------------------------------------------------- evidence linkage

def load_json(rel):
    p = REPO / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect_domain_evidence():
    """object-name -> list of {domain, process[], via, confidence}. MULTI-VALUED."""
    ev = defaultdict(list)

    def add(obj, domain, via, conf, processes=None):
        if not obj or not domain:
            return
        ev[obj.upper()].append({
            "domain": domain, "via": via, "confidence": conf,
            "processes": sorted(set(processes or [])),
        })

    # 1. claims / incidents / annotations / rules — a human asserted the link
    for rel, kind in (("brain_v2/claims/claims.json", "claim"),
                      ("brain_v2/incidents/incidents.json", "incident"),
                      ("brain_v2/annotations/annotations.json", "annotation"),
                      ("brain_v2/agent_rules/feedback_rules.json", "rule")):
        data = load_json(rel)
        if data is None:
            continue
        items = data if isinstance(data, list) else (
            data.get(kind + "s") or data.get("items") or [])
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            dom = it.get("domain")
            axes = it.get("domain_axes") or {}
            funcs = axes.get("functional") if isinstance(axes, dict) else None
            procs = axes.get("process") if isinstance(axes, dict) else None
            if isinstance(axes, list):
                funcs = axes
            doms = [d for d in ([dom] + list(funcs or [])) if d]
            ident = it.get("id") or it.get("name") or "?"
            for obj in (it.get("related_objects") or []):
                if not isinstance(obj, str):
                    continue
                for d in doms:
                    add(obj, d, f"{kind}:{ident}", "high", procs)

    # 2. brain_state objects — the curated graph's own axes
    bs = load_json("brain_v2/brain_state.json")
    if bs:
        for name, o in (bs.get("objects") or {}).items():
            if not isinstance(o, dict):
                continue
            axes = o.get("domain_axes") or {}
            funcs = axes.get("functional") if isinstance(axes, dict) else []
            procs = axes.get("process") if isinstance(axes, dict) else []
            for d in (funcs or []):
                add(name, d, "brain_state:objects", "high", procs)

    # 3. measured execution — usage map + per-domain footprints
    eom = load_json("brain_v2/executed_objects_domain_map.json")
    if eom:
        for d, objs in (eom.get("top_objects_by_domain") or {}).items():
            for o in objs or []:
                add(o.get("object"), d, "usage:executed_objects_map", "medium")
    # 3b. TADIR package — the MEASURED owner of an object. A package is not a domain, so
    # only unambiguous packages map; 'YA' is a catch-all and deliberately does not.
    PKG_DOMAIN = {"ZPBC": "PBC", "YHR_OM_WF": "HR-Workflows", "YWFI": "FI"}
    tadir = load_json("brain_v2/tadir_object_package.json") or {}
    for obj, pkg in (tadir.get("object_package") or {}).items():
        d = PKG_DOMAIN.get(pkg)
        if d:
            add(obj, d, f"tadir:{pkg}", "high")

    # 3c. WHAT THE CODE READS. The strongest name-independent signal available: an object
    # that reads FMIFIIT and FMIT is doing funds management whatever it is called. Tables
    # come from the parsed sections; table->domain from the gold table registry.
    reg = load_json("brain_v2/gold_table_registry.json") or {}
    table_domain = {}
    for dom, cats in (reg.get("domains") or {}).items():
        if not isinstance(cats, dict):
            continue
        for rows in cats.values():
            for x in (rows or []):
                if isinstance(x, dict) and x.get("gold"):
                    table_domain.setdefault(x["gold"].upper(), dom)
    secs = load_json("brain_v2/code_sections.json") or {}
    for obj, o in (secs.get("objects") or {}).items():
        counts = defaultdict(int)
        for s in o.get("sections", []):
            for t in s.get("reads_tables", []):
                d = table_domain.get(t.upper())
                if d:
                    counts[d] += 1
        # require 2+ distinct hits so a single incidental read cannot label an object
        for d, c in counts.items():
            if c >= 2:
                add(obj, d, f"reads_tables:{c}", "medium")

    fp_dir = BRAIN / "domain_footprints"
    if fp_dir.is_dir():
        for fp in fp_dir.glob("*.json"):
            if fp.name.startswith("_"):
                continue
            data = load_json(f"brain_v2/domain_footprints/{fp.name}") or {}
            d = data.get("domain") or fp.stem
            for o in (data.get("top_objects") or []):
                add(o.get("object"), d, f"footprint:{fp.stem}", "medium")

    return ev


def collect_doc_citations(object_names):
    """Which knowledge docs mention each object. Cheap set-intersection, one pass."""
    cites = defaultdict(set)
    names = {n for n in object_names if len(n) >= 5}
    kdir = REPO / "knowledge"
    if not kdir.is_dir():
        return cites
    for p in kdir.rglob("*.md"):
        text, _ = read_text(p)
        if not text:
            continue
        words = set(re.split(r"[^A-Za-z0-9_/]+", text.upper()))
        rel = str(p.relative_to(REPO)).replace("\\", "/")
        for n in names & words:
            cites[n].add(rel)
    return cites


# ---------------------------------------------------------------- assembly

def build():
    print("scanning source roots...")
    files = scan_files()
    print(f"  {len(files)} source files "
          f"({sum(1 for f in files if f['in_corpus'])} in corpus, "
          f"{sum(1 for f in files if not f['in_corpus'])} outside)")

    # token index — this is what makes a split object findable
    token_index = defaultdict(list)
    for i, f in enumerate(files):
        for t in f["tokens"]:
            token_index[t].append(i)

    # A token only IDENTIFIES an object if it is rare. 'PAYMEDIUM' is shared by a dozen
    # distinct function modules, so grouping on it merged Y_FI_PAYMEDIUM_06,
    # Y_FI_PAYMEDIUM_41, _NOTE_TO_PAYEE... into one 535-line file and reported eleven
    # phantom stubs. 'YRGGBS00' is shared by exactly two files and does identify them.
    token_df = {t: len({files[i]["name"] for i in ix}) for t, ix in token_index.items()}
    RARE_MAX = 3

    print("collecting domain evidence...")
    evidence = collect_domain_evidence()

    # group files into objects by normalised name
    by_name = defaultdict(list)
    for i, f in enumerate(files):
        by_name[f["name"]].append(i)

    print("resolving integrity + domain links...")
    doc_cites = collect_doc_citations(set(by_name))

    objects = {}
    for name, idxs in by_name.items():
        fl = sorted((files[i] for i in idxs), key=lambda x: -x["lines"])
        primary = fl[0]

        # every file that shares a RARE (therefore identifying) token with this object
        related = set(idxs)
        for t in primary["tokens"]:
            if token_df.get(t, 99) > RARE_MAX:
                continue
            for j in token_index.get(t, []):
                related.add(j)
        rel_files = sorted((files[j] for j in related), key=lambda x: -x["lines"])
        biggest = rel_files[0] if rel_files else primary

        corpus_best = max((f["lines"] for f in rel_files if f["in_corpus"]), default=0)
        status, note = "OK", ""
        if biggest["lines"] == 0:
            status, note = "EMPTY", "no content in any copy"
        elif corpus_best == 0:
            status = "ONLY_OUTSIDE_CORPUS"
            note = f"largest copy ({biggest['lines']} lines) lives at {biggest['path']}"
        elif biggest["lines"] > 0 and corpus_best < biggest["lines"] * 0.5:
            status = "STUB_AT_CANONICAL"
            note = (f"corpus copy has {corpus_best} lines but {biggest['path']} "
                    f"has {biggest['lines']} — grepping the corpus MISSES the body")

        # multi-valued domains, deduped, provenance preserved
        links = list(evidence.get(name, []))
        for t in primary["tokens"]:
            links.extend(evidence.get(t, []))
        if not links:
            for part in Path(primary["path"]).parts:
                if part in PATH_DOMAIN_HINTS:
                    links.append({"domain": PATH_DOMAIN_HINTS[part], "confidence": "low",
                                  "via": f"path:{part}", "processes": []})
                    break

        doms = {}
        procs = set()
        for l in links:
            d = l["domain"]
            procs.update(l.get("processes") or [])
            cur = doms.get(d)
            rank = {"high": 3, "medium": 2, "low": 1}
            if cur is None or rank[l["confidence"]] > rank[cur["confidence"]]:
                doms[d] = {"domain": d, "confidence": l["confidence"], "via": [l["via"]]}
            elif l["via"] not in cur["via"] and len(cur["via"]) < 8:
                cur["via"].append(l["via"])

        objects[name] = {
            "object": name,
            "primary_source": biggest["path"],
            "lines": biggest["lines"],
            "encoding": biggest["encoding"],
            "files": [{k: f[k] for k in ("path", "lines", "bytes", "encoding", "in_corpus")}
                      for f in rel_files[:12]],
            "integrity": {"status": status, "note": note},
            "domains": sorted(doms.values(), key=lambda x: (-len(x["via"]), x["domain"])),
            "processes": sorted(procs),
            "knowledge_docs": sorted(doc_cites.get(name, []))[:12],
        }

    integ = defaultdict(int)
    for o in objects.values():
        integ[o["integrity"]["status"]] += 1
    undomained = [n for n, o in objects.items() if not o["domains"]]

    by_domain = defaultdict(list)
    for n, o in objects.items():
        for d in o["domains"]:
            by_domain[d["domain"]].append(n)

    inv = {
        "_meta": {
            "built_by": "brain_v2/build_code_inventory.py",
            "why": "code is where behaviour lives; one object serves many domains",
            "corpus_roots": CORPUS_ROOTS,
            "source_files": len(files),
            "objects": len(objects),
            "encoding_normalised": True,
        },
        "_integrity": dict(integ),
        "_undomained": sorted(undomained)[:200],
        "_undomained_count": len(undomained),
        "objects": objects,
        "by_domain": {k: sorted(v) for k, v in sorted(by_domain.items())},
        "token_index": {t: sorted({files[i]["name"] for i in ix})
                        for t, ix in token_index.items() if len(ix) > 1},
    }

    OUT.write_text(json.dumps(inv, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(f"  objects: {len(objects)}   source files: {len(files)}")
    print("  integrity:", dict(integ))
    print(f"  objects with NO domain link: {len(undomained)}")
    print(f"  domains covered: {len(by_domain)}")
    return inv


if __name__ == "__main__":
    build()
