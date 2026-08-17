FUNCTION Y_FI_PAYMEDIUM_101_41.
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

data: w_mttrailer LIKE dta_mttrailer.

*  PERFORM create_trailer
*          USING    i_fpayhx
*          CHANGING t_file_output[].         "Output table

w_mttrailer-endoffile = '-'.
PERFORM fill_output_table
       USING    w_mttrailer
       CHANGING t_file_output[].

e_repid = sy-repid.

***OSS Note 1313075
CALL FUNCTION 'Y_FI_PAYMEDIUM_41'
  EXPORTING
    I_FPAYH             = I_FPAYH
    I_FPAYHX            = I_FPAYHX
  TABLES
    T_FILE_OUTPUT       = T_FILE_OUTPUT
  CHANGING
    C_WAERS             = E_WAERS
    C_SUM               = E_SUM.

ENDFUNCTION.