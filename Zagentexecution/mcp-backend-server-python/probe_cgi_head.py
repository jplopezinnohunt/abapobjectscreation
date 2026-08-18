# -*- coding: utf-8 -*-
"""DMEE_TREE_HEAD for /CGI_XML_CT_UNESCO across systems: version, active flag,
who last changed it and when. READ-ONLY.
Purpose: none of D01/V01/P01 currently holds the structured CdtrAgt config that
produced the 'v2' file Marlies tested — establish whether it was ever there."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from rfc_helpers import get_connection
F = ["TREE_TYPE","TREE_ID","VERSION","EX_STATUS","PARAM_STRUC",
     "FIRSTNODE_ID","CREA_USER","CREA_DATE","VERS_USER","VERS_DATE"]
for sysid in ("D01","V01","P01"):
    try:
        c = get_connection(sysid)
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_HEAD", DELIMITER="|",
                   FIELDS=[{"FIELDNAME": f} for f in F], ROWCOUNT=0)
        rows = [dict(zip(F, [x.strip() for x in d["WA"].split("|")])) for d in r["DATA"]]
        mine = [x for x in rows if x["TREE_ID"] == "/CGI_XML_CT_UNESCO"]
        print(f"\n===== {sysid} =====  ({len(rows)} heads total)")
        for x in mine:
            print(f"  V{x['VERSION']} active={x['EX_STATUS']!r:>4} "
                  f"root={x['FIRSTNODE_ID']} struc={x['PARAM_STRUC']}")
            print(f"        created {x['CREA_USER']:<12} {x['CREA_DATE']}"
                  f"   | version-op {x['VERS_USER']:<12} {x['VERS_DATE']}")
        c.close()
    except Exception as e:
        print(f"\n===== {sysid} ===== ERROR: {str(e)[:160]}")
