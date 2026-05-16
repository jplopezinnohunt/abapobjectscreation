"""Read source of Y_FI_DMEE_ADR FM from D01 to use as signature template
for the new Y_FI_DMEE_NAME exit FM.
"""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected D01")

FM = "Y_FI_DMEE_ADR"
print(f"\n=== {FM} source via RPY_FUNCTIONMODULE_READ_NEW ===")
try:
    r = conn.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME=FM)
    print(f"  GROUPNAME    : {r.get('GROUPNAME','')}")
    print(f"  SHORT_TEXT   : {r.get('SHORT_TEXT','')}")
    print(f"  NAMESPACE    : {r.get('NAMESPACE','')}")
    print(f"  DEVCLASS     : {r.get('DEVCLASS','')}")
    src = r.get('SOURCE', [])
    print(f"  Source lines : {len(src)}\n")
    print("--- SOURCE ---")
    for i, line in enumerate(src):
        print(f"{i+1:4d}: {line}")
    # Also import/export/tables structure
    print("\n--- IMPORT params ---")
    for p in r.get('IMPORT_PARAMETER', []):
        print(f"  {p}")
    print("\n--- EXPORT params ---")
    for p in r.get('EXPORT_PARAMETER', []):
        print(f"  {p}")
    print("\n--- TABLES params ---")
    for p in r.get('TABLES_PARAMETER', []):
        print(f"  {p}")
    print("\n--- CHANGING params ---")
    for p in r.get('CHANGING_PARAMETER', []):
        print(f"  {p}")
    print("\n--- EXCEPTIONS ---")
    for p in r.get('EXCEPTION_LIST', []):
        print(f"  {p}")
except Exception as e:
    print(f"  err: {e}")
