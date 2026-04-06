METHOD enrich_corequisite.
  DATA: lx_badi_error TYPE REF TO cx_hcmfab_badi_error,
    ls_return     TYPE bapiret2.

  IF gb_hcmfab_ben_enroll_enrich IS INITIAL.
    RETURN.
  ENDIF.
*
  TRY.
      CALL BADI gb_hcmfab_ben_enroll_enrich->enrich_corequisite
        CHANGING
          cs_coreqisite_entity = coreqisiteentity.

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

      RAISE EXCEPTION TYPE cx_hcmfab_benefits_enrollment
        EXPORTING
          textid = cx_hcmfab_benefits_enrollment=>benenroll_enrichment_error.
  ENDTRY.

ENDMETHOD.
