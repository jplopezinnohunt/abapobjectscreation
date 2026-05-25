import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# TADIR
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
              OPTIONS=[{"TEXT": "OBJ_NAME = 'ZABAPGIT_STANDALONE'"}],
              FIELDS=[{"FIELDNAME": "PGMID"}, {"FIELDNAME": "OBJECT"},
                      {"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"},
                      {"FIELDNAME": "AUTHOR"}, {"FIELDNAME": "CREATED_ON"}])
print("=== TADIR ===")
for row in r.get("DATA", []):
    print(row["WA"])

# TRDIR
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
              OPTIONS=[{"TEXT": "NAME = 'ZABAPGIT_STANDALONE'"}],
              FIELDS=[{"FIELDNAME": "NAME"}, {"FIELDNAME": "SUBC"},
                      {"FIELDNAME": "CNAM"}, {"FIELDNAME": "CDAT"},
                      {"FIELDNAME": "EDTX"}])
print("\n=== TRDIR ===")
for row in r.get("DATA", []):
    print(row["WA"])
# SUBC meanings: 1=executable, M=module pool, F=function group, I=include, S=subroutine pool

conn.close()
