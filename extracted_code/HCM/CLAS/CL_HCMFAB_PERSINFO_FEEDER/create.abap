METHOD create.

  DATA lo_exception TYPE REF TO cx_hrpa_violated_assertion.
  DATA ls_pskey TYPE hcmfab_s_pers_pskey.
  DATA lv_ui_structure_name TYPE strukname.
  DATA lr_ui_structure TYPE REF TO data.
  DATA lt_subty_metadata TYPE if_hrpa_pernr_infty_xss=>subty_metadata_tab.
  DATA lv_group_name TYPE ddgroup.
  DATA ls_screen_header TYPE hrpad00screen_header.
  DATA ls_message TYPE bapiret2.
  DATA lv_locked TYPE boole_d.
  DATA lv_default_versionid TYPE hcmfab_versionid.
  DATA lv_eahrrxx TYPE dlvunit VALUE 'EA-HRRXX'. "#EC NOTEXT    "2709841
  DATA lv_compvers TYPE saprelease.                         "2709841
  DATA lv_mapped_versionid TYPE hcmfab_versionid.           "2774032
  DATA lo_persinfo_update_badi TYPE REF TO hcmfab_b_persinfo_update_data. "2964654
  DATA lv_call_badi TYPE boole_d.                           "2964654
  DATA ls_badi_pskey TYPE pskey.                            "2964654

  FIELD-SYMBOLS <ls_ui_structure> TYPE any.
  FIELD-SYMBOLS <ls_entity_ui_struc> TYPE any.
  FIELD-SYMBOLS <lv_object_key> TYPE hcm_object_key.
  FIELD-SYMBOLS <lv_object_key_main> TYPE hcm_object_key.
  FIELD-SYMBOLS <ls_pskey_main> TYPE hcmfab_s_pers_pskey.
  FIELD-SYMBOLS <ls_subty_metadata> TYPE if_hrpa_pernr_infty_xss=>subty_metadata.
  FIELD-SYMBOLS <lv_begda> TYPE begda.
  FIELD-SYMBOLS <lv_endda> TYPE endda.
  FIELD-SYMBOLS <lv_pernr> TYPE pernr_d.
  FIELD-SYMBOLS <lv_infty> TYPE infty.

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

  ls_pskey = is_pskey.

  lv_ui_structure_name =  me->get_sname_using_versionid(
      iv_versionid         = iv_versionid ).

  CREATE DATA lr_ui_structure TYPE (lv_ui_structure_name).
  ASSIGN lr_ui_structure->* TO <ls_ui_structure>.

  TRY.
      CALL METHOD mo_xss_adapter->read_metadata
        IMPORTING
          metadata_tab = lt_subty_metadata
          today        = mv_user_today.

      READ TABLE lt_subty_metadata WITH KEY subty = ls_pskey-hcmfab_subty ASSIGNING  <ls_subty_metadata>.
      IF sy-subrc EQ 0.
* create default record in XSS adapter to initialize buffers
        lv_default_versionid = get_default_versionid( ).
        lv_mapped_versionid = get_mapped_versionid(         "2904969
          iv_versionid = lv_default_versionid
          iv_pernr     = mv_pernr
          iv_infty     = mv_infty ).
        IF lv_mapped_versionid IS INITIAL.
          lv_mapped_versionid = lv_default_versionid.
        ENDIF.
        IF ls_pskey-hcmfab_infty = '0006' AND iv_versionid <> lv_mapped_versionid "2774032
          AND iv_versionid <> lv_default_versionid.         "2964654
* here we have to pass VersionId
          CALL METHOD mo_xss_adapter->create
            EXPORTING
              subty     = ls_pskey-hcmfab_subty
              objps     = ls_pskey-hcmfab_objps
*             line_data =
              itbld     = iv_versionid
            IMPORTING
              record    = <ls_ui_structure>
              messages  = et_messages.
        ELSE.
          CALL METHOD mo_xss_adapter->create
            EXPORTING
              subty     = ls_pskey-hcmfab_subty
              objps     = ls_pskey-hcmfab_objps
*             line_data =
*             itbld     = iv_versionid
            IMPORTING
              record    = <ls_ui_structure>
              messages  = et_messages.
        ENDIF.

        IF ls_pskey-hcmfab_begda IS INITIAL.
          ASSIGN COMPONENT gc_fname-begda OF STRUCTURE <ls_ui_structure> TO <lv_begda>.
          ls_pskey-hcmfab_begda = <lv_begda>.
        ENDIF.
        IF ls_pskey-hcmfab_endda IS INITIAL.
          ASSIGN COMPONENT gc_fname-endda OF STRUCTURE <ls_ui_structure> TO <lv_endda>.
          ls_pskey-hcmfab_endda = <lv_endda>.
        ENDIF.

        ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE <ls_ui_structure> TO <lv_object_key>.
        ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE cs_main_record TO <lv_object_key_main>.
        <lv_object_key_main> = <lv_object_key>.
        ASSIGN COMPONENT gc_groupname_pskey OF STRUCTURE cs_main_record TO <ls_pskey_main>.
        <ls_pskey_main> = ls_pskey.

*update BEGDA/ENDDA
        MOVE-CORRESPONDING <ls_ui_structure> TO ls_screen_header.
        ls_screen_header-begda = ls_pskey-hcmfab_begda.
        ls_screen_header-endda = ls_pskey-hcmfab_endda.
* update UI structure fields
        ASSIGN COMPONENT gc_fname-begda OF STRUCTURE cs_main_record TO <lv_begda>.
        <lv_begda> = ls_pskey-hcmfab_begda.
        ASSIGN COMPONENT gc_fname-endda OF STRUCTURE cs_main_record TO <lv_endda>.
        <lv_endda> = ls_pskey-hcmfab_endda.
        ASSIGN COMPONENT gc_fname-pernr OF STRUCTURE cs_main_record TO <lv_pernr>.
        <lv_pernr> = ls_pskey-hcmfab_pernr.
        ASSIGN COMPONENT gc_fname-infty OF STRUCTURE cs_main_record TO <lv_infty>.
        IF <lv_infty> IS ASSIGNED.
          <lv_infty> = ls_pskey-hcmfab_infty.
        ENDIF.

        CONCATENATE 'UI_' ls_pskey-hcmfab_infty INTO lv_group_name.
        ASSIGN COMPONENT lv_group_name OF STRUCTURE cs_main_record TO <ls_entity_ui_struc>.
        MOVE-CORRESPONDING <ls_entity_ui_struc> TO <ls_ui_structure>.
        MOVE-CORRESPONDING ls_screen_header TO <ls_ui_structure>.

* get component release version of EA-HRRXX
        CALL FUNCTION 'DELIVERY_GET_COMPONENT_RELEASE'      "2709841
          EXPORTING
            iv_compname         = lv_eahrrxx
         IMPORTING
           ev_compvers          = lv_compvers
           EXCEPTIONS                                       "3255326
           comp_not_found       = 1
           OTHERS               = 2  .

        IF sy-subrc <> 0.
* with SAP HCM for S/4 HANA On-Premise EA-HRRXX is not available anymore. The corresponding
* software component in S/4 HANA is S4HCMRXX  100 covering all necesary functionality
          CLEAR lv_compvers.
        ENDIF.

        IF lv_compvers = '605'.                             "2709841
          CALL METHOD mo_xss_adapter->modify
            IMPORTING
              messages = et_messages
            CHANGING
              record   = <ls_ui_structure>.
        ELSE.
          CALL METHOD mo_xss_adapter->modify2
            IMPORTING
              messages = et_messages
            CHANGING
              record   = <ls_ui_structure>.
        ENDIF.

        MOVE-CORRESPONDING <ls_ui_structure> TO <ls_entity_ui_struc>.

        READ TABLE et_messages WITH KEY type = 'E' TRANSPORTING NO FIELDS.
        IF sy-subrc NE 0. "no error messages found -> save data
          CLEAR et_messages.
          IF iv_no_save IS INITIAL.
            mo_xss_adapter->save( IMPORTING messages = et_messages ).
            READ TABLE et_messages WITH KEY type = 'E' TRANSPORTING NO FIELDS.
            IF sy-subrc NE 0. "no error messages found -> call BAdi
              lv_call_badi = abap_true.                     "2964654
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
* call badi hcmfab_b_persinfo_update_data to allow updating of further business data
    GET BADI lo_persinfo_update_badi
      FILTERS
        infty = mv_infty.

    ls_badi_pskey = get_pskey_from_hcmfab_pskey( ls_pskey ).

    CALL BADI lo_persinfo_update_badi->create
      EXPORTING
        is_pskey             = ls_badi_pskey
        is_uinnnn            = <ls_ui_structure>
        iv_versionid         = iv_versionid
        iv_ui_structure_name = lv_ui_structure_name.
  ENDIF.

ENDMETHOD.
