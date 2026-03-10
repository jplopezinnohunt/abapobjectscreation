METHOD delete.

  DATA: lo_exception         TYPE REF TO cx_hrpa_violated_assertion,
        lr_ui_structure_tab  TYPE REF TO data,
        ls_message           TYPE bapiret2,
        lv_unkey             TYPE hcmt_bsp_pad_unkey,
        ls_mapping           TYPE hcmt_bsp_pad_tuid_mapping,
        lv_locked            TYPE boole_d.
  DATA lo_persinfo_update_badi TYPE REF TO hcmfab_b_persinfo_update_data. "2964654
  DATA lv_call_badi TYPE boole_d.                           "2964654
  DATA ls_badi_pskey TYPE pskey.                            "2964654

  FIELD-SYMBOLS: <ls_ui_structure> TYPE any,
                 <lt_ui_structure> TYPE STANDARD TABLE,
                 <lv_object_key>   TYPE hcm_object_key.


  CLEAR et_messages.

* try to lock the PERNR
  CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
    EXPORTING
      iv_lock   = abap_true
      iv_pernr  = mv_pernr
    IMPORTING
      ev_locked = lv_locked
      messages  = et_messages.

  IF lv_locked <> abap_true.
    RETURN.
  ENDIF.

  CLEAR et_messages.

* we need to re-construct the original record in order to find the right OBJECT_KEY to delete
  CREATE DATA lr_ui_structure_tab TYPE TABLE OF (mv_xx_structure_name).
  ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure>.

* read all records to initialize xss adapter buffers
  CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data
    IMPORTING
      main_records = <lt_ui_structure>
      messages     = et_messages.

  lv_unkey = is_pskey.
  CALL METHOD go_tuid_mapper->compute_mapping
    EXPORTING
      sname   = gc_strucname_pskey
      unkey   = lv_unkey
    IMPORTING
      mapping = ls_mapping.

  READ TABLE <lt_ui_structure> WITH KEY (gc_fname-object_key) = ls_mapping-tuid ASSIGNING <ls_ui_structure>.
  IF <ls_ui_structure> IS ASSIGNED.
    ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE <ls_ui_structure> TO <lv_object_key>.

    TRY.
        CALL METHOD mo_xss_adapter->delete
          EXPORTING
            object_key = <lv_object_key>
          IMPORTING
            messages   = et_messages.

        READ TABLE et_messages WITH KEY type = 'E' TRANSPORTING NO FIELDS.
        IF sy-subrc NE 0. "no error messages found -> save data
          CLEAR et_messages.
          mo_xss_adapter->save( IMPORTING messages = et_messages ).
          READ TABLE et_messages WITH KEY type = 'E' TRANSPORTING NO FIELDS.
          IF sy-subrc NE 0. "no error messages found -> call BAdi
            lv_call_badi = abap_true.                       "2964654
          ENDIF.
        ENDIF.

      CATCH cx_hrpa_violated_assertion INTO lo_exception.
        ls_message-type = 'E'.
        ls_message-message = lo_exception->if_message~get_text( ).
        APPEND ls_message TO et_messages.
    ENDTRY.
  ELSE.
                                                            "#EC NEEDED
* message "Record not found" ?
* -> This may only happen in case the record-pskey was changed before deletion which is not possible in the current implementation
  ENDIF.

* unlock PERNR
  CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
    EXPORTING
      iv_lock  = abap_false
      iv_pernr = mv_pernr.

  IF lv_call_badi = abap_true.                              "2964654
* call BAdI HCMFAB_B_PERSINFO_UPDATE_DATA to allow updating of further business data
    GET BADI lo_persinfo_update_badi
      FILTERS
        infty = mv_infty.

    ls_badi_pskey = get_pskey_from_hcmfab_pskey( is_pskey ).

    CALL BADI lo_persinfo_update_badi->delete
      EXPORTING
        is_pskey             = ls_badi_pskey
        is_uinnnn            = <ls_ui_structure>
        iv_ui_structure_name = mv_xx_structure_name
        iv_versionid         = iv_versionid.
  ENDIF.

ENDMETHOD.
