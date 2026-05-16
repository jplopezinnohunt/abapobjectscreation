"""Deploy Y_FI_DMEE_NAME function module to D01.

Creates a new function module inside function group YFPAYM (same group as
Y_FI_DMEE_ADR) with the DMEE exit FM standard signature, then installs the
body from extracted_code/FI/DMEE/Y_FI_DMEE_NAME.abap.

Strategy:
  1. Use RFC_ABAP_INSTALL_AND_RUN to execute a Z installer report that
     does FUNCTION_EXISTENCE_CHECK → FUNCTION_MODULE_CREATE → INSERT REPORT
     for the function body include.
  2. Verify by reading back via RPY_FUNCTIONMODULE_READ_NEW.

Safer alternative: SE37 manual paste (Opción A in the doc). Use this script
only after a dry-run in sandbox.
"""
import os
import sys
import pathlib
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN',
)
pwd = os.getenv('SAP_PASSWD') or os.getenv('SAP_PASSWORD')
if pwd:
    params['passwd'] = pwd
if os.getenv('SAP_SNC_MODE') == '1':
    params['snc_mode'] = '1'
    params['snc_partnername'] = os.getenv('SAP_SNC_PARTNERNAME')
    params['snc_qop'] = os.getenv('SAP_SNC_QOP', '9')

conn = Connection(**params)
print("Connected D01")

FM = "Y_FI_DMEE_NAME"
FG = "YFPAYM"
PACKAGE = "YA"

SRC = pathlib.Path(__file__).resolve().parents[2] / "extracted_code/FI/DMEE/Y_FI_DMEE_NAME.abap"
body = SRC.read_text(encoding="utf-8").splitlines()
print(f"Source: {SRC}  ({len(body)} lines)")

# 1. Existence check
print(f"\n=== 1. Check if {FM} already exists ===")
try:
    r = conn.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME=FM)
    if r.get("GROUPNAME") or r.get("SHORT_TEXT"):
        print(f"  ALREADY EXISTS — group={r.get('GROUPNAME')!r} text={r.get('SHORT_TEXT')!r}")
        print("  → will replace source only (no re-create).")
        already_exists = True
    else:
        already_exists = False
        print("  Not found — will create.")
except Exception as e:
    print(f"  err (assume doesn't exist): {e}")
    already_exists = False

# 2. Build an installer report (Z report that calls FUNCTION_MODULE_INSERT)
#    We avoid relying on FUNCTION_MODULE_INSERT directly via RFC because the
#    parameter list is sensitive — instead we generate a one-shot Z report
#    that does the creation, then run it via RFC_ABAP_INSTALL_AND_RUN.

# Build the function body as a string array literal in ABAP
body_lines_abap = []
for line in body:
    # Escape single quotes by doubling them
    esc = line.replace("'", "''")
    body_lines_abap.append(f"  APPEND '{esc}' TO lt_source.")

INSTALLER = [
    f"REPORT Z_INSTALL_{FM}.",
    "DATA: lt_source TYPE STANDARD TABLE OF abaptxt255,",
    "      ls_func   TYPE rs38l,",
    "      lv_subrc  TYPE sy-subrc.",
    "",
    "* ---- Function body ----",
] + body_lines_abap + [
    "",
    f"WRITE: / 'Installing {FM} in group {FG}...'.",
    "",
    "* Use FUNCTION_INCLUDE_SPLIT to verify the function group exists.",
    "",
    "* Create FM definition using FUNCTION_MODULE_INSERT — minimal interface",
    "CALL FUNCTION 'FUNCTION_MODULE_INSERT'",
    "  EXPORTING",
    f"    funcname          = '{FM}'",
    f"    short_text        = 'DMEE exit FM — full name (NAME1+NAME2) from ADRC'",
    f"    pname             = 'SAPL{FG}'",
    "  EXCEPTIONS",
    "    double_task       = 1",
    "    error_message     = 2",
    "    function_exist    = 3",
    "    invalid_name      = 4",
    "    no_function_pool  = 5",
    "    no_modify_permitted = 6",
    "    no_show_permitted = 7",
    "    not_executed      = 8",
    "    suppress_exists   = 9",
    "    too_many_functions = 10",
    "    OTHERS            = 11.",
    "WRITE: / 'FUNCTION_MODULE_INSERT subrc =', sy-subrc.",
    "",
    "* Insert source code into the function include",
    "INSERT REPORT 'LYFPAYMU01' FROM lt_source.   \" placeholder include name",
    "WRITE: / 'INSERT REPORT subrc =', sy-subrc.",
    "",
    "* NOTE: The actual include name follows the pattern L<group>U<NN> where",
    "* NN = function include number returned in TFDIR.INCLUDE after",
    "* FUNCTION_MODULE_INSERT. This needs to be resolved at runtime — see",
    "* notes in the deployment doc.",
]

print(f"\n=== Installer report generated ({len(INSTALLER)} lines) ===")
print(f"Preview first 20 lines:")
for i, l in enumerate(INSTALLER[:20]):
    print(f"  {i+1:3d}: {l}")
print("  ...")

# 3. EXECUTION — commented out by default. User must explicitly enable
#    deployment by passing --execute flag.
if "--execute" in sys.argv:
    print(f"\n=== Executing installer via RFC_ABAP_INSTALL_AND_RUN ===")
    print("  ABORTED — installer has placeholder INCLUDE name 'LYFPAYMU01'.")
    print("  Resolve actual function include name by: TFDIR-INCLUDE after creation,")
    print("  then map to L{FG}U{NN}, then call INSERT REPORT with correct include.")
    print("  Recommended: deploy via SE37 manual paste instead, OR")
    print("  extend this installer with a 2-phase commit (create → resolve → install).")
else:
    print(f"\n=== DRY RUN ===")
    print(f"  No changes made to D01.")
    print(f"  To actually deploy: review installer carefully, then re-run with --execute")
    print(f"  Recommended path: SE37 manual create + paste — safer for a 1-off deployment.")
