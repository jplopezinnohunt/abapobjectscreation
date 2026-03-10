  METHOD /iwbep/if_mgw_appl_srv_runtime~execute_action.

    DATA: ls_actionreturn TYPE zcl_zhr_benefits_req_a_mpc_ext=>actionreturn,
          lo_education    TYPE REF TO zcl_hr_fiori_education_grant,
          lv_guid         TYPE ze_hrfiori_guidreq.

    CASE iv_action_name.
      WHEN 'addClaimForAdvance'.

        DATA(lt_params) = io_tech_request_context->get_parameters( ).
        IF line_exists( lt_params[ name = 'GUID' ] ).
          lv_guid =  lt_params[ name = 'GUID' ]-value  .
        ENDIF.

        IF lv_guid IS NOT INITIAL.
          CREATE OBJECT lo_education.

          lo_education->add_claim_advance_status(
            EXPORTING
              iv_guid   =   lv_guid               " Benefits request - GUID Request
            IMPORTING
              os_return =  ls_actionreturn
          ).
*

          copy_data_to_ref( EXPORTING is_data = ls_actionreturn
                             CHANGING cr_data  = er_data ).


        ENDIF.

*        check_eligibility( EXPORTING it_parameter = it_parameter
*                           IMPORTING os_return = er_data ).

    ENDCASE.
  ENDMETHOD.
