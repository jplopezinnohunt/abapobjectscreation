FUNCTION /CITIPMW/V3_DMEE_EXIT_INV_DESC.
*"--------------------------------------------------------------------
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
*"--------------------------------------------------------------------

  DATA: lwa_item   TYPE dmee_paym_if_type,
        l_fpayp    TYPE fpayp.

  data : l_bukrs type bkpf-bukrs,
         l_belnr type bkpf-belnr,
         l_gjahr type bkpf-gjahr.

  lwa_item = i_item.

  l_fpayp  = lwa_item-fpayp.

  l_bukrs = l_fpayp-doc2r(4).
  l_belnr = l_fpayp-doc2r+4(10).
  l_gjahr = l_fpayp-doc2r+14(4).

  select SINGLE bktxt from bkpf into c_value where bukrs =  l_bukrs and
                                                   belnr =  l_belnr and
                                                   gjahr =  l_gjahr.
  if sy-subrc <> 0 or c_value = ' '.
*    c_value = 'No Description'.
  endif.

ENDFUNCTION.