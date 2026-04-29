FUNCTION /CITIPMW/V3_TAXAMT_TXBASEAMT.
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

" start of Note 1857318

data : lwa_item TYPE dmee_paym_if_type,
       l_fpayp type fpayp.

data : lv_amt_dis type DEC11_4.
data : lv_amt_int type DEC11_4.

lwa_item = i_item.
l_fpayp  = lwa_item-fpayp.
lv_amt_int = gs_with_item-wt_qsshh.

if gs_with_item is not initial.

*  p_value = abs( gs_with_item-wt_qsshh ). "Note 1857318

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

endif.

" end of Note 1857318

ENDFUNCTION.