"""
forensic_class_loss.py — READ-ONLY forensic of the class-loss incident on D01.

NO WRITES. NO LOCKS. NO ACTIVATE. Pure RFC_READ_TABLE + version directory reads.

Goal: establish ground truth for the panic report "14 classes lost".
  1. Blast radius: every source unit JP_LOPEZ last changed in the damage window
     (REPOSRC.UNAM = JP_LOPEZ, UDAT in window) — classes AND programs/includes.
  2. Per affected CLASS: current health
       - TADIR registered?  SEOCLASS registered?  SEOCOMPO component count (now)
       - vs the Jun-10 census (nmenard_seo_anatomy.json) component count = damage delta
  3. Recoverability: VRSD version directory — how many prior versions exist to restore.

Output: console table + forensic_class_loss_result.json
"""
import os, sys, json, datetime, collections

from dotenv import load_dotenv
from pyrfc import Connection

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.normpath(os.path.join(HERE, "..", "..", "mcp-backend-server-python"))
load_dotenv(os.path.join(BACKEND, ".env"))

# Damage window — probes created Jun 7; widen to be safe.
WIN_FROM = "20260601"
WIN_TO   = "20260612"
SUSPECT_USER = (os.getenv("SAP_USER") or "JP_LOPEZ").upper()

# Known candidates from the write/deploy scripts (cross-check even if outside window).
KNOWN_CANDIDATES = [
    "ZCL_CRP_CERT_READER",
    "YCL_FI_ACC_DOCUMENT_ARGA",
    "YCL_FI_BANK_RECONCILIATION_BL",
    "ZCL_FI_ACCOUNT_SUBST",
]

CENSUS = os.path.normpath(os.path.join(
    HERE, "..", "2026_06_10_nmenard_inventory", "nmenard_seo_anatomy.json"))


def get_conn():
    return Connection(
        ashost=os.getenv("SAP_ASHOST"),
        sysnr=os.getenv("SAP_SYSNR"),
        client=os.getenv("SAP_CLIENT"),
        user=os.getenv("SAP_USER"),
        passwd=os.getenv("SAP_PASSWD") or os.getenv("SAP_PASSWORD"),
        lang="EN",
    )


def read_table(conn, table, fields, where, rowcount=0):
    """RFC_READ_TABLE — one call, no ROWSKIPS (D01 rejects paging)."""
    opts = []
    # SAP RFC_READ_TABLE OPTIONS lines are max 72 chars each; split on AND boundaries.
    for chunk in where:
        opts.append({"TEXT": chunk})
    res = conn.call(
        "RFC_READ_TABLE",
        QUERY_TABLE=table,
        DELIMITER="|",
        FIELDS=[{"FIELDNAME": f} for f in fields],
        OPTIONS=opts,
        ROWCOUNT=rowcount,
    )
    rows = []
    for d in res["DATA"]:
        parts = d["WA"].split("|")
        rows.append({fields[i]: (parts[i].strip() if i < len(parts) else "")
                     for i in range(len(fields))})
    return rows


def classname_from_include(name):
    """ABAP class include NAME -> class name. Class includes look like
    'YCL_FI_ACC_DOCUMENT_ARGA======CP' (name padded to 30 with '=', + suffix).
    Programs/includes have no '=' run."""
    if "=" in name:
        return name.split("=")[0]
    return None


def main():
    print("=" * 70)
    print("CLASS-LOSS FORENSIC — D01 (READ-ONLY)")
    print(f"window {WIN_FROM}..{WIN_TO}  user={SUSPECT_USER}")
    print("=" * 70)

    conn = get_conn()
    print(f"connected: {os.getenv('SAP_ASHOST')}:{os.getenv('SAP_SYSNR')} "
          f"client {os.getenv('SAP_CLIENT')} as {os.getenv('SAP_USER')}\n")

    # ── 1. Blast radius via SEO change tables (REPOSRC unreadable via RFC) ────
    # SEOCLASSDF = class-definition header (per version); SEOCOMPODF = component
    # (method/attr) defs. Both carry AUTHOR/CREATEDON/CHANGEDBY/CHANGEDON.
    print("[1] SEOCLASSDF / SEOCOMPODF — changed by suspect in window ...")
    cls_changed = read_table(
        conn, "SEOCLASSDF",
        ["CLSNAME", "VERSION", "STATE", "AUTHOR", "CREATEDON",
         "CHANGEDBY", "CHANGEDON"],
        [f"CHANGEDBY = '{SUSPECT_USER}' AND CHANGEDON >= '{WIN_FROM}'"],
        rowcount=0,
    )
    cmp_changed = read_table(
        conn, "SEOCOMPODF",
        ["CLSNAME", "CMPNAME", "VERSION", "STATE", "CHANGEDBY", "CHANGEDON"],
        [f"CHANGEDBY = '{SUSPECT_USER}' AND CHANGEDON >= '{WIN_FROM}'"],
        rowcount=0,
    )
    print(f"    SEOCLASSDF rows changed: {len(cls_changed)}")
    print(f"    SEOCOMPODF rows changed: {len(cmp_changed)}\n")

    classes = collections.defaultdict(list)   # class -> [change rows]
    for r in cls_changed:
        classes[r["CLSNAME"]].append({**r, "_src": "CLASSDF"})
    for r in cmp_changed:
        classes[r["CLSNAME"]].append({**r, "_src": f"COMPODF:{r['CMPNAME']}"})
    non_class = []

    print(f"    -> {len(classes)} distinct CLASSES touched by {SUSPECT_USER} "
          f"since {WIN_FROM}")
    for cn in sorted(classes):
        rows = classes[cn]
        last = max(rows, key=lambda x: x.get("CHANGEDON", ""))
        states = sorted({r.get("STATE", "?") for r in rows})
        print(f"       CLASS  {cn:38s} last {last.get('CHANGEDON','?')} "
              f"states={states} ({len(rows)} change-rows)")

    # Union with known candidates
    all_classes = sorted(set(classes) | set(KNOWN_CANDIDATES))

    # ── census baseline (Jun-10 component counts) ────────────────────────────
    census_counts = {}
    if os.path.exists(CENSUS):
        try:
            with open(CENSUS, encoding="utf-8") as f:
                cdata = json.load(f)
            # tolerate a few shapes; count SEOCOMPO rows per class if present
            if isinstance(cdata, dict):
                comp = cdata.get("SEOCOMPO") or cdata.get("seocompo") or []
                if isinstance(comp, list):
                    for row in comp:
                        c = (row.get("CLSNAME") or row.get("clsname") or "").strip()
                        if c:
                            census_counts[c] = census_counts.get(c, 0) + 1
        except Exception as e:
            print(f"    (census parse skipped: {e})")
    print(f"\n    census component counts loaded for {len(census_counts)} classes")

    # ── 2/3. Per-class health + recoverability ───────────────────────────────
    print("\n[2] Per-class health (TADIR / SEOCLASS / SEOCOMPO / versions) ...")
    report = []
    def safe(table, fields, where, rowcount=0):
        try:
            return read_table(conn, table, fields, where, rowcount)
        except Exception as e:
            print(f"    (read {table} failed: {str(e)[:80]})")
            return []

    for cn in all_classes:
        tadir = safe("TADIR", ["OBJ_NAME", "DEVCLASS", "AUTHOR"],
                     [f"PGMID = 'R3TR' AND OBJECT = 'CLAS' AND ",
                      f"OBJ_NAME = '{cn}'"], rowcount=1)
        seoclass = safe("SEOCLASS", ["CLSNAME"],
                        [f"CLSNAME = '{cn}'"], rowcount=1)
        compo = safe("SEOCOMPO", ["CLSNAME", "CMPNAME"],
                     [f"CLSNAME = '{cn}'"], rowcount=0)
        # version directory: prior versions available to RESTORE.
        # Class version objects: OBJTYPE in CLSD/CPUB/CPRO/CPRI/CINC/METH...,
        # OBJNAME begins with the class name. LIKE catches method-version objects.
        vrsd = safe("VRSD",
                    ["OBJTYPE", "OBJNAME", "VERSNO", "AUTHOR", "DATUM"],
                    [f"OBJNAME LIKE '{cn}%'"], rowcount=0)

        now_comp = len(compo)
        base_comp = census_counts.get(cn)
        status = "?"
        if not tadir:
            status = "GONE (no TADIR)"
        elif not seoclass:
            status = "GONE (no SEOCLASS)"
        elif now_comp == 0:
            status = "EMPTY (0 components)"
        elif base_comp is not None and now_comp < base_comp:
            status = f"SHRUNK ({now_comp}<{base_comp})"
        elif base_comp is not None and now_comp == base_comp:
            status = "OK (matches census)"
        else:
            status = f"PRESENT ({now_comp} comp)"

        rec = {
            "class": cn,
            "in_window": cn in classes,
            "known_candidate": cn in KNOWN_CANDIDATES,
            "tadir": bool(tadir),
            "package": tadir[0]["DEVCLASS"] if tadir else None,
            "author": tadir[0]["AUTHOR"] if tadir else None,
            "seoclass": bool(seoclass),
            "components_now": now_comp,
            "components_census": base_comp,
            "vrsd_versions": len(vrsd),
            "status": status,
        }
        report.append(rec)
        print(f"    {status:24s} {cn:38s} comp now={now_comp} "
              f"census={base_comp} versions={len(vrsd)} pkg={rec['package']}")

    conn.close()

    out = {
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "window": [WIN_FROM, WIN_TO],
        "suspect_user": SUSPECT_USER,
        "touched_units": touched,
        "classes_in_window": sorted(classes),
        "non_class_units": [r["NAME"] for r in non_class],
        "class_health": report,
    }
    outpath = os.path.join(HERE, "forensic_class_loss_result.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nwrote {outpath}")
    print("\nDONE (read-only).")


if __name__ == "__main__":
    main()
