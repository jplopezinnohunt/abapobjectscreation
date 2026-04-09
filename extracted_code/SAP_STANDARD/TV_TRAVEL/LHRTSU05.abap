
FUNCTION ptrv_acc_employee_pay_post.
*"----------------------------------------------------------------------
*"*"Lokale Schnittstelle:
*"  IMPORTING
*"     VALUE(DOCUMENTHEADER) LIKE  BAPIACHE06 STRUCTURE  BAPIACHE06
*"     REFERENCE(I_EXIT) TYPE REF TO  IF_EX_TRIP_POST_FI
*"     REFERENCE(I_AWREF) TYPE  PTRV_DOC_HD-AWREF
*"     REFERENCE(I_AWORG) TYPE  PTRV_DOC_HD-AWORG
*"     REFERENCE(I_RUNID) TYPE  PEVSH-RUNID
*"  EXPORTING
*"     REFERENCE(RECEIVER) LIKE  BDBAPIDEST STRUCTURE  BDBAPIDEST
*"  TABLES
*"      ACCOUNTPAYABLE STRUCTURE  BAPIACAP06
*"      ACCOUNTGL STRUCTURE  BAPIACGL06
*"      ACCOUNTTAX STRUCTURE  BAPIACTX01
*"      CURRENCYAMOUNT STRUCTURE  BAPIACCR04
*"      RETURN STRUCTURE  BAPIRET2
*"      TRAVEL STRUCTURE  BAPIACTR00
*"      TRAVELAMOUNT STRUCTURE  BAPIACCRPO
*"      EXTENSION1 STRUCTURE  BAPIEXTC
*"      COMMUNICATION_DOCUMENTS STRUCTURE  SWOTOBJID OPTIONAL
*"  CHANGING
*"     REFERENCE(I_RUNID_STATUS) TYPE  PEVSH-STATUS
*"  EXCEPTIONS
*"      ERROR_IN_FILTEROBJECTS
*"      ERROR_IN_ALE_CUSTOMIZING
*"      NOT_UNIQUE_RECEIVER
*"      NO_RFC_DESTINATION_MAINTAINED
*"      ERROR_CREATING_IDOCS
*"----------------------------------------------------------------------

  DATA:
    unique_receiver      LIKE bdbapidest,
    receivers            LIKE bdi_logsys OCCURS 10 WITH HEADER LINE,
    filterobjects_values LIKE bdi_fobj OCCURS 10 WITH HEADER LINE.
  DATA: h_subrc TYPE sy-subrc.
  DATA: lv_rfc_message TYPE char255.
  DATA: ls_return TYPE bapiret2.
  DATA: lv_use_srfc TYPE xfeld.
  DATA: lv_awref TYPE sy-msgv1.
  DATA: lv_awsys TYPE sy-msgv1.
  DATA: lv_awtyp TYPE sy-msgv1.
  DATA: prev_status TYPE pevsh-status.

  prev_status = i_runid_status.

  CLEAR filterobjects_values. REFRESH filterobjects_values.
  filterobjects_values-objtype = 'COMP_CODE'.
  filterobjects_values-objvalue = documentheader-comp_code.
  APPEND filterobjects_values.

  CALL FUNCTION 'ALE_BAPI_GET_UNIQUE_RECEIVER'
    EXPORTING
      object                        = 'BUS6006'
      method                        = 'POST'
    IMPORTING
      receiver                      = unique_receiver
    TABLES
      filterobjects_values          = filterobjects_values
    EXCEPTIONS
      error_in_filterobjects        = 1
      error_in_ale_customizing      = 2
      not_unique_receiver           = 3
      no_rfc_destination_maintained = 4
      OTHERS                        = 5.

  CASE sy-subrc.
    WHEN 1.
      RAISE error_in_filterobjects.
    WHEN 2.
      RAISE error_in_ale_customizing.
    WHEN 3.
      RAISE not_unique_receiver.
    WHEN 4.
      RAISE no_rfc_destination_maintained.
  ENDCASE.

  receivers-logsys = unique_receiver-log_sys.
  APPEND receivers.

  IF NOT unique_receiver IS INITIAL AND i_exit IS BOUND.
    i_exit->determine_srfc( EXPORTING flt_val = documentheader-comp_code
                                      is_document_header = documentheader
                            CHANGING  c_srfc = lv_use_srfc ).

  ENDIF.

  IF NOT unique_receiver IS INITIAL AND lv_use_srfc IS INITIAL .
    receiver = unique_receiver.

    CALL FUNCTION 'ALE_ACC_EMPLOYEE_PAY_POST'
      EXPORTING
        documentheader          = documentheader
      TABLES
        accountpayable          = accountpayable
        accountgl               = accountgl
        accounttax              = accounttax
        currencyamount          = currencyamount
        travel                  = travel
        travelamount            = travelamount
        extension1              = extension1
        receivers               = receivers
        communication_documents = communication_documents
      EXCEPTIONS
        error_creating_idocs    = 1
        OTHERS                  = 2.

    IF sy-subrc <> 0.
      RAISE error_creating_idocs.
    ENDIF.

  ELSE.

    lv_awref = documentheader-obj_key.
    lv_awsys = documentheader-obj_sys.
    lv_awtyp = documentheader-obj_type.

    CALL FUNCTION 'BAPI_ACC_EMPLOYEE_PAY_POST' DESTINATION unique_receiver-rfc_dest
      EXPORTING
        documentheader        = documentheader
      TABLES
        accountpayable        = accountpayable
        accountgl             = accountgl
        accounttax            = accounttax
        currencyamount        = currencyamount
        return                = return
        travel                = travel
        travelamount          = travelamount
        extension1            = extension1
      EXCEPTIONS
        communication_failure = 1 MESSAGE lv_rfc_message
        system_failure        = 2 MESSAGE lv_rfc_message
        error_message         = 3
        OTHERS                = 4.

    h_subrc = sy-subrc.

    LOOP AT return WHERE
       type = 'A' OR
       type = 'E'.
    ENDLOOP.

    IF sy-subrc IS INITIAL OR h_subrc IS NOT INITIAL.

      IF h_subrc IS NOT INITIAL.
        REFRESH return.
      ENDIF.

      IF lines( return ) = 0.
        CALL FUNCTION 'BALW_BAPIRETURN_GET2'
          EXPORTING
            type   = 'E'
            cl     = 'RW'
            number = '609'
            par1   = lv_awtyp
            par2   = lv_awref
            par3   = lv_awsys
          IMPORTING
            return = ls_return.

        APPEND ls_return TO return.
        CLEAR ls_return.
      ENDIF.

      CASE h_subrc.
        WHEN 1 OR 2.

          CALL FUNCTION 'BALW_BAPIRETURN_GET2'
            EXPORTING
              type   = 'E'
              cl     = '56'
              number = '016'
              par1   = lv_rfc_message+0(50)
              par2   = lv_rfc_message+50(50)
              par3   = lv_rfc_message+100(50)
              par4   = lv_rfc_message+150(50)
            IMPORTING
              return = ls_return.

          APPEND ls_return TO return.
          CLEAR ls_return.

        WHEN 3 OR 4.

          CALL FUNCTION 'BALW_BAPIRETURN_GET2'
            EXPORTING
              type   = 'E'
              cl     = sy-msgid
              number = sy-msgno
              par1   = sy-msgv1
              par2   = sy-msgv2
              par3   = sy-msgv3
              par4   = sy-msgv4
            IMPORTING
              return = ls_return.

          APPEND ls_return TO return.
          CLEAR ls_return.

      ENDCASE.

    ELSE.

      IF i_runid_status NE '35'.
        CALL FUNCTION 'HR_EVAL_STATUS_SET'
          EXPORTING
            type   = 'TR'
            runid  = i_runid
            status = '35'      "teilweise gebucht
            lock   = space
            unlock = space.

        i_runid_status = '35'.
      ENDIF.

      PERFORM awref_commit USING i_awref i_aworg 'X' unique_receiver-log_sys. "GLW note 2252313

      CALL FUNCTION 'BAPI_TRANSACTION_COMMIT' DESTINATION unique_receiver-rfc_dest
        EXPORTING
          wait   = 'X'
        IMPORTING
          return = ls_return.

      IF ls_return-type = 'E'.

        IF prev_status NE '35' AND i_runid_status = '35'.   "GLW note 2252313
* status was set to partially posted right before: undo
          i_runid_status = prev_status.
          PERFORM run_status USING i_runid.
        ENDIF.

        PERFORM awref_commit USING i_awref i_aworg ' ' space. "GLW note 2252313

        REFRESH return.

        APPEND ls_return TO return.

        CALL FUNCTION 'BALW_BAPIRETURN_GET2'
          EXPORTING
            type   = 'E'
            cl     = 'RW'
            number = '609'
            par1   = lv_awtyp
            par2   = lv_awref
            par3   = lv_awsys
          IMPORTING
            return = ls_return.

        INSERT ls_return INTO return INDEX 1.
        CLEAR ls_return.
      ENDIF.

    ENDIF.

  ENDIF.

ENDFUNCTION.