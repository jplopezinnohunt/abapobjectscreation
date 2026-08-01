*&---------------------------------------------------------------------*
*& Subroutinenpool  YFI_YRGGBS00_EXIT
*&
*&---------------------------------------------------------------------*
*&
*&
*&---------------------------------------------------------------------*
PROGRAM YFI_YRGGBS00_EXIT.


*---------------------------------------------------------------------*
*       FORM U901                                                     *
*---------------------------------------------------------------------*
*       Payment currency for travel               .                   *
*---------------------------------------------------------------------*
FORM YY_GET_TRAVEL_BANK_DATA USING F_LIFNR TYPE LIFNR
                             CHANGING F_BVTYP TYPE BVTYP
                                      F_SUBRC TYPE SY-SUBRC
                                      F_FOUND TYPE XFELD.

  F_FOUND = ABAP_TRUE.

  CLEAR: F_BVTYP, F_SUBRC.
  SELECT SINGLE BVTYP FROM LFBK WHERE LIFNR = @F_LIFNR
                                AND   YYTRAVEL = @ABAP_TRUE
                      INTO @F_BVTYP.
  F_SUBRC = SY-SUBRC.

ENDFORM.