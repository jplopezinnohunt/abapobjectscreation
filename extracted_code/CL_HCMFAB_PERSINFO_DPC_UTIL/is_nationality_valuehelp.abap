METHOD is_nationality_valuehelp.

  CLEAR rv_is_nationality_valuehelp.

  IF ( find( val = iv_nav_property_name sub = 'VALUEHELP' ) <> -1 AND
       find( val = iv_nav_property_name sub = 'NATION' ) <> -1 )         "e.g. TOVALUEHELPNATION
    OR iv_nav_property_name = 'TOVALUEHELPFNAMK'
    OR iv_nav_property_name = 'TOVALUEHELPNATLAND'.

    rv_is_nationality_valuehelp = abap_true.
    EXIT.
  ENDIF.

  IF ( find( val = iv_entity_name sub = 'ValueHelp' ) <> -1 AND
       find( val = iv_entity_name sub = 'Nation' ) <> -1 )         "e.g. VALUEHELPNATION
    OR iv_entity_name = 'ValueHelpNatiotxt'
    OR iv_entity_name = 'ValueHelpNatLand'.

    rv_is_nationality_valuehelp = abap_true.
    EXIT.
  ENDIF.


ENDMETHOD.
