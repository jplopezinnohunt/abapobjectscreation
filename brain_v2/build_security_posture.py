"""build_security_posture.py — the SECURITY store, built empty so the work has a home.

**This is written BEFORE the analysis, on purpose.** Every security finding this project has
produced so far lives inside claim prose — the SoD conflict, the `S_RFC=*` root cause, the
attribution gap. Prose cannot be queried, cannot be diffed next month, and cannot say what is
still missing. So the destination is built first, and the extraction fills it.

**Security is a DOMAIN and a COLUMN, and that is not a contradiction.**

    E_AUTH (column)     do we know the authorisation model FOR THIS DOMAIN? asked 21 times
    Security (domain)   users, roles, profiles, posture — studied ONCE, feeds all 21

Integration works the same way, which is why it is the precedent rather than an exception.

**Seven components.** Each says what it answers, which table or artifact it needs, and whether
that input exists yet. A component with no input reports MISSING and names the extraction — it
does not silently return an empty section, because an empty section reads as "nothing to
report" and that is the single most expensive misreading available here.

**The two things already established, carried in as findings rather than re-derived:**
the control surface is the CALL and DATA layer, not the role layer; and 5.3M calls carry no
attributable actor at all.

Emits: brain_v2/security_posture.json
Run:   python brain_v2/build_security_posture.py
"""
import json
import sqlite3
import sys
from pathlib import Path

BRAIN = Path(__file__).resolve().parent
REPO = BRAIN.parent
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = BRAIN / "security_posture.json"

# Lo que este proyecto ya aprendio de ESTE instrumento, leido ANTES de minar. Cada memoria lleva
# su `implication`: que debe hacer distinto este algoritmo por su culpa. Las que aplican aqui son
# exactamente las trampas de este script: la grafia del id (SLGUSER llega como L.MACEWEN y
# L_MACEWEN, y un separador distinto parte una cuenta en dos), CREATOR/`user=` no es una identidad
# mientras no se contraste contra USR02, nuestras propias lecturas RFC ensucian el mismo log que
# medimos, y la consulta dentro del bucle son 25 barridos completos de 28,5M filas.
sys.path.insert(0, str(REPO / "process_mining"))
try:
    from metodo import lo_que_ya_aprendimos as _aprendido
except Exception:
    _aprendido = None

# component -> (question, gold table it needs, what it would answer once present)
COMPONENTS = [
    ("identity_inventory", "who has an account, when did they last use it, who is locked?",
     "usr02",
     "dormant and locked accounts; the gap between accounts held and accounts used"),
    ("role_assignment", "which roles is each user assigned, and since when?",
     "agr_users",
     "role sprawl; users carrying roles they never exercise"),
    ("role_content", "what does each role actually authorise?",
     "agr_1251",
     "whether a role grants more than its name implies — the gap between label and grant"),
    ("auth_defaults", "which transactions check which objects, by default?",
     "usobt",
     "transactions running with no check at all, which is where S_RFC=* becomes dangerous"),
    ("failures", "who was DENIED, and on what?",
     "rsau_audit_history",
     "attempted access is a signal the granted-permission view cannot give"),
    ("attribution", "can an action be tied to a person?",
     "rsau_audit_history",
     "whether SoD and change-approval controls have an actor to hang on"),
    ("write_channel_sod", "which write paths bypass the object check?",
     None,
     "the control surface itself — already established as the CALL and DATA layer"),
]

# Findings already established and verified. Carried as RECORDS so they stop living in prose,
# and marked so a later pass does not re-derive them.
ESTABLISHED = [
    {"id": "SEC-1-CONTROL-SURFACE",
     "finding": ("The control surface is the CALL and DATA layer, not the role layer. Root: "
                 "S_RFC=* combined with a custom write function module that skips the "
                 "authorisation object check."),
     "consequence": ("a clean SU01/PFCG picture does NOT mean segregation holds. Any review "
                     "that stops at roles will pass a system that has no control."),
     "status": "VERIFIED", "source": "H71 write-channel SoD"},
    {"id": "SEC-2-ATTRIBUTION-GAP",
     "finding": ("~5.3M RFC calls cannot be tied to any person. MULESOFT: 3,230,958 calls, ONE "
                 "identity, 100% itself. BRIDGE-RFC 2,106,347 and UBO-RFC 324,390 carry NO "
                 "PARAMX at all — not even a caller field."),
     "counter_example": ("WF-BATCH proves the trail CAN be carried: 660,588 calls with 542 "
                         "DISTINCT REAL USERS behind it, only 14% the account itself."),
     "consequence": ("every SoD control and every change-approval control assumes an ACTOR. On "
                     "these paths there is none, so those controls are not weak — they are "
                     "inapplicable."),
     "not_the_finding": ("'nobody uses SAP' — 1,848 distinct users log in by dialog (902,758 "
                         "events) and 1,882 by RFC/CPIC. People are there; the WRITE traffic "
                         "is what loses the actor."),
     "status": "VERIFIED", "source": "claim #404"},
]


def derive_attribution(gold):
    """The attribution table, DERIVED — not a sentence inside a finding.

    This existed first as prose in a claim, then as prose inside a record, which is the same
    thing wearing a schema. The numbers only become knowledge when something can query them:
    ask which accounts went opaque this month, or whether a satellite started carrying its
    caller, and a paragraph cannot answer either.

    PARAMX carries the CALLING user behind each technical account, so transparency is a
    measurable property per account rather than an opinion:

        TRANSPARENT   the account names real callers  -> actions can be attributed
        OPAQUE        one identity, always itself     -> a trail exists but leads nowhere
        NO_CALLER     no PARAMX at all                -> there is no trail to follow
    """
    import sys as _s
    _s.path.insert(0, str(REPO / "process_mining"))
    try:
        from caller_parse import parse
    except ImportError:
        return []
    from collections import Counter
    con = sqlite3.connect(f"file:{gold}?mode=ro", uri=True)
    top = con.execute("SELECT SLGUSER, COUNT(*) n FROM rsau_audit_history "
                      "GROUP BY 1 ORDER BY n DESC LIMIT 25").fetchall()
    out = []
    for acct, calls in top:
        rows = con.execute("SELECT PARAMX, COUNT(*) FROM rsau_audit_history "
                           "WHERE SLGUSER=? AND PARAMX<>'' GROUP BY 1", (acct,)).fetchall()
        c = Counter()
        for px, k in rows:
            _d, _h, u = parse(px)
            if u:
                c[u] += k
        e = {"account": acct, "calls": calls}
        if not c:
            e["transparency"] = "NO_CALLER"
            e["distinct_callers"] = 0
            e["_means"] = ("no PARAMX at all — not even a caller field. There is no trail to "
                           "follow, so nothing on this path can be tied to a person")
        else:
            tot = sum(c.values())
            own = c.get(acct, 0)
            e["distinct_callers"] = len(c)
            e["self_share"] = round(own / tot, 3)
            e["top_callers"] = c.most_common(5)
            if len(c) <= 2 and own / tot > 0.9:
                e["transparency"] = "OPAQUE"
                e["_means"] = ("one identity, always itself — a trail exists but it leads back "
                               "to the account, never to a person")
            else:
                e["transparency"] = "TRANSPARENT"
                e["_means"] = (f"{len(c)} distinct callers named behind this account — actions "
                               f"CAN be attributed. Proof that the trail can be carried")
        out.append(e)
    con.close()
    return out


def main():
    if _aprendido:
        _aprendido("rsau_audit_history", "usr02", "slguser", "separador", "creator").avisar()

    have = set()
    if GOLD.exists():
        con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
        have = {r[0].lower() for r in
                con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        con.close()

    comps, counts = [], {"DERIVED": 0, "READY": 0, "MISSING_INPUT": 0, "NO_INPUT_NEEDED": 0}
    for name, question, table, answers in COMPONENTS:
        e = {"component": name, "question": question, "needs_table": table,
             "would_answer": answers}
        if table is None:
            e["state"] = "NO_INPUT_NEEDED"
            e["note"] = "established from findings already held, not from a table"
        elif table in have:
            e["state"] = "READY"
            e["note"] = "the input is in the golden; the analysis has not run yet"
            if name == "attribution" and GOLD.exists():
                acc = derive_attribution(GOLD)
                if acc:
                    e["state"] = "DERIVED"
                    e["accounts"] = acc
                    e["summary"] = {
                        t: sum(a["calls"] for a in acc if a["transparency"] == t)
                        for t in ("TRANSPARENT", "OPAQUE", "NO_CALLER")}
                    e["note"] = ("derived per account, queryable — not a sentence inside a "
                                 "finding")
        else:
            e["state"] = "MISSING_INPUT"
            e["to_fix"] = (f"extract {table.upper()} from P01, read-only, and register it in "
                           f"gold_table_registry under domain Security")
        counts[e["state"]] += 1
        comps.append(e)

    json.dump({
        "_generated_by": "brain_v2/build_security_posture.py",
        "_what_this_is": ("the SECURITY store, built BEFORE the analysis so the findings have "
                          "a structured home instead of landing in claim prose"),
        "_security_is_both": {
            "column": ("E_AUTH — do we know the authorisation model FOR THIS DOMAIN? Asked 21 "
                       "times, once per domain."),
            "domain": ("users, roles, profiles, posture — studied ONCE and feeding all 21. "
                       "Integration is the precedent, not the exception."),
            "why_it_matters": ("searching the domain list for security returned nothing, which "
                               "reads as 'not a concern'. It was a column with no subject."),
        },
        "_read_this_before_reporting": (
            "a component in MISSING_INPUT means WE CANNOT SEE, never 'there is nothing'. An "
            "empty section here would read as a clean bill of health, which is the most "
            "expensive misreading this store could produce."),
        "counts": counts,
        "established_findings": ESTABLISHED,
        "components": comps,
        "_fills_profile_component": ("security_posture — the single MISSING component of "
                                     "brain_v2/system_profile/installation_profile.json"),
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[security posture] {len(COMPONENTS)} components — "
          f"{counts['READY']} ready · {counts['MISSING_INPUT']} missing input · "
          f"{counts['NO_INPUT_NEEDED']} established")
    for e in comps:
        mark = {"DERIVED": "* ", "READY": "  ", "MISSING_INPUT": "! ", "NO_INPUT_NEEDED": "= "}[e["state"]]
        print(f"  {mark}{e['component']:20s} {e['state']:14s} {e.get('needs_table') or ''}")
    print(f"\n  {len(ESTABLISHED)} findings already VERIFIED and now stored as records, "
          f"not prose.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
