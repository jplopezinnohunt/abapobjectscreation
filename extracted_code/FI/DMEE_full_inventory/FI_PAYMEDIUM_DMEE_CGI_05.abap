FUNCTION fi_paymedium_dmee_cgi_05 .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IS_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(IS_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"     VALUE(I_PAYMEDIUM) TYPE  XFELD OPTIONAL
*"  EXPORTING
*"     REFERENCE(ES_FPAYHX) LIKE  FPAYHX_FREF STRUCTURE  FPAYHX_FREF
*"  TABLES
*"      T_FPAYP STRUCTURE  FPAYP
*"----------------------------------------------------------------------

  DATA:
    lo_cgi_call05 TYPE REF TO if_idfi_cgi_call05.

* ---------------------------------------------------------------------
* START OF DMEE without EXIT
* ---------------------------------------------------------------------
* New fiori app processing requires logging of non-persistent info

  CALL METHOD cl_idfi_cgi_call05_factory=>get_instance
    EXPORTING
      is_fpayh     = is_fpayh
      is_fpayhx    = is_fpayhx
      iv_paymedium = i_paymedium
      it_fpayp     = t_fpayp[]
    RECEIVING
      ro_instance  = lo_cgi_call05.
  IF lo_cgi_call05 IS BOUND.
    CALL METHOD lo_cgi_call05->fill_fpay_fref
      EXPORTING
        is_fpayh       = is_fpayh
        is_fpayhx      = is_fpayhx
        iv_paymedium   = i_paymedium
      CHANGING
        cs_fpayhx_fref = es_fpayhx
        ct_fpayp_fref  = t_fpayp[].
  ENDIF. "IF lo_cgi_call05 IS BOUND.

ENDFUNCTION.