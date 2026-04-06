METHOD teamcalendarview_get_entity.
  DATA: lv_application_id TYPE hcmfab_application_id,
          lv_instance_id TYPE hcmfab_tcal_instance_id,
          lv_employee_assignment TYPE pernr_d,
          lv_view_type TYPE hcmfab_view_type,
          lv_view_id TYPE hcmfab_view_id,
          lt_key_tab TYPE /iwbep/t_mgw_tech_pairs,
          ls_tech_key TYPE /iwbep/s_mgw_tech_pair,
          lt_views TYPE hcmfab_t_tcal_view,
          ls_view TYPE hcmfab_s_tcal_view,
          lx_exception TYPE REF TO cx_static_check,
          lv_default_view_pers_mode TYPE hcmfab_tcal_view_pers_mode.

  CLEAR: er_entity, es_response_context.

  lt_key_tab = io_tech_request_context->get_keys( ).
  LOOP AT lt_key_tab INTO ls_tech_key.
    CASE ls_tech_key-name.
      WHEN 'APPLICATION_ID'.
        lv_application_id = ls_tech_key-value.
      WHEN 'EMPLOYEE_ASSIGNMENT'.
        lv_employee_assignment = ls_tech_key-value.
      WHEN 'VIEW_TYPE'.
        lv_view_type = ls_tech_key-value.
      WHEN 'VIEW_ID'.
        lv_view_id = ls_tech_key-value.
      WHEN 'INSTANCE_ID'.
        lv_instance_id = ls_tech_key-value.
    ENDCASE.
  ENDLOOP.

  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation(
        iv_pernr          = lv_employee_assignment
        iv_application_id = lv_application_id ).

*     copy key fields
      er_entity-application_id = lv_application_id.
      er_entity-instance_id = lv_instance_id.
      er_entity-employee_assignment = lv_employee_assignment.
      er_entity-view_id = lv_view_id.
      er_entity-view_type = lv_view_type.

*     get the default view personalization mode
      CALL BADI go_badi_tcal_settings->get_ui_settings
        EXPORTING
          iv_application_id         = lv_application_id
          iv_instance_id            = lv_instance_id
          iv_employee_assignment    = lv_employee_assignment
        IMPORTING
          ev_default_view_pers_mode = lv_default_view_pers_mode.
      IF lv_default_view_pers_mode IS INITIAL.
        lv_default_view_pers_mode = if_hcmfab_tcal_constants=>gc_view_pers_mode-full.
      ENDIF.

*     read description and personalization mode
      IF lv_view_type = if_hcmfab_constants=>gc_viewtype-custom.
*       custom view read title from personalization db
        SELECT SINGLE description sequence_number FROM hcmfab_d_tcalcvw INTO (er_entity-description, er_entity-sequence_number )
          WHERE application_id = lv_application_id AND instance_id = lv_instance_id AND emp_assignment = lv_employee_assignment AND view_id = lv_view_id.
        er_entity-personalization_mode = lv_default_view_pers_mode.
      ELSE.
*       standard view read description from settings BADI
        CALL BADI go_badi_tcal_settings->get_views
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = lv_employee_assignment
          IMPORTING
            et_views               = lt_views.
        READ TABLE lt_views INTO ls_view WITH KEY view_type = lv_view_type view_id = lv_view_id.
        er_entity-description = ls_view-description.
        er_entity-personalization_mode = ls_view-personalization_mode.
        IF er_entity-personalization_mode IS INITIAL.
          er_entity-personalization_mode = lv_default_view_pers_mode.
        ENDIF.
      ENDIF.

*     call extension BADI for view
      me->enrich_view(
        CHANGING
          cs_view = er_entity
      ).

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.
ENDMETHOD.
