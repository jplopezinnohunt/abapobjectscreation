FUNCTION Y_FI_PAYMEDIUM_101_40.
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(I_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"  EXPORTING
*"     REFERENCE(E_WAERS) LIKE  FPAYH-WAERS
*"     REFERENCE(E_SUM) LIKE  FPAYH-RWBTR
*"     REFERENCE(E_REPID) LIKE  SY-REPID
*"  TABLES
*"      T_FILE_OUTPUT STRUCTURE  FPM_FILE
*"--------------------------------------------------------------------

*-----------------------------------------------------------------------
* Creates trailer record of payment medium format S.W.I.F.T. MT 101
*-----------------------------------------------------------------------

  PERFORM create_trailer
          USING    i_fpayhx
          CHANGING t_file_output[].         "Output table

  e_repid = sy-repid.

ENDFUNCTION.