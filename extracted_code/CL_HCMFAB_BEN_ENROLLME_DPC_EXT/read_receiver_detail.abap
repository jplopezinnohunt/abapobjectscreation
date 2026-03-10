METHOD read_receiver_detail.

  DATA: lo_employee_api TYPE REF TO cl_hcmfab_employee_api,
        lv_pernr        TYPE pernr_d,
        ls_p0105        TYPE p0105,
        lv_data_exists  TYPE boole_d,
        lo_ex           TYPE REF TO cx_root.

  lv_pernr = iv_pernr.

  TRY .
      lo_employee_api = cl_hcmfab_employee_api=>get_instance( ).
      IF lv_pernr IS INITIAL.
        EXIT.
      ENDIF.
      """ get name of employee
      lo_employee_api->get_name(
        EXPORTING
          iv_pernr         = lv_pernr
        RECEIVING
          rv_name          = ev_name
      ).

      """ get office email of employee
      CALL METHOD cl_hcmfab_utilities=>read_infotype_record
        EXPORTING
          iv_pernr       = lv_pernr
          iv_infty       = '0105'
          iv_subty       = '0010'
        IMPORTING
          es_pnnnn       = ls_p0105
          ev_data_exists = lv_data_exists.

      IF lv_data_exists = abap_false.
        CALL METHOD cl_hcmfab_utilities=>read_infotype_record
          EXPORTING
            iv_pernr       = lv_pernr
            iv_infty       = '0105'
            iv_subty       = 'MAIL'
          IMPORTING
            es_pnnnn       = ls_p0105
            ev_data_exists = lv_data_exists.
      ENDIF.

      IF lv_data_exists = abap_true.
        IF ls_p0105-usrid_long IS NOT INITIAL.
          ev_email = ls_p0105-usrid_long.
        ELSE.
          ev_email = ls_p0105-usrid.
        ENDIF.
      ENDIF.

    CATCH cx_root INTO lo_ex.

  ENDTRY.


ENDMETHOD.
