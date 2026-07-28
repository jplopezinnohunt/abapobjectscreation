"""
build_brain_index.py — TIERED LOADING (B1, s079). The LEAN L1 bootstrap index.
=============================================================================
Verified pattern (research wwrqcozf1, Anthropic 'Effective context engineering'):
HYBRID = a small index loaded up front + just-in-time drill-down. Avoids 'context rot'
(recall degrades as tokens grow). The full brain_state.json (~400K tokens) is PRESERVED
(CP-002) but no longer the mandatory full read — a session loads THIS (~4KB) and drills
via graph_queries.py only what it needs.

Emits brain_v2/BRAIN_INDEX.md. Run after rebuild_all.py.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
STATE = HERE / "brain_state.json"
MAT = HERE / "capability_model" / "maturity.json"
EB = HERE / "capability_model" / "execution_backlog.json"
PROFILE = HERE / "system_profile" / "unesco_system_profile.json"
OUT = HERE / "BRAIN_INDEX.md"


def _profile_block():
    """THE UNESCO PROFILE — what the tenant IS, at bootstrap (s097).

    Rendered from unesco_system_profile.json so the index can never drift from the
    profile. Answers 'what is installed / implemented / used / how is it operated'
    BEFORE any session re-derives it from cvers + audit logs (which is what went
    wrong in s097 and produced 5 wrong module verdicts).
    """
    if not PROFILE.exists():
        return "## ⚠️ UNESCO profile MISSING — brain_v2/system_profile/unesco_system_profile.json not found\n"
    p = json.load(open(PROFILE, encoding="utf-8"))
    mods = p.get("modules", {})
    om = p.get("operating_model", {})
    addons = p.get("third_party_addons", {})

    def names(pred):
        return ", ".join(k for k, v in mods.items()
                         if isinstance(v, dict) and pred(v.get("status", "")))

    active_addons = ", ".join(k for k, v in addons.items()
                              if isinstance(v, dict) and v.get("status") == "ACTIVE")
    return f"""## 🇺🇳 THE UNESCO PROFILE — what this tenant IS (read before answering anything about scope)
`brain_v2/system_profile/unesco_system_profile.json` — the base fact-sheet. Profile = the SYSTEM;
capability_model = our KNOWLEDGE of it. Never re-derive this from cvers/logs mid-conversation.
- **Platform:** {p.get('landscape', {}).get('product', '?')} · {p.get('landscape', {}).get('components_installed_total', '?')} components installed
  (**installed ≠ implemented** — most ship by default: ~60 country HR versions + industry solutions).
- **PRODUCTIVE modules:** {names(lambda s: s == 'PRODUCTIVE')}
- **Configured / marginal:** {names(lambda s: s in ('CONFIGURED', 'PARTIAL', 'MARGINAL'))}
- **NOT used:** {names(lambda s: s == 'NOT_USED')}
- **Third-party add-ons ACTIVE:** {active_addons} (each = a licence + an independent DATA-EXIT channel)
- **⚡ HOW IT OPERATES:** {om.get('headline', '?')}
  Satellites: {' · '.join(f"{k} {v.get('volume', '')}" for k, v in om.get('satellites', {}).items() if v.get('volume'))}
- **Integration:** {p.get('integration', {}).get('documented_flows', '?')} flows / {p.get('integration', {}).get('external_systems', '?')} external systems ·
  detail in `knowledge/domains/Integration/integration_map_complete.md` + `knowledge/system_operating_model_rfc.md`
- ⚠️ **{p.get('known_limits', {}).get('execution_map_is_a_floor', '')[:170]}...**
"""


def run():
    s = json.load(open(STATE, encoding="utf-8"))
    cm = s.get("capability_model", {})
    dims = cm.get("dimensions", {})
    mat = json.load(open(MAT, encoding="utf-8")) if MAT.exists() else {}
    eb = json.load(open(EB, encoding="utf-8")) if EB.exists() else {}

    # systemic empty columns (computed)
    doms = cm.get("domains", {})
    empty_cols = [d for d in dims if doms and all(doms[n].get(d) == "NONE" for n in doms)]

    rules = s.get("rules", [])
    n_inc = len(s.get("indexes", {}).get("by_incident", {}))
    research_dir = HERE / "research"
    n_research = len(list(research_dir.glob("w*_*.json"))) if research_dir.exists() else 0

    md = f"""# BRAIN INDEX (L1 lean bootstrap — read THIS first, drill the rest)

> Tiered loading (s079). This ~4KB index replaces reading the full ~400K-token brain_state.json at
> bootstrap. Load this, then DRILL on demand via `python brain_v2/graph_queries.py <cmd>`. Read the full
> brain_state.json ONLY when you need depth this index doesn't give.

{_profile_block()}
## ⛔ THE OPERATING MODEL EXISTS — do not re-invent
`brain_v2/capability_model/capability_model.json` = **Layer 15** of brain_state. Domain × {len(dims)}
capabilities; AS-DESIGNED (standard SAP) + AS-RUN (ours); G = delta = the product. Model maturity:
**{mat.get('model_maturity_pct','?')}%**. Do NOT propose a new framework or redesign the schema — EXTEND it.

## Brain at a glance ({len(s.get('objects', {}))} objects · {len(rules)} rules · {len(s.get('claims', []))} claims · {n_inc} incidents · {n_research} closed researches)
16 layers (L0–L15): core_principles · objects · indexes · rules · claims · known_unknowns · falsification ·
superseded · user_questions · data_quality · incidents · blind_spots(0) · interactions · domains_layer(3-axis) ·
**capability_model(L15)**.

## Capability model — {len(dims)} dimensions, systemic empty columns: {', '.join(empty_cols) or 'none'}
{chr(10).join(f"- **{d}** ({v.get('method_tier','?')}) — {v.get('question','')[:80]}" for d, v in dims.items())}

## Where we are (execution sequence s079)
{eb.get('_execution_sequence_s079', {}).get('GATE', 'see execution_backlog.json')}
Pending after gate: {' · '.join(x.split('.')[0] for x in eb.get('_execution_sequence_s079', {}).get('after_gate', []))}

## DRILL — load on demand (don't read the whole brain)
- `python brain_v2/graph_queries.py capability_gaps` — the ranked plan (generated, not written)
- `python brain_v2/graph_queries.py capability <domain>` — a domain's capability coverage
- `python brain_v2/graph_queries.py domain <name>` — domain registry entry
- `python brain_v2/graph_queries.py incident <id>` — incident trace
- `python brain_v2/graph_queries.py what_reads <table>` / `what_depends_on <obj>` — code dependency
- `python brain_v2/graph_queries.py stats` — freshness check
- Research base: `brain_v2/research/` — dedupe new research vs `sources_index.json` (175 urls); never re-assert `findings_registry.json` refuted.
- Full model: `brain_v2/capability_model/` (capability_model · s4_readiness_model · execution_backlog · applied_models · maturity).

## Rules to load first (behavioral DNA — {len(rules)} total)
Read `brain_v2/agent_rules/feedback_rules.json` for all. CRITICAL ones added s079: research_quality_gate (#148),
capability_model_is_the_operating_model (#149), archive_and_dedupe_deep_research (#150),
ask_strategy_before_scoping (#151), model_exists_do_not_reinvent (#152).
"""
    OUT.write_text(md, encoding="utf-8")
    print(f"wrote {OUT} ({len(md)} chars ~ {len(md)//4} tokens)")


if __name__ == "__main__":
    run()
