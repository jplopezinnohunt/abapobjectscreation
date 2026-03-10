  METHOD schoolsvhset_get_entity.

    DATA : lt_keys           TYPE /iwbep/t_mgw_tech_pairs,
           lv_egssl          TYPE pun_egssl,
           ls_school_details TYPE zshr_fiori_school,
           "error handling
           lr_hr_benef_exc   TYPE REF TO zcx_hr_benef_exception.


    lt_keys = io_tech_request_context->get_keys( ).
*    READ TABLE lt_keys ASSIGNING <key> INDEX 1.
    IF lines( lt_keys[] ) > 0.
      lv_egssl = lt_keys[ 1 ]-value.
         ENDIF.

      "Get school infos
      zcl_hr_fiori_education_grant=>get_school_detail(
        EXPORTING
          iv_egssl          =          lv_egssl        " EG School Identifier
*        iv_datum          =          sy-datum        " Date
        RECEIVING
          rs_school_details =      ls_school_details            " Beenfit App - School infos
      ).

      er_entity = CORRESPONDING #( ls_school_details ).
*
* DATA:
*      lt_keys       TYPE        /iwbep/t_mgw_tech_pairs,
*      lv_request_id TYPE        os_guid,
*      " error handling
*      lr_hr_exc     TYPE REF TO zcx_hr_exception.
*
*    FIELD-SYMBOLS <key> LIKE LINE OF lt_keys.
*
*    TRY.
*        lt_keys = io_tech_request_context->get_keys( ).
*
*        READ TABLE lt_keys ASSIGNING <key> INDEX 1.
*
*        lv_request_id = <key>-value.
*
*        zcl_hr_position_request=>get_instance( )->get_request(
*          EXPORTING
*            iv_request_id    = lv_request_id    " Position Request - GUID (32 characters format)
*          IMPORTING
*            es_request       = er_entity ).
*
*      CATCH zcx_hr_exception INTO lr_hr_exc.
*
*        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
*          EXPORTING
*            textid            = /iwbep/cx_mgw_busi_exception=>business_error_unlimited
*            message_unlimited = lr_hr_exc->get_text( ).
*
*    ENDTRY.

    ENDMETHOD.
