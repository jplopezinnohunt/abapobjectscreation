METHOD employeepictur01_get_entityset.

  DATA: lt_filter_select_options        TYPE /iwbep/t_mgw_select_option,
        ls_filter_select_option         TYPE /iwbep/s_mgw_select_option,
        ls_filter                       TYPE /iwbep/s_cod_select_option,
        lv_pernr                        TYPE pernr_d,
        lt_allowed_mime_types           TYPE if_ex_hcmfab_common=>ty_t_mimetypes,
        ls_allowed_mime_type            TYPE LINE OF if_ex_hcmfab_common=>ty_t_mimetypes,
        lt_entity_allowed_mime_types    TYPE hcmfab_t_pic_allowed_mime_type,
        ls_entity_allowed_mime_type     TYPE hcmfab_s_pic_allowed_mime_type,
        lv_application_id               TYPE hcmfab_application_id.

  CLEAR: et_entityset, es_response_context.

  lt_filter_select_options = io_tech_request_context->get_filter( )->get_filter_select_options( ).
  LOOP AT lt_filter_select_options INTO ls_filter_select_option.
    READ TABLE ls_filter_select_option-select_options INDEX 1 INTO ls_filter.
    CASE ls_filter_select_option-property.
      WHEN 'EMPLOYEE_ID'.
        lv_pernr = ls_filter-low.
      WHEN 'APPLICATION_ID'.
        lv_application_id = ls_filter-low.
    ENDCASE.
  ENDLOOP.

  IF me->is_persinfo_application( lv_application_id ) = abap_true.
*   retrieve the allowed picture MIME-types from the BAdI
    CALL BADI gb_hcmfab_b_persinfo_settings->get_settings
      EXPORTING
        iv_application_id    = lv_application_id
        iv_employee_number   = lv_pernr
      IMPORTING
        et_allowed_mimetypes = lt_allowed_mime_types.

    LOOP AT lt_allowed_mime_types INTO ls_allowed_mime_type.
      ls_entity_allowed_mime_type-application_id = lv_application_id.
      ls_entity_allowed_mime_type-employee_id = lv_pernr.
      ls_entity_allowed_mime_type-mime_type = ls_allowed_mime_type.
      APPEND ls_entity_allowed_mime_type TO lt_entity_allowed_mime_types.
    ENDLOOP.

    et_entityset = lt_entity_allowed_mime_types.
  ENDIF.

ENDMETHOD.
