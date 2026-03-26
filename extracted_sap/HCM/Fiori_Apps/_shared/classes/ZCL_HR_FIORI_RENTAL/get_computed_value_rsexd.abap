  METHOD get_computed_value_rsexd.

    DATA: lv_pernr        TYPE persno,
          lv_userid       TYPE sysid,
          lv_years        TYPE p,
          lv_enabled      TYPE boole_d,
          lv_adjust_rsadt TYPE pun_rsadt,
          lv_sflag_badi   TYPE flag,
          ls_rsrr         TYPE t7unpad_rsrr,
          ls_lwop2        TYPE pun_lwop,
          lt_rsrr         TYPE STANDARD TABLE OF t7unpad_rsrr,
          lt_p2001        TYPE p2001_tab ##NEEDED,
          lt_lwop1        TYPE hrpayun_lwop ##NEEDED,
          lt_lwop2        TYPE hrpayun_lwop,
          lo_hrpayun_lwop TYPE REF TO hrpayun_lwop_periods.


*   Get PERNR of connected user if needed
    IF iv_pernr IS INITIAL.
      MOVE sy-uname TO lv_userid.
      SELECT SINGLE pernr INTO lv_pernr
        FROM pa0105
          WHERE subty = '0001'
            AND endda >= sy-datum
            AND begda <= sy-datum
            AND usrid = lv_userid ##WARN_OK.
    ELSE.
      lv_pernr = iv_pernr.
    ENDIF.


    SELECT * INTO TABLE lt_rsrr
      FROM t7unpad_rsrr
        WHERE molga  EQ 'UN'
          AND rsrea  EQ '2' .
    IF sy-subrc = 0.
      SORT lt_rsrr BY rsycn DESCENDING.
      READ TABLE lt_rsrr INTO ls_rsrr INDEX 1.
      lv_years = ls_rsrr-rsycn.

      IF iv_rsrea = c_regulr.
        ov_rsexd = c_31129999.

      ELSE.
        CALL METHOD cl_hrun_attributes=>get_attribute
          EXPORTING
            name  = 'RS_ENABLE_EXTEND_RSEXD'
          RECEIVING
            value = lv_enabled.

        IF iv_rsdsa <> 'X' AND lv_enabled = 'X'.
          lv_adjust_rsadt = iv_rsadt.

          CALL FUNCTION 'HR_UN_CALC_DATE'
            EXPORTING
              i_start_date = lv_adjust_rsadt
              i_term       = '1'
              i_periodunit = '012'
            IMPORTING
              e_end_date   = lv_adjust_rsadt.
        ENDIF.

        IF lv_adjust_rsadt IS INITIAL.
          lv_adjust_rsadt = iv_rsadt.
        ENDIF.

        CALL FUNCTION 'HR_99S_DATE_PLUS_TIME_UNIT'
          EXPORTING
            i_idate               = lv_adjust_rsadt
            i_time                = lv_years
            i_timeunit            = 'Y'
          IMPORTING
            o_idate               = ov_rsexd
          EXCEPTIONS
            invalid_period        = 1
            invalid_round_up_rule = 2
            internal_error        = 3
            OTHERS                = 4 ##FM_SUBRC_OK.

      ENDIF.
      ov_rsexd   = ov_rsexd - 1.

      TRY.
          lv_sflag_badi = 'X'.
          GET BADI lo_hrpayun_lwop.
        CATCH cx_badi_not_implemented.
          CLEAR lv_sflag_badi.
      ENDTRY.
      IF lv_sflag_badi = 'X'.

        CALL BADI lo_hrpayun_lwop->get_lwop
          EXPORTING
            i_begda         = iv_rsadt
            i_endda         = iv_endda
            i_pernr         = lv_pernr
          IMPORTING
            e_infty2001_tab = lt_p2001
            e_lwop_tab      = lt_lwop1
            e_lwop_tab30    = lt_lwop2.

      ENDIF.

      IF lt_lwop2[] IS NOT INITIAL.
        LOOP AT lt_lwop2 INTO ls_lwop2.
          IF ls_lwop2-begda < iv_rsadt AND ls_lwop2-endda > ov_rsexd.
            ls_lwop2-begda = iv_rsadt.
            ls_lwop2-endda = ov_rsexd.
          ELSEIF ls_lwop2-begda < iv_rsadt.
            ls_lwop2-begda = iv_rsadt.
          ELSEIF ls_lwop2-endda > ov_rsexd.
            ls_lwop2-endda = ov_rsexd.
          ENDIF.

          CALL FUNCTION 'DAYS_BETWEEN_TWO_DATES'
            EXPORTING
              i_datum_bis             = ls_lwop2-endda
              i_datum_von             = ls_lwop2-begda
              i_kz_incl_bis           = '1'
              i_szbmeth               = space
            IMPORTING
              e_tage                  = ls_lwop2-kaltg
            EXCEPTIONS
              days_method_not_defined = 1
              OTHERS                  = 2 ##FM_SUBRC_OK.

          ov_rsexd = ov_rsexd + ls_lwop2-kaltg.

        ENDLOOP.

      ENDIF.

    ENDIF.

  ENDMETHOD.
