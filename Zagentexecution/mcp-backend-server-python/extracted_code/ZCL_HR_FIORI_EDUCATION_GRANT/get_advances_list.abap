  METHOD get_advances_list.

    "Get advance
    SELECT * FROM  zthr_eg_advance INTO CORRESPONDING FIELDS OF table et_advances WHERE request_guid EQ iv_guid.

  ENDMETHOD.
