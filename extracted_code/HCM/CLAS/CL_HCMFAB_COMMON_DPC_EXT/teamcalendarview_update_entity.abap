METHOD teamcalendarview_update_entity.

  DATA: lv_view_type TYPE hcmfab_view_type,
        lv_view_id TYPE hcmfab_view_id,
        lv_application_id TYPE hcmfab_application_id,
        lv_instance_id TYPE hcmfab_tcal_instance_id,
        lv_employee_assignment TYPE pernr_d,
        lt_key_tab TYPE /iwbep/t_mgw_tech_pairs,
        ls_tech_key TYPE /iwbep/s_mgw_tech_pair.
  DATA lv_personalization_mode TYPE hcmfab_tcal_app_pers_mode.
  DATA: lo_message_container TYPE REF TO /iwbep/if_message_container,
        lx_error             TYPE REF TO /iwbep/cx_mgw_busi_exception.
  DATA lv_param TYPE symsgv.
  DATA lt_custom_views type standard table of hcmfab_d_tcalcvw.

  FIELD-SYMBOLS <ls_custom_view> type hcmfab_d_tcalcvw.

  lt_key_tab = io_tech_request_context->get_keys( ).
  LOOP AT lt_key_tab INTO ls_tech_key.
    CASE ls_tech_key-name.
      WHEN 'APPLICATION_ID'.
        lv_application_id = ls_tech_key-value.
      WHEN 'INSTANCE_ID'.
        lv_instance_id = ls_tech_key-value.
      WHEN 'EMPLOYEE_ASSIGNMENT'.
        lv_employee_assignment = ls_tech_key-value.
      WHEN 'VIEW_TYPE'.
        lv_view_type = ls_tech_key-value.
      WHEN 'VIEW_ID'.
        lv_view_id = ls_tech_key-value.
    ENDCASE.
  ENDLOOP.

* get the entity data
  io_data_provider->read_entry_data(
    IMPORTING
      es_data = er_entity
  ).

  IF lv_view_type <> if_hcmfab_constants=>gc_viewtype-custom.
*   Only custom views can be changed
    RETURN.
  ENDIF.

* check if personalization is allowed
  me->get_tcal_personalization_mode(
    EXPORTING
      iv_application_id       = er_entity-application_id
      iv_instance_id          = er_entity-instance_id
      iv_employee_assignment  = er_entity-employee_assignment
    RECEIVING
      rv_personalization_mode = lv_personalization_mode
  ).
  IF lv_personalization_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-none.
    lv_param = er_entity-employee_assignment.
    CREATE OBJECT lx_error.
    lo_message_container = lx_error->get_msg_container( ).
    lo_message_container->add_message(
      EXPORTING
        iv_msg_type               = 'E'
        iv_msg_id                 =  'HCMFAB_COMMON'
        iv_msg_number             =  '001'
        iv_msg_v1                 =  lv_param
    ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = if_t100_message=>default_textid
        message_container = lo_message_container.
  ENDIF.

* update view title in database (for all usages of the view)
  UPDATE hcmfab_d_tcalcvw                               "#EC CI_NOFIRST
    SET description = er_entity-description
    WHERE view_id = lv_view_id.

* update the sequence numbers (only for current usage of the view)
  SELECT * FROM hcmfab_d_tcalcvw INTO TABLE lt_custom_views
    WHERE application_id = lv_application_id AND instance_id = lv_instance_id AND emp_assignment = lv_employee_assignment
    ORDER BY sequence_number view_id. "#EC CI_BYPASS
  LOOP AT lt_custom_views ASSIGNING <ls_custom_view>.
    IF <ls_custom_view>-view_id = lv_view_id.
      <ls_custom_view>-sequence_number = er_entity-sequence_number.
    ELSEIF <ls_custom_view>-sequence_number IS INITIAL.
      <ls_custom_view>-sequence_number = sy-tabix.
    ENDIF.
  ENDLOOP.
  MODIFY hcmfab_d_tcalcvw FROM TABLE lt_custom_views.

ENDMETHOD.
