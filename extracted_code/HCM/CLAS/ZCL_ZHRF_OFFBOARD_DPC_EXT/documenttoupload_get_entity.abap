  METHOD documenttoupload_get_entity.

    DATA: lv_pernr      TYPE pernr_d,
          lv_guid       TYPE string,
          lv_guid_raw   TYPE ze_hrfiori_guidreq,
          lv_doc_type   TYPE zde_doctype,
          lf_visibility TYPE boolean,
          ls_key        TYPE /iwbep/s_mgw_name_value_pair,
          ls_doc_upload TYPE zthrfiori_offb_u,
          ls_result     TYPE zcl_zhrf_offboard_mpc=>ts_documenttoupload.

*   Get parameters
    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'Guid' ##NO_TEXT.
    IF sy-subrc EQ 0.
      MOVE ls_key-value TO lv_guid.
      lv_guid_raw = lv_guid.
    ENDIF.

    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'Doc_Type' ##NO_TEXT.
    IF sy-subrc EQ 0.
      MOVE ls_key-value TO lv_doc_type.
    ENDIF.

*   Get request information
    SELECT SINGLE creator_pernr INTO lv_pernr
      FROM zthrfiori_hreq
        WHERE guid = lv_guid_raw.

*   Get all doc type to upload
    SELECT SINGLE * INTO ls_doc_upload
      FROM zthrfiori_offb_u
        WHERE doc_type = lv_doc_type
          AND language = sy-langu.

*   Check visibility
    zcl_hr_fiori_offboarding_req=>check_doc_upload_visibility(
        EXPORTING iv_doc_upload = ls_doc_upload-doc_type
                  iv_pernr = lv_pernr
        IMPORTING ov_to_be_displayed = lf_visibility ).

*   return result
    ls_result-guid = lv_guid.
    ls_result-doctype = lv_doc_type.
    ls_result-doctypetxt = ls_doc_upload-doc_txt.

    ls_result-visible = lf_visibility.

    er_entity = ls_result.

  ENDMETHOD.
