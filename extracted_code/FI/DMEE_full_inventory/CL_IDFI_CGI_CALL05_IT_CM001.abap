METHOD country_specific_call.
  DATA: ls_fpayp TYPE fpayp,
        lv_cup   TYPE itcup,
        lv_cig   TYPE itcug,
        lv_mgo   TYPE itmgo,
        lv_gjahr TYPE gjahr,
        lv_belnr TYPE belnr_d.

  DATA: ls_t042z TYPE t042z.                                  "n2699168

*  CHECK is_fpayh-zbnks EQ 'IT'.                              "n3043741

* ---------------------------------------------------------------------
* START OF DMEE without EXIT
* ---------------------------------------------------------------------

* Begin of SAP Note 2699168
* ----------------------------------------------------------------------
* Check that FBPM is not executed before RFWEBU00 execution - Italy Only
* ----------------------------------------------------------------------
*  Check if format is credit transfer or direct debit
  IF is_fpayh-mguid IS NOT INITIAL " SEPA Mandate exists
    OR is_fpayhx-xeinz EQ abap_true. "direct debit

    CALL FUNCTION 'FI_PAYMENT_METHOD_PROPERTIES'
      EXPORTING
        i_zlsch = is_fpayh-rzawe
        i_zbukr = is_fpayh-zbukr
        i_hwaer = is_fpayh-waers
        i_zwaer = is_fpayh-waers
      IMPORTING
        e_t042z = ls_t042z
      EXCEPTIONS
        OTHERS  = 99.

*     Check that the report RFWEBU00 has been executed
    IF ls_t042z-xwech IS NOT INITIAL AND is_fpayh-paygr IS INITIAL.
*       For Payment Run Date &1 / Id &2 post Bill of Exchange first.
      MESSAGE e010(idfipaym_msg) WITH is_fpayh-laufd is_fpayh-laufi.
    ENDIF. "IF ls_t042z-xwech IS NOT INITIAL AND is_fpayh-paygr IS INITIAL.
  ENDIF. "IF is_fpayh-mguid IS NOT INITIAL OR is_fpayhx-xeinz EQ abap_true..
* ----------------------------------------------------------------------
* Check that FBPM is not executed before RFWEBU00 execution - Italy Only
* ----------------------------------------------------------------------
* End of SAP Note 2699168

*   -------------------------------------------------------------------
*   FPAYHX-REF14:
*   -------------------------------------------------------------------
*
*   CUP + no + CIG + no + MGO + no
*   -------------------------------------------------------------------

  LOOP AT ct_fpayp_fref INTO ls_fpayp.
    lv_belnr = ls_fpayp-doc2r+4(10).
    lv_gjahr = ls_fpayp-doc2r+14(4).

    CALL FUNCTION 'GET_CUP_CIG_IT'
      EXPORTING
        i_bukrs = ls_fpayp-bukrs
        i_belnr = lv_belnr
        i_gjahr = lv_gjahr
      IMPORTING
        e_cup   = lv_cup
        e_cig   = lv_cig
        e_mgo   = lv_mgo.
    EXIT.
  ENDLOOP.

  IF lv_cup IS NOT INITIAL.
    CONCATENATE
      'CUP'                                           "#EC NOTEXT
      lv_cup
      INTO
        cs_fpayhx_fref-ref14
      SEPARATED BY
        space.
  ENDIF.

  IF lv_cig IS NOT INITIAL.
    CONCATENATE
      cs_fpayhx_fref-ref14
      'CIG'                                         "#EC NOTEXT
      lv_cig
      INTO
        cs_fpayhx_fref-ref14
      SEPARATED BY
        space.
  ENDIF.

  IF lv_mgo IS NOT INITIAL.
    CONCATENATE
      cs_fpayhx_fref-ref14
      'MGO'                                         "#EC NOTEXT
      lv_mgo
      INTO
        cs_fpayhx_fref-ref14
      SEPARATED BY
        space.
  ENDIF.

ENDMETHOD.