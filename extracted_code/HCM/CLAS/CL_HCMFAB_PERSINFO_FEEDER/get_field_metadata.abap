METHOD get_field_metadata.

  DATA: lo_exception         TYPE REF TO cx_hrpa_violated_assertion,
        lv_unkey             TYPE hcmt_bsp_pad_unkey,
        ls_mapping           TYPE hcmt_bsp_pad_tuid_mapping,
        lt_field_attributes  TYPE hrpad_obj_field_attribute_tab,
        lv_ui_structure_name TYPE strukname,
        lr_main_record       TYPE REF TO data,
        lv_locked            TYPE boole_d,
        lo_strucdescr        TYPE REF TO cl_abap_structdescr,
        lr_ui_structure_tab  TYPE REF TO data,
        lv_versionid         TYPE hcmfab_versionid,
        ls_message           TYPE bapiret2.

  FIELD-SYMBOLS: <ls_main_record>      TYPE data,
                 <ls_ui_structure_xx>  TYPE any,
                 <lt_ui_structure_xx>  TYPE STANDARD TABLE,
                 <lv_object_key>       TYPE hcm_object_key,
                 <lv_itbld>            TYPE itbld,
                 <ls_field_attributes> TYPE hrpad_obj_field_attribute.


  CLEAR: et_field_metadata, et_messages.

* try to read edit properties
  CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
    EXPORTING
      iv_lock   = abap_true
      iv_pernr  = is_pskey-hcmfab_pernr
    IMPORTING
      ev_locked = lv_locked.

*Initialize buffers of XSS adapter
  CREATE DATA lr_ui_structure_tab TYPE TABLE OF (me->mv_xx_structure_name).
  ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure_xx>.

  TRY.
      CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data
        IMPORTING
          main_records = <lt_ui_structure_xx>.

      lv_unkey = is_pskey.


      CALL METHOD go_tuid_mapper->compute_mapping
        EXPORTING
          sname   = gc_strucname_pskey
          unkey   = lv_unkey
        IMPORTING
          mapping = ls_mapping.

      READ TABLE <lt_ui_structure_xx> WITH KEY (gc_fname-object_key) = ls_mapping-tuid ASSIGNING <ls_ui_structure_xx>.
      IF <ls_ui_structure_xx> IS ASSIGNED.

        ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE <ls_ui_structure_xx> TO <lv_object_key>.
        ASSIGN COMPONENT gc_fname-itbld OF STRUCTURE <ls_ui_structure_xx> TO <lv_itbld>.
        IF <lv_itbld> IS ASSIGNED AND NOT <lv_itbld> IS INITIAL.
          lv_versionid = <lv_itbld>.
*          lv_ui_structure_name = me->get_sname_using_versionid( iv_versionid = <lv_itbld> ).
        ELSE.
          lv_versionid = me->get_default_versionid( ).
        ENDIF.
        lv_ui_structure_name = me->get_sname_using_versionid( iv_versionid = lv_versionid ).

        CREATE DATA lr_main_record TYPE (lv_ui_structure_name).
        ASSIGN lr_main_record->* TO <ls_main_record>.

        mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_data(
        EXPORTING
          object_key          = ls_mapping-tuid
        IMPORTING
          main_record         = <ls_main_record>
          et_field_attributes = lt_field_attributes ).

        READ TABLE lt_field_attributes INDEX 1 ASSIGNING <ls_field_attributes>.
        IF sy-subrc EQ 0.
          <ls_field_attributes>-object_key = <lv_object_key>. "OBJECT_KEY is not filled ...

          lo_strucdescr ?= cl_abap_structdescr=>describe_by_name( lv_ui_structure_name ).

          CALL METHOD me->map_field_attributes
            EXPORTING
              iv_object_key       = ls_mapping-tuid
              is_pskey            = is_pskey
              iv_locked           = lv_locked
              it_field_attributes = lt_field_attributes
              it_components       = lo_strucdescr->components
              iv_versionid        = lv_versionid
            IMPORTING
              et_field_metadata   = et_field_metadata.

          RETURN.
        ENDIF.
      ENDIF.

    CATCH cx_hrpa_violated_assertion INTO lo_exception.
      ls_message-type = 'E'.
      ls_message-message = lo_exception->if_message~get_text( ).
      APPEND ls_message TO et_messages.
  ENDTRY.

  IF lv_locked = abap_true.
* unlock PERNR
    CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
      EXPORTING
        iv_lock  = abap_false
        iv_pernr = is_pskey-hcmfab_pernr.

  ENDIF.

ENDMETHOD.
