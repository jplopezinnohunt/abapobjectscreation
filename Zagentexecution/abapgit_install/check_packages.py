"""Check which local packages exist on D01."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# Check each candidate package
for pkg in ["$TMP", "$LOC", "$ABAPGIT", "ZABAPGIT", "Z_ABAPGIT"]:
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TDEVC", DELIMITER="|",
                  OPTIONS=[{"TEXT": f"DEVCLASS = '{pkg}'"}],
                  FIELDS=[{"FIELDNAME": "DEVCLASS"}, {"FIELDNAME": "AS4USER"},
                          {"FIELDNAME": "CTEXT"}], ROWCOUNT=2)
    rows = r.get("DATA", [])
    if rows:
        print(f"[OK]   {pkg:15s}  {rows[0]['WA']}")
    else:
        print(f"[MISS] {pkg:15s}  NOT in TDEVC")

# Also count how many $-prefix packages exist
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TDEVC", DELIMITER="|",
              OPTIONS=[{"TEXT": "DEVCLASS LIKE '$%'"}],
              FIELDS=[{"FIELDNAME": "DEVCLASS"}], ROWCOUNT=100)
print(f"\nTotal $-prefix local packages on D01: {len(r.get('DATA', []))}")
for row in r.get("DATA", [])[:20]:
    print(f"  {row['WA']}")

# Where exactly does ZABAPGIT_STANDALONE live? Confirm $TMP
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
              OPTIONS=[{"TEXT": "OBJ_NAME = 'ZABAPGIT_STANDALONE'"}],
              FIELDS=[{"FIELDNAME": "DEVCLASS"}, {"FIELDNAME": "AUTHOR"}], ROWCOUNT=2)
print(f"\nZABAPGIT_STANDALONE actual DEVCLASS:")
for row in r.get("DATA", []):
    print(f"  {row['WA']}")

conn.close()
