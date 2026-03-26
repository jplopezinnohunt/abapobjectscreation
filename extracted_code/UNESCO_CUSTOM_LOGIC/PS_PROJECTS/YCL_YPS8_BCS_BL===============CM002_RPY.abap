  METHOD GET_DATA.

    ME->INITIALIZE_DATA( ).
    ME->READ_DATA_FROM_DB( ).
    ME->PREPARE_DATA( ).
    IF MP_AGGREG = ABAP_TRUE.   "Only one summarized line per fund
      ME->AGGREGATE_DATA( ).
    ENDIF.

  ENDMETHOD.