* XRK 20180213 Note 2602438 Authority check and anonymize data
*              New method
METHOD auth_check_and_anonymize_data.                       "#EC NEEDED

* code moved to CL_HCMFAB_FB_TCAL_SETTINGS

*  DATA: no_authcheck    TYPE c,
*        lt_employees    TYPE pernr_us_tab,
*        lv_pernr        TYPE pernr_d,
*        constraints     TYPE ptarq_tconstr,
*        lv_is_manager   TYPE c,
*        message_handler TYPE REF TO if_pt_req_message_handler,
*        message_wa      TYPE  LINE OF ptreq_message_tab.
*
*  FIELD-SYMBOLS: <ls_data_list> TYPE ptarq_attabsdata_struc,
*                 <ls_employee>  TYPE pernr_us,
*                 <abs>          TYPE p2001,
*                 <atts>         TYPE p2002.
*
*  et_data_list = it_data_list.
*
** Fetch personnel number from sy-uname
*  CALL FUNCTION 'HR_GET_EMPLOYEES_FROM_USER_DB'
*    EXPORTING
*      user   = sy-uname
*      begda  = sy-datum
*      endda  = sy-datum
*    TABLES
*      ee_tab = lt_employees.
*  READ TABLE lt_employees INDEX 1 ASSIGNING <ls_employee>.
*  IF sy-subrc EQ 0 AND NOT <ls_employee>-pernr IS INITIAL.
*    lv_pernr = <ls_employee>-pernr.
*  ELSE.
**     Missing PA0105 customizing
*    message_wa-message_v1 = sy-uname.
*    IF 1 = 2.
**---Workaround for where-used list
*      MESSAGE e075(hrtim_abs_req) WITH sy-uname.
*    ENDIF.
**---Create message handler singleton
*    CALL METHOD cl_pt_req_message_handler=>instance_get
*      RECEIVING
*        result = message_handler.
*    CALL METHOD message_handler->add_message
*      EXPORTING
*        im_type       = 'E'
*        im_cl         = 'HRTIM_ABS_REQ'
*        im_number     = '075'
*        im_par1       = message_wa-message_v1
*        im_context    = 'GET_ABSENCE_DATA'
*        im_classname  = 'CL_HCMFAB_COMMON_DPC_EXT'
*        im_methodname = 'AUTH_CHECK_AND_ANONYMIZE_DATA'.
*  ENDIF.
*
** Get customizing for constraints
*  CALL METHOD cl_pt_arq_customizing=>get_time_constraints
*    EXPORTING
*      im_pernr       = lv_pernr
*      im_date        = sy-datum
*    IMPORTING
*      ex_constraints = constraints
*    EXCEPTIONS
*      OTHERS         = 1.
*  IF sy-subrc NE 0.
*    "error handling
*  ENDIF.
*
** Check if given employee is manager
*  CALL METHOD go_employee_api->is_manager
*    EXPORTING
*      iv_application_id = ''
*      iv_pernr          = lv_pernr
*    RECEIVING
*      rv_is_manager     = lv_is_manager.
** Deactivate infotype authority check based on IMG customizing
*  IF lv_is_manager EQ 'X'.
*    IF NOT constraints-mss_no_authcheck IS INITIAL.
*      no_authcheck = 'X'.
*    ENDIF.
*  ELSE.
*    IF NOT constraints-ess_no_authcheck IS INITIAL.
*      no_authcheck = 'X'.
*    ENDIF.
*  ENDIF.
*
** Process all absence/attendance data records
*  LOOP AT et_data_list ASSIGNING <ls_data_list>.
*    IF no_authcheck IS INITIAL. "perform authorization check
**     process absences
*      LOOP AT <ls_data_list>-abs_attribs ASSIGNING <abs>.
*        IF <abs>-pernr NE lv_pernr. "auth_check not necessary if person wants to see own data
*          CALL FUNCTION 'HR_CHECK_AUTHORITY_INFTY'
*            EXPORTING
*              tclas            = 'A'
*              pernr            = <abs>-pernr
*              infty            = <abs>-infty
*              subty            = <abs>-subty
*              begda            = <abs>-begda
*              endda            = <abs>-endda
*              level            = 'R'
*              uname            = sy-uname
*            EXCEPTIONS
*              no_authorization = 1
*              internal_error   = 2
*              OTHERS           = 3.
**         No authorization --> clear subtype for later anonymization
*          IF sy-subrc NE 0.
*            CLEAR <abs>-subty.
*          ENDIF.
*        ENDIF.
*      ENDLOOP.
**     process attendances
*      LOOP AT <ls_data_list>-atts_attribs ASSIGNING <atts>.
*        IF <atts>-pernr NE lv_pernr. "auth_check not necessary if person wants to see own data
*          CALL FUNCTION 'HR_CHECK_AUTHORITY_INFTY'
*            EXPORTING
*              tclas            = 'A'
*              pernr            = <atts>-pernr
*              infty            = <atts>-infty
*              subty            = <atts>-subty
*              begda            = <atts>-begda
*              endda            = <atts>-endda
*              level            = 'R'
*              uname            = sy-uname
*            EXCEPTIONS
*              no_authorization = 1
*              internal_error   = 2
*              OTHERS           = 3.
**         No authorization --> clear subtype for later anonymization
*          IF sy-subrc NE 0.
*            CLEAR <atts>-subty.
*          ENDIF.
*        ENDIF.
*      ENDLOOP.
*    ENDIF.
*  ENDLOOP.

ENDMETHOD.
