"""
install_via_rpy.py — Insert abapGit source via RPY_PROGRAM_INSERT (RFC).

RPY_PROGRAM_INSERT signature (SAP standard, NW 7.40):
  IMPORTING
    PROGRAM_NAME    TYPE SOBJ_NAME
    TITLE_STRING    TYPE STRING DEFAULT ''
    SUPPRESS_DIALOG TYPE BOOLEAN DEFAULT 'X'
    DEVELOPMENT_CLASS TYPE DEVCLASS DEFAULT '$TMP'
    USER_COMMAND    TYPE BOOLEAN DEFAULT 'X'
  TABLES
    SOURCE_EXTENDED TYPE ABAPSOURCE
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

SOURCE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "zabapgit_standalone_2026-05-25.abap")
PROG_NAME = "ZABAPGIT_STANDALONE"
PACKAGE   = "$TMP"

print(f"[1] Reading {SOURCE_FILE}")
with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    source_text = f.read()
lines = source_text.split("\n")
print(f"    {len(source_text):,} bytes / {len(lines):,} lines")

# ABAPSOURCE is TABLE OF C72 (technical name CHAR 72). Lines longer than 72 must
# be wrapped. abapGit source has LINE-SIZE 100 — lines may exceed 72 chars.
# Check max line length and wrap if needed.
maxlen = max(len(l) for l in lines)
print(f"    Max line length: {maxlen}")

# RPY_PROGRAM_INSERT actually uses TABLE OF STRING for SOURCE_EXTENDED on
# NW 7.40+ (the EXTENDED suffix), not C72. So no wrapping needed.

print(f"[2] Connecting to D01")
p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# First, inspect the FM signature
print(f"[3] Inspecting RPY_PROGRAM_INSERT signature")
fd = conn.call("RFC_GET_FUNCTION_INTERFACE", FUNCNAME="RPY_PROGRAM_INSERT")
print(f"    IMPORT params:")
for p_ in fd.get("PARAMS", []):
    if p_.get("PARAMCLASS") == "I":
        print(f"      {p_['PARAMETER']:25s} {p_['TABNAME']:30s} {p_['FIELDNAME']:20s} optional={p_['OPTIONAL']}")
print(f"    TABLE params:")
for p_ in fd.get("PARAMS", []):
    if p_.get("PARAMCLASS") == "T":
        print(f"      {p_['PARAMETER']:25s} {p_['TABNAME']:30s} {p_['FIELDNAME']:20s}")
print(f"    EXPORT params:")
for p_ in fd.get("PARAMS", []):
    if p_.get("PARAMCLASS") == "E":
        print(f"      {p_['PARAMETER']:25s} {p_['TABNAME']:30s}")
print(f"    EXCEPTIONS:")
for p_ in fd.get("PARAMS", []):
    if p_.get("PARAMCLASS") == "X":
        print(f"      {p_['PARAMETER']}")

print(f"\n[4] Calling RPY_PROGRAM_INSERT (this overwrites existing source)")
# Build source table as TABLE OF C72 (wrap if needed) — most SAP source FMs use C72
source_tab = []
for line in lines:
    # Wrap lines > 72 chars into multiple C72 lines (very rare in abapGit source)
    if len(line) <= 72:
        source_tab.append({"LINE": line})
    else:
        # naive wrap
        while line:
            source_tab.append({"LINE": line[:72]})
            line = line[72:]
print(f"    SOURCE table built: {len(source_tab):,} C72 lines (after wrap from {len(lines):,} source lines)")

t0 = time.time()
try:
    result = conn.call("RPY_PROGRAM_INSERT",
                       PROGRAM_NAME=PROG_NAME,
                       TITLE_STRING="abapGit standalone bootstrap",
                       SUPPRESS_DIALOG="X",
                       DEVELOPMENT_CLASS=PACKAGE,
                       SOURCE_EXTENDED=source_tab)
    elapsed = time.time() - t0
    print(f"    OK in {elapsed:.1f}s")
    print(f"    result keys: {list(result.keys())}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"    FAILED in {elapsed:.1f}s")
    print(f"    error: {e}")

conn.close()
