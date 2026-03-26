method update_request.

  data: lv_count               type i,
        lv_lname               type pad_nachn,
        lv_fname               type pad_vorna,
        ls_status              type zthrfiori_reqsta,
        ls_previous_status     type zthrfiori_reqsta,
        lt_all_previous_status type table of zthrfiori_reqsta,
        ls_updater_return      type bapiret2,
        lv_existing_guid       type ze_hrfiori_guidreq,
        ls_approval            type zthrfiori_dapprv,
        lv_approval_seqno      type seqno,
        lv_success             type char1,
        ls_return              type bapiret2 ##NEEDED,
        lv_validation_type     type ze_hrfiori_valtype,
        lv_comments            type ze_hrfiori_comments,
        lv_max_seqno           type seqno,
        lv_exec_mode           type ze_hrfiori_execmode,
        lv_step_value          type c,
        lv_max_seqno_num       type i,
        lv_max_appr_seq        type seqno,
        lv_updater_to_use      type persno,
        lv_persnumber          type usr21-persnumber,
        lv_detected_step       type string.

  clear: ev_seqno, ev_previous_status, ev_new_status, ev_updater_name.

  " 1. FIND OR CREATE GUID
  if cv_guid is initial.
    select single guid
      from zv_hrfiori_req
      into lv_existing_guid
      where creator_pernr = iv_pernr
        and action_type   = iv_action_type
        and reason        = iv_reason
        and closed <> 'X'
        and cancelled <> 'X'.
    if sy-subrc = 0.
      cv_guid = lv_existing_guid.
    endif.
  endif.

  if cv_guid is initial.
    lv_success = me->create_request(
      exporting
        iv_pernr          = iv_pernr
        iv_updater        = iv_updater
        iv_action_type    = iv_action_type
        iv_reason         = iv_reason
        iv_endda          = sy-datum
        iv_effective_date = iv_effective
      importing
        es_return         = ls_return
    ).
    if lv_success <> 'X'.
      rv_ok = '-'.
      ev_new_status = c_error_create_request.
      return.
    endif.
  endif.

  " 2. LOAD ALL PREVIOUS STATUSES
  clear lt_all_previous_status.
  if cv_guid is not initial.
    select * into table lt_all_previous_status
      from zthrfiori_reqsta
      where guid = cv_guid
      order by seqno ascending.
  endif.

  clear ls_previous_status.
  if lt_all_previous_status is not initial.
    ls_previous_status = lt_all_previous_status[ lines( lt_all_previous_status ) ].
    ev_previous_status = c_status_found.
  else.
    ev_previous_status = c_no_status.
    clear ls_status.
    ls_status-guid = cv_guid.
  endif.

  " 3. INITIALIZE ls_status WITH PREVIOUS DATA
  if iv_merged_status is not initial and iv_merged_status-guid is not initial.
    move-corresponding iv_merged_status to ls_status.
    ls_status-guid = cv_guid.
  elseif ls_previous_status-guid is not initial.
    ls_status = ls_previous_status.
  else.
    ls_status-guid = cv_guid.
  endif.

  " 4. RESOLVE UPDATER NAME
  clear: lv_lname, lv_fname, ev_updater_name, lv_updater_to_use.

  if iv_updater is initial or iv_updater = '00000000'.
    select single pernr into lv_updater_to_use
      from pa0105
      where uname = sy-uname
        and endda >= sy-datum
        and begda <= sy-datum
        and subty = '0001'.
    if sy-subrc <> 0.
      select single persnumber into lv_persnumber
        from usr21
        where bname = sy-uname.
      if sy-subrc = 0.
        lv_updater_to_use = lv_persnumber.
        condense lv_updater_to_use no-gaps.
      endif.
    endif.
  else.
    lv_updater_to_use = iv_updater.
  endif.

  if lv_updater_to_use is not initial and lv_updater_to_use <> '00000000'.

    ls_updater_return = me->get_employee_data(
      exporting iv_persno = lv_updater_to_use
      importing ev_nachn  = lv_lname
                ev_vorna  = lv_fname
    ).
  endif.

  if lv_lname is initial or ls_updater_return-type = 'E'.
    lv_lname = sy-uname.
    lv_fname = 'User' ##NO_TEXT.
    ev_updater_name = sy-uname.
  else.
    ev_updater_name = |{ lv_fname } { lv_lname }|.
  endif.

  " 🔍 5. DETECT WHICH STEP IS BEING VALIDATED (comparaison entre ancien et nouveau)
  clear lv_detected_step.

  if iv_merged_status is initial.
    data(lv_step) = iv_step.
    data ls_merged type zthrfiori_reqsta .
    lv_step = to_upper( iv_step ).

    assign component lv_step of structure ls_merged to field-symbol(<fs>).
    if sy-subrc eq 0.
      <fs> = abap_true.
    endif.

  else .
    ls_merged = iv_merged_status.
  endif.

  " Vérifier quelle étape a changé entre ls_previous_status et iv_merged_status
  if ls_merged-request_init = 'X' and ls_previous_status-request_init <> 'X'.
    lv_detected_step = c_request_init.
  elseif ls_merged-sep_slwop = 'X' and ls_previous_status-sep_slwop <> 'X'.
    lv_detected_step = c_sep_slwop.
  elseif ls_merged-sep_letter_staf = 'X' and ls_previous_status-sep_letter_staf <> 'X'.
    lv_detected_step = c_sep_staf.
  elseif ls_merged-sep_slwop_oth_parties = 'X' and ls_previous_status-sep_slwop_oth_parties <> 'X'.
    lv_detected_step = c_sep_oth_parties.
  elseif ls_merged-checkout = 'X' and ls_previous_status-checkout <> 'X'.
    lv_detected_step = c_checkout.
  elseif ls_merged-checkout_completed = 'X' and ls_previous_status-checkout_completed <> 'X'.
    lv_detected_step = c_checkout_completed.
  elseif ls_merged-checkout_cancelled = 'X' and ls_previous_status-checkout_cancelled <> 'X'.
    lv_detected_step = c_checkout_cancelled.
  elseif ls_merged-travel = 'X' and ls_previous_status-travel <> 'X'.
    lv_detected_step = c_travel.
  elseif ls_merged-shipment = 'X' and ls_previous_status-shipment <> 'X'.
    lv_detected_step = c_shipment.
  elseif ls_merged-salary_suspense = 'X' and ls_previous_status-salary_suspense <> 'X'.
    lv_detected_step = c_salary_suspense.
  elseif ls_merged-action_rec_iris = 'X' and ls_previous_status-action_rec_iris <> 'X'.
    lv_detected_step = c_action_rec_iris.
  elseif ls_merged-paf = 'X' and ls_previous_status-paf <> 'X'.
    lv_detected_step = c_paf.
  elseif ls_merged-closed = 'X' and ls_previous_status-closed <> 'X'.
    lv_detected_step = c_close_request.

    "--------------------------En attente de confirmation----------------------------------------
  elseif ls_merged-cancelled = 'X' and ls_previous_status-cancelled <> 'X'.
    lv_detected_step = c_cancelled.
  endif.
  "--------------------------------------------------------------------------------------------

  " 6. CHECK IF SELECTED STEP ALREADY VALIDATED
  clear: lv_step_value.

  if lv_detected_step is not initial.
    case lv_detected_step.
      when c_request_init.              lv_step_value = ls_previous_status-request_init.
      when c_sep_slwop.                 lv_step_value = ls_previous_status-sep_slwop.
      when c_sep_staf.                  lv_step_value = ls_previous_status-sep_letter_staf.
      when c_sep_oth_parties.           lv_step_value = ls_previous_status-sep_slwop_oth_parties.
      when c_checkout.                  lv_step_value = ls_previous_status-checkout.
      when c_checkout_completed.        lv_step_value = ls_previous_status-checkout_completed.
      when c_checkout_cancelled.        lv_step_value = ls_previous_status-checkout_cancelled.
      when c_travel.                    lv_step_value = ls_previous_status-travel.
      when c_shipment.                  lv_step_value = ls_previous_status-shipment.
      when c_salary_suspense.           lv_step_value = ls_previous_status-salary_suspense.
      when c_action_rec_iris.           lv_step_value = ls_previous_status-action_rec_iris.
      when c_paf.                       lv_step_value = ls_previous_status-paf.
      when c_close_request.             lv_step_value = ls_previous_status-closed.

        "--------------------En attente de confirmation---------------------------------------------
      when c_cancelled.                 lv_step_value = ls_previous_status-cancelled.
        "-------------------------------------------------------------------------------------------

    endcase.

    if lv_step_value = 'X'
      and lv_detected_step ne c_close_request
      and iv_comments is initial.
      rv_ok = '-'.
      ev_new_status = c_error_step_already_validated.
      return.
    endif.
  endif.

  " 7. COMPUTE NEXT SEQNO
  lv_max_seqno_num = 0.
  select max( seqno ) into lv_max_seqno
    from zthrfiori_reqsta
    where guid = cv_guid.

  if sy-subrc = 0 and lv_max_seqno is not initial.
    try.
        lv_max_seqno_num = conv i( lv_max_seqno ).
      catch cx_sy_conversion_error.
        lv_max_seqno_num = 0.
    endtry.
  else.
    lv_max_seqno_num = 0.
  endif.

  lv_count = lv_max_seqno_num + 1.
  ev_seqno = |{ lv_count width = 3 align = right pad = '0' }|.

  " 8. APPLY NEW STEP BASED ON DETECTED CHANGE
  clear lv_validation_type.
  clear lv_exec_mode.

  case lv_detected_step.
    when c_request_init.
      ls_status-request_init = 'X'.
      ev_new_status = c_request_init.
      lv_validation_type = '01'.
      lv_exec_mode = '01'.
    when c_sep_slwop.
      ls_status-sep_slwop = 'X'.
      ev_new_status = c_sep_slwop.
      lv_validation_type = '02'.
      lv_exec_mode = '01'.
    when c_sep_staf.
      ls_status-sep_letter_staf = 'X'.
      ev_new_status = c_sep_staf.
      lv_validation_type = '03'.
      lv_exec_mode = '02'.
    when c_sep_oth_parties.
      ls_status-sep_slwop_oth_parties = 'X'.
      ev_new_status = c_sep_oth_parties.
      lv_validation_type = '04'.
      lv_exec_mode = '02'.
    when c_checkout.
      ls_status-checkout = 'X'.
      ev_new_status = c_checkout.
      lv_validation_type = '05'.
      lv_exec_mode = '01'.
    when c_checkout_completed.
      ls_status-checkout_completed = 'X'.
      ev_new_status = c_checkout_completed.
      lv_validation_type = '13'.
      lv_exec_mode = '01'.
    when c_checkout_cancelled.
      ls_status-checkout_cancelled = 'X'.
      ev_new_status = c_checkout_cancelled.
      lv_validation_type = '14'.
      lv_exec_mode = '01'.
    when c_travel.
      ls_status-travel = 'X'.
      ev_new_status = c_travel.
      lv_validation_type = '06'.
      lv_exec_mode = '02'.
    when c_shipment.
      ls_status-shipment = 'X'.
      ev_new_status = c_shipment.
      lv_validation_type = '07'.
      lv_exec_mode = '02'.
    when c_salary_suspense.
      ls_status-salary_suspense = 'X'.
      ev_new_status = c_salary_suspense.
      lv_validation_type = '08'.
      lv_exec_mode = '02'.
    when c_action_rec_iris.
      ls_status-action_rec_iris = 'X'.
      ev_new_status = c_action_rec_iris.
      lv_validation_type = '09'.
      lv_exec_mode = '01'.
    when c_paf.
      ls_status-paf = 'X'.
      ev_new_status = c_paf.
      lv_validation_type = '10'.
      lv_exec_mode = '01'.
    when c_close_request.
      ls_status-closed = 'X'.
      ev_new_status = c_close_request.
      lv_validation_type = '11'.
      lv_exec_mode = '02'.

      "---------------------------------En attente de confirmation---------------------------------------------
    when c_cancelled.
      ls_status-cancelled = 'X'.
      ev_new_status = c_cancelled.
      lv_validation_type = '12'.
      lv_exec_mode = '02'.
      "--------------------------------------------------------------------------------------------------------

    when others.
      " Si aucun step détecté, utiliser des valeurs par défaut
      lv_validation_type = '01'.
      lv_exec_mode = '01'.
  endcase.

  if iv_closed = 'X'.
    ls_status-closed = 'X'.
  endif.

  " 9. ENRICH STATUS WITH METADATA
  ls_status-mandt     = sy-mandt.
  ls_status-guid      = cv_guid.
  ls_status-seqno     = ev_seqno.
  ls_status-upd_pernr = lv_updater_to_use.
  ls_status-upd_lname = lv_lname.
  ls_status-upd_fname = lv_fname.
  ls_status-closed    = iv_closed.

  " 10. PREPARE APPROVAL RECORD
  lv_max_appr_seq = ''.
  select max( seqno ) into lv_max_appr_seq
    from zthrfiori_dapprv
    where guid = cv_guid.

  if sy-subrc = 0 and lv_max_appr_seq is not initial.
    try.
        lv_count = conv i( lv_max_appr_seq ).
      catch cx_sy_conversion_error.
        lv_count = 0.
    endtry.
  else.
    lv_count = 0.
  endif.

  lv_count = lv_count + 1.
  lv_approval_seqno = |{ lv_count width = 3 align = right pad = '0' }|.

  if iv_comments is not initial.
    if strlen( iv_comments ) > 255.
      lv_comments = iv_comments(255).
    else.
      lv_comments = iv_comments.
    endif.
  else.
    clear lv_comments. "ticket 1262
  endif.

  " Construire l'enregistrement d'approbation avec les bonnes valeurs
  ls_approval = value zthrfiori_dapprv(
    mandt           = sy-mandt
    guid            = cv_guid
    seqno           = lv_approval_seqno
    validation_type = lv_validation_type
    date_approval   = sy-datum
    comments        = lv_comments
    uname           = sy-uname
    exec_mode       = lv_exec_mode
  ).

  " 11. INSERT RECORDS (WITH CONTROLS)
  insert zthrfiori_reqsta from ls_status.
  if sy-subrc <> 0.
    rollback work.
    rv_ok = '-'.
    ev_new_status = c_error_db_insert.
    return.
  endif.

  insert zthrfiori_dapprv from ls_approval.
  if sy-subrc <> 0.
    rollback work.
    rv_ok = '-'.
    ev_new_status = c_error_db_approval.
    return.
  endif.

  commit work and wait.
  rv_ok = 'X'.

endmethod.
