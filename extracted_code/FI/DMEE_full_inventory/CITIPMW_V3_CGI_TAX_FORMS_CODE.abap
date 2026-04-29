FUNCTION /citipmw/v3_cgi_tax_forms_code.
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
  DATA :  lwa_item       TYPE dmee_paym_if_type,
          l_fpayh        TYPE fpayh,
          l_fpayhx       TYPE fpayhx,
          l_fpayp        TYPE fpayp,
          lv_belnr       TYPE belnr_d,
          lv_gjahr       TYPE gjahr,
          lv_bukrs       TYPE bukrs,
          lv_buzei       TYPE buzei.

  lwa_item = i_item.
  l_fpayhx  = lwa_item-fpayhx.

  IF gs_with_item IS NOT INITIAL.
    c_value = gs_with_item-qsrec.
    CHECK l_fpayhx-ubiso = 'TH'.
    IF c_value = '03'.
      c_value = '4'.
    ELSEIF c_value = '53'.
      c_value = '7'.
    ENDIF.
  ENDIF.


ENDFUNCTION.