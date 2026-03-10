METHOD get_value_help_set.

  DATA: lv_unkey             TYPE hcmt_bsp_pad_unkey,
        ls_mapping           TYPE hcmt_bsp_pad_tuid_mapping,
        lt_f4_ext            TYPE if_hrpa_pernr_infty_xss_ext=>tt_f4,
        lv_ui_structure_name TYPE strukname,
        lr_ui_copy           TYPE REF TO data,
        lt_f4                TYPE hrxss_per_f4_t,
        lr_ui_structure      TYPE REF TO data,
        lr_ui_structure_tab  TYPE REF TO data,
        lv_default_versionid TYPE hcmfab_versionid.

  FIELD-SYMBOLS: <ls_current_record>      TYPE any,
                 <ls_copy_record>         TYPE any,
                 <ls_changed_field_value> TYPE ty_s_fieldvalue,
                 <lv_fieldvalue>          TYPE any,
                 <ls_fieldname>           TYPE fieldnames,
                 <lt_ui_structure>        TYPE STANDARD TABLE.


  CLEAR es_help_values.

  lv_default_versionid = me->get_default_versionid( ).

  lv_ui_structure_name = get_sname_using_versionid( iv_versionid = lv_default_versionid ).

  CREATE DATA lr_ui_structure_tab TYPE TABLE OF (lv_ui_structure_name).
  ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure>.

*Initialize buffers of XSS adapter
  CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data
    IMPORTING
      main_records = <lt_ui_structure>.

  lv_unkey = is_pskey.

  TRY.
      CALL METHOD go_tuid_mapper->compute_mapping
        EXPORTING
          sname   = gc_strucname_pskey
          unkey   = lv_unkey
        IMPORTING
          mapping = ls_mapping.

      READ TABLE <lt_ui_structure> WITH KEY (gc_fname-object_key) = ls_mapping-tuid ASSIGNING <ls_current_record>.

      IF NOT <ls_current_record> IS ASSIGNED OR <ls_current_record> IS INITIAL.
* PSKEY not found -> create new record in XSS buffer
        IF iv_versionid = lv_default_versionid.

          CREATE DATA lr_ui_structure TYPE (lv_ui_structure_name).
          ASSIGN lr_ui_structure->* TO <ls_current_record>. "lr_ui_structure is of type 'default' UI structure

          CALL METHOD mo_xss_adapter->create
            EXPORTING
              subty  = is_pskey-hcmfab_subty
*             itbld  = iv_versionid "create with default versionid
            IMPORTING
              record = <ls_current_record>.
        ELSE.
          lv_ui_structure_name = get_sname_using_versionid( iv_versionid = iv_versionid ).

          CREATE DATA lr_ui_structure TYPE (lv_ui_structure_name).
          ASSIGN lr_ui_structure->* TO <ls_current_record>.

          CALL METHOD mo_xss_adapter->create
            EXPORTING
              subty  = is_pskey-hcmfab_subty
              itbld  = iv_versionid
            IMPORTING
              record = <ls_current_record>.
        ENDIF.
      ELSE.
* check whether record has the right UI structure
        IF iv_versionid <> lv_default_versionid.
          lv_ui_structure_name = get_sname_using_versionid( iv_versionid = iv_versionid ).

          CREATE DATA lr_ui_structure TYPE (lv_ui_structure_name).
          ASSIGN lr_ui_structure->* TO <ls_current_record>.

          CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_data
            EXPORTING
              object_key  = ls_mapping-tuid
            IMPORTING
              main_record = <ls_current_record>.

        ENDIF.
      ENDIF.

      IF <ls_current_record> IS NOT ASSIGNED OR <ls_current_record> IS INITIAL.
        RETURN.
      ENDIF.

* Update record with current field values
* Necessary because F4-help values might be field-dependent ...
      LOOP AT it_changed_field_values ASSIGNING <ls_changed_field_value>.
        ASSIGN COMPONENT <ls_changed_field_value>-fieldname OF STRUCTURE <ls_current_record> TO <lv_fieldvalue>.
        IF <lv_fieldvalue> IS ASSIGNED.
          <lv_fieldvalue> = <ls_changed_field_value>-fieldvalue.
          UNASSIGN <lv_fieldvalue>.
        ENDIF.
      ENDLOOP.
* Delete values of fields contained in IT_FIELDNAMES
* This is necessary because otherwise F4-Value list contains 'old' value
* regardless of whether it matches the new list or not
      CREATE DATA lr_ui_copy TYPE (lv_ui_structure_name).
      ASSIGN lr_ui_copy->* TO <ls_copy_record>.
      <ls_copy_record> = <ls_current_record>.
      LOOP AT it_fieldnames ASSIGNING <ls_fieldname>.
        ASSIGN COMPONENT <ls_fieldname>-fieldname OF STRUCTURE <ls_current_record> TO <lv_fieldvalue>.
        IF <lv_fieldvalue> IS ASSIGNED.
          CLEAR <lv_fieldvalue>.
        ENDIF.
      ENDLOOP.
      IF sy-subrc EQ 0.
* record changed -> send 'MODIFY' to XSS buffer
        CALL METHOD mo_xss_adapter->modify
          CHANGING
            record = <ls_copy_record>.

      ENDIF.

      CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_f4_values
        EXPORTING
          included_fields = it_fieldnames
          record          = <ls_current_record>
        IMPORTING
          f4table_ext     = lt_f4_ext
          f4table         = lt_f4.

      me->valuehelp_add_initial_entry(
      CHANGING
        ct_f4 = lt_f4
        ct_f4_ext = lt_f4_ext ).

      MOVE-CORRESPONDING is_pskey TO es_help_values.
      es_help_values-help_values = lt_f4.
      es_help_values-help_values_ext = lt_f4_ext.

* reset changes: necessary because further F4-request of the same cycle
* might rely on wrong (initial) values, e.g. initial field 'LAND1' in
* F4-request for region
      CALL METHOD mo_xss_adapter->modify
        CHANGING
          record = <ls_copy_record>.

    CATCH cx_hrpa_violated_assertion.
      RETURN.
  ENDTRY.

ENDMETHOD.
