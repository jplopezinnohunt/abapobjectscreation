  METHOD genericvhset_get_entityset.

    DATA:
      " error handling
      lr_hr_benef_exc TYPE REF TO zcx_hr_benef_exception,
      lt_filters      TYPE /iwbep/t_mgw_select_option,
      lv_method       TYPE seocpdname,
      lv_request_type TYPE ze_hrfiori_requesttype.

*-get filter
    lt_filters = io_tech_request_context->get_filter( )->get_filter_select_options( ).

*-get filter for Request Flow
    IF line_exists( lt_filters[ property = 'METHOD' ] ).
      lv_method =   lt_filters[ property = 'METHOD' ]-select_options[ 1 ]-low .
    ENDIF.

    IF line_exists( lt_filters[ property = 'REQUEST_TYPE' ] ).
      lv_request_type =   lt_filters[ property = 'REQUEST_TYPE' ]-select_options[ 1 ]-low .
    ENDIF.


    ##TODO " gerer les exceptions et déclarer dans les méthodes à catcher!
    ##TODO " whitelist des méthodes? ou aps besoin puisque que lecture?
    TRY .
        IF lv_request_type EQ zcl_hr_fiori_request=>c_request_type_eg.
          CALL METHOD zcl_hr_fiori_education_grant=>(lv_method)
            IMPORTING
              ot_list = et_entityset.    "ot_list doit être le nom exact du paramètre out
        ENDIF.

        IF lv_request_type EQ zcl_hr_fiori_request=>c_request_type_rs.
          CALL METHOD zcl_hr_fiori_rental=>(lv_method)
            IMPORTING
              ot_list = et_entityset.    "ot_list doit être le nom exact du paramètre out
        ENDIF.


*        "Formattage des VH avec key = ''
*        LOOP AT et_entityset ASSIGNING FIELD-SYMBOL(<ls_es>).
*          <ls_es>-method = lv_method.
*          IF <ls_es>-id EQ ''.
*            <ls_es>-id = '-'.
*          ENDIF.
*        ENDLOOP.

      CATCH zcx_hr_benef_exception INTO lr_hr_benef_exc.

        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid            = /iwbep/cx_mgw_busi_exception=>business_error_unlimited
            message_unlimited = lr_hr_benef_exc->get_text( ).

    ENDTRY.

  ENDMETHOD.


*METHOD genericvhset_get_entityset.
*
*  DATA: lr_hr_benef_exc TYPE REF TO zcx_hr_benef_exception,
*        lt_filters      TYPE /iwbep/t_mgw_select_option,
*        lv_method       TYPE seocpdname.
*
*  lt_filters = io_tech_request_context->get_filter( )->get_filter_select_options( ).
*  IF line_exists( lt_filters[ property = 'METHOD' ] ).
*    lv_method = lt_filters[ property = 'METHOD' ]-select_options[ 1 ]-low.
*  ENDIF.
*  TRANSLATE lv_method TO UPPER CASE.
*
*  " 1) Prépare un réceptacle générique pour le résultat EXPORTING (OT_LIST)
*  DATA lr_src TYPE REF TO data.
*  CREATE DATA lr_src TYPE any  .              " <-- table générique
*  FIELD-SYMBOLS <lt_src> TYPE ANY TABLE.
*  ASSIGN lr_src->* TO <lt_src>.
*
*  TRY.
*      " 2) Appel dynamique → on bind l’EXPORTING vers <lt_src>
*      CALL METHOD zcl_hr_fiori_education_grant=>(lv_method)
*        IMPORTING
*          ot_list = <lt_src>.                     " ot_list → table générique
*
*    CATCH zcx_hr_benef_exception INTO lr_hr_benef_exc.
*      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
*        EXPORTING textid            = /iwbep/cx_mgw_busi_exception=>business_error_unlimited
*                  message_unlimited = lr_hr_benef_exc->get_text( ).
*    CATCH cx_sy_dyn_call_illegal_method cx_sy_dyn_call_param_not_found INTO DATA(lx_dyn).
*      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
*        EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
*                  message = lx_dyn->get_text( ).
*  ENDTRY.
*
*  " 3) Mapping propre → <lt_src> (ID/TXT plus longs) vers et_entityset (ID/TXT plus courts)
*  CLEAR et_entityset.
*  DATA ls_dst TYPE LINE OF et_entityset.
*
*  FIELD-SYMBOLS <ls_src> TYPE any.
*  FIELD-SYMBOLS <id>  TYPE any.
*  FIELD-SYMBOLS <txt> TYPE any.
*
*  LOOP AT <lt_src> ASSIGNING <ls_src>.
*    CLEAR ls_dst.
*
*    " On prend les composants par nom (mêmes noms, longueurs différentes)
*    ASSIGN COMPONENT 'ID'  OF STRUCTURE <ls_src> TO <id>.
*    ASSIGN COMPONENT 'TXT' OF STRUCTURE <ls_src> TO <txt>.
*
*    IF <id>  IS ASSIGNED. ls_dst-id  = <id>.  ENDIF.  " conversion & troncation automatiques
*    IF <txt> IS ASSIGNED. ls_dst-txt = <txt>. ENDIF.
*
*    APPEND ls_dst TO et_entityset.
*  ENDLOOP.
*
*ENDMETHOD.
