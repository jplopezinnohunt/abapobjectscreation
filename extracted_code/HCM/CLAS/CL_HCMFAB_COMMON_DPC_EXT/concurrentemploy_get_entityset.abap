METHOD concurrentemploy_get_entityset.

  DATA: lo_person_info_reader     TYPE REF TO if_hrcce_person_info_reader,
        lt_filter_select_options  TYPE /iwbep/t_mgw_select_option,
        ls_filter_select_option   TYPE /iwbep/s_mgw_select_option,
        ls_filter                 TYPE /iwbep/s_cod_select_option,
        lv_default_pernr          TYPE pernr_d,
        lt_pernrs                 TYPE pccet_pernr,
        lv_pernr                  TYPE pernr_d,
        lv_hide_pic               TYPE boole_d,
        lv_hide_number            TYPE boole_d,
        lv_hide_button            TYPE boole_d,
        lv_application_id         TYPE hcmfab_application_id,
        lx_exception              TYPE REF TO cx_static_check,
        ls_entity                 TYPE cl_hcmfab_common_mpc=>ts_concurrentemployment,
        lv_hide_inactive          TYPE boole_d,
        lv_hide_withdrawn         TYPE boole_d,
        lv_hide_retiree           TYPE boole_d.


  CLEAR: et_entityset, es_response_context.

  me->set_no_cache( ).

* get default PERNR for user
  TRY.
      lv_default_pernr = go_employee_api->get_employeenumber_from_user( ).
    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

  lt_filter_select_options = io_tech_request_context->get_filter( )->get_filter_select_options( ).
  LOOP AT lt_filter_select_options INTO ls_filter_select_option.
    READ TABLE ls_filter_select_option-select_options INDEX 1 INTO ls_filter.
    CASE ls_filter_select_option-property.
      WHEN 'APPLICATION_ID'.
        lv_application_id = ls_filter-low.
    ENDCASE.
  ENDLOOP.

  CALL METHOD cl_hrcce_person_info_reader=>get_instance
    IMPORTING
      person_info_reader = lo_person_info_reader.

* get the additional CE infos from BAdI HCMFAB_B_COMMON
  CALL BADI gb_hcmfab_b_common->get_ce_configuration
    EXPORTING
      iv_application_id  = lv_application_id
      iv_employee_number = lv_default_pernr
    IMPORTING
      ev_hide_withdrawn  = lv_hide_withdrawn
      ev_hide_inactive   = lv_hide_inactive
      ev_hide_retiree    = lv_hide_retiree.


* read other assignments
  lt_pernrs = go_employee_api->get_assignments( lv_default_pernr ).
  LOOP AT lt_pernrs INTO lv_pernr.
    ls_entity-employee_id           = lv_pernr.
    ls_entity-application_id        = lv_application_id.
    ls_entity-is_default_assignment = boolc( lv_pernr = lv_default_pernr ).
    ls_entity-default_version_id    = go_employee_api->get_default_version_id( lv_pernr ).

*   read assignment text
    ls_entity-assignment_text = lo_person_info_reader->read_pernr_text(
                                      pernr  = lv_pernr
                                      begda  = sy-datlo ).
*   read employment status
    go_employee_api->get_employment_status(
      EXPORTING
        iv_pernr       = lv_pernr
      IMPORTING
        ev_status      = ls_entity-employment_status
        ev_status_text = ls_entity-employment_status_text
    ).

*   check whether the employee number shall be excluded because of the employment status.
    IF ls_entity-is_default_assignment = abap_false.
      IF ( ls_entity-employment_status = '0' AND lv_hide_withdrawn = abap_true ) OR
        ( ls_entity-employment_status = '1' AND lv_hide_inactive = abap_true ) OR
        ( ls_entity-employment_status = '2' AND lv_hide_retiree = abap_true ).
        CONTINUE.
      ENDIF.
    ENDIF.

*   check whether employee is a manager
    ls_entity-is_manager = go_employee_api->is_manager(
        iv_application_id = lv_application_id
        iv_pernr          = lv_pernr
        iv_eval_date      = sy-datlo
    ).

*   get the global configuration info from BAdI HCMFAB_B_COMMON
    CALL BADI gb_hcmfab_b_common->get_configuration
      EXPORTING
        iv_application_id              = lv_application_id
        iv_employee_number             = lv_pernr
      IMPORTING
        ev_hide_employee_picture       = lv_hide_pic
        ev_hide_employee_number        = lv_hide_number
        ev_hide_ce_button              = lv_hide_button
        ev_enable_onbehalf             = ls_entity-is_onbehalf_enabled
        ev_show_empl_number_wo_zeros   = ls_entity-show_employee_number_wo_zeros
        ev_use_onbehalf_backend_search = ls_entity-use_onbehalf_backend_search.

    ls_entity-show_employee_number      = boolc( lv_hide_number = abap_false ).
    ls_entity-show_employee_picture     = boolc( lv_hide_pic = abap_false ).
    ls_entity-is_ce_button_enabled      = boolc( lv_hide_button = abap_false ).
    ls_entity-is_change_picture_enabled = me->is_employee_pic_change_allowed( iv_application_id  = lv_application_id
                                                                              iv_employee_number = lv_pernr ).
    CALL METHOD get_employee_pic_settings
      EXPORTING
        iv_application_id            = lv_application_id
        iv_employee_number           = lv_pernr
      IMPORTING
        ev_employee_pic_max_filesize = ls_entity-employee_pic_max_filesize.

    APPEND ls_entity TO et_entityset.
  ENDLOOP.

ENDMETHOD.
