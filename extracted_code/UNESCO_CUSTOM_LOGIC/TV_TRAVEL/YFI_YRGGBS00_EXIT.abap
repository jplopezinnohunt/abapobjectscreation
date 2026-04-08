*&---------------------------------------------------------------------*
*& Subroutinenpool  YFI_YRGGBS00_EXIT
*&
*&---------------------------------------------------------------------*
*&
*&
*&---------------------------------------------------------------------*
PROGRAM yfi_yrggbs00_exit.


*---------------------------------------------------------------------*
*       FORM U901                                                     *
*---------------------------------------------------------------------*
*       Payment currency for travel               .                   *
*---------------------------------------------------------------------*
FORM yy_get_travel_bank_data USING f_lifnr TYPE lifnr
                             CHANGING f_bvtyp TYPE bvtyp
                                      f_subrc TYPE sy-subrc
                                      f_found TYPE xfeld.

  f_found = abap_true.

  CLEAR: f_bvtyp, f_subrc.
  SELECT SINGLE bvtyp FROM lfbk WHERE lifnr = @f_lifnr
                                AND   yytravel = @abap_true
                      INTO @f_bvtyp.
  f_subrc = sy-subrc.

ENDFORM.
