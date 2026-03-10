METHOD enrich_expanded_entityset.

  DATA lx_badi TYPE REF TO cx_badi.
  DATA ls_return TYPE bapiret2.
  DATA lr_source_entity TYPE REF TO data.
  DATA lo_badi TYPE REF TO cl_badi_base.
  DATA lt_badi_impl TYPE enh_badi_impl_head_it.
*
  FIELD-SYMBOLS <lt_entity> TYPE STANDARD TABLE.
  FIELD-SYMBOLS <ls_entity> TYPE any.
  FIELD-SYMBOLS <ls_source_entity> TYPE any.


  IF NOT iv_entity_name CP iv_entity_pattern.               "2656876
* we only support extensions to main and default entities
    RETURN.
  ENDIF.

  lt_badi_impl = cl_enh_badi_runtime_functions=>get_active_impls_4_badi( badi_name = iv_badi_name ).
  IF NOT lt_badi_impl IS INITIAL.

    TRY.
        GET BADI lo_badi TYPE (iv_badi_name).
        IF NOT lo_badi IS INITIAL AND NOT io_expand IS INITIAL.

          CREATE DATA lr_source_entity TYPE (iv_entity_structure).
          ASSIGN lr_source_entity->* TO <ls_source_entity>.

          ASSIGN cr_entityset->* TO <lt_entity>.

          LOOP AT <lt_entity> ASSIGNING <ls_entity>.
* enrich source entity
            MOVE-CORRESPONDING <ls_entity> TO <ls_source_entity>.

            IF <ls_source_entity> IS ASSIGNED.
              enrich_entity(
                EXPORTING
                   iv_entity_name    = iv_entity_name
                   iv_entity_pattern = iv_entity_pattern
                   iv_badi_name      = iv_badi_name
                   io_context        = io_context
                 CHANGING
                   cr_entity         = lr_source_entity ).
            ENDIF.

            MOVE-CORRESPONDING <ls_source_entity> TO <ls_entity>. "2656876
          ENDLOOP.
        ENDIF.

      CATCH cx_badi INTO lx_badi.
        "log the error
        ls_return = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_badi ).
        io_context->get_logger( )->log_message(
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
  ENDIF.

ENDMETHOD.
