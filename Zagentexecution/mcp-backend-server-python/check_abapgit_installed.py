import os
from pyrfc import Connection
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
         "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_PASSWD"):
        p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"
        p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = os.getenv("SAP_SNC_QOP", "9")
    return Connection(**p)


def query(conn, table, where, fields, label):
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE=table, DELIMITER="|",
                      OPTIONS=[{"TEXT": where}],
                      FIELDS=[{"FIELDNAME": f} for f in fields],
                      ROWCOUNT=10)
        rows = r.get("DATA", [])
        print(f"[{label}]  table={table}  where={where}")
        print(f"           rows_returned={len(rows)}")
        for row in rows[:5]:
            print(f"           {row['WA']}")
        return len(rows)
    except Exception as e:
        print(f"[{label}]  ERROR: {str(e)[:120]}")
        return -1


conn = get_conn()
print(f"Connected to {os.getenv('SAP_ASHOST')}:{os.getenv('SAP_SYSNR')} client={os.getenv('SAP_CLIENT')}")
print("=" * 80)

probes = [
    ("TADIR", "PGMID = 'R3TR' AND OBJECT = 'PROG' AND OBJ_NAME LIKE 'ZABAPGIT%'",
     ["OBJ_NAME", "DEVCLASS"], "1. TADIR programs ZABAPGIT*"),
    ("TADIR", "PGMID = 'R3TR' AND OBJECT = 'CLAS' AND OBJ_NAME LIKE 'ZCL_ABAPGIT%'",
     ["OBJ_NAME", "DEVCLASS"], "2. TADIR classes ZCL_ABAPGIT*"),
    ("TRDIR", "NAME LIKE 'ZABAPGIT%'",
     ["NAME", "SUBC"], "3. TRDIR reports ZABAPGIT*"),
    ("TDEVC", "DEVCLASS LIKE 'ZABAPGIT%'",
     ["DEVCLASS", "PDEVCLASS"], "4a. TDEVC packages ZABAPGIT*"),
    ("TDEVC", "DEVCLASS = '$ABAPGIT'",
     ["DEVCLASS", "PDEVCLASS"], "4b. TDEVC package $ABAPGIT"),
    ("TDEVC", "DEVCLASS LIKE '%ABAPGIT%'",
     ["DEVCLASS", "PDEVCLASS"], "4c. TDEVC any *ABAPGIT*"),
    ("TFDIR", "FUNCNAME LIKE 'ZABAPGIT%'",
     ["FUNCNAME", "PNAME"], "5. TFDIR function modules ZABAPGIT*"),
    ("TADIR", "PGMID = 'R3TR' AND OBJECT = 'CLAS' AND OBJ_NAME LIKE 'ZIF_ABAPGIT%'",
     ["OBJ_NAME", "DEVCLASS"], "6. TADIR interfaces ZIF_ABAPGIT*"),
    ("TADIR", "OBJ_NAME LIKE '%ABAPGIT%'",
     ["OBJ_NAME", "OBJECT", "DEVCLASS"], "7. TADIR ANY %ABAPGIT%"),
    ("TADIR", "OBJ_NAME LIKE 'ZAG%'",
     ["OBJ_NAME", "OBJECT", "DEVCLASS"], "8. TADIR ZAG* (alternative naming)"),
]

results = {}
for table, where, fields, label in probes:
    n = query(conn, table, where, fields, label)
    results[label] = n
    print("-" * 80)

print("=" * 80)
print("SUMMARY:")
total = 0
for label, n in results.items():
    if n > 0:
        total += n
    print(f"  {label}: {n}")
print(f"  TOTAL artifact hits: {total}")
print()
if total == 0:
    print("VERDICT: abapGit is NOT installed on D01. Confirms brain claim #197 (session #76).")
else:
    print("VERDICT: abapGit artifacts FOUND on D01. Brain claim #197 needs update.")

conn.close()
