"""
install_abapgit_v3.py — Use the existing sap_adt_client wrapper write_program_source.
PROG/P shell already exists from v1/v2 attempts; this just uploads source + activates.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from sap_adt_client import from_env

SOURCE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "zabapgit_standalone_2026-05-25.abap")
PROG_NAME = "ZABAPGIT_STANDALONE"

print(f"[1] Reading {SOURCE_FILE}")
with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    source = f.read()
print(f"    {len(source):,} bytes / {source.count(chr(10)):,} lines")

print(f"[2] Connecting to D01 via ADT")
adt = from_env("D01")
adt.fetch_csrf()

print(f"[3] write_program_source -> {PROG_NAME}")
# Patch the wrapper's timeout for this huge body
import urllib.request
_orig_open = urllib.request.urlopen
def _open_with_timeout(req, *args, **kwargs):
    kwargs["timeout"] = 300
    return _orig_open(req, *args, **kwargs)
urllib.request.urlopen = _open_with_timeout

ok = adt.write_program_source(PROG_NAME, source, transport="")
print(f"\n[RESULT] write_program_source returned {ok}")
