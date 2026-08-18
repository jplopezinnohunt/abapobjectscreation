"""
install_abapgit_standalone.py — Deploy the official zabapgit_standalone bootstrap
report into D01 in package ZABAPGIT under a fresh workbench TR.

Architecture: workstation-bridge (no STRUST needed). The report is fetched here
and pushed to SAP via ADT REST. SAP never talks to GitHub.

Steps:
  1. Read source from local cached file (already downloaded)
  2. Create transportable package ZABAPGIT
  3. Create workbench TR (type K)
  4. Create PROG ZABAPGIT_STANDALONE skeleton in ZABAPGIT under TR
  5. PUT 4.86 MB source via /sap/bc/adt/programs/programs/zabapgit_standalone/source/main
  6. Activate via /sap/bc/adt/activation
  7. Report status
"""

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")

from dotenv import load_dotenv
load_dotenv()

from sap_adt_client import SAPADTClient, from_env

SOURCE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "zabapgit_standalone_2026-05-25.abap")
PACKAGE     = "$TMP"   # local package, always exists on every SAP system, no TR needed
PROG_NAME   = "ZABAPGIT_STANDALONE"
PROG_DESC   = "abapGit standalone - official build from github.com/abapGit"

# ── Load source ────────────────────────────────────────────────────────────────
print(f"[1/7] Reading {SOURCE_FILE}")
with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    source = f.read()
print(f"      {len(source):,} bytes / {source.count(chr(10)):,} lines")
print(f"      first line: {source.splitlines()[0]!r}")

# ── Connect ────────────────────────────────────────────────────────────────────
print(f"[ADT] Connecting via from_env() (D01 default)")
adt = from_env("D01")
adt.fetch_csrf()

# ── 2. Package — $TMP exists by default, no creation needed ───────────────────
print(f"\n[2/7] Using package {PACKAGE} (default $TMP — no creation required, no TR required)")
trkorr = ""  # $TMP objects are not transported

# ── 4. Create PROG skeleton in $TMP ───────────────────────────────────────────
print(f"\n[3-4/7] Creating PROG {PROG_NAME} skeleton in {PACKAGE}")
status = adt.create_object("PROG/P", PROG_NAME, PROG_DESC, PACKAGE, trkorr)
if status >= 400 and status != 400:  # 400 may = already exists
    print(f"      ERROR: create_object failed with HTTP {status}")
    sys.exit(3)

# ── 5. Upload source ───────────────────────────────────────────────────────────
prog_uri = f"/sap/bc/adt/programs/programs/{PROG_NAME.lower()}"
print(f"\n[5/7] Uploading source to {prog_uri}/source/main ({len(source):,} bytes)")
t0 = time.time()
lock_handle = adt.lock(prog_uri)
print(f"      Lock obtained: {lock_handle[:30]}...")
status = adt.set_source(prog_uri, source, lock_handle, trkorr)
elapsed = time.time() - t0
print(f"      Upload status: HTTP {status} in {elapsed:.1f}s")

if status >= 400:
    print(f"      Upload FAILED — releasing lock")
    try:
        adt.unlock(prog_uri, lock_handle)
    except Exception as e:
        print(f"      unlock error: {e}")
    sys.exit(4)

# ── 6. Activate ────────────────────────────────────────────────────────────────
print(f"\n[6/7] Activating {PROG_NAME}")
try:
    activate_result = adt.activate(prog_uri, PROG_NAME, "PROG/P")
    print(f"      activate result: {activate_result}")
except Exception as e:
    print(f"      activate FAILED: {e}")
    print(f"      (Source is uploaded but inactive. Manual SE38 activation possible.)")

# ── 7. Unlock & report ─────────────────────────────────────────────────────────
try:
    adt.unlock(prog_uri, lock_handle)
except Exception as e:
    print(f"  unlock error (non-fatal): {e}")

print(f"\n[7/7] Install attempt complete.")
print(f"      Package: {PACKAGE}")
print(f"      TR     : {trkorr}")
print(f"      Program: {PROG_NAME}")
print(f"      Source : {len(source):,} bytes uploaded")
print(f"\nNext: run check_abapgit_installed.py to verify TADIR/TRDIR")
