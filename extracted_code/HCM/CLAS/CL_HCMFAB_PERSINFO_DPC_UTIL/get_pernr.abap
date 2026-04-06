METHOD get_pernr.

  DATA lx_exception TYPE REF TO cx_static_check.
  DATA lv_entity_type_name TYPE string.

* get default pernr
  TRY.
      rv_pernr = go_employee_api->get_employeenumber_from_user( ).
    CATCH cx_hcmfab_common INTO lx_exception.
      IF io_tech_req_context_entityset IS  SUPPLIED.
        lv_entity_type_name = io_tech_req_context_entityset->get_entity_type_name( ).
      ELSE.
        lv_entity_type_name =  io_tech_req_context_entity->get_entity_type_name( ).
      ENDIF.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = lv_entity_type_name
      ).
  ENDTRY.

ENDMETHOD.
