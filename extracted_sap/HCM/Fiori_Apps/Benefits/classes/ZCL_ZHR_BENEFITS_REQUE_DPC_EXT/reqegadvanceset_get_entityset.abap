METHOD reqegadvanceset_get_entityset.
*DATA: lt_entityset TYPE STANDARD TABLE OF zcl_zhr_benefits_reque_mpc=>ts_reqegadvance WITH EMPTY KEY,
*        ls_entity    TYPE zcl_zhr_benefits_reque_mpc=>ts_reqegadvance,
*        lv_guid      TYPE sysuuid_x.
* " === Données TEST liées au parent (remplace par ton SELECT) ===
*    CLEAR ls_entity.
*    ls_entity-Guid  = lv_guid.     " Renseigne bien toutes les parties de clé de l'enfant si nécessaire
*    ls_entity-Waers = 'USD'.
*    ls_entity-Exdat = sy-datum.
*    ls_entity-Excos = 'TEST'.
*    ls_entity-Examt = 123.
*    APPEND ls_entity TO lt_entityset.

  DATA : lo_education    TYPE REF TO zcl_hr_fiori_education_grant.
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

  "Get advances
  CREATE OBJECT lo_education.
  lo_education->get_advances_list(
            EXPORTING
              iv_guid     =     lv_guid             " Benefits request - GUID Request
            IMPORTING
              et_advances = et_entityset
          ).
ENDMETHOD.
