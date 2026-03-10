METHOD workflowstepset_get_entityset.

  "----------------------------------------------------------------------
  " Déclaration des variables locales
  "----------------------------------------------------------------------
  DATA: ls_odata      TYPE zcl_zhrf_offboard_mpc=>ts_workflowstep, " Structure OData de sortie
        lv_guid       TYPE string,                                 " GUID au format texte
        lv_guid_raw   TYPE sysuuid_x16,                            " GUID au format RAW
        lv_step_str   TYPE ze_hrfiori_offboarding_step,
        lf_visibility TYPE boolean,
        lv_pernr      TYPE pernr_d.

  FIELD-SYMBOLS <fs_status> TYPE any.                            " Pointeur générique pour champs dynamiques

  "----------------------------------------------------------------------
  " Étape 1 : Récupération du GUID depuis les filtres ou la clé d’entrée
  "----------------------------------------------------------------------
  LOOP AT it_filter_select_options INTO DATA(ls_filter) WHERE property = 'Guid'.
    LOOP AT ls_filter-select_options INTO DATA(ls_selopt).
      lv_guid = ls_selopt-low.
      REPLACE ALL OCCURRENCES OF '-' IN lv_guid WITH ''.          " Nettoyage du GUID (suppression des tirets)
      EXIT.
    ENDLOOP.
    IF lv_guid IS NOT INITIAL. EXIT. ENDIF.
  ENDLOOP.

  " Si aucun GUID trouvé dans les filtres, on le récupère via la clé
  IF lv_guid IS INITIAL.
    READ TABLE it_key_tab INTO DATA(ls_key) WITH KEY name = 'Guid' ##NO_TEXT.
    IF sy-subrc = 0.
      lv_guid = ls_key-value.
      REPLACE ALL OCCURRENCES OF '-' IN lv_guid WITH ''.
    ENDIF.
  ENDIF.

  " Si aucun GUID n’est fourni, on sort immédiatement
  IF lv_guid IS INITIAL. RETURN. ENDIF.

  " Conversion du GUID texte en RAW (format interne SAP)
  TRY.
      lv_guid_raw = lv_guid.
    CATCH cx_root.
      RETURN. " En cas d’erreur de conversion, on arrête le traitement
  ENDTRY.

  "----------------------------------------------------------------------
  " Étape 2 : Lecture des données jointes (DAPPRV + REQSTA)
  "----------------------------------------------------------------------
  SELECT a~guid,
         a~seqno,
         a~date_approval,
         a~comments,
         b~request_init,
         b~sep_slwop,
         b~sep_letter_staf,
         b~sep_slwop_oth_parties,
         b~paf,
         b~action_rec_iris,
         b~checkout,
         b~travel,
         b~shipment,
         b~salary_suspense,
         b~closed,
         b~cancelled,
         b~upd_pernr,
         b~upd_fname,
         b~upd_lname
    FROM zthrfiori_dapprv AS a
    INNER JOIN zthrfiori_reqsta AS b
      ON a~guid = b~guid
     AND a~seqno = b~seqno
    INTO TABLE @DATA(lt_req)
    WHERE a~guid = @lv_guid_raw.

  " Si aucune donnée n’est trouvée, on sort
  IF lt_req IS INITIAL. RETURN. ENDIF.

  "----------------------------------------------------------------------
  " Étape 3 : Définition du mapping entre les étapes du workflow
  "           et les champs de statut correspondants
  "----------------------------------------------------------------------
  TYPES: BEGIN OF ts_step,
           stepname     TYPE string,
           status_field TYPE fieldname,
         END OF ts_step.

  DATA: ls_steps TYPE ts_step,
        lt_steps TYPE STANDARD TABLE OF ts_step.

  SELECT step_code step_txt
    INTO ( ls_steps-status_field, ls_steps-stepname )
      FROM zthrfiori_offb_s
        WHERE language = sy-langu.
    APPEND ls_steps TO lt_steps.
  ENDSELECT.
  "----------------------------------------------------------------------
  " Étape 4 : Construction de l’entityset pour l’OData
  "----------------------------------------------------------------------
  "Get request information
  SELECT SINGLE creator_pernr INTO lv_pernr
    FROM zthrfiori_hreq
      WHERE guid = lv_guid_raw.

  LOOP AT lt_steps INTO DATA(ls_step).

    " Vérifier si l'étape doit être affiché ou non
    CLEAR: lf_visibility, lv_step_str.
    lv_step_str = ls_step-status_field.
    zcl_hr_fiori_offboarding_req=>check_wf_step_visibility( EXPORTING iv_guid = lv_guid
                                                                      iv_pernr = lv_pernr
                                                                      iv_step = lv_step_str
                                                            IMPORTING ov_to_be_displayed = lf_visibility  ).
    CHECK lf_visibility = abap_true.

    " Initialisation de la structure OData pour chaque étape
    CLEAR ls_odata.
    ls_odata-guid      = lv_guid_raw.
    ls_odata-stepcode  = ls_step-status_field.
    ls_odata-stepname  = ls_step-stepname.
    ls_odata-completed = ''.
    ls_odata-validator = '-'.
    CLEAR ls_odata-date_approval.

    " Parcours des enregistrements pour déterminer le statut de l’étape
    LOOP AT lt_req INTO DATA(ls_req).
      ASSIGN COMPONENT ls_step-status_field OF STRUCTURE ls_req TO <fs_status>.

      " Si le champ de statut est coché ('X'), la step est considérée comme complétée
      IF sy-subrc = 0 AND <fs_status> = 'X'.
        ls_odata-completed = 'X'.
        ls_odata-date_approval = ls_req-date_approval.

        " Détermination du validateur (nom complet ou matricule)
        IF ls_req-upd_fname IS NOT INITIAL OR ls_req-upd_lname IS NOT INITIAL.
          ls_odata-validator = |{ ls_req-upd_fname } { ls_req-upd_lname }|.
          CONDENSE ls_odata-validator.
        ELSEIF ls_req-upd_pernr IS NOT INITIAL.
          ls_odata-validator = ls_req-upd_pernr.
        ELSE.
          ls_odata-validator = '-'.
        ENDIF.

        " Sortir dès qu’une correspondance est trouvée pour cette étape
        EXIT.
      ENDIF.
    ENDLOOP.

    " Ajouter l’étape construite à l’entityset de sortie
    APPEND ls_odata TO et_entityset.

  ENDLOOP.

ENDMETHOD.
