METHOD searchhelp_get_entityset.

  CONSTANTS fixed_domvalues_structure_name TYPE pad_sname VALUE 'PAOC_PAD_UI_FIXED_DOMVAL_HELP'.

  DATA ls_filter TYPE /iwbep/s_mgw_select_option.
  DATA ls_pskey TYPE hcmfab_s_pers_pskey.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA ls_help_values TYPE cl_hcmfab_persinfo_feeder=>ty_s_help_values.
  DATA lv_fieldname TYPE fieldname.
  DATA lo_filter TYPE REF TO /iwbep/if_mgw_req_filter.
  DATA lt_filter_select_options TYPE /iwbep/t_mgw_select_option.
  DATA lv_structure_name TYPE strukname.
  DATA lt_sel_options TYPE ddshselops.
  DATA ls_sel_options TYPE ddshselopt.
  DATA ls_shlp TYPE shlp_descr.
  DATA ls_help_values_ext TYPE if_hrpa_pernr_infty_xss_ext=>ts_f4.
  DATA lt_records TYPE TABLE OF seahlpres.
  DATA lv_f4_value_struc_name TYPE selmethod.
  DATA lr_sels TYPE REF TO data.
  DATA lr_selline TYPE REF TO data.
  DATA lt_components TYPE abap_component_tab.
  DATA ls_components TYPE abap_componentdescr.
  DATA ls_interface TYPE ddshiface.
  DATA lv_component_name TYPE string.
  DATA ls_fieldprop TYPE LINE OF ddshfprops.
  DATA ls_fielddescr TYPE dfies.
  DATA lr_new_help_type TYPE REF TO cl_abap_structdescr.
  DATA lv_f4fieldnamea TYPE shlpfield.
  DATA lv_f4fieldnameb TYPE dfies-lfieldname.
  DATA lt_shlp TYPE shlp_desct.
  DATA ls_callcontrol TYPE ddshf4ctrl.
  DATA lv_max_hits TYPE i VALUE 9999.
  DATA lv_top TYPE i.
  DATA lt_orderby TYPE /iwbep/t_mgw_tech_order.
  DATA lt_otab TYPE abap_sortorder_tab.
  DATA ls_oline TYPE abap_sortorder.

  FIELD-SYMBOLS <ls_sel_options> TYPE /iwbep/s_cod_select_option.
  FIELD-SYMBOLS <lt_sels> TYPE STANDARD TABLE.
  FIELD-SYMBOLS <ls_selline> TYPE any.
  FIELD-SYMBOLS <ls_orderby> TYPE /iwbep/s_mgw_tech_order.


  IF ls_pskey IS INITIAL.
    ls_pskey = get_pskey_from_filter( io_tech_request_context = io_tech_request_context ).
  ENDIF.

  lo_filter = io_tech_request_context->get_filter( ).
  lt_filter_select_options = lo_filter->get_filter_select_options( ).

* get filter values
  LOOP AT lt_filter_select_options INTO ls_filter.

* retrieve UI values of dependent fields
    IF ls_filter-property CS 'HCMFAB_'
      OR ls_filter-property CS 'MAPPED_FIELDNAMES'
      OR ls_filter-property CS 'VERSIONID'
      OR ls_filter-property CS 'IS_SEARCHHELP'.
      CONTINUE. "not considered
    ENDIF.
    IF ls_filter-property = 'FIELDNAME'.
      READ TABLE ls_filter-select_options ASSIGNING <ls_sel_options> INDEX 1.
      lv_fieldname = <ls_sel_options>-low.
      CONTINUE.
    ENDIF.
    ls_sel_options-shlpfield = ls_filter-property.
    LOOP AT ls_filter-select_options ASSIGNING <ls_sel_options>.
      IF NOT <ls_sel_options>-low IS INITIAL.
        MOVE-CORRESPONDING <ls_sel_options> TO ls_sel_options.
        APPEND ls_sel_options TO lt_sel_options.
      ENDIF.
    ENDLOOP.
  ENDLOOP.

  lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance( iv_pernr = ls_pskey-hcmfab_pernr iv_infty = ls_pskey-hcmfab_infty ).

  lv_structure_name = lo_feeder->get_sname_using_versionid( iv_versionid ).

  CALL METHOD cl_hrpa_generic_f4=>determine_searchhelp
    EXPORTING
      screen_structure_name = lv_structure_name
      f4_fieldname          = lv_fieldname
    IMPORTING
      shlp                  = ls_shlp
      f4_value_struc_name   = lv_f4_value_struc_name.

* Check if SHLPTYPES is one of the supported types
  IF ls_shlp-shlptype <> 'CT' AND  "Checktable with texttable
     ls_shlp-shlptype <> 'SH' AND  "Search help
     ls_shlp-shlptype <> 'CH' AND  "Checktable
     ls_shlp-shlptype <> 'FV'.     "Domain fixed values
    RETURN.
  ENDIF.

  IF ls_shlp-shlptype = 'FV'.
*   create table and structure of f4 data table
    lv_f4_value_struc_name = fixed_domvalues_structure_name.
    CREATE DATA lr_sels TYPE TABLE OF (lv_f4_value_struc_name).
    ASSIGN lr_sels->* TO <lt_sels>.

    CREATE DATA lr_selline TYPE (lv_f4_value_struc_name).
    ASSIGN lr_selline->* TO <ls_selline>.

  ELSE.
    READ TABLE ls_shlp-interface INTO ls_interface WITH KEY f4field = 'X'.
    ASSERT sy-subrc = 0.

    LOOP AT ls_shlp-fieldprop INTO ls_fieldprop.
      CLEAR ls_components.

      IF ls_fieldprop-shlplispos IS NOT INITIAL        OR
         ls_interface-shlpfield = ls_fieldprop-fieldname .

        READ TABLE ls_shlp-fielddescr INTO ls_fielddescr WITH KEY fieldname =  ls_fieldprop-fieldname.
        ASSERT sy-subrc = 0.

* Determine components for F4 table
        ls_components-name = ls_fieldprop-fieldname.
        IF ls_fielddescr-tabname IS NOT INITIAL.
          CONCATENATE ls_fielddescr-tabname '-' ls_fielddescr-fieldname INTO lv_component_name .
        ELSE.
          lv_component_name = ls_fielddescr-rollname.
        ENDIF.
        ls_components-type ?= cl_abap_typedescr=>describe_by_name( lv_component_name ) .

        APPEND ls_components TO lt_components.

      ENDIF.
    ENDLOOP.

* Now create type for F4 help dynamically
    lr_new_help_type  = cl_abap_structdescr=>create( lt_components ).
    ASSERT  lr_new_help_type IS NOT INITIAL.

    CREATE DATA lr_selline TYPE HANDLE lr_new_help_type.
    ASSIGN lr_selline->* TO <ls_selline>.

    CREATE DATA lr_sels LIKE STANDARD TABLE OF <ls_selline> WITH DEFAULT KEY.
    ASSIGN lr_sels->* TO <lt_sels>.
  ENDIF.

  ls_shlp-selopt = lt_sel_options.

  CALL FUNCTION 'F4IF_SELECT_VALUES'
    EXPORTING
      shlp           = ls_shlp
*     maxrows        = lv_max_hits
      sort           = abap_true
      call_shlp_exit = abap_true
    TABLES
      record_tab     = lt_records.

  LOOP AT ls_shlp-fieldprop INTO ls_fieldprop.
    lv_f4fieldnamea = ls_fieldprop-fieldname.
    lv_f4fieldnameb = ls_fieldprop-fieldname.

    CALL FUNCTION 'F4UT_PARAMETER_VALUE_GET'                "#EC *
      EXPORTING
        parameter         = lv_f4fieldnamea
        fieldname         = lv_f4fieldnameb
      TABLES
        shlp_tab          = lt_shlp
        record_tab        = lt_records
        results_tab       = <lt_sels>
      CHANGING
        shlp              = ls_shlp
        callcontrol       = ls_callcontrol
      EXCEPTIONS
        parameter_unknown = 1
        OTHERS            = 2.
    IF sy-subrc <> 0.
      CONTINUE.
    ENDIF.

  ENDLOOP.

* handle count request ($count)
  IF io_tech_request_context->has_count( ) = abap_true.
    es_response_context-count = lines( <lt_sels> ).
    RETURN.
  ELSE.
    IF io_tech_request_context->has_inlinecount( ) = abap_true.
      es_response_context-inlinecount = lines( <lt_sels> ).
    ENDIF.

* apply 'order by'($orderby)
    IF io_tech_request_context->get_orderby( ) IS NOT INITIAL.
      lt_orderby = io_tech_request_context->get_orderby( ).
      LOOP AT lt_orderby ASSIGNING <ls_orderby>.
        ls_oline-name = <ls_orderby>-property.
        ls_oline-descending = boolc( <ls_orderby>-order = if_hcmfab_constants=>gcs_sorting_order-descending ) .
        APPEND ls_oline TO lt_otab.
      ENDLOOP.

      SORT <lt_sels> STABLE BY (lt_otab).
    ENDIF.

* apply paging ($skip, $top)
    lv_top = io_tech_request_context->get_top( ).
    cl_hcmfab_utilities=>apply_paging(
      EXPORTING
         iv_top  = lv_top
         iv_skip = io_tech_request_context->get_skip( )
      CHANGING
         ct_data = <lt_sels>
    ).
  ENDIF.

  MOVE-CORRESPONDING ls_pskey TO ls_help_values.
  ls_help_values_ext-fieldname = lv_fieldname.
  ls_help_values_ext-f4_tab_ref = lr_sels.
  APPEND ls_help_values_ext TO ls_help_values-help_values_ext.

  convert_f4_to_valuehelp(
   EXPORTING
     is_pskey            = ls_pskey
     is_help_values      = ls_help_values
     iv_entity_name      = iv_entity_name
   IMPORTING
     et_valuehelp        = et_entityset ).

* ensure data is not cached on client
  es_response_context-do_not_cache_on_client = /iwbep/if_mgw_appl_types=>gcs_cache_on_client-do_not_cache.

ENDMETHOD.
