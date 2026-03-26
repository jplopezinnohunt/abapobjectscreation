  METHOD update_claim_list.
    DATA : lt_insert_claims TYPE TABLE OF  zthr_eg_claim,
           lv_tabix         TYPE n LENGTH 3.
    DATA: lv_dummy_famount TYPE t7unpad_egexpmgt-examt.
    DATA: lv_dummy_tamount TYPE t7unpad_egexpmgt-examt.

    "get egcur

    SELECT SINGLE egcur FROM zthrfiori_eg_mai INTO @DATA(lv_hwae) WHERE guid EQ @iv_guid.
    "Delete
    DELETE FROM zthr_eg_claim WHERE request_guid EQ iv_guid.

    IF lines( it_claims[] ) > 0.
      lt_insert_claims = CORRESPONDING #( it_claims ).

      "Exart
      SELECT * FROM t7unpad_egcos INTO TABLE @DATA(lt_egcos) WHERE molga EQ 'UN' AND exmappl EQ 'NPO_EG' AND endda GE @sy-datum .

      "Lines with empty guid are the new ones, we create guid for eache one, complete teh other fields, then delete all and recreate
      LOOP AT lt_insert_claims ASSIGNING FIELD-SYMBOL(<lfs_clm>) .
*        WHERE

        lv_tabix = sy-tabix.
        <lfs_clm>-exlnr = lv_tabix.

        IF <lfs_clm>-guid IS INITIAL.
          "create guid
          TRY.
              CALL METHOD cl_system_uuid=>create_uuid_x16_static
                RECEIVING
                  uuid = <lfs_clm>-guid.
            CATCH cx_uuid_error.
              RAISE EXCEPTION TYPE cx_os_internal_error.
          ENDTRY.

          "Request guid
          <lfs_clm>-request_guid = iv_guid.

          ##TODO "-> complete technical fields
          <lfs_clm>-paycurr = <lfs_clm>-waers.
          "get rate change

          IF lv_hwae  NE <lfs_clm>-waers
            .
            lv_dummy_famount = 1.
            CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
              EXPORTING
                date             = sy-datum
                foreign_amount   = lv_dummy_famount
                foreign_currency = <lfs_clm>-waers
                local_currency   = lv_hwae
                rate             = 0
                type_of_rate     = 'M'
              IMPORTING
                exchange_rate    = <lfs_clm>-kursb
                foreign_factor   = <lfs_clm>-ffact
                local_amount     = lv_dummy_tamount
                local_factor     = <lfs_clm>-tfact
              EXCEPTIONS
                no_rate_found    = 04
                overflow         = 08.

          ELSE.
            <lfs_clm>-ffact = <lfs_clm>-tfact = <lfs_clm>-kursb = 1.
          ENDIF.
          "Waers = paycurr as we disable Waers
*          <lfs_adv>-advflag = abap_true.

*          EXART
          IF line_exists( lt_egcos[ excos = <lfs_clm>-excos ] ).
            <lfs_clm>-exart = lt_egcos[ excos = <lfs_clm>-excos ]-exart.

          ENDIF.

        ENDIF.


      ENDLOOP.
      "
      MODIFY  zthr_eg_claim FROM TABLE lt_insert_claims.
      IF sy-subrc NE 0.
      ELSE.

        ##TODO "handle error
      ENDIF.
    ENDIF.

  ENDMETHOD.
