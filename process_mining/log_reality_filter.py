"""ALGORITHM A19 - THE REALITY FILTER, APPLIED TO THE LOG ITSELF.

WHAT IT ANSWERS
    Which of the 28.5M rows of security-audit log carry knowledge, and which carry noise
    that LOOKS like knowledge. A18 (reality_filter.py) asks that of business documents --
    which recorded rows never became real. This asks it one layer down, of the log we index:
    which identifiers are OBJECTS and which are GENERATED INSTANCES wearing an object's field.

WHY IT EXISTS, MEASURED 2026-08-22
    The month of July was recovered into the Gold DB and 576 program names appeared that no
    prior analysis had ever seen. Read naively that is 576 new objects. It is not:

        ~520  SAP Query generated   (!QGYAO / !QGYHR01 / AQZZSYSTGENERATE...)
          24  table browser         (/1BCDWB/DB<TABLE>)
           4  job with a date baked into its name (MSS20260706040038)
          22  real standard programs
           7  real custom programs

    So 95% of the "discovery" was phantom. Indexing those as objects inflates the corpus
    roughly twentyfold and buries the 29 names that actually mattered.

    But they are not garbage either, and deleting them would be the opposite error.
    `!QGYHR01========F_DERA15091343` is not a program -- it IS the fact that user F_DERA ran
    an ad-hoc query against HR on the 15th. That is an EXTRACTION EVENT, which is exactly the
    ungoverned data-egress channel the brain already tracks. Same string, wrong shelf.

    The same day, the actor field: 2,504 distinct users of which 126 collapse once normalised
    (L.MACEWEN = L_MACEWEN; S.LEITE = SLEITE = S_LEITE), plus 39 carrying a truncated e-mail
    or a domain prefix (A.ASSALY@UN, HQ/M_NOZAWA, A-backslash-THIBAULT). Counting actors
    without normalising over-counts them.

THE RULE THIS ENCODES
    A log field is not a class. Classify every identifier, route each class to its own shelf,
    and let the index eat only what belongs on the object shelf. Nothing is discarded --
    misfiled is not the same as worthless.

FAILURE MODE
    A generated pattern nobody taught it is classified OBJECT and quietly re-inflates the
    corpus. That is why UNKNOWN is reported as a first-class number and never folded into
    OBJECT: an unclassified remainder must stay visible, the way A6 keeps its frontier.

Run:  python process_mining/log_reality_filter.py
"""
import os, sys, re, json, sqlite3, collections, datetime

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "process_mining"))
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
OUT = os.path.join(ROOT, "brain_v2", "log_reality.json")
BRAIN = os.path.join(ROOT, "brain_v2", "brain_state.json")
# El ESTADO del delta: hasta donde se leyo y que conjuntos se llevan acumulados. Sin esto
# no hay delta posible, porque lo que se acumula son CONJUNTOS, no cifras.
ESTADO = os.path.join(ROOT, "brain_v2", "log_reality_state.json")

# --- the generated-name grammars, each with what it REALLY is and what it carries ----------
# ORDER MATTERS: most specific first. Anything unmatched stays UNKNOWN on purpose.
GRAMMARS = [
    ("SAP_QUERY",
     re.compile(r"^!QGY(?P<area>[A-Z0-9]{2,8})=*(?P<who>[A-Z0-9_.\-]+?)(?P<ts>\d{8,})=*$"),
     "extraction_event", "ad-hoc SAP Query run by a person - ungoverned data egress"),
    ("SAP_QUERY",
     re.compile(r"^AQ(ZZ|[0-9A-Z]{2})SYSTGENERATE.*$"),
     "extraction_event", "SAP Query generated report"),
    # NAMED saved query: AQ<area><QUERYNAME>. Found by the UNKNOWN remainder on A19's own
    # first run (2026-08-22) -- which is the point of keeping UNKNOWN visible. These matter
    # MORE than the ad-hoc ones: the query NAME states its target, and the ones we found sit
    # squarely on HR master data (PA_IT0008 = basic pay, PA_IT0021 = family, PA_IT0000 =
    # personnel actions, OM_* = org structure). A catalogued extraction layer over payroll
    # data is a governance fact, not a program.
    ("SAP_QUERY_NAMED",
     re.compile(r"^AQ(?P<area>[A-Z0-9]{2,8}|ZZ/SAPQUERY)/?=*(?P<qname>[A-Z0-9_/]+?)=*$"),
     "extraction_event", "named saved SAP Query - the query NAME names its target"),
    ("CLASS_POOL",
     re.compile(r"^(?P<base>[A-Z0-9_/]+?)=+CP$"),
     "class_pool", "generated class pool - the CLASS is the object, not the pool"),
    ("TABLE_BROWSER",
     re.compile(r"^/1BCDWB/DB(?P<table>[A-Z0-9_/]+)$"),
     "table_read_event", "direct table browse - the TABLE is the signal, not the program"),
    ("DATED_JOB",
     re.compile(r"^(?P<base>[A-Z_]{2,})(?P<ts>20\d{12})$"),
     "job_instance", "one run of a scheduled job; the base name is the object"),
    ("RUNTIME_GENERATED",
     re.compile(r"^(/1BCWDY/|GP[A-Z0-9]{8,}|%_|SAPLZ_TMP)"),
     "runtime_artifact", "generated by the runtime, not authored"),
]


def classify_program(p):
    """-> (klass, subtype, payload, why). klass in OBJECT | GENERATED | UNKNOWN."""
    if not p or not p.strip():
        return "UNKNOWN", None, None, "empty"
    for name, rx, event_kind, why in GRAMMARS:
        m = rx.match(p)
        if m:
            g = m.groupdict()
            payload = (g.get("table") or g.get("qname") or g.get("base")
                       or g.get("who") or None)
            return "GENERATED", name, {"event_kind": event_kind, "carries": payload,
                                       "area": g.get("area"), "ts": g.get("ts")}, why
    if re.match(r"^[A-Z_/][A-Z0-9_/]{1,39}$", p):
        return "OBJECT", ("CUSTOM" if p[0] in "YZ" else "STANDARD"), None, "repository name"
    return "UNKNOWN", None, None, "matches no known grammar"


def normalize_actor(u):
    """Collapse the spellings of one person. SAP's audit field carries the user id as typed
    by whatever front-end wrote it, so the same human arrives as L.MACEWEN and L_MACEWEN, or
    with a domain prefix, or as an e-mail truncated at the field width."""
    if not u:
        return None, "empty"
    s = u.strip().upper()
    note = []
    if "/" in s:
        s = s.split("/")[-1]
        note.append("domain_prefix")
    if "\\" in s:
        s = s.split("\\")[-1]
        note.append("backslash")
    if "@" in s:
        s = s.split("@")[0]
        note.append("truncated_email")
    if s.startswith("="):
        s = s.lstrip("=")
        note.append("leading_equals")
    key = re.sub(r"[^A-Z0-9]", "", s)
    return key, ("+".join(note) or "clean")


def main():
    # LO APRENDIDO, ANTES DE CLASIFICAR. Este minero vive justo encima de las tres memorias que
    # le aplican: SLGREPNA mezcla objetos con instancias generadas, SLGUSER trae la grafia del
    # front-end que escribio la fila (sobre-cuenta actores), y el cubo UNKNOWN es un SENSOR, no
    # un residuo -- esa ultima la aprendio A19 en su propia primera corrida. Ademas enseña las
    # preguntas abiertas del foro que esta corrida puede contestar, mientras el Gold sigue abierto.
    if _aprendido:
        _aprendido("slgrepna", "slguser", "clasific", "unknown", "actor").avisar()

    if not os.path.exists(GOLD):
        print(f"Gold DB ausente: {GOLD}")
        return 2
    c = sqlite3.connect("file:" + GOLD + "?mode=ro", uri=True)
    q = c.execute
    rep = {"_generated_by": "process_mining/log_reality_filter.py (A19)",
           "_question": "que del log es OBJETO, que es INSTANCIA GENERADA, y quien es quien",
           "_measured_utc": datetime.datetime.now(datetime.timezone.utc)
                            .isoformat(timespec="seconds"),
           "_source": "rsau_audit_history"}

    # ⛔ DELTA POR `_first_seen`. Medido el 2026-08-30: la tabla tiene 29.788.445 filas y solo
    # 356.186 (el 1,2%) llegaron desde la corrida anterior. Barrerla entera cada vez es recorrer
    # el 99% de mas para encontrar el 1,2% que cambio -- y por eso este paso producia LA MISMA
    # conclusion una y otra vez.
    #
    # Es EXACTO, no una aproximacion: lo que se calcula son CONJUNTOS DISTINTOS (que nombres de
    # programa y que usuarios aparecen), y la union de conjuntos se puede acumular sin perder
    # nada. Lo que NO se podria acumular asi es un COUNT(DISTINCT) guardado como numero -- por
    # eso se guarda el conjunto, no la cifra.
    #
    # Y la primera vez, o si el estado no existe, hace el barrido completo y lo dice.
    prev = {}
    if os.path.exists(ESTADO):
        try:
            prev = json.load(open(ESTADO, encoding="utf-8"))
        except (OSError, ValueError):
            prev = {}
    marca = prev.get("hasta_first_seen")
    total = q("SELECT COUNT(*) FROM rsau_audit_history").fetchone()[0]
    rep["rows"] = total
    if marca:
        nuevas = q("SELECT COUNT(*) FROM rsau_audit_history WHERE _first_seen > ?",
                   (marca,)).fetchone()[0]
        print(f"rsau_audit_history: {total:,} filas · DELTA desde {marca}: {nuevas:,} nuevas "
              f"({100.0*nuevas/max(1,total):.1f}%)")
        rep["_delta"] = {"desde": marca, "filas_nuevas": nuevas,
                         "_nota": "conjuntos acumulados; la union es exacta"}
    else:
        print(f"rsau_audit_history: {total:,} filas · BARRIDO COMPLETO (no hay marca previa)")
        rep["_delta"] = {"desde": None, "filas_nuevas": total, "_nota": "primera corrida"}
    _w = "" if not marca else " AND _first_seen > '%s'" % marca

    # ---- PROGRAMAS ------------------------------------------------------------------------
    print("clasificando programas ...")
    progs = sorted(set(prev.get("programas", [])) |
                   {r[0] for r in
                    q("SELECT DISTINCT SLGREPNA FROM rsau_audit_history "
                      "WHERE SLGREPNA != ''" + _w)})
    kl, sub = collections.Counter(), collections.Counter()
    carried = collections.defaultdict(set)
    objects, unknown = [], []
    for p in progs:
        k, st, pl, _ = classify_program(p)
        kl[k] += 1
        if st:
            sub[f"{k}:{st}"] += 1
        if k == "OBJECT":
            objects.append(p)
        if k == "UNKNOWN":
            unknown.append(p)
        if pl and pl.get("carries"):
            carried[st].add(pl["carries"])
    rep["programs"] = {
        "distinct": len(progs), "by_class": dict(kl), "by_subtype": dict(sub),
        "indexable_objects": len(objects),
        "inflation_factor": round(len(progs) / max(1, len(objects)), 1),
        "unknown_sample": sorted(unknown)[:40],
        "carried_signal": {k: sorted(v)[:60] for k, v in carried.items()},
        "_note": ("indexable_objects es lo unico que debe entrar al indice como OBJETO. "
                  "El resto no se tira: se re-enruta por event_kind."),
    }
    print(f"  distintos {len(progs):,} -> OBJETO {len(objects):,} | "
          f"GENERADO {kl['GENERATED']:,} | UNKNOWN {kl['UNKNOWN']:,} "
          f"(inflacion x{rep['programs']['inflation_factor']})")

    # ---- ACTORES --------------------------------------------------------------------------
    print("normalizando actores ...")
    users = sorted(set(prev.get("actores", [])) |
                   {r[0] for r in
                    q("SELECT DISTINCT SLGUSER FROM rsau_audit_history "
                      "WHERE SLGUSER != ''" + _w)})
    groups = collections.defaultdict(set)
    notes = collections.Counter()
    for u in users:
        k, n = normalize_actor(u)
        if k:
            groups[k].add(u)
            notes[n] += 1
    dup = {k: sorted(v) for k, v in groups.items() if len(v) > 1}
    rep["actors"] = {
        "distinct_raw": len(users), "distinct_normalized": len(groups),
        "overcount": len(users) - len(groups),
        "spellings_collapsed": len(dup), "by_note": dict(notes),
        "sample_collisions": dict(list(dup.items())[:25]),
    }
    print(f"  crudos {len(users):,} -> reales {len(groups):,} "
          f"(sobre-cuenta {len(users) - len(groups)})")

    # ---- DELTA CONTRA EL MODELO -----------------------------------------------------------
    # Lo que EJECUTA y el brain no explica. Solo sobre OBJETOS: preguntarselo de una
    # instancia generada fabricaria 500 huecos falsos, que es el defecto que A19 corrige.
    if os.path.exists(BRAIN):
        print("cruzando contra brain_state.objects ...")
        try:
            known = set(json.load(open(BRAIN, encoding="utf-8")).get("objects", {}).keys())
            unexplained = sorted(o for o in objects if o not in known)
            rep["delta_vs_model"] = {
                "brain_objects": len(known),
                "executing_objects": len(objects),
                "unexplained": len(unexplained),
                "coverage_pct": round(100 * (len(objects) - len(unexplained))
                                      / max(1, len(objects)), 1),
                "worklist_custom": [o for o in unexplained if o[:1] in "YZ"][:80],
                "worklist_standard": [o for o in unexplained if o[:1] not in "YZ"][:80],
                "_note": "worklist_custom primero: lo nuestro sin explicar pesa mas que lo estandar",
            }
            print(f"  ejecutan {len(objects):,} | sin explicar {len(unexplained):,} "
                  f"({rep['delta_vs_model']['coverage_pct']}% cubierto)")
        except Exception as e:
            rep["delta_vs_model"] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
            print(f"  delta no calculado: {e}")
    else:
        rep["delta_vs_model"] = {"error": "brain_state.json ausente - corre rebuild_all.py"}

    json.dump(rep, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # ⛔ EL ESTADO SE GUARDA AL FINAL, Y SOLO SI SE LLEGO AQUI. Moverlo antes -- o guardarlo con
    # un fallo a medias -- congelaria un agujero que ningun delta posterior vuelve a mirar: las
    # filas entre la marca vieja y la nueva no se leerian NUNCA MAS.
    try:
        tope = q("SELECT MAX(_first_seen) FROM rsau_audit_history").fetchone()[0]
        json.dump({"hasta_first_seen": tope,
                   "programas": progs, "actores": users,
                   "filas_al_guardar": total,
                   "_que_es": ("hasta donde leyo este paso y los CONJUNTOS acumulados. Se guardan "
                               "los conjuntos, no sus cifras: un COUNT(DISTINCT) no se puede "
                               "sumar entre corridas, un conjunto si se puede unir")},
                  open(ESTADO, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"  marca -> _first_seen <= {tope}")
    except Exception as e:                                            # noqa: BLE001
        print(f"  AVISO: no se pudo guardar la marca ({type(e).__name__}): la proxima corrida "
              f"hara barrido completo, que es lo correcto si no se sabe hasta donde se leyo")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
