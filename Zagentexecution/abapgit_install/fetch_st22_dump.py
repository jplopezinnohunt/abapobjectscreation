"""Fetch latest ST22 dump for current user — read SNAP/SNAPT tables via inline ABAP."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

# Use SNAP_LIST_FOR_DEVELOPER or read SNAP directly
abap = [
    {"LINE": "REPORT zfetch_dump."},
    {"LINE": "DATA: lt_snap TYPE TABLE OF snap,"},
    {"LINE": "      lv_str  TYPE string,"},
    {"LINE": "      lv_n    TYPE i."},
    {"LINE": ""},
    {"LINE": "* Find the latest SAPSQL_DATA_LOSS dump for current user"},
    {"LINE": "SELECT datum uzeit ausname uname mandt seqno"},
    {"LINE": "  FROM snap INTO TABLE @DATA(lt_idx)"},
    {"LINE": "  WHERE uname = @sy-uname"},
    {"LINE": "    AND ausname = 'SAPSQL_DATA_LOSS'"},
    {"LINE": "  ORDER BY datum DESCENDING uzeit DESCENDING"},
    {"LINE": "  UP TO 5 ROWS."},
    {"LINE": "LOOP AT lt_idx ASSIGNING FIELD-SYMBOL(<i>)."},
    {"LINE": "  WRITE: / 'IDX:', <i>-datum, <i>-uzeit, <i>-ausname, 'seqno=', <i>-seqno."},
    {"LINE": "ENDLOOP."},
    {"LINE": ""},
    {"LINE": "* Read text snippets for the latest one"},
    {"LINE": "READ TABLE lt_idx INDEX 1 INTO DATA(ls_top)."},
    {"LINE": "IF sy-subrc = 0."},
    {"LINE": "  WRITE: / '--- Latest dump details ---'."},
    {"LINE": "  WRITE: / 'DATE:', ls_top-datum, 'TIME:', ls_top-uzeit."},
    {"LINE": ""},
    {"LINE": "  SELECT seqno text"},
    {"LINE": "    FROM snap INTO TABLE @DATA(lt_text)"},
    {"LINE": "    WHERE datum   = @ls_top-datum"},
    {"LINE": "      AND uzeit   = @ls_top-uzeit"},
    {"LINE": "      AND uname   = @ls_top-uname"},
    {"LINE": "      AND mandt   = @ls_top-mandt"},
    {"LINE": "      AND ausname = @ls_top-ausname"},
    {"LINE": "      AND ( fldname = 'C'    OR fldname = 'AKT'   OR fldname = 'TLINE'"},
    {"LINE": "          OR fldname = 'PROGRAM' OR fldname = 'INCLUDE' OR fldname = 'LINNO'"},
    {"LINE": "          OR fldname = 'NAME' )"},
    {"LINE": "    ORDER BY seqno UP TO 50 ROWS."},
    {"LINE": "  lv_n = lines( lt_text )."},
    {"LINE": "  WRITE: / 'Text rows read:', lv_n."},
    {"LINE": "  LOOP AT lt_text ASSIGNING FIELD-SYMBOL(<t>)."},
    {"LINE": "    WRITE: / 'T', <t>-seqno, ':', <t>-text+0(120)."},
    {"LINE": "  ENDLOOP."},
    {"LINE": "ENDIF."},
]
r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap, MODE="F")
print(f"WRITES ({len(r.get('WRITES', []))}):")
for w in r.get("WRITES", []):
    print(f"  {w.get('ZEILE', dict(w))}")
if r.get("ERRORMESSAGE"):
    print(f"ERROR: {r['ERRORMESSAGE']}")
conn.close()
