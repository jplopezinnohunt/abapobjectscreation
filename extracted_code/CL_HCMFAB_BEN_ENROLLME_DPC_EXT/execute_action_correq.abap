METHOD execute_action_correq.

  DATA: lt_credit_offer TYPE TABLE OF rpben_o1,
        lt_health_offer TYPE TABLE OF rpben_oa,
        lt_insure_offer TYPE TABLE OF rpben_ob,
        lt_saving_offer TYPE TABLE OF rpben_oc,
        lt_spenda_offer TYPE TABLE OF rpben_od,
        lt_miscel_offer TYPE TABLE OF rpben_oe,
        lt_stockp_offer TYPE TABLE OF rpben_of,
        lt_coreq        TYPE hrben00crq,
        lt_coreq_out    TYPE TABLE OF hcmfab_s_enro_corequisite,
        lt_error_table  TYPE TABLE OF rpbenerr,
        ls_param        LIKE LINE OF it_parameter,
        ls_credit_offer TYPE rpben_o1,
        ls_health_offer TYPE rpben_oa,
        ls_insure_offer TYPE rpben_ob,
        ls_saving_offer TYPE rpben_oc,
        ls_spenda_offer TYPE rpben_od,
        ls_miscel_offer TYPE rpben_oe,
        ls_stockp_offer TYPE rpben_of,
        ls_coreq        TYPE rpbencrq,
        ls_coreq_out    TYPE hcmfab_s_enro_corequisite,
        ls_h5uca        TYPE t5uca,
        lv_subrc        TYPE sysubrc,
        lv_plan_cat     TYPE ben_categ,
        lv_plan         TYPE ben_plan,
        lv_beg_date     TYPE begda,
        lv_ben_area     TYPE ben_area.

  CLEAR:lv_plan_cat,lv_ben_area,lv_plan,lv_beg_date.
  LOOP AT it_parameter INTO ls_param.

    CASE ls_param-name.
      WHEN 'PlanCategory'.
        lv_plan_cat = ls_param-value.

      WHEN 'BenefitArea'.
        lv_ben_area = ls_param-value.

      WHEN 'Plan'.
        lv_plan = ls_param-value.

      WHEN 'BeginDate'.
        lv_beg_date = ls_param-value.

    ENDCASE.

  ENDLOOP.

  CLEAR:ls_health_offer,lt_health_offer,ls_insure_offer,lt_insure_offer,ls_saving_offer,lt_saving_offer,
  ls_spenda_offer,lt_spenda_offer,ls_stockp_offer,lt_stockp_offer,ls_credit_offer,lt_credit_offer,lt_coreq,lt_error_table.

  CASE lv_plan_cat.
    WHEN c_health_plan.
      ls_health_offer-barea = lv_ben_area.
      ls_health_offer-begda = lv_beg_date.
      ls_health_offer-bpcat = lv_plan_cat.
      ls_health_offer-bplan = lv_plan.
      APPEND ls_health_offer TO lt_health_offer.

    WHEN c_insurance_plan.
      ls_insure_offer-barea = lv_ben_area.
      ls_insure_offer-begda = lv_beg_date.
      ls_insure_offer-bpcat = lv_plan_cat.
      ls_insure_offer-bplan = lv_plan.
      APPEND ls_insure_offer TO lt_insure_offer.

    WHEN c_savings_plan.
      ls_saving_offer-barea = lv_ben_area.
      ls_saving_offer-begda = lv_beg_date.
      ls_saving_offer-bpcat = lv_plan_cat.
      ls_saving_offer-bplan = lv_plan.
      APPEND ls_saving_offer TO lt_saving_offer.

    WHEN c_spendings_plan.
      ls_spenda_offer-barea = lv_ben_area.
      ls_spenda_offer-begda = lv_beg_date.
      ls_spenda_offer-bpcat = lv_plan_cat.
      ls_spenda_offer-bplan = lv_plan.
      APPEND ls_spenda_offer TO lt_spenda_offer.

    WHEN c_miscellaneous_plan.
      ls_miscel_offer-barea = lv_ben_area.
      ls_miscel_offer-begda = lv_beg_date.
      ls_miscel_offer-bpcat = lv_plan_cat.
      ls_miscel_offer-bplan = lv_plan.
      APPEND ls_miscel_offer TO lt_miscel_offer.

    WHEN c_stock_purchase_plan.
      ls_stockp_offer-barea = lv_ben_area.
      ls_stockp_offer-begda = lv_beg_date.
      ls_stockp_offer-bpcat = lv_plan_cat.
      ls_stockp_offer-bplan = lv_plan.
      APPEND ls_stockp_offer TO lt_stockp_offer.

    WHEN c_credit_plan.
      ls_credit_offer-barea = lv_ben_area.
      ls_credit_offer-begda = lv_beg_date.
      ls_credit_offer-bpcat = lv_plan_cat.
      ls_credit_offer-bplan = lv_plan.
      APPEND ls_credit_offer TO lt_credit_offer.

  ENDCASE.

  CALL FUNCTION 'HR_BEN_GET_COREQUISITES'
    EXPORTING
      reaction          = c_reaction_n
    IMPORTING
      subrc             = lv_subrc
    TABLES
      credit_offer      = lt_credit_offer
      health_offer      = lt_health_offer
      insure_offer      = lt_insure_offer
      saving_offer      = lt_saving_offer
      spenda_offer      = lt_spenda_offer
      miscel_offer      = lt_miscel_offer
      stockp_offer      = lt_stockp_offer
      corequisite_plans = lt_coreq
      error_table       = lt_error_table.
  IF lv_subrc = 0.
    LOOP AT lt_coreq INTO ls_coreq.
      MOVE-CORRESPONDING ls_coreq TO ls_coreq_out.
      cl_hr_t5uca=>read(
        EXPORTING
          langu = sy-langu
          barea = ls_coreq-barea
          bplan = ls_coreq-bplan
        RECEIVING
          t5uca = ls_h5uca
      ).
      ls_coreq_out-txt_copln = ls_h5uca-ltext.
      APPEND ls_coreq_out TO lt_coreq_out.
      CLEAR : ls_coreq_out,ls_coreq, ls_h5uca.
    ENDLOOP.

    copy_data_to_ref(
      EXPORTING
        is_data = lt_coreq_out
      CHANGING
        cr_data = er_data
    ).
  ELSE.
    me->raise_exceptions(
     EXPORTING
       it_messages = lt_error_table
       iv_entity_name = iv_action_name
     ).
  ENDIF.

ENDMETHOD.
