METHOD /iwbep/if_mgw_appl_srv_runtime~execute_action.

  CASE iv_action_name.

    WHEN 'FI_GetCorequisites'.
      execute_action_correq(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_EmailConfStatement'.
      execute_action_email_conf_stmt(
        EXPORTING
          iv_action_name          = iv_action_name
          it_parameter            = it_parameter
          io_tech_request_context = io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).


    WHEN 'FI_GetEoiText'.
      execute_action_get_eoi_text(
        EXPORTING
          iv_action_name          = iv_action_name
          it_parameter            = it_parameter
          io_tech_request_context = io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_GetTermsAndConds'.
      execute_action_terms_condition(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_ContribCheck'.
      execute_action_contrib_check(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_CostCreditCheck'.
      execute_action_ccredit_check(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_SpendingCheck'.
      execute_action_spending_check(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_CalcPerPeriodCntr'.
      exec_action_calc_perperio_cntr(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_BeneficiaryCheck'.
      execute_action_beneficiary_chk(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_DependentCheck'.
      execute_action_dependent_check(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_InvestmentCheck'.
      execute_action_investment_chk(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

    WHEN 'FI_GetEoiEntries'.
      execute_action_get_eoi_entries(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).

      "Start of changes for Additional units calculation
    WHEN 'FI_RecalInsureEmpCost'.
      execute_action_recal_insure_em(
        EXPORTING
          iv_action_name          =  iv_action_name
          it_parameter            =  it_parameter
          io_tech_request_context =  io_tech_request_context
        IMPORTING
          er_data                 = er_data
      ).
  ENDCASE.

ENDMETHOD.
