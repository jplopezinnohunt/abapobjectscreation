METHOD infotype_default_get_entityset.

  DATA ls_filter TYPE /iwbep/s_mgw_select_option.
  DATA ls_select TYPE /iwbep/s_cod_select_option.
  DATA lt_filter_select_options TYPE /iwbep/t_mgw_select_option.
  DATA lo_filter TYPE REF TO /iwbep/if_mgw_req_filter.
  DATA lv_pernr TYPE pernr_d.
  DATA lv_subty TYPE subty.
  DATA lv_country_versionid TYPE hcmfab_versionid.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA lr_entity TYPE REF TO data.
  DATA lv_main_record_type TYPE abap_abstypename.
  DATA lt_messages TYPE bapirettab.
  DATA lr_default_entity TYPE REF TO data.
  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.
  DATA lt_ui_screens TYPE if_ex_hcmfab_persinfo_config=>ty_t_ui_screens.
  DATA lt_valuehelp_fields TYPE hcmfab_t_pers_fieldname.
  DATA lx_hcmfab_common TYPE REF TO cx_hcmfab_common.
  DATA lv_country TYPE land1.                               "2709841

  FIELD-SYMBOLS <ls_ui_screen> TYPE if_ex_hcmfab_persinfo_config=>ty_s_ui_screens.
  FIELD-SYMBOLS <lv_subty> TYPE subty.
  FIELD-SYMBOLS <ls_default_entity> TYPE any.

* get subtype and pernr from filter
  lo_filter = io_tech_request_context->get_filter( ).
  lt_filter_select_options = lo_filter->get_filter_select_options( ).

  LOOP AT lt_filter_select_options INTO ls_filter.
    READ TABLE ls_filter-select_options INTO ls_select INDEX 1 TRANSPORTING low.
    CASE ls_filter-property.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_pernr.
        lv_pernr = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_subty.
        lv_subty = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-itbld.
        lv_country_versionid = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-land1.       "2709841
        lv_country = ls_select-low.
    ENDCASE.
  ENDLOOP.

* ensure that content is only retrieved for own PERNR
  TRY.
      CALL METHOD go_employee_api->do_employeenumber_validation
        EXPORTING
          iv_pernr          = lv_pernr
          iv_application_id = iv_app_id.

      lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance( iv_pernr = lv_pernr iv_infty = iv_infty ).

      CREATE DATA lr_default_entity LIKE LINE OF et_entityset.
      ASSIGN lr_default_entity->* TO <ls_default_entity>.

      APPEND LINES OF it_fieldnames TO lt_valuehelp_fields.

      IF et_field_metadata IS SUPPLIED AND et_help_values IS SUPPLIED AND et_validity_info IS SUPPLIED.
        lo_feeder->get_default_entity(
         EXPORTING
           iv_subty             = lv_subty
           iv_versionid         = iv_versionid
           iv_country_versionid = lv_country_versionid
           iv_country           = lv_country                "2709841
           it_fieldnames        = lt_valuehelp_fields
         IMPORTING
           es_default_entity    = <ls_default_entity>
           et_field_metadata    = et_field_metadata
           et_help_values       = et_help_values
           et_validity_info     = et_validity_info
           et_messages          = lt_messages ).

      ELSEIF et_field_metadata IS SUPPLIED.
        lo_feeder->get_default_entity(
         EXPORTING
           iv_subty             = lv_subty
           iv_versionid         = iv_versionid
           iv_country_versionid = lv_country_versionid
           iv_country           = lv_country                "2709841
*       it_fieldnames      = lt_valuehelp_fields
         IMPORTING
           es_default_entity    = <ls_default_entity>
           et_field_metadata    = et_field_metadata
           et_messages          = lt_messages ).

      ELSEIF et_help_values IS SUPPLIED.
        lo_feeder->get_default_entity(
         EXPORTING
           iv_subty             = lv_subty
           iv_versionid         = iv_versionid
           iv_country_versionid = lv_country_versionid
           iv_country           = lv_country                "2709841
           it_fieldnames        = lt_valuehelp_fields
         IMPORTING
           es_default_entity    = <ls_default_entity>
           et_help_values       = et_help_values
           et_messages          = lt_messages ).

      ELSEIF et_validity_info IS SUPPLIED.
        lo_feeder->get_default_entity(
         EXPORTING
           iv_subty             = lv_subty
           iv_versionid         = iv_versionid
           iv_country_versionid = lv_country_versionid
           iv_country           = lv_country                "2709841
*       it_fieldnames      = lt_valuehelp_fields
         IMPORTING
           es_default_entity    = <ls_default_entity>
           et_validity_info     = et_validity_info
           et_messages          = lt_messages ).

      ELSE.
        lo_feeder->get_default_entity(
         EXPORTING
           iv_subty             = lv_subty
           iv_versionid         = iv_versionid
           iv_country_versionid = lv_country_versionid
           iv_country           = lv_country                "2709841
*       it_fieldnames      = lt_valuehelp_fields
         IMPORTING
           es_default_entity    = <ls_default_entity>
           et_messages          = lt_messages ).

      ENDIF.

* call BAdI
      GET BADI lo_persinfo_config_badi
        FILTERS
          versionid = iv_versionid.

      CALL BADI lo_persinfo_config_badi->get_screen_versions
        EXPORTING
          iv_app_id     = iv_app_id
        CHANGING
          ct_ui_screens = lt_ui_screens.

      ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_subty OF STRUCTURE <ls_default_entity> TO <lv_subty>.
      READ TABLE lt_ui_screens WITH KEY subtype = <lv_subty> ASSIGNING <ls_ui_screen>.
      IF NOT <ls_ui_screen> IS ASSIGNED.
        READ TABLE lt_ui_screens WITH KEY subtype = if_ex_hcmfab_persinfo_config=>gc_subtype_default ASSIGNING <ls_ui_screen>.
      ENDIF.
      IF <ls_ui_screen> IS ASSIGNED.
        MOVE-CORRESPONDING <ls_ui_screen> TO <ls_default_entity>.
      ENDIF.

      IF NOT <ls_default_entity> IS INITIAL.
        APPEND <ls_default_entity> TO et_entityset.
      ENDIF.

* message handling
* we don't return business messages on reading the default values
*      CALL METHOD cl_hcmfab_persinfo_dpc_util=>handle_messages
*        EXPORTING
*          io_context     = io_context
*          iv_entity_name = io_tech_request_context->get_entity_type_name( )
*          it_messages    = lt_messages.

    CATCH cx_hcmfab_common INTO lx_hcmfab_common.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_hcmfab_common )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
