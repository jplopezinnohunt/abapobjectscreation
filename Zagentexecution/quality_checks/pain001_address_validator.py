#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pain001_address_validator.py — validate a payment file BEFORE the bank does.

WHY THIS EXISTS
---------------
The CGI_XML_CT_UNESCO loop cost 7 weeks of round-trips: send file -> Treasury
uploads it to the bank portal -> error comes back days later -> guess -> resend.
Two rejections, two different defects, one holiday in between.

Both were catchable locally in under a second:
  * v1 (2026-07-02) — CdtrAgt PstlAdr had Ctry + 2x AdrLine, no structured TwnNm.
    Nov-2026 rule violation. NOT an XSD error: the file is schema-valid.
  * v2 (2026-07-21) — CdtrAgt PstlAdr emitted Ctry, StrtNm, TwnNm. Pure XSD
    xs:sequence violation; Ctry must sit second-to-last, before AdrLine.

So this runs BOTH layers, because passing one proves nothing about the other —
but they carry VERY different authority, and conflating them would make this
tool grade its own homework:

  LAYER 1  XSD  — AUTHORITATIVE, THIRD-PARTY. Runs the official ISO 20022
    schema published with the scheme. Nothing here is our opinion. Proof it is
    independent: on the v2 file it produced, offline, the bank's own wording —
      bank : "The element 'StrtNm' is not expected here ... One of the
               following elements is expected: 'AdrLine'"
      here : "Element 'StrtNm': This element is not expected.
               Expected is ( AdrLine )."
    Use this as a GATE.

  LAYER 2  BANK — NOT AUTHORITATIVE. This is OUR transcription of the banks'
    prose (SocGen brochure §3.3.5 + the guide quoted by the validator). It is a
    pre-warning so a defect is caught in a second instead of in a week — it is
    NOT a verdict, and it must never be the reason a file is declared good.
    Measured divergence proving the point: this layer flags DbtrAgt/PstlAdr as
    an error, and the bank did NOT flag it on v1 (its two errors were lines 88
    and 98 = CdtrAgt). Either our reading is stricter than the bank's actual
    enforcement, or the bank validates progressively. Unresolved — so WARN-grade
    thinking applies to every rule-(a) finding outside CdtrAgt.

For third-party confirmation of LAYER 2, use a real bank tool. The cheapest is
Citi's self-service file testing — their own deck states "No account or
connectivity set-up required to access and use the self-testing application"
(developer.citi.com). The SWIFT tool Marlies mentioned (2026-08-18) needs an
access procedure and she advised against it: "All requirements are in the
documentation". They are — but documentation transcribed by us is still us.

BANK RULES ENCODED (claim 499, verbatim sources)
------------------------------------------------
SocGen "TECHNICAL BROCHURE Cross-border Transfer pain.001.001.03" §3.3.5.1 and
the bank validator's own quoted guide (claim #329):
  (a) if <PstlAdr> is emitted at all, <TwnNm> AND <Ctry> are mandatory inside it;
  (b) pure <AdrLine>+<Ctry> is accepted only UNTIL November 2026;
  (c) hybrid: content in a structured tag must NOT be repeated in <AdrLine>;
  (d) structured format forbids <AdrLine> entirely;
  (e) unstructured whole address <= 105 chars including <Ctry>;
  (f) unstructured is already forbidden for UltmtCdtr / UltmtDbtr / InitgPty.

USAGE
    python pain001_address_validator.py <file.xml> [more.xml ...]
    python pain001_address_validator.py --after-nov2026 <file.xml>   # future mode

Exit code 0 = clean, 1 = at least one ERROR. WARN does not fail the build; it is
what becomes an ERROR in November 2026.
"""

from __future__ import annotations

import os
import sys

# ISO 20022 PostalAddress6 — the ORDER IS THE CONTRACT. Ctry is second-to-last.
# Confirmed twice over: SocGen brochure tables 7/8/9, and Citi ISOXML CREDIT V3
# GOLD format rules as consecutive Field IDs 599..608.
ISO_ORDER = ["AdrTp", "Dept", "SubDept", "StrtNm", "BldgNb", "PstCd",
             "TwnNm", "CtrySubDvsn", "Ctry", "AdrLine"]
STRUCTURED = {"Dept", "SubDept", "StrtNm", "BldgNb", "PstCd", "TwnNm",
              "CtrySubDvsn"}
# Actors for which unstructured is ALREADY forbidden (SocGen §3.3.5.1).
NO_UNSTRUCTURED = {"UltmtCdtr", "UltmtDbtr", "InitgPty"}

# FINANCIAL INSTITUTIONS ARE A DIFFERENT RULE, and missing it cost a whole day.
# A party (Dbtr/Cdtr/Ultmt*) is identified by name+address. An AGENT is identified
# by its BIC, and SocGen's own brochure says so in the CdtrAgt row:
#     BIC <BIC> [0..1] ... "BIC is recommended (IF FILLED IN, NAME AND ADDRESS
#     ARE IGNORED)"
#   -- 202601 TECHNICAL BROCH_FR_pain.001.001.03_Cross border CT.docx
# So for an agent the address is CONDITIONAL on the BIC being absent. The same
# brochure spells out the exception for RUB/Russia: "choose one option between:
# Option 1: clearing code (BIK) + BIC ... Option 2: clearing code (BIK) + name +
# address + country of the creditor agent."
#
# Why this matters in numbers (REGUH P01, 2026): on /CGI_XML_CT_UNESCO 8419 of
# 8419 payments carry a BIC -- 100%. Every CdtrAgt address on that rail is
# ignored. On /CITI/XML/UNESCO/DC_V3_01, 898 of 11185 (8%) have NO BIC, and there
# the address is the only identification the bank gets. Grading both the same way
# sends you cleaning 2229 bank master records that nobody reads, while the 898
# that actually matter stay broken.
AGENTS = {"CdtrAgt", "DbtrAgt", "IntrmyAgt1", "IntrmyAgt2", "IntrmyAgt3",
          "CdtrAgtAcct", "InstgAgt", "InstdAgt"}

XSD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "incidents", "xml_payment_structured_address",
                       "xsd_validators")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _agent_has_bic(pstl, parents):
    """Does the agent hosting this PstlAdr identify itself with a BIC?

    Looks in the same <FinInstnId> the address hangs from -- BIC and BICFI are
    the two spellings in use across pain.001 versions.
    """
    fin = parents.get(pstl)
    if fin is None or _local(fin.tag) != "FinInstnId":
        return None
    for c in fin:
        if _local(c.tag) in ("BIC", "BICFI") and (c.text or "").strip():
            return (c.text or "").strip()
    return None


def _owner(el, parents) -> str:
    """The XML party/agent that hosts this PstlAdr — for a legible message."""
    p = parents.get(el)
    while p is not None:
        n = _local(p.tag)
        if n not in ("PstlAdr", "FinInstnId"):
            return n
        p = parents.get(p)
    return "?"


def validate_xsd(path, xml_bytes):
    """LAYER 1 — schema. Catches the v2 class of defect (element order)."""
    try:
        from lxml import etree
    except ImportError:
        return [("SKIP", "lxml not installed — XSD layer skipped "
                         "(pip install lxml); bank-rule layer still ran")]
    ns = ""
    try:
        root = etree.fromstring(xml_bytes)
        ns = root.tag.split("}")[0].strip("{")
    except etree.XMLSyntaxError as exc:
        return [("ERROR", "not well-formed XML: %s" % exc)]
    ver = ns.rsplit(":", 1)[-1] if ns else "pain.001.001.03"
    xsd = os.path.join(XSD_DIR, ver + ".xsd")
    if not os.path.exists(xsd):
        return [("SKIP", "no XSD on disk for %s (looked in %s)" % (ver, XSD_DIR))]
    schema = etree.XMLSchema(etree.parse(xsd))
    if schema.validate(etree.fromstring(xml_bytes)):
        return [("OK", "XSD %s — valid" % ver)]
    out = []
    for e in schema.error_log:
        out.append(("ERROR", "XSD line %s: %s" % (e.line, e.message)))
    return out


def validate_bank_rules(xml_bytes, after_nov2026=False):
    """LAYER 2 — the dated bank rules. Catches the v1 class of defect."""
    from xml.etree import ElementTree as ET
    root = ET.fromstring(xml_bytes)
    parents = {c: p for p in root.iter() for c in p}
    findings = []
    n = 0
    for pstl in root.iter():
        if _local(pstl.tag) != "PstlAdr":
            continue
        n += 1
        who = _owner(pstl, parents)
        kids = [_local(c.tag) for c in pstl]
        present = set(kids)
        struct = present & STRUCTURED
        adrline = [c.text or "" for c in pstl if _local(c.tag) == "AdrLine"]
        tag = "%s/PstlAdr" % who
        # Agente con BIC: el banco IGNORA nombre y direccion. Los hallazgos de
        # esta direccion no son bloqueantes -- pero el fichero debe seguir siendo
        # estructuralmente valido, porque el XSD valida lo emitido lo lea el banco
        # o no (fue justo lo que tumbo el fichero del 21-07-2026).
        es_agente = who in AGENTS
        bic = _agent_has_bic(pstl, parents) if es_agente else None
        if es_agente and bic:
            findings.append(("INFO", "%s: el agente va identificado por BIC %s -- "
                                     "el banco IGNORA nombre y direccion (brochure "
                                     "SocGen, fila CdtrAgt/BIC). Emitirla es "
                                     "opcional; si se emite, debe ser valida."
                             % (tag, bic)))
        if es_agente and not bic:
            findings.append(("ERROR", "%s: agente SIN BIC -- aqui la direccion es "
                                      "la unica identificacion que recibe el banco "
                                      "y debe estar completa y estructurada" % tag))

        # order — the XSD says this too, but say it in the operator's language
        seq = [k for k in kids if k in ISO_ORDER]
        idx = [ISO_ORDER.index(k) for k in seq]
        if idx != sorted(idx):
            want = [k for k in ISO_ORDER if k in set(seq)]
            findings.append(("ERROR", "%s: children out of ISO order. got %s -> "
                                      "must be %s" % (tag, seq, want)))

        # (a) PstlAdr emitted => TwnNm + Ctry mandatory
        # An element is "legacy-shaped" when it carries NO structured tag: either
        # pure AdrLine+Ctry, or Ctry alone. Those are the shapes the grace period
        # still covers, and grading them ERROR today makes a file the bank accepts
        # look broken. Proven by the bank itself: on v1 it flagged ONLY CdtrAgt
        # (lines 88/98) and left DbtrAgt (Ctry+AdrLine) and IntrmyAgt1 (Ctry only)
        # alone -- not because they are compliant, but because Nov-2026 has not
        # arrived. They are DEADLINE debt, not defects. Run --after-nov2026 to see
        # the file the way the bank will read it from November 2026.
        legacy_shape = not struct
        # AdrLine present AND no structured tag = the format the bank calls
        # "unstructured" (the one that dies in Nov-2026). Ctry-only is legacy-shaped
        # too but is not "unstructured" — it has no AdrLine to measure or forbid.
        pure_unstructured = bool(adrline) and not struct
        for need in ("TwnNm", "Ctry"):
            if need not in present:
                if legacy_shape and not after_nov2026:
                    findings.append(("WARN", "%s: no structured <%s> — accepted "
                                             "only until Nov-2026, then rejected "
                                             "(rule b)" % (tag, need)))
                else:
                    findings.append(("ERROR", "%s: <%s> is mandatory whenever "
                                              "<PstlAdr> is emitted (rule a)"
                                     % (tag, need)))

        # (c) hybrid must not repeat structured content inside AdrLine
        if struct and adrline:
            vals = {(c.text or "").strip().upper() for c in pstl
                    if _local(c.tag) in STRUCTURED and (c.text or "").strip()}
            for line in adrline:
                u = line.strip().upper()
                for v in vals:
                    if v and v in u:
                        findings.append(("ERROR", "%s: hybrid repeats structured "
                                                  "value %r inside <AdrLine> "
                                                  "(rule c)" % (tag, v)))
            findings.append(("WARN", "%s: hybrid (structured + AdrLine). Allowed, "
                                     "but structured-only is the target (rule d)"
                             % tag))

        # (e) unstructured length budget
        if pure_unstructured:
            total = sum(len(x) for x in adrline) + len(
                "".join(c.text or "" for c in pstl if _local(c.tag) == "Ctry"))
            if total > 105:
                findings.append(("ERROR", "%s: unstructured address %d chars > 105 "
                                          "incl <Ctry> (rule e)" % (tag, total)))
            # (f) actors where unstructured is already forbidden
            if who in NO_UNSTRUCTURED:
                findings.append(("ERROR", "%s: unstructured format is forbidden for "
                                          "this actor today (rule f)" % tag))
            if after_nov2026:
                findings.append(("ERROR", "%s: unstructured is prohibited from "
                                          "Nov-2026 (rule b)" % tag))
    if not n:
        findings.append(("WARN", "no <PstlAdr> element found in the file"))
    return findings, n


def downgrade_ignored_agents(findings):
    """Un hallazgo sobre un agente que ya va identificado por BIC no es un
    bloqueo: es cosmetica. Se degrada a INFO conservando el texto, para que
    nadie lance una campana de dato maestro sobre direcciones que nadie lee."""
    ignorados = {m.split(":")[0] for lvl, m in findings
                 if lvl == "INFO" and "IGNORA nombre y direccion" in m}
    out = []
    for lvl, msg in findings:
        duenno = msg.split(":")[0]
        if duenno in ignorados and lvl in ("ERROR", "WARN") and                 "IGNORA" not in msg and "SIN BIC" not in msg:
            out.append(("IGNORA", msg + "  [no bloquea: el banco lo ignora, "
                                        "hay BIC]"))
        else:
            out.append((lvl, msg))
    return out


def run(path, after_nov2026=False):
    data = open(path, "rb").read()
    print("=" * 78)
    print(os.path.basename(path))
    print("=" * 78)
    res = validate_xsd(path, data)
    try:
        rules, n = validate_bank_rules(data, after_nov2026)
        rules = downgrade_ignored_agents(rules)
    except Exception as exc:
        rules, n = [("ERROR", "bank-rule layer failed: %s" % exc)], 0
    print("  LAYER 1 — XSD schema")
    for lvl, msg in res:
        print("    [%-5s] %s" % (lvl, msg))
    print("  LAYER 2 — bank Nov-2026 rules  (%d PstlAdr elements)" % n)
    if not [x for x in rules if x[0] != "OK"]:
        print("    [OK   ] all address rules satisfied")
    for lvl, msg in rules:
        print("    [%-5s] %s" % (lvl, msg))
    errs = sum(1 for lvl, _ in res + rules if lvl == "ERROR")
    warns = sum(1 for lvl, _ in res + rules if lvl == "WARN")
    print("  => %d error(s), %d warning(s)\n" % (errs, warns))
    return errs


def main():
    args = [a for a in sys.argv[1:] if a]
    after = "--after-nov2026" in args
    files = [a for a in args if not a.startswith("--")]
    if not files:
        print(__doc__)
        return 0
    total = sum(run(f, after) for f in files)
    print("TOTAL ERRORS:", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
