METHOD update.

  DATA lo_exception TYPE REF TO cx_hrpa_violated_assertion.
  DATA lv_ui_structure_name TYPE strukname.
  DATA lr_ui_structure TYPE REF TO data.
  DATA lr_ui_entity TYPE REF TO data.
  DATA lr_ui_structure_tab TYPE REF TO data.
  DATA lv_group_name TYPE ddgroup.
  DATA ls_message TYPE bapiret2.
  DATA lv_unkey TYPE hcmt_bsp_pad_unkey.
  DATA ls_mapping TYPE hcmt_bsp_pad_tuid_mapping.
  DATA lv_default_versionid TYPE hcmfab_versionid.
  DATA lv_locked TYPE boole_d.
  DATA lv_eahrrxx TYPE dlvunit VALUE 'EA-HRRXX'. "#EC NOTEXT    "2709841
  DATA lv_compvers TYPE saprelease.                         "2709841
  DATA lv_mapped_versionid TYPE hcmfab_versionid.           "2774032
  DATA lv_struc_versionid TYPE hcmfab_versionid.            "2807656
  DATA lo_persinfo_update_badi TYPE REF TO hcmfab_b_persinfo_update_data. "2964654
  DATA lr_old_uinnnn TYPE REF TO data.                      "2964654
  DATA lv_call_badi TYPE boole_d.                           "2964654
  DATA ls_badi_pskey TYPE pskey.                            "2964654

  FIELD-SYMBOLS <ls_orig_record> TYPE any.
  FIELD-SYMBOLS <lt_ui_structure> TYPE STANDARD TABLE.
  FIELD-SYMBOLS <lv_object_key> TYPE hcm_object_key.
  FIELD-SYMBOLS <lv_object_key_orig> TYPE hcm_object_key.
  FIELD-SYMBOLS <ls_ui_entity> TYPE any.
  FIELD-SYMBOLS <ls_ui_entity_orig> TYPE any.
  FIELD-SYMBOLS <lv_itbld> TYPE itbld.
  FIELD-SYMBOLS <lv_uname> TYPE aenam.
  FIELD-SYMBOLS <lv_aedtm> TYPE aedat.
  FIELD-SYMBOLS <ls_old_uinnnn> TYPE any.                   "2964654
  FIELD-SYMBOLS <ls_new_uinnnn> TYPE any.                   "2964654
  FIELD-SYMBOLS <lv_begda> TYPE begda.                      "2964654
  FIELD-SYMBOLS <lv_endda> TYPE endda.                      "2964654

  IF iv_no_save IS INITIAL.
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

  ENDIF.

  CLEAR et_messages.

* we need to re-construct the original record in order to find the right OBJECT_KEY to modify
  lv_default_versionid = me->get_default_versionid( ).

  lv_mapped_versionid = get_mapped_versionid(               "2904969
          iv_versionid = iv_versionid
          iv_pernr     = mv_pernr
          iv_infty     = mv_infty ).

  IF lv_mapped_versionid IS INITIAL.
    lv_mapped_versionid = lv_default_versionid.
  ENDIF.

  IF mv_infty <> '0006'.                                    "2807656
    lv_struc_versionid = lv_mapped_versionid.
  ELSE.
    lv_struc_versionid = get_mapped_versionid(              "2904969
          iv_versionid = lv_default_versionid
          iv_pernr     = mv_pernr
          iv_infty     = mv_infty ).
    IF lv_struc_versionid IS INITIAL.
      lv_struc_versionid = lv_default_versionid.
    ENDIF.
  ENDIF.

  lv_ui_structure_name = me->get_sname_using_versionid(
      iv_versionid         = lv_struc_versionid ).          "2807656

  CREATE DATA lr_ui_structure_tab TYPE TABLE OF (lv_ui_structure_name).
  ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure>.

  CREATE DATA lr_ui_structure TYPE (lv_ui_structure_name).
  ASSIGN lr_ui_structure->* TO <ls_orig_record>.
  ASSIGN lr_ui_structure->* TO <ls_new_uinnnn>.             "2964654

  CREATE DATA lr_old_uinnnn TYPE (lv_ui_structure_name).    "2964654
  ASSIGN lr_old_uinnnn->* TO <ls_old_uinnnn>. "here we need a copy

  TRY.
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

      READ TABLE <lt_ui_structure> WITH KEY (gc_fname-object_key) = ls_mapping-tuid ASSIGNING <ls_orig_record>.
      IF <ls_orig_record> IS ASSIGNED.
        <ls_old_uinnnn> = <ls_orig_record>.                 "2964654
        ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE <ls_orig_record> TO <lv_object_key_orig>.
        ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE cs_entity_main TO <lv_object_key>.
        <lv_object_key> = <lv_object_key_orig>.
        CONCATENATE 'UI_' is_pskey-hcmfab_infty INTO lv_group_name.
        ASSIGN COMPONENT lv_group_name OF STRUCTURE cs_entity_main TO <ls_ui_entity>.
        ASSIGN COMPONENT gc_fname-uname OF STRUCTURE <ls_ui_entity> TO <lv_uname>.
        <lv_uname> = sy-uname.
        ASSIGN COMPONENT gc_fname-aedtm OF STRUCTURE <ls_ui_entity> TO <lv_aedtm>.
        <lv_aedtm> = sy-datum.
        ASSIGN COMPONENT gc_fname-itbld OF STRUCTURE <ls_ui_entity> TO <lv_itbld>.
* get component release version of EA-HRRXX
        CALL FUNCTION 'DELIVERY_GET_COMPONENT_RELEASE'      "2709841
          EXPORTING
            iv_compname         = lv_eahrrxx
         IMPORTING
           ev_compvers          = lv_compvers
         EXCEPTIONS                                         "3255326
           comp_not_found       = 1
           OTHERS               = 2  .

        IF sy-subrc <> 0.
* with SAP HCM for S/4 HANA On-Premise EA-HRRXX is not available anymore. The corresponding
* software component in S/4 HANA is S4HCMRXX  100 covering all necesary functionality
          CLEAR lv_compvers.
        ENDIF.

        IF mv_infty = '0006' AND iv_versionid <> lv_struc_versionid "2807656
          AND <lv_itbld> IS ASSIGNED AND NOT <lv_itbld> IS INITIAL. "2964654
* foreign address -> read record in foreign UI structure
          IF <lv_itbld> = lv_mapped_versionid.              "2807656
            lv_ui_structure_name = me->get_sname_using_versionid( iv_versionid = lv_mapped_versionid ). "2807656
            CREATE DATA lr_ui_entity TYPE (lv_ui_structure_name).
            ASSIGN lr_ui_entity->* TO <ls_ui_entity_orig>.
            ASSIGN lr_ui_entity->* TO <ls_new_uinnnn>.      "2964654
* get main record in foreign UI structure
            CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_data
              EXPORTING
                object_key  = <lv_object_key>
              IMPORTING
                main_record = <ls_ui_entity_orig>.

            MOVE-CORRESPONDING <ls_ui_entity> TO <ls_ui_entity_orig>.
            IF lv_compvers = '605'.                         "2709841
              CALL METHOD mo_xss_adapter->modify
                IMPORTING
                  messages = et_messages
                CHANGING
                  record   = <ls_ui_entity_orig>.
            ELSE.
              CALL METHOD mo_xss_adapter->modify2
                IMPORTING
                  messages = et_messages
                CHANGING
                  record   = <ls_ui_entity_orig>.
            ENDIF.
            <ls_new_uinnnn> = <ls_ui_entity_orig>.          "2964654
          ELSE.
                                                            "#EC NEEDED
* message .... "Wrong versionid" ...
          ENDIF.
        ELSE.
          IF <lv_itbld> IS ASSIGNED AND NOT <lv_itbld> IS INITIAL. "2774032
* we must not have ITBLD filled for records <> foreign address
            CLEAR <lv_itbld>.
          ENDIF.
          MOVE-CORRESPONDING <ls_ui_entity> TO <ls_orig_record>.
          IF lv_compvers = '605'.                           "2709841
            CALL METHOD mo_xss_adapter->modify
              IMPORTING
                messages = et_messages
              CHANGING
                record   = <ls_orig_record>.
          ELSE.
            CALL METHOD mo_xss_adapter->modify2
              IMPORTING
                messages = et_messages
              CHANGING
                record   = <ls_orig_record>.
          ENDIF.
          <ls_new_uinnnn> = <ls_orig_record>.               "2964654
        ENDIF.
        READ TABLE et_messages WITH KEY type = 'E' TRANSPORTING NO FIELDS.
        IF sy-subrc NE 0. "no error messages found -> save data
          CLEAR et_messages.
          IF iv_no_save IS INITIAL.
            mo_xss_adapter->save( IMPORTING messages = et_messages ).
            READ TABLE et_messages WITH KEY type = 'E' TRANSPORTING NO FIELDS.
            IF sy-subrc NE 0. "no error messages found -> call BAdi
              lv_call_badi = abap_true.
            ENDIF.
          ENDIF.
        ENDIF.
      ENDIF.
    CATCH cx_hrpa_violated_assertion INTO lo_exception.
      ls_message-type = 'E'.
      ls_message-message = lo_exception->if_message~get_text( ).
      APPEND ls_message TO et_messages.
  ENDTRY.

* unlock PERNR
  CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
    EXPORTING
      iv_lock  = abap_false
      iv_pernr = mv_pernr.

  IF lv_call_badi = abap_true.                              "2964654
* call BAdI HCMFAB_B_PERSINFO_UPDATE_DATA to allow updating of further business data
    ls_badi_pskey = get_pskey_from_hcmfab_pskey( is_pskey ).
* update pskey with new begda/endda
    ASSIGN COMPONENT gc_fname-begda OF STRUCTURE <ls_new_uinnnn> TO <lv_begda>.
    ASSIGN COMPONENT gc_fname-endda OF STRUCTURE <ls_new_uinnnn> TO <lv_endda>.

    ls_badi_pskey-begda = <lv_begda>.
    ls_badi_pskey-endda = <lv_endda>.

    GET BADI lo_persinfo_update_badi
      FILTERS
        infty = mv_infty.

    CALL BADI lo_persinfo_update_badi->update
      EXPORTING
        is_pskey             = ls_badi_pskey
        is_old_uinnnn        = <ls_old_uinnnn>
        is_new_uinnnn        = <ls_new_uinnnn>
        iv_versionid         = iv_versionid
        iv_ui_structure_name = lv_ui_structure_name.
  ENDIF.

ENDMETHOD.
