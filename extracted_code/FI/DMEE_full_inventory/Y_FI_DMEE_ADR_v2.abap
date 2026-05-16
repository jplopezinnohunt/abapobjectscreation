FUNCTION y_fi_dmee_adr.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE_ABA
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID_ABA
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"     REFERENCE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE_ABA
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"----------------------------------------------------------------------
* V001 SEPA Dbtr structured address — Pattern A (paying-co lookup)
* Mapping logic aligned with CGI BAdI standard:
*   Nm           <- ADRC-NAME1
*   StrtNm       <- ADRC-STREET
*   BldgNb       <- ADRC-HOUSE_NUM1
*   PstCd        <- ADRC-POST_CODE1
*   TwnNm        <- ADRC-CITY1
*   Ctry         <- ADRC-COUNTRY
*   CtrySubDvsn  <- ADRC-REGION
*   Dept/SubDept <- '' (Treasury decision pending; suppress via condition later)
*
* Source resolved via:
*   FPAYH-ZBUKR -> T001-ADRNR -> ADRC (current-valid record by sy-datlo)

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
  " v2: extended SELECT to include name1, country, region for full PstlAdr coverage
  SELECT SINGLE name1, street, house_num1, post_code1,
                city1, country, region
    FROM adrc INTO @DATA(ls_adrc)
    WHERE addrnumber = @lv_adrnr
      AND date_from <= @sy-datlo
      AND date_to   >= @sy-datlo.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " Dispatch by leaf TECH_NAME
  CASE i_extension-node-tech_name.
    WHEN 'Nm'.
      c_value = ls_adrc-name1.
    WHEN 'StrtNm'.
      c_value = ls_adrc-street.
    WHEN 'BldgNb'.
      c_value = ls_adrc-house_num1.
    WHEN 'PstCd'.
      c_value = ls_adrc-post_code1.
    WHEN 'TwnNm'.
      c_value = ls_adrc-city1.
    WHEN 'Ctry'.
      c_value = ls_adrc-country.
    WHEN 'CtrySubDvsn'.
      c_value = ls_adrc-region.
    WHEN 'Dept'.
      " Treasury decision pending — empty for now
      " (will be suppressed via condition node once configured)
      c_value = ''.
    WHEN 'SubDept'.
      c_value = ''.
    WHEN OTHERS.
      " Unknown leaf path -- leave c_value blank, X-flag will suppress
      RETURN.
  ENDCASE.

  o_value = c_value.

ENDFUNCTION.
