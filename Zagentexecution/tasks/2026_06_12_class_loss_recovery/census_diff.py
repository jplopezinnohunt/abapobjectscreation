"""
census_diff.py — READ-ONLY. Isolate THIS incident's scope.

Baseline: nmenard_seo_anatomy.json (captured 2026-06-10 08:54) — class component
counts BEFORE the incident.
Now: live SEOCOMPO/SEOCLASS on D01.

Incident-damaged class = had components in the Jun-10 census  AND  now has
0 components (or no SEOCLASS).  That delta is what broke in the last 48h.
"""
import os, json, collections
from dotenv import load_dotenv
from pyrfc import Connection

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.normpath(os.path.join(HERE, "..", "..", "mcp-backend-server-python"))
load_dotenv(os.path.join(B, ".env"))
CENSUS = os.path.normpath(os.path.join(
    HERE, "..", "2026_06_10_nmenard_inventory", "nmenard_seo_anatomy.json"))


def get_conn():
    return Connection(
        ashost=os.getenv("SAP_ASHOST"), sysnr=os.getenv("SAP_SYSNR"),
        client=os.getenv("SAP_CLIENT"), user=os.getenv("SAP_USER"),
        passwd=os.getenv("SAP_PASSWD") or os.getenv("SAP_PASSWORD"), lang="EN")


def rt(conn, t, f, w, rc=0):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=t, DELIMITER="|",
                  FIELDS=[{"FIELDNAME": x} for x in f],
                  OPTIONS=[{"TEXT": w}], ROWCOUNT=rc)
    return [d["WA"].split("|") for d in r["DATA"]]


def main():
    cen = json.load(open(CENSUS, encoding="utf-8"))

    # census component counts per class (from compodf list)
    def keyset(rows, idx_name="CLSNAME"):
        out = collections.Counter()
        for row in rows:
            if isinstance(row, dict):
                c = (row.get("CLSNAME") or row.get("clsname") or "").strip()
            else:
                c = ""
            if c:
                out[c] += 1
        return out

    # discover the shape of one compodf row
    sample = cen["compodf"][0] if cen.get("compodf") else {}
    print("census compodf sample keys:", list(sample.keys()) if isinstance(sample, dict) else type(sample))
    cen_comp = keyset(cen.get("compodf", []))
    cen_classes = {(r.get("CLSNAME") or r.get("clsname") or "").strip()
                   for r in cen.get("classdf", []) if isinstance(r, dict)}
    cen_classes.discard("")
    print(f"census: {len(cen_classes)} classes, "
          f"{len(cen_comp)} with components, "
          f"{sum(cen_comp.values())} total component-defs\n")

    conn = get_conn()

    # current live state: distinct classes that still have SEOCOMPO, per namespace
    live_has_comp = set()
    live_seoclass = set()
    for ns in ("Y%", "Z%"):
        for p in rt(conn, "SEOCOMPO", ["CLSNAME"], f"CLSNAME LIKE '{ns}'"):
            live_has_comp.add(p[0].strip())
        for p in rt(conn, "SEOCLASS", ["CLSNAME"], f"CLSNAME LIKE '{ns}'"):
            live_seoclass.add(p[0].strip())
    conn.close()

    # INCIDENT SCOPE: census-healthy classes now broken
    damaged = []
    for cls in sorted(cen_classes):
        base = cen_comp.get(cls, 0)
        if base == 0:
            continue  # had no components in census anyway — not a regression
        now_has = cls in live_has_comp
        now_seoclass = cls in live_seoclass
        if not now_has:
            damaged.append({
                "class": cls,
                "census_components": base,
                "seoclass_now": now_seoclass,
                "status": ("ORPHAN(no SEOCLASS)" if not now_seoclass
                           else "EMPTY(0 components)"),
            })

    print(f"=== INCIDENT SCOPE: classes healthy on Jun-10, broken now ===")
    print(f"    {len(damaged)} classes regressed\n")
    for d in damaged:
        print(f"    {d['status']:22s} {d['class']:40s} "
              f"had {d['census_components']} comps -> 0")

    json.dump({"damaged": damaged, "count": len(damaged)},
              open(os.path.join(HERE, "census_diff_result.json"), "w",
                   encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\nwrote census_diff_result.json — {len(damaged)} regressed classes")


if __name__ == "__main__":
    main()
