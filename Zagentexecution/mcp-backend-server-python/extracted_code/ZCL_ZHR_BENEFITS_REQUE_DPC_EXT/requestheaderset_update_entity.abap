  METHOD requestheaderset_update_entity.
*    " error handling
*    DATA :     lr_hr_benef_exc TYPE REF TO zcx_hr_benef_exception.
*    io_data_provider->read_entry_data( IMPORTING es_data = er_entity ).
*
*    TRY.
*        zcl_hr_fiori_request=>get_instance( )->update_request( er_entity ).
*
*      CATCH zcx_hr_benef_exception lr_hr_benef_exc.
*
*        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
*          EXPORTING
*            textid            = /iwbep/cx_mgw_busi_exception=>business_error_unlimited
*            message_unlimited = lr_hr_exc->get_text( ).
*
*    ENDTRY.
  ENDMETHOD.
