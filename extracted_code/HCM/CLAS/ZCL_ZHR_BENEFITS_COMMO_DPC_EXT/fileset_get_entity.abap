  METHOD fileset_get_entity.

    DATA: lv_guid        TYPE ze_hrfiori_guidreq,
          lv_attach_type TYPE ze_hrfiori_attachment_type,
          lv_inc_nb      TYPE ze_hrfiori_incrment_nb,
          ls_key_tab     TYPE /iwbep/s_mgw_name_value_pair,
          ls_return      TYPE zcl_zhr_benefits_commo_mpc=>ts_file.

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

    ls_return-guid = lv_guid.
    ls_return-attachtype = lv_attach_type.
    ls_return-incnb = lv_inc_nb.

    er_entity = ls_return.

  ENDMETHOD.
