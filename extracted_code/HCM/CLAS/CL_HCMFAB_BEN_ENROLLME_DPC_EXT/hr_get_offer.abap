METHOD hr_get_offer.

  DATA: lt_error_table       TYPE hrben00err_ess,
        lt_health_offer      TYPE TABLE OF rpben_oa,
        lt_insure_offer      TYPE TABLE OF rpben_ob,
        lt_saving_offer      TYPE TABLE OF rpben_oc,
        lt_spenda_offer      TYPE TABLE OF rpben_od,
        lt_miscel_offer      TYPE TABLE OF rpben_oe,
        lt_stockp_offer      TYPE TABLE OF rpben_of,
        lt_credit_offer      TYPE TABLE OF rpben_o1,
        lt_depend_offer      TYPE TABLE OF rpbenodp,
        lt_benefi_offer      TYPE TABLE OF rpbenobf,
        lt_invest_offer      TYPE TABLE OF rpbenoiv,
        lt_adjust_reason     TYPE TABLE OF rpbenevent,

        ls_event_description TYPE rpbenevent,
        ls_adjust_reason     TYPE rpbenevent,
        ls_enrol_reason      TYPE rpbenenrollmentreason,
        ls_health_offer      TYPE rpben_oa,
        ls_insure_offer      TYPE rpben_ob,
        ls_saving_offer      TYPE rpben_oc,
        ls_spenda_offer      TYPE rpben_od,
        ls_miscel_offer      TYPE rpben_oe,
        ls_stockp_offer      TYPE rpben_of,
        ls_credit_offer      TYPE rpben_o1,
        ls_benefit           LIKE LINE OF et_ben_unenrolled,

        lv_currency          TYPE ben_curr,
        lv_enrtyp            TYPE ben_enrtyp,
        lv_open_begda        TYPE ben_opbeg,
        lv_open_endda        TYPE ben_opend.

  CLEAR: ev_subrc, et_error_table, et_ben_unenrolled.

  REFRESH lt_error_table.

  lv_enrtyp = iv_event_type.

  IF is_event_desc IS INITIAL.

    IF iv_event_type = c_open_offer.
      CALL FUNCTION 'HR_BEN_GET_OPEN_ENROLL_PERIOD'
        EXPORTING
          pernr       = iv_pernr
          datum       = iv_datum
          reaction    = c_reaction_x
        IMPORTING
          open_begda  = lv_open_begda
          open_endda  = lv_open_endda
          subrc       = ev_subrc
        TABLES
          error_table = lt_error_table.

      CHECK ev_subrc EQ 0.
      ls_enrol_reason-barea = iv_ben_area.
      ls_enrol_reason-enrty = iv_event_type.
      ls_enrol_reason-event = iv_event.
      ls_enrol_reason-pernr = iv_pernr.
      ls_enrol_reason-txt_event = text-t01.
      ls_enrol_reason-begda = lv_open_begda.
      ls_enrol_reason-endda = lv_open_endda.
    ELSE.
      CALL FUNCTION 'HR_BEN_GET_EVENT_LIST'
        EXPORTING
          pernr       = iv_pernr
          datum       = iv_datum
          reaction    = c_reaction_x
        IMPORTING
          subrc       = ev_subrc
        TABLES
          event_list  = lt_adjust_reason
          error_table = lt_error_table.

      READ TABLE lt_adjust_reason INTO ls_adjust_reason
       WITH KEY pernr = iv_pernr
                barea = iv_ben_area
                event = iv_event.
      IF sy-subrc = 0.
        MOVE-CORRESPONDING ls_adjust_reason TO ls_enrol_reason.
      ENDIF.
    ENDIF.

    MOVE-CORRESPONDING ls_enrol_reason TO ls_event_description.
    REFRESH lt_error_table.

  ELSE.
    MOVE-CORRESPONDING is_event_desc TO ls_event_description.
  ENDIF.
* 4) Get employee's currency
  CALL FUNCTION 'HR_BEN_GET_CURRENCY'
    EXPORTING
      barea       = iv_ben_area
      datum       = sy-datum
      reaction    = c_reaction_n
    IMPORTING
      currency    = lv_currency
      subrc       = ev_subrc
    TABLES
      error_table = lt_error_table.

*  GET all offer from for a particulur enrollment reason.
  CALL FUNCTION 'HR_BEN_GET_OFFER'
    EXPORTING
      pernr              = iv_pernr
      datum              = iv_datum
      enrollment_type    = lv_enrtyp
      event_description  = ls_event_description
      desired_currency   = lv_currency
      reaction           = c_reaction_n
    IMPORTING
      subrc              = ev_subrc
    TABLES
      credit_offer       = lt_credit_offer
      health_offer       = lt_health_offer
      insure_offer       = lt_insure_offer
      saving_offer       = lt_saving_offer
      spenda_offer       = lt_spenda_offer
      miscel_offer       = lt_miscel_offer
      stockp_offer       = lt_stockp_offer
      poss_dependents    = lt_depend_offer
      poss_beneficiaries = lt_benefi_offer
      poss_investments   = lt_invest_offer
      error_table        = lt_error_table.

  et_health_offer = lt_health_offer.
  et_insure_offer = lt_insure_offer.
  et_saving_offer = lt_saving_offer.
  et_spenda_offer = lt_spenda_offer.
  et_miscel_offer = lt_miscel_offer.
  et_stockp_offer = lt_stockp_offer.
  et_credit_offer = lt_credit_offer.
  et_dependents = lt_depend_offer.
  et_beneficiaries = lt_benefi_offer.        "Name, relationship, perc (cont and prim diff)
  et_investments = lt_invest_offer.

ENDMETHOD.
