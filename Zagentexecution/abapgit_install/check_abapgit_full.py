"""List ALL TADIR + TDEVC entries that match ABAPGIT or LOC after dev edition import attempt."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

print("=== ALL TADIR rows matching %ABAPGIT% ===")
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
              OPTIONS=[{"TEXT": "OBJ_NAME LIKE '%ABAPGIT%'"}],
              FIELDS=[{"FIELDNAME": "PGMID"}, {"FIELDNAME": "OBJECT"},
                      {"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"},
                      {"FIELDNAME": "AUTHOR"}, {"FIELDNAME": "CREATED_ON"}],
              ROWCOUNT=50)
for row in r.get("DATA", []):
    print(f"  {row['WA']}")
print(f"Total: {len(r.get('DATA', []))}")

print()
print("=== TADIR rows in package $LOC (where abapGit would land) ===")
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
              OPTIONS=[{"TEXT": "DEVCLASS = '$LOC'"}],
              FIELDS=[{"FIELDNAME": "PGMID"}, {"FIELDNAME": "OBJECT"},
                      {"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"},
                      {"FIELDNAME": "AUTHOR"}, {"FIELDNAME": "CREATED_ON"}],
              ROWCOUNT=20)
print(f"Rows in $LOC: {len(r.get('DATA', []))}")
for row in r.get("DATA", []):
    print(f"  {row['WA']}")

print()
print("=== Did anyone log into abapGit's repo metadata? (ZIF_ABAPGIT_* / ZCL_ABAPGIT_*) ===")
for prefix in ["ZIF_ABAPGIT", "ZCL_ABAPGIT", "ZCX_ABAPGIT"]:
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
                  OPTIONS=[{"TEXT": f"OBJ_NAME LIKE '{prefix}%'"}],
                  FIELDS=[{"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "OBJECT"}],
                  ROWCOUNT=5)
    print(f"  {prefix}*: {len(r.get('DATA', []))} rows")

conn.close()
