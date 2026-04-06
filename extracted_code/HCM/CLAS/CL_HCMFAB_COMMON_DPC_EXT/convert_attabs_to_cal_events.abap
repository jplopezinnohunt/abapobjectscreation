* XRK 20180628 Note 2650135 Additional fields - lines not marked
* XRK 20180213 Note 2602438 Authority check and anonymize data - lines not marked
METHOD convert_attabs_to_cal_events.                        "#EC NEEDED

* code moved to CL_HCMFAB_FB_TCAL_SETTINGS

*  DATA: ls_cal_event    TYPE hcmfab_s_tcal_event,
*        lt_attabs_types TYPE attabs_type_tab,
*        lt_attabs_list  TYPE ptarq_attabsdata_tab,
*        lv_tabix        TYPE sy-tabix,
*        lt_attabs_attributes TYPE attabs_attributes_tab.
*
*  FIELD-SYMBOLS: <attabs_struc>                TYPE ptarq_attabsdata_struc,
*                 <non_anonymized_attabs_struc> TYPE ptarq_attabsdata_struc,
*                 <ls_attabs_type>              TYPE attabs_type_struc,
*                 <non_anonymized_abs>          TYPE p2001,
*                 <abs>                         TYPE p2001,
*                 <non_anonymized_atts>         TYPE p2002,
*                 <atts>                        TYPE p2002.
*
** Always use the date range as event description
*  ls_cal_event-description = '{DATERANGE}'.
** Is it a tentative event?
*  ls_cal_event-is_tentative = is_cal_event-is_tentative.
** Anonymize data
*  CALL METHOD me->auth_check_and_anonymize_data
*    EXPORTING
*      it_data_list = it_attabs_list
*    IMPORTING
*      et_data_list = lt_attabs_list.
*
*  LOOP AT lt_attabs_list ASSIGNING <attabs_struc>.
*    lv_tabix = sy-tabix.
*    ls_cal_event-absenceoperation = <attabs_struc>-operation.
*
**   Process all absences
*    ls_cal_event-event_category = if_hcmfab_tcal_constants=>gc_event_category-leave.
*    LOOP AT <attabs_struc>-abs_attribs ASSIGNING <abs>.
*      CONCATENATE <abs>-subty ',' is_cal_event-absencestatus ',' ls_cal_event-absenceoperation INTO ls_cal_event-event_subcategory.
*
**     Get possible attendance and absence types
*      CALL METHOD cl_pt_arq_customizing=>get_attabs_types_and_attribs
*        EXPORTING
*          im_pernr             = <abs>-pernr
*          im_begda             = <abs>-begda
*          im_endda             = <abs>-endda
*        IMPORTING
*          ex_attabs_types      = lt_attabs_types
*          ex_attabs_attributes = lt_attabs_attributes
*        EXCEPTIONS
*          OTHERS               = 1.
**     Get non-anonymized subtype to determine status text
*      READ TABLE it_attabs_list INDEX lv_tabix ASSIGNING <non_anonymized_attabs_struc>.
*      LOOP AT <non_anonymized_attabs_struc>-abs_attribs ASSIGNING <non_anonymized_abs>.
*        ls_cal_event-absencestatus = is_cal_event-absencestatus.
*        CALL METHOD me->get_status_text
*          EXPORTING
*            it_attabs_attributes = lt_attabs_attributes
*            iv_subtype           = <non_anonymized_abs>-subty
*            iv_status            = is_cal_event-absencestatus
*          IMPORTING
*            ev_status_text       = ls_cal_event-absencestatustext.
*      ENDLOOP.
**     Fill calendar event with absence data
*      ls_cal_event-employee_id = <abs>-pernr.
*      ls_cal_event-start_date = <abs>-begda.
*      ls_cal_event-end_date = <abs>-endda.
*      ls_cal_event-start_time = <abs>-beguz.
*      ls_cal_event-end_time = <abs>-enduz.
*      ls_cal_event-absencedays = <abs>-abwtg.
*      ls_cal_event-absencehours = <abs>-stdaz.
*      ls_cal_event-title = '{ABSENCETYPE_OPERATION}'.
**     Check if absence type can be added to calendar
*      IF <abs>-subty IS INITIAL.
*        CLEAR ls_cal_event-absencetype.
*        ls_cal_event-absencetypetext = text-005. "text: 'absent'
*        APPEND ls_cal_event TO ct_calendar_events.
*      ELSE.
*        READ TABLE lt_attabs_types WITH KEY subty = <abs>-subty ASSIGNING <ls_attabs_type>.
*        IF sy-subrc EQ 0.
*          ls_cal_event-absencetype = <abs>-subty.
*          ls_cal_event-absencetypetext = <ls_attabs_type>-subtytext.
*          APPEND ls_cal_event TO ct_calendar_events.
*        ENDIF.
*      ENDIF.
*    ENDLOOP.
*
**   Process all attendances
*    ls_cal_event-event_category = if_hcmfab_tcal_constants=>gc_event_category-attendance.
*    LOOP AT <attabs_struc>-atts_attribs ASSIGNING <atts>.
*      CONCATENATE <atts>-subty ',' is_cal_event-absencestatus ',' ls_cal_event-absenceoperation INTO ls_cal_event-event_subcategory.
*
**   Get possible attendance and absence types
*      CALL METHOD cl_pt_arq_customizing=>get_attabs_types_and_attribs
*        EXPORTING
*          im_pernr             = <atts>-pernr
*          im_begda             = <atts>-begda
*          im_endda             = <atts>-endda
*        IMPORTING
*          ex_attabs_types      = lt_attabs_types
*          ex_attabs_attributes = lt_attabs_attributes
*        EXCEPTIONS
*          OTHERS               = 1.
**     Get non-anonymized subtype to determine status text
*      READ TABLE it_attabs_list INDEX lv_tabix ASSIGNING <non_anonymized_attabs_struc>.
*      LOOP AT <non_anonymized_attabs_struc>-atts_attribs ASSIGNING <non_anonymized_atts>.
*        ls_cal_event-absencestatus = is_cal_event-absencestatus.
*        CALL METHOD me->get_status_text
*          EXPORTING
*            it_attabs_attributes = lt_attabs_attributes
*            iv_subtype           = <non_anonymized_atts>-subty
*            iv_status            = is_cal_event-absencestatus
*          IMPORTING
*            ev_status_text       = ls_cal_event-absencestatustext.
*      ENDLOOP.
**     Fill calendar event with attendance data
*      ls_cal_event-employee_id = <atts>-pernr.
*      ls_cal_event-start_date = <atts>-begda.
*      ls_cal_event-end_date = <atts>-endda.
*      ls_cal_event-start_time = <atts>-beguz.
*      ls_cal_event-end_time = <atts>-enduz.
*      ls_cal_event-absencedays = <atts>-abwtg.
*      ls_cal_event-absencehours = <atts>-stdaz.
*      ls_cal_event-title = '{ABSENCETYPE_OPERATION}'.
**     Check if attendance type can be added to calendar
*      IF <atts>-subty IS INITIAL.
*        CLEAR ls_cal_event-absencetype.
*        ls_cal_event-absencetypetext = text-006. "text: 'present'
*        APPEND ls_cal_event TO ct_calendar_events.
*      ELSE.
*        READ TABLE lt_attabs_types WITH KEY subty = <atts>-subty ASSIGNING <ls_attabs_type>.
*        IF sy-subrc EQ 0.
*          ls_cal_event-absencetype = <atts>-subty.
*          ls_cal_event-absencetypetext = <ls_attabs_type>-subtytext.
*          APPEND ls_cal_event TO ct_calendar_events.
*        ENDIF.
*      ENDIF.
*    ENDLOOP.
*  ENDLOOP.

ENDMETHOD.
