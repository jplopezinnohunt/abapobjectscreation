FUNCTION /CITIPMW/V3_POSTALCODE.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"     REFERENCE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"----------------------------------------------------------------------

  DATA:   lwa_item   TYPE dmee_paym_if_type,
          lwa_item1   TYPE dmee_paym_if_type,
          l_fpayhx   TYPE fpayhx,
          l_fpayh    TYPE fpayh,
          l_fpayp    TYPE fpayp,
          c_zbiso    TYPE fpayhx-zbiso,
          c_zliso    TYPE fpayhx-zliso.

  DATA: temp(10) TYPE c,
        c_piuid(35) TYPE c.

  lwa_item = i_item.
  l_fpayhx  = lwa_item-fpayhx.
  l_fpayh  = lwa_item-fpayh.

  c_zliso = l_fpayhx-zliso.

  IF NOT l_fpayh-zpst2 IS INITIAL AND
     NOT l_fpayh-zpfac IS INITIAL.
    temp = l_fpayh-zpst2.
  ELSE.
    temp = l_fpayh-zpstl.
  ENDIF.

  CASE c_zliso.
    WHEN 'SE'.
      CONDENSE temp NO-GAPS.
    WHEN OTHERS.
* Remove the character '-' from zip code 'XXXXX-xxxx'.
      IF c_zliso = 'US'.
        REPLACE '-' IN temp WITH ''.
        CONDENSE temp NO-GAPS.
      ENDIF.
  ENDCASE.

  c_value = temp.

*}   INSERT
ENDFUNCTION.