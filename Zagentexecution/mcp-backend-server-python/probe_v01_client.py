"""Which V01 client am I in? Are DMEE trees anywhere? READ-ONLY."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from rfc_helpers import get_connection

print("SAP_V01_CLIENT (logon client from .env):", os.getenv("SAP_V01_CLIENT"))
print("SAP_V01_ASHOST:", os.getenv("SAP_V01_ASHOST"))
print("SAP_V01_SYSNR:", os.getenv("SAP_V01_SYSNR"))

c = get_connection("V01")

# logon client + system id via RFC_SYSTEM_INFO
try:
    info = c.call("RFC_SYSTEM_INFO")["RFCSI_EXPORT"]
    print("\nRFC_SYSTEM_INFO: SYSID=%s  HOST=%s  DBSYS=%s  RFCMANDT(if any)=%s" % (
        info.get("RFCSYSID"), info.get("RFCHOST"), info.get("RFCDBSYS"),
        info.get("RFCMANDT", "(n/a)")))
except Exception as e:
    print("RFC_SYSTEM_INFO ERROR:", e)

# all clients
try:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="T000",
               FIELDS=[{"FIELDNAME": "MANDT"}, {"FIELDNAME": "MTEXT"},
                       {"FIELDNAME": "ORT01"}, {"FIELDNAME": "CCCATEGORY"}])
    print("\nAll clients in V01:")
    for row in r.get("DATA", []):
        print("  ", row["WA"])
except Exception as e:
    print("T000 ERROR:", e)

# does DMEE_TREE_HEAD have ANY rows in this client?
try:
    r = c.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_HEAD",
               FIELDS=[{"FIELDNAME": "TREE_TYPE"}, {"FIELDNAME": "TREE_ID"},
                       {"FIELDNAME": "VERSION"}], ROWCOUNT=10)
    rows = r.get("DATA", [])
    print(f"\nDMEE_TREE_HEAD any rows (this client)? {len(rows)}")
    for row in rows:
        print("  ", row["WA"])
except Exception as e:
    print("\nDMEE_TREE_HEAD (no where) ERROR:", e)

c.close()
