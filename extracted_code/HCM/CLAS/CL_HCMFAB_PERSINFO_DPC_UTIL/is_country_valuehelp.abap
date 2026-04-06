METHOD is_country_valuehelp.

  CLEAR rv_is_country_valuehelp.

  IF find( val = iv_nav_property_name
               sub = 'VALUEHELP' ) <> -1 AND
     find( val = iv_nav_property_name
               sub = 'COUNTRY' ) <> -1.        "e.g. TOVALUEHELPCOUNTRY
    rv_is_country_valuehelp = abap_true.
    EXIT.
  ENDIF.

  IF find( val = iv_entity_name
               sub = 'VALUEHELP' ) <> -1 AND
     find( val = iv_entity_name
               sub = 'COUNTRY' ) <> -1.        "e.g. TOVALUEHELPCOUNTRY
    rv_is_country_valuehelp = abap_true.
    EXIT.
  ENDIF.

ENDMETHOD.
