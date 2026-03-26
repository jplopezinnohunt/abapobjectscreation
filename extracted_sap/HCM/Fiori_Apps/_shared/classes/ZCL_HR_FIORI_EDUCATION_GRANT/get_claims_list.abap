  METHOD get_claims_list.

    DATA : lt_advances TYPE TABLE OF zthr_eg_advance.

*    "Get advance
*    SELECT * FROM  zthr_eg_advance INTO CORRESPONDING FIELDS OF TABLE lt_advances WHERE request_guid EQ iv_guid.
    "Get claims
    SELECT * FROM  zthr_eg_claim INTO CORRESPONDING FIELDS OF TABLE et_claims WHERE request_guid EQ iv_guid.
*
*    "Add advances if exists
*    LOOP AT lt_advances ASSIGNING FIELD-SYMBOL(<lfs_advance>).
*
*      APPEND INITIAL LINE TO et_claims ASSIGNING FIELD-SYMBOL(<lfs_claim_for_advance>).
*
*      <lfs_claim_for_advance> = CORRESPONDING #( <lfs_advance> ).
*
*    ENDLOOP.

  ENDMETHOD.
