"""Test Y_FI_DMEE_ADR runtime by calling it via RFC with mock values for each TECH_NAME."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# Build a one-shot ABAP that calls Y_FI_DMEE_ADR for each leaf TECH_NAME
abap = [
    "REPORT zfix_test_adr.",
    "DATA: ls_item  TYPE dmee_paym_if_type,",
    "      ls_ext   TYPE dmee_exit_interface_aba,",
    "      lv_o     TYPE dmee_max_c_aba,",
    "      lv_c     TYPE dmee_max_c_aba,",
    "      lv_n     TYPE dmee_max_n_aba,",
    "      lv_p     TYPE dmee_p_value_aba,",
    "      lt_tab   TYPE STANDARD TABLE OF dmee_node_if_aba.",
    "ls_item-fpayh-zbukr = 'UNES'.",
    "",
    "DATA: lt_techs TYPE STANDARD TABLE OF char30.",
    "APPEND 'Nm' TO lt_techs.",
    "APPEND 'StrtNm' TO lt_techs.",
    "APPEND 'BldgNb' TO lt_techs.",
    "APPEND 'PstCd' TO lt_techs.",
    "APPEND 'TwnNm' TO lt_techs.",
    "APPEND 'Ctry' TO lt_techs.",
    "APPEND 'CtrySubDvsn' TO lt_techs.",
    "APPEND 'Dept' TO lt_techs.",
    "APPEND 'SubDept' TO lt_techs.",
    "",
    "DATA lv_t TYPE char30.",
    "LOOP AT lt_techs INTO lv_t.",
    "  CLEAR: lv_o, lv_c, lv_n, lv_p.",
    "  ls_ext-node-tech_name = lv_t.",
    "  CALL FUNCTION 'Y_FI_DMEE_ADR'",
    "    EXPORTING",
    "      i_tree_type = 'PAYM'",
    "      i_tree_id   = '/SEPA_CT_UNES'",
    "      i_item      = ls_item",
    "      i_param     = lv_o",
    "      i_uparam    = lv_o",
    "      i_extension = ls_ext",
    "    IMPORTING",
    "      o_value = lv_o",
    "      c_value = lv_c",
    "      n_value = lv_n",
    "      p_value = lv_p",
    "    TABLES",
    "      i_tab   = lt_tab.",
    "  WRITE: / lv_t, '=>', lv_c.",
    "ENDLOOP.",
]

overlong = [(i+1,l) for i,l in enumerate(abap) if len(l) > 72]
if overlong:
    print(f"WARN {len(overlong)} >72")
    for i,l in overlong[:3]: print(f"  {i}({len(l)}): {l}")

print("=== Execute test ===")
try:
    r = c.call("RFC_ABAP_INSTALL_AND_RUN", MODE='F',
               PROGRAMNAME='ZFIX_TEST_ADR',
               PROGRAM=[{"LINE": l} for l in abap])
    if r.get("ERRORMESSAGE"): print(f"ERR: {r.get('ERRORMESSAGE')}")
    print("--- WRITES ---")
    for w in (r.get("WRITES") or []):
        txt = w.get("ZEILE") if isinstance(w, dict) else str(w)
        print(f"  {txt}")
except Exception as e:
    print(f"FAIL: {e}")
