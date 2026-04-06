  METHOD attachmentset_get_entityset.

    DATA: lv_guid          TYPE ze_hrfiori_guidreq,
          lv_attach_type   TYPE ze_hrfiori_attachment_type,
          lv_inc_nb        TYPE ze_hrfiori_incrment_nb,
          lv_file_name     TYPE swr_filename,
          ls_filter        TYPE /iwbep/s_mgw_select_option,
          ls_filter_range  TYPE /iwbep/s_cod_select_option,
          lt_attach_list   TYPE zcl_hr_fiori_benefits=>tt_attachments,
          lo_util_benefits TYPE REF TO zcl_hr_fiori_benefits.

*   Get filter values if any
    IF it_filter_select_options[] IS NOT INITIAL.
      LOOP AT it_filter_select_options INTO ls_filter.
        LOOP AT ls_filter-select_options INTO ls_filter_range.
          CASE ls_filter-property.
            WHEN 'Guid'.
              MOVE ls_filter_range-low TO lv_guid.
            WHEN 'AttachType'.
              MOVE ls_filter_range-low TO lv_attach_type.
            WHEN 'IncNb'.
              MOVE ls_filter_range-low TO lv_inc_nb.
            WHEN 'Filename'.
              MOVE ls_filter_range-low TO lv_file_name.
          ENDCASE.
        ENDLOOP.
      ENDLOOP.
    ENDIF.

    CREATE OBJECT lo_util_benefits.
    lo_util_benefits->get_attachments(
          EXPORTING iv_guid = lv_guid
          IMPORTING ot_attachment_list = lt_attach_list ).

*   Filter results if necessary
    IF lv_attach_type IS NOT INITIAL.
      DELETE lt_attach_list WHERE attach_type <> lv_attach_type.
    ENDIF.
    IF lv_inc_nb IS NOT INITIAL.
      DELETE lt_attach_list WHERE inc_nb <> lv_inc_nb.
    ENDIF.
    IF lv_file_name IS NOT INITIAL.
      DELETE lt_attach_list WHERE filename <> lv_file_name.
    ENDIF.

*   Return results
    et_entityset = lt_attach_list.

  ENDMETHOD.
