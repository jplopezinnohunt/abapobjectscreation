METHOD build_expanded_entity.

  DATA:
    ls_navprop_vhfieldname TYPE if_ex_hcmfab_persinfo_config=>ty_s_navprop_vh_field,
    ls_pskey               TYPE hcmfab_s_pers_pskey,
    lv_init                TYPE boole_d,
    lv_longtext_found      TYPE boole_d,
    lt_help_values         TYPE cl_hcmfab_persinfo_feeder=>ty_t_help_values.

  FIELD-SYMBOLS:
    <lt_fieldmetadata>       TYPE STANDARD TABLE,
    <ls_fieldmetadata>       LIKE LINE OF it_fieldmetadata,
    <ls_fieldmetadata_pskey> TYPE any,
    <lt_validityinfo>        TYPE STANDARD TABLE,
    <ls_validity_info>       LIKE LINE OF it_validity_info,
    <ls_validity_info_pskey> TYPE any,
    <lt_valuehelp>           TYPE STANDARD TABLE,
    <ls_valuehelp>           TYPE any,
    <ls_help_values_ext>     TYPE if_hrpa_pernr_infty_xss_ext=>ts_f4,
    <ls_f4_tab>              TYPE any,
    <lt_f4_tab>              TYPE STANDARD TABLE,
    <ls_help_values>         TYPE cl_hcmfab_persinfo_feeder=>ty_s_help_values,
    <lv_id>                  TYPE any,
    <lv_text>                TYPE any,
    <lv_id_f4>               TYPE any,
    <lv_text_f4>             TYPE any.


  MOVE-CORRESPONDING is_entity TO es_expanded_entity.
  MOVE-CORRESPONDING is_entity TO ls_pskey.

* add fieldmetadata
  ASSIGN COMPONENT 'TOFIELDMETADATA' OF STRUCTURE es_expanded_entity TO <lt_fieldmetadata>.
  IF sy-subrc = 0.
    LOOP AT it_fieldmetadata ASSIGNING <ls_fieldmetadata> WHERE hcmfab_pskey = ls_pskey.
      APPEND INITIAL LINE TO <lt_fieldmetadata> ASSIGNING <ls_fieldmetadata_pskey>.
      MOVE-CORRESPONDING <ls_fieldmetadata> TO <ls_fieldmetadata_pskey>. "3266905
    ENDLOOP.
    APPEND 'TOFIELDMETADATA' TO ct_expanded_tech_clauses.
  ENDIF.


* add validity info
  ASSIGN COMPONENT 'TOVALIDITYINFO' OF STRUCTURE es_expanded_entity TO <lt_validityinfo>.
  IF sy-subrc = 0.
*   extract validity info corresponding to PSKEY
    LOOP AT it_validity_info ASSIGNING <ls_validity_info> WHERE hcmfab_pskey = ls_pskey.
      APPEND INITIAL LINE TO <lt_validityinfo> ASSIGNING <ls_validity_info_pskey>.
      MOVE-CORRESPONDING <ls_validity_info> TO <ls_validity_info_pskey>. "3266905
    ENDLOOP.
    APPEND 'TOVALIDITYINFO' TO ct_expanded_tech_clauses.
  ENDIF.

* add valuehelps
* extract help values corresponding to PSKEY
  lt_help_values = it_help_values.
  READ TABLE lt_help_values ASSIGNING <ls_help_values> WITH TABLE KEY hcmfab_pskey = ls_pskey.
  IF sy-subrc = 0.
*   for IT0006 we have to adapt HELP_VALUES_EXT
    IF ls_pskey-hcmfab_infty = '0006'.
      adapt_f4_values_for_land1(
        CHANGING
          cs_help_values = <ls_help_values>
      ).
    ENDIF.

    LOOP AT it_navprop_vhfield INTO ls_navprop_vhfieldname.

      ASSIGN COMPONENT ls_navprop_vhfieldname-nav_property
          OF STRUCTURE es_expanded_entity TO <lt_valuehelp>.

      CALL METHOD cl_hcmfab_persinfo_dpc_util=>convert_f4_to_valuehelp
        EXPORTING
          is_pskey       = ls_pskey
          is_help_values = <ls_help_values>
          is_navigation  = ls_navprop_vhfieldname
        IMPORTING
          et_valuehelp   = <lt_valuehelp>.

      APPEND ls_navprop_vhfieldname-nav_property TO ct_expanded_tech_clauses.

    ENDLOOP.
  ENDIF.

ENDMETHOD.
