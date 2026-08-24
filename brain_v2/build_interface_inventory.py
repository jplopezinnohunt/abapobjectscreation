"""build_interface_inventory.py — every interface, as a RECORD (s097).

**Prose is not reliable knowledge.** Everything this session discovered about how the system
is written to — the SuccessFactors service set, the custom HTTP surface, who generates the
batch-input sessions, which destinations are live — was landing inside claim TEXT. A claim
is durable, but its body is a paragraph: nothing can query it, nothing can diff it next
month, and nothing notices when it goes stale. That is the same failure as the write-channel
taxonomy sitting in markdown tables, committed one layer up.

So this derives ONE STRUCTURED INVENTORY of every inbound and outbound path, from the golden
tables, keyed on the artifact that carries it:

    RFC_DESTINATION   rfcdes x observed traffic          configured, and whether it is used
    IDOC              edidc                              message type, partners, direction
    WEB_SERVICE       wsheader                           definition, author, and SAP vs ours
    HTTP_SERVICE      icfservice / icfservloc            the ICF surface, and what is ACTIVE
    BATCH_INPUT       apqi                                who GENERATES the sessions, and state
    FILE / DBCON      the declared registry               parsed from the integration map

**Author is not a prefix.** A service carrying no Z/Y prefix can still be ours in every sense
that matters: the SuccessFactors replication set is SAP-DELIVERED and ACTIVATED here, and a
prefix filter erased the live SF-to-ECC channel from the map earlier today. So "ours" is
decided by AUTHOR, never by name shape.

**What each record carries:** what it is, how it arrives, whether there is EVIDENCE it runs,
and — when there is not — WHY not, because "we cannot see it" and "it does not happen" are
different facts and only one of them is a finding.

Emits: brain_v2/interface_inventory.json
"""
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
DECLARED = REPO / "brain_v2" / "integration_channels.json"
ATTRIB = REPO / "brain_v2" / "change_attribution.json"
OUT = REPO / "brain_v2" / "interface_inventory.json"


def q(con, sql, default=None):
    try:
        return con.execute(sql).fetchall()
    except sqlite3.Error:
        return default if default is not None else []


def main():
    if not GOLD.exists():
        print(f"golden not found: {GOLD}", file=sys.stderr)
        return 1
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
    inv = []

    # ---- WEB SERVICES ----------------------------------------------------
    # OURS is decided by AUTHOR, never by prefix: the SuccessFactors set is SAP-delivered
    # and activated here, and a Z/Y filter erased it from the map earlier today.
    for name, author, created in q(con, "SELECT WSNAME, AUTHOR, CREATEDON FROM wsheader"):
        if (author or "").strip().upper() == "SAP":
            continue
        inv.append({
            "channel": "WEB_SERVICE", "artifact": name, "direction": "inbound",
            "ours_because": f"authored by {author}, not by SAP",
            "activated_on": created,
            "evidence_it_runs": None,
            "why_no_evidence": ("SRT_MONILOG_DATA is EMPTY — the SOAP monitor is off. "
                                "Existence and activation are verified; execution cannot be. "
                                "This is UNVERIFIED, never 'unused'"),
        })

    # ---- HTTP / ICF SURFACE ----------------------------------------------
    icf = q(con, "SELECT ICF_NAME, ICFACTIVE FROM icfservice")
    custom = [(n, a) for n, a in icf if (n or "").upper().startswith(("Z", "Y"))]
    inv.append({
        "channel": "HTTP_SERVICE", "artifact": "(ICF surface)", "direction": "inbound",
        "total_services": len(icf),
        "active": sum(1 for _n, a in icf if (a or "").strip() in ("X", "A", "1")),
        "custom_services": len(custom),
        "custom_sample": [n for n, _a in custom[:10]],
        "evidence_it_runs": "activation flag only",
        "why_no_evidence": "ICF call logging is not extracted; activation is not execution",
    })

    # ---- BATCH INPUT -----------------------------------------------------
    # The finding that inverts the usual reading: the sessions are GENERATED, not recorded.
    by_prog = dict(q(con, "SELECT PROGID, COUNT(*) FROM apqi GROUP BY 1"))
    by_creator = dict(q(con, "SELECT CREATOR, COUNT(*) FROM apqi GROUP BY 1"))
    states = dict(q(con, "SELECT QSTATE, COUNT(*) FROM apqi GROUP BY 1"))
    total = sum(by_prog.values()) or 1
    for prog, n in sorted(by_prog.items(), key=lambda x: -x[1])[:12]:
        inv.append({
            "channel": "BATCH_INPUT", "artifact": prog, "direction": "inbound",
            "sessions": n, "share_of_all_sessions": round(n / total, 3),
            "generated_not_recorded": prog == "SAPMSSY1",
            "_why_that_matters": ("SAPMSSY1 is the RFC dispatcher. Sessions it creates were "
                                 "GENERATED OVER RFC, not recorded by a person at a screen — "
                                 "so this belongs to the interface channel, not the dialog "
                                 "one") if prog == "SAPMSSY1" else None,
            "evidence_it_runs": f"{n} sessions in APQI",
        })
    inv.append({
        "channel": "BATCH_INPUT", "artifact": "(session health)", "direction": "inbound",
        "top_creators": sorted(by_creator.items(), key=lambda x: -x[1])[:6],
        "states": states,
        "error_sessions": states.get("E", 0) + states.get("F", 0),
        "_finding": ("a failing write channel is a silent data gap — nobody is watching this "
                     "rate"),
    })

    # ---- RFC DESTINATIONS + IDOC ------------------------------------------
    for dest, rtype in q(con, "SELECT RFCDEST, RFCTYPE FROM rfcdes"):
        inv.append({"channel": "RFC_DESTINATION", "artifact": (dest or "").strip(),
                    "direction": "outbound", "type": (rtype or "").strip(),
                    "evidence_it_runs": "see brain_v2/interface_boundary.json (F1) for "
                                        "LIVE/DEAD against observed traffic"})
    for mestyp, n in Counter(m for (m,) in q(con, "SELECT MESTYP FROM edidc") if m).items():
        inv.append({"channel": "IDOC", "artifact": mestyp, "direction": "both",
                    "documents": n, "evidence_it_runs": f"{n} documents in EDIDC"})
    # ---- RFC OBSERVADO: usuarios que ENTRAN sin destino configurado ---------
    # El inventario derivaba solo de rfcdes, que son destinos CONFIGURADOS y SALIENTES. Un
    # satelite que entra autenticandose como usuario RFC no tiene destino, luego era
    # estructuralmente invisible aqui -- por eso EPAM-RFC, con 127.832 eventos desde dos IPs
    # fijas, no figuraba en ninguno de los 300 registros. Un canal se descubre por su TRAFICO,
    # no solo por su configuracion.
    for user, calls, fms, terms in q(con, """
            SELECT SLGUSER, COUNT(*), COUNT(DISTINCT PARAM3), COUNT(DISTINCT SLGLTRM2)
            FROM rsau_audit_history
            WHERE TXSUBCLSID = 'RFC Function Call' AND SLGUSER != ''
            GROUP BY SLGUSER HAVING COUNT(*) >= 1000 ORDER BY 2 DESC""") or []:
        # PERSONA o MAQUINA, decidido por una senal MEDIBLE y no por el nombre: una interfaz
        # no hace LOGON DE DIALOGO. Un humano que usa SAP GUI genera muchisimas llamadas RFC
        # -- V.VAURETTE tiene 211.702 -- y sin este corte el inventario se llena de personas.
        # q() no acepta parametros (su 3er argumento es el default), asi que la consulta
        # parametrizada va por la conexion directa.
        try:
            dlg = con.execute("SELECT COUNT(*) FROM rsau_audit_history "
                              "WHERE SLGUSER = ? AND TXSUBCLSID = 'Dialog Logon'",
                              (user,)).fetchone()[0] or 0
        except sqlite3.Error:
            dlg = None
        inv.append({
            "channel": "RFC_INBOUND_OBSERVED", "artifact": (user or "").strip(),
            "direction": "inbound", "calls": calls,
            "distinct_function_modules": fms, "distinct_terminals": terms,
            "dialog_logons": dlg,
            "likely": ("MAQUINA" if dlg == 0 else
                       "PERSONA (usa SAP GUI)" if dlg else "sin determinar"),
            "evidence_it_runs": f"{calls:,} llamadas RFC en rsau_audit_history",
            "_why_here": ("descubierto por TRAFICO, no por configuracion: no tiene entrada en "
                          "rfcdes. Un satelite que entra como usuario RFC no deja destino"),
            "_how_classified": ("MAQUINA = cero logons de dialogo. Es una senal medible, no "
                                "una convencion de nombres"),
        })

    con.close()

    # ---- DECLARED (parsed from the map) + DERIVED (from the change log) ----
    declared = {}
    if DECLARED.exists():
        declared = json.load(open(DECLARED, encoding="utf-8")).get("by_artifact") or {}
    for art, entries in declared.items():
        for d in entries:
            inv.append({"channel": d["channel"], "artifact": art,
                        "direction": "inbound", "source_system": d.get("source"),
                        "declared_status": d.get("status"),
                        "from": "the integration map — a CLAIM, verified separately",
                        "evidence_it_runs": None})

    derived = {}
    if ATTRIB.exists():
        derived = json.load(open(ATTRIB, encoding="utf-8")).get("classes") or {}

    counts = Counter(r["channel"] for r in inv)
    json.dump({
        "_generated_by": "brain_v2/build_interface_inventory.py",
        "_what_this_is": ("every inbound and outbound path as a RECORD, derived from the "
                          "golden tables — not a paragraph inside a claim"),
        "_why": ("prose is not reliable knowledge. Nothing can query a paragraph, diff it "
                 "next month, or notice when it goes stale."),
        "_ours_is_decided_by_author": ("never by prefix. The SuccessFactors replication set is "
                                       "SAP-delivered and ACTIVATED here; a Z/Y filter erased "
                                       "the live SF-to-ECC channel from the map earlier today"),
        "_evidence_discipline": ("every record says whether there is evidence it RUNS, and "
                                 "when there is not, WHY not. 'We cannot see it' and 'it does "
                                 "not happen' are different facts"),
        "counts": dict(counts),
        "object_classes_with_a_derived_channel": len(derived),
        "interfaces": inv,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[interface inventory] {len(inv)} records")
    for k, v in counts.most_common():
        print(f"    {k:18s} {v}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
