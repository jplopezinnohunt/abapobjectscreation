METHOD enrich_entityset.

  DATA lv_methodname TYPE seocpdname.
  DATA lx_badi TYPE REF TO cx_badi.
  DATA lx_illegal_method TYPE REF TO cx_sy_dyn_call_illegal_method. "2656876
  DATA ls_return TYPE bapiret2.
  DATA ptab TYPE abap_parmbind_tab.
  DATA ptab_line TYPE abap_parmbind.
  DATA lo_badi TYPE REF TO cl_badi_base.
  DATA lt_badi_impl TYPE enh_badi_impl_head_it.

  IF NOT iv_entity_name CP iv_entity_pattern.               "2656876
    RETURN.
  ENDIF.
* we only support extensions to main and default entities

  lt_badi_impl = cl_enh_badi_runtime_functions=>get_active_impls_4_badi( badi_name = iv_badi_name ).
  IF NOT lt_badi_impl IS INITIAL.

    TRY.
        GET BADI lo_badi TYPE (iv_badi_name).
        IF NOT lo_badi IS INITIAL.

          CONCATENATE 'ENRICH_' iv_entity_name INTO lv_methodname.
          TRANSLATE lv_methodname TO UPPER CASE.
          CONCATENATE 'CT_' iv_entity_name INTO ptab_line-name.
          TRANSLATE ptab_line-name TO UPPER CASE.
          ptab_line-kind = cl_abap_objectdescr=>changing.
          ptab_line-value = cr_entityset.
          INSERT ptab_line INTO TABLE ptab.

          CALL BADI lo_badi->(lv_methodname)
            PARAMETER-TABLE ptab.
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

      CATCH cx_sy_dyn_call_illegal_method INTO lx_illegal_method. "2656876
        "log the error
        ls_return = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_illegal_method ).
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
