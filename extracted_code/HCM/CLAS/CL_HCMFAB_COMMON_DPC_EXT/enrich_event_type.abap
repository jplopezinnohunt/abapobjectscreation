METHOD enrich_event_type.

  DATA: lx_badi_error TYPE REF TO cx_hcmfab_badi_error,
        ls_return     TYPE bapiret2.

  IF go_badi_tcal_extension IS INITIAL.
    RETURN.
  ENDIF.

  TRY.
*     call the extension BADI to add custom entity data
      CALL BADI go_badi_tcal_extension->enrich_event_type
        CHANGING
          cs_event_type = cs_event_type.

    CATCH cx_hcmfab_badi_error INTO lx_badi_error.
      "log the error
      ls_return = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_badi_error ).
      me->mo_context->get_logger( )->log_message(
          iv_msg_type      = ls_return-type
          iv_msg_id        = ls_return-id
          iv_msg_number    = ls_return-number
          iv_msg_v1        = ls_return-message_v1
          iv_msg_v2        = ls_return-message_v2
          iv_msg_v3        = ls_return-message_v3
          iv_msg_v4        = ls_return-message_v4
          iv_agent         = 'LOGGER'
      ).

  ENDTRY.

ENDMETHOD.
