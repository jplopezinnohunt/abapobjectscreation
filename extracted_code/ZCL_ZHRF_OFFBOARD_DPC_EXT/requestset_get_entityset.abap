method requestset_get_entityset.

  " ---------------------------------------
  " Déclarations
  " ---------------------------------------
  data: lo_object        type ref to zcl_hr_fiori_offboarding_req,
        lt_requests      type standard table of zv_hrfiori_req,
        ls_request       type zv_hrfiori_req,
        ls_entity        type zcl_zhrf_offboard_mpc=>ts_request,
        lv_persg         type pa0001-persg,
        lv_contract_type type pa0016-cttyp,
        lv_status        type string,
        lv_year          type i,
        lv_month         type i,
        lv_search        type string,
        lv_filter_string type string,
        lt_order         type /iwbep/t_mgw_tech_order,
        ls_order         type /iwbep/s_mgw_tech_order,
        ls_return        type bapiret2,
        lo_filter        type ref to /iwbep/if_mgw_req_filter,
        lt_filters       type /iwbep/t_mgw_select_option.

  " Note : plus besoin de déclarer ET_ENTITYSET
  " ---------------------------------------
  " 1. Récupérer $search et $orderby
  " ---------------------------------------
  lo_filter = io_tech_request_context->get_filter( ).
  lv_filter_string = lo_filter->get_filter_string( ).

  try.
      lv_search = io_tech_request_context->get_search_string( ).
    catch cx_root.
      clear lv_search.
  endtry.

  try.
      lt_order = io_tech_request_context->get_orderby( ).
    catch cx_root.
      clear lt_order.
  endtry.

  clear: et_entityset, ls_return.

  " ---------------------------------------
  " 2. Appel de la méthode métier get_requests
  " ---------------------------------------
  lo_object = zcl_hr_fiori_offboarding_req=>get_instance( ).

  lo_object->get_requests(
    exporting
      iv_filter_string = iv_filter_string
      iv_filter_abap_string = lv_filter_string
      iv_search_string = lv_search
    importing
      et_requests      = lt_requests
      es_return        = ls_return
  ).

  if ls_return-type = 'E' or lt_requests is initial.
    return.
  endif.

  " ---------------------------------------
  " 3. Appliquer $search côté serveur
  " ---------------------------------------
  if lv_search is not initial.
    delete lt_requests where not (
        creator_fname  cp |*{ lv_search }*| or
        creator_lname  cp |*{ lv_search }*| or
        reason         cp |*{ lv_search }*|
    ).
  endif.

  " ---------------------------------------
  " 4. Construire l'entité de sortie
  " ---------------------------------------
  loop at lt_requests into ls_request.

    " Groupe de personnel
    select single persg
      from pa0001
      into @lv_persg
      where pernr = @ls_request-creator_pernr
        and endda >= @sy-datum
        and begda <= @sy-datum ##WARN_OK.

    " Statut
    if ls_request-closed = abap_true.
*      lv_status = c_completed."'COMPLETED'.
      lv_status = text-007."'COMPLETED'.
    elseif ls_request-request_init = abap_true
        and  ls_request-closed = abap_false
        and ls_request-cancelled = abap_false.
*      lv_status = c_in_progress."'IN_PROGRESS'.
      lv_status = text-005."'IN_PROGRESS'.

    "-----------------En attente de confirmation ---------------------------------------------
    else.
*      lv_status = c_cancelled."'CANCELLED'.
      lv_status = text-006."'CANCELLED'.
    endif.
    "-----------------------------------------------------------------------------------------

    " Type de contrat
    select single cttyp
      from pa0016
      into @lv_contract_type
      where pernr = @ls_request-creator_pernr
        and endda >= @sy-datum
        and begda <= @sy-datum ##WARN_OK.

    " Year & Month
    if ls_request-effective_date is not initial and ls_request-effective_date <> '00000000'.
      lv_year  = ls_request-effective_date(4).
      lv_month = ls_request-effective_date+4(2).
    else.
      clear: lv_year, lv_month.
    endif.

    " Construire l'entité
    clear ls_entity.
    ls_entity-guid           = ls_request-guid.
    ls_entity-creator_pernr  = ls_request-creator_pernr.
    ls_entity-creator_fname  = ls_request-creator_fname.
    ls_entity-creator_lname  = ls_request-creator_lname.

    " EmployeeName calculé
    ls_entity-employeename = |{ ls_request-creator_fname } { ls_request-creator_lname }|.
    condense ls_entity-employeename.

    " Dates
    ls_entity-effective_date = ls_request-effective_date.
    ls_entity-endda          = ls_request-endda.

    " Raison
    ls_entity-reason = lo_object->get_domain_value_text(
                         iv_domain_name  = 'ZD_HRFIORI_REASON'
                         iv_domain_value = conv string( ls_request-reason )
                         iv_language     = sy-langu ).

    " Champs logiques
    ls_entity-request_init        = cond #( when ls_request-request_init = abap_true then 'X' else '' ).
    ls_entity-sep_slwop           = cond #( when ls_request-sep_slwop = abap_true then 'X' else '' ).
    ls_entity-checkout            = cond #( when ls_request-checkout = abap_true then 'X' else '' ).
    ls_entity-travel              = cond #( when ls_request-travel = abap_true then 'X' else '' ).
    ls_entity-shipment            = cond #( when ls_request-shipment = abap_true then 'X' else '' ).
    ls_entity-salary_suspense     = cond #( when ls_request-salary_suspense = abap_true then 'X' else '' ).
    ls_entity-closed              = cond #( when ls_request-closed = abap_true then 'X' else '' ).
    ls_entity-action_rec_iris     = cond #( when ls_request-action_rec_iris = abap_true then 'X' else '' ).
    ls_entity-paf                 = cond #( when ls_request-paf = abap_true then 'X' else '' ).
    ls_entity-sep_letter_staf     = cond #( when ls_request-sep_letter_staf = abap_true then 'X' else '' ).
    ls_entity-sep_slwop_oth_parties = cond #( when ls_request-sep_slwop_oth_parties = abap_true then 'X' else '' ).

    "--------------------------------En attente de validation-----------------------------------------------
    ls_entity-cancelled           = cond #( when ls_request-cancelled = abap_true then 'X' else '' ).
    "-------------------------------------------------------------------------------------------------------

    " Champs calculés
    ls_entity-year         = lv_year.
    ls_entity-month        = lv_month.
    ls_entity-persg        = lv_persg.
    ls_entity-status       = lv_status.
    ls_entity-contracttype = lv_contract_type.
    ls_entity-action_type  = ls_request-action_type.

    " Ajouter à la table de sortie (paramètre)
    append ls_entity to et_entityset.

  endloop.

  " ---------------------------------------
  " 5. Appliquer $orderby
  " ---------------------------------------
  if lt_order is not initial.
    loop at lt_order into ls_order.
      case ls_order-property.
        when 'EFFECTIVE_DATE'.
          if ls_order-order = 'desc'.
            sort et_entityset by effective_date descending.
          else.
            sort et_entityset by effective_date ascending.
          endif.
        when 'CREATOR_PERNR'.
          if ls_order-order = 'desc'.
            sort et_entityset by creator_pernr descending.
          else.
            sort et_entityset by creator_pernr ascending.
          endif.
        when 'EMPLOYEENAME'.
          if ls_order-order = 'desc'.
            sort et_entityset by employeename descending.
          else.
            sort et_entityset by employeename ascending.
          endif.
        when 'ENDDA'.
          if ls_order-order = 'desc'.
            sort et_entityset by endda descending.
          else.
            sort et_entityset by endda ascending.
          endif.
        when 'REASON'.
          if ls_order-order = 'desc'.
            sort et_entityset by reason descending.
          else.
            sort et_entityset by reason ascending.
          endif.
        when others.
          sort et_entityset by effective_date descending.
      endcase.
    endloop.
  else.
    sort et_entityset by effective_date descending.
  endif.

endmethod.
