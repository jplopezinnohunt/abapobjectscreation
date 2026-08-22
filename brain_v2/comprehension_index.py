"""ALGORITHM A20 - THE COMPREHENSION INDEX.

THE QUESTION, AND IT IS THE MATURITY QUESTION
    Is everything this system EXECUTES identified and classified -- and of the part that is
    not merely technical, do we understand it and can we name the domain it belongs to?

    Not "how many objects are catalogued". Whether the execution surface is CLOSED.

FOUR SURFACES, BECAUSE EXECUTION IS NOT ONLY A PROGRAM
    Measuring programs alone answers a quarter of the question and reads like the whole one.

        OBJECTS  what ran             RSAU/SM20     program and report names
        CHANGES  what was altered     CDHDR         the tcode that made the change
        JOBS     what runs unattended TBTCO/TBTCP   job -> program -> VARIANT
        RFC      what ENTERS          RSAU.PARAM3   the function module a satellite called

    A job is not its program: the program says what CAN be done, the variant says what IS
    done. A change is not an execution: something can run all day and alter nothing, and one
    quiet posting can alter the ledger.

TWO TRACKS, BECAUSE "TECHNICAL" IS AN ANSWER AND NOT A GAP
    17.5M of this log's executions are SAPMSSY1 -- the dispatcher every dialog and RFC call
    passes through. 2.4M are RSBTCRTE, the batch scheduler. Those are IDENTIFIED, and calling
    them "not understood" would make the index say the system is a mystery when in fact its
    plumbing is exactly where plumbing should be. So:

        TECHNICAL      substrate, Basis, security, transport, third-party runtime.
                       Classifying it as technical IS the answer. It is closed, not open.
        BUSINESS       everything else -- and here a domain alone is not enough. It needs
                       a process chain, an actor shape, and finally an explanation.
        UNCLASSIFIED   we cannot even say which of the two it is. This is the real gap,
                       and it is the number that must go to zero.

    The trap is that TECHNICAL becomes a dumping ground. A6 already solved this: substrate is
    matched LAST, never before a business rule. This index inherits that and additionally
    NAMES its technical domains explicitly instead of accepting whatever falls there.

THE BUSINESS GRADES
        1 PLACED     domain + process chain (assigned by A4's ladder, not by eye)
        2 DESCRIBED  we know WHO, WHEN and through WHICH CHANNEL -- proven by a SHAPE
                     (a concentrated actor set, or a real temporal profile), never by the
                     mere presence of a user field, which everything has
        3 EXPLAINED  a store names it with prose, a claim or an annotation. Never granted
                     from plausibility by this script.

    Reported as a distribution, never as one number: 90% placed with 5% explained says the
    true thing -- good at labelling, poor at explaining -- and one blended percentage hides
    exactly that.

WHY IT EXISTS
    2026-08-22. The discovery loop had been stopped for 75 days and nobody noticed, because
    nothing measured whether understanding MOVED. A6 says it in its own record: "watch the
    TREND, not the size: a frontier that stops moving means the discovery loop stopped
    running". A frontier measures what is left; this measures what is held, and keeps the
    derivative so a stalled loop is visible to whoever looks next.

THE FOURTH SURFACE, AND WHY IT WAS THE POINT
    The first three read PROGRAM names (RSAU.SLGREPNA), the TCODE that made a change
    (CDHDR.TCODE) and the program of a job step (TBTCP.PROGNAME). An inbound RFC call is in
    none of them: in SLGREPNA it shows up as SAPMSSY1, the dispatcher, which is technical --
    so those three saw the pipe and not what flows through it. The function module's real
    name travels in PARAM3 of the 'RFC Function Call' rows, and that is surface 4.

    It is not an extra: 80.6% of this tenant's business RFC traffic is driven by external
    satellites, so this is how work mostly ENTERS the system. Running with three surfaces
    reported CROSS_CUTTING at exactly 0 executions with Integration -- a domain that is
    plainly not idle -- invisible, because its objects are function modules.

    A function module does not hang off TADIR directly, it hangs off its function GROUP, so
    it is classified through A4's TFDIR.APP_DOMAIN overlay, which is the FIRST rung of
    domain_of. Skipping that overlay lets BAPIs -- exactly the satellite calls -- dominate
    the frontier while looking unclassifiable.

WHAT IT FEEDS
    brain_v2/comprehension_index.json -> the brain index, the domain docs, and the
    log-process-discovery agent, whose worklist IS `keep_exploring`, ranked by executions.

FAILURE MODES ALREADY HIT, KEPT HERE SO THEY ARE NOT HIT AGAIN
    1. Reading A4's `top_objects_by_domain` (a 317-name SUMMARY) instead of running A4's
       classifier: every object fell to grade 0 and the index confidently reported that we
       understand nothing.
    2. Looking up a `domain_axes.process` field that does not exist: the map came back empty,
       every object lost its grade, and nothing failed. Hence the assert.
    3. Counting Basis as incomprehension: 92.8% "ununderstood", of which 24.3M executions
       were the dispatcher and the scheduler.
    All three produced a plausible number from a broken join. A number that looks like a
    finding is the most expensive kind of defect here.

Run:  python brain_v2/comprehension_index.py
"""
import os, sys, json, sqlite3, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
BRAIN = os.path.join(ROOT, "brain_v2", "brain_state.json")
DOMAINS = os.path.join(ROOT, "brain_v2", "domains", "domains.json")
OUT = os.path.join(ROOT, "brain_v2", "comprehension_index.json")
HIST = os.path.join(ROOT, "brain_v2", "comprehension_history.jsonl")

# Grade 2 needs a SHAPE, not a field that happens to be populated.
CONCENTRATED_ACTORS = 5
MIN_EXECS_FOR_PROFILE = 20
PEAK_SHARE = 0.40

# Domains whose nature IS technical. Named explicitly and kept SHORT on purpose: the moment
# this list grows to absorb something awkward, the index starts lying in our favour.
TECHNICAL_DOMAINS = {
    "Basis_Security", "Technical_Substrate", "Security", "CTS_Transport",
    "BW_embedded", "ThirdParty_Addon",
}
UNPLACED = {"Uncatalogued", "", None}


def load(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def process_resolver():
    """domain -> (process chains, kind). THE authority, in the order the model declares it.

    Three stores carry this and they are not equal:
      1. brain_state.domains_layer.domains[*].primary_processes -- the RESOLVED answer, and
         what build_brain_index prints as the process spine. Primary.
      2. capability_model/ontology.json .process_axis -- the VOCABULARY contract, gated at
         step 0. Carries rows the registry lacks, and the aliases.
      3. domains.json .process_map -- the oldest and narrowest: 5 chains, no A2R, no O2C.

    The first version of this index read only (3) and reported CO, TRM, PBC, PM, SD and
    RE_FX as domains with no process chain -- 21% of business changes stuck at grade 0. Five
    of those six were already answered in (1) and (2): CO is B2R, TRM is T2R, PBC is B2R+H2R,
    PM is P2P, SD is O2C. Nothing was missing from the model; the index was reading the
    thinnest of three files. So: UNION, never pick one, because losing a chain silently
    degrades every object under it.

    A domain with no chain in ANY of the three is not automatically a gap:
      CROSS_CUTTING  serves every process, so demanding one chain is a category error.
                     Same rule build_brain_index uses: BASIS or CTS among primary_modules.
      STRANDED       no process and not technical either. A real, named gap -- RE_FX and
                     Output. Naming it is the point; it does not get quietly absorbed.

    Alias resolution is EXACT, never prefix. The ontology's own _resolution_rules say so:
    "EXACT match only - no token matching, no fuzzy fallback". The earlier prefix match here
    violated that contract and would happily resolve PS from PSM_FM.
    """
    chains = collections.defaultdict(set)
    modules = {}

    b = load(BRAIN)
    for name, e in ((b.get("domains_layer") or {}).get("domains") or {}).items():
        if not isinstance(e, dict):
            continue
        for pr in (e.get("primary_processes") or []):
            chains[name].add(pr)
        modules[name] = e.get("primary_modules") or []

    alias = {}
    onto = load(os.path.join(ROOT, "brain_v2", "capability_model", "ontology.json"))
    for e in onto.get("domains") or []:
        ck = e.get("canonical_key")
        if not ck:
            continue
        alias[ck] = ck
        for a in e.get("aliases") or []:
            alias[a] = ck
        for pr in (e.get("process_axis") or []):
            chains[ck].add(pr)
        modules.setdefault(ck, e.get("module_axis") or [])

    pm = (load(DOMAINS).get("process_map") or {})
    for proc, entry in pm.items():
        if proc.startswith("_") or not isinstance(entry, dict):
            continue
        for dom in entry.get("domains") or []:
            chains[alias.get(dom, dom)].add(proc)

    assert chains, "ninguna de las 3 fuentes trae cadenas de proceso - no grades sobre esto"

    def resolve(domain):
        if not domain:
            return [], "UNKNOWN"
        key = alias.get(domain, domain)
        ch = sorted(chains.get(key, ()))
        if ch:
            return ch, "PLACED"
        mods = modules.get(key) or []
        if "BASIS" in mods or "CTS" in mods:
            return [], "CROSS_CUTTING"
        return [], "STRANDED"

    return resolve


def a4_classifier():
    """A4's own classifier, reused -- not re-implemented. Its docstring says it is reusable
    on purpose 'so nobody reinvents the wheel next session'; taking it at its word is the
    difference between one source of truth and two that drift."""
    # A4 importa gold_ref de su propio directorio: sin esto el import falla y el indice
    # entero se cae antes de medir nada.
    pm_dir = os.path.join(ROOT, "process_mining")
    if pm_dir not in sys.path:
        sys.path.insert(0, pm_dir)
    from importlib import util as _u
    spec = _u.spec_from_file_location(
        "eodm", os.path.join(ROOT, "process_mining", "executed_objects_domain_map.py"))
    m = _u.module_from_spec(spec)
    spec.loader.exec_module(m)
    con = sqlite3.connect(GOLD, timeout=180)     # ensure_cache writes its cache tables
    domain_of, ctx = m.make_classifier(con)
    return domain_of, ctx


def reality_classifier():
    """A19: is this identifier an OBJECT or a generated instance? Grading a generated
    instance would manufacture thousands of false gaps, which is what A19 exists to stop."""
    from importlib import util as _u
    spec = _u.spec_from_file_location(
        "lrf", os.path.join(ROOT, "process_mining", "log_reality_filter.py"))
    m = _u.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.classify_program


def explained_objects():
    """Objects a STORE actually names. Grade 3 comes from evidence someone wrote."""
    b = load(BRAIN)
    out = set()
    for name, o in (b.get("objects") or {}).items():
        if isinstance(o, dict) and (o.get("knowledge_docs") or o.get("claims")
                                    or o.get("annotations")):
            out.add(name)
    return out


def grade_item(name, execs, actors, bands, dom, resolve, explained):
    """-> (track, grade). track in BUSINESS | TECHNICAL | CROSS_CUTTING | STRANDED | UNCLASSIFIED."""
    if dom in TECHNICAL_DOMAINS:
        return "TECHNICAL", 1                      # identified as substrate = closed
    if dom in UNPLACED:
        return "UNCLASSIFIED", 0
    proc, kind = resolve(dom)
    if kind == "CROSS_CUTTING":
        return "CROSS_CUTTING", 1                  # serves every chain: closed, not open
    if kind == "STRANDED":
        return "STRANDED", 0                       # real gap, and it is NAMED
    if not proc:
        return "BUSINESS", 0
    total = max(1, execs)
    shaped = (actors <= CONCENTRATED_ACTORS or
              (total >= MIN_EXECS_FOR_PROFILE and max(bands) / total >= PEAK_SHARE))
    if not shaped:
        return "BUSINESS", 1
    return "BUSINESS", (3 if name in explained else 2)


def main():
    if not os.path.exists(GOLD):
        print(f"Gold DB ausente: {GOLD}")
        return 2
    con = sqlite3.connect("file:" + GOLD + "?mode=ro", uri=True)
    resolve = process_resolver()
    explained = explained_objects()
    print("cargando clasificadores A4 (dominio) y A19 (objeto vs generado) ...")
    domain_of, a4ctx = a4_classifier()
    classify_program = reality_classifier()
    print(f"  {len(explained):,} objetos con prosa/claim en un store")

    surfaces = {}
    keep = []
    map_gaps = collections.Counter()
    tech_names = collections.Counter()

    def tally(surface, rows, kind):
        """rows: (name, execs, actors, b0,b1,b2,b3)"""
        TRACKS = ["BUSINESS", "TECHNICAL", "CROSS_CUTTING", "STRANDED", "UNCLASSIFIED"]
        acc = {t: collections.Counter() for t in TRACKS}
        accn = {t: collections.Counter() for t in TRACKS}
        generated = 0
        for name, execs, actors, *bands in rows:
            if kind == "object":
                k, _, _, _ = classify_program(name)
                if k != "OBJECT":
                    generated += execs
                    continue
            # Un TCODE no es un programa. A4 clasifica programas y trae el mapa
            # TSTC/TSTCT para resolverlo; pasarle el codigo pelado deja XK01, SU01 y
            # PFCG en "Uncatalogued" y fabrica un hueco del 35% que no existe. Tercera
            # vez en este fichero que un join roto produce una cifra creible.
            if kind == "change":
                prog = a4ctx["tc_prog"].get(name)
                dom = domain_of(name, program=prog, text=a4ctx["tc_text"].get(name))
            elif kind == "rfc":
                # Un modulo de funcion no cuelga de TADIR directamente: cuelga de su GRUPO
                # de funciones. A4 resuelve eso con el overlay TFDIR.APP_DOMAIN, y ese
                # overlay es el PRIMER peldano de domain_of -- no pasarlo deja las BAPI,
                # que son justo las llamadas de los satelites, dominando la frontera.
                dom = domain_of(name, overlay=a4ctx["fm_dom"].get(name))
            else:
                dom = domain_of(name)
            track, g = grade_item(name, execs, actors, bands, dom, resolve, explained)
            acc[track][g] += execs
            accn[track][g] += 1
            if track == "TECHNICAL":
                tech_names[dom] += execs
            if track in ("BUSINESS", "STRANDED") and g == 0:
                map_gaps[dom] += execs
            if track in ("UNCLASSIFIED", "STRANDED") or (track == "BUSINESS" and g <= 1):
                keep.append({"surface": surface, "object": name, "track": track, "grade": g,
                             "execs": execs, "actors": actors, "domain": dom,
                             "custom": name[:1] in "YZ",
                             "next": ("clasificar: no sabemos ni si es tecnico o de negocio"
                                      if track == "UNCLASSIFIED" else
                                      ("el dominio no tiene cadena de proceso en domains.json"
                                       if g == 0 else
                                       "describir: quien, cuando, por que canal"))})
        tot_e = max(1, sum(sum(c.values()) for c in acc.values()))
        surfaces[surface] = {
            "executions_graded": tot_e,
            "executions_generated_excluded": generated,
            "by_track_executions": {t: sum(c.values()) for t, c in acc.items()},
            "by_track_objects": {t: sum(c.values()) for t, c in accn.items()},
            "pct_by_track": {t: round(100 * sum(c.values()) / tot_e, 1) for t, c in acc.items()},
            "business_grades_executions": {f"{g}": acc["BUSINESS"].get(g, 0) for g in range(4)},
            "business_grades_objects": {f"{g}": accn["BUSINESS"].get(g, 0) for g in range(4)},
        }

    # ---- SUPERFICIE 1: lo que EJECUTA -------------------------------------------------
    print("1/3 objetos que ejecutan (RSAU) ...")
    tally("objects", con.execute("""
        SELECT SLGREPNA, COUNT(*), COUNT(DISTINCT SLGUSER),
               SUM(CASE WHEN CAST(SUBSTR(SAL_TIME,1,2) AS INT) <  6 THEN 1 ELSE 0 END),
               SUM(CASE WHEN CAST(SUBSTR(SAL_TIME,1,2) AS INT) BETWEEN  6 AND 11 THEN 1 ELSE 0 END),
               SUM(CASE WHEN CAST(SUBSTR(SAL_TIME,1,2) AS INT) BETWEEN 12 AND 17 THEN 1 ELSE 0 END),
               SUM(CASE WHEN CAST(SUBSTR(SAL_TIME,1,2) AS INT) >= 18 THEN 1 ELSE 0 END)
        FROM rsau_audit_history WHERE SLGREPNA != '' GROUP BY SLGREPNA"""), "object")

    # ---- SUPERFICIE 2: lo que CAMBIA --------------------------------------------------
    # La transaccion que hizo el cambio, no la clase de objeto: la clase dice QUE se toco,
    # la transaccion dice POR DONDE -- y es lo que se puede situar en un dominio.
    print("2/3 cambios (CDHDR) ...")
    try:
        tally("changes", con.execute("""
            SELECT TCODE, COUNT(*), COUNT(DISTINCT USERNAME),
                   SUM(CASE WHEN CAST(SUBSTR(UTIME,1,2) AS INT) <  6 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN CAST(SUBSTR(UTIME,1,2) AS INT) BETWEEN  6 AND 11 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN CAST(SUBSTR(UTIME,1,2) AS INT) BETWEEN 12 AND 17 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN CAST(SUBSTR(UTIME,1,2) AS INT) >= 18 THEN 1 ELSE 0 END)
            FROM cdhdr_history WHERE TCODE != '' GROUP BY TCODE"""), "change")
    except sqlite3.Error as e:
        surfaces["changes"] = {"error": str(e)[:160]}

    # ---- SUPERFICIE 3: lo que corre SOLO ----------------------------------------------
    # El programa del PASO, no el nombre del job: el nombre lo pone una persona, el programa
    # es el objeto. La variante queda registrada porque es lo que dice que hace de verdad.
    print("3/3 jobs (TBTCO x TBTCP) ...")
    try:
        tally("jobs", con.execute("""
            SELECT p.PROGNAME, COUNT(*), COUNT(DISTINCT o.AUTHCKNAM), 0, 0, 0, 0
            FROM tbtcp_history p JOIN tbtco_history o
              ON o.JOBNAME = p.JOBNAME AND o.JOBCOUNT = p.JOBCOUNT
            WHERE p.PROGNAME != '' GROUP BY p.PROGNAME"""), "job")
    except sqlite3.Error as e:
        surfaces["jobs"] = {"error": str(e)[:160]}

    # ---- SUPERFICIE 4: lo que ENTRA POR RFC ------------------------------------------
    # La mayor de las cuatro y la ultima en cablearse. El modulo de funcion NO esta en
    # SLGREPNA: ahi solo aparece SAPMSSY1, el despachador, que es tecnico -- por eso las
    # otras tres superficies veian el tubo y no lo que pasa por dentro. El nombre real
    # viaja en PARAM3 de las filas 'RFC Function Call'. Aqui vive el 80,6% del trabajo de
    # negocio de este tenant, que llega desde satelites externos y no desde una pantalla.
    print("4/4 llamadas RFC entrantes (RSAU PARAM3) ...")
    try:
        tally("rfc", con.execute("""
            SELECT PARAM3, COUNT(*), COUNT(DISTINCT SLGUSER),
                   SUM(CASE WHEN CAST(SUBSTR(SAL_TIME,1,2) AS INT) <  6 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN CAST(SUBSTR(SAL_TIME,1,2) AS INT) BETWEEN  6 AND 11 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN CAST(SUBSTR(SAL_TIME,1,2) AS INT) BETWEEN 12 AND 17 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN CAST(SUBSTR(SAL_TIME,1,2) AS INT) >= 18 THEN 1 ELSE 0 END)
            FROM rsau_audit_history
            WHERE TXSUBCLSID = 'RFC Function Call' AND PARAM3 != ''
            GROUP BY PARAM3"""), "rfc")
    except sqlite3.Error as e:
        surfaces["rfc"] = {"error": str(e)[:160]}

    keep.sort(key=lambda x: -x["execs"])
    tot_all = sum(s.get("executions_graded", 0) for s in surfaces.values())
    unclass = sum(s.get("by_track_executions", {}).get("UNCLASSIFIED", 0)
                  for s in surfaces.values())
    rep = {
        "_generated_by": "brain_v2/comprehension_index.py (A20)",
        "_question": ("todo lo que se ejecuta, se cambia y corre solo: esta identificado y "
                      "clasificado? y lo que no es tecnico, lo entendemos y sabemos su dominio?"),
        "_measured_utc": datetime.datetime.now(datetime.timezone.utc)
                         .isoformat(timespec="seconds"),
        "_tracks": {
            "TECHNICAL": ("sustrato, Basis, seguridad, transporte, runtime de terceros. "
                          "Clasificarlo como tecnico ES la respuesta: esta cerrado"),
            "BUSINESS": "todo lo demas; aqui el dominio solo no basta, hacen falta los 3 grados",
            "UNCLASSIFIED": "no sabemos ni de cual de los dos es. ESTE es el hueco real",
        },
        "headline": {
            "executions_total": tot_all,
            "unclassified_executions": unclass,
            "pct_unclassified": round(100 * unclass / max(1, tot_all), 2),
            "_note": "pct_unclassified es EL numero que debe ir a cero",
        },
        "surfaces": surfaces,
        "technical_domains_used": dict(tech_names.most_common()),
        "process_map_gaps": {
            "_what": ("dominios de NEGOCIO que A4 asigna y domains.json no ata a ninguna "
                      "cadena de proceso. No es que no se entiendan: es que el mapa no los "
                      "cubre, y sin arreglarlo sus objetos no pueden pasar de grado 0"),
            "domains": dict(map_gaps.most_common()),
        },
        "keep_exploring": keep[:200],
        "keep_exploring_total": len(keep),
        "keep_exploring_custom": sum(1 for k in keep if k["custom"]),
        "_grade_rules": {
            "1_PLACED": "dominio + cadena de proceso",
            "2_DESCRIBED": (f"forma real: <={CONCENTRATED_ACTORS} actores, o >="
                            f"{int(PEAK_SHARE*100)}% en una banda de 4h con >="
                            f"{MIN_EXECS_FOR_PROFILE} ejecuciones"),
            "3_EXPLAINED": "un store lo nombra con prosa, claim o anotacion",
        },
    }

    prev = None
    if os.path.exists(HIST):
        try:
            lines = [l for l in open(HIST, encoding="utf-8").read().splitlines() if l.strip()]
            prev = json.loads(lines[-1]) if lines else None
        except Exception:
            pass
    # Comparar dos corridas con DISTINTO conjunto de superficies no es una derivada, es una
    # ilusion: al cablear la cuarta superficie el "sin clasificar" subio de 2,66% a 5,09% --
    # no porque entendieramos menos, sino porque empezamos a ver 12,6M de ejecuciones que
    # antes no miraba nadie. Un lector futuro leeria eso como un retroceso. Asi que el
    # historico guarda QUE superficies se midieron y el movimiento solo se calcula cuando
    # coinciden; si no, se dice que el alcance cambio.
    cur_surfaces = sorted(surfaces)
    if prev and "pct_unclassified" in prev:
        if sorted(prev.get("surface_set") or []) == cur_surfaces:
            rep["movement_since_last"] = round(
                rep["headline"]["pct_unclassified"] - prev["pct_unclassified"], 2)
            rep["_movement_note"] = ("0.0 significa que el bucle de descubrimiento no se movio "
                                     "desde la ultima corrida - eso ES el hallazgo")
        else:
            rep["movement_since_last"] = None
            rep["_movement_note"] = (
                f"ALCANCE CAMBIADO: la corrida anterior midio {prev.get('surface_set')} y esta "
                f"mide {cur_surfaces}. No hay derivada comparable - un porcentaje que sube "
                f"porque se anadio una superficie no es un retroceso, es mas vision")

    json.dump(rep, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    with open(HIST, "a", encoding="utf-8") as f:
        f.write(json.dumps({"utc": rep["_measured_utc"],
                            "surface_set": cur_surfaces,
                            "pct_unclassified": rep["headline"]["pct_unclassified"],
                            "surfaces": {k: v.get("pct_by_track")
                                         for k, v in surfaces.items()}},
                           ensure_ascii=False) + "\n")

    print("\n=== INDICE DE COMPRENSION ===")
    for s, v in surfaces.items():
        if "error" in v:
            print(f"  {s:9s} ERROR {v['error']}")
            continue
        p = v["pct_by_track"]
        print(f"  {s:9s} {v['executions_graded']:>12,} ejec | "
              f"tecnico {p['TECHNICAL']:>5}% · negocio {p['BUSINESS']:>5}% · "
              f"SIN CLASIFICAR {p['UNCLASSIFIED']:>5}%")
        b = v["business_grades_executions"]
        tb = max(1, sum(b.values()))
        print(f"            negocio por grado: "
              f"g0 {100*b['0']/tb:.0f}% · g1 {100*b['1']/tb:.0f}% · "
              f"g2 {100*b['2']/tb:.0f}% · g3 {100*b['3']/tb:.0f}%")
    h = rep["headline"]
    print(f"\n  SIN CLASIFICAR: {h['pct_unclassified']}% "
          f"({h['unclassified_executions']:,} de {h['executions_total']:,})")
    if rep.get("movement_since_last") is not None:
        print(f"  movimiento desde la ultima corrida: {rep['movement_since_last']:+}")
    if map_gaps:
        print(f"  huecos del process_map: {', '.join(list(map_gaps)[:8])}")
    print(f"  seguir explorando: {len(keep):,} ({rep['keep_exploring_custom']:,} custom)")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
