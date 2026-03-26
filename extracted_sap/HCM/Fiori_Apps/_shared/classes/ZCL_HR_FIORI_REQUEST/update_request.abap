  METHOD update_request.

*    TRY.
*
*        DATA(ls_request) = is_request.
*        db_reqst_update( CHANGING cs_reqst = ls_request ).
*
*
*      CATCH zcx_hr_preq_symsg INTO DATA(lx).
*        CALL FUNCTION 'BAPI_TRANSACTION_ROLLBACK'.
*
*        CALL METHOD request_unlock( is_request-guid ).
*
*        RAISE EXCEPTION TYPE zcx_hr_exception
*          EXPORTING
*            textid       = zcx_hr_exception=>os_error
*            message_long = CONV #( lx->get_text( ) ).
*
*    ENDTRY.
*





*    IF is_request-action IS NOT INITIAL.
*      DATA(ls_timeline) = CORRESPONDING zthr_req_timel( is_request ).
*      CALL METHOD mo_db_handler->create_timeline(
*        EXPORTING
*          is_timeline = ls_timeline
*          iv_action   = is_request-action
*      ).
*    ENDIF.

  ENDMETHOD.
