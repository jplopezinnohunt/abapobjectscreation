  method /iwbep/if_mgw_appl_srv_runtime~get_stream.
    data : lv_guid             type ze_hrfiori_guidreq,
           lv_attach_type      type ze_hrfiori_attachment_type,
           lv_inc_nb           type ze_hrfiori_incrment_nb,
           lv_filename         type swr_filename,
           lv_file_ext         type swr_fileext,
           lv_full_filename    type string,
           lv_encoded_filename type string,
           ls_stream           type ty_s_media_resource,
           ls_header           type ihttpnvp,
           ls_key_tab          type /iwbep/s_mgw_name_value_pair,
           lo_benefits_util    type ref to zcl_hr_fiori_benefits.

    if iv_entity_name = 'Attachment'.
      loop at it_key_tab into ls_key_tab.
        case ls_key_tab-name.
          when 'Guid'.
            move ls_key_tab-value to lv_guid.
          when 'AttachType'.
            move ls_key_tab-value to lv_attach_type.
          when 'IncNb'.
            move ls_key_tab-value to lv_inc_nb.
        endcase.

      endloop.
      create object lo_benefits_util.
      lo_benefits_util->get_attachment( exporting iv_guid = lv_guid
                                                  iv_attach_type = lv_attach_type
                                                  iv_inc_nb = lv_inc_nb
                                        importing ov_filename = lv_filename
                                                  ov_file_ext = lv_file_ext
                                                  os_media = ls_stream ).
*     Return file content
      copy_data_to_ref( exporting is_data = ls_stream
                        changing  cr_data = er_stream ).
*     Set header
      concatenate lv_filename lv_file_ext
        into lv_full_filename separated by '.' .
*     Attachment displayed in web browser
      ls_header-name = 'Content-Disposition' ##NO_TEXT.
      lv_encoded_filename = cl_http_utility=>escape_url( lv_full_filename ).
      concatenate 'inline; filename=' lv_encoded_filename
        into ls_header-value respecting blanks ##NO_TEXT.
      set_header( exporting is_header = ls_header ).
    endif.
  endmethod.
