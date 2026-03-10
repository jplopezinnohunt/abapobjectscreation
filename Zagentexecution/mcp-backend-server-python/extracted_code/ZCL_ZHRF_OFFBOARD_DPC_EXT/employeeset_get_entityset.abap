method employeeset_get_entityset.
  data: lv_err_msg               type bapi_msg,
        lt_employees             type zv_hrfiori_req_tt,
        ls_employee              type zv_hrfiori_req,
        lv_pernr                 type persno,
        ls_return                type bapiret2,
        lv_top                   type i,
        lv_skip                  type i,
        lv_full_count            type i,
        LV_OBJECTID              TYPE SAEOBJID,
        LV_AR_OBJECT             TYPE SAEOBJART,
        lo_offboarding           type ref to zcl_hr_fiori_offboarding_req,
        lt_filter_select_options type /iwbep/t_mgw_select_option,
        lv_reason                type string..

  " Instanciation
  try.
      lo_offboarding = zcl_hr_fiori_offboarding_req=>get_instance( ).
    catch cx_root into data(lx_exception).
      message id 'ZHRFIORI' type 'E' number '110'
        into lv_err_msg with lx_exception->get_text( ).
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid  = /iwbep/cx_mgw_busi_exception=>business_error
          message = lv_err_msg.
  endtry.

  " Récupération des filtres OData (sans transformation ActionType)
  lt_filter_select_options = io_tech_request_context->get_filter( )->get_filter_select_options( ).

  "get Pernr from 0105
  select single pernr into @lv_pernr
        from pa0105
          where subty = '0001'
            and endda >= @sy-datum
            and begda <= @sy-datum
            and usrid = @sy-uname .
  if sy-subrc ne 0.
    ls_return-type    = 'E'.
*    rs_return-message = 'The PERNR is empty.'.
    message id 'ZHRFIORI' type 'E' number '058'
      into ls_return-message.
    raise exception type /iwbep/cx_mgw_busi_exception
      exporting
        textid  = /iwbep/cx_mgw_busi_exception=>business_error
        message = ls_return-message.
  endif.

  " Pagination
  lv_top  = io_tech_request_context->get_top( ).
  lv_skip = io_tech_request_context->get_skip( ).

  " Appel de la méthode métier
  call method lo_offboarding->get_requests_by_pernr
    exporting
      iv_pernr    = lv_pernr
      it_filters  = lt_filter_select_options
    importing
      et_requests = lt_employees
    receiving
      rs_return   = ls_return.

  if ls_return-type = 'E'.
    raise exception type /iwbep/cx_mgw_busi_exception
      exporting
        textid  = /iwbep/cx_mgw_busi_exception=>business_error
        message = ls_return-message.
  endif.

* TICKET 1697
  LOOP AT LT_EMPLOYEES INTO LS_EMPLOYEE.
    IF LS_EMPLOYEE-SEP_LETTER_STAF = ' '.
*      delete LT_EMPLOYEES from LS_EMPLOYEE  .
      DELETE LT_EMPLOYEES where GUID = LS_EMPLOYEE-guid.
    endif.

*    LV_OBJECTID = LS_EMPLOYEE-creator_pernr && LS_EMPLOYEE-EFFECTIVE_DATE.
*
*    if LS_EMPLOYEE-ACTION_TYPE = '01'. " 01 Separation
*      LV_AR_OBJECT = 'YHRSEPLET'.
*    ELSE. " 00  Leave without pay
*       LV_AR_OBJECT = 'YHRLWOPLET'.
*    ENDIF.
*    select single object_id into LV_OBJECTID from toahr where sap_object = 'PREL' and object_id = LV_OBJECTID and AR_OBJECT = LV_AR_OBJECT .
*    if sy-subrc ne 0.
*      delete LT_EMPLOYEES from LS_EMPLOYEE.
*    endif.

  ENDLOOP.
* end ticket 1697

  " Nombre total avant pagination
  lv_full_count = lines( lt_employees ).

  " Pagination : skip
  if lv_skip > 0.
    data(lv_count) = lines( lt_employees ).
    if lv_skip >= lv_count.
      clear lt_employees.
    else.
      delete lt_employees from 1 to lv_skip.
    endif.
  endif.

  " Pagination : top
  if lv_top > 0.
    data(lv_count2) = lines( lt_employees ).
    if lv_top < lv_count2.
      delete lt_employees from lv_top + 1.
    endif.
  endif.

  " Conversion EntitySet
  loop at lt_employees into ls_employee.
    append initial line to et_entityset assigning field-symbol(<fs_entity>).

    <fs_entity>-guid         = ls_employee-guid.
    <fs_entity>-creatorpernr = ls_employee-creator_pernr.
    <fs_entity>-creatorfname = ls_employee-creator_fname.
    <fs_entity>-creatorlname = ls_employee-creator_lname.
    " Texte Reason
    try.
        lv_reason = lo_offboarding->get_domain_value_text(
                         iv_domain_name  = 'ZD_HRFIORI_REASON'
                         iv_domain_value = to_upper( condense( ls_employee-reason ) )
                         iv_language     = sy-langu ).
        <fs_entity>-reason = cond #( when lv_reason is not initial then lv_reason else ls_employee-reason ).
      catch cx_root.
        <fs_entity>-reason = ls_employee-reason.
    endtry.

    " ActionType : garder la clé brute
    <fs_entity>-actiontype   = ls_employee-action_type.

    " Dates
    <fs_entity>-effectivedate = cond #( when ls_employee-effective_date is not initial
                                        and ls_employee-effective_date <> '00000000'
                                        then ls_employee-effective_date ).
    <fs_entity>-endda = cond #( when ls_employee-endda is not initial
                                and ls_employee-endda <> '00000000'
                                then ls_employee-endda ).
    <fs_entity>-seqno = ls_employee-seqno.
    <fs_entity>-status = cond #(
     when ls_employee-cancelled = 'X'          "CANCELLED
*       then c_cancelled
       then text-006
     when ls_employee-closed = 'X'             "CLOSED
*       then c_completed
       then text-007
     else
*       c_in_progress                       "IN PROGRESS
        text-005
  ).
  endloop.

  " Inlinecount
  if io_tech_request_context->has_inlinecount( ) = abap_true.
    es_response_context-inlinecount = lv_full_count.
  endif.
endmethod.
