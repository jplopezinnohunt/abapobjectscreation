  METHOD documentlinkset_get_entityset.

    DATA: lv_guid         TYPE string,
          lv_guid_raw     TYPE ze_hrfiori_guidreq,
          lv_pernr        TYPE pernr_d,
          lf_visibility   TYPE boolean,
          ls_filter       TYPE /iwbep/s_mgw_select_option,
          ls_filter_range TYPE /iwbep/s_cod_select_option,
          ls_results      TYPE zcl_zhrf_offboard_mpc=>ts_documentlink,
          ls_links        TYPE zthrfiori_offb_l,
          ls_req_data     TYPE zthrfiori_hreq,
          lt_results      TYPE zcl_zhrf_offboard_mpc=>tt_documentlink,
          lt_links        TYPE STANDARD TABLE OF  zthrfiori_offb_l,
          lo_manager      TYPE REF TO zcl_hr_document_manager,
          lv_letter_type  TYPE char10,
          lv_letter_url   TYPE saeuri,
          lv_message      TYPE string.

    lo_manager = zcl_hr_document_manager=>get_instance( ).


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

*   Get all doc links
    SELECT * INTO TABLE lt_links
      FROM zthrfiori_offb_l
        WHERE language = sy-langu
          AND link <> ''
          AND action_type = ls_req_data-action_type.


    LOOP AT lt_links INTO ls_links.

*     Manage the dynamic link for Separation/LOWP letter
      IF ls_links-id_link EQ 'LWP_LETTER' OR ls_links-id_link EQ 'SEP_LETTER'.
        IF ls_links-action_type EQ 00 . "LWOP
          lv_letter_type = 'YHRLWOPLET'.
        ELSEIF ls_links-action_type EQ 01 . "Separation
          lv_letter_type = 'YHRSEPLET'.
        ENDIF.
        CLEAR lv_letter_url.
        lo_manager->get_url_archive(
          EXPORTING
            im_pernr   = lv_pernr
            im_doctype = lv_letter_type
          IMPORTING
            ex_url     = lv_letter_url
            ev_message = lv_message     " SAP ArchiveLink: Data Element for Absolute URI
        ).
        IF sy-subrc NE 0 OR lv_letter_url IS INITIAL.
*         DELETE lt_links.
          ls_links-link_txt = lv_message.
*         Document not found page within the Offboarding Emp app
          ls_links-link = 'flp?#yhrappoffboardingemp-display&/ResourceNotFound'.
        ELSE.
          ls_links-link = lv_letter_url.
        ENDIF.
      ENDIF.

*     Check visibility if needed
      zcl_hr_fiori_offboarding_req=>check_doc_link_visibility(
        EXPORTING iv_id_link = ls_links-id_link
                  iv_pernr   = lv_pernr
                  iv_reason  = ls_req_data-reason
                  iv_action_type = ls_req_data-action_type
        IMPORTING ov_to_be_displayed = lf_visibility ).

      CHECK lf_visibility = abap_true.

      MOVE-CORRESPONDING ls_links TO ls_results.
      APPEND ls_results TO lt_results.

    ENDLOOP.

    et_entityset = lt_results.

  ENDMETHOD.
