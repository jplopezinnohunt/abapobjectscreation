METHOD get_tcal_ui_settings.

  DATA:ls_key                  TYPE /iwbep/s_mgw_name_value_pair,
       lx_exception            TYPE REF TO cx_static_check,
       ls_periods              TYPE hcmfab_s_tcal_periods,
       lv_periods_str(6)       TYPE c,
       lt_attributes           TYPE if_hcmfab_tcal_settings=>ty_t_attribute,
       ls_attribute            TYPE if_hcmfab_tcal_settings=>ty_s_attribute,
       lt_attribute_groups     TYPE if_hcmfab_tcal_settings=>ty_t_attribute_group,
       ls_attribute_group      TYPE if_hcmfab_tcal_settings=>ty_s_attribute_group.

  CLEAR: es_ui_settings.

  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation(
        iv_pernr          = iv_employee_assignment
        iv_application_id = iv_application_id ).

*     read the UI settings
      es_ui_settings-application_id = iv_application_id.
      es_ui_settings-instance_id = iv_instance_id.
      es_ui_settings-employee_assignment = iv_employee_assignment.
      CALL BADI go_badi_tcal_settings->get_ui_settings
        EXPORTING
          iv_application_id       = iv_application_id
          iv_instance_id          = iv_instance_id
          iv_employee_assignment  = iv_employee_assignment
        IMPORTING
          ev_show_employee_photo  = es_ui_settings-show_employee_photo
          ev_show_filter          = es_ui_settings-show_filter
          ev_show_search          = es_ui_settings-show_search
          ev_show_ce_button       = es_ui_settings-show_ce_button
          ev_show_legend          = es_ui_settings-show_legend
*         ev_personalization_mode = er_entity-personalization_mode
          ev_default_filter_mode  = es_ui_settings-default_filter_mode
          ev_show_excel_download  = es_ui_settings-show_excel_download.

      es_ui_settings-personalization_mode = me->get_tcal_personalization_mode(
          iv_application_id       = iv_application_id
          iv_instance_id          = iv_instance_id
          iv_employee_assignment  = iv_employee_assignment
      ).

*     call BADI method to get the periods
      CALL BADI go_badi_tcal_settings->get_periods
        EXPORTING
          iv_application_id      = iv_application_id
          iv_instance_id         = iv_instance_id
          iv_employee_assignment = iv_employee_assignment
        IMPORTING
          es_periods             = ls_periods.
*     map the periods into string.
      WRITE ls_periods TO lv_periods_str.
      es_ui_settings-periods = lv_periods_str.

*     call BADI to get the employee detail attributes
      CALL BADI go_badi_tcal_settings->get_employee_detail_attributes
        EXPORTING
          iv_application_id      = iv_application_id
          iv_instance_id         = iv_instance_id
          iv_employee_assignment = iv_employee_assignment
        IMPORTING
          et_attribute_groups    = lt_attribute_groups
          et_attributes          = lt_attributes.
*     attributes without group assignment first
      LOOP AT lt_attributes INTO ls_attribute WHERE group_id IS INITIAL.
        IF es_ui_settings-employee_detail_attributes IS INITIAL.
          es_ui_settings-employee_detail_attributes = ls_attribute-id.
        ELSE.
          CONCATENATE es_ui_settings-employee_detail_attributes ',' ls_attribute-id INTO es_ui_settings-employee_detail_attributes.
        ENDIF.
      ENDLOOP.
*     add the attribute groups and attributes
      LOOP AT lt_attribute_groups INTO ls_attribute_group.
        IF es_ui_settings-employee_detail_attributes IS INITIAL.
          CONCATENATE '{' ls_attribute_group-title '}' INTO es_ui_settings-employee_detail_attributes.
        ELSE.
          CONCATENATE es_ui_settings-employee_detail_attributes ',{' ls_attribute_group-title '}' INTO es_ui_settings-employee_detail_attributes.
        ENDIF.
        LOOP AT lt_attributes INTO ls_attribute WHERE group_id = ls_attribute_group-id.
          CONCATENATE es_ui_settings-employee_detail_attributes ',' ls_attribute-id INTO es_ui_settings-employee_detail_attributes.
        ENDLOOP.
      ENDLOOP.

*     call BADI to get the approval settings
      CALL BADI go_badi_tcal_settings->get_approval_settings
        IMPORTING
          ev_approval_mode      = es_ui_settings-approval_mode
          ev_default_share_mode = es_ui_settings-default_share_mode.

*     call the extensio BADI for UI settings
      me->enrich_ui_settings(
        CHANGING
          cs_ui_settings = es_ui_settings
      ).

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = 'TeamcalendarUISettings' "#EC_NOTEXT
      ).
  ENDTRY.

ENDMETHOD.
