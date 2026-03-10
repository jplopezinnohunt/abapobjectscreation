  METHOD attachmentconfig_get_entityset.

    DATA: lv_request_type  TYPE ze_hrfiori_requesttype,
          lv_attach_type   TYPE ze_hrfiori_attachment_type,
          lv_rs_reason     TYPE ze_hrfiori_req_reason,
          lv_eg_att_part   TYPE ze_hrfiori_eg_attach_part,
          ls_filter        TYPE /iwbep/s_mgw_select_option,
          ls_filter_range  TYPE /iwbep/s_cod_select_option,
          lt_attach_config TYPE zcl_hr_fiori_benefits=>tt_attach_config,
          lo_util_benefits TYPE REF TO zcl_hr_fiori_benefits.

*   Get filter values if any
    IF it_filter_select_options[] IS NOT INITIAL.
      LOOP AT it_filter_select_options INTO ls_filter.
        LOOP AT ls_filter-select_options INTO ls_filter_range.
          CASE ls_filter-property.
            WHEN 'RequestType'.
              MOVE ls_filter_range-low TO lv_request_type.
            WHEN 'AttachType'.
              MOVE ls_filter_range-low TO lv_attach_type.
            WHEN 'RsReason'.
              MOVE ls_filter_range-low TO lv_rs_reason.
            WHEN 'EgAttPart'.
              MOVE ls_filter_range-low TO lv_eg_att_part.
          ENDCASE.
        ENDLOOP.
      ENDLOOP.
    ENDIF.

    CREATE OBJECT lo_util_benefits.
    lo_util_benefits->get_attachment_configuration( EXPORTING iv_request_type = lv_request_type
                                                     IMPORTING ot_attach_config = lt_attach_config ).

*   Filter results if necessary
    IF lv_attach_type IS NOT INITIAL.
      DELETE lt_attach_config WHERE attach_type <> lv_attach_type.
    ENDIF.
    IF lv_rs_reason IS NOT INITIAL.
      DELETE lt_attach_config WHERE rs_reason <> lv_rs_reason.
    ENDIF.
    IF lv_eg_att_part IS NOT INITIAL.
      DELETE lt_attach_config WHERE eg_att_part <> lv_eg_att_part.
    ENDIF.

*   Return results
    et_entityset = lt_attach_config.

  ENDMETHOD.
