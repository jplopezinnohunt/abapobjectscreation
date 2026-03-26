  METHOD add_claim_advance_status.

    DATA : lt_claims TYPE TABLE OF zthr_eg_claim,
           lv_info1  TYPE zthrfiori_breq-info1.


      lv_info1 = |Advance with Claim|.

    UPDATE zthrfiori_breq SET isclaim = @abap_true , info1 = @lv_info1
               WHERE guid EQ @iv_guid.
    os_return-returncode = sy-subrc.
    IF sy-subrc EQ 0.

      "Move advances to claim
      SELECT * FROM zthr_eg_advance INTO TABLE @DATA(lt_advances_tobe_claimed) WHERE request_guid  EQ @iv_guid.
*      os_return-returncode = sy-subrc.
      IF sy-subrc EQ 0.
        lt_claims = CORRESPONDING #( lt_advances_tobe_claimed ).

        MODIFY  zthr_eg_claim FROM TABLE lt_claims.
        os_return-returncode = sy-subrc.
      ENDIF.
*    DELETE FROM zthr_eg_advance WHERE request_guid EQ iv_guid.
*
*    IF lines( it_advances[] ) > 0.
*      lt_insert_advances = CORRESPONDING #( it_advances ).
*
*      MODIFY  zthr_eg_advance FROM TABLE lt_insert_advances.


    ENDIF.

  ENDMETHOD.
