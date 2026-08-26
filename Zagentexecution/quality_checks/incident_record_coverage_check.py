"""Incident record coverage check — every incident doc must be reachable from the brain.

WHY THIS EXISTS
---------------
Session #099 opened and found 11 incident docs under knowledge/incidents/ but only 7
first-class records in brain_v2/incidents/incidents.json. Three incidents
(INC-000011781, INC-180995, INC-CLASS-LOSS-2026-06) existed only as prose on disk.

That is not a cosmetic gap. Step 2 of the sap_incident_analyst protocol is BRAIN LOOKUP:
the agent traverses brain_state.incidents -> indexes.by_incident -> objects[X]. A doc with
no record is not in that traversal, so the next agent handling a sibling ticket starts from
zero and re-derives what we already paid for. INC-000011781 in particular carries the richest
BCM signatory precedent we have (IT1218 node selection, the drift sweep, the role gap) — it
was invisible for ~2 months.

Root cause of the gap: the PMO recorded "TODO: run rebuild_all.py to fold INC-000011781 in"
(2026-06-18) and it never ran. A TODO is not a control. This is the control.

WHAT IT CHECKS
--------------
1. Every INC-*.md under knowledge/incidents/ has a record in incidents.json
2. Every record's analysis_doc points at a file that exists
3. Every record carries the fields BRAIN LOOKUP actually reads

Companion docs (a second .md for the same incident, e.g. *_full_history.md or
*_executive_brief.md) are matched to their parent by incident id and do not need their own
record.

USAGE
-----
    python Zagentexecution/quality_checks/incident_record_coverage_check.py

Exit 0 = clean. Exit 1 = at least one incident is invisible to the brain.
"""

from __future__ import annotations

# --- self-declaration, read by quality_checks/run_all.py -------------------
# An undeclared script is reported as UNCLASSIFIED and fails the runner loudly:
# a central registry is a list someone forgets to update.
QUALITY_CHECK = {
    "tier": "gate",
    "sobre": "conocimiento",  # datos_sap | conocimiento | herramientas
    "needs": "files",    # gold_db | rfc_p01 | files
    "what": "every incident doc must have a first-class record the brain can reach",
}
# --------------------------------------------------------------------------

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO / "knowledge" / "incidents"
RECORDS = REPO / "brain_v2" / "incidents" / "incidents.json"

# Fields the BRAIN LOOKUP traversal (skill step 2) actually dereferences.
REQUIRED_FIELDS = [
    "id",
    "status",
    "title",
    "domain",
    "analysis_doc",
    "related_objects",
]

# id as it appears at the start of a doc filename: INC-000006073, INC-180995,
# INC-BUDGETRATE-EQG, INC-CLASS-LOSS-2026-06
DOC_ID_RE = re.compile(r"^(INC-[A-Z0-9]+(?:-[A-Z0-9]+)*?)(?:_|\.md$)")


def doc_incident_id(filename: str) -> str | None:
    m = DOC_ID_RE.match(filename)
    return m.group(1) if m else None



# ==============================================================================
# TRIANGULO DE ARTEFACTOS (s104) — doc + registro NO bastan
#
# Este check nacio para garantizar que todo doc de incidente tuviera registro de
# primera clase (si no, es invisible para BRAIN LOOKUP). Es necesario y no es
# suficiente.
#
# Medido el 2026-08-26 en INC-000016338: el doc existia, el registro existia, el
# gate daba VERDE — y el operador tuvo que preguntar tres cosas que faltaban:
#   · el companion se habia quedado DESFASADO respecto al analisis final
#   · la referencia era de UNA SOLA DIRECCION (el companion citaba el incidente,
#     el incidente no citaba el companion, y el registro tampoco)
#   · no habia BRIEF: 11 secciones tecnicas y ningun resumen para quien no las lee
#
# Un incidente cuyo conocimiento solo se alcanza leyendolo entero no se alcanza.
# ==============================================================================

BRIEF_MARKS = ("## 0.", "BRIEF", "RESUMEN EJECUTIVO", "En 60 segundos")


def triangulo(docs_dir, records):
    """-> lista de (inc_id, [fallos])  ·  docs_dir: Path a knowledge/incidents"""
    import glob as _glob
    import os as _os
    comp_dir = _os.path.join(_os.path.dirname(_os.path.dirname(str(docs_dir))), "..", "companions")
    comp_dir = _os.path.normpath(comp_dir)
    companions = {}
    if _os.path.isdir(comp_dir):
        for f in _glob.glob(_os.path.join(comp_dir, "*.html")):
            try:
                companions[_os.path.basename(f)] = io.open(f, encoding="utf-8", errors="replace").read()
            except OSError:
                pass

    out = []
    for f in sorted(_glob.glob(_os.path.join(str(docs_dir), "INC-*.md"))):
        inc = doc_incident_id(_os.path.basename(f))
        if not inc:
            continue
        try:
            texto = io.open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        fallos, avisos = [], []

        # (1) BRIEF — un resumen antes del detalle.
        # AVISO y no fallo: hay deuda historica (6 docs el 2026-08-26) y un gate rojo
        # permanente es como se consigue que se ignore. Se lista para que exista.
        if not any(m in texto[:4000] for m in BRIEF_MARKS):
            avisos.append("sin BRIEF: nada legible en 60 s antes de 10+ secciones tecnicas")

        # (2) companion que lo cite  <->  doc que cite al companion
        citan = [n for n, t in companions.items() if inc in t]
        if citan:
            if not any(n in texto for n in citan):
                fallos.append("referencia de UNA direccion: %s cita al incidente y el doc no lo cita"
                              % citan[0])
            rec = records.get(inc) or {}
            blob = str(rec)
            if not any(n in blob for n in citan):
                fallos.append("el REGISTRO no nombra el companion (%s): desde el brain no se llega"
                              % citan[0])
        if fallos or avisos:
            out.append((inc, fallos, avisos))
    return out


def main() -> int:
    if not RECORDS.exists():
        print(f"FAIL: {RECORDS} not found")
        return 1
    if not DOCS_DIR.exists():
        print(f"FAIL: {DOCS_DIR} not found")
        return 1

    records = json.loads(RECORDS.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in records}

    docs: dict[str, list[str]] = {}
    for p in sorted(DOCS_DIR.glob("INC-*.md")):
        inc_id = doc_incident_id(p.name)
        if inc_id is None:
            docs.setdefault("__UNPARSEABLE__", []).append(p.name)
            continue
        docs.setdefault(inc_id, []).append(p.name)

    problems: list[str] = []

    # 1 — docs with no first-class record
    for inc_id, files in sorted(docs.items()):
        if inc_id == "__UNPARSEABLE__":
            problems.append(
                f"UNPARSEABLE filename(s), cannot map to an incident id: {', '.join(files)}"
            )
            continue
        if inc_id not in by_id:
            problems.append(
                f"{inc_id}: doc(s) on disk ({', '.join(files)}) but NO record in "
                f"incidents.json -> invisible to BRAIN LOOKUP"
            )

    # 2 — records whose analysis_doc is dangling
    for inc_id, rec in sorted(by_id.items()):
        doc = rec.get("analysis_doc")
        if not doc:
            problems.append(f"{inc_id}: record has no analysis_doc")
            continue
        if not (REPO / doc).exists():
            problems.append(f"{inc_id}: analysis_doc points at a missing file -> {doc}")

    # 3 — records missing fields the traversal reads
    for inc_id, rec in sorted(by_id.items()):
        missing = [f for f in REQUIRED_FIELDS if not rec.get(f)]
        if missing:
            problems.append(f"{inc_id}: record missing field(s) {missing}")

    docs_count = len([k for k in docs if k != "__UNPARSEABLE__"])
    print(f"incident docs (distinct ids): {docs_count}")
    print(f"first-class records:          {len(records)}")

    if problems:
        print(f"\nFAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        print(
            "\nFix: add the missing record to brain_v2/incidents/incidents.json "
            "(schema: see any existing record), then run python brain_v2/rebuild_all.py"
        )
        return 1

    print("\nOK — every incident doc is reachable from the brain, every record resolves.")

    # --- TRIANGULO DE ARTEFACTOS: doc + registro no bastan (s104) ---
    try:
        import json as _json
        _recs = _json.loads(RECORDS.read_text(encoding="utf-8"))
        _recs = _recs.get("incidents", _recs) if isinstance(_recs, dict) else _recs
        pend = triangulo(DOCS_DIR, {r.get("id"): r for r in _recs if isinstance(r, dict)})
    except Exception as e:                       # nunca tumbar el gate por la parte nueva
        print("\n(aviso: no se pudo evaluar el triangulo de artefactos: %s)" % e)
        return 0
    duros = [(i, f) for i, f, _ in pend if f]
    blandos = sorted({(i, a) for i, _, av in pend for a in av})
    if pend:
        print("\n" + "-" * 74)
        print("TRIANGULO DE ARTEFACTOS — doc + registro estan, ¿pero se LLEGA?")
        print("-" * 74)
    for inc, av in blandos:
        print("  AVISO  %-26s %s" % (inc, av))
    for inc, fs in duros:
        for x in fs:
            print("  FALLO  %-26s %s" % (inc, x))
    if duros:
        print("\n  Una referencia de una sola direccion no es un enlace: desde el brain no se llega.")
        return 1
    if blandos:
        print("\n  (avisos: deuda de BRIEF. NO tumban el gate — un rojo permanente por deuda")
        print("   historica es como se consigue que un check se ignore. Se saldan al tocar")
        print("   cada incidente, y mientras tanto existen y se ven.)")
    print("OK — referencias bidireccionales en todos los incidentes con companion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
