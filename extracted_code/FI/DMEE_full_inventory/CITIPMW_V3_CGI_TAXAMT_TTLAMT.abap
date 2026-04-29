FUNCTION /CITIPMW/V3_CGI_TAXAMT_TTLAMT.
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
          l_fpayp        TYPE fpayp,
          lv_belnr       TYPE belnr_d,
          lv_gjahr       TYPE gjahr,
          lv_bukrs       TYPE bukrs,
          lv_buzei       TYPE buzei.

  data : lv_amt_dis type DEC11_4. "Note 1857318
  data : lv_amt_int type DEC11_4. "Note 1857318

  lwa_item = i_item.
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

  lv_amt_int = gs_with_item-wt_qbshh.     "Note 1857318

 if gs_with_item is not initial.

*p_value = abs( gs_with_item-wt_qbshh ).  "Note 1857318

 "Start of Note 1857318

CALL FUNCTION 'CURRENCY_AMOUNT_SAP_TO_DISPLAY'
     EXPORTING
       CURRENCY              = l_fpayp-waers
       AMOUNT_INTERNAL       = lv_amt_int
     IMPORTING
      AMOUNT_DISPLAY        = lv_amt_dis
*    EXCEPTIONS
*      INTERNAL_ERROR        = 1
*      OTHERS                = 2
             .
   IF SY-SUBRC <> 0.
* Implement suitable error handling here
   ENDIF.

p_value = abs( lv_amt_dis ).

  "End of Note 1857318

endif.

ENDFUNCTION.