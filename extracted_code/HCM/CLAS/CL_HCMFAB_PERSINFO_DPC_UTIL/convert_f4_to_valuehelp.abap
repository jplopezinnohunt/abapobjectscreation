METHOD convert_f4_to_valuehelp.

  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.
  DATA lt_valuehelp_fields TYPE hcmfab_t_pers_fieldname.
  DATA lv_init TYPE boole_d.

  FIELD-SYMBOLS <ls_help_values> TYPE hrxss_per_f4.
  FIELD-SYMBOLS <ls_f4_untyped> TYPE hrxss_per_f4_value.
  FIELD-SYMBOLS <ls_valuehelp> TYPE any.
  FIELD-SYMBOLS <ls_f4_tab> TYPE any.
  FIELD-SYMBOLS <lt_f4_tab> TYPE STANDARD TABLE.
  FIELD-SYMBOLS <ls_domvalue> TYPE hcmfab_s_pers_domvalue.
  FIELD-SYMBOLS <lv_id> TYPE any.
  FIELD-SYMBOLS <lv_text> TYPE any.
  FIELD-SYMBOLS <lv_id_f4> TYPE any.
  FIELD-SYMBOLS <lv_text_f4> TYPE any.
  FIELD-SYMBOLS <ls_help_values_ext> TYPE if_hrpa_pernr_infty_xss_ext=>ts_f4.

  IF is_navigation IS SUPPLIED.
    READ TABLE is_help_values-help_values_ext
           WITH KEY fieldname = is_navigation-vh_fieldname
           ASSIGNING <ls_help_values_ext>.
  ELSE.
    READ TABLE is_help_values-help_values_ext INDEX 1 ASSIGNING <ls_help_values_ext>.
  ENDIF.
* we are converting a single F4-help here
  IF <ls_help_values_ext> IS ASSIGNED.                      "2861486
    lv_init = abap_true.
    ASSIGN <ls_help_values_ext>-f4_tab_ref->* TO <lt_f4_tab>.
    LOOP AT <lt_f4_tab> ASSIGNING <ls_f4_tab>.
      APPEND INITIAL LINE TO et_valuehelp ASSIGNING <ls_valuehelp>.
* fill pskey
      MOVE-CORRESPONDING is_pskey TO <ls_valuehelp>.
* check whether we deal with domain fix values
* domain values are returned in structure format [_LOW, _TEXT]
      ASSIGN COMPONENT '_LOW' OF STRUCTURE <ls_f4_tab> TO <lv_id_f4>.
      IF sy-subrc = 0.
        ASSIGN COMPONENT 'ID' OF STRUCTURE <ls_valuehelp> TO <lv_id>.
        IF sy-subrc = 0.
          <lv_id> = <lv_id_f4>.
        ELSE.
* the value help structure does not match structure [HCMFAB_PSKEY, ID, TEXT]
* -> delete the initial line and exit the loop
          DELETE et_valuehelp FROM 1.
          EXIT.
        ENDIF.

        ASSIGN COMPONENT '_TEXT' OF STRUCTURE <ls_f4_tab> TO <lv_text_f4>.
        IF sy-subrc = 0.
          ASSIGN COMPONENT 'TEXT' OF STRUCTURE <ls_valuehelp> TO <lv_text>.
          IF sy-subrc = 0.
            <lv_text> = <lv_text_f4>.
          ENDIF.
        ENDIF.
      ELSE.
* we don't deal deal with domain fix values from f4 help
* check whether the valuehelp is based on [HCMFAB_PSKEY, ID, TEXT]
        ASSIGN COMPONENT 'ID' OF STRUCTURE <ls_valuehelp> TO <lv_id>.
        IF sy-subrc EQ 0.
* the value help structure expects domain fixed values, i.e. it does not match the F4-help structure
* -> delete the initial line and exit the loop
          DELETE et_valuehelp FROM 1.
          EXIT.
        ENDIF.

        MOVE-CORRESPONDING <ls_f4_tab> TO <ls_valuehelp>.


        IF is_nationality_valuehelp( iv_nav_property_name = is_navigation-nav_property iv_entity_name = iv_entity_name ) = abap_true OR
           is_country_valuehelp( iv_nav_property_name = is_navigation-nav_property iv_entity_name = iv_entity_name ) = abap_true.
          handle_valuehelp_longtext(
            EXPORTING
              iv_initialize       = lv_init
            CHANGING
              cs_single_helpvalue = <ls_valuehelp>
          ).
        ENDIF.
      ENDIF.
      lv_init = abap_false.
    ENDLOOP.
  ENDIF.

ENDMETHOD.
