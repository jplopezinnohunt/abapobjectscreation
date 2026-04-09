*----------------------------------------------------------------------*
***INCLUDE LHRTSF06 .
*----------------------------------------------------------------------*



*&---------------------------------------------------------------------*
*&      Form  MODIFY_PTRV_DOC_TAX
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      <--P_*PTRV_DOC_TAX  text
*----------------------------------------------------------------------*
form modify_ptrv_doc_tax changing
                         p_*ptrv_doc_tax structure ptrv_doc_tax.

  call method exit_trip_post_fi->MODIFY_PTRV_DOC_TAX
       exporting
         flt_val            = p_*ptrv_doc_tax-bukrs
       changing
         ptrv_doc_tax       = p_*ptrv_doc_tax.

endform.                    " MODIFY_PTRV_DOC_TAX



*&---------------------------------------------------------------------*
*&      Form  MODIFY_PTRV_DOC_IT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      <--P_*PTRV_DOC_IT  text
*----------------------------------------------------------------------*
form modify_ptrv_doc_it changing
                        p_*ptrv_doc_it structure ptrv_doc_it.

  call method exit_trip_post_fi->MODIFY_PTRV_DOC_it
       exporting
         flt_val            = p_*ptrv_doc_it-bukrs
       changing
         ptrv_doc_it        = p_*ptrv_doc_it.

endform.                    " MODIFY_PTRV_DOC_IT



*&---------------------------------------------------------------------*
*&      Form  MODIFY_PTRV_DOC_HD
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      <--P_*PTRV_DOC_HD  text
*----------------------------------------------------------------------*
form modify_ptrv_doc_hd changing
                        p_*ptrv_doc_hd structure ptrv_doc_hd.

  call method exit_trip_post_fi->MODIFY_PTRV_DOC_hd
       exporting
         flt_val            = p_*ptrv_doc_hd-bukrs
       changing
         ptrv_doc_hd        = p_*ptrv_doc_hd.

endform.                    " MODIFY_PTRV_DOC_HD