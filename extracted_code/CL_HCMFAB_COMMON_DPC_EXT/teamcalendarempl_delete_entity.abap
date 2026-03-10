METHOD teamcalendarempl_delete_entity.

  DATA: lv_employee_assignment TYPE pernr_d,
        lv_employee_id TYPE pernr_d,
        lv_view_type TYPE hcmfab_view_type,
        lv_view_id TYPE hcmfab_view_id,
        lt_key_tab              TYPE /iwbep/t_mgw_tech_pairs,
        ls_tech_key             TYPE /iwbep/s_mgw_tech_pair.
  DATA lv_personalization_mode TYPE hcmfab_tcal_app_pers_mode.
  DATA lo_message_container TYPE REF TO /iwbep/if_message_container.
  DATA lx_error             TYPE REF TO /iwbep/cx_mgw_busi_exception.
  DATA lv_param TYPE symsgv.
  DATA lv_application_id TYPE hcmfab_application_id.
  DATA lv_instance_id TYPE char20.


* get the key fields
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
      WHEN 'EMPLOYEE_ID'.
        lv_employee_id = ls_tech_key-value.
    ENDCASE.
  ENDLOOP.

* check if personalization is allowed
  me->get_tcal_personalization_mode(
    EXPORTING
      iv_application_id       = lv_application_id
      iv_instance_id          = lv_instance_id
      iv_employee_assignment  = lv_employee_assignment
    RECEIVING
      rv_personalization_mode = lv_personalization_mode
  ).
  IF lv_personalization_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-none.
    lv_param = lv_employee_id.

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

* delete employee from custom view
  me->change_employee_display_state(
    EXPORTING
      iv_employee_assignment = lv_employee_assignment
      iv_view_type           = lv_view_type
      iv_view_id             = lv_view_id
      iv_employee_id         = lv_employee_id
      iv_display_state       = if_hcmfab_tcal_constants=>gc_display_state-deleted
  ).

ENDMETHOD.
