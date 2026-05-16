************************************************************************
* Include FPAYM_INI                                                    *
* Initialization                                                       *
************************************************************************


*- Initialization -----------------------------------------------------*

INITIALIZATION.

* Set info button
  IBUTTON = ICON_INFORMATION.

* Default values for parameters
  PAR_XLST = 'X'.
  PAR_XERR = 'X'.

* default variant for accompanying list
  CLEAR GS_VARIANT.
  GS_VARIANT-REPORT = SY-REPID.
  CALL FUNCTION 'REUSE_ALV_VARIANT_DEFAULT_GET'
       EXPORTING
            I_SAVE     = 'A'
       CHANGING
            CS_VARIANT = GS_VARIANT
       EXCEPTIONS
            NOT_FOUND  = 4.
  IF SY-SUBRC EQ 0.
    PAR_VARI = GS_VARIANT-VARIANT.
  ENDIF.