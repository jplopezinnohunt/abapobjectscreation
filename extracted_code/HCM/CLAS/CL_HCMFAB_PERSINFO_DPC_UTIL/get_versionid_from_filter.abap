METHOD get_versionid_from_filter.

  DATA ls_filter TYPE /iwbep/s_mgw_select_option.
  DATA ls_select TYPE /iwbep/s_cod_select_option.
  DATA lt_filter_select_options TYPE /iwbep/t_mgw_select_option.
  DATA lo_filter TYPE REF TO /iwbep/if_mgw_req_filter.

  lo_filter = io_tech_request_context->get_filter( ).
  lt_filter_select_options = lo_filter->get_filter_select_options( ).

  LOOP AT lt_filter_select_options INTO ls_filter.
    READ TABLE ls_filter-select_options INTO ls_select INDEX 1 TRANSPORTING low.
    CASE ls_filter-property.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-versionid.
        rv_versionid = ls_select-low.
        EXIT.
    ENDCASE.
  ENDLOOP.


ENDMETHOD.
