METHOD teamcalendarview_create_entity.

  DATA: ls_view_db TYPE hcmfab_d_tcalcvw,
        ls_view TYPE cl_hcmfab_common_mpc=>ts_teamcalendarview,
        lv_uuid TYPE sysuuid_x16,
        lx_exception TYPE REF TO cx_static_check.
  DATA lv_personalization_mode TYPE hcmfab_tcal_app_pers_mode.
  DATA: lo_message_container TYPE REF TO /iwbep/if_message_container,
        lx_error             TYPE REF TO /iwbep/cx_mgw_busi_exception.
  DATA lv_param TYPE symsgv.
  DATA lv_default_view_pers_mode TYPE hcmfab_tcal_view_pers_mode.
  DATA lt_custom_views TYPE STANDARD TABLE OF hcmfab_d_tcalcvw.
  DATA lv_tabix TYPE sytabix.

  FIELD-SYMBOLS <ls_custom_view> TYPE hcmfab_d_tcalcvw.

  CLEAR er_entity.

* get the given data (description is needed)
  io_data_provider->read_entry_data(
    IMPORTING
      es_data = ls_view
  ).

* check if personalization is allowed
  me->get_tcal_personalization_mode(
    EXPORTING
      iv_application_id       = ls_view-application_id
      iv_instance_id          = ls_view-instance_id
      iv_employee_assignment  = ls_view-employee_assignment
    RECEIVING
      rv_personalization_mode = lv_personalization_mode
  ).
  IF lv_personalization_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-none.
    lv_param = ls_view-employee_assignment.
    CREATE OBJECT lx_error.
    lo_message_container = lx_error->get_msg_container( ).
    lo_message_container->add_message(
      EXPORTING
        iv_msg_type               = 'E'
        iv_msg_id                 = 'HCMFAB_COMMON'
        iv_msg_number             = '001'
        iv_msg_v1                 = lv_param
    ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = if_t100_message=>default_textid
        message_container = lo_message_container.
  ENDIF.

* get the default view personalization mode
  CALL BADI go_badi_tcal_settings->get_ui_settings
    EXPORTING
      iv_application_id         = ls_view-application_id
      iv_instance_id            = ls_view-instance_id
      iv_employee_assignment    = ls_view-employee_assignment
    IMPORTING
      ev_default_view_pers_mode = lv_default_view_pers_mode.
  IF lv_default_view_pers_mode IS INITIAL.
    lv_default_view_pers_mode = if_hcmfab_tcal_constants=>gc_view_pers_mode-full.
  ENDIF.

  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation(
        iv_pernr          = ls_view-employee_assignment
        iv_application_id = ls_view-application_id ).

      IF ls_view-view_id IS INITIAL.
*       it's a new view
        TRY.
*         create view ID
            CALL METHOD cl_system_uuid=>if_system_uuid_static~create_uuid_x16
              RECEIVING
                uuid = lv_uuid.
            ls_view_db-view_id = lv_uuid.
          CATCH cx_uuid_error .                         "#EC NO_HANDLER
        ENDTRY.
      ELSE.
*       an existing custom view is assigned to the current calendar usage
        ls_view_db-view_id = ls_view-view_id.
      ENDIF.

*     store the view (if employee create comes without viewId in same request
      gv_last_created_tcal_view = ls_view_db-view_id.

*     add missing sequence numbers for existing views
      SELECT * FROM hcmfab_d_tcalcvw INTO TABLE lt_custom_views
        WHERE application_id = ls_view-application_id AND instance_id = ls_view-instance_id AND emp_assignment = ls_view-employee_assignment
        ORDER BY sequence_number view_id. "#EC CI_BYPASS
      LOOP AT lt_custom_views ASSIGNING <ls_custom_view>.
        lv_tabix = sy-tabix.
        IF <ls_custom_view>-sequence_number IS INITIAL.
          <ls_custom_view>-sequence_number = lv_tabix.
        ENDIF.
      ENDLOOP.

*     add the new view
      ls_view_db-application_id = ls_view-application_id.
      ls_view_db-description = ls_view-description.
      ls_view_db-emp_assignment = ls_view-employee_assignment.
      ls_view_db-instance_id = ls_view-instance_id.
      ls_view_db-sequence_number = lv_tabix + 1.
      ls_view_db-mandt = sy-mandt.

*     update the database
      APPEND ls_view_db TO lt_custom_views.
      MODIFY hcmfab_d_tcalcvw FROM table lt_custom_views.

*     return the new entity record
      er_entity-application_id = ls_view-application_id.
      er_entity-description = ls_view-description.
      er_entity-employee_assignment = ls_view-employee_assignment.
      er_entity-instance_id = ls_view-instance_id.
      er_entity-is_default_view = abap_false.
      er_entity-personalization_mode = lv_default_view_pers_mode.
      er_entity-view_type = 'C'. "must be 'Custom'
      er_entity-view_id = ls_view_db-view_id.
      er_entity-sequence_number = ls_view_db-sequence_number.

*     call extension badi for view
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
