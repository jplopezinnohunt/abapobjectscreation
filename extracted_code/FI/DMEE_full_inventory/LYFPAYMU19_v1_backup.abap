FUNCTION y_fi_dmee_adr.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE_ABA
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID_ABA
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"     VALUE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE_ABA
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"----------------------------------------------------------------------

  FIELD-SYMBOLS: <fs_item> TYPE dmee_paym_if_type.

  CLEAR: o_value, c_value, n_value, p_value.

  ASSIGN i_item TO <fs_item>.
  IF sy-subrc <> 0 OR <fs_item>-fpayh-zbukr IS INITIAL.
    RETURN.
  ENDIF.

  " Resolve paying-co ADRNR via T001
  SELECT SINGLE adrnr
    FROM t001 INTO @DATA(lv_adrnr)
    WHERE bukrs = @<fs_item>-fpayh-zbukr.
  IF sy-subrc <> 0 OR lv_adrnr IS INITIAL.
    RETURN.
  ENDIF.

  " Read paying-co address from ADRC (current valid record)
  SELECT SINGLE street, house_num1, post_code1, city1
    FROM adrc INTO @DATA(ls_adrc)
    WHERE addrnumber = @lv_adrnr
      AND date_from <= @sy-datlo
      AND date_to   >= @sy-datlo.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " Dispatch by leaf TECH_NAME
  CASE i_extension-node-TECH_NAME.
    WHEN 'StrtNm'.
      c_value = ls_adrc-street.
    WHEN 'BldgNb'.
      c_value = ls_adrc-house_num1.
    WHEN 'PstCd'.
      c_value = ls_adrc-post_code1.
    WHEN 'TwnNm'.
      c_value = ls_adrc-city1.
    WHEN OTHERS.
      " Unknown leaf path -- leave c_value blank, X-flag will suppress
      RETURN.
  ENDCASE.

  o_value = c_value.

ENDFUNCTION.