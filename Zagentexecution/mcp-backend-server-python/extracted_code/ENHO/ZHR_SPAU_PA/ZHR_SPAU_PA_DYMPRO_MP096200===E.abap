ENHANCEMENT 2  .
*
ENDENHANCEMENT.
ENHANCEMENT 3  .
*Screen Field DSisplay
  LOOP AT SCREEN .
        IF screen-name eq 'P0962-RSPCN' OR screen-name eq 'P0962-RSWAI' OR screen-name eq 'LANDLORD'.
          screen-active = '0'.
          MODIFY SCREEN.
        ENDIF.
  ENDLOOP.
ENDENHANCEMENT.
