METHOD /iwbep/if_mgw_appl_srv_runtime~get_stream.

  DATA: lt_error_table    TYPE hrben00err_ess,
        lt_assignments    TYPE pccet_pernr,
        lt_messages       TYPE TABLE OF bapiret2,
        lt_filter_select_options TYPE /iwbep/t_mgw_select_option,
        ls_error          LIKE LINE OF lt_error_table,
        ls_filter         TYPE /iwbep/s_mgw_select_option,
        ls_filter_range   TYPE /iwbep/s_cod_select_option,
        ls_t100_msg       TYPE scx_t100key,
        ls_key_tab        TYPE /iwbep/s_mgw_name_value_pair,
        ls_stream         TYPE ty_s_media_resource,
        ls_header         TYPE ihttpnvp,
        lv_xstring        TYPE xstring,                     "#EC NEEDED
        lv_result         TYPE boole_d,
        lv_assignment     TYPE pcce_pernr,
        lv_size           TYPE i,                           "#EC NEEDED
        lv_pernr          TYPE pernr_d,
        lv_subrc          TYPE sy-subrc,
        lv_date           TYPE sydatum,
        lv_bapi_error     TYPE bapi_msg,                    "#EC NEEDED
        lv_filter_str     TYPE string,
        lv_filename       TYPE string,
        lo_message_container     TYPE REF TO /iwbep/if_message_container,
        lo_employee_api          TYPE REF TO cl_hcmfab_employee_api,
        lx_exception             TYPE REF TO cx_static_check,
        lo_filter                TYPE REF TO /iwbep/if_mgw_req_filter.



  DATA: s_filter TYPE /iwbep/s_mgw_select_option,
        s_range TYPE /iwbep/s_cod_select_option.

  CLEAR:lv_date,lv_pernr.
  IF iv_entity_name = 'ConfirmationForm' OR
     iv_entity_name = 'PaycheckSimulation'.

    CLEAR:ls_key_tab.

    IF iv_entity_name = 'ConfirmationForm'.

      READ TABLE it_key_tab INTO ls_key_tab WITH KEY name = 'FileKey'.

      IF ls_key_tab-value <> 'CONF_FORM'.
*      --- raise exception that other Options are not supported
        ls_t100_msg-msgid = c_msg_class_enro.
        ls_t100_msg-msgno = '003'.
        ls_t100_msg-attr1 = '''FileKey'''.
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid = ls_t100_msg.
      ENDIF.

      CLEAR:ls_key_tab.

      READ TABLE it_key_tab INTO ls_key_tab WITH KEY name = 'Date'. "#EC NOTEXT
      IF sy-subrc = 0 AND ls_key_tab-value IS NOT INITIAL.
        lv_date = ls_key_tab-value.
      ELSE.
        lv_date = sy-datum.
      ENDIF.

    ENDIF.

    CLEAR:ls_key_tab.
    READ TABLE it_key_tab INTO ls_key_tab WITH KEY name = 'EmployeeNumber'.
    IF sy-subrc EQ 0.
      lv_pernr = ls_key_tab-value.
      TRY.
* Check if Pernr is valid or not
          go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                         iv_application_id = gc_application_id-mybenefitsenrollment ).
        CATCH cx_hcmfab_common INTO lx_exception.
          cl_hcmfab_utilities=>raise_gateway_error(
              is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
              iv_entity   = io_tech_request_context->get_entity_type_name( )
          ).
      ENDTRY.
      DELETE lt_messages WHERE type CA 'WIS'.

      IF lt_messages IS NOT INITIAL.
        lo_message_container = me->mo_context->get_message_container( ).
        lo_message_container->add_messages_from_bapi(
        it_bapi_messages         = lt_messages
        iv_determine_leading_msg = /iwbep/if_message_container=>gcs_leading_msg_search_option-last
        iv_entity_type           = iv_entity_name
        ).

        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            message_container = lo_message_container.
      ENDIF.
    ENDIF.
    CLEAR:ls_stream-value,lt_error_table,lv_subrc.

    IF iv_entity_name = 'ConfirmationForm'.

      CALL METHOD me->get_conf_stmt_pdf
        EXPORTING
          iv_pernr    = lv_pernr
          iv_datum    = lv_date
        IMPORTING
          ev_pdf_data = ls_stream-value
          et_error    = lt_error_table
          ev_subrc    = lv_subrc.

          IF lv_subrc <> 0.
            LOOP AT lt_error_table INTO ls_error.
              me->/iwbep/if_sb_dpc_comm_services~log_message(
                EXPORTING
                  iv_msg_type   = ls_error-sever
                  iv_msg_id     = ls_error-class
                  iv_msg_number = ls_error-msgno
                  iv_msg_v1     = ls_error-msgv1
                  iv_msg_v2     = ls_error-msgv2
                  iv_msg_v3     = ls_error-msgv3
                  iv_msg_v4     = ls_error-msgv4
                  ).
            ENDLOOP.
            ls_t100_msg-msgid = c_msg_class_enro.
            ls_t100_msg-msgno = '004'.
            RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
              EXPORTING
                textid = ls_t100_msg.

        ENDIF.

        lv_filename = c_conf_stmt_pdf.

    ELSE.

      get_paycheck_data(
        EXPORTING
          iv_pernr   = lv_pernr
        IMPORTING
          ev_content = ls_stream-value
      ).

      lv_filename = c_paycheck_pdf.

      """ Delete content from the temp. table
      update_paycheck_data(
        EXPORTING
          iv_pernr   = lv_pernr
      ).

    ENDIF.

    ls_stream-mime_type = 'application/pdf'.              "#EC NOTEXT
    copy_data_to_ref( EXPORTING is_data = ls_stream
                        CHANGING  cr_data = er_stream ).

    ls_header-name = 'Cache-Control'.                     "#EC NOTEXT
    ls_header-value = 'no-cache, no-store'.               "#EC NOTEXT
    set_header( EXPORTING is_header = ls_header ).

    ls_header-name = 'Pragma'.                            "#EC NOTEXT
    ls_header-value = 'no-cache'.                         "#EC NOTEXT
    set_header( EXPORTING is_header = ls_header ).

    ls_header-name = 'Content-Disposition'.
    CONCATENATE 'attachment; filename=' lv_filename INTO ls_header-value RESPECTING BLANKS. "#EC NOTEXT
    set_header( EXPORTING is_header = ls_header ).

  ENDIF.

ENDMETHOD.
