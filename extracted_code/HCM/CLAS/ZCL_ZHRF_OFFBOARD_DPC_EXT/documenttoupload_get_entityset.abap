  METHOD documenttoupload_get_entityset.

    DATA: lv_guid         TYPE string,
          lv_guid_raw     TYPE ze_hrfiori_guidreq,
          lv_pernr        TYPE pernr_d,
          lf_visibility   TYPE boolean,
          ls_req_data     TYPE zthrfiori_hreq,
          ls_filter       TYPE /iwbep/s_mgw_select_option,
          ls_filter_range TYPE /iwbep/s_cod_select_option,
          ls_results      TYPE zcl_zhrf_offboard_mpc=>ts_documenttoupload,
          ls_doctoupload  TYPE zthrfiori_offb_u,
          lt_results      TYPE zcl_zhrf_offboard_mpc=>tt_documenttoupload,
          lt_doctoupload  TYPE STANDARD TABLE OF  zthrfiori_offb_u.

*   Get filter values
    IF it_filter_select_options[] IS NOT INITIAL.
      LOOP AT it_filter_select_options INTO ls_filter.

        LOOP AT ls_filter-select_options INTO ls_filter_range.
          CASE ls_filter-property.
            WHEN 'Guid'.
              MOVE ls_filter_range-low TO lv_guid.
              lv_guid_raw = lv_guid.
          ENDCASE.
        ENDLOOP.
      ENDLOOP.
    ENDIF.

*   Get request information
    SELECT SINGLE * INTO ls_req_data
      FROM zthrfiori_hreq
        WHERE guid = lv_guid_raw.
    lv_pernr = ls_req_data-creator_pernr.

*   Get all doc type to upload
    SELECT * INTO TABLE lt_doctoupload
      FROM zthrfiori_offb_u
        WHERE language = sy-langu
          AND action_type = ls_req_data-action_type.

    LOOP AT lt_doctoupload INTO ls_doctoupload.
*     Check visibility if needed
      zcl_hr_fiori_offboarding_req=>check_doc_upload_visibility(
        EXPORTING iv_doc_upload = ls_doctoupload-doc_type
                  iv_pernr = lv_pernr
        IMPORTING ov_to_be_displayed = lf_visibility ).

      CHECK lf_visibility = abap_true.

      ls_results-doctype = ls_doctoupload-doc_type.
      ls_results-doctypetxt = ls_doctoupload-doc_txt.
      ls_results-visible = lf_visibility.
      ls_results-guid = lv_guid.

      APPEND ls_results TO lt_results.
    ENDLOOP.

    et_entityset = lt_results.

  ENDMETHOD.
