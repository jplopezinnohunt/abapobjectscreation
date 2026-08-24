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

# REGLAS QUE APLICAN AQUI (citadas para que existan en su punto de uso, no solo en el JSON):
#   feedback_register_on_create_not_at_close
#     -> el momento es cuando nace un modelo y hay que anunciarlo: este genera el anuncio
import json
import os
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


_SERVES_CACHE = {}


def _serves(art_path, cap=3_000_000):
    """Que dominios cubre un artefacto -- MEDIDO en su contenido, no clasificado a mano.

    Ninguno de los 47 algoritmos declaraba dominio, y ponerselo a ojo habria sido inventarlo.
    Esto lee el fichero y cuenta que claves de dominio del registro aparecen dentro. Si un
    artefacto no nombra ninguna, se dice: `--`. Un fichero grande se corta al leer, porque el
    indice tiene que generarse rapido.
    """
    if art_path in _SERVES_CACHE:
        return _SERVES_CACHE[art_path]
    base = os.path.basename(art_path)
    ruta = None
    for d in ("brain_v2", "process_mining", "Zagentexecution", "scripts"):
        raiz = HERE.parent / d
        if not raiz.is_dir():
            continue
        for root, _, files in os.walk(raiz):
            if ".git" in root:
                continue
            if base in files:
                ruta = os.path.join(root, base)
                break
        if ruta:
            break
    doms = []
    if ruta:
        try:
            if os.path.getsize(ruta) <= cap:
                txt = open(ruta, encoding="utf-8", errors="ignore").read()
                reg = json.load(open(HERE / "domains" / "domains.json",
                                     encoding="utf-8")).get("domains", {})
                doms = sorted({d for d in reg if len(d) > 3 and d in txt})
        except Exception:
            doms = []
    val = ", ".join(doms[:4]) + (f" +{len(doms)-4}" if len(doms) > 4 else "") if doms else "--"
    _SERVES_CACHE[art_path] = val
    return val


def _findings_block():
    """QUE ANALISIS EXISTEN Y DONDE ATERRIZAN. El indice de los analisis, generado.

    El gate de alcanzabilidad encontro 24 artefactos INVISIBLES de 31: existian, se
    regeneraban en cada rebuild, eran correctos, y no se llegaba a ellos desde ningun punto de
    entrada. Se generaban para nadie.

    Meterlos a mano habria inflado el indice y habria envejecido igual. La fuente correcta ya
    existia: `algorithms.json` dice de cada algoritmo QUE HACE (`does`) y DONDE DEJA su
    resultado (`lands_in`). Este bloque lo lee y lo publica.

    Se agrupa por `operates_on` porque esa es la pregunta con la que se llega: "quiero saber
    algo de los LOGS" antes que "quiero el fichero X".
    """
    algos = {}
    try:
        algos = json.load(open(HERE / "methods" / "algorithms.json",
                               encoding="utf-8")).get("algorithms", {})
    except Exception:
        return ""
    by = {}
    for aid, a in algos.items():
        li = str(a.get("lands_in") or "")
        art = ""
        for tok in li.replace(",", " ").replace("(", " ").replace(")", " ").split():
            if tok.endswith(".json") and "/" in tok:
                art = tok
                break
        if not art:
            continue          # tecnicas puras: no producen fichero, no van en este indice
        grp = str(a.get("operates_on") or "otros")
        if len(grp) > 22:
            grp = grp[:22] + "..."
        by.setdefault(grp, []).append((aid, str(a.get("does") or "")[:74], art,
                                       str(a.get("state") or ""), _serves(art)))
    if not by:
        return ""
    out = []
    for grp in sorted(by, key=lambda g: -len(by[g])):
        out.append(f"\n**{grp}**\n")
        out.append("| algoritmo | qué contesta | dominios que cubre | aterriza en |")
        out.append("|---|---|---|---|")
        for aid, does, art, st, srv in sorted(by[grp]):
            flag = " ⚠️" if st in ("FRAGILE", "WEAK") else ""
            out.append(f"| `{aid}`{flag} | {does} | {srv} | `{art}` |")
    n = sum(len(v) for v in by.values())
    return f"""## 🧭 LOS {n} ANÁLISIS QUE EXISTEN, Y DÓNDE DEJAN SU RESULTADO
El gate de alcanzabilidad encontró **24 artefactos invisibles de 31**: existían, se regeneraban
en cada rebuild, eran correctos, y **no se llegaba a ellos desde ningún sitio**. Se generaban
para nadie. Esta tabla se genera de `algorithms.json`, que ya sabía qué hace cada uno y dónde
lo deja — solo que nadie lo publicaba.

⚠️ = el algoritmo está marcado FRAGILE o WEAK: **lee su `failure_mode` antes de usar su salida.**
{chr(10).join(out)}

- 📐 **Cómo encajan entre sí:** `knowledge/exploration_architecture.md` — la cadena completa,
  las 4 superficies, las 5 vías, los 4 grados y las trampas que costó llegar ahí.
- **Ninguno de estos ficheros se lee entero.** Se abren con
  `python brain_v2/graph_queries.py search <termino>` o directamente cuando la tabla de arriba
  dice que contestan tu pregunta.
- **Comprobar que siguen siendo alcanzables:**
  `python Zagentexecution/quality_checks/artifact_reachability_check.py`
"""


def _stores_block():
    """QUE HAY Y COMO SE ABRE. El bloque que faltaba, y su ausencia era el agujero.

    Medido 2026-08-24, comparando cada store contra lo que los puntos de entrada NOMBRAN:
        reglas          230 de 230 alcanzables    0% invisible
        incidentes       11 de  13               15%
        companions       10 de  42               76%
        docs de dominio   5 de 143               96%
        claims           10 de 575               98%
        memorias metodo   0 de 129              100%

    Las REGLAS son el unico store sano, y por un motivo concreto: el indice las enumera. Ese
    es el patron que funciona y no se habia aplicado a nada mas.

    El resto depende de que alguien sepa preguntar. `load_domain.py` resuelve el acceso POR
    TEMA -- pero hay que nombrar el tema primero, y solo se encuentra lo que ya se sabe que
    existe. Ese es el mecanismo exacto de la perdida.

    La solucion NO es volcarlo todo aqui: eso recrea el problema de los 400K que la carga
    escalonada vino a resolver. Es decir CUANTO hay y CON QUE COMANDO se abre. Un inventario,
    no el contenido.
    """
    import glob as _g

    def _n(path, key=None):
        try:
            d = json.load(open(HERE / path, encoding="utf-8"))
            if key:
                d = d.get(key, d)
            return len(d)
        except Exception:
            return "?"

    docs = len(_g.glob(str(HERE.parent / "knowledge" / "domains" / "**" / "*.md"),
                       recursive=True))
    try:
        cos = len(json.load(open(HERE.parent / "companions" / "companions.json",
                                 encoding="utf-8")))
    except Exception:
        cos = "?"
    return f"""## 🗄️ LO QUE HAY, Y CON QUÉ COMANDO SE ABRE
Este bloque existe porque **solo se encuentra lo que ya se sabe que existe**. Medido: los
claims eran 98% invisibles desde aquí, los docs de dominio 96%, y las memorias de método
**100%**. Las reglas eran el único store sano — porque este índice las enumera. Aquí está el
inventario del resto; el contenido se abre con su comando.

| Store | Cuánto | Cómo se abre |
|---|---:|---|
| **claims** | {_n('claims/claims.json')} | `python brain_v2/graph_queries.py search <termino>` |
| **docs de dominio** | {docs} | `python brain_v2/load_domain.py <tema>` — **carga el dominio ENTERO** |
| **companions** | {cos} | `companions/how_unesco_works.html` los indexa todos |
| **incidentes** | {_n('incidents/incidents.json')} | `python brain_v2/graph_queries.py incident <id>` |
| **reglas** | {_n('agent_rules/feedback_rules.json')} | `brain_v2/agent_rules/feedback_rules.json` |
| **memorias de MÉTODO** | {_n('methods/algorithm_memory.json', 'memories')} | `brain_v2/methods/algorithm_memory.json` — INSTRUMENT · SUBSTRATE · CARRIER · TRAP |
| **algoritmos** | {_n('methods/algorithms.json', 'algorithms')} | `brain_v2/methods/algorithms.json` — lee su `failure_mode` ANTES de correrlo |

- ⚠️ **Las memorias de MÉTODO son el store que nos hace mejores y nadie apuntaba a él.** Dicen
  qué campo miente, qué lectura produce una respuesta segura y falsa, hasta dónde ve un
  instrumento. Léelas antes de medir algo nuevo.
- 🔍 **Gate de alcanzabilidad:** `python Zagentexecution/quality_checks/artifact_reachability_check.py`
  — comprueba que cada artefacto prometido por un algoritmo exista, lo lea alguien, y se llegue
  a él. En su primera corrida: **24 invisibles y 4 ausentes de 31**.
"""


def _comprehension_block():
    """Is the EXECUTION SURFACE closed? Lives in the entry index on purpose.

    A20 measured this and wrote a JSON that nothing read. Guardar no es recuperar: if a fact
    is not reachable from the entry points it does not exist, and this project has measured
    that failure before -- an incident held a complete fix while BRAIN_INDEX and MEMORY had
    zero mentions of it. So the number that says how much of this system we can actually
    account for belongs HERE, next to maturity, not in a file someone has to know to open.
    """
    ci = HERE / "comprehension_index.json"
    if not ci.exists():
        return ""
    C = json.load(open(ci, encoding="utf-8"))
    h = C.get("headline", {})
    rows = []
    for name, v in (C.get("surfaces") or {}).items():
        if "error" in v:
            continue
        t = v.get("pct_by_track", {})
        rows.append(f"- **{name}** — {v.get('executions_graded', 0):,} ejec · "
                    f"tecnico {t.get('TECHNICAL', 0)}% · negocio {t.get('BUSINESS', 0)}% · "
                    f"sin clasificar **{t.get('UNCLASSIFIED', 0)}%**")
    gaps = list((C.get("process_map_gaps") or {}).get("domains") or {})
    gb = gn = 0
    for v in (C.get("surfaces") or {}).values():
        g = v.get("business_grades_executions") or {}
        gb += sum(g.values()); gn += g.get("3", 0)
    ex = round(100 * gn / gb, 1) if gb else 0
    mv = C.get("movement_since_last")
    mv_txt = ("sin linea base comparable" if mv is None else
              ("**no se movio** desde la ultima corrida — eso ES el hallazgo" if mv == 0
               else f"{mv:+} desde la ultima corrida"))
    return f"""## 🔍 ¿ENTENDEMOS LO QUE EL SISTEMA EJECUTA? — {h.get('pct_unclassified', '?')}% sin clasificar
Cuatro superficies, porque ejecutar no es solo un programa: lo que corre, lo que CAMBIA, lo que
corre solo, y lo que ENTRA por RFC — esta ultima es la mayor y la que no esta en SLGREPNA.
{NL.join(rows)}
- **TECNICO es una respuesta, no un hueco** (el despachador y el planificador son fontaneria).
  El hueco real es SIN CLASIFICAR: {h.get('unclassified_executions', 0):,} de {h.get('executions_total', 0):,}.
- **Situar no es explicar:** solo el **{ex}%** de las ejecuciones de negocio llega a grado 3
  (alguien lo escribio con evidencia). Ese salto no lo da ningun algoritmo.
- Movimiento: {mv_txt} · sin cadena de proceso: {', '.join(gaps) or 'ninguno'} (stranded, no olvido)
- **{C.get('keep_exploring_total', 0)} objetos por explorar** ({C.get('keep_exploring_custom', 0)} custom) —
  la lista es `brain_v2/comprehension_index.json` → `keep_exploring`, ordenada por ejecuciones,
  y es el trabajo del agente `log-process-discovery`.
- Lo aprendido sobre COMO explorar (no sobre el dato) vive aparte, en
  `brain_v2/methods/algorithm_memory.json`: INSTRUMENT · SUBSTRATE · CARRIER · TRAP.
"""


NL = chr(10)

def _knowledge_block(top=10):
    """The deepest analyses we hold, and the terms each actually covers.

    OPEN WORK makes pending incidents reachable. This makes KNOWLEDGE reachable, which is a
    different problem and the one that bit us: the DMEE work lives in a companion titled
    "BCM Structured Address Change" tagged "finance" -- 965 mentions of DMEE and not a word
    of it in the name or the registry entry. A session that did not live through that work
    could not know it existed, and would re-derive it.

    Terms are filtered to those carried by 2..15 of the companions. Below 2 is a one-off;
    above 15 is vocabulary everything mentions (system, payment, transport, fund) which says
    nothing about WHERE to look. 'dmee' sits at 15 -- precisely the band that was invisible.
    """
    f = HERE.parent / "companions" / "companion_graph.json"
    if not f.exists():
        return "## WARNING - companion_graph.json missing, run scripts/build_companion_graph.py" + NL
    g = json.load(open(f, encoding="utf-8"))
    nodes = g.get("nodes", [])
    if not nodes:
        return "## WHAT WE KNOW DEEPLY - no companions indexed" + NL

    df = {}
    for n in nodes:
        for e in n.get("entities") or []:
            k = str(e).lower()
            df[k] = df.get(k, 0) + 1
    lo, hi = 2, 15

    lines = []
    for n in sorted(nodes, key=lambda z: -z.get("n_signals", 0))[:top]:
        terms = [e for e in (n.get("entities") or []) if lo <= df.get(str(e).lower(), 0) <= hi]
        if not terms:
            terms = list(n.get("entities") or [])[:6]
        lines.append("- `{}` - {} - {}".format(
            n.get("file"), n.get("title"), ", ".join(sorted(terms)[:9])))

    return ("## WHAT WE KNOW DEEPLY - {} companions; the {} densest, and what each covers"
            .format(len(nodes), min(top, len(nodes))) + NL
            + "> Do NOT re-derive these. Search any term across every store AND the "
              "companions: `python brain_v2/graph_queries.py search <term>`." + NL + NL
            + NL.join(lines) + NL)


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



def _bank_findings():
    """Hallazgos del explorador del modelo de banca, en el indice.

    Existe por la regla de que el conocimiento tiene que ser ALCANZABLE desde los puntos de
    entrada: el explorador puede emitir NEW o BLIND en cada rebuild, y si nadie lo lee esta
    gritando al vacio. Solo se muestran los veredictos que piden accion -- STABLE se calla,
    porque un bloque que siempre dice algo deja de leerse.
    """
    f = HERE / "bank_model_findings.json"
    if not f.exists():
        return ""
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        return ""
    act = [x for x in d.get("findings", []) if x.get("verdict") in ("NEW", "BLIND", "RISK", "DRIFT")]
    if not act:
        return ""
    out = ["## BANCA - el explorador del modelo encontro {} cosa(s) que pedir accion".format(len(act)),
           "> `python brain_v2/bank_model_explorer.py` (paso 2i del rebuild). El CRITERIO lo pone el",
           "> agente `bank-process-discovery`; el modelo vive en",
           "> `knowledge/domains/Treasury/house_bank_operating_roles.md`."]
    for x in act[:6]:
        out.append("- `{}` - {}".format(x["verdict"], x["title"]))
    if len(act) > 6:
        out.append("- _{} mas en `brain_v2/bank_model_findings.json`_".format(len(act) - 6))
    return NL.join(out) + NL


def _agents_block():
    """Los AGENTES son la superficie de CAPACIDAD: lo que sabemos HACER, no solo lo que sabemos.
    Se derivan de .claude/agents/*.md, asi que un agente nuevo aparece solo, sin tocar esto.

    Nace de s102: se construyeron tres capacidades de alineamiento (GL, variantes, FSV) y el
    INDICE -- que es uno de los dos puntos de entrada de una sesion nueva -- no las mencionaba.
    Regla feedback_knowledge_must_be_reachable_from_the_entry_points."""
    import re as _re
    d = HERE.parent / ".claude" / "agents"
    if not d.exists():
        return "## AGENTES - directorio .claude/agents no encontrado" + NL
    out = []
    for f in sorted(d.glob("*.md")):
        txt = f.read_text(encoding="utf-8", errors="replace")[:1500]
        m = _re.search(r"^name:[ \t]*(.+)$", txt, _re.M)
        name = m.group(1).strip() if m else f.stem
        desc = ""
        lines = txt.splitlines()
        for i, ln in enumerate(lines):
            if ln.startswith("description:"):
                for nxt in lines[i + 1:i + 4]:
                    t = nxt.strip()
                    if not t or t.endswith(":"):
                        break
                    desc += " " + t
                break
        out.append("- **`%s`** - %s" % (name, " ".join(desc.split())[:145]))
    tail = ""
    if (HERE.parent / "knowledge" / "alignment_executors_model.md").exists():
        tail = (NL + "**Modelo de ejecutores de alineamiento P01 -> D01/V01**: "
                "`knowledge/alignment_executors_model.md` - la escalera de canales "
                "(API estandar / BC-Set / escritura directa bajo excepcion), los medidores, "
                "los actuadores por objeto y el metodo comun. Excepciones autorizadas, lista "
                "cerrada: `.agents/skills/sap_master_data_sync/SKILL.md`." + NL)
    return ("## AGENTES - lo que sabemos HACER (%d disponibles)" % len(out) + NL
            + NL.join(out) + NL + tail)


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

## ⛔ THIS INDEX ORIENTS YOU. IT DOES NOT MAKE YOU COMPETENT ON A TOPIC.
**The moment a topic or domain is named, run the DOMAIN LOAD and read every part it emits —
before proposing, diagnosing or answering anything:**
```
python brain_v2/load_domain.py <topic>     # dmee · "purpose of payment" · avc · ebs · Payment_BCM · --list
```
It emits ONE ordered payload: domain docs + companions (prose) + claims + incidents + annotations +
rules + code objects + Gold tables + capability rows, chunked into `part_NN.md`, plus a PERIPHERAL
list of what it deliberately left out. A `graph_queries` drill returns fragments; this returns the
domain. Measured on DMEE: 40 docs + 20 companions + 165 claims + 11 incidents that no drill surfaces.
**Do not wait to be asked** — rule `feedback_load_the_domain_before_you_reason` (CRITICAL, s100).

{_installation_block()}
{_profile_block()}
{_process_spine()}
{_integration_block()}
{_security_block()}
{_maturity_block()}
{_comprehension_block()}
{_stores_block()}
{_findings_block()}
{_open_work_block()}

{_agents_block()}
{_bank_findings()}
{_knowledge_block()}
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
- `python brain_v2/load_domain.py <topic>` — **THE DOMAIN LOAD. Run this FIRST when a topic is named**
  (everything the topic knows, ordered + chunked). The drills below are for follow-up questions, not
  for getting up to speed.
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
