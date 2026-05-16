* === DOCUMENTATION ===
PARAMETER=IS_FPAYH | KIND=P | STEXT=Payment medium: Payment data | INDEX= 001
PARAMETER=IS_FPAYHX | KIND=P | STEXT=Payment Medium: Payment Data Format | INDEX= 002
PARAMETER=I_PAYMEDIUM | KIND=P | STEXT=Payment Medium (X) or Note to Payee (Space) | INDEX= 003
PARAMETER=ES_FPAYHX | KIND=P | STEXT=Payment Medium: Customer-Specific Format Reference Fields | INDEX= 004
PARAMETER=T_FPAYP | KIND=P | STEXT=Payment medium: Data on paid items | INDEX= 005
* === EXPORT_PARAMETER ===
PARAMETER=ES_FPAYHX | DBFIELD=FPAYHX_FREF | REFERENCE=X
* === IMPORT_PARAMETER ===
PARAMETER=IS_FPAYH | DBFIELD=FPAYH
PARAMETER=IS_FPAYHX | DBFIELD=FPAYHX
PARAMETER=I_PAYMEDIUM | OPTIONAL=X | TYP=XFELD
* === TABLES_PARAMETER ===
PARAMETER=T_FPAYP | DBSTRUCT=FPAYP
* === SOURCE ===
LINE=FUNCTION fi_paymedium_dmee_cgi_05 .
LINE=*"----------------------------------------------------------------------
LINE=*"*"Local Interface:
LINE=*"  IMPORTING
LINE=*"     VALUE(IS_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
LINE=*"     VALUE(IS_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
LINE=*"     VALUE(I_PAYMEDIUM) TYPE  XFELD OPTIONAL
LINE=*"  EXPORTING
LINE=*"     REFERENCE(ES_FPAYHX) LIKE  FPAYHX_FREF STRUCTURE  FPAYHX_FREF
LINE=*"  TABLES
LINE=*"      T_FPAYP STRUCTURE  FPAYP
LINE=*"----------------------------------------------------------------------

LINE=  DATA:
LINE=    lo_cgi_call05 TYPE REF TO if_idfi_cgi_call05.

LINE=* ---------------------------------------------------------------------
LINE=* START OF DMEE without EXIT
LINE=* ---------------------------------------------------------------------
LINE=* New fiori app processing requires logging of non-persistent info

LINE=  CALL METHOD cl_idfi_cgi_call05_factory=>get_instance
LINE=    EXPORTING
LINE=      is_fpayh     = is_fpayh
LINE=      is_fpayhx    = is_fpayhx
LINE=      iv_paymedium = i_paymedium
LINE=      it_fpayp     = t_fpayp[]
LINE=    RECEIVING
LINE=      ro_instance  = lo_cgi_call05.
LINE=  IF lo_cgi_call05 IS BOUND.
LINE=    CALL METHOD lo_cgi_call05->fill_fpay_fref
LINE=      EXPORTING
LINE=        is_fpayh       = is_fpayh
LINE=        is_fpayhx      = is_fpayhx
LINE=        iv_paymedium   = i_paymedium
LINE=      CHANGING
LINE=        cs_fpayhx_fref = es_fpayhx
LINE=        ct_fpayp_fref  = t_fpayp[].
LINE=  ENDIF. "IF lo_cgi_call05 IS BOUND.

LINE=ENDFUNCTION.