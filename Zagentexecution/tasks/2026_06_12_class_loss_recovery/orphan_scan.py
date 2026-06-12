"""
orphan_scan.py — READ-ONLY. Find ALL damaged custom classes on D01.

Damage signatures (both found in the known-4):
  A. ORPHAN  : TADIR has R3TR CLAS <name>  but SEOCLASS row is GONE.
  B. EMPTY   : SEOCLASS exists but SEOCOMPO component count = 0.
  C. (info)  : present + component count, for context.

Scope: custom namespaces Y* and Z*. Pure set diff, no writes.
"""
import os, json, datetime, collections
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


def rt(conn, table, fields, where, rc=0):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                  FIELDS=[{"FIELDNAME": f} for f in fields],
                  OPTIONS=[{"TEXT": where}], ROWCOUNT=rc)
    out = []
    for d in r["DATA"]:
        p = d["WA"].split("|")
        out.append({fields[i]: (p[i].strip() if i < len(p) else "")
                    for i in range(len(fields))})
    return out


def main():
    conn = get_conn()
    print("orphan_scan — D01 (read-only)\n")

    result = {"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "orphans": [], "empties": [], "namespaces": {}}

    for ns in ("Y%", "Z%"):
        print(f"=== namespace {ns} ===")
        tadir = rt(conn, "TADIR", ["OBJ_NAME", "DEVCLASS", "AUTHOR"],
                   f"PGMID = 'R3TR' AND OBJECT = 'CLAS' AND OBJ_NAME LIKE '{ns}'")
        tadir_names = {r["OBJ_NAME"]: r for r in tadir}
        seo = rt(conn, "SEOCLASS", ["CLSNAME"], f"CLSNAME LIKE '{ns}'")
        seo_names = {r["CLSNAME"] for r in seo}
        print(f"  TADIR CLAS: {len(tadir_names)}   SEOCLASS: {len(seo_names)}")

        # A. ORPHANS: in TADIR, missing from SEOCLASS
        orphans = sorted(set(tadir_names) - seo_names)
        print(f"  ORPHANS (TADIR but no SEOCLASS): {len(orphans)}")
        for o in orphans:
            r = tadir_names[o]
            print(f"     ORPHAN  {o:40s} pkg={r['DEVCLASS']:12s} auth={r['AUTHOR']}")
            result["orphans"].append({"class": o, "package": r["DEVCLASS"],
                                       "author": r["AUTHOR"], "namespace": ns})

        result["namespaces"][ns] = {
            "tadir_clas": len(tadir_names), "seoclass": len(seo_names),
            "orphans": len(orphans)}

    # B. EMPTIES — SEOCLASS present but 0 components. Check classes that still
    #    have SEOCLASS in custom ns. To keep it bounded, only check classes
    #    whose SEOCMP count is 0 — do it per class on a candidate list:
    #    cheaper: pull SEOCLASS Y*/Z* and SEOCOMPO Y*/Z*, diff.
    print("\n=== EMPTY scan (SEOCLASS present, 0 SEOCOMPO) ===")
    for ns in ("Y%", "Z%"):
        seo = {r["CLSNAME"] for r in rt(conn, "SEOCLASS", ["CLSNAME"],
                                        f"CLSNAME LIKE '{ns}'")}
        # classes that DO have components
        comp_classes = {r["CLSNAME"] for r in
                        rt(conn, "SEOCOMPO", ["CLSNAME"],
                           f"CLSNAME LIKE '{ns}'")}
        empties = sorted(seo - comp_classes)
        print(f"  {ns}: SEOCLASS={len(seo)} with-components={len(comp_classes)} "
              f"EMPTY={len(empties)}")
        for e in empties:
            print(f"     EMPTY   {e}")
            result["empties"].append({"class": e, "namespace": ns})

    conn.close()
    out = os.path.join(HERE, "orphan_scan_result.json")
    json.dump(result, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    n_orphan = len(result["orphans"]); n_empty = len(result["empties"])
    print(f"\nTOTAL: {n_orphan} orphans + {n_empty} empties = "
          f"{n_orphan + n_empty} damaged class candidates")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
