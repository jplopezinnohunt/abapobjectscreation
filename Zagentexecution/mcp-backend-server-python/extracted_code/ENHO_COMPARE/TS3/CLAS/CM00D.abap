  METHOD get_br_impact.

    IF iv_trbtrp = 0.
      ev_zzbrimpacted = 'E'.
    ELSE.
      ev_zzbrimpacted = 'X'.
    ENDIF.

    IF iv_wrttp = '54'.    "Check if from BSEG
      IF iv_bseg_dmbtr IS NOT INITIAL AND iv_bseg_shkzg IS NOT INITIAL.
        ev_zzamountbrlc = iv_bseg_dmbtr.
        IF iv_bseg_shkzg = 'H'.
          MULTIPLY ev_zzamountbrlc BY -1.
        ENDIF.
      ELSEIF iv_bseg_belnr IS NOT INITIAL.
        SELECT SINGLE shkzg, dmbtr FROM bseg WHERE bukrs = @iv_bukrs
                                             AND   belnr = @iv_bseg_belnr
                                             AND   gjahr = @iv_bseg_gjahr
                                             AND   buzei = @iv_bseg_buzei
                                   INTO ( @DATA(lv_shkzg), @ev_zzamountbrlc ).
        IF lv_shkzg = 'H'.
          MULTIPLY ev_zzamountbrlc BY -1.
        ENDIF.
      ENDIF.
      "Check if the value is filled from table EKBE
    ELSEIF iv_wrttp = '51'    "Purchase Orders    "Check if the value is filled from table EKBE
       AND iv_vrgng = 'RMBE'
       AND iv_btart = '0200'.   "Reduction

      "GET amount from ekbe
      ycl_mm_po_utilities=>get_ekbe_amounts_1( EXPORTING iv_ebeln = iv_refbn
                                                         iv_ebelp = iv_rfpos
                                                         iv_vgabe = '1'  "GR
                                                         iv_gjahr = iv_gjahr
                                                         iv_waers = iv_twaer
                                                         iv_geber = iv_fincode
                                               IMPORTING ev_dmbtr = ev_zzamountbrlc ).
      MULTIPLY ev_zzamountbrlc BY -1.  "Because of reduction
    ELSE.
      IF iv_kursf IS NOT INITIAL.
        IF iv_kursf < 0.
          ev_zzamountbrlc = - iv_trbtrp / iv_kursf.
        ELSE.
          ev_zzamountbrlc = iv_trbtrp * iv_kursf.
        ENDIF.
      ELSE.
*Convert Tramsaction Amount to UNORE
        CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
          EXPORTING
            date             = iv_budat
            foreign_amount   = iv_trbtrp
            foreign_currency = iv_twaer
            local_currency   = 'USD'
            type_of_rate     = 'M'
          IMPORTING
            local_amount     = ev_zzamountbrlc
          EXCEPTIONS
            no_rate_found    = 1
            overflow         = 2
            no_factors_found = 3
            no_spread_found  = 4
            derived_2_times  = 5
            OTHERS           = 6.
      ENDIF.
    ENDIF.

    ev_zzamountbrdiff = iv_fkbtrp - ev_zzamountbrlc.

  ENDMETHOD.
