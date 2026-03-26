  METHOD get_rs_request_detail.

*    SELECT SINGLE * FROM zthrfiori_eg_mai  INTO @ls_eg_main WHERE guid EQ @lv_request_id.
    SELECT SINGLE * FROM zthrfiori_rs_mai  INTO CORRESPONDING FIELDS OF @rs_detail_rs WHERE guid EQ @iv_guid.
    IF sy-subrc EQ 0.

    ENDIF.
  ENDMETHOD.
