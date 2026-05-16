"""Verify which D01 RFC FMs are available for ABAP source deploy."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

candidates = [
    ("RFC_ABAP_INSTALL_AND_RUN", "Standard SAP — install + run a one-shot ABAP report"),
    ("RPY_PROGRAM_INSERT",       "Insert a new program / report"),
    ("RPY_PROGRAM_UPDATE",       "Update existing program source"),
    ("RPY_INCLUDE_INSERT",       "Insert a new include"),
    ("RS_TOOL_ACCESS",           "Generic toolset access"),
    ("RPY_TADIR_OBJECT_INSERT",  "Insert TADIR entry"),
    ("FUNCTION_EXISTS",          "Check FM existence"),
]

print("=== D01 RFC FM availability for deploy ===\n")
print(f"  {'FM':<35} {'available':<12} note")
print(f"  {'-'*35} {'-'*12} {'-'*40}")
for fm, note in candidates:
    try:
        # Use FUNCTION_EXISTS to test
        r = c.call("FUNCTION_EXISTS", FUNCNAME=fm)
        # If no exception, it exists
        print(f"  {fm:<35} ✓ YES        {note}")
    except Exception as e:
        emsg = str(e)
        if "FUNCTION_NOT_EXIST" in emsg:
            print(f"  {fm:<35} ✗ NO         {note}")
        else:
            print(f"  {fm:<35} ? ERROR      {emsg[:50]}")
