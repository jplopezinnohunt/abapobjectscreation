#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dmee_tree_map.py -- the map of EVERY live DMEE tree: structure + mapping + EXITS.

WHY THIS EXISTS
---------------
Session 2026-08-18/19: I handed over a change spec for the CGI CdtrAgt address
built on the node MAPPING alone, and the user stopped me twice on the same
thing -- "estan los codigos de las extensiones para cada elemento, y eso
deberias conocerlo para todos". Both times he was right, and the second time
the miss was bigger than the first:

  1. I read ONE exit column. Six things decide a node's content -- MP_IF_TP,
     MP_SC_TAB/FLD, MP_CONST, MP_EXIT_FUNC, CK_EXIT_FUNC, CV_RULE. A node can
     carry a mapping AND an exit (screenshot: CdtrAgt/BIC has FPAYH-ZSWIF *and*
     FI_CGI_DMEE_EXIT_W_BADI). The exit wins. Reading the mapping alone tells
     you what SAP would do if nobody had overridden it. In /CGI_XML_CT_UNESCO
     that is 392 of 628 nodes -- 62% of the tree was invisible to me.
  2. I analysed 3 trees. REGUT says SIX formats are live in 2026. The Italian
     ICTP family -- including /SEPA_CT_ICTP_ISO_EXTRASEPA, the cross-border one
     and therefore the one Nov-2026 hits hardest -- was never looked at.

The lesson is not "check the exits". It is that a per-question hand probe
re-derives a partial picture every time and silently omits whatever the
question did not ask about. So this is a MAP, not an answer: it walks every
live tree end to end and prints what is there, whether or not anyone asked.

WHAT IT REPORTS
---------------
  * which formats are actually live      (REGUT.DTFOR, measured -- not assumed)
  * every PstlAdr subtree in each        (child order = XML order)
  * per node: mapping, constant, MP exit, CK exit, conversion rule, conditions
  * every exit function the tree uses, and where -- ours vs delivered
  * three defect classes, flagged:
      ORDER   children violate the ISO 20022 PostalAddress6 xs:sequence
      HYBRID  structured tag and AdrLine in the same PstlAdr
      NOV26   no structured TwnNm/Ctry -- legal today, rejected from Nov-2026
      TECNICO     un hijo con nombre de etiqueta ISO es NODE_TYPE=TECH y por tanto
                  NO emite etiqueta XML: borra el dato en silencio
      SIN-ORIGEN  hijos sin constante, sin mapping y sin fila PPC que respalde su
                  exit. SOSPECHA, no veredicto: el BAdI tiene una segunda fuente
                  (YCL_IDFI_CGI_DMEE_FALLBACK, ABAP) que no se lee de tablas.
                  Confirmar siempre contra un fichero generado.

USAGE
    python dmee_tree_map.py                  # D01 trees, live formats from P01
    python dmee_tree_map.py --sys P01
    python dmee_tree_map.py --tree /SEPA_CT_ICTP_ISO_EXTRASEPA
    python dmee_tree_map.py --all-trees      # do not filter to live formats
    python dmee_tree_map.py --json out.json

Read-only. Two RFC_READ_TABLE reads per system, no ROWSKIPS (P01 rejects it).
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "mcp-backend-server-python"))

# ISO 20022 PostalAddress6 is an xs:sequence -- this order IS the contract.
# Ctry is second-to-last. Emitting it first is the 2026-07-21 bank rejection.
ISO_ORDER = ["AdrTp", "Dept", "SubDept", "StrtNm", "BldgNb", "PstCd",
             "TwnNm", "CtrySubDvsn", "Ctry", "AdrLine"]
STRUCTURED = {"Dept", "SubDept", "StrtNm", "BldgNb", "PstCd", "TwnNm",
              "CtrySubDvsn"}

NODE_F = ["TREE_ID", "VERSION", "NODE_ID", "TECH_NAME", "REF_NAME", "PARENT_ID",
          "FIRSTCHILD_ID", "BROTHER_ID", "NODE_TYPE", "MP_IF_TP", "MP_SC_TAB",
          "MP_SC_FLD", "MP_SC_NODE", "MP_CONST", "CV_RULE", "MP_EXIT_FUNC",
          "CK_EXIT_FUNC", "MP_SELECTION", "LEV"]
COND_F = ["TREE_ID", "VERSION", "NODE_ID", "COND_NUMBER", "ARG1_TYPE", "ARG1_TAB",
          "ARG1_FLD", "ARG1_CONST", "ARG1_NODE", "ARG1_NODE_ATTR", "ARG1_REF_NAME",
          "ARG2_TYPE", "ARG2_TAB", "ARG2_FLD", "ARG2_CONST", "OPERATOR",
          "LINK_OPERATOR"]
REGUT_F = ["LAUFD", "DTFOR", "ZBUKR", "BANKS"]

# Implementa feedback_build_the_map_before_answering: recorre los arboles VIVOS
# enteros e imprime lo que hay, lo haya preguntado alguien o no.

# La configuracion que hay DETRAS del exit. Sin esto, un nodo que solo cuelga de
# FI_CGI_DMEE_EXIT_W_BADI se lee como "tiene origen" cuando en realidad no emite
# nada -- y ese fue exactamente el estado roto del 19-08-2026 que este mapa daba
# por bueno. La implementacion FR del BAdI no tiene logica propia: resuelve cada
# etiqueta contra YTFI_PPC_TAG (ruta -> tag_id) x YTFI_PPC_STRUC (como componer
# el valor). Si no hay fila para la ruta, el exit devuelve vacio.
PPC_TAG_F = ["LAND1", "DEB_CRE", "TAG_ID", "TAG_FULL"]
PPC_STRUC_F = ["LAND1", "TAG_ID", "PAY_TYPE", "CODE_ORD", "PPC_CODE", "PPC_VALUE",
               "PAY_STRUC", "PAY_FIELD"]


def exit_owner(fn):
    """An exit is OURS if we can change it. SAP- and Citi-delivered we cannot."""
    if fn.startswith(("Z", "Y")):
        return "CUSTOM"          # ours -- source belongs in extracted_code/
    if fn.startswith("/CITIPMW/"):
        return "CITI"            # bank add-on, delivered
    return "SAP"                 # standard (FI_CGI_DMEE_EXIT_W_BADI, DMEE_EXIT_*)


def read_table(conn, table, fields, where=""):
    kw = dict(QUERY_TABLE=table, DELIMITER="|",
              FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=0)
    if where:
        kw["OPTIONS"] = [{"TEXT": where}]
    r = conn.call("RFC_READ_TABLE", **kw)
    return [dict(zip(fields, [c.strip() for c in d["WA"].split("|")]))
            for d in r["DATA"]]


def live_formats(since="20240101"):
    """What is ACTUALLY used, from the media table -- never from assumption."""
    from rfc_helpers import get_connection
    c = get_connection("P01")
    try:
        rows = read_table(c, "REGUT", REGUT_F, "LAUFD >= '%s'" % since)
    finally:
        c.close()
    out = {}
    for x in rows:
        f = x["DTFOR"]
        if not f:
            continue
        d = out.setdefault(f, {"total": 0, "by_year": collections.Counter(),
                               "countries": set()})
        d["total"] += 1
        d["by_year"][x["LAUFD"][:4]] += 1
        if x["BANKS"]:
            d["countries"].add(x["BANKS"])
    return out


def load_trees(system):
    from rfc_helpers import get_connection
    c = get_connection(system)
    ppc = {"tags": [], "struc": []}
    try:
        nodes = read_table(c, "DMEE_TREE_NODE", NODE_F)
        conds = read_table(c, "DMEE_TREE_COND", COND_F)
        try:
            ppc["tags"] = read_table(c, "YTFI_PPC_TAG", PPC_TAG_F)
            ppc["struc"] = read_table(c, "YTFI_PPC_STRUC", PPC_STRUC_F)
        except Exception as exc:            # el motor PPC puede no existir aqui
            ppc["error"] = str(exc)[:120]
    finally:
        c.close()
    return nodes, conds, ppc


def tag_path(src, nid):
    """La ruta en la notacion que usa YTFI_PPC_TAG: <PmtInf><CdtTrfTxInf><...>.

    Empieza en <PmtInf> — los niveles Document / CstmrCdtTrfInitn no cuentan,
    porque asi estan escritas las filas de configuracion.
    """
    o, cur, k = [], src.get(nid), 0
    while cur and k < 40:
        o.append(cur["TECH_NAME"])
        cur = src.get(cur["PARENT_ID"])
        k += 1
    o.reverse()
    if "PmtInf" in o:
        o = o[o.index("PmtInf"):]
    return "".join("<%s>" % x for x in o)


def ppc_backing(ppc, path):
    """Que filas de configuracion PPC respaldan esta ruta. Vacio = el exit no da nada."""
    tags = [t for t in ppc.get("tags", []) if t["TAG_FULL"] == path]
    if not tags:
        return []
    out = []
    for t in tags:
        rows = [s for s in ppc.get("struc", [])
                if s["LAND1"] == t["LAND1"] and s["TAG_ID"] == t["TAG_ID"]]
        out.append((t, rows))
    return out


def pick_version(versions):
    """V001 = maintenance (what you edit). V000 = active. V002+ = backup."""
    return "001" if "001" in versions else sorted(versions)[0]


def children(src, parent):
    """Walk FIRSTCHILD then the BROTHER chain. Sibling order IS the XML order."""
    out, cur, seen = [], src.get(parent["FIRSTCHILD_ID"]), set()
    while cur and cur["NODE_ID"] not in seen:
        seen.add(cur["NODE_ID"])
        out.append(cur)
        cur = src.get(cur["BROTHER_ID"])
    return out


def node_path(src, nid):
    o, cur, k = [], src.get(nid), 0
    while cur and k < 40:
        o.append(cur["TECH_NAME"])
        cur = src.get(cur["PARENT_ID"])
        k += 1
    p = " > ".join(reversed(o))
    return p.replace("Document > CstmrCdtTrfInitn > PmtInf > ", "")


def source_of(n, ppc=None, path=""):
    """De donde sale el valor de este nodo -- y si ese origen REALMENTE da algo.

    Un exit sin configuracion detras no es un origen: es un hueco. Distinguirlo
    es la diferencia entre leer el arbol y entenderlo.
    """
    bits = []
    if n["MP_CONST"]:
        bits.append("const %r" % n["MP_CONST"])
    if n["MP_SC_TAB"]:
        bits.append("%s-%s" % (n["MP_SC_TAB"], n["MP_SC_FLD"]))
    if n["MP_SC_NODE"]:
        bits.append("node %s" % n["MP_SC_NODE"])
    if n["MP_EXIT_FUNC"]:
        tag = "EXIT %s [%s]" % (n["MP_EXIT_FUNC"], exit_owner(n["MP_EXIT_FUNC"]))
        if ppc is not None and path:
            back = ppc_backing(ppc, path)
            if back:
                paises = ",".join(sorted({t["LAND1"] for t, _ in back}))
                tag += " {PPC: %s}" % paises
            elif not ppc.get("error"):
                tag += " {PPC: SIN CONFIG}"
        bits.append(tag)
    if n["CK_EXIT_FUNC"]:
        bits.append("CHECK %s [%s]" % (n["CK_EXIT_FUNC"],
                                       exit_owner(n["CK_EXIT_FUNC"])))
    if n["CV_RULE"]:
        bits.append("cv %r" % n["CV_RULE"])
    if n["NODE_TYPE"] and n["NODE_TYPE"] != "ELEM":
        bits.append("tipo=%s" % n["NODE_TYPE"])
    return bits or ["(vacio)"]


def emits_nothing(n, ppc, path):
    """True si el nodo no puede producir valor: sin constante, sin mapping, sin
    nodo fuente, y su exit (si lo hay) no tiene configuracion PPC que lo respalde."""
    if n["MP_CONST"] or n["MP_SC_TAB"] or n["MP_SC_NODE"]:
        return False
    if not n["MP_EXIT_FUNC"]:
        return True
    if n["MP_EXIT_FUNC"] != "FI_CGI_DMEE_EXIT_W_BADI":
        return False        # exits propios/Citi traen su logica dentro
    if ppc.get("error") or not ppc.get("tags"):
        return False        # no se pudo evaluar -- no afirmar nada
    return not ppc_backing(ppc, path)


def audit_pstladr(src, parent, ppc=None):
    """Las clases de defecto. Devuelve lista de (CLASE, mensaje)."""
    kids = children(src, parent)
    names = [k["TECH_NAME"] for k in kids]
    seq = [n for n in names if n in ISO_ORDER]
    idx = [ISO_ORDER.index(n) for n in seq]
    out = []
    if idx != sorted(idx):
        want = [n for n in ISO_ORDER if n in set(seq)]
        out.append(("ORDER", "orden ISO roto: %s -> debe ser %s"
                    % (" ".join(seq), " ".join(want))))
    present = set(names)
    if (present & STRUCTURED) and "AdrLine" in present:
        out.append(("HYBRID", "estructurado + AdrLine en el mismo PstlAdr"))
    for need in ("TwnNm", "Ctry"):
        if need not in present:
            out.append(("NOV26", "sin <%s> estructurado" % need))
    # Un nodo TECH con nombre de etiqueta ISO no emite nada: borra el dato en
    # silencio. Fue lo que hizo desaparecer <Ctry> el 19-08-2026.
    for k in kids:
        if k["TECH_NAME"] in ISO_ORDER and k["NODE_TYPE"] == "TECH":
            out.append(("TECNICO", "<%s> %s es NODE_TYPE=TECH: no emite etiqueta"
                        % (k["TECH_NAME"], k["NODE_ID"])))
    # Nodos sin origen VISIBLE: ni constante, ni mapping, ni fila PPC que respalde
    # el exit. NO es prueba de que no emitan -- el BAdI tiene una segunda fuente
    # que no se puede leer de tablas: la clase YCL_IDFI_CGI_DMEE_FALLBACK resuelve
    # rutas en ABAP (p.ej. <Cdtr><PstlAdr><StrtNm>, verificado contra fichero real
    # 2026-07-21, que SI sale). Asi que esto es una SOSPECHA que hay que confirmar
    # contra un fichero generado, no un veredicto. Se marca porque cuando ademas
    # falla -- CdtrAgt el 19-08-2026 -- es exactamente esto lo que se ve.
    if ppc is not None:
        ciegos = [k for k in kids
                  if emits_nothing(k, ppc, tag_path(src, k["NODE_ID"]))]
        if ciegos and len(ciegos) == len(kids):
            out.append(("SIN-ORIGEN", "NINGUN hijo (%d) tiene origen visible: solo "
                        "puede venir del BAdI en ABAP. Si el BAdI tampoco resuelve "
                        "estas rutas, DMEE suprime el <PstlAdr> entero -> verificar "
                        "contra un fichero generado" % len(ciegos)))
        elif ciegos:
            out.append(("SIN-ORIGEN", "sin origen visible (puede venir del BAdI): %s"
                        % ", ".join("<%s>" % k["TECH_NAME"] for k in ciegos)))
    return out


def render_conditions(rows):
    if not rows:
        return ""
    parts = []
    for x in sorted(rows, key=lambda z: int(z["COND_NUMBER"] or 0)):
        # ARG_TYPE 3 = referencia a OTRO NODO. Sin leer ARG1_NODE/REF_NAME la
        # condicion se pintaba vacia ("IF  <> 'X'") y parecia rota estando bien.
        a1 = (("nodo %s attr %s" % (x["ARG1_REF_NAME"] or x["ARG1_NODE"],
                                    x["ARG1_NODE_ATTR"])) if x["ARG1_TYPE"] == "3"
              else x["ARG1_CONST"] or ("%s-%s" % (x["ARG1_TAB"], x["ARG1_FLD"])).strip("-"))
        a2 = (("nodo %s" % x["ARG2_CONST"]) if x["ARG2_TYPE"] == "3"
              else x["ARG2_CONST"] or ("%s-%s" % (x["ARG2_TAB"], x["ARG2_FLD"])).strip("-"))
        parts.append(("%s %s %s %s" % (x["LINK_OPERATOR"], a1, x["OPERATOR"], a2)).strip())
    return "  IF " + " ".join(parts)


def report(system, only_tree=None, all_trees=False, dump=None, md=None):
    nodes, conds, ppc = load_trees(system)
    by_tree = collections.defaultdict(list)
    for n in nodes:
        by_tree[n["TREE_ID"]].append(n)
    cond_ix = collections.defaultdict(list)
    for c in conds:
        cond_ix[(c["TREE_ID"], c["VERSION"], c["NODE_ID"])].append(c)

    usage = {}
    if only_tree:
        targets = [only_tree]
    elif all_trees:
        targets = sorted(by_tree)
    else:
        usage = live_formats()
        targets = sorted(usage, key=lambda f: -usage[f]["total"])

    print("=" * 100)
    print("MAPA DMEE -- sistema %s -- %d arboles en total, %d bajo analisis"
          % (system, len(by_tree), len(targets)))
    print("=" * 100)
    if usage:
        print("\nFORMATOS VIVOS (medido en REGUT P01, 2024+, campo DTFOR):")
        print("  %-38s %7s %7s %7s %7s   %s"
              % ("FORMATO (= TREE_ID)", "total", "2024", "2025", "2026", "paises"))
        for f in targets:
            d = usage[f]
            print("  %-38s %7d %7d %7d %7d   %s"
                  % (f, d["total"], d["by_year"]["2024"], d["by_year"]["2025"],
                     d["by_year"]["2026"], ",".join(sorted(d["countries"]))))

    result, totals = {}, collections.Counter()
    for tid in targets:
        rows = by_tree.get(tid)
        if not rows:
            print("\n\n%s\n!! %s -- NO EXISTE en %s" % ("#" * 100, tid, system))
            continue
        versions = sorted({r["VERSION"] for r in rows})
        v = pick_version(versions)
        # index PER VERSION: NODE_IDs repeat across versions, and one dict for
        # all of them silently builds a cross-version chimera (burned 2026-08-18)
        src = {r["NODE_ID"]: r for r in rows if r["VERSION"] == v}

        exits = collections.Counter()
        for n in src.values():
            for fld in ("MP_EXIT_FUNC", "CK_EXIT_FUNC"):
                if n[fld]:
                    exits[n[fld]] += 1

        print("\n\n%s\n# %s   V%s   %d nodos   versiones=%s"
              % ("#" * 100, tid, v, len(src), ",".join(versions)))
        print("#   exits: %d nodos, %d funciones distintas"
              % (sum(exits.values()), len(exits)))
        for fn, k in exits.most_common():
            print("#     %4dx  %-38s %s" % (k, fn, exit_owner(fn)))

        tre = {"version": v, "versions": versions, "nodes": len(src),
               "exits": dict(exits), "pstladr": []}
        pstl = [n for n in src.values() if n["TECH_NAME"] == "PstlAdr"]
        print("#   PstlAdr: %d" % len(pstl))
        for p in sorted(pstl, key=lambda z: node_path(src, z["NODE_ID"])):
            flags = audit_pstladr(src, p, ppc)
            for cls, _ in flags:
                totals[cls] += 1
            tag = "  ".join("[%s]" % c for c, _ in flags) or "[OK]"
            print("\n  %s   %s" % (node_path(src, p["NODE_ID"]), tag))
            print("     padre %s%s" % (p["NODE_ID"],
                  render_conditions(cond_ix.get((tid, v, p["NODE_ID"]), []))))
            for cls, msg in flags:
                print("     !! %-7s %s" % (cls, msg))
            for i, k in enumerate(children(src, p), 1):
                print("     %2d. %-26s %-14s %s%s"
                      % (i, k["TECH_NAME"], k["NODE_ID"], " | ".join(source_of(k, ppc, tag_path(src, k["NODE_ID"]))),
                         render_conditions(cond_ix.get((tid, v, k["NODE_ID"]), []))))
            tre["pstladr"].append({
                "path": node_path(src, p["NODE_ID"]), "node_id": p["NODE_ID"],
                "flags": [{"class": c, "msg": m} for c, m in flags],
                "children": [{"pos": i, "tag": k["TECH_NAME"],
                              "node_id": k["NODE_ID"], "source": source_of(k, ppc, tag_path(src, k["NODE_ID"])),
                              "mp_exit": k["MP_EXIT_FUNC"],
                              "ck_exit": k["CK_EXIT_FUNC"],
                              "cv_rule": k["CV_RULE"]}
                             for i, k in enumerate(children(src, p), 1)]})
        result[tid] = tre

    print("\n\n%s\nRESUMEN: %s" % ("=" * 100,
          "  ".join("%s=%d" % (k, n) for k, n in sorted(totals.items()))
          or "sin hallazgos"))
    if dump:
        json.dump({"system": system,
                   "usage": {k: {"total": v["total"],
                                 "countries": sorted(v["countries"])}
                             for k, v in usage.items()},
                   "trees": result}, open(dump, "w"), indent=1)
        print("JSON -> %s" % dump)
    if md:
        if not usage:
            print("!! --md necesita el barrido de formatos vivos "
                  "(no combinar con --tree / --all-trees)")
        else:
            write_markdown(md, system, usage, result)
    return totals


def write_markdown(path, system, usage, trees):
    """The knowledge doc, one section per format -- GENERATED, never hand-written.

    Hand-written config docs drift the moment someone edits the tree, and a
    drifted doc is worse than none: it is read as fact. So this is regenerated
    from the system every time and carries the date it was measured.
    """
    ICON = {"ORDER": "ORDEN", "HYBRID": "HIBRIDO", "NOV26": "NOV-2026",
            "TECNICO": "NODO-TECNICO", "SIN-ORIGEN": "SIN-ORIGEN-VISIBLE"}
    L = []
    w = L.append
    w("# Configuracion DMEE por formato -- %s" % system)
    w("")
    w("> GENERADO por `Zagentexecution/quality_checks/dmee_tree_map.py`. **No editar a mano.**")
    w("> Regenerar: `python Zagentexecution/quality_checks/dmee_tree_map.py "
      "--sys %s --md <este_fichero>`" % system)
    w("")
    w("Que lee cada seccion: el arbol DMEE completo de un formato -- estructura, "
      "de donde sale el valor de cada nodo, que exit lo decide, y bajo que condicion "
      "se emite. El **orden de los hijos es el orden del XML**, y para `PstlAdr` ese "
      "orden es un `xs:sequence` de ISO 20022: violarlo es el rechazo del 21-07-2026.")
    w("")
    w("Un nodo puede tener mapping **y** exit a la vez. **Gana el exit** -- el mapping "
      "solo dice que haria SAP si nadie lo hubiera sobrescrito.")
    w("")
    w("## Formatos vivos")
    w("")
    w("Medido en `REGUT.DTFOR` de P01 (la tabla de medios = lo que ve FDTA), no supuesto.")
    w("")
    w("| Formato (= TREE_ID) | Total 2024+ | 2026 | Paises | Nodos | PstlAdr | Hallazgos |")
    w("|---|---:|---:|---|---:|---:|---|")
    for f in sorted(usage, key=lambda z: -usage[z]["total"]):
        t = trees.get(f)
        if not t:
            continue
        d = usage[f]
        fl = collections.Counter(x["class"] for p in t["pstladr"] for x in p["flags"])
        w("| `%s` | %d | %d | %s | %d | %d | %s |"
          % (f, d["total"], d["by_year"]["2026"], ", ".join(sorted(d["countries"])),
             t["nodes"], len(t["pstladr"]),
             ", ".join("%s×%d" % (ICON[k], n) for k, n in sorted(fl.items())) or "-"))
    w("")
    for f in sorted(usage, key=lambda z: -usage[z]["total"]):
        t = trees.get(f)
        if not t:
            continue
        w("---")
        w("")
        w("## `%s`" % f)
        w("")
        w("%d nodos en V%s (versiones existentes: %s). %d medios generados desde 2024, "
          "%d en 2026, paises %s."
          % (t["nodes"], t["version"], ", ".join(t["versions"]), usage[f]["total"],
             usage[f]["by_year"]["2026"], ", ".join(sorted(usage[f]["countries"]))))
        w("")
        w("### Exits que llama")
        w("")
        if t["exits"]:
            w("| Funcion | Nodos | Quien la entrega |")
            w("|---|---:|---|")
            for fn, k in sorted(t["exits"].items(), key=lambda z: -z[1]):
                o = exit_owner(fn)
                who = {"CUSTOM": "**nuestra** -- la podemos cambiar",
                       "CITI": "Citi (add-on del banco)",
                       "SAP": "SAP estandar"}[o]
                w("| `%s` | %d | %s |" % (fn, k, who))
        else:
            w("Ninguno -- todo el arbol es mapping directo.")
        w("")
        w("### Direcciones postales")
        w("")
        for p in t["pstladr"]:
            flags = p["flags"]
            tag = " ".join("**[%s]**" % ICON[x["class"]] for x in flags) or "OK"
            w("#### `%s` -- %s" % (p["path"], tag))
            w("")
            w("Nodo padre `%s`." % p["node_id"])
            w("")
            for x in flags:
                w("- **%s** -- %s" % (ICON[x["class"]], x["msg"]))
            if flags:
                w("")
            w("| # | Etiqueta XML | Nodo | De donde sale el valor |")
            w("|---:|---|---|---|")
            for k in p["children"]:
                w("| %d | `%s` | `%s` | %s |"
                  % (k["pos"], k["tag"], k["node_id"],
                     " · ".join("`%s`" % s for s in k["source"])))
            w("")
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("MARKDOWN -> %s" % path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sys", default="D01")
    ap.add_argument("--tree")
    ap.add_argument("--all-trees", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--md", help="genera el doc de conocimiento, seccion por formato")
    a = ap.parse_args()
    report(a.sys, a.tree, a.all_trees, a.json, a.md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
