  METHOD convert_to_currency.

    CLEAR ev_local_amount.

    CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
      EXPORTING
*       CLIENT           = SY-MANDT
        date             = iv_date
        foreign_amount   = iv_foreign_amount
        foreign_currency = iv_foreign_currency
        local_currency   = iv_local_currency
*       RATE             = 0
        type_of_rate     = iv_type_of_rate
*       READ_TCURR       = 'X'
      IMPORTING
*       EXCHANGE_RATE    =
*       FOREIGN_FACTOR   =
        local_amount     = ev_local_amount
*       LOCAL_FACTOR     =
*       EXCHANGE_RATEX   =
*       FIXED_RATE       =
*       DERIVED_RATE_TYPE       =
      EXCEPTIONS
        no_rate_found    = 1
        overflow         = 2
        no_factors_found = 3
        no_spread_found  = 4
        derived_2_times  = 5
        OTHERS           = 6.
    ev_subrc = sy-subrc.

  ENDMETHOD.
