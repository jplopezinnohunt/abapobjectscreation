METHOD /iwbep/if_mgw_appl_srv_runtime~get_expanded_entityset.



    DATA: lt_assignments      TYPE pccet_pernr,
          lt_offer            TYPE cl_hcmfab_ben_enrollme_mpc=>tt_offer,
          ls_key_tab          LIKE LINE OF it_key_tab,
          lt_error_table      TYPE hrben00err_ess,
          lt_error_table_temp TYPE TABLE OF rpbenerr,
          lt_part_plans       TYPE cl_hcmfab_ben_enrollme_mpc=>tt_participatingplan,
          lt_health_plans     TYPE TABLE OF rpben_da,
          lt_credit_plans     TYPE TABLE OF rpben_d1,
          lt_insurance_plans  TYPE TABLE OF rpben_db,
          lt_savings_plans    TYPE TABLE OF rpben_dc,
          lt_spendings_plans  TYPE TABLE OF rpben_dd,
          lt_miscel_plans     TYPE TABLE OF rpben_de,
          lt_stockp_plans     TYPE TABLE OF rpben_df,
          lt_health_offer     TYPE TABLE OF rpben_oa,
          lt_insure_offer     TYPE TABLE OF rpben_ob,
          lt_saving_offer     TYPE TABLE OF rpben_oc,
          lt_spenda_offer     TYPE TABLE OF rpben_od,
          lt_miscel_offer     TYPE TABLE OF rpben_oe,
          lt_stockp_offer     TYPE TABLE OF rpben_of,
          lt_credit_offer     TYPE TABLE OF rpben_o1,
          lt_depend_offer     TYPE TABLE OF rpbenodp,
          lt_depend_displ     TYPE TABLE OF rpbenddp,
          lt_benefi_offer     TYPE TABLE OF rpbenobf,
          lt_invest_offer     TYPE TABLE OF rpbenoiv,
          lt_coreq            TYPE hrben00crq,
          lt_t74hb            TYPE TABLE OF t74hb,

          ls_part_plans       TYPE cl_hcmfab_ben_enrollme_mpc=>ts_participatingplan,
          ls_health_plan      TYPE rpben_da,
          ls_credit_plan      TYPE rpben_d1,
          ls_insurance_plan   TYPE rpben_db,
          ls_savings_plan     TYPE rpben_dc,
          ls_spendings_plan   TYPE rpben_dd,
          ls_miscel_plan      TYPE rpben_de,
          ls_stockp_plan      TYPE rpben_df,
          ls_stockp_plans     TYPE rpben_df,
          ls_health_offer     TYPE rpben_oa,
          ls_insure_offer     TYPE rpben_ob,
          ls_saving_offer     TYPE rpben_oc,
          ls_spenda_offer     TYPE rpben_od,
          ls_miscel_offer     TYPE rpben_oe,
          ls_stockp_offer     TYPE rpben_of,
          ls_credit_offer     TYPE rpben_o1,
          ls_depend_offer     TYPE rpbenodp,
          ls_depend_displ     TYPE rpbenddp,
          ls_benefi_offer     TYPE rpbenobf,
          ls_invest_offer     TYPE rpbenoiv,
          ls_filter           TYPE /iwbep/s_mgw_select_option,
          ls_range            TYPE /iwbep/s_cod_select_option,
          ls_event_desc       TYPE rpbenevent,
          ls_offer_un         TYPE cl_hcmfab_ben_enrollme_mpc=>ts_offer,
          ls_offer            TYPE cl_hcmfab_ben_enrollme_mpc=>ts_offer,
          ls_beneficiary      TYPE cl_hcmfab_ben_enrollme_mpc=>ts_beneficiary,
          ls_correq           TYPE rpbencrq,
          ls_correq_out       TYPE cl_hcmfab_ben_enrollme_mpc=>ts_corequisite,
          ls_investment       TYPE cl_hcmfab_ben_enrollme_mpc=>ts_investment,
          ls_expanded         LIKE LINE OF et_expanded_tech_clauses,
          ls_h5uca            TYPE t5uca,
          ls_t74hb            TYPE t74hb,
          ls_benefit_data     TYPE rpbeneedat,

          lv_ben_area         TYPE ben_area,
          lv_event_type       TYPE ben_enrtyp,
          lv_event            TYPE ben_event,
          lv_pernr            TYPE pernr_d,
          lv_assignment       TYPE pcce_pernr,
          lv_eff_begda        TYPE sy-datum,
          lv_eff_endda        TYPE sy-datum,
          lv_enrl_begda       TYPE sy-datum,
          lv_enrl_endda       TYPE sy-datum,
          lv_depen            TYPE string,
          lv_benif            TYPE string,
          lv_invest           TYPE string,
          lv_perc             TYPE string,
          lv_subrc            TYPE sysubrc,
          lv_datum            TYPE sydatum,
          lv_event_group      TYPE t74f1-evtgr,
          lv_prev_ins_plan    TYPE ben_plan,
          lv_prev_sav_plan    TYPE ben_plan,
          lv_prev_misc_plan   TYPE ben_plan,
          lv_prev_stoc_plan   TYPE ben_plan,
          lv_retcd            TYPE sysubrc,

          lo_employee_api     TYPE REF TO cl_hcmfab_employee_api,
          lx_badi_error       TYPE REF TO cx_hcmfab_benefits_enrollment,
          lx_exception        TYPE REF TO cx_static_check.

    FIELD-SYMBOLS:<fs_sprps>       TYPE sprps,
                  <fs_part_plans>  TYPE cl_hcmfab_ben_enrollme_mpc=>ts_participatingplan.

  IF iv_entity_name EQ 'Offer'.

    CLEAR:lv_ben_area, lv_event_type,lv_pernr,lv_event ,lv_eff_begda,
          lv_eff_endda,lv_enrl_begda,lv_enrl_endda.
    LOOP AT it_filter_select_options INTO ls_filter.
      CLEAR ls_range.
      READ TABLE ls_filter-select_options INTO ls_range INDEX 1.
      IF sy-subrc = 0 AND
         ls_range-sign EQ 'I' AND ls_range-option EQ 'EQ'.
        CASE ls_filter-property.
          WHEN 'BenefitArea'.
            lv_ben_area = ls_range-low.
          WHEN 'EventType'.
            lv_event_type = ls_range-low.
          WHEN 'EmployeeNumber'.
            lv_pernr = ls_range-low.
          WHEN 'Event'.
            lv_event = ls_range-low.
          WHEN 'BeginDate'.
            lv_eff_begda = ls_range-low.
          WHEN 'EndDate'.
            lv_eff_endda = ls_range-low.
          WHEN 'EnrollmentBeginDate'.
            lv_enrl_begda = ls_range-low.
          WHEN 'EnrollmentEndDate'.
            lv_enrl_endda = ls_range-low.
        ENDCASE.
      ENDIF.
    ENDLOOP.

    lv_datum = sy-datum.

    TRY.

        TRY.
            "Check if Pernr is valid or not
             go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                            iv_application_id = gc_application_id-mybenefitsenrollment ).
          CATCH cx_hcmfab_common INTO lx_exception.
            cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
            ).
        ENDTRY.
        "Set terms and agreement
        agree_terms_and_conds(
          EXPORTING
            iv_pernr  = lv_pernr
            iv_event  = lv_event
            iv_agreed = c_true
            iv_barea  = lv_ben_area
            iv_enrty  = lv_event_type
        ).
        "Beneficaires, Investments and Corequisites will be filled irrespective of whether the Plan is enrolled Plan or not.
        CLEAR:lt_credit_plans,lt_health_plans,lt_insurance_plans,lt_savings_plans,
              lt_spendings_plans,lt_miscel_plans,lt_stockp_plans,lv_subrc,lt_error_table,ls_event_desc.
        CALL FUNCTION 'HR_BEN_ESS_GET_PARTICP_PLANS'
          EXPORTING
            pernr        = lv_pernr
            begda        = lv_eff_begda
            endda        = lv_eff_endda
            reaction     = c_reaction_n
          IMPORTING
            subrc        = lv_subrc
            error_table  = lt_error_table
          TABLES
            credit_displ = lt_credit_plans
            health_displ = lt_health_plans
            insure_displ = lt_insurance_plans
            saving_displ = lt_savings_plans
            spenda_displ = lt_spendings_plans
            miscel_displ = lt_miscel_plans
            stockp_displ = lt_stockp_plans.

        ls_event_desc-barea = lv_ben_area.
        ls_event_desc-pernr = lv_pernr.
        ls_event_desc-event = lv_event.
        ls_event_desc-begda = lv_enrl_begda.
        ls_event_desc-endda = lv_enrl_endda.

        CLEAR :lv_subrc,lt_health_offer,lt_insure_offer,lt_saving_offer,lt_spenda_offer,lt_miscel_offer,
               lt_stockp_offer,lt_credit_offer,lt_depend_offer,lt_benefi_offer,lt_invest_offer.
        CALL METHOD me->hr_get_offer
          EXPORTING
            iv_pernr         = lv_pernr
            iv_datum         = lv_datum
            iv_ben_area      = lv_ben_area
            iv_event         = lv_event
            iv_event_type    = lv_event_type
            is_event_desc    = ls_event_desc
          IMPORTING
            ev_subrc         = lv_subrc
            et_error_table   = lt_error_table
            et_health_offer  = lt_health_offer
            et_insure_offer  = lt_insure_offer
            et_saving_offer  = lt_saving_offer
            et_spenda_offer  = lt_spenda_offer
            et_miscel_offer  = lt_miscel_offer
            et_stockp_offer  = lt_stockp_offer
            et_credit_offer  = lt_credit_offer
            et_dependents    = lt_depend_offer
            et_beneficiaries = lt_benefi_offer
            et_investments   = lt_invest_offer.

        SORT lt_health_offer BY barea bpcat pltyp bplan begda endda sprps DESCENDING enrolled DESCENDING.
        DELETE ADJACENT DUPLICATES FROM lt_health_offer COMPARING barea bpcat pltyp bplan begda endda sprps.

        SORT lt_insure_offer BY barea bpcat pltyp bplan begda endda sprps DESCENDING enrolled DESCENDING.
        DELETE ADJACENT DUPLICATES FROM lt_insure_offer COMPARING barea bpcat pltyp bplan begda endda sprps.

        SORT lt_saving_offer BY barea bpcat pltyp bplan begda endda enrolled DESCENDING.
        DELETE ADJACENT DUPLICATES FROM lt_saving_offer COMPARING barea bpcat pltyp bplan begda endda.

        SORT lt_spenda_offer BY barea bpcat pltyp bplan begda endda enrolled DESCENDING.
        DELETE ADJACENT DUPLICATES FROM lt_spenda_offer COMPARING barea bpcat pltyp bplan begda endda.

        SORT lt_miscel_offer BY barea bpcat pltyp bplan begda endda enrolled DESCENDING.
        DELETE ADJACENT DUPLICATES FROM lt_miscel_offer COMPARING barea bpcat pltyp bplan begda endda.

        SORT lt_stockp_offer BY barea bpcat pltyp bplan begda endda  enrolled DESCENDING.
        DELETE ADJACENT DUPLICATES FROM lt_stockp_offer COMPARING barea bpcat pltyp bplan begda endda.

        SORT lt_credit_offer BY barea bpcat pltyp bplan begda endda enrolled DESCENDING.
        DELETE ADJACENT DUPLICATES FROM lt_credit_offer COMPARING barea bpcat pltyp bplan begda endda.
        CLEAR:lv_subrc.

        "" Get co-requisites for offer tables
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

        IF lv_event_type = c_event_offer.

          CALL FUNCTION 'HR_BEN_GET_FROM_FEATURE_EVTGR'
            EXPORTING
              pernr       = lv_pernr
              begda       = lv_eff_begda
              endda       = lv_eff_endda
              barea       = lv_ben_area
              reaction    = c_reaction_n
            IMPORTING
              evtgr       = lv_event_group
            TABLES
              error_table = lt_error_table.

          IF lv_event_group IS NOT INITIAL.

            SELECT * FROM t74hb INTO TABLE lt_t74hb
              WHERE barea = lv_ben_area
              AND   event = lv_event
              AND   evtgr = lv_event_group.

          ENDIF.

        ENDIF.

        IF lt_health_offer IS NOT INITIAL.

          ls_benefit_data-pernr = lv_pernr.
          ls_benefit_data-barea = lv_ben_area.

          CALL FUNCTION 'HR_BEN_READ_DEPENDENTS'
            EXPORTING
              ee_benefit_data = ls_benefit_data
              bpcat           = c_health_plan
              begda           = lv_eff_begda
              endda           = lv_eff_endda
              logicview       = ''
              reaction        = c_reaction_n
            IMPORTING
              subrc           = lv_subrc
            TABLES
              existing_dep    = lt_depend_displ
              error_table     = lt_error_table.

          CLEAR:ls_h5uca.
          LOOP AT lt_health_offer INTO ls_health_offer.
            IF ls_health_offer-enrolled = c_true.
              CLEAR ls_health_plan.
              READ TABLE lt_health_plans INTO ls_health_plan
                WITH KEY barea = ls_health_offer-barea
                         bpcat = ls_health_offer-bpcat
                         pltyp = ls_health_offer-pltyp
                         bplan = ls_health_offer-bplan
                         begda = ls_health_offer-begda
                         endda = ls_health_offer-endda
                         sprps = ls_health_offer-sprps.
              IF sy-subrc = 0.
                MOVE-CORRESPONDING ls_health_plan TO ls_offer.
              ENDIF.
              LOOP AT lt_depend_displ INTO ls_depend_displ   "Dependents needs to be filled only for enrolled Plans
                WHERE barea = ls_health_offer-barea AND
                      bpcat = ls_health_offer-bpcat AND
                      pltyp = ls_health_offer-pltyp AND
                      begda = ls_health_offer-begda AND
                      endda = ls_health_offer-endda AND
                      bplan = ls_health_offer-bplan.
                ASSIGN COMPONENT 'SPRPS' OF STRUCTURE ls_depend_displ to <fs_sprps>.
                IF <fs_sprps> IS ASSIGNED AND <fs_sprps> = ls_health_offer-sprps.
*                 CONCATENATE ls_depend_displ-dep_name '(' ls_depend_displ-relation ')' INTO lv_depen. "Note 2825660
                 lv_depen = ls_depend_displ-dep_name. "Note 2825660
                 IF ls_offer-depben_name IS INITIAL.
                   ls_offer-depben_name = lv_depen.
                 ELSE.
                   CONCATENATE ls_offer-depben_name lv_depen INTO ls_offer-depben_name SEPARATED BY ', '.
                 ENDIF.
                 CLEAR:ls_depend_displ, lv_depen.
                ENDIF.
              ENDLOOP.

              ls_offer-add_bplan = c_false.
              ls_offer-chg_bplan = c_true.
              IF lt_t74hb IS NOT INITIAL.
                READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_offer-pltyp.
                ls_offer-del_bplan = ls_t74hb-del_bplan.
                CLEAR ls_t74hb.
              ELSE.
                ls_offer-del_bplan = c_true.
              ENDIF.

            ENDIF.
            ls_offer-event = lv_event.
            ls_offer-enrty = lv_event_type.
            LOOP AT lt_coreq INTO ls_correq
              WHERE barea = ls_health_offer-barea AND
                    bplan = ls_health_offer-bplan.

              cl_hr_t5uca=>read(
                EXPORTING
                  langu = sy-langu
                  barea = ls_correq-barea
                  bplan = ls_correq-copln
                RECEIVING
                  t5uca = ls_h5uca
              ).
              ls_correq_out-txt_copln = ls_h5uca-ltext.
              CLEAR ls_h5uca.

              MOVE-CORRESPONDING ls_health_offer TO ls_correq_out.
              MOVE-CORRESPONDING ls_correq TO ls_correq_out.
              enrich_corequisite( CHANGING coreqisiteentity = ls_correq_out ).
              APPEND ls_correq_out TO ls_offer-offercorequisite.
              CLEAR:ls_h5uca,ls_correq_out.
            ENDLOOP.

            MOVE-CORRESPONDING ls_health_offer TO ls_offer.
            IF ls_offer-enrolled <> c_true.
              ls_offer_un = ls_offer.
              adjust_unenrolled_offer(
                EXPORTING
                  is_offer = ls_offer_un
                IMPORTING
                  es_offer = ls_offer
              ).
              ls_offer-offercorequisite = ls_offer_un-offercorequisite.
              CLEAR ls_offer_un.
            ENDIF.

            enrich_offer( CHANGING offerentity = ls_offer ).
            APPEND ls_offer TO lt_offer.
            CLEAR:ls_health_offer,ls_offer.
          ENDLOOP.
        ENDIF.

        IF lt_insure_offer IS NOT INITIAL.
          CLEAR:ls_h5uca.
          LOOP AT lt_insure_offer INTO ls_insure_offer.
            IF ls_insure_offer-enrolled = c_true.
              CLEAR:ls_insurance_plan.
              READ TABLE lt_insurance_plans INTO ls_insurance_plan
                WITH KEY barea = ls_insure_offer-barea
                         bpcat = ls_insure_offer-bpcat
                         pltyp = ls_insure_offer-pltyp
                         bplan = ls_insure_offer-bplan
                         begda = ls_insure_offer-begda
                         endda = ls_insure_offer-endda
                         sprps = ls_insure_offer-sprps.
              IF sy-subrc = 0.
                MOVE-CORRESPONDING ls_insurance_plan TO ls_offer.
              ENDIF.
              ls_offer-add_bplan = c_false.
              ls_offer-chg_bplan = c_true.
              IF lt_t74hb IS NOT INITIAL.
                READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_offer-pltyp.
                ls_offer-del_bplan = ls_t74hb-del_bplan.
                CLEAR ls_t74hb.
              ELSE.
                ls_offer-del_bplan = c_true.
              ENDIF.
            ENDIF.

            ls_offer-event = lv_event.
            ls_offer-enrty = lv_event_type.
            LOOP AT lt_benefi_offer INTO ls_benefi_offer
            WHERE barea = ls_insure_offer-barea AND
                  bpcat = ls_insure_offer-bpcat AND
                  pltyp = ls_insure_offer-pltyp AND
                  bplan = ls_insure_offer-bplan AND
                  begda = ls_insure_offer-begda AND
                  endda = ls_insure_offer-endda.
              IF ls_benefi_offer-selected = c_true.
                MOVE ls_benefi_offer-ben_pct TO lv_perc.
                CONDENSE lv_perc NO-GAPS.
*                CONCATENATE ls_benefi_offer-ben_name '(' ls_benefi_offer-relation '-' lv_perc ')'  "Note 2825660
*                  INTO lv_benif.
                CONCATENATE '(' lv_perc '%' ')' INTO lv_benif.
                CONCATENATE ls_benefi_offer-ben_name lv_benif INTO lv_benif SEPARATED BY space.
                IF ls_benefi_offer-contingent = c_true.
                  IF ls_offer-cntg_ben_name IS INITIAL.
                    ls_offer-cntg_ben_name = lv_benif.
                  ELSE.
                    CONCATENATE ls_offer-cntg_ben_name lv_benif INTO ls_offer-cntg_ben_name SEPARATED BY ', '.
                  ENDIF.
                ELSE.
                  IF ls_offer-prmy_ben_name IS INITIAL.
                    ls_offer-prmy_ben_name = lv_benif.
                  ELSE.
                    CONCATENATE ls_offer-prmy_ben_name lv_benif INTO ls_offer-prmy_ben_name SEPARATED BY ', '.
                  ENDIF.
                ENDIF.
                CLEAR :lv_perc, lv_benif.
              ENDIF.
              MOVE-CORRESPONDING ls_insure_offer TO ls_beneficiary.
              MOVE-CORRESPONDING ls_benefi_offer TO ls_beneficiary.
              ls_beneficiary-event = lv_event.
              enrich_beneficiary( CHANGING beneficiaryentity = ls_beneficiary ).
              APPEND ls_beneficiary  TO ls_offer-offerbeneficiary.
              CLEAR:ls_benefi_offer,ls_beneficiary.
            ENDLOOP.

            LOOP AT lt_coreq INTO ls_correq
              WHERE barea = ls_insure_offer-barea AND
                    bplan = ls_insure_offer-bplan.
              cl_hr_t5uca=>read(
                EXPORTING
                  langu = sy-langu
                  barea = ls_correq-barea
                  bplan = ls_correq-copln
                RECEIVING
                  t5uca = ls_h5uca
              ).
              ls_correq_out-txt_copln = ls_h5uca-ltext.
              CLEAR ls_h5uca.

              MOVE-CORRESPONDING ls_insure_offer TO ls_correq_out.
              MOVE-CORRESPONDING ls_correq TO ls_correq_out.
              enrich_corequisite( CHANGING coreqisiteentity = ls_correq_out ).
              APPEND ls_correq_out TO ls_offer-offercorequisite.
              CLEAR:ls_h5uca,ls_correq_out.
            ENDLOOP.

            MOVE-CORRESPONDING ls_insure_offer TO ls_offer.
            "Note 2925289: Fill alternative cost of the enrolled plans ( if maintained )
            "and change option text to ' Current Coverage Amount"
            CLEAR:ls_insurance_plan.
            READ TABLE lt_insurance_plans  INTO ls_insurance_plan
                WITH KEY barea = ls_insure_offer-barea
                         bpcat = ls_insure_offer-bpcat
                         pltyp = ls_insure_offer-pltyp
                         bplan = ls_insure_offer-bplan
                         begda = ls_insure_offer-begda
                         endda = ls_insure_offer-endda
                         sprps = ls_insure_offer-sprps.

              IF sy-subrc = 0 and ls_insurance_plan-covov gt 0.
                ls_offer-covov = ls_insurance_plan-covov.
                ls_offer-txt_option = text-TAC.
              ENDIF.

            IF ls_offer-enrolled <> c_true.
              ls_offer_un = ls_offer.
              adjust_unenrolled_offer(
                EXPORTING
                  is_offer = ls_offer_un
                IMPORTING
                  es_offer = ls_offer
              ).
              ls_offer-offercorequisite = ls_offer_un-offercorequisite.
              ls_offer-offerbeneficiary = ls_offer_un-offerbeneficiary.
              CLEAR ls_offer_un.
            ENDIF.

            enrich_offer( CHANGING offerentity = ls_offer ).

            APPEND ls_offer TO lt_offer.
            lv_prev_ins_plan = ls_insure_offer-bplan.
            CLEAR:ls_insure_offer,ls_offer.
          ENDLOOP.
        ENDIF.

        IF lt_saving_offer IS NOT INITIAL.
          CLEAR:ls_invest_offer,ls_investment,ls_benefi_offer,ls_beneficiary,ls_h5uca,ls_correq.
          LOOP AT lt_saving_offer INTO ls_saving_offer.
            IF ls_saving_offer-enrolled = c_true.
              CLEAR ls_savings_plan.
              READ TABLE lt_savings_plans INTO ls_savings_plan
                WITH KEY barea = ls_saving_offer-barea
                         bpcat = ls_saving_offer-bpcat
                         pltyp = ls_saving_offer-pltyp
                         bplan = ls_saving_offer-bplan
                         begda = ls_saving_offer-begda
                         endda = ls_saving_offer-endda.
              IF sy-subrc = 0.
                MOVE-CORRESPONDING ls_savings_plan TO ls_offer.
              ENDIF.
              ls_offer-add_bplan = c_false.
              ls_offer-chg_bplan = c_true.
              IF lt_t74hb IS NOT INITIAL.
                READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_offer-pltyp.
                ls_offer-del_bplan = ls_t74hb-del_bplan.
                CLEAR ls_t74hb.
              ELSE.
                ls_offer-del_bplan = c_true.
              ENDIF.
            ENDIF.

            LOOP AT lt_invest_offer INTO ls_invest_offer
            WHERE barea = ls_saving_offer-barea AND
                  bpcat = ls_saving_offer-bpcat AND
                  pltyp = ls_saving_offer-pltyp AND
                  bplan = ls_saving_offer-bplan AND
                  begda = ls_saving_offer-begda AND
                  endda = ls_saving_offer-endda.
              IF ls_invest_offer-selected = c_true.
                CLEAR:lv_invest.
                concat_investment_offer( EXPORTING is_investment = ls_invest_offer IMPORTING ev_investment = lv_invest ).
                IF ls_offer-ben_investment IS INITIAL.
                  ls_offer-ben_investment = lv_invest.
                ELSE.
                  CONCATENATE ls_offer-ben_investment lv_invest INTO ls_offer-ben_investment SEPARATED BY ', '.
                ENDIF.
              ENDIF.
              MOVE-CORRESPONDING ls_saving_offer TO ls_investment.
              MOVE-CORRESPONDING ls_invest_offer TO ls_investment.
              enrich_investment( CHANGING investment_entity = ls_investment ).
              APPEND ls_investment  TO ls_offer-offerinvestment.
              CLEAR:ls_invest_offer,ls_investment.
            ENDLOOP.

            LOOP AT lt_benefi_offer INTO ls_benefi_offer
            WHERE barea = ls_saving_offer-barea AND
                  bpcat = ls_saving_offer-bpcat AND
                  pltyp = ls_saving_offer-pltyp AND
                  bplan = ls_saving_offer-bplan AND
                  begda = ls_saving_offer-begda AND
                  endda = ls_saving_offer-endda.
              IF ls_benefi_offer-selected = c_true.
                CLEAR:lv_perc, lv_benif.
                MOVE ls_benefi_offer-ben_pct TO lv_perc.
                CONDENSE lv_perc NO-GAPS.
*                CONCATENATE ls_benefi_offer-ben_name '(' ls_benefi_offer-relation '-' lv_perc ')' INTO lv_benif. "Note 2825660
                CONCATENATE '(' lv_perc '%' ')' INTO lv_benif.
                CONCATENATE ls_benefi_offer-ben_name lv_benif INTO lv_benif SEPARATED BY space.
                IF ls_benefi_offer-contingent = c_true.
                  IF ls_offer-cntg_ben_name IS INITIAL.
                    ls_offer-cntg_ben_name = lv_benif.
                  ELSE.
                    CONCATENATE ls_offer-cntg_ben_name lv_benif INTO ls_offer-cntg_ben_name SEPARATED BY ', '.
                  ENDIF.
                ELSE.
                  IF ls_offer-prmy_ben_name IS INITIAL.
                    ls_offer-prmy_ben_name = lv_benif.
                  ELSE.
                    CONCATENATE ls_offer-prmy_ben_name lv_benif INTO ls_offer-prmy_ben_name SEPARATED BY ', '.
                  ENDIF.
                ENDIF.
                CLEAR:lv_perc,lv_benif.
              ENDIF.
              MOVE-CORRESPONDING ls_saving_offer TO ls_beneficiary.
              MOVE-CORRESPONDING ls_benefi_offer TO ls_beneficiary.
              ls_beneficiary-event = lv_event.
              enrich_beneficiary( CHANGING beneficiaryentity = ls_beneficiary ).
              APPEND ls_beneficiary  TO ls_offer-offerbeneficiary.
              CLEAR:ls_benefi_offer,ls_beneficiary.
            ENDLOOP.

            ls_offer-event = lv_event.
            ls_offer-enrty = lv_event_type.

            LOOP AT lt_coreq INTO ls_correq
              WHERE barea = ls_saving_offer-barea AND
                    bplan = ls_saving_offer-bplan.

              cl_hr_t5uca=>read(
                EXPORTING
                  langu = sy-langu
                  barea = ls_correq-barea
                  bplan = ls_correq-copln
                RECEIVING
                  t5uca = ls_h5uca
              ).
              ls_correq_out-txt_copln = ls_h5uca-ltext.
              CLEAR ls_h5uca.
              MOVE-CORRESPONDING ls_saving_offer TO ls_correq_out.
              MOVE-CORRESPONDING ls_correq TO ls_correq_out.
              enrich_corequisite( CHANGING coreqisiteentity = ls_correq_out ).
              APPEND ls_correq_out TO ls_offer-offercorequisite.
              CLEAR:ls_h5uca,ls_correq_out.
            ENDLOOP.

            MOVE-CORRESPONDING ls_saving_offer TO ls_offer.
            IF ls_offer-enrolled <> c_true.
              ls_offer_un = ls_offer.
              adjust_unenrolled_offer(
                EXPORTING
                  is_offer = ls_offer_un
                IMPORTING
                  es_offer = ls_offer
              ).
              ls_offer-offercorequisite = ls_offer_un-offercorequisite.
              ls_offer-offerbeneficiary = ls_offer_un-offerbeneficiary.
              ls_offer-offerinvestment = ls_offer_un-offerinvestment.
              CLEAR ls_offer_un.
            ENDIF.

            enrich_offer( CHANGING offerentity = ls_offer ).
            APPEND ls_offer TO lt_offer.
            lv_prev_sav_plan = ls_saving_offer-bplan.
            CLEAR:ls_saving_offer,ls_offer.
          ENDLOOP.
        ENDIF.

        IF lt_spenda_offer IS NOT INITIAL.
          CLEAR:ls_h5uca,ls_correq.
          LOOP AT lt_spenda_offer INTO ls_spenda_offer.
            IF ls_spenda_offer-enrolled = c_true.
              READ TABLE lt_spendings_plans INTO ls_spendings_plan
                WITH KEY barea = ls_spenda_offer-barea
                         bpcat = ls_spenda_offer-bpcat
                         pltyp = ls_spenda_offer-pltyp
                         bplan = ls_spenda_offer-bplan
                         begda = ls_spenda_offer-begda
                         endda = ls_spenda_offer-endda.
              IF sy-subrc = 0.
                MOVE-CORRESPONDING ls_spendings_plan TO ls_offer.
                CLEAR ls_spendings_plan.
              ENDIF.

              ls_offer-add_bplan = c_false.
              ls_offer-chg_bplan = c_true.
              IF lt_t74hb IS NOT INITIAL.
                READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_offer-pltyp.
                ls_offer-del_bplan = ls_t74hb-del_bplan.
                CLEAR ls_t74hb.
              ELSE.
                ls_offer-del_bplan = c_true.
              ENDIF.

              calculate_per_period_cntr(
                EXPORTING
                  iv_pernr               = lv_pernr
                  iv_datum               = lv_datum
                  iv_contrib_amount      = ls_spenda_offer-camnt
                IMPORTING
                  ev_cntr_amt_per_period = ls_offer-perperiodcamnt
              ).

            ENDIF.

            ls_offer-event = lv_event.
            ls_offer-enrty = lv_event_type.
            LOOP AT lt_coreq INTO ls_correq
              WHERE barea = ls_spenda_offer-barea AND
                    bplan = ls_spenda_offer-bplan.
              cl_hr_t5uca=>read(
                EXPORTING
                  langu = sy-langu
                  barea = ls_correq-barea
                  bplan = ls_correq-copln
                RECEIVING
                  t5uca = ls_h5uca
              ).
              ls_correq_out-txt_copln = ls_h5uca-ltext.
              CLEAR ls_h5uca.
              MOVE-CORRESPONDING ls_spenda_offer TO ls_correq_out.
              MOVE-CORRESPONDING ls_correq TO ls_correq_out.
              enrich_corequisite( CHANGING coreqisiteentity = ls_correq_out ).
              APPEND ls_correq_out TO ls_offer-offercorequisite.
              CLEAR:ls_h5uca,ls_correq_out.
            ENDLOOP.
            MOVE-CORRESPONDING ls_spenda_offer TO ls_offer.
            get_perio_and_perio_text(
               EXPORTING
                  iv_pernr               = lv_pernr
                  iv_datum               = lv_datum
                IMPORTING
                  ev_period              = ls_offer-perio
                  ev_period_text         = ls_offer-txt_period
            ).
            IF ls_offer-enrolled <> c_true.
              ls_offer_un = ls_offer.
              adjust_unenrolled_offer(
                EXPORTING
                  is_offer = ls_offer_un
                IMPORTING
                  es_offer = ls_offer
              ).
              ls_offer-offercorequisite = ls_offer_un-offercorequisite.
              CLEAR ls_offer_un.
            ENDIF.
            enrich_offer( CHANGING offerentity = ls_offer ).
            APPEND ls_offer TO lt_offer.
            CLEAR:ls_spenda_offer,ls_offer.
          ENDLOOP.
        ENDIF.

        IF lt_miscel_offer IS NOT INITIAL.
          CLEAR:ls_invest_offer,ls_investment,ls_depend_offer,ls_benefi_offer,ls_beneficiary,ls_h5uca,ls_correq.

          LOOP AT lt_miscel_offer INTO ls_miscel_offer.
            IF ls_miscel_offer-enrolled = c_true.
              CLEAR ls_miscel_plan.
              READ TABLE lt_miscel_plans INTO ls_miscel_plan
                WITH KEY barea = ls_miscel_offer-barea
                         bpcat = ls_miscel_offer-bpcat
                         pltyp = ls_miscel_offer-pltyp
                         bplan = ls_miscel_offer-bplan
                         begda = ls_miscel_offer-begda
                         endda = ls_miscel_offer-endda.
              IF sy-subrc = 0.
                MOVE-CORRESPONDING ls_miscel_plan TO ls_offer.
              ENDIF.
              ls_offer-add_bplan = c_false.
              ls_offer-chg_bplan = c_true.
              IF lt_t74hb IS NOT INITIAL.
                READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_offer-pltyp.
                ls_offer-del_bplan = ls_t74hb-del_bplan.
                CLEAR ls_t74hb.
              ELSE.
                ls_offer-del_bplan = c_true.
              ENDIF.
              IF ls_miscel_offer-depyn = c_true.
                LOOP AT lt_depend_offer INTO ls_depend_offer
                  WHERE barea = ls_miscel_offer-barea AND
                        bpcat = ls_miscel_offer-bpcat AND
                        pltyp = ls_miscel_offer-pltyp AND
                        bplan = ls_miscel_offer-bplan AND
                        begda = ls_miscel_offer-begda AND
                        endda = ls_miscel_offer-endda AND
                        selected = c_true.
                  CLEAR:lv_depen.
*                  CONCATENATE ls_depend_offer-dep_name '(' ls_depend_offer-relation ')' INTO lv_depen. "Note 2825660
                  lv_depen = ls_depend_offer-dep_name. "Note 2825660
                  IF ls_offer-depben_name IS INITIAL.
                    ls_offer-depben_name = lv_depen.
                  ELSE.
                    CONCATENATE ls_offer-depben_name lv_depen INTO ls_offer-depben_name SEPARATED BY ', '.
                  ENDIF.
                  CLEAR:ls_depend_offer.
                ENDLOOP.
              ENDIF.
            ENDIF.

            IF ls_miscel_offer-invyn = c_true.
              LOOP AT lt_invest_offer INTO ls_invest_offer
              WHERE barea = ls_miscel_offer-barea AND
                    bpcat = ls_miscel_offer-bpcat AND
                    pltyp = ls_miscel_offer-pltyp AND
                    bplan = ls_miscel_offer-bplan AND
                    begda = ls_miscel_offer-begda AND
                    endda = ls_miscel_offer-endda.
                IF ls_invest_offer-selected = c_true.
                  CLEAR:lv_invest.
                  concat_investment_offer( EXPORTING is_investment = ls_invest_offer IMPORTING ev_investment = lv_invest ).
                  IF ls_offer-ben_investment IS INITIAL.
                    ls_offer-ben_investment = lv_invest.
                  ELSE.
                    CONCATENATE ls_offer-ben_investment lv_invest INTO ls_offer-ben_investment SEPARATED BY ', '.
                  ENDIF.
                ENDIF.
                MOVE-CORRESPONDING ls_miscel_offer TO ls_investment.
                MOVE-CORRESPONDING ls_invest_offer TO ls_investment.
                enrich_investment( CHANGING investment_entity = ls_investment ).
                APPEND ls_investment  TO ls_offer-offerinvestment.
                CLEAR:ls_invest_offer,ls_investment.
              ENDLOOP.
            ENDIF.
            IF ls_miscel_offer-benyn = c_true.
              LOOP AT lt_benefi_offer INTO ls_benefi_offer
              WHERE barea = ls_miscel_offer-barea AND
                    bpcat = ls_miscel_offer-bpcat AND
                    pltyp = ls_miscel_offer-pltyp AND
                    bplan = ls_miscel_offer-bplan AND
                    begda = ls_miscel_offer-begda AND
                    endda = ls_miscel_offer-endda.
                IF ls_benefi_offer-selected = c_true.
                  CLEAR:lv_perc,lv_benif.
                  MOVE ls_benefi_offer-ben_pct TO lv_perc.
                  CONDENSE lv_perc NO-GAPS.
*                  CONCATENATE ls_benefi_offer-ben_name '(' ls_benefi_offer-relation '-' lv_perc ')' INTO lv_benif. "Note 2825660
                  CONCATENATE '(' lv_perc '%' ')' INTO lv_benif.
                  CONCATENATE ls_benefi_offer-ben_name lv_benif INTO lv_benif SEPARATED BY space.
                  IF ls_benefi_offer-contingent = c_true.
                    IF ls_offer-cntg_ben_name IS INITIAL.
                      ls_offer-cntg_ben_name = lv_benif.
                    ELSE.
                      CONCATENATE ls_offer-cntg_ben_name lv_benif INTO ls_offer-cntg_ben_name SEPARATED BY ', '.
                    ENDIF.
                  ELSE.
                    IF ls_offer-prmy_ben_name IS INITIAL.
                      ls_offer-prmy_ben_name = lv_benif.
                    ELSE.
                      CONCATENATE ls_offer-prmy_ben_name lv_benif INTO ls_offer-prmy_ben_name SEPARATED BY ', '.
                    ENDIF.
                  ENDIF.
                ENDIF.
                MOVE-CORRESPONDING ls_miscel_offer TO ls_beneficiary.
                MOVE-CORRESPONDING ls_benefi_offer TO ls_beneficiary.
                ls_beneficiary-event = lv_event.
                enrich_beneficiary( CHANGING beneficiaryentity = ls_beneficiary ).
                APPEND ls_beneficiary  TO ls_offer-offerbeneficiary.
                CLEAR:ls_benefi_offer,ls_beneficiary.
              ENDLOOP.
            ENDIF.
            ls_offer-event = lv_event.
            ls_offer-enrty = lv_event_type.
            LOOP AT lt_coreq INTO ls_correq
              WHERE barea = ls_miscel_offer-barea AND
                    bplan = ls_miscel_offer-bplan.
              cl_hr_t5uca=>read(
                EXPORTING
                  langu = sy-langu
                  barea = ls_correq-barea
                  bplan = ls_correq-copln
                RECEIVING
                  t5uca = ls_h5uca
              ).
              ls_correq_out-txt_copln = ls_h5uca-ltext.
              CLEAR ls_h5uca.
              MOVE-CORRESPONDING ls_miscel_offer TO ls_correq_out.
              MOVE-CORRESPONDING ls_correq TO ls_correq_out.
              enrich_corequisite( CHANGING coreqisiteentity = ls_correq_out ).
              APPEND ls_correq_out TO ls_offer-offercorequisite.
              CLEAR :ls_h5uca,ls_correq_out.
            ENDLOOP.
            MOVE-CORRESPONDING ls_miscel_offer TO ls_offer.

            IF ls_offer-enrolled <> c_true.
              ls_offer_un = ls_offer.
              adjust_unenrolled_offer(
                EXPORTING
                  is_offer = ls_offer_un
                IMPORTING
                  es_offer = ls_offer
              ).
              ls_offer-offercorequisite = ls_offer_un-offercorequisite.
              ls_offer-offerbeneficiary = ls_offer_un-offerbeneficiary.
              ls_offer-offerinvestment = ls_offer_un-offerinvestment.
              CLEAR ls_offer_un.
            ENDIF.
            enrich_offer( CHANGING offerentity = ls_offer ).
            APPEND ls_offer TO lt_offer.
            lv_prev_misc_plan = ls_miscel_offer.
            CLEAR:ls_miscel_offer,ls_offer.
          ENDLOOP.

        ENDIF.

        IF lt_stockp_offer IS NOT INITIAL.
          CLEAR:ls_benefi_offer,ls_beneficiary,ls_h5uca,ls_correq,ls_h5uca.
          LOOP AT lt_stockp_offer INTO ls_stockp_offer.
            IF ls_stockp_offer-enrolled = c_true.
              READ TABLE lt_stockp_plans INTO ls_stockp_plan
                WITH KEY barea = ls_stockp_offer-barea
                         bpcat = ls_stockp_offer-bpcat
                         pltyp = ls_stockp_offer-pltyp
                         bplan = ls_stockp_offer-bplan
                         begda = ls_stockp_offer-begda
                         endda = ls_stockp_offer-endda.
              CLEAR ls_stockp_plan.
              IF sy-subrc = 0.
                MOVE-CORRESPONDING ls_stockp_plan TO ls_offer.
              ENDIF.
              ls_offer-add_bplan = c_false.
              ls_offer-chg_bplan = c_true.
              IF lt_t74hb IS NOT INITIAL.
                READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_offer-pltyp.
                ls_offer-del_bplan = ls_t74hb-del_bplan.
                CLEAR ls_t74hb.
              ELSE.
                ls_offer-del_bplan = c_true.
              ENDIF.
            ENDIF.
            LOOP AT lt_benefi_offer INTO ls_benefi_offer
            WHERE barea = ls_stockp_offer-barea AND
                  bpcat = ls_stockp_offer-bpcat AND
                  pltyp = ls_stockp_offer-pltyp AND
                  bplan = ls_stockp_offer-bplan AND
                  begda = ls_stockp_offer-begda AND
                  endda = ls_stockp_offer-endda.
              IF ls_benefi_offer-selected = c_true.
                CLEAR:lv_perc, lv_benif.
                MOVE ls_benefi_offer-ben_pct TO lv_perc.
                CONDENSE lv_perc NO-GAPS.
*                CONCATENATE ls_benefi_offer-ben_name '(' ls_benefi_offer-relation '-' lv_perc ')' INTO lv_benif. "Note 2825660
                CONCATENATE '(' lv_perc '%' ')' INTO lv_benif.
                CONCATENATE ls_benefi_offer-ben_name lv_benif INTO lv_benif SEPARATED BY space.
                IF ls_benefi_offer-contingent = c_true.
                  IF ls_offer-cntg_ben_name IS INITIAL.
                    ls_offer-cntg_ben_name = lv_benif.
                  ELSE.
                    CONCATENATE ls_offer-cntg_ben_name lv_benif INTO ls_offer-cntg_ben_name SEPARATED BY ', '.
                  ENDIF.
                ELSE.
                  IF ls_offer-prmy_ben_name IS INITIAL.
                    ls_offer-prmy_ben_name = lv_benif.
                  ELSE.
                    CONCATENATE ls_offer-prmy_ben_name lv_benif INTO ls_offer-prmy_ben_name SEPARATED BY ', '.
                  ENDIF.
                ENDIF.
              ENDIF.
              MOVE-CORRESPONDING ls_stockp_offer TO ls_beneficiary.
              MOVE-CORRESPONDING ls_benefi_offer TO ls_beneficiary.
              ls_beneficiary-event = lv_event.
              enrich_beneficiary( CHANGING beneficiaryentity = ls_beneficiary ).
              APPEND ls_beneficiary  TO ls_offer-offerbeneficiary.
              CLEAR:ls_benefi_offer,ls_beneficiary.
            ENDLOOP.
            ls_offer-event = lv_event.
            ls_offer-enrty = lv_event_type.
            LOOP AT lt_coreq INTO ls_correq
              WHERE barea = ls_stockp_offer-barea AND
                    bplan = ls_stockp_offer-bplan.
              cl_hr_t5uca=>read(
                EXPORTING
                  langu = sy-langu
                  barea = ls_correq-barea
                  bplan = ls_correq-copln
                RECEIVING
                  t5uca = ls_h5uca
              ).
              ls_correq_out-txt_copln = ls_h5uca-ltext.
              CLEAR ls_h5uca.
              MOVE-CORRESPONDING ls_stockp_offer TO ls_correq_out.
              MOVE-CORRESPONDING ls_correq TO ls_correq_out.
              enrich_corequisite( CHANGING coreqisiteentity = ls_correq_out ).
              APPEND ls_correq_out TO ls_offer-offercorequisite.
              CLEAR :ls_h5uca,ls_correq_out.
            ENDLOOP.
            MOVE-CORRESPONDING ls_stockp_offer TO ls_offer.

            IF ls_offer-enrolled <> c_true.
              ls_offer_un = ls_offer.
              adjust_unenrolled_offer(
                EXPORTING
                  is_offer = ls_offer_un
                IMPORTING
                  es_offer = ls_offer
              ).
              ls_offer-offerbeneficiary = ls_offer_un-offerbeneficiary.
              ls_offer-offercorequisite = ls_offer_un-offercorequisite.
              CLEAR ls_offer_un.
            ENDIF.
            enrich_offer( CHANGING offerentity = ls_offer ).
            APPEND ls_offer TO lt_offer.
            lv_prev_stoc_plan = ls_stockp_offer-bplan.
            CLEAR:ls_stockp_offer,ls_offer.
          ENDLOOP.
        ENDIF.


        IF lt_credit_offer IS NOT INITIAL.
          CLEAR:ls_h5uca,ls_correq.
          LOOP AT lt_credit_offer INTO ls_credit_offer.
            IF ls_credit_offer-enrolled = c_true.
              CLEAR ls_credit_plan.
              READ TABLE lt_credit_plans INTO ls_credit_plan
                WITH KEY barea = ls_credit_offer-barea
                         bpcat = ls_credit_offer-bpcat
                         pltyp = ls_credit_offer-pltyp
                         bplan = ls_credit_offer-bplan
                         begda = ls_credit_offer-begda
                         endda = ls_credit_offer-endda.
              IF sy-subrc = 0.
                MOVE-CORRESPONDING ls_credit_plan TO ls_offer.
              ENDIF.

              ls_offer-add_bplan = c_false.
              ls_offer-chg_bplan = c_true.
              IF lt_t74hb IS NOT INITIAL.
                READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_offer-pltyp.
                ls_offer-del_bplan = ls_t74hb-del_bplan.
                CLEAR ls_t74hb.
              ELSE.
                ls_offer-del_bplan = c_true.
              ENDIF.
            ENDIF.
            ls_offer-event = lv_event.
            ls_offer-enrty = lv_event_type.
            LOOP AT lt_coreq INTO ls_correq
              WHERE barea = ls_credit_offer-barea AND
                    bplan = ls_credit_offer-bplan.

              cl_hr_t5uca=>read(
                EXPORTING
                  langu = sy-langu
                  barea = ls_correq-barea
                  bplan = ls_correq-copln
                RECEIVING
                  t5uca = ls_h5uca
              ).
              ls_correq_out-txt_copln = ls_h5uca-ltext.
              CLEAR ls_h5uca.
              MOVE-CORRESPONDING ls_credit_offer TO ls_correq_out.
              MOVE-CORRESPONDING ls_correq TO ls_correq_out.
              enrich_corequisite( CHANGING coreqisiteentity = ls_correq_out ).
              APPEND ls_correq_out TO ls_offer-offercorequisite.
              CLEAR:ls_h5uca,ls_correq_out.
            ENDLOOP.
            MOVE-CORRESPONDING ls_credit_offer TO ls_offer.
            IF ls_offer-enrolled <> c_true.
              ls_offer_un = ls_offer.
              adjust_unenrolled_offer(
                EXPORTING
                  is_offer = ls_offer_un
                IMPORTING
                  es_offer = ls_offer
              ).
              ls_offer-offercorequisite = ls_offer_un-offercorequisite.
              CLEAR ls_offer_un.
            ENDIF.
            enrich_offer( CHANGING offerentity = ls_offer ).
            APPEND ls_offer TO lt_offer.
            CLEAR:ls_credit_offer,ls_offer.
          ENDLOOP.
        ENDIF.

        APPEND 'OFFERBENEFICIARY' TO et_expanded_clauses.   "#EC NOTEXT
        APPEND 'OFFERINVESTMENT' TO et_expanded_clauses.    "#EC NOTEXT
        APPEND 'OFFERCOREQUISITE' TO et_expanded_clauses.   "#EC NOTEXT

        copy_data_to_ref(
          EXPORTING
            is_data = lt_offer
          CHANGING
            cr_data = er_entityset
        ).

        """ Delete paycheck related content from temp. table
        update_paycheck_data(
          EXPORTING
            iv_pernr   = lv_pernr
        ).

      CATCH cx_hcmfab_benefits_enrollment INTO lx_badi_error.
        cl_hcmfab_utilities=>raise_gateway_error(
            is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_badi_error )
            iv_entity   = io_tech_request_context->get_entity_type_name( )
        ).
    ENDTRY.

  ELSEIF iv_entity_name = 'ParticipatingPlan'.

    LOOP AT it_filter_select_options INTO ls_filter.
      CLEAR ls_range.
      READ TABLE ls_filter-select_options INTO ls_range INDEX 1.
      IF sy-subrc = 0 AND
         ls_range-sign EQ 'I' AND ls_range-option EQ 'EQ'.
         CASE ls_filter-property.
           WHEN 'EmployeeNumber'.
             lv_pernr = ls_range-low.
           WHEN 'EffectiveBeignDate'.
             lv_eff_begda = ls_range-low.
           WHEN 'EffectiveEndDate'.
             lv_eff_endda = ls_range-low.
         ENDCASE.
      ENDIF.
    ENDLOOP.

    TRY.

        TRY.
            "Check if Pernr is valid or not
             go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                            iv_application_id = gc_application_id-mybenefitsenrollment ).
          CATCH cx_hcmfab_common INTO lx_exception.
            cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
            ).
        ENDTRY.

        REFRESH lt_error_table_temp.

        CALL FUNCTION 'HR_BEN_READ_CREDIT_PLANS'
          EXPORTING
            pernr         = lv_pernr
            begda         = lv_eff_begda
            endda         = lv_eff_endda
            logicview     = c_false
            reaction      = c_reaction_n
          IMPORTING
            subrc         = lv_retcd
          TABLES
            ex_cred_plans = lt_credit_plans
            error_table   = lt_error_table_temp.
        IF lv_retcd NE 0.
           lv_subrc = lv_retcd.
        ENDIF.
        APPEND LINES OF lt_error_table_temp TO lt_error_table.

        REFRESH lt_error_table_temp.
        CALL FUNCTION 'HR_BEN_READ_HEALTH_PLANS'
          EXPORTING
            pernr         = lv_pernr
            begda         = lv_eff_begda
            endda         = lv_eff_endda
            logicview     = c_false
            reaction      = c_reaction_n
          IMPORTING
            subrc         = lv_retcd
          TABLES
            ex_heal_plans = lt_health_plans
            error_table   = lt_error_table_temp.
        IF lv_retcd NE 0.
           lv_subrc = lv_retcd.
        ENDIF.
        APPEND LINES OF lt_error_table_temp TO lt_error_table.

        REFRESH lt_error_table_temp.
        CALL FUNCTION 'HR_BEN_READ_INSURANCE_PLANS'
          EXPORTING
            pernr         = lv_pernr
            begda         = lv_eff_begda
            endda         = lv_eff_endda
            logicview     = c_false
            reaction      = c_reaction_n
          IMPORTING
            subrc         = lv_retcd
          TABLES
            ex_insu_plans = lt_insurance_plans
            error_table   = lt_error_table_temp.
        IF lv_retcd NE 0.
           lv_subrc = lv_retcd.
        ENDIF.
        APPEND LINES OF lt_error_table_temp TO lt_error_table.

        REFRESH lt_error_table_temp.
        CALL FUNCTION 'HR_BEN_READ_SAVINGS_PLANS'
          EXPORTING
            pernr         = lv_pernr
            begda         = lv_eff_begda
            endda         = lv_eff_endda
            logicview     = c_false
            reaction      = c_reaction_n
          IMPORTING
            subrc         = lv_retcd
          TABLES
            ex_save_plans = lt_savings_plans
            error_table   = lt_error_table_temp.
        IF lv_retcd NE 0.
           lv_subrc = lv_retcd.
        ENDIF.
        APPEND LINES OF lt_error_table_temp TO lt_error_table.

        REFRESH lt_error_table_temp.
        CALL FUNCTION 'HR_BEN_READ_SPENDING_PLANS'
          EXPORTING
            pernr         = lv_pernr
            begda         = lv_eff_begda
            endda         = lv_eff_endda
            logicview     = c_false
            reaction      = c_reaction_n
          IMPORTING
            subrc         = lv_retcd
          TABLES
            ex_spen_plans = lt_spendings_plans
            error_table   = lt_error_table_temp.
        IF lv_retcd NE 0.
           lv_subrc = lv_retcd.
        ENDIF.
        APPEND LINES OF lt_error_table_temp TO lt_error_table.

        REFRESH lt_error_table_temp.
        CALL FUNCTION 'HR_BEN_READ_MISCEL_PLANS'
          EXPORTING
            pernr         = lv_pernr
            begda         = lv_eff_begda
            endda         = lv_eff_endda
            logicview     = c_false
            reaction      = c_reaction_n
          IMPORTING
            subrc         = lv_retcd
          TABLES
            ex_misc_plans = lt_miscel_plans
            error_table   = lt_error_table_temp.
        IF lv_retcd NE 0.
           lv_subrc = lv_retcd.
        ENDIF.
        APPEND LINES OF lt_error_table_temp TO lt_error_table.

        REFRESH lt_error_table_temp.
        CALL FUNCTION 'HR_BEN_READ_STOCKP_PLANS'
          EXPORTING
            pernr         = lv_pernr
            begda         = lv_eff_begda
            endda         = lv_eff_endda
            logicview     = c_false
            reaction      = c_reaction_n
          IMPORTING
            subrc         = lv_retcd
          TABLES
            ex_stck_plans = lt_stockp_plans
            error_table   = lt_error_table_temp.
        IF lv_retcd NE 0.
           lv_subrc = lv_retcd.
        ENDIF.
        APPEND LINES OF lt_error_table_temp TO lt_error_table.

        IF lv_subrc NE 0.

          me->raise_exceptions(
          EXPORTING
             it_messages = lt_error_table
             iv_entity_name = iv_entity_name
          ).

        ELSE.

          LOOP AT lt_credit_plans INTO ls_credit_plan.
            MOVE-CORRESPONDING ls_credit_plan TO ls_part_plans.
            MOVE-CORRESPONDING ls_credit_plan TO ls_credit_offer.
            APPEND ls_credit_offer TO lt_credit_offer.
            APPEND ls_part_plans TO lt_part_plans.
            CLEAR: ls_credit_offer, ls_part_plans.
          ENDLOOP.

          LOOP AT lt_insurance_plans INTO ls_insurance_plan.
            MOVE-CORRESPONDING ls_insurance_plan TO ls_part_plans.
            MOVE-CORRESPONDING ls_insurance_plan TO ls_insure_offer.
            APPEND ls_insure_offer TO lt_insure_offer.
            APPEND ls_part_plans TO lt_part_plans.
            CLEAR: ls_insure_offer, ls_part_plans.
          ENDLOOP.

          LOOP AT lt_health_plans INTO ls_health_plan.
            MOVE-CORRESPONDING ls_health_plan TO ls_part_plans.
            MOVE-CORRESPONDING ls_health_plan TO ls_health_offer.
            APPEND ls_health_offer TO lt_health_offer.
            APPEND ls_part_plans TO lt_part_plans.
            CLEAR: ls_part_plans, ls_health_offer.
          ENDLOOP.

          LOOP AT lt_savings_plans INTO ls_savings_plan.
            MOVE-CORRESPONDING ls_savings_plan TO ls_part_plans.
            MOVE-CORRESPONDING ls_savings_plan TO ls_saving_offer.
            APPEND ls_saving_offer TO lt_saving_offer.
            APPEND ls_part_plans TO lt_part_plans.
            CLEAR: ls_part_plans, ls_saving_offer.
          ENDLOOP.

          LOOP AT lt_stockp_plans INTO ls_stockp_plan.
            MOVE-CORRESPONDING ls_stockp_plan TO ls_part_plans.
            MOVE-CORRESPONDING ls_stockp_plan TO ls_stockp_offer.
            APPEND ls_stockp_offer TO lt_stockp_offer.
            APPEND ls_part_plans TO lt_part_plans.
            CLEAR: ls_stockp_offer, ls_part_plans.
          ENDLOOP.

          LOOP AT lt_spendings_plans INTO ls_spendings_plan.
            MOVE-CORRESPONDING ls_spendings_plan TO ls_part_plans.
            MOVE-CORRESPONDING ls_spendings_plan TO ls_spenda_offer.
            APPEND ls_spenda_offer TO lt_spenda_offer.
            APPEND ls_part_plans TO lt_part_plans.
            CLEAR: ls_spenda_offer, ls_part_plans.
          ENDLOOP.

          LOOP AT lt_miscel_plans INTO ls_miscel_plan.
            MOVE-CORRESPONDING ls_miscel_plan TO ls_part_plans.
            MOVE-CORRESPONDING ls_miscel_plan TO ls_miscel_offer.
            APPEND ls_miscel_offer TO lt_miscel_offer.
            APPEND ls_part_plans TO lt_part_plans.
            CLEAR: ls_miscel_offer, ls_part_plans.
          ENDLOOP.

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
              error_table       = lt_error_table_temp.

          APPEND LINES OF lt_error_table_temp TO lt_error_table.

          LOOP AT lt_part_plans ASSIGNING <fs_part_plans>.

            LOOP AT lt_coreq INTO ls_correq
              WHERE barea = <fs_part_plans>-barea AND
                    bplan = <fs_part_plans>-bplan.

              cl_hr_t5uca=>read(
                EXPORTING
                  langu = sy-langu
                  barea = ls_correq-barea
                  bplan = ls_correq-copln
                RECEIVING
                  t5uca = ls_h5uca
              ).
              ls_correq_out-txt_copln = ls_h5uca-ltext.
              CLEAR ls_h5uca.

              MOVE-CORRESPONDING <fs_part_plans> TO ls_correq_out.
              MOVE-CORRESPONDING ls_correq TO ls_correq_out.
              enrich_corequisite( CHANGING coreqisiteentity = ls_correq_out ).
              APPEND ls_correq_out TO <fs_part_plans>-offercorequisite.
              CLEAR:ls_h5uca,ls_correq_out.
            ENDLOOP.

          ENDLOOP.

          APPEND 'OFFERCOREQUISITE' TO et_expanded_clauses.   "#EC NOTEXT

          copy_data_to_ref(
            EXPORTING
              is_data = lt_part_plans
            CHANGING
              cr_data = er_entityset
          ).

        ENDIF.

      CATCH cx_hcmfab_benefits_enrollment INTO lx_exception.
        cl_hcmfab_utilities=>raise_gateway_error(
        is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
        iv_entity   = io_tech_request_context->get_entity_type_name( )
    ).

    ENDTRY.

  ENDIF.
ENDMETHOD.
