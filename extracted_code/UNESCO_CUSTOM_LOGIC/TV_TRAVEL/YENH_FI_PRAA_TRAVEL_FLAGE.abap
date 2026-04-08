ENHANCEMENT 1  .
  IF XBLFBK-YYTRAVEL(1)                   NE NODATA.
    CLEAR FT.
    FT-FNAM = 'LFBK-YYTRAVEL                 '.
    FT-FNAM+30(4) =  '(01)'.
    CONDENSE FT-FNAM NO-GAPS.
    FT-FVAL = XBLFBK-YYTRAVEL                  .
    APPEND FT.
  ENDIF.
ENDENHANCEMENT.
