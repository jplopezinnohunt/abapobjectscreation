METHOD SUBTYPEATTRIBUTE_GET_ENTITYSET.

  DATA lv_pernr TYPE pernr_d.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA lt_messages TYPE bapirettab.
  DATA lo_message_container TYPE REF TO /iwbep/if_message_container.

  lv_pernr = cl_hcmfab_persinfo_dpc_util=>get_pernr_from_filter(
      io_tech_request_context  = io_tech_request_context ).

  lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance(
      iv_pernr      = lv_pernr
      iv_infty      = iv_infty ).

  lo_feeder->get_subtype_attributes( IMPORTING et_subtype_attributes = et_entityset ).

ENDMETHOD.
