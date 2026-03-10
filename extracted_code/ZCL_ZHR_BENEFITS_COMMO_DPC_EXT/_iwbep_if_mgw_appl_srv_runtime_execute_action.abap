  METHOD /iwbep/if_mgw_appl_srv_runtime~execute_action.

    CASE iv_action_name.
      WHEN 'CheckEligibility'.
        check_eligibility( EXPORTING it_parameter = it_parameter
                           IMPORTING os_return = er_data ).

      WHEN 'CheckRequestValidity'.
        check_request_validity( EXPORTING it_parameter = it_parameter
                         IMPORTING os_return = er_data ).

      WHEN 'IsHRAorHRO'.
        is_hra_or_hro( IMPORTING os_return = er_data ).

      WHEN 'GetPersonaUrl'.
        get_persona_url( IMPORTING os_return = er_data ).

    ENDCASE.

  ENDMETHOD.
