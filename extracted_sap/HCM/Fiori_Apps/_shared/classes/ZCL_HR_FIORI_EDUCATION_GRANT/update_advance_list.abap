  METHOD update_advance_list.

    DATA : lt_insert_advances TYPE TABLE OF  zthr_eg_advance,
           lv_tabix           TYPE n LENGTH 3.
    DATA: lv_dummy_famount TYPE t7unpad_egexpmgt-examt.
    DATA: lv_dummy_tamount TYPE t7unpad_egexpmgt-examt.


    "get egcur

    SELECT SINGLE egcur FROM zthrfiori_eg_mai INTO @DATA(lv_hwae) WHERE guid EQ @iv_guid.

    "Delete
    DELETE FROM zthr_eg_advance WHERE request_guid EQ iv_guid.

    IF lines( it_advances[] ) > 0.
      lt_insert_advances = CORRESPONDING #( it_advances ).

      "Exart
      SELECT * FROM t7unpad_egcos INTO TABLE @DATA(lt_egcos) WHERE molga EQ 'UN' AND exmappl EQ 'NPO_EG' AND endda GE @sy-datum .

      "Lines with empty guid are the new ones, we create guid for eache one, complete teh other fields, then delete all and recreate
      LOOP AT lt_insert_advances ASSIGNING FIELD-SYMBOL(<lfs_adv>) .
*        WHERE

        lv_tabix = sy-tabix.
        <lfs_adv>-exlnr = lv_tabix.

        IF <lfs_adv>-guid IS INITIAL.
          "create guid
          TRY.
              CALL METHOD cl_system_uuid=>create_uuid_x16_static
                RECEIVING
                  uuid = <lfs_adv>-guid.
            CATCH cx_uuid_error.
              RAISE EXCEPTION TYPE cx_os_internal_error.
          ENDTRY.

          "Request guid
          <lfs_adv>-request_guid = iv_guid.

          ##TODO "-> complete technical fields
          <lfs_adv>-paycurr = <lfs_adv>-waers.

          IF lv_hwae  NE <lfs_adv>-waers
  .
            lv_dummy_famount = 1.
            CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
              EXPORTING
                date             = sy-datum
                foreign_amount   = lv_dummy_famount
                foreign_currency = <lfs_adv>-waers
                local_currency   = lv_hwae
                rate             = 0
                type_of_rate     = 'M'
              IMPORTING
                exchange_rate    = <lfs_adv>-kursb
                foreign_factor   = <lfs_adv>-ffact
                local_amount     = lv_dummy_tamount
                local_factor     = <lfs_adv>-tfact
              EXCEPTIONS
                no_rate_found    = 04
                overflow         = 08.

          ELSE.
            <lfs_adv>-ffact = <lfs_adv>-tfact = <lfs_adv>-kursb = 1.
          ENDIF.


*          <lfs_adv>-ffact = <lfs_adv>-tfact = <lfs_adv>-kursb = 1. "Waers = paycurr as we disable Waers
          <lfs_adv>-advflag = abap_true.

*          EXART
          IF line_exists( lt_egcos[ excos = <lfs_adv>-excos ] ).
            <lfs_adv>-exart = lt_egcos[ excos = <lfs_adv>-excos ]-exart.

          ENDIF.
*          <lfs_adv>-exdat = sy-datum.


        ENDIF.


      ENDLOOP.
      "
      MODIFY  zthr_eg_advance FROM TABLE lt_insert_advances.
      IF sy-subrc NE 0.
      ELSE.

        ##TODO "handle error
      ENDIF.
    ENDIF.



  ENDMETHOD.
