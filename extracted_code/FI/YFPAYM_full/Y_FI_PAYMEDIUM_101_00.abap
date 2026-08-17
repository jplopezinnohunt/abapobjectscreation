FUNCTION Y_FI_PAYMEDIUM_101_00.
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(I_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"  EXPORTING
*"     VALUE(E_SRTF1) LIKE  FPAYH-SRTF1
*"--------------------------------------------------------------------

*-----------------------------------------------------------------------
* Fill additional sort field for payment medium format S.W.I.F.T. MT 101
*-----------------------------------------------------------------------

  DATA:
    BEGIN OF ls_srtf1,
      ausfd(6)  TYPE c,
      ubknt     LIKE fpayhx-ubknt,
    END OF ls_srtf1.

*  ls_srtf1-ausfd = i_fpayh-ausfd+2(6). "without century - save space
*  ls_srtf1-ubknt = i_fpayhx-ubknt.
*  e_srtf1        = ls_srtf1.
  e_srtf1 = 'TEST SORT FIELD'.

ENDFUNCTION.