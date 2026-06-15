import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
c = get_connection("V01")

# 1) REGUT structure (NO_DATA -> just FIELDS metadata)
print("=== REGUT columns ===")
r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUT", NO_DATA="X")
cols=[f["FIELDNAME"] for f in r.get("FIELDS",[])]
print(", ".join(cols))

# 2) Does the run header REGUV exist for the phantom vs a date we know is real?
def regv(laufd, laufi):
    try:
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="REGUV",
            OPTIONS=[{"TEXT": f"LAUFD = '{laufd}' AND LAUFI = '{laufi}'"}],
            FIELDS=[{"FIELDNAME":"LAUFD"},{"FIELDNAME":"LAUFI"},{"FIELDNAME":"XECHT"},{"FIELDNAME":"STATUS"}])
        rows=r.get("DATA",[])
        return rows[0]["WA"] if rows else "NO ROW"
    except Exception as e:
        return "NO ROW" if "TABLE_WITHOUT_DATA" in str(e) else "ERR "+str(e)[:30]
print("\n=== REGUV existence ===")
for d,i in [("20240531","00001B"),("20240531","0001B"),("20240531","00002B"),
            ("20240424","00012B"),("20240425","00006B")]:
    print(f"  {d}/{i!r:9} -> {regv(d,i)}")
c.close()
