METHOD add_plan_to_selection.

  DATA: lv_pernr            TYPE pernr_d,
        lv_subrc            TYPE sy-subrc,
        ls_offer            TYPE cl_hcmfab_ben_enrollme_mpc=>ts_offer,
        ls_proc_plan        TYPE rpben_gen_plan_info,
        ls_scrn_ctrl        TYPE rpben_screen_ctrl,
        ls_cost_cred        TYPE rpben_costcred_trans,
        ls_contrib          TYPE rpben_contrib_trans,
        ls_enrl_reason      TYPE rpbenenrollmentreason,
        ls_fsa_contr        TYPE rpben_fsacontrib_trans,
        ls_dependent        TYPE cl_hcmfab_ben_enrollme_mpc=>ts_dependent,
        ls_beneficiary      TYPE cl_hcmfab_ben_enrollme_mpc=>ts_beneficiary,
        ls_investment       TYPE cl_hcmfab_ben_enrollme_mpc=>ts_investment,
        ls_dep              TYPE rpbenodp,
        ls_ben              TYPE rpbenobf_ess,
        ls_inv              TYPE rpbenoiv,
        lt_dep              TYPE hrben00odp_ess,
        lt_ben              TYPE hrben00obf_ess,
        lt_inv              TYPE hrben00oiv,
        lt_error_table      TYPE hrben00err_ess,
        lo_employee_api     TYPE REF TO cl_hcmfab_employee_api,
        lo_ex               TYPE REF TO cx_root,
        lx_exception        TYPE REF TO cx_hcmfab_common.

  READ TABLE it_offer INTO ls_offer INDEX 1.
  lv_pernr = ls_offer-pernr.

  ls_enrl_reason-barea = ls_offer-barea.
  ls_enrl_reason-pernr = lv_pernr.
  ls_enrl_reason-event = ls_offer-event.
  ls_enrl_reason-begda = ls_offer-enrol_begda.
  ls_enrl_reason-endda = ls_offer-enrol_endda.
  ls_enrl_reason-enrty = ls_offer-enrty.

  TRY .
      LOOP AT it_offer INTO ls_offer.

        MOVE-CORRESPONDING ls_offer TO ls_proc_plan.

        CASE ls_offer-bpcat.
          WHEN c_credit_plan.  ""Credit,

            ls_scrn_ctrl-cred_yn = c_true.
            MOVE-CORRESPONDING ls_offer TO ls_cost_cred.

          WHEN c_health_plan. "Health

            ls_scrn_ctrl-cscyn = c_true.
            MOVE-CORRESPONDING ls_offer TO ls_cost_cred.

            LOOP AT it_dependent INTO ls_dependent
              WHERE barea = ls_offer-barea AND
              bpcat = ls_offer-bpcat AND
              pltyp = ls_offer-pltyp AND
              bplan = ls_offer-bplan AND
              sprps = ls_offer-sprps.

              MOVE-CORRESPONDING ls_dependent TO ls_dep.
              APPEND ls_dep TO lt_dep.
              CLEAR ls_dep.

            ENDLOOP.

          WHEN c_insurance_plan. "Insurance

            ls_scrn_ctrl-cscyn = c_true.
            MOVE-CORRESPONDING ls_offer TO ls_cost_cred.

            LOOP AT it_beneficiary INTO ls_beneficiary
              WHERE barea = ls_offer-barea AND
              bpcat = ls_offer-bpcat AND
              pltyp = ls_offer-pltyp AND
              bplan = ls_offer-bplan AND
              sprps = ls_offer-sprps.

              MOVE-CORRESPONDING ls_beneficiary TO ls_ben.
              IF ls_beneficiary-contingent IS NOT INITIAL. "2792075
                ls_ben-ctg_pct = ls_beneficiary-ben_pct.
                CLEAR ls_ben-ben_pct.
              ENDIF.
              APPEND ls_ben TO lt_ben.
              CLEAR ls_ben.

            ENDLOOP.

          WHEN c_savings_plan OR c_stock_purchase_plan.        ""Savings, Stock

            ls_scrn_ctrl-conyn = c_true.
            MOVE-CORRESPONDING ls_offer TO ls_contrib.

            LOOP AT it_beneficiary INTO ls_beneficiary
              WHERE barea = ls_offer-barea AND
              bpcat = ls_offer-bpcat AND
              pltyp = ls_offer-pltyp AND
              bplan = ls_offer-bplan AND
              sprps = ls_offer-sprps.

              MOVE-CORRESPONDING ls_beneficiary TO ls_ben.
              IF  ls_beneficiary-contingent = 'X'.
                ls_ben-ctg_pct = ls_beneficiary-ben_pct.
                CLEAR ls_ben-ben_pct.
              ENDIF.
              APPEND ls_ben TO lt_ben.
              CLEAR ls_ben.

            ENDLOOP.

            LOOP AT it_investment INTO ls_investment
              WHERE barea = ls_offer-barea AND
              bpcat = ls_offer-bpcat AND
              pltyp = ls_offer-pltyp AND
              bplan = ls_offer-bplan AND
              sprps = ls_offer-sprps.

              MOVE-CORRESPONDING ls_investment TO ls_inv.
              APPEND ls_inv TO lt_inv.
              CLEAR ls_inv.

            ENDLOOP.

          WHEN c_spendings_plan.  "FSA

            ls_scrn_ctrl-fsayn = c_true.
            MOVE-CORRESPONDING ls_offer TO ls_fsa_contr.


          WHEN c_miscellaneous_plan.  "Misc

            IF ls_offer-cstcr = c_true.
              ls_scrn_ctrl-cscyn = c_true.
            ELSE.
              ls_scrn_ctrl-cscyn = c_false.
              ls_scrn_ctrl-conyn = c_true.
            ENDIF.
            MOVE-CORRESPONDING ls_offer TO ls_cost_cred.
            MOVE-CORRESPONDING ls_offer TO ls_contrib.

            LOOP AT it_beneficiary INTO ls_beneficiary
              WHERE barea = ls_offer-barea AND
              bpcat = ls_offer-bpcat AND
              pltyp = ls_offer-pltyp AND
              bplan = ls_offer-bplan AND
              sprps = ls_offer-sprps.

              MOVE-CORRESPONDING ls_beneficiary TO ls_ben.
              IF ls_beneficiary-contingent IS NOT INITIAL."2792075
                ls_ben-ctg_pct = ls_beneficiary-ben_pct.
                CLEAR ls_ben-ben_pct.
              ENDIF.
              APPEND ls_ben TO lt_ben.
              CLEAR ls_ben.

            ENDLOOP.

            LOOP AT it_dependent INTO ls_dependent
              WHERE barea = ls_offer-barea AND
              bpcat = ls_offer-bpcat AND
              pltyp = ls_offer-pltyp AND
              bplan = ls_offer-bplan AND
              sprps = ls_offer-sprps.

              MOVE-CORRESPONDING ls_dependent TO ls_dep.
              APPEND ls_dep TO lt_dep.
              CLEAR ls_dep.

            ENDLOOP.

        ENDCASE.
        "Even the dependents, beneficiaries and investments from lt_dep, lt_ben and lt_inv will get filled into the *select_gt tables
        CALL FUNCTION 'HR_BEN_ESS_RFC_ADD_PLAN_TO_SEL'
          EXPORTING
            processed_plan   = ls_proc_plan
            screen_ctrl      = ls_scrn_ctrl
            costcred_trans   = ls_cost_cred
            contrib_trans    = ls_contrib
            fsacontrib_trans = ls_fsa_contr
            dep_trans        = lt_dep
            ben_trans        = lt_ben
            inv_trans        = lt_inv
          IMPORTING
            subrc            = lv_subrc
            error_table      = lt_error_table.
        APPEND LINES OF lt_error_table TO et_error_table.

        CLEAR: ls_proc_plan, ls_scrn_ctrl, ls_cost_cred, ls_contrib, ls_fsa_contr, lt_dep, lt_ben, lt_inv.

      ENDLOOP.

    CATCH cx_root INTO lo_ex.

  ENDTRY.


ENDMETHOD.
