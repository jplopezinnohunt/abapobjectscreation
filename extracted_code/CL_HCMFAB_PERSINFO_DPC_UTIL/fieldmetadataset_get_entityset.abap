METHOD fieldmetadataset_get_entityset.

  DATA ls_pskey TYPE hcmfab_s_pers_pskey.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA lt_messages TYPE bapirettab.
  DATA lo_message_container TYPE REF TO /iwbep/if_message_container.

  ls_pskey = cl_hcmfab_persinfo_dpc_util=>get_pskey_from_filter(
      io_tech_request_context  = io_tech_request_context ).

  lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance(
      iv_pernr      = ls_pskey-hcmfab_pernr
      iv_infty      = ls_pskey-hcmfab_infty ).

  lo_feeder->get_field_metadata(
    EXPORTING
      is_pskey          = ls_pskey
    IMPORTING
      et_field_metadata = et_entityset
      et_messages       = lt_messages ).

* message handling
  IF lt_messages IS NOT INITIAL.
    DELETE lt_messages WHERE type <> 'E'.
    IF lt_messages IS NOT INITIAL.
      lo_message_container = io_context->get_message_container( ).
      lo_message_container->add_messages_from_bapi(
        it_bapi_messages         = lt_messages
        iv_determine_leading_msg = /iwbep/if_message_container=>gcs_leading_msg_search_option-last
        iv_entity_type           = iv_entity_name
      ).

      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
        EXPORTING
          message_container = lo_message_container.
    ENDIF.
  ENDIF.

ENDMETHOD.
