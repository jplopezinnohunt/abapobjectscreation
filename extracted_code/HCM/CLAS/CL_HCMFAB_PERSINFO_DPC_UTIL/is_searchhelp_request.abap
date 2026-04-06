METHOD is_searchhelp_request.

  DATA ls_filter TYPE /iwbep/s_mgw_select_option.
  DATA ls_select TYPE /iwbep/s_cod_select_option.
  DATA lt_filter_select_options TYPE /iwbep/t_mgw_select_option.
  DATA lo_filter TYPE REF TO /iwbep/if_mgw_req_filter.

  lo_filter = io_tech_request_context->get_filter( ).
  lt_filter_select_options = lo_filter->get_filter_select_options( ).

  READ TABLE lt_filter_select_options INTO ls_filter WITH KEY property = 'IS_SEARCHHELP'.
  IF sy-subrc EQ 0.
    READ TABLE ls_filter-select_options INTO ls_select INDEX 1 TRANSPORTING low.
    IF sy-subrc EQ 0.
      IF NOT ls_select-low IS INITIAL.
        rv_is_searchhelp = abap_true.
      ENDIF.
    ENDIF.
  ENDIF.

ENDMETHOD.
