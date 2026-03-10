METHOD dependentset_get_entityset.
  DATA:  ls_filter_range TYPE /iwbep/s_cod_select_option,
         ls_filter       TYPE /iwbep/s_mgw_select_option.

  DATA : lt_health_offer      TYPE TABLE OF rpben_oa,
         lt_insure_offer      TYPE TABLE OF rpben_ob,
         lt_saving_offer      TYPE TABLE OF rpben_oc,
         lt_spenda_offer      TYPE TABLE OF rpben_od,
         lt_miscel_offer      TYPE TABLE OF rpben_oe,
         lt_stockp_offer      TYPE TABLE OF rpben_of,
         lt_credit_offer      TYPE TABLE OF rpben_o1,
         lt_depend_offer      TYPE TABLE OF rpbenodp,
         lt_benefi_offer      TYPE TABLE OF rpbenobf,
         lt_invest_offer      TYPE TABLE OF rpbenoiv,
         lt_depend_displ      TYPE TABLE OF rpbenddp,
         lt_error_table       TYPE hrben00err_ess,
         lt_error_table_temp  TYPE hrben00err_ess.

  DATA : ls_event_desc            TYPE rpbenevent,
         ls_health_offer          TYPE rpben_oa,
         ls_insure_offer          TYPE rpben_ob,
         ls_saving_offer          TYPE rpben_oc,
         ls_spenda_offer          TYPE rpben_od,
         ls_miscel_offer          TYPE rpben_oe,
         ls_stockp_offer          TYPE rpben_of,
         ls_credit_offer          TYPE rpben_o1,
         ls_depend_offer          TYPE rpbenodp,
         ls_benefi_offer          TYPE rpbenobf,
         ls_invest_offer          TYPE rpbenoiv,
         ls_t74hr                 TYPE t74hr,
         ls_costcred_trans_s      TYPE rpben_costcred_trans,
         ls_contrib_trans_s       TYPE rpben_contrib_trans,
         ls_processed_plan        TYPE rpben_gen_plan_info,
         ls_depend_displ          TYPE rpbenddp,
         ls_ee_benefit_data       TYPE rpbeneedat,
         ls_key_tab               TYPE /iwbep/s_mgw_name_value_pair,
         ls_entity_temp           TYPE cl_hcmfab_ben_enrollme_mpc=>ts_dependent,
         ls_entity                TYPE cl_hcmfab_ben_enrollme_mpc=>ts_dependent.

  DATA : lv_subrc                TYPE sysubrc,
         lv_event                TYPE ben_event,
         lv_etype                TYPE ben_enrtyp,
         lv_datum                TYPE sydatum,
         lv_bopti                TYPE ben_option,
         lv_levl1	               TYPE	ben_level1,
         lv_depcv	               TYPE	ben_depcov,
         lx_exception            TYPE REF TO cx_static_check,
         lx_badi_error           TYPE REF TO cx_hcmfab_benefits_enrollment,
         lv_clear_depben         TYPE boolean VALUE ' '.

 DATA : lt_enroll_event           TYPE hrben00enrollmentreason,
        ls_selected_enroll_reason TYPE rpbenenrollmentreason.

 FIELD-SYMBOLS: <fs_sprps> type sprps.
  lv_datum = sy-datum.

* get the filter data
   loop at it_filter_select_options into ls_filter.
  READ TABLE ls_filter-select_options INTO ls_filter_range INDEX 1.
  IF sy-subrc = 0 AND
     ls_filter_range-sign EQ 'I' AND ls_filter_range-option EQ 'EQ'.
    CASE ls_filter-property.
      WHEN 'EmployeeNumber'.
        ls_processed_plan-pernr = ls_filter_range-low.
      WHEN 'Event'.
        lv_event = ls_filter_range-low.
      WHEN 'EventType'.
        lv_etype = ls_filter_range-low.
      WHEN 'BenefitArea'.
        ls_processed_plan-barea = ls_filter_range-low.
      WHEN 'BenefitCategory'.
        ls_processed_plan-bpcat = ls_filter_range-low.
      WHEN 'PlanType'.
        ls_processed_plan-pltyp = ls_filter_range-low.
      WHEN 'Plan'.
        ls_processed_plan-bplan = ls_filter_range-low.
      WHEN 'BeginDate'.
        ls_processed_plan-begda = ls_filter_range-low.
      WHEN 'EndDate'.
        ls_processed_plan-endda = ls_filter_range-low.
      WHEN 'LockIndicator'.
        ls_processed_plan-sprps = ls_filter_range-low.
      WHEN 'HealthPlanOption'.
        lv_bopti = ls_filter_range-low.
      WHEN 'DepenCoverage'.
        lv_depcv = ls_filter_range-low.
      WHEN 'MiscOption'.
        lv_levl1 = ls_filter_range-low.
    ENDCASE.
  ENDIF.
ENDLOOP.
TRY.
    "check whether PERNR actually belongs to the logon user
    go_employee_api->do_employeenumber_validation( iv_pernr          = ls_processed_plan-pernr
                                                   iv_application_id = gc_application_id-mybenefitsenrollment ).
    CALL FUNCTION 'HR_BEN_ESS_RFC_ENRO_REASONS'
        EXPORTING
          pernr              = ls_processed_plan-pernr
          datum              = sy-datum
        IMPORTING
          enrollment_reasons = lt_enroll_event
          error_table        = lt_error_table
          subrc              = lv_subrc.
      "Note 2945606
      READ TABLE lt_enroll_event INTO ls_selected_enroll_reason WITH KEY  event = lv_event
                                                                          enrty = lv_etype.
      IF sy-subrc = 0.
        ls_event_desc-begda = ls_selected_enroll_reason-begda.
        ls_event_desc-endda = ls_selected_enroll_reason-endda.
      ENDIF.
      "Note 2945606

    ls_event_desc-barea = ls_processed_plan-barea.
    ls_event_desc-pernr = ls_processed_plan-pernr.
    ls_event_desc-event = lv_event.
*    ls_event_desc-begda = ls_processed_plan-begda."Note 2945606
*    ls_event_desc-endda = ls_processed_plan-endda."Note 2945606
    ls_ee_benefit_data-pernr = ls_processed_plan-pernr.
    ls_ee_benefit_data-barea = ls_processed_plan-barea.

    CLEAR :lt_health_offer,lt_insure_offer,lt_saving_offer,lt_spenda_offer,lt_miscel_offer,
           lt_stockp_offer,lt_credit_offer,lt_depend_offer,lt_benefi_offer,lt_invest_offer.
    CALL METHOD me->hr_get_offer
      EXPORTING
        iv_pernr         = ls_processed_plan-pernr
        iv_datum         = sy-datum
        iv_ben_area      = ls_processed_plan-barea
        iv_event         = lv_event
        iv_event_type    = lv_etype
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


    CASE ls_processed_plan-bpcat.
*PROCESSING OF HEALTH PLANS*
      WHEN c_health_plan.
        READ TABLE lt_health_offer INTO ls_health_offer
          WITH KEY barea = ls_processed_plan-barea
                   pltyp = ls_processed_plan-pltyp
                   bplan = ls_processed_plan-bplan
                   bopti = lv_bopti
                   depcv = lv_depcv
                   begda = ls_processed_plan-begda
                   endda = ls_processed_plan-endda
                   sprps = ls_processed_plan-sprps.
      IF ls_health_offer-enrolled = c_true.
        CALL FUNCTION 'HR_BEN_READ_DEPENDENTS'
        EXPORTING
          ee_benefit_data = ls_ee_benefit_data
          bpcat           = c_health_plan
          begda           = ls_processed_plan-begda
          endda           = ls_processed_plan-endda
          reaction        = c_reaction_n
          logicview       = c_false
        IMPORTING
          subrc           = lv_subrc
        TABLES
          existing_dep    = lt_depend_displ
          error_table     = lt_error_table.
        LOOP AT lt_depend_displ INTO ls_depend_displ WHERE barea EQ ls_processed_plan-barea AND
                                                           pltyp EQ ls_processed_plan-pltyp AND
                                                           bplan EQ ls_processed_plan-bplan AND
                                                           begda LE ls_processed_plan-begda AND
                                                           endda GE ls_processed_plan-endda.      "Note 2806541
          ASSIGN COMPONENT 'SPRPS' OF STRUCTURE ls_depend_displ TO <fs_sprps>.
          IF <fs_sprps> IS ASSIGNED AND <fs_sprps> = ls_processed_plan-sprps.
            CLEAR:ls_t74hr,lv_subrc,ls_entity.
            MOVE-CORRESPONDING ls_processed_plan TO ls_entity.
            MOVE-CORRESPONDING ls_depend_displ TO ls_entity.
            ls_entity-selected = c_true.
            PERFORM re74hr IN PROGRAM sapfben0 TABLES lt_error_table_temp
            USING ls_processed_plan-barea
                  lv_depcv
                  ls_depend_displ-dep_type
                  c_reaction_n
            CHANGING ls_t74hr
                     lv_subrc.
            IF lv_subrc NE 0.
              ls_entity-not_elig = abap_true.
              ls_entity-inel_reas = 'Ineligible: Not valid for selected coverage level'(t12).
            ENDIF.
            ls_entity-enrty = lv_etype.
            ls_entity-event = lv_event.
            ls_entity-depcv = lv_depcv.
            ls_entity-bopti = lv_bopti.
            me->enrich_dependent( CHANGING dependententity = ls_entity ).
            APPEND ls_entity TO et_entityset.
          ENDIF.
        ENDLOOP.
      ENDIF.
      LOOP AT lt_depend_offer INTO ls_depend_offer WHERE barea = ls_processed_plan-barea AND
                                                         pltyp = ls_processed_plan-pltyp AND
                                                         bplan = ls_processed_plan-bplan AND
                                                         begda = ls_processed_plan-begda AND
                                                         endda = ls_processed_plan-endda.
          CLEAR:ls_entity,ls_entity_temp,ls_depend_offer-selected.
          IF ls_health_offer-enrolled = c_true.
          READ TABLE et_entityset INTO ls_entity_temp WITH KEY dep_type = ls_depend_offer-dep_type dep_id = ls_depend_offer-dep_id.
          IF sy-subrc EQ 0.
            CONTINUE.
          ENDIF.
          ENDIF.
          MOVE-CORRESPONDING ls_processed_plan TO ls_entity.
          MOVE-CORRESPONDING ls_depend_offer TO ls_entity.
          PERFORM re74hr IN PROGRAM sapfben0 TABLES lt_error_table_temp
                                   USING ls_processed_plan-barea
                                         lv_depcv
                                         ls_depend_offer-dep_type
                                         c_reaction_n
                                   CHANGING ls_t74hr
                                            lv_subrc.
          IF lv_subrc NE 0.
            IF ls_entity-not_elig NE abap_true.
              ls_entity-not_elig = abap_true.
              ls_entity-inel_reas = 'Ineligible: Not valid for selected coverage level'(t12).
            ENDIF.
          ENDIF.
          ls_entity-enrty = lv_etype.
          ls_entity-event = lv_event.
          ls_entity-depcv = lv_depcv.
          ls_entity-bopti = lv_bopti.
          me->enrich_dependent( CHANGING dependententity = ls_entity ).
          APPEND ls_entity TO et_entityset.
      ENDLOOP.

*PROCESSING OF MISCELLANEOUS PLANS*
      WHEN c_miscellaneous_plan.

        READ TABLE lt_miscel_offer INTO ls_miscel_offer
          WITH KEY barea = ls_processed_plan-barea
                   pltyp = ls_processed_plan-pltyp
                   bplan = ls_processed_plan-bplan
                   levl1 = lv_levl1
                   begda = ls_processed_plan-begda
                   endda = ls_processed_plan-endda.

        LOOP AT lt_depend_offer INTO ls_depend_offer WHERE barea EQ ls_processed_plan-barea AND
                                                           pltyp EQ ls_processed_plan-pltyp AND
                                                           bplan EQ ls_processed_plan-bplan AND
                                                           begda LE ls_processed_plan-begda AND
                                                           endda GE ls_processed_plan-endda.
          CLEAR ls_entity.
          IF ls_miscel_offer-enrolled NE abap_true.
            CLEAR ls_depend_offer-selected.
          ENDIF.
          MOVE-CORRESPONDING ls_processed_plan TO ls_entity.
          MOVE-CORRESPONDING ls_depend_offer TO ls_entity.
          ls_entity-enrty = lv_etype.
          ls_entity-event = lv_event.
          ls_entity-levl1 = lv_levl1.
          me->enrich_dependent( CHANGING dependententity = ls_entity ).
          APPEND ls_entity TO et_entityset.
        ENDLOOP.

    ENDCASE.
    SORT et_entityset by pltyp bplan bopti depcv dep_type dep_id.

    IF lt_error_table IS NOT INITIAL.
      me->raise_exceptions(
      EXPORTING
        it_messages = lt_error_table
         iv_entity_name = iv_entity_name
       ).
    ENDIF.

  CATCH cx_hcmfab_common INTO lx_exception.
    cl_hcmfab_utilities=>raise_gateway_error(
        is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
        iv_entity   = io_tech_request_context->get_entity_type_name( )
    ).

  CATCH cx_hcmfab_benefits_enrollment INTO lx_badi_error.
    cl_hcmfab_utilities=>raise_gateway_error(
        is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_badi_error )
        iv_entity   = io_tech_request_context->get_entity_type_name( )
    ).

ENDTRY.
ENDMETHOD.
