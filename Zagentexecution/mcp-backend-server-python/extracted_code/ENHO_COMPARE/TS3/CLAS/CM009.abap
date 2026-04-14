  METHOD convert_to_currency_2.

    DATA: ev_local_amount_2 TYPE bseg-dmbtr.


*Step 1 Convert USD UNORE to EUR UNORE
    CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
      EXPORTING
        date             = iv_date
        foreign_amount   = iv_foreign_amount
        foreign_currency = 'USD'                 " USD UNORE
        local_currency   = 'EUR'                 " EUR UNORE
        type_of_rate     = iv_type_of_rate_unore " M
*       READ_TCURR       = 'X'
      IMPORTING
        local_amount     = ev_local_amount_2      "USD Unore converted to EUR Unore
      EXCEPTIONS
        no_rate_found    = 1
        overflow         = 2
        no_factors_found = 3
        no_spread_found  = 4
        derived_2_times  = 5
        OTHERS           = 6.
    ev_subrc = sy-subrc.


*Step 2 Convert EUR UNORE to USD BR
    CLEAR ev_local_amount.
    CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
      EXPORTING
        date             = iv_date
        foreign_amount   = ev_local_amount_2     " Amount converted to EUR unore
        foreign_currency = 'EUR'                " EUR
        local_currency   = 'USD'                " USD
        type_of_rate     = iv_type_of_rate      "EURX
      IMPORTING
        local_amount     = ev_local_amount    "EUR Unore converted to USD BR
      EXCEPTIONS
        no_rate_found    = 1
        overflow         = 2
        no_factors_found = 3
        no_spread_found  = 4
        derived_2_times  = 5
        OTHERS           = 6.
    ev_subrc = sy-subrc.

  ENDMETHOD.
