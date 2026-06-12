"""
incident_scope.py — READ-ONLY. Definitive incident scope.

Write footprint  = distinct classes in JP_LOPEZ transports since 2026-06-01 (E070/E071).
Health           = current TADIR / SEOCLASS / SEOCOMPO / VRSD per class.
Damaged          = footprint class that is now ORPHAN (no SEOCLASS) or EMPTY (0 comp).
"""
import os, json, datetime
from dotenv import load_dotenv
from pyrfc import Connection

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.normpath(os.path.join(HERE, "..", "..", "mcp-backend-server-python"))
load_dotenv(os.path.join(B, ".env"))


def get_conn():
    return Connection(
        ashost=os.getenv("SAP_ASHOST"), sysnr=os.getenv("SAP_SYSNR"),
        client=os.getenv("SAP_CLIENT"), user=os.getenv("SAP_USER"),
        passwd=os.getenv("SAP_PASSWD") or os.getenv("SAP_PASSWORD"), lang="EN")


def _split72(where):
    """RFC_READ_TABLE OPTIONS lines must be <=72 chars. Split on ' AND '."""
    lines, cur = [], ""
    for i, tok in enumerate(where.split(" AND ")):
        piece = ("" if not cur else cur + " AND ") + tok
        if len(piece) <= 72:
            cur = piece
        else:
            if cur:
                lines.append(cur + " AND")
            cur = tok
    if cur:
        lines.append(cur)
    return [{"TEXT": ln} for ln in lines]


def rt(conn, t, f, w, rc=0):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=t, DELIMITER="|",
                  FIELDS=[{"FIELDNAME": x} for x in f],
                  OPTIONS=_split72(w), ROWCOUNT=rc)
    return [d["WA"].split("|") for d in r["DATA"]]


CLASS_OBJTYPES = {"CLAS", "CLSD", "CPUB", "CPRO", "CPRI", "CDEF",
                  "CIMP", "CINC", "METH"}


def main():
    conn = get_conn()

    # 1. JP_LOPEZ transports since Jun 1
    tr = rt(conn, "E070", ["TRKORR", "AS4DATE"],
            "AS4USER = 'JP_LOPEZ' AND AS4DATE >= '20260601'")
    trkorrs = [(p[0].strip(), p[1].strip()) for p in tr]

    # 2. class objects in those transports -> distinct class names + first-seen date
    footprint = {}   # class -> {transports:set, types:set, first_date}
    for tk, date in trkorrs:
        for p in rt(conn, "E071", ["PGMID", "OBJECT", "OBJ_NAME"],
                    f"TRKORR = '{tk}'"):
            obj = p[1].strip()
            if obj not in CLASS_OBJTYPES:
                continue
            cls = p[2].strip().split()[0]  # METH names carry 'CLASS  method'
            d = footprint.setdefault(cls, {"transports": set(), "types": set(),
                                           "first_date": date})
            d["transports"].add(tk)
            d["types"].add(obj)
            d["first_date"] = min(d["first_date"], date)

    # 3. health per footprint class
    print(f"{'CLASS':40s} {'STATUS':22s} {'comp':>4s} {'vers':>5s} "
          f"{'types(transport)':22s} dates")
    report = []
    for cls in sorted(footprint):
        tadir = rt(conn, "TADIR", ["DEVCLASS", "AUTHOR"],
                   f"PGMID = 'R3TR' AND OBJECT = 'CLAS' AND OBJ_NAME = '{cls}'", 1)
        seoclass = rt(conn, "SEOCLASS", ["CLSNAME"], f"CLSNAME = '{cls}'", 1)
        compo = rt(conn, "SEOCOMPO", ["CMPNAME"], f"CLSNAME = '{cls}'")
        vrsd = rt(conn, "VRSD", ["VERSNO"], f"OBJNAME LIKE '{cls}%'")
        ncomp = len(compo)
        if not tadir:
            status = "GONE (no TADIR)"
        elif not seoclass:
            status = "ORPHAN (no SEOCLASS)"
        elif ncomp == 0:
            status = "EMPTY (0 comp)"
        else:
            status = f"HEALTHY"
        fp = footprint[cls]
        rec = {"class": cls, "status": status, "components": ncomp,
               "vrsd_versions": len(vrsd),
               "package": tadir[0][0].strip() if tadir else None,
               "object_types": sorted(fp["types"]),
               "transports": sorted(fp["transports"]),
               "first_date": fp["first_date"]}
        report.append(rec)
        flag = "  <-- DAMAGED" if status != "HEALTHY" else ""
        print(f"{cls:40s} {status:22s} {ncomp:4d} {len(vrsd):5d} "
              f"{','.join(sorted(fp['types'])):22s} {fp['first_date']}{flag}")

    conn.close()
    damaged = [r for r in report if r["status"] != "HEALTHY"]
    out = {"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "footprint_count": len(report), "damaged_count": len(damaged),
           "report": report}
    json.dump(out, open(os.path.join(HERE, "incident_scope_result.json"), "w",
                        encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\n{len(report)} classes in write footprint, "
          f"{len(damaged)} DAMAGED, {len(report)-len(damaged)} healthy")
    print("DAMAGED:", ", ".join(r["class"] for r in damaged))


if __name__ == "__main__":
    main()
