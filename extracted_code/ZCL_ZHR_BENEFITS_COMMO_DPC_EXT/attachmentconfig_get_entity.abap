  METHOD attachmentconfig_get_entity.

    DATA: lv_request_type  TYPE ze_hrfiori_requesttype,
          lv_attach_type   TYPE ze_hrfiori_attachment_type,
          lv_rs_reason     TYPE ze_hrfiori_req_reason,
          lv_eg_att_part   TYPE ze_hrfiori_eg_attach_part,
          ls_key_tab       TYPE /iwbep/s_mgw_name_value_pair,
          ls_attach_config TYPE zcl_hr_fiori_benefits=>ty_attach_config,
          lt_attach_config TYPE zcl_hr_fiori_benefits=>tt_attach_config,
          lo_util_benefits TYPE REF TO zcl_hr_fiori_benefits.

    LOOP AT it_key_tab INTO ls_key_tab.
      CASE ls_key_tab-name.
        WHEN 'RequestType'.
          MOVE ls_key_tab-value TO lv_request_type.
        WHEN 'AttachType'.
          MOVE ls_key_tab-value TO lv_attach_type.
        WHEN 'RsReason'.
          MOVE ls_key_tab-value TO lv_rs_reason.
        WHEN 'EgAttPart'.
          MOVE ls_key_tab-value TO lv_eg_att_part.
      ENDCASE.
    ENDLOOP.

    CREATE OBJECT lo_util_benefits.
    lo_util_benefits->get_attachment_configuration( EXPORTING iv_request_type = lv_request_type
                                                               iv_attach_type = lv_attach_type
                                                               iv_rs_reason = lv_rs_reason
                                                               iv_eg_att_part = lv_eg_att_part
                                                     IMPORTING ot_attach_config = lt_attach_config ).

    READ TABLE lt_attach_config INTO ls_attach_config INDEX 1.

    er_entity = ls_attach_config.

  ENDMETHOD.
