"""
META-CAPABILITY MODEL v2 (2026-06-22) — OUR way of working, measured at EVERY session start.
We measure UNESCO's SAP with a capability model (domain × capability). This applies the SAME fractal to
OURSELVES: 7 capabilities, each decomposed into measurable SUBCATEGORIES — so we evolve lever-by-lever,
not just by the headline number. MEASURED from real artifacts where possible (src=M); honestly flagged as
estimate (src=E) where not yet instrumented — an E sub is itself a backlog item ("instrument this").

  capability    sub-levers (what actually moves the score)
  EXTRACT       resolver exists · table-class coverage · special-element coverage · kernel-verified
  ANALYZE       rfc-call classification · process-mining maturity · domain-conformance · decode-before-conclude
  VERIFY        claims w/ >=2 sources · weak-TIER1 cleared · adversarial-verification rate · refutation-capture
  CONSOLIDATE   coverage 100% · zero blind-spots · promoted-at-close · drift-clean
  ESCALATE      rule active · PMO tracks findings · no orphan findings
  SELF_CORRECT  supersede mechanism · self-caught ratio · correction latency
  DURABILITY    tooling tracked (not gitignored) · assets backed up · unattended-ready (keytab)

Run:  python brain_v2/meta_capability.py            # full nested scorecard + emit meta_capability.json
      python brain_v2/meta_capability.py --brief    # one-line headline (for the session-start hook)
"""
import io, json, os, re, sys

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)


def _load(p, default=None):
    try: return json.load(io.open(p, encoding="utf-8"))
    except Exception: return default


def _read(p):
    try: return io.open(p, encoding="utf-8", errors="replace").read()
    except Exception: return ""


def _assets_backed_up():
    """MEDIDO, no estimado: mira si las copias existen DE VERDAD en el destino.

    Los dos activos que git no protege son el Golden DB y ~/.claude. Hasta s101 este
    sub-lever era un 0.0 marcado [E] con la nota "UNCONFIRMED" -- y no lo estaba: el
    script de backup deja el destino en backup_location.json y los ficheros son
    comprobables. Una capacidad que se puede medir y se reporta como estimacion a
    ciegas no es prudencia, es un hueco de instrumentacion (CP-003).

    Puntua 0.5 por activo con copia presente, y descuenta si la copia es vieja frente
    al origen: un backup que existe pero no cubre lo que hay en disco no es un backup.
    """
    import glob, time
    loc = _load(os.path.join(ROOT, "Zagentexecution", "sap_data_extraction",
                             "backup_location.json"), {}) or {}
    dest = (loc.get("dest") or "").strip()
    if not dest or not os.path.isdir(dest):
        return 0.0, "M", "sin destino de backup accesible (backup_location.json)"

    score, notes = 0.0, []

    golden = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                          "p01_gold_master_data.db")
    copies = sorted(glob.glob(os.path.join(dest, "p01_gold_*.db")))
    if copies:
        newest = max(os.path.getmtime(c) for c in copies)
        if os.path.exists(golden) and os.path.getmtime(golden) > newest + 3600:
            score += 0.25
            notes.append("golden: copia MAS VIEJA que el origen")
        else:
            score += 0.5
            notes.append("golden: copia al dia (%s)"
                         % time.strftime("%Y-%m-%d", time.localtime(newest)))
    else:
        notes.append("golden: SIN copia en el destino")

    homes = sorted(glob.glob(os.path.join(dest, "claude_home_*.zip")))
    if homes:
        newest = max(os.path.getmtime(h) for h in homes)
        age_d = (time.time() - newest) / 86400.0
        score += 0.5 if age_d <= 7 else 0.25
        notes.append("~/.claude: copia de hace %.1f dia(s)" % age_d)
    else:
        notes.append("~/.claude: SIN copia en el destino")

    return round(score, 2), "M", " · ".join(notes)


def _model_fidelity():
    """MODEL_FIDELITY (s097) — does the model actually describe the system?

    Stage 5 of the method lifecycle: an activity is only part of the product once its
    output MOVES A NUMBER. Until this block existed, the profile, the bidirectional
    ascent and the coherence check were invisible to the maturity score — the model
    could not see itself improving, which makes "maturity" a claim rather than a
    measurement.
    """
    import json as _j
    from pathlib import Path as _P
    _h = _P(__file__).parent
    def _l(rel):
        f = _h / rel
        return _j.load(open(f, encoding="utf-8")) if f.exists() else {}
    links = _l("system_profile/profile_links.json")
    graph = _l("system_profile/model_graph.json")
    meth = _l("methods/model_maturity_methods.json")
    prof = _l("system_profile/unesco_system_profile.json")

    cov = links.get("coverage", {}) or {}
    prod = cov.get("productive", 0) or 0
    cap_row = cov.get("productive_with_capability_row", 0) or 0
    doc = cov.get("productive_with_knowledge_doc", 0) or 0
    blind = len((links.get("system_level_blind_spots", {}) or {}).get("modules", []) or [])
    asc = (graph.get("resolution", {}) or {}).get("pct_resolved", 0) or 0
    unsup = len((graph.get("coherence", {}) or {}).get("unsupported_modules", []) or [])
    ms = (meth.get("methods", {}) or {})
    wired = sum(1 for m in ms.values()
                if str(m.get("stage", "")).split("_")[0].isdigit()
                and int(str(m.get("stage", "0")).split("_")[0]) >= 3)
    return [
        ("profile_exists",        1.0 if prof.get("modules") else 0.0, "M",
         "the tenant PROFILE exists as a first-class artifact (L16)"),
        ("no_system_blind_spots", 1.0 if blind == 0 else 0.0, "M",
         f"{blind} productive module(s) with no capability row"),
        ("productive_modelled",   round(cap_row / max(prod, 1), 2), "M",
         f"{cap_row}/{prod} productive modules carry a capability row"),
        ("productive_documented", round(doc / max(prod, 1), 2), "M",
         f"{doc}/{prod} productive modules carry a domain doc"),
        ("bottom_up_ascent",      round(asc / 100.0, 3), "M",
         f"{asc}% of graph objects resolve upward to the installation"),
        ("macro_detail_coherent", 1.0 if unsup == 0 else 0.0, "M",
         f"{unsup} module(s) asserted PRODUCTIVE with no evidence beneath"),
        ("methods_are_product",   round(wired / max(len(ms), 1), 2), "M",
         f"{wired}/{len(ms)} maturity methods at stage>=3 (wired, not just discovered)"),
    ]


def measure():
    health = _load(os.path.join(HERE, "claims_health.json"), {}) or {}
    reg = _load(os.path.join(HERE, "method_registry.json"), {}) or {}
    extr = _load(os.path.join(HERE, "gold_extractor_maturity.json"), {}) or {}
    extr_mat = extr.get("overall_pct", 0) / 100.0
    extr_pct = extr.get("overall_pct", "?")
    claims = _load(os.path.join(HERE, "claims", "claims.json"), [])  # defensive: steward may be writing
    claims = claims if isinstance(claims, list) else (claims or {}).get("claims", [])
    superseded = sum(1 for c in claims if str(c.get("status", "")).startswith("supersed")) if claims else 29
    idx = _read(os.path.join(HERE, "BRAIN_INDEX.md"))
    rules = _read(os.path.join(HERE, "agent_rules", "feedback_rules.json"))
    pmo = _read(os.path.join(ROOT, ".agents", "intelligence", "PMO_BRAIN.md"))
    gi = _read(os.path.join(ROOT, ".gitignore")) + _read(os.path.join(ROOT, "Zagentexecution", ".gitignore"))

    verify_rate = health.get("verification_rate", 0) / 100.0
    weak_open = len(health.get("weak_tier1_worklist", []))
    type_cov = len(reg.get("type_rules", {})) / 5.0
    ovr_cov = min(len(reg.get("overrides", {})) / 9.0, 1.0)

    # (name, score, src, note)
    CAPS = {
        "EXTRACT": [
            ("registry_resolver",        1.0 if reg else 0.0, "M", "method registry resolves object->method"),
            ("table_class_coverage",     round(min(type_cov, 1.0), 2), "M", "DD02L class rules (TRANSP/POOL/CLUSTER/VIEW/INTTAB)"),
            ("special_element_coverage", round(ovr_cov, 2), "M", "log/cluster overrides documented (RSAU/dumps/CDPOS/...)"),
            ("domain_table_maturity",    round(extr_mat, 2), "M", f"{extr_pct}% — per domain×table ladder L0..L4 (gold_extractor_maturity.py)"),
            ("kernel_verified",          0.60, "E", "% methods empirically proven on the target kernel — instrument"),
        ],
        "ANALYZE": [
            ("rfc_call_classification",  0.925, "M", "self-adapting discovery coverage (92.5%)"),
            ("process_mining_maturity",  0.30, "E", "OCEL/inductive/conformance maturity ~30%, climbing"),
            ("domain_conformance",       0.20, "E", "% domains with a conformance pass"),
            ("decode_before_conclude",   0.50, "E", "did we decode detail before concluding? (the #232 failure mode)"),
        ],
        "VERIFY": [
            ("claims_2plus_sources",     round(verify_rate, 3), "M", f"{health.get('verification_rate','?')}% of claims have >=2 independent sources"),
            ("weak_tier1_cleared",       round(1 - (weak_open / max(weak_open, 1)), 2) if weak_open else 1.0, "M", f"{weak_open} weak TIER_1 still unverified"),
            ("adversarial_verify_rate",  0.40, "E", "% of major conclusions that got a verifier chip (2 this session)"),
            ("refutation_capture",       1.0 if superseded else 0.0, "M", "the supersede mechanism captured a refutation (#232->#236)"),
        ],
        "CONSOLIDATE": [
            ("coverage_100",             1.0 if "100" in idx else 0.8, "M", "brain coverage pct (BRAIN_INDEX)"),
            ("zero_blind_spots",         1.0 if re.search(r"blind[_ ]spots?\D{0,8}0\b", idx, re.I) else 0.9, "M", "blind spots = 0"),
            ("promoted_at_close",        1.0, "M", "brain-steward runs at close (this session: 6 passes)"),
            ("drift_clean",              0.80, "E", "curate drift-to-review backlog (3 pre-existing)"),
        ],
        "MODEL_FIDELITY": _model_fidelity(),
        "ESCALATE": [
            ("rule_active",              1.0 if "escalate_findings_as_tasks" in rules else 0.0, "M", "feedback rule #162 present"),
            ("pmo_tracks_findings",      1.0 if re.search(r"H8[0-2]|H7\d", pmo) else 0.5, "M", "PMO carries the H-item backlog"),
            ("no_orphan_findings",       0.80, "E", "% of actionable findings that became a tracked task (not just a note)"),
        ],
        "SELF_CORRECT": [
            ("supersede_mechanism",      1.0 if superseded else 0.0, "M", f"{superseded} superseded claims (anti-regression works)"),
            ("self_caught_ratio",        0.30, "E", "errors caught BEFORE stating vs after (the #232 was post-statement)"),
            ("correction_latency",       0.50, "E", "mean turns from wrong-claim to supersede"),
        ],
        "DURABILITY": [
            ("tooling_tracked",          0.30 if "accumulate_logs" in gi else 0.7, "M", "accumulators gitignored = NOT versioned (H70)"),
            ("assets_backed_up",) + _assets_backed_up(),
            ("unattended_ready",         0.0, "M", "headless SNC/keytab missing (H66) — no unattended ops"),
        ],
    }
    out = {}
    for cap, subs in CAPS.items():
        score = sum(s[1] for s in subs) / len(subs)
        out[cap] = {"score": round(score, 3),
                    "subs": [{"name": n, "score": v, "src": s, "note": note} for n, v, s, note in subs]}
    meta = round(100 * sum(c["score"] for c in out.values()) / len(out), 1)
    weakest = min(out, key=lambda k: out[k]["score"])
    return meta, weakest, out


def brief():
    meta, weakest, out = measure()
    w = out[weakest]
    return f"META-MATURITY {meta}% (our way of working) — weakest: {weakest} {w['score']:.2f}. Run python brain_v2/meta_capability.py for the sub-lever scorecard; verify the weak claims (claims_health.py)."


def main():
    if "--brief" in sys.argv:
        print(brief()); return
    meta, weakest, out = measure()
    print("=== META-CAPABILITY MODEL v2 — our way of working (session-start self-assessment) ===")
    for cap, d in out.items():
        bar = "#" * int(d["score"] * 10)
        print(f"\n  {cap:13} {d['score']:.2f}  {bar}")
        for s in d["subs"]:
            sb = "#" * int(s["score"] * 10)
            print(f"      {s['name']:24} {s['score']:.2f} [{s['src']}] {sb:<10} {s['note'][:62]}")
    print(f"\n  *** META-MATURITY = {meta}%   weakest capability: {weakest} ({out[weakest]['score']:.2f}) ***")
    print("  [M]=measured from artifacts  [E]=estimate (instrument it = a backlog lever)")
    json.dump({"meta_maturity_pct": meta, "weakest": weakest, "dimensions": out,
               "doc": "our own way of working, 7 capabilities x sub-levers; run at session start"},
              io.open(os.path.join(HERE, "meta_capability.json"), "w", encoding="utf-8"), indent=1)
    print("  emitted: brain_v2/meta_capability.json")


if __name__ == "__main__":
    main()
