  METHOD init_default_values_request.

    DATA : l_pnnnn      TYPE prelp, lt_pnnnn TYPE prelp_tab,
           l_beg        TYPE begda, "Note 2543474
           l_end        TYPE endda, "Note 2543474
           lt_eve_log   TYPE hrpadun_logging,ls_eve_log       TYPE pun_logging,lr_msg_list    TYPE REF TO cl_hrpa_message_list,
           lr_eve       TYPE REF TO cl_hrpadun_eve_environment,
           "Education Grant
           ls_main_eg   TYPE zthrfiori_eg_mai,
           ls_p0965     TYPE p0965,
           lt_childs    TYPE zcl_zhr_benefits_reque_mpc=>tt_childsvh,
           lo_education TYPE REF TO zcl_hr_fiori_education_grant,
           ls_ds        TYPE pun_ds,
           "Rental Subsidy
           ls_main_rs   TYPE zthrfiori_rs_mai,
           ls_p0962     TYPE p0962
           .

***********************************************************************************************
********************************* Education Grant *********************************************
***********************************************************************************************
    IF is_request_header-request_type  EQ c_request_type_eg.

      "Guid, begda , endda, objps etc...
      ls_main_eg = CORRESPONDING #( is_request_header  MAPPING famsa = subty  egyto = endda egyfr = begda ).

      CREATE OBJECT lo_education.
      lo_education->get_child_list(
         EXPORTING
           iv_pernr  =         is_request_header-creator_pernr         " Personnel Number
           iv_begda  =         sy-datum         " Start Date
           iv_endda  =         sy-datum          " End Date
         RECEIVING
           rt_childs =         lt_childs " Benefit App - type of table child
       ).

      "Adding child Infos
      IF line_exists( lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]  ) .
        ls_main_eg-fanam = lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]-fanam.
        ls_main_eg-fgbna = lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]-fgbna.
        ls_main_eg-favor = lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]-favor.
        ls_main_eg-fgbdt = lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]-fgbdt.
        ls_main_eg-fanat = lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]-fanat.
        ls_main_eg-fasex = lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]-fasex.
*        ls_main_eg-kdgbr = lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]-kdgbr.
        ls_main_eg-egage = lt_childs[ objps = is_request_header-objps famsa =  is_request_header-subty ]-egage.

      ENDIF.

*********************************************************************************************************************************

      ls_p0965  = CORRESPONDING #( is_request_header  MAPPING pernr = creator_pernr  ).
      ls_p0965 = CORRESPONDING #( BASE ( ls_p0965 ) ls_main_eg ).
      ls_p0965-infty = '0965'. ##TODO "-> in constant

      "Dependancy Status
      ls_main_eg-kdgbr = lo_education->get_dependancy_status(
                           is_request_header =  is_request_header
                           is_p0965 = ls_p0965
                         ).


      "duty station s/m
      ycl_hr_benef_common=>get_duty_station_infos(
        EXPORTING
          iv_begda =          ls_p0965-begda        " Start Date
          iv_pernr =           ls_p0965-pernr        " Personnel Number
        IMPORTING
          os_ds    =           ls_ds        " Duty Station
*      ot_ds    =                  " Duty Station
      ).
      ls_main_eg-dstat = ls_ds-dstat.
      ls_main_eg-egdds = ls_ds-egdds.

      "Natio
      SELECT SINGLE natio FROM pa0002 INTO  @ls_main_eg-natio
        WHERE pernr EQ @ls_p0965-pernr AND begda LE @ls_p0965-begda AND endda GE @ls_p0965-begda.

      "CTTYP AND CTEDT
      SELECT SINGLE *  FROM pa0016  INTO @DATA(ls_pa0016)
        WHERE pernr = @ls_p0965-pernr AND begda <= @ls_p0965-begda AND endda >= @ls_p0965-begda.
      IF sy-subrc EQ 0.
        ls_main_eg-ctedt = ls_pa0016-ctedt.
        ls_main_eg-cttyp = ls_pa0016-cttyp.
      ENDIF.

      "proration factor      LIGNE 1040 MP096520 depend on begda/endda
*       ls_main_eg-egfac =
      lo_education->get_proration_factor_elidates(
        EXPORTING
          is_pa0016 =  ls_pa0016                  " HR Master Record: Infotype 0016 (Contract Elements)
          is_p0965  =  ls_p0965                  " HR Master Record for Infotype 0965
        IMPORTING
          ev_egfac    =    ls_main_eg-egfac              " EG Proration Factor
          ev_elibegda =     ls_main_eg-elibegda             " EG : Eligible From
          ev_eliendda =      ls_main_eg-eliendda            " EG : Eligible From
      ).




      "Eligibility
      ls_main_eg-egsst = lo_education->get_eligibility(  EXPORTING is_p0965 =  ls_p0965   iv_elibegda = ls_main_eg-elibegda iv_eliendda = ls_main_eg-eliendda ).
      "eg system status ##TOCHECK

*       (
*                           is_pa0016 =  ls_pa0016
*
*                         ).

      "Currency
      SELECT SINGLE waers FROM pa0008 INTO @ls_main_eg-egcur
         WHERE pernr = @ls_p0965-pernr AND begda <= @ls_p0965-begda AND endda >= @ls_p0965-begda.

      "MAJ de la table Main
      "Insert EG main infos
      INSERT zthrfiori_eg_mai FROM ls_main_eg.
      IF sy-subrc NE 0.
*          MESSAGE e002 WITH 'ZTHR_REQ_POS' INTO sy-msgli.
**      RAISE EXCEPTION TYPE zcx_hr_preq_symsg
**        MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
**        WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
      ENDIF.

      UPDATE zthrfiori_breq SET info2 = ls_main_eg-favor child_name = ls_main_eg-favor
       WHERE guid = ls_main_eg-guid.

    ENDIF.

***********************************************************************************************
********************************* Rental Subsidy **********************************************
***********************************************************************************************
    IF is_request_header-request_type  EQ c_request_type_rs.
      ls_main_rs = CORRESPONDING #( is_request_header   ).

****************    RSDRT
      ls_main_rs-rsdrt = 	'0001'. ##TODO " a mettre dans la tvarvc

************ Duty station
      ycl_hr_benef_common=>get_duty_station_infos(
             EXPORTING
              iv_begda =          is_request_header-begda        " Start Date
               iv_pernr =           is_request_header-creator_pernr       " Personnel Number
             IMPORTING
               os_ds    =           ls_ds        " Duty Station
*      ot_ds    =                  " Duty Station
           ).

**********      RSREA  3
      DATA : l_ds1p TYPE t7unpad_ds1p.
      CALL METHOD cl_hr_t7unpad_ds1p=>read_at_date
        EXPORTING
          molga = if_hrpadun_const=>c_un_molga
          dstat = ls_ds-dstat
          date  = is_request_header-begda
        RECEIVING
          ds1p  = l_ds1p.
*
      CONSTANTS lc_schema  TYPE pun_rssch VALUE '1'.
      CONSTANTS lc_newcom  TYPE pun_rssch VALUE '2'.
      CONSTANTS lc_regulr  TYPE pun_rsrea VALUE '3'.

      IF l_ds1p-rssch = lc_schema.
*   Scheme A
        ls_main_rs-rsrea = lc_newcom.
*     Type Newcomer as default.
      ELSE.
*   it's Scheme B and mofified Scheme B's
        ls_main_rs-rsrea = lc_regulr.
      ENDIF.



************      WAERS  USD
      SELECT SINGLE btrtl, werks
        FROM pa0001
        INTO (@DATA(lv_btrtl), @DATA(lv_werks))
        WHERE pernr = @is_request_header-creator_pernr
          AND begda <= @is_request_header-begda
          AND endda >= @is_request_header-begda.

      IF sy-subrc EQ 0.


        SELECT SINGLE * FROM t001p INTO @DATA(ls_t001p) WHERE werks EQ @lv_werks AND
                                          btrtl EQ @lv_btrtl.

        IF sy-subrc EQ 0.
          CALL METHOD cl_hr_t7unpad_ds=>read
            EXPORTING
              molga = ls_t001p-molga
              dstat = lv_btrtl
            RECEIVING
              ds    = DATA(ls_tds_p).
        ENDIF.

        IF ls_tds_p IS NOT INITIAL.
          SELECT SINGLE waers  FROM t500c INTO ls_main_rs-waers
                                WHERE land1 = ls_tds_p-land1
                                  AND endda >= is_request_header-begda
                                  AND begda <= is_request_header-begda.
          IF sy-subrc EQ 0.
            ls_main_rs-waamt  =  ls_main_rs-wabfa = ls_main_rs-waers.
          ENDIF.
        ELSE.


          DATA : ls_005 TYPE t005.
          CALL FUNCTION 'T005_SINGLE_READ'
            EXPORTING
*             KZRFB      = ' '
              t005_land1 = ls_tds_p-land1
            IMPORTING
              wt005      = ls_005
            EXCEPTIONS
              not_found  = 1
*             OTHERS     = 2
            .


*       if t005-waers is initial. "changed to curha 20040809
          IF ls_005-curha IS INITIAL.
            ls_main_rs-wabfa = ls_main_rs-waamt =  ls_main_rs-waers = if_hrpadun_const=>c_rs_waers.

          ELSE.
            ls_main_rs-wabfa = ls_main_rs-waamt =  ls_main_rs-waers = ls_005-curha.

          ENDIF.
*      ENDIF.   "T500C-WAERS
*    ENDIF.   "P0962-WAERS


        ENDIF.
*      ENDIF.

      ENDIF.


************      LGART  0400

      CALL METHOD cl_hr_t7unpad_rsdr=>read
        EXPORTING
          molga = ls_t001p-molga
          rsdrt = ls_main_rs-rsdrt
        RECEIVING
          rsdr  = DATA(ls_rsdr).

      IF NOT ls_rsdr IS INITIAL.
        ls_main_rs-lgart = ls_rsdr-lgart.
        ls_main_rs-lgbfa = ls_rsdr-lgbfa.

      ENDIF.


************     DSTXT
      CALL METHOD cl_hr_t7unpad_ds_t=>read_text
        EXPORTING
          molga = if_hrpadun_const=>c_un_molga
          dstat = ls_ds-dstat
        RECEIVING
          text  = ls_main_rs-dstxt.


************     RSADT  03.01.2024
      ls_main_rs-rsadt =  COND #( WHEN ls_ds-dseod IS NOT INITIAL THEN ls_ds-dseod ELSE is_request_header-begda ).


************     RSEXD
      IF ls_main_rs-rsrea EQ '3'.
        ls_main_rs-rsexd = '99991231'.
      ENDIF.



      INSERT zthrfiori_rs_mai FROM ls_main_rs.
      IF sy-subrc NE 0.
*          MESSAGE e002 WITH 'ZTHR_REQ_POS' INTO sy-msgli.
**      RAISE EXCEPTION TYPE zcx_hr_preq_symsg
**        MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
**        WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
      ENDIF.


    ENDIF.

  ENDMETHOD.
