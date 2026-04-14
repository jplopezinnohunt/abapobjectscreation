  METHOD get_exchange_rate.

    CALL FUNCTION 'READ_EXCHANGE_RATE'
      EXPORTING
*       CLIENT           = SY-MANDT
        date             = iv_date
        foreign_currency = iv_foreign_currency
        local_currency   = iv_local_currency
        type_of_rate     = 'EURX'
*       EXACT_DATE       = ' '
      IMPORTING
        exchange_rate    = ev_exchange_rate
*       FOREIGN_FACTOR   =
*       LOCAL_FACTOR     =
*       VALID_FROM_DATE  =
*       DERIVED_RATE_TYPE       =
*       FIXED_RATE       =
*       OLDEST_RATE_FROM =
      EXCEPTIONS
        no_rate_found    = 1
        no_factors_found = 2
        no_spread_found  = 3
        derived_2_times  = 4
        overflow         = 5
        zero_rate        = 6
        OTHERS           = 7.

    ev_subrc = sy-subrc.

  ENDMETHOD.
