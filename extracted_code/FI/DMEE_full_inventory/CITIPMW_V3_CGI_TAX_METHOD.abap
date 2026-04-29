FUNCTION /citipmw/v3_cgi_tax_method .
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
  l_fpayhx = lwa_item-fpayhx.
  l_fpayh  = lwa_item-fpayh.
  l_fpayp  = lwa_item-fpayp.

  lv_bukrs = l_fpayp-doc2r(4).
  lv_belnr = l_fpayp-doc2r+4(10).
  lv_gjahr = l_fpayp-doc2r+14(4).
  lv_buzei = l_fpayp-doc2r+18(3).

  CLEAR gs_with_item.

  SELECT witht ctnumber wt_withcd qsrec qsatz wt_qsshh wt_qbshh
              FROM with_item INTO CORRESPONDING FIELDS OF gs_with_item
                                               WHERE bukrs EQ lv_bukrs
                                                 AND belnr EQ lv_belnr
                                                 AND gjahr EQ lv_gjahr
                                                 AND buzei EQ lv_buzei
                                                 AND wt_qsshh NE 0
                                                 AND wt_qbshh NE 0.
  ENDSELECT.

  IF gs_with_item IS NOT INITIAL.
    c_value = gs_with_item-witht.
  ENDIF.

  IF l_fpayhx-ubiso = 'TH'.
    c_value = '3'.
  ELSEIF l_fpayhx-ubiso = 'BR' AND l_fpayhx-ctgypurp = 'TAXS'.
    c_value = '17'.
  ENDIF.

ENDFUNCTION.