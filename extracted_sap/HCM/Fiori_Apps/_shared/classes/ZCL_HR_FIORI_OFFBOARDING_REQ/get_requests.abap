method get_requests.

  "======================================================================
  " Méthode : GET_REQUESTS
  "----------------------------------------------------------------------
  " Objectif :
  "   Récupère les demandes (requests) depuis la vue ZV_HRFIORI_REQ en
  "   appliquant dynamiquement les filtres OData et le paramètre $search.
  "
  " Description :
  "   1. Parse les filtres OData reçus (iv_filter_string)
  "   2. Construit dynamiquement la clause WHERE pour la sélection SQL
  "   3. Exécute la requête sur la table de base
  "   4. Applique des filtres logiques supplémentaires (année, mois,
  "      statut, catégorie d’employé, type de contrat, etc.)
  "   5. Enrichit les résultats avec les données employé (nom, prénom)
  "   6. Applique le filtre global $SEARCH si présent
  "   7. Retourne les enregistrements filtrés et le message de statut
  "
  " Paramètres :
  "   iv_filter_string   - Chaîne de filtres OData
  "   iv_filter_abap_string - Clause WHERE générée par le framework
  "   iv_search_string   - Terme de recherche global ($search)
  "   iv_pernr           - Numéro de personnel du créateur
  "
  " Résultats :
  "   et_requests        - Liste des demandes filtrées
  "   es_return          - Structure de retour (type, message)
  "======================================================================


  "------------------------------------------------------------
  " Déclaration des données locales
  "------------------------------------------------------------
  data: lt_all_data        type standard table of zv_hrfiori_req with empty key,
        lt_filtered        type standard table of zv_hrfiori_req with empty key,
        ls_request         type zv_hrfiori_req,
        lv_where           type string,
        lv_persg           type pa0001-persg,
        lv_contract        type pa0016-cttyp,
        lv_status          type string,
        lv_year            type string,
        lv_month           type string,
        " Variables pour le parsing des filtres OData
        lv_filter_guid     type string,
        lv_filter_year     type string,
        lv_filter_month    type string,
        lv_filter_status   type string,
        lv_filter_persg    type string,
        lv_filter_contract type string,
        lv_filter_action   type string,
        lv_filter_pernr    type string,
        lv_filter_fname    type string,
        lv_filter_lname    type string,
        lv_filter_empname  type string,
        lv_search_term     type string,
        lv_search_match    type abap_bool value abap_false,
        lv_fname           type pad_vorna,
        lv_lname           type pad_nachn,
        lv_full_name       type string,
        lv_reason          type string,
        lv_match           type abap_bool value abap_false.

  clear: et_requests, es_return, lv_where.

  "Si on recoit le GUID, on est dans un cas de display dun detail donc pas besoin d'aller plus loin dans les fltres,
  "A refaire plus trad , remplacer getentityset par getEntity

  "************************************************************
  "* ÉTAPE 1 : Analyse des filtres OData
  "************************************************************
  if iv_filter_string is not initial.


    if iv_filter_string cs 'Guid eq'.
      find regex 'Guid eq ''([^'']+)''' in iv_filter_string submatches lv_filter_guid ##NO_TEXT.
    endif.

    if lv_filter_guid is  initial. "Cas d'une recherche de plusieurs requetes

      " Extraction des valeurs de filtres avec expressions régulières
      if iv_filter_string cs 'Year eq'.
        find regex 'Year eq ''([^'']+)''' in iv_filter_string submatches lv_filter_year ##NO_TEXT.
      endif.

      if iv_filter_string cs 'Month eq'.
        find regex 'Month eq ''([^'']+)''' in iv_filter_string submatches lv_filter_month ##NO_TEXT.
      endif.

      if iv_filter_string cs 'Status eq'.
        find regex 'Status eq ''([^'']+)''' in iv_filter_string submatches lv_filter_status ##NO_TEXT.
      endif.

      if iv_filter_string cs 'Persg eq'.
        find regex 'Persg eq ''([^'']+)''' in iv_filter_string submatches lv_filter_persg ##NO_TEXT.
      endif.

      if iv_filter_string cs 'ContractType eq'.
        find regex 'ContractType eq ''([^'']+)''' in iv_filter_string submatches lv_filter_contract ##NO_TEXT.
      endif.

      if iv_filter_string cs 'ActionType eq'.
        find regex 'ActionType eq ''([^'']+)''' in iv_filter_string submatches lv_filter_action ##NO_TEXT.
      endif.

      " Filtres de type 'contains' ou 'substringof' pour les champs texte
      if iv_filter_string cs 'CreatorPernr'.
        find regex 'contains\(CreatorPernr,''([^'']+)''\)' in iv_filter_string submatches lv_filter_pernr ##NO_TEXT.
        if sy-subrc <> 0.
          find regex 'substringof\(''([^'']+)'',CreatorPernr\)' in iv_filter_string submatches lv_filter_pernr ##NO_TEXT.
        endif.
      endif.

      if iv_filter_string cs 'CreatorFname'.
        find regex 'contains\(CreatorFname,''([^'']+)''\)' in iv_filter_string submatches lv_filter_fname ##NO_TEXT.
        if sy-subrc <> 0.
          find regex 'substringof\(''([^'']+)'',CreatorFname\)' in iv_filter_string submatches lv_filter_fname ##NO_TEXT.
        endif.
      endif.

      if iv_filter_string cs 'CreatorLname'.
        find regex 'contains\(CreatorLname,''([^'']+)''\)' in iv_filter_string submatches lv_filter_lname ##NO_TEXT.
        if sy-subrc <> 0.
          find regex 'substringof\(''([^'']+)'',CreatorLname\)' in iv_filter_string submatches lv_filter_lname ##NO_TEXT.
        endif.
      endif.

      if iv_filter_string cs 'EmployeeName'.
        find regex 'contains\(EmployeeName,''([^'']+)''\)' in iv_filter_string submatches lv_filter_empname ##NO_TEXT.
        if sy-subrc <> 0.
          find regex 'substringof\(''([^'']+)'',EmployeeName\)' in iv_filter_string submatches lv_filter_empname ##NO_TEXT.
        endif.
      endif.

      " Cas particulier : extraction du filtre EmployeeName depuis la clause ABAP
      if iv_filter_abap_string cs 'EmployeeName'.
        find first occurrence of 'EMPLOYEENAME like ''%' in iv_filter_abap_string results data(lv_pos1) ##NO_TEXT.
        data(lv_idx) = lv_pos1-offset + lv_pos1-length.
        data(lv_substr1) = iv_filter_abap_string+lv_idx.
        find first occurrence of '%''' in lv_substr1 results data(lv_pos2).
        lv_filter_empname = lv_substr1(lv_pos2-offset).
      endif.


    endif.



  endif.


  "************************************************************
  "* ÉTAPE 1.5 : Traitement du paramètre $SEARCH
  "************************************************************
  if iv_search_string is not initial.
    lv_search_term = iv_search_string.
    lv_search_term = replace( val = lv_search_term sub = '"' with = '' occ = 0 ).
    translate lv_search_term to upper case.
    condense lv_search_term.
  endif.


  "************************************************************
  "* ÉTAPE 2 : Construction dynamique de la clause WHERE
  "************************************************************
  if iv_pernr is not initial.
    lv_where = |creator_pernr = '{ iv_pernr }'| ##NO_TEXT.
  endif.

  if lv_filter_pernr is not initial.
    data(lv_pernr_pattern) = |%{ lv_filter_pernr }%|.
    if lv_where is not initial.
      lv_where = lv_where && | AND creator_pernr LIKE '{ lv_pernr_pattern }'| ##NO_TEXT.
    else.
      lv_where = |creator_pernr LIKE '{ lv_pernr_pattern }'| ##NO_TEXT.
    endif.
  endif.

  if lv_filter_action is not initial.
    if lv_where is not initial.
      lv_where = lv_where && | AND action_type = '{ lv_filter_action }'| ##NO_TEXT.
    else.
      lv_where = |action_type = '{ lv_filter_action }'| ##NO_TEXT.
    endif.
  endif.

  "Guid
  if lv_filter_guid is not initial.
    if lv_where is not initial.
      lv_where = lv_where && | AND guid = '{ lv_filter_guid }'| ##NO_TEXT.
    else.
      lv_where = |guid = '{ lv_filter_guid }'| ##NO_TEXT.
    endif.
  endif.


  "************************************************************
  "* ÉTAPE 3 : Lecture en base de données
  "************************************************************
  if lv_where is initial.
    select * from zv_hrfiori_req into corresponding fields of table lt_all_data.
  else.
    select * from zv_hrfiori_req into corresponding fields of table lt_all_data where (lv_where).
  endif.

  if lt_all_data is initial.
    es_return-type    = 'W'.
*    es_return-message = 'No records found'.
    message id 'ZHRFIORI' type 'W' number '043'
      into es_return-message.
    return.
  endif.

  sort lt_all_data by guid ascending seqno descending.
  delete adjacent duplicates from lt_all_data comparing guid.


  "************************************************************
  "* ÉTAPE 4 : Filtres logiques et enrichissement des données
  "************************************************************
  data(lo_object) = zcl_hr_fiori_offboarding_req=>get_instance( ).

  loop at lt_all_data into ls_request.

    clear lv_match.

    "--- Récupération des données employé (nom, prénom) ---
    lo_object->get_employee_data(
      exporting iv_persno = ls_request-creator_pernr
      importing ev_vorna  = lv_fname
                ev_nachn  = lv_lname ).

    lv_full_name = |{ lv_fname } { lv_lname }|.
    condense lv_full_name.

    "--- Récupération catégorie employé (PERSG) ---
    select single persg from pa0001 into @lv_persg
      where pernr = @ls_request-creator_pernr
        and endda >= @sy-datum
        and begda <= @sy-datum ##WARN_OK.

    if lv_filter_persg is not initial and lv_persg <> lv_filter_persg.
      continue.
    endif.

    "--- Récupération type de contrat ---
    select single cttyp from pa0016 into @lv_contract
      where pernr = @ls_request-creator_pernr
        and endda >= @sy-datum
        and begda <= @sy-datum ##WARN_OK.

    if lv_filter_contract is not initial and lv_contract <> lv_filter_contract.
      continue.
    endif.

    "--- Détermination du statut logique ---
    if ls_request-closed = abap_true.
      lv_status = c_completed.
    elseif ls_request-request_init = abap_true
         and  ls_request-closed = abap_false
         and ls_request-cancelled = abap_false.
      lv_status = c_in_progress."'IN_PROGRESS'.
    else.
      lv_status = c_cancelled.
    endif.

    if  lv_filter_status is not initial and lv_status <> lv_filter_status. "
      continue.
    endif.

    "--- Dérivation de l’année et du mois ---
    if ls_request-effective_date is not initial and ls_request-effective_date <> '00000000'.
      lv_year  = ls_request-effective_date(4).
      lv_month = ls_request-effective_date+4(2).
    else.
      clear: lv_year, lv_month.
    endif.
    if  lv_filter_year is not initial and lv_year <> lv_filter_year. "l
      continue.
    endif.

    if  lv_filter_month is not initial and lv_month <> lv_filter_month. "
      continue.
    endif.

    "--- Filtres sur le nom employé ---
    if lv_filter_fname is not initial or lv_filter_lname is not initial or lv_filter_empname is not initial.

      " Conversion en majuscules pour comparaison insensible à la casse
      translate: lv_fname to upper case,
                 lv_lname to upper case,
                 lv_full_name to upper case.

      if lv_filter_fname is not initial and lv_fname cs lv_filter_fname.
        lv_match = abap_true.
      endif.

      if lv_filter_lname is not initial and lv_lname cs lv_filter_lname.
        lv_match = abap_true.
      endif.

      if lv_filter_empname is not initial and lv_full_name cs lv_filter_empname.
        lv_match = abap_true.
      endif.

      if lv_match = abap_false.
        continue.
      endif.
    endif.

    "--- Application du filtre global $SEARCH ---
    if lv_search_term is not initial.

      lv_reason = lo_object->get_domain_value_text(
                    iv_domain_name  = 'ZD_HRFIORI_REASON'
                    iv_domain_value = conv string( ls_request-reason )
                    iv_language     = sy-langu ).

      translate: lv_reason to upper case,
                 lv_fname to upper case,
                 lv_lname to upper case,
                 lv_full_name to upper case.

      if lv_search_term cs ls_request-creator_pernr
         or lv_search_term cs lv_fname
         or lv_search_term cs lv_lname
         or lv_search_term cs lv_full_name
         or lv_search_term cs lv_reason
         or lv_search_term cs ls_request-action_type.
        lv_search_match = abap_true.
      endif.

      if lv_search_match = abap_false.
        continue.
      endif.
    endif.

    " Si tous les filtres sont validés, ajouter à la liste finale
    append ls_request to lt_filtered.

  endloop.


  "************************************************************
  "* ÉTAPE 5 : Sortie et message de retour
  "************************************************************
  et_requests = lt_filtered.

  if et_requests is initial.
    es_return-type    = 'W'.
    message id 'ZHRFIORI' type 'W' number '044'
      into es_return-message.
    return.
  endif.

  sort et_requests by effective_date descending.

  data(lv_count) = lines( et_requests ).
  es_return-type    = 'S'.
  message id 'ZHRFIORI' type 'S' number '045'
    into es_return-message
      with lv_count.

endmethod.
