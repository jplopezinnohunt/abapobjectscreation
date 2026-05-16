************************************************************************
* Include ZFPAYM_GET — REPLAY MODE                                     *
* Origin: FPAYM_GET (P01 RPY_PROGRAM_READ session #072)                *
* Changes:                                                             *
*   1. lines 11-40 commented (FI_REF_DOCUMENT_CHECK + REJECT)          *
*   2. BREAK-POINT ID 'YDMEE_REPLAY' inserted before FI_PAYM_MEDIUM_WRITE
************************************************************************

************************************************************************
* Include FPAYM_GET                                                    *
* Get Payment Data                                                     *
************************************************************************

* Read Payment item and initialize internal table of with the former
* payment item processed items
GET fpayh.
  CHECK NOT fpayh-rzawe IS INITIAL.

*** >>> ZREPLAY-REMOVED (FI_REF_DOCUMENT_CHECK gate (would REJECT payments failing ref-doc validation)) — lines 11-40
*   IF fpayh-xvorl IS INITIAL AND NOT par_belp IS INITIAL.
*     CALL FUNCTION 'FI_REF_DOCUMENT_CHECK'   "payment document validation
*       EXPORTING
*         im_doc1r  = fpayh-doc1r
*         im_doc1t  = fpayh-doc1t
*         im_origin = fpayh-dorigin
*       EXCEPTIONS
*         not_found = 4.
* 
*     IF sy-subrc NE 0.
*       CALL FUNCTION 'FI_PAYM_MESSAGE_COLLECT'
*         EXPORTING
*           i_msgid = sy-msgid
*           i_msgty = sy-msgty
*           i_msgno = sy-msgno
*           i_msgv1 = sy-msgv1
*           i_msgv2 = sy-msgv2
*           i_msgv3 = sy-msgv3
*           i_msgv4 = sy-msgv4.
*       DATA: L_BADI_BATCH_PAYMED type ref to FPAYM_BATCH_PAYMENTS_MEDIUM.
*       TRY.
*         GET BADI L_BADI_BATCH_PAYMED.
*         CALL BADI L_BADI_BATCH_PAYMED->remove_batch_item    "nte1133478
*           EXPORTING
*             I_fpayh = fpayh.
*         CATCH cx_badi_not_implemented cx_badi_multiply_implemented.
*       ENDTRY.
*       REJECT.
*     ENDIF.
*   ENDIF.
*** <<< ZREPLAY-REMOVED

  CLEAR gt_fpayp.
  REFRESH gt_fpayp.

* Read processed items of the payment item
GET fpayp.
  APPEND fpayp TO gt_fpayp.
  PERFORM hr_remittance_acknowledgement USING fpayh fpayp.

* Call controller functions after reading the payment item with it
* processed items
GET fpayh LATE.
* Processing of first payment
  IF gc_xselect IS INITIAL.
    gc_xselect = 'X'.
    CALL FUNCTION 'FI_PAYM_MEDIUM_OPEN'
      EXPORTING
        is_fpayh              = fpayh
      TABLES
        t_fpayp               = gt_fpayp
      EXCEPTIONS
        cancel_payment_medium = 1
        OTHERS                = 2.

*   e.g. event 20 have raised an exception
    IF sy-subrc NE 0.
      MESSAGE ID sy-msgid TYPE 'S' NUMBER sy-msgno
            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
      EXIT.
    ENDIF.

*** ★★★ DEBUG ENTRY POINT — antes de invocar el motor DMEE ★★★
*** Estructuras visibles aquí (todas INTTAB, populadas por LDB FPMF):
***   fpayh    144 fields, header del pago actual
***   gt_fpayp internal table de items del header
***   par_form DMEE TREE_ID activo (e.g. /SEPA_CT_UNES)
*** F5 → step into FI_PAYM_MEDIUM_WRITE → motor DMEE
*** Para break en nodo X del árbol DMEE: SE24 USER-BP en
***   YCL_IDFI_CGI_DMEE_FALLBACK_CM001->GET_CREDIT
***   FI_PAYMEDIUM_DMEE_CGI_05  (Event 05 callback SAP std)
    BREAK-POINT.   "plain BP — no checkpoint group needed

    CALL FUNCTION 'FI_PAYM_MEDIUM_WRITE'
      EXPORTING
        is_fpayh = fpayh
        ix_first = 'X'
      TABLES
        it_fpayp = gt_fpayp.

* Processing of next payments
  ELSE.
    CALL FUNCTION 'FI_PAYM_MEDIUM_WRITE'
      EXPORTING
        is_fpayh = fpayh
        ix_first = space
      TABLES
        it_fpayp = gt_fpayp.
  ENDIF.
