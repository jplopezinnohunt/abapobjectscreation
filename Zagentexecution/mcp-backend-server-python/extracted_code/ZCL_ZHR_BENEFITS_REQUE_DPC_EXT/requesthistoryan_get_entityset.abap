  METHOD requesthistoryan_get_entityset.

    DATA: "ls_filter       TYPE /iwbep/s_mgw_select_option,
      "ls_filter_range TYPE /iwbep/s_cod_select_option,
      "lr_filter_guid  TYPE RANGE OF ze_hrfiori_guidreq,
      "ls_filter_guid  LIKE LINE OF lr_filter_guid,

      lt_filters TYPE /iwbep/t_mgw_select_option,
      lt_result  TYPE zcl_zhr_benefits_reque_mpc=>tt_requesthistoryandcoments,

      lv_guid    TYPE ze_hrfiori_guidreq.


*-get filter
    lt_filters = io_tech_request_context->get_filter( )->get_filter_select_options( ).

*-get filter for Request Flow
    IF line_exists( lt_filters[ property = 'GUID' ] ).
      lv_guid =   lt_filters[ property = 'GUID' ]-select_options[ 1 ]-low .
    ENDIF.

    IF lv_guid IS NOT INITIAL.

      zcl_hr_fiori_request=>get_instance( )->get_timeline(
      EXPORTING iv_request_guid = lv_guid
               IMPORTING
                 et_result       = lt_result ).

      et_entityset = CORRESPONDING #( lt_result ).

    ENDIF.

  ENDMETHOD.
