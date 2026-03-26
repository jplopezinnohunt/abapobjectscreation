  METHOD requestheaderset_delete_entity.
    DATA:
      ls_converted_keys TYPE        zcl_zhr_benefits_reque_mpc=>ts_requestheader,
      lv_request_guid   TYPE        os_guid,
      lr_hr_exc         TYPE REF TO zcx_hr_benef_exception.

    TRY.
        io_tech_request_context->get_converted_keys(
          IMPORTING
            es_key_values  = ls_converted_keys ).

        lv_request_guid = ls_converted_keys-guid. "casting

        zcl_hr_fiori_request=>get_instance( )->cancel_request( lv_request_guid ).

      CATCH zcx_hr_benef_exception INTO lr_hr_exc.

        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid            = /iwbep/cx_mgw_busi_exception=>business_error_unlimited
            message_unlimited = lr_hr_exc->get_text( ).

    ENDTRY.
  ENDMETHOD.
