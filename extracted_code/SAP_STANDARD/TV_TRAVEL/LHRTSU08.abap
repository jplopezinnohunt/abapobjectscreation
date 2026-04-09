
FUNCTION ptrv_acc_travel_post.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(DOCUMENTHEADER) TYPE  BAPIACHE04
*"     REFERENCE(I_AWREF) TYPE  PTRV_DOC_HD-AWREF
*"     REFERENCE(I_AWORG) TYPE  PTRV_DOC_HD-AWORG
*"     REFERENCE(I_RUNID) TYPE  PEVSH-RUNID
*"     REFERENCE(I_SIMULATION) TYPE  XFELD
*"     VALUE(ACCOUNTPAYABLE) TYPE  CL_FITV_POSTING_UTIL=>GTY_T_ACCPAY
*"     VALUE(ACCOUNTGL) TYPE  CL_FITV_POSTING_UTIL=>GTY_T_ACCGL
*"     VALUE(ACCOUNTTAX) TYPE  CL_FITV_POSTING_UTIL=>GTY_T_ACCTAX
*"     VALUE(TRAVEL) TYPE  PTRV_ACCMTRVL01_T
*"     VALUE(TRAVELAMOUNT) TYPE
*"CL_FITV_POSTING_UTIL=>GTY_T_TRAVELAMOUNT
*"     VALUE(EXTENSION1) TYPE  CL_FITV_POSTING_UTIL=>GTY_T_EXTENSION
*"     VALUE(CURRENCYAMOUNT) TYPE
*"CL_FITV_POSTING_UTIL=>GTY_T_CURRENCY
*"     VALUE(ACCOUNTRECEIVABLE) TYPE
*"CL_FITV_POSTING_UTIL=>GTY_T_ACCREC
*"  EXPORTING
*"     REFERENCE(RECEIVER) TYPE  BDBAPIDEST
*"     REFERENCE(RETURN) TYPE  BAPIRETTAB
*"  CHANGING
*"     REFERENCE(I_RUNID_STATUS) TYPE  PEVSH-STATUS
*"  EXCEPTIONS
*"      ERROR_IN_FILTEROBJECTS
*"      ERROR_IN_ALE_CUSTOMIZING
*"      NOT_UNIQUE_RECEIVER
*"      NO_RFC_DESTINATION_MAINTAINED
*"----------------------------------------------------------------------

  DATA:
    unique_receiver      TYPE bdbapidest,
    filterobjects_values TYPE TABLE OF bdi_fobj.
  FIELD-SYMBOLS <filterobjects_value> TYPE bdi_fobj.
  DATA: h_subrc TYPE sy-subrc.
  DATA: lv_rfc_message TYPE char255.
  FIELD-SYMBOLS: <ls_return> TYPE bapiret2.
  DATA: ls_return TYPE bapiret2.
  DATA: lv_awref TYPE sy-msgv1.
  DATA: lv_awsys TYPE sy-msgv1.
  DATA: lv_awtyp TYPE sy-msgv1.
  DATA: prev_status TYPE pevsh-status.
  CONSTANTS acc_travel_document_post TYPE string VALUE 'ACC_TRAVEL_DOCUMENT_POST'.
  TYPES: BEGIN OF ty_receiver_mem,
           bukrs TYPE bukrs,
           dest  TYPE bdbapidest,
         END OF ty_receiver_mem.
  STATICS lt_receiver_mem TYPE TABLE OF ty_receiver_mem.
  FIELD-SYMBOLS <receiver_mem> TYPE ty_receiver_mem.

  prev_status = i_runid_status.
  CLEAR: receiver, return.

  READ TABLE lt_receiver_mem WITH KEY
     bukrs = documentheader-comp_code ASSIGNING <receiver_mem>.

  CASE sy-subrc.

    WHEN 0.
      unique_receiver = <receiver_mem>-dest.
    WHEN OTHERS.

      APPEND INITIAL LINE TO lt_receiver_mem ASSIGNING <receiver_mem>.
      <receiver_mem>-bukrs = documentheader-comp_code.

      APPEND INITIAL LINE TO filterobjects_values ASSIGNING <filterobjects_value>.
      <filterobjects_value>-objtype = 'COMP_CODE'.
      <filterobjects_value>-objvalue = documentheader-comp_code.

      CALL FUNCTION 'ALE_BAPI_GET_UNIQUE_RECEIVER'
        EXPORTING
          object                        = 'BUS6004'
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
        WHEN 0.
        WHEN 1.
          RAISE error_in_filterobjects.
        WHEN 2.
          RAISE error_in_ale_customizing.
        WHEN 3.
          RAISE not_unique_receiver.
        WHEN 4.
          RAISE no_rfc_destination_maintained.
        WHEN OTHERS.
          RAISE not_unique_receiver.
      ENDCASE.

      IF unique_receiver-rfc_dest IS INITIAL.  "GLW note 2838499: add NONE, so that new fields can be added
        unique_receiver-rfc_dest = 'NONE'.
      ENDIF.

      <receiver_mem>-dest = unique_receiver.

  ENDCASE.

  lv_awref = documentheader-obj_key.
  lv_awsys = documentheader-obj_sys.
  lv_awtyp = documentheader-obj_type.

  IF unique_receiver-rfc_dest NE 'NONE'.  "GLW note 2838499
    receiver = unique_receiver.
  ENDIF.

  CALL FUNCTION acc_travel_document_post DESTINATION unique_receiver-rfc_dest
    EXPORTING
      documentheader        = documentheader
      simulation            = i_simulation
    TABLES
      accountpayable        = accountpayable
      accountgl             = accountgl
      accounttax            = accounttax
      accountreceivable     = accountreceivable
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

  LOOP AT return ASSIGNING <ls_return> WHERE
     type = 'A' OR
     type = 'E'.
    EXIT.
  ENDLOOP.

  IF sy-subrc IS INITIAL OR h_subrc IS NOT INITIAL.
* an error occurred: either an exception or in the return table!
    IF h_subrc IS NOT INITIAL.
      REFRESH return.
    ENDIF.

    IF lines( return ) = 0.
      APPEND INITIAL LINE TO return ASSIGNING <ls_return>.
      CALL FUNCTION 'BALW_BAPIRETURN_GET2'
        EXPORTING
          type   = 'E'
          cl     = 'RW'
          number = '609'
          par1   = lv_awtyp
          par2   = lv_awref
          par3   = lv_awsys
        IMPORTING
          return = <ls_return>.

    ENDIF.

    CASE h_subrc.
      WHEN 1 OR 2.

        APPEND INITIAL LINE TO return ASSIGNING <ls_return>.

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
            return = <ls_return>.

      WHEN 3 OR 4.
        APPEND INITIAL LINE TO return ASSIGNING <ls_return>.
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
            return = <ls_return>.

    ENDCASE.

  ELSE.
* no error occurred
    CASE i_simulation.
      WHEN space.
* productive mode
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
* the commit failed!
          IF prev_status NE '35' AND i_runid_status = '35'.   "GLW note 2252313
* status was set to partially posted right before: undo
            i_runid_status = prev_status.
            PERFORM run_status USING i_runid.
          ENDIF.

          PERFORM awref_commit USING i_awref i_aworg ' ' space. "GLW note 2252313

          REFRESH return.

          APPEND INITIAL LINE TO return ASSIGNING <ls_return>.
          CALL FUNCTION 'BALW_BAPIRETURN_GET2'
            EXPORTING
              type   = 'E'
              cl     = 'RW'
              number = '609'
              par1   = lv_awtyp
              par2   = lv_awref
              par3   = lv_awsys
            IMPORTING
              return = <ls_return>.

          APPEND ls_return TO return.

        ENDIF.
      WHEN OTHERS.
* check mode
        IF NOT ( unique_receiver-rfc_dest IS INITIAL ).
          READ TABLE travel INDEX 1 TRANSPORTING NO FIELDS.
          IF sy-subrc EQ 0.
            CALL FUNCTION 'BAPI_TRANSACTION_ROLLBACK'
              DESTINATION unique_receiver-rfc_dest.
          ENDIF.
        ENDIF.
    ENDCASE.
  ENDIF.

ENDFUNCTION.