  METHOD requestheaderset_get_entity.

    DATA:
      lt_keys      TYPE        /iwbep/t_mgw_tech_pairs,
      lv_guid      TYPE ze_hrfiori_guidreq,
      ls_reqheader TYPE zthrfiori_breq,
      " error handling
      lr_hr_exc    TYPE REF TO zcx_hr_benef_exception.

    FIELD-SYMBOLS <key> LIKE LINE OF lt_keys.

    TRY.
        lt_keys = io_tech_request_context->get_keys( ).

        READ TABLE lt_keys ASSIGNING <key> INDEX 1.

        lv_guid = <key>-value.

        SELECT SINGLE * FROM zthrfiori_breq
           INTO CORRESPONDING FIELDS OF @er_entity
           WHERE guid = @lv_guid.

      CATCH zcx_hr_benef_exception INTO lr_hr_exc.

        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid            = /iwbep/cx_mgw_busi_exception=>business_error_unlimited
            message_unlimited = lr_hr_exc->get_text( ).

    ENDTRY.

  ENDMETHOD.
