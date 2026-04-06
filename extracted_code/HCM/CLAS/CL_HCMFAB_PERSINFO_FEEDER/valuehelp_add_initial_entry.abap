METHOD valuehelp_add_initial_entry.

  DATA lr_f4_tab_line TYPE REF TO data.
  DATA ls_f4_initial TYPE hrxss_per_f4_value.
  DATA lv_tabix_initial_key TYPE i.

  FIELD-SYMBOLS <ls_f4> TYPE hrxss_per_f4.
  FIELD-SYMBOLS <ls_f4_ext> TYPE if_hrpa_pernr_infty_xss_ext=>ts_f4.
  FIELD-SYMBOLS <lt_f4_tab> TYPE STANDARD TABLE.
  FIELD-SYMBOLS <ls_f4_tab> TYPE any.
  FIELD-SYMBOLS <ls_copy_of_f4_tab> TYPE any.


  LOOP AT ct_f4 ASSIGNING <ls_f4>.
    IF it_field_metadata IS SUPPLIED AND NOT it_field_metadata IS INITIAL. "n3076713
      READ TABLE it_field_metadata WITH KEY field_name = <ls_f4>-fieldname is_required = abap_true TRANSPORTING NO FIELDS.
      IF sy-subrc EQ 0.
        CONTINUE. "do not add an initial entry for mandatory fields
      ENDIF.
    ENDIF.
    UNASSIGN <ls_f4_ext>.                                   "2904969
    READ TABLE <ls_f4>-f4values WITH KEY valuekey =  ls_f4_initial-valuekey TRANSPORTING NO FIELDS.
    IF sy-subrc NE 0.
* no initial key available -> insert initial table line:
* this is necessary as otherwise the first entry is pre-selected in drop down boxes
      INSERT INITIAL LINE INTO <ls_f4>-f4values INDEX 1.
* insert inital line into corresponding ct_f4_ext-f4_tab_ref, too
      READ TABLE ct_f4_ext WITH KEY fieldname = <ls_f4>-fieldname ASSIGNING <ls_f4_ext>. "#EC WARNOK
      IF <ls_f4_ext> IS ASSIGNED.
        ASSIGN  <ls_f4_ext>-f4_tab_ref->* TO <lt_f4_tab>.
        IF <lt_f4_tab> IS ASSIGNED.
* we have to search <lt_f4_tab> for initial table lines
* as <lt_f4_tab> and <ls_f4> are not always synchronously
          CREATE DATA lr_f4_tab_line LIKE LINE OF <lt_f4_tab>.
          ASSIGN lr_f4_tab_line->* TO <ls_f4_tab>.
          READ TABLE <lt_f4_tab> FROM <ls_f4_tab> TRANSPORTING NO FIELDS.
          IF sy-subrc NE 0.
* no initial line available
            INSERT INITIAL LINE INTO <lt_f4_tab> INDEX 1.
          ENDIF.
        ENDIF.
      ENDIF.
    ELSE. "record with initial key available
* we have to make sure that the "initial key"-record is on position 1 as the dropdown
* in UI positions on the first entry per default in case of an initial value
      IF sy-tabix <> 1.
        lv_tabix_initial_key = sy-tabix.
        READ TABLE ct_f4_ext WITH KEY fieldname = <ls_f4>-fieldname ASSIGNING <ls_f4_ext>. "#EC WARNOK
        IF <ls_f4_ext> IS ASSIGNED.
          ASSIGN  <ls_f4_ext>-f4_tab_ref->* TO <lt_f4_tab>.
          READ TABLE <lt_f4_tab> INDEX lv_tabix_initial_key ASSIGNING <ls_f4_tab>.
          IF <ls_f4_tab> IS ASSIGNED.
            CREATE DATA lr_f4_tab_line LIKE <ls_f4_tab>.
            ASSIGN lr_f4_tab_line->* TO <ls_copy_of_f4_tab>.
            <ls_copy_of_f4_tab> = <ls_f4_tab>.
            UNASSIGN <ls_f4_tab>.
            DELETE <lt_f4_tab> INDEX lv_tabix_initial_key.
            INSERT <ls_copy_of_f4_tab> INTO <lt_f4_tab> INDEX 1.
          ENDIF.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDLOOP.

ENDMETHOD.
