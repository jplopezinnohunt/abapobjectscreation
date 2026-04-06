METHOD adapt_f4_values_for_land1.

  DATA lo_struc_descr TYPE REF TO cl_abap_structdescr.      "2649658
  DATA lt_comp_view TYPE abap_component_view_tab.           "2649658
  DATA lv_fieldname_land1 TYPE fieldname.                   "2649658
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.     "2649658
  DATA lv_default_versionid TYPE molga.                     "2649658
  DATA lv_ui_structure_name TYPE strukname.                 "2649658

  FIELD-SYMBOLS <ls_help_values_ext> TYPE if_hrpa_pernr_infty_xss_ext=>ts_f4.
  FIELD-SYMBOLS <ls_help_values> TYPE hrxss_per_f4.
  FIELD-SYMBOLS <ls_f4_tab> TYPE any.
  FIELD-SYMBOLS <lt_f4_tab> TYPE STANDARD TABLE.
  FIELD-SYMBOLS <lv_land1> TYPE land1.
  FIELD-SYMBOLS <comp_view> LIKE LINE OF lt_comp_view.      "2649658
  FIELD-SYMBOLS <lv_pernr> TYPE pernr_d.                    "2649658
  FIELD-SYMBOLS <lv_infty> TYPE infty.                      "2649658

  READ TABLE cs_help_values-help_values_ext WITH KEY fieldname = 'LAND1' ASSIGNING <ls_help_values_ext>.
* begin of "2649658
  IF sy-subrc EQ 0.
    lv_fieldname_land1 = 'LAND1'.
  ELSE.
* Russia uses KLAND1 instead of LAND1. To accomodate such cases, find field of type LAND1.
    ASSIGN COMPONENT 'HCMFAB_PERNR' OF STRUCTURE cs_help_values TO <lv_pernr>.
    ASSIGN COMPONENT 'HCMFAB_INFTY' OF STRUCTURE cs_help_values TO <lv_infty>.
    IF <lv_pernr> IS ASSIGNED AND <lv_infty> IS ASSIGNED.
      lv_default_versionid = cl_hcmfab_persinfo_feeder=>get_molga_of_pernr( <lv_pernr> ).
      CREATE OBJECT lo_feeder
        EXPORTING
          iv_pernr = <lv_pernr>
          iv_infty = <lv_infty>.

      lv_ui_structure_name = lo_feeder->get_sname_using_versionid( lv_default_versionid ).
      lo_struc_descr ?= cl_abap_typedescr=>describe_by_name( lv_ui_structure_name ).
      lt_comp_view = lo_struc_descr->get_included_view( ).
      READ TABLE lt_comp_view WITH KEY type->absolute_name = '\TYPE=LAND1' ASSIGNING <comp_view>.
      IF sy-subrc EQ 0.
        lv_fieldname_land1 = <comp_view>-name.
        READ TABLE cs_help_values-help_values_ext WITH KEY fieldname = lv_fieldname_land1 ASSIGNING <ls_help_values_ext>.
      ENDIF.
    ENDIF.
  ENDIF.
* end of "2649658

  IF <ls_help_values_ext> IS ASSIGNED.
    READ TABLE cs_help_values-help_values WITH KEY fieldname = lv_fieldname_land1 ASSIGNING <ls_help_values>.
    IF sy-subrc EQ 0.
      ASSIGN <ls_help_values_ext>-f4_tab_ref->* TO <lt_f4_tab>.
      LOOP AT <lt_f4_tab> ASSIGNING <ls_f4_tab>.
        ASSIGN COMPONENT 'LAND1' OF STRUCTURE <ls_f4_tab> TO <lv_land1>.
        IF <lv_land1> IS ASSIGNED.
          READ TABLE <ls_help_values>-f4values WITH KEY valuekey = <lv_land1> TRANSPORTING NO FIELDS.
          IF sy-subrc NE 0.
* 'country' not enabled in ESS -> remove from F4_ext
            DELETE TABLE <lt_f4_tab> FROM <ls_f4_tab>.
          ENDIF.
        ENDIF.
      ENDLOOP.
    ENDIF.
  ENDIF.

ENDMETHOD.
