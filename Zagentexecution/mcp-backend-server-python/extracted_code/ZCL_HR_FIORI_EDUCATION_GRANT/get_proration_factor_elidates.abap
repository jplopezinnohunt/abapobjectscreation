  METHOD get_proration_factor_elidates.

    DATA : lv_round       TYPE pun_egrty VALUE '4',
           lv_yearss      TYPE i,
           lv_months      TYPE i,
           lv_days        TYPE i,
           lv_month_syear TYPE pun_egfac,
           lv_month_atten TYPE pun_egfac.

    DATA(ls_pa0016) = is_pa0016.
    DATA(ls_p0965) = is_p0965.

    "calc eliBegda and eliEndda
    IF ls_pa0016-begda > ls_p0965-egyfr .
      ls_p0965-elibegda = ls_pa0016-begda.
    ELSE.
      ls_p0965-elibegda =  ls_p0965-egyfr .
    ENDIF.
    IF ls_pa0016-ctedt > ls_p0965-egyto .
      ls_p0965-eliendda = ls_p0965-egyto.
    ELSE.
      ls_p0965-eliendda = ls_pa0016-ctedt.
    ENDIF.

    "New way of calculating proration factor

    CALL METHOD cl_hrpadun_eg_appl=>bl_calc_period_days
      EXPORTING
        begda = ls_p0965-begda
        endda = ls_p0965-endda
      IMPORTING
        days  = DATA(lv_days_year).


    CALL METHOD cl_hrpadun_eg_appl=>bl_calc_period_days
      EXPORTING
        begda = ls_p0965-elibegda
        endda = ls_p0965-eliendda
      IMPORTING
        days  = DATA(lv_days_attend).

    IF NOT lv_days_attend IS INITIAL AND lv_days_attend gt 0 and lv_days_year > 0.
      ev_egfac = ( lv_days_attend / lv_days_year ) * 100 .


*    CALL METHOD cl_hrpadun_eg_appl=>bl_calc_period
*      EXPORTING
*        begda     = ls_p0965-begda
*        endda     = ls_p0965-endda
*        round     = lv_round
*      IMPORTING
*        years     = lv_yearss
*        months    = lv_months
*        days      = lv_days
*        calc_base = lv_month_syear.
*
*    CLEAR : lv_yearss, lv_months, lv_days.
*
*    CALL METHOD cl_hrpadun_eg_appl=>bl_calc_period
*      EXPORTING
*        begda     = ls_p0965-elibegda
*        endda     = ls_p0965-eliendda
*        round     = lv_round
*      IMPORTING
*        years     = lv_yearss
*        months    = lv_months
*        days      = lv_days
*        calc_base = lv_month_atten.
*
*    IF NOT lv_month_atten IS INITIAL AND lv_month_atten > 0.
*      ev_egfac = ( lv_month_atten / lv_month_syear ) * 100 .
*    ENDIF.

      "eli dates
      ev_elibegda = ls_p0965-elibegda.
      ev_eliendda = ls_p0965-eliendda.



    ENDIF.

  ENDMETHOD.
