  METHOD fileuploadset_get_entity.

    DATA: lv_requ_id  TYPE string,
          lv_doc_type TYPE string,
          ls_key_tab  TYPE /iwbep/s_mgw_name_value_pair,
          ls_return   TYPE zcl_zhrf_offboard_mpc=>ts_fileupload.

    LOOP AT it_key_tab INTO ls_key_tab.
      CASE ls_key_tab-name.
        WHEN 'RequestId'.
          MOVE ls_key_tab-value TO lv_requ_id.
        WHEN 'DocumentType'.
          MOVE ls_key_tab-value TO lv_doc_type.
      ENDCASE.
    ENDLOOP.

    ls_return-request_id = lv_requ_id.
    ls_return-document_type = lv_doc_type.

    er_entity = ls_return.

  ENDMETHOD.
