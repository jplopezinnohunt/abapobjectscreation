METHOD infotype_get_entity.

  DATA ls_pskey TYPE hcmfab_s_pers_pskey.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA lt_messages TYPE bapirettab.
  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.
  DATA lt_ui_screens TYPE if_ex_hcmfab_persinfo_config=>ty_t_ui_screens.
  DATA lx_hcmfab_common TYPE REF TO cx_hcmfab_common.

  FIELD-SYMBOLS <ls_ui_screen> TYPE if_ex_hcmfab_persinfo_config=>ty_s_ui_screens.
  FIELD-SYMBOLS <lv_subty> TYPE subty.

  ls_pskey = get_pskey_from_key( io_tech_request_context->get_keys( ) ).

* ensure that content is only retrieved for own PERNR
  TRY.
      CALL METHOD go_employee_api->do_employeenumber_validation
        EXPORTING
          iv_pernr          = ls_pskey-hcmfab_pernr
          iv_application_id = iv_app_id.

      lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance( iv_pernr = ls_pskey-hcmfab_pernr iv_infty = ls_pskey-hcmfab_infty ).

      IF et_field_metadata IS SUPPLIED AND es_help_values IS SUPPLIED AND et_validity_info IS SUPPLIED.
        lo_feeder->get_entity(
           EXPORTING
             is_pskey           = ls_pskey
             iv_versionid       = iv_versionid
             it_fieldnames      = it_fieldnames
           IMPORTING
             es_entity_main     = es_entity
             et_field_metadata  = et_field_metadata
             es_help_values     = es_help_values
             et_validity_info   = et_validity_info
             et_messages        = lt_messages ).

      ELSEIF et_field_metadata IS SUPPLIED.
        lo_feeder->get_entity(
           EXPORTING
             is_pskey           = ls_pskey
             iv_versionid       = iv_versionid
             it_fieldnames      = it_fieldnames
           IMPORTING
             es_entity_main     = es_entity
             et_field_metadata  = et_field_metadata
             et_messages        = lt_messages ).

      ELSEIF es_help_values IS SUPPLIED.
        lo_feeder->get_entity(
           EXPORTING
             is_pskey           = ls_pskey
             iv_versionid       = iv_versionid
             it_fieldnames      = it_fieldnames
           IMPORTING
             es_entity_main     = es_entity
             es_help_values     = es_help_values
             et_messages        = lt_messages ).

      ELSEIF et_validity_info IS SUPPLIED.
        lo_feeder->get_entity(
           EXPORTING
             is_pskey           = ls_pskey
             iv_versionid       = iv_versionid
             it_fieldnames      = it_fieldnames
           IMPORTING
             es_entity_main     = es_entity
             et_validity_info   = et_validity_info
             et_messages        = lt_messages ).

      ELSE.
        lo_feeder->get_entity(
           EXPORTING
             is_pskey           = ls_pskey
             iv_versionid       = iv_versionid
             it_fieldnames      = it_fieldnames
           IMPORTING
             es_entity_main     = es_entity
             et_messages        = lt_messages ).

      ENDIF.

* message handling
      CALL METHOD cl_hcmfab_persinfo_dpc_util=>handle_messages
        EXPORTING
          io_context     = io_context
          iv_entity_name = io_tech_request_context->get_entity_type_name( )
          is_pskey       = ls_pskey                         "n2709841
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

      ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_subty OF STRUCTURE es_entity TO <lv_subty>.
      READ TABLE lt_ui_screens WITH KEY subtype = <lv_subty> ASSIGNING <ls_ui_screen>.
      IF NOT <ls_ui_screen> IS ASSIGNED.
        READ TABLE lt_ui_screens WITH KEY subtype = if_ex_hcmfab_persinfo_config=>gc_subtype_default ASSIGNING <ls_ui_screen>.
      ENDIF.
      IF <ls_ui_screen> IS ASSIGNED.
        MOVE-CORRESPONDING <ls_ui_screen> TO es_entity.
        UNASSIGN <ls_ui_screen>.                            "n2711669
      ENDIF.

    CATCH cx_hcmfab_common INTO lx_hcmfab_common.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_hcmfab_common )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
