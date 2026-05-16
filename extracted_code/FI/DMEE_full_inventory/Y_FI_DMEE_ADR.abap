* === IMPORT_PARAMETER ===
PARAMETER=I_TREE_TYPE | TYP=DMEE_TREETYPE_ABA
PARAMETER=I_TREE_ID | TYP=DMEE_TREEID_ABA
PARAMETER=I_ITEM
PARAMETER=I_PARAM
PARAMETER=I_UPARAM
PARAMETER=I_EXTENSION | TYP=DMEE_EXIT_INTERFACE_ABA
* === EXPORT_PARAMETER ===
PARAMETER=O_VALUE | REFERENCE=X
PARAMETER=C_VALUE | REFERENCE=X
PARAMETER=N_VALUE | REFERENCE=X
PARAMETER=P_VALUE | REFERENCE=X
* === TABLES_PARAMETER ===
PARAMETER=I_TAB
* === SOURCE ===
LINE=FUNCTION y_fi_dmee_adr.
LINE=*"----------------------------------------------------------------------
LINE=*"*"Local Interface:
LINE=*"  IMPORTING
LINE=*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE_ABA
LINE=*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID_ABA
LINE=*"     VALUE(I_ITEM)
LINE=*"     VALUE(I_PARAM)
LINE=*"     VALUE(I_UPARAM)
LINE=*"     VALUE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE_ABA
LINE=*"  EXPORTING
LINE=*"     REFERENCE(O_VALUE)
LINE=*"     REFERENCE(C_VALUE)
LINE=*"     REFERENCE(N_VALUE)
LINE=*"     REFERENCE(P_VALUE)
LINE=*"  TABLES
LINE=*"      I_TAB
LINE=*"----------------------------------------------------------------------

LINE=  FIELD-SYMBOLS: <fs_item> TYPE dmee_paym_if_type.

LINE=  CLEAR: o_value, c_value, n_value, p_value.

LINE=  ASSIGN i_item TO <fs_item>.
LINE=  IF sy-subrc <> 0 OR <fs_item>-fpayh-zbukr IS INITIAL.
LINE=    RETURN.
LINE=  ENDIF.

LINE=  " Resolve paying-co ADRNR via T001
LINE=  SELECT SINGLE adrnr
LINE=    FROM t001 INTO @DATA(lv_adrnr)
LINE=    WHERE bukrs = @<fs_item>-fpayh-zbukr.
LINE=  IF sy-subrc <> 0 OR lv_adrnr IS INITIAL.
LINE=    RETURN.
LINE=  ENDIF.

LINE=  " Read paying-co address from ADRC (current valid record)
LINE=  SELECT SINGLE street, house_num1, post_code1, city1
LINE=    FROM adrc INTO @DATA(ls_adrc)
LINE=    WHERE addrnumber = @lv_adrnr
LINE=      AND date_from <= @sy-datlo
LINE=      AND date_to   >= @sy-datlo.
LINE=  IF sy-subrc <> 0.
LINE=    RETURN.
LINE=  ENDIF.

LINE=  " Dispatch by leaf TECH_NAME
LINE=  CASE i_extension-node-TECH_NAME.
LINE=    WHEN 'StrtNm'.
LINE=      c_value = ls_adrc-street.
LINE=    WHEN 'BldgNb'.
LINE=      c_value = ls_adrc-house_num1.
LINE=    WHEN 'PstCd'.
LINE=      c_value = ls_adrc-post_code1.
LINE=    WHEN 'TwnNm'.
LINE=      c_value = ls_adrc-city1.
LINE=    WHEN OTHERS.
LINE=      " Unknown leaf path -- leave c_value blank, X-flag will suppress
LINE=      RETURN.
LINE=  ENDCASE.

LINE=  o_value = c_value.

LINE=ENDFUNCTION.