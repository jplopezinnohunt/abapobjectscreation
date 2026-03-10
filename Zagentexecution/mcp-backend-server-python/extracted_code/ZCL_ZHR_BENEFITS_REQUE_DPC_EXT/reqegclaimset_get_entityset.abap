  METHOD reqegclaimset_get_entityset.

    DATA : lo_education TYPE REF TO zcl_hr_fiori_education_grant,
           lt_filters   TYPE /iwbep/t_mgw_select_option,
           lt_result    TYPE zcl_zhr_benefits_reque_mpc=>tt_requesthistoryandcoments,
           lv_guid      TYPE ze_hrfiori_guidreq.

*-get filter
    lt_filters = io_tech_request_context->get_filter( )->get_filter_select_options( ).

*-get filter for Request Flow
    IF line_exists( lt_filters[ property = 'GUID' ] ).
      lv_guid =   lt_filters[ property = 'GUID' ]-select_options[ 1 ]-low .
    ENDIF.

    "Get advances
    CREATE OBJECT lo_education.
    lo_education->get_claims_list(
              EXPORTING
                iv_guid     =     lv_guid             " Benefits request - GUID Request
              IMPORTING
                et_claims = et_entityset
            ).
  ENDMETHOD.
