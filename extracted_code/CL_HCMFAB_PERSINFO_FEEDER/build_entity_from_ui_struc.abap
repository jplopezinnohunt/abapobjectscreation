METHOD build_entity_from_ui_struc.

  DATA lv_delete_allowed TYPE boole_d.
  DATA lt_subty_metadata TYPE if_hrpa_pernr_infty_xss=>subty_metadata_tab.
  DATA lt_messages TYPE bapirettab.
  DATA lt_field_attributes TYPE hrpad_obj_field_attribute_tab.
  DATA lt_field_metadata TYPE ty_t_fieldmetadata.
  DATA lr_ui_structure TYPE REF TO data.
  DATA lo_strucdescr TYPE REF TO cl_abap_structdescr.
  DATA lt_f4_ext TYPE if_hrpa_pernr_infty_xss_ext=>tt_f4.
  DATA lt_f4 TYPE hrxss_per_f4_t.
  DATA lv_versionid TYPE hcmfab_versionid.

  FIELD-SYMBOLS <ls_ui_structure> TYPE any.
  FIELD-SYMBOLS <lv_deletable> TYPE boole_d.
  FIELD-SYMBOLS <lv_editable> TYPE boole_d.
  FIELD-SYMBOLS <ls_subty_metadata> TYPE if_hrpa_pernr_infty_xss=>subty_metadata.
  FIELD-SYMBOLS <lv_object_key> TYPE hcm_object_key.
  FIELD-SYMBOLS <ls_field_attributes> TYPE hrpad_obj_field_attribute.
  FIELD-SYMBOLS <lv_itbld> TYPE itbld.

  MOVE-CORRESPONDING is_pskey TO es_entity_main.

  MOVE-CORRESPONDING is_ui_structure TO es_entity_main.

  ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE is_ui_structure TO <lv_object_key>.

  CREATE DATA lr_ui_structure LIKE is_ui_structure.
  ASSIGN lr_ui_structure->* TO <ls_ui_structure>.

  IF et_field_metadata IS SUPPLIED.
    CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_data
      EXPORTING
        object_key          = <lv_object_key>
      IMPORTING
        ev_delete_allowed   = lv_delete_allowed
        main_record         = <ls_ui_structure>
        et_field_attributes = lt_field_attributes
        messages            = et_messages.

* unfortunately field OBJECT_KEY is not filled ...
    READ TABLE lt_field_attributes INDEX 1 ASSIGNING <ls_field_attributes>.
    IF sy-subrc EQ 0.
      <ls_field_attributes>-object_key = <lv_object_key>.

      lo_strucdescr ?= cl_abap_structdescr=>describe_by_data( is_ui_structure ).

      ASSIGN COMPONENT gc_fname-itbld OF STRUCTURE <ls_ui_structure> TO <lv_itbld>.
      IF <lv_itbld> IS ASSIGNED AND NOT <lv_itbld> IS INITIAL.
        lv_versionid = <lv_itbld>.
      ELSE.
        lv_versionid = me->get_default_versionid( ).
      ENDIF.

      me->map_field_attributes(
        EXPORTING
          iv_object_key        = <lv_object_key>
          is_pskey             = is_pskey
          iv_locked            = iv_locked
          it_field_attributes  = lt_field_attributes
          it_components        = lo_strucdescr->components
          iv_versionid         = lv_versionid
        IMPORTING
          et_field_metadata    = lt_field_metadata ).

      APPEND LINES OF lt_field_metadata TO et_field_metadata.
    ENDIF.

  ELSE.
    CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_data
      EXPORTING
        object_key        = <lv_object_key>
      IMPORTING
        ev_delete_allowed = lv_delete_allowed
        main_record       = <ls_ui_structure>
        messages          = et_messages.
  ENDIF.

* calculate hash for ETag    "2734354
  calculate_hash_for_etag(
    EXPORTING is_ui_record  = <ls_ui_structure>
    CHANGING cs_entity_main = es_entity_main     ).

  TRY.
      CALL METHOD mo_xss_adapter->read_metadata
        IMPORTING
          metadata_tab = lt_subty_metadata
          messages     = lt_messages.

      APPEND LINES OF lt_messages TO et_messages.
    CATCH cx_hrpa_violated_assertion.
      CLEAR lt_subty_metadata.
  ENDTRY.

  READ TABLE lt_subty_metadata WITH KEY subty = is_pskey-hcmfab_subty ASSIGNING <ls_subty_metadata>.
  IF sy-subrc EQ 0.
    IF <ls_subty_metadata>-disp_only = abap_true.           "2664785
* disable 'Edit' and 'Delete'
      ASSIGN COMPONENT gc_fname-is_editable OF STRUCTURE es_entity_main TO <lv_editable>.
      <lv_editable> = abap_false.
      ASSIGN COMPONENT gc_fname-is_deletable OF STRUCTURE es_entity_main TO <lv_deletable>.
      <lv_deletable> = abap_false.
    ELSE.
      ASSIGN COMPONENT gc_fname-is_editable OF STRUCTURE es_entity_main TO <lv_editable>.
      <lv_editable> = abap_true.
      ASSIGN COMPONENT gc_fname-is_deletable OF STRUCTURE es_entity_main TO <lv_deletable>.
      IF iv_locked = abap_true.
        <lv_deletable> = lv_delete_allowed.
      ELSE.
* in case the pernr isn't locked property delete_allowed is not evaluated by XSS Adapter
        <lv_deletable> =  me->is_delete_allowed( is_pskey = is_pskey ).
      ENDIF.
    ENDIF.
  ENDIF.

* handle F4-helps
  IF es_help_values IS SUPPLIED AND NOT it_fieldnames IS INITIAL.

    CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_f4_values
      EXPORTING
        included_fields = it_fieldnames
        record          = is_ui_structure
      IMPORTING
        f4table_ext     = lt_f4_ext
        f4table         = lt_f4.

    me->valuehelp_add_initial_entry(
      EXPORTING
        it_field_metadata = et_field_metadata               "n3076713
      CHANGING
        ct_f4 = lt_f4
        ct_f4_ext = lt_f4_ext ).


    MOVE-CORRESPONDING is_pskey TO es_help_values.
    es_help_values-help_values = lt_f4.
    es_help_values-help_values_ext = lt_f4_ext.

  ENDIF.

  IF et_validity_info IS SUPPLIED.

    CALL METHOD me->get_validity_info
      EXPORTING
        iv_object_key     = <lv_object_key>
        is_pskey          = is_pskey
        iv_is_create_mode = abap_false
      IMPORTING
        et_validity_info  = et_validity_info.

  ENDIF.

ENDMETHOD.
