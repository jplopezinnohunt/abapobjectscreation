METHOD get_pskey_from_filter.

  DATA ls_filter TYPE /iwbep/s_mgw_select_option.
  DATA ls_select TYPE /iwbep/s_cod_select_option.
  DATA lt_filter_select_options TYPE /iwbep/t_mgw_select_option.
  DATA lo_filter TYPE REF TO /iwbep/if_mgw_req_filter.

  lo_filter = io_tech_request_context->get_filter( ).
  lt_filter_select_options = lo_filter->get_filter_select_options( ).

  LOOP AT lt_filter_select_options INTO ls_filter.
    READ TABLE ls_filter-select_options INTO ls_select INDEX 1 TRANSPORTING low.
    CASE ls_filter-property.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_pernr.
        rs_pskey-hcmfab_pernr = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_infty.
        rs_pskey-hcmfab_infty = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_subty.
        rs_pskey-hcmfab_subty = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_objps.
        rs_pskey-hcmfab_objps =  ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_sprps.
        rs_pskey-hcmfab_sprps = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_begda.
        rs_pskey-hcmfab_begda = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_endda.
        rs_pskey-hcmfab_endda = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_seqnr.
        rs_pskey-hcmfab_seqnr = ls_select-low.
    ENDCASE.
  ENDLOOP.

ENDMETHOD.
