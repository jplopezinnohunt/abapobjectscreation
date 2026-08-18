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


INSTALL = HERE / "installation" / "installation.json"


def _installation_block():
    """THE ROOT — what this brain is ABOUT, and the deterministic firing order.

    Rendered before everything else because every other block is a statement about
    this object. Distinct in kind from L0 core_principles: that is the agent's
    constitution, this is the subject.
    """
    if not INSTALL.exists():
        return "## ⚠️ INSTALLATION root MISSING — brain_v2/installation/installation.json\n"
    i = json.load(open(INSTALL, encoding="utf-8"))
    idt = i.get("identity", {})
    tr = i.get("traversal", {})
    steps = [f"{k.split('_', 1)[1]}" for k in sorted(tr) if k[0].isdigit()]
    return f"""## 🏛️ ROOT — THE INSTALLATION (what this whole brain is ABOUT)
`brain_v2/installation/installation.json`. Two roots, different kinds: **L0 core_principles = the
AGENT's constitution** (how we work) · **installation = the SUBJECT** (what we model). Anchor, not
container — it holds identity, axes, pointers and the firing order; never content a store owns.
- **{idt.get('tenant', '?')}** — {idt.get('tenant_type', '')}
- **{idt.get('product', '?')}** · character: {idt.get('operating_character', '')}
- Systems: {' · '.join(f"**{k}** ({v.get('role')})" for k, v in idt.get('systems', {}).items())}
  · ⚠️ {idt.get('no_QAS', '')}
- **FIRING ORDER** (deterministic, steps 0–1 mandatory before ANY scope answer — rule #171):
  {' → '.join(steps)}
"""


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



def _process_spine():
    """The end-to-end processes, ranked by how many domains serve them.

    B2R is not first because someone decided it should be — it is first because more
    domains serve it than any other, and this tenant is a public-sector finance
    installation whose reason for existing is budget-to-report. Ranking it by measurement
    rather than by opinion means the order corrects itself if the installation changes.
    """
    st = json.load(open(STATE, encoding="utf-8"))
    doms = (st.get("domains_layer") or {}).get("domains", {})
    spine, cov = {}, {}
    for name, d in doms.items():
        if not isinstance(d, dict):
            continue
        for p in (d.get("primary_processes") or []):
            spine.setdefault(p, []).append(name)
        cov[name] = d.get("coverage_pct")
    if not spine:
        return ""
    rows = []
    for p, names in sorted(spine.items(), key=lambda x: -len(x[1])):
        measured = [c for c in (cov.get(n) for n in names) if c not in (None, "None")]
        avg = round(sum(int(c) for c in measured) / len(measured)) if measured else None
        rows.append(f"- **{p}** — {len(names)} domains: {', '.join(sorted(names))}"
                    + (f" · avg coverage {avg}%" if avg is not None else " · none measured"))
    orphans = [n for n, d in doms.items()
               if isinstance(d, dict) and not (d.get("primary_processes") or [])]
    cross = [n for n in orphans if "BASIS" in (doms[n].get("primary_modules") or [])
             or "CTS" in (doms[n].get("primary_modules") or [])]
    stranded = [n for n in orphans if n not in cross]
    return f"""## 🎯 THE PROCESS SPINE — B2R is the heart, and it is measured that way
Ranked by domains served, not by opinion. This tenant exists to run **budget-to-report**:
public-sector finance, not manufacturing or sales.
{chr(10).join(rows)}
- **Cross-cutting by construction** (serve NO single process because they touch all): {', '.join(cross) or 'none'}
- **⚠️ Stranded** (no process AND not technical — neither in a flow nor across one): {', '.join(stranded) or 'none'}
"""


def _security_block():
    """Security as a FIRST-CLASS topic, because it is not a domain and so it is invisible.

    Looking for security in the domain list finds nothing, which reads as 'not a concern'.
    It is capability column E, empty nearly everywhere — one missing MODEL capability, not
    21 separate gaps. Closing it once lifts every row.
    """
    st = json.load(open(STATE, encoding="utf-8"))
    cm = st.get("capability_model", {})
    doms = cm.get("domains", {})
    have = [n for n, d in doms.items() if isinstance(d, dict)
            and str(d.get("E_AUTH")) in ("HAVE", "PARTIAL")]
    claims = [c for c in st.get("claims", []) if isinstance(c, dict)
              and any(k in str(c.get("claim", "")).upper()
                      for k in ("SOD", "S_RFC", "AUTHORIZATION", "SEGREGATION"))]
    return f"""## 🔐 SECURITY — a COLUMN, not a domain (that is why searching for it fails)
`E_AUTH` has content in **{len(have)} of {len(doms)}** domains: {', '.join(have) or 'none'}.
It is ONE missing model capability, not {len(doms)} separate gaps — closing it once lifts every row.
- **Known and verified:** portal-as-user RFC writes carry SoD conflicts. Root: `S_RFC=*` plus a
  custom write FM that skips the object check, so the control has to live at the CALL and DATA
  layer, not at the role layer.
- **What that means for any answer about roles:** the role model is NOT the control surface here.
  A clean SU01/PFCG picture does not mean segregation holds.
- Claims touching authorization: {len(claims)} · drill: `graph_queries.py capability E_AUTH`
{_security_store()}"""


def _security_store():
    """The posture store, when it exists. Says what we CANNOT see, never silence."""
    f = HERE / "security_posture.json"
    if not f.exists():
        return "- No posture store yet — findings are still landing in claim prose.\n"
    S = json.load(open(f, encoding="utf-8"))
    c = S.get("counts", {})
    miss = [x["component"] for x in S.get("components", [])
            if x.get("state") == "MISSING_INPUT"]
    return (f"- **Posture store** `brain_v2/security_posture.json` — {c.get('READY',0)} ready · "
            f"{c.get('MISSING_INPUT',0)} missing input · {len(S.get('established_findings',[]))} "
            f"findings already stored as RECORDS.\n"
            f"- **Cannot see yet:** {', '.join(miss) or 'nothing'} — MISSING_INPUT means WE "
            f"CANNOT SEE, never 'there is nothing'.\n")


def _integration_block():
    """Integration as a first-class topic — it is the richest thing this tenant has.

    80% of business traffic is external. Whoever reads this index must know that BEFORE
    answering anything about how the system is used, or they will describe a dialog system
    that does not exist.
    """
    inv, bnd, att = HERE / "interface_inventory.json", HERE / "interface_boundary.json", HERE / "change_attribution.json"
    if not inv.exists():
        return ""
    I = json.load(open(inv, encoding="utf-8"))
    B = json.load(open(bnd, encoding="utf-8")) if bnd.exists() else {}
    A = json.load(open(att, encoding="utf-8")) if att.exists() else {}
    sm = B.get("summary", {})
    ch = {}
    for r in (A.get("classes") or {}).values():
        for c in r.get("channels_DERIVED_from_logs", []):
            ch[c["channel"]] = ch.get(c["channel"], 0) + 1
    return f"""## 🔌 INTEGRATION — the richest surface, and the one that explains the operating model
**SAP here is a system-of-record fed by satellites, not a dialog system.** Any answer about how
the system is used that assumes people in screens is wrong before it starts.
- **{len(I.get('interfaces', []))} interface records** (derived, queryable — `brain_v2/interface_inventory.json`):
  {' · '.join(f"{k} {v}" for k, v in sorted((I.get('counts') or {{}}).items(), key=lambda x: -x[1]))}
- **The boundary is mostly dead:** {sm.get('destinations_configured','?')} RFC destinations configured,
  **{sm.get('destinations_live','?')} live**, **{sm.get('destinations_dead','?')} dead**,
  **{sm.get('destinations_undeclared','?')} undeclared** — traffic crossing with no configuration entry.
- **Write channels, derived per object class:** {' · '.join(f"{k} {v}" for k, v in sorted(ch.items(), key=lambda x: -x[1]))}
- **An empty transaction code is a POINTER, not a gap** — usually a BAPI/RFC whose design never set
  one. Reading it as 'batch' loses the interface.
- **What CANNOT be seen:** inbound web-service CALLS. The SOAP monitor is off, so existence and
  activation are verified and execution is not. UNVERIFIED, never 'unused'.
"""


def _maturity_block():
    """Maturity of the METHOD, measured from artifacts — not a self-assessment."""
    mc = HERE / "meta_capability.json"
    if not mc.exists():
        return ""
    M = json.load(open(mc, encoding="utf-8"))
    dims = M.get("dimensions", {})
    rows = sorted(((v.get("score") if isinstance(v, dict) else v), k) for k, v in dims.items())
    weak = [f"**{k}** {v:.2f}" for v, k in rows[:3]]
    strong = [f"{k} {v:.2f}" for v, k in rows[-3:]]
    return f"""## 📈 MATURITY OF THE METHOD — {M.get('meta_maturity_pct','?')}%, measured from artifacts
Not a self-assessment: each dimension is derived from what is on disk.
- **Weakest:** {' · '.join(weak)}
- **Strongest:** {' · '.join(reversed(strong))}
- **Read this together with the capability grid.** Two independent instruments agree: strong at
  COLLECTING, weak at VERIFYING. We know precisely what the system DOES and little about what it
  SHOULD do — which is the same finding as the near-empty `S_STANDARD_REF` column.
"""


NL = chr(10)

DONE_STATUSES = {"CLOSED", "RESOLVED", "DONE", "CLOSED_WITH_CLEANUP"}


def _open_work_block():
    """The incidents that still need something DONE, deadline first.

    The index used to print the incident COUNT and never say which ones. A count is not a
    pointer: a fresh session could only reach INC-EGYPT-PPC by already knowing to ask for it
    by name, which is precisely what a fresh session does not know. Measured at s099 --
    BRAIN_INDEX.md had zero mentions of purpose-of-payment, PPC, Egypt or T015L while the
    incident record held the complete ten-code fix and the transport order.

    Generated, so it covers the NEXT incident too, not just the one that exposed the hole.
    """
    f = HERE / "incidents" / "incidents.json"
    if not f.exists():
        return "## WARNING - incidents.json MISSING" + NL
    data = json.load(open(f, encoding="utf-8"))
    inc = data if isinstance(data, list) else data.get("incidents", [])
    live = [i for i in inc if str(i.get("status", "")).upper() not in DONE_STATUSES]
    if not live:
        return "## OPEN WORK - no incident is awaiting action" + NL

    # a hard date outranks everything else
    live.sort(key=lambda i: (i.get("deadline") or "9999-99-99", i.get("id", "")))
    shown, extra = live[:8], max(0, len(live) - 8)

    lines = []
    for i in shown:
        due = " - **DUE {}**".format(i["deadline"]) if i.get("deadline") else ""
        lines.append("- `{}` - {}{} - {}".format(
            i.get("id"), i.get("status"), due, (i.get("title") or "")[:96]))
        if i.get("next_action"):
            lines.append("  - NEXT: {}".format(i["next_action"][:260]))
        lines.append("  - drill: `python brain_v2/graph_queries.py incident {}`".format(
            i.get("id")))

    # No silent cap. The first 8 get full detail; the rest are still LISTED by id, because
    # an incident that does not appear here cannot be found by a session that does not
    # already know its name -- which is the entire failure this block exists to prevent.
    # knowledge_reachability_check.py enforces exactly that, and caught this cap on its
    # first run: INC-FXREVAL-OB09 was live and unreachable.
    tail = ""
    if extra:
        rest = "  ".join("`{}` ({})".format(i.get("id"), i.get("status"))
                         for i in live[8:])
        tail = (NL + "_{} more open, drill by id:_ {}".format(extra, rest) + NL)
    return ("## OPEN WORK - incidents awaiting action ({} live, deadline first)".format(len(live))
            + NL + NL.join(lines) + NL + tail)


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

{_installation_block()}
{_profile_block()}
{_process_spine()}
{_integration_block()}
{_security_block()}
{_maturity_block()}
{_open_work_block()}
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
