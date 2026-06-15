import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
PROGS = ["ZSAPFPAYM_REPLAY","ZFPAYM_STA","ZFPAYM_GET","ZFPAYM_END","ZFPAYM_TOP"]
def check(sysid):
    print(f"\n{'='*60}\n=== {sysid} ===\n{'='*60}")
    try:
        c = get_connection(sysid)
    except Exception as e:
        print(f"  CONN FAIL: {e}"); return
    # TRDIR = program directory
    for p in PROGS:
        try:
            r = c.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR",
                OPTIONS=[{"TEXT": f"NAME = '{p}'"}],
                FIELDS=[{"FIELDNAME":"NAME"},{"FIELDNAME":"SUBC"},{"FIELDNAME":"CNAM"}])
            rows=r.get("DATA",[])
            print(f"  {p:20} -> {'PRESENT '+rows[0]['WA'].strip() if rows else 'ABSENT'}")
        except Exception as e:
            msg=str(e)
            print(f"  {p:20} -> {'ABSENT (no row)' if 'TABLE_WITHOUT_DATA' in msg else 'ERR '+msg[:40]}")
    # Is the 2024 CITI data here? DFPAYG count
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="DFPAYG",
            OPTIONS=[{"TEXT":"FORMI = '/CITI/XML/UNESCO/DC_V3_01' AND LAUFD LIKE '2024%'"}],
            FIELDS=[{"FIELDNAME":"LAUFD"}])
        print(f"  -- DFPAYG CITI 2024 groups here: {len(r.get('DATA',[]))}")
    except Exception as e:
        msg=str(e)
        print(f"  -- DFPAYG CITI 2024 groups here: {'0 (none)' if 'TABLE_WITHOUT_DATA' in msg else 'ERR '+msg[:40]}")
    c.close()
check("D01")   # default bare SAP_* = D01
check("V01")
