METHOD teamcalendarview_delete_entity.

  DATA: lv_application_id TYPE hcmfab_application_id,
        lv_instance_id TYPE hcmfab_tcal_instance_id,
        lv_employee_assignment TYPE pernr_d,
        lv_view_type TYPE hcmfab_view_type,
        lv_view_id TYPE hcmfab_view_id,
        lv_num_usages TYPE i,
        lt_key_tab TYPE /iwbep/t_mgw_tech_pairs,
        ls_tech_key TYPE /iwbep/s_mgw_tech_pair,
        lx_exception TYPE REF TO cx_static_check.
  DATA lv_personalization_mode TYPE hcmfab_tcal_app_pers_mode.
  DATA: lo_message_container TYPE REF TO /iwbep/if_message_container,
        lx_error             TYPE REF TO /iwbep/cx_mgw_busi_exception.
  DATA lv_param TYPE symsgv.
  DATA lt_custom_views TYPE STANDARD TABLE OF hcmfab_d_tcalcvw.

  FIELD-SYMBOLS <ls_custom_view> TYPE hcmfab_d_tcalcvw.

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

  IF lv_view_type <> if_hcmfab_constants=>gc_viewtype-custom.
*   Only custom views can be deleted
    RETURN.
  ENDIF.

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
    lv_param = lv_employee_assignment.
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


  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation(
        iv_pernr          = lv_employee_assignment
        iv_application_id = lv_application_id ).

*     delete view
      DELETE FROM hcmfab_d_tcalcvw
        WHERE application_id = lv_application_id
        AND instance_id = lv_instance_id
        AND emp_assignment = lv_employee_assignment
        AND view_id = lv_view_id.

*     adjust the sequence numbers
      SELECT * FROM hcmfab_d_tcalcvw INTO TABLE lt_custom_views
        WHERE application_id = lv_application_id AND instance_id = lv_instance_id AND emp_assignment = lv_employee_assignment
        ORDER BY sequence_number view_id. "#EC CI_BYPASS
      IF lt_custom_views is NOT INITIAL.
        LOOP AT lt_custom_views ASSIGNING <ls_custom_view>.
          <ls_custom_view>-sequence_number = sy-tabix.
        ENDLOOP.
        MODIFY hcmfab_d_tcalcvw FROM TABLE lt_custom_views.
      ENDIF.

*     check if view is referenced somewhere else
      SELECT COUNT( * ) FROM hcmfab_d_tcalcvw INTO lv_num_usages "#EC CI_BYPASS
        WHERE view_id = lv_view_id.

*     if last usage  was deleted => remove peronalization entries as well
      IF lv_num_usages = 0.
        DELETE FROM hcmfab_d_tcalper WHERE view_id = lv_view_id. "#EC CI_NOFIRST
      ENDIF.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.
ENDMETHOD.
