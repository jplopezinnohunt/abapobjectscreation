METHOD handle_valuehelp_longtext.
* ensure to fill all relevant text fields
* -> needed as in SAP_HRRXX (with SAP-note 2849675) e.g. HRPAD00_NATIO
*    was extended with NATIOs long text (50 char)

  STATICS:
    st_comp_view       TYPE abap_component_view_tab,
    sv_fieldname_long  TYPE fieldname,
    sv_fieldname_short TYPE fieldname.

  DATA:
     lo_struc_descr TYPE REF TO cl_abap_structdescr,
     lv_abs_name    TYPE abap_abstypename.

  FIELD-SYMBOLS:
    <lv_text_long>  TYPE any,
    <lv_text>       TYPE any,
    <ls_comp_view>  TYPE abap_simple_componentdescr.


  IF st_comp_view IS INITIAL OR iv_initialize = abap_true.
    CLEAR: sv_fieldname_short, sv_fieldname_long.
    lo_struc_descr ?= cl_abap_structdescr=>describe_by_data( cs_single_helpvalue ).
    st_comp_view = lo_struc_descr->get_included_view( ).

*    check if valuehelp supports long text
    "1st try with LANDX/LANDX50
    lv_abs_name = '\TYPE=' && 'LANDX50'.
    READ TABLE st_comp_view WITH KEY type->absolute_name = lv_abs_name ASSIGNING <ls_comp_view>.
    IF sy-subrc = 0.
      sv_fieldname_long = <ls_comp_view>-name.

      lv_abs_name = '\TYPE=' && 'LANDX'.
      UNASSIGN <ls_comp_view>.
      READ TABLE st_comp_view WITH KEY type->absolute_name = lv_abs_name ASSIGNING <ls_comp_view>.
      IF sy-subrc EQ 0.
        sv_fieldname_short = <ls_comp_view>-name.
      ENDIF.

    ELSE.
      "2nd try with NATIO/NATIO50
      lv_abs_name = '\TYPE=' && 'NATIO50'.
      READ TABLE st_comp_view WITH KEY type->absolute_name = lv_abs_name ASSIGNING <ls_comp_view>.
      IF sy-subrc = 0.
        sv_fieldname_long = <ls_comp_view>-name.

        lv_abs_name = '\TYPE=' && 'NATIO'.
        UNASSIGN <ls_comp_view>.
        READ TABLE st_comp_view WITH KEY type->absolute_name = lv_abs_name ASSIGNING <ls_comp_view>.
        IF sy-subrc EQ 0.
          sv_fieldname_short = <ls_comp_view>-name.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDIF.

  IF sv_fieldname_long IS NOT INITIAL AND
     sv_fieldname_short IS NOT INITIAL.
    ASSIGN COMPONENT sv_fieldname_long  OF STRUCTURE cs_single_helpvalue TO <lv_text_long>.
    ASSIGN COMPONENT sv_fieldname_short OF STRUCTURE cs_single_helpvalue TO <lv_text>.

*   if long textfield exists and contains a value,
*   we need to ensure the short textfield is also filled
    IF <lv_text_long> IS NOT INITIAL.
      <lv_text> = <lv_text_long>.
    ELSEIF <lv_text> IS NOT INITIAL.
      <lv_text_long> = <lv_text>.
    ENDIF.
  ENDIF.

ENDMETHOD.                    "handle_valuehelp_longtext
