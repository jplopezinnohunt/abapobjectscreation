  METHOD check_eligibility_step_02.

    DATA: lv_nb_years_c TYPE cmp_noyrs,
          lv_nb_years   TYPE i,
          lv_str1       TYPE string,
          lv_str2       TYPE string.

*   Default values for return variables
    ov_is_eligible = abap_false.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '005'
      INTO lv_str1.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '006'
      INTO lv_str2.
    CONCATENATE lv_str1 lv_str2
      INTO ov_message.

    CHECK is_p0021 IS NOT INITIAL.

*   Check age of child (below 25)
    IF iv_option = c_eligibility_option_1.
      CALL FUNCTION 'HRCM_TIME_PERIOD_CALCULATE'
        EXPORTING
          begda = is_p0021-fgbdt
          endda = sy-datum
        IMPORTING
          noyrs = lv_nb_years_c.
      MOVE lv_nb_years_c TO lv_nb_years.

      IF lv_nb_years < 25.
        CLEAR: ov_message.
        ov_is_eligible = abap_true.
        RETURN.
      ENDIF.

    ENDIF.

*   Others cases: check if child is a disabled child
    IF is_p0021-kdbsl IS NOT INITIAL.
      CLEAR: ov_message.
      ov_is_eligible = abap_true.
      RETURN.
    ENDIF.

  ENDMETHOD.
