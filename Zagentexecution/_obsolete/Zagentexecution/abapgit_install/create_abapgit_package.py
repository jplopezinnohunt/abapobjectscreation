"""Create $ABAPGIT local package via inline ABAP (since ADT REST /packages 404 on EhP8).
$ABAPGIT is a $-prefix local package -- no TR required, but does need explicit creation
(unlike $TMP which is always pre-existing)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# Check if exists first
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TDEVC", DELIMITER="|",
              OPTIONS=[{"TEXT": "DEVCLASS = '$ABAPGIT'"}],
              FIELDS=[{"FIELDNAME": "DEVCLASS"}], ROWCOUNT=5)
existing = r.get("DATA", [])
print(f"Pre-check: $ABAPGIT in TDEVC: {len(existing)} rows")

if existing:
    print("Already exists - skipping creation")
else:
    # Use BAPI to create the package
    print("Creating $ABAPGIT package via TR_DEVCLASS_CREATE...")
    abap = [
        {"LINE": "REPORT zcreate_abapgit_pkg."},
        {"LINE": "DATA: ls_pak TYPE scompkdtln,"},
        {"LINE": "      ls_pak_data TYPE pkgmast_attr_str_010,"},
        {"LINE": "      lt_ret TYPE TABLE OF bapiret2,"},
        {"LINE": "      lv_subrc TYPE sy-subrc."},
        {"LINE": ""},
        {"LINE": "* Build minimal package attributes for a local $-package"},
        {"LINE": "ls_pak-devclass     = '$ABAPGIT'."},
        {"LINE": "ls_pak-ctext        = 'abapGit local objects'."},
        {"LINE": "ls_pak-as4user      = sy-uname."},
        {"LINE": "ls_pak-pdevclass    = '$TMP'."},
        {"LINE": "ls_pak-component    = 'HOME'."},
        {"LINE": "ls_pak-as4langu     = 'E'."},
        {"LINE": "ls_pak-dlvunit      = 'LOCAL'."},
        {"LINE": ""},
        {"LINE": "* Try to create via low-level FM (works on NW 7.40)"},
        {"LINE": "CALL FUNCTION 'PAK_DETAIL_CREATE_OR_UPDATE'"},
        {"LINE": "  EXPORTING"},
        {"LINE": "    iv_devclass             = '$ABAPGIT'"},
        {"LINE": "    is_data                 = ls_pak"},
        {"LINE": "    iv_create_mode          = 'X'"},
        {"LINE": "  EXCEPTIONS"},
        {"LINE": "    invalid_input           = 1"},
        {"LINE": "    package_data_inconsistent = 2"},
        {"LINE": "    other_problem_class     = 3"},
        {"LINE": "    OTHERS                  = 4."},
        {"LINE": "WRITE: / 'PAK_DETAIL_CREATE_OR_UPDATE subrc =', sy-subrc."},
        {"LINE": "IF sy-subrc = 0."},
        {"LINE": "  COMMIT WORK AND WAIT."},
        {"LINE": "  WRITE: / 'Commit done'."},
        {"LINE": "ENDIF."},
    ]
    r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap, MODE="F")
    print(f"WRITES ({len(r.get('WRITES', []))} rows):")
    for w in r.get("WRITES", []):
        print(f"  {w.get('ZEILE', w.get('LINE', dict(w)))}")
    if r.get("ERRORMESSAGE"):
        print(f"ERROR: {r['ERRORMESSAGE']}")

# Verify post
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TDEVC", DELIMITER="|",
              OPTIONS=[{"TEXT": "DEVCLASS = '$ABAPGIT'"}],
              FIELDS=[{"FIELDNAME": "DEVCLASS"}, {"FIELDNAME": "AS4USER"},
                      {"FIELDNAME": "CTEXT"}], ROWCOUNT=5)
print(f"\nPost-check: $ABAPGIT in TDEVC: {len(r.get('DATA', []))} rows")
for row in r.get("DATA", []):
    print(f"  {row['WA']}")
conn.close()
