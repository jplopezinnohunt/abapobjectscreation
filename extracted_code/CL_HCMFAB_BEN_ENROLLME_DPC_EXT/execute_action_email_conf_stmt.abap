METHOD execute_action_email_conf_stmt.

  DATA: lo_employee_api          TYPE REF TO cl_hcmfab_employee_api,
        lv_pernr                 TYPE pernr_d,
        ls_param                 LIKE LINE OF it_parameter,
        lo_ex                    TYPE REF TO cx_root.

  TRY .

      LOOP AT it_parameter INTO ls_param.
        CASE ls_param-name.
          WHEN 'EmployeeNumber'.
            lv_pernr = ls_param-value.
          WHEN OTHERS.
        ENDCASE.
      ENDLOOP.

      go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).

      send_conf_stmt_mail(
        EXPORTING
          iv_date  = sy-datum
          iv_pernr =  lv_pernr
      ).
    CATCH cx_root INTO lo_ex.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lo_ex )
          iv_entity   = iv_action_name
      ).
  ENDTRY.

ENDMETHOD.
