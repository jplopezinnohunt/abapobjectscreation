  METHOD ui5propertyset_get_entity.

    DATA: lv_request_type TYPE ze_hrfiori_requesttype,
          lv_actor        TYPE ze_hrfiori_actor,
          lv_field        TYPE ze_hrfiori_uifield,
          lv_status       TYPE ze_hrfiori_requeststatus,
          ls_key_tab      TYPE /iwbep/s_mgw_name_value_pair,
          ls_uiproperty   TYPE  zthrfiori_ui5pro.

    LOOP AT it_key_tab INTO ls_key_tab.
      CASE ls_key_tab-name.
        WHEN 'RequestType'.
          MOVE ls_key_tab-value TO lv_request_type.
        WHEN 'Actor'.
          MOVE ls_key_tab-value TO lv_actor.
        WHEN 'Field'.
          MOVE ls_key_tab-value TO lv_field.
        WHEN 'Status'.
          MOVE ls_key_tab-value TO lv_status.
      ENDCASE.
    ENDLOOP.

    SELECT SINGLE * INTO ls_uiproperty
      FROM zthrfiori_ui5pro
        WHERE request_type = lv_request_type
          AND actor = lv_actor
          and status = lv_status
          AND field = lv_field.

    er_entity = ls_uiproperty.

  ENDMETHOD.
