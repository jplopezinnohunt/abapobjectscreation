METHOD get_entity.

  DATA: lo_exception         TYPE REF TO cx_hrpa_violated_assertion,
        lv_unkey             TYPE hcmt_bsp_pad_unkey,
        ls_mapping           TYPE hcmt_bsp_pad_tuid_mapping,
        lv_ui_structure_name TYPE strukname,
        lr_ui_structure      TYPE REF TO data,
        lr_ui_structure_tab  TYPE REF TO data,
        lv_locked            TYPE boole_d,
        dummy                TYPE char255,                  "#EC NEEDED
        ls_message           TYPE bapiret2.

  FIELD-SYMBOLS: <ls_ui_structure>    TYPE any,
                 <lv_object_key>      TYPE hcm_object_key,
                 <ls_ui_structure_xx> TYPE any,
                 <lt_ui_structure_xx> TYPE STANDARD TABLE.

  CLEAR: es_entity_main,
         et_field_metadata,
         es_help_values,
         et_validity_info,
         et_messages.

  lv_ui_structure_name = get_sname_using_versionid(
      iv_versionid         = iv_versionid ).

  CREATE DATA lr_ui_structure TYPE (lv_ui_structure_name).
  ASSIGN lr_ui_structure->* TO <ls_ui_structure>.

  CREATE DATA lr_ui_structure_tab TYPE TABLE OF (me->mv_xx_structure_name).
  ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure_xx>.

  IF et_field_metadata IS SUPPLIED.
* try to read edit properties
    CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
      EXPORTING
        iv_lock   = abap_true
        iv_pernr  = is_pskey-hcmfab_pernr
      IMPORTING
        ev_locked = lv_locked.
*        messages  = lt_messages.
  ENDIF.

  TRY.

      CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data
        IMPORTING
          main_records = <lt_ui_structure_xx>
          messages     = et_messages.

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

* get main record in country-dependent UI structure
        CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_data
          EXPORTING
            object_key  = <lv_object_key>
          IMPORTING
            main_record = <ls_ui_structure>.

        me->build_entity_from_ui_struc(
          EXPORTING
            is_pskey          = is_pskey
            is_ui_structure   = <ls_ui_structure>
            iv_locked         = lv_locked
            it_fieldnames     = it_fieldnames
          IMPORTING
            es_entity_main    = es_entity_main
            et_field_metadata = et_field_metadata
            es_help_values    = es_help_values
            et_messages       = et_messages
            et_validity_info  = et_validity_info ).


        IF lv_locked = abap_true.
* unlock PERNR
          CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
            EXPORTING
              iv_lock  = abap_false
              iv_pernr = is_pskey-hcmfab_pernr.
        ENDIF.

      ENDIF.

    CATCH cx_hrpa_violated_assertion INTO lo_exception.
      ls_message-type = 'E'.
      ls_message-message = lo_exception->if_message~get_text( ).
      APPEND ls_message TO et_messages.
  ENDTRY.

  IF es_entity_main IS INITIAL.
    MESSAGE e009(hcmfab_common) INTO dummy.
*    MOVE-CORRESPONDING sy TO ls_message.
    CALL FUNCTION 'BALW_BAPIRETURN_GET2'
      EXPORTING
        type          = sy-msgty
        cl            = sy-msgid
        number        = sy-msgno
        par1          = sy-msgv1
        par2          = sy-msgv2
        par3          = sy-msgv3
        par4          = sy-msgv4
      IMPORTING
        return        = ls_message
      EXCEPTIONS
        error-message = 0                               "#EC ARGCHECKED
        OTHERS        = 0.
    "we do not expect to get any exceptions here ...

    APPEND ls_message TO et_messages.
  ENDIF.

ENDMETHOD.
