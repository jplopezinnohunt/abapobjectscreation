METHOD get_default_entity.

  DATA: lt_subty_metadata    TYPE if_hrpa_pernr_infty_xss=>subty_metadata_tab,
        lo_exception         TYPE REF TO cx_hrpa_violated_assertion,
        ls_message           TYPE bapiret2,
        lv_ui_structure_name TYPE strukname,
        lr_ui_structure      TYPE REF TO data,
        lt_f4_ext            TYPE if_hrpa_pernr_infty_xss_ext=>tt_f4,
        lt_f4                TYPE hrxss_per_f4_t,
        ls_my_help_values    TYPE ty_s_help_values,
        lt_field_attributes  TYPE hrpad_obj_field_attribute_tab,
        lo_strucdescr        TYPE REF TO cl_abap_structdescr,
        ls_pskey             TYPE hcmfab_s_pers_pskey,
        lv_locked            TYPE boole_d,
        lv_pernr_itvers      TYPE itvers.

  FIELD-SYMBOLS: <ls_ui_structure>     TYPE any,
                 <lv_pernr>            TYPE pernr_d,
                 <lv_hcmfab_pernr>     TYPE pernr_d,
                 <lv_hcmfab_infty>     TYPE infty,
                 <lv_hcmfab_subty>     TYPE subty,
                 <lv_sprps>            TYPE sprps,
                 <lv_hcmfab_sprps>     TYPE sprps,
                 <lv_begda>            TYPE begda,
                 <lv_hcmfab_begda>     TYPE begda,
                 <lv_endda>            TYPE endda,
                 <lv_hcmfab_endda>     TYPE endda,
                 <lv_objps>            TYPE objps,
                 <lv_hcmfab_objps>     TYPE objps,
                 <lv_seqnr>            TYPE seqnr,
                 <lv_hcmfab_seqnr>     TYPE seqnr,
                 <ls_field_attributes> TYPE hrpad_obj_field_attribute,
                 <lv_object_key>       TYPE hcm_object_key,
                 <lv_land1>            TYPE land1.          "2709841


  CLEAR: es_default_entity,
         et_field_metadata,
         et_help_values,
         et_validity_info,
         et_messages.

  lv_ui_structure_name = get_sname_using_versionid(
      iv_versionid         = iv_versionid ).

  CREATE DATA lr_ui_structure TYPE (lv_ui_structure_name).
  ASSIGN lr_ui_structure->* TO <ls_ui_structure>.

  TRY.
      CALL METHOD mo_xss_adapter->read_metadata
        IMPORTING
          metadata_tab = lt_subty_metadata.

      READ TABLE lt_subty_metadata WITH KEY subty = iv_subty TRANSPORTING NO FIELDS. " ASSIGNING <ls_subty_metadata> .
      IF sy-subrc EQ 0.
* check whether IV_ITVERS = LV_PERNR_ITVERS -> don't pass ITVERS as adapter fills IV_ITVERS into ITVERS-Field of UI-structure
        lv_pernr_itvers = mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_itvers( '' ).
        IF iv_versionid = lv_pernr_itvers OR
          ( iv_versionid = '99' AND iv_country_versionid = lv_pernr_itvers ). "2653604
          CALL METHOD mo_xss_adapter->create
            EXPORTING
              subty    = iv_subty
            IMPORTING
              record   = <ls_ui_structure>
              messages = et_messages.
        ELSE.
          IF iv_versionid = '99' AND NOT iv_country_versionid IS INITIAL. "2653604
* we're creating a foreign address record based on the international backend functionality
            CALL METHOD mo_xss_adapter->create
              EXPORTING
                subty     = iv_subty
*               objps     =
*               line_data =
                itbld     = iv_country_versionid
              IMPORTING
                record    = <ls_ui_structure>
                messages  = et_messages.
          ELSE.
            CALL METHOD mo_xss_adapter->create
              EXPORTING
                subty     = iv_subty
*               objps     =
*               line_data =
                itbld     = iv_versionid
              IMPORTING
                record    = <ls_ui_structure>
                messages  = et_messages.
          ENDIF.
        ENDIF.

        ASSIGN COMPONENT gc_fname-pernr OF STRUCTURE <ls_ui_structure> TO <lv_pernr>.
        ASSIGN COMPONENT gc_fname-hcmfab_pernr OF STRUCTURE es_default_entity TO <lv_hcmfab_pernr>.
        <lv_hcmfab_pernr> = <lv_pernr>.
        ASSIGN COMPONENT gc_fname-hcmfab_infty OF STRUCTURE es_default_entity TO <lv_hcmfab_infty>.
        <lv_hcmfab_infty> = mv_infty.
        ASSIGN COMPONENT gc_fname-hcmfab_subty OF STRUCTURE es_default_entity TO <lv_hcmfab_subty>.
        <lv_hcmfab_subty> = iv_subty.
        ASSIGN COMPONENT gc_fname-objps OF STRUCTURE <ls_ui_structure> TO <lv_objps>.
        IF <lv_objps> IS ASSIGNED.
* field OBJPS is not avaialable in all UI structures
          ASSIGN COMPONENT gc_fname-hcmfab_objps OF STRUCTURE es_default_entity TO <lv_hcmfab_objps>.
          <lv_hcmfab_objps> = <lv_objps>.
        ENDIF.
        ASSIGN COMPONENT gc_fname-sprps OF STRUCTURE <ls_ui_structure> TO <lv_sprps>.
        ASSIGN COMPONENT gc_fname-hcmfab_sprps OF STRUCTURE es_default_entity TO <lv_hcmfab_sprps>.
        <lv_hcmfab_sprps> = <lv_sprps>.
        ASSIGN COMPONENT gc_fname-endda OF STRUCTURE <ls_ui_structure> TO <lv_endda>.
        ASSIGN COMPONENT gc_fname-hcmfab_endda OF STRUCTURE es_default_entity TO <lv_hcmfab_endda>.
        <lv_hcmfab_endda> = <lv_endda>.
        ASSIGN COMPONENT gc_fname-begda OF STRUCTURE <ls_ui_structure> TO <lv_begda>.
        ASSIGN COMPONENT gc_fname-hcmfab_begda OF STRUCTURE es_default_entity TO <lv_hcmfab_begda>.
        <lv_hcmfab_begda> = <lv_begda>.
        ASSIGN COMPONENT gc_fname-seqnr OF STRUCTURE <ls_ui_structure> TO <lv_seqnr>.
        IF <lv_seqnr> IS ASSIGNED.
          ASSIGN COMPONENT gc_fname-hcmfab_seqnr OF STRUCTURE es_default_entity TO <lv_hcmfab_seqnr>.
          <lv_hcmfab_seqnr> = <lv_seqnr>.
        ENDIF.

        IF mv_infty = '0006' AND NOT iv_country IS INITIAL. "2709841
* here a foreign address record is created based on T7XSSPERFORADR customizing
* based on a versionid <> 'country-versionid'
* we have to 'correct' the country as otherwise the depending F4-helps don't display the
* correct values
          ASSIGN COMPONENT gc_fname-land1 OF STRUCTURE <ls_ui_structure> TO <lv_land1>.
          IF NOT <lv_land1> IS ASSIGNED.
            ASSIGN COMPONENT gc_fname-kland1 OF STRUCTURE <ls_ui_structure> TO <lv_land1>.
          ENDIF.
          IF <lv_land1> IS ASSIGNED.
            <lv_land1> = iv_country.
          ENDIF.

        ENDIF.

        MOVE-CORRESPONDING <ls_ui_structure> TO es_default_entity.

        IF et_field_metadata IS SUPPLIED.

* try to read edit properties
          CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
            EXPORTING
              iv_lock   = abap_true
              iv_pernr  = mv_pernr
            IMPORTING
              ev_locked = lv_locked.
*      messages  = lt_messages.

          ASSIGN COMPONENT  gc_fname-object_key OF STRUCTURE <ls_ui_structure> TO <lv_object_key>.

          mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_data(
          EXPORTING
            object_key        = <lv_object_key>
          IMPORTING
*            ev_delete_allowed   = lv_delete_allowed
*            main_record         = <ls_ui_structure>    "n3299014
            et_field_attributes = lt_field_attributes ).
*            messages            = lt_messages ).

          READ TABLE lt_field_attributes INDEX 1 ASSIGNING <ls_field_attributes>.
          IF sy-subrc EQ 0.
            <ls_field_attributes>-object_key = <lv_object_key>. "OBJECT_KEY is not filled ...

            lo_strucdescr ?= cl_abap_structdescr=>describe_by_name( lv_ui_structure_name ).

            MOVE-CORRESPONDING es_default_entity TO ls_pskey.

            CALL METHOD me->map_field_attributes
              EXPORTING
                iv_object_key       = <lv_object_key>
                is_pskey            = ls_pskey
                iv_locked           = lv_locked
                it_field_attributes = lt_field_attributes
                it_components       = lo_strucdescr->components
                iv_versionid        = iv_versionid
              IMPORTING
                et_field_metadata   = et_field_metadata.

          ENDIF.

          IF lv_locked = abap_true.
* unlock PERNR
            CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
              EXPORTING
                iv_lock  = abap_false
                iv_pernr = mv_pernr.

          ENDIF.
        ENDIF.

* handle F4-helps
        IF et_help_values IS SUPPLIED AND NOT it_fieldnames IS INITIAL.
          CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_f4_values
            EXPORTING
              included_fields = it_fieldnames
              record          = <ls_ui_structure>
            IMPORTING
              f4table_ext     = lt_f4_ext
              f4table         = lt_f4.


          me->valuehelp_add_initial_entry(
                EXPORTING
                  it_field_metadata = et_field_metadata
                CHANGING
                  ct_f4 = lt_f4
                  ct_f4_ext = lt_f4_ext ).

          MOVE-CORRESPONDING es_default_entity TO ls_my_help_values.
          ls_my_help_values-help_values = lt_f4.
          ls_my_help_values-help_values_ext = lt_f4_ext.
          APPEND ls_my_help_values TO et_help_values.

        ENDIF.

        IF et_validity_info IS SUPPLIED.
          ASSIGN COMPONENT  gc_fname-object_key OF STRUCTURE <ls_ui_structure> TO <lv_object_key>.
          MOVE-CORRESPONDING es_default_entity TO ls_pskey.

          CALL METHOD me->get_validity_info
            EXPORTING
              iv_object_key     = <lv_object_key>
              is_pskey          = ls_pskey
              iv_is_create_mode = abap_true
            IMPORTING
              et_validity_info  = et_validity_info.

        ENDIF.

      ENDIF.

    CATCH cx_hrpa_violated_assertion INTO lo_exception.
      ls_message-type = 'E'.
      ls_message-message = lo_exception->if_message~get_text( ).
      APPEND ls_message TO et_messages.
  ENDTRY.

ENDMETHOD.
