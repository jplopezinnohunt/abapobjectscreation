  METHOD constructor.

    "Set values for ranges
    APPEND VALUE #( sign = 'I' option = 'EQ' low = '9A' ) TO mr_rldnr.
    APPEND VALUE #( sign = 'I' option = 'EQ' low = 'UNES' ) TO mr_bukrs.
    APPEND VALUE #( sign = 'I' option = 'EQ' low = 'UNES' ) TO mr_fikrs.
    APPEND VALUE #( sign = 'I' option = 'EQ' low = 'GEF' ) TO mr_gsber.
    APPEND VALUE #( sign = 'I' option = 'EQ' low = 'EUR' ) TO mr_waers.
    mr_fipex = VALUE #( ( sign = 'E' option = 'EQ' low = 'GAINS' )
                        ( sign = 'E' option = 'EQ' low = 'REVENUE' ) ).
    mr_vrgng = VALUE #( ( sign = 'E' option = 'EQ' low = 'HRM1' )   "PBC pre-commitment
                        ( sign = 'E' option = 'EQ' low = 'HRM2' )   "PBC commitment
                        ( sign = 'E' option = 'EQ' low = 'HRP1' ) )."Payroll posting
    "Set fund types perimeters
     "APPEND VALUE #( sign = 'E' option = 'EQ' low = '019' ) TO mr_fund_type.
    SELECT 'I', 'EQ', fund_type AS low FROM fmfundtype WHERE fm_area IN @mr_fikrs
                                                       AND   zzfix_rate = @abap_true
                                       INTO TABLE @mr_fund_type.
    "For revaluation exclusion
    "APPEND VALUE #( sign = 'I' option = 'EQ' low = '019' ) TO mr_fund_type3.
    SELECT 'E', 'EQ', fund_type AS low FROM fmfundtype WHERE fm_area IN @mr_fikrs
                                                       AND   zzfix_rate = @abap_true
                                       INTO TABLE @mr_fund_type3.

    mr_fipex3 = VALUE #( ( sign = 'I' option = 'EQ' low = 'GAINS' )
                         ( sign = 'I' option = 'EQ' low = 'REVENUE' ) ).

    mr_vrgng3 = VALUE #( ( sign = 'I' option = 'EQ' low = 'HRM1' )   "PBC pre-commitment
                        ( sign = 'I' option = 'EQ' low = 'HRM2' )   "PBC commitment
                        ( sign = 'I' option = 'EQ' low = 'HRP1' ) )."Payroll posting

    "Get start date for fixed rate
    SELECT SINGLE CAST( low AS DATS ) INTO @mv_start_date FROM tvarvc WHERE name = 'Y_FM_FIXED_RATE_START'
                                                                      AND   type = 'P'.
    IF mv_start_date IS INITIAL OR mv_start_date = space.
      mv_start_date = '99991231'.
    ENDIF.

    "staff operations
    mr_vrgng2 = VALUE #( ( sign = 'I' option = 'EQ' low = 'HRM1' )   "PBC pre-commitment
                        ( sign = 'I' option = 'EQ' low = 'HRM2' )   "PBC commitment
                        ( sign = 'I' option = 'EQ' low = 'HRP1' ) )."Payroll posting

    APPEND VALUE #( sign = 'I' option = 'EQ' low = 'EUR' ) TO mr_waers2.
    APPEND VALUE #( sign = 'I' option = 'EQ' low = 'USD' ) TO mr_waers2.

  ENDMETHOD.
