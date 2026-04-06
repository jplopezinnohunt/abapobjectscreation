METHOD benefiteventset_get_entityset.
  DATA:ls_ben_event            TYPE rpbenevent,
       ls_ee_benefit_data      TYPE rpbeneedat,
       ls_filter               TYPE /iwbep/s_mgw_select_option,
       ls_benefitevent         TYPE cl_hcmfab_ben_enrollme_mpc=>ts_benefitevent,
       ls_enroll_event         TYPE rpbenenrollmentreason,
       ls_filter_range         TYPE /iwbep/s_cod_select_option,
       ls_t100_msg             TYPE scx_t100key.

  DATA:lt_error_table          TYPE hrben00err_ess,
       ls_error_table          TYPE rpbenerr,
       lt_enroll_event         TYPE hrben00enrollmentreason,
       lt_assignments          TYPE pccet_pernr,
       lt_events_docu          TYPE TABLE OF hcmfab_ben_event,
       ls_event_docu           TYPE hcmfab_ben_event .

  DATA:lv_eff_begdate          TYPE sy-datum,
       lv_eff_enddate          TYPE sy-datum,
       lv_subrc                TYPE sy-subrc,
       lv_pernr                TYPE pernr_d,
       lv_barea                TYPE ben_area,
       lv_datum                TYPE sy-datum,
       lv_psmop                TYPE ben_psmop,
       lv_psmad                TYPE ben_psmad,
       lv_assignment           TYPE pcce_pernr,
       lv_psmfo                TYPE ben_psmfo.
  DATA:lo_employee_api     TYPE REF TO cl_hcmfab_employee_api,
       lx_badi_error       TYPE REF TO cx_hcmfab_benefits_enrollment,
       lx_exception        TYPE REF TO cx_static_check.

  IF  iv_filter_string   IS NOT INITIAL
        AND it_filter_select_options IS INITIAL.
*    " If the string of the Filter System Query Option is not automatically converted into
*    " filter option table (lt_filter_select_options), then the filtering combination is not supported
*    " Log message in the application log
    me->/iwbep/if_sb_dpc_comm_services~log_message(
      EXPORTING
        iv_msg_type   = 'E'
        iv_msg_id     = '/IWBEP/MC_SB_DPC_ADM'
        iv_msg_number = 025 ).
*    " Raise Exception
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_tech_exception
      EXPORTING
        textid = /iwbep/cx_mgw_tech_exception=>internal_error.
  ENDIF.
  CLEAR: lv_pernr, lv_datum, lv_barea,lt_events_docu.
* Get the filter data
  LOOP AT it_filter_select_options INTO ls_filter.
    READ TABLE ls_filter-select_options INTO ls_filter_range INDEX 1.
    CASE ls_filter-property.
      WHEN 'EmployeeNumber'.
        lv_pernr = ls_filter_range-low.
    ENDCASE.
  ENDLOOP.
  lv_datum = sy-datum. "Events or Open offer is always fetched for today's date.
  TRY.
* Check if Pernr is valid or not
      go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).
* Ensure Pernr is not locked ( Enqueued )
      CLEAR: lt_error_table, ls_error_table.
      CALL METHOD me->read_pernr_lock
        EXPORTING
          iv_pernr       = lv_pernr
        IMPORTING
          et_error_table = lt_error_table.
      IF lt_error_table IS NOT INITIAL.
        READ TABLE lt_error_table INTO ls_error_table INDEX 1.
        CLEAR:ls_t100_msg.
        ls_t100_msg-msgid = ls_error_table-class.
        ls_t100_msg-msgno = ls_error_table-msgno.
        ls_t100_msg-attr1 = ls_error_table-msgv1.
        ls_t100_msg-attr2 = ls_error_table-msgv2.
        ls_t100_msg-attr3 = ls_error_table-msgv3.
        ls_t100_msg-attr4 = ls_error_table-msgv4.

        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid = ls_t100_msg.
      ENDIF.
      CLEAR:lt_enroll_event,lv_subrc,lv_barea.
*Get all enrollment events for pernr
      CALL FUNCTION 'HR_BEN_ESS_RFC_ENRO_REASONS'
        EXPORTING
          pernr              = lv_pernr
          datum              = lv_datum
        IMPORTING
          enrollment_reasons = lt_enroll_event
          error_table        = lt_error_table
          subrc              = lv_subrc.

      IF lt_enroll_event IS INITIAL.
*****No valid events exists
        CLEAR:ls_t100_msg.
        ls_t100_msg-msgid = c_msg_class_enro.
        ls_t100_msg-msgno = '007'.
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid = ls_t100_msg.
      ENDIF.
      CLEAR:ls_ee_benefit_data, lv_subrc.
      CALL FUNCTION 'HR_BEN_READ_EE_BENEFIT_DATA'
        EXPORTING
          pernr           = lv_pernr
          datum           = lv_datum
          reaction        = c_reaction_x
        IMPORTING
          ee_benefit_data = ls_ee_benefit_data
          subrc           = lv_subrc
        TABLES
          error_table     = lt_error_table.

      READ TABLE lt_enroll_event INTO ls_enroll_event INDEX 1.
      lv_barea = ls_enroll_event-barea.
* Check whether paycheck simualtion can be offered
      CLEAR lv_subrc.
      CALL FUNCTION 'HR_BEN_ESS_GET_SETTINGS'
        EXPORTING
          barea       = lv_barea
          reaction    = c_reaction_n
        IMPORTING
          psmop       = lv_psmop
          psmad       = lv_psmad
          psmfo       = lv_psmfo
          error_table = lt_error_table
          subrc       = lv_subrc.
*Check for events terms and condition
      SELECT * FROM hcmfab_ben_event INTO TABLE lt_events_docu WHERE barea = lv_barea.
      IF sy-subrc = 0.
        SORT lt_events_docu BY event enrty.
        SORT lt_enroll_event BY event enrty.
      ELSE.
*    --- raise exception when no events are maintained in the customizing table
****No valid events exists
        CLEAR ls_t100_msg.
        ls_t100_msg-msgid = c_msg_class_enro.
        ls_t100_msg-msgno = '000'.
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid = ls_t100_msg.
      ENDIF.

      CLEAR:ls_enroll_event.
* Build the event table for the pernr
      LOOP AT lt_events_docu INTO ls_event_docu.
*  LOOP AT lt_enroll_event INTO ls_enroll_event.
        READ TABLE lt_enroll_event INTO ls_enroll_event WITH KEY event = ls_event_docu-event
                                                                 enrty = ls_event_docu-enrty.
        IF sy-subrc <> 0.
          CONTINUE.
        ENDIF.
        MOVE-CORRESPONDING ls_enroll_event TO ls_benefitevent.
        MOVE-CORRESPONDING ls_enroll_event TO ls_ben_event.
        ls_benefitevent-enrol_begda = ls_enroll_event-begda.
        ls_benefitevent-enrol_endda = ls_enroll_event-endda.
        ls_benefitevent-doc_object = ls_event_docu-doc_object.
*Get effective dates for the event
        CALL FUNCTION 'HR_BEN_GET_PROCESS_DATES'
          EXPORTING
            event_description = ls_ben_event
            enrty             = ls_benefitevent-enrty
            datum             = sy-datum
            reaction          = c_reaction_n
          IMPORTING
            process_begda     = lv_eff_begdate
            process_endda     = lv_eff_enddate
            subrc             = lv_subrc
          TABLES
            error_table       = lt_error_table
          CHANGING
            ee_benefit_data   = ls_ee_benefit_data.

        ls_benefitevent-eff_begda = lv_eff_begdate.
        ls_benefitevent-eff_endda = lv_eff_enddate.

        CASE ls_enroll_event-enrty.
          WHEN 'O'.
            IF lv_psmfo IS NOT INITIAL OR lv_psmop IS NOT INITIAL..
              ls_benefitevent-simu = 'X'.
            ENDIF.
          WHEN 'E'.
            IF lv_psmfo IS NOT INITIAL OR lv_psmad IS NOT INITIAL..
              ls_benefitevent-simu = 'X'.
            ENDIF.
        ENDCASE.
        me->enrich_event( CHANGING evententity = ls_benefitevent ).
        APPEND ls_benefitevent TO et_entityset.
        CLEAR:ls_event_docu,ls_benefitevent,ls_ben_event,lv_eff_begdate,lv_eff_enddate,lv_subrc,ls_enroll_event.
      ENDLOOP.
    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
    CATCH cx_hcmfab_benefits_enrollment INTO lx_badi_error.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_badi_error )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
