METHOD subtypeattribute_get_entityset.

  cl_hcmfab_persinfo_dpc_util=>subtypeattribute_get_entityset(
    EXPORTING
      iv_entity_name           = iv_entity_name
      iv_entity_set_name       = iv_entity_set_name
      iv_source_name           = iv_source_name
      it_filter_select_options = it_filter_select_options
      is_paging                = is_paging
      it_key_tab               = it_key_tab
      it_navigation_path       = it_navigation_path
      it_order                 = it_order
      iv_filter_string         = iv_filter_string
      iv_search_string         = iv_search_string
      iv_infty                 = gc_infty
      io_tech_request_context  = io_tech_request_context
    IMPORTING
      et_entityset             = et_entityset
      es_response_context      = es_response_context
      ).

ENDMETHOD.
