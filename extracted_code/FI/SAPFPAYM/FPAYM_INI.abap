************************************************************************
* Include FPAYM_INI                                                    *
* Initialization                                                       *
************************************************************************


*- Initialization -----------------------------------------------------*

INITIALIZATION.

* Set info button
  ibutton = icon_information.

* Default values for parameters
  par_xlst = 'X'.
  par_xerr = 'X'.

* default variant for accompanying list
  CLEAR gs_variant.
  gs_variant-report = sy-repid.
  CALL FUNCTION 'REUSE_ALV_VARIANT_DEFAULT_GET'
       EXPORTING
            i_save     = 'A'
       CHANGING
            cs_variant = gs_variant
       EXCEPTIONS
            not_found  = 4.
  IF sy-subrc EQ 0.
    par_vari = gs_variant-variant.
  ENDIF.