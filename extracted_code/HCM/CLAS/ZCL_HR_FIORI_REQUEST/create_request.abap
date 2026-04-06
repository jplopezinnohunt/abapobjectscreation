  METHOD create_request.

*&- ----------------------------------------------------------------------- -&*
*&- CREATE - Processing (Save in BD minimalist Request with default values  )
*&- ----------------------------------------------------------------------- -&*

    DATA(ls_request_header) = CORRESPONDING zthrfiori_breq( cs_request ).
    DATA :lo_util        TYPE REF TO zcl_hr_fiori_benefits.

    TRY.
        CALL METHOD cl_system_uuid=>create_uuid_x16_static
          RECEIVING
            uuid = ls_request_header-guid.
      CATCH cx_uuid_error.
        RAISE EXCEPTION TYPE cx_os_internal_error.
    ENDTRY.

*          RequestKey             -> to be generated
    ls_request_header-request_key  = get_request_req_key( iv_request_type =   ls_request_header-request_type ).
*CATCH zcx_hr_benef_exception. " Exception class for Benefits

*          RequestDesc            -> from front
*          RequestType            -> from front
*          RequestTypeTxt         -> deducted from RequestType
*        ls_request_header-request_type_txt = 'EDUCATION GRANT'.
    SELECT SINGLE name INTO  @ls_request_header-request_type_txt FROM zthrfiori_reqtyp WHERE id EQ @ls_request_header-request_type AND language EQ @sy-langu.
*          RequestStatus          -> from front
*          RequestStatusTxt       -> deducted from RequestStatus
    SELECT SINGLE name INTO  @ls_request_header-request_status_txt FROM zthrfiori_status WHERE id EQ @ls_request_header-request_status AND language EQ @sy-langu.
*          Info           -> deducted
    ls_request_header-request_status_txt =  ls_request_header-request_status_txt .
*    ls_request_header-info1 = cond #( case  (  ls_request_header-request_type eq '01' and ls_request_header-isclaim eq abap_true ) then |Claim| else .
    IF ls_request_header-request_type EQ '01'.
      ls_request_header-info1 = COND #( WHEN ls_request_header-isclaim EQ abap_true  THEN |Claim| ELSE  |Advance| ).
    ENDIF.

    ls_request_header-info2 = ''.
    ls_request_header-info3 = sy-datum(4).
*    ls_request_header-info3 = |{ ls_request_header-begda } - { ls_request_header-endda }|.
*          CreationDate           -> automatic
    ls_request_header-creation_date = sy-datum.
*          CreationTime           -> automatic
    ls_request_header-creation_time = sy-uzeit.
*          CreatorUsrId           -> automatic
    ls_request_header-creator_usr_id = sy-uname.


*ls_request_header-LAS
*        Pernr
*    SELECT SINGLE pernr FROM pa0105 INTO @ls_request_header-creator_pernr
*          WHERE usrid EQ  @sy-uname AND subty EQ '0001' AND begda LE @ls_request_header-endda AND endda GE @ls_request_header-begda..

    CREATE OBJECT lo_util.
*   Get actor infos (current user)
    lo_util->get_actor_infos( IMPORTING ov_first_name = ls_request_header-creator_fname
                               ov_last_name = ls_request_header-creator_lname
                               ov_pernr = ls_request_header-creator_pernr
                               ov_usrid =  ls_request_header-creator_usr_id ).

    "in creation upd = creation infos ( for timeline etc )
    ls_request_header-last_upd_date = ls_request_header-creation_date.
    ls_request_header-last_upd_time = ls_request_header-creation_time.
    ls_request_header-upd_usr_id    = ls_request_header-creator_usr_id.
    ls_request_header-upd_pernr     = ls_request_header-creator_pernr.
    ls_request_header-upd_lname     = ls_request_header-creator_lname.
    ls_request_header-upd_fname     = ls_request_header-creator_fname.

*PERSG
    SELECT SINGLE persg FROM pa0001 INTO @ls_request_header-persg
              WHERE pernr EQ  @ls_request_header-creator_pernr  AND begda LE @ls_request_header-endda AND endda GE @ls_request_header-begda..

*CHILD_NAME
*update in detail
    ls_request_header-next_actor = '02'. "HRA in all cases
*NEXT_ACTOR_TXT

* * DB Inserts

    INSERT zthrfiori_breq FROM ls_request_header.
    IF sy-subrc NE 0.
*          MESSAGE e002 WITH 'ZTHR_REQ_POS' INTO sy-msgli.
**      RAISE EXCEPTION TYPE zcx_hr_preq_symsg
**        MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
**        WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
    ENDIF.

**************************************************************************************************************************************
*************************   "init default request details for EG or RS in main detail tables  ****************************************
**************************************************************************************************************************************
    init_default_values_request(
               EXPORTING
                 is_request_header =     ls_request_header              " Fiori - Benefits request header
               IMPORTING
                 ev_subrc          =    DATA(l_subrc)               " Subroutines for return code
             ).

*****************************************************************************************
*************************   "Update table Histo  ****************************************
*****************************************************************************************
    init_table_histo_log(
       EXPORTING
         is_request_header =                 ls_request_header  " Fiori - Benefits request header
       IMPORTING
         ev_subrc          =                 l_subrc  " Subroutines for return code
     ).

*****************************************************************************************
*************************   "Commit or Rollback  ****************************************
*****************************************************************************************
    IF l_subrc EQ 0.
      "Commit si tout est ok
      CALL FUNCTION 'BAPI_TRANSACTION_COMMIT' EXPORTING  wait = abap_true.
      COMMIT WORK.
    ELSE.
      CALL FUNCTION 'BAPI_TRANSACTION_ROLLBACK' EXPORTING  wait = abap_true.
      ROLLBACK WORK.
    ENDIF.

    "Return
    cs_request = CORRESPONDING #( ls_request_header ).

*&- Create TimeLine
*    DATA(ls_timeline) = CORRESPONDING zthr_req_timel( cs_request ).
*    CASE cs_request-version .
*      WHEN '1'.
*        CALL METHOD mo_db_handler->create_timeline(
*          EXPORTING
*            is_timeline = ls_timeline
*            iv_action   = co_ui_action-create
*        ).
*      WHEN OTHERS.
*        CALL METHOD mo_db_handler->create_timeline(
*          EXPORTING
*            is_timeline = ls_timeline
*            iv_action   = co_ui_action-new_version
*        ).
*    ENDCASE.


*&- ----------------------------------------------------------------------- -&*
*&- CREATE - Post-Processing
*&- ----------------------------------------------------------------------- -&*

*    CALL METHOD create_post_processing(
*      CHANGING
*        cs_request = cs_request ).




  ENDMETHOD.
