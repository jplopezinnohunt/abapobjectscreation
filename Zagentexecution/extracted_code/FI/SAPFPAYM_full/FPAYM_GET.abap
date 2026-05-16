************************************************************************
* Include FPAYM_GET                                                    *
* Get Payment Data                                                     *
************************************************************************

* Read Payment item and initialize internal table of with the former
* payment item processed items
GET FPAYH.
  CHECK NOT FPAYH-RZAWE IS INITIAL.

  IF FPAYH-XVORL IS INITIAL AND NOT PAR_BELP IS INITIAL.
    CALL FUNCTION 'FI_REF_DOCUMENT_CHECK'   "payment document validation
      EXPORTING
        IM_DOC1R  = FPAYH-DOC1R
        IM_DOC1T  = FPAYH-DOC1T
        IM_ORIGIN = FPAYH-DORIGIN
      EXCEPTIONS
        NOT_FOUND = 4.

    IF SY-SUBRC NE 0.
      CALL FUNCTION 'FI_PAYM_MESSAGE_COLLECT'
        EXPORTING
          I_MSGID = SY-MSGID
          I_MSGTY = SY-MSGTY
          I_MSGNO = SY-MSGNO
          I_MSGV1 = SY-MSGV1
          I_MSGV2 = SY-MSGV2
          I_MSGV3 = SY-MSGV3
          I_MSGV4 = SY-MSGV4.
      DATA: L_BADI_BATCH_PAYMED TYPE REF TO FPAYM_BATCH_PAYMENTS_MEDIUM.
      TRY.
        GET BADI L_BADI_BATCH_PAYMED.
        CALL BADI L_BADI_BATCH_PAYMED->REMOVE_BATCH_ITEM    "nte1133478
          EXPORTING
            I_FPAYH = FPAYH.
        CATCH CX_BADI_NOT_IMPLEMENTED CX_BADI_MULTIPLY_IMPLEMENTED.
      ENDTRY.
      REJECT.
    ENDIF.
  ENDIF.

  CLEAR GT_FPAYP.
  REFRESH GT_FPAYP.

* Read processed items of the payment item
GET FPAYP.
  APPEND FPAYP TO GT_FPAYP.
  PERFORM HR_REMITTANCE_ACKNOWLEDGEMENT USING FPAYH FPAYP.

* Call controller functions after reading the payment item with it
* processed items
GET FPAYH LATE.
* Processing of first payment
  IF GC_XSELECT IS INITIAL.
    GC_XSELECT = 'X'.
    CALL FUNCTION 'FI_PAYM_MEDIUM_OPEN'
      EXPORTING
        IS_FPAYH              = FPAYH
      TABLES
        T_FPAYP               = GT_FPAYP
      EXCEPTIONS
        CANCEL_PAYMENT_MEDIUM = 1
        OTHERS                = 2.

*   e.g. event 20 have raised an exception
    IF SY-SUBRC NE 0.
      MESSAGE ID SY-MSGID TYPE 'S' NUMBER SY-MSGNO
            WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
      EXIT.
    ENDIF.
    CALL FUNCTION 'FI_PAYM_MEDIUM_WRITE'
      EXPORTING
        IS_FPAYH = FPAYH
        IX_FIRST = 'X'
      TABLES
        IT_FPAYP = GT_FPAYP.

* Processing of next payments
  ELSE.
    CALL FUNCTION 'FI_PAYM_MEDIUM_WRITE'
      EXPORTING
        IS_FPAYH = FPAYH
        IX_FIRST = SPACE
      TABLES
        IT_FPAYP = GT_FPAYP.
  ENDIF.