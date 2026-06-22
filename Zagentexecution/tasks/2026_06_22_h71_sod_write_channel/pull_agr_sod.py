"""
pull_agr_sod.py — PMO H71: pull P01 role data to confirm WRITE-CHANNEL SoD (declared half).

The behavioral half (audit log + CDHDR + posted docs) already CONFIRMS the 6 users
EXERCISE both incompatible duties. This pulls AGR_USERS + AGR_1251 (NOT in the Gold DB)
to confirm they are AUTHORIZED for both (declared SoD) and to NAME the roles to remediate.

P01 = READ-ONLY via RFC/SSO. Single ROWSKIPS-free RFC_READ_TABLE calls (P01-secured-safe),
WHERE-filtered to the 6 users / their roles. Reuses the extraction skill's shared helpers.
Writes results into the Gold DB (agr_users / agr_1251_sod) + prints the SoD role map.
"""
import os, sys, sqlite3, json

HERE = os.path.dirname(__file__)
MCP = os.path.abspath(os.path.join(HERE, "..", "..", "mcp-backend-server-python"))
sys.path.insert(0, MCP)
from rfc_helpers import get_connection
from pyrfc import RFCError

GOLD = os.path.abspath(os.path.join(HERE, "..", "..", "sap_data_extraction",
                                    "sqlite", "p01_gold_master_data.db"))

USERS = ["E_SILVA", "L_NEVES", "C_SOUZA", "B_LOPES", "MP_ANCUTA", "S_STANTIC", "UBO-RFC"]

# Auth objects that gate each incompatible duty (the SoD-relevant ones) + cross objects.
OBJ_GR   = {"M_MSEG_BWA", "M_MSEG_WMB", "M_MSEG_WWA", "M_MSEG_WWE"}            # goods receipt
OBJ_INV  = {"M_RECH_WRK", "M_RECH_BUK", "M_RECH_EKG", "M_RECH_SPG",
            "F_BKPF_BUK", "F_BKPF_KOA"}                                       # invoice/FI post
OBJ_PR   = {"M_BANF_BSA", "M_BANF_EKG", "M_BANF_EKO", "M_BANF_WRK"}           # purchase req
OBJ_PO   = {"M_BEST_BSA", "M_BEST_EKG", "M_BEST_EKO", "M_BEST_WRK"}           # purchase order
OBJ_VEND = {"F_LFA1_GEN", "F_LFA1_BEK", "F_LFA1_GRP", "F_LFA1_BUK",
            "F_LFA1_APP", "M_LFM1_EKO"}                                       # vendor master
OBJ_CROSS = {"S_TCODE", "S_RFC"}
RELEVANT = OBJ_GR | OBJ_INV | OBJ_PR | OBJ_PO | OBJ_VEND | OBJ_CROSS
DUTY = {**{o: "GR" for o in OBJ_GR}, **{o: "INVOICE" for o in OBJ_INV},
        **{o: "PR" for o in OBJ_PR}, **{o: "PO" for o in OBJ_PO},
        **{o: "VENDOR" for o in OBJ_VEND}}


def read_window(conn, table, fields, where):
    """One ROWSKIPS-free RFC_READ_TABLE call (P01-secured-safe)."""
    opts = [{"TEXT": where}] if where else []
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|", ROWCOUNT=0,
                    FIELDS=[{"FIELDNAME": f} for f in fields], OPTIONS=opts)
    hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out = []
    for row in res.get("DATA", []):
        p = row["WA"].split("|")
        out.append({h: (p[i].strip() if i < len(p) else "") for i, h in enumerate(hdrs)})
    return out


def read_eq(conn, table, fields, field, values):
    """P01-secured RFC_READ_TABLE rejects IN(...) ('suspicious WHERE'); loop equality."""
    out = []
    for v in values:
        try:
            out += read_window(conn, table, fields, f"{field} = '{v}'")
        except RFCError as e:
            if "TABLE_WITHOUT_DATA" in str(e):
                continue
            raise
    return out


def main():
    print(f"Gold DB: {GOLD}")
    print("Connecting to P01 (SNC/SSO, read-only)...")
    conn = get_connection("P01")
    print("  connected.\n")

    # 1) AGR_USERS for the 6 users -> their roles --------------------------------
    print("=== AGR_USERS (role assignments) ===")
    au = read_eq(conn, "AGR_USERS",
                 ["AGR_NAME", "UNAME", "FROM_DAT", "TO_DAT"], "UNAME", USERS)
    by_user = {}
    for r in au:
        by_user.setdefault(r["UNAME"], []).append(r["AGR_NAME"])
    for u in USERS:
        roles = sorted(set(by_user.get(u, [])))
        print(f"  {u:12s}: {len(roles)} roles -> {roles}")
    all_roles = sorted({r["AGR_NAME"] for r in au})
    print(f"\n  distinct roles total: {len(all_roles)}")

    # 2) composite -> single role expansion (AGR_AGRS) --------------------------
    comp = {}
    if all_roles:
        try:
            ag = read_eq(conn, "AGR_AGRS", ["AGR_NAME", "CHILD_AGR"], "AGR_NAME", all_roles)
            for r in ag:
                comp.setdefault(r["AGR_NAME"], []).append(r["CHILD_AGR"])
        except RFCError as e:
            print(f"  (AGR_AGRS read skipped: {e})")
    expand = set(all_roles)
    for parent, kids in comp.items():
        expand.update(kids)
    expand = sorted(expand)
    if comp:
        print(f"  composite roles found: {len(comp)}; expanded role set: {len(expand)}")

    # 3) AGR_1251 for those roles, SoD-relevant objects only ---------------------
    print("\n=== AGR_1251 (authorization values, SoD-relevant objects) ===")
    rows = []
    for role in expand:
        try:
            r = read_window(conn, "AGR_1251",
                            ["AGR_NAME", "OBJECT", "AUTH", "FIELD", "LOW", "HIGH", "DELETED"],
                            f"AGR_NAME = '{role}'")
        except RFCError as e:
            print(f"  [WARN] {role}: {e}")
            continue
        for x in r:
            if x.get("DELETED") == "X":
                continue
            if x["OBJECT"] in RELEVANT:
                rows.append(x)
    print(f"  collected {len(rows)} SoD-relevant authorization rows")

    # persist
    db = sqlite3.connect(GOLD)
    db.execute("DROP TABLE IF EXISTS d01_tmp")  # noop guard
    db.execute("""CREATE TABLE IF NOT EXISTS agr_users
                  (AGR_NAME TEXT, UNAME TEXT, FROM_DAT TEXT, TO_DAT TEXT)""")
    db.execute("DELETE FROM agr_users WHERE UNAME IN (%s)" %
               ",".join("'%s'" % u for u in USERS))
    db.executemany("INSERT INTO agr_users VALUES (?,?,?,?)",
                   [(r["AGR_NAME"], r["UNAME"], r.get("FROM_DAT", ""), r.get("TO_DAT", "")) for r in au])
    db.execute("""CREATE TABLE IF NOT EXISTS agr_1251_sod
                  (AGR_NAME TEXT, OBJECT TEXT, AUTH TEXT, FIELD TEXT, LOW TEXT, HIGH TEXT)""")
    db.execute("DELETE FROM agr_1251_sod")
    db.executemany("INSERT INTO agr_1251_sod VALUES (?,?,?,?,?,?)",
                   [(r["AGR_NAME"], r["OBJECT"], r["AUTH"], r["FIELD"], r.get("LOW", ""), r.get("HIGH", "")) for r in rows])
    db.commit()

    # 4) SoD MAP: per user, which duties are granted (via which role) ------------
    role_duties = {}   # role -> set(duty)
    role_tcodes = {}   # role -> set(tcode LOW)
    role_rfc = {}      # role -> set(func group LOW)
    for r in rows:
        role = r["AGR_NAME"]; obj = r["OBJECT"]
        if obj in DUTY:
            role_duties.setdefault(role, set()).add(DUTY[obj])
        if obj == "S_TCODE" and r["FIELD"] == "TCD" and r["LOW"]:
            role_tcodes.setdefault(role, set()).add(r["LOW"])
        if obj == "S_RFC" and r["FIELD"] == "RFC_NAME" and r["LOW"]:
            role_rfc.setdefault(role, set()).add(r["LOW"])

    print("\n=== SoD ROLE MAP (declared capability per user) ===")
    out = {}
    for u in USERS:
        # direct roles + their composite children
        direct = set(by_user.get(u, []))
        eff = set(direct)
        for d in direct:
            eff.update(comp.get(d, []))
        duties = set()
        granting = {}
        for role in eff:
            for dty in role_duties.get(role, set()):
                duties.add(dty)
                granting.setdefault(dty, []).append(role)
        out[u] = {"roles": sorted(direct), "effective_roles": sorted(eff),
                  "duties_granted": sorted(duties),
                  "granting_roles": {k: sorted(set(v)) for k, v in granting.items()}}
        print(f"\n  {u}: duties granted = {sorted(duties)}")
        for dty, rs in sorted(granting.items()):
            print(f"      {dty:8s} <- {sorted(set(rs))}")

    json.dump({"by_user": out,
               "role_duties": {k: sorted(v) for k, v in role_duties.items()},
               "role_tcodes": {k: sorted(v) for k, v in role_tcodes.items()},
               "role_rfc": {k: sorted(v) for k, v in role_rfc.items()}},
              open(os.path.join(HERE, "agr_sod_map.json"), "w"), indent=2)
    print(f"\nWrote agr_sod_map.json + Gold DB tables agr_users, agr_1251_sod.")
    conn.close()


if __name__ == "__main__":
    main()
