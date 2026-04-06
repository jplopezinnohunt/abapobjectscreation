method requestset_update_entity.

  data: lv_err_msg         type bapi_msg,
        lo_offboarding     type ref to zcl_hr_fiori_offboarding_req,
        ls_input           type zv_hrfiori_req,
        lv_guid            type ze_hrfiori_guidreq,
        lv_ok              type char1,
        lv_seqno           type seqno,
        lv_previous_status type string ##NEEDED,
        lv_new_status      type string,
        lv_updater_name    type string ##NEEDED,
        ls_previous_reqsta type zthrfiori_reqsta,
        ls_merged_input    type zv_hrfiori_req,
        lv_primary_step    type string,
        lv_extracted_step  type string,
        lv_bracket_pos     type i,
        lv_bracket_end     type i,
        lv_comment_clean   type string,
        lv_len             type i,
        lo_benefits_util   type ref to zcl_hr_fiori_benefits.


  " (1) Récupérer les données OData
  io_data_provider->read_entry_data( importing es_data = ls_input ).

  data(lt_keys) = io_tech_request_context->get_keys( ).

  read table lt_keys assigning field-symbol(<key>) index 1.
  if sy-subrc eq 0.
    lv_guid = <key>-value.
  else.
    message id 'ZHRFIORI' type 'E' number '104'
     into lv_err_msg.
    raise exception type /iwbep/cx_mgw_busi_exception
      exporting
        textid  = /iwbep/cx_mgw_busi_exception=>business_error
        message = lv_err_msg.
  endif.
* Get personnel number of current updater
  create object lo_benefits_util.
  lo_benefits_util->get_actor_infos( importing ov_pernr = ls_input-upd_pernr ).

  " ============================================
  " (2) Récupérer le dernier statut existant
  " ============================================
  select * from zthrfiori_reqsta
    into ls_previous_reqsta
    where guid = lv_guid
    order by seqno descending.
    exit.
  endselect.

  " ============================================
  " (3) Fusionner : anciennes cases + nouvelles
  " ============================================
  ls_merged_input = ls_input.

  if ls_input-request_init is initial and ls_previous_reqsta-request_init = 'X'.
    ls_merged_input-request_init = 'X'.
  endif.
  if ls_input-sep_slwop is initial and ls_previous_reqsta-sep_slwop = 'X'.
    ls_merged_input-sep_slwop = 'X'.
  endif.
  if ls_input-sep_letter_staf is initial and ls_previous_reqsta-sep_letter_staf = 'X'.
    ls_merged_input-sep_letter_staf = 'X'.
  endif.
  if ls_input-sep_slwop_oth_parties is initial and ls_previous_reqsta-sep_slwop_oth_parties = 'X'.
    ls_merged_input-sep_slwop_oth_parties = 'X'.
  endif.
  if ls_input-checkout is initial and ls_previous_reqsta-checkout = 'X'.
    ls_merged_input-checkout = 'X'.
  endif.
  if ls_input-travel is initial and ls_previous_reqsta-travel = 'X'.
    ls_merged_input-travel = 'X'.
  endif.
  if ls_input-shipment is initial and ls_previous_reqsta-shipment = 'X'.
    ls_merged_input-shipment = 'X'.
  endif.
  if ls_input-salary_suspense is initial and ls_previous_reqsta-salary_suspense = 'X'.
    ls_merged_input-salary_suspense = 'X'.
  endif.
  if ls_input-action_rec_iris is initial and ls_previous_reqsta-action_rec_iris = 'X'.
    ls_merged_input-action_rec_iris = 'X'.
  endif.
  if ls_input-paf is initial and ls_previous_reqsta-paf = 'X'.
    ls_merged_input-paf = 'X'.
  endif.
  if ls_input-closed is initial and ls_previous_reqsta-closed = 'X'.
    ls_merged_input-closed = 'X'.
  endif.

  "----------------------------ATTENTE DE CONFIRMATION-----------------------------------
  if ls_input-cancelled is initial and ls_previous_reqsta-cancelled = 'X'.
    ls_merged_input-cancelled = 'X'.
  endif.
  "--------------------------------------------------------------------------------------

  " ============================================
  " (4) EXTRAIRE L'ÉTAPE SÉLECTIONNÉE DEPUIS LES COMMENTAIRES
  " ============================================
  " Format attendu : "[REQUEST_INIT] Mon commentaire..."

  lv_comment_clean = ls_input-comments.
  lv_extracted_step = ''.

  if lv_comment_clean is not initial and lv_comment_clean(1) = '['.
    lv_bracket_pos = 1.
    lv_bracket_end = 0.
    lv_len = strlen( lv_comment_clean ).

    " Chercher le crochet fermant ']'
    do.
      lv_bracket_end = lv_bracket_end + 1.
      if lv_bracket_end > lv_len.
        exit.
      endif.
      if substring( val = lv_comment_clean off = lv_bracket_end len = 1 ) = ']'.
        exit.
      endif.
    enddo.

    " Si on a trouvé le crochet
    if lv_bracket_end > 1 and lv_bracket_end < lv_len.
      " Extraire le contenu entre [ et ]
      lv_extracted_step = substring(
                            val = lv_comment_clean
                            off = lv_bracket_pos
                            len = lv_bracket_end - lv_bracket_pos + 1 ).

      " Nettoyer les commentaires : supprimer "[STEP] "
      if lv_bracket_end + 2 <= lv_len.
        lv_comment_clean = substring( val = lv_comment_clean
                                      off = lv_bracket_end + 2 ).
      else.
        lv_comment_clean = ''.
      endif.

      ls_merged_input-comments = lv_comment_clean.
    endif.
  endif.

  " ============================================
  " (5) Déterminer l'étape principale
  " ============================================
  if lv_extracted_step is not initial.
    lv_primary_step = lv_extracted_step.
  else.
    if ls_input-request_init = 'X'.
      lv_primary_step = c_request_init."'REQUEST_INIT'.
    elseif ls_input-sep_slwop = 'X'.
      lv_primary_step = c_sep_slwop."'SEP_SLWOP'.
    elseif ls_input-sep_letter_staf = 'X'.
      lv_primary_step = c_sep_letter_staf."'SEP_LETTER_STAF'.
    elseif ls_input-sep_slwop_oth_parties = 'X'.
      lv_primary_step = c_sep_slwop_oth_parties."'SEP_SLWOP_OTH_PARTIES'.
    elseif ls_input-checkout = 'X'.
      lv_primary_step = c_checkout."'CHECKOUT IN PROGRESS'.
    elseif ls_input-travel = 'X'.
      lv_primary_step = c_travel."'TRAVEL'.
    elseif ls_input-shipment = 'X'.
      lv_primary_step = c_shipment."'SHIPMENT'.
    elseif ls_input-salary_suspense = 'X'.
      lv_primary_step = c_salary_suspense."'SALARY_SUSPENSE'.
    elseif ls_input-action_rec_iris = 'X'.
      lv_primary_step = c_action_rec_iris."'ACTION_REC_IRIS'.
    elseif ls_input-paf = 'X'.
      lv_primary_step = c_paf."'PAF'.
    elseif ls_input-closed = 'X'.
      lv_primary_step = c_close_request."'CLOSE_REQUEST'.

    "----------------------------ATTENTE DE CONFIRMATION-----------------------------------
    elseif ls_input-cancelled = 'X'.
      lv_primary_step = c_cancelled."'CANCELLED'.
    "--------------------------------------------------------------------------------------

    else.
      lv_primary_step = c_comment_only."'COMMENT_ONLY'.
    endif.
  endif.

  " ============================================
  " (6) Mise à jour de la requête Offboarding
  " ============================================
  lo_offboarding = zcl_hr_fiori_offboarding_req=>get_instance( ).

  " Convertir ls_merged_input (ZV_HRFIORI_REQ) en ls_previous_reqsta (ZTHRFIORI_REQSTA)
  move-corresponding ls_merged_input to ls_previous_reqsta.
  ls_previous_reqsta-guid = lv_guid.

  lv_ok = lo_offboarding->update_request(
    exporting
      iv_pernr           = ls_merged_input-creator_pernr
      iv_action_type     = ls_merged_input-action_type
      iv_reason          = ls_merged_input-reason
      iv_effective       = ls_merged_input-effective_date
      iv_updater         = ls_merged_input-upd_pernr
      iv_step            = lv_primary_step
      iv_closed          = ls_merged_input-closed
      iv_comments        = ls_merged_input-comments
      iv_merged_status   = ls_previous_reqsta
    importing
      ev_seqno           = lv_seqno
      ev_previous_status = lv_previous_status
      ev_new_status      = lv_new_status
      ev_updater_name    = lv_updater_name
    changing
      cv_guid            = lv_guid
  ).

  if lv_ok <> 'X'.
    clear lv_err_msg.
    if lv_new_status = 'ERROR_STEP_ALREADY_VALIDATED'.
      message id 'ZHRFIORI' type 'E' number '105'
        into lv_err_msg.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid  = /iwbep/cx_mgw_busi_exception=>business_error
          message = lv_err_msg.
    else.
      message id 'ZHRFIORI' type 'E' number '106'
        into lv_err_msg with lv_new_status.
      raise exception type /iwbep/cx_mgw_busi_exception
        exporting
          textid  = /iwbep/cx_mgw_busi_exception=>business_error
          message = lv_err_msg.
    endif.
  endif.

  " ============================================
  " (7) Retourner la réponse OData
  " ============================================
  move-corresponding ls_merged_input to er_entity.
  er_entity-guid  = lv_guid.
  er_entity-seqno = lv_seqno.

endmethod.
