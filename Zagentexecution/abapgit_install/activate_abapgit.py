"""Activate ZABAPGIT_STANDALONE via ADT activation REST endpoint."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from sap_adt_client import from_env

PROG_NAME = "ZABAPGIT_STANDALONE"
PROG_URI = f"/sap/bc/adt/programs/programs/{PROG_NAME.lower()}"

print(f"Connecting to D01 via ADT")
adt = from_env("D01")
adt.fetch_csrf()

print(f"Activating {PROG_NAME}")
try:
    result = adt.activate(PROG_URI, PROG_NAME, "PROG/P")
    print(f"  result: {result}")
except Exception as e:
    print(f"  activate raised: {e}")

print(f"\nDone. Next: check REPOSRC R3STATE = 'A' (active) via ABAP probe.")
