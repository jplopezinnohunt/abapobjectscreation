METHOD get_entity_set.

  DATA: lo_exception         TYPE REF TO cx_hrpa_violated_assertion,
        lv_unkey             TYPE hcmt_bsp_pad_unkey,
        ls_pskey             TYPE pskey,
        lv_ui_structure_name TYPE strukname,
        lr_ui_structure_tab  TYPE REF TO data,
        lr_ui_struc          TYPE REF TO data,
        lt_messages          TYPE bapirettab,
        lv_pernr_itvers      TYPE itvers,
        lt_field_metadata    TYPE ty_t_fieldmetadata,
        ls_help_values       TYPE ty_s_help_values,
        lv_locked            TYPE boole_d,
        ls_message           TYPE bapiret2,
        lt_validity_info     TYPE ty_t_validity_info.

  FIELD-SYMBOLS: <ls_main_record>     TYPE any,
                 <lt_ui_structure>    TYPE ANY TABLE,
                 <ls_ui_structure>    TYPE any,
                 <ls_entity_ui_struc> TYPE any,
                 <lv_object_key>      TYPE hcm_object_key,
                 <lv_itbld>           TYPE itbld,
                 <ls_ui_structure_xx> TYPE any,
                 <lt_ui_structure_xx> TYPE ANY TABLE.


  CLEAR: et_entity_set_main,
         et_field_metadata,
         et_help_values,
         et_validity_info,
         et_messages.

  lv_pernr_itvers = mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_itvers( '' ).

  lv_ui_structure_name =  me->get_sname_using_versionid( iv_versionid = iv_versionid ).

  CREATE DATA lr_ui_structure_tab TYPE TABLE OF (lv_ui_structure_name).
  ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure>.

  CREATE DATA lr_ui_struc TYPE (lv_ui_structure_name).
  ASSIGN lr_ui_struc->* TO <ls_entity_ui_struc>.

  IF et_field_metadata IS SUPPLIED.
* lock PERNR to be able to read edit properties
    CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock
      EXPORTING
        iv_lock   = abap_true
        iv_pernr  = mv_pernr
      IMPORTING
        ev_locked = lv_locked
        messages  = lt_messages.
  ENDIF.

  TRY.
      IF lv_pernr_itvers = iv_versionid "read data for PERNR_ITVERS
        OR lv_ui_structure_name = mv_xx_structure_name. "read data in international format

        CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data
          IMPORTING
            main_records        = <lt_ui_structure>
*           et_delete_allowed   = lt_delete_allowed     "always false as PERNR not locked!!!
*           et_field_attributes = lt_field_attributes   "not filled here
            messages            = et_messages.

        LOOP AT <lt_ui_structure> ASSIGNING <ls_ui_structure>.
          ASSIGN COMPONENT gc_fname-itbld OF STRUCTURE <ls_ui_structure> TO <lv_itbld>.

          IF <lv_itbld> IS ASSIGNED
            AND lv_ui_structure_name <> mv_xx_structure_name
            AND NOT <lv_itbld> IS INITIAL
            AND NOT <lv_itbld> = iv_versionid.
            CONTINUE.
          ENDIF.
          APPEND INITIAL LINE TO et_entity_set_main ASSIGNING <ls_main_record>.
* get complete PSKEY from tuid mapper
          ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE <ls_ui_structure> TO <lv_object_key>.
          go_tuid_mapper->read_mapping( EXPORTING tuid = <lv_object_key>
                                        IMPORTING unkey = lv_unkey ).
          ls_pskey = lv_unkey.

          CLEAR lt_field_metadata.
          CLEAR ls_help_values.

          IF et_field_metadata IS SUPPLIED AND et_help_values IS SUPPLIED AND et_validity_info IS SUPPLIED.
            me->build_entity_from_ui_struc(
            EXPORTING
              is_pskey          = ls_pskey
              is_ui_structure   = <ls_ui_structure>
              iv_locked         = lv_locked
              it_fieldnames     = it_fieldnames
            IMPORTING
              es_entity_main    = <ls_main_record>
              et_field_metadata = lt_field_metadata
              es_help_values    = ls_help_values
              et_validity_info  = lt_validity_info
              et_messages       = lt_messages ) .

            APPEND LINES OF lt_field_metadata TO et_field_metadata.
            APPEND ls_help_values TO et_help_values.
            APPEND LINES OF lt_validity_info TO et_validity_info.
            APPEND LINES OF lt_messages TO et_messages.

          ELSEIF et_field_metadata IS SUPPLIED.
            me->build_entity_from_ui_struc(
            EXPORTING
              is_pskey          = ls_pskey
              is_ui_structure   = <ls_ui_structure>
              iv_locked         = lv_locked
              it_fieldnames     = it_fieldnames
            IMPORTING
              es_entity_main    = <ls_main_record>
              et_field_metadata = lt_field_metadata
              et_messages       = lt_messages ) .

            APPEND LINES OF lt_field_metadata TO et_field_metadata.
            APPEND LINES OF lt_messages TO et_messages.

          ELSEIF et_help_values IS SUPPLIED AND NOT it_fieldnames IS INITIAL.
            me->build_entity_from_ui_struc(
            EXPORTING
              is_pskey          = ls_pskey
              is_ui_structure   = <ls_ui_structure>
              iv_locked         = lv_locked
              it_fieldnames     = it_fieldnames
            IMPORTING
              es_entity_main    = <ls_main_record>
              es_help_values    = ls_help_values
              et_messages       = lt_messages ) .

            APPEND ls_help_values TO et_help_values.
            APPEND LINES OF lt_messages TO et_messages.

          ELSEIF et_validity_info IS SUPPLIED.
            me->build_entity_from_ui_struc(
            EXPORTING
              is_pskey          = ls_pskey
              is_ui_structure   = <ls_ui_structure>
              iv_locked         = lv_locked
              it_fieldnames     = it_fieldnames
            IMPORTING
              es_entity_main    = <ls_main_record>
              et_validity_info  = lt_validity_info
              et_messages       = lt_messages ) .

            APPEND LINES OF lt_validity_info TO et_validity_info.
            APPEND LINES OF lt_messages TO et_messages.

          ELSE.
            me->build_entity_from_ui_struc(
            EXPORTING
              is_pskey          = ls_pskey
              is_ui_structure   = <ls_ui_structure>
              iv_locked         = lv_locked
              it_fieldnames     = it_fieldnames
            IMPORTING
              es_entity_main    = <ls_main_record>
              et_messages       = lt_messages ) .

            APPEND LINES OF lt_messages TO et_messages.

          ENDIF.

        ENDLOOP.

      ELSE.
* retrieve data in XX-structure
        CREATE DATA lr_ui_structure_tab TYPE TABLE OF (me->mv_xx_structure_name).
        ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure_xx>.

        CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data
          IMPORTING
            main_records = <lt_ui_structure_xx>
            messages     = et_messages.

        LOOP AT <lt_ui_structure_xx> ASSIGNING <ls_ui_structure_xx>.
          ASSIGN COMPONENT gc_fname-itbld OF STRUCTURE <ls_ui_structure_xx> TO <lv_itbld>.
*          IF NOT <lv_itbld> IS ASSIGNED OR <lv_itbld> = iv_versionid.                                "Note 2652973
           IF NOT <lv_itbld> IS ASSIGNED OR <lv_itbld> = iv_versionid OR <lv_itbld> IS INITIAL.       "Note 2652973
            ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE <ls_ui_structure_xx> TO <lv_object_key>.
            APPEND INITIAL LINE TO et_entity_set_main ASSIGNING <ls_main_record>.
* map record to UI structure corresponding of 'caller versionid'
            CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_data
              EXPORTING
                object_key  = <lv_object_key>
              IMPORTING
                main_record = <ls_entity_ui_struc>.

* get complete PSKEY from tuid mapper
            go_tuid_mapper->read_mapping( EXPORTING tuid = <lv_object_key>
                                          IMPORTING unkey = lv_unkey ).
            ls_pskey = lv_unkey.

            CLEAR lt_field_metadata.
            CLEAR ls_help_values.

            IF et_field_metadata IS SUPPLIED AND et_help_values IS SUPPLIED AND et_validity_info IS SUPPLIED.
              me->build_entity_from_ui_struc(
              EXPORTING
                is_pskey          = ls_pskey
                is_ui_structure   = <ls_entity_ui_struc>
                iv_locked         = lv_locked
                it_fieldnames     = it_fieldnames
              IMPORTING
                es_entity_main    = <ls_main_record>
                et_field_metadata = lt_field_metadata
                es_help_values    = ls_help_values
                et_validity_info  = lt_validity_info
                et_messages       = lt_messages ) .

              APPEND LINES OF lt_field_metadata TO et_field_metadata.
              APPEND ls_help_values TO et_help_values.
              APPEND LINES OF lt_validity_info TO et_validity_info.
              APPEND LINES OF lt_messages TO et_messages.

            ELSEIF et_field_metadata IS SUPPLIED.
              me->build_entity_from_ui_struc(
              EXPORTING
                is_pskey          = ls_pskey
                is_ui_structure   = <ls_entity_ui_struc>
                iv_locked         = lv_locked
                it_fieldnames     = it_fieldnames
              IMPORTING
                es_entity_main    = <ls_main_record>
                et_field_metadata = lt_field_metadata
                et_messages       = lt_messages ) .

              APPEND LINES OF lt_field_metadata TO et_field_metadata.
              APPEND LINES OF lt_messages TO et_messages.

            ELSEIF et_help_values IS SUPPLIED.
              me->build_entity_from_ui_struc(
              EXPORTING
                is_pskey          = ls_pskey
                is_ui_structure   = <ls_entity_ui_struc>
                iv_locked         = lv_locked
                it_fieldnames     = it_fieldnames
              IMPORTING
                es_entity_main    = <ls_main_record>
                es_help_values    = ls_help_values
                et_messages       = lt_messages ) .

              APPEND ls_help_values TO et_help_values.
              APPEND LINES OF lt_messages TO et_messages.

            ELSEIF et_validity_info IS SUPPLIED.
              me->build_entity_from_ui_struc(
              EXPORTING
                is_pskey          = ls_pskey
                is_ui_structure   = <ls_entity_ui_struc>
                iv_locked         = lv_locked
                it_fieldnames     = it_fieldnames
              IMPORTING
                es_entity_main    = <ls_main_record>
                et_validity_info  = lt_validity_info
                et_messages       = lt_messages ) .

              APPEND LINES OF lt_validity_info TO et_validity_info.
              APPEND LINES OF lt_messages TO et_messages.

            ELSE.
              me->build_entity_from_ui_struc(
              EXPORTING
                is_pskey          = ls_pskey
                is_ui_structure   = <ls_entity_ui_struc>
                iv_locked         = lv_locked
                it_fieldnames     = it_fieldnames
              IMPORTING
                es_entity_main    = <ls_main_record>
                et_messages       = lt_messages ) .

              APPEND LINES OF lt_messages TO et_messages.
            ENDIF.

          ENDIF.
        ENDLOOP.

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
        iv_pernr = mv_pernr.

  ENDIF.

ENDMETHOD.
