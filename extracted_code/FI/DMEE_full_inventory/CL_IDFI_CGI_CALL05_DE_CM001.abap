  METHOD country_specific_call.
    DATA:
      lv_code       TYPE string,
      ls_instparams TYPE i015w1_par,
      lv_not_found  TYPE boole-boole.

*   ---------------------------------------------------------------------
*   FPAYHX-REF14:
*   ---------------------------------------------------------------------
*   0
*   Payment Method
*   ---------------------------------------------------------------------
    IF is_fpayh-dtws2 IS NOT INITIAL.
      CLEAR ls_instparams.
      ls_instparams-dtws2 = is_fpayh-dtws2.
      CALL FUNCTION 'FI_PAYMENT_INSTRUCTION_CONVERT'
        EXPORTING
          i_dtwsc      = 'SEPA'                       "#EC NOTEXT
          i_dtwsf      = '2'                          "#EC NOTEXT
          i_i015w1_par = ls_instparams
        IMPORTING
          e_code       = lv_code
          e_not_found  = lv_not_found.

      IF lv_not_found IS NOT INITIAL.
        lv_code = cl_idfi_cgi_dmee_fallback=>gc_trf.
      ENDIF.
      cs_fpayhx_fref-ref14+0(10) = lv_code.
    ENDIF.
  ENDMETHOD.