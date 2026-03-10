  METHOD attachmentset_get_entity.

    DATA: lv_guid          TYPE ze_hrfiori_guidreq,
          lv_attach_type   TYPE ze_hrfiori_attachment_type,
          lv_inc_nb        TYPE ze_hrfiori_incrment_nb,
          ls_key_tab       TYPE /iwbep/s_mgw_name_value_pair,
          ls_attachment    TYPE zcl_hr_fiori_benefits=>ty_attachment,
          lt_attachments   TYPE zcl_hr_fiori_benefits=>tt_attachments,
          lo_util_benefits TYPE REF TO zcl_hr_fiori_benefits.

    LOOP AT it_key_tab INTO ls_key_tab.
      CASE ls_key_tab-name.
        WHEN 'Guid'.
          MOVE ls_key_tab-value TO lv_guid.
        WHEN 'AttachType'.
          MOVE ls_key_tab-value TO lv_attach_type.
        WHEN 'IncNb'.
          MOVE ls_key_tab-value TO lv_inc_nb.
      ENDCASE.
    ENDLOOP.

    CREATE OBJECT lo_util_benefits.
    lo_util_benefits->get_attachments( EXPORTING iv_guid = lv_guid
                                                 iv_attach_type = lv_attach_type
                                                 iv_inc_nb = lv_inc_nb
                                       IMPORTING ot_attachment_list = lt_attachments ).

    READ TABLE lt_attachments INTO ls_attachment INDEX 1.

    er_entity = ls_attachment.

  ENDMETHOD.
