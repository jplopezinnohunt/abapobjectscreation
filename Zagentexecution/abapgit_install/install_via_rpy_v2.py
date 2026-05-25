"""
install_via_rpy_v2.py — Two-step:
  Step A: DELETE existing ZABAPGIT_STANDALONE via RFC_ABAP_INSTALL_AND_RUN
          (tiny ABAP that does DELETE REPORT)
  Step B: RPY_PROGRAM_INSERT with SOURCE_EXTENDED (ABAPTXT255 wide table)
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
# Strip trailing empty line if file ended with \n
if lines and lines[-1] == "":
    lines = lines[:-1]
print(f"    {len(source_text):,} bytes / {len(lines):,} non-empty-trailing lines")
maxlen = max(len(l) for l in lines)
print(f"    Max line length: {maxlen} (ABAPTXT255 holds 255-char lines)")
if maxlen > 255:
    print(f"    ERROR: source has lines > 255 chars. Need different approach.")
    sys.exit(1)

print(f"[2] Connecting to D01")
p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# Step A: Delete the existing PROG via RFC_ABAP_INSTALL_AND_RUN
print(f"[3a] Deleting existing PROG {PROG_NAME} via inline ABAP")
delete_abap = [
    {"LINE": "REPORT zdelete_zabapgit."},
    {"LINE": "DATA lv_subrc TYPE sy-subrc."},
    {"LINE": "DELETE REPORT 'ZABAPGIT_STANDALONE'."},
    {"LINE": "lv_subrc = sy-subrc."},
    {"LINE": "IF lv_subrc = 0."},
    {"LINE": "  WRITE: / 'DELETED ZABAPGIT_STANDALONE'."},
    {"LINE": "ELSE."},
    {"LINE": "  WRITE: / 'DELETE failed sy-subrc=', lv_subrc."},
    {"LINE": "ENDIF."},
]
try:
    r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=delete_abap, MODE="F")
    print(f"     WRITES output:")
    for w in r.get("WRITES", []):
        print(f"       {w.get('LINE', w)!r}")
except Exception as e:
    print(f"     RFC_ABAP_INSTALL_AND_RUN failed: {e}")

# Step B: Insert via RPY_PROGRAM_INSERT
print(f"\n[3b] RPY_PROGRAM_INSERT (SOURCE_EXTENDED, 255-char wide)")
# ABAPTXT255 line type field is named LINE
source_tab = [{"LINE": l} for l in lines]
print(f"     Source table: {len(source_tab):,} rows")

t0 = time.time()
try:
    result = conn.call("RPY_PROGRAM_INSERT",
                       PROGRAM_NAME=PROG_NAME,
                       TITLE_STRING="abapGit standalone bootstrap",
                       SUPPRESS_DIALOG="X",
                       DEVELOPMENT_CLASS=PACKAGE,
                       SOURCE_EXTENDED=source_tab)
    elapsed = time.time() - t0
    print(f"     OK in {elapsed:.1f}s")
except Exception as e:
    elapsed = time.time() - t0
    print(f"     FAILED in {elapsed:.1f}s")
    print(f"     error: {e}")
    sys.exit(2)

# Verify
print(f"\n[4] Verifying source in REPOSRC (where ABAP program source lives)")
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="REPOSRC", DELIMITER="|",
              OPTIONS=[{"TEXT": f"PROGNAME = '{PROG_NAME}'"}],
              FIELDS=[{"FIELDNAME": "PROGNAME"}, {"FIELDNAME": "R3STATE"},
                      {"FIELDNAME": "UNAM"}, {"FIELDNAME": "UDAT"},
                      {"FIELDNAME": "VERNO"}])
for row in r.get("DATA", []):
    print(f"     {row['WA']}")
# R3STATE: A=active, I=inactive

conn.close()
print(f"\n[5] If R3STATE=A, install succeeded. If I, run activation next.")
