METHOD employeepictures_delete_entity.
  DATA lv_pernr TYPE pernr_d.
  DATA lt_keys TYPE /iwbep/t_mgw_tech_pairs.
  DATA ls_key TYPE /iwbep/s_mgw_tech_pair.
  DATA return TYPE bapiret2.
  DATA subrc LIKE sy-subrc.
  DATA lx_exception       TYPE REF TO cx_static_check.
  data lv_application_id type hcmfab_application_id.

  lt_keys = io_tech_request_context->get_keys( ).
  READ TABLE lt_keys INTO ls_key WITH KEY name = 'EMPLOYEE_ID'.
  IF sy-subrc = 0.
    lv_pernr = ls_key-value.
  ENDIF.
  READ TABLE lt_keys INTO ls_key WITH KEY name = 'APPLICATION_ID'.
  IF sy-subrc = 0.
    lv_application_id = ls_key-value.
  ENDIF.
  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation(
        iv_pernr          = lv_pernr
        iv_application_id = lv_application_id ).

      CALL FUNCTION 'HRXSS_COD_DELETE_OLDPHOTO'
        EXPORTING
          pernr = lv_pernr.
      IF subrc <> 0.
        cx_hcmfab_common=>raise(
      EXPORTING
        iv_msgty = return-type
        iv_msgno = return-number
        iv_msgid = return-id
        iv_msgv1 = return-message_v1
        iv_msgv2 = return-message_v2
        iv_msgv3 = return-message_v3
        iv_msgv4 = return-message_v4 ).
      ENDIF.
      "System error when archiving a photo

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
                  is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                  iv_entity   = io_tech_request_context->get_entity_type_name( )
        ).

  ENDTRY.

ENDMETHOD.
