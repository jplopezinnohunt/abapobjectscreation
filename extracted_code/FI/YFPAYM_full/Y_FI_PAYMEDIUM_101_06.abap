FUNCTION Y_FI_PAYMEDIUM_101_06.
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IS_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(IS_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"     VALUE(I_PAYMEDIUM) TYPE  XFELD OPTIONAL
*"  EXPORTING
*"     REFERENCE(ES_FPAYHX_CREF) LIKE  FPAYHX_CREF
*"  STRUCTURE  FPAYHX_CREF
*"  TABLES
*"      T_FPAYP STRUCTURE  FPAYP
*"--------------------------------------------------------------------

ES_FPAYHX_CREF-zref01 = 'Reference TEST'.

ENDFUNCTION.