METHOD infotype_get_entityset.

  DATA lv_pernr TYPE pernr_d.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.
  DATA lt_ui_screens TYPE if_ex_hcmfab_persinfo_config=>ty_t_ui_screens.
  DATA lt_source_keys TYPE /iwbep/t_mgw_tech_pairs.
  DATA lv_subty TYPE subty.
  DATA lt_messages TYPE bapirettab.
  DATA lx_hcmfab_common TYPE REF TO cx_hcmfab_common.

  FIELD-SYMBOLS <ls_ui_screen> TYPE if_ex_hcmfab_persinfo_config=>ty_s_ui_screens.
  FIELD-SYMBOLS <lv_subty> TYPE subty.
  FIELD-SYMBOLS <ls_entity> TYPE any.

  lt_source_keys = io_tech_request_context->get_source_keys( ).

  IF lt_source_keys IS NOT INITIAL.
    lv_pernr = cl_hcmfab_persinfo_dpc_util=>get_pskey_from_key( lt_source_keys )-hcmfab_pernr.
    lv_subty = cl_hcmfab_persinfo_dpc_util=>get_pskey_from_key( lt_source_keys )-hcmfab_subty.
  ELSE.
    lv_pernr = cl_hcmfab_persinfo_dpc_util=>get_pernr_from_filter(
        io_tech_request_context  = io_tech_request_context ).
    lv_subty = cl_hcmfab_persinfo_dpc_util=>get_pskey_from_filter(
        io_tech_request_context  = io_tech_request_context )-hcmfab_subty.
  ENDIF.

* ensure that content is only retrieved for own PERNR
  TRY.
      CALL METHOD go_employee_api->do_employeenumber_validation
        EXPORTING
          iv_pernr          = lv_pernr
          iv_application_id = iv_app_id.

      lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance( iv_pernr = lv_pernr iv_infty = iv_infty ).

      IF et_field_metadata IS SUPPLIED AND et_help_values IS SUPPLIED  AND et_validity_info IS SUPPLIED.
        lo_feeder->get_entity_set(
         EXPORTING
           iv_versionid       = iv_versionid
           it_fieldnames      = it_fieldnames
         IMPORTING
           et_entity_set_main = et_entityset
           et_field_metadata  = et_field_metadata
           et_help_values     = et_help_values
           et_validity_info   = et_validity_info
           et_messages        = lt_messages ).

      ELSEIF et_field_metadata IS SUPPLIED.
        lo_feeder->get_entity_set(
         EXPORTING
           iv_versionid       = iv_versionid
           it_fieldnames      = it_fieldnames
         IMPORTING
           et_entity_set_main = et_entityset
           et_field_metadata  = et_field_metadata
           et_messages        = lt_messages ).

      ELSEIF et_help_values IS SUPPLIED AND NOT it_fieldnames IS INITIAL.
        lo_feeder->get_entity_set(
         EXPORTING
           iv_versionid       = iv_versionid
           it_fieldnames      = it_fieldnames
         IMPORTING
           et_entity_set_main = et_entityset
           et_help_values     = et_help_values
           et_messages        = lt_messages ).

      ELSEIF et_validity_info IS SUPPLIED.
        lo_feeder->get_entity_set(
         EXPORTING
           iv_versionid       = iv_versionid
           it_fieldnames      = it_fieldnames
         IMPORTING
           et_entity_set_main = et_entityset
           et_validity_info  = et_validity_info
           et_messages        = lt_messages ).

      ELSE.
        lo_feeder->get_entity_set(
         EXPORTING
           iv_versionid       = iv_versionid
           it_fieldnames      = it_fieldnames
         IMPORTING
           et_entity_set_main = et_entityset
           et_messages        = lt_messages ).

      ENDIF.

* message handling
      CALL METHOD cl_hcmfab_persinfo_dpc_util=>handle_messages
        EXPORTING
          io_context     = io_context
          iv_entity_name = io_tech_request_context->get_entity_type_name( )
          it_messages    = lt_messages.

* call BAdI to add UI screen versions
      GET BADI lo_persinfo_config_badi
        FILTERS
          versionid = iv_versionid.

      CALL BADI lo_persinfo_config_badi->get_screen_versions
        EXPORTING
          iv_app_id     = iv_app_id
        CHANGING
          ct_ui_screens = lt_ui_screens.


      LOOP AT et_entityset ASSIGNING <ls_entity>.
        ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_subty OF STRUCTURE <ls_entity> TO <lv_subty>.
        READ TABLE lt_ui_screens WITH KEY subtype = <lv_subty> ASSIGNING <ls_ui_screen>.
        IF NOT <ls_ui_screen> IS ASSIGNED.
          READ TABLE lt_ui_screens WITH KEY subtype = if_ex_hcmfab_persinfo_config=>gc_subtype_default ASSIGNING <ls_ui_screen>.
        ENDIF.
        IF <ls_ui_screen> IS ASSIGNED.
          MOVE-CORRESPONDING <ls_ui_screen> TO <ls_entity>.
          UNASSIGN <ls_ui_screen>.                          "n2711669
        ENDIF.
      ENDLOOP.

    CATCH cx_hcmfab_common INTO lx_hcmfab_common.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_hcmfab_common )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
