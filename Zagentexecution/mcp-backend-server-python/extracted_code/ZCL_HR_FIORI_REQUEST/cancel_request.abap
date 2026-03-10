  METHOD cancel_request.

    "If request is in Draft, delete from db otherwise Cancel

    "Get request*
    TRY.
        me->get_request(
          EXPORTING
            iv_request_guid =      iv_request_guid             " Globally Unique Identifier
          IMPORTING
            es_result       =  DATA(ls_request)
        ).
      CATCH zcx_hr_benef_exception. " Exception class for Benefits
    ENDTRY.

    IF ls_request-request_status EQ '00'. "DRAFT
      DELETE FROM zthrfiori_breq WHERE guid EQ @iv_request_guid.
      IF ls_request-request_type   EQ zcl_hr_fiori_request=>c_request_type_eg.
        DELETE FROM zthrfiori_eg_mai WHERE guid EQ @iv_request_guid.
      ENDIF.
      IF ls_request-request_type   EQ zcl_hr_fiori_request=>c_request_type_rs.
        DELETE FROM zthrfiori_rs_mai WHERE guid EQ @iv_request_guid.
      ENDIF.
    ELSE.

      UPDATE zthrfiori_breq SET flag_deleted = @abap_true
                WHERE guid EQ @iv_request_guid.

    ENDIF.


*    TRY.


*      CATCH zcx_hr_preq_symsg INTO DATA(lx).
*        RAISE EXCEPTION TYPE zcx_hr_exception
*          EXPORTING
*            textid       = zcx_hr_exception=>os_error
*            message_long = CONV #( lx->get_text( ) ).
*    ENDTRY.

  ENDMETHOD.
