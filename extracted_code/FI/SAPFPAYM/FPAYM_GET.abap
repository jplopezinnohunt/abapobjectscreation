************************************************************************
* Include FPAYM_GET                                                    *
* Get Payment Data                                                     *
************************************************************************

* Read Payment item and initialize internal table of with the former
* payment item processed items
GET fpayh.
  CHECK NOT fpayh-rzawe IS INITIAL.

  IF fpayh-xvorl IS INITIAL AND NOT par_belp IS INITIAL.
    CALL FUNCTION 'FI_REF_DOCUMENT_CHECK'   "payment document validation
      EXPORTING
        im_doc1r  = fpayh-doc1r
        im_doc1t  = fpayh-doc1t
        im_origin = fpayh-dorigin
      EXCEPTIONS
        not_found = 4.

    IF sy-subrc NE 0.
      CALL FUNCTION 'FI_PAYM_MESSAGE_COLLECT'
        EXPORTING
          i_msgid = sy-msgid
          i_msgty = sy-msgty
          i_msgno = sy-msgno
          i_msgv1 = sy-msgv1
          i_msgv2 = sy-msgv2
          i_msgv3 = sy-msgv3
          i_msgv4 = sy-msgv4.
      DATA: L_BADI_BATCH_PAYMED type ref to FPAYM_BATCH_PAYMENTS_MEDIUM.
      TRY.
        GET BADI L_BADI_BATCH_PAYMED.
        CALL BADI L_BADI_BATCH_PAYMED->remove_batch_item    "nte1133478
          EXPORTING
            I_fpayh = fpayh.
        CATCH cx_badi_not_implemented cx_badi_multiply_implemented.
      ENDTRY.
      REJECT.
    ENDIF.
  ENDIF.

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